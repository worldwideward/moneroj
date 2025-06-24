'''Views module'''

import locale
from datetime import date
from datetime import timedelta
from datetime import datetime
from django.shortcuts import render
from charts.models import DailyData
from charts.models import Social

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

def get_subscriber_count(name):

    query = Social.objects.filter(name=name).order_by('date')
    dates = []
    subscriber_count = []

    for item in query:

        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        subscriber_count.append(item.subscriber_count)

    data = { 'name': name, 'dates': dates, 'subscribers': subscriber_count }

    return data

def get_market_cap_data():

    query = DailyData.objects.order_by('date')
    dates = []
    monero_marketcaps = []
    bitcoin_marketcaps = []

    for item in query:

        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        monero_marketcaps.append(item.xmr_marketcap)
        bitcoin_marketcaps.append(item.btc_marketcap)

    data = { 'monero' : monero_marketcaps, 'bitcoin': bitcoin_marketcaps, 'dates': dates }

    return data

def social(request):
    '''Total Reddit subscribers chart'''

    monero = get_subscriber_count("Monero")
    bitcoin = get_subscriber_count("Bitcoin")

    context = {
            'monero_dates': monero['dates'],
            'monero': monero['subscribers'],
            'bitcoin_dates': bitcoin['dates'],
            'bitcoin': bitcoin['subscribers'] }

    return render(request, 'charts/social.html', context)

def social2(request):
    '''Marketcap Divided by Number of Reddit Subscribers'''

    monero = get_subscriber_count("Monero")
    bitcoin = get_subscriber_count("Bitcoin")

    market_cap_data = get_market_cap_data()

    dates = market_cap_data['dates']
    monero_market_cap_per_subscriber = []
    bitcoin_market_cap_per_subscriber = []

    monero_data_points = len(monero['dates'])
    bitcoin_data_points = len(bitcoin['dates'])

    monero_dates = monero['dates']
    monero_dates.reverse()
    market_cap_data['monero'].reverse()

    index = 0
    while index < monero_data_points:

        current_date = monero_dates[index]

        for date in dates:

            if current_date == date:

                    subscribers = monero['subscribers'][index]
                    market_cap = market_cap_data['monero'][index]
                    division = market_cap / subscribers

                    monero_market_cap_per_subscriber.append(division)

                    subscribers = bitcoin['subscribers'][index]
                    market_cap = market_cap_data['bitcoin'][index]
                    division = market_cap / subscribers

                    bitcoin_market_cap_per_subscriber.append(division)

        index =+ index + 1

    print(monero_market_cap_per_subscriber, flush=True)
    print(bitcoin_market_cap_per_subscriber, flush=True)

    context = {
            'dates': dates,
            'social_xmr': monero_market_cap_per_subscriber,
            'social_btc': bitcoin_market_cap_per_subscriber,
            }
    return render(request, 'charts/social2.html', context)

def social3(request):
    '''Reddit Subscribers of /Monero as a Percentage of /Bitcoin'''
    data = DailyData.objects.order_by('date')

    dates = []
    social_xmr = []
    social_crypto = []
    last_xmr = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriber_count > 0 and item.xmr_subscriber_count > 0:
            last_xmr = 100*(item.xmr_subscriber_count/item.btc_subscriber_count)
            social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

        if item.btc_subscriber_count > 0 and item.crypto_subscriber_count > 0:
            last_crypto = 100*(item.crypto_subscriber_count/item.btc_subscriber_count)
            social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale._format('%.1f', last_xmr, grouping=True)+ '%'
    last_crypto = locale._format('%.1f', last_crypto, grouping=True)+ '%'

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'last_xmr': last_xmr, 'last_crypto': last_crypto}
    return render(request, 'charts/social3.html', context)

def social4(request):
    '''/Bitcoin, /CryptoCurrency and /Monero Monthly New Subscribers'''
    data = DailyData.objects.order_by('date')
    dates = []
    dates2 = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        dates2.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriber_count > last_btc:
            social_btc.append(item.btc_subscriber_count)
            last_btc = item.btc_subscriber_count
        else:
            social_btc.append(last_btc)

        if item.xmr_subscriber_count > last_xmr:
            social_xmr.append(item.xmr_subscriber_count)
            last_xmr = item.xmr_subscriber_count
        else:
            social_xmr.append(last_xmr)

        if item.crypto_subscriber_count > last_crypto:
            social_crypto.append(item.crypto_subscriber_count)
            last_crypto = item.crypto_subscriber_count
        else:
            social_crypto.append(last_crypto)

    N = 30
    last_btc = ''
    speed_btc = []
    for i in range(len(social_btc)):
        if i < N:
            speed_btc.append(last_btc)
        else:
            if social_btc[i-N] != 0 and social_btc[i] - social_btc[i-N] != 0:
                last_btc = 100*(social_btc[i] - social_btc[i-N])/social_btc[i-N]
                if last_btc < 0.2:
                    last_btc = 0.2
                if last_btc > 1000:
                    last_btc = ''
            else:
                last_btc = ''
            speed_btc.append(last_btc)

    last_btc = ''
    newcomers_btc = []
    for i in range(len(social_btc)):
        if i < N:
            newcomers_btc.append(last_btc)
        else:
            last_btc = social_btc[i] - social_btc[i-N]
            if last_btc < 10:
                last_btc = ''
            newcomers_btc.append(last_btc)

    last_crypto = ''
    speed_crypto = []
    for i in range(len(social_crypto)):
        if i < N:
            speed_crypto.append(last_crypto)
        else:
            if social_crypto[i-N] != 0 and social_crypto[i] - social_crypto[i-N] != 0:
                last_crypto = 100*(social_crypto[i] - social_crypto[i-N])/social_crypto[i-N]
                if last_crypto < 0.2:
                    last_crypto = 0.2
                if last_crypto > 1000:
                    last_crypto = ''
            else:
                last_crypto = ''
            speed_crypto.append(last_crypto)

    last_crypto = ''
    newcomers_crypto = []
    for i in range(len(social_crypto)):
        if i < N:
            newcomers_crypto.append(last_crypto)
        else:
            last_crypto = social_crypto[i] - social_crypto[i-N]
            if last_crypto < 2:
                last_crypto = ''
            newcomers_crypto.append(last_crypto)


    last_xmr = ''
    speed_xmr = []
    for i in range(len(social_xmr)):
        if i < N:
            speed_xmr.append(last_xmr)
        else:
            if social_xmr[i-N] != 0 and social_xmr[i] - social_xmr[i-N] != 0:
                last_xmr = 100*(social_xmr[i] - social_xmr[i-N])/social_xmr[i-N]
                if last_xmr < 0.2:
                    last_xmr = 0.2
                if last_xmr > 1000:
                    last_xmr = ''
            else:
                last_xmr = ''
            speed_xmr.append(last_xmr)

    last_xmr = ''
    newcomers_xmr = []
    for i in range(len(social_xmr)):
        if i < N:
            newcomers_xmr.append(last_xmr)
        else:
            last_xmr = social_xmr[i] - social_xmr[i-N]
            if last_xmr < 0:
                last_xmr = ''
            newcomers_xmr.append(last_xmr)

    try:
        last_xmr = locale._format('%.0f', last_xmr, grouping=True)
        last_btc = locale._format('%.0f', last_btc, grouping=True)
        last_crypto = locale._format('%.0f', last_crypto, grouping=True)
    except:
        last_xmr = 0
        last_btc = 0
        last_crypto = 0

    context = {'dates': dates, 'speed_xmr': speed_xmr, 'speed_crypto': speed_crypto, 'speed_btc': speed_btc, 'newcomers_xmr': newcomers_xmr, 'newcomers_btc': newcomers_btc, 'newcomers_crypto': newcomers_crypto, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social4.html', context)

def social5(request):
    '''Total Number of Reddit Subscribers for Monero and Number of Transactions'''
    data = DailyData.objects.order_by('date')
    transactions = []
    dates = []
    social_xmr = []
    now_transactions = 0
    last_xmr = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.xmr_subscriber_count > last_xmr:
            social_xmr.append(item.xmr_subscriber_count)
            last_xmr = item.xmr_subscriber_count
        else:
            social_xmr.append(last_xmr)

        if item.xmr_transactions > 300:
            now_transactions = item.xmr_transactions
            transactions.append(now_transactions)
        else:
            transactions.append('')

    last_xmr = locale._format('%.0f', last_xmr, grouping=True)
    now_transactions = locale._format('%.0f', now_transactions, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'now_transactions': now_transactions, 'transactions': transactions}
    return render(request, 'charts/social5.html', context)

def social6(request):
    '''Comments per day on Subreddits /Bitcoin and /CryptoCurrency'''
    data = DailyData.objects.order_by('date')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_comments_per_hour*24 < last_btc/4:
            social_btc.append(last_btc)
        else:
            last_btc = item.btc_comments_per_hour*24
            social_btc.append(last_btc)

        if item.xmr_comments_per_hour*24 < last_xmr/4:
            social_xmr.append(last_xmr)
        else:
            last_xmr = item.xmr_comments_per_hour*24
            social_xmr.append(last_xmr)

        if item.crypto_comments_per_hour*24 < last_crypto/4:
            social_crypto.append(last_crypto)
        else:
            last_crypto = item.crypto_comments_per_hour*24
            social_crypto.append(last_crypto)

    last_xmr = locale._format('%.0f', last_xmr, grouping=True)
    last_btc = locale._format('%.0f', last_btc, grouping=True)
    last_crypto = locale._format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social6.html', context)

def social7(request):
    '''Posts per day on Subreddits /Bitcoin and /CryptoCurrency & Posts per day on Reddit /Monero'''
    data = DailyData.objects.order_by('date')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_posts_per_hour > 0:
            last_btc = item.btc_posts_per_hour*24
            social_btc.append(last_btc)
        else:
            social_btc.append(last_btc)

        if item.xmr_posts_per_hour > 0:
            last_xmr = item.xmr_posts_per_hour*24
            social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

        if item.crypto_posts_per_hour > 0:
            last_crypto = item.crypto_posts_per_hour*24
            social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale._format('%.0f', last_xmr, grouping=True)
    last_btc = locale._format('%.0f', last_btc, grouping=True)
    last_crypto = locale._format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social7.html', context)
