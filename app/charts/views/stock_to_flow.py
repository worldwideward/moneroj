'''Views module'''

import locale

from datetime import date
from datetime import datetime
from datetime import timedelta

from django.shortcuts import render

from charts.models import Coin
from charts.models import Sfmodel

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

####################################################################################
#   Views
####################################################################################

def sfmodel(request):
    '''Stock-to-flow Model (logarithmic)'''
    dates = []
    stock_to_flow = []
    projection = []
    color = []
    values = []
    now_price = 0
    now_sf = 0
    now_inflation = 0

    data = Sfmodel.objects.order_by('date')
    count_aux = 0
    for item in data:
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.greyline != 0:
            projection.append(item.greyline)
            if count_aux > 25:
                count_aux = 0
            else:
                projection.append(item.greyline)
        else:
            projection.append('')

        if item.stocktoflow > 0.2:
            stock_to_flow.append(item.stocktoflow)
        else:
            stock_to_flow.append('')

        if item.priceusd > 0.1:
            values.append(item.priceusd)
            now_price = item.priceusd
            now_sf = item.stocktoflow
            if item.date > date.today() - timedelta(4):
                coins = Coin.objects.filter(name='xmr').filter(date=item.date)
                if coins:
                    for coin in coins:
                        now_inflation = coin.inflation
        else:
            values.append('')
        count_aux += 1

        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale._format('%.2f', now_sf, grouping=True)
    now_inflation = locale._format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow, 'projection': projection, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodel.html', context)

def sfmodellin(request):
    '''Stock-to-flow Model (linear)'''
    dates = []
    stock_to_flow = []
    projection = []
    color = []
    values = []
    now_price = 0
    now_sf = 0
    now_inflation = 0

    data = Sfmodel.objects.order_by('date')
    count_aux = 0
    for item in data:
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.greyline != 0:
            projection.append(item.greyline)
            if count_aux > 25:
                count_aux = 0
            else:
                projection.append(item.greyline)
        else:
            projection.append('')

        if item.stocktoflow > 0.2:
            stock_to_flow.append(item.stocktoflow)
        else:
            stock_to_flow.append('')

        if item.priceusd > 0.1:
            values.append(item.priceusd)
            now_price = item.priceusd
            now_sf = item.stocktoflow
            if item.date > date.today() - timedelta(4):
                coins = Coin.objects.filter(name='xmr').filter(date=item.date)
                if coins:
                    for coin in coins:
                        now_inflation = coin.inflation
        else:
            values.append('')
        count_aux += 1

        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale._format('%.2f', now_sf, grouping=True)
    now_inflation = locale._format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow,'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodellin.html', context)

def sfmultiple(request):
    '''Stock-to-flow Multiple (Price / SF Model)'''

    symbol = 'xmr'
    now_sf = 0
    maximum = 0
    dates = []
    stock_to_flow = []
    buy = []
    sell = []
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    sf_aux = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.strftime(coin.date, '%Y-%m-%d'))
        buy.append(1)
        sell.append(100)
        if coin.stocktoflow > sf_aux*2+250:
            coin.stocktoflow = sf_aux
        sf_aux = coin.stocktoflow
        if coin.priceusd < 1:
            coin.priceusd = 1
        if coin.stocktoflow != 0:
            now_sf = coin.supply*coin.priceusd/(coin.stocktoflow*1500000)
        stock_to_flow.append(now_sf)
        buy.append(1)
        sell.append(100)
        if now_sf > maximum:
            maximum = now_sf
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        count += 1

    now_sf = locale._format('%.2f', now_sf, grouping=True)
    maximum = locale._format('%.2f', maximum, grouping=True)

    context = {'dates': dates, 'maximum': maximum, 'stock_to_flow': stock_to_flow, 'now_sf': now_sf, 'buy': buy, 'sell': sell, 'color': color}
    return render(request, 'charts/sfmultiple.html', context)
