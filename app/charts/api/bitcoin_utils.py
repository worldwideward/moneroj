import json
import sys
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from datetime import timezone

from requests import get

BITCOIN_EXPLORER_API = "https://bitcoinexplorer.org/api"
NOW = datetime.now(timezone.utc)
PREVIOUS_DAY = NOW - timedelta(1)
YESTERDAY_STRING = datetime.strftime(PREVIOUS_DAY.date(), "%d-%m-%Y %H:%M:%S")
YESTERDAY = datetime.strptime(YESTERDAY_STRING,"%d-%m-%Y %H:%M:%S")

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
        print(f'[WARN] {BITCOIN_EXPLORER_API} unreachable: {error}')
        raise ValueError('[ERROR] Could not get blockchain tip')

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

def first_block_of_the_day(time_object, latest_block):

    print(f'[INFO] Searching the first block at {time_object}')

    latest_block = get_latest_block_height()

    latest_block_timestamp = get_block_timestamp(latest_block)
    latest_block_time_object = datetime.strptime(latest_block_timestamp, '%d-%m-%Y %H:%M')

    time_delta = latest_block_time_object - time_object
    seconds = time_delta.total_seconds()
    blocks_mined_since_time_object = int(seconds / 60 / 10)

    print(f'[INFO] There are approximately {blocks_mined_since_time_object} blocks mined since time object')

    first_block_today = latest_block - blocks_mined_since_time_object
    first_block_timestamp = get_block_timestamp(first_block_today)
    first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')

    print(f'[INFO] First block of day {time_object} seems to be {first_block_today} mined at {first_block_time_object}')

    compare_day = time_object.day - first_block_time_object.day

    while compare_day != 0:

        first_block_today = first_block_today + 1
        first_block_timestamp = get_block_timestamp(first_block_today)
        first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
        print(f'[INFO] First block of day {time_object} seems to be {first_block_today} mined at {first_block_time_object}')
        compare_day = time_object.day - first_block_time_object.day

    while 0 < first_block_time_object.hour < 24:

        if first_block_time_object.hour > 12:
            first_block_today = first_block_today - 60
        if first_block_time_object.hour > 3:
            first_block_today = first_block_today - 24
        if first_block_time_object.hour > 0:
            first_block_today = first_block_today - 1

        first_block_timestamp = get_block_timestamp(first_block_today)
        first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')

    print(f'[INFO] First block of day {time_object} seems to be {first_block_today} mined at {first_block_time_object}')
    return first_block_today

def range_of_blocks_today():

    latest_block = get_latest_block_height()

    if latest_block is None:
        raise SystemExit

    first_block_today = first_block_of_the_day(NOW, latest_block)
    first_block_yesterday = first_block_of_the_day(YESTERDAY, first_block_today)

    block_count = first_block_today - first_block_yesterday

    blocks_today = {
            "block_count": block_count,
            "start_block": first_block_yesterday,
            "end_block": first_block_today
            }

    return blocks_today
