'''Update data functions'''

import math
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist

from charts.models import Coin
from charts.models import Sfmodel
from charts.models import DailyData

def erase_coin_data(symbol):
    '''Erase all data for a certain coin'''

    try:
        Coin.objects.filter(name=symbol).all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase data for {symbol}: {error}')
        return False

    return True

def erase_sf_model_data():
    '''Erase all data for the sf model object'''

    try:
        Sfmodel.objects.all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase Sfmodel data: {error}')
        return False

    return True

def erase_daily_data_data():
    '''Erase all data for the daily data object'''

    try:
        DailyData.objects.all().delete()
    except Exception as error:
        print(f'[ERROR] Failed to erase Sfmodel data: {error}')
        return False

    return True

def calculate_base_reward(minted_coins: int):
    '''XMR Base block reward calculation'''

    # https://monero-book.cuprate.org/consensus_rules/blocks/reward.html

    money_supply = 2**64 - 1
    target_block_time_minutes = 2
    emission_speed_factor = 20 - (target_block_time_minutes - 1)

    base_reward = (money_supply - minted_coins) >> emission_speed_factor

    # Tail emission: When we reach a specific emission point, a minimum reward is enforced
    # The minimum subsidy is 0.3 XMR per minute = 0.6 XMR per block with 2-minute blocks
    # 0.6 XMR = 0.6 * 10^12 piconero (1 XMR = 10^12 piconero)
    minimum_subsidy = int(0.6 * (10**12))  # 0.6 XMR in piconero

    # For testing the specific supply that triggers tail emission:
    # If we're very close to max supply, use the minimum subsidy
    if minted_coins > (money_supply - (minimum_subsidy << emission_speed_factor)):
        base_reward = minimum_subsidy

    return base_reward

def calculate_block_reward(base_reward, block_weight=None, median_block_weight=None):
    '''XMR Block reward calculation with penalty for large blocks

    Args:
        base_reward: The base reward amount in piconero
        block_weight: Current block weight (optional)
        median_block_weight: Effective median block weight (optional)
    Returns:
        The final block reward after applying any penalty
    '''

    # Default values if not provided
    if block_weight is None:
        block_weight = 100  # Example block weight

    if median_block_weight is None:
        median_block_weight = 300000  # Default effective median weight
        # Reference: https://monero-book.cuprate.org/consensus_rules/blocks/weights.html#effective-median-weight

    # If the current block weight is not more than the median weight, then the block reward is the base reward
    if block_weight <= median_block_weight:
        return base_reward

    # Otherwise, apply penalty formula: baseReward * (1 - ((blockWeight/effectiveMedianWeight) - 1)^2)
    penalty_ratio = (block_weight / median_block_weight) - 1
    block_reward = base_reward * (1 - penalty_ratio ** 2)

    return int(block_reward)
