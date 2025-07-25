from datetime import timedelta
from charts.models import Dread
from charts.api.tor import DreadSession

from django.core.exceptions import ObjectDoesNotExist

def get_dread_subscribers_previous_day(date, subdread):

    try:
        entry = Dread.objects.get(date=date)

        if subdread == "btc":

            return entry.bitcoin_subscriber_count

        if subdread == "xmr":

            return entry.monero_subscriber_count

    except Exception as error:

        print(f'[ERROR] Something went wrong: {error}')

    return 0

def add_dread_entry(date):

    session = DreadSession()

    try:
        Dread.objects.get(date=date)
        print("[INFO] Entry already exists, skipping")
    except ObjectDoesNotExist:
        btc_subscribers = session.get_dread_subscriber_count("btc")

        if btc_subscribers is None:

            yesterday = date - timedelta(1)
            btc_subscribers = get_dread_subscribers_previous_day(yesterday, "btc")

        xmr_subscribers = session.get_dread_subscriber_count("xmr")

        if xmr_subscribers is None:

            yesterday = date - timedelta(1)
            xmr_subscribers = get_dread_subscribers_previous_day(yesterday, "xmr")

        entry = Dread()

        entry.date = date
        entry.bitcoin_subscriber_count = btc_subscribers
        entry.monero_subscriber_count = xmr_subscribers
        entry.save()
    except Exception as error:
        print(f'[INFO] An unknown error occurred: {error}')

    return True
