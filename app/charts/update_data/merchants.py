from datetime import date
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from charts.api.merchants import BTCmapAPI
from charts.models import Adoption

MERCHANTS_API = BTCmapAPI()

NOW = date.today()

def add_merchants_entry():

    merchants_data = MERCHANTS_API.get_aggregated_merchants_data()

    print(merchants_data)

    try:
        Adoption.objects.get(date=NOW)
        print('[INFO] Already an entry for today')
    except ObjectDoesNotExist:

        entry = Adoption()
        entry.date = NOW
        entry.merchants_accepting_bitcoin = merchants_data['accept_btc']
        entry.merchants_accepting_ethereum = merchants_data['accept_eth']
        entry.merchants_accepting_bitcoincash = merchants_data['accept_bch']
        entry.merchants_accepting_litecoin = merchants_data['accept_ltc']
        entry.merchants_accepting_ripple = merchants_data['accept_xrp']
        entry.merchants_accepting_dash = merchants_data['accept_dash']
        entry.merchants_accepting_monero = merchants_data['accept_xmr']
        entry.data_source = "multi"
        entry.save()
