'''Synchronous functions'''

import json
import datetime
from datetime import date, timedelta
import pytz
import requests
import pandas as pd
from psaw import PushshiftAPI
from requests import Session
from requests.exceptions import Timeout, TooManyRedirects
from .models import Coin, Social, P2Pool, Dominance, Rank, Sfmodel, DailyData, Withdrawal
from .spreadsheets import PandasSpreadSheetManager

sheets = PandasSpreadSheetManager()

####################################################################################
#   Reddit api
####################################################################################
API = PushshiftAPI()

def data_prep_posts(subreddit, start_time, end_time, filters, limit):
    '''Get daily posts in a certain subreddit '''

    if len(filters) == 0:
        filters = ['id', 'author', 'created_utc', 'domain', 'url', 'title', 'num_comments']

    try:
        posts = list(API.search_submissions(subreddit=subreddit, after=start_time, before=end_time, filter=filters, limit=limit))
        return pd.DataFrame(posts)
    except Exception as error:
        print(f'Something went wrong: {error}', flush=True)
        return None

def data_prep_comments(term, start_time, end_time, filters, limit):
    '''Get daily comments in a certain subreddit'''
    if len(filters) == 0:
        filters = ['id', 'author', 'created_utc','body', 'permalink', 'subreddit']

    try:
        comments = list(API.search_comments(q=term, after=start_time, before=end_time, filter=filters, limit=limit))
        return pd.DataFrame(comments)
    except Exception as error:
        print(f'Something went wrong: {error}', flush=True)
        return None

####################################################################################
#   Other useful functions
####################################################################################

def get_history_function(symbol, start_time=None, end_time=None):
    '''Get historic data from a cryptocurrency coin'''
    update = True
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

    with open("settings.json", 'r', encoding="utf8") as file:
        data = json.load(file)
        file.close()

    if not(start_time and end_time):
        start_time = '2000-01-01'
        end_time = '2100-01-01'

    url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time + '/' + end_time
    print(url, flush=True)

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

    while update:
        response = requests.get(url, timeout=60)
        data_aux = json.loads(response.text)
        data_aux2 = data_aux['data']
        for item in data_aux2:
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
                print(coin.name + ' ' + str(coin.date) + ' ' + str(item['SplyCur']), flush=True)

            except Exception as error:
                print(f'Something went wrong: {error}', flush=True)
        try:
            url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time + '/' + end_time + '/' + data_aux['next_page_token']
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)
            update = False
            break
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

def get_binance_withdrawal(symbol):
    '''Get binance withdrawal state'''

    url = 'https://www.binance.com/en/network'

    withdrawals = Withdrawal.objects.order_by('-date')
    if len(withdrawals) > 0:
        for withdrawal in withdrawals:
            break
    else:
        withdrawal = Withdrawal()
        withdrawal.state = True
        withdrawal.save()
        return True

    current_date = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    response = requests.get(url, timeout=60)
    result = response.text
    position = result.find(symbol)
    result = result[position:position+400]
    position = result.find('withdrawEnable')
    result = result[position:position+25]
    try:
        result.index('true')
        if (current_date - withdrawal.date).seconds > 3600:
            new_withdrawal = Withdrawal()
            new_withdrawal.state = True
            new_withdrawal.save()
        return True
    except Exception as error:
        print(f'Something went wrong {error}', flush=True)
        try:
            result.index('false')
            if ((current_date - withdrawal.date).seconds > 3600) or withdrawal.state:
                new_withdrawal = Withdrawal()
                new_withdrawal.state = False
                new_withdrawal.save()
            return False
        except Exception as inner_error:
            print(f'Something went wrong {inner_error}', flush=True)
            return None

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

def update_dominance(data):
    '''Get latest dominance value and update'''

    if not data:
        print('error updating dominance', flush=True)
        return False

    dominance = Dominance()
    dominance.name = 'xmr'
    dominance.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    dominance.dominance = float(data['data']['XMR']['quote']['USD']['market_cap_dominance'])
    dominance.save()

    values_mat = sheets.get_values("zcash_bitcoin.ods", "Sheet7", start=(2, 0), end=(9999, 2))

    k = len(values_mat)
    date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
    date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')

    if date_aux < date_aux2:

        values_mat[k][1] = dominance.dominance
        values_mat[k][0] = dominance.date

        #TODO: Figure out where undefined vars came from
        df.iloc[start_row:end_row, start_col:end_col] = values_mat
        df.to_excel(DATA_FILE, sheet_name="Sheet7", index=False)

        print("spreadsheet updated", flush=True)
    else:
        print('spreadsheet already with the latest data', flush=True)
        return False

    return data

def update_rank(data=None):
    '''Get latest rank value and update'''

    if not data:
        data = get_latest_price('xmr')
    if not data:
        print('error updating rank', flush=True)
        return False

    rank = Rank()
    rank.name = 'xmr'
    rank.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    rank.rank = int(data['data']['XMR']['cmc_rank'])
    rank.save()

    values_mat = sheets.get_values("zcash_bitcoin.ods", "Sheet8", start=(2, 0), end=(9999, 2))
    k = len(values_mat)
    date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
    date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')

    if date_aux < date_aux2:

        values_mat[k][1] = rank.rank
        values_mat[k][0] = rank.date

        #TODO: Figure out where undefined vars came from
        df.iloc[start_row:end_row, start_col:end_col] = values_mat
        df.to_excel(DATA_FILE, sheet_name="Sheet8", index=False)

        print("spreadsheet updated", flush=True)
    else:
        print('spreadsheet already with the latest data', flush=True)

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
    else:
        print(str(date_from) + " to " + str(date_to), flush=True)
        date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d")
        date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d")
        amount = date_from - datetime.datetime.strptime(date_zero, "%Y-%m-%d")

    count = 0
    date_aux = date_from
    while date_aux <= date_to:
        date_aux = date_from + timedelta(count)
        date_aux2 = date_aux - timedelta(1)
        try:
            coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)
            coin_xmr2 = Coin.objects.filter(name='xmr').get(date=date_aux2)
            coin_btc = Coin.objects.filter(name='btc').get(date=date_aux)
            coin_btc2 = Coin.objects.filter(name='btc').get(date=date_aux2)
            try:
                coin_dash = Coin.objects.filter(name='dash').get(date=date_aux)
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin_dash = Coin()
            try:
                coin_zcash = Coin.objects.filter(name='zec').get(date=date_aux)
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin_zcash = Coin()
            try:
                coin_grin = Coin.objects.filter(name='grin').get(date=date_aux)
            except Exception as error:
                print(f'Something went wrong {error}', flush=True)
                coin_grin = Coin()

            if coin_btc.inflation == 0 or coin_xmr.inflation == 0:
                return count

            count_aux = 0
            found = False
            while count_aux < 100 and not found:
                try:
                    date_aux3 = date_aux - timedelta(count_aux)
                    social_btc = Social.objects.filter(name='Bitcoin').get(date=date_aux3)
                    social_xmr = Social.objects.filter(name='Monero').get(date=date_aux3)
                    social_crypto = Social.objects.filter(name='Cryptocurrency').get(date=date_aux3)
                    found = True
                except Exception as error:
                    print(f'Something went wrong {error}', flush=True)
                    found = False
                count_aux += 1
        except:
            return count

        try:
            data = Sfmodel.objects.get(date=coin_xmr.date)

        except Exception as error:
            print(f'Something went wrong {error}', flush=True)
            data = Sfmodel()
            data.priceusd = 0
            data.pricebtc = 0
            data.stocktoflow = 0
            data.greyline = 0
            data.color = 0
            data.date = coin_xmr.date
        data.pricebtc = coin_xmr.pricebtc
        data.priceusd = coin_xmr.priceusd
        if data.stocktoflow == 0 and coin_xmr.supply > 0:
            supply = int(coin_xmr.supply)*10**12
            reward = (2**64 -1 - supply) >> 19
            reward = max(0.6*(10**12))
            inflation = 100*reward*720*365/supply
            data.stocktoflow = (100/(inflation))**1.65
        v0 = 0.002
        delta = (0.015 - 0.002)/(6*365)
        data.color = 30*coin_xmr.pricebtc/((amount.days)*delta + v0)
        amount += timedelta(1)
        data.save()

        try:
            data = DailyData.objects.get(date=coin_xmr.date)
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)
            data = DailyData()
            # Date field
            data.date = coin_xmr.date
            # Basic information
            data.btc_priceusd = 0
            data.xmr_priceusd = 0
            data.xmr_pricebtc = 0
            # Marketcap charts
            data.btc_marketcap = 0
            data.xmr_marketcap = 0
            data.dash_marketcap = 0
            data.grin_marketcap = 0
            data.zcash_marketcap = 0
            # Transactions charts
            data.xmr_transacpercentage = 0
            data.btc_transactions = 0
            data.zcash_transactions = 0
            data.dash_transactions = 0
            data.grin_transactions = 0
            data.xmr_transactions = 0
            data.btc_supply = 0
            data.xmr_supply = 0
            # Issuance charts
            data.btc_inflation = 0
            data.xmr_inflation = 0
            data.dash_inflation = 0
            data.grin_inflation = 0
            data.zcash_inflation = 0
            data.xmr_metcalfebtc = 0
            data.xmr_metcalfeusd = 0
            data.btc_return = 0
            data.xmr_return = 0
            data.btc_emissionusd = 0
            data.btc_emissionntv = 0
            data.xmr_emissionusd = 0
            data.xmr_emissionntv = 0
            # Mining charts
            data.btc_minerrevntv = 0
            data.xmr_minerrevntv = 0
            data.btc_minerrevusd = 0
            data.xmr_minerrevusd = 0
            data.btc_minerfeesntv = 0
            data.xmr_minerfeesntv = 0
            data.btc_minerfeesusd = 0
            data.xmr_minerfeesusd = 0
            data.btc_transcostntv = 0
            data.xmr_transcostntv = 0
            data.btc_transcostusd = 0
            data.xmr_transcostusd = 0
            data.xmr_minerrevcap = 0
            data.btc_minerrevcap = 0
            data.btc_commitntv = 0
            data.xmr_commitntv = 0
            data.btc_commitusd = 0
            data.xmr_commitusd = 0
            data.btc_blocksize = 0
            data.xmr_blocksize = 0
            data.btc_difficulty = 0
            data.xmr_difficulty = 0
            # Reddit charts
            data.btc_subscriber_count = 0
            data.btc_comments_per_hour = 0
            data.btc_posts_per_hour = 0
            data.xmr_subscriber_count = 0
            data.xmr_comments_per_hour = 0
            data.xmr_posts_per_hour = 0
            data.crypto_subscriber_count = 0
            data.crypto_comments_per_hour = 0
            data.crypto_posts_per_hour = 0

        # Date field
        data.date = coin_xmr.date
        # Basic information
        data.btc_priceusd = coin_btc.priceusd
        data.xmr_priceusd = coin_xmr.priceusd
        data.xmr_pricebtc = coin_xmr.pricebtc
        # Marketcap charts
        data.btc_marketcap = float(coin_btc.priceusd)*float(coin_btc.supply)
        data.xmr_marketcap = float(coin_xmr.priceusd)*float(coin_xmr.supply)
        data.dash_marketcap = float(coin_dash.priceusd)*float(coin_dash.supply)
        data.grin_marketcap = float(coin_grin.priceusd)*float(coin_grin.supply)
        data.zcash_marketcap = float(coin_zcash.priceusd)*float(coin_zcash.supply)

        # Transactions charts
        try:
            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        data.xmr_transactions = coin_xmr.transactions
        data.btc_transactions = coin_btc.transactions
        data.zcash_transactions = coin_zcash.transactions
        data.dash_transactions = coin_dash.transactions
        data.grin_transactions = coin_grin.transactions
        data.btc_supply = coin_btc.supply
        data.xmr_supply = coin_xmr.supply
        # Issuance charts
        data.btc_inflation = coin_btc.inflation
        data.xmr_inflation = coin_xmr.inflation
        data.dash_inflation = coin_dash.inflation
        data.grin_inflation = coin_grin.inflation
        data.zcash_inflation = coin_zcash.inflation
        try:
            data.xmr_metcalfebtc = coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
            data.xmr_metcalfeusd = coin_btc.priceusd*coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        data.btc_return = coin_btc.priceusd/30
        data.xmr_return = coin_xmr.priceusd/5.01
        data.btc_emissionusd = (coin_btc.supply - coin_btc2.supply)*coin_btc.priceusd
        data.btc_emissionntv = coin_btc.supply - coin_btc2.supply
        data.xmr_emissionusd = (coin_xmr.supply - coin_xmr2.supply)*coin_xmr.priceusd
        data.xmr_emissionntv = coin_xmr.supply - coin_xmr2.supply
        # Mining charts
        data.btc_minerrevntv = coin_btc.revenue
        data.xmr_minerrevntv = coin_xmr.revenue
        data.btc_minerrevusd = coin_btc.revenue*coin_btc.priceusd
        data.xmr_minerrevusd = coin_xmr.revenue*coin_xmr.priceusd
        data.btc_minerfeesntv = coin_btc.revenue - coin_btc.supply + coin_btc2.supply
        data.xmr_minerfeesntv = coin_xmr.revenue - coin_xmr.supply + coin_xmr2.supply
        data.btc_minerfeesusd = (coin_btc.revenue - coin_btc.supply + coin_btc2.supply)*coin_btc.priceusd
        data.xmr_minerfeesusd = (coin_xmr.revenue - coin_xmr.supply + coin_xmr2.supply)*coin_xmr.priceusd
        try:
            data.btc_transcostntv = coin_btc.fee/coin_btc.transactions
            data.xmr_transcostntv = coin_xmr.fee/coin_xmr.transactions
            data.btc_transcostusd = coin_btc.priceusd*coin_btc.fee/coin_btc.transactions
            data.xmr_transcostusd = coin_xmr.priceusd*coin_xmr.fee/coin_xmr.transactions
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        try:
            data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        try:
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        try:
            data.btc_blocksize = coin_btc.blocksize
            data.xmr_blocksize = coin_xmr.blocksize
            data.btc_difficulty = coin_btc.difficulty
            data.xmr_difficulty = coin_xmr.difficulty
        except Exception as error:
            print(f'Something went wrong {error}', flush=True)

        # Reddit charts
        try:
            data.btc_subscriber_count = social_btc.subscriber_count
            data.btc_comments_per_hour = social_btc.comments_per_hour
            data.btc_posts_per_hour = social_btc.posts_per_hour
            data.xmr_subscriber_count = social_xmr.subscriber_count
            data.xmr_comments_per_hour = social_xmr.comments_per_hour
            data.xmr_posts_per_hour = social_xmr.posts_per_hour
            data.crypto_subscriber_count = social_crypto.subscriber_count
            data.crypto_comments_per_hour = social_crypto.comments_per_hour
            data.crypto_posts_per_hour = social_crypto.posts_per_hour
        except (Social.DoesNotExist, UnboundLocalError):
            data.btc_subscriber_count = 0
            data.btc_comments_per_hour = 0
            data.btc_posts_per_hour = 0
            data.xmr_subscriber_count = 0
            data.xmr_comments_per_hour = 0
            data.xmr_posts_per_hour = 0
            data.crypto_subscriber_count = 0
            data.crypto_comments_per_hour = 0
            data.crypto_posts_per_hour = 0

        data.save()

        try:
            print(
                str(coin_xmr.supply)
                + " xmr "
                + str(data.xmr_subscriberCount)
                + " - "
                + str(social_xmr.subscriberCount)
                + " = "
                + str(int(data.xmr_marketcap))
                + " => "
                + str(coin_xmr.inflation)
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

        values_mat = sheets.get_values("zcash_bitcoin.ods", "p2pool", start=(2, 0), end=(9999, 3))

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

        values_mat = sheets.get_values("zcash_bitcoin.ods", "p2poolmini", start=(2, 0), end=(9999, 3))

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
