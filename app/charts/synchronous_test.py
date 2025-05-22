from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from datetime import date
from datetime import datetime
from datetime import timedelta

from .models import Coin

from .synchronous import get_history_function
from .synchronous import add_stock_to_flow_entry
from .synchronous import update_database
from .synchronous import update_daily_data_price_information
from .utils import get_yesterday
from .utils import get_socks_proxy

class TestSynchronous(TestCase):
    '''Testing sync functions'''

    def setUp(self):

        xmr_data_point = Coin()
        xmr_data_point.name = "xmr"
        xmr_data_point.date = "2025-05-21"
        xmr_data_point.priceusd = 300
        xmr_data_point.pricebtc = 0.005
        xmr_data_point.inflation = 0.85123
        xmr_data_point.transactions = 35550.0
        xmr_data_point.hashrate = 1000000.7555
        xmr_data_point.stocktoflow = 2500.05
        xmr_data_point.supply = 18000000
        xmr_data_point.fee = 9.6456
        xmr_data_point.revenue = 460.85
        xmr_data_point.blocksize = 12456.5654
        xmr_data_point.difficulty = 53235348544.0
        xmr_data_point.save()

        self.xmr_previous_data_point = xmr_data_point

        xmr_data_point = Coin()
        xmr_data_point.name = "xmr"
        xmr_data_point.date = "2025-05-21"
        xmr_data_point.priceusd = 300
        xmr_data_point.pricebtc = 0.005
        xmr_data_point.inflation = 0.85123
        xmr_data_point.transactions = 35550.0
        xmr_data_point.hashrate = 1000000.7555
        xmr_data_point.stocktoflow = 2500.05
        xmr_data_point.supply = 18000000
        xmr_data_point.fee = 9.6456
        xmr_data_point.revenue = 460.85
        xmr_data_point.blocksize = 12456.5654
        xmr_data_point.difficulty = 53235348544.0
        xmr_data_point.save()

        self.xmr_data_point = xmr_data_point

        date_zero = '2014-05-20'
        self.amount = datetime.strptime(xmr_data_point.date, '%Y-%m-%d') - datetime.strptime(date_zero, '%Y-%m-%d')

        btc_data_point = Coin()
        btc_data_point.name = "btc"
        btc_data_point.date = "2025-05-21"
        btc_data_point.priceusd = 300
        btc_data_point.pricebtc = 0.005
        btc_data_point.inflation = 0.85123
        btc_data_point.transactions = 35550.0
        btc_data_point.hashrate = 1000000.7555
        btc_data_point.stocktoflow = 2500.05
        btc_data_point.supply = 18000000
        btc_data_point.fee = 9.6456
        btc_data_point.revenue = 460.85
        btc_data_point.blocksize = 12456.5654
        btc_data_point.difficulty = 53235348544.0
        btc_data_point.save()

        self.btc_data_point = btc_data_point

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

    def test_add_stock_to_flow_entry(self):

        result = add_stock_to_flow_entry(self.xmr_data_point, self.amount)

        self.assertEqual(result, None)


    def test_update_daily_data_price_information(self):

        result = update_daily_data_price_information(self.xmr_data_point, self.btc_data_point)

        self.assertEqual(result, True)

    def test_update_database(self):

        result = update_database("2025-05-21", "2025-05-21")

        self.assertEqual(result, 1)
