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
#   Marketcap Charts
####################################################################################

def dominance(request):
    '''Monero's Marketcap Dominance (%)'''

    values = []
    pricexmr = []
    dates = []
    now_value = 0
    maximum = 0

    coin_data = Coin.objects.order_by('date').filter(name='xmr')

    for data_point in coin_data:

        data_point_date = datetime.datetime.strftime(data_point.date, '%Y-%m-%d')

        try:
            dominance = Dominance.objects.get(date=data_point_date)

            if dominance.dominance > 0:
                values.append(dominance.dominance)
                now_value = dominance.dominance

                if now_value > maximum:
                    maximum = now_value
            else:
                values.append('')

        except Exception as error:
            #print(f'[ERRPR] Error loading Dominance: {error}')
            values.append('')

        if data_point.priceusd > 0.001:
            pricexmr.append(data_point.priceusd)
        else:
            pricexmr.append('')

        data_point.date = datetime.datetime.strftime(data_point.date, '%Y-%m-%d')
        dates.append(data_point.date)

    yesterday = date.today() - timedelta(1)
    yesterday = datetime.datetime.strftime(yesterday, '%Y-%m-%d')

    if data_point.date == yesterday:
        today = date.today()
        today = datetime.datetime.strftime(today, '%Y-%m-%d')
        try:
            dominance = list(Dominance.objects.order_by('-date'))[0]
            if str(dominance.date) == str(today):
                now_value = dominance.dominance
                dates.append(today)
                values.append(now_value)
                if now_value > maximum:
                    maximum = now_value
        except Exception as error:
            print(f'[ERROR] An error occured: {error}')

    now_value = locale._format('%.2f', now_value, grouping=True)
    maximum = locale._format('%.2f', maximum, grouping=True)

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'charts/dominance.html', context)

def monerodominance(request):
    '''Monero's Dominance Over Other 'Privacy' Coins (%)'''
    data = DailyData.objects.order_by('date')
    dates = []
    marketcaps = []
    xmr_dominance = []
    now_marketcap = 0
    now_dominance = 0
    top_marketcap = 0
    top_dominance = 0
    zec_cap = 0
    dash_cap = 0
    grin_cap = 0

    for item in data:
        marketcap = 0
        dominance = 0
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.zcash_marketcap > 1000000:
            zec_cap = item.zcash_marketcap
            marketcap += zec_cap
        else:
            marketcap += zec_cap

        if item.dash_marketcap > 1000000:
            dash_cap = item.dash_marketcap
            marketcap += dash_cap
        else:
            marketcap += dash_cap

        if item.grin_marketcap > 1000000:
            grin_cap = item.grin_marketcap
            marketcap += grin_cap
        else:
            marketcap += grin_cap

        if item.xmr_marketcap > 1000000:
            marketcap += item.xmr_marketcap
            dominance = 100*item.xmr_marketcap/marketcap

        now_marketcap = marketcap
        now_dominance = dominance

        if now_marketcap > top_marketcap:
            top_marketcap = now_marketcap
        if now_dominance > top_dominance:
            top_dominance = now_dominance

        if marketcap > 3000000:
            marketcaps.append(marketcap)
        else:
            marketcaps.append('')

        if dominance > 0:
            xmr_dominance.append(dominance)
        else:
            xmr_dominance.append('')

    now_marketcap = '$'+locale._format('%.0f', now_marketcap, grouping=True)
    now_dominance = locale._format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale._format('%.0f', top_marketcap, grouping=True)
    top_dominance = locale._format('%.2f', top_dominance, grouping=True) + '%'

    context = {'marketcaps': marketcaps, 'xmr_dominance': xmr_dominance, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates}
    return render(request, 'charts/monerodominance.html', context)

def privacydominance(request):
    '''Total Dominance of Privacy Coins Over the Cryptocurrency Market (%)'''
    data = DailyData.objects.order_by('date')
    dates = []
    marketcaps = []
    dominances = []
    now_marketcap = 0
    now_dominance = 0
    top_marketcap = 0
    top_dominance = 0

    for item in data:
        marketcap = 0
        dominance = 0
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.zcash_marketcap > 100000:
            marketcap += item.zcash_marketcap

        if item.dash_marketcap > 100000:
            marketcap += item.dash_marketcap

        if item.grin_marketcap > 100000:
            marketcap += item.grin_marketcap

        if item.xmr_marketcap > 100000:
            marketcap += item.xmr_marketcap
            try:
                xmr_dominance = Dominance.objects.get(date=item.date)
                dominance = marketcap*xmr_dominance.dominance/item.xmr_marketcap
            except:
                dominance = now_dominance

        now_marketcap = marketcap
        now_dominance = dominance

        if now_marketcap > top_marketcap:
            top_marketcap = now_marketcap
        if now_dominance > top_dominance:
            top_dominance = now_dominance

        if marketcap > 300000:
            marketcaps.append(marketcap)
        else:
            marketcaps.append('')

        if dominance > 0:
            dominances.append(dominance)
        else:
            dominances.append('')

    now_marketcap = '$'+locale._format('%.0f', now_marketcap, grouping=True)
    now_dominance = locale._format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale._format('%.0f', top_marketcap, grouping=True)
    top_dominance = locale._format('%.2f', top_dominance, grouping=True) + '%'

    context = {'marketcaps': marketcaps, 'dominances':dominances, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates}
    return render(request, 'charts/privacydominance.html', context)

def rank(request):
    '''Monero's Marketcap Rank'''

    symbol = 'xmr'
    values = []
    pricexmr = []
    dates = []
    now_value = 25
    maximum = 100

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        try:
            rank = Rank.objects.get(date=coin.date)
            if rank.rank > 0:
                values.append(rank.rank)
                now_value = rank.rank
                if now_value < maximum:
                    maximum = now_value
            else:
                values.append(now_value)
        except:
            values.append(now_value)

        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append('')

        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

    yesterday = date.today() - timedelta(1)
    yesterday = datetime.datetime.strftime(yesterday, '%Y-%m-%d')
    if coin.date == yesterday:
        today = date.today()
        today = datetime.datetime.strftime(today, '%Y-%m-%d')
        try:
            rank = list(Rank.objects.order_by('-date'))[0]
            if str(rank.date) == str(today):
                now_value = rank.rank
                dates.append(today)
                values.append(now_value)
                if now_value < maximum:
                    maximum = now_value
        except:
            pass

    if now_value == 1:
        now_value = locale._format('%.0f', now_value, grouping=True) + 'st'
    if now_value == 2:
        now_value = locale._format('%.0f', now_value, grouping=True) + 'nd'
    if now_value == 3:
        now_value = locale._format('%.0f', now_value, grouping=True) + 'rd'
    if now_value > 3:
        now_value = locale._format('%.0f', now_value, grouping=True) + 'th'
    if maximum == 1:
        maximum = locale._format('%.0f', maximum, grouping=True) + 'st'
    if maximum == 2:
        maximum = locale._format('%.0f', maximum, grouping=True) + 'nd'
    if maximum == 3:
        maximum = locale._format('%.0f', maximum, grouping=True) + 'rd'
    if maximum > 3:
        maximum = locale._format('%.0f', maximum, grouping=True) + 'th'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'charts/rank.html', context)

def marketcap(request):
    '''Privacy coins Marketcap (USD)'''
    data = DailyData.objects.order_by('date')

    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.zcash_marketcap > 1000000:
            zcash.append(item.zcash_marketcap)
            now_zcash = item.zcash_marketcap
        else:
            zcash.append('')

        if item.dash_marketcap > 1000000:
            dash.append(item.dash_marketcap)
            now_dash = item.dash_marketcap
        else:
            dash.append('')

        if item.xmr_marketcap > 1000000:
            xmr.append(item.xmr_marketcap)
            now_xmr = item.xmr_marketcap
        else:
            xmr.append('')

        if item.grin_marketcap > 1000000:
            grin.append(item.grin_marketcap)
            now_grin = item.grin_marketcap
        else:
            grin.append('')

    now_dash = '$'+locale._format('%.0f', now_dash, grouping=True)
    now_grin = '$'+locale._format('%.0f', now_grin, grouping=True)
    now_zcash = '$'+locale._format('%.0f', now_zcash, grouping=True)
    now_xmr = '$'+locale._format('%.0f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr,
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/marketcap.html', context)

def privacymarketcap(request):
    '''Total Marketcap of Privacy Coins (USD)'''
    data = DailyData.objects.order_by('date')

    dates = []
    marketcaps = []
    xmr_marketcaps = []
    now_marketcap = 0
    now_dominance = 0
    top_marketcap = 0
    top_dominance = 0

    for item in data:
        marketcap = 0
        dominance = 0
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.zcash_marketcap > 1000000:
            marketcap += item.zcash_marketcap

        if item.dash_marketcap > 1000000:
            marketcap += item.dash_marketcap

        if item.grin_marketcap > 1000000:
            marketcap += item.grin_marketcap

        if item.xmr_marketcap > 1000000:
            marketcap += item.xmr_marketcap
            try:
                xmr_dominance = Dominance.objects.get(date=item.date)
                dominance = marketcap*xmr_dominance.dominance/item.xmr_marketcap
            except:
                dominance = now_dominance

            xmr_marketcaps.append(item.xmr_marketcap)
        else:
            xmr_marketcaps.append('')

        now_marketcap = marketcap
        now_dominance = dominance

        if now_marketcap > top_marketcap:
            top_marketcap = now_marketcap
        if now_dominance > top_dominance:
            top_dominance = now_dominance

        if marketcap > 3000000:
            marketcaps.append(marketcap)
        else:
            marketcaps.append('')

    now_marketcap = '$'+locale._format('%.0f', now_marketcap, grouping=True)
    now_dominance = locale._format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale._format('%.0f', top_marketcap, grouping=True)
    top_dominance = locale._format('%.2f', top_dominance, grouping=True) + '%'

    context = {'marketcaps': marketcaps, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates, 'xmr_marketcaps': xmr_marketcaps}
    return render(request, 'charts/privacymarketcap.html', context)
