import json
import sys
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from datetime import timezone

from requests import get

BITCOIN_EXPLORER_API = "https://bitcoinexplorer.org/api"

NOW_TZ = datetime.now(timezone.utc)
NOW = NOW_TZ.replace(tzinfo=None)
PREVIOUS_DAY = NOW - timedelta(1)

YESTERDAY_STRING = datetime.strftime(PREVIOUS_DAY.date(), "%d-%m-%Y %H:%M:%S")
YESTERDAY_TZ = datetime.strptime(YESTERDAY_STRING,"%d-%m-%Y %H:%M:%S")
YESTERDAY = YESTERDAY_TZ.replace(tzinfo=None)

AVG_BLOCKS_PER_DAY=144

def get_blocks_mined_today(time_object):

    hour = time_object.hour
    minutes = time_object.minute
    hour_in_minutes = hour * 60
    total_minutes_today = hour_in_minutes + minutes

    blocks_mined_today = int(round(total_minutes_today / 10))

    return blocks_mined_today

def get_latest_block_height():

    try:
        response = get(f'{BITCOIN_EXPLORER_API}/blocks/tip', timeout=60)
        data = json.loads(response.text)
        latest_block = int(data['height'])
        return latest_block

    except Exception as error:
        print(f'[ERROR] Could not get latest block - {BITCOIN_EXPLORER_API} unreachable: {error}')
        return None

def get_block_timestamp(block_height):

    try:
        response = get(f'{BITCOIN_EXPLORER_API}/block/header/{block_height}', timeout=60)
        data = json.loads(response.text)
        epoch = data['time']
        timestamp = datetime.fromtimestamp(epoch, timezone.utc).strftime('%d-%m-%Y %H:%M')
        print(f'[INFO] Block {block_height} was mined at {timestamp}')
        return timestamp

    except Exception as error:
        print(f'[WARN] {BITCOIN_EXPLORER_API} unreachable: {error}')
        return None

def compare_days_of_time_objects(first_day, second_day):
    '''Compare if two time objects share the same day'''

    compare = first_day - second_day

    if compare > 0:
        # First time object is more recent than second time object
        return False
    if compare < 0:
        # First time object is less recent than second time object
        return False
    if compare == 0:
        # First and second time object share the same day
        return True

def evaluate_hour_of_time_object(hour):
    '''Check if the hour is between 0 and 1 am'''

    # The interval is the amount of blocks that will be added / substracted

    if hour > 12:
        interval = 60
        return interval
    if hour > 2:
        interval = 24
        return interval
    if hour > 0:
        interval = 1
        return interval
    if hour == 0:
        interval = 0
        return interval

def find_first_block(first_block_today, time_object, first_block_time_object):

    retry = 0
    while 0 < first_block_time_object.hour < 24 and retry <= 3:

        # assumed first block was mined later than 1 am
        # so we will check if a block was mined already before this point in time

        interval = evaluate_hour_of_time_object(first_block_time_object.hour)

        compare_days = compare_days_of_time_objects(time_object.day, first_block_time_object.day)

        if compare_days is True: # assumed first block was mined on the same day as the supplied time object

            first_block_today = first_block_today - interval
            first_block_timestamp = get_block_timestamp(first_block_today)
            first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')

        if compare_days is False:

            first_block_today = first_block_today + 1
            first_block_timestamp = get_block_timestamp(first_block_today)
            first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
            retry += 1

    return first_block_today, first_block_time_object

def first_block_of_the_day(time_object):

    print('--------------------------------------------------')
    print(f'[INFO] Searching the first block at {time_object}')

    latest_block = get_latest_block_height()

    if latest_block is None:
        return None

    latest_block_timestamp = get_block_timestamp(latest_block)
    latest_block_time_object = datetime.strptime(latest_block_timestamp, '%d-%m-%Y %H:%M')
    latest_block_time = datetime.strftime(latest_block_time_object, '%d-%m-%Y %H:%M:%S')

    time_delta = latest_block_time_object - time_object
    seconds = time_delta.total_seconds()
    blocks_mined_since_time_object = int(seconds / 60 / 10)

    print(f'[INFO] There are approximately {blocks_mined_since_time_object} blocks mined since {time_object}')

    start_of_day = time_object.date()
    start_of_day_string = datetime.strftime(start_of_day, '%d-%m-%Y %H:%M')
    start_of_day_time_object = datetime.strptime(start_of_day_string, '%d-%m-%Y %H:%M')

    now = datetime.strftime(time_object, '%d-%m-%Y %H:%M:%S')
    morning = datetime.strftime(start_of_day, '%d-%m-%Y %H:%M:%S')

    print(f'[INFO] Now: {now} Morning : {morning}')

    if latest_block_time_object.day == start_of_day.day:
        print('[INFO] Latest block mined same day as the submitted time')

        time_delta = latest_block_time_object - start_of_day_time_object
        seconds = time_delta.total_seconds()
        blocks_mined_since_time_object = int(seconds / 60 / 10)
        print(f'[INFO] There are approximately {blocks_mined_since_time_object} blocks mined since {start_of_day}')

        first_block_today = latest_block - blocks_mined_since_time_object
        first_block_timestamp = get_block_timestamp(first_block_today)
        first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
        first_block_today, first_block_time_object = find_first_block(first_block_today, time_object, first_block_time_object)
        print(f'[INFO] First block of day {time_object} seems to be {first_block_today} mined at {first_block_time_object}')


    if latest_block_time_object.day > start_of_day.day:
        print('[INFO] Latest block mined a more recent day than the submitted time')

        time_delta = latest_block_time_object - start_of_day_time_object
        seconds = time_delta.total_seconds()
        blocks_mined_since_time_object = int(seconds / 60 / 10)
        print(f'[INFO] There are approximately {blocks_mined_since_time_object} blocks mined since {start_of_day}')

        first_block_today = latest_block - blocks_mined_since_time_object
        first_block_timestamp = get_block_timestamp(first_block_today)
        first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
        first_block_today, first_block_time_object = find_first_block(first_block_today, time_object, first_block_time_object)
        print(f'[INFO] First block of day {time_object} seems to be {first_block_today} mined at {first_block_time_object}')

    if latest_block_time_object.day < start_of_day.day:
        raise ValueError("[ERROR] Latest block mined on a day before the submitted time. Did you specify a date in the future?")

    return first_block_today

def range_of_blocks_today():

    first_block_today = first_block_of_the_day(NOW)
    first_block_yesterday = first_block_of_the_day(YESTERDAY)

    if first_block_today is None:
        return None

    block_count = first_block_today - first_block_yesterday

    blocks_today = {
            "block_count": block_count,
            "start_block": first_block_yesterday,
            "end_block": first_block_today
            }

    return blocks_today
