import json
import requests

class HavenoMarketsAPI():

    def __init__(self):

        self.endpoint = "https://haveno.markets/api/v1"

    def get_volume_data(self):

        url = f'{self.endpoint}/volumes?interval=daily'

        response = requests.get(url, timeout=10)

        if response.status_code == 200:

            json_data=json.loads(response.text)

            return json_data

        raise Exception(f'[ERROR] API returned status: {response.status_code}')
