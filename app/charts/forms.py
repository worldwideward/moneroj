'''Forms module'''

from django import forms

class CsvImportForm(forms.Form):

    csv_file = forms.FileField()
