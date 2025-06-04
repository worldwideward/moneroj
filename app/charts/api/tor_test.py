from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

import datetime

from charts.api.tor import DreadSession

class TestTorApi(TestCase):
    '''Testing Tor class'''

    @patch('charts.api.tor.requests')
    def test_get_dread_subscriber_count_success(self, mock_get):
        '''Test retrieving dread subscriber count'''

        mock_get.Session().get().text = '<p class="subscriber_count">100</p>'
        mock_get.Session().get().status_code = 200

        session = DreadSession()

        subscriber_count = session.get_dread_subscriber_count("btc")

        got = subscriber_count
        want = 100

        self.assertEqual(got, want)

    @patch('charts.api.tor.requests')
    def test_get_dread_subscriber_count_failed_request(self, mock_get):
        '''Test retrieving dread subscriber count in case of non 200 code'''

        mock_get.Session().get().text = '<p class="subscriber_count">100</p>'
        mock_get.Session().get().status_code = 400

        session = DreadSession()

        subscriber_count = session.get_dread_subscriber_count("btc")

        got = subscriber_count
        want = None

        self.assertEqual(got, want)

    @patch('charts.api.tor.requests')
    def test_get_dread_subscriber_count_symbol_not_found(self, mock_get):
        '''Test succesful request but dread subscriber count not found due to unkown ticker symbol'''

        mock_get.Session().get().text = '<p>This page does not exist</p>'
        mock_get.Session().get().status_code = 200

        session = DreadSession()

        subscriber_count = session.get_dread_subscriber_count("xxx")

        got = subscriber_count
        want = None

        self.assertEqual(got, want)

    @patch('charts.api.tor.requests')
    def test_get_dread_subscriber_count_not_found(self, mock_get):
        '''Test succesful request but dread subscriber count not found'''

        mock_get.Session().get().text = '<p class="subscriber_count"></p>'
        mock_get.Session().get().status_code = 200

        session = DreadSession()

        subscriber_count = session.get_dread_subscriber_count("btc")

        got = subscriber_count
        want = None

        self.assertEqual(got, want)
