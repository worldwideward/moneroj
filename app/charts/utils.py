'''Utilities module'''

from datetime import datetime
from datetime import date
from datetime import timedelta

from django.conf import settings

def get_today():
    '''Get todays date'''

    today_raw = date.today()
    today_formatted = datetime.strftime(today_raw, '%Y-%m-%d')

    return today_formatted

def get_yesterday():
    '''Get yesterdays date'''

    yesterday_raw = date.today() - timedelta(1)
    yesterday_formatted = datetime.strftime(yesterday_raw,  '%Y-%m-%d')

    return yesterday_formatted

def get_socks_proxy():
    '''Configure SOCKS proxy'''

    host = settings.SOCKS_PROXY_HOST
    port = settings.SOCKS_PROXY_PORT

    proxies = {
            'http': f'socks5h://{host}:{port}',
            'https': f'socks5h://{host}:{port}'
            }

    return proxies
