import os
import aiohttp
import asyncio
import json
import datetime
import requests
from datetime import date, timedelta
from django.conf import settings

from .models import Coin, Social, P2Pool

from .spreadsheets import PandasSpreadSheetManager
from .utils import get_today, get_yesterday
from .utils import get_socks_proxy

from .api.coinmetrics import CoinmetricsAPI
from .api.localmonero import LocalMoneroAPI
from .api.coingecko import CoingeckoAPI
from .api.reddit import RedditAPI

BASE_DIR = settings.BASE_DIR

sheets = PandasSpreadSheetManager()

LOCAL_MONERO_API = LocalMoneroAPI()
MARKET_DATA_API = CoingeckoAPI()
REDDIT_API = RedditAPI()

# Async client configuration
ASYNC_TIMEOUT = aiohttp.ClientTimeout(
    total=10,
    sock_connect=10,
    sock_read=10
    )

ASYNC_CLIENT_ARGS = dict(
    trust_env=True,
    timeout=ASYNC_TIMEOUT
    )

####################################################################################
#   Get block data from localmonero.co
#################################################################################### 
async def get_block_data(session, block: str):

    data = LOCAL_MONERO_API.get_block_data(block)
    return data

####################################################################################
#   Get network data from xmrchain
#################################################################################### 
async def get_network_data(session, block: str):
    url = f'https://xmrchain.net/api/networkinfo'

    response = requests.get(url)

    if response.status_code == 200:

        json_data = json.loads(response.text)
        return json_data

    else:
        raise Exception(f'[ERROR] API returned status: {response.status_code}')


####################################################################################
#   Asynchronous get coinmetrics data for any coin inside URL
#################################################################################### 
async def get_coin_data(session, symbol, url):
    update = True
    count = 0

    while update:
        async with session.get(url) as res:
            data = await res.read()
            data = json.loads(data)
            data_aux = data['data']
            for item in data_aux:
                day, hour = str(item['time']).split('T')
                day = datetime.datetime.strptime(day, '%Y-%m-%d')
                day = datetime.datetime.strftime(day, '%Y-%m-%d')
                try:
                    coin = Coin.objects.filter(name=symbol).get(date=day)
                except:
                    coin = Coin()

                try:
                    coin.name = symbol
                    coin.date = day
                    try:
                        coin.priceusd = float(item['PriceUSD'])
                    except:
                        coin.priceusd = 0
                    try:
                        coin.pricebtc = float(item['PriceBTC'])
                    except:
                        coin.pricebtc = 0
                    try:
                        coin.inflation = float(item['IssContPctAnn'])
                        coin.stocktoflow = (100/coin.inflation)**1.65
                    except:
                        coin.inflation = 0
                        coin.stocktoflow = 0
                    try:
                        coin.supply = float(item['SplyCur'])
                    except:
                        coin.supply = 0
                    try:
                        coin.fee = float(item['FeeTotNtv'])
                    except:
                        coin.fee = 0
                    try:
                        coin.revenue = float(item['RevNtv'])
                    except:
                        coin.revenue = 0
                    try:
                        coin.hashrate = float(item['HashRate'])
                    except:
                        coin.hashrate = 0
                    try:
                        coin.transactions = float(item['TxCnt'])
                    except:
                        coin.transactions = 0
                    coin.save()
                    count += 1
                except:
                    pass
            try:
                url = data['next_page_url']
                update = True
            except:
                update = False
                break
    return count

####################################################################################
#   Asynchronous get social metrics from reddit
#################################################################################### 

def get_social_data(symbol):
    yesterday = get_yesterday()

    try:
        social = Social.objects.filter(name=symbol).get(date=yesterday)
        print(f'[INFO] Social data already present in database: {social}')
    except:

        data = REDDIT_API.get_subreddit_metadata(symbol)

        # calculate comments and posts / hour
        end_time = int(datetime.datetime.timestamp(datetime.datetime.strptime(yesterday, '%Y-%m-%d')))
        start_time = int(end_time - 7200)
        limit = 1000
        filters = []

        posts = REDDIT_API.get_subreddit_posts(symbol)
        comments = REDDIT_API.get_subreddit_comments(symbol)

        #posts = data_prep_posts(symbol, start_time, end_time, filters, limit)
        #comments = data_prep_comments(symbol, start_time, end_time, filters, limit)

        model = Social()
        model.name = symbol
        model.date = yesterday
        model.subscriber_count = data['subscribers']
        model.posts_per_hour = len(posts)/2
        model.comments_per_hour = len(comments)/2

        model.save()
        print(f'[INFO] Added Social data to database: {model}')
    return True

####################################################################################
#   Asynchronous get social and coins data
#################################################################################### 
async def update_coin_data(coin, date):

    url = f'http://162.210.173.181/coinmetrics/{coin}/{date}'

    async with aiohttp.ClientSession(**ASYNC_CLIENT_ARGS) as session:

        asyncio.ensure_future(get_coin_data(session, coin, url))

        #actions.append(asyncio.ensure_future(get_p2pool_data(session, mini=False)))
        #actions.append(asyncio.ensure_future(get_p2pool_data(session, mini=True)))

    return True

####################################################################################
#   Asynchronous get social and coins data
#################################################################################### 
async def update_social_data(symbol):

    actions = []

    async with aiohttp.ClientSession(**ASYNC_CLIENT_ARGS) as session:
        # reddit data
        actions.append(asyncio.ensure_future(get_social_data(session, 'Monero')))
        actions.append(asyncio.ensure_future(get_social_data(session, 'Bitcoin')))
        actions.append(asyncio.ensure_future(get_social_data(session, 'Cryptocurrency')))

        try:
            await asyncio.gather(*actions, return_exceptions=True)
        except asyncio.exceptions.TimeoutError:
            print('Timeout!')

    return True

####################################################################################
#   Asynchronous get p2pool and p2poolmini data and then save to google sheets
#################################################################################### 
async def get_p2pool_data(session, mini):
    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=mini).get(date=today)
        if p2pool_stat.percentage > 0:
            update  = False
        else:
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)
                if coin.hashrate > 0:
                    update = True
                else:
                    update  = False
            except:
                update  = False
    except:
        try:
            coin = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin.hashrate > 0:
                update = True
            else:
                update  = False
        except:
            update  = False

    if update:
        p2pool_stat = P2Pool()
        p2pool_stat.date = today

        if not(mini):
            async with session.get('https://p2pool.io/api/pool/stats') as res:
                data = await res.read()
                data = json.loads(data) 
                p2pool_stat.hashrate = data['pool_statistics']['hashRate']
                p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
                p2pool_stat.miners = data['pool_statistics']['miners']
                p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
                p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
                p2pool_stat.mini = False
                p2pool_stat.save()
                print('p2pool saved!')
                values_mat = sheets.get_values("zcash_bitcoin.ods", "p2pool", start=(2,0), end=(9999,3))
                k = len(values_mat)
                date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
                date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
                date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
                if date_aux < date_aux2:
                    cell = 'F' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.totalblocksfound)
                    cell = 'E' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.totalhashes)
                    cell = 'D' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.percentage)
                    cell = 'C' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.hashrate)
                    cell = 'B' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.miners)
                    cell = 'A' + str(k + 3)
                    wks.update_value(cell, datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))
                    print('spreadsheet updated')
                else:   
                    print('spreadsheet already with the latest data')
                    return data
        else:
            async with session.get('https://p2pool.io/mini/api/pool/stats') as res:
                data = await res.read()
                data = json.loads(data) 
                p2pool_stat.hashrate = data['pool_statistics']['hashRate']
                p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
                p2pool_stat.miners = data['pool_statistics']['miners']
                p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
                p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
                p2pool_stat.mini = True
                p2pool_stat.save()
                print('p2pool_mini saved!')
                values_mat = sheets.get_values("zcash_bitcoin.ods", "p2poolmini", start=(2,0), end=(9999,3))
                k = len(values_mat)
                date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
                date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
                date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
                if date_aux < date_aux2:
                    cell = 'F' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.totalblocksfound)
                    cell = 'E' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.totalhashes)
                    cell = 'D' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.percentage)
                    cell = 'C' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.hashrate)
                    cell = 'B' + str(k + 3)
                    wks.update_value(cell, p2pool_stat.miners)
                    cell = 'A' + str(k + 3)
                    wks.update_value(cell, datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))
                    print('spreadsheet updated')
                else:
                    print('spreadsheet already with the latest data')
                    return data
    else:
        return False
    return True
