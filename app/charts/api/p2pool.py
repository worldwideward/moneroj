import requests
import json

class P2PoolAPI():

    def __init__(self):

        self.endpoint = "https://p2pool.io/api/pool/stats"

        self.endpoint_mini = "https://p2pool.io/mini/api/pool/stats"

        return None

    def get_json_data(self, mini=bool):

        if mini == True:
            url = f'{self.endpoint_mini}'

        if mini == False:
            url = f'{self.endpoint}'

        response = requests.get(url, timeout=60)

        if response.status_code == 200:

            json_data=json.loads(response.text)

            return json_data
        else:
            raise Exception(f'[ERROR] API returned status: {response.status_code}')
