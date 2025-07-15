from charts.models import Dread
from charts.api.tor import DreadSession

from django.core.exceptions import ObjectDoesNotExist

def add_dread_entry(date):

    session = DreadSession()

    try:
        Dread.objects.get(date=date)
        print("[INFO] Entry already exists, skipping")
    except ObjectDoesNotExist:
        btc_subscribers = session.get_dread_subscriber_count("btc")

        if btc_subscribers is None:
            btc_subscribers = 0

        xmr_subscribers = session.get_dread_subscriber_count("xmr")

        if xmr_subscribers is None:
            xmr_subscribers = 0

        entry = Dread()

        entry.date = date
        entry.bitcoin_subscriber_count = btc_subscribers
        entry.monero_subscriber_count = xmr_subscribers
        entry.save()
    except Exception as error:
        print(f'[INFO] An unknown error occurred: {error}')

    return True
