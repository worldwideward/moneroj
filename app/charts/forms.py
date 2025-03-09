'''Forms module'''

from django import forms
from .models import Coin


class CoinForm(forms.ModelForm):
    '''Form to add cryptocurrency coins to the database'''

    class Meta:
        '''Form layout for adding cryptocurrency coins'''
        model = Coin
        fields = ['name', 'date', 'priceusd', 'pricebtc', 'inflation', 'transactions', 'hashrate', 'supply', 'fee', 'revenue', 'blocksize', 'difficulty']
