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
        return None

def get_block_timestamp(block_height):

    try:
        response = get(f'{BITCOIN_EXPLORER_API}/block/{block_height}', timeout=60)
        data = json.loads(response.text)
        epoch = data['time']
        timestamp = datetime.fromtimestamp(epoch, timezone.utc).strftime('%d-%m-%Y %H:%M')
        return timestamp

    except Exception as error:
        print(f'[WARN] {BITCOIN_EXPLORER_API} unreachable: {error}')
        return None

def verify_first_block(block_timestamp, block_height):

    time_object = datetime.strptime(block_timestamp, '%d-%m-%Y %H:%M')

    if time_object.hour < 1:

        if time_object.minute < 10:
            return True
    return False

def first_block_of_the_day(time_object, latest_block):

    blocks_mined = get_blocks_mined_today(time_object)
    first_block_today = latest_block - blocks_mined
    first_block_timestamp = get_block_timestamp(first_block_today)
    today_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')

    print(f'[INFO] Searching the first block at {time_object}')
    print(f'[INFO] There are {blocks_mined} blocks mined this day')
    print(f'[INFO] The last block this day has height {latest_block}')
    print(f'[INFO] The first block this day has height {first_block_today} at {first_block_timestamp}')

    if blocks_mined == 0:
        return first_block_today

    first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
    check = time_object.day - first_block_time_object.day

    if check != 0:
        print('[ERROR] Going to far back')
        first_block_today = first_block_today + 1
        first_block_timestamp = get_block_timestamp(first_block_today)
        print(f'[INFO] The first block today has height {first_block_today} at {first_block_timestamp}')
        return first_block_today

    verify = verify_first_block(first_block_timestamp, first_block_today)

    while verify is False:

        first_block_today = first_block_today - 1
        first_block_timestamp = get_block_timestamp(first_block_today)
        first_block_time_object = datetime.strptime(first_block_timestamp, '%d-%m-%Y %H:%M')
        check = today_time_object.day - first_block_time_object.day
        print(f'[INFO] The first block today has height {first_block_today} at {first_block_timestamp}')
        verify = verify_first_block(first_block_timestamp, first_block_today)

        if check != 0:
            print('[ERROR] Going to far back')
            first_block_today = first_block_today + 1
            print(f'[INFO] Will use {first_block_today} as the first block for this period')
            break

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
