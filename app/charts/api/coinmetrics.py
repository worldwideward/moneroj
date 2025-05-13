import requests
import json

class CoinmetricsAPI():

    def __init__(self):

        self.endpoint = "https://community-api.coinmetrics.io/v4"

        return None

    def get_asset_metrics(self, symbol, start_time=None, end_time=None):

        metrics="PriceUSD,PriceBTC,IssContPctAnn,SplyCur,FeeTotNtv,RevNtv,HashRate,TxCnt,BlkSizeMeanByte,DiffLast"

        if not(start_time and end_time):

            start_time = '2008-01-01'
            end_time = '2100-01-01'

        url = f'{self.endpoint}/timeseries/asset-metrics?assets={symbol}&start_time={start_time}&end_time={end_time}&metrics={metrics}'

        headers = {"Content-Type": "application/json"}

        response = requests.get(url, timeout=60, headers=headers)

        print(f'[DEBUG] Response status: {response.status_code}')

        json_data = json.loads(response.text)

        if response.status_code == 200:

            data = []
            data.extend(json_data["data"])

            print(f'[DEBUG] Data length: {len(json_data["data"])}')

            while len(json_data["data"]) == 100:

                url = json_data["next_page_url"]
                response = requests.get(url, timeout=60, headers=headers)
                json_data = json.loads(response.text)

                if response.status_code == 400:

                    raise Exception(json_data["error"]["type"])

                data.extend(json_data["data"])
                print(f'[DEBUG] Data length next page: {len(json_data["data"])}')

            print(f'[DEBUG] Total data length: {len(data)}')

            return data

        if response.status_code == 400:
            raise Exception(json_data["error"]["type"])
        else:
            raise Exception
