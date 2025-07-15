'''Celery worker'''

import sys
import os

from datetime import datetime
from datetime import timedelta
from datetime import date

import asyncio
from django.conf import settings
from celery import Celery
from tasks.data_sync import check_for_updates
from tasks.data_sync import check_daily_objects_for_updates
from tasks.data_sync import update_xmr_marketcap
from tasks.data_sync import update_coin_data
from tasks.data_sync import daily_objects_updates
from tasks.data_sync import recalculate_sf_model
from tasks.data_sync import recalculate_daily_data
from tasks.data_sync import update_dread_subscriber_count
from tasks.data_sync import update_reddit_data
from tasks.data_sync import update_p2pool_data
from tasks.data_sync import update_shielded_transactions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneropro.settings')


class TaskWorker():
    '''Celery worker configuration'''

    def __init__(self):
        self.host = settings.MONEROJ_REDIS_HOST
        self.agent = Celery('tasks', broker=f'redis://{self.host}/0', backend=f'redis://{self.host}')

def work():
    '''Celery worker logic'''

    agent = TaskWorker().agent

    @agent.task
    async def todo_list():
        '''Tasks the worker should perform each run'''

        ## Calculate time for this session
        today = date.today()
        yesterday = datetime.strftime(today - timedelta(1), '%Y-%m-%d')
        date_aux = datetime.strftime(today - timedelta(2), '%Y-%m-%d')

        print(f'[INFO] Today: {today}')
        print(f'[INFO] Yesterday: {yesterday}')
        print(f'[INFO] Two days ago: {date_aux}')

        print('[INFO] Check for XMR updates')
        result = check_for_updates(yesterday, "xmr")

        if result is True:
            print('[INFO] Update XMR coin data')
            update_coin_data("xmr", yesterday, today)
        else:
            print('[WARN] Skipped updating XMR coin data')

        print('[INFO] Update XMR marketcap')
        update_xmr_marketcap()

        print('[INFO] Check for competitor updates')

        print('[INFO] Check for Bitcoin updates')

        result = check_for_updates(yesterday, "btc")

        if result is True:
            print("[INFO] Update Bitcoin coin data", flush=True)
            update_coin_data("btc", yesterday, today)
        else:
            print('[WARN] Skipped updating Bitcoin coin data')

        print('[INFO] Check for Dash updates')

        result = check_for_updates(yesterday, "dash")

        if result is True:
            print("[INFO] Update Dash coin data", flush=True)
            update_coin_data("dash", yesterday, today)
        else:
            print('[WARN] Skipped updating Dash coin data')

        print('[INFO] Check for Zcash updates')

        result = check_for_updates(yesterday, "zec")

        if result is True:
            print("[INFO] Update Zcash coin data", flush=True)
            update_coin_data("zec", yesterday, today)
        else:
            print('[WARN] Skipped updating Zcash coin data')

        print('[INFO] Check for Grin updates')

        result = check_for_updates(yesterday, "grin")

        if result is True:
            print("[INFO] Update Grin coin data", flush=True)
            update_coin_data("grin", yesterday, today)
        else:
            print('[WARN] Skipped updating Grin coin data')

        print('[INFO] Check for Daily data updates')

        result = check_daily_objects_for_updates(yesterday)

        if result is True:
            print(f'[INFO] Update daily data for {yesterday}', flush=True)
            daily_objects_updates(yesterday)
        else:
            print('[WARN] Skipped updating daily data')

        print('[INFO] Perform marketcap updates')
        recalculate_sf_model()
        recalculate_daily_data()

        print('[info] perform P2Pool updates')
        update_p2pool_data()

        print('[info] perform dread updates')
        update_dread_subscriber_count(today)

        print('[info] perform reddit updates')
        update_reddit_data()

        print('[INFO] Executed all jobs', flush=True)
        return None

    asyncio.run(todo_list())

    @agent.task
    def shielded_transactions():
        print('[info] perform transactions updates')
        update_shielded_transactions()

    sys.exit(0)

work()
