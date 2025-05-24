'''Spreadsheets module'''
import pandas
from django.conf import settings

SPREADSHEET_DIR = settings.MONEROJ_SPREADSHEET_DIR

class SpreadSheetManager():
    '''Generic spreadsheet class'''

    def __init__(self):
        '''Initialize Spreadsheet manager'''

        self.spreadsheet_dir = SPREADSHEET_DIR

    def get_values(self, spreadsheet_file: str, spreadsheet_sheet, start, end):
        '''Get data from spreadsheet'''

        sheet = f'{self.spreadsheet_dir}/{spreadsheet_file}'

        return sheet

    def insert_values(self, spreadsheet: str):
        '''Add data to spreadsheet'''

        pass

    def update_values(self, spreadsheet: str):
        '''Update data in spreadsheet'''

        pass

class PandasSpreadSheetManager(SpreadSheetManager):
    '''Pandas spreadsheet implementation'''

    def get_values(self, spreadsheet_file: str, spreadsheet_sheet, start, end):
        '''Get data from spreadsheet'''

        sheet = pandas.read_excel(f'{self.spreadsheet_dir}/{spreadsheet_file}', spreadsheet_sheet, engine="odf")

        row_start = start[0]
        row_end   = end[0]
        col_start = start[1]
        col_end   = end[1]

        data = sheet.iloc[row_start:row_end, col_start:col_end].to_numpy()

        return data
