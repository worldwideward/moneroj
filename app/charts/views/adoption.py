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
    new_merchants_accepting_bitcoin = []
    new_merchants_accepting_ethereum = []
    new_merchants_accepting_bitcoincash = []
    new_merchants_accepting_litecoin = []
    new_merchants_accepting_ripple = []
    new_merchants_accepting_dash = []
    new_merchants_accepting_monero = []

    adoption_data = list(Adoption.objects.all())

    for item in adoption_data:

        previous_item_key = adoption_data.index(item) - 1

        if previous_item_key != -1:

            dates.append(item.date.strftime("%Y-%m-%d"))

            previous_item = adoption_data[previous_item_key]

            new_merchants_bitcoin = item.merchants_accepting_bitcoin - previous_item.merchants_accepting_bitcoin
            new_merchants_ethereum = item.merchants_accepting_ethereum - previous_item.merchants_accepting_ethereum
            new_merchants_bitcoincash = item.merchants_accepting_bitcoincash - previous_item.merchants_accepting_bitcoincash
            new_merchants_litecoin = item.merchants_accepting_litecoin - previous_item.merchants_accepting_litecoin
            new_merchants_ripple = item.merchants_accepting_ripple - previous_item.merchants_accepting_ripple
            new_merchants_dash = item.merchants_accepting_dash - previous_item.merchants_accepting_dash
            new_merchants_monero = item.merchants_accepting_monero - previous_item.merchants_accepting_monero

            new_merchants_accepting_bitcoin.append(new_merchants_bitcoin)
            new_merchants_accepting_ethereum.append(new_merchants_ethereum)
            new_merchants_accepting_bitcoincash.append(new_merchants_bitcoincash)
            new_merchants_accepting_litecoin.append(new_merchants_litecoin)
            new_merchants_accepting_ripple.append(new_merchants_ripple)
            new_merchants_accepting_dash.append(new_merchants_dash)
            new_merchants_accepting_monero.append(new_merchants_monero)
        else:
            print("[WARN] first item in list", flush=True)

    context = {
            'dates': dates,
            'data1': new_merchants_accepting_bitcoin,
            'data2': new_merchants_accepting_monero,
            'data3': new_merchants_accepting_ethereum,
            'data4': new_merchants_accepting_bitcoincash,
            'data5': new_merchants_accepting_litecoin,
            'data6': new_merchants_accepting_ripple,
            'data7': new_merchants_accepting_dash
            }
    return render(request, 'charts/merchants_increase.html', context)

def merchants_percentage(request):
    '''Increase in number of merchants accepting cryptocurrency (percentage)'''

    dates = []
    new_merchants_accepting_bitcoin = []
    new_merchants_accepting_ethereum = []
    new_merchants_accepting_bitcoincash = []
    new_merchants_accepting_litecoin = []
    new_merchants_accepting_ripple = []
    new_merchants_accepting_dash = []
    new_merchants_accepting_monero = []

    adoption_data = list(Adoption.objects.all())

    for item in adoption_data:

        previous_item_key = adoption_data.index(item) - 1

        if previous_item_key != -1:

            dates.append(item.date.strftime("%Y-%m-%d"))

            previous_item = adoption_data[previous_item_key]

            new_merchants_bitcoin = (( item.merchants_accepting_bitcoin - previous_item.merchants_accepting_bitcoin) / item.merchants_accepting_bitcoin ) * 100
            new_merchants_ethereum = (( item.merchants_accepting_ethereum - previous_item.merchants_accepting_ethereum) / item.merchants_accepting_ethereum ) * 100
            new_merchants_bitcoincash = (( item.merchants_accepting_bitcoincash - previous_item.merchants_accepting_bitcoincash) / item.merchants_accepting_bitcoincash ) * 100
            new_merchants_litecoin = (( item.merchants_accepting_litecoin - previous_item.merchants_accepting_litecoin) / item.merchants_accepting_litecoin ) * 100
            new_merchants_ripple = (( item.merchants_accepting_ripple - previous_item.merchants_accepting_ripple) / item.merchants_accepting_ripple ) * 100
            new_merchants_dash = (( item.merchants_accepting_dash - previous_item.merchants_accepting_dash) / item.merchants_accepting_dash ) * 100
            new_merchants_monero = (( item.merchants_accepting_monero - previous_item.merchants_accepting_monero) / item.merchants_accepting_monero ) * 100

            new_merchants_accepting_bitcoin.append(new_merchants_bitcoin)
            new_merchants_accepting_ethereum.append(new_merchants_ethereum)
            new_merchants_accepting_bitcoincash.append(new_merchants_bitcoincash)
            new_merchants_accepting_litecoin.append(new_merchants_litecoin)
            new_merchants_accepting_ripple.append(new_merchants_ripple)
            new_merchants_accepting_dash.append(new_merchants_dash)
            new_merchants_accepting_monero.append(new_merchants_monero)
        else:
            print("[WARN] first item in list", flush=True)

    context = {
            'dates': dates,
            'data1': new_merchants_accepting_bitcoin,
            'data2': new_merchants_accepting_monero,
            'data3': new_merchants_accepting_ethereum,
            'data4': new_merchants_accepting_bitcoincash,
            'data5': new_merchants_accepting_litecoin,
            'data6': new_merchants_accepting_ripple,
            'data7': new_merchants_accepting_dash
            }
    return render(request, 'charts/merchants_percentage.html', context)
