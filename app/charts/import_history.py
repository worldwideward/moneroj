'''Import functions'''

from django.conf import settings

from charts.models import Rank
from charts.models import Dominance
from charts.models import P2Pool
from charts.models import Dread
from charts.spreadsheets import PandasSpreadSheetManager

SHEETS = PandasSpreadSheetManager()
CSV_DATA_SHEET = settings.CSV_DATA_SHEET


def import_dominance_history(symbol):

    csv_data = SHEETS.get_values(CSV_DATA_SHEET, "dominance", start=(2, 0), end=(9999, 2))

    Dominance.objects.all().delete()

    for row in csv_data:

        model = Dominance()
        model.name = symbol
        model.date = row[0]
        model.dominance = row[1]
        model.save()

    return len(csv_data)

def import_rank_history(symbol):
    '''Import rank data from a spreadsheet'''

    csv_data = SHEETS.get_values(CSV_DATA_SHEET, "rank", start=(2, 0), end=(9999, 2))

    Rank.objects.all().delete()
    print('[DEBUG] Deleted all Rank database entries')

    for row in csv_data:

        model = Rank()
        model.name = symbol
        model.date = row[0]
        model.rank = row[1]

        if not model.rank and not rank.date:
            break
        else:
            model.save()

    return len(csv_data)

def import_p2pool_history():
    '''Import P2Pool historic data from a spreadsheet'''

    csv_data = SHEETS.get_values(CSV_DATA_SHEET, "p2pool", start=(2, 0), end=(9999, 6))

    P2Pool.objects.all().delete()

    for row in csv_data:

        model = P2Pool()
        model.date = row[0]
        model.miners = row[1]
        model.hashrate = row[2]
        model.percentage = row[3]
        model.totalhashes = row[4]
        model.totalblocksfound = row[5]
        model.mini = False
        model.save()

    csv_data = SHEETS.get_values(CSV_DATA_SHEET, "p2poolmini", start=(2,0), end=(994,6), returnas='matrix')

    for row in csv_data:

        model = P2Pool()
        model.date = row[0]
        model.miners = row[1]
        model.hashrate = row[2]
        model.percentage = row[3]
        model.totalhashes = row[4]
        model.totalblocksfound = row[5]
        model.mini = True
        model.save()

    return len(csv_data)

def import_dread_subscribers():
    '''Import Dread subscriber data from a spreadsheet'''

    csv_data = SHEETS.get_values(CSV_DATA_SHEET, "dread", start=(1, 0), end=(99, 4))

    Dread.objects.all().delete()

    for row in csv_data:

        model = Dread()
        model.date = row[0]
        model.bitcoin_subscriber_count = row[1]
        model.monero_subscriber_count = row[2]
        model.save()


    return len(csv_data)
