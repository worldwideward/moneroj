import os
import requests
import json
import praw

from django.conf import settings

REDDIT_CLIENT_ID = settings.REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_REDIRECT_URI = settings.REDDIT_REDIRECT_URI

TOR_HOST = settings.TOR_HOST
TOR_PORT = settings.TOR_PORT

class RedditAPI():

    def __init__(self):

        self.endpoint = "https://www.reddittorjg6rue252oqsxryoxengawnmo46qy4kyii5wtqnwfj4ooad.onion"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Moneroj.net"
        }

        self.proxy = {
                "http": f'socks5h://{TOR_HOST}:{TOR_PORT}',
                "https": f'socks5h://{TOR_HOST}:{TOR_PORT}'
        }

        return None

    def connect(self):

        client_id=REDDIT_CLIENT_ID
        client_secret=REDDIT_CLIENT_SECRET
        redirect_uri=REDDIT_REDIRECT_URI

        connect = praw.Reddit(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, user_agent=self.headers["User-Agent"])

        implicit_flow = connect.auth.url(scopes=["identity"], implicit=True)

        return implicit_flow

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


    def get_subreddit_metadata(self, symbol):

        coin_id = self.get_coin_id(symbol)

        url = f'{self.endpoint}/r/{coin_id}/about.json'

        response = requests.get(url, headers=self.headers, proxies=self.proxy)

        if response.status_code == 200:

            data = json.loads(response.text)
        else:
            print(f'Request not succesful, returned HTTP status: {response.status_code}')
            return None

        return data["data"]

    def get_subreddit_posts(self, symbol):

        coin_id = self.get_coin_id(symbol)

        print('[INFO] Not implemented')
        list_of_posts = []

        return list_of_posts

    def get_subreddit_comments(self, symbol):

        coin_id = self.get_coin_id(symbol)

        print('[INFO] Not implemented')

        list_of_comments = []

        return list_of_comments
