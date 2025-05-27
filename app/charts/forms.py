'''Forms module'''

from django import forms

class CsvImportForm(forms.Form):
    '''Import CSV files'''

    csv_file = forms.FileField()
