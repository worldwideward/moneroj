'''Tasks to perform with Celery for updating chart data'''

import datetime
import math
from datetime import date
from datetime import timedelta

from charts.models import Coin
from charts.models import Sfmodel
from charts.models import Social
from charts.models import DailyData
#from charts.asynchronous import update_others_data
from charts.synchronous import update_database
from charts.synchronous import get_history_function

from charts.update_data.utils import erase_sf_model_data
from charts.update_data.utils import erase_daily_data_data
from charts.update_data.stock_to_flow import calculate_sf_model
from charts.update_data.daily_data import calculate_daily_data
from charts.update_data.marketcap import update_rank
from charts.update_data.marketcap import update_dominance


def check_for_updates(yesterday, coin) -> bool:
    '''Check if it is necessary to update XMR data'''

    try:
        coin = Coin.objects.filter(name=coin).get(date=yesterday)

        if coin:
            print(f'[INFO] Data for {coin.name} found', flush=True)
            if coin.priceusd > 1 and coin.transactions > 0 and coin.inflation > 0:
                print(f'[INFO] Data up to date: {coin.priceusd} {coin.name}/USD', flush=True)
            else:
                print(f'[INFO] Updating data for {coin.name}')
                coin.delete()
                return True
        else:
            print(f'[WARN] No data for {coin.name}')
            return True
    except Exception as error:
        print(f'[ERROR] Can not fetch coin data: {error}')
        return True

    return False

def check_monero_available() -> str:
    '''Check if coin data about Monero is present in the database'''

    coins = Coin.objects.filter(name='xmr').order_by('-date')
    count = 0
    for coin in coins:
        count += 1
        if count< 200:
            if coin.supply < 18000000:
                coin.supply += 499736
                print(coin.date)
                coin.save()

    coin = list(Coin.objects.order_by('-date'))[0]

    message = f'[INFO] {coin.name} available'

    if not coin:
        message = f'[INFO ] {coin.name} unavailable'

    return message

def update_xmr_marketcap():
    '''Update XMR dominance & rank from the last day'''

    update_rank('xmr')
    update_dominance('xmr')
    return None

def check_competitors_for_updates(yesterday) -> bool:
    '''Check if it is necessary to update non-XMR coin data'''

    competitors = ["btc", "zec", "dash", "grin"]

    result = False

    for coin in competitors:

        result = check_for_updates(yesterday, coin)

        if result is True:
            print(f'[INFO] Updates available for {coin} - {yesterday}', flush=True)
            result = True

        if result is False:
            print(f'[INFO] Data up to date of {coin} - {yesterday}', flush=True)

    return result


#async def competitors_updates(yesterday):
#    '''Update data from non-XMR coins'''
#
#    await update_others_data(yesterday)

def check_daily_objects_for_updates(yesterday) -> bool:
    '''Check if recent data in the database is present'''

    try:
        data = list(DailyData.objects.filter(date=yesterday))[0]
        if data:
            print(f'[INFO] Data objects up to date. Latest data point at {yesterday}', flush=True)
        else:
            print(f'[WARN] Data objects not found for {yesterday}', flush=True)
            return True
    except Exception as error:
        print(f'[ERROR] No data found: {error}', flush=True)
        return True

    return False

def daily_objects_updates(yesterday):
    '''Update database with recent data'''

    update_database(yesterday, yesterday)

def recalculate_sf_model():
    '''Recalculate Charts based on Stock to Flow model'''

    erase_sf_model_data()
    result = calculate_sf_model()

    if result == True:
        print('[INFO] Recreated Sfmodel database entries')
    else:
        print('[ERROR] Something went wrong during calculation')

def recalculate_daily_data():
    '''Recalculate Charts based on Daily Data '''

    erase_daily_data_data()
    result = calculate_daily_data()

    if result == True:
        print('[INFO] Recreated Daily data database entries')
    else:
        print('[ERROR] Something went wrong during calculation')
