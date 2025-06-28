'''Update data functions'''

import math
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist

from charts.models import Coin
from charts.models import Social
from charts.models import DailyData

def update_daily_data_price_information(xmr_data_point, btc_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)
        model.xmr_priceusd = xmr_data_point.priceusd
        model.xmr_pricebtc = xmr_data_point.pricebtc
        model.btc_priceusd = btc_data_point.priceusd

        model.save()

    except Exception as error:
        print(f'[ERROR] Could not update price information: {error}')
        return None

    return model

def update_daily_data_marketcap(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)

        model.xmr_marketcap = float(xmr_data_point.priceusd)*float(xmr_data_point.supply)
        model.btc_marketcap = float(btc_data_point.priceusd)*float(btc_data_point.supply)
        model.dash_marketcap = float(dash_data_point.priceusd)*float(dash_data_point.supply)
        model.zcash_marketcap = float(zcash_data_point.priceusd)*float(zcash_data_point.supply)
        model.grin_marketcap = float(grin_data_point.priceusd)*float(grin_data_point.supply)

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating marketcap information: {error}')
        return None
    return model

def update_daily_data_transactions(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)

        model.xmr_transacpercentage = xmr_data_point.transactions / btc_data_point.transactions

        model.xmr_transactions = xmr_data_point.transactions
        model.btc_transactions = btc_data_point.transactions
        model.dash_transactions = dash_data_point.transactions
        model.zcash_transactions = zcash_data_point.transactions
        model.grin_transactions = grin_data_point.transactions

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating transaction information: {error}')
        return None
    return model

def update_daily_data_issuance(xmr_data_point, btc_data_point, dash_data_point, zcash_data_point, grin_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)

        model.xmr_inflation = xmr_data_point.inflation
        model.btc_inflation = btc_data_point.inflation
        model.dash_inflation = dash_data_point.inflation
        model.zcash_inflation = zcash_data_point.inflation
        model.grin_inflation = grin_data_point.inflation

        model.xmr_metcalfebtc = xmr_data_point.transactions * xmr_data_point.supply / ( btc_data_point.transactions * btc_data_point.supply )
        model.xmr_metcalfeusd = btc_data_point.priceusd * xmr_data_point.transactions * xmr_data_point.supply / ( btc_data_point.transactions * btc_data_point.supply )

        model.xmr_return = xmr_data_point.priceusd / 30
        model.btc_return = btc_data_point.priceusd / 5.01

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating issuance information: {error}')
        return None
    return model

def update_daily_data_emission(xmr_data_point, xmr_previous_data_point, btc_data_point, btc_previous_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)

        model.xmr_emissionusd = ( xmr_data_point.supply - xmr_previous_data_point.supply ) * xmr_data_point.priceusd
        model.xmr_emissionntv = xmr_data_point.supply - xmr_previous_data_point.supply

        model.btc_emissionusd = ( btc_data_point.supply - btc_previous_data_point.supply ) * btc_data_point.priceusd
        model.btc_emissionntv = btc_data_point.supply - btc_previous_data_point.supply

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating mining information: {error}')
        return None
    return model

def update_daily_data_mining(xmr_data_point, xmr_previous_data_point, btc_data_point, btc_previous_data_point):

    try:
        model = DailyData.objects.get(date=xmr_data_point.date)

        model.xmr_minerrevusd = xmr_data_point.revenue * xmr_data_point.priceusd
        model.xmr_minerrevntv = xmr_data_point.revenue
        model.xmr_minerfeesusd = ( xmr_data_point.revenue - xmr_data_point.supply + xmr_previous_data_point.supply ) * xmr_data_point.priceusd
        model.xmr_minerfeesntv = xmr_data_point.revenue - xmr_data_point.supply + xmr_previous_data_point.supply
        model.xmr_transcostusd = xmr_data_point.priceusd * xmr_data_point.fee / xmr_data_point.transactions
        model.xmr_transcostntv = xmr_data_point.fee / xmr_data_point.transactions
        model.xmr_minerrevcap = 365 * 100 * xmr_data_point.revenue / xmr_data_point.supply
        model.xmr_commitusd = xmr_data_point.hashrate / ( xmr_data_point.revenue * xmr_data_point.priceusd )
        model.xmr_commitntv = xmr_data_point.hashrate / xmr_data_point.revenue
        model.xmr_blocksize = xmr_data_point.blocksize
        model.xmr_difficulty = xmr_data_point.difficulty

        model.btc_minerrevusd = btc_data_point.revenue * btc_data_point.priceusd
        model.btc_minerrevntv = btc_data_point.revenue
        model.btc_minerfeesusd = ( btc_data_point.revenue - btc_data_point.supply + btc_previous_data_point.supply ) * btc_data_point.priceusd
        model.btc_minerfeesntv = btc_data_point.revenue - btc_data_point.supply + btc_previous_data_point.supply
        model.btc_transcostusd = btc_data_point.priceusd * btc_data_point.fee / btc_data_point.transactions
        model.btc_transcostntv = btc_data_point.fee / btc_data_point.transactions
        model.btc_minerrevcap = 365 * 100 * btc_data_point.revenue / btc_data_point.supply
        model.btc_commitusd = btc_data_point.hashrate / ( btc_data_point.revenue * btc_data_point.priceusd )
        model.btc_commitntv = btc_data_point.hashrate / btc_data_point.revenue
        model.btc_blocksize = btc_data_point.blocksize
        model.btc_difficulty = btc_data_point.difficulty

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating mining information: {error}')
        return None
    return model

def update_daily_data_social(social_xmr, social_btc, social_crypto):

    try:
        model = DailyData.objects.get(date=data_point.date)

        model.xmr_subscriber_count = social_xmr.subscriber_count
        model.xmr_comments_per_hour = social_xmr.comments_per_hour
        model.xmr_posts_per_hour = social_xmr_posts_per_hour

        model.btc_subscriber_count = social_btc.subscriber_count
        model.btc_comments_per_hour = social_btc.comments_per_hour
        model.btc_posts_per_hour = social_btc_posts_per_hour

        model.crypto_subscriber_count = social_crypto.subscriber_count
        model.crypto_comments_per_hour = social_crypto.comments_per_hour
        model.crypto_posts_per_hour = social_crypto_posts_per_hour

        model.save()
    except Exception as error:
        print(f'[ERROR] Something went wrong updating social information: {error}')
        return None
    return model

def calculate_daily_data():
    '''Reset and recalculate the Daily Data model'''

    objects = DailyData.objects.count()

    if objects > 0:
        print(f'[ERROR] Daily data already present, erase all data before proceeding.')
        return False

    supply_btc = 0
    supply_xmr = 0
    count = 0
    count_aux = 0
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    for coin_btc in coins_btc:
        count_aux += 1
        data = DailyData()
        data.date = datetime.strftime(coin_btc.date, '%Y-%m-%d')

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

    return True
