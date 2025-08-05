'''Update data functions'''

import math
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist

from charts.models import Coin
from charts.models import Social
from charts.models import Sfmodel
from charts.models import DailyData

from charts.update_data.utils import calculate_base_reward

def add_stock_to_flow_entry(data_point, amount):

    try:
        model = Sfmodel.objects.get(date=data_point.date)

    except Exception as error:
        print(f'Something went wrong while retrieving Stock to flow entry for {data_point.date}: {error}', flush=True)
        model = Sfmodel()
        model.priceusd = 0
        model.pricebtc = 0
        model.stocktoflow = 0
        model.greyline = 0
        model.color = 0
        model.date = data_point.date

    model.pricebtc = data_point.pricebtc
    model.priceusd = data_point.priceusd

    if model.stocktoflow == 0 and int(data_point.supply) > 0:
        supply = int(data_point.supply)*10**12
        reward = calculate_base_reward(supply)
        inflation = 100*reward*720*365/supply
        model.stocktoflow = (100/(inflation))**1.65

    initial_velocity = 0.002
    velocity_delta = (0.015 - 0.002)/(6*365)

    model.color = 30*int(data_point.pricebtc)/((amount.days)*velocity_delta + initial_velocity)
    model.save()

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

            try:
                coin_date = Coin.objects.filter(name='xmr').get(date=base_date)
            except ObjectDoesNotExist as error:
                coin_date = False
                print(f'[ERROR] No data for date {coin_date}: {error}')

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
