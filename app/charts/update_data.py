'''Update data functions'''

import math
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist

from .models import Coin
from .models import Social
from .models import Sfmodel
from .models import DailyData

def erase_coin_data(symbol):
    '''Erase all data for a certain coin'''

    try:
        Coin.objects.filter(name=symbol).all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase data for {symbol}: {error}')
        return False

    return True

def erase_sf_model_data():
    '''Erase all data for the sf model object'''

    try:
        Sfmodel.objects.all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase Sfmodel data: {error}')
        return False

    return True

def erase_daily_data_data():
    '''Erase all data for the daily data object'''

    try:
        DailyData.objects.all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase Sfmodel data: {error}')
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

def calculate_sf_model():
    '''Reset and recalculate the Stock-to-Flow model'''

    objects = Sfmodel.objects.count()

    if objects > 0:
        print(f'[ERROR] Sf Model data already present, erase all data before proceeding.')
        return False

    previous_supply = 0
    current_supply = 0
    calculate_days_in_the_future = 90
    previous_stocktoflow_ratio = 0

    count = 0
    greyline_count = 0

    coin_data = Coin.objects.order_by('date').filter(name='xmr')

    total_data_points = len(coin_data)
    print(f'[DEBUG] XMR data points: {len(coin_data)}')

    if total_data_points == 0:

        print('[INFO] No coin data found for XMR')
        return False

    for data_point in coin_data:

        # Determine the current supply

        if data_point.supply > 0:
            current_supply = int(data_point.supply) * 10 ** 12
            previous_supply = current_supply
        else:
            current_supply = previous_supply

        # Initialize XMR Price

        if data_point.priceusd < 0.1:
            data_point.priceusd = 0.1
            data_point.pricebtc = 0.000001

        sf_calculation = previous_stocktoflow_ratio * 1.3 + 100

        if data_point.stocktoflow > sf_calculation:
            data_point.stocktoflow = previous_stocktoflow_ratio

        previous_stocktoflow_ratio = data_point.stocktoflow

        count += 1
        greyline_count += 1

        # Calculate annual stock flow

        significant_date = '2017-12-29'

        reference_date = datetime.strptime(significant_date, '%Y-%m-%d')
        data_point_date = datetime.strptime(str(data_point.date), '%Y-%m-%d')

        if data_point_date < reference_date:

            lastprice = data_point.priceusd
            current_inflation = data_point.inflation
            greyline = 0
            greyline_count = 0
        else:
            time_interval_days = 1283

            # Format date
            base_date = data_point_date - timedelta(time_interval_days)
            coin_date = Coin.objects.filter(name='xmr').get(date=base_date)

            base_date_plus_one = data_point_date - timedelta(time_interval_days+1)

            try:
                coin_date_plus_one = Coin.objects.filter(name='xmr').get(date=base_date_plus_one)
            except ObjectDoesNotExist as error:
                coin_date_plus_one = False
                print(f'[ERROR] No data for date {base_date_plus_one}: {error}')

            significant_date = datetime.strptime(significant_date, '%Y-%m-%d')

            if significant_date + timedelta(int(greyline_count*2)) < datetime.strptime('2021-07-03', '%Y-%m-%d'):

                significant_base_date = significant_date + timedelta(int(greyline_count*2))
                try:
                    significant_coin_date = Coin.objects.filter(name='xmr').get(date=significant_base_date)
                except ObjectDoesNotExist as error:
                    significant_coin_date = False
                    print(f'[ERROR] No data for date {significant_base_date}: {error}')

                if significant_coin_date:
                    if (significant_coin_date.inflation/current_inflation) > 1.2 or (significant_coin_date.inflation/current_inflation) < 0.8:
                        significant_coin_date.inflation = current_inflation
                    else:
                        current_inflation = significant_coin_date.inflation
                        coins_in_circulation = current_supply

                    coins_in_circulation = current_supply
                else:
                    block_reward = calculate_base_reward(current_supply)
                    coins_in_circulation = int(720*block_reward)
                    current_inflation = 100*block_reward*720*365/coins_in_circulation

            if coin_date and coin_date_plus_one:
                lastprice += (coin_date.priceusd/coin_date_plus_one.priceusd-1)*lastprice
                actualprice = lastprice*(math.sqrt(data_point.inflation/current_inflation))
                greyline = actualprice
            else:
                greyline = 0

        # Create the entry in the database

        velocity_delta = (0.015 - 0.002)/(6*365)
        initial_velocity = 0.002

        model = Sfmodel()
        model.date = data_point.date
        model.priceusd = data_point.priceusd
        model.pricebtc = data_point.pricebtc
        model.stocktoflow = data_point.stocktoflow
        model.greyline = greyline
        model.color = 30 * data_point.pricebtc / (count * velocity_delta + initial_velocity)
        model.save()

    # Calculate Stocktoflow X days in the future

    greyline_count = 0
    for greyline_count in range(calculate_days_in_the_future):

        future_date = date.today() + timedelta(greyline_count)
        block_reward = calculate_base_reward(current_supply)
        current_supply += int(720*block_reward)

        # Create the entry in the database
        model = Sfmodel()
        model.date = datetime.strftime(future_date, '%Y-%m-%d')
        model.stocktoflow = (100/(100*block_reward*720*365/current_supply))**1.65
        model.priceusd = 0
        model.pricebtc = 0
        model.greyline = 0
        model.color = 0
        model.priceusd = 0
        model.greyline = 0
        model.save()

        count += 1

    return True

def calculate_daily_data():
    '''Reset and recalculate the Daily Data model'''

    objects = DailyData.objects.count()

    if objects > 0:
        print(f'[ERROR] Daily data already present, erase all data before proceeding.')
        return False

    supply_btc = 0
    supply_xmr = 0
    count = 0
    count_aux = 0
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    for coin_btc in coins_btc:
        count_aux += 1
        data = DailyData()
        data.date = datetime.strftime(coin_btc.date, '%Y-%m-%d')

        if coin_btc.blocksize > 0:
            data.btc_blocksize = coin_btc.blocksize
            data.btc_transactions = coin_btc.transactions
        else:
            data.btc_blocksize = 0
            data.btc_transactions = 0

        if coin_btc.difficulty > 0:
            data.btc_difficulty = coin_btc.difficulty
        else:
            data.btc_difficulty = 0

        if coin_btc.transactions == 0:
            data.btc_transcostusd = 0
            data.btc_transcostntv = 0
        else:
            if coin_btc.fee*coin_btc.priceusd/coin_btc.transactions < 0.0001:
                data.btc_transcostusd = 0
                data.btc_transcostntv = 0
            else:
                data.btc_transcostusd = coin_btc.fee*coin_btc.priceusd/coin_btc.transactions
                data.btc_transcostntv = coin_btc.fee/coin_btc.transactions

        if coin_btc.revenue < 0.000001 or coin_btc.priceusd < 0.001:
            data.btc_minerrevntv = 0
            data.btc_minerrevusd = 0
            data.btc_commitntv = 0
            data.btc_commitusd = 0
            data.btc_priceusd = 0
            data.btc_marketcap = 0
        else:
            data.btc_minerrevntv = coin_btc.revenue
            data.btc_minerrevusd = coin_btc.revenue*coin_btc.priceusd
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.btc_priceusd = coin_btc.priceusd
            data.btc_marketcap = coin_btc.priceusd*coin_btc.supply

        if coin_btc.supply == 0:
            data.btc_minerrevcap = 0
        else:
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply

        if coin_btc.priceusd:
            if coin_btc.priceusd/30 > 0.02:
                data.btc_return = coin_btc.priceusd/30
            else:
                data.btc_return = 0
        else:
            data.btc_return = 0

        if coin_btc.inflation > 0:
            data.btc_inflation = coin_btc.inflation
        else:
            data.btc_inflation = 0
        if coin_btc.supply > 0:
            data.btc_supply = coin_btc.supply
        else:
            data.btc_supply = 0

        if coin_btc.supply - supply_btc < 0.000001:
            data.btc_minerfeesntv = 0
            data.btc_minerfeesusd = 0
            data.btc_emissionntv = 0
        else:
            data.btc_minerfeesntv = coin_btc.revenue - coin_btc.supply + supply_btc
            data.btc_minerfeesusd = (coin_btc.revenue - coin_btc.supply + supply_btc)*coin_btc.priceusd
            data.btc_emissionntv = coin_btc.supply -  supply_btc

        if (coin_btc.supply - supply_btc)*coin_btc.priceusd < 1000:
            data.btc_emissionusd = 0
        else:
            data.btc_emissionusd = (coin_btc.supply - supply_btc)*coin_btc.priceusd
        supply_btc = coin_btc.supply

        if count_aux > 1750:
            coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
            if coins_xmr:
                for coin_xmr in coins_xmr:
                    if coin_xmr.blocksize > 0:
                        data.xmr_blocksize = coin_xmr.blocksize
                    else:
                        data.xmr_blocksize = 0

                    if coin_xmr.difficulty > 0:
                        data.xmr_difficulty = coin_xmr.difficulty
                    else:
                        data.xmr_difficulty = 0

                    if coin_xmr.priceusd < 0.001:
                        data.xmr_pricebtc = 0
                        data.xmr_priceusd = 0
                        data.xmr_marketcap = 0
                    else:
                        data.xmr_pricebtc = coin_xmr.pricebtc
                        data.xmr_priceusd = coin_xmr.priceusd
                        data.xmr_marketcap = coin_xmr.priceusd*coin_xmr.supply

                    if coin_btc.supply > 0 and coin_btc.transactions > 0:
                        data.xmr_transactions = coin_xmr.transactions
                        data.xmr_metcalfeusd = coin_btc.priceusd*coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                        data.xmr_metcalfebtc = coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                    else:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0
                        data.xmr_transactions = 0
                    if data.xmr_metcalfeusd < 0.23:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0

                    if coin_xmr.transactions == 0:
                        data.xmr_transacpercentage = 0
                        data.xmr_transcostusd = 0
                        data.xmr_transcostntv = 0
                    else:
                        if coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions < 0.0001:
                            data.xmr_transcostusd = 0
                            data.xmr_transcostntv = 0
                        else:
                            data.xmr_transcostusd = coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions
                            data.xmr_transcostntv = coin_xmr.fee/coin_xmr.transactions
                        if coin_btc.transactions == 0:
                            data.xmr_transacpercentage = 0
                        else:
                            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions

                    if coin_xmr.revenue < 0.000001 or coin_xmr.priceusd < 0.001:
                        data.xmr_minerrevntv = 0
                        data.xmr_minerrevusd = 0
                        data.xmr_commitntv = 0
                        data.xmr_commitusd = 0
                    else:
                        data.xmr_minerrevntv = coin_xmr.revenue
                        data.xmr_minerrevusd = coin_xmr.revenue*coin_xmr.priceusd
                        data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
                        data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)

                    if coin_xmr.supply == 0:
                        data.xmr_minerrevcap = 0
                    else:
                        data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply

                    if coin_xmr.priceusd/5.01 > 0.02:
                        data.xmr_return = coin_xmr.priceusd/5.01
                    else:
                        data.xmr_return = 0
                    if coin_xmr.inflation > 0:
                        data.xmr_inflation = coin_xmr.inflation
                    else:
                        data.xmr_inflation = 0

                    if coin_xmr.supply > 0:
                        data.xmr_supply = coin_xmr.supply
                    else:
                        data.xmr_supply = 0

                    if coin_xmr.supply - supply_xmr < 0.000001:
                        data.xmr_minerfeesntv = 0
                        data.xmr_minerfeesusd = 0
                        data.xmr_emissionntv = 0
                    else:
                        data.xmr_minerfeesntv = coin_xmr.revenue - coin_xmr.supply + supply_xmr
                        data.xmr_minerfeesusd = (coin_xmr.revenue - coin_xmr.supply + supply_xmr)*coin_xmr.priceusd
                        data.xmr_emissionntv = coin_xmr.supply - supply_xmr

                    if (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd < 1000:
                        data.xmr_emissionusd = 0
                    else:
                        data.xmr_emissionusd = (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd
                    supply_xmr = coin_xmr.supply
            else:
                data.xmr_emissionntv = 0
                data.xmr_emissionusd = 0
                data.xmr_inflation = 0
                data.xmr_supply = 0
                data.xmr_return = 0
                data.xmr_minerrevntv = 0
                data.xmr_minerrevusd = 0
                data.xmr_minerfeesntv = 0
                data.xmr_minerfeesusd = 0
                data.xmr_transcostntv = 0
                data.xmr_transcostusd = 0
                data.xmr_commitntv = 0
                data.xmr_commitusd = 0
                data.xmr_metcalfeusd = 0
                data.xmr_metcalfebtc = 0
                data.xmr_pricebtc = 0
                data.xmr_priceusd = 0
                data.xmr_transacpercentage = 0
                data.xmr_marketcap = 0
                data.xmr_minerrevcap = 0
                data.xmr_transactions = 0
                data.xmr_blocksize = 0
                data.xmr_difficulty = 0

            coins_dash = Coin.objects.filter(name='dash').filter(date=coin_btc.date)
            if coins_dash:
                for coin_dash in coins_dash:
                    if coin_dash.transactions > 0:
                        data.dash_transactions = coin_dash.transactions
                    else:
                        data.dash_transactions = 0
                    if coin_dash.inflation > 0:
                        data.dash_inflation = coin_dash.inflation
                    else:
                        data.dash_inflation = 0

                    if coin_dash.priceusd > 0:
                        data.dash_marketcap = coin_dash.priceusd*coin_dash.supply
                    else:
                        data.dash_marketcap = 0
            else:
                data.dash_inflation = 0
                data.dash_marketcap = 0
                data.dash_transactions = 0
        else:
            data.xmr_emissionntv = 0
            data.xmr_emissionusd = 0
            data.xmr_inflation = 0
            data.xmr_supply = 0
            data.xmr_return = 0
            data.dash_inflation = 0
            data.dash_marketcap = 0
            data.dash_transactions = 0
            data.xmr_marketcap = 0
            data.xmr_minerrevntv = 0
            data.xmr_minerrevusd = 0
            data.xmr_minerfeesntv = 0
            data.xmr_minerfeesusd = 0
            data.xmr_transcostntv = 0
            data.xmr_transcostusd = 0
            data.xmr_commitntv = 0
            data.xmr_commitusd = 0
            data.xmr_metcalfeusd = 0
            data.xmr_metcalfebtc = 0
            data.xmr_pricebtc = 0
            data.xmr_priceusd = 0
            data.xmr_transacpercentage = 0
            data.xmr_minerrevcap = 0
            data.xmr_transactions = 0
            data.xmr_blocksize = 0
            data.xmr_difficulty = 0

        if count_aux > 2800:
            coins_zcash = Coin.objects.filter(name='zec').filter(date=coin_btc.date)
            if coins_zcash:
                for coin_zcash in coins_zcash:
                    if coin_zcash.transactions > 0:
                        data.zcash_transactions = coin_zcash.transactions
                    else:
                        data.zcash_transactions = 0
                    if coin_zcash.inflation > 0:
                        data.zcash_inflation = coin_zcash.inflation
                    else:
                        data.zcash_inflation = 0

                    if coin_zcash.priceusd > 0:
                        data.zcash_marketcap = coin_zcash.priceusd*coin_zcash.supply
                    else:
                        data.zcash_marketcap = 0
            else:
                data.zcash_inflation = 0
                data.zcash_marketcap = 0
                data.zcash_transactions = 0
        else:
            data.zcash_inflation = 0
            data.zcash_marketcap = 0
            data.zcash_transactions = 0

        if count_aux > 3600:
            coins_grin = Coin.objects.filter(name='grin').filter(date=coin_btc.date)
            if coins_grin:
                for coin_grin in coins_grin:
                    if coin_grin.transactions > 0:
                        data.grin_transactions = coin_grin.transactions
                    else:
                        data.grin_transactions = 0
                    if coin_grin.inflation > 0:
                        data.grin_inflation = coin_grin.inflation
                    else:
                        data.grin_inflation = 0

                    if coin_grin.priceusd > 0:
                        data.grin_marketcap = coin_grin.priceusd*coin_grin.supply
                    else:
                        data.grin_marketcap = 0
            else:
                data.grin_inflation = 0
                data.grin_marketcap = 0
                data.grin_transactions = 0
        else:
            data.grin_inflation = 0
            data.grin_marketcap = 0
            data.grin_transactions = 0

        socials = Social.objects.filter(name='Bitcoin').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.btc_subscriber_count = social.subscriber_count
                data.btc_comments_per_hour = social.comments_per_hour
                data.btc_posts_per_hour = social.posts_per_hour
        else:
            data.btc_subscriber_count = 0
            data.btc_comments_per_hour = 0
            data.btc_posts_per_hour = 0

        socials = Social.objects.filter(name='Monero').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.xmr_subscriber_count = social.subscriber_count
                data.xmr_comments_per_hour = social.comments_per_hour
                data.xmr_posts_per_hour = social.posts_per_hour
        else:
            data.xmr_subscriber_count = 0
            data.xmr_comments_per_hour = 0
            data.xmr_posts_per_hour = 0

        socials = Social.objects.filter(name='CryptoCurrency').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.crypto_subscriber_count = social.subscriber_count
                data.crypto_comments_per_hour = social.comments_per_hour
                data.crypto_posts_per_hour = social.posts_per_hour
        else:
            data.crypto_subscriber_count = 0
            data.crypto_comments_per_hour = 0
            data.crypto_posts_per_hour = 0

        data.save()
        count += 1

    return True
