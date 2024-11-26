import datetime
import asyncio

from moneropro import settings
from charts.models import Coin
from charts.asynchronous import update_xmr_data
from charts.asynchronous import update_others_data
from charts.synchronous import update_database
from charts.synchronous import get_history_function

date = datetime.date
timedelta = datetime.timedelta

yesterday = datetime.datetime.strftime(date.today() - timedelta(1), '%Y-%m-%d')
date_aux = datetime.datetime.strftime(date.today() - timedelta(2), '%Y-%m-%d')

async def update_data():

    try:
        coin_xmr = list(Coin.objects.filter(name='xmr').order_by('-date'))[0]
    except:
        coin_xmr = Coin.objects.filter(name='xmr').get(date=date_aux)

    print(f'[INFO] XMR: {coin_xmr}')

    count = get_history_function('xmr', yesterday, yesterday)


    await update_xmr_data(yesterday, coin_xmr)

    await update_others_data(yesterday)

    update_database(yesterday, yesterday)

asyncio.run(update_data())
