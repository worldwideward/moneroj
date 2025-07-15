'''Update Transactions data'''
import shutil

from datetime import date
from charts.api.zec import ZecExplorer
from charts.api.bitcoin import whirlpool_analysis
from charts.models import Transaction

from django.conf import settings

FILE_CACHE_PATH = settings.BITCOIN_EXPLORER_CACHE_DIR
ZEC_EXPLORER = ZecExplorer()

def add_transactions_entry():

    today = date.today()

    try:
        shielded_transactions = ZEC_EXPLORER.get_real_time_shielded_transactions_count()
    except Exception as error:
        print(f'[ERROR] Something went wrong while getting shielded transactions: {error}')
        return False

    try:
        whirlpool_transactions = whirlpool_analysis()
    except Exception as error:
        print(f'[ERROR] Something went wrong while getting whirlpool transactions: {error}')
        return False

    entry = Transaction()

    entry.date = today
    entry.zcash_shielded_transactions = shielded_transactions
    entry.bitcoin_whirpool_transactions = whirlpool_transactions
    entry.save()

    # clear transaction cache when data was saved successfully
    shutil.rmtree(BITCOIN_EXPLORER_CACHE_DIR)

    return True
