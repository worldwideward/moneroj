from .models import *
from django import forms

class CoinForm(forms.ModelForm):
	class Meta:
		model = Coin
		fields = ['name', 'date', 'priceusd', 'pricebtc', 'inflation', 'transactions', 'hashrate', 'supply', 'fee', 'revenue', 'blocksize', 'difficulty']
