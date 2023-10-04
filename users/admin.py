from django.contrib import admin

# Register your models here.
from charts.models import *

class CoinAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "priceusd")

admin.site.register(Coin, CoinAdmin)