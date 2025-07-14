from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

import json
import datetime
import asyncio

from charts.api.bitcoin import analyze_transaction_data
from charts.api.bitcoin import download_block_data
from charts.api.bitcoin import whirlpool_analysis

TX_DATA = '{"txid":"d4fae09b14d12f937409e683eea22ae02935d90c4aee5fafb5a49f12db5e2783","hash":"dd44f2df2bb61ad7a5d738a61b78908be57d47f44acad9fcda5256c4168e7a43","version":2,"size":378,"vsize":351,"weight":1404,"locktime":0,"vin":[{"coinbase":"0385d00d04a38873682f466f756e6472792055534120506f6f6c202364726f70676f6c642ffabe6d6dedd795db5040d2790083bb4cc320a97b0b7c0b086a2817425d7707d2de60028201000000000000005f3115a77fcd010000000000","txinwitness":["0000000000000000000000000000000000000000000000000000000000000000"],"sequence":4294967295}],"vout":[{"value":3.1432233,"n":0,"scriptPubKey":{"asm":"0 7086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c2","desc":"addr(bc1qwzrryqr3ja8w7hnja2spmkgfdcgvqwp5swz4af4ngsjecfz0w0pqud7k38)#y9upg3rz","hex":"00207086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c2","address":"bc1qwzrryqr3ja8w7hnja2spmkgfdcgvqwp5swz4af4ngsjecfz0w0pqud7k38","type":"witness_v0_scripthash"}},{"value":0,"n":1,"scriptPubKey":{"asm":"OP_RETURN aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56","desc":"raw(6a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56)#w4uz80d2","hex":"6a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a56","type":"nulldata"}},{"value":0,"n":2,"scriptPubKey":{"asm":"OP_RETURN 434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765","desc":"raw(6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765)#eyjrnxlm","hex":"6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e765","type":"nulldata"}},{"value":0,"n":3,"scriptPubKey":{"asm":"OP_RETURN 52534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986","desc":"raw(6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986)#scfrgxm7","hex":"6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b1500769986","type":"nulldata"}}],"hex":"020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff5d0385d00d04a38873682f466f756e6472792055534120506f6f6c202364726f70676f6c642ffabe6d6dedd795db5040d2790083bb4cc320a97b0b7c0b086a2817425d7707d2de60028201000000000000005f3115a77fcd010000000000ffffffff049a2dbc12000000002200207086320071974eef5e72eaa01dd9096e10c0383483855ea6b344259c244f73c20000000000000000266a24aa21a9edf468d820cff9a30dbc0318aaf85c1b0f67db1ec01d1dc741ce3395c0e00f6a5600000000000000002f6a2d434f5245012e50087fb834747606ed01ad67ad0f32129ab431e6d18fda214e5b9f350ffc7b6cf3058b9026e76500000000000000002b6a2952534b424c4f434b3a79dbca11a0a7915d44e7813bb7c426524cc7006f248da5b173129b15007699860120000000000000000000000000000000000000000000000000000000000000000000000000","blockhash":"00000000000000000001c45d9686bc4a33871e0cdaec02a2cc9ba26d908f7637","confirmations":3,"time":1752402083,"blocktime":1752402083,"fee":{"amount":-3.1432233,"unit":"BTC"}}'

class TestWhirlpoolAnalysis(TestCase):
    '''Testing Bitcoin Whirlpool Analysis'''

    def test_analyze_transaction_data(self):

        tx_data = json.loads(TX_DATA)

        got = analyze_transaction_data(tx_data)
        want = None
        self.assertEqual(got, want)

    def test_download_transaction_data(self):

        #self.assertEqual(got, want)
        pass

#    @patch('charts.analyze_bitcoin_transactions.aiohttp')
#    def test_download_block_data(self, mock_response):
#
#        response = Mock()
#        response.text = "BLOCK_DATA"
#        mock_response.return_value = response
#
#        got = asyncio.run(download_block_data(904929, 904930))
#        want = "BLOCK_DATA"
#        self.assertEqual(got, want)

    def test_whirlpool_analysis(self):

        #self.assertEqual(got, want)
        pass
