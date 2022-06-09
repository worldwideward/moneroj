from __future__ import unicode_literals
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Coin(models.Model):
	name = models.CharField(max_length=4)
	date = models.DateField()
	priceusd = models.FloatField()
	pricebtc = models.FloatField()
	inflation = models.FloatField()
	transactions = models.FloatField()
	hashrate = models.FloatField()
	stocktoflow = models.FloatField()
	supply = models.FloatField()
	fee = models.FloatField(default="0")
	revenue = models.FloatField(default="0")
	def __str__(self):
		return self.priceusd

class Social(models.Model):
	name = models.CharField(max_length=4)
	date = models.DateField()
	subscriberCount = models.IntegerField()
	commentsPerHour = models.FloatField()
	postsPerHour = models.FloatField()

	def __str__(self):
		return self.subscriberCount

class Dominance(models.Model):
	name = models.CharField(max_length=4)
	date = models.DateField()
	dominance = models.FloatField()

	def __str__(self):
		return self.dominance

class Rank(models.Model):
	name = models.CharField(max_length=4)
	date = models.DateField()
	rank = models.IntegerField()

	def __str__(self):
		return self.rank

class Sfmodel(models.Model):
	date = models.DateField()
	priceusd = models.FloatField()
	pricebtc = models.FloatField()
	color = models.FloatField()
	stocktoflow = models.FloatField()
	greyline = models.FloatField()

	def __str__(self):
		return self.date

class DailyData(models.Model):
	date = models.DateField()
	btc_usd = models.FloatField()
	btc_ntv = models.FloatField()
	xmr_usd = models.FloatField()
	xmr_ntv = models.FloatField()
	xmr_transacpercentage = models.FloatField()
	xmr_transactions = models.FloatField()
	xmr_priceusd = models.FloatField()
	xmr_pricebtc = models.FloatField()
	btc_inflation = models.FloatField()
	xmr_inflation = models.FloatField()
	dash_inflation = models.FloatField()
	grin_inflation = models.FloatField()
	zcash_inflation = models.FloatField()
	btc_supply = models.IntegerField()
	xmr_supply = models.IntegerField()
	btc_return = models.FloatField()
	xmr_return = models.FloatField()
	btc_minerrevntv = models.FloatField()
	xmr_minerrevntv = models.FloatField()
	btc_minerrevusd = models.FloatField()
	xmr_minerrevusd = models.FloatField()
	btc_minerfeesntv = models.FloatField()
	xmr_minerfeesntv = models.FloatField()
	btc_minerfeesusd = models.FloatField()
	xmr_minerfeesusd = models.FloatField()
	btc_transcostntv = models.FloatField()
	xmr_transcostntv = models.FloatField()
	btc_transcostusd = models.FloatField()
	xmr_transcostusd = models.FloatField()
	btc_commitntv = models.FloatField()
	xmr_commitntv = models.FloatField()
	btc_commitusd = models.FloatField()
	xmr_commitusd = models.FloatField()
	xmr_metcalfebtc = models.FloatField()
	xmr_metcalfeusd = models.FloatField()
	xmr_minerrevcap = models.FloatField()
	btc_minerrevcap = models.FloatField()
	btc_marketcap = models.FloatField()
	btc_priceusd = models.FloatField()
	xmr_marketcap = models.FloatField()
	dash_marketcap = models.FloatField()
	grin_marketcap = models.FloatField()
	zcash_marketcap = models.FloatField()
	btc_subscriberCount = models.IntegerField()
	btc_commentsPerHour = models.FloatField()
	btc_postsPerHour = models.FloatField()
	xmr_subscriberCount = models.IntegerField()
	xmr_commentsPerHour = models.FloatField()
	xmr_postsPerHour = models.FloatField()
	crypto_subscriberCount = models.IntegerField()
	crypto_commentsPerHour = models.FloatField()
	crypto_postsPerHour = models.FloatField()

	def __str__(self):
		return self.date