from django.test import TestCase

from unittest.mock import Mock

from .authenticated import get_history
from .authenticated import load_rank
from .authenticated import load_dominance
from .authenticated import load_p2pool
from .authenticated import reset
from .authenticated import populate_database
from .authenticated import update_database_admin

class TestAuthenticatedViews(TestCase):
    '''Testing Authenticated views'''

    def test_get_history(self):
        '''Test retrieving coin history data'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = get_history(request, "xmr", start_time="2025-01-01", end_time="2025-01-01")

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_load_rank(self):
        '''Test loading rank data to database'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = load_rank(request, "xmr")

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_load_dominance(self):
        '''Test loading dominance data to database'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = load_dominance(request, "xmr")

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_load_p2pool(self):
        '''Test loading P2Pool data to database'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = load_p2pool(request)

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_reset(self):
        '''Test removing coin data from database'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = reset(request, "xmr")

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_populate_database(self):
        '''Test populating database with data'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = populate_database(request)

        got = view.status_code
        want = 200

        self.assertEqual(got, want)

    def test_update_database_admin(self):
        '''Test populating database with data'''

        request = Mock()
        request.user.is_superuser.return_value = True

        view = update_database_admin(request, "2024-01-01", "2024-01-01")

        got = view.status_code
        want = 200

        self.assertEqual(got, want)
