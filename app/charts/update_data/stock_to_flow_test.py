from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from charts.models import Coin

from charts.update_data.stock_to_flow import calculate_sf_model

class TestStocktoFlow(TestCase):
    '''Testing update data functions'''

    def setUp(self):

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2025-01-01"
        data_point.priceusd = 300
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2021-06-28"
        data_point.priceusd = 200
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2017-12-23"
        data_point.priceusd = 50
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

    def test_calculate_sf_model(self):
        '''Test resetting SF Model Objects'''

        result = calculate_sf_model()

        got = result
        want = True

        self.assertEqual(got, want)
