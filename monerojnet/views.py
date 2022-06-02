from os import readlink
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
import json
from .models import *
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import math
import locale
import pandas as pd
from operator import truediv
from datetime import timezone
import pygsheets
from django.contrib.auth.decorators import login_required
from requests import Session
from psaw import PushshiftAPI    #library Pushshift
from django.contrib.staticfiles.storage import staticfiles_storage  


###########################################
# Set some parameters 
###########################################

locale.setlocale(locale.LC_ALL, 'en_US.utf8')
# This loads Reddit stats about a subreddit
api = PushshiftAPI() 

###########################################
# Useful functions for admins
###########################################

# Get all history for metrics of a certain coin named as 'symbol'
# Only authorized users can download all price data via URL request
@login_required 
def get_history(request, symbol, start_time=None, end_time=None):
    update = True
    count = 0
    with open("settings.json") as file:
        data = json.load(file)
        file.close()

    if start_time and end_time:
        url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time + '&end_time=' + end_time
    else:
        url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"]

    while update: 
        response = requests.get(url)
        data = json.loads(response.text)
        data_aux = data['data']
        for item in data_aux:
            day, hour = str(item['time']).split('T')
            day = datetime.datetime.strptime(day, '%Y-%m-%d')
            day = datetime.datetime.strftime(day, '%Y-%m-%d')
            coin = Coin.objects.filter(name=symbol).filter(date=day)
            if coin:
                coin.delete()
            try:
                coin = Coin()
                coin.name = symbol
                coin.date = day
                coin.priceusd = float(item['PriceUSD'])
                coin.pricebtc = float(item['PriceBTC'])
                coin.inflation = float(item['IssContPctAnn'])
                coin.stocktoflow = (100/coin.inflation)**1.65
                coin.supply = float(item['SplyCur'])
                try:
                    coin.fee = float(item['FeeTotNtv'])
                except:
                    coin.fee = 0
                try:
                    coin.revenue = float(item['RevNtv'])
                except:
                    coin.revenue = 0
                try:
                    coin.hashrate = float(item['HashRate'])
                except:
                    coin.hashrate = 0
                try:
                    coin.transactions = float(item['TxCnt'])
                except:
                    coin.transactions = 0
                coin.save()
                count += 1
                print(str(symbol) + ' ' + str(coin.date))

            except:
                pass
        try:
            url = data['next_page_url']
            update = True
        except:
            update = False
            break

    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'monerojnet/maintenance.html', context)

# Populate database with rank history
# Only authorized users can do this
@login_required 
def load_rank(request, symbol):
    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet8')
    
    count = 0
    values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')
    print(len(values_mat))
    Rank.objects.all().delete()

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][1]:
            rank = Rank()
            rank.name = symbol
            rank.date = values_mat[k][0]
            rank.rank = int(values_mat[k][1].replace(',', '.'))
            if not(rank.rank) and not(rank.date):
                break
            else:
                rank.save()
                count += 1
        else:
            break

    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'monerojnet/maintenance.html', context)

# Populate database with dominance history
# Only authorized users can do this
@login_required 
def load_dominance(request, symbol):
    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet7')
    
    count = 0
    values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')
    #print(len(values_mat))
    Dominance.objects.all().delete()

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][1]:
            dominance = Dominance()
            dominance.name = symbol
            dominance.date = values_mat[k][0]
            dominance.dominance = float(values_mat[k][1].replace(',', '.'))
            if not(dominance.dominance) and not(dominance.date):
                break
            else:
                dominance.save()
                count += 1
        else:
            break

    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'monerojnet/maintenance.html', context)

# Import Reddit history from file on static folder
# Only authorized users can do this
@login_required 
def importer(request):
    count = 0
    Social.objects.all().delete()
    filename = staticfiles_storage.path('import.txt')
    with open(filename) as f:
        content = f.readlines()
        for line in content:
            data = json.loads(line)
            symbol = data['name']
            item = data['subscriberCountTimeSeries']
            dates = []
            subscriberCount = []
            commentsPerHour = []
            postsPerHour = []
            for unit in item:
                date_now = datetime.datetime.strptime('1970-01-01', '%Y-%m-%d')
                date_now += timedelta(int(unit['utcDay']))
                dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
                value = float(unit['count'])
                subscriberCount.append(value)
            item = data['commentsPerHourTimeSeries']
            for unit in item:
                value = float(unit['commentsPerHour'])
                commentsPerHour.append(value)
            item = data['postsPerHourTimeSeries']
            for unit in item:
                value = float(unit['postsPerHour'])
                postsPerHour.append(value)
                
            for i in range(len(dates)-1):
                social = Social()
                social.name = symbol
                social.date = dates[i]
                if i >= len(dates) - len(subscriberCount):
                    social.subscriberCount = subscriberCount[i-len(subscriberCount)]
                else: 
                    social.subscriberCount = 0
                if i >= len(dates) - len(commentsPerHour):
                    social.commentsPerHour = commentsPerHour[i-(len(dates) - len(commentsPerHour))]
                else: 
                    social.commentsPerHour = 0
                if i >= len(dates) - len(postsPerHour):
                    social.postsPerHour = postsPerHour[i-(len(dates) - len(postsPerHour))]
                else: 
                    social.postsPerHour = 0 
                social.save()
                count += 1

    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'monerojnet/maintenance.html', context)

# Erase all data for a certain coin
# Only authorized users can do this
@login_required 
def reset(request, symbol):
    coins = Coin.objects.filter(name=symbol).all().delete()
    
    message = 'All data for ' + str(symbol) + ' erased'
    context = {'message': message}
    return render(request, 'monerojnet/maintenance.html', context)

###########################################
# Other useful functions                  
###########################################

# Get most recent metrics from a data provider of your choice for 'symbol'
def get_latest_metrics(symbol):
    now = datetime.datetime.now()
    current_time = int(now.strftime("%H"))
    if current_time >= 3:
        yesterday = date.today() - timedelta(1)
        start_time = datetime.datetime.strftime(yesterday, '%Y-%m-%d')
        try:
            coin = Coin.objects.filter(name=symbol).get(date=yesterday)
            if coin:
                if (coin.inflation > 0) and (coin.priceusd > 0):
                    return False
                else:
                    coin.delete()
                    update = True
            else:
                update = True
        except:
            update = True
    else:
        return False

    count = 0
    with open("settings.json") as file:
        data = json.load(file)
        file.close()
        
    url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
    while update: 
        response = requests.get(url)
        data = json.loads(response.text)
        data_aux = data['data']
        for item in data_aux:
            day, hour = str(item['time']).split('T')
            day = datetime.datetime.strptime(day, '%Y-%m-%d')
            day = datetime.datetime.strftime(day, '%Y-%m-%d')
            coin = Coin.objects.filter(name=symbol).filter(date=day)
            if coin:
                coin.delete()
            try:
                coin = Coin()
                coin.name = symbol
                coin.date = day
                coin.priceusd = float(item['PriceUSD'])
                coin.pricebtc = float(item['PriceBTC'])
                coin.inflation = float(item['IssContPctAnn'])
                coin.stocktoflow = (100/coin.inflation)**1.65
                coin.supply = float(item['SplyCur'])
                try:
                    coin.fee = float(item['FeeTotNtv'])
                except:
                    coin.fee = 0
                try:
                    coin.revenue = float(item['RevNtv'])
                except:
                    coin.revenue = 0
                try:
                    coin.hashrate = float(item['HashRate'])
                except:
                    coin.hashrate = 0
                try:
                    coin.transactions = float(item['TxCnt'])
                except:
                    coin.transactions = 0
                coin.save()
                count += 1
                print(str(symbol) + ' ' + str(coin.date))

            except:
                pass
        try:
            url = data['next_page_url']
            update = True
        except:
            update = False
            break
            
    return count

# Get daily post on Reddit
def data_prep_posts(subreddit, start_time, end_time, filters, limit):
    if(len(filters) == 0):
        filters = ['id', 'author', 'created_utc', 'domain', 'url', 'title', 'num_comments'] 

    posts = list(api.search_submissions(subreddit=subreddit, after=start_time, before=end_time, filter=filters, limit=limit))

    return pd.DataFrame(posts)

# Get daily comments on Reddit
def data_prep_comments(term, start_time, end_time, filters, limit):
    if (len(filters) == 0):
        filters = ['id', 'author', 'created_utc','body', 'permalink', 'subreddit'] 

    comments = list(api.search_comments(q=term, after=start_time, before=end_time, filter=filters, limit=limit))
    return pd.DataFrame(comments) 

# Get latest price data for Monero
def get_latest_price():
    with open("settings.json") as file:
        data = json.load(file)

        url = data["metrics_provider"][0]["price_url"]
        parameters = {
            'convert':'USD',
        }
        headers = {
            'Accepts': 'application/json',
            data["metrics_provider"][0]["api_key_name"]: data["metrics_provider"][0]["api_key_value"],
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            data = False

        file.close()
    return data

# Get latest dominance value and update
def update_dominance(data):
    if not(data):
        #print('error updating dominance')
        return False
    else:
        dominance = Dominance()
        dominance.name = 'xmr'
        dominance.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        dominance.dominance = float(data['data']['XMR']['quote']['USD']['market_cap_dominance'])
        dominance.save()

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('Sheet7')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'B' + str(k + 3)
            wks.update_value(cell, dominance.dominance)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, dominance.date)
        else:
            #print('spreadsheet with the latest data already')
            return False

    #print('updated')
    return data

# Get latest rank value and update
def update_rank():
    data = get_latest_price()
    if not(data):
        return False
    else:
        rank = Rank()
        rank.name = 'xmr'
        rank.date = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        rank.rank = int(data['data']['XMR']['cmc_rank'])
        rank.save()

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('Sheet8')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,2), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'B' + str(k + 3)
            wks.update_value(cell, rank.rank)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, rank.date)
            #print('spreadsheet updated')
        else:
            #print('spreadsheet with the latest data already')
            return data

    #print('updated')
    return data

# Load Reddit api to check if there are new followers
def check_new_social(symbol):
    date_now = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    socials = Social.objects.filter(name=symbol).filter(date=date_now)

    if not(socials):
        print('getting new data')
        request = 'https://www.reddit.com/r/'+ symbol +'/about.json'
        response = requests.get(request, headers = {'User-agent': 'Checking new social data'})
        data = json.loads(response.content)    
        data = data['data']
        subscribers = data['subscribers']
        social = Social()
        social.name = symbol
        social.date = date_now
        social.subscriberCount = subscribers

        date_aux = date.today()
        date_aux = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        date_aux = datetime.datetime.strptime(date_aux, '%Y-%m-%d')
        timestamp1 = int(datetime.datetime.timestamp(date_aux))

        timestamp2 = int(timestamp1 - 86400)
        limit = 1000
        filters = []
        data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.postsPerHour = len(data)/24

        timestamp2 = int(timestamp1 - 7200)
        limit = 1000
        data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.commentsPerHour = len(data)/2
        social.save()
    return True

###########################################
# Views
###########################################

def index(request):
    dt = datetime.datetime.now(timezone.utc).timestamp()
    symbol = 'xmr'

    rank = list(Rank.objects.order_by('-date'))[1]
    if rank.date < date.today():
        print('here 1')
        data = update_rank()    
        dominance = list(Dominance.objects.order_by('-date'))[1]
        if dominance.date < date.today():
            data = update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[1]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'monerojnet/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    
    dt = 'index.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'monerojnet/index.html', context)

def pt(request):
    symbol = 'xmr'

    rank = list(Rank.objects.order_by('-date'))[1]
    if rank.date < date.today():
        data = update_rank()    
        dominance = list(Dominance.objects.order_by('-date'))[1]
        if dominance.date < date.today():
            data = update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[1]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'monerojnet/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'monerojnet/pt.html', context)

def fr(request):
    symbol = 'xmr'

    rank = list(Rank.objects.order_by('-date'))[1]
    if rank.date < date.today():
        data = update_rank()    
        dominance = list(Dominance.objects.order_by('-date'))[1]
        if dominance.date < date.today():
            data = update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[1]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'monerojnet/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'monerojnet/fr.html', context)

def artigos(request):
    context = {}
    return render(request, 'monerojnet/artigos.html', context)

def articles(request):
    context = {}
    return render(request, 'monerojnet/articles.html', context)

def social(request):
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
        if social.subscriberCount > last_btc:
            last_btc = social.subscriberCount
            social_btc.append(social.subscriberCount)       
        else:
            social_btc.append(last_btc)   
        socialscrypto = Social.objects.filter(date=social.date).filter(name='CryptoCurrency')
        if socialscrypto:
            for socialcrypto in socialscrypto:
                if socialcrypto.subscriberCount > last_crypto:
                    social_crypto.append(socialcrypto.subscriberCount)
                    last_crypto = socialcrypto.subscriberCount
                else:
                    social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)
        socialsxmr = Social.objects.filter(date=social.date).filter(name='Monero')
        if socialsxmr:
            for socialxmr in socialsxmr:
                if socialxmr.subscriberCount > last_xmr:
                    social_xmr.append(socialxmr.subscriberCount)
                    last_xmr = socialxmr.subscriberCount
                else:
                    social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'monerojnet/social.html', context)

def social2(request):
    dates = []
    social_btc = []
    last_btc = 0
    N = 1

    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        coins = Coin.objects.filter(date=social.date).filter(name='btc')
        if coins:
            for coin in coins:
                if social.subscriberCount > 0 and coin.priceusd > 0 and coin.supply > 0:
                    last_btc = ((coin.priceusd*coin.supply)**N)/social.subscriberCount
                    social_btc.append(last_btc)       
                    dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
    dates2 = []
    social_xmr = []
    last_xmr = 0
    N = 1

    socials = Social.objects.order_by('date').filter(name='Monero')
    for social in socials:
        coins = Coin.objects.filter(date=social.date).filter(name='xmr')
        if coins:
            for coin in coins:
                if social.subscriberCount > 0 and coin.priceusd > 0 and coin.supply > 0:
                    last_xmr = ((coin.priceusd*coin.supply)**N)/social.subscriberCount
                    social_xmr.append(last_xmr)       
                    dates2.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
    
    last_xmr = '$' + locale.format('%.0f', last_xmr, grouping=True)
    last_btc = '$' + locale.format('%.0f', last_btc, grouping=True)
       
    context = {'dates': dates, 'dates2': dates2, 'social_btc': social_btc, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'last_btc': last_btc}
    return render(request, 'monerojnet/social2.html', context)

def social3(request):
    dates = []
    social_xmr = []
    last_xmr = 0.001
    social_crypto = []
    last_crypto = 0.001

    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
        socialsxmr = Social.objects.filter(date=social.date).filter(name='Monero')
        if socialsxmr:
            for socialxmr in socialsxmr:
                if socialxmr.subscriberCount > 0.001 and social.subscriberCount > 0.001:
                    if socialxmr.subscriberCount/social.subscriberCount > 0.001:
                        last_xmr = 100*(socialxmr.subscriberCount/social.subscriberCount)
                        social_xmr.append(last_xmr)
                    else:
                        social_xmr.append(last_xmr)
                else:
                    social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)
        
        socialscrypto = Social.objects.filter(date=social.date).filter(name='CryptoCurrency')
        if socialscrypto:
            for socialcrypto in socialscrypto:
                if socialcrypto.subscriberCount > 0.001 and social.subscriberCount > 0.001:
                    if socialcrypto.subscriberCount/social.subscriberCount > 0.001:
                        last_crypto = 100*(socialcrypto.subscriberCount/social.subscriberCount)
                        social_crypto.append(last_crypto)
                    else:
                        social_crypto.append(last_crypto)
                else:
                    social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale.format('%.1f', last_xmr, grouping=True)+ '%'
    last_crypto = locale.format('%.1f', last_crypto, grouping=True)+ '%'

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'last_xmr': last_xmr, 'last_crypto': last_crypto}
    return render(request, 'monerojnet/social3.html', context)

def social4(request):
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
        if social.subscriberCount > last_btc:
            last_btc = social.subscriberCount
            social_btc.append(social.subscriberCount)       
        else:
            social_btc.append(last_btc)   
        socialscrypto = Social.objects.filter(date=social.date).filter(name='CryptoCurrency')
        if socialscrypto:
            for socialcrypto in socialscrypto:
                if socialcrypto.subscriberCount > last_crypto:
                    social_crypto.append(socialcrypto.subscriberCount)
                    last_crypto = socialcrypto.subscriberCount
                else:
                    social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)
        socialsxmr = Social.objects.filter(date=social.date).filter(name='Monero')
        if socialsxmr:
            for socialxmr in socialsxmr:
                if socialxmr.subscriberCount > last_xmr:
                    social_xmr.append(socialxmr.subscriberCount)
                    last_xmr = socialxmr.subscriberCount
                else:
                    social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

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
            last_btc = (social_btc[i] - social_btc[i-N])
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
            last_crypto = (social_crypto[i] - social_crypto[i-N])
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
            last_xmr = (social_xmr[i] - social_xmr[i-N])
            if last_xmr < 0:
                last_xmr = ''
            newcomers_xmr.append(last_xmr)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'speed_xmr': speed_xmr, 'speed_crypto': speed_crypto, 'speed_btc': speed_btc, 'newcomers_xmr': newcomers_xmr, 'newcomers_btc': newcomers_btc, 'newcomers_crypto': newcomers_crypto, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'monerojnet/social4.html', context)

def social5(request):
    symbol = 'xmr'
    transactions = []
    pricexmr = []
    dates = []
    now_transactions = 0
    dates = []
    social_xmr = []
    last_xmr = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    if coins:
        for coin in coins:
            dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
            socials = Social.objects.filter(date=coin.date).filter(name='Monero')
            if socials:
                for social in socials:
                    if social.subscriberCount > last_xmr:
                        last_xmr = social.subscriberCount
                        social_xmr.append(social.subscriberCount)       
                    else:
                        social_xmr.append(last_xmr)   
            else:
                social_xmr.append(last_xmr)
            if coin.transactions > 200:
                transactions.append(coin.transactions)
                now_transactions = coin.transactions       
            else:
                transactions.append('')
            if coin.priceusd > 0.001:
                pricexmr.append(coin.priceusd)
            else:
                pricexmr.append('')
    else:
        pricexmr.append('')
        transactions.append('')
    
    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    now_transactions = locale.format('%.0f', now_transactions, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'now_transactions': now_transactions, 'transactions': transactions, 'pricexmr': pricexmr}
    return render(request, 'monerojnet/social5.html', context)

def social6(request):
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
        if social.commentsPerHour*24 < last_btc/4:
            social_btc.append(last_btc)
        else:
            social_btc.append(social.commentsPerHour*24)
            last_btc = social.commentsPerHour*24
        socialscrypto = Social.objects.filter(date=social.date).filter(name='CryptoCurrency')
        if socialscrypto:
            for socialcrypto in socialscrypto:
                if socialcrypto.commentsPerHour*24 < last_crypto/4:
                    social_crypto.append(last_crypto)
                else:
                    social_crypto.append(socialcrypto.commentsPerHour*24)
                    last_crypto = socialcrypto.commentsPerHour*24
        else:
            social_crypto.append(last_crypto)
        socialsxmr = Social.objects.filter(date=social.date).filter(name='Monero')
        if socialsxmr:
            for socialxmr in socialsxmr:
                if socialxmr.commentsPerHour*24 < last_xmr/4:
                    social_xmr.append(last_xmr)
                else:
                    social_xmr.append(socialxmr.commentsPerHour*24)
                    last_xmr = socialxmr.commentsPerHour*24

        else:
            social_xmr.append(last_xmr)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'monerojnet/social6.html', context)

def social7(request):
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0
    socials = Social.objects.order_by('date').filter(name='Bitcoin')
    for social in socials:
        dates.append(datetime.datetime.strftime(social.date, '%Y-%m-%d'))
        social_btc.append(social.postsPerHour*24)
        last_btc = social.postsPerHour*24
        socialscrypto = Social.objects.filter(date=social.date).filter(name='CryptoCurrency')
        if socialscrypto:
            for socialcrypto in socialscrypto:
                social_crypto.append(socialcrypto.postsPerHour*24)
                last_crypto = socialcrypto.postsPerHour*24
        else:
            social_crypto.append(last_crypto)
        socialsxmr = Social.objects.filter(date=social.date).filter(name='Monero')
        if socialsxmr:
            for socialxmr in socialsxmr:
                social_xmr.append(socialxmr.postsPerHour*24)
                last_xmr = socialxmr.postsPerHour*24

        else:
            social_xmr.append(last_xmr)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)

    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'monerojnet/social7.html', context)

def pricelog(request):
    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    dates = []
    color = []
    values = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        count += 1

    count = 0
    for count in range(650):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(  10**12)
        supply += int(720*reward)

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'monerojnet/pricelog.html', context)

def movingaverage(request):
    symbol = 'xmr'
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    dates = []
    color = []
    values = []
    average1 = []
    average2 = []
    total = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.priceusd < 0.2:
            coin.priceusd = 0.2
        total += coin.priceusd
        values.append(coin.priceusd)
        if count < 1460:
            aux = total/(730 + count/2)
            if aux < 0.2:
                aux = 0.2
            average1.append(aux)
            average2.append(aux*5)
            if coin.priceusd > 5*aux:
                new_color = 1
            if coin.priceusd < aux:
                new_color = 0
            else:
                new_color = coin.priceusd/(5*aux)
            color.append(new_color)
        else:
            color.append(new_color)
        
        count += 1
    
    n = 1460
    median = pd.Series(values).rolling(window=n).mean().iloc[n-1:].values

    #for count in range(1460):
    #    average1.append('')
    #    average2.append('')
    for item in median:
        average1.append(item)
        average2.append(item*5)

    context = {'values': values, 'dates': dates, 'color': color, 'average1': average1, 'average2': average2}
    return render(request, 'monerojnet/movingaverage.html', context)

def powerlaw(request):
    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    dates = []
    counter = []
    years = []
    line3 = []
    line2 = []
    line1 = []
    a3 = 0.00000000000000000009
    a2 = 0.0000000000000000000000008
    a1 = 0.00000000000000000000000002
    b3 = ((math.log(477,10)-math.log(5.01,10))/(math.log(2511,10)-math.log(1231,10)))
    b2 = ((math.log(95,10)-math.log(0.23,10))/(math.log(3297,10)-math.log(1468,10)))
    b1 = ((math.log(84,10)-math.log(0.39,10))/(math.log(3507,10)-math.log(1755,10)))
    color = []
    values = []

    yearnumber = 2014
    days = 1200
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if coin.priceusd < 0.01:
            continue
        days += 1
        price3 = a3*(days**b3)
        price2 = a2*(days**b2)
        price1 = a1*(days**b1)
        line3.append(price3)
        line2.append(price2)
        line1.append(price1)
        counter.append(days)
        if coin.date.year > yearnumber:
            yearnumber += 1
            years.append(yearnumber)
            dates.append(days)
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        count += 1

    for count in range(1, 3650):
        date_now = date.today() + timedelta(count)   
        values.append('')     
        days += 1
        price3 = a3*(days**b3)
        price2 = a2*(days**b2)
        price1 = a1*(days**b1)
        line3.append(price3)
        line2.append(price2)
        line1.append(price1)
        counter.append(days)
        if date_now.year > yearnumber:
            yearnumber += 1
            years.append(yearnumber)
            dates.append(days)   

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 
    'now_sf': now_sf, 'color': color, 'years': years, 'counter': counter, 'line1': line1, 'line2': line2, 'line3': line3}
    return render(request, 'monerojnet/powerlaw.html', context)

def pricelin(request):
    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    dates = []
    color = []
    values = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        count += 1

    count = 0
    for count in range(650):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(  10**12)
        supply += int(720*reward)
        stock = (100/(100*reward*720*365/supply))**1.65         

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'monerojnet/pricelin.html', context)

def pricesats(request):
    symbol = 'xmr'
    projection = []
    color = []
    values = []
    dates = []
    now_price = 0
    maximum = 0
    bottom = 1
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.pricebtc > 0.001:
            values.append(coin.pricebtc)
        else:
            values.append('')
        date_aux1 = datetime.datetime.strptime('2021-03-15', '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux2 < date_aux1:
            lastprice = coin.pricebtc
            projection.append('')
        else:
            day = date_aux2 - timedelta(1700)
            coin_aux1 = Coin.objects.filter(name=symbol).get(date=day)
            day = date_aux2 - timedelta(1701)
            coin_aux2 = Coin.objects.filter(name=symbol).get(date=day)
            if coin_aux1 and coin_aux2:
                lastprice += (coin_aux1.pricebtc/coin_aux2.pricebtc-1)*lastprice*0.75
                projection.append(lastprice)
            else:
                projection.append('')
        if coin.pricebtc > 0:
            now_price = coin.pricebtc
        if now_price > maximum:
            maximum = now_price
        if now_price > 0:
            if now_price < bottom:
                bottom = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        count += 1

    count = 0
    for count in range(300):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
        day = date_now - timedelta(1900)
        coin_aux1 = Coin.objects.filter(name=symbol).get(date=day)
        day = date_now - timedelta(1901)
        coin_aux2 = Coin.objects.filter(name=symbol).get(date=day)
        if coin_aux1 and coin_aux2:
            lastprice += (coin_aux1.pricebtc/coin_aux2.pricebtc-1)*lastprice*0.75
            projection.append(lastprice)
        else:
            projection.append('')
    
    now_price = locale.format('%.4f', now_price, grouping=True) + ' BTC'
    maximum = locale.format('%.4f', maximum, grouping=True) + ' BTC'
    bottom = locale.format('%.4f', bottom, grouping=True) + ' BTC'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'projection': projection, 'bottom': bottom}
    return render(request, 'monerojnet/pricesats.html', context)

def fractal(request):
    symbol = 'xmr'
    dates1 = []
    dates2 = []
    cycle1 = []
    cycle2 = []
    now_multiple = 0
    maximum = 0

    count1 = 1
    count2 = 1
    date1_aux = datetime.datetime(2017, 12, 29) 
    date2_aux = datetime.datetime(2014, 6, 21)
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        date3_aux = datetime.datetime.combine(coin.date, datetime.time(0, 0))
        if date3_aux < date1_aux and date3_aux > date2_aux:
            start_inflation = coin.inflation
            cycle1.append(coin.priceusd/5)
            dates1.append(count1/12.7)
            if (coin.priceusd/5) > maximum:
                maximum = coin.priceusd/5
            count1 += 1
        elif date3_aux > date1_aux:
            cycle2.append(coin.priceusd/477.12)
            dates2.append(count2/20.7) #24
            now_multiple = coin.priceusd/477.12
            count2 += 0.86

    now_multiple = locale.format('%.2f', now_multiple, grouping=True) + 'x'
    maximum = locale.format('%.2f', maximum, grouping=True) + 'x'

    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'monerojnet/fractal.html', context)

def inflationfractal(request):
    symbol = 'xmr'
    dates1 = []
    dates2 = []
    cycle1 = []
    cycle2 = []
    now_multiple = 0
    maximum = 0

    current_inflation = 0
    start_inflation = 0
    count1 = 1
    count2 = 1
    date1_aux = datetime.datetime(2017, 12, 29) 
    date2_aux = datetime.datetime(2014, 6, 21)
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        date3_aux = datetime.datetime.combine(coin.date, datetime.time(0, 0))
        if date3_aux < date1_aux and date3_aux > date2_aux:
            start_inflation = coin.inflation
            current_inflation = start_inflation
            cycle1.append(coin.priceusd/5)
            dates1.append(count1/12.7)
            if (coin.priceusd/5) > maximum:
                maximum = coin.priceusd/5
            count1 += 1
        elif date3_aux > date1_aux:
            if (coin.inflation/current_inflation) > 1.15 or (coin.inflation/current_inflation) < 0.85:
                coin.inflation = current_inflation
            else:
                current_inflation = coin.inflation
            delta = math.sqrt(coin.inflation/start_inflation)
            cycle2.append(delta*coin.priceusd/477.12)
            dates2.append(count2/20.55) #24
            now_multiple = delta*coin.priceusd/477.12
            count2 += 0.86

    now_multiple = locale.format('%.2f', now_multiple, grouping=True) + 'x'
    maximum = locale.format('%.2f', maximum, grouping=True) + 'x'

    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'monerojnet/inflationfractal.html', context)

def golden(request):
    symbol = 'xmr'
    dates = []
    prices = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        firstdate = coin.date
        break     

    day = firstdate - timedelta(350)
    for i in range(350):
        dates.append(datetime.datetime.strftime(day, '%Y-%m-%d'))
        prices.append(0.2)

    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.priceusd > 0.2:
            prices.append(coin.priceusd)
        else:
            prices.append(0.2)
    
    n = 350
    median = pd.Series(prices).rolling(window=n).mean().iloc[n-1:].values
    m_350 = []
    m_350_0042 = []
    m_350_0060 = []
    m_350_0200 = []
    m_350_0300 = []
    m_350_0500 = []
    m_350_0800 = []
    m_350_1300 = []
    for i in range(350):
        m_350.append('')
        m_350_0042.append('')
        m_350_0060.append('')
        m_350_0200.append('')
        m_350_0300.append('')
        m_350_0500.append('')
        m_350_0800.append('')
        m_350_1300.append('')
    for item in median:
        m_350.append(float(item))
        m_350_0042.append(float(item)*0.42)
        m_350_0060.append(float(item)*0.60)
        m_350_0200.append(float(item)*2.00)
        m_350_0300.append(float(item)*3.00)
        m_350_0500.append(float(item)*5.00)
        m_350_0800.append(float(item)*8.00)
        m_350_1300.append(float(item)*13.00)

    n = 120
    median = pd.Series(prices).rolling(window=n).mean().iloc[n-1:].values
    m_111 = []
    for i in range(120):
        m_111.append('')
    for item in median:
        m_111.append(float(item))

    i = 0
    down = True
    price_cross = []
    for price in prices:
        if m_111[i] != '' and m_350_0200[i] != '':
            if down == True and m_111[i] > m_350_0200[i]:
                down = False
                price_cross.append(price)
            elif price > m_350_0500[i]:
                price_cross.append(price)
            elif down == False and m_111[i] < m_350_0200[i]:
                down = True
            else:
                price_cross.append('')
        else:
            price_cross.append('')
        i += 1

    context = {'dates': dates, 'prices': prices, 'm_350': m_350, 'm_350_0042': m_350_0042, 'm_350_0060': m_350_0060, 'm_350_0200': m_350_0200, 'm_350_0300': m_350_0300, 
    'm_350_0500': m_350_0500, 'm_350_0800': m_350_0800, 'm_350_1300': m_350_1300, 'median': median, 'm_111': m_111, 'price_cross': price_cross}
    return render(request, 'monerojnet/golden.html', context)

def competitors(request):
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count > 30:
                xmr.append(coin_xmr.priceusd/5.01)
                now_xmr = coin_xmr.priceusd/5.01
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.priceusd and count > 130:
            dash.append(coin_dash.priceusd/14.7)
            now_dash = coin_dash.priceusd/14.7
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.priceusd and count > 155:
            grin.append(coin_grin.priceusd/6.37)
            now_grin = coin_grin.priceusd/6.37
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.priceusd and count > 434:
            zcash.append(coin_zcash.priceusd/750)
            now_zcash = coin_zcash.priceusd/750
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale.format('%.2f', now_dash, grouping=True) 
    now_grin = locale.format('%.2f', now_grin, grouping=True)
    now_zcash = locale.format('%.2f', now_zcash, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'monerojnet/competitors.html', context)

def marketcap(request):
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        dates.append(datetime.datetime.strftime(coin_xmr.date, '%Y-%m-%d'))
        if coin_xmr.priceusd:
            xmr.append(coin_xmr.priceusd*coin_xmr.supply)
            now_xmr = coin_xmr.priceusd*coin_xmr.supply
        else:
            xmr.append('')

        try:
            coin_dash = Coin.objects.filter(name='dash').get(date=coin_xmr.date)
            now_dash = coin_dash.priceusd*coin_dash.supply
            if now_dash > 1000000:
                dash.append(now_dash)
            else:
                dash.append('')
        except:
            dash.append('')

        try:
            coin_zcash = Coin.objects.filter(name='zec').get(date=coin_xmr.date)
            now_zcash = coin_zcash.priceusd*coin_zcash.supply
            if now_zcash > 1000000:
                zcash.append(now_zcash)
            else:
                zcash.append('')
        except:
            zcash.append('')

        try:
            coin_grin = Coin.objects.filter(name='grin').get(date=coin_xmr.date)
            now_grin = coin_grin.priceusd*coin_grin.supply
            if now_grin > 1000000:
                grin.append(now_grin)
            else:
                grin.append('')
        except:
            grin.append('')

    now_dash = '$'+locale.format('%.0f', now_dash, grouping=True) 
    now_grin = '$'+locale.format('%.0f', now_grin, grouping=True)
    now_zcash = '$'+locale.format('%.0f', now_zcash, grouping=True)
    now_xmr = '$'+locale.format('%.0f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'monerojnet/marketcap.html', context)

def inflationreturn(request):
    count = 0
    xmr = []
    dash = []
    grin = []
    zcash = []
    btc = []
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0
    now_btc = 0
    inflation_xmr = []
    inflation_dash = []
    inflation_grin = []
    inflation_zcash = []
    inflation_btc = []

    lastxmrA = 0
    lastxmrB = 0

    count = 0
    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 30:
            now_xmr = coin.priceusd/5.01
            #correcao de um erro nos dados
            if 100/coin.inflation > 110 and now_xmr < 10:
                xmr.append(lastxmrA)
                inflation_xmr.append(lastxmrB)
            else:
                xmr.append(now_xmr)
                inflation_xmr.append(100/coin.inflation)
                lastxmrA = now_xmr
                lastxmrB = 100/coin.inflation

    count = 0
    coins = Coin.objects.order_by('date').filter(name='dash')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 130:
            now_dash = coin.priceusd/14.7
            dash.append(now_dash)
            inflation_dash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='grin')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 155:
            now_grin = coin.priceusd/6.37
            grin.append(now_grin)
            inflation_grin.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='zec')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 434:
            now_zcash = coin.priceusd/750
            zcash.append(now_zcash)
            inflation_zcash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='btc')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 325:
            now_btc = coin.priceusd/30
            btc.append(now_btc)
            inflation_btc.append(100/coin.inflation)

    now_dash = locale.format('%.2f', now_dash, grouping=True) 
    now_grin = locale.format('%.2f', now_grin, grouping=True)
    now_zcash = locale.format('%.2f', now_zcash, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    now_btc = locale.format('%.2f', now_btc, grouping=True)

    context = {'inflation_btc': inflation_btc,'inflation_xmr': inflation_xmr, 'inflation_dash': inflation_dash, 'inflation_grin': inflation_grin, 'inflation_zcash': inflation_zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'btc': btc, 'xmr': xmr, 'dash': dash, 'zcash': zcash, 'grin': grin}
    return render(request, 'monerojnet/inflationreturn.html', context)

def bitcoin(request):
    dates = []
    dates3 = []
    dates4 = []
    btc = []
    xmr3 = []
    count1 = 0
    count3 = 0
    now_xmr = 0
    now_btc = 0

    coins_btc = Coin.objects.order_by('date').filter(name='btc')
    for coin_btc in coins_btc:
        if coin_btc.priceusd:
            if count1 > 325: #450
                btc.append(coin_btc.priceusd/30)
                now_btc = coin_btc.priceusd/30
            dates.append(count1)
            count1 += 1 #1.4
        elif count1 <= 325: #450
            continue
        else:
            btc.append('')

    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')

    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count3 > 30:
                xmr3.append(coin_xmr.priceusd/5.01)
            dates4.append(count3)
            count3 += 0.82
        elif count3 <= 30:
            continue
        else:
            xmr3.append('')

    dates2 = []
    xmr2 = []
    btc2 = []

    for coin_btc in coins_btc:
        if coin_btc.priceusd:
            if coin_btc.priceusd/30 > 0.02:
                btc2.append(coin_btc.priceusd/30)
            else:
                btc2.append('')
        else:
            btc2.append('')
        dates2.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.priceusd/5.01 > 0.02:
                    xmr2.append(coin_xmr.priceusd/5.01)
                else:
                    xmr2.append('')
        else:
            xmr2.append('')

    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)

    context = {'btc': btc, 'xmr2': xmr2, 'btc2': btc2, 'xmr3': xmr3, 'dates': dates, 'dates2': dates2, 'dates3': dates3, 'dates4': dates4}
    return render(request, 'monerojnet/bitcoin.html', context)

def translin(request):
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
    return render(request, 'monerojnet/translin.html', context)

def percentage(request):
    symbol = 'xmr'
    transactions = []
    dates = []
    now_transactions = 0
    maximum = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        coins_aux = Coin.objects.order_by('date').filter(name='btc').filter(date=coin.date)
        if coin.transactions < 500:
            coin.transactions = 500
        if coins_aux:
            for coin_aux in coins_aux:
                if coin_aux.supply > 0 and coin_aux.transactions > 0:
                    now_transactions = 100*coin.transactions/coin_aux.transactions
                    if now_transactions > maximum:
                        maximum = now_transactions
                if now_transactions < 0.001:
                    now_transactions = 0.001
        transactions.append(now_transactions)
        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)
    
    now_transactions = locale.format('%.1f', now_transactions, grouping=True) + '%'
    maximum = locale.format('%.1f', maximum, grouping=True) + '%'

    context = {'transactions': transactions, 'dates': dates, 'now_transactions': now_transactions, 'maximum': maximum}
    return render(request, 'monerojnet/percentage.html', context)

def translog(request):
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
    return render(request, 'monerojnet/translog.html', context)

def hashrate(request):
    symbol = 'xmr'
    hashrate = []
    dates = []
    now_hashrate = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)
        if coin.hashrate > 0:
            now_hashrate = coin.hashrate
        hashrate.append(coin.hashrate)
    
    now_hashrate = locale.format('%.0f', now_hashrate, grouping=True)

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate}
    return render(request, 'monerojnet/hashrate.html', context)

def hashprice(request):
    symbol = 'xmr'
    hashrate = []
    dates = []
    buy = []
    sell = []
    now_hashrate = 0
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if count > 50:
            buy.append(0.00000003)
            sell.append(0.00000100)
            coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
            dates.append(coin.date)
            if coin.hashrate > 0 and coin.priceusd > 0:
                now_hashrate = coin.priceusd/coin.hashrate
                hashrate.append(now_hashrate)
            else:
                hashrate.append('')
            new_color = 30*coin.pricebtc/(count*delta + v0)
            color.append(new_color)
        count += 1
    
    now_hashrate = locale.format('%.8f', now_hashrate, grouping=True)

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'buy': buy, 'sell': sell}
    return render(request, 'monerojnet/hashprice.html', context)

def hashvsprice(request):
    symbol = 'xmr'
    hashrate = []
    prices = []
    dates = []
    now_hashrate = 0
    now_priceusd = 0
    now_pricebtc = 0
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        if count > 55:
            coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
            dates.append(coin.date)
            if coin.priceusd > 0:
                now_hashrate = coin.hashrate
                now_priceusd = coin.priceusd
                now_pricebtc = coin.pricebtc
                hashrate.append(now_hashrate)
                prices.append(now_priceusd)
            else:
                hashrate.append('')
                prices.append('')
            new_color = 30*coin.pricebtc/(count*delta + v0)
            color.append(new_color)
        count += 1
    
    now_hashrate = locale.format('%.0f', now_hashrate, grouping=True)
    now_priceusd = '$' + locale.format('%.2f', now_priceusd, grouping=True)
    now_pricebtc = locale.format('%.5f', now_pricebtc, grouping=True) + ' BTC'

    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'prices': prices, 'now_pricebtc': now_pricebtc, 'now_priceusd': now_priceusd}
    return render(request, 'monerojnet/hashvsprice.html', context)

def metcalfesats(request):
    symbol = 'xmr'
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

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        coins_aux = Coin.objects.order_by('date').filter(name='btc').filter(date=coin.date)
        if coin.transactions < 500:
            coin.transactions = 500
        if coins_aux:
            for coin_aux in coins_aux:
                if coin_aux.supply > 0 and coin_aux.transactions > 0:
                    now_metcalfe = coin.transactions*coin.supply/(coin_aux.supply*coin_aux.transactions)
                if now_metcalfe < 0.001:
                    now_metcalfe = 0.001
        metcalfe.append(now_metcalfe)
        if now_metcalfe > maximum:
            maximum = now_metcalfe
        if coin.pricebtc > 0:
            now_price = coin.pricebtc
        prices.append(coin.pricebtc)
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)
        count += 1
    
    now_price = locale.format('%.4f', now_price, grouping=True) + ' BTC'
    now_metcalfe = locale.format('%.4f', now_metcalfe, grouping=True) + ' BTC'
    maximum = locale.format('%.4f', maximum, grouping=True) + ' BTC'

    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'monerojnet/metcalfesats.html', context)

def metcalfeusd(request):
    symbol = 'xmr'
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

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        coins_aux = Coin.objects.order_by('date').filter(name='btc').filter(date=coin.date)
        if coin.transactions < 500:
            coin.transactions = 500
        if coins_aux:
            for coin_aux in coins_aux:
                if coin_aux.supply > 0 and coin_aux.transactions > 0:
                    now_metcalfe = coin_aux.priceusd*coin.transactions*coin.supply/(coin_aux.supply*coin_aux.transactions)
                if now_metcalfe < 0.23:
                    now_metcalfe = 0.23
        metcalfe.append(now_metcalfe)
        if now_metcalfe > maximum:
            maximum = now_metcalfe
        if coin.priceusd > 0:
            now_price = coin.priceusd
        prices.append(now_price)
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)
        count += 1

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_metcalfe = "$"+ locale.format('%.2f', now_metcalfe, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)

    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'monerojnet/metcalfeusd.html', context)

def coins(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    supplyxmr = []
    supplybtc = []
    fsupplyxmr = []
    fsupplybtc = []
    dates = []
    now_xmr = 0
    now_btc = 0
    
    for coin_btc in coins_btc:
        supplybtc.append(int(coin_btc.supply))
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                supplyxmr.append(int(coin_xmr.supply))
                if coin_xmr.supply > now_xmr:
                    now_xmr = int(coin_xmr.supply)
        else:
            supplyxmr.append('')
        if coin_btc.supply > now_btc:
            now_btc = int(coin_btc.supply)
        fsupplyxmr.append('')
        fsupplybtc.append('')

    rewardbtc = 900
    supplybitcoin = coin_btc.supply
    supply = int(coin_xmr.supply)*10**12
    for i in range(365*(2060-2020)):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        fsupplyxmr.append(supply/(10**12))
        date_aux = coin_btc.date + timedelta(i)
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
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)

    context = {'supplyxmr': supplyxmr, 'supplybtc': supplybtc, 'fsupplyxmr': fsupplyxmr, 'fsupplybtc': fsupplybtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/coins.html', context)

def dailyemission(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    emissionbtc = []
    emissionxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    high_btc = 0
    high_xmr = 0
    supplybtc = 0
    supplyxmr = 0
    valuebtc = 0
    valuexmr = 0

    for coin_btc in coins_btc:
        valuebtc = (coin_btc.supply - supplybtc)*coin_btc.priceusd
        if valuebtc < 1000:
            emissionbtc.append('')
        else:
            emissionbtc.append(valuebtc)
        supplybtc = coin_btc.supply
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = (coin_xmr.supply - supplyxmr)*coin_xmr.priceusd
                supplyxmr = coin_xmr.supply
                if valuexmr < 1000:
                    emissionxmr.append('')
                else:
                    emissionxmr.append(valuexmr)
                now_xmr = valuexmr
                if valuexmr > high_xmr:
                    high_xmr = valuexmr
        else:
            emissionxmr.append('')
        now_btc = valuebtc
        if valuebtc > high_btc:
            high_btc = int(valuebtc)

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        emissionxmr.append('')
        emissionbtc.append('')
        
    now_btc = "$" + locale.format('%.0f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.0f', now_xmr, grouping=True)
    high_btc = "$" + locale.format('%.0f', high_btc, grouping=True)
    high_xmr = "$" + locale.format('%.0f', high_xmr, grouping=True)

    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'high_xmr': high_xmr, 'high_btc': high_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/dailyemission.html', context)

def extracoins(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    nsupply = []
    fsupply = []
    dates = []
    now_diff = 0
    
    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        coins_xmr = Coin.objects.order_by('date').filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                nsupply.append(int(- coin_xmr.supply + coin_btc.supply))
                now_diff = int(- coin_xmr.supply + coin_btc.supply)
        else:
            nsupply.append(int(coin_btc.supply))
        fsupply.append('')

    rewardbtc = 900
    supplybitcoin = coin_btc.supply
    supply = int(coin_xmr.supply)*10**12
    for i in range(365*(2060-2020)):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        date_aux = coin_btc.date + timedelta(i)
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
        
    now_diff = locale.format('%.0f', now_diff, grouping=True)

    context = {'nsupply': nsupply, 'fsupply': fsupply, 'dates': dates, 'now_diff': now_diff}
    return render(request, 'monerojnet/extracoins.html', context)

def inflation(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    inflationxmr = []
    inflationbtc = []
    finflationxmr = []
    finflationbtc = []
    dates = []
    now_xmr = 999999
    now_btc = 999999
    
    for coin_btc in coins_btc:
        if float(coin_btc.inflation) > 0.1:
            inflationbtc.append(float(coin_btc.inflation))
            now_btc = float(coin_btc.inflation)
        else:
            inflationbtc.append('')
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        coins_xmr = Coin.objects.order_by('date').filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                inflationxmr.append(float(coin_xmr.inflation))
                now_xmr = float(coin_xmr.inflation)
        else:
            inflationxmr.append('')
        finflationxmr.append('')
        finflationbtc.append('')

    inflationbitcoin = 1.75
    supply = int(coin_xmr.supply)*10**12
    for i in range(2000):
        supply = int(supply)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        finflationxmr.append(100*reward*720*365/supply)
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        finflationbtc.append(inflationbitcoin)
        date_aux2 = datetime.datetime.strftime(date_aux, '%Y-%m-%d')
        if date_aux2 == '2024-04-23':
            inflationbitcoin = 0.65
        inflationxmr.append('')
        inflationbtc.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + '%'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + '%'

    context = {'inflationxmr': inflationxmr, 'inflationbtc': inflationbtc, 'finflationxmr': finflationxmr, 'finflationbtc': finflationbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/inflation.html', context)

def compinflation(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

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
    count = 0
    
    for coin_btc in coins_btc:
        count += 1
        if coin_btc.inflation > 0.1:
            inflationbtc.append(coin_btc.inflation)
        else:
            inflationbtc.append('')
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if count < 1750:
            inflationdash.append('')
            inflationxmr.append('')
        else:
            coins_dash = Coin.objects.filter(name='dash').filter(date=coin_btc.date)
            if coins_dash:
                for coin_dash in coins_dash:
                    if coin_dash.inflation > 0.1:
                        inflationdash.append(coin_dash.inflation)
                    else:
                        inflationdash.append('')
            else:
                inflationdash.append('')
            coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
            if coins_xmr:
                for coin_xmr in coins_xmr:
                    if coin_xmr.inflation > 0.1:
                        inflationxmr.append(coin_xmr.inflation)
                    else:
                        inflationxmr.append('')
            else:
                inflationxmr.append('')

        if count < 2800:
            inflationzcash.append('')
        else:
            coins_zcash = Coin.objects.filter(name='zec').filter(date=coin_btc.date)
            if coins_zcash:
                for coin_zcash in coins_zcash:
                    if coin_zcash.inflation > 0.1:
                        inflationzcash.append(coin_zcash.inflation)
                    else:
                        inflationzcash.append('')
            else:
                inflationzcash.append('')

        if count < 3600:
            inflationgrin.append('')
        else:
            coins_grin = Coin.objects.filter(name='grin').filter(date=coin_btc.date)
            if coins_grin:
                for coin_grin in coins_grin:
                    if coin_grin.inflation > 0.1:
                        inflationgrin.append(coin_grin.inflation)
                    else:
                        inflationgrin.append('')
            else:
                inflationgrin.append('')

    if count > 4300:
        now_grin = coin_grin.inflation
        now_zcash = coin_zcash.inflation
        now_btc = coin_btc.inflation
        now_xmr = coin_xmr.inflation
        now_dash = coin_dash.inflation
        
    now_dash = locale.format('%.2f', now_dash, grouping=True) + '%'
    now_grin = locale.format('%.2f', now_grin, grouping=True) + '%'
    now_zcash = locale.format('%.2f', now_zcash, grouping=True) + '%'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + '%'
    now_btc = locale.format('%.2f', now_btc, grouping=True) + '%'

    context = {'inflationxmr': inflationxmr, 'inflationdash': inflationdash, 'inflationgrin': inflationgrin, 'inflationzcash': inflationzcash, 'inflationbtc': inflationbtc,
    'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/compinflation.html', context)

def sfmodel(request):
    print('social')
    check_new_social('Bitcoin')
    check_new_social('Monero')
    check_new_social('CryptoCurrency')
    print('metrics')
    symbol = 'btc'
    get_latest_metrics(symbol)
    symbol = 'dash'
    get_latest_metrics(symbol)
    symbol = 'grin'
    get_latest_metrics(symbol)
    symbol = 'zec'
    get_latest_metrics(symbol)
    symbol = 'xmr'
    get_latest_metrics(symbol)
    print('done')

    timevar = 1283
    now_price = 0
    now_sf = 0
    now_inflation = 0.001
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    stock = 0.000001
    dates = []
    inflations = []
    circulations = []
    stock_to_flow = []
    projection = []
    color = []
    values = []

    sf_aux = 0
    skipped = 0
    start_inflation = 0
    count2 = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        date_aux1 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux2 < date_aux1:
            lastprice = coin.priceusd
            start_inflation = coin.inflation
            current_inflation = start_inflation
            projection.append('')
            count2 = 0
        else:
            day = date_aux2 - timedelta(timevar)
            coin_aux1 = Coin.objects.filter(name=symbol).get(date=day)
            day = date_aux2 - timedelta(timevar+1)
            coin_aux2 = Coin.objects.filter(name=symbol).get(date=day)
            date_aux3 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
            
            if date_aux3 + timedelta(int(count2*2)) < datetime.datetime.strptime('2021-07-03', '%Y-%m-%d'):
                day = date_aux3 + timedelta(int(count2*2))
                coin_aux3 = Coin.objects.filter(name=symbol).get(date=day)
                if coin_aux3:
                    if (coin_aux3.inflation/current_inflation) > 1.2 or (coin_aux3.inflation/current_inflation) < 0.8:
                        coin_aux3.inflation = current_inflation
                    else:
                        current_inflation = coin_aux3.inflation
                supply2 = supply
            else:
                reward2 = (2**64 -1 - supply2) >> 19
                if reward2 < 0.6*(10**12):
                    reward2 = 0.6*(10**12)
                supply2 += int(720*reward2)
                current_inflation = 100*reward2*720*365/supply2
                
            if coin_aux1 and coin_aux2:
                lastprice += (coin_aux1.priceusd/coin_aux2.priceusd-1)*lastprice
                actualprice = lastprice*(math.sqrt(start_inflation/current_inflation))
                projection.append(actualprice)
                if skipped < 12:
                    projection.append(actualprice)
                else:
                    skipped = 0
            else:
                projection.append('')
            skipped += 1

        if coin.priceusd < 0.01:
            coin.priceusd = 0.01
        if coin.stocktoflow > sf_aux*2+250:
            coin.stocktoflow = sf_aux
        sf_aux = coin.stocktoflow
        if coin.stocktoflow < 0.1:
            coin.stocktoflow = 0.1
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        stock_to_flow.append(coin.stocktoflow)
        count += 1
        count2 += 1

    count = 0
    for count in range(650):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)
        inflation = 100*reward*720*365/supply
        inflations.append(inflation)
        circulations.append(supply)
        stock = (100/(inflation))**1.65
        stock_to_flow.append(stock)            

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'inflations': inflations, 'circulations': circulations, 'stock_to_flow': stock_to_flow, 'projection': projection,
    'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'monerojnet/sfmodel.html', context)

def sfmodellin(request):
    symbol = 'xmr'
    now_price = 0
    now_sf = 0
    now_inflation = 0.001
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    maximum = 0
    supply = 0
    stock = 0.000001
    dates = []
    inflations = []
    circulations = []
    stock_to_flow = []
    color = []
    values = []

    sf_aux = 0 
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        values.append(coin.priceusd)
        now_inflation = coin.inflation
        now_price = coin.priceusd
        now_sf = coin.stocktoflow
        lastprice = coin.priceusd
        if now_price > maximum:
            maximum = now_price
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)
        supply = int(coin.supply)*10**12
        if coin.stocktoflow > sf_aux*2+250:
            coin.stocktoflow = sf_aux
        sf_aux = coin.stocktoflow
        stock_to_flow.append(coin.stocktoflow)
        count += 1

    count = 0
    for count in range(1):
        date_now = date.today() + timedelta(count)
        dates.append(datetime.datetime.strftime(date_now, '%Y-%m-%d'))
        day = date_now - timedelta(1700)
        coin_aux1 = Coin.objects.filter(name=symbol).get(date=day)
        day = date_now - timedelta(1701)
        coin_aux2 = Coin.objects.filter(name=symbol).get(date=day)
        if coin_aux1 and coin_aux2:
            lastprice += (coin_aux1.priceusd/coin_aux2.priceusd-1)*lastprice*0.75
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(  10**12)
        supply += int(720*reward)
        inflations.append(100*reward*720*365/supply)
        circulations.append(supply)
        stock = (100/(100*reward*720*365/supply))**1.65
        stock_to_flow.append(stock)            

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'inflations': inflations, 'circulations': circulations, 'stock_to_flow': stock_to_flow,
    'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'monerojnet/sfmodellin.html', context)

def sfmultiple(request):
    symbol = 'btc'
    get_latest_metrics(symbol)
    symbol = 'dash'
    get_latest_metrics(symbol)
    symbol = 'grin'
    get_latest_metrics(symbol)
    symbol = 'zec'
    get_latest_metrics(symbol)
    symbol = 'xmr'
    get_latest_metrics(symbol)

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
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
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

    now_sf = locale.format('%.2f', now_sf, grouping=True)
    maximum = locale.format('%.2f', maximum, grouping=True)

    context = {'dates': dates, 'maximum': maximum, 'stock_to_flow': stock_to_flow, 'now_sf': now_sf, 'buy': buy, 'sell': sell, 'color': color}
    return render(request, 'monerojnet/sfmultiple.html', context)

def thermocap(request):
    symbol = 'xmr'
    dates = []
    values = []
    thermocap = []
    color = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    sf_aux = 0 
    supply = 0
    calorie = 1
    calories = []
    calories2 = []
    calories3 = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
        if coin.stocktoflow > sf_aux*2+250:
            coin.stocktoflow = sf_aux
        sf_aux = coin.stocktoflow
        values.append(coin.priceusd)
        new_color = 30*coin.pricebtc/(count*delta + v0)
        color.append(new_color)

        calorie += (coin.supply - supply)*coin.priceusd
        if calorie/(4200000*math.sqrt(coin.inflation)) < 0.1:
            calories.append('')
        else:
            calories.append(calorie/(4200000*math.sqrt(coin.inflation)))
        if calorie/(1000000*math.sqrt(coin.inflation)) < 0.1:
            calories2.append('')
        else:
            calories2.append(calorie/(1000000*math.sqrt(coin.inflation)))
        if 28*calorie/(2500000*math.sqrt(coin.inflation)) < 0.1:
            calories3.append('')
        else:
            calories3.append(28*calorie/(2500000*math.sqrt(coin.inflation)))
        temperature = coin.priceusd/calorie
        if temperature > 0.000004:
            temperature = 0.000004
        thermocap.append(temperature)
        supply = coin.supply
        count += 1  

    temperature = locale.format('%.2f', temperature, grouping=True)

    context = {'dates': dates, 'temperature': temperature, 'values': values, 'thermocap': thermocap, 'color': color, 'calories': calories,
    'calories2': calories2, 'calories3': calories3}
    return render(request, 'monerojnet/thermocap.html', context)

def sharpe(request):
    symbol = 'xmr'
    dates = []
    values = []
    color = []
    rocs = []
    sharpe = []
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    price = 0
    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        new_color = 30*coin.pricebtc/(count*delta + v0)
        count += 1  
        if count % 7 == 0:
            if price == 0:
                if coin.priceusd > 0:
                    price = coin.priceusd
                    roc = 0
                else:
                    roc = 0
            else:
                roc = (coin.priceusd - price)/price
                price = coin.priceusd
            rocs.append(roc)
            dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))
            values.append(coin.priceusd)
            color.append(new_color)
    
    n = 52
    median = pd.Series(rocs).rolling(window=n).mean().iloc[n-1:].values
    std = pd.Series(rocs).rolling(window=n).std().iloc[n-1:].values

    aux = list(map(truediv, median, std))
    for count in range(51):
        sharpe.append('')
    for item in aux:
        sharpe.append(item*math.sqrt(52))

    context = {'dates': dates, 'values': values, 'color': color, 'sharpe': sharpe}
    return render(request, 'monerojnet/sharpe.html', context)

def about(request):
    context = {}
    return render(request, 'monerojnet/about.html', context)

def transcost(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    costxmr2 = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if coin_btc.transactions == 0:
            costbtc.append('')
        else:
            valuebtc = coin_btc.fee*coin_btc.priceusd/coin_btc.transactions
            if valuebtc < 0.0001:
                costbtc.append('')
            else:
                costbtc.append(valuebtc)
                now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.transactions == 0:
                    costxmr.append('')
                    costxmr2.append('')
                else:
                    valuexmr = coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions
                    valuexmr2 = coin_xmr.fee*coin_btc.priceusd/coin_xmr.transactions
                    if valuexmr < 0.0001:
                        costxmr.append('')
                        costxmr2.append('')
                    else:
                        costxmr.append(valuexmr)
                        costxmr2.append(valuexmr2)
                        now_xmr = valuexmr
        else:
            costxmr.append('')
            costxmr2.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = "$" + locale.format('%.2f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costxmr2': costxmr2, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/transcost.html', context)

def transcostntv(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if coin_btc.transactions == 0:
            costbtc.append('')
        else:
            valuebtc = coin_btc.fee/coin_btc.transactions
            if valuebtc < 0.000001:
                costbtc.append('')
            else:
                costbtc.append(valuebtc)
                now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.transactions == 0:
                    costxmr.append('')
                else:
                    valuexmr = coin_xmr.fee/coin_xmr.transactions
                    if valuexmr < 0.000001:
                        costxmr.append('')
                    else:
                        costxmr.append(valuexmr)
                        now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.6f', now_btc, grouping=True)
    now_xmr = locale.format('%.6f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/transcostntv.html', context)

def minerrevcap(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = 365*100*coin_btc.revenue/coin_btc.supply
        if valuebtc < 0.0000001:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = 365*100*coin_xmr.revenue/coin_xmr.supply
                if valuexmr < 0.0000001:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + "%"
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + "%"

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/minerrevcap.html', context)

def minerrev(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = coin_btc.revenue*coin_btc.priceusd
        if valuebtc < 0.0001:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = coin_xmr.revenue*coin_xmr.priceusd
                if valuexmr < 0.0001:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = "$" + locale.format('%.2f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/minerrev.html', context)

def minerrevntv(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = coin_btc.revenue
        if valuebtc < 0.000001:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = coin_xmr.revenue
                if valuexmr < 0.000001:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/minerrevntv.html', context)

def minerfeesntv(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    supply_btc = 0
    supply_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = coin_btc.revenue - coin_btc.supply + supply_btc
        supply_btc = coin_btc.supply
        if valuebtc < 0.1:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = coin_xmr.revenue - coin_xmr.supply + supply_xmr
                supply_xmr = coin_xmr.supply
                if valuexmr < 0.1:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/minerfeesntv.html', context)

def minerfees(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    supply_btc = 0
    supply_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = (coin_btc.revenue - coin_btc.supply + supply_btc)*coin_btc.priceusd
        supply_btc = coin_btc.supply
        if valuebtc < 1:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = (coin_xmr.revenue - coin_xmr.supply + supply_xmr)*coin_xmr.priceusd
                supply_xmr = coin_xmr.supply
                if valuexmr < 1:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/minerfees.html', context)

def dailyemissionntv(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    supply_btc = 0
    supply_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = coin_btc.supply -  supply_btc
        if valuebtc < 0.000001:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
            supply_btc = coin_btc.supply
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = coin_xmr.supply - supply_xmr
                if valuexmr < 0.000001:
                    costxmr.append('')
                else:
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
                    supply_xmr = coin_xmr.supply
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/dailyemissionntv.html', context)

def commit(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if coin_btc.revenue*coin_btc.priceusd < 0.01:
            costbtc.append('')
        else:
            valuebtc = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.revenue*coin_xmr.priceusd < 0.01:
                    costxmr.append('')
                else:
                    valuexmr = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)
                    costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + " hashs / dollar"
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + " hashs / dollar"

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/commit.html', context)

def commitntv(request):
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if coin_btc.revenue  < 0.01:
            costbtc.append('')
        else:
            valuebtc = coin_btc.hashrate/coin_btc.revenue
            if valuebtc < 0.001:
                costbtc.append('')
            else:
                costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.revenue < 0.01:
                    costxmr.append('')
                else:
                    valuexmr = coin_xmr.hashrate/coin_xmr.revenue
                    if valuexmr < 0.001:
                        costxmr.append('')
                    else:
                        costxmr.append(valuexmr)
                    now_xmr = valuexmr
        else:
            costxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        costbtc.append('')
        costxmr.append('')
        
    now_btc = locale.format('%.0f', now_btc, grouping=True) + " hashs / btc"
    now_xmr = locale.format('%.0f', now_xmr, grouping=True) + " hashs / xmr"

    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'monerojnet/commitntv.html', context)

def competitorssats(request):
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.pricebtc:
            if count > 32:
                xmr.append(coin_xmr.pricebtc/0.0058)
                now_xmr = coin_xmr.pricebtc/0.0058
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.pricebtc and count > 130:
            dash.append(coin_dash.pricebtc/0.02)
            now_dash = coin_dash.pricebtc/0.02
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.pricebtc and count > 155:
            grin.append(coin_grin.pricebtc/0.000513)
            now_grin = coin_grin.pricebtc/0.000513
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.pricebtc and count > 434:
            zcash.append(coin_zcash.pricebtc/0.05)
            now_zcash = coin_zcash.pricebtc/0.05
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale.format('%.3f', now_dash, grouping=True) 
    now_grin = locale.format('%.3f', now_grin, grouping=True)
    now_zcash = locale.format('%.3f', now_zcash, grouping=True)
    now_xmr = locale.format('%.3f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'monerojnet/competitorssats.html', context)

def competitorssatslin(request):
    dates = []
    xmr = []
    dash = []
    grin = []
    zcash = []
    count = 0
    now_xmr = 0
    now_dash = 0
    now_grin = 0
    now_zcash = 0

    count = 0
    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')
    for coin_xmr in coins_xmr:
        if coin_xmr.pricebtc:
            if count > 32:
                xmr.append(coin_xmr.pricebtc/0.0058)
                now_xmr = coin_xmr.pricebtc/0.0058
            dates.append(count)
            count += 1
        elif count <= 63:
            continue
        else:
            xmr.append('')

    count = 0
    coins_dash = Coin.objects.order_by('date').filter(name='dash')
    for coin_dash in coins_dash:
        count += 1
        if coin_dash.pricebtc and count > 130:
            dash.append(coin_dash.pricebtc/0.02)
            now_dash = coin_dash.pricebtc/0.02
        elif count <= 130:
            continue
        else:
            dash.append('')
        dates.append(count)

    count = 0
    coins_grin = Coin.objects.order_by('date').filter(name='grin')
    for coin_grin in coins_grin:
        count += 1
        if coin_grin.pricebtc and count > 155:
            grin.append(coin_grin.pricebtc/0.000513)
            now_grin = coin_grin.pricebtc/0.000513
        elif count <= 155:
            continue
        else:
            grin.append('')
        dates.append(count)

    count = 0
    coins_zcash = Coin.objects.order_by('date').filter(name='zec')
    for coin_zcash in coins_zcash:
        count += 1
        if coin_zcash.pricebtc and count > 434:
            zcash.append(coin_zcash.pricebtc/0.05)
            now_zcash = coin_zcash.pricebtc/0.05
        elif count <= 434:
            continue
        else:
            zcash.append('')
        dates.append(count)

    now_dash = locale.format('%.3f', now_dash, grouping=True) 
    now_grin = locale.format('%.3f', now_grin, grouping=True)
    now_zcash = locale.format('%.3f', now_zcash, grouping=True)
    now_xmr = locale.format('%.3f', now_xmr, grouping=True)

    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'monerojnet/competitorssatslin.html', context)

def dread_subscribers(request):
    dates = []
    data1 = []
    data2 = []
    now_xmr = 0
    now_btc = 0

    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet6')
    
    values_mat = wks.get_values(start=(3,1), end=(99,3), returnas='matrix')
    print(len(values_mat))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            if not(value1) or not(value2):
                break
            else:
                dates.append(date)
                data1.append(int(value1))
                data2.append(int(value2))
                now_xmr = int(value2)
                now_btc = int(value1)
        else:
            break
        
    dominance = 100*int(value2)/(int(value2)+int(value1))

    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    dominance = locale.format('%.2f', dominance, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr, 'data1': data1, "data2": data2, "dominance": dominance}
    return render(request, 'monerojnet/dread_subscribers.html', context)

def coincards(request):
    dates = []
    data1 = []
    data2 = []
    data3 = []
    data4 = []
    now_xmr = 0
    now_btc = 0

    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet2')
    
    values_mat = wks.get_values(start=(3,1), end=(99,5), returnas='matrix')
    print(len(values_mat))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            value3 = values_mat[k][3]
            value4 = values_mat[k][4]
            if not(value1) or not(value2) or not(value3) or not(value4):
                break
            else:
                dates.append(date)
                data1.append(float(value1.replace(',','.')))
                data2.append(float(value2.replace(',','.')))
                data3.append(float(value3.replace(',','.')))
                data4.append(float(value4.replace(',','.')))
                now_btc = float(value1.replace(',','.'))
                now_xmr = float(value2.replace(',','.'))
                now_eth = float(value3.replace(',','.'))
                now_others = float(value4.replace(',','.'))
        else:
            break

    now_btc = locale.format('%.1f', now_btc, grouping=True)
    now_xmr = locale.format('%.1f', now_xmr, grouping=True)
    now_eth = locale.format('%.1f', now_eth, grouping=True)
    now_others = locale.format('%.1f', now_others, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'now_others': now_others, 'data1': data1, "data2": data2, "data3": data3, "data4": data4}
    return render(request, 'monerojnet/coincards.html', context)

def merchants(request):
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

    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet3')
    
    values_mat = wks.get_values(start=(3,1), end=(99,8), returnas='matrix')
    print(len(values_mat))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            value3 = values_mat[k][3]
            value4 = values_mat[k][4]
            value5 = values_mat[k][5]
            value6 = values_mat[k][6]
            value7 = values_mat[k][7]
            if not(value1) or not(value2) or not(value3) or not(value4) or not(value5) or not(value6) or not(value7):
                break
            else:
                dates.append(date)
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
        else:
            break

    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    now_eth = locale.format('%.0f', now_eth, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'monerojnet/merchants.html', context)

def merchants_increase(request):
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

    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet4')
    
    values_mat = wks.get_values(start=(3,1), end=(99,8), returnas='matrix')
    print(len(values_mat))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            value3 = values_mat[k][3]
            value4 = values_mat[k][4]
            value5 = values_mat[k][5]
            value6 = values_mat[k][6]
            value7 = values_mat[k][7]
            if not(value1) or not(value2) or not(value3) or not(value4) or not(value5) or not(value6) or not(value7):
                break
            else:
                dates.append(date)
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
        else:
            break

    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    now_eth = locale.format('%.0f', now_eth, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'monerojnet/merchants_increase.html', context)

def merchants_percentage(request):
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
    
    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet5')
    
    values_mat = wks.get_values(start=(3,1), end=(99,8), returnas='matrix')
    print(len(values_mat))

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][2]:
            date = values_mat[k][0]
            value1 = values_mat[k][1]
            value2 = values_mat[k][2]
            value3 = values_mat[k][3]
            value4 = values_mat[k][4]
            value5 = values_mat[k][5]
            value6 = values_mat[k][6]
            value7 = values_mat[k][7]
            if not(value1) or not(value2) or not(value3) or not(value4) or not(value5) or not(value6) or not(value7):
                break
            else:
                dates.append(date)
                data1.append(float(value1.replace(',', '.')))
                data2.append(float(value2.replace(',', '.')))
                data3.append(float(value3.replace(',', '.')))
                data4.append(float(value4.replace(',', '.')))
                data5.append(float(value5.replace(',', '.')))
                data6.append(float(value6.replace(',', '.')))
                data7.append(float(value7.replace(',', '.')))
                now_btc = float(value1.replace(',', '.'))
                now_xmr = float(value2.replace(',', '.'))
                now_eth = float(value3.replace(',', '.'))
        else:
            break

    now_btc = locale.format('%.1f', now_btc, grouping=True)
    now_xmr = locale.format('%.1f', now_xmr, grouping=True)
    now_eth = locale.format('%.1f', now_eth, grouping=True)

    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'monerojnet/merchants_percentage.html', context)

def dominance(request):
    symbol = 'xmr'
    values = []
    pricexmr = []
    dates = []
    now_value = 0
    maximum = 0

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:
        try:
            dominance = Dominance.objects.get(date=coin.date)
            if dominance.dominance > 0:
                values.append(dominance.dominance)
                now_value = dominance.dominance
                if now_value > maximum:
                    maximum = now_value            
            else:
                values.append('')
        except:
            values.append('')

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
            dominance = list(Dominance.objects.order_by('-date'))[1]
            if str(dominance.date) == str(today):
                now_value = dominance.dominance 
                dates.append(today)
                values.append(now_value)
                if now_value > maximum:
                    maximum = now_value  
        except:
            pass

    now_value = locale.format('%.2f', now_value, grouping=True)
    maximum = locale.format('%.2f', maximum, grouping=True)

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'monerojnet/dominance.html', context)

def rank(request):
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
            rank = list(Rank.objects.order_by('-date'))[1]
            if str(rank.date) == str(today):
                now_value = rank.rank 
                dates.append(today)
                values.append(now_value)
                if now_value < maximum:
                    maximum = now_value  
        except:
            pass

    if now_value == 1:
        now_value = locale.format('%.0f', now_value, grouping=True) + 'st'
    if now_value == 2:
        now_value = locale.format('%.0f', now_value, grouping=True) + 'nd'
    if now_value == 3:
        now_value = locale.format('%.0f', now_value, grouping=True) + 'rd'
    if now_value > 3:
        now_value = locale.format('%.0f', now_value, grouping=True) + 'th'
    if maximum == 1:
        maximum = locale.format('%.0f', maximum, grouping=True) + 'st'
    if maximum == 2:
        maximum = locale.format('%.0f', maximum, grouping=True) + 'nd'
    if maximum == 3:
        maximum = locale.format('%.0f', maximum, grouping=True) + 'rd'
    if maximum > 3:
        maximum = locale.format('%.0f', maximum, grouping=True) + 'th'

    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'monerojnet/rank.html', context)
