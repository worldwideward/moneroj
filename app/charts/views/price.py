'''Price Chart views'''

import math
import locale
import pandas as pd

from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from operator import truediv

from django.shortcuts import render

from charts.models import Coin
from charts.models import Sfmodel

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

####################################################################################
# Price charts
####################################################################################

def pricelog(request):
    '''Monero price logarithmic'''

    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    dates = []
    color = []
    values = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        count += 1

    count = 0
    for count in range(650):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.strftime(date_now, '%Y-%m-%d'))
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(  10**12)
        supply += int(720*reward)

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale._format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale._format('%.2f', maximum, grouping=True)
    now_inflation = locale._format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/pricelog.html', context)

def pricelin(request):
    '''Monero price linear'''

    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    dates = []
    color = []
    values = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        count += 1

    count = 0
    for count in range(650):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.strftime(date_now, '%Y-%m-%d'))
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(  10**12)
        supply += int(720*reward)
        stock = (100/(100*reward*720*365/supply))**1.65

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale._format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale._format('%.2f', maximum, grouping=True)
    now_inflation = locale._format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/pricelin.html', context)

def pricesats(request):
    '''Bitcoin price linear'''
    dates = []
    color = []
    values = []
    now_price = 0
    maximum = 0
    bottom = 1

    data = Sfmodel.objects.order_by('date')
    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.pricebtc > 0.0001:
            values.append(item.pricebtc)
            now_price = item.pricebtc
            if bottom > item.pricebtc:
                bottom = item.pricebtc
            if maximum < item.pricebtc:
                maximum = item.pricebtc
        else:
            values.append('')

    now_price = locale._format('%.4f', now_price, grouping=True) + ' BTC'
    maximum = locale._format('%.4f', maximum, grouping=True) + ' BTC'
    bottom = locale._format('%.4f', bottom, grouping=True) + ' BTC'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'bottom': bottom}
    return render(request, 'charts/pricesats.html', context)

def pricesatslog(request):
    '''Bitcoin price logarythmic'''
    dates = []
    color = []
    values = []
    now_price = 0
    maximum = 0
    bottom = 1

    data = Sfmodel.objects.order_by('date')
    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.pricebtc > 0.0001:
            values.append(item.pricebtc)
            now_price = item.pricebtc
            if bottom > item.pricebtc:
                bottom = item.pricebtc
            if maximum < item.pricebtc:
                maximum = item.pricebtc
        else:
            values.append('')

    now_price = locale._format('%.4f', now_price, grouping=True) + ' BTC'
    maximum = locale._format('%.4f', maximum, grouping=True) + ' BTC'
    bottom = locale._format('%.4f', bottom, grouping=True) + ' BTC'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'bottom': bottom}
    return render(request, 'charts/pricesatslog.html', context)

def fractal(request):
    '''Fractal Multiple chart'''

    symbol = 'xmr'
    dates1 = []
    dates2 = []
    cycle1 = []
    cycle2 = []
    now_multiple = 0
    maximum = 0

    count1 = 1
    count2 = 1
    date1_aux = datetime(2017, 12, 29)
    date2_aux = datetime(2014, 6, 21)
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        date3_aux = datetime.combine(coin.date, time(0, 0))
        if date3_aux < date1_aux and date3_aux > date2_aux:
            cycle1.append(coin.priceusd/5)
            dates1.append(count1/12.7)
            if (coin.priceusd/5) > maximum:
                maximum = coin.priceusd/5
            count1 += 1
        elif date3_aux > date1_aux:
            cycle2.append(coin.priceusd/477.12)
            dates2.append(count2/20.7) #24
            now_multiple = coin.priceusd/477.12
            count2 += 0.86

    now_multiple = locale._format('%.2f', now_multiple, grouping=True) + 'x'
    maximum = locale._format('%.2f', maximum, grouping=True) + 'x'

    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'charts/fractal.html', context)

def inflationfractal(request):
    '''Inflation-Adjusted Fractal Chart'''

    symbol = 'xmr'
    dates1 = []
    dates2 = []
    cycle1 = []
    cycle2 = []
    now_multiple = 0
    maximum = 0

    current_inflation = 0
    start_inflation = 0
    count1 = 1
    count2 = 1
    date1_aux = datetime(2017, 12, 29)
    date2_aux = datetime(2014, 6, 21)
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        date3_aux = datetime.combine(coin.date, time(0, 0))
        if date3_aux < date1_aux and date3_aux > date2_aux:
            start_inflation = coin.inflation
            current_inflation = start_inflation
            cycle1.append(coin.priceusd/5)
            dates1.append(count1/12.7)
            if (coin.priceusd/5) > maximum:
                maximum = coin.priceusd/5
            count1 += 1
        elif date3_aux > date1_aux:
            if (coin.inflation/current_inflation) > 1.15 or (coin.inflation/current_inflation) < 0.85:
                coin.inflation = current_inflation
            else:
                current_inflation = coin.inflation
            delta = math.sqrt(coin.inflation/start_inflation)
            cycle2.append(delta*coin.priceusd/477.12)
            dates2.append(count2/20.55) #24
            now_multiple = delta*coin.priceusd/477.12
            count2 += 0.86

    now_multiple = locale._format('%.2f', now_multiple, grouping=True) + 'x'
    maximum = locale._format('%.2f', maximum, grouping=True) + 'x'

    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'charts/inflationfractal.html', context)

def marketcycle(request):
    '''Market Cycle'''

    dates = []
    color = []
    sell = []
    buy = []
    data = Sfmodel.objects.order_by('date')
    for item in data:
        if item.color > 0:
            color.append(item.color - 5)
        else:
            color.append('')

        sell.append(100)
        buy.append(0)
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

    now_cycle = locale._format('%.2f', item.color, grouping=True)

    context = {'dates': dates, 'color': color, 'sell': sell, 'buy': buy, 'now_cycle': now_cycle}
    return render(request, 'charts/marketcycle.html', context)

def golden(request):
    '''Golden Ratio Multiplier chart'''

    symbol = 'xmr'
    dates = []
    prices = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        firstdate = coin.date
        break

    day = firstdate - timedelta(350)
    for i in range(350):
        dates.append(datetime.strftime(day, '%Y-%m-%d'))
        prices.append(0.2)

    for coin in coins:
        dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.priceusd > 0.2:
            prices.append(coin.priceusd)
        else:
            prices.append(0.2)

    n = 350
    median = pd.Series(prices).rolling(window=n).mean().iloc[n-1:].values
    m_350 = []
    m_350_0042 = []
    m_350_0060 = []
    m_350_0200 = []
    m_350_0300 = []
    m_350_0500 = []
    m_350_0800 = []
    m_350_1300 = []
    for i in range(350):
        m_350.append('')
        m_350_0042.append('')
        m_350_0060.append('')
        m_350_0200.append('')
        m_350_0300.append('')
        m_350_0500.append('')
        m_350_0800.append('')
        m_350_1300.append('')
    for item in median:
        m_350.append(float(item))
        m_350_0042.append(float(item)*0.42)
        m_350_0060.append(float(item)*0.60)
        m_350_0200.append(float(item)*2.00)
        m_350_0300.append(float(item)*3.00)
        m_350_0500.append(float(item)*5.00)
        m_350_0800.append(float(item)*8.00)
        m_350_1300.append(float(item)*13.00)

    n = 120
    median = pd.Series(prices).rolling(window=n).mean().iloc[n-1:].values
    m_111 = []
    for i in range(120):
        m_111.append('')
    for item in median:
        m_111.append(float(item))

    i = 0
    down = True
    price_cross = []
    for price in prices:
        if m_111[i] != '' and m_350_0200[i] != '':
            if down == True and m_111[i] > m_350_0200[i]:
                down = False
                price_cross.append(price)
            elif price > m_350_0500[i]:
                price_cross.append(price)
            elif down == False and m_111[i] < m_350_0200[i]:
                down = True
            else:
                price_cross.append('')
        else:
            price_cross.append('')
        i += 1

    context = {'dates': dates, 'prices': prices, 'm_350': m_350, 'm_350_0042': m_350_0042, 'm_350_0060': m_350_0060, 'm_350_0200': m_350_0200, 'm_350_0300': m_350_0300,
    'm_350_0500': m_350_0500, 'm_350_0800': m_350_0800, 'm_350_1300': m_350_1300, 'median': median, 'm_111': m_111, 'price_cross': price_cross}
    return render(request, 'charts/golden.html', context)

def competitors(request):
    '''Competitor Performance (Logarithmic Scale) '''

    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count > 30:
                xmr.append(coin_xmr.priceusd/5.01)
                now_xmr = coin_xmr.priceusd/5.01
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.priceusd and count > 130:
            dash.append(coin_dash.priceusd/14.7)
            now_dash = coin_dash.priceusd/14.7
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.priceusd and count > 155:
            grin.append(coin_grin.priceusd/6.37)
            now_grin = coin_grin.priceusd/6.37
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.priceusd and count > 434:
            zcash.append(coin_zcash.priceusd/750)
            now_zcash = coin_zcash.priceusd/750
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale._format('%.2f', now_dash, grouping=True)
    now_grin = locale._format('%.2f', now_grin, grouping=True)
    now_zcash = locale._format('%.2f', now_zcash, grouping=True)
    now_xmr = locale._format('%.2f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitors.html', context)

def competitorslin(request):
    '''Competitor Performance (Linear Scale) '''
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count > 30:
                xmr.append(coin_xmr.priceusd/5.01)
                now_xmr = coin_xmr.priceusd/5.01
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.priceusd and count > 130:
            dash.append(coin_dash.priceusd/14.7)
            now_dash = coin_dash.priceusd/14.7
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.priceusd and count > 155:
            grin.append(coin_grin.priceusd/6.37)
            now_grin = coin_grin.priceusd/6.37
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.priceusd and count > 434:
            zcash.append(coin_zcash.priceusd/750)
            now_zcash = coin_zcash.priceusd/750
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale._format('%.2f', now_dash, grouping=True)
    now_grin = locale._format('%.2f', now_grin, grouping=True)
    now_zcash = locale._format('%.2f', now_zcash, grouping=True)
    now_xmr = locale._format('%.2f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorslin.html', context)

def competitorssats(request):
    '''Competitor Performance (logarithmic)'''
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0
    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.pricebtc:
            if count > 32:
                xmr.append(coin_xmr.pricebtc/0.0058)
                now_xmr = coin_xmr.pricebtc/0.0058
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.pricebtc and count > 130:
            dash.append(coin_dash.pricebtc/0.02)
            now_dash = coin_dash.pricebtc/0.02
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.pricebtc and count > 155:
            grin.append(coin_grin.pricebtc/0.000513)
            now_grin = coin_grin.pricebtc/0.000513
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.pricebtc and count > 434:
            zcash.append(coin_zcash.pricebtc/0.05)
            now_zcash = coin_zcash.pricebtc/0.05
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale._format('%.3f', now_dash, grouping=True)
    now_grin = locale._format('%.3f', now_grin, grouping=True)
    now_zcash = locale._format('%.3f', now_zcash, grouping=True)
    now_xmr = locale._format('%.3f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorssats.html', context)

def competitorssatslin(request):
    '''Competitor Performance (linear)'''
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0
    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.pricebtc:
            if count > 32:
                xmr.append(coin_xmr.pricebtc/0.0058)
                now_xmr = coin_xmr.pricebtc/0.0058
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.pricebtc and count > 130:
            dash.append(coin_dash.pricebtc/0.02)
            now_dash = coin_dash.pricebtc/0.02
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.pricebtc and count > 155:
            grin.append(coin_grin.pricebtc/0.000513)
            now_grin = coin_grin.pricebtc/0.000513
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.pricebtc and count > 434:
            zcash.append(coin_zcash.pricebtc/0.05)
            now_zcash = coin_zcash.pricebtc/0.05
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale._format('%.3f', now_dash, grouping=True)
    now_grin = locale._format('%.3f', now_grin, grouping=True)
    now_zcash = locale._format('%.3f', now_zcash, grouping=True)
    now_xmr = locale._format('%.3f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorssatslin.html', context)

def inflationreturn(request):
    '''Return Versus Inflation chart'''

    count = 0
    xmr = []
    dash = []
    grin = []
    zcash = []
    btc = []
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0
    now_btc = 0
    inflation_xmr = []
    inflation_dash = []
    inflation_grin = []
    inflation_zcash = []
    inflation_btc = []

    lastxmrA = 0
    lastxmrB = 0

    count = 0
    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 30 and coin.inflation > 0:
            now_xmr = coin.priceusd/5.01
            #correcao de um erro nos dados
            if 100/coin.inflation > 110 and now_xmr < 10:
                xmr.append(lastxmrA)
                inflation_xmr.append(lastxmrB)
            else:
                xmr.append(now_xmr)
                inflation_xmr.append(100/coin.inflation)
                lastxmrA = now_xmr
                lastxmrB = 100/coin.inflation

    count = 0
    coins = Coin.objects.order_by('date').filter(name='dash')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 130 and coin.inflation > 0:
            now_dash = coin.priceusd/14.7
            dash.append(now_dash)
            inflation_dash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='grin')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 155 and coin.inflation > 0:
            now_grin = coin.priceusd/6.37
            grin.append(now_grin)
            inflation_grin.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='zec')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 434 and coin.inflation > 0:
            now_zcash = coin.priceusd/750
            zcash.append(now_zcash)
            inflation_zcash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='btc')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 325 and coin.inflation > 0:
            now_btc = coin.priceusd/30
            btc.append(now_btc)
            inflation_btc.append(100/coin.inflation)

    now_dash = locale._format('%.2f', now_dash, grouping=True)
    now_grin = locale._format('%.2f', now_grin, grouping=True)
    now_zcash = locale._format('%.2f', now_zcash, grouping=True)
    now_xmr = locale._format('%.2f', now_xmr, grouping=True)
    now_btc = locale._format('%.2f', now_btc, grouping=True)

    context = {'inflation_btc': inflation_btc,'inflation_xmr': inflation_xmr, 'inflation_dash': inflation_dash, 'inflation_grin': inflation_grin, 'inflation_zcash': inflation_zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'btc': btc, 'xmr': xmr, 'dash': dash, 'zcash': zcash, 'grin': grin}
    return render(request, 'charts/inflationreturn.html', context)

def bitcoin(request):
    '''Total Blockchain Size for Monero and Bitcoin (KB) & Comparison to Bitcoin (aligned)'''
    dates = []
    dates3 = []
    dates4 = []
    btc = []
    xmr3 = []
    count1 = 0
    count3 = 0
    now_xmr = 0
    now_btc = 0

    coins_btc = Coin.objects.order_by('date').filter(name='btc')
    for coin_btc in coins_btc:
        if coin_btc.priceusd:
            if count1 > 890: #450
                btc.append(coin_btc.priceusd/30)
                now_btc = coin_btc.priceusd/30
            dates.append(count1)
            count1 += 1 #1.4
        elif count1 <= 890: #450
            continue
        else:
            btc.append('')

    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')

    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count3 > 30:
                xmr3.append(coin_xmr.priceusd/5.01)
            dates4.append(count3)
            count3 += 0.92
        elif count3 <= 30:
            continue
        else:
            xmr3.append('')

    data = DailyData.objects.order_by('date')

    dates2 = []
    xmr2 = []
    btc2 = []

    for item in data:
        dates2.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_return > 0.0001:
            btc2.append(item.btc_return)
        else:
            btc2.append('')

        if item.xmr_return > 0.0001:
            xmr2.append(item.xmr_return)
        else:
            xmr2.append('')

    now_btc = locale._format('%.2f', now_btc, grouping=True)
    now_xmr = locale._format('%.2f', now_xmr, grouping=True)

    context = {'btc': btc, 'xmr2': xmr2, 'btc2': btc2, 'xmr3': xmr3, 'dates': dates, 'dates2': dates2, 'dates3': dates3, 'dates4': dates4}
    return render(request, 'charts/bitcoin.html', context)

def powerlaw(request):
    '''Power Law chart'''
    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    dates = []
    counter = []
    years = []
    line3 = []
    line2 = []
    line1 = []
    a3 = 0.00000000000000000009
    a2 = 0.0000000000000000000000008
    a1 = 0.00000000000000000000000002
    b3 = ((math.log(477,10)-math.log(5.01,10))/(math.log(2511,10)-math.log(1231,10)))
    b2 = ((math.log(92,10)-math.log(0.23,10))/(math.log(3297,10)-math.log(1468,10)))
    b1 = ((math.log(93,10)-math.log(0.39,10))/(math.log(3570,10)-math.log(1755,10)))
    color = []
    values = []

    yearnumber = 2014
    days = 1200
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if coin.priceusd < 0.01:
            continue
        days += 1
        price3 = a3*(days**b3)
        price2 = a2*(days**b2)
        price1 = a1*(days**b1)
        line3.append(price3)
        line2.append(price2)
        line1.append(price1)
        counter.append(days)
        if coin.date.year > yearnumber:
            yearnumber += 1
            years.append(yearnumber)
            dates.append(days)
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        count += 1

    for count in range(1, 3650):
        date_now = date.today() + timedelta(count)
        values.append('')
        days += 1
        price3 = a3*(days**b3)
        price2 = a2*(days**b2)
        price1 = a1*(days**b1)
        line3.append(price3)
        line2.append(price2)
        line1.append(price1)
        counter.append(days)
        if date_now.year > yearnumber:
            yearnumber += 1
            years.append(yearnumber)
            dates.append(days)

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale._format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale._format('%.2f', maximum, grouping=True)
    now_inflation = locale._format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation,
    'now_sf': now_sf, 'color': color, 'years': years, 'counter': counter, 'line1': line1, 'line2': line2, 'line3': line3}
    return render(request, 'charts/powerlaw.html', context)

def thermocap(request):
    '''Thermocap Multiple'''

    symbol = 'xmr'
    dates = []
    values = []
    thermocap = []
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    sf_aux = 0
    supply = 0
    calorie = 1
    calories = []
    calories2 = []
    calories3 = []
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.stocktoflow > sf_aux*2+250:
            coin.stocktoflow = sf_aux
        sf_aux = coin.stocktoflow
        values.append(coin.priceusd)
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)

        calorie += (coin.supply - supply)*coin.priceusd
        if coin.inflation != 0:
            if calorie/(4200000*math.sqrt(coin.inflation)) < 0.1:
                calories.append('')
            else:
                calories.append(calorie/(4200000*math.sqrt(coin.inflation)))
            if calorie/(1000000*math.sqrt(coin.inflation)) < 0.1:
                calories2.append('')
            else:
                calories2.append(calorie/(1000000*math.sqrt(coin.inflation)))
            if 28*calorie/(2500000*math.sqrt(coin.inflation)) < 0.1:
                calories3.append('')
            else:
                calories3.append(28*calorie/(2500000*math.sqrt(coin.inflation)))
        else:
            calories.append('')
        temperature = coin.priceusd/calorie
        if temperature > 0.000004:
            temperature = 0.000004
        thermocap.append(temperature)
        supply = coin.supply
        count += 1

    temperature = locale._format('%.2f', temperature, grouping=True)

    context = {'dates': dates, 'temperature': temperature, 'values': values, 'thermocap': thermocap, 'color': color, 'calories': calories,
    'calories2': calories2, 'calories3': calories3}
    return render(request, 'charts/thermocap.html', context)

def sharpe(request):
    '''Sharpe Ratio'''

    symbol = 'xmr'
    dates = []
    values = []
    color = []
    rocs = []
    sharpe = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    price = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        new_color = 30*coin.pricebtc/(count*delta + v0)
        count += 1
        if count % 7 == 0:
            if price == 0:
                if coin.priceusd > 0:
                    price = coin.priceusd
                    roc = 0
                else:
                    roc = 0
            else:
                roc = (coin.priceusd - price)/price
                price = coin.priceusd
            rocs.append(roc)
            dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
            values.append(coin.priceusd)
            color.append(new_color)

    n = 52
    median = pd.Series(rocs).rolling(window=n).mean().iloc[n-1:].values
    std = pd.Series(rocs).rolling(window=n).std().iloc[n-1:].values

    aux = list(map(truediv, median, std))
    for count in range(51):
        sharpe.append('')
    for item in aux:
        sharpe.append(float(item*math.sqrt(52)))

    context = {'dates': dates, 'values': values, 'color': color, 'sharpe': sharpe}
    return render(request, 'charts/sharpe.html', context)

def deviation(request):
    '''Price Deviation from 6 Months Average'''

    symbol = 'xmr'
    pricexmr = []
    dates = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append(0.20)

        coin.date = datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

    n = 180
    median_long_price = pd.Series(pricexmr).rolling(window=n).mean().iloc[n-1:].values
    m_long_price = []
    for i in range(n):
        m_long_price.append(0)
    for item in median_long_price:
        m_long_price.append(float(item))

    n = 3
    median_short_price = pd.Series(pricexmr).rolling(window=n).mean().iloc[n-1:].values
    m_short_price = []
    for i in range(n):
        m_short_price.append(0)
    for item in median_short_price:
        m_short_price.append(float(item))

    deviation_percentage = []
    deviation_price = []
    for count in range(0, len(m_short_price)):
        if float(m_long_price[count]) < 0.001:
            deviation_price.append('')
            deviation_percentage.append('')
        else:
            deviation_price.append((float(m_short_price[count])-float(m_long_price[count]))/(1))
            deviation_percentage.append(100*(float(m_short_price[count])-float(m_long_price[count]))/(float(m_long_price[count])))

    context = {'deviation_percentage': deviation_percentage, 'deviation_price': deviation_price, 'dates': dates, 'pricexmr': pricexmr}
    return render(request, 'charts/deviation.html', context)
