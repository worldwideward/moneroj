import os
import pandas
from django.conf import settings

SPREADSHEET_DIR = settings.MONEROJ_SPREADSHEET_DIR

class SpreadSheetManager():

    def __init__(self):

        self.SPREADSHEET_DIR = SPREADSHEET_DIR

        return None

    def get_values(self, spreadsheet_file: str, spreadsheet_sheet: str, start, end):

        sheet = f'{self.SPREADSHEET_DIR}/{spreadsheet_file}'

        return sheet

    def insert_values(self, spreadsheet: str):

        pass

    def update_values(self, spreadsheet: str):

        pass

class PandasSpreadSheetManager(SpreadSheetManager):

    def get_values(self, spreadsheet_file: str, spreadsheet_sheet, start, end, returnas='matrix'):

        sheet = pandas.read_excel(f'{self.SPREADSHEET_DIR}/{spreadsheet_file}', spreadsheet_sheet, engine="odf")

        row_start = start[0]
        row_end   = end[0]
        col_start = start[1]
        col_end   = end[1]

        data = sheet.iloc[row_start:row_end, col_start:col_end].to_numpy()

        return data


