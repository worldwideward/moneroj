import aiohttp
import asyncio
import json
from .synchronous import *
import datetime
from datetime import date, timedelta
from .models import Coin, Social, P2Pool
import requests
import pygsheets

####################################################################################
#   Asynchronous get block data from xmrchain
#################################################################################### 
async def get_block_data(session, block: str):
    url = 'https://localmonero.co/blocks/api/get_block_data/' + block
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
    url = 'https://xmrchain.net/api/networkinfo'
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
async def get_coinmarketcap_data(session, symbol: str, convert: str):
    with open("settings.json") as file:
        data = json.load(file)
        file.close()

    url = data["metrics_provider"][0]["price_url_old"] + symbol
    parameters = {'convert': convert,}
    headers = {'Accepts': 'application/json', data["metrics_provider"][0]["api_key_name"]: data["metrics_provider"][0]["api_key_value"],}

    async with session.get(url, headers=headers, params=parameters) as res:
        data = await res.read()
        data = json.loads(data)
        data['provider'] = 'coinmarketcap'
        if res.status < 299:
            try:
                if data['data'][symbol.upper()]['cmc_rank']:
                    data['success'] = True
                else:
                    data['success'] = False
            except:
                data['success'] = False
        else:
            data['success'] = False
        return data

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
async def get_social_data(session, symbol):
    yesterday = datetime.datetime.strftime(date.today()-timedelta(1), '%Y-%m-%d')
    try:
        social = Social.objects.filter(name=symbol).get(date=yesterday)
    except:
        url = 'https://www.reddit.com/r/'+ symbol +'/about.json'

        async with session.get(url, headers={'User-agent': 'Checking new social data'}) as res:
            data = await res.read()
            data = json.loads(data) 
            data = data['data']

            social = Social()
            social.name = symbol
            social.date = yesterday
            social.subscriberCount = data['subscribers']

            timestamp1 = int(datetime.datetime.timestamp(datetime.datetime.strptime(yesterday, '%Y-%m-%d')))
            timestamp2 = int(timestamp1 - 7200)
            limit = 1000
            filters = []
            data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
            social.postsPerHour = len(data)/2
            data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
            social.commentsPerHour = len(data)/2
            social.save()
    return True

####################################################################################
#   Asynchronous get whole xmr data calling coinmarketcap and xmrchain
#################################################################################### 
async def update_xmr_data(yesterday, coin):
    name = coin.name
    Coin.objects.filter(name=coin.name).filter(date=yesterday).delete()

    url = 'https://localmonero.co/blocks/api/get_stats'
    response = requests.get(url)
    data = json.loads(response.text)
    height = int(data['height'])
    difficulty = int(data['difficulty'])
    hashrate = int(data['hashrate'])
    supply = int(data['total_emission'])
    blocksize = 0        
    actions = []

    my_timeout = aiohttp.ClientTimeout(
        total=10,
        sock_connect=10, 
        sock_read=10 
    )
    client_args = dict(
        trust_env=True,
        timeout=my_timeout
    )

    async with aiohttp.ClientSession(**client_args) as session:  
        for count in range(1, 1400):
            block = str(height - count)
            actions.append(asyncio.ensure_future(get_block_data(session, block)))
        actions.append(asyncio.ensure_future(get_coinmarketcap_data(session, 'xmr', 'USD')))
        actions.append(asyncio.ensure_future(get_coinmarketcap_data(session, 'xmr', 'BTC')))

        try:
            responses = await asyncio.gather(*actions, return_exceptions=True)
        except asyncio.exceptions.TimeoutError:
            print('Timeout!')

        errors = 0
        success = 0
        txs = 0
        revenue = 0
        fees = 0
        priceusd = 0
        pricebtc = 0
        for response in responses:
            if response:
                try:
                    if response['provider'] == 'localmonero':
                        date_aux = response['block_header']['timestamp']
                        if date_aux == yesterday:
                            try:
                                blocksize += int(response['block_header']['size'])
                                for tx in response['block_header']['txs']:
                                    if tx['coinbase']:
                                        revenue += int(tx['xmr_outputs'])
                                    else:
                                        txs += 1
                                        fees += int(tx['tx_fee'])
                                        revenue += int(tx['tx_fee'])
                                success += 1
                            except:
                                errors += 1

                    if response['provider'] == 'coinmarketcap':
                        try:
                            priceusd = float(response['data']['XMR']['quote']['USD']['price'])
                            update_rank(response)    
                            update_dominance(response)
                        except:
                            try:
                                pricebtc = float(response['data']['XMR']['quote']['BTC']['price'])
                            except:
                                errors += 1
                except:
                    errors += 1
            else:
                errors += 1

        blocksize = blocksize/success
        revenue = float(revenue)/10**12
        fees = float(fees)/10**12
        inflation = 100*365*(revenue)/float(coin.supply)
        stocktoflow = (100/inflation)**1.65 
        supply = coin.supply + revenue

        try:        
            coin = Coin()
            coin.name = name
            coin.date = datetime.datetime.strptime(yesterday, '%Y-%m-%d')
            coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
            coin.blocksize = blocksize
            coin.transactions = txs
            coin.revenue = revenue
            coin.fee = fees
            coin.inflation = inflation
            coin.hashrate = hashrate
            coin.difficulty = difficulty
            coin.stocktoflow = stocktoflow
            coin.priceusd = priceusd
            coin.pricebtc = pricebtc
            coin.supply = supply
            coin.save()

            # print('Success: ' + str(success))
            # print('Errors: ' + str(errors))
            # print('Name: ' + coin.name)
            # print('Date: ' + str(coin.date))
            # print('Blocksize: ' + str(coin.blocksize))
            # print('Transactions: ' + str(coin.transactions))
            # print('Revenue: ' + str(coin.revenue))
            # print('Fees: ' + str(coin.fee))
            # print('Inflation: ' + str(coin.inflation))
            # print('Hashrate: ' + str(coin.hashrate))
            # print('Stocktoflow: ' + str(coin.stocktoflow))
            # print('Priceusd: ' + str(coin.priceusd))
            # print('Pricebtc: ' + str(coin.pricebtc))
            # print('Supply: ' + str(coin.supply))
        except:
            return False
    return True

####################################################################################
#   Asynchronous get social and coins data
#################################################################################### 
async def update_others_data(date):
    with open("settings.json") as file:
        data = json.load(file)
        file.close()

    url_btc = data["metrics_provider"][0]["metrics_url_new"] + 'btc/' + date 
    url_dash = data["metrics_provider"][0]["metrics_url_new"] + 'dash/' + date
    url_grin = data["metrics_provider"][0]["metrics_url_new"] + 'grin/' + date 
    url_zec = data["metrics_provider"][0]["metrics_url_new"] + 'zec/' + date
    actions = []

    my_timeout = aiohttp.ClientTimeout(
        total=10,
        sock_connect=10, 
        sock_read=10 
    )
    client_args = dict(
        trust_env=True,
        timeout=my_timeout
    )

    async with aiohttp.ClientSession(**client_args) as session:  
        # reddit data
        #actions.append(asyncio.ensure_future(get_social_data(session, 'Monero')))
        #actions.append(asyncio.ensure_future(get_social_data(session, 'Bitcoin')))
        #actions.append(asyncio.ensure_future(get_social_data(session, 'Cryptocurrency')))
        # coinmetrics data
        actions.append(asyncio.ensure_future(get_coin_data(session, 'btc', url_btc)))
        actions.append(asyncio.ensure_future(get_coin_data(session, 'dash', url_dash)))
        actions.append(asyncio.ensure_future(get_coin_data(session, 'grin', url_grin)))
        actions.append(asyncio.ensure_future(get_coin_data(session, 'zec', url_zec)))
        actions.append(asyncio.ensure_future(get_p2pool_data(session, mini=False)))
        actions.append(asyncio.ensure_future(get_p2pool_data(session, mini=True)))

        try:
            await asyncio.gather(*actions, return_exceptions=True)
        except asyncio.exceptions.TimeoutError:
            print('Timeout!')

    return True

####################################################################################
#   Asynchronous get social and coins data
#################################################################################### 
async def update_social_data(symbol):

    actions = []
    my_timeout = aiohttp.ClientTimeout(
        total=10,
        sock_connect=10, 
        sock_read=10 
    )
    client_args = dict(
        trust_env=True,
        timeout=my_timeout
    )

    async with aiohttp.ClientSession(**client_args) as session:  
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
    else:   
        return False
    return True







