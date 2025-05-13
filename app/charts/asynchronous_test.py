from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch
import aiohttp
import datetime

from .asynchronous import update_xmr_data
from .asynchronous import update_coin_data
from .asynchronous import get_coin_rank_data
from .asynchronous import get_coin_dominance_data
from .asynchronous import get_block_data
from .asynchronous import get_coin_data
from .utils import get_yesterday
from .utils import get_socks_proxy

class TestAsynchronous(TestCase):
    '''Testing async functions'''

    async def test_get_block_data(self):

        block = 1

        async with aiohttp.ClientSession() as session:

            data = await get_block_data(session, block)

        got = data["status"]
        want = "OK"

        self.assertEqual(got, want)

    async def test_get_coin_rank_data_success(self):

        async with aiohttp.ClientSession() as session:

            data = await get_coin_rank_data(session, "xmr")

        got = type(data)
        want = int

        self.assertEqual(got, want)

    async def test_get_coin_dominance_success(self):

        async with aiohttp.ClientSession() as session:

            data = await get_coin_dominance_data(session, "xmr")

        got_type = type(data)
        want_type = float

        self.assertEqual(got_type, want_type)
        self.assertLess(data, 100)

    async def test_update_xmr_data(self):

        got = await update_xmr_data()
        want = True

        self.assertEqual(got, want)

#    async def test_get_coin_data(self):
#
#        url = "http://162.210.173.181/coinmetrics"
#
#        async with aiohttp.ClientSession() as session:
#            data = await get_coin_data(session, 'xmr', url)
#
#        got = data
#        want = True
#
#        self.assertEqual(got, want)

#    async def test_update_coin_data(self):
#
#        coin = 'btc'
#
#        date = datetime.datetime.today()
#
#        response = await update_coin_data(coin, date)
#
#        got = response
#
#        want = True
#
#        self.assertEqual(got, want)
