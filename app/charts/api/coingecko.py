import os
import requests
import json

class CoingeckoAPI():

    def __init__(self):

        access_token = os.getenv("COINGECKO_API_KEY")

        self.endpoint = "https://api.coingecko.com/api/v3"
        self.headers = {
            "Content-Type": "application/json",
            "x-cg-demo-api-key": access_token
        }

        return None

    def get_coin_id(self, symbol):

        coin_id = None

        if symbol == 'xmr':
            coin_id = "monero"

        if symbol == 'btc':
            coin_id = "bitcoin"

        if symbol == 'zec':
            coin_id = "zcash"

        if symbol == 'dash':
            coin_id = 'dash'

        if symbol == 'grin':
            coin_id = 'grin'

        return coin_id

    def get_coin_realtime_data(self, symbol):

        coin_id = self.get_coin_id(symbol)

        url = f'{self.endpoint}/coins/{coin_id}'

        params = {
            "localization": "false",
            "ticker": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:

            json_data = json.loads(response.text)
            return json_data
        else:
            raise Exception(f'[ERROR] API Response: {response.status_code}')

    def get_global_realtime_data(self):

        url = f'{self.endpoint}/global'

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:

            json_data = json.loads(response.text)
            return json_data
        else:
            raise Exception(f'[ERROR] API Response: {response.status_code}')
