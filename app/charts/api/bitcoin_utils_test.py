from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from datetime import datetime
from datetime import timezone

from charts.api.bitcoin_utils import get_blocks_mined_today
from charts.api.bitcoin_utils import get_latest_block_height
from charts.api.bitcoin_utils import get_block_timestamp
from charts.api.bitcoin_utils import verify_first_block
from charts.api.bitcoin_utils import first_block_of_the_day
from charts.api.bitcoin_utils import range_of_blocks_today

BLOCK_DATA = '{"hash":"00000000000000000001c45d9686bc4a33871e0cdaec02a2cc9ba26d908f7637","confirmations":2,"height":905349,"version":939524096,"versionHex":"38000000","merkleroot":"848171adf1cdd6a72633e643ec1f1336ebb72f715a3b16f96a52d8fcd9b4ed11","time":1752402083,"mediantime":1752397715,"nonce":2598429897,"bits":"17023aa6","difficulty":126271255279307,"chainwork":"0000000000000000000000000000000000000000d1dcc17bf117126cdc68d58e","nTx":1466,"previousblockhash":"00000000000000000001a37e950b89a1f0ed01685f4ca402f4fa4ce219f7410e","nextblockhash":"0000000000000000000209f4371c9c7f64dbfa8c6eee9f21e5f8c69b176d2681","strippedsize":726001,"size":1815577,"weight":3993580,"tx":["d4fae09b14d12f937409e683eea22ae02935d90c4aee5fafb5a49f12db5e2783"],"coinbaseTx":{"in_active_chain":true,"txid":"d4fae09b14d12f937409e683eea22ae02935d90c4aee5fafb5a49f12db5e2783","hash":"dd44f2df2bb61ad7a5d738a61b78908be57d47f44acad9fcda5256c4168e7a43","version":2,"size":378,"vsize":351,"weight":1404,"locktime":0,"vin":[{"coinbase":"0385d00d04a38873682f466f756e6472792055534120506f6f6c202364726f70676f6c642ffabe6d6dedd795db5040d2790083bb4cc320a97b0b7c0b086a2817425d7707d2de60028201000000000000005f3115a77fcd010000000000","txinwitness":["0000000000000000000000000000000000000000000000000000000000000000"],"sequence":4294967295}],"vout":[{"value":3.1432233,"n":0,"scriptPubKey":{"asm":"0 7086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c2","desc":"addr(bc1qwzrryqr3ja8w7hnja2spmkgfdcgvqwp5swz4af4ngsjecfz0w0pqud7k38)#y9upg3rz","hex":"00207086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c2","address":"bc1qwzrryqr3ja8w7hnja2spmkgfdcgvqwp5swz4af4ngsjecfz0w0pqud7k38","type":"witness_v0_scripthash"}},{"value":0,"n":1,"scriptPubKey":{"asm":"OP_RETURN aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56","desc":"raw(6a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56)#w4uz80d2","hex":"6a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56","type":"nulldata"}},{"value":0,"n":2,"scriptPubKey":{"asm":"OP_RETURN 434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765","desc":"raw(6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765)#eyjrnxlm","hex":"6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765","type":"nulldata"}},{"value":0,"n":3,"scriptPubKey":{"asm":"OP_RETURN 52534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986","desc":"raw(6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986)#scfrgxm7","hex":"6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986","type":"nulldata"}}],"hex":"020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0385d00d04a38873682f466f756e6472792055534120506f6f6c202364726f70676f6c642ffabe6d6dedd795db5040d2790083bb4cc320a97b0b7c0b086a2817425d7707d2de60028201000000000000005f3115a77fcd010000000000ffffffff049a2dbc12000000002200207086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c20000000000000000266a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a5600000000000000002f6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e76500000000000000002b6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b15007699860120000000000000000000000000000000000000000000000000000000000000000000000000","blockhash":"00000000000000000001c45d9686bc4a33871e0cdaec02a2cc9ba26d908f7637","confirmations":2,"time":1752402083,"blocktime":1752402083},"totalFees":"0.0182233","miner":{"name":"Foundry USA","link":"https://foundrydigital.com/","identifiedBy":"coinbase tag \'Foundry USA Pool\'"},"subsidy":"3.125"}'


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

    def test_verify_first_block(self):
        '''Check if a block is the first block of the day'''

        got = verify_first_block("13-07-2025 10:21", 905349)
        want = False
        self.assertEqual(got, want)

    def test_first_block_of_the_day(self):
        '''Find the first block of the day'''

        time_object = datetime.strptime("13-07-2025 10:21:00", "%d-%m-%Y %H:%M:%S")
        got = first_block_of_the_day(time_object, 905349)
        want = 905288
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
