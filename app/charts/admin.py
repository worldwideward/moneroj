from django.contrib import admin

from .models import Coin
from .models import Social
from .models import DailyData

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ["name", "date"]
    list_filter = ["name", "date"]
    list_per_page = 10
    search_fields = ["name"]
    ordering = ["date"]


@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    pass


@admin.register(DailyData)
class DailyDataAdmin(admin.ModelAdmin):
    list_display = ["date","xmr_priceusd","btc_priceusd"]
    list_filter = ["date","xmr_priceusd","btc_priceusd"]
    list_per_page = 10
    ordering = ["date"]
