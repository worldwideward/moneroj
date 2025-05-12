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
#   Views
####################################################################################

def dread_subscribers(request):
    '''Dread Subscribes (Darknet forum)'''

    dates = []
    data1 = []
    data2 = []
    now_xmr = 0
    now_btc = 0
    values_mat = sheets.get_values("zcash_bitcoin.ods", "Sheet6", start=(1, 0), end=(99, 4))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            if not value1 or not value2:
                break
            else:
                print(date, flush=True)
                dates.append(date.strftime("%Y-%m-%d"))
                data1.append(int(value1))
                data2.append(int(value2))
                now_xmr = int(value2)
                now_btc = int(value1)
        else:
            break

    dominance = 100*int(value2)/(int(value2)+int(value1))

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)
    dominance = locale._format('%.2f', dominance, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr, 'data1': data1, "data2": data2, "dominance": dominance}
    return render(request, 'charts/dread_subscribers.html', context)
