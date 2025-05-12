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
#   Issuance Charts
####################################################################################

def coins(request):
    '''Coins in circulation'''

    data = DailyData.objects.order_by('date')

    supplyxmr = []
    supplybtc = []
    fsupplyxmr = []
    fsupplybtc = []
    dates = []
    now_xmr = 0
    now_btc = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_supply > 0.1:
            supplybtc.append(item.btc_supply)
            now_btc = item.btc_supply
        else:
            supplybtc.append('')

        if item.xmr_inflation > 0.1:
            supplyxmr.append(item.xmr_supply)
            now_xmr = item.xmr_supply
        else:
            supplyxmr.append('')

        fsupplyxmr.append('')
        fsupplybtc.append('')

    rewardbtc = 900
    supplybitcoin = item.btc_supply
    supply = int(item.xmr_supply)*10**12
    for i in range(365*(2060-2020)):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        fsupplyxmr.append(supply/(10**12))
        date_aux = item.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        supplybitcoin += rewardbtc
        if supplybitcoin > 21000000:
            supplybitcoin = 21000000
        fsupplybtc.append(supplybitcoin)
        date_aux2 = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        if date_aux2 == '2024-04-23':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2028-05-05':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2032-05-03':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2036-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2040-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2044-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2048-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2052-04-19':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2056-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2060-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2064-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2068-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2072-04-19':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2076-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2080-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2084-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2088-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2140-01-01':
            rewardbtc = 0
            supplybitcoin = 21000000
        supplyxmr.append('')
        supplybtc.append('')

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)

    context = {'supplyxmr': supplyxmr, 'supplybtc': supplybtc, 'fsupplyxmr': fsupplyxmr, 'fsupplybtc': fsupplybtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/coins.html', context)

def extracoins(request):
    '''Supply Difference'''

    data = DailyData.objects.order_by('date')

    nsupply = []
    fsupply = []
    dates = []
    now_diff = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_supply - item.xmr_supply > 0:
            nsupply.append(item.btc_supply - item.xmr_supply)
        else:
            nsupply.append('')

        fsupply.append('')

    rewardbtc = 900
    supplybitcoin = item.btc_supply
    supply = int(item.xmr_supply)*10**12
    for i in range(365*(2060-2020)):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        date_aux = item.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        supplybitcoin += rewardbtc
        if supplybitcoin > 21000000:
            supplybitcoin = 21000000
        fsupply.append(-supply/(10**12) + supplybitcoin)
        date_aux2 = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        if date_aux2 == '2024-04-23':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2028-05-05':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2032-05-03':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2036-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2040-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2044-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2048-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2052-04-19':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2056-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2060-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2064-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2068-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2072-04-19':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2076-04-30':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2080-04-27':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2084-04-25':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2088-04-22':
            rewardbtc = rewardbtc/2
        if date_aux2 == '2140-01-01':
            rewardbtc = 0
            supplybitcoin = 21000000
        nsupply.append('')

    now_diff = locale._format('%.0f', now_diff, grouping=True)

    context = {'nsupply': nsupply, 'fsupply': fsupply, 'dates': dates, 'now_diff': now_diff}
    return render(request, 'charts/extracoins.html', context)

def inflation(request):
    '''Annualized Inflation for both Monero and Bitcoin'''

    data = DailyData.objects.order_by('date')

    inflationxmr = []
    inflationbtc = []
    finflationxmr = []
    finflationbtc = []
    dates = []
    now_xmr = 999999
    now_btc = 999999

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_inflation > 0.1:
            inflationbtc.append(item.btc_inflation)
            now_btc = item.btc_inflation
        else:
            inflationbtc.append('')

        if item.xmr_inflation > 0.1:
            inflationxmr.append(item.xmr_inflation)
            now_xmr = item.xmr_inflation
        else:
            inflationxmr.append('')

        finflationxmr.append('')
        finflationbtc.append('')

    inflationbitcoin = 1.75
    supply = int(item.xmr_supply)*10**12
    for i in range(2000):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        finflationxmr.append(100*reward*720*365/supply)
        date_aux = item.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        finflationbtc.append(inflationbitcoin)
        date_aux2 = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        if date_aux2 == '2024-04-23':
            inflationbitcoin = 0.65
        inflationxmr.append('')
        inflationbtc.append('')

    now_btc = locale._format('%.2f', now_btc, grouping=True) + '%'
    now_xmr = locale._format('%.2f', now_xmr, grouping=True) + '%'

    context = {'inflationxmr': inflationxmr, 'inflationbtc': inflationbtc, 'finflationxmr': finflationxmr, 'finflationbtc': finflationbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/inflation.html', context)

def tail_emission(request):
    '''Monero's Tail Emission'''

    inflationxmr = []
    finflationxmr = []
    dates = []
    now_xmr = 999999

    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        now_xmr = float(coin.inflation)

    supply = int(coin.supply)*10**12
    for i in range(210000):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        finflationxmr.append(100*reward*720*365/supply)
        date_aux = coin.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))

    now_xmr = locale._format('%.2f', now_xmr, grouping=True) + '%'

    context = {'inflationxmr': inflationxmr, 'finflationxmr': finflationxmr, 'now_xmr': now_xmr, 'dates': dates}
    return render(request, 'charts/tail_emission.html', context)

def compinflation(request):
    '''Annualized Inflation for Monero and its competitors (Bitcoin and privacy-oriented Dash, Zcash and Grin)'''

    data = DailyData.objects.order_by('date')

    dates = []
    inflationxmr = []
    inflationdash = []
    inflationgrin = []
    inflationzcash = []
    inflationbtc = []
    now_xmr = 999999
    now_dash = 999999
    now_grin = 999999
    now_zcash = 999999
    now_btc = 999999

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_inflation > 0.1:
            inflationbtc.append(item.btc_inflation)
            now_btc = item.btc_inflation
        else:
            inflationbtc.append('')

        if item.zcash_inflation > 0.1:
            inflationzcash.append(item.zcash_inflation)
            now_zcash = item.zcash_inflation
        else:
            inflationzcash.append('')

        if item.dash_inflation > 0.1:
            inflationdash.append(item.dash_inflation)
            now_dash = item.dash_inflation
        else:
            inflationdash.append('')

        if item.xmr_inflation > 0.1:
            inflationxmr.append(item.xmr_inflation)
            now_xmr = item.xmr_inflation
        else:
            inflationxmr.append('')

        if item.grin_inflation > 0.1:
            inflationgrin.append(item.grin_inflation)
            now_grin = item.grin_inflation
        else:
            inflationgrin.append('')

    now_dash = locale._format('%.2f', now_dash, grouping=True) + '%'
    now_grin = locale._format('%.2f', now_grin, grouping=True) + '%'
    now_zcash = locale._format('%.2f', now_zcash, grouping=True) + '%'
    now_xmr = locale._format('%.2f', now_xmr, grouping=True) + '%'
    now_btc = locale._format('%.2f', now_btc, grouping=True) + '%'

    context = {'inflationxmr': inflationxmr, 'inflationdash': inflationdash, 'inflationgrin': inflationgrin, 'inflationzcash': inflationzcash, 'inflationbtc': inflationbtc,
    'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/compinflation.html', context)

def dailyemission(request):
    '''Daily Emission (USD)'''

    data = DailyData.objects.order_by('date')

    emissionbtc = []
    emissionxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    high_btc = 0
    high_xmr = 0

    for item in data:
        if item.btc_emissionusd == 0:
            emissionbtc.append('')
        else:
            emissionbtc.append(item.btc_emissionusd)
            now_btc = item.btc_emissionusd
            if item.btc_emissionusd > high_btc:
                high_btc = item.btc_emissionusd

        if item.xmr_emissionusd == 0:
            emissionxmr.append('')
        else:
            emissionxmr.append(item.xmr_emissionusd)
            now_xmr = item.xmr_emissionusd
            if item.xmr_emissionusd > high_xmr:
                high_xmr = item.xmr_emissionusd
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

    for i in range(500):
        date_aux = item.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        emissionxmr.append('')
        emissionbtc.append('')

    now_btc = "$" + locale._format('%.0f', now_btc, grouping=True)
    now_xmr = "$" + locale._format('%.0f', now_xmr, grouping=True)
    high_btc = "$" + locale._format('%.0f', high_btc, grouping=True)
    high_xmr = "$" + locale._format('%.0f', high_xmr, grouping=True)

    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'high_xmr': high_xmr, 'high_btc': high_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemission.html', context)

def dailyemissionntv(request):
    '''Daily Emission (Native Units)'''

    data = DailyData.objects.order_by('date')
    emissionbtc = []
    emissionxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    for item in data:
        if item.btc_emissionntv == 0:
            emissionbtc.append('')
        else:
            emissionbtc.append(item.btc_emissionntv)
            now_btc = item.btc_emissionntv

        if item.xmr_emissionntv == 0:
            emissionxmr.append('')
        else:
            emissionxmr.append(item.xmr_emissionntv)
            now_xmr = item.xmr_emissionntv
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

    for i in range(500):
        date_aux = item.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        emissionxmr.append('')
        emissionbtc.append('')

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)

    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemissionntv.html', context)
