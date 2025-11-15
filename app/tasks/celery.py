'''Celery worker'''

import sys
import os

from datetime import datetime
from datetime import timedelta
from datetime import date

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
from tasks.data_sync import update_merchants_data
from tasks.data_sync import update_dex_volume

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneropro.settings')


class TaskWorker():
    '''Celery worker configuration'''

    def __init__(self):
        self.host = settings.MONEROJ_REDIS_HOST
        self.agent = Celery('tasks', broker=f'redis://{self.host}/0', backend=f'redis://{self.host}')

def get_times():

    today = date.today()
    yesterday = datetime.strftime(today - timedelta(1), '%Y-%m-%d')
    print(f'[INFO] Today: {today}')
    print(f'[INFO] Yesterday: {yesterday}')

    return today, yesterday

def work():
    '''Celery worker logic'''

    agent = TaskWorker().agent

    @agent.task
    def update_xmr_data():

        print('[INFO] Check for XMR updates')

        try:
            today, yesterday = get_times()
            result = check_for_updates(yesterday, "xmr")

            if result is True:
                print('[INFO] Update XMR coin data')
                update_coin_data("xmr", yesterday, today)
            else:
                print('[WARN] Skipped updating XMR coin data')

            print('[INFO] Update XMR marketcap')
            update_xmr_marketcap()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def update_btc_data():

        print('[INFO] Check for Bitcoin updates')

        try:
            today, yesterday = get_times()
            result = check_for_updates(yesterday, "btc")

            if result is True:
                print("[INFO] Update Bitcoin coin data", flush=True)
                update_coin_data("btc", yesterday, today)
            else:
                print('[WARN] Skipped updating Bitcoin coin data')

        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def update_dash_data():

        print('[INFO] Check for Dash updates')

        try:
            today, yesterday = get_times()
            result = check_for_updates(yesterday, "dash")

            if result is True:
                print("[INFO] Update Dash coin data", flush=True)
                update_coin_data("dash", yesterday, today)
            else:
                print('[WARN] Skipped updating Dash coin data')

        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def update_zec_data():

        print('[INFO] Check for Zcash updates')

        try:
            today, yesterday = get_times()
            result = check_for_updates(yesterday, "zec")

            if result is True:
                print("[INFO] Update Zcash coin data", flush=True)
                update_coin_data("zec", yesterday, today)
            else:
                print('[WARN] Skipped updating Zcash coin data')

        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def update_grin_data():

        print('[INFO] Check for Grin updates')

        try:
            today, yesterday = get_times()
            result = check_for_updates(yesterday, "grin")

            if result is True:
                print("[INFO] Update Grin coin data", flush=True)
                update_coin_data("grin", yesterday, today)
            else:
                print('[WARN] Skipped updating Grin coin data')

        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def update_database():

        print('[INFO] Check for Daily data updates')

        try:
            today, yesterday = get_times()
            result = check_daily_objects_for_updates(yesterday)

            if result is True:
                print(f'[INFO] Update daily data for {yesterday}', flush=True)
                daily_objects_updates(yesterday)
            else:
                print('[WARN] Skipped updating daily data')

            print('[INFO] Perform marketcap updates')
            recalculate_sf_model()
            recalculate_daily_data()

        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def mining_data_updates():
        print('[INFO] perform P2Pool updates')

        try:
            update_p2pool_data()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def social_data_updates():
        print('[INFO] Perform Dread updates')

        try:
            today, yesterday = get_times()
            update_dread_subscriber_count(today)

            print('[INFO] Perform Reddit updates')
            update_reddit_data()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def merchants_data_updates():
        print('[INFO] Perform merchant adoption data updates')
        try:
            update_merchants_data()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def transactions_data_updates():
        print('[INFO] Perform transaction data updates')
        try:
            update_shielded_transactions()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    @agent.task
    def volume_data_updates():
        print('[INFO] Perform Dex volume updates')
        try:
            update_dex_volume()
        except Exception as error:
            print(f'[ERROR] Something went wrong while fetching data: {error}')

    ## Run all tasks
    update_xmr_data()
    update_btc_data()
    update_dash_data()
    update_zec_data()
    update_grin_data()
    update_database()
    mining_data_updates()
    social_data_updates()
    merchants_data_updates()
    transactions_data_updates()
    volume_data_updates()

    sys.exit(0)

work()
