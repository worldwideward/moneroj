import requests
import json

class LocalMoneroAPI():

    def __init__(self):

        self.endpoint = "https://localmonero.co/blocks/api"

        return None

    def get_block_data(self, block: int):

        url = f'{self.endpoint}/get_block_data/{block}'

        response = requests.get(url)

        if response.status_code == 200:

            json_data=json.loads(response.text)

            return json_data
        else:
            raise Exception(f'[ERROR] API returned status: {response.status_code}')
