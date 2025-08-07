'''Views module'''

import locale

from datetime import date
from datetime import datetime

from django.shortcuts import render

from charts.models import Coin
from charts.models import DailyData
from charts.models import P2Pool

locale.setlocale(locale.LC_ALL, 'en_US.utf8')


def hashrate(request):
    '''Monero's Hashrate'''

    symbol = 'xmr'
    hashrate = []
    dates = []
    now_hashrate = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        coin.date = datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)
        if coin.hashrate > 0:
            now_hashrate = coin.hashrate
            hashrate.append(coin.hashrate)
        else:
            hashrate.append('')

    now_hashrate = locale._format('%.0f', now_hashrate, grouping=True)

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate}
    return render(request, 'charts/hashrate.html', context)

def hashprice(request):
    '''Price in Dollars Per Hashrate'''

    symbol = 'xmr'
    hashrate = []
    dates = []
    buy = []
    sell = []
    now_hashrate = 0
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if count > 50:
            buy.append(0.00000003)
            sell.append(0.00000100)
            coin.date = datetime.strftime(coin.date, '%Y-%m-%d')
            dates.append(coin.date)
            if coin.hashrate > 0 and coin.priceusd > 0:
                now_hashrate = coin.priceusd/coin.hashrate
                hashrate.append(now_hashrate)
            else:
                hashrate.append('')
            new_color = 30*coin.pricebtc/(count*delta + v0)
            color.append(new_color)
        count += 1

    now_hashrate = locale._format('%.8f', now_hashrate, grouping=True)

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'buy': buy, 'sell': sell}
    return render(request, 'charts/hashprice.html', context)

def hashvsprice(request):
    ''' Price Versus Hashrate (Dollars)'''

    symbol = 'xmr'
    hashrate = []
    prices = []
    dates = []
    now_hashrate = 0
    now_priceusd = 0
    now_pricebtc = 0
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if count > 55:
            coin.date = datetime.strftime(coin.date, '%Y-%m-%d')
            dates.append(coin.date)
            if coin.priceusd > 0 and coin.hashrate:
                now_hashrate = coin.hashrate
                now_priceusd = coin.priceusd
                now_pricebtc = coin.pricebtc
                hashrate.append(now_hashrate)
                prices.append(now_priceusd)
            else:
                hashrate.append('')
                prices.append('')
            new_color = 30*coin.pricebtc/(count*delta + v0)
            color.append(new_color)
        count += 1

    now_hashrate = locale._format('%.0f', now_hashrate, grouping=True)
    now_priceusd = '$' + locale._format('%.2f', now_priceusd, grouping=True)
    now_pricebtc = locale._format('%.5f', now_pricebtc, grouping=True) + ' BTC'

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'prices': prices, 'now_pricebtc': now_pricebtc, 'now_priceusd': now_priceusd}
    return render(request, 'charts/hashvsprice.html', context)

def minerrev(request):
    '''Miner Revenue (Dollars / day)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_revenue = 0
    btc_miner_revenue_difference = 0
    now_btc = 0

    previous_xmr_miner_revenue = 0
    xmr_miner_revenue_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_revenue = data[item].btc_minerrevusd
        xmr_miner_revenue = data[item].xmr_minerrevusd

        if item > 0:
            previous_btc_miner_revenue = data[item-1].btc_minerrevusd
            previous_xmr_miner_revenue = data[item-1].xmr_minerrevusd

        if btc_miner_revenue > 0:
            btc_miner_revenue_difference = ( btc_miner_revenue - previous_btc_miner_revenue ) / btc_miner_revenue * 100

        if xmr_miner_revenue > 0:
            xmr_miner_revenue_difference = ( xmr_miner_revenue - previous_xmr_miner_revenue ) / xmr_miner_revenue * 100

        if btc_miner_revenue_difference < 10:
            if previous_btc_miner_revenue < 15:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_revenue)
                now_btc = btc_miner_revenue
        else:
            costbtc.append(btc_miner_revenue)
            now_btc = btc_miner_revenue

        if xmr_miner_revenue_difference < 10:
            if previous_xmr_miner_revenue < 15:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_revenue)
                now_xmr = xmr_miner_revenue
        else:
            costxmr.append(xmr_miner_revenue)
            now_xmr = xmr_miner_revenue

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrev.html', context)

def minerrevntv(request):
    '''Daily Miner Revenue (Fees plus new coins, Native Units / day)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_revenue = 0
    btc_miner_revenue_difference = 0
    now_btc = 0

    previous_xmr_miner_revenue = 0
    xmr_miner_revenue_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_revenue = data[item].btc_minerrevntv
        xmr_miner_revenue = data[item].xmr_minerrevntv

        if item > 0:
            previous_btc_miner_revenue = data[item-1].btc_minerrevntv
            previous_xmr_miner_revenue = data[item-1].xmr_minerrevntv

        if btc_miner_revenue > 0:
            btc_miner_revenue_difference = ( btc_miner_revenue - previous_btc_miner_revenue ) / btc_miner_revenue * 100

        if xmr_miner_revenue > 0:
            xmr_miner_revenue_difference = ( xmr_miner_revenue - previous_xmr_miner_revenue ) / xmr_miner_revenue * 100

        if btc_miner_revenue_difference < 10:
            if previous_btc_miner_revenue < 50:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_revenue)
                now_btc = btc_miner_revenue
        else:
            costbtc.append(btc_miner_revenue)
            now_btc = btc_miner_revenue

        if xmr_miner_revenue_difference < 10:
            if previous_xmr_miner_revenue < 50:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_revenue)
                now_xmr = xmr_miner_revenue
        else:
            costxmr.append(xmr_miner_revenue)
            now_xmr = xmr_miner_revenue

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevntv.html', context)

def minerfees(request):
    '''Miner Fees (Fees excluded new coins, Dollars)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_fees = 0
    btc_miner_fees_difference = 0
    now_btc = 0

    previous_xmr_miner_fees = 0
    xmr_miner_fees_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_fees = data[item].btc_minerfeesusd
        xmr_miner_fees = data[item].xmr_minerfeesusd

        if item > 0:
            previous_btc_miner_fees = data[item-1].btc_minerfeesusd
            previous_xmr_miner_fees = data[item-1].xmr_minerfeesusd

        if btc_miner_fees > 0:
            btc_miner_fees_difference = ( btc_miner_fees - previous_btc_miner_fees ) / btc_miner_fees * 100

        if xmr_miner_fees > 0:
            xmr_miner_fees_difference = ( xmr_miner_fees - previous_xmr_miner_fees ) / xmr_miner_fees * 100

        if btc_miner_fees_difference < 0:
            if previous_btc_miner_fees < 1:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_fees)
                now_btc = btc_miner_fees
        elif btc_miner_fees_difference >= 8:
            if previous_btc_miner_fees < 1:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_fees)
                now_btc = btc_miner_fees
        else:
            costbtc.append(btc_miner_fees)
            now_btc = btc_miner_fees

        if xmr_miner_fees_difference < 0:
            if previous_xmr_miner_fees < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_fees)
                now_xmr = xmr_miner_fees
        elif xmr_miner_fees_difference >= 8:
            if previous_xmr_miner_fees < 10:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_fees)
                now_xmr = xmr_miner_fees
        else:
            costxmr.append(xmr_miner_fees)
            now_xmr = xmr_miner_fees

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfees.html', context)

def minerfeesntv(request):
    '''Miner Fees (Fees excluded new coins, Native Units)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_fees = 0
    btc_miner_fees_difference = 0
    now_btc = 0

    previous_xmr_miner_fees = 0
    xmr_miner_fees_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_fees = data[item].btc_minerfeesntv
        xmr_miner_fees = data[item].xmr_minerfeesntv

        if item > 0:
            previous_btc_miner_fees = data[item-1].btc_minerfeesntv
            previous_xmr_miner_fees = data[item-1].xmr_minerfeesntv

        if btc_miner_fees > 0:
            btc_miner_fees_difference = ( btc_miner_fees - previous_btc_miner_fees ) / btc_miner_fees * 100

        if xmr_miner_fees > 0:
            xmr_miner_fees_difference = ( xmr_miner_fees - previous_xmr_miner_fees ) / xmr_miner_fees * 100

        if btc_miner_fees_difference < 0:
            if previous_btc_miner_fees < 1:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_fees)
                now_btc = btc_miner_fees
        elif btc_miner_fees_difference >= 10:
            if previous_btc_miner_fees < 1:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_fees)
                now_btc = btc_miner_fees
        else:
            costbtc.append(btc_miner_fees)
            now_btc = btc_miner_fees

        if xmr_miner_fees_difference < 0:
            if previous_xmr_miner_fees < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_fees)
                now_xmr = xmr_miner_fees
        elif xmr_miner_fees_difference >= 1:
            if previous_xmr_miner_fees < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_fees)
                now_xmr = xmr_miner_fees
        else:
            costxmr.append(xmr_miner_fees)
            now_xmr = xmr_miner_fees

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfeesntv.html', context)

def miningprofitability(request):
    '''Monero Mining Profitability (USD/day for 1 KHash/s)'''

    dates = []
    value = []
    now_value = 0
    previous_value = 0
    difference = 0

    data = Coin.objects.order_by('date').filter(name='xmr')

    for item in range(len(data)):

        dates.append(datetime.strftime(data[item].date, '%Y-%m-%d'))

        hashrate = data[item].hashrate
        price = data[item].priceusd
        revenue = data[item].revenue

        if hashrate > 0 and price > 0 and revenue > 0:

            now_value = 1000 * price * revenue / hashrate

            if now_value < 0.01:
                value.append('')
            else:
                value.append(now_value)

    context = {'value': value, 'dates': dates}
    return render(request, 'charts/miningprofitability.html', context)

def minerrevcap(request):
    '''Annualized Miner Revenue / Marketcap (Fees plus new coins, percentage)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_revenue = 0
    btc_miner_revenue_difference = 0
    now_btc = 0

    previous_xmr_miner_revenue = 0
    xmr_miner_revenue_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_revenue = data[item].btc_minerrevcap
        xmr_miner_revenue = data[item].xmr_minerrevcap

        if item > 0:
            previous_btc_miner_revenue = data[item-1].btc_minerrevcap
            previous_xmr_miner_revenue = data[item-1].xmr_minerrevcap

        if btc_miner_revenue > 0:
            btc_miner_revenue_difference = ( btc_miner_revenue - previous_btc_miner_revenue ) / btc_miner_revenue * 100

        if xmr_miner_revenue > 0:
            xmr_miner_revenue_difference = ( xmr_miner_revenue - previous_xmr_miner_revenue ) / xmr_miner_revenue * 100

        if btc_miner_revenue_difference < 10000:
            if previous_btc_miner_revenue < 0.7:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_revenue)
                now_btc = btc_miner_revenue
        elif btc_miner_revenue_difference >= 1000:
            if previous_btc_miner_revenue < 0:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_revenue)
                now_btc = btc_miner_revenue
        else:
            costbtc.append(btc_miner_revenue)
            now_btc = btc_miner_revenue

        if xmr_miner_revenue_difference < 10000:
            if previous_xmr_miner_revenue < 0.7:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_revenue)
                now_xmr = xmr_miner_revenue
        elif xmr_miner_revenue_difference >= 1000:
            if previous_xmr_miner_revenue < 0:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_revenue)
                now_xmr = xmr_miner_revenue
        else:
            costxmr.append(xmr_miner_revenue)
            now_xmr = xmr_miner_revenue

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevcap.html', context)

def commit(request):
    '''Miner Commitment (Hashrate divided by revenue, hashs/dollar) - WARNING: DON'T COMPARE DIRECTLY BOTH COINS'''
    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_commitment = 0
    btc_miner_commitment_difference = 0
    now_btc = 0

    previous_xmr_miner_commitment = 0
    xmr_miner_commitment_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_commitment = data[item].btc_commitusd
        xmr_miner_commitment = data[item].xmr_commitusd

        if item > 0:
            previous_btc_miner_commitment = data[item-1].btc_commitusd
            previous_xmr_miner_commitment = data[item-1].xmr_commitusd

        if btc_miner_commitment > 0:
            btc_miner_commitment_difference = ( btc_miner_commitment - previous_btc_miner_commitment ) / btc_miner_commitment * 100

        if xmr_miner_commitment > 0:
            xmr_miner_commitment_difference = ( xmr_miner_commitment - previous_xmr_miner_commitment ) / xmr_miner_commitment * 100

        if btc_miner_commitment_difference < 1:
            if previous_btc_miner_commitment < 0.000001:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_commitment)
                now_btc = btc_miner_commitment
        elif btc_miner_commitment_difference >= 0.0000001:
            if previous_btc_miner_commitment < 0.000001:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_commitment)
                now_btc = btc_miner_commitment
        else:
            costbtc.append(btc_miner_commitment)
            now_btc = btc_miner_commitment

        if xmr_miner_commitment_difference > 0:
            if previous_xmr_miner_commitment < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_commitment)
                now_xmr = xmr_miner_commitment
        elif xmr_miner_commitment_difference >= 0:
            if previous_xmr_miner_commitment < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_commitment)
                now_xmr = xmr_miner_commitment
        else:
            costxmr.append(xmr_miner_commitment)
            now_xmr = xmr_miner_commitment

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commit.html', context)

def commitntv(request):
    '''Miner Commitment (Hashrate divided by revenue, hashs/coin) - WARNING: DON'T COMPARE DIRECTLY BOTH COINS'''
    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []

    previous_btc_miner_commitment = 0
    btc_miner_commitment_difference = 0
    now_btc = 0

    previous_xmr_miner_commitment = 0
    xmr_miner_commitment_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_miner_commitment = data[item].btc_commitntv
        xmr_miner_commitment = data[item].xmr_commitntv

        if item > 0:
            previous_btc_miner_commitment = data[item-1].btc_commitntv
            previous_xmr_miner_commitment = data[item-1].xmr_commitntv

        if btc_miner_commitment > 0:
            btc_miner_commitment_difference = ( btc_miner_commitment - previous_btc_miner_commitment ) / btc_miner_commitment * 100

        if xmr_miner_commitment > 0:
            xmr_miner_commitment_difference = ( xmr_miner_commitment - previous_xmr_miner_commitment ) / xmr_miner_commitment * 100

        if btc_miner_commitment_difference < 1:
            if previous_btc_miner_commitment < 0.000001:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_commitment)
                now_btc = btc_miner_commitment
        elif btc_miner_commitment_difference >= 0.0000001:
            if previous_btc_miner_commitment < 0.000001:
                costbtc.append('')
            else:
                costbtc.append(previous_btc_miner_commitment)
                now_btc = btc_miner_commitment
        else:
            costbtc.append(btc_miner_commitment)
            now_btc = btc_miner_commitment

        if xmr_miner_commitment_difference > 0:
            if previous_xmr_miner_commitment < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_commitment)
                now_xmr = xmr_miner_commitment
        elif xmr_miner_commitment_difference >= 0:
            if previous_xmr_miner_commitment < 1:
                costxmr.append('')
            else:
                costxmr.append(previous_xmr_miner_commitment)
                now_xmr = xmr_miner_commitment
        else:
            costxmr.append(xmr_miner_commitment)
            now_xmr = xmr_miner_commitment

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commitntv.html', context)

def blocksize(request):
    '''Average Block Size for both Monero and Bitcoin (KB)'''

    data = DailyData.objects.order_by('date')

    blocksize_xmr = []
    blocksize_btc = []
    dates = []

    previous_btc_blocksize = 0
    btc_blocksize_difference = 0
    now_btc = 0

    previous_xmr_blocksize = 0
    xmr_blocksize_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_blocksize = data[item].btc_blocksize / 1024
        xmr_blocksize = data[item].xmr_blocksize / 1024

        if item > 0:
            previous_btc_blocksize = data[item-1].btc_blocksize / 1024
            previous_xmr_blocksize = data[item-1].xmr_blocksize / 1024

        if btc_blocksize > 0:
            btc_blocksize_difference = ( btc_blocksize - previous_btc_blocksize ) / btc_blocksize * 100

        if xmr_blocksize > 0:
            xmr_blocksize_difference = ( xmr_blocksize - previous_xmr_blocksize ) / xmr_blocksize * 100

        ## Bitcoin blocksize
        if btc_blocksize_difference < 1:
            if previous_btc_blocksize < 0.5:
                blocksize_btc.append('')
            else:
                blocksize_btc.append(previous_btc_blocksize)
                now_btc = btc_blocksize
        elif btc_blocksize_difference >= 0:
            if previous_btc_blocksize < 0:
                blocksize_btc.append('')
            else:
                blocksize_btc.append(previous_btc_blocksize)
                now_btc = btc_blocksize
        else:
            blocksize_btc.append(btc_blocksize)
            now_btc = btc_blocksize

        ## Monero blocksize
        if xmr_blocksize_difference < 1:
            if previous_xmr_blocksize < 1:
                blocksize_xmr.append('')
            else:
                blocksize_xmr.append(previous_xmr_blocksize)
                now_xmr = xmr_blocksize
        elif xmr_blocksize_difference >= 0:
            if previous_xmr_blocksize < 1:
                blocksize_xmr.append('')
            else:
                blocksize_xmr.append(previous_xmr_blocksize)
                now_xmr = xmr_blocksize
        else:
            blocksize_xmr.append(xmr_blocksize)
            now_xmr = xmr_blocksize

    context = {'xmr_blocksize': blocksize_xmr, 'btc_blocksize': blocksize_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/blocksize.html', context)

def blockchainsize(request):
    '''Total Blockchain Size for Monero and Bitcoin (KB)'''
    data = DailyData.objects.order_by('date')

    xmr_blocksize = []
    btc_blocksize = []
    dates = []
    now_xmr = 0
    now_btc = 0
    hardfork = datetime.strptime('2016-03-23', '%Y-%m-%d') #block time changed here

    for item in data:
        date = datetime.strftime(item.date, '%Y-%m-%d')
        dates.append(date)
        date = datetime.strptime(date, '%Y-%m-%d')

        if item.btc_blocksize > 0.001 and item.btc_transactions > 0:
            now_btc += 144*item.btc_blocksize/1024
            if now_btc < 200:
                btc_blocksize.append('')
            else:
                btc_blocksize.append(now_btc)
        else:
            btc_blocksize.append('')

        if item.xmr_blocksize > 0.001 and item.xmr_transactions > 0:
            if date < hardfork:
                now_xmr += 1440*item.xmr_blocksize/1024
            else:
                now_xmr += 720*item.xmr_blocksize/1024

            if now_xmr < 200:
                xmr_blocksize.append('')
            else:
                xmr_blocksize.append(now_xmr)
        else:
            xmr_blocksize.append('')

    now_btc = locale._format('%.2f', now_btc/(1024*1024), grouping=True) + ' Gb'
    now_xmr = locale._format('%.2f', now_xmr/(1024*1024), grouping=True) + ' Gb'

    context = {'xmr_blocksize': xmr_blocksize, 'btc_blocksize': btc_blocksize, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/blockchainsize.html', context)

def transactionsize(request):
    '''Average Transaction Size for both Monero and Bitcoin (KB)'''

    data = DailyData.objects.order_by('date')

    transactionsize_xmr = []
    transactionsize_btc = []
    dates = []

    btc_transactionsize = 1
    previous_btc_transactionsize = 0
    btc_transactionsize_difference = 0
    now_btc = 0

    xmr_transactionsize = 1
    previous_xmr_transactionsize = 0
    xmr_transactionsize_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        if data[item].btc_transactions > 0:
            btc_transactionsize = (144 * data[item].btc_blocksize) / (data[item].btc_transactions * 1024)
        if data[item].xmr_transactions > 0:
            xmr_transactionsize = (720 * data[item].xmr_blocksize) / (data[item].xmr_transactions * 1024)

        if item > 0:
            if data[item-1].btc_transactions > 0:
                previous_btc_transactionsize = (144 * data[item-1].btc_blocksize) / (data[item-1].btc_transactions * 1024)
            if data[item-1].xmr_transactions > 0:
                previous_xmr_transactionsize = (720 * data[item-1].xmr_blocksize) / (data[item-1].xmr_transactions * 1024)

        if btc_transactionsize > 0:
            btc_transactionsize_difference = ( btc_transactionsize - previous_btc_transactionsize ) / btc_transactionsize * 100

        if xmr_transactionsize > 0:
            xmr_transactionsize_difference = ( xmr_transactionsize - previous_xmr_transactionsize ) / xmr_transactionsize * 100

        ## Bitcoin transactionsize
        if btc_transactionsize_difference < -100:
            if previous_btc_transactionsize < 10:
                transactionsize_btc.append(previous_btc_transactionsize)
                now_btc = btc_transactionsize
            else:
                transactionsize_btc.append('')
        elif btc_transactionsize_difference >= 0:
            if previous_btc_transactionsize > 10:
                transactionsize_btc.append(previous_btc_transactionsize)
                now_btc = btc_transactionsize
            else:
                transactionsize_btc.append('')
        else:
            transactionsize_btc.append(btc_transactionsize)
            now_btc = btc_transactionsize

        ## Monero transactionsize
        if xmr_transactionsize_difference < -100:
            if previous_xmr_transactionsize < 10:
                transactionsize_xmr.append(previous_xmr_transactionsize)
                now_xmr = xmr_transactionsize
            else:
                transactionsize_xmr.append('')

        elif xmr_transactionsize_difference >= 0:
            if previous_xmr_transactionsize > 10:
                transactionsize_xmr.append(previous_xmr_transactionsize)
                now_xmr = xmr_transactionsize
            else:
                transactionsize_xmr.append('')
        else:
            transactionsize_xmr.append(xmr_transactionsize)
            now_xmr = xmr_transactionsize

    context = {'xmr_blocksize': transactionsize_xmr, 'btc_blocksize': transactionsize_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transactionsize.html', context)

def difficulty(request):
    '''Mining Difficulty'''
    data = DailyData.objects.order_by('date')

    xmr_difficulty = []
    btc_difficulty = []
    dates = []
    now_xmr = 0
    now_btc = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_difficulty > 0.001:
            now_btc = item.btc_difficulty
            btc_difficulty.append(now_btc)
        else:
            btc_difficulty.append('')

        if item.xmr_difficulty > 0.001:
            now_xmr = item.xmr_difficulty
            xmr_difficulty.append(now_xmr)
        else:
            xmr_difficulty.append('')

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)

    context = {'xmr_difficulty': xmr_difficulty, 'btc_difficulty': btc_difficulty, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/difficulty.html', context)

def securitybudget(request):
    '''Security Budget for Monero and Bitcoin (Dollars/second)'''
    data = DailyData.objects.order_by('date')

    security_xmr = []
    security_btc = []
    dates = []

    previous_btc_security = 0
    btc_security_difference = 0
    now_btc = 0

    previous_xmr_security = 0
    xmr_security_difference = 0
    now_xmr = 0

    for item in range(len(data)):

        item_date = data[item].date
        dates.append(datetime.strftime(item_date, '%Y-%m-%d'))

        btc_security = data[item].btc_minerrevusd / 86400
        xmr_security = data[item].xmr_minerrevusd / 86400

        if item > 0:
            previous_btc_security = data[item-1].btc_minerrevusd / 86400
            previous_xmr_security = data[item-1].xmr_minerrevusd / 86400

        if btc_security > 0:
            btc_security_difference = ( btc_security - previous_btc_security ) / btc_security * 100

        if xmr_security > 0:
            xmr_security_difference = ( xmr_security - previous_xmr_security ) / xmr_security * 100

        ## Bitcoin security
        if btc_security_difference < 0:
            if previous_btc_security < 0:
                security_btc.append('')
            else:
                security_btc.append(previous_btc_security)
                now_btc = btc_security
        elif btc_security_difference >= 0:
            if previous_btc_security > 50:
                security_btc.append('')
            else:
                security_btc.append(previous_btc_security)
                now_btc = btc_security
        else:
            security_btc.append(btc_security)
            now_btc = btc_security

        ## Monero security
        if xmr_security_difference < 0:
            if previous_xmr_security < 0:
                print(f'[DEBUG] A - {item_date}: {xmr_security_difference}', flush=True)
                security_xmr.append('')
            else:
                print(f'[DEBUG] B - {item_date}: {xmr_security_difference}', flush=True)
                security_xmr.append(previous_xmr_security)
                now_xmr = xmr_security

        elif xmr_security_difference >= 0:
            if previous_xmr_security < 50:
                print(f'[DEBUG] C - {item_date}: {xmr_security_difference}', flush=True)
                security_xmr.append('')
            else:
                print(f'[DEBUG] D - {item_date}: {xmr_security_difference}', flush=True)
                security_xmr.append(previous_xmr_security)
                now_xmr = xmr_security
        else:
            security_xmr.append(xmr_security)
            now_xmr = xmr_security

    context = {'xmr_security': security_xmr, 'btc_security': security_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/securitybudget.html', context)

def efficiency(request):
    '''Breakeven efficiency required for mining profitability for Monero and Bitcoin (at $0.10/KWh, Hashes/Watt*second)'''
    data = DailyData.objects.order_by('date')

    xmr_efficiency = []
    btc_efficiency = []
    dates = []
    now_xmr = 0
    now_btc = 0

    for item in data:
        date = datetime.strftime(item.date, '%Y-%m-%d')
        dates.append(date)
        if item.btc_minerrevusd != 0 and item.btc_inflation > 0:
            if (2**32)*item.btc_difficulty*0.10/(item.btc_minerrevusd*24000) > 10:
                now_btc = (2**32)*item.btc_difficulty*0.10/(item.btc_minerrevusd*24000)
            if now_btc > 0.01:
                btc_efficiency.append(now_btc)
            else:
                btc_efficiency.append('')
        else:
            btc_efficiency.append('')

        if item.xmr_minerrevusd != 0 and item.xmr_inflation > 0:
            if item.xmr_difficulty*0.10/(item.xmr_minerrevusd*5000) > 0.01:
                now_xmr = item.xmr_difficulty*0.10/(item.xmr_minerrevusd*5000)
            if now_xmr > 0.01:
                xmr_efficiency.append(now_xmr)
            else:
                xmr_efficiency.append('')
        else:
            xmr_efficiency.append('')

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)

    context = {'xmr_efficiency': xmr_efficiency, 'btc_efficiency': btc_efficiency, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/efficiency.html', context)

def p2pool_hashrate(request):
    '''P2Pool and P2Pool_mini Hashrate (MH/s)'''
    hashrate = []
    hashrate_mini = []
    combined = []
    dates = []
    now_hashrate = 0
    now_hashrate_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.hashrate and p2pool_stat.percentage > 0:
            now_hashrate = p2pool_stat.hashrate/1000000
            now_combined = p2pool_stat.hashrate/1000000
        hashrate.append(now_hashrate)

        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.hashrate and p2pool_stat_mini.percentage > 0:
                now_hashrate_mini = p2pool_stat_mini.hashrate/1000000
                now_combined += p2pool_stat_mini.hashrate/1000000
        except:
            pass
        hashrate_mini.append(now_hashrate_mini)
        combined.append(now_combined)

        dates.append(datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    context = {'hashrate': hashrate, 'dates': dates, 'hashrate_mini': hashrate_mini, 'combined': combined}
    return render(request, 'charts/p2pool_hashrate.html', context)

def p2pool_dominance(request):
    '''P2Pool and P2Pool_mini Market Share (%)'''
    dominance = []
    dominance_mini = []
    dates = []
    combined = []
    now_dominance = 0
    now_dominance_mini = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.hashrate and p2pool_stat.percentage > 0:
            now_dominance = p2pool_stat.percentage
            now_combined += p2pool_stat.percentage
        dominance.append(now_dominance)

        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.hashrate and p2pool_stat_mini.percentage > 0:
                now_dominance_mini = p2pool_stat_mini.percentage
                now_combined += p2pool_stat_mini.percentage
        except:
            pass
        dominance_mini.append(now_dominance_mini)
        combined.append(now_combined)

        dates.append(datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    context = {'dominance': dominance, 'dates': dates, 'dominance_mini': dominance_mini,'combined': combined}
    return render(request, 'charts/p2pool_dominance.html', context)

def p2pool_miners(request):
    '''P2Pool and P2Pool_mini Miners'''

    miners = []
    miners_mini = []
    dates = []
    combined = []
    now_miners = 0
    now_miners_mini = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.miners > 0:
            now_miners = p2pool_stat.miners
            now_combined += p2pool_stat.miners
        miners.append(now_miners)

        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.miners > 0:
                now_miners_mini = p2pool_stat_mini.miners
                now_combined += p2pool_stat_mini.miners
        except:
            pass
        miners_mini.append(now_miners_mini)
        combined.append(now_combined)

        dates.append(datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    context = {'miners': miners, 'dates': dates, 'miners_mini': miners_mini, 'combined': combined}
    return render(request, 'charts/p2pool_miners.html', context)

def p2pool_totalblocks(request):
    '''P2Pool Blocks Found'''
    dates = []
    totalblocks = []
    totalblocks_mini = []
    combined = []
    now_totalblocks = 0
    now_totalblocks_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.totalblocksfound > now_totalblocks:
            now_totalblocks = p2pool_stat.totalblocksfound
            now_combined += p2pool_stat.totalblocksfound
        totalblocks.append(now_totalblocks)

        p2pool_stats_mini = P2Pool.objects.filter(mini=True).filter(date=p2pool_stat.date)
        for p2pool_stat_mini in p2pool_stats_mini:
            if p2pool_stat_mini.totalblocksfound >= now_totalblocks_mini:
                now_totalblocks_mini = p2pool_stat_mini.totalblocksfound
                now_combined += p2pool_stat_mini.totalblocksfound
                break


        totalblocks_mini.append(now_totalblocks_mini)
        combined.append(now_combined)

        dates.append(datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    context = {'totalblocks': totalblocks, 'totalblocks_mini': totalblocks_mini, 'dates': dates, 'combined': combined}
    return render(request, 'charts/p2pool_totalblocks.html', context)

def p2pool_totalhashes(request):
    '''P2Pool Total Hashes (Tera Hashes) Found'''
    dates = []
    totalblocks = []
    totalblocks_mini = []
    combined = []
    now_totalblocks = 0
    now_totalblocks_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.totalhashes > now_totalblocks:
            now_totalblocks = p2pool_stat.totalhashes/1000000000000
            now_combined += p2pool_stat.totalhashes/1000000000000
        totalblocks.append(now_totalblocks)

        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.totalhashes >= now_totalblocks_mini:
                now_totalblocks_mini = p2pool_stat_mini.totalhashes/1000000000000
                now_combined += p2pool_stat_mini.totalhashes/1000000000000
        except:
            pass
        totalblocks_mini.append(now_totalblocks_mini)
        combined.append(now_combined)

        dates.append(datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    context = {'totalblocks': totalblocks, 'totalblocks_mini': totalblocks_mini, 'dates': dates, 'combined': combined}
    return render(request, 'charts/p2pool_totalhashes.html', context)
