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