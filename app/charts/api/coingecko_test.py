from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from .coingecko import CoingeckoAPI

class TestCoingeckoAPI(TestCase):
    '''Testing Coingecko API class'''

    def test_coingecko_api(self):
        '''Test retrieving init model'''

        cg = CoingeckoAPI()

        got = cg.endpoint
        want = "https://api.coingecko.com/api/v3"

        self.assertEqual(got, want)

    def test_get_coin_id(self):

        cg = CoingeckoAPI()

        got = cg.get_coin_id('xmr')
        want = 'monero'

        self.assertEqual(got, want)
