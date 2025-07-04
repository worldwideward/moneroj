import os
import requests
import json

from bs4 import BeautifulSoup

def extract_paths_from_table(url):

    response = requests.get(url, timeout=60)

    if response.status_code == 200:

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.table
        rows = table.findAll(class_='font-medium')

        paths = []

        for row in rows:
            item = row.find('a')
            if item != None:
                paths.append(item.get('href'))

        return paths
    else:
        raise Exception(f'[ERROR] Path extraction returned status: {response.status_code}')

def extract_shielded_transactions(url):

    response = requests.get(url, timeout=60)


    if response.status_code == 200:

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        shielded_transactions = soup.findAll('dt')[5]
        inputs_outputs = shielded_transactions.next_element.next_element.next_element.string.strip()
        shielded_transactions_count = int(inputs_outputs.split('/')[0].strip())

        return shielded_transactions_count

    else:
        print(f'[DEBUG] Parsing failed for {url} : response {response.status_code}')
        return 0

class ZecExplorer():

    def __init__(self):

        self.endpoint = "https://mainnet.zcashexplorer.app"

        return None

    def get_real_time_shielded_transactions_count(self):

        url = f'{self.endpoint}/blocks'
        blocks = extract_paths_from_table(url)

        shielded_transactions = []

        for block in blocks:

            url = self.endpoint + block
            transactions = extract_paths_from_table(url)

            for transaction in transactions:

                url = self.endpoint + transaction
                shielded_transactions_count = extract_shielded_transactions(url)
                shielded_transactions.append(shielded_transactions_count)

        count = 0

        for tx in shielded_transactions:
            count += tx

        return count

    def get_historic_shielded_transactions_count(self, date):

        url = f'{self.endpoint}/blocks?{date}'

        shielded_transactions = []

        for block in blocks:

            url = self.endpoint + block
            transactions = extract_paths_from_table(url)

            for transaction in transactions:

                url = self.endpoint + transaction
                shielded_transactions_count = extract_shielded_transactions(url)
                shielded_transactions.append(shielded_transactions_count)

        count = 0

        for tx in shielded_transactions:
            count += tx

        return count
