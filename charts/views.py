from ctypes import sizeof
from os import readlink
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
import json
from .models import *
from .forms import *
from users.models import PageViews
from users.views import update_visitors
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
from psaw import PushshiftAPI
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

# Add manually a new entrance for coin
# To be used when there's a problem with the API
@login_required
def add_coin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')

    if request.method != 'POST':
        #create new page with blank form
        form = CoinForm()
    else:
        #process data and submit article
        form = CoinForm(data=request.POST)
        if form.is_valid():
            add_coin = form.save(commit=False)

            try:
                day = datetime.datetime.strftime(add_coin.date, '%Y-%m-%d')
                coin = Coin.objects.filter(name=add_coin.name).get(date=day)
                coin.delete()
                print('coin found and deleted')
            except:
                print('coin not found')
                pass

            add_coin.stocktoflow = (100/add_coin.inflation)**1.65 
            add_coin.save()
            print('coin saved')
            message = 'Coin added to the database!'

            print(str(add_coin.name) + ' ' +str(add_coin.date) + ' ' +str(add_coin.priceusd) + ' ' +str(add_coin.pricebtc) + ' ' +str(add_coin.inflation) + ' ' +str(add_coin.name) + ' ' +str(add_coin.transactions) + ' ' +str(add_coin.hashrate) + ' ' +str(add_coin.stocktoflow) + ' ' +str(add_coin.supply) + ' ' + ' ' +str(add_coin.fee) + ' ' + ' ' +str(add_coin.revenue) )

            print('updating p2pool')
            update_p2pool()

            print('updating database')
            update_database(day, day)
            context = {'form': form, 'message': message}
            return render(request, 'charts/add_coin.html', context)
        else:
            message = 'An error has happened. Try again.'
            context = {'form': form, 'message': message}
            return render(request, 'charts/add_coin.html', context)

    context = {'form': form}
    return render(request, 'charts/add_coin.html', context)

# Get all history for metrics of a certain coin named as 'symbol'
# Only authorized users can download all price data via URL request
@login_required 
def get_history(request, symbol, start_time=None, end_time=None):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
    update = True
    count = 0
    priceusd = 0
    inflation = 0
    pricebtc = 0
    stocktoflow = 0
    supply = 0
    fee = 0
    revenue = 0
    hashrate = 0
    transactions = 0
    blocksize = 0
    difficulty = 0

    with open("settings.json") as file:
        data = json.load(file)
        file.close()

    if not(start_time and end_time):
        start_time = '2000-01-01'
        end_time = '2100-01-01'

    url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time + '/' + end_time 

    while update: 
        response = requests.get(url)
        data_aux = json.loads(response.text)
        data_aux2 = data_aux['data']
        for item in data_aux2:
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
                try:
                    coin.priceusd = float(item['PriceUSD'])
                    priceusd = coin.priceusd
                except:
                    coin.priceusd = priceusd
                try:
                    coin.pricebtc = float(item['PriceBTC'])
                    pricebtc = coin.pricebtc
                except:
                    coin.pricebtc = pricebtc
                try:
                    coin.inflation = float(item['IssContPctAnn'])  
                    coin.stocktoflow = (100/coin.inflation)**1.65 
                    inflation = coin.inflation
                    stocktoflow = coin.stocktoflow
                except:
                    coin.inflation = inflation
                    coin.stocktoflow = stocktoflow
                try:
                    coin.supply = float(item['SplyCur'])
                    supply = coin.supply
                except:
                    coin.supply = supply
                try:
                    coin.fee = float(item['FeeTotNtv'])
                    fee = coin.fee
                except:
                    coin.fee = fee
                try:
                    coin.revenue = float(item['RevNtv'])
                    revenue = coin.revenue
                except:
                    coin.revenue = revenue
                try:
                    coin.hashrate = float(item['HashRate'])
                    hashrate = coin.hashrate
                except:
                    coin.hashrate = hashrate
                try:
                    coin.transactions = float(item['TxCnt'])
                    transactions = coin.transactions
                except:
                    coin.transactions = transactions
                try:
                    coin.blocksize = float(item['BlkSizeMeanByte'])
                    blocksize = coin.blocksize
                except:
                    coin.blocksize = blocksize
                try:
                    coin.difficulty = float(item['DiffLast'])
                    difficulty = coin.difficulty
                except:
                    coin.difficulty = difficulty

                coin.save()
                count += 1
                print(str(symbol) + ' ' + str(coin.date))

            except:
                pass
        try:
            url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time + '/' + end_time + '/' + data_aux['next_page_token']
        except:
            update = False
            break

    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

# Populate database with rank history
# Only authorized users can do this
@login_required 
def load_rank(request, symbol):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
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
    return render(request, 'charts/maintenance.html', context)

# Populate database with p2pool history
# Only authorized users can do this
@login_required 
def load_p2pool(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')

    count = 0
    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('p2pool')
    values_mat = wks.get_values(start=(3,1), end=(9999,6), returnas='matrix')
    P2Pool.objects.all().delete()

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][1]:
            p2pool_stat = P2Pool()
            p2pool_stat.date = values_mat[k][0]
            p2pool_stat.miners = float(values_mat[k][1].replace(',', '.'))
            p2pool_stat.hashrate = float(values_mat[k][2].replace(',', '.'))
            p2pool_stat.percentage = float(values_mat[k][3].replace(',', '.'))
            p2pool_stat.totalhashes = float(values_mat[k][4].replace(',', '.'))
            p2pool_stat.totalblocksfound = float(values_mat[k][5].replace(',', '.'))
            p2pool_stat.mini = False
            p2pool_stat.save()
            count += 1
            #print('p2poolmini data saved - ' + str(p2pool_stat.date) + ' - ' + str(p2pool_stat.percentage) + ' - ' + str(p2pool_stat.miners))
        else:
            break

    wks = sh.worksheet_by_title('p2poolmini')
    values_mat = wks.get_values(start=(3,1), end=(9999,6), returnas='matrix')

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][1]:
            p2pool_stat = P2Pool()
            p2pool_stat.date = values_mat[k][0]
            p2pool_stat.miners = float(values_mat[k][1].replace(',', '.'))
            p2pool_stat.hashrate = float(values_mat[k][2].replace(',', '.'))
            p2pool_stat.percentage = float(values_mat[k][3].replace(',', '.'))
            p2pool_stat.totalhashes = float(values_mat[k][4].replace(',', '.'))
            p2pool_stat.totalblocksfound = float(values_mat[k][5].replace(',', '.'))
            p2pool_stat.mini = True
            p2pool_stat.save()
            count += 1
            #print('p2poolmini data saved - ' + str(p2pool_stat.date) + ' - ' + str(p2pool_stat.percentage) + ' - ' + str(p2pool_stat.miners))
        else:
            break
    
    message = 'Total of ' + str(count) + ' data imported'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

# Populate database with dominance history
# Only authorized users can do this
@login_required 
def load_dominance(request, symbol):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
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
    return render(request, 'charts/maintenance.html', context)

# Import Reddit history from file on static folder
# Only authorized users can do this
@login_required 
def importer(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
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
    return render(request, 'charts/maintenance.html', context)

# Erase all data for a certain coin
# Only authorized users can do this
@login_required 
def reset(request, symbol):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
    coins = Coin.objects.filter(name=symbol).all().delete()
    
    message = 'All data for ' + str(symbol) + ' erased'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

# Populate database with especific chart variables
# Only authorized users can do this
@login_required 
def populate_database(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')
    count = 0

    ###################################################################
    # SF model charts
    ###################################################################
    print('Populating database for sfmodel.html, sfmodelin.html and pricesats.html, wait a moment...')
    Sfmodel.objects.all().delete()
    timevar = 1283
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    previous_supply = 0
    supply = 0
    sf_aux = 0
    count_aux = 0

    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        if coin.priceusd < 0.1:
            coin.priceusd = 0.1
            coin.pricebtc = 0.000001
        if coin.stocktoflow > sf_aux*1.3+100:
            coin.stocktoflow = sf_aux
        
        sf_aux = coin.stocktoflow
        if coin.supply > 0:
            supply = int(coin.supply)*10**12
        else:
            supply = previous_supply
        count += 1
        count_aux += 1

        data = Sfmodel()
        data.date = coin.date
        data.priceusd = coin.priceusd
        data.pricebtc = coin.pricebtc
        data.stocktoflow = coin.stocktoflow
        data.color = 30*coin.pricebtc/(count*delta + v0)
        date_aux1 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux2 < date_aux1:
            lastprice = coin.priceusd
            current_inflation = coin.inflation
            data.greyline = 0
            count_aux = 0
        else:
            day = date_aux2 - timedelta(timevar)
            coin_aux1 = Coin.objects.filter(name='xmr').get(date=day)
            day = date_aux2 - timedelta(timevar+1)
            coin_aux2 = Coin.objects.filter(name='xmr').get(date=day)
            date_aux3 = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
            
            if date_aux3 + timedelta(int(count_aux*2)) < datetime.datetime.strptime('2021-07-03', '%Y-%m-%d'):
                day = date_aux3 + timedelta(int(count_aux*2))
                coin_aux3 = Coin.objects.filter(name='xmr').get(date=day)
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
                actualprice = lastprice*(math.sqrt(coin.inflation/current_inflation))
                data.greyline = actualprice
            else:
                data.greyline = 0
            previous_supply = supply
        data.save()

    count_aux = 0
    for count_aux in range(700):
        date_now = date.today() + timedelta(count_aux)
        reward = (2**64 -1 - supply) >> 19
        if reward < 0.6*(10**12):
            reward = 0.6*(10**12)
        supply += int(720*reward)

        data = Sfmodel()
        data.date = datetime.datetime.strftime(date_now, '%Y-%m-%d')
        data.stocktoflow = (100/(100*reward*720*365/supply))**1.65   
        data.priceusd = 0
        data.pricebtc = 0
        data.greyline = 0    
        data.color = 0
        data.priceusd = 0
        data.greyline = 0
        data.save()
        count += 1

    ###################################################################
    # Daily Emissions, inflation charts and coins against bitcoin
    ###################################################################
    print('Populating database for dailyemission.html and dailyemissionntv.html, wait a moment...')
    DailyData.objects.all().delete()
    supply_btc = 0
    supply_xmr = 0
    count_aux = 0
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    for coin_btc in coins_btc:
        count_aux += 1
        data = DailyData()
        data.date = datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d')
        
        if coin_btc.blocksize > 0:
            data.btc_blocksize = coin_btc.blocksize
            data.btc_transactions = coin_btc.transactions
        else:
            data.btc_blocksize = 0
            data.btc_transactions = 0
        
        if coin_btc.difficulty > 0:
            data.btc_difficulty = coin_btc.difficulty
        else:
            data.btc_difficulty = 0
        
        if coin_btc.transactions == 0:
            data.btc_transcostusd = 0
            data.btc_transcostntv = 0
        else:
            if coin_btc.fee*coin_btc.priceusd/coin_btc.transactions < 0.0001:
                data.btc_transcostusd = 0
                data.btc_transcostntv = 0
            else:
                data.btc_transcostusd = coin_btc.fee*coin_btc.priceusd/coin_btc.transactions
                data.btc_transcostntv = coin_btc.fee/coin_btc.transactions

        if coin_btc.revenue < 0.000001 or coin_btc.priceusd < 0.001:
            data.btc_minerrevntv = 0
            data.btc_minerrevusd = 0
            data.btc_commitntv = 0
            data.btc_commitusd = 0
            data.btc_priceusd = 0
            data.btc_marketcap = 0
        else:
            data.btc_minerrevntv = coin_btc.revenue
            data.btc_minerrevusd = coin_btc.revenue*coin_btc.priceusd
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.btc_priceusd = coin_btc.priceusd
            data.btc_marketcap = coin_btc.priceusd*coin_btc.supply

        if coin_btc.supply == 0:
            data.btc_minerrevcap = 0
        else:
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply

        if coin_btc.priceusd:
            if coin_btc.priceusd/30 > 0.02:
                data.btc_return = coin_btc.priceusd/30
            else:
                data.btc_return = 0
        else:
            data.btc_return = 0

        if coin_btc.inflation > 0:
            data.btc_inflation = coin_btc.inflation
        else:
            data.btc_inflation = 0
        if coin_btc.supply > 0:
            data.btc_supply = coin_btc.supply
        else:
            data.btc_supply = 0

        if coin_btc.supply - supply_btc < 0.000001:
            data.btc_minerfeesntv = 0
            data.btc_minerfeesusd = 0
            data.btc_emissionntv = 0
        else:
            data.btc_minerfeesntv = coin_btc.revenue - coin_btc.supply + supply_btc
            data.btc_minerfeesusd = (coin_btc.revenue - coin_btc.supply + supply_btc)*coin_btc.priceusd
            data.btc_emissionntv = coin_btc.supply -  supply_btc
        
        if (coin_btc.supply - supply_btc)*coin_btc.priceusd < 1000:
            data.btc_emissionusd = 0
        else:
            data.btc_emissionusd = (coin_btc.supply - supply_btc)*coin_btc.priceusd
        supply_btc = coin_btc.supply

        if count_aux > 1750:
            coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
            if coins_xmr:
                for coin_xmr in coins_xmr:
                    if coin_xmr.blocksize > 0:
                        data.xmr_blocksize = coin_xmr.blocksize
                    else:
                        data.xmr_blocksize = 0

                    if coin_xmr.difficulty > 0:
                        data.xmr_difficulty = coin_xmr.difficulty
                    else:
                        data.xmr_difficulty = 0

                    if coin_xmr.priceusd < 0.001:
                        data.xmr_pricebtc = 0
                        data.xmr_priceusd = 0
                        data.xmr_marketcap = 0
                    else:
                        data.xmr_pricebtc = coin_xmr.pricebtc
                        data.xmr_priceusd = coin_xmr.priceusd
                        data.xmr_marketcap = coin_xmr.priceusd*coin_xmr.supply

                    if coin_btc.supply > 0 and coin_btc.transactions > 0:
                        data.xmr_transactions = coin_xmr.transactions
                        data.xmr_metcalfeusd = coin_btc.priceusd*coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                        data.xmr_metcalfebtc = coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
                    else:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0
                        data.xmr_transactions = 0
                    if data.xmr_metcalfeusd < 0.23:
                        data.xmr_metcalfeusd = 0
                        data.xmr_metcalfebtc = 0

                    if coin_xmr.transactions == 0:
                        data.xmr_transacpercentage = 0
                        data.xmr_transcostusd = 0
                        data.xmr_transcostntv = 0
                    else:
                        if coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions < 0.0001:
                            data.xmr_transcostusd = 0
                            data.xmr_transcostntv = 0
                        else:
                            data.xmr_transcostusd = coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions
                            data.xmr_transcostntv = coin_xmr.fee/coin_xmr.transactions
                        if coin_btc.transactions == 0:
                            data.xmr_transacpercentage = 0
                        else:
                            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions

                    if coin_xmr.revenue < 0.000001 or coin_xmr.priceusd < 0.001:
                        data.xmr_minerrevntv = 0
                        data.xmr_minerrevusd = 0
                        data.xmr_commitntv = 0
                        data.xmr_commitusd = 0
                    else:
                        data.xmr_minerrevntv = coin_xmr.revenue
                        data.xmr_minerrevusd = coin_xmr.revenue*coin_xmr.priceusd
                        data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
                        data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)

                    if coin_xmr.supply == 0:
                        data.xmr_minerrevcap = 0
                    else:
                        data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply

                    if coin_xmr.priceusd/5.01 > 0.02:
                        data.xmr_return = coin_xmr.priceusd/5.01
                    else:
                        data.xmr_return = 0

                    if coin_xmr.inflation > 0:
                        data.xmr_inflation = coin_xmr.inflation
                    else:
                        data.xmr_inflation = 0

                    if coin_xmr.supply > 0:
                        data.xmr_supply = coin_xmr.supply
                    else:
                        data.xmr_supply = 0

                    if coin_xmr.supply - supply_xmr < 0.000001:
                        data.xmr_minerfeesntv = 0
                        data.xmr_minerfeesusd = 0
                        data.xmr_emissionntv = 0
                    else:
                        data.xmr_minerfeesntv = coin_xmr.revenue - coin_xmr.supply + supply_xmr
                        data.xmr_minerfeesusd = (coin_xmr.revenue - coin_xmr.supply + supply_xmr)*coin_xmr.priceusd
                        data.xmr_emissionntv = coin_xmr.supply - supply_xmr

                    if (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd < 1000:
                        data.xmr_emissionusd = 0
                    else:
                        data.xmr_emissionusd = (coin_xmr.supply - supply_xmr)*coin_xmr.priceusd
                    supply_xmr = coin_xmr.supply
            else:
                data.xmr_emissionntv = 0
                data.xmr_emissionusd = 0
                data.xmr_inflation = 0
                data.xmr_supply = 0
                data.xmr_return = 0
                data.xmr_minerrevntv = 0
                data.xmr_minerrevusd = 0
                data.xmr_minerfeesntv = 0
                data.xmr_minerfeesusd = 0
                data.xmr_transcostntv = 0
                data.xmr_transcostusd = 0
                data.xmr_commitntv = 0
                data.xmr_commitusd = 0
                data.xmr_metcalfeusd = 0
                data.xmr_metcalfebtc = 0
                data.xmr_pricebtc = 0
                data.xmr_priceusd = 0
                data.xmr_transacpercentage = 0
                data.xmr_marketcap = 0
                data.xmr_minerrevcap = 0
                data.xmr_transactions = 0
                data.xmr_blocksize = 0
                data.xmr_difficulty = 0

            coins_dash = Coin.objects.filter(name='dash').filter(date=coin_btc.date)
            if coins_dash:
                for coin_dash in coins_dash:
                    if coin_dash.transactions > 0:
                        data.dash_transactions = coin_dash.transactions
                    else:
                        data.dash_transactions = 0
                    if coin_dash.inflation > 0:
                        data.dash_inflation = coin_dash.inflation
                    else:
                        data.dash_inflation = 0

                    if coin_dash.priceusd > 0:
                        data.dash_marketcap = coin_dash.priceusd*coin_dash.supply
                    else:
                        data.dash_marketcap = 0
            else:
                data.dash_inflation = 0
                data.dash_marketcap = 0
                data.dash_transactions = 0
        else:
            data.xmr_emissionntv = 0
            data.xmr_emissionusd = 0
            data.xmr_inflation = 0
            data.xmr_supply = 0
            data.xmr_return = 0
            data.dash_inflation = 0
            data.dash_marketcap = 0
            data.dash_transactions = 0
            data.xmr_marketcap = 0
            data.xmr_minerrevntv = 0
            data.xmr_minerrevusd = 0
            data.xmr_minerfeesntv = 0
            data.xmr_minerfeesusd = 0
            data.xmr_transcostntv = 0
            data.xmr_transcostusd = 0
            data.xmr_commitntv = 0
            data.xmr_commitusd = 0
            data.xmr_metcalfeusd = 0
            data.xmr_metcalfebtc = 0
            data.xmr_pricebtc = 0
            data.xmr_priceusd = 0
            data.xmr_transacpercentage = 0
            data.xmr_minerrevcap = 0
            data.xmr_transactions = 0
            data.xmr_blocksize = 0
            data.xmr_difficulty = 0

        if count_aux > 2800:
            coins_zcash = Coin.objects.filter(name='zec').filter(date=coin_btc.date)
            if coins_zcash:
                for coin_zcash in coins_zcash:
                    if coin_zcash.transactions > 0:
                        data.zcash_transactions = coin_zcash.transactions
                    else:
                        data.zcash_transactions = 0
                    if coin_zcash.inflation > 0:
                        data.zcash_inflation = coin_zcash.inflation
                    else:
                        data.zcash_inflation = 0
                
                    if coin_zcash.priceusd > 0:
                        data.zcash_marketcap = coin_zcash.priceusd*coin_zcash.supply
                    else:
                        data.zcash_marketcap = 0
            else:
                data.zcash_inflation = 0
                data.zcash_marketcap = 0
                data.zcash_transactions = 0
        else:
            data.zcash_inflation = 0
            data.zcash_marketcap = 0
            data.zcash_transactions = 0

        if count_aux > 3600:
            coins_grin = Coin.objects.filter(name='grin').filter(date=coin_btc.date)
            if coins_grin:
                for coin_grin in coins_grin:
                    if coin_grin.transactions > 0:
                        data.grin_transactions = coin_grin.transactions
                    else:
                        data.grin_transactions = 0
                    if coin_grin.inflation > 0:
                        data.grin_inflation = coin_grin.inflation
                    else:
                        data.grin_inflation = 0

                    if coin_grin.priceusd > 0:
                        data.grin_marketcap = coin_grin.priceusd*coin_grin.supply
                    else:
                        data.grin_marketcap = 0
            else:
                data.grin_inflation = 0
                data.grin_marketcap = 0
                data.grin_transactions = 0
        else:
            data.grin_inflation = 0
            data.grin_marketcap = 0
            data.grin_transactions = 0
    
        socials = Social.objects.filter(name='Bitcoin').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.btc_subscriberCount = social.subscriberCount
                data.btc_commentsPerHour = social.commentsPerHour
                data.btc_postsPerHour = social.postsPerHour
        else:
            data.btc_subscriberCount = 0
            data.btc_commentsPerHour = 0
            data.btc_postsPerHour = 0
        
        socials = Social.objects.filter(name='Monero').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.xmr_subscriberCount = social.subscriberCount
                data.xmr_commentsPerHour = social.commentsPerHour
                data.xmr_postsPerHour = social.postsPerHour
        else:
            data.xmr_subscriberCount = 0
            data.xmr_commentsPerHour = 0
            data.xmr_postsPerHour = 0

        socials = Social.objects.filter(name='CryptoCurrency').filter(date=coin_btc.date)
        if socials:
            for social in socials:
                data.crypto_subscriberCount = social.subscriberCount
                data.crypto_commentsPerHour = social.commentsPerHour
                data.crypto_postsPerHour = social.postsPerHour
        else:
            data.crypto_subscriberCount = 0
            data.crypto_commentsPerHour = 0
            data.crypto_postsPerHour = 0

        data.save()
        count += 1

    message = 'Total of ' + str(count) + ' data generated'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

# Update database with between certain dates
# Only authorized users can do this
@login_required 
def update_database_admin(request, date_from, date_to):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        return render(request, 'users/error.html')

    update_database(date_from, date_to)

    message = 'Database updated from ' + str(date_from) + ' to ' + str(date_to)
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

###########################################
# Other useful functions                  
###########################################

# Get most recent metrics from a data provider of your choice for 'symbol'
def get_latest_metrics(symbol, url):
    update = True
    count = 0

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
                try:
                    coin.priceusd = float(item['PriceUSD'])
                except:
                    coin.priceusd = 0
                try:
                    coin.pricebtc = float(item['PriceBTC'])
                except:
                    coin.pricebtc = 0
                try:
                    coin.inflation = float(item['IssContPctAnn'])  
                    coin.stocktoflow = (100/coin.inflation)**1.65 
                except:
                    coin.inflation = 0
                    coin.stocktoflow = 0
                try:
                    coin.supply = float(item['SplyCur'])
                except:
                    coin.supply = 0
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
                
                if (symbol == 'xmr' or symbol == 'btc') and (coin.inflation == 0 or coin.supply == 0 or coin.hashrate == 0 or coin.transactions == 0):
                    continue

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

        url = data["metrics_provider"][0]["price_url_old"]
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
            print('getting latest data')
            print(data)
            try:
                if data['data']['XMR']['cmc_rank']:
                    print('new data received')
                    pass
                else:
                    print('problem with the data provider')
                    data = False
            except:
                data = False
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            data = False

        file.close()
    return data

# Get latest dominance value and update
def update_dominance(data):
    if not(data):
        print('error updating dominance')
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
            print('spreadsheet updated')
        else:
            print('spreadsheet already with the latest data')
            return False

    #print('updated')
    return data

# Get latest rank value and update
def update_rank():
    data = get_latest_price()
    if not(data):
        print('error updating rank')
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
            print('spreadsheet updated')
        else:
            print('spreadsheet already with the latest data')
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

        timestamp2 = int(timestamp1 - 43200)
        limit = 1000
        filters = []
        data = data_prep_posts(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.postsPerHour = len(data)/12

        timestamp2 = int(timestamp1 - 3600)
        limit = 1000
        data = data_prep_comments(symbol, timestamp2, timestamp1, filters, limit)
        print(len(data))
        social.commentsPerHour = len(data)/1
        social.save()
    return True

# Update database DailyData with most recent coin data
def update_database(date_from=None, date_to=None):
    date_zero = '2014-05-20'

    if not(date_from) or not(date_to):
        date_to = date.today()
        date_from = date_to - timedelta(5)
        amount = date_from - datetime.datetime.strptime(date_zero, '%Y-%m-%d')
    else:
        print(str(date_from) + ' to ' + str(date_to))
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        amount = date_from - datetime.datetime.strptime(date_zero, '%Y-%m-%d')

    count = 0
    date_aux = date_from
    while date_aux <= date_to:
        date_aux = date_from + timedelta(count)
        date_aux2 = date_aux - timedelta(1)
        try:
            coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)
            coin_xmr2 = Coin.objects.filter(name='xmr').get(date=date_aux2)
            coin_btc = Coin.objects.filter(name='btc').get(date=date_aux)
            coin_btc2 = Coin.objects.filter(name='btc').get(date=date_aux2)

            try:
                coin_dash = Coin.objects.filter(name='dash').get(date=date_aux)
            except:
                coin_dash = Coin()
            try:
                coin_zcash = Coin.objects.filter(name='zec').get(date=date_aux)
            except:
                coin_zcash = Coin()
            try:
                coin_grin = Coin.objects.filter(name='grin').get(date=date_aux)
            except:
                coin_grin = Coin()


            if coin_btc.inflation == 0 or coin_xmr.inflation == 0:
                return count

            count_aux = 0
            found = False
            while count_aux < 100 and not(found):
                try:
                    date_aux2 = date_aux - timedelta(count_aux)
                    social_btc = Social.objects.filter(name='Bitcoin').get(date=date_aux2)
                    social_xmr = Social.objects.filter(name='Monero').get(date=date_aux2)
                    social_crypto = Social.objects.filter(name='CryptoCurrency').get(date=date_aux2)
                    found = True
                except:
                    count_aux += 1
                    found = False
        except:
            return count

        try:
            data = Sfmodel.objects.get(date=coin_xmr.date)
        except:
            data = Sfmodel()
            data.priceusd = 0
            data.pricebtc = 0
            data.stocktoflow = 0
            data.greyline = 0
            data.color = 0
            data.date = coin_xmr.date
        if data.pricebtc == 0:
            data.pricebtc = coin_xmr.pricebtc
        if data.priceusd == 0:
            data.priceusd = coin_xmr.priceusd
        if data.stocktoflow == 0 and coin_xmr.supply > 0:
            supply = int(coin_xmr.supply)*10**12
            reward = (2**64 -1 - supply) >> 19
            if reward < 0.6*(10**12):
                reward = 0.6*(10**12)
            inflation = 100*reward*720*365/supply
            data.stocktoflow = (100/(inflation))**1.65
        v0 = 0.002
        delta = (0.015 - 0.002)/(6*365)
        data.color = 30*coin_xmr.pricebtc/((amount.days)*delta + v0)
        amount += timedelta(1)
        data.save()

        try:
            data = DailyData.objects.get(date=coin_xmr.date)
        except: 
            data = DailyData()
            # Date field
            data.date = coin_xmr.date
            # Basic information
            data.btc_priceusd = 0
            data.xmr_priceusd = 0
            data.xmr_pricebtc = 0
            # Marketcap charts
            data.btc_marketcap = 0
            data.xmr_marketcap = 0
            data.dash_marketcap = 0
            data.grin_marketcap = 0
            data.zcash_marketcap = 0
            # Transactions charts
            data.xmr_transacpercentage = 0
            data.btc_transactions = 0
            data.zcash_transactions = 0
            data.dash_transactions = 0
            data.grin_transactions = 0
            data.xmr_transactions = 0
            data.btc_supply = 0
            data.xmr_supply = 0
            # Issuance charts
            data.btc_inflation = 0
            data.xmr_inflation = 0
            data.dash_inflation = 0
            data.grin_inflation = 0
            data.zcash_inflation = 0
            data.xmr_metcalfebtc = 0
            data.xmr_metcalfeusd = 0
            data.btc_return = 0
            data.xmr_return = 0
            data.btc_emissionusd = 0
            data.btc_emissionntv = 0
            data.xmr_emissionusd = 0
            data.xmr_emissionntv = 0
            # Mining charts
            data.btc_minerrevntv = 0
            data.xmr_minerrevntv = 0
            data.btc_minerrevusd = 0
            data.xmr_minerrevusd = 0
            data.btc_minerfeesntv = 0
            data.xmr_minerfeesntv = 0
            data.btc_minerfeesusd = 0
            data.xmr_minerfeesusd = 0
            data.btc_transcostntv = 0
            data.xmr_transcostntv = 0
            data.btc_transcostusd = 0
            data.xmr_transcostusd = 0
            data.xmr_minerrevcap = 0
            data.btc_minerrevcap = 0
            data.btc_commitntv = 0
            data.xmr_commitntv = 0
            data.btc_commitusd = 0
            data.xmr_commitusd = 0
            data.btc_blocksize = 0
            data.xmr_blocksize = 0
            data.btc_difficulty = 0
            data.xmr_difficulty = 0
            # Reddit charts
            data.btc_subscriberCount = 0
            data.btc_commentsPerHour = 0
            data.btc_postsPerHour = 0
            data.xmr_subscriberCount = 0
            data.xmr_commentsPerHour = 0
            data.xmr_postsPerHour = 0
            data.crypto_subscriberCount = 0
            data.crypto_commentsPerHour = 0
            data.crypto_postsPerHour = 0
            
        # Date field
        data.date = coin_xmr.date
        # Basic information
        data.btc_priceusd = coin_btc.priceusd
        data.xmr_priceusd = coin_xmr.priceusd
        data.xmr_pricebtc = coin_xmr.pricebtc
        # Marketcap charts
        data.btc_marketcap = coin_btc.priceusd*coin_btc.supply
        data.xmr_marketcap = coin_xmr.priceusd*coin_xmr.supply
        data.dash_marketcap = coin_dash.priceusd*coin_dash.supply
        data.grin_marketcap = coin_grin.priceusd*coin_grin.supply
        data.zcash_marketcap = coin_zcash.priceusd*coin_zcash.supply
        # Transactions charts
        try:
            data.xmr_transacpercentage = coin_xmr.transactions/coin_btc.transactions
        except:
            pass
        data.xmr_transactions = coin_xmr.transactions
        data.btc_transactions = coin_btc.transactions
        data.zcash_transactions = coin_zcash.transactions
        data.dash_transactions = coin_dash.transactions
        data.grin_transactions = coin_grin.transactions
        data.btc_supply = coin_btc.supply
        data.xmr_supply = coin_xmr.supply
        # Issuance charts
        data.btc_inflation = coin_btc.inflation
        data.xmr_inflation = coin_xmr.inflation
        data.dash_inflation = coin_dash.inflation
        data.grin_inflation = coin_grin.inflation
        data.zcash_inflation = coin_zcash.inflation
        try:
            data.xmr_metcalfebtc = coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
            data.xmr_metcalfeusd = coin_btc.priceusd*coin_xmr.transactions*coin_xmr.supply/(coin_btc.supply*coin_btc.transactions)
        except:
            pass
        data.btc_return = coin_btc.priceusd/30
        data.xmr_return = coin_xmr.priceusd/5.01
        data.btc_emissionusd = (coin_btc.supply - coin_btc2.supply)*coin_btc.priceusd
        data.btc_emissionntv = coin_btc.supply - coin_btc2.supply
        data.xmr_emissionusd = (coin_xmr.supply - coin_xmr2.supply)*coin_xmr.priceusd
        data.xmr_emissionntv = coin_xmr.supply - coin_xmr2.supply
        # Mining charts
        data.btc_minerrevntv = coin_btc.revenue
        data.xmr_minerrevntv = coin_xmr.revenue
        data.btc_minerrevusd = coin_btc.revenue*coin_btc.priceusd
        data.xmr_minerrevusd = coin_xmr.revenue*coin_xmr.priceusd
        data.btc_minerfeesntv = coin_btc.revenue - coin_btc.supply + coin_btc2.supply
        data.xmr_minerfeesntv = coin_xmr.revenue - coin_xmr.supply + coin_xmr2.supply
        data.btc_minerfeesusd = (coin_btc.revenue - coin_btc.supply + coin_btc2.supply)*coin_btc.priceusd
        data.xmr_minerfeesusd = (coin_xmr.revenue - coin_xmr.supply + coin_xmr2.supply)*coin_xmr.priceusd
        try:
            data.btc_transcostntv = coin_btc.fee/coin_btc.transactions
            data.xmr_transcostntv = coin_xmr.fee/coin_xmr.transactions
            data.btc_transcostusd = coin_btc.priceusd*coin_btc.fee/coin_btc.transactions
            data.xmr_transcostusd = coin_xmr.priceusd*coin_xmr.fee/coin_xmr.transactions
        except:
            pass
        try:
            data.xmr_minerrevcap = 365*100*coin_xmr.revenue/coin_xmr.supply
            data.btc_minerrevcap = 365*100*coin_btc.revenue/coin_btc.supply
        except:
            pass
        try:
            data.btc_commitntv = coin_btc.hashrate/(coin_btc.revenue)
            data.xmr_commitntv = coin_xmr.hashrate/(coin_xmr.revenue)
            data.btc_commitusd = coin_btc.hashrate/(coin_btc.revenue*coin_btc.priceusd)
            data.xmr_commitusd = coin_xmr.hashrate/(coin_xmr.revenue*coin_xmr.priceusd)
        except:
            pass
        try:
            data.btc_blocksize = coin_btc.blocksize
            data.xmr_blocksize = coin_xmr.blocksize
            data.btc_difficulty = coin_btc.difficulty
            data.xmr_difficulty = coin_xmr.difficulty
        except:
            pass
        # Reddit charts
        try:
            data.btc_subscriberCount = social_btc.subscriberCount
            data.btc_commentsPerHour = social_btc.commentsPerHour
            data.btc_postsPerHour = social_btc.postsPerHour
            data.xmr_subscriberCount = social_xmr.subscriberCount
            data.xmr_commentsPerHour = social_xmr.commentsPerHour
            data.xmr_postsPerHour = social_xmr.postsPerHour
            data.crypto_subscriberCount = social_crypto.subscriberCount
            data.crypto_commentsPerHour = social_crypto.commentsPerHour
            data.crypto_postsPerHour = social_crypto.postsPerHour
        except:
            data.btc_subscriberCount = 0
            data.btc_commentsPerHour = 0
            data.btc_postsPerHour = 0
            data.xmr_subscriberCount = 0
            data.xmr_commentsPerHour = 0
            data.xmr_postsPerHour = 0
            data.crypto_subscriberCount = 0
            data.crypto_commentsPerHour = 0
            data.crypto_postsPerHour = 0

        data.save()
        print(str(coin_xmr.date) + ' - ' + str(int(coin_xmr.supply)) + ' xmr @ ' + str(coin_xmr.priceusd) + ' = ' + str(int(data.xmr_marketcap)) + ' => ' + str(coin_xmr.inflation))

        count += 1

    return count

# Get latest P2Pool data
def update_p2pool():
    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=False).get(date=today)
        print('achou p2pool de hoje')
        if p2pool_stat.percentage > 0:

            print('porcentagem > 0')
            update  = False
        else:
            print('porcentagem < 0')
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)

                print('achou coin de ontem')
                if coin.hashrate > 0:
                    update = True
                else:
                    update  = False
            except:
                print('nao achou coin de ontem')
                update  = False
    except:

        print('nao achou p2pool de hoje')
        try:
            coin = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin.hashrate > 0:
                update = True
            else:
                update  = False
        except:
            update  = False

    if update:
        p2pool_stat = P2Pool()
        p2pool_stat.date = today
        response = requests.get('https://p2pool.io/api/pool/stats')
        
        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = False
        p2pool_stat.save()
        print('p2pool saved!')

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('p2pool')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,3), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'F' + str(k + 3)
            wks.update_value(cell, p2pool_stat.totalblocksfound)
            cell = 'E' + str(k + 3)
            wks.update_value(cell, p2pool_stat.totalhashes)
            cell = 'D' + str(k + 3)
            wks.update_value(cell, p2pool_stat.percentage)
            cell = 'C' + str(k + 3)
            wks.update_value(cell, p2pool_stat.hashrate)
            cell = 'B' + str(k + 3)
            wks.update_value(cell, p2pool_stat.miners)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))
            print('spreadsheet updated')
        else:   
            print('spreadsheet already with the latest data')
            return data
        
    today = date.today()
    yesterday = date.today() - timedelta(1)
    try:
        p2pool_stat = P2Pool.objects.filter(mini=True).get(date=today)
        print('achou p2pool_mini de hoje')
        if p2pool_stat.percentage > 0:

            print('porcentagem > 0')
            update  = False
        else:
            print('porcentagem < 0')
            p2pool_stat.delete()
            try:
                coin = Coin.objects.filter(name='xmr').get(date=yesterday)

                print('achou coin de ontem')
                if coin.hashrate > 0:
                    update = True
                else:
                    update  = False
            except:
                print('nao achou coin de ontem')
                update  = False
    except:

        print('nao achou p2pool_mini de hoje')
        try:
            coin = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin.hashrate > 0:
                update = True
            else:
                update  = False
        except:
            update  = False

    if update:
        p2pool_stat = P2Pool()
        p2pool_stat.date = today
        response = requests.get('https://p2pool.io/mini/api/pool/stats')
        
        data = json.loads(response.text)
        p2pool_stat.hashrate = data['pool_statistics']['hashRate']
        p2pool_stat.percentage = 100*data['pool_statistics']['hashRate']/coin.hashrate
        p2pool_stat.miners = data['pool_statistics']['miners']
        p2pool_stat.totalhashes = data['pool_statistics']['totalHashes']
        p2pool_stat.totalblocksfound = data['pool_statistics']['totalBlocksFound']
        p2pool_stat.mini = True
        p2pool_stat.save()
        print('p2pool_mini saved!')

        gc = pygsheets.authorize(service_file='service_account_credentials.json')
        sh = gc.open('zcash_bitcoin')
        wks = sh.worksheet_by_title('p2poolmini')
        
        values_mat = wks.get_values(start=(3,1), end=(9999,3), returnas='matrix')

        k = len(values_mat)
        date_aux = datetime.datetime.strptime(values_mat[k-1][0], '%Y-%m-%d')
        date_aux2 = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
        date_aux2 = datetime.datetime.strptime(date_aux2, '%Y-%m-%d')
        if date_aux < date_aux2:
            cell = 'F' + str(k + 3)
            wks.update_value(cell, p2pool_stat.totalblocksfound)
            cell = 'E' + str(k + 3)
            wks.update_value(cell, p2pool_stat.totalhashes)
            cell = 'D' + str(k + 3)
            wks.update_value(cell, p2pool_stat.percentage)
            cell = 'C' + str(k + 3)
            wks.update_value(cell, p2pool_stat.hashrate)
            cell = 'B' + str(k + 3)
            wks.update_value(cell, p2pool_stat.miners)
            cell = 'A' + str(k + 3)
            wks.update_value(cell, datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))
            print('spreadsheet updated')
        else:   
            print('spreadsheet already with the latest data')
            return data

    return True

###########################################
# Views
###########################################

def index(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(True)

    dt = datetime.datetime.now(timezone.utc).timestamp()
    symbol = 'xmr'

    try:
        rank = list(Rank.objects.order_by('-date'))[0]
    except:
        message = 'Page under maintenance. Check back in a few minutes.'
        context = {'message': message}
        return render(request, 'charts/maintenance.html', context)

    if rank.date < date.today():
        data = update_rank()    
        update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[0]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'charts/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    
    dt = 'index.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'charts/index.html', context)

def pt(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(True)
        
    symbol = 'xmr'

    rank = list(Rank.objects.order_by('-date'))[0]
    if rank.date < date.today():
        data = update_rank()    
        dominance = list(Dominance.objects.order_by('-date'))[0]
        if dominance.date < date.today():
            data = update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[0]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'charts/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'charts/pt.html', context)

def fr(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(True)
        
    symbol = 'xmr'

    rank = list(Rank.objects.order_by('-date'))[0]
    if rank.date < date.today():
        data = update_rank()    
        dominance = list(Dominance.objects.order_by('-date'))[0]
        if dominance.date < date.today():
            data = update_dominance(data)

    coin = list(Coin.objects.filter(name=symbol).order_by('-date'))[0]
    if coin:
        now_inflation = coin.inflation
        supply = int(coin.supply)*10**12
        now_units = supply/(10**12)
    else:
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'charts/maintenance.html', context)

    now_units = locale.format('%.0f', now_units, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    context = {'now_inflation': now_inflation, 'now_units': now_units}
    return render(request, 'charts/fr.html', context)

def social(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        dates2.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriberCount > last_btc:
            social_btc.append(item.btc_subscriberCount)
            last_btc = item.btc_subscriberCount
        else:
            social_btc.append(last_btc)

        if item.xmr_subscriberCount > last_xmr:
            social_xmr.append(item.xmr_subscriberCount)
            last_xmr = item.xmr_subscriberCount
        else:
            social_xmr.append(last_xmr)

        if item.crypto_subscriberCount > last_crypto:
            social_crypto.append(item.crypto_subscriberCount)
            last_crypto = item.crypto_subscriberCount
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)
    
    dt = 'social.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'dates2': dates2, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social.html', context)

def social2(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')
    dates = []
    social_btc = []
    last_btc = 0
    dates2 = []
    social_xmr = []
    last_xmr = 0
    N = 1

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        dates2.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriberCount > 0:
            if item.btc_marketcap > 10000:
                last_btc = ((item.btc_marketcap)**N)/item.btc_subscriberCount
                social_btc.append(last_btc)
            else:
                social_btc.append('')
        else:
            social_btc.append(last_btc)

        if item.xmr_subscriberCount > 0:
            if item.xmr_marketcap > 10000:
                last_xmr = ((item.xmr_marketcap)**N)/item.xmr_subscriberCount
                social_xmr.append(last_xmr)
            else:
                social_xmr.append('')

        else:
            social_xmr.append(last_xmr)

    last_xmr = '$' + locale.format('%.0f', last_xmr, grouping=True)
    last_btc = '$' + locale.format('%.0f', last_btc, grouping=True)
    
    dt = 'social2.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'dates2': dates2, 'social_btc': social_btc, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'last_btc': last_btc}
    return render(request, 'charts/social2.html', context)

def social3(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    dates = []
    social_xmr = []
    social_crypto = []
    last_xmr = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriberCount > 0 and item.xmr_subscriberCount > 0:
            last_xmr = 100*(item.xmr_subscriberCount/item.btc_subscriberCount)
            social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

        if item.btc_subscriberCount > 0 and item.crypto_subscriberCount > 0:
            last_crypto = 100*(item.crypto_subscriberCount/item.btc_subscriberCount)
            social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale.format('%.1f', last_xmr, grouping=True)+ '%'
    last_crypto = locale.format('%.1f', last_crypto, grouping=True)+ '%'
    
    dt = 'social3.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'last_xmr': last_xmr, 'last_crypto': last_crypto}
    return render(request, 'charts/social3.html', context)

def social4(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        dates2.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_subscriberCount > last_btc:
            social_btc.append(item.btc_subscriberCount)
            last_btc = item.btc_subscriberCount
        else:
            social_btc.append(last_btc)

        if item.xmr_subscriberCount > last_xmr:
            social_xmr.append(item.xmr_subscriberCount)
            last_xmr = item.xmr_subscriberCount
        else:
            social_xmr.append(last_xmr)

        if item.crypto_subscriberCount > last_crypto:
            social_crypto.append(item.crypto_subscriberCount)
            last_crypto = item.crypto_subscriberCount
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
    
    dt = 'social4.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'speed_xmr': speed_xmr, 'speed_crypto': speed_crypto, 'speed_btc': speed_btc, 'newcomers_xmr': newcomers_xmr, 'newcomers_btc': newcomers_btc, 'newcomers_crypto': newcomers_crypto, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social4.html', context)

def social5(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')
    transactions = []
    dates = []
    social_xmr = []
    now_transactions = 0
    last_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.xmr_subscriberCount > last_xmr:
            social_xmr.append(item.xmr_subscriberCount)
            last_xmr = item.xmr_subscriberCount
        else:
            social_xmr.append(last_xmr)

        if item.xmr_transactions > 300:
            now_transactions = item.xmr_transactions
            transactions.append(now_transactions)
        else:
            transactions.append('')

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    now_transactions = locale.format('%.0f', now_transactions, grouping=True)
    
    dt = 'social5.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'now_transactions': now_transactions, 'transactions': transactions}
    return render(request, 'charts/social5.html', context)

def social6(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_commentsPerHour*24 < last_btc/4:
            social_btc.append(last_btc)
        else:
            last_btc = item.btc_commentsPerHour*24
            social_btc.append(last_btc)

        if item.xmr_commentsPerHour*24 < last_xmr/4:
            social_xmr.append(last_xmr)
        else:
            last_xmr = item.xmr_commentsPerHour*24
            social_xmr.append(last_xmr)

        if item.crypto_commentsPerHour*24 < last_crypto/4:
            social_crypto.append(last_crypto)
        else:
            last_crypto = item.crypto_commentsPerHour*24
            social_crypto.append(last_crypto)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)
    
    dt = 'social6.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social6.html', context)

def social7(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')
    dates = []
    social_xmr = []
    social_crypto = []
    social_btc = []
    last_xmr = 0
    last_btc = 0
    last_crypto = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_postsPerHour > 0:
            last_btc = item.btc_postsPerHour*24
            social_btc.append(last_btc)
        else:
            social_btc.append(last_btc)

        if item.xmr_postsPerHour > 0:
            last_xmr = item.xmr_postsPerHour*24
            social_xmr.append(last_xmr)
        else:
            social_xmr.append(last_xmr)

        if item.crypto_postsPerHour > 0:
            last_crypto = item.crypto_postsPerHour*24
            social_crypto.append(last_crypto)
        else:
            social_crypto.append(last_crypto)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)
    
    dt = 'social7.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social7.html', context)

def pricelog(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'pricelog.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/pricelog.html', context)

def movingaverage(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'movingaverage.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'color': color, 'average1': average1, 'average2': average2}
    return render(request, 'charts/movingaverage.html', context)

def powerlaw(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    b2 = ((math.log(92,10)-math.log(0.23,10))/(math.log(3297,10)-math.log(1468,10)))
    b1 = ((math.log(93,10)-math.log(0.39,10))/(math.log(3570,10)-math.log(1755,10)))
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
    
    dt = 'powerlaw.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 
    'now_sf': now_sf, 'color': color, 'years': years, 'counter': counter, 'line1': line1, 'line2': line2, 'line3': line3}
    return render(request, 'charts/powerlaw.html', context)

def pricelin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'pricelin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/pricelin.html', context)

def pricesats(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    
    dates = []
    color = []
    values = []
    now_price = 0
    maximum = 0
    bottom = 1

    data = Sfmodel.objects.order_by('date')
    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.pricebtc > 0.0001:
            values.append(item.pricebtc)
            now_price = item.pricebtc
            if bottom > item.pricebtc:
                bottom = item.pricebtc
            if maximum < item.pricebtc:
                maximum = item.pricebtc
        else:
            values.append('')

    now_price = locale.format('%.4f', now_price, grouping=True) + ' BTC'
    maximum = locale.format('%.4f', maximum, grouping=True) + ' BTC'
    bottom = locale.format('%.4f', bottom, grouping=True) + ' BTC'
    
    dt = 'pricesats.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'bottom': bottom}
    return render(request, 'charts/pricesats.html', context)

def pricesatslog(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    
    dates = []
    color = []
    values = []
    now_price = 0
    maximum = 0
    bottom = 1

    data = Sfmodel.objects.order_by('date')
    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.pricebtc > 0.0001:
            values.append(item.pricebtc)
            now_price = item.pricebtc
            if bottom > item.pricebtc:
                bottom = item.pricebtc
            if maximum < item.pricebtc:
                maximum = item.pricebtc
        else:
            values.append('')

    now_price = locale.format('%.4f', now_price, grouping=True) + ' BTC'
    maximum = locale.format('%.4f', maximum, grouping=True) + ' BTC'
    bottom = locale.format('%.4f', bottom, grouping=True) + ' BTC'
    
    dt = 'pricesatslog.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'bottom': bottom}
    return render(request, 'charts/pricesatslog.html', context)

def fractal(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'fractal.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'charts/fractal.html', context)

def inflationfractal(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'inflationfractal.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'cycle1': cycle1, 'cycle2': cycle2, 'dates1': dates1, 'dates2': dates2, 'now_multiple': now_multiple, 'maximum': maximum}
    return render(request, 'charts/inflationfractal.html', context)

def golden(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'golden.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'prices': prices, 'm_350': m_350, 'm_350_0042': m_350_0042, 'm_350_0060': m_350_0060, 'm_350_0200': m_350_0200, 'm_350_0300': m_350_0300, 
    'm_350_0500': m_350_0500, 'm_350_0800': m_350_0800, 'm_350_1300': m_350_1300, 'median': median, 'm_111': m_111, 'price_cross': price_cross}
    return render(request, 'charts/golden.html', context)

def competitors(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'competitors.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitors.html', context)

def competitorslin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'competitorslin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorslin.html', context)

def marketcap(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_dash = '$'+locale.format('%.0f', now_dash, grouping=True) 
    now_grin = '$'+locale.format('%.0f', now_grin, grouping=True)
    now_zcash = '$'+locale.format('%.0f', now_zcash, grouping=True)
    now_xmr = '$'+locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'marketcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/marketcap.html', context)

def inflationreturn(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        if coin.priceusd and count > 30 and coin.inflation > 0:
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
        if coin.priceusd and count > 130 and coin.inflation > 0:
            now_dash = coin.priceusd/14.7
            dash.append(now_dash)
            inflation_dash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='grin')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 155 and coin.inflation > 0:
            now_grin = coin.priceusd/6.37
            grin.append(now_grin)
            inflation_grin.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='zec')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 434 and coin.inflation > 0:
            now_zcash = coin.priceusd/750
            zcash.append(now_zcash)
            inflation_zcash.append(100/coin.inflation)

    count = 0
    coins = Coin.objects.order_by('date').filter(name='btc')
    for coin in coins:
        count += 1
        if coin.priceusd and count > 325 and coin.inflation > 0:
            now_btc = coin.priceusd/30
            btc.append(now_btc)
            inflation_btc.append(100/coin.inflation)

    now_dash = locale.format('%.2f', now_dash, grouping=True) 
    now_grin = locale.format('%.2f', now_grin, grouping=True)
    now_zcash = locale.format('%.2f', now_zcash, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    
    dt = 'inflationreturn.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflation_btc': inflation_btc,'inflation_xmr': inflation_xmr, 'inflation_dash': inflation_dash, 'inflation_grin': inflation_grin, 'inflation_zcash': inflation_zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'btc': btc, 'xmr': xmr, 'dash': dash, 'zcash': zcash, 'grin': grin}
    return render(request, 'charts/inflationreturn.html', context)

def bitcoin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
            if count1 > 890: #450
                btc.append(coin_btc.priceusd/30)
                now_btc = coin_btc.priceusd/30
            dates.append(count1)
            count1 += 1 #1.4
        elif count1 <= 890: #450
            continue
        else:
            btc.append('')

    coins_xmr = Coin.objects.order_by('date').filter(name='xmr')

    for coin_xmr in coins_xmr:
        if coin_xmr.priceusd:
            if count3 > 30:
                xmr3.append(coin_xmr.priceusd/5.01)
            dates4.append(count3)
            count3 += 0.92
        elif count3 <= 30:
            continue
        else:
            xmr3.append('')

    data = DailyData.objects.order_by('date')

    dates2 = []
    xmr2 = []
    btc2 = []
    
    for item in data:
        dates2.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_return > 0.0001:
            btc2.append(item.btc_return)
        else:
            btc2.append('')

        if item.xmr_return > 0.0001:
            xmr2.append(item.xmr_return)
        else:
            xmr2.append('')

    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'bitcoin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'btc': btc, 'xmr2': xmr2, 'btc2': btc2, 'xmr3': xmr3, 'dates': dates, 'dates2': dates2, 'dates3': dates3, 'dates4': dates4}
    return render(request, 'charts/bitcoin.html', context)

def translin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'translin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/translin.html', context)

def pageviews(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    pageviews = []
    unique = []
    dates = []

    users = PageViews.objects.order_by('date')
    for user in users:
        pageviews.append(user.total_pageviews)
        unique.append(user.unique_visitors)
        dates.append(datetime.datetime.strftime(user.date, '%Y-%m-%d'))

    print(dates)
    print(unique)
    print(pageviews)

    dt = 'pageviews.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'pageviews': pageviews, 'dates': dates, 'unique': unique}
    return render(request, 'charts/pageviews.html', context)

def transmonth(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_transactions = locale.format('%.0f', now_transactions, grouping=True)
    maximum = locale.format('%.0f', maximum, grouping=True)
    
    dt = 'transmonth.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/transmonth.html', context)

def percentmonth(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        except:
            pass
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

    now_transactions = locale.format('%.1f', total, grouping=True) + ' %'
    maximum = locale.format('%.1f', maximum, grouping=True) + ' %'
    
    dt = 'percentmonth.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/percentmonth.html', context)

def deviation(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    symbol = 'xmr'
    pricexmr = []
    dates = []

    coins = Coin.objects.order_by('date').filter(name=symbol)
    for coin in coins:        
        if coin.priceusd > 0.001:
            pricexmr.append(coin.priceusd)
        else:
            pricexmr.append(0.20)

        coin.date = datetime.datetime.strftime(coin.date, '%Y-%m-%d')
        dates.append(coin.date)

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
    deviation_price = []
    for count in range(0, len(m_short_price)):
        if float(m_long_price[count]) < 0.001:
            deviation_price.append('')
            deviation_percentage.append('')
        else:
            deviation_price.append((float(m_short_price[count])-float(m_long_price[count]))/(1))
            deviation_percentage.append(100*(float(m_short_price[count])-float(m_long_price[count]))/(float(m_long_price[count])))

    dt = 'deviation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'deviation_percentage': deviation_percentage, 'deviation_price': deviation_price, 'dates': dates, 'pricexmr': pricexmr}
    return render(request, 'charts/deviation.html', context)

def deviation_tx(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    dt = 'deviation_tx.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'deviation_percentage': deviation_percentage, 'dates': dates, 'pricexmr': pricexmr}
    return render(request, 'charts/deviation_tx.html', context)

def percentage(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    now_transactions = locale.format('%.1f', now_transactions, grouping=True) + '%'
    maximum = locale.format('%.1f', maximum, grouping=True) + '%'
    
    dt = 'percentage.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'now_transactions': now_transactions, 'maximum': maximum}
    return render(request, 'charts/percentage.html', context)

def translog(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'translog.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'maximum': maximum, 'now_transactions': now_transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/translog.html', context)

def hashrate(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        else:
            hashrate.append('')

    now_hashrate = locale.format('%.0f', now_hashrate, grouping=True)
    
    dt = 'hashrate.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate}
    return render(request, 'charts/hashrate.html', context)

def hashprice(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'hashprice.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'buy': buy, 'sell': sell}
    return render(request, 'charts/hashprice.html', context)

def hashvsprice(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
            if coin.priceusd > 0 and coin.hashrate:
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
    
    dt = 'hashvsprice.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'hashrate': hashrate, 'dates': dates, 'now_hashrate': now_hashrate, 'color': color, 'prices': prices, 'now_pricebtc': now_pricebtc, 'now_priceusd': now_priceusd}
    return render(request, 'charts/hashvsprice.html', context)

def metcalfesats(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    now_price = locale.format('%.4f', now_price, grouping=True) + ' BTC'
    now_metcalfe = locale.format('%.4f', now_metcalfe, grouping=True) + ' BTC'
    maximum = locale.format('%.4f', maximum, grouping=True) + ' BTC'
    
    dt = 'metcalfesats.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfesats.html', context)

def metcalfesats_deviation(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    now_metcalfe = locale.format('%.4f', now_metcalfe, grouping=True) 
    now_metcalfe_percentage = locale.format('%.0f', now_metcalfe_percentage, grouping=True) 
    
    dt = 'metcalfesats_deviation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'now_metcalfe': now_metcalfe, 'now_metcalfe_percentage': now_metcalfe_percentage, 'metcalfe_percentage': metcalfe_percentage}
    return render(request, 'charts/metcalfesats_deviation.html', context)

def metcalfe_deviation(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    now_metcalfe = locale.format('%.0f', now_metcalfe, grouping=True) 
    now_metcalfe_percentage = locale.format('%.0f', now_metcalfe_percentage, grouping=True) 
    
    dt = 'metcalfe_deviation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'now_metcalfe': now_metcalfe, 'now_metcalfe_percentage': now_metcalfe_percentage, 'metcalfe_percentage': metcalfe_percentage}
    return render(request, 'charts/metcalfe_deviation.html', context)

def metcalfeusd(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_metcalfe = "$"+ locale.format('%.2f', now_metcalfe, grouping=True)
    maximum = "$"+ locale.format('%.2f', maximum, grouping=True)
    
    dt = 'metcalfeusd.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfeusd.html', context)

def coins(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'coins.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'supplyxmr': supplyxmr, 'supplybtc': supplybtc, 'fsupplyxmr': fsupplyxmr, 'fsupplybtc': fsupplybtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/coins.html', context)

def dailyemission(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_btc = "$" + locale.format('%.0f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.0f', now_xmr, grouping=True)
    high_btc = "$" + locale.format('%.0f', high_btc, grouping=True)
    high_xmr = "$" + locale.format('%.0f', high_xmr, grouping=True)
    
    dt = 'dailyemission.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'high_xmr': high_xmr, 'high_btc': high_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemission.html', context)

def extracoins(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_diff = locale.format('%.0f', now_diff, grouping=True)
    
    dt = 'extracoins.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'nsupply': nsupply, 'fsupply': fsupply, 'dates': dates, 'now_diff': now_diff}
    return render(request, 'charts/extracoins.html', context)

def inflation(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + '%'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + '%'
    
    dt = 'inflation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflationxmr': inflationxmr, 'inflationbtc': inflationbtc, 'finflationxmr': finflationxmr, 'finflationbtc': finflationbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/inflation.html', context)

def blocksize(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_blocksize = []
    btc_blocksize = []
    dates = []
    now_xmr = 0
    now_btc = 0
    
    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_blocksize > 0.001:
            btc_blocksize.append(item.btc_blocksize/1024)
            now_btc = item.btc_blocksize
        else:
            btc_blocksize.append('')

        if item.xmr_blocksize > 0.001:
            xmr_blocksize.append(item.xmr_blocksize/1024)
            now_xmr = item.xmr_blocksize
        else:
            xmr_blocksize.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + ' bytes'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + ' bytes'
    
    dt = 'blocksize.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_blocksize': xmr_blocksize, 'btc_blocksize': btc_blocksize, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/blocksize.html', context)

def transactionsize(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_blocksize = []
    btc_blocksize = []
    dates = []
    now_xmr = 0
    now_btc = 0
    
    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_blocksize > 0.001 and item.btc_transactions > 0:
            now_btc = 144*item.btc_blocksize/(1024*item.btc_transactions)
            btc_blocksize.append(144*item.btc_blocksize/(1024*item.btc_transactions))
        else:
            btc_blocksize.append('')

        if item.xmr_blocksize > 0.001 and item.xmr_transactions > 0:
            now_xmr = 720*item.xmr_blocksize/(1024*item.xmr_transactions)
            xmr_blocksize.append(720*item.xmr_blocksize/(1024*item.xmr_transactions))
        else:
            xmr_blocksize.append('')
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + ' bytes'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + ' bytes'
    
    dt = 'transactionsize.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_blocksize': xmr_blocksize, 'btc_blocksize': btc_blocksize, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transactionsize.html', context)

def transactiondominance(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_xmr = locale.format('%.1f', now_xmr, grouping=True) + '%'
    maximum = locale.format('%.1f', maximum, grouping=True) + '%'
    
    dt = 'transactiondominance.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_dominance': xmr_dominance, 'now_xmr': now_xmr, 'maximum': maximum, 'dates': dates}
    return render(request, 'charts/transactiondominance.html', context)

def difficulty(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_difficulty = []
    btc_difficulty = []
    dates = []
    now_xmr = 0
    now_btc = 0
    
    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

        if item.btc_difficulty > 0.001:
            now_btc = item.btc_difficulty
            btc_difficulty.append(now_btc)
        else:
            btc_difficulty.append('')

        if item.xmr_difficulty > 0.001:
            now_xmr = item.xmr_difficulty
            xmr_difficulty.append(now_xmr)
        else:
            xmr_difficulty.append('')
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'difficulty.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_difficulty': xmr_difficulty, 'btc_difficulty': btc_difficulty, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/difficulty.html', context)

def blockchainsize(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_blocksize = []
    btc_blocksize = []
    dates = []
    now_xmr = 0
    now_btc = 0
    hardfork = datetime.datetime.strptime('2016-03-23', '%Y-%m-%d') #block time changed here

    for item in data:
        date = datetime.datetime.strftime(item.date, '%Y-%m-%d')
        dates.append(date)
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

        if item.btc_blocksize > 0.001 and item.btc_transactions > 0:
            now_btc += 144*item.btc_blocksize/1024
            if now_btc < 200:
                btc_blocksize.append('')
            else:
                btc_blocksize.append(now_btc)
        else:
            btc_blocksize.append('')

        if item.xmr_blocksize > 0.001 and item.xmr_transactions > 0:            
            if date < hardfork: 
                now_xmr += 1440*item.xmr_blocksize/1024
            else:
                now_xmr += 720*item.xmr_blocksize/1024

            if now_xmr < 200:
                xmr_blocksize.append('')
            else:
                xmr_blocksize.append(now_xmr)
        else:
            xmr_blocksize.append('')
        
    now_btc = locale.format('%.2f', now_btc/(1024*1024), grouping=True) + ' Gb'
    now_xmr = locale.format('%.2f', now_xmr/(1024*1024), grouping=True) + ' Gb'
    
    dt = 'blockchainsize.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_blocksize': xmr_blocksize, 'btc_blocksize': btc_blocksize, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/blockchainsize.html', context)

def securitybudget(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_security = []
    btc_security = []
    dates = []
    now_xmr = 0
    now_btc = 0

    for item in data:
        date = datetime.datetime.strftime(item.date, '%Y-%m-%d')
        dates.append(date)
        if item.btc_minerrevusd > 0.001:
            now_btc = item.btc_minerrevusd/86400
            btc_security.append(now_btc)
        else:
            btc_security.append('')

        if item.xmr_minerrevusd > 0.001:            
            now_xmr = item.xmr_minerrevusd/86400
            xmr_security.append(now_xmr)
        else:
            xmr_security.append('')
        
    now_btc = '$' + locale.format('%.2f', now_btc, grouping=True) 
    now_xmr = '$' + locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'securitybudget.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_security': xmr_security, 'btc_security': btc_security, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/securitybudget.html', context)

def efficiency(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    xmr_efficiency = []
    btc_efficiency = []
    dates = []
    now_xmr = 0
    now_btc = 0

    for item in data:
        date = datetime.datetime.strftime(item.date, '%Y-%m-%d')
        dates.append(date)
        if item.btc_minerrevusd != 0 and item.btc_inflation > 0:        
            if (2**32)*item.btc_difficulty*0.10/(item.btc_minerrevusd*24000) > 10:
                now_btc = (2**32)*item.btc_difficulty*0.10/(item.btc_minerrevusd*24000)
            if now_btc > 0.01:
                btc_efficiency.append(now_btc)
            else:
                btc_efficiency.append('')
        else:
            btc_efficiency.append('')

        if item.xmr_minerrevusd != 0 and item.xmr_inflation > 0:            
            if item.xmr_difficulty*0.10/(item.xmr_minerrevusd*5000) > 0.01:
                now_xmr = item.xmr_difficulty*0.10/(item.xmr_minerrevusd*5000)
            if now_xmr > 0.01:
                xmr_efficiency.append(now_xmr)
            else:
                xmr_efficiency.append('')
        else:
            xmr_efficiency.append('')
        
    now_btc = locale.format('%.0f', now_btc, grouping=True) 
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'efficiency.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr_efficiency': xmr_efficiency, 'btc_efficiency': btc_efficiency, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/efficiency.html', context)


def compinflation(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
            
    now_dash = locale.format('%.2f', now_dash, grouping=True) + '%'
    now_grin = locale.format('%.2f', now_grin, grouping=True) + '%'
    now_zcash = locale.format('%.2f', now_zcash, grouping=True) + '%'
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + '%'
    now_btc = locale.format('%.2f', now_btc, grouping=True) + '%'
    
    dt = 'compinflation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflationxmr': inflationxmr, 'inflationdash': inflationdash, 'inflationgrin': inflationgrin, 'inflationzcash': inflationzcash, 'inflationbtc': inflationbtc,
    'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/compinflation.html', context)


def comptransactions(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
            
    now_dash = locale.format('%.0f', now_dash, grouping=True)
    now_grin = locale.format('%.0f', now_grin, grouping=True)
    now_zcash = locale.format('%.0f', now_zcash, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    now_btc = locale.format('%.0f', now_btc, grouping=True) 
    
    dt = 'comptransactions.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'btc': btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/comptransactions.html', context)

def sfmodel(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    update = False

    today = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
    yesterday = date.today() - timedelta(1)
    start_time = datetime.datetime.strftime(date.today() - timedelta(5), '%Y-%m-%d')
    try:
        coin = Coin.objects.filter(name='btc').get(date=yesterday)
        #coin_aux = Coin.objects.filter(name='btc').get(date=yesterday)
        if coin: #and coin_aux: 
            print('coin found yesterday')
            if coin.inflation > 0 and coin.priceusd > 0 and coin.supply > 0: #and coin_aux.inflation > 0 and coin_aux.priceusd > 0 and coin_aux.supply > 0:
                print('no need to update')
                update = False
            else:
                coin.delete()
                update = True
        else:
            print('no coin found yesterday - 1')
            update = True
    except:
        print('no coin found yesterday - 2')
        update = True

    now = datetime.datetime.now()
    current_time = int(now.strftime("%H"))
        
    if update and (current_time >= 5):
        print('social')
        check_new_social('Bitcoin')
        check_new_social('Monero')
        check_new_social('CryptoCurrency')

        print('metrics')
        with open("settings.json") as file:
            data = json.load(file)
            file.close()
            
        symbol = 'btc'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'dash'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'grin'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'zec'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'xmr'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)

        print('p2pool')
        update_p2pool()

        print('updating database')
        update_database(start_time, today)
        print('done')

    dates = []
    stock_to_flow = []
    projection = []
    color = []
    values = []
    now_price = 0
    now_sf = 0
    now_inflation = 0

    data = Sfmodel.objects.order_by('date')
    count_aux = 0
    for item in data:
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.greyline != 0:
            projection.append(item.greyline)
            if count_aux > 25:
                count_aux = 0
            else:
                projection.append(item.greyline)
        else:
            projection.append('')

        if item.stocktoflow > 0.2:
            stock_to_flow.append(item.stocktoflow)
        else:
            stock_to_flow.append('')

        if item.priceusd > 0.1:
            values.append(item.priceusd)
            now_price = item.priceusd
            now_sf = item.stocktoflow
            if item.date > date.today() - timedelta(4):
                coins = Coin.objects.filter(name='xmr').filter(date=item.date)
                if coins:
                    for coin in coins:
                        now_inflation = coin.inflation
        else:
            values.append('')
        count_aux += 1
    
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'

    dt = 'sfmodel.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow, 'projection': projection, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodel.html', context)

def sfmodellin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    stock_to_flow = []
    projection = []
    color = []
    values = []
    now_price = 0
    now_sf = 0
    now_inflation = 0

    data = Sfmodel.objects.order_by('date')
    count_aux = 0
    for item in data:
        if item.color != 0:
            color.append(item.color)
        else:
            color.append('')

        if item.greyline != 0:
            projection.append(item.greyline)
            if count_aux > 25:
                count_aux = 0
            else:
                projection.append(item.greyline)
        else:
            projection.append('')

        if item.stocktoflow > 0.2:
            stock_to_flow.append(item.stocktoflow)
        else:
            stock_to_flow.append('')

        if item.priceusd > 0.1:
            values.append(item.priceusd)
            now_price = item.priceusd
            now_sf = item.stocktoflow
            if item.date > date.today() - timedelta(4):
                coins = Coin.objects.filter(name='xmr').filter(date=item.date)
                if coins:
                    for coin in coins:
                        now_inflation = coin.inflation
        else:
            values.append('')
        count_aux += 1
    
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'
    
    dt = 'sfmodellin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow,'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodellin.html', context)

def sfmultiple(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    symbol = 'xmr'

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
    
    dt = 'sfmultiple.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'maximum': maximum, 'stock_to_flow': stock_to_flow, 'now_sf': now_sf, 'buy': buy, 'sell': sell, 'color': color}
    return render(request, 'charts/sfmultiple.html', context)

def marketcycle(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    color = []
    sell = []
    buy = []

    data = Sfmodel.objects.order_by('date')
    for item in data:
        if item.color > 0:
            color.append(item.color - 5)
        else:
            color.append('')

        sell.append(100)
        buy.append(0)
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))

    now_cycle = locale.format('%.2f', item.color, grouping=True)
    
    dt = 'marketcycle.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'color': color, 'sell': sell, 'buy': buy, 'now_cycle': now_cycle}
    return render(request, 'charts/marketcycle.html', context)

def shielded(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)

    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    values = []
    values2 = []
    values3 = []
    
    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet1')

    dominance = 0
    monthly = 0 
    
    values_mat = wks.get_values(start=(3,1), end=(999,5), returnas='matrix')

    for k in range(0,len(values_mat)):
        if values_mat[k][0] and values_mat[k][3]:
            date = values_mat[k][0]
            value = values_mat[k][3]
            value3 = values_mat[k][4]
            if not(value) or not(value):
                break
            else:
                dates.append(date)
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
    dominance = locale.format('%.2f', dominance, grouping=True)
    
    dt = 'shielded.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'values': values, 'values2': values2, 'values3': values3, "monthly": monthly, "dominance": dominance}
    return render(request, 'charts/shielded.html', context)

def thermocap(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        if coin.inflation != 0:
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
        else:
            calories.append('')
        temperature = coin.priceusd/calorie
        if temperature > 0.000004:
            temperature = 0.000004
        thermocap.append(temperature)
        supply = coin.supply
        count += 1  

    temperature = locale.format('%.2f', temperature, grouping=True)
    
    dt = 'thermocap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'temperature': temperature, 'values': values, 'thermocap': thermocap, 'color': color, 'calories': calories,
    'calories2': calories2, 'calories3': calories3}
    return render(request, 'charts/thermocap.html', context)

def sharpe(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'sharpe.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'values': values, 'color': color, 'sharpe': sharpe}
    return render(request, 'charts/sharpe.html', context)

def about(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    context = {}
    return render(request, 'charts/about.html', context)

def transcost(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_btc = "$" + locale.format('%.2f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'transcost.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcost.html', context)

def transcostntv(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_btc = locale.format('%.6f', now_btc, grouping=True)
    now_xmr = locale.format('%.6f', now_xmr, grouping=True)
    
    dt = 'transcostntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcostntv.html', context)

def minerrevcap(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.xmr_minerrevcap == 0:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_minerrevcap)
            now_xmr = item.xmr_minerrevcap
        if item.btc_minerrevcap == 0:
            costbtc.append('')
        else:
            costbtc.append(item.btc_minerrevcap)
            now_btc = item.btc_minerrevcap
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + "%"
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + "%"
    
    dt = 'minerrevcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevcap.html', context)

def minerrev(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_minerrevusd < 0.0001:
            costbtc.append('')
        else:
            costbtc.append(item.btc_minerrevusd)
            now_btc = item.btc_minerrevusd
        if item.xmr_minerrevusd < 0.0001:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_minerrevusd)
            now_xmr = item.xmr_minerrevusd

    now_btc = "$" + locale.format('%.2f', now_btc, grouping=True)
    now_xmr = "$" + locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'minerrev.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrev.html', context)

def minerrevntv(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_minerrevntv < 0.0001:
            costbtc.append('')
        else:
            costbtc.append(item.btc_minerrevntv)
            now_btc = item.btc_minerrevntv
        if item.xmr_minerrevntv < 0.0001:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_minerrevntv)
            now_xmr = item.xmr_minerrevntv
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'minerrevntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevntv.html', context)

def minerfeesntv(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_minerfeesntv < 0.1:
            costbtc.append('')
        else:
            costbtc.append(item.btc_minerfeesntv)
            now_btc = item.btc_minerfeesntv
        if item.xmr_minerfeesntv < 0.1:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_minerfeesntv)
            now_xmr = item.xmr_minerfeesntv
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'minerfeesntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfeesntv.html', context)

def minerfees(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_minerfeesusd < 1:
            costbtc.append('')
        else:
            costbtc.append(item.btc_minerfeesusd)
            now_btc = item.btc_minerfeesusd
        if item.xmr_minerfeesusd < 1:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_minerfeesusd)
            now_xmr = item.xmr_minerfeesusd
        
    now_btc = locale.format('%.2f', now_btc, grouping=True)
    now_xmr = locale.format('%.2f', now_xmr, grouping=True)
    
    dt = 'minerfees.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfees.html', context)

def dailyemissionntv(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'dailyemissionntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemissionntv.html', context)

def commit(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_commitusd < 0.000001:
            costbtc.append('')
        else:
            costbtc.append(item.btc_commitusd)
            now_btc = item.btc_commitusd
        if item.xmr_commitusd < 0.000001:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_commitusd)
            now_xmr = item.xmr_commitusd
        
    now_btc = locale.format('%.2f', now_btc, grouping=True) + " hashs / dollar"
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + " hashs / dollar"
    
    dt = 'commit.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commit.html', context)

def commitntv(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for item in data:
        dates.append(datetime.datetime.strftime(item.date, '%Y-%m-%d'))
        if item.btc_commitntv < 0.00001:
            costbtc.append('')
        else:
            costbtc.append(item.btc_commitntv)
            now_btc = item.btc_commitntv
        if item.xmr_commitntv < 0.00001:
            costxmr.append('')
        else:
            costxmr.append(item.xmr_commitntv)
            now_xmr = item.xmr_commitntv
        
    now_btc = locale.format('%.0f', now_btc, grouping=True) + " hashs / btc"
    now_xmr = locale.format('%.0f', now_xmr, grouping=True) + " hashs / xmr"
    
    dt = 'commitntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commitntv.html', context)

def competitorssats(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'competitorssats.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorssats.html', context)

def competitorssatslin(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'competitorssatslin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/competitorssatslin.html', context)

def dread_subscribers(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    data1 = []
    data2 = []
    now_xmr = 0
    now_btc = 0

    gc = pygsheets.authorize(service_file='service_account_credentials.json')
    sh = gc.open('zcash_bitcoin')
    wks = sh.worksheet_by_title('Sheet6')
    
    values_mat = wks.get_values(start=(3,1), end=(99,3), returnas='matrix')

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
    
    dt = 'dread_subscribers.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr, 'data1': data1, "data2": data2, "dominance": dominance}
    return render(request, 'charts/dread_subscribers.html', context)

def coincards(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'coincards.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'now_others': now_others, 'data1': data1, "data2": data2, "data3": data3, "data4": data4}
    return render(request, 'charts/coincards.html', context)

def merchants(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'merchants.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'charts/merchants.html', context)

def merchants_increase(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'merchants_increase.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'charts/merchants_increase.html', context)

def merchants_percentage(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'merchants_percentage.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'now_btc': now_btc, 'now_xmr': now_xmr,  'now_eth': now_eth, 'data1': data1, "data2": data2, "data3": data3, "data4": data4, "data5": data5, "data6": data6, "data7": data7}
    return render(request, 'charts/merchants_percentage.html', context)

def dominance(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
            dominance = list(Dominance.objects.order_by('-date'))[0]
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
    
    dt = 'dominance.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'charts/dominance.html', context)

def rank(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'rank.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_value': now_value, 'pricexmr': pricexmr}
    return render(request, 'charts/rank.html', context)

def p2pool_hashrate(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    hashrate = []
    hashrate_mini = []
    combined = []
    dates = []
    now_hashrate = 0
    now_hashrate_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.hashrate and p2pool_stat.percentage > 0:
            now_hashrate = p2pool_stat.hashrate/1000000    
            now_combined = p2pool_stat.hashrate/1000000
        hashrate.append(now_hashrate)
        
        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.hashrate and p2pool_stat_mini.percentage > 0:
                now_hashrate_mini = p2pool_stat_mini.hashrate/1000000     
                now_combined += p2pool_stat_mini.hashrate/1000000    
        except:
            pass
        hashrate_mini.append(now_hashrate_mini) 
        combined.append(now_combined) 

        dates.append(datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    dt = 'p2pool_hashrate.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'hashrate': hashrate, 'dates': dates, 'hashrate_mini': hashrate_mini, 'combined': combined}
    return render(request, 'charts/p2pool_hashrate.html', context)

def p2pool_dominance(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dominance = []
    dominance_mini = []
    dates = []
    combined = []
    now_dominance = 0
    now_dominance_mini = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.hashrate and p2pool_stat.percentage > 0:
            now_dominance = p2pool_stat.percentage       
            now_combined += p2pool_stat.percentage      
        dominance.append(now_dominance)
        
        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.hashrate and p2pool_stat_mini.percentage > 0: 
                now_dominance_mini = p2pool_stat_mini.percentage    
                now_combined += p2pool_stat_mini.percentage      
        except:
            pass
        dominance_mini.append(now_dominance_mini) 
        combined.append(now_combined) 

        dates.append(datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    dt = 'p2pool_dominance.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dominance': dominance, 'dates': dates, 'dominance_mini': dominance_mini,'combined': combined}
    return render(request, 'charts/p2pool_dominance.html', context)

def p2pool_totalblocks(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    totalblocks = []
    totalblocks_mini = []
    combined = []
    now_totalblocks = 0
    now_totalblocks_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.totalblocksfound > now_totalblocks:
            now_totalblocks = p2pool_stat.totalblocksfound  
            now_combined += p2pool_stat.totalblocksfound          
        totalblocks.append(now_totalblocks)

        p2pool_stats_mini = P2Pool.objects.filter(mini=True).filter(date=p2pool_stat.date)
        for p2pool_stat_mini in p2pool_stats_mini:
            if p2pool_stat_mini.totalblocksfound >= now_totalblocks_mini: 
                now_totalblocks_mini = p2pool_stat_mini.totalblocksfound    
                now_combined += p2pool_stat_mini.totalblocksfound    
                break
                

        totalblocks_mini.append(now_totalblocks_mini) 
        combined.append(now_combined) 

        dates.append(datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    dt = 'p2pool_totalblocks.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'totalblocks': totalblocks, 'totalblocks_mini': totalblocks_mini, 'dates': dates, 'combined': combined}
    return render(request, 'charts/p2pool_totalblocks.html', context)

def p2pool_totalhashes(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    totalblocks = []
    totalblocks_mini = []
    combined = []
    now_totalblocks = 0
    now_totalblocks_mini = 0
    now_combined = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.totalhashes > now_totalblocks:
            now_totalblocks = p2pool_stat.totalhashes/1000000000000
            now_combined += p2pool_stat.totalhashes/1000000000000
        totalblocks.append(now_totalblocks)

        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.totalhashes >= now_totalblocks_mini: 
                now_totalblocks_mini = p2pool_stat_mini.totalhashes/1000000000000
                now_combined += p2pool_stat_mini.totalhashes/1000000000000
        except:
            pass
        totalblocks_mini.append(now_totalblocks_mini) 
        combined.append(now_combined) 

        dates.append(datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    dt = 'p2pool_totalhashes.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'totalblocks': totalblocks, 'totalblocks_mini': totalblocks_mini, 'dates': dates, 'combined': combined}
    return render(request, 'charts/p2pool_totalhashes.html', context)

def p2pool_miners(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    miners = []
    miners_mini = []
    dates = []
    combined = []
    now_miners = 0
    now_miners_mini = 0

    p2pool_stats = P2Pool.objects.order_by('date').filter(mini=False)
    for p2pool_stat in p2pool_stats:
        now_combined = 0
        if p2pool_stat.miners > 0:
            now_miners = p2pool_stat.miners       
            now_combined += p2pool_stat.miners      
        miners.append(now_miners)
        
        try:
            p2pool_stat_mini = P2Pool.objects.filter(mini=True).get(date=p2pool_stat.date)
            if p2pool_stat_mini.miners > 0: 
                now_miners_mini = p2pool_stat_mini.miners    
                now_combined += p2pool_stat_mini.miners    
        except:
            pass
        miners_mini.append(now_miners_mini) 
        combined.append(now_combined) 

        dates.append(datetime.datetime.strftime(p2pool_stat.date, '%Y-%m-%d'))

    dt = 'p2pool_miners.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'miners': miners, 'dates': dates, 'miners_mini': miners_mini, 'combined': combined}
    return render(request, 'charts/p2pool_miners.html', context)

def miningprofitability(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    value = []
    now_value = 0

    coins = Coin.objects.order_by('date').filter(name='xmr')
    for coin in coins:
        if coin.hashrate > 0 and coin.priceusd > 0 and coin.revenue > 0:
            if 1000*coin.priceusd*coin.revenue/coin.hashrate < 5000:
                now_value = 1000*coin.priceusd*coin.revenue/coin.hashrate     
                dates.append(datetime.datetime.strftime(coin.date, '%Y-%m-%d'))     
                value.append(now_value)

    dt = 'miningprofitability.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'value': value, 'dates': dates}
    return render(request, 'charts/miningprofitability.html', context)

def tail_emission(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        
    now_xmr = locale.format('%.2f', now_xmr, grouping=True) + '%'
    
    dt = 'tail_emission.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflationxmr': inflationxmr, 'finflationxmr': finflationxmr, 'now_xmr': now_xmr, 'dates': dates}
    return render(request, 'charts/tail_emission.html', context)

def privacymarketcap(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_marketcap = '$'+locale.format('%.0f', now_marketcap, grouping=True) 
    now_dominance = locale.format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale.format('%.0f', top_marketcap, grouping=True) 
    top_dominance = locale.format('%.2f', top_dominance, grouping=True) + '%'
    
    dt = 'privacymarketcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'marketcaps': marketcaps, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates, 'xmr_marketcaps': xmr_marketcaps}
    return render(request, 'charts/privacymarketcap.html', context)

def privacydominance(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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

    now_marketcap = '$'+locale.format('%.0f', now_marketcap, grouping=True) 
    now_dominance = locale.format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale.format('%.0f', top_marketcap, grouping=True) 
    top_dominance = locale.format('%.2f', top_dominance, grouping=True) + '%'
    
    dt = 'privacymarketcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'marketcaps': marketcaps, 'dominances':dominances, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates}
    return render(request, 'charts/privacydominance.html', context)

def monerodominance(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    data = DailyData.objects.order_by('date')

    dates = []
    marketcaps = []
    xmr_dominance = []
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

    now_marketcap = '$'+locale.format('%.0f', now_marketcap, grouping=True) 
    now_dominance = locale.format('%.2f', now_dominance, grouping=True) + '%'
    top_marketcap = '$'+locale.format('%.0f', top_marketcap, grouping=True) 
    top_dominance = locale.format('%.2f', top_dominance, grouping=True) + '%'
    
    dt = 'privacymarketcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'marketcaps': marketcaps, 'xmr_dominance': xmr_dominance, 'now_marketcap': now_marketcap, 'now_dominance': now_dominance, 'top_marketcap': top_marketcap, 'top_dominance': top_dominance, 'dates': dates}
    return render(request, 'charts/monerodominance.html', context)

###########################################
# Previous functions / Older versions                
###########################################

def sfmodel_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()

    update = True
    symbol = 'xmr'

    yesterday = date.today() - timedelta(1)
    start_time = datetime.datetime.strftime(yesterday, '%Y-%m-%d')
    try:
        coin = Coin.objects.filter(name=symbol).get(date=yesterday)
        if coin:
            coin.delete()
            update = False
            print('here')
            return 
            if (coin.inflation > 0) and (coin.priceusd > 0):
                update = False
            else:
                now = datetime.datetime.now()
                current_time = int(now.strftime("%H"))
                if current_time >= 5:
                    coin.delete()
                    update = True
        else:
            update = True
    except:
        update = True

    if update:
        #print('social')
        check_new_social('Bitcoin')
        check_new_social('Monero')
        check_new_social('CryptoCurrency')

        #print('metrics')
        with open("settings.json") as file:
            data = json.load(file)
            file.close()
            
        symbol = 'btc'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'dash'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'grin'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'zec'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        symbol = 'xmr'
        url = data["metrics_provider"][0]["metrics_url_new"] + symbol + '/' + start_time #url = data["metrics_provider"][0]["metrics_url"] + symbol + data["metrics_provider"][0]["metrics"] + '&start_time=' + start_time
        get_latest_metrics(symbol, url)
        #print('done')

    timevar = 1283
    now_price = 0
    now_sf = 0
    now_inflation = 0.001
    v0 = 0.002
    delta = (0.015 - 0.002)/(6*365)
    count = 0
    supply = 0
    stock = 0.000001
    dates = []
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
        stock = (100/(inflation))**1.65
        stock_to_flow.append(stock)            

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'
    
    dt = 'sfmodel.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow, 'projection': projection,
    'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodel.html', context)

def sfmodellin_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
        stock = (100/(100*reward*720*365/supply))**1.65
        stock_to_flow.append(stock)            

    now_price = "$"+ locale.format('%.2f', now_price, grouping=True)
    now_sf = "$"+ locale.format('%.2f', now_sf, grouping=True)
    now_inflation = locale.format('%.2f', now_inflation, grouping=True)+'%'
    
    dt = 'sfmodellin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'stock_to_flow': stock_to_flow, 'now_price': now_price, 'now_inflation': now_inflation, 'now_sf': now_sf, 'color': color}
    return render(request, 'charts/sfmodellin.html', context)

def dailyemission_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'dailyemission.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'high_xmr': high_xmr, 'high_btc': high_btc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemission.html', context)

def dailyemissionntv_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    emissionbtc = []
    emissionxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0
    supply_btc = 0
    supply_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        valuebtc = coin_btc.supply -  supply_btc
        if valuebtc < 0.000001:
            emissionbtc.append('')
        else:
            emissionbtc.append(valuebtc)
            now_btc = valuebtc
            supply_btc = coin_btc.supply
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                valuexmr = coin_xmr.supply - supply_xmr
                if valuexmr < 0.000001:
                    emissionxmr.append('')
                else:
                    emissionxmr.append(valuexmr)
                    now_xmr = valuexmr
                    supply_xmr = coin_xmr.supply
        else:
            emissionxmr.append('')

    for i in range(500):
        date_aux = coin_btc.date + timedelta(i)
        dates.append(datetime.datetime.strftime(date_aux, '%Y-%m-%d'))
        emissionbtc.append('')
        emissionxmr.append('')
        
    now_btc = locale.format('%.0f', now_btc, grouping=True)
    now_xmr = locale.format('%.0f', now_xmr, grouping=True)
    
    dt = 'dailyemissionntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'emissionxmr': emissionxmr, 'emissionbtc': emissionbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/dailyemissionntv.html', context)

def compinflation_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'compinflation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflationxmr': inflationxmr, 'inflationdash': inflationdash, 'inflationgrin': inflationgrin, 'inflationzcash': inflationzcash, 'inflationbtc': inflationbtc,
    'now_xmr': now_xmr, 'now_btc': now_btc, 'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/compinflation.html', context)

def bitcoin_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'bitcoin.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'btc': btc, 'xmr2': xmr2, 'btc2': btc2, 'xmr3': xmr3, 'dates': dates, 'dates2': dates2, 'dates3': dates3, 'dates4': dates4}
    return render(request, 'charts/bitcoin.html', context)

def coins_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'coins.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'supplyxmr': supplyxmr, 'supplybtc': supplybtc, 'fsupplyxmr': fsupplyxmr, 'fsupplybtc': fsupplybtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/coins.html', context)

def inflation_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'inflation.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'inflationxmr': inflationxmr, 'inflationbtc': inflationbtc, 'finflationxmr': finflationxmr, 'finflationbtc': finflationbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/inflation.html', context)

def extracoins_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'extracoins.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'nsupply': nsupply, 'fsupply': fsupply, 'dates': dates, 'now_diff': now_diff}
    return render(request, 'charts/extracoins.html', context)

def transcost_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
                else:
                    valuexmr = coin_xmr.fee*coin_xmr.priceusd/coin_xmr.transactions
                    if valuexmr < 0.0001:
                        costxmr.append('')
                    else:
                        costxmr.append(valuexmr)
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
    
    dt = 'transcost.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcost.html', context)

def transcostntv_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'transcostntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/transcostntv.html', context)

def metcalfesats_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'metcalfesats.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfesats.html', context)

def metcalfeusd_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'metcalfeusd.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'metcalfe': metcalfe, 'dates': dates, 'maximum': maximum, 'now_metcalfe': now_metcalfe, 'color': color, 'prices': prices, 'now_price': now_price}
    return render(request, 'charts/metcalfeusd.html', context)

def minerrevcap_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    coins_btc = Coin.objects.order_by('date').filter(name='btc')

    costbtc = []
    costxmr = []
    dates = []
    now_btc = 0
    now_xmr = 0

    for coin_btc in coins_btc:
        dates.append(datetime.datetime.strftime(coin_btc.date, '%Y-%m-%d'))
        if coin_btc.supply == 0:
            valuebtc = 0
        else:
            valuebtc = 365*100*coin_btc.revenue/coin_btc.supply
        if valuebtc < 0.0000001:
            costbtc.append('')
        else:
            costbtc.append(valuebtc)
            now_btc = valuebtc
        coins_xmr = Coin.objects.filter(name='xmr').filter(date=coin_btc.date)
        if coins_xmr:
            for coin_xmr in coins_xmr:
                if coin_xmr.supply == 0:
                    valuexmr = 0
                else:
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
    
    dt = 'minerrevcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevcap.html', context)

def marketcap_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'marketcap.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'xmr': xmr, 'dash': dash, 'grin': grin, 'zcash': zcash, 'now_xmr': now_xmr, 
    'now_dash': now_dash, 'now_grin': now_grin, 'now_zcash': now_zcash, 'dates': dates}
    return render(request, 'charts/marketcap.html', context)

def social_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
    dates = []
    dates2 = []
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

    socialsxmr = Social.objects.order_by('date').filter(name='Monero')
    for socialxmr in socialsxmr:
        dates2.append(datetime.datetime.strftime(socialxmr.date, '%Y-%m-%d'))
        if socialxmr.subscriberCount > last_xmr:
            social_xmr.append(socialxmr.subscriberCount)
            last_xmr = socialxmr.subscriberCount
        else:
            social_xmr.append(last_xmr)

    last_xmr = locale.format('%.0f', last_xmr, grouping=True)
    last_btc = locale.format('%.0f', last_btc, grouping=True)
    last_crypto = locale.format('%.0f', last_crypto, grouping=True)
    
    dt = 'social.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'dates2': dates2, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social.html', context)

def social2_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social2.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'dates2': dates2, 'social_btc': social_btc, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'last_btc': last_btc}
    return render(request, 'charts/social2.html', context)

def social3_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social3.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'last_xmr': last_xmr, 'last_crypto': last_crypto}
    return render(request, 'charts/social3.html', context)

def social4_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social4.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'speed_xmr': speed_xmr, 'speed_crypto': speed_crypto, 'speed_btc': speed_btc, 'newcomers_xmr': newcomers_xmr, 'newcomers_btc': newcomers_btc, 'newcomers_crypto': newcomers_crypto, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social4.html', context)

def social5_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social5.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'last_xmr': last_xmr, 'now_transactions': now_transactions, 'transactions': transactions, 'pricexmr': pricexmr}
    return render(request, 'charts/social5.html', context)

def social6_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social6.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social6.html', context)

def social7_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'social7.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'dates': dates, 'social_xmr': social_xmr, 'social_crypto': social_crypto, 'social_btc': social_btc, 'last_xmr': last_xmr, 'last_btc': last_btc, 'last_crypto': last_crypto}
    return render(request, 'charts/social7.html', context)

def minerrev_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'minerrev.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrev.html', context)

def minerrevntv_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'minerrevntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerrevntv.html', context)

def minerfees_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'minerfees.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfees.html', context)

def minerfeesntv_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'minerfeesntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/minerfeesntv.html', context)

def commit_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'commit.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commit.html', context)

def commitntv_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'commitntv.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'costxmr': costxmr, 'costbtc': costbtc, 'now_xmr': now_xmr, 'now_btc': now_btc, 'dates': dates}
    return render(request, 'charts/commitntv.html', context)

def percentage_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'percentage.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'transactions': transactions, 'dates': dates, 'now_transactions': now_transactions, 'maximum': maximum}
    return render(request, 'charts/percentage.html', context)

def pricesats_old(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)
        
    dt = datetime.datetime.now(timezone.utc).timestamp()
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
    
    dt = 'pricesats.html ' + locale.format('%.2f', datetime.datetime.now(timezone.utc).timestamp() - dt, grouping=True)+' seconds'
    print(dt)
    context = {'values': values, 'dates': dates, 'maximum': maximum, 'now_price': now_price, 'color': color, 'projection': projection, 'bottom': bottom}
    return render(request, 'charts/pricesats.html', context)