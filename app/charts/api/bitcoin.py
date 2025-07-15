import os
import sys
import json
import asyncio
import aiohttp

from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from datetime import timezone

from requests.exceptions import ConnectionError
from urllib3.exceptions import NameResolutionError
from concurrent import futures

from charts.api.bitcoin_utils import range_of_blocks_today

BITCOIN_EXPLORER_API = "https://bitcoinexplorer.org/api"
FILE_CACHE_PATH = "/tmp/bitcoin-explorer-api"

def create_file_cache(path):

    try:
        os.mkdir(path)
        print(f'[INFO] Directory {path} created')
    except FileExistsError:
        pass
    except PermissionError:
        print(f'[WARN] Permission denied: Unable to create directory {path}')
        return False
    except Exception as error:
        print(f'[ERROR] An unknown error occured: {error}')
        return False
    return True

def download_blockchain_data_wrapper(uri, object_list, directory):
    return asyncio.run(download_blockchain_data(uri, object_list, directory))

async def download_blockchain_data(uri, object_list, directory_name):

    download_data = []
    connection_error_count = 0

    increment = 100 / len(object_list)
    progress = 0

    cache = create_file_cache(f'{FILE_CACHE_PATH}/{directory_name}')
    if cache is False:
        raise SystemExit

    async with aiohttp.ClientSession() as session:

        for item in object_list:

            data_filename = f'{FILE_CACHE_PATH}/{directory_name}/{item}.json'
            data_file = os.path.isfile(data_filename)

            if data_file is False:
                try:
                    path = f'{uri}/{item}'
                    async with session.get(path) as response:
                        data = await response.json()

                        with open(data_filename, "w") as file:
                            file.write(str(data))

                except ConnectionError as error:
                    connection_error_count += 1
                    print(f'[WARN] No data for {item}, Connection error: {error}')
                except NameResolutionError as error:
                    connection_error_count += 1
                    print(f'[WARN] No data for {item}, Connection error: {error}')
                except aiohttp.client_exceptions.ClientConnectorDNSError as error:
                    connection_error_count += 1
                    print(f'[WARN] No data for {item}, Connection error: {error}')

            with open(data_filename, "r") as file:
                content = file.read()
                download_data.append(eval(content))

            progress += increment
            print(f'[INFO] {round(progress, 2)} % of transactions downloaded', end='\r')

    return download_data

def analyze_transaction_data(tx_data):
    '''Determine if a transaction is likely an Ashigaru whirlpool TX0'''

    string = tx_data['vout'][0]['scriptPubKey']['asm']

    if string.find("OP_RETURN") != -1:

        tx_id = tx_data['txid']
        tx_out_list = tx_data['vout']

        in_count = len(tx_data['vin'])
        out_count = len(tx_data['vout'])

        for vout in tx_out_list:

            if 0.0125 <= vout['value'] <= 0.01259:
                print(f'[INFO] TX with id {tx_id} has an output with value: {vout['value']} - inputs: {in_count} outputs: {out_count} ')
                if len(tx_data['vin']) == len(tx_data['vout']):
                    return tx_id

            if 0.00125 <= vout['value'] <= 0.001259:
                print(f'[INFO] TX with id {tx_id} has an output with value: {vout['value']} - inputs: {in_count} outputs: {out_count} ')
                if len(tx_data['vin']) == len(tx_data['vout']):
                    return tx_id

            if len(tx_data['vin']) == 5 and len(tx_data['vout']) == 5:
                print(f'[INFO] TX with id {tx_id} has an output with value: {vout['value']} - inputs: {in_count} outputs: {out_count} ')
                return tx_id
    return None

def whirlpool_analysis():

    blocks = range_of_blocks_today()

    if blocks is None:
        return None

    first_block_today = blocks["end_block"]
    first_block_yesterday = blocks["start_block"]
    block_count = blocks["block_count"]

    process_start = datetime.now(timezone.utc)

    print(f'[INFO] Analyzing {block_count} blocks, from {first_block_yesterday} to {first_block_today}')
    print(f'[INFO] Starting process at {process_start}')

    ## 1. Download block data

    block_range = range(first_block_yesterday, first_block_today)
    block_uri = f'{BITCOIN_EXPLORER_API}/block'

    block_data = asyncio.run(download_blockchain_data(block_uri, block_range, 'blocks'))

    total_tx_count = 0

    for block in block_data:
        total_tx_count += block['nTx']

    print(f'[DEBUG] Attempting to analyze {total_tx_count} transactions')

    ## 2. Download transaction data
    with futures.ProcessPoolExecutor(len(block_data)) as pool:

        tasks = []
        task_count = 0
        all_tx_data = []
        progress = 0

        tx_uri = f'{BITCOIN_EXPLORER_API}/tx'

        for block in block_data:
            tasks.append(pool.submit(download_blockchain_data_wrapper, tx_uri, block['tx'], "transactions"))

        completed_tasks = futures.as_completed(tasks)
        increment = 100 / len(tasks)

        for task in completed_tasks:

            block_tx_data = task.result()
            all_tx_data.append(block_tx_data)

            task_count += 1
            progress += increment
            process_end = datetime.now(timezone.utc)
            delta = process_end - process_start
            delta_minutes = delta.seconds / 60
            print(f'[INFO] {round(progress, 2)} % of Tasks completed {task_count}/{len(tasks)} in {delta_minutes} minutes', end='\r')

    ## 3. Analyse transaction data
    whirlpool_tx_list = []

    for block_tx_data in all_tx_data:
        for tx_data in block_tx_data:
            whirlpool_tx_id = analyze_transaction_data(tx_data)
            if whirlpool_tx_id != None:
                whirlpool_tx_list.append(whirlpool_tx_id)

    whirlpool_tx_count = len(whirlpool_tx_list)
    process_end = datetime.now(timezone.utc)
    delta = process_end - process_start
    delta_minutes = delta.seconds / 60

    print(f'[INFO] There are {whirlpool_tx_count} whirlpool UTX0s today')
    print(f'[INFO] Ending process at {process_end}')
    print(f'[INFO] This calculation took {round(delta_minutes, 2)} minutes')

    return whirlpool_tx_count
