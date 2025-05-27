import io
import csv
import datetime

from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect

from .models import Coin
from .models import Sfmodel
from .models import Social
from .models import Dread
from .models import DailyData
from .models import Usage
from .models import Dominance
from .models import Rank
from .models import P2Pool
from .models import Adoption

from .forms import CsvImportForm

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ["name", "date"]
    list_filter = ["name", "date"]
    list_per_page = 10
    search_fields = ["name"]
    ordering = ["date"]

@admin.register(Sfmodel)
class SfmodelAdmin(admin.ModelAdmin):
    list_display = ["date", "priceusd", "pricebtc", "color", "greyline"]
    list_filter = ["date", "stocktoflow", "color"]
    list_per_page = 10
    search_fields = ["stocktoflow", "color", "greyline"]
    ordering = ["date"]

@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):

    list_display = ["data_source", "date", "bitcoin_pct", "monero_pct", "ethereum_pct", "others_pct"]
    list_filter = ["data_source", "date"]
    list_per_page = 10
    ordering = ["date"]

    change_list_template = "charts/usage_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('import-csv/', self.import_csv)
                ]
        return my_urls+ urls

    def import_csv(self, request):
        if request.method == "POST":

            upload_csv_file = request.FILES["csv_file"]

            csv_file_bytes = upload_csv_file.read()
            csv_file_string = csv_file_bytes.decode('utf_7')
            csv_file = io.StringIO(csv_file_string)

            reader = csv.reader(csv_file, delimiter=',')

            for row in reader:

                if row[0] == 'Coincards':
                    pass
                elif row[0] == 'Date':
                    pass
                else:
                    string_to_date = datetime.datetime.strptime(row[0], "%Y-%m").date()
                    insert = Usage()
                    insert.data_source = "coincards"
                    insert.date = string_to_date
                    insert.bitcoin_pct = row[1]
                    insert.monero_pct = row[2]
                    insert.ethereum_pct = row[3]
                    insert.others_pct = row[4]
                    insert.save()

            self.message_user(request, "CSV imported successfully")

            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

@admin.register(Adoption)
class AdoptionAdmin(admin.ModelAdmin):

    list_display = ["data_source", "date", "merchants_accepting_bitcoin", "merchants_accepting_monero", "merchants_accepting_ethereum"]
    list_filter = ["data_source", "date"]
    list_per_page = 10
    ordering = ["date"]

    change_list_template = "charts/adoption_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('import-csv/', self.import_csv)
                ]
        return my_urls+ urls

    def import_csv(self, request):
        if request.method == "POST":

            upload_csv_file = request.FILES["csv_file"]

            csv_file_bytes = upload_csv_file.read()
            csv_file_string = csv_file_bytes.decode('utf_7')
            csv_file = io.StringIO(csv_file_string)

            reader = csv.reader(csv_file, delimiter=',')

            for row in reader:

                if row[0] == 'Acceptedhere':
                    pass
                elif row[0] == 'Date':
                    pass
                else:
                    string_to_date = datetime.datetime.strptime(row[0], "%Y-%m").date()
                    insert = Adoption()
                    insert.data_source = "acceptedhere"
                    insert.date = string_to_date
                    insert.merchants_accepting_bitcoin = row[1]
                    insert.merchants_accepting_monero = row[2]
                    insert.merchants_accepting_ethereum = row[3]
                    insert.merchants_accepting_bitcoincash = row[4]
                    insert.merchants_accepting_litecoin = row[5]
                    insert.merchants_accepting_ripple = row[6]
                    insert.merchants_accepting_dash = row[7]
                    insert.save()

            self.message_user(request, "CSV imported successfully")

            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    pass

@admin.register(Dread)
class DreadAdmin(admin.ModelAdmin):
    list_display = ["date", "monero_subscriber_count", "bitcoin_subscriber_count"]
    list_filter = ["date"]
    list_per_page = 10
    ordering = ["date"]

@admin.register(Dominance)
class DominanceAdmin(admin.ModelAdmin):
    list_display = ["name", "date"]
    list_filter = ["name", "date"]
    list_per_page = 10
    search_fields = ["name"]
    ordering = ["date"]

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ["name", "rank", "date"]
    list_filter = ["name", "date"]
    list_per_page = 10
    search_fields = ["name"]
    ordering = ["date"]

@admin.register(P2Pool)
class P2PoolAdmin(admin.ModelAdmin):
    list_display = ["mini", "date", "hashrate", "percentage", "miners", "totalhashes", "totalblocksfound"]
    list_filter = ["mini", "date"]
    list_per_page = 10
    search_fields = ["mini"]
    ordering = ["date"]

@admin.register(DailyData)
class DailyDataAdmin(admin.ModelAdmin):
    list_display = ["date","xmr_priceusd","btc_priceusd"]
    list_filter = ["date"]
    list_per_page = 10
    ordering = ["date"]
