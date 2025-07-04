'''Update P2Pool data'''

from datetime import date
from datetime import timedelta

from charts.api.p2pool import P2PoolAPI
from charts.models import P2Pool
from charts.models import Coin

POOL_API = P2PoolAPI()

def calculate_pool_percentage(hashrate, date):

    try:
        entry = Coin.objects.filter(name='xmr').get(date=date)

        percentage = 100 * hashrate / entry.hashrate
        print(f'[INFO] No XMR pool percentage is {percentage}')

    except Coin.DoesNotExist:
        print(f'[ERROR] No XMR data for date {date}, setting percentage to 0')
        percentage = 0

    return percentage

def add_p2pool_entry(mini=bool):
    '''Create P2Pool entry in the database'''

    today = date.today()
    yesterday = today - timedelta(1)

    try:
        entry = P2Pool.objects.filter(mini=mini).get(date=today)
        print(f'[INFO] Found P2Pool entry {entry} for date {today}')
        return False

    except P2Pool.DoesNotExist:
        print(f'[INFO] No P2Pool entry for date {today}')

    if mini == True:
        data = POOL_API.get_json_data(mini=True)
    if mini == False:
        data = POOL_API.get_json_data(mini=False)

    pool_percentage = calculate_pool_percentage(data['pool_statistics']['hashRate'], yesterday)

    entry = P2Pool()

    entry.date = today
    entry.mini = mini
    entry.hashrate = data['pool_statistics']['hashRate']
    entry.percentage = pool_percentage
    entry.miners = data['pool_statistics']['miners']
    entry.totalhashes = data['pool_statistics']['totalHashes']
    entry.totalblocksfound = data['pool_statistics']['totalBlocksFound']
    entry.save()

    print(f'[INFO] Successfully added new P2Pool entry at {today}')

    return True
