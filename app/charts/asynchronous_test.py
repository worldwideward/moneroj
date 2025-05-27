'''Tests for asynchronous functions'''
from django.test import TestCase

import aiohttp

from .asynchronous import update_xmr_data
#from .asynchronous import update_coin_data
from .asynchronous import get_block_data
#from .asynchronous import get_coin_data
from .asynchronous import get_social_data


class TestAsynchronous(TestCase):
    '''Testing async functions'''

    async def test_get_block_data(self):
        '''Test get block data'''

        block = 1

        async with aiohttp.ClientSession() as session:

            data = await get_block_data(session, block)

        got = data["status"]
        want = "OK"

        self.assertEqual(got, want)

#    async def test_get_coin_data(self):
#        async with aiohttp.ClientSession() as session:
#        got await get_coin_data(

    def test_get_social_data(self):
        '''Test getting social data'''

        got = get_social_data('xmr')
        want = True

        self.assertEqual(got, want)

    async def test_update_xmr_data(self):
        '''Test getting XMR data'''

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
