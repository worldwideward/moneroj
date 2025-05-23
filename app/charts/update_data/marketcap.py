from datetime import datetime
from datetime import date
from django.conf import settings
from charts.models import Rank
from charts.models import Dominance
from charts.api.coingecko import CoingeckoAPI

MARKET_DATA_API = CoingeckoAPI()

def get_coin_rank_data(symbol: str):
    '''Get the current rank of a cryptocurrency coin'''

    data = MARKET_DATA_API.get_coin_realtime_data(symbol)

    rank = data["market_cap_rank"]

    return rank

def get_coin_dominance_data(symbol: str):
    '''Get the current dominance of a cryptocurrency coin'''

    coin_market_cap_data = MARKET_DATA_API.get_coin_realtime_data(symbol)
    coin_market_cap = coin_market_cap_data["market_data"]["market_cap"]["usd"]

    global_data = MARKET_DATA_API.get_global_realtime_data()
    total_market_cap = global_data["data"]["total_market_cap"]["usd"]

    dominance = round(( coin_market_cap / total_market_cap ) * 100, 2)

    return dominance

def add_rank_entry(symbol, rank):
    '''Add new rank value to database'''

    today = datetime.strftime(date.today(), '%Y-%m-%d')

    try:
        entry = Rank.objects.get(date=today)
    except Exception as error:
        entry = False

    if entry == False:
        try:
            model = Rank()
            model.name = symbol
            model.date = today
            model.rank = rank
            model.save()

        except Exception as error:

            print(f'[ERROR] Something went wrong while updating the rank of {symbol}: {error}')
            return 1
    return 0

def add_dominance_entry(symbol, dominance):
    '''Add new dominance value to database'''

    today = datetime.strftime(date.today(), '%Y-%m-%d')
    try:
        entry = Dominance.objects.get(date=today)
    except Exception as error:
        entry = False

    if entry == False:
        try:
            model = Dominance()
            model.name = symbol
            model.date = today
            model.dominance = dominance
            model.save()

        except Exception as error:
            print(f'[ERROR] Something went wrong while updating the dominance of {symbol}: {error}')
            return 1
    return 0

def update_rank(symbol):

    rank = get_coin_rank_data(symbol)
    result = add_rank_entry(symbol, rank)

    return result

def update_dominance(symbol):

    dominance = get_coin_dominance_data(symbol)
    result = add_dominance_entry(symbol, dominance)

    return result
