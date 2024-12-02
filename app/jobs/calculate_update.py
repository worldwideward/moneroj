def calculate_update():
    coins = Coin.objects.filter(name='xmr').order_by('-date')
    count = 0
    for coin in coins:
        count += 1
        if count< 200:
            if coin.supply < 18000000:
                coin.supply += 499736
                print(coin.date)
                coin.save()

    coin = list(Coin.objects.order_by('-date'))[0]
    if not(coin):
        message = 'Website under maintenance. Check back in a few minutes'
        context = {'message': message}
        return render(request, 'charts/maintenance.html', context)

    now = int(datetime.datetime.now().strftime("%H"))
    yesterday = datetime.datetime.strftime(date.today() - timedelta(1), '%Y-%m-%d')
    date_aux = datetime.datetime.strftime(date.today() - timedelta(2), '%Y-%m-%d')
    update_xmr = False
    update_btc = False
    update_socials = False
    update_data = False

    if now > 2 and now < 12:
        try:
            coin_xmr = Coin.objects.filter(name='xmr').get(date=yesterday)
            if coin_xmr:
                print('xmr found yesterday')
                if coin_xmr.priceusd > 1 and coin_xmr.transactions > 0 and coin_xmr.inflation > 0:
                    print('no need to update xmr')
                    update_xmr = False
                else:
                    print('will update xmr')
                    coin_xmr.delete()
                    update_xmr = True
            else:
                print('no xmr found yesterday - 1')
                update_xmr = True
        except:
            print('no xmr found yesterday - 2')
            update_xmr = True
    if now > 6 and now < 12:
        try:
            coin_btc = list(Coin.objects.filter(name='btc').filter(date=yesterday))[0]
            coin_zec = list(Coin.objects.filter(name='zec').filter(date=yesterday))[0]
            coin_dash = list(Coin.objects.filter(name='dash').filter(date=yesterday))[0]
            coin_grin = list(Coin.objects.filter(name='grin').filter(date=yesterday))[0]
            if coin_btc and coin_zec and coin_dash and coin_grin:
                print('coins found yesterday')
                if coin_btc.transactions > 0 and coin_btc.inflation > 0 and coin_zec.supply > 0 and coin_dash.supply > 0 and coin_grin.supply > 0:
                    print('no need to update coins')
                    update_btc = False
                else:
                    print('will update coins')
                    coin_btc.delete()
                    coin_zec.delete()
                    coin_dash.delete()
                    coin_grin.delete()
                    update_btc = True
            else:
                print('no coins found yesterday - 1')
                update_btc = True
        except:
            print('no coins found yesterday - 2')
            update_btc = True
        try:
            data = list(DailyData.objects.filter(date=yesterday))[0]
            if data:
                print('data found yesterday')
                update_data = False
            else:
                print('no data found yesterday - 1')
                update_data = True
        except:
            print('no data found yesterday - 2')
            update_data = True

    ## To update job

    try:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)
    except:
        coin_xmr = list(Coin.objects.filter(name='xmr').order_by('-date'))[0]

    if update_xmr:
        count = get_history_function('xmr', yesterday, yesterday)
        await asynchronous.update_xmr_data(yesterday, coin_xmr)

    if update_btc:
        await asynchronous.update_others_data(yesterday)

    if update_data:
        synchronous.update_database(yesterday, yesterday)

    if True:
        enabled = synchronous.get_binance_withdrawal('Monero')

    supply = locale._format('%.0f', coin_xmr.supply, grouping=True)
    inflation = locale._format('%.2f', coin_xmr.inflation, grouping=True)+'%'
    context = {'inflation': inflation, 'supply': supply, 'enabled': enabled}

