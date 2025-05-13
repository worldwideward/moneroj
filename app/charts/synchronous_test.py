from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

import datetime

from .synchronous import get_history_function
from .synchronous import update_database
from .utils import get_yesterday
from .utils import get_socks_proxy

class TestSynchronous(TestCase):
    '''Testing sync functions'''

    @patch('charts.api.coinmetrics.CoinmetricsAPI.get_asset_metrics')
    def test_get_history_function_success(self, mock_get_request):
        '''Test retrieving coin history data'''

        mock_get_request.return_value = [{
          "asset": "xmr",
          "time": "2024-01-01T00:00:00.000000000Z",
          "PriceBTC": "0.003844390632273722",
          "PriceUSD": "169.343383485578",
          "BlkSizeMeanByte": "63027.131326949384",
          "DiffLast": "261032251576",
          "FeeTotNtv": "4.61497044",
          "HashRate": "2108895852.786833",
          "IssContPctAnn": "0.8952483115",
          "RevNtv": "443.208162214248",
          "SplyCur": "17881800.037843543351",
          "TxCnt": "16348"
        }]

        data = get_history_function("xmr", "2024-01-01", "2024-01-01")

        got = data
        want = 1

        self.assertEqual(got, want)

    def test_update_database(self):

        result = update_database()
