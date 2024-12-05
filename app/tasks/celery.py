import sys
import os
import asyncio
import django
import time
import datetime
import json
from django.conf import settings
from redis import Redis
from celery import Celery
from tasks.data_sync import check_for_updates
from tasks.data_sync import check_monero_available
from tasks.data_sync import check_competitors_for_updates
from tasks.data_sync import check_daily_objects_for_updates
from tasks.data_sync import xmr_updates
from tasks.data_sync import competitors_updates
from tasks.data_sync import daily_objects_updates

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneropro.settings')

class celery():

    def __init__(self):
        self.host = settings.MONEROJ_REDIS_HOST
        self.agent = Celery('tasks', broker=f'redis://{self.host}/0', backend=f'redis://{self.host}')
        return None

def work():

    agent = celery().agent

    @agent.task
    def todo_list():

        message = check_monero_available()
        print(message)

        ## Set checks
        update_btc = False
        update_socials = False
        update_data = False

        ## Calculate time for this session
        date = datetime.date
        timedelta = datetime.timedelta

        now = int(datetime.datetime.now().strftime("%H"))
        yesterday = datetime.datetime.strftime(date.today() - timedelta(1), '%Y-%m-%d')
        date_aux = datetime.datetime.strftime(date.today() - timedelta(2), '%Y-%m-%d')

        ### check monero updates
        result = check_for_updates(yesterday)

        if result == True:
            print("Executing updates..")
            xmr_updates(yesterday, date_aux)

        ### check competitor updates
        result = check_competitors_for_updates(yesterday)

        if result == True:
            print("Executing updates..")
            competitors_updates(yesterday)

        result = check_daily_objects_for_updates(yesterday)

        if result == True:
            daily_objects_updates(yesterday, yesterday)

        print(f'executed all jobs', flush=True)
        return None

    todo_list()

    sys.exit(0)

work()
