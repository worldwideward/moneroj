import datetime
from charts.models import Coin
from charts.asynchronous import update_xmr_data
from charts.synchronous import get_history_function

def xmr_updates(yesterday, date_aux):

    try:
        coin_xmr = list(Coin.objects.filter(name='xmr').order_by('-date'))[0]
    except:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)

    print(f'[INFO] XMR: {coin_xmr}')
    count = get_history_function('xmr', yesterday, yesterday)
    update_xmr_data(yesterday, coin_xmr)

    return None

def check_for_updates(yesterday) -> bool:
    '''Check if it is necessary to update coin data'''

    try:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=yesterday)
        print(coin_xmr, flush=True)
        if coin_xmr:
            print('xmr found yesterday', flush=True)
            if coin_xmr.priceusd > 1 and coin_xmr.transactions > 0 and coin_xmr.inflation > 0:
                print('no need to update xmr', flush=True)
            else:
                print('will update xmr')
                coin_xmr.delete()
                return True
        else:
            print('no xmr found yesterday - 1')
            return True
    except Exception as error:
        print(f'Exception while trying to look for coin data - {error}')
        return True

    return False

def check_competitors_for_updates(yesterday) -> bool:
    try:
        coin_btc = list(Coin.objects.filter(name='btc').filter(date=yesterday))[0]
        coin_zec = list(Coin.objects.filter(name='zec').filter(date=yesterday))[0]
        coin_dash = list(Coin.objects.filter(name='dash').filter(date=yesterday))[0]
        coin_grin = list(Coin.objects.filter(name='grin').filter(date=yesterday))[0]

        if coin_btc and coin_zec and coin_dash and coin_grin:
            print('coins found yesterday')
            if coin_btc.transactions > 0 and coin_btc.inflation > 0 and coin_zec.supply > 0 and coin_dash.supply > 0 and coin_grin.supply > 0:
                print('no need to update coins')
            else:
                print('will update coins')
                coin_btc.delete()
                coin_zec.delete()
                coin_dash.delete()
                coin_grin.delete()
                return True
        else:
            print('no coins found yesterday - 1')
            return True
    except:
        print('no coins found yesterday - 2')
        return True

    return False

def check_daily_objects_for_updates(yesterday) -> bool:

    try:
        data = list(DailyData.objects.filter(date=yesterday))[0]
        if data:
            print('data found yesterday')
        else:
            print('no data found yesterday - 1')
            return True
    except:
        print('no data found yesterday - 2')
        return True

    return False

def check_monero_available() -> str:
    '''Check if coin data about Monero is present'''

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

    message = coin

    if not(coin):
        message = 'Monero unavailable'

    return message
