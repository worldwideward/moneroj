import datetime
import os

from django.conf import settings

def get_today():

    today_raw = datetime.date.today()
    today_formatted = datetime.datetime.strftime(today_raw, '%Y-%m-%d')

    return today_formatted

def get_yesterday():

    yesterday_raw = datetime.date.today() - datetime.timedelta(1)
    yesterday_formatted = datetime.datetime.strftime(yesterday_raw,  '%Y-%m-%d')

    return yesterday_formatted

def get_socks_proxy():

    host = settings.SOCKS_PROXY_HOST
    port = settings.SOCKS_PROXY_PORT

    proxies = {
            'http': f'socks5h://{host}:{port}',
            'https': f'socks5h://{host}:{port}'
            }

    return proxies
