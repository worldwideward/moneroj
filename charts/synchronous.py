from psaw import PushshiftAPI
import pandas as pd
import json
import requests
import datetime
from datetime import date, timedelta
from .models import Coin, Social, P2Pool, Dominance, Rank, Sfmodel, DailyData
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import pygsheets

####################################################################################
#   Reddit api
####################################################################################
api = PushshiftAPI() 

# Get daily post on Reddit
def data_prep_posts(subreddit, start_time, end_time, filters, limit):
    if(len(filters) == 0):
        filters = ['id', 'author', 'created_utc', 'domain', 'url', 'title', 'num_comments'] 

    posts = list(api.search_submissions(subreddit=subreddit, after=start_time, before=end_time, filter=filters, limit=limit))

    return pd.DataFrame(posts)

# Get daily comments on Reddit
def data_prep_comments(term, start_time, end_time, filters, limit):
    if (len(filters) == 0):
        filters = ['id', 'author', 'created_utc','body', 'permalink', 'subreddit'] 

    comments = list(api.search_comments(q=term, after=start_time, before=end_time, filter=filters, limit=limit))
    return pd.DataFrame(comments) 

####################################################################################
#   Other useful functions                  
####################################################################################

# Get most recent metrics from a data provider of your choice for 'symbol'
def get_latest_metrics(symbol, url):
    update = True
    count = 0

    while update: 
        response = requests.get(url)
        data = json.loads(response.text)
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
                print(str(symbol) + ' ' + str(coin.date))

            except:
                pass
        try:
            url = data['next_page_url']
            update = True
        except:
            update = False
            break 
    return count

# Get latest price data for Monero
def get_latest_price(symbol):
    with open("settings.json") as file:
        data = json.load(file)

        url = data["metrics_provider"][0]["price_url_old"] + symbol
        print(url)
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
            print(response)
            data = json.loads(response.text)
            print('getting latest data')
            print(data)
            try:
                if data['data'][symbol.upper()]['cmc_rank']:
                    print('new data received')
                    pass
                else:
                    print('problem with the data provider')
                    data = False
            except:
                data = False
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            data = False

        file.close()
    return data

# Get latest dominance value and update
def update_dominance(data):
    if not(data):
        print('error updating dominance')
        return False
    else:
        dominance = Dominance()
        dominance.name = 'xmr'
        dominance.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        dominance.dominance = float(data['data']['XMR']['quote']['USD']['market_cap_dominance'])
        dominance.save()

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('Sheet7')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'B' + str(k + 3)
            wks.update_value(cell, dominance.dominance)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, dominance.date)
            print('spreadsheet updated')
        else:
            print('spreadsheet already with the latest data')
            return False
    return data

# Get latest rank value and update
def update_rank(data=None):
    if not(data):
        data = get_latest_price('xmr')
    if not(data):
        print('error updating rank')
        return False
    else:
        rank = Rank()
        rank.name = 'xmr'
        rank.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        rank.rank = int(data['data']['XMR']['cmc_rank'])
        rank.save()

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('Sheet8')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'B' + str(k + 3)
            wks.update_value(cell, rank.rank)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, rank.date)
            print('spreadsheet updated')
        else:
            print('spreadsheet already with the latest data')
            return data

    return data

# Load Reddit api to check if there are new followers
def check_new_social(symbol):
    date_now = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    socials = Social.objects.filter(name=symbol).filter(date=date_now)

    if not(socials):
        print('getting new data')
        request = 'https://www.reddit.com/r/'+ symbol +'/about.json'
        response = requests.get(request, headers = {'User-agent': 'Checking new social data'})
        data = json.loads(response.content)    
        data = data['data']
        subscribers = data['subscribers']
        social = Social()
        social.name = symbol
        social.date = date_now
        social.subscriberCount = subscribers

        date_aux = date.today()
        date_aux = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        date_aux = datetime.datetime.strptime(date_aux, '%Y-%m-%d')
        timestamp1 = int(datetime.datetime.timestamp(date_aux))

        timestamp2 = int(timestamp1 - 43200)
        limit = 1000
        filters = []
        data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.postsPerHour = len(data)/12

        timestamp2 = int(timestamp1 - 3600)
        limit = 1000
        data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.commentsPerHour = len(data)/1
        social.save()
    return True

# Update database DailyData with most recent coin data
def update_database(date_from=None, date_to=None):
    date_zero = '2014-05-20'

    if not(date_from) or not(date_to):
        date_to = date.today()
        date_from = date_to - timedelta(5)
        amount = date_from - datetime.datetime.strptime(date_zero, '%Y-%m-%d')
    else:
        print(str(date_from) + ' to ' + str(date_to))
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        amount = date_from - datetime.datetime.strptime(date_zero, '%Y-%m-%d')

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
            except:
                coin_dash = Coin()
            try:
                coin_zcash = Coin.objects.filter(name='zec').get(date=date_aux)
            except:
                coin_zcash = Coin()
            try:
                coin_grin = Coin.objects.filter(name='grin').get(date=date_aux)
            except:
                coin_grin = Coin()

            if coin_btc.inflation == 0 or coin_xmr.inflation == 0:
                return count

            count_aux = 0
            found = False
            while count_aux < 100 and not(found):

                try:
                    date_aux2 = date_aux - timedelta(count_aux)
                    social_btc = Social.objects.filter(name='Bitcoin').get(date=date_aux2)
                    social_xmr = Social.objects.filter(name='Monero').get(date=date_aux2)
                    social_crypto = Social.objects.filter(name='CryptoCurrency').get(date=date_aux2)
                    found = True

                except:
                    count_aux += 1
                    found = False
        except:
            return count

        try:
            data = Sfmodel.objects.get(date=coin_xmr.date)

        except:
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
            if reward < 0.6*(10**12):
                reward = 0.6*(10**12)
            inflation = 100*reward*720*365/supply
            data.stocktoflow = (100/(inflation))**1.65
        v0 = 0.002
        delta = (0.015 - 0.002)/(6*365)
        data.color = 30*coin_xmr.pricebtc/((amount.days)*delta + v0)
        amount += timedelta(1)
        data.save()

        try:
            data = DailyData.objects.get(date=coin_xmr.date)
        except: 
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
            data.btc_subscriberCount = 0
            data.btc_commentsPerHour = 0
            data.btc_postsPerHour = 0
            data.xmr_subscriberCount = 0
            data.xmr_commentsPerHour = 0
            data.xmr_postsPerHour = 0
            data.crypto_subscriberCount = 0
            data.crypto_commentsPerHour = 0
            data.crypto_postsPerHour = 0
            
        # Date field
        data.date = coin_xmr.date
        # Basic information
        data.btc_priceusd = coin_btc.priceusd
        data.xmr_priceusd = coin_xmr.priceusd
        data.xmr_pricebtc = coin_xmr.pricebtc
        # Marketcap charts
        data.btc_marketcap = coin_btc.priceusd*coin_btc.supply
        data.xmr_marketcap = coin_xmr.priceusd*coin_xmr.supply
        print(coin_dash.priceusd)
        print(coin_dash.supply)
        data.dash_marketcap = coin_dash.priceusd*coin_dash.supply
        data.grin_marketcap = coin_grin.priceusd*coin_grin.supply
        data.zcash_marketcap = coin_zcash.priceusd*coin_zcash.supply

        # Transactions charts
        try:
            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions
        except:
            pass
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
        except:
            pass
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
        except:
            pass
        try:
            data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply
        except:
            pass
        try:
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)
        except:
            pass
        try:
            data.btc_blocksize = coin_btc.blocksize
            data.xmr_blocksize = coin_xmr.blocksize
            data.btc_difficulty = coin_btc.difficulty
            data.xmr_difficulty = coin_xmr.difficulty
        except:
            pass
        # Reddit charts
        try:
            data.btc_subscriberCount = social_btc.subscriberCount
            data.btc_commentsPerHour = social_btc.commentsPerHour
            data.btc_postsPerHour = social_btc.postsPerHour
            data.xmr_subscriberCount = social_xmr.subscriberCount
            data.xmr_commentsPerHour = social_xmr.commentsPerHour
            data.xmr_postsPerHour = social_xmr.postsPerHour
            data.crypto_subscriberCount = social_crypto.subscriberCount
            data.crypto_commentsPerHour = social_crypto.commentsPerHour
            data.crypto_postsPerHour = social_crypto.postsPerHour
        except:
            data.btc_subscriberCount = 0
            data.btc_commentsPerHour = 0
            data.btc_postsPerHour = 0
            data.xmr_subscriberCount = 0
            data.xmr_commentsPerHour = 0
            data.xmr_postsPerHour = 0
            data.crypto_subscriberCount = 0
            data.crypto_commentsPerHour = 0
            data.crypto_postsPerHour = 0

        data.save()
        print(str(coin_xmr.date) + ' - ' + str(int(coin_xmr.supply)) + ' xmr @ ' + str(coin_xmr.priceusd) + ' = ' + str(int(data.xmr_marketcap)) + ' => ' + str(coin_xmr.inflation))

        count += 1

    return count

# Get latest P2Pool data
def update_p2pool():
    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=False).get(date=today)
        print('achou p2pool de hoje')
        if p2pool_stat.percentage > 0:
            print('porcentagem > 0')
            update  = False
        else:
            print('porcentagem < 0')
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)
                print('achou coin de ontem')
                if coin.hashrate > 0:
                    update = True
                else:
                    update  = False
            except:
                print('nao achou coin de ontem')
                update  = False
    except:
        print('nao achou p2pool de hoje')
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
        response = requests.get('https://p2pool.io/api/pool/stats')
        
        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = False
        p2pool_stat.save()
        print('p2pool saved!')

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('p2pool')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,3), returnas='matrix')

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
        
    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=True).get(date=today)
        print('achou p2pool_mini de hoje')
        if p2pool_stat.percentage > 0:

            print('porcentagem > 0')
            update  = False
        else:
            print('porcentagem < 0')
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)

                print('achou coin de ontem')
                if coin.hashrate > 0:
                    update = True
                else:
                    update  = False
            except:
                print('nao achou coin de ontem')
                update  = False
    except:
        print('nao achou p2pool_mini de hoje')
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
        response = requests.get('https://p2pool.io/mini/api/pool/stats')
        
        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = True
        p2pool_stat.save()
        print('p2pool_mini saved!')

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('p2poolmini')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,3), returnas='matrix')

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

    return True
