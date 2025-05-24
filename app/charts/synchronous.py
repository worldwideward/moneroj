'''Synchronous functions'''

import json
import datetime
from datetime import date, timedelta
import requests

from requests import Session
from requests.exceptions import Timeout, TooManyRedirects

from django.conf import settings

from charts.models import Coin
from charts.models import P2Pool
from charts.models import Social

from charts.update_data.stock_to_flow import add_stock_to_flow_entry

from charts.update_data.daily_data import update_daily_data_price_information
from charts.update_data.daily_data import update_daily_data_marketcap
from charts.update_data.daily_data import update_daily_data_transactions
from charts.update_data.daily_data import update_daily_data_issuance
from charts.update_data.daily_data import update_daily_data_emission
#from charts.update_data.daily_data import update_daily_data_mining
from charts.update_data.daily_data import update_daily_data_social

from .spreadsheets import PandasSpreadSheetManager
from .api.coinmetrics import CoinmetricsAPI

SHEETS = PandasSpreadSheetManager()
METRICS_API = CoinmetricsAPI()

CSV_DATA_SHEET = settings.CSV_DATA_SHEET


####################################################################################
#   Other useful functions
####################################################################################

def get_history_function(symbol, start_time=None, end_time=None):
    '''Get historic data from a cryptocurrency coin'''

    count = 0
    priceusd = 0
    inflation = 0
    pricebtc = 0
    stocktoflow = 0
    supply = 0
    fee = 0
    revenue = 0
    hashrate = 0
    transactions = 0
    blocksize = 0
    difficulty = 0

    coins = Coin.objects.filter(name=symbol).order_by('-date')
    for coin in coins:
        if coin.supply > 0:
            supply = coin.supply
            break
    for coin in coins:
        if coin.inflation > 0:
            inflation = coin.inflation
            break
    for coin in coins:
        if coin.hashrate > 0:
            hashrate = coin.hashrate
            break
    for coin in coins:
        if coin.transactions > 0:
            transactions = coin.transactions
            break
    for coin in coins:
        if coin.priceusd > 0:
            priceusd = coin.priceusd
            break

    metrics = METRICS_API.get_asset_metrics(symbol, start_time, end_time)

    for item in metrics:

        time_array = str(item['time']).split('T')
        day = datetime.datetime.strptime(time_array[0], '%Y-%m-%d')
        day = datetime.datetime.strftime(day, '%Y-%m-%d')
        coin = Coin.objects.filter(name=symbol).filter(date=day)
        if coin:
            coin.delete()
        try:
            coin = Coin()
            coin.name = symbol
            coin.date = day
            try:
                coin.priceusd = float(item['PriceUSD'])
                priceusd = coin.priceusd
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.priceusd = priceusd
            try:
                coin.pricebtc = float(item['PriceBTC'])
                pricebtc = coin.pricebtc
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.pricebtc = pricebtc
            try:
                coin.inflation = float(item['IssContPctAnn'])
                coin.stocktoflow = (100/coin.inflation)**1.65
                inflation = coin.inflation
                stocktoflow = coin.stocktoflow
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.inflation = inflation
                coin.stocktoflow = stocktoflow
            try:
                if symbol == 'xmr':
                    if float(item['SplyCur']) < 18000000:
                        coin.supply = float(item['SplyCur']) + 497108
                    else:
                        coin.supply = float(item['SplyCur'])
                    supply = coin.supply
                else:
                    coin.supply = float(item['SplyCur'])
                    supply = coin.supply
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.supply = supply
            try:
                coin.fee = float(item['FeeTotNtv'])
                fee = coin.fee
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.fee = fee
            try:
                coin.revenue = float(item['RevNtv'])
                revenue = coin.revenue
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.revenue = revenue
            try:
                coin.hashrate = float(item['HashRate'])
                hashrate = coin.hashrate
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.hashrate = hashrate
            try:
                coin.transactions = float(item['TxCnt'])
                transactions = coin.transactions
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.transactions = transactions
            try:
                coin.blocksize = float(item['BlkSizeMeanByte'])
                blocksize = coin.blocksize
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.blocksize = blocksize
            try:
                coin.difficulty = float(item['DiffLast'])
                difficulty = coin.difficulty
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin.difficulty = difficulty
            coin.save()
            count += 1

        except Exception as error:
            print(f'Something went wrong: {error}', flush=True)

    return count

def get_latest_metrics(symbol, url):
    '''Get most recent metrics from a data provider of your choice for 'symbol'''

    update = True
    count = 0

    while update:
        response = requests.get(url, timeout=60)
        data = json.loads(response.text)
        data_aux = data['data']
        for item in data_aux:
            time_array = str(item['time']).split('T')
            day = datetime.datetime.strptime(time_array[0], '%Y-%m-%d')
            day = datetime.datetime.strftime(day, '%Y-%m-%d')
            try:
                coin = Coin.objects.filter(name=symbol).get(date=day)
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin = Coin()

            try:
                coin.name = symbol
                coin.date = day
                try:
                    coin.priceusd = float(item['PriceUSD'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.priceusd = 0
                try:
                    coin.pricebtc = float(item['PriceBTC'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.pricebtc = 0
                try:
                    coin.inflation = float(item['IssContPctAnn'])
                    coin.stocktoflow = (100/coin.inflation)**1.65
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.inflation = 0
                    coin.stocktoflow = 0
                try:
                    coin.supply = float(item['SplyCur'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.supply = 0
                try:
                    coin.fee = float(item['FeeTotNtv'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.fee = 0
                try:
                    coin.revenue = float(item['RevNtv'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.revenue = 0
                try:
                    coin.hashrate = float(item['HashRate'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.hashrate = 0
                try:
                    coin.transactions = float(item['TxCnt'])
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    coin.transactions = 0

                coin.save()
                count += 1
                print(str(symbol) + ' ' + str(coin.date), flush=True)

            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
        try:
            url = data['next_page_url']
            update = True
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)
            update = False
            break
    return count

def get_latest_price(symbol):
    '''Get latest price data for Monero'''

    with open("settings.json", 'r', encoding="utf8") as file:
        data = json.load(file)

        url = data["metrics_provider"][0]["price_url_old"] + symbol
        print(url, flush=True)
        parameters = {
            'convert':'USD',
        }
        headers = {
            'Accepts': 'application/json',
            data["metrics_provider"][0]["api_key_name"]: data["metrics_provider"][0]["api_key_value"],
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            print('getting latest data', flush=True)
            try:
                if data['data'][symbol.upper()]['cmc_rank']:
                    print('new data received', flush=True)
                else:
                    print('problem with the data provider', flush=True)
                    data = False
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                data = False
        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(f'Something went wrong {error}', flush=True)
            data = False

        file.close()
    return data

def check_new_social(symbol):
    '''Load Reddit api to check if there are new followers'''

    yesterday = datetime.datetime.strftime(date.today()-timedelta(1), '%Y-%m-%d')
    socials = Social.objects.filter(name=symbol).filter(date=yesterday)
    if symbol == 'Bitcoin':
        timeframe = 14400
        hours = 86400/timeframe
        timeframe2 = 3600
        hours2 = 86400/timeframe2

    if symbol == 'Monero':
        timeframe = 43200
        hours = 86400/timeframe
        timeframe2 = 43200
        hours2 = 86400/timeframe2

    if symbol == 'Cryptocurrency':
        timeframe = 14400
        hours = 86400/timeframe
        timeframe2 = 1800
        hours2 = 86400/timeframe2

    if not socials:
        print('new social', flush=True)
        request = 'https://www.reddit.com/r/'+ symbol +'/about.json'
        response = requests.get(request, headers = {'User-agent': 'Checking new social data'}, timeout=60)
        data = json.loads(response.content)
        data = data['data']
        subscribers = data['subscribers']
        social = Social()
        social.name = symbol
        social.date = yesterday
        social.subscriber_count = subscribers

        date_aux = date.today()
        date_aux = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        date_aux = datetime.datetime.strptime(date_aux, '%Y-%m-%d')
        timestamp1 = int(datetime.datetime.timestamp(date_aux))

        timestamp2 = int(timestamp1 - timeframe)
        limit = 1000
        filters = []
        data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
        if data != 0:
            social.posts_per_hour = len(data)/hours
        else:
            social.posts_per_hour = 0

        timestamp2 = int(timestamp1 - timeframe2)
        limit = 1000
        data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
        if data != 0:
            social.comments_per_hour = len(data)/hours2
        else:
            social.comments_per_hour = 0
        social.save()
        print('getting new data - ' + str(social.name) + ' - ' + str(social.date), flush=True)
    return True

def update_database(date_from=None, date_to=None):
    '''Update database DailyData with most recent coin data'''

    date_zero = '2014-05-20'

    if not date_from or not date_to:
        date_to = date.today()
        date_from = date_to - timedelta(5)
        amount = date_from - datetime.datetime.strptime(date_zero, "%Y-%m-%d").date()
        print(f'[INFO] Updating from {str(date_from)} to {str(date_to)}', flush=True)
        print(f'[INFO] There are {str(amount)} passed since {date_zero}', flush=True)
    else:
        date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d")
        date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d")
        amount = date_from - datetime.datetime.strptime(date_zero, "%Y-%m-%d")
        print(f'[INFO] Updating from {str(date_from)} to {str(date_to)}', flush=True)
        print(f'[INFO] There are {str(amount)} passed since {date_zero}', flush=True)

    count = 0
    day_to_process = date_from
    while day_to_process <= date_to:

        print(f'[INFO] Processing {str(day_to_process)}', flush=True)
        day_to_process = date_from + timedelta(count)
        day_before = day_to_process - timedelta(1)
        print(f'[INFO] Day before {str(day_to_process)} is {str(day_before)}', flush=True)

        # Retrieve data points for cryptocurrencies

        try:
            try:
                xmr_data_point = Coin.objects.filter(name='xmr').get(date=day_to_process)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting XMR data: {error}', flush=True)
                return False
            try:
                xmr_previous_data_point = Coin.objects.filter(name='xmr').get(date=day_before)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting previous XMR data: {error}', flush=True)
                return False
            try:
                btc_data_point = Coin.objects.filter(name='btc').get(date=day_to_process)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting BTC data: {error}', flush=True)
                return False
            try:
                btc_previous_data_point = Coin.objects.filter(name='btc').get(date=day_before)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting previous BTC data: {error}', flush=True)
                return False
            try:
                dash_data_point = Coin.objects.filter(name='dash').get(date=day_to_process)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting DASH data: {error}', flush=True)
                dash_data_point = Coin()
            try:
                zcash_data_point = Coin.objects.filter(name='zec').get(date=day_to_process)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting ZEC data: {error}', flush=True)
                zcash_data_point = Coin()
            try:
                grin_data_point = Coin.objects.filter(name='grin').get(date=day_to_process)
            except Exception as error:
                print(f'[ERROR] Something went wrong getting GRIN data: {error}', flush=True)
                grin_data_point = Coin()

            if btc_data_point.inflation == 0 or xmr_data_point.inflation == 0:

                print(f'[INFO] BTC inflation: {btc_data_point.inflation} , XMR inflation: {xmr_data_point.inflation}')
                print(f'[INFO] Returning {count}')
                return count

            # Retrieve social data points for cryptocurrencies

            social_count = 0
            found = False
            while social_count < 100 and not found:
                print(f'[INFO] Processing social data, {social_count}')
                try:
                    day_to_process_social_data = day_to_process - timedelta(social_count)
                    social_btc = Social.objects.filter(name='Bitcoin').get(date=day_to_process_social_data)
                    social_xmr = Social.objects.filter(name='Monero').get(date=day_to_process_social_data)
                    social_crypto = Social.objects.filter(name='Cryptocurrency').get(date=day_to_process_social_data)
                    found = True
                    print('[INFO] Found Social Data', flush=True)
                except Exception as error:
                    print(f'[ERROR] Something went wrong retrieving Social Data: {error}', flush=True)
                    found = False
                social_count += 1
        except Exception as error:
            print(f'[INFO] Processing failed, returning {count}. Error: {error}')
            return count

        # Create stock to flow entry for XMR

        add_stock_to_flow_entry(xmr_data_point, amount)
        amount += timedelta(1)

        # Create daily data entry for XMR

        entry = update_daily_data_price_information(xmr_data_point, btc_data_point)

        entry = update_daily_data_marketcap(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point)

        entry = update_daily_data_transactions(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point)

        entry = update_daily_data_issuance(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point)

        entry = update_daily_data_emission(xmr_data_point, xmr_previous_data_point, btc_data_point, btc_previous_data_point)

        entry = update_daily_data_social(social_xmr, social_btc, social_crypto)

        try:
            print(
                str(xmr_data_point.supply)
                + " xmr "
                + str(entry.xmr_subscriber_count)
                + " - "
                + str(social_xmr.subscriber_count)
                + " = "
                + str(int(entry.xmr_marketcap))
                + " => "
                + str(xmr_data_point.inflation)
            , flush=True)
        except (Social.DoesNotExist, UnboundLocalError) as error:
            print(f'Something went wrong {error}', flush=True)

        count += 1

    return count

def update_p2pool():
    '''Get latest P2Pool data'''

    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=False).get(date=today)
        print("Found P2Pool of today", flush=True)
        if p2pool_stat.percentage > 0:
            print("Percentage > 0", flush=True)
            update = False
        else:
            print("Percentage < 0", flush=True)
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name="xmr").get(date=yesterday)
                print("Found coin of yesterday", flush=True)
                if coin.hashrate > 0:
                    update = True
                else:
                    update = False
            except Coin.DoesNotExist:
                print("Didn't find coin of yesterday", flush=True)
                update = False
    except P2Pool.DoesNotExist:
        print("Didn't find P2Pool of today", flush=True)
        try:
            coin = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin.hashrate > 0:
                update = True
            else:
                update  = False
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)
            update  = False

    if update:
        p2pool_stat = P2Pool()
        p2pool_stat.date = today
        response = requests.get('https://p2pool.io/api/pool/stats', timeout=60)

        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = False
        p2pool_stat.save()
        print('p2pool saved!', flush=True)

        values_mat = SHEETS.get_values(CSV_DATA_SHEET, "p2pool", start=(2, 0), end=(9999, 3))

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
            print('spreadsheet updated', flush=True)
        else:
            print('spreadsheet already with the latest data', flush=True)
            return data

    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=True).get(date=today)
        print("Found P2PoolMini of today", flush=True)
        if p2pool_stat.percentage > 0:
            print("Percentage > 0", flush=True)
            update = False
        else:
            print("Percentage < 0", flush=True)
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)

                print("Found coin of yesterday", flush=True)
                if coin.hashrate > 0:
                    update = True
                else:
                    update = False
            except Coin.DoesNotExist:
                print("Didn't find coin of yesterday", flush=True)
                update = False
    except P2Pool.DoesNotExist:
        print("Didn't find P2PoolMini of today", flush=True)
        try:
            coin = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin.hashrate > 0:
                update = True
            else:
                update  = False
        except Exception as error:
            print(f'Something went wrong: {error}', flush=True)
            update  = False

    if update:
        p2pool_stat = P2Pool()
        p2pool_stat.date = today
        response = requests.get('https://p2pool.io/mini/api/pool/stats', timeout=60)

        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = True
        p2pool_stat.save()
        print('p2pool_mini saved!', flush=True)

        values_mat = SHEETS.get_values(CSV_DATA_SHEET, "p2poolmini", start=(2, 0), end=(9999, 3))

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
            print('spreadsheet updated', flush=True)
        else:
            print('spreadsheet already with the latest data', flush=True)
            return data

    return True
