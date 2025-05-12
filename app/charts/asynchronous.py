import os
import aiohttp
import asyncio
import json
import datetime
import requests
from datetime import date, timedelta
from django.conf import settings

from .models import Coin, Social, P2Pool
from .synchronous import *
from .synchronous import update_rank
from .synchronous import update_dominance
from .spreadsheets import PandasSpreadSheetManager
from .utils import get_today, get_yesterday
from .utils import get_socks_proxy

BASE_DIR = settings.BASE_DIR

sheets = PandasSpreadSheetManager()

LOCAL_MONERO_API = "https://localmonero.co/blocks/api"
XMR_BLOCKCHAIN_EXPLORER_API = settings.XMR_BLOCKCHAIN_EXPLORER_API
METRICS_API = settings.METRICS_API

MARKET_DATA_API = settings.MARKET_DATA_API
MARKET_DATA_API_KEY = settings.MARKET_DATA_API_KEY

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

def get_coin_id(symbol: str):

    if symbol == 'xmr':
        coin_id = "monero"
    elif symbol == 'btc':
        coin_id = "bitcoin"
    elif symbol == 'zec':
        coin_id = "zcash"
    elif symbol == 'dash':
        coin_id = 'dash'
    elif symbol == 'grin':
        coin_id = 'grin'
    else:
        return None

    return coin_id

####################################################################################
#   Asynchronous get block data from xmrchain
#################################################################################### 
async def get_block_data(session, block: str):
    url = f'{LOCAL_MONERO_API}/get_block_data/{block}'

    async with session.get(url) as res:
        data = await res.read()
        data = json.loads(data)
        data['provider'] = 'localmonero'
        if res.status < 299:
            data['success'] = True
        else:
            data['success'] = False
        return data

####################################################################################
#   Asynchronous get network data from xmrchain
#################################################################################### 
async def get_network_data(session, block: str):
    url = f'{XMR_BLOCKCHAIN_EXPLORER_API}/networkinfo'
    async with session.get(url) as res:
        data = await res.read()
        data = json.loads(data)
        data['provider'] = 'xmrchain'
        if res.status < 299:
            data['success'] = True
        else:
            data['success'] = False
        return data

####################################################################################
#   Asynchronous get coinmarketcap data for price USD and BTC
#################################################################################### 
async def get_coin_rank_data(session, symbol: str):
    '''Get the current rank of a cryptocurrency coin'''

    coin_id = get_coin_id(symbol)

    url = f'{MARKET_DATA_API}/coins/{coin_id}'

    headers = {
            "Content-Type": "application/json",
            "x-cg-demo-api-key": MARKET_DATA_API_KEY
            }

    params = {
            "localization": "false",
            "ticker": "false",
            "market_data": "false",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
            }

    async with session.get(url, headers=headers, params=params) as response:

        data = await response.read()
        json_data = json.loads(data)

        if response.status == 200:
            rank = json_data["market_cap_rank"]

        if response.status != 200:
            return None

    return rank

async def get_coin_dominance_data(session, symbol: str):
    '''Get the current dominance of a cryptocurrency coin'''

    coin_id = get_coin_id(symbol)

    url = f'{MARKET_DATA_API}/coins/{coin_id}'

    headers = {
            "Content-Type": "application/json",
            "x-cg-demo-api-key": MARKET_DATA_API_KEY
            }

    params = {
            "localization": "false",
            "ticker": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
            }

    async with session.get(url, headers=headers, params=params) as response:

        data = await response.read()
        json_data = json.loads(data)

        if response.status == 200:
            coin_market_cap = json_data["market_data"]["market_cap"]["usd"]

        if response.status != 200:
            return None

    url = f'{MARKET_DATA_API}/global'

    async with session.get(url, headers=headers) as response:

        data = await response.read()
        json_data = json.loads(data)

        if response.status == 200:
            total_market_cap = json_data["data"]["total_market_cap"]["usd"]

        if response.status != 200:
            return None

    dominance = round(( coin_market_cap / total_market_cap ) * 100, 2)

    return dominance

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
    yesterday = yesterday()
    try:
        social = Social.objects.filter(name=symbol).get(date=yesterday)
    except:

        session = requests.session()

        url = f'{settings.REDDIT_API_URL}/r/{symbol}/about.json'

        if settings.SOCKS_PROXY_ENABLED is True:

            session.proxies = get_socks_proxy()

        with session.get(url, headers={'User-agent': 'Checking new social data'}) as res:
            data = res.content
            data = json.loads(data)
            data = data['data']

            social = Social()
            social.name = symbol
            social.date = yesterday
            social.subscriber_count = data['subscribers']

            timestamp1 = int(datetime.datetime.timestamp(datetime.datetime.strptime(yesterday, '%Y-%m-%d')))
            timestamp2 = int(timestamp1 - 7200)
            limit = 1000
            filters = []
            data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
            social.posts_per_hour = len(data)/2
            data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
            social.comments_per_hour = len(data)/2
            social.save()
    return True

####################################################################################
#   Asynchronous get whole xmr data calling coinmarketcap and xmrchain
#################################################################################### 
async def update_xmr_data():

    symbol = 'xmr'

    async with aiohttp.ClientSession(**ASYNC_CLIENT_ARGS) as session:

        rank = await get_coin_rank_data(session, symbol)

    result = update_rank(symbol, rank)

    if result != 0:
        return False

    async with aiohttp.ClientSession(**ASYNC_CLIENT_ARGS) as session:

        dominance = await get_coin_dominance_data(session, symbol)

    result = update_dominance(symbol, dominance)

    if result != 0:
        return False

    print('[INFO] Updated XMR')
    print(f'[INFO] XMR rank: {rank}')
    print(f'[INFO] XMR dominance: {dominance}')

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
