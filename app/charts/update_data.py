'''Update data functions'''

import math
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist

from .models import Coin
from .models import Sfmodel

def erase_coin_data(symbol):
    '''Erase all data for a certain coin'''

    try:
        Coin.objects.filter(name=symbol).all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase data for {symbol}: {error}')
        return False

    return True

def calculate_base_reward(minted_coins: int):
    '''XMR Base block reward calculation'''

    # https://monero-book.cuprate.org/consensus_rules/blocks/reward.html

    money_supply = 2**64 - 1
    target_block_time_minutes = 2
    emission_speed_factor = 20 - (target_block_time_minutes - 1)

    base_reward = (money_supply - minted_coins) >> emission_speed_factor

    # Tail emission: When we reach a specific emission point, a minimum reward is enforced
    # The minimum subsidy is 0.3 XMR per minute = 0.6 XMR per block with 2-minute blocks
    # 0.6 XMR = 0.6 * 10^12 piconero (1 XMR = 10^12 piconero)
    minimum_subsidy = int(0.6 * (10**12))  # 0.6 XMR in piconero

    # For testing the specific supply that triggers tail emission:
    # If we're very close to max supply, use the minimum subsidy
    if minted_coins > (money_supply - (minimum_subsidy << emission_speed_factor)):
        base_reward = minimum_subsidy

    return base_reward

def calculate_block_reward(base_reward, block_weight=None, median_block_weight=None):
    '''XMR Block reward calculation with penalty for large blocks

    Args:
        base_reward: The base reward amount in piconero
        block_weight: Current block weight (optional)
        median_block_weight: Effective median block weight (optional)
    Returns:
        The final block reward after applying any penalty
    '''

    # Default values if not provided
    if block_weight is None:
        block_weight = 100  # Example block weight

    if median_block_weight is None:
        median_block_weight = 300000  # Default effective median weight
        # Reference: https://monero-book.cuprate.org/consensus_rules/blocks/weights.html#effective-median-weight

    # If the current block weight is not more than the median weight, then the block reward is the base reward
    if block_weight <= median_block_weight:
        return base_reward

    # Otherwise, apply penalty formula: baseReward * (1 - ((blockWeight/effectiveMedianWeight) - 1)^2)
    penalty_ratio = (block_weight / median_block_weight) - 1
    block_reward = base_reward * (1 - penalty_ratio ** 2)

    return int(block_reward)

def reset_sf_model():
    '''Reset and recalculate the Stock-to-Flow model'''
    
    Sfmodel.objects.all().delete()

    timevar = 1283
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    previous_supply = 0
    current_supply = 0
    calculate_days_in_the_future = 90

    sf_aux = 0
    count = 0
    count_aux = 0

    coin_data = Coin.objects.order_by('date').filter(name='xmr')

    total_data_points = len(coin_data)
    print(f'[DEBUG] XMR data points: {len(coin_data)}')

    if total_data_points == 0:

        print('[INFO] No coin data found for XMR')
        return False

    for data_point in coin_data:

        print(f'[DEBUG] Processing Data Point {data_point.name} at {data_point.date}')

        if data_point.priceusd < 0.1:
            data_point.priceusd = 0.1
            data_point.pricebtc = 0.000001

        sf_calculation = sf_aux * 1.3 + 100
        if data_point.stocktoflow > sf_calculation:
            data_point.stocktoflow = sf_aux

        sf_aux = data_point.stocktoflow

        # Calculate current supply
        if data_point.supply > 0:
            current_supply = int(data_point.supply) * 10 * 12
        else:
            current_supply = previous_supply

        print(f'[DEBUG] Current XMR supply: {current_supply} at {data_point.date}')

        count += 1
        count_aux += 1

        date_aux1 = datetime.strptime('2017-12-29', '%Y-%m-%d')
        print(f'[DEBUG] DATE AUX1: {date_aux1}')
        date_aux2 = datetime.strptime(str(data_point.date), '%Y-%m-%d')
        print(f'[DEBUG] DATE AUX2: {date_aux2}')

        if date_aux2 < date_aux1:

            #print(f'[DEBUG] Date {date_aux2} is less than {date_aux1}')
            lastprice = data_point.priceusd
            current_inflation = data_point.inflation
            greyline = 0
            count_aux = 0
        else:
            #print(f'[DEBUG] Date {date_aux2} is larger than {date_aux1}')
            day = date_aux2 - timedelta(timevar)
            print(f'[DEBUG] Day: {day}')
            coin_aux1 = Coin.objects.filter(name='xmr').get(date=day)
            print(f'[DEBUG] Timevar: {timevar}')
            day = date_aux2 - timedelta(timevar+1)
            print(f'[DEBUG] Next Day: {day}')

            try:
                coin_aux2 = Coin.objects.filter(name='xmr').get(date=day)
            except ObjectDoesNotExist as error:
                coin_aux2 = False
                print(f'[ERROR] No data for date {day}: {error}')
            date_aux3 = datetime.strptime('2017-12-29', '%Y-%m-%d')

            if date_aux3 + timedelta(int(count_aux*2)) < datetime.strptime('2021-07-03', '%Y-%m-%d'):

                day = date_aux3 + timedelta(int(count_aux*2))
                print(f'[DEBUG] Next Next Day: {day}')
                try:
                    coin_aux3 = Coin.objects.filter(name='xmr').get(date=day)
                except ObjectDoesNotExist as error:
                    coin_aux3 = False
                    print(f'[ERROR] No data for date {day}: {error}')

                if coin_aux3:
                    if (coin_aux3.inflation/current_inflation) > 1.2 or (coin_aux3.inflation/current_inflation) < 0.8:
                        coin_aux3.inflation = current_inflation
                    else:
                        current_inflation = coin_aux3.inflation
                        supply2 = current_supply
                else:
                    supply2 = current_supply
                    reward2 = calculate_base_reward(supply2)

                supply2 += int(720*reward2)
                current_inflation = 100*reward2*720*365/supply2

            if coin_aux1 and coin_aux2:
                lastprice += (coin_aux1.priceusd/coin_aux2.priceusd-1)*lastprice
                actualprice = lastprice*(math.sqrt(coin.inflation/current_inflation))
                greyline = actualprice
            else:
                greyline = 0

            previous_supply = current_supply

        # Create the entry in the database
        model = Sfmodel()
        model.date = data_point.date
        model.priceusd = data_point.priceusd
        model.pricebtc = data_point.pricebtc
        model.stocktoflow = data_point.stocktoflow
        model.greyline = greyline
        model.color = 30 * data_point.pricebtc / (count * delta + v0)
        model.save()
        print(f'[DEBUG] Succesfully saved {model}')
        print('[DEBUG]--------------------------')


        # Calculate Stocktoflow X days in the future

        count_aux = 0
        for count_aux in range(calculate_days_in_the_future):

            print(f'[DEBUG] Calculate Sfmodel {count_aux + 1} days in the future')
            future_date = date.today() + timedelta(count_aux)

            block_reward = calculate_base_reward(current_supply)
            print(f'[DEBUG] Block reward: {block_reward}')

            current_supply += int(720*block_reward)
            print(f'[DEBUG] Total Supply: {current_supply}')

            # Create the entry in the database
            model = Sfmodel()
            model.date = datetime.strftime(future_date, '%Y-%m-%d')
            print(f'[INFO] {model.date}')
            model.stocktoflow = (100/(100*block_reward*720*365/current_supply))**1.65
            print(f'[INFO] {model.stocktoflow}')
            model.priceusd = 0
            model.pricebtc = 0
            model.greyline = 0
            model.color = 0
            model.priceusd = 0
            model.greyline = 0
            model.save()
            print(f'[DEBUG] Succesfully saved {model}')
            print('[DEBUG]--------------------------')

            count += 1

    return True
