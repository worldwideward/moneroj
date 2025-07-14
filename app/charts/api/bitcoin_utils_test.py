from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from datetime import datetime
from datetime import timezone

from charts.api.bitcoin_utils import get_blocks_mined_today
from charts.api.bitcoin_utils import get_latest_block_height
from charts.api.bitcoin_utils import get_block_timestamp
from charts.api.bitcoin_utils import first_block_of_the_day
from charts.api.bitcoin_utils import range_of_blocks_today

BLOCK_DATA = '{"hash":"00000000000000000001c45d9686bc4a33871e0cdaec02a2cc9ba26d908f7637","confirmations":166,"height":905349,"version":939524096,"versionHex":"38000000","merkleroot":"848171adf1cdd6a72633e643ec1f1336ebb72f715a3b16f96a52d8fcd9b4ed11","time":1752402083,"mediantime":1752397715,"nonce":2598429897,"bits":"17023aa6","difficulty":126271255279307,"chainwork":"0000000000000000000000000000000000000000d1dcc17bf117126cdc68d58e","nTx":1466,"previousblockhash":"00000000000000000001a37e950b89a1f0ed01685f4ca402f4fa4ce219f7410e","nextblockhash":"0000000000000000000209f4371c9c7f64dbfa8c6eee9f21e5f8c69b176d2681"}'


class TestCalculateBitcoinBlocks(TestCase):
    '''Testing Bitcoin Block Range calculation'''

    def test_get_blocks_mined_today(self):
        '''Estimate blocks mined today'''

        time_object = datetime.strptime("2025-01-01 02:00:00", "%Y-%m-%d %H:%M:%S")

        got = get_blocks_mined_today(time_object)
        want = 12

        self.assertEqual(got, want)

    @patch('charts.api.bitcoin_utils.get')
    def test_get_latest_block_height(self, mock_response):
        '''Get most recent block'''

        response = Mock()
        response.text = '{"height":905349,"hash":"00000000000000000001c45d9686bc4a33871e0cdaec02a2cc9ba26d908f7637"}'
        mock_response.return_value = response

        got = get_latest_block_height()
        want = 905349

        self.assertEqual(got, want)

    @patch('charts.api.bitcoin_utils.get')
    def test_get_block_timestamp(self, mock_response):
        '''Get the timestamp for a block'''

        response = Mock()
        response.text = BLOCK_DATA
        mock_response.return_value = response

        got = get_block_timestamp(905349)
        timestamp = datetime.fromtimestamp(1752402083, timezone.utc).strftime('%d-%m-%Y %H:%M')
        want = timestamp
        self.assertEqual(got, want)

    def test_first_block_of_the_day_multiple_blocks_mined(self):
        '''Find the first block of the day'''

        time_object = datetime.strptime("13-07-2025 10:21:00", "%d-%m-%Y %H:%M:%S")
        got = first_block_of_the_day(time_object, 905349)
        want = 905296
        self.assertEqual(got, want)

    def test_first_block_of_the_day_zero_blocks_mined(self):
        '''Find the first block of the day'''

        time_object = datetime.strptime("13-07-2025 00:00:00", "%d-%m-%Y %H:%M:%S")
        got = first_block_of_the_day(time_object, 905349)
        want = 905296
        self.assertEqual(got, want)

    @patch('charts.api.bitcoin_utils.get_latest_block_height')
    @patch('charts.api.bitcoin_utils.first_block_of_the_day')
    def test_range_of_blocks_today(self, mock_block_height, mock_first_block):

        mock_block_height.return_value = 905349
        mock_first_block.return_value = 905288
        #mock_first_block.side_effect = [905288,905349]

        got = range_of_blocks_today()
        want = {
                "block_count": 0,
                "start_block": 905349,
                "end_block": 905349
                }
        self.assertEqual(got, want)
