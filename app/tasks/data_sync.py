'''Tasks to perform with Celery for updating chart data'''

import datetime
import math
from datetime import date
from datetime import timedelta

from charts.models import Coin
from charts.models import Sfmodel
from charts.models import Social
from charts.models import DailyData
from charts.asynchronous import update_xmr_data
from charts.asynchronous import update_others_data
from charts.synchronous import update_database
from charts.synchronous import get_history_function


def check_for_updates(yesterday) -> bool:
    '''Check if it is necessary to update XMR data'''

    try:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=yesterday)
        if coin_xmr:
            print('xmr found yesterday', flush=True)
            if coin_xmr.priceusd > 1 and coin_xmr.transactions > 0 and coin_xmr.inflation > 0:
                print('no need to update xmr', flush=True)
            else:
                print('will update xmr')
                coin_xmr.delete()
                return True
        else:
            print('no xmr found yesterday - 1')
            return True
    except Exception as error:
        print(f'Exception while trying to look for coin data - {error}')
        return True

    return False

def check_monero_available() -> str:
    '''Check if coin data about Monero is present in the database'''

    coins = Coin.objects.filter(name='xmr').order_by('-date')
    count = 0
    for coin in coins:
        count += 1
        if count< 200:
            if coin.supply < 18000000:
                coin.supply += 499736
                print(coin.date)
                coin.save()

    coin = list(Coin.objects.order_by('-date'))[0]

    message = coin

    if not coin:
        message = 'Monero unavailable'

    return message

async def xmr_updates(yesterday, date_aux):
    '''Update XMR data from the last day'''

    try:
        coin_xmr = list(Coin.objects.filter(name='xmr').order_by('-date'))[0]
    except Exception as error:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)
        print(f'Error during XMR updates: {error}', flush=True)

    get_history_function('xmr', yesterday, yesterday)
    await update_xmr_data(yesterday, coin_xmr)

    return None

def check_competitors_for_updates(yesterday) -> bool:
    '''Check if it is necessary to update non-XMR coin data'''
    try:
        coin_btc = list(Coin.objects.filter(name='btc').filter(date=yesterday))[0]
        coin_zec = list(Coin.objects.filter(name='zec').filter(date=yesterday))[0]
        coin_dash = list(Coin.objects.filter(name='dash').filter(date=yesterday))[0]
        coin_grin = list(Coin.objects.filter(name='grin').filter(date=yesterday))[0]

        if coin_btc and coin_zec and coin_dash and coin_grin:
            print('coins found yesterday', flush=True)
            if coin_btc.transactions > 0 and coin_btc.inflation > 0 and coin_zec.supply > 0 and coin_dash.supply > 0 and coin_grin.supply > 0:
                print('no need to update coins', flush=True)
            else:
                print('will update coins', flush=True)
                coin_btc.delete()
                coin_zec.delete()
                coin_dash.delete()
                coin_grin.delete()
                return True
        else:
            print('no coins found yesterday - 1', flush=True)
            return True
    except Exception as error:
        print(f'no coins found yesterday: {error}', flush=True)
        return True

    return False

async def competitors_updates(yesterday):
    '''Update data from non-XMR coins'''

    await update_others_data(yesterday)

def check_daily_objects_for_updates(yesterday) -> bool:
    '''Check if recent data in the database is present'''

    try:
        data = list(DailyData.objects.filter(date=yesterday))[0]
        if data:
            print('data found yesterday', flush=True)
        else:
            print('no data found yesterday - 1', flush=True)
            return True
    except:
        print('no data found yesterday - 2', flush=True)
        return True

    return False

def daily_objects_updates(yesterday):
    '''Update database with recent data'''

    update_database(yesterday, yesterday)

def populate_database():
    '''Populate database with specific chart variables'''

    count = 0

    ###################################################################
    # SF model charts
    ###################################################################
    print('Populating database for sfmodel.html, sfmodelin.html and pricesats.html, wait a moment...', flush=True)
    Sfmodel.objects.all().delete()
    timevar = 1283
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    previous_supply = 0
    supply = 0
    sf_aux = 0
    count_aux = 0

    print('Populating XMR coin', flush=True)

    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        if coin.priceusd < 0.1:
            coin.priceusd = 0.1
            coin.pricebtc = 0.000001
        if coin.stocktoflow > sf_aux*1.3+100:
            coin.stocktoflow = sf_aux

        sf_aux = coin.stocktoflow
        if coin.supply > 0:
            supply = int(coin.supply)*10**12
        else:
            supply = previous_supply
        count += 1
        count_aux += 1

        data = Sfmodel()
        data.date = coin.date
        data.priceusd = coin.priceusd
        data.pricebtc = coin.pricebtc
        data.stocktoflow = coin.stocktoflow
        data.color = 30*coin.pricebtc/(count*delta + v0)
        date_aux1 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux2 < date_aux1:
            lastprice = coin.priceusd
            current_inflation = coin.inflation
            data.greyline = 0
            count_aux = 0
        else:
            day = date_aux2 - timedelta(timevar)
            coin_aux1 = Coin.objects.filter(name='xmr').get(date=day)
            day = date_aux2 - timedelta(timevar+1)
            coin_aux2 = Coin.objects.filter(name='xmr').get(date=day)
            date_aux3 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')

            if date_aux3 + timedelta(int(count_aux*2)) < datetime.datetime.strptime('2021-07-03', '%Y-%m-%d'):
                day = date_aux3 + timedelta(int(count_aux*2))
                coin_aux3 = Coin.objects.filter(name='xmr').get(date=day)
                if coin_aux3:
                    if (coin_aux3.inflation/current_inflation) > 1.2 or (coin_aux3.inflation/current_inflation) < 0.8:
                        coin_aux3.inflation = current_inflation
                    else:
                        current_inflation = coin_aux3.inflation
                supply2 = supply
            else:
                reward2 = (2**64 -1 - supply2) >> 19
                if reward2 < 0.6*(10**12):
                    reward2 = 0.6*(10**12)
                supply2 += int(720*reward2)
                current_inflation = 100*reward2*720*365/supply2

            if coin_aux1 and coin_aux2:
                lastprice += (coin_aux1.priceusd/coin_aux2.priceusd-1)*lastprice
                actualprice = lastprice*(math.sqrt(coin.inflation/current_inflation))
                data.greyline = actualprice
            else:
                data.greyline = 0
            previous_supply = supply
        data.save()
    count_aux = 0
    for count_aux in range(700):
        date_now = date.today() + timedelta(count_aux)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)

        data = Sfmodel()
        data.date = datetime.datetime.strftime(date_now, '%Y-%m-%d')
        data.stocktoflow = (100/(100*reward*720*365/supply))**1.65
        data.priceusd = 0
        data.pricebtc = 0
        data.greyline = 0
        data.color = 0
        data.priceusd = 0
        data.greyline = 0
        data.save()
        count += 1

    ###################################################################
    # Daily Emissions, inflation charts and coins against bitcoin
    ###################################################################
    print('Populating database for dailyemission.html and dailyemissionntv.html, wait a moment...')
    DailyData.objects.all().delete()
    supply_btc = 0
    supply_xmr = 0
    count_aux = 0
    coins_btc = Coin.objects.order_by('date').filter(name='btc')
    for coin_btc in coins_btc:
        count_aux += 1
        data = DailyData()
        data.date = datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d')

        if coin_btc.blocksize > 0:
            data.btc_blocksize = coin_btc.blocksize
            data.btc_transactions = coin_btc.transactions
        else:
            data.btc_blocksize = 0
            data.btc_transactions = 0

        if coin_btc.difficulty > 0:
            data.btc_difficulty = coin_btc.difficulty
        else:
            data.btc_difficulty = 0

        if coin_btc.transactions == 0:
            data.btc_transcostusd = 0
            data.btc_transcostntv = 0
        else:
            if coin_btc.fee*coin_btc.priceusd/coin_btc.transactions < 0.0001:
                data.btc_transcostusd = 0
                data.btc_transcostntv = 0
            else:
                data.btc_transcostusd = coin_btc.fee*coin_btc.priceusd/coin_btc.transactions
                data.btc_transcostntv = coin_btc.fee/coin_btc.transactions

        if coin_btc.revenue < 0.000001 or coin_btc.priceusd < 0.001:
            data.btc_minerrevntv = 0
            data.btc_minerrevusd = 0
            data.btc_commitntv = 0
            data.btc_commitusd = 0
            data.btc_priceusd = 0
            data.btc_marketcap = 0
        else:
            data.btc_minerrevntv = coin_btc.revenue
            data.btc_minerrevusd = coin_btc.revenue*coin_btc.priceusd
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.btc_priceusd = coin_btc.priceusd
            data.btc_marketcap = coin_btc.priceusd*coin_btc.supply

        if coin_btc.supply == 0:
            data.btc_minerrevcap = 0
        else:
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply

        if coin_btc.priceusd:
            if coin_btc.priceusd/30 > 0.02:
                data.btc_return = coin_btc.priceusd/30
            else:
                data.btc_return = 0
        else:
            data.btc_return = 0

        if coin_btc.inflation > 0:
            data.btc_inflation = coin_btc.inflation
        else:
            data.btc_inflation = 0
        if coin_btc.supply > 0:
            data.btc_supply = coin_btc.supply
        else:
            data.btc_supply = 0

        if coin_btc.supply - supply_btc < 0.000001:
            data.btc_minerfeesntv = 0
            data.btc_minerfeesusd = 0
            data.btc_emissionntv = 0
        else:
            data.btc_minerfeesntv = coin_btc.revenue - coin_btc.supply + supply_btc
            data.btc_minerfeesusd = (coin_btc.revenue - coin_btc.supply + supply_btc)*coin_btc.priceusd
            data.btc_emissionntv = coin_btc.supply -  supply_btc

        if (coin_btc.supply - supply_btc)*coin_btc.priceusd < 1000:
            data.btc_emissionusd = 0
        else:
            data.btc_emissionusd = (coin_btc.supply - supply_btc)*coin_btc.priceusd
        supply_btc = coin_btc.supply
        if count_aux > 1750:
            coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
            if coins_xmr:
                for coin_xmr in coins_xmr:
                    if coin_xmr.blocksize > 0:
                        data.xmr_blocksize = coin_xmr.blocksize
                    else:
                        data.xmr_blocksize = 0

                    if coin_xmr.difficulty > 0:
                        data.xmr_difficulty = coin_xmr.difficulty
                    else:
                        data.xmr_difficulty = 0

                    if coin_xmr.priceusd < 0.001:
                        data.xmr_pricebtc = 0
                        data.xmr_priceusd = 0
                        data.xmr_marketcap = 0
                    else:
                        data.xmr_pricebtc = coin_xmr.pricebtc
                        data.xmr_priceusd = coin_xmr.priceusd
                        data.xmr_marketcap = coin_xmr.priceusd*coin_xmr.supply

                    if coin_btc.supply > 0 and coin_btc.transactions > 0:
                        data.xmr_transactions = coin_xmr.transactions
                        data.xmr_metcalfeusd = coin_btc.priceusd*coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                        data.xmr_metcalfebtc = coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                    else:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0
                        data.xmr_transactions = 0
                    if data.xmr_metcalfeusd < 0.23:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0

                    if coin_xmr.transactions == 0:
                        data.xmr_transacpercentage = 0
                        data.xmr_transcostusd = 0
                        data.xmr_transcostntv = 0
                    else:
                        if coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions < 0.0001:
                            data.xmr_transcostusd = 0
                            data.xmr_transcostntv = 0
                        else:
                            data.xmr_transcostusd = coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions
                            data.xmr_transcostntv = coin_xmr.fee/coin_xmr.transactions
                        if coin_btc.transactions == 0:
                            data.xmr_transacpercentage = 0
                        else:
                            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions

                    if coin_xmr.revenue < 0.000001 or coin_xmr.priceusd < 0.001:
                        data.xmr_minerrevntv = 0
                        data.xmr_minerrevusd = 0
                        data.xmr_commitntv = 0
                        data.xmr_commitusd = 0
                    else:
                        data.xmr_minerrevntv = coin_xmr.revenue
                        data.xmr_minerrevusd = coin_xmr.revenue*coin_xmr.priceusd
                        data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
                        data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)

                    if coin_xmr.supply == 0:
                        data.xmr_minerrevcap = 0
                    else:
                        data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply

                    if coin_xmr.priceusd/5.01 > 0.02:
                        data.xmr_return = coin_xmr.priceusd/5.01
                    else:
                        data.xmr_return = 0

                    if coin_xmr.inflation > 0:
                        data.xmr_inflation = coin_xmr.inflation
                    else:
                        data.xmr_inflation = 0

                    if coin_xmr.supply > 0:
                        data.xmr_supply = coin_xmr.supply
                    else:
                        data.xmr_supply = 0

                    if coin_xmr.supply - supply_xmr < 0.000001:
                        data.xmr_minerfeesntv = 0
                        data.xmr_minerfeesusd = 0
                        data.xmr_emissionntv = 0
                    else:
                        data.xmr_minerfeesntv = coin_xmr.revenue - coin_xmr.supply + supply_xmr
                        data.xmr_minerfeesusd = (coin_xmr.revenue - coin_xmr.supply + supply_xmr)*coin_xmr.priceusd
                        data.xmr_emissionntv = coin_xmr.supply - supply_xmr

                    if (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd < 1000:
                        data.xmr_emissionusd = 0
                    else:
                        data.xmr_emissionusd = (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd
                    supply_xmr = coin_xmr.supply
            else:
                data.xmr_emissionntv = 0
                data.xmr_emissionusd = 0
                data.xmr_inflation = 0
                data.xmr_supply = 0
                data.xmr_return = 0
                data.xmr_minerrevntv = 0
                data.xmr_minerrevusd = 0
                data.xmr_minerfeesntv = 0
                data.xmr_minerfeesusd = 0
                data.xmr_transcostntv = 0
                data.xmr_transcostusd = 0
                data.xmr_commitntv = 0
                data.xmr_commitusd = 0
                data.xmr_metcalfeusd = 0
                data.xmr_metcalfebtc = 0
                data.xmr_pricebtc = 0
                data.xmr_priceusd = 0
                data.xmr_transacpercentage = 0
                data.xmr_marketcap = 0
                data.xmr_minerrevcap = 0
                data.xmr_transactions = 0
                data.xmr_blocksize = 0
                data.xmr_difficulty = 0

            coins_dash = Coin.objects.filter(name='dash').filter(date=coin_btc.date)
            if coins_dash:
                for coin_dash in coins_dash:
                    if coin_dash.transactions > 0:
                        data.dash_transactions = coin_dash.transactions
                    else:
                        data.dash_transactions = 0
                    if coin_dash.inflation > 0:
                        data.dash_inflation = coin_dash.inflation
                    else:
                        data.dash_inflation = 0

                    if coin_dash.priceusd > 0:
                        data.dash_marketcap = coin_dash.priceusd*coin_dash.supply
                    else:
                        data.dash_marketcap = 0
            else:
                data.dash_inflation = 0
                data.dash_marketcap = 0
                data.dash_transactions = 0
        else:
            data.xmr_emissionntv = 0
            data.xmr_emissionusd = 0
            data.xmr_inflation = 0
            data.xmr_supply = 0
            data.xmr_return = 0
            data.dash_inflation = 0
            data.dash_marketcap = 0
            data.dash_transactions = 0
            data.xmr_marketcap = 0
            data.xmr_minerrevntv = 0
            data.xmr_minerrevusd = 0
            data.xmr_minerfeesntv = 0
            data.xmr_minerfeesusd = 0
            data.xmr_transcostntv = 0
            data.xmr_transcostusd = 0
            data.xmr_commitntv = 0
            data.xmr_commitusd = 0
            data.xmr_metcalfeusd = 0
            data.xmr_metcalfebtc = 0
            data.xmr_pricebtc = 0
            data.xmr_priceusd = 0
            data.xmr_transacpercentage = 0
            data.xmr_minerrevcap = 0
            data.xmr_transactions = 0
            data.xmr_blocksize = 0
            data.xmr_difficulty = 0

        if count_aux > 2800:
            coins_zcash = Coin.objects.filter(name='zec').filter(date=coin_btc.date)
            if coins_zcash:
                for coin_zcash in coins_zcash:
                    if coin_zcash.transactions > 0:
                        data.zcash_transactions = coin_zcash.transactions
                    else:
                        data.zcash_transactions = 0
                    if coin_zcash.inflation > 0:
                        data.zcash_inflation = coin_zcash.inflation
                    else:
                        data.zcash_inflation = 0

                    if coin_zcash.priceusd > 0:
                        data.zcash_marketcap = coin_zcash.priceusd*coin_zcash.supply
                    else:
                        data.zcash_marketcap = 0
            else:
                data.zcash_inflation = 0
                data.zcash_marketcap = 0
                data.zcash_transactions = 0
        else:
            data.zcash_inflation = 0
            data.zcash_marketcap = 0
            data.zcash_transactions = 0

        if count_aux > 3600:
            coins_grin = Coin.objects.filter(name='grin').filter(date=coin_btc.date)
            if coins_grin:
                for coin_grin in coins_grin:
                    if coin_grin.transactions > 0:
                        data.grin_transactions = coin_grin.transactions
                    else:
                        data.grin_transactions = 0
                    if coin_grin.inflation > 0:
                        data.grin_inflation = coin_grin.inflation
                    else:
                        data.grin_inflation = 0

                    if coin_grin.priceusd > 0:
                        data.grin_marketcap = coin_grin.priceusd*coin_grin.supply
                    else:
                        data.grin_marketcap = 0
            else:
                data.grin_inflation = 0
                data.grin_marketcap = 0
                data.grin_transactions = 0
        else:
            data.grin_inflation = 0
            data.grin_marketcap = 0
            data.grin_transactions = 0

        socials = Social.objects.filter(name='Bitcoin').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.btc_subscriber_count = social.subscriber_count
                data.btc_comments_per_hour = social.comments_per_hour
                data.btc_posts_per_hour = social.posts_per_hour
        else:
            data.btc_subscriber_count = 0
            data.btc_comments_per_hour = 0
            data.btc_posts_per_hour = 0

        socials = Social.objects.filter(name='Monero').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.xmr_subscriber_count = social.subscriber_count
                data.xmr_comments_per_hour = social.comments_per_hour
                data.xmr_posts_per_hour = social.posts_per_hour
        else:
            data.xmr_subscriber_count = 0
            data.xmr_comments_per_hour = 0
            data.xmr_posts_per_hour = 0

        socials = Social.objects.filter(name='CryptoCurrency').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.crypto_subscriber_count = social.subscriber_count
                data.crypto_comments_per_hour = social.comments_per_hour
                data.crypto_posts_per_hour = social.posts_per_hour
        else:
            data.crypto_subscriber_count = 0
            data.crypto_comments_per_hour = 0
            data.crypto_posts_per_hour = 0

        data.save()
        count += 1

    message = 'Total of ' + str(count) + ' data generated'
    context = {'message': message}
