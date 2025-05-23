from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

import datetime

from charts.api.coinmetrics import CoinmetricsAPI

class TestCoinmetricsAPI(TestCase):
    '''Testing Coin Metrics API class'''

    def test_coinmetrics_api(self):
        '''Test retrieving coin history data'''

        coinmetrics = CoinmetricsAPI()

        got = coinmetrics.endpoint
        want = "https://community-api.coinmetrics.io/v4"

        self.assertEqual(got, want)

    def test_get_asset_metrics_succesful(self):

        cma = CoinmetricsAPI()

        response = cma.get_asset_metrics("xmr", "2024-01-01", "2024-01-01")

        got = response[0]["asset"]

        want = "xmr"

        self.assertEqual(got, want)

    def test_get_asset_metrics_paged_succesful(self):

        cma = CoinmetricsAPI()

        response = cma.get_asset_metrics("xmr", "2023-01-01", "2024-01-01")

        got_status = response[200]["asset"]
        want_status = "xmr"

        got_count = len(response)
        want_count = 366

        self.assertEqual(got_status, want_status)
        self.assertEqual(got_count, want_count)
