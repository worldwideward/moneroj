'''Tasks to perform with Celery for updating chart data'''

from charts.models import Coin
from charts.models import DailyData
from charts.models import Dread
from charts.synchronous import update_database
from charts.synchronous import get_history_function

from charts.api.tor import DreadSession
from charts.update_data.utils import erase_sf_model_data
from charts.update_data.utils import erase_daily_data_data
from charts.update_data.stock_to_flow import calculate_sf_model
from charts.update_data.daily_data import calculate_daily_data
from charts.update_data.marketcap import update_rank
from charts.update_data.marketcap import update_dominance


def check_for_updates(yesterday, coin) -> bool:
    '''Check if it is necessary to update coin data'''

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

def update_xmr_marketcap():
    '''Update XMR dominance & rank from the last day'''

    update_rank('xmr')
    update_dominance('xmr')

def update_coin_data(symbol, start_time, end_time):
    '''Update coin data from the last day'''

    get_history_function(symbol, start_time, end_time)

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

    if result is True:
        print('[INFO] Recreated Sfmodel database entries')
    else:
        print('[ERROR] Something went wrong during calculation')

def recalculate_daily_data():
    '''Recalculate Charts based on Daily Data '''

    erase_daily_data_data()
    result = calculate_daily_data()

    if result is True:
        print('[INFO] Recreated Daily data database entries')
    else:
        print('[ERROR] Something went wrong during calculation')

def update_dread_subscriber_count(today):

    session = DreadSession()

    btc_subscribers = session.get_dread_subscriber_count("btc")

    if btc_subscribers is None:
        btc_subscribers = 0

    xmr_subscribers = session.get_dread_subscriber_count("xmr")

    if xmr_subscribers is None:
        xmr_subscribers = 0

    entry = Dread()

    entry.date = today
    entry.bitcoin_subscriber_count = btc_subscribers
    entry.monero_subscriber_count = xmr_subscribers
    entry.save()

    return True
