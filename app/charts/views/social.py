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

    data = {}
    data['name'] = name
    data['data'] = {}

    for item in query:

        item_date = datetime.strftime(item.date, '%Y-%m-%d')
        data['data'][item_date] = item.subscriber_count

    #print(f'[DEBUG] {data}', flush=True)
    return data

def get_market_cap_data():

    query = DailyData.objects.order_by('date')

    data = {}
    data['data'] = {}

    for item in query:

        item_date = datetime.strftime(item.date, '%Y-%m-%d')
        data['data'][item_date] = { 'monero' : item.xmr_marketcap , 'bitcoin': item.btc_marketcap }

    #print(f'[DEBUG] {data}', flush=True)
    return data

def social(request):
    '''Total Reddit subscribers chart'''

    monero_subscribers = get_subscriber_count("Monero")
    bitcoin_subscribers = get_subscriber_count("Bitcoin")

    xmr_dates = []
    xmr_subscribers = []
    btc_dates = []
    btc_subscribers = []

    for x in monero_subscribers['data']:

        xmr_dates.append(x)
        xmr_subscribers.append(monero_subscribers['data'][x])

    for x in bitcoin_subscribers['data']:

        btc_dates.append(x)
        btc_subscribers.append(bitcoin_subscribers['data'][x])

    context = {
            'monero_dates': xmr_dates,
            'monero': xmr_subscribers,
            'bitcoin_dates': btc_dates,
            'bitcoin': btc_subscribers }

    return render(request, 'charts/social.html', context)

def social_dividend(request):
    '''Marketcap Divided by Number of Reddit Subscribers'''

    monero_subscribers = get_subscriber_count("Monero")
    bitcoin_subscribers = get_subscriber_count("Bitcoin")

    market_cap_data = get_market_cap_data()

    dates = []
    monero_market_cap_per_subscriber = []
    bitcoin_market_cap_per_subscriber = []

    for x in monero_subscribers['data']:

        try:
            xmr_subscribers = monero_subscribers['data'][x]

            if xmr_subscribers == 0:
                xmr_subscribers = 1
        except KeyError as error:
            xmr_subscribers = 1
        try:
            btc_subscribers = bitcoin_subscribers['data'][x]

            if btc_subscribers == 0:
                btc_subscribers = 1
        except KeyError as error:
            btc_subscribers = 1

        try:
            xmr_marketcap = market_cap_data['data'][x]['monero']
        except KeyError as error:
            xmr_marketcap = 0

        try:
            btc_marketcap = market_cap_data['data'][x]['bitcoin']
        except KeyError as error:
            btc_marketcap = 0

        xmr_market_cap_per_subscriber = xmr_marketcap / xmr_subscribers
        btc_market_cap_per_subscriber = btc_marketcap / btc_subscribers

        dates.append(x)
        monero_market_cap_per_subscriber.append(xmr_market_cap_per_subscriber)
        bitcoin_market_cap_per_subscriber.append(btc_market_cap_per_subscriber)

    context = {
            'dates': dates,
            'social_xmr': monero_market_cap_per_subscriber,
            'social_btc': bitcoin_market_cap_per_subscriber,
            }
    return render(request, 'charts/social_dividend.html', context)

def social_subscribers_percentage(request):
    '''Reddit Subscribers of /Monero as a Percentage of /Bitcoin'''

    monero_subscribers = get_subscriber_count("Monero")
    bitcoin_subscribers = get_subscriber_count("Bitcoin")
    cryptocurrency_subscribers = get_subscriber_count("CryptoCurrency")

    dates = []
    xmr_subscriber_percentage = []
    crypto_subscriber_percentage = []
    last_xmr = 0
    last_crypto = 0

    for item in monero_subscribers['data']:

        dates.append(item)

        try:
            xmr_subscribers = monero_subscribers['data'][item]
        except KeyError as error:
            xmr_subscribers = 0

        try:
            crypto_subscribers = cryptocurrency_subscribers['data'][item]
        except KeyError as error:
            crypto_subscribers = 0

        try:
            btc_subscribers = bitcoin_subscribers['data'][item]
        except KeyError as error:
            btc_subscribers = 1

        if btc_subscribers > 0 and xmr_subscribers > 0:
            last_xmr = xmr_subscribers/btc_subscribers
            xmr_subscriber_percentage.append(last_xmr)
        else:
            xmr_subscriber_percentage.append(last_xmr)

        if btc_subscribers > 0 and crypto_subscribers > 0:
            last_crypto = crypto_subscribers/btc_subscribers
            crypto_subscriber_percentage.append(last_crypto)
        else:
            crypto_subscriber_percentage.append(last_crypto)

    last_xmr = locale._format('%.1f', last_xmr, grouping=True)+ '%'
    last_crypto = locale._format('%.1f', last_crypto, grouping=True)+ '%'

    context = {
            'dates': dates,
            'social_xmr': xmr_subscriber_percentage,
            'social_crypto': crypto_subscriber_percentage,
            }

    return render(request, 'charts/social_subscribers_percentage.html', context)

def social_monthly_increase(request):
    '''/Bitcoin, /CryptoCurrency and /Monero Monthly New Subscribers'''

    monero_subscribers = get_subscriber_count("Monero")
    bitcoin_subscribers = get_subscriber_count("Bitcoin")
    cryptocurrency_subscribers = get_subscriber_count("CryptoCurrency")

    def monthly_increase_data(subscribers):

        dates = []
        previous_subscribers = 0
        new_subscribers = []
        increase = []

        for item in subscribers['data']:

            dates.append(item)
            total_subscribers = subscribers['data'][item]

            new_subscriber_amount = total_subscribers - previous_subscribers

            if new_subscriber_amount < 0:
                new_subscriber_amount = previous_subscribers

            new_subscribers.append(new_subscriber_amount)

            if total_subscribers > previous_subscribers:
                increase_percentage = ( (total_subscribers - previous_subscribers) / total_subscribers ) * 100
                increase.append(increase_percentage)

            if total_subscribers < previous_subscribers:
                increase_percentage = ( (previous_subscribers - total_subscribers) / previous_subscribers ) * 100
                increase.append(increase_percentage)

            previous_subscribers = subscribers['data'][item]

        return [dates, new_subscribers, increase]

    xmr_data = monthly_increase_data(monero_subscribers)
    btc_data = monthly_increase_data(bitcoin_subscribers)
    crypto_data = monthly_increase_data(cryptocurrency_subscribers)

    context = {
            'dates': xmr_data[0],
            'newcomers_xmr': xmr_data[1],
            'newcomers_btc': btc_data[1],
            'newcomers_crypto': crypto_data[1],
            'speed_xmr': xmr_data[2],
            'speed_btc': btc_data[2],
            'speed_crypto': crypto_data[2]
            }
    print(f'[DEBUG] {context}', flush=True)
    return render(request, 'charts/social_monthly_increase.html', context)

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
