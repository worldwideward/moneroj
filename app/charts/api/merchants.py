import json
import requests

from bs4 import BeautifulSoup
from django.conf import settings

TIMEOUT = 180

class BTCmapAPI():

    def __init__(self):

        self.endpoint = "https://api.btcmap.org/v2"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Moneroj.net"
        }

        return None

    def get_all_data(self):

        url = f'{self.endpoint}/elements'

        print(f'[DEBUG] Querying {url}')

        session = requests.Session()

        try:
            response = session.get(url, headers=self.headers, timeout=TIMEOUT)
            response_text = response.text

            data = json.loads(response_text)

            print(f'[INFO] found {len(data)} merchant entries')

        except Exception as error:

            print(f'[ERROR] An unknown error occured: {error}')
            return None

        return data

    def get_aggregated_merchants_data(self):

        merchants_data = self.get_all_data()

        accept_multi_currencies = []
        accept_bitcoin = []

        accept_btc_count = 0    # bitcoin
        accept_eth_count = 0    # ethereum
        accept_bch_count = 0    # bitcoin cash
        accept_ltc_count = 0    # litecoin
        accept_xrp_count = 0    # ripple
        accept_xmr_count = 0    # monero
        accept_dash_count = 0   # dash

        for data_point in merchants_data:

            data_point_type = data_point['osm_json']['type']

            created_at = data_point['created_at']
            deleted_at = data_point['deleted_at']

            if data_point_type == "node":

                try:
                    if data_point['osm_json']['tags']["payment:cryptocurrencies"] == "yes":
                        accept_multi_currencies.append(data_point)
                except KeyError:
                    pass
                except TypeError:
                    pass

                try:
                    if data_point['osm_json']['tags']["payment:bitcoin"] == "yes":
                        accept_bitcoin.append(data_point)
                except KeyError:
                    pass
                except TypeError:
                    pass

        for data_point in accept_multi_currencies:

            try:
                if data_point['osm_json']['tags']['currency:XBT'] == "yes":
                    accept_btc_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:ETH'] == "yes":
                    accept_eth_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:BCH'] == "yes":
                    accept_bch_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:LTC'] == "yes":
                    accept_ltc_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:XRP'] == "yes":
                    accept_xrp_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:XMR'] == "yes":
                    accept_xmr_count += 1
            except KeyError:
                pass
            except TypeError:
                pass

            try:
                if data_point['osm_json']['tags']['currency:DASH'] == "yes":
                    accept_dash_count += 1
            except KeyError:
                pass
            except TypeError:
                pass


        accept_btc_count += len(accept_bitcoin)

        print(f'[INFO] {len(accept_multi_currencies)} accept multiple currencies')
        print(f'[INFO] {len(accept_bitcoin)} accept bitcoin')

        aggregated_data = {
                'accept_btc': accept_btc_count,
                'accept_eth': accept_eth_count,
                'accept_bch': accept_bch_count,
                'accept_ltc': accept_ltc_count,
                'accept_xrp': accept_xrp_count,
                'accept_xmr': accept_xmr_count,
                'accept_dash': accept_dash_count
                }

        return aggregated_data

class MonericaSession():

    def __init__(self):

        self.endpoint = "https://app.monerica.com"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Moneroj.net"
        }

        return None

    def parse_single_page(self, html):

        businesses = []
        html_lists = html.findAll(class_="blank_list_item")

        for category in html_lists:

            links = category.findAll("a")
            for item in links:
                link = item.get("href")
                businesses.append(link)

        return businesses

    def get_all_businesses(self):

        url = f'{self.endpoint}/businesses'

        print(f'[DEBUG] Querying {url}')

        session = requests.Session()

        try:
            response = session.get(url, headers=self.headers, timeout=TIMEOUT)

        except Exception as error:
            print(f'[ERROR] An unknown error occured: {error}')
            return None

        businesses = 0

        if response.status_code == 200:

            soup = BeautifulSoup(response.text, 'html.parser')

            ## parse the first page

            parse_results = self.parse_single_page(soup)
            businesses += len(parse_results)
            print(f'[DEBUG] Found {len(parse_results)} businesses on page {url}')

            ## parse the pagination

            pagination = soup.find(class_="pagination")
            pages = pagination.findAll("a")

            links = []

            for link in pages:
                links.append(link.get("href"))

        for link in links[1:]:

            print(f'[DEBUG] Following {link}')

            try:
                response = session.get(link, headers=self.headers, timeout=TIMEOUT)

            except Exception as error:
                print(f'[ERROR] Page {link} not parsed. An unknown error occured: {error}')
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            parse_results = self.parse_single_page(soup)
            businesses += len(parse_results)
            print(f'[DEBUG] Found {len(parse_results)} businesses on page {link}')

        return businesses

    def get_aggregated_merchants_data(self):

        businesses = self.get_all_businesses()

        aggregated_data = {
                'accept_xmr': businesses
                }

        return aggregated_data
