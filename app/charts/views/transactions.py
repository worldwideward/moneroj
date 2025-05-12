'''Views module'''

import requests
import json
import datetime
import aiohttp
import asyncio
import math
import locale
import pandas as pd

from datetime import date, timedelta
from datetime import timezone
from dateutil.relativedelta import relativedelta
from requests.exceptions import Timeout, TooManyRedirects
from requests import Session
from operator import truediv
from ctypes import sizeof
from os import readlink

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage

from charts.models import *
from charts.forms import *
from charts import asynchronous
from charts import synchronous
from charts.synchronous import get_history_function
from charts.spreadsheets import SpreadSheetManager, PandasSpreadSheetManager

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

sheets = PandasSpreadSheetManager()

####################################################################################
#   Transactions Charts
####################################################################################

def translin(request):
    '''Monero Transaction Count (linear)'''

    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []
    now_transactions = 0
    maximum = 0

    coins = Coin.objects.order_by('date')
    for coin in coins:
        print(str(coin.name) + '    ' + str(coin.date))
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if coin.transactions > 200:
            transactions.append(coin.transactions)
            now_transactions = coin.transactions
            if now_transactions > maximum:
                maximum = now_transactions
        else:
            transactions.append('')

        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append('')

        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

    now_transactions = int(now_transactions)
    maximum = int(maximum)

    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/translin.html', context)

def translog(request):
    '''Monero Transaction Count (logarithmic scale) '''

    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []
    now_transactions = 0
    maximum = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if coin.transactions > 200:
            transactions.append(coin.transactions)
            now_transactions = coin.transactions
            if now_transactions > maximum:
                maximum = now_transactions
        else:
            transactions.append('')

        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append('')

        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

    now_transactions = int(now_transactions)
    maximum = int(maximum)

    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/translog.html', context)

def transmonth(request):
    '''Monero Monthly Transactions'''
    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []
    now_transactions = 0
    maximum = 0

    month_previous = '2014-01'
    month = 0
    total = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        aux = str(coin.date)
        month = aux.split("-")[0] + '-' + aux.split("-")[1]
        if month != month_previous:
            dates.append(month_previous)
            transactions.append(total)
            if total > maximum:
                maximum = total
            total = 0
            month_previous = month

        if coin.transactions > 0:
            total += coin.transactions

    now_transactions = int(total)
    maximum = int(maximum)

    now_transactions = locale._format('%.0f', now_transactions, grouping=True)
    maximum = locale._format('%.0f', maximum, grouping=True)

    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/transmonth.html', context)

def transcost(request):
    '''Average Transaction Cost'''
    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_transcostusd == 0:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_transcostusd)
            now_xmr = item.xmr_transcostusd
        if item.btc_transcostusd == 0:
            costbtc.append('')
        else:
            costbtc.append(item.btc_transcostusd)
            now_btc = item.btc_transcostusd

    now_btc = "$" + locale._format('%.2f', now_btc, grouping=True)
    now_xmr = "$" + locale._format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcost.html', context)

def transcostntv(request):
    '''Average Transaction Cost (Native Units)'''

    data = DailyData.objects.order_by('date')
    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_transcostntv == 0:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_transcostntv)
            now_xmr = item.xmr_transcostntv
        if item.btc_transcostntv == 0:
            costbtc.append('')
        else:
            costbtc.append(item.btc_transcostntv)
            now_btc = item.btc_transcostntv

    now_btc = locale._format('%.6f', now_btc, grouping=True)
    now_xmr = locale._format('%.6f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcostntv.html', context)

def percentage(request):
    '''Transaction Percentage (XMR's tx / BTC's tx)'''
    data = DailyData.objects.order_by('date')

    transactions = []
    dates = []
    now_transactions = 0
    maximum = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_transacpercentage > 0.00001:
            transactions.append(100*item.xmr_transacpercentage)
            now_transactions = 100*item.xmr_transacpercentage
            if now_transactions > maximum:
                maximum = now_transactions
        else:
            transactions.append('')

    now_transactions = locale._format('%.1f', now_transactions, grouping=True) + '%'
    maximum = locale._format('%.1f', maximum, grouping=True) + '%'

    context = {'transactions': transactions, 'dates': dates, 'now_transactions': now_transactions, 'maximum': maximum}
    return render(request, 'charts/percentage.html', context)

def percentmonth(request):
    '''Monthly Percentage (XMR's tx / BTC's tx)'''
    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []
    now_transactions = 0
    maximum = 0

    month_previous = '2014-01'
    month = 0
    total = 0
    total_btc = 0
    total_xmr = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        aux = str(coin.date)
        month = aux.split("-")[0] + '-' + aux.split("-")[1]
        try:
            coin_btc = Coin.objects.filter(name='btc').get(date=coin.date)
        except Coin.DoesNotExist as error:

            class coin_btc:
                transactions = 0

        if month != month_previous:
            dates.append(month_previous)
            if total_btc > 0:
                total = 100*total_xmr/total_btc
            else:
                total = 0
            transactions.append(total)
            if total > maximum:
                maximum = total
            total_xmr = 0
            total_btc = 0
            month_previous = month

        if coin.transactions > 0:
            total_xmr += coin.transactions
        if coin_btc.transactions > 0:
            total_btc += coin_btc.transactions

    if total_btc > 0:
        total = 100*total_xmr/total_btc
    else:
        total = 0

    now_transactions = locale._format('%.1f', total, grouping=True) + ' %'
    maximum = locale._format('%.1f', maximum, grouping=True) + ' %'

    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/percentmonth.html', context)

def shielded(request):
    '''Shielded Transactions'''

    dates = []
    values = []
    values2 = []
    values3 = []
    dominance = 0
    monthly = 0

    values_mat = sheets.get_values("zcash_bitcoin.ods", "Sheet1", start=(1, 0), end=(999, 5))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][3]:
            date = values_mat[k][0]
            value = values_mat[k][3]
            value3 = values_mat[k][4]
            if not value or not value:
                break
            else:
                dates.append(date.strftime("%Y-%m-%d"))
                values.append(int(value))
                values3.append(int(value3))
        else:
            break

    previous_date = 0
    coins = Coin.objects.order_by('date').filter(name='xmr')
    for date in dates:
        value2 = 0
        for coin in coins:
            aux = str(coin.date)
            month = aux.split("-")[0] + '-' + aux.split("-")[1]
            if month == date:
                if previous_date != coin.date:
                    value2 += coin.transactions
                    previous_date = coin.date

        values2.append(int(value2))

    dominance = 100*int(value2)/(int(value2)+int(value)+int(value3))
    monthly = int(value2)

    monthly = format(int(monthly),',')
    dominance = locale._format('%.2f', dominance, grouping=True)

    context = {'dates': dates, 'values': values, 'values2': values2, 'values3': values3, "monthly": monthly, "dominance": dominance}
    return render(request, 'charts/shielded.html', context)

def comptransactions(request):
    '''Daily Transactions for Monero and its competitors (Bitcoin and privacy-oriented Dash, Zcash and Grin)'''
    data = DailyData.objects.order_by('date')

    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    btc = []
    now_xmr = 999999
    now_dash = 999999
    now_grin = 999999
    now_zcash = 999999
    now_btc = 999999

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_transactions > 10:
            btc.append(item.btc_transactions)
            now_btc = item.btc_transactions
        else:
            btc.append('')

        if item.zcash_transactions > 10:
            zcash.append(item.zcash_transactions)
            now_zcash = item.zcash_transactions
        else:
            zcash.append('')

        if item.dash_transactions > 10:
            dash.append(item.dash_transactions)
            now_dash = item.dash_transactions
        else:
            dash.append('')

        if item.xmr_transactions > 10:
            xmr.append(item.xmr_transactions)
            now_xmr = item.xmr_transactions
        else:
            xmr.append('')

        if item.grin_transactions > 10:
            grin.append(item.grin_transactions)
            now_grin = item.grin_transactions
        else:
            grin.append('')

    now_dash = locale._format('%.0f', now_dash, grouping=True)
    now_grin = locale._format('%.0f', now_grin, grouping=True)
    now_zcash = locale._format('%.0f', now_zcash, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)
    now_btc = locale._format('%.0f', now_btc, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'btc': btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/comptransactions.html', context)

def metcalfesats(request):
    '''Metcalfe's Law (BTC)'''

    data = DailyData.objects.order_by('date')

    color = []
    metcalfe = []
    prices = []
    dates = []
    now_metcalfe = 0
    now_price = 0
    maximum = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_metcalfebtc < 0.0007:
            metcalfe.append('')
            color.append('')
            prices.append('')
        else:
            metcalfe.append(item.xmr_metcalfebtc)
            now_price = item.xmr_pricebtc
            now_metcalfe = item.xmr_metcalfebtc
            if now_metcalfe > maximum:
                maximum = now_metcalfe
            color.append(30*item.xmr_pricebtc/(count*delta + v0))
            prices.append(now_price)
            count += 1

    now_price = locale._format('%.4f', now_price, grouping=True) + ' BTC'
    now_metcalfe = locale._format('%.4f', now_metcalfe, grouping=True) + ' BTC'
    maximum = locale._format('%.4f', maximum, grouping=True) + ' BTC'

    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfesats.html', context)

def metcalfeusd(request):
    '''Metcalfe's Law (USD)'''

    data = DailyData.objects.order_by('date')

    color = []
    metcalfe = []
    prices = []
    dates = []
    now_metcalfe = 0
    now_price = 0
    maximum = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_metcalfeusd < 0.001:
            metcalfe.append('')
            color.append('')
            prices.append('')
        else:
            metcalfe.append(item.xmr_metcalfeusd)
            now_price = item.xmr_priceusd
            now_metcalfe = item.xmr_metcalfeusd
            if now_metcalfe > maximum:
                maximum = now_metcalfe
            color.append(30*item.xmr_pricebtc/(count*delta + v0))
            prices.append(now_price)
            count += 1

    now_price = "$"+ locale._format('%.2f', now_price, grouping=True)
    now_metcalfe = "$"+ locale._format('%.2f', now_metcalfe, grouping=True)
    maximum = "$"+ locale._format('%.2f', maximum, grouping=True)

    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfeusd.html', context)

def metcalfesats_deviation(request):
    '''Metcalfe's Model Deviation (linear chart, percentage and BTC)'''

    data = DailyData.objects.order_by('date')

    metcalfe_percentage = []
    metcalfe = []
    dates = []
    now_metcalfe = 0
    now_metcalfe_percentage = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_metcalfebtc < 0.0007 and item.xmr_pricebtc <= 0:
            metcalfe.append('')
            metcalfe_percentage.append('')
        else:
            now_metcalfe = item.xmr_metcalfebtc - item.xmr_pricebtc
            now_metcalfe_percentage = 100*((item.xmr_metcalfebtc/item.xmr_pricebtc) - 1)
            metcalfe.append(now_metcalfe)
            metcalfe_percentage.append(now_metcalfe_percentage)

    now_metcalfe = locale._format('%.4f', now_metcalfe, grouping=True)
    now_metcalfe_percentage = locale._format('%.0f', now_metcalfe_percentage, grouping=True)

    context = {'metcalfe': metcalfe, 'dates': dates, 'now_metcalfe': now_metcalfe, 'now_metcalfe_percentage': now_metcalfe_percentage, 'metcalfe_percentage': metcalfe_percentage}
    return render(request, 'charts/metcalfesats_deviation.html', context)

def metcalfe_deviation(request):
    '''Metcalfe's Model Deviation (linear chart, percentage and dollars)'''

    data = DailyData.objects.order_by('date')

    metcalfe_percentage = []
    metcalfe = []
    dates = []
    now_metcalfe = 0
    now_metcalfe_percentage = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_metcalfeusd < 0.0007 and item.xmr_priceusd <= 0:
            metcalfe.append('')
            metcalfe_percentage.append('')
        else:
            now_metcalfe = item.xmr_metcalfeusd - item.xmr_priceusd
            now_metcalfe_percentage = 100*((item.xmr_metcalfeusd/item.xmr_priceusd) - 1)
            metcalfe.append(now_metcalfe)
            metcalfe_percentage.append(now_metcalfe_percentage)

    now_metcalfe = locale._format('%.0f', now_metcalfe, grouping=True)
    now_metcalfe_percentage = locale._format('%.0f', now_metcalfe_percentage, grouping=True)

    context = {'metcalfe': metcalfe, 'dates': dates, 'now_metcalfe': now_metcalfe, 'now_metcalfe_percentage': now_metcalfe_percentage, 'metcalfe_percentage': metcalfe_percentage}
    return render(request, 'charts/metcalfe_deviation.html', context)

def deviation_tx(request):
    '''Transacted Price Deviation (USD)'''

    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        transactions.append(coin.transactions)
        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append(0.20)

        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

    n = 180
    median_long = pd.Series(transactions).rolling(window=n).mean().iloc[n-1:].values
    m_long = []
    for i in range(n):
        m_long.append(0)
    for item in median_long:
        m_long.append(float(item))

    n = 3
    median_short = pd.Series(transactions).rolling(window=n).mean().iloc[n-1:].values
    m_short = []
    for i in range(n):
        m_short.append(0)
    for item in median_short:
        m_short.append(float(item))

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
    for count in range(0, len(m_short)):
        if float(m_long[count]) < 0.001 or float(m_long_price[count]) < 0.001:
            deviation_percentage.append('')
        else:
            calculation = (float(m_short_price[count])-float(m_long_price[count]))*abs(float(m_short[count])-float(m_long[count]))/(float(m_long[count]))
            if calculation > 100:
                calculation = 100
            if calculation < -100:
                calculation = -100
            deviation_percentage.append(calculation)

    context = {'deviation_percentage': deviation_percentage, 'dates': dates, 'pricexmr': pricexmr}
    return render(request, 'charts/deviation_tx.html', context)

def transactiondominance(request):
    '''Monero's Dominance Over the Number of Transactions on the Privacy Market (%)'''

    data = DailyData.objects.order_by('date')

    xmr_dominance = []
    dates = []
    now_xmr = 0
    maximum = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_transactions > 0:
            now_xmr = 100*item.xmr_transactions/(item.xmr_transactions+item.dash_transactions+item.zcash_transactions+item.grin_transactions)
        else:
            now_xmr = 0
        if now_xmr > maximum:
            maximum = now_xmr
        xmr_dominance.append(now_xmr)

    now_xmr = locale._format('%.1f', now_xmr, grouping=True) + '%'
    maximum = locale._format('%.1f', maximum, grouping=True) + '%'

    context = {'xmr_dominance': xmr_dominance, 'now_xmr': now_xmr, 'maximum': maximum, 'dates': dates}
    return render(request, 'charts/transactiondominance.html', context)
