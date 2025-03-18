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
from tasks.data_sync import competitors_updates
from tasks.data_sync import daily_objects_updates
from tasks.data_sync import populate_database

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
        print(message)

        ## Calculate time for this session
        date = datetime.date
        timedelta = datetime.timedelta

        yesterday = datetime.datetime.strftime(date.today() - timedelta(1), '%Y-%m-%d')
        date_aux = datetime.datetime.strftime(date.today() - timedelta(2), '%Y-%m-%d')

        ### check monero updates
        result = check_for_updates(yesterday)

        if result is True:
            print("Executing XMR updates..")
            await xmr_updates(yesterday, date_aux)

        ### check competitor updates
        result = check_competitors_for_updates(yesterday)

        if result is True:
            print("Executing Competitor updates..")
            await competitors_updates(yesterday)

        result = check_daily_objects_for_updates(yesterday)

        if result is True:
            print("Executing daily updates..")
            daily_objects_updates(yesterday)

        ### Populate the database
        populate_database()


        print('Executed all jobs', flush=True)
        return None

    asyncio.run(todo_list())

    sys.exit(0)

work()
