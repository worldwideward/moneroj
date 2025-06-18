import os
import json
import time
import re
import requests

from django.conf import settings
from bs4 import BeautifulSoup

TOR_HOST = settings.TOR_HOST
TOR_PORT = settings.TOR_PORT
TIMEOUT = 180
RETRY_COUNT = 3

class DreadSession():

    def __init__(self):

        self.endpoint = "http://dreadytofatroptsdj6io7l3xptbet6onoyno2yv7jicoxknyazubrad.onion"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Moneroj.net"
        }

        self.proxy = {
                "http": f'socks5h://{TOR_HOST}:{TOR_PORT}',
                "https": f'socks5h://{TOR_HOST}:{TOR_PORT}'
        }

        return None

    def get_coin_id(self, symbol):

        coin_id = None

        if symbol == 'xmr':
            coin_id = "monero"

        if symbol == 'btc':
            coin_id = "bitcoin"

        return coin_id

    def get_dread_subscriber_count(self, symbol):

        coin_id = self.get_coin_id(symbol)

        print(f'[INFO] Looking up Dread subscriber count for {coin_id}')

        if coin_id is None:

            print('[ERROR] This ticker symbol is not supported')
            return None

        url = f'{self.endpoint}/d/{coin_id}'

        session = requests.Session()
        retries = 0

        while retries < RETRY_COUNT:

            try:
                response = session.get(url, headers=self.headers, proxies=self.proxy, timeout=TIMEOUT)
                response_text = response.text

                if "Access Queue" in response_text:
                    print('[WARN] Bouncer detected')
                    time.sleep(10)
                else:
                    print('[INFO] Redirecting')
                    time.sleep(5)
                    break

            except Exception as error:
                response_text = None
                print(f'[DEBUG] {error}', flush=True)
                retries += 1
                time.sleep(10)

        if retries == RETRY_COUNT:

            print(f'[DEBUG] Too many retries ({retries}). Aborting lookup.')
            return None

        response = session.get(url, headers=self.headers, proxies=self.proxy, timeout=TIMEOUT)

        if response.status_code == 200:

            soup = BeautifulSoup(response.text, 'html.parser')

            search = soup.find(class_="subscriber_count")

            if search is None:

                print(f'[ERROR] Search for subscriber count failed: {response.text}')
                return None

            if len(search) > 0:
                text = search.contents[0]
                number_in_text = re.findall(r'\d+[,|.]?\d+', text)

                formatted_number = number_in_text[0].replace(',', '')

                subscriber_count = int(formatted_number)
            else:
                print(f'[ERROR] Subscriber count not found on this page, search returned {len(search)} results')
                return None

        else:
            print(f'[ERROR] Request not succesful, returned HTTP status: {response.status_code}')
            return None

        return subscriber_count
