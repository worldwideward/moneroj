from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

import datetime

from charts.api.localmonero import LocalMoneroAPI

class TestLocalMoneroAPI(TestCase):
    '''Testing Coin Metrics API class'''

    def test_localmonero_api(self):
        '''Test retrieving init model'''

        lm = LocalMoneroAPI()

        got = lm.endpoint
        want = "https://localmonero.co/blocks/api"

        self.assertEqual(got, want)

    def test_get_block_data_succesful(self):

        lm = LocalMoneroAPI()

        response = lm.get_block_data(1)

        got_status = response["status"]
        want_status = "OK"

        got_data = response["block_data"]["result"]["block_header"]["timestamp"]
        want_data = 1397818193

        self.assertEqual(got_status, want_status)
        self.assertEqual(got_data, want_data)
