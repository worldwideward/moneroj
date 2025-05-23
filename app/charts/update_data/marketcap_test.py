from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from charts.models import Coin
from charts.models import Rank
from charts.models import Dominance

from charts.update_data.marketcap import get_coin_rank_data
from charts.update_data.marketcap import get_coin_dominance_data
from charts.update_data.marketcap import add_rank_entry
from charts.update_data.marketcap import add_dominance_entry
from charts.update_data.marketcap import update_rank
from charts.update_data.marketcap import update_dominance

class TestUpdateData(TestCase):
    '''Testing update data functions'''

    def setUp(self):

        data_point = Rank()
        data_point.name = "xmr"
        data_point.date = "2025-05-20"
        data_point.rank = "25"
        data_point.save()

    @patch('charts.api.coingecko.CoingeckoAPI.get_coin_realtime_data')
    def test_get_coin_rank_data(self, mock_coin_data):
        '''Test getting coin rank data from external API'''

        mock_coin_data.return_value = {"market_cap_rank": 25 }

        result = get_coin_rank_data('xmr')

        got = result
        want = 25

        self.assertEqual(got, want)

    @patch('charts.api.coingecko.CoingeckoAPI.get_global_realtime_data')
    @patch('charts.api.coingecko.CoingeckoAPI.get_coin_realtime_data')
    def test_get_coin_dominance_data(self, mock_coin_data, mock_global_data):
        '''Test getting coin rank data from external API'''

        mock_coin_data.return_value = { 'market_data': { 'market_cap': { 'usd': 200 } } }
        mock_global_data.return_value = { 'data': { 'total_market_cap': { 'usd': 1000 } } }

        result = get_coin_dominance_data('xmr')

        got = result
        want = 20.0

        self.assertEqual(got, want)

    def test_add_rank_entry(self):

        result = add_rank_entry('xmr', 25)

        got = result
        want = 0

        self.assertEqual(got, want)

    def test_add_dominance_entry(self):

        result = add_dominance_entry('xmr', 20.0)

        got = result
        want = 0

        self.assertEqual(got, want)

    @patch('charts.api.coingecko.CoingeckoAPI.get_coin_realtime_data')
    def test_update_rank(self, mock_coin_data):

        mock_coin_data.return_value = {"market_cap_rank": 25 }

        result = update_rank('xmr')

        got = result
        want = 0
        self.assertEqual(got, want)

    @patch('charts.api.coingecko.CoingeckoAPI.get_global_realtime_data')
    @patch('charts.api.coingecko.CoingeckoAPI.get_coin_realtime_data')
    def test_update_dominance(self, mock_coin_data, mock_global_data):

        mock_coin_data.return_value = { 'market_data': { 'market_cap': { 'usd': 200 } } }
        mock_global_data.return_value = { 'data': { 'total_market_cap': { 'usd': 1000 } } }

        result = update_dominance('xmr')

        got = result
        want = 0
        self.assertEqual(got, want)
