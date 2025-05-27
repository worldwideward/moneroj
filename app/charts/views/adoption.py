'''Views module'''

import locale

from datetime import date
from django.shortcuts import render
from django.conf import settings

from charts.models import Usage
from charts.models import Adoption
from charts.spreadsheets import SpreadSheetManager, PandasSpreadSheetManager

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

sheets = PandasSpreadSheetManager()
CSV_DATA_SHEET = settings.CSV_DATA_SHEET

####################################################################################
#   Adoption Charts
####################################################################################

def coincards(request):
    '''Coincards Usage (%)'''

    dates = []
    data_btc = []
    data_xmr = []
    data_eth = []
    data_oth = []
    now_xmr = 0
    now_btc = 0

    usage_data = list(Usage.objects.all())

    for item in usage_data:

        date = item.date
        btc = item.bitcoin_pct
        xmr = item.monero_pct
        eth = item.ethereum_pct
        oth = item.others_pct

        dates.append(date.strftime("%Y-%m-%d"))
        data_btc.append(btc)
        data_xmr.append(xmr)
        data_eth.append(eth)
        data_oth.append(oth)
        now_btc = btc
        now_xmr = xmr
        now_eth = eth
        now_others = oth

    now_btc = locale._format('%.1f', now_btc, grouping=True)
    now_xmr = locale._format('%.1f', now_xmr, grouping=True)
    now_eth = locale._format('%.1f', now_eth, grouping=True)
    now_others = locale._format('%.1f', now_others, grouping=True)

    context = {
            'dates': dates,
            'now_btc': now_btc,
            'now_xmr': now_xmr,
            'now_eth': now_eth,
            'now_others': now_others,
            'data1': data_btc,
            'data2': data_xmr,
            'data3': data_eth,
            'data4': data_oth
            }

    return render(request, 'charts/coincards.html', context)

def merchants(request):
    ''' Merchants accepting cryptocurrency (absolute numbers)'''

    dates = []
    merchants_accepting_bitcoin = []
    merchants_accepting_ethereum = []
    merchants_accepting_bitcoincash = []
    merchants_accepting_litecoin = []
    merchants_accepting_ripple = []
    merchants_accepting_dash = []
    merchants_accepting_monero = []

    adoption_data = list(Adoption.objects.all())

    for item in adoption_data:

        dates.append(item.date.strftime("%Y-%m-%d"))

        merchants_accepting_bitcoin.append(item.merchants_accepting_bitcoin)
        merchants_accepting_ethereum.append(item.merchants_accepting_ethereum)
        merchants_accepting_bitcoincash.append(item.merchants_accepting_bitcoincash)
        merchants_accepting_litecoin.append(item.merchants_accepting_litecoin)
        merchants_accepting_ripple.append(item.merchants_accepting_ripple)
        merchants_accepting_dash.append(item.merchants_accepting_dash)
        merchants_accepting_monero.append(item.merchants_accepting_monero)

    context = {
            'dates': dates,
            'data1': merchants_accepting_bitcoin,
            'data2': merchants_accepting_monero,
            'data3': merchants_accepting_ethereum,
            'data4': merchants_accepting_bitcoincash,
            'data5': merchants_accepting_litecoin,
            'data6': merchants_accepting_ripple,
            'data7': merchants_accepting_dash
            }
    return render(request, 'charts/merchants.html', context)

def merchants_increase(request):
    '''Monthly increase in number of merchants accepting cryptocurrency (absolute numbers)'''
    dates = []
    data1 = []
    data2 = []
    data3 = []
    data4 = []
    data5 = []
    data6 = []
    data7 = []
    now_xmr = 0
    now_btc = 0
    now_eth = 0

    values_mat = sheets.get_values(CSV_DATA_SHEET, "Sheet4", start=(1, 0), end=(99, 8))

    for k in range(0,len(values_mat)):

        date = values_mat[k][0]
        value1 = values_mat[k][1]
        value2 = values_mat[k][2]
        value3 = values_mat[k][3]
        value4 = values_mat[k][4]
        value5 = values_mat[k][5]
        value6 = values_mat[k][6]
        value7 = values_mat[k][7]

        dates.append(date.strftime("%Y-%m-%d"))
        data1.append(int(value1))
        data2.append(int(value2))
        data3.append(int(value3))
        data4.append(int(value4))
        data5.append(int(value5))
        data6.append(int(value6))
        data7.append(int(value7))
        now_btc = int(value1)
        now_xmr = int(value2)
        now_eth = int(value3)

    now_btc = locale._format('%.0f', now_btc, grouping=True)
    now_xmr = locale._format('%.0f', now_xmr, grouping=True)
    now_eth = locale._format('%.0f', now_eth, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'charts/merchants_increase.html', context)

def merchants_percentage(request):
    '''Increase in number of merchants accepting cryptocurrency (percentage)'''
    dates = []
    data1 = []
    data2 = []
    data3 = []
    data4 = []
    data5 = []
    data6 = []
    data7 = []
    now_xmr = 0
    now_btc = 0
    now_eth = 0

    values_mat = sheets.get_values(CSV_DATA_SHEET, "Sheet2", start=(1, 0), end=(99, 8))

    for k in range(0,len(values_mat)):

        date = values_mat[k][0]
        value1 = values_mat[k][1]
        value2 = values_mat[k][2]
        value3 = values_mat[k][3]
        value4 = values_mat[k][4]
        value5 = values_mat[k][5]
        value6 = values_mat[k][6]
        value7 = values_mat[k][7]

        dates.append(date.strftime("%Y-%m-%d"))
        data1.append(value1)
        data2.append(value2)
        data3.append(value3)
        data4.append(value4)
        data5.append(value5)
        data6.append(value6)
        data7.append(value7)
        now_btc = value1
        now_xmr = value2
        now_eth = value3

    now_btc = locale._format('%.1f', now_btc, grouping=True)
    now_xmr = locale._format('%.1f', now_xmr, grouping=True)
    now_eth = locale._format('%.1f', now_eth, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'charts/merchants_percentage.html', context)
