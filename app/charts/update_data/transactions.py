'''Update Transactions data'''
from datetime import date
from charts.api.zec import ZecExplorer
from charts.models import Transaction

ZEC_EXPLORER = ZecExplorer()

def add_transactions_entry():

    today = date.today()

    try:
        shielded_transactions = ZEC_EXPLORER.get_real_time_shielded_transactions_count()
    except Exception as error:
        print(f'[ERROR] Something went wrong while getting shielded transactions: {error}')
        return False

    entry = Transaction()

    entry.date = today
    entry.zcash_shielded_transactions = shielded_transactions
    entry.bitcoin_whirpool_transactions = 0
    entry.save()

    return True
