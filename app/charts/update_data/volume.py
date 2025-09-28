from datetime import datetime
from charts.models import DailyData
from charts.api.haveno import HavenoMarketsAPI
from charts.api.bisq import BisqMarketsAPI

HAVENO_MARKETS_API = HavenoMarketsAPI()
BISQ_MARKETS_API = BisqMarketsAPI()

def add_volume_entry():

    haveno_vol = HAVENO_MARKETS_API.get_volume_data()
    bisq_vol = BISQ_MARKETS_API.get_volume_data()

    for vols in haveno_vol:
        date = datetime.utcfromtimestamp(vols['period_start'])
        try:
            entry = DailyData.objects.get(date=date)
            entry.haveno_volume = vols['volume']
            entry.haveno_num_trades = vols['num_trades']
            entry.save()
        except Exception as error:
            print(f'[WARN] Adding daily data {date} for Haveno failed. {error}')

    for vols in bisq_vol:
        date = datetime.utcfromtimestamp(vols['period_start'])
        try:
            entry = DailyData.objects.get(date=date)
            entry.bisq_volume = vols['volume']
            entry.bisq_num_trades = vols['num_trades']
            entry.save()
        except Exception as error:
            print(f'[WARN] Adding daily data {date} for Bisq failed. {error}')
