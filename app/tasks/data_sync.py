'''Tasks to perform with Celery for updating chart data'''

from charts.models import Coin
from charts.models import DailyData
from charts.synchronous import update_database
from charts.synchronous import get_history_function

from charts.update_data.utils import erase_sf_model_data
from charts.update_data.utils import erase_daily_data_data
from charts.update_data.stock_to_flow import calculate_sf_model
from charts.update_data.daily_data import calculate_daily_data
from charts.update_data.marketcap import update_rank
from charts.update_data.marketcap import update_dominance
from charts.update_data.social import add_socials_entry
from charts.update_data.subscribers import add_dread_entry
from charts.update_data.p2pool import add_p2pool_entry
from charts.update_data.transactions import add_transactions_entry
from charts.update_data.merchants import add_merchants_entry
from charts.update_data.volume import add_volume_entry


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

def update_p2pool_data():

    add_p2pool_entry(mini=False)
    add_p2pool_entry(mini=True)

def update_reddit_data():

    add_socials_entry("Monero")
    add_socials_entry("Bitcoin")
    add_socials_entry("CryptoCurrency")

def update_dread_subscriber_count(today):

    add_dread_entry(today)

def update_shielded_transactions():

    add_transactions_entry()

def update_merchants_data():

    add_merchants_entry()

def update_dex_volume():

    add_volume_entry()
