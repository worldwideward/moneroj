from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from .models import Coin

from .update_data import erase_coin_data
from .update_data import calculate_base_reward
from .update_data import calculate_block_reward
from .update_data import reset_sf_model

class TestUpdateData(TestCase):
    '''Testing update data functions'''

    def setUp(self):

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2025-01-01"
        data_point.priceusd = 300
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2021-06-28"
        data_point.priceusd = 200
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

        data_point = Coin()
        data_point.name = "xmr"
        data_point.date = "2017-12-23"
        data_point.priceusd = 50
        data_point.pricebtc = 0.005
        data_point.inflation = 0.85123
        data_point.transactions = 35550.0
        data_point.hashrate = 1000000.7555
        data_point.stocktoflow = 2500.05
        data_point.supply = 18000000
        data_point.fee = 9.6456
        data_point.revenue = 460.85
        data_point.blocksize = 12456.5654
        data_point.difficulty = 53235348544.0
        data_point.save()

    def test_erase_coin_data(self):
        '''Test erasing coin data'''

        result = erase_coin_data("xmr")

        got = result
        want = True

        self.assertEqual(got, want)

    def test_calculate_base_reward(self):
        '''Test calculation of base reward'''

        # Calculate a supply value that should trigger tail emission
        # Using (2^64 - 1) - (0.6 * 10^12 << 19) to ensure it's very close to max
        money_supply = 2**64 - 1
        minimum_subsidy = int(0.6 * (10**12))
        emission_speed_factor = 19
        
        # Supply value that should trigger tail emission
        high_supply = money_supply - (minimum_subsidy << emission_speed_factor) + 1
        result1 = calculate_base_reward(high_supply)
        
        # Test with a supply that should give a normal reward
        low_supply = 10000000000000  # Lower supply value
        result2 = calculate_base_reward(low_supply)
        
        # The first result should be the minimum subsidy (0.6 XMR = 0.6 * 10^12)
        self.assertEqual(result1, minimum_subsidy)
        
        # The second result should be higher than the minimum subsidy
        self.assertTrue(result2 > minimum_subsidy)

    def test_calculate_block_reward(self):
        '''Test calculation of block reward'''

        base_reward = 35184372088797

        # Test with block weight below median (no penalty)
        result1 = calculate_block_reward(base_reward, block_weight=200000, median_block_weight=300000)
        
        # Test with block weight above median (should apply penalty)
        result2 = calculate_block_reward(base_reward, block_weight=600000, median_block_weight=300000)
        
        # First result should equal base reward (no penalty)
        self.assertEqual(result1, base_reward)
        
        # Second result should be less than base reward (with penalty)
        self.assertTrue(result2 < base_reward)
        
        # Calculate the expected penalty manually
        penalty_ratio = (600000 / 300000) - 1  # = 1
        expected_reward = int(base_reward * (1 - penalty_ratio**2))  # = 0
        
        # Verify the penalty calculation
        self.assertEqual(result2, expected_reward)

    def test_reset_sf_model(self):
        '''Test resetting SF Model Charts'''

        result = reset_sf_model()

        got = result
        want = False

        self.assertEqual(got, want)
