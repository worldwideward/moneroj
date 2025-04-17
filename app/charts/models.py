'''Models for the Charts database'''

from __future__ import unicode_literals
from django.db import models


class Coin(models.Model):
    '''Model for cryptocurrency coin'''

    name = models.CharField(max_length=4, default="0")
    date = models.DateField(default="0")
    priceusd = models.FloatField(default="0")
    pricebtc = models.FloatField(default="0")
    inflation = models.FloatField(default="0")
    transactions = models.FloatField(default="0")
    hashrate = models.FloatField(default="0")
    stocktoflow = models.FloatField(default="0")
    supply = models.FloatField(default="0")
    fee = models.FloatField(default="0")
    revenue = models.FloatField(default="0")
    blocksize = models.FloatField(default="0")
    difficulty = models.FloatField(default="0")


class Social(models.Model):
    '''Model for Social Platforms (Reddit, ...)'''

    name = models.CharField(max_length=4)
    date = models.DateField()
    subscriber_count = models.IntegerField()
    comments_per_hour = models.FloatField()
    posts_per_hour = models.FloatField()


class Dominance(models.Model):
    '''Model for cryptocurrency coin dominance'''

    name = models.CharField(max_length=4)
    date = models.DateField()
    dominance = models.FloatField()

    def __str__(self):
        return self.dominance


class Rank(models.Model):
    '''Model for cryptocurrency popularity ranking'''

    name = models.CharField(max_length=4)
    date = models.DateField()
    rank = models.IntegerField()

    def __str__(self):
        return self.rank


class Sfmodel(models.Model):
    '''Model for stocktoflow chart'''

    date = models.DateField()
    priceusd = models.FloatField()
    pricebtc = models.FloatField()
    color = models.FloatField()
    stocktoflow = models.FloatField()
    greyline = models.FloatField()


class DailyData(models.Model):
    '''Model for daily data objects'''

    # Date field
    date = models.DateField()

    # Basic information
    btc_priceusd = models.FloatField()
    xmr_priceusd = models.FloatField()
    xmr_pricebtc = models.FloatField()

    # Marketcap charts
    btc_marketcap = models.FloatField()
    xmr_marketcap = models.FloatField()
    dash_marketcap = models.FloatField()
    grin_marketcap = models.FloatField()
    zcash_marketcap = models.FloatField()

    # Transactions charts
    xmr_transacpercentage = models.FloatField()
    btc_transactions = models.FloatField()
    xmr_transactions = models.FloatField()
    zcash_transactions = models.FloatField()
    dash_transactions = models.FloatField()
    grin_transactions = models.FloatField()
    btc_supply = models.IntegerField()
    xmr_supply = models.IntegerField()

    # Issuance charts
    btc_inflation = models.FloatField()
    xmr_inflation = models.FloatField()
    dash_inflation = models.FloatField()
    grin_inflation = models.FloatField()
    zcash_inflation = models.FloatField()
    xmr_metcalfebtc = models.FloatField()
    xmr_metcalfeusd = models.FloatField()
    btc_return = models.FloatField()
    xmr_return = models.FloatField()
    btc_emissionusd = models.FloatField()
    btc_emissionntv = models.FloatField()
    xmr_emissionusd = models.FloatField()
    xmr_emissionntv = models.FloatField()

    # Mining charts
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
    xmr_minerrevcap = models.FloatField()
    btc_minerrevcap = models.FloatField()
    btc_commitntv = models.FloatField()
    xmr_commitntv = models.FloatField()
    btc_commitusd = models.FloatField()
    xmr_commitusd = models.FloatField()
    btc_blocksize = models.FloatField()
    xmr_blocksize = models.FloatField()
    btc_difficulty = models.FloatField()
    xmr_difficulty = models.FloatField()

    # Reddit charts
    btc_subscriber_count = models.IntegerField()
    btc_comments_per_hour = models.FloatField()
    btc_posts_per_hour = models.FloatField()
    xmr_subscriber_count = models.IntegerField()
    xmr_comments_per_hour = models.FloatField()
    xmr_posts_per_hour = models.FloatField()
    crypto_subscriber_count = models.IntegerField()
    crypto_comments_per_hour = models.FloatField()
    crypto_posts_per_hour = models.FloatField()


class P2Pool(models.Model):
    '''Model for P2Pool mining data'''

    date = models.DateField()
    mini = models.BooleanField()
    hashrate = models.IntegerField()
    percentage = models.FloatField()
    miners = models.IntegerField()
    totalhashes = models.IntegerField()
    totalblocksfound = models.IntegerField()


class Withdrawal(models.Model):
    '''Model for withdrawal data'''

    date = models.DateTimeField(auto_now_add=True)
    state = models.BooleanField()


class Usage(models.Model):
    '''Model for Cryptocurrency usage'''

    date = models.DateTimeField()
    bitcoin_pct = models.FloatField(default=0)
    monero_pct = models.FloatField(default=0)
    ethereum_pct = models.FloatField(default=0)
    others_pct = models.FloatField(default=0)
    data_source = models.CharField(max_length=32, default="coincards")
