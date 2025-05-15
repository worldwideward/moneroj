from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from .import_history import import_rank_history
from .import_history import import_dominance_history
from .import_history import import_p2pool_history

class TestImport(TestCase):
    '''Testing importer functions'''

    def test_import_rank_history(self):
        '''Test import rank history data'''

        result = import_rank_history("xmr")

        got = result
        want = 1020

        self.assertEqual(got, want)

    def test_import_dominance_history(self):
        '''Test import dominance history data'''

        result = import_dominance_history("xmr")

        got = result
        want = 3434

        self.assertEqual(got, want)

    def test_import_p2pool_history(self):
        '''Test import P2Pool history data'''

        result = import_p2pool_history()

        got = result
        want = 992

        self.assertEqual(got, want)
