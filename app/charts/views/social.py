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

def get_comments_per_day(name):

    query = Social.objects.filter(name=name).order_by('date')

    data = {}
    data['name'] = name
    data['data'] = {}

    for item in query:

        item_date = datetime.strftime(item.date, '%Y-%m-%d')
        data['data'][item_date] = ( item.comments_per_hour * 24 )

    #print(f'[DEBUG] {data}', flush=True)
    return data

def get_posts_per_day(name):

    query = Social.objects.filter(name=name).order_by('date')

    data = {}
    data['name'] = name
    data['data'] = {}

    for item in query:

        item_date = datetime.strftime(item.date, '%Y-%m-%d')
        data['data'][item_date] = ( item.posts_per_hour * 24 )

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

def get_transactions_data():

    query = DailyData.objects.order_by('date')

    data = {}
    data['data'] = {}

    for item in query:

        item_date = datetime.strftime(item.date, '%Y-%m-%d')
        data['data'][item_date] = { 'monero' : item.xmr_transactions }

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

            if total_subscribers == previous_subscribers:
                increase_percentage = ''
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

def social_transactions_percentage(request):
    '''Total Number of Reddit Subscribers for Monero and Number of Transactions'''

    monero_subscribers = get_subscriber_count("Monero")

    monero_transactions = get_transactions_data()

    previous_subscribers = 0

    xmr_subscribers = []
    xmr_transactions = []
    xmr_dates = []

    for x in monero_subscribers['data']:

        subscribers = monero_subscribers['data'][x]
        try:
            transactions = monero_transactions['data'][x]['monero']
        except KeyError as error:
            transactions = 0

        xmr_dates.append(x)

        if subscribers > previous_subscribers:
            xmr_subscribers.append(subscribers)
            previous_subscribers = subscribers
        else:
            xmr_subscribers.append(previous_subscribers)

        if transactions > 100:
            xmr_transactions.append(transactions)
        else:
            xmr_transactions.append('')

    previous_subcribers = locale._format('%.0f', previous_subscribers, grouping=True)

    context = {
            'dates': xmr_dates,
            'social_xmr': xmr_subscribers,
            'last_xmr': previous_subscribers,
            'now_transactions': transactions,
            'transactions': xmr_transactions
            }
    return render(request, 'charts/social_transactions_percentage.html', context)

def social_comments_per_day(request):
    '''Comments per day on Subreddits /Bitcoin and /CryptoCurrency'''

    monero_comments = get_comments_per_day('Monero')
    bitcoin_comments = get_comments_per_day('Bitcoin')
    crypto_comments = get_comments_per_day('CryptoCurrency')

    def comments_per_day_data(comments):

        dates = []
        comments_data = []
        previous_comments = 0

        for x in comments['data']:

            dates.append(x)
            comments_per_day = comments['data'][x]

            if comments_per_day < previous_comments:

                comments_data.append(previous_comments)
            else:
                comments_data.append(comments_per_day)
                previous_comments = comments_per_day

        return [dates, comments_data, previous_comments]

    monero = comments_per_day_data(monero_comments)
    bitcoin = comments_per_day_data(bitcoin_comments)
    crypto = comments_per_day_data(crypto_comments)

    context = {
            'dates': monero[0],
            'social_xmr': monero[1],
            'social_btc': bitcoin[1],
            'social_crypto': crypto[1],
            'last_xmr': monero[2],
            'last_btc': bitcoin[2],
            'last_crypto': crypto[2]
            }
    return render(request, 'charts/social_comments_per_day.html', context)

def social_posts_per_day(request):
    '''Posts per day on Subreddits /Bitcoin and /CryptoCurrency & Posts per day on Reddit /Monero'''

    monero_posts = get_posts_per_day('Monero')
    bitcoin_posts = get_posts_per_day('Bitcoin')
    crypto_posts = get_posts_per_day('CryptoCurrency')

    def posts_per_day_data(posts):

        dates = []
        posts_data = []
        previous_posts = 0

        for x in posts['data']:

            dates.append(x)
            posts_per_day = posts['data'][x]

            if posts_per_day < previous_posts:

                posts_data.append(previous_posts)
            else:
                posts_data.append(posts_per_day)
                previous_posts = posts_per_day

        return [dates, posts_data, previous_posts]

    monero = posts_per_day_data(monero_posts)
    bitcoin = posts_per_day_data(bitcoin_posts)
    crypto = posts_per_day_data(crypto_posts)

    context = {
            'dates': monero[0],
            'social_xmr': monero[1],
            'social_btc': bitcoin[1],
            'social_crypto': crypto[1],
            'last_xmr': monero[2],
            'last_btc': bitcoin[2],
            'last_crypto': crypto[2]
            }
    return render(request, 'charts/social_posts_per_day.html', context)
