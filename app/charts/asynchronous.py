import os
import aiohttp
import asyncio
import json
import datetime
import requests
from datetime import date, timedelta
from django.conf import settings

from .models import Coin, Social

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
