'''Celery worker'''

import sys
import os
import datetime
import asyncio
from django.conf import settings
from celery import Celery
from tasks.data_sync import check_for_updates
from tasks.data_sync import check_monero_available
from tasks.data_sync import check_competitors_for_updates
from tasks.data_sync import check_daily_objects_for_updates
from tasks.data_sync import xmr_updates
#from tasks.data_sync import competitors_updates
from tasks.data_sync import daily_objects_updates
from tasks.data_sync import recalculate_sf_model
from tasks.data_sync import recalculate_daily_data

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

        message = check_monero_available()
        print(message, flush=True)

        ## Calculate time for this session
        date = datetime.date
        timedelta = datetime.timedelta

        yesterday = datetime.datetime.strftime(date.today() - timedelta(1), '%Y-%m-%d')
        date_aux = datetime.datetime.strftime(date.today() - timedelta(2), '%Y-%m-%d')

        ### check monero updates
        result = check_for_updates(yesterday, "xmr")

        if result is True:
            print("[INFO] Executing XMR updates..", flush=True)
            await xmr_updates(yesterday, date_aux)

        ### check competitor updates
        result = check_competitors_for_updates(yesterday)

#        if result is True:
#            print("[INFO] Executing Competitor updates..", flush=True)
#            await competitors_updates(yesterday)

        result = check_daily_objects_for_updates(yesterday)

        if result is True:
            print(f'[INFO] Executing daily updates for {yesterday}', flush=True)
            daily_objects_updates(yesterday)

        recalculate_sf_model()

        recalculate_daily_data()

        ### Load marketcap and dominance
        #load_dominance()


        print('[INFO] Executed all jobs', flush=True)
        return None

    asyncio.run(todo_list())

    sys.exit(0)

work()
