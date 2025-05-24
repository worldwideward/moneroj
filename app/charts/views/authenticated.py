'''Views module'''

import locale

from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required

from charts.models import Coin
from charts.models import Social
from charts.models import Sfmodel
from charts.models import DailyData

from charts.synchronous import get_history_function
from charts.synchronous import update_database

from charts.import_history import import_rank_history
from charts.import_history import import_dominance_history
from charts.import_history import import_p2pool_history

from charts.update_data.utils import erase_coin_data
from charts.update_data.utils import erase_sf_model_data
from charts.update_data.utils import erase_daily_data_data
from charts.update_data.stock_to_flow import calculate_sf_model
from charts.update_data.daily_data import calculate_daily_data

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

####################################################################################
#   Useful functions for admins
####################################################################################

@login_required
def get_history(request, symbol, start_time=None, end_time=None):
    '''Get all history for metrics of a certain coin named as 'symbol'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    count = get_history_function(symbol, start_time, end_time)

    if type(count) in [int, 'int']:
        message = 'Total of ' + str(count) + ' data imported'
        context = {'message': message}
    else:
        message = 'Failed to load the data'
        context = {'message': message}

    return render(request, 'charts/maintenance.html', context)

@login_required
def load_rank(request, symbol):
    '''Populate database with rank history from spreadsheet'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = import_rank_history(symbol)

    message = 'Total of ' + str(result) + ' rows imported'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

@login_required
def load_dominance(request, symbol):
    '''Populate database with dominance history'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = import_dominance_history(symbol)

    message = 'Total of ' + str(result) + ' data imported'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

@login_required
def load_p2pool(request):
    '''Populate database with p2pool history from spreadsheet'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = import_p2pool_history()

    message = 'Total of ' + str(result) + ' data imported'
    context = {'message': message}
    return render(request, 'charts/maintenance.html', context)

@login_required
def reset(request, symbol: str):
    '''Erase all data for a certain coin'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = erase_coin_data(symbol)

    if result == True:
        message = f'All data for {symbol} erased'
    else:
        message = f'Something went wrong trying to erase data for {symbol}. Please try again.'

    context = {'message': message}

    return render(request, 'charts/maintenance.html', context)

@login_required
def reset_sf_model(request):
    '''Erase all data for sf model'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = erase_sf_model_data()

    if result == True:
        message = f'All Stock to flow data erased'
    else:
        message = f'Something went wrong trying to erase Stock to flow data. Please try again.'

    context = {'message': message}

    return render(request, 'charts/maintenance.html', context)

@login_required
def reset_daily_data(request):
    '''Erase all data for sf model'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    result = erase_daily_data_data()

    if result == True:
        message = f'All Daily data erased'
    else:
        message = f'Something went wrong trying to erase Daily data. Please try again.'

    context = {'message': message}

    return render(request, 'charts/maintenance.html', context)

@login_required
def populate_database(request):
    '''Populate database with specific chart variables'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    erase_sf_model_data()
    result = calculate_sf_model()

    if result == True:
        print('[INFO] Recreated Sfmodel database entries')
    else:
        print('[ERROR] Something went wrong during calculation')

    erase_daily_data_data()
    result = calculate_daily_data()

    if result == True:
        print('[INFO] Recreated Daily data database entries')
    else:
        print('[ERROR] Something went wrong during calculation')

    context = {'message': 'Database populated'}
    return render(request, 'charts/maintenance.html', context)

@login_required
def update_database_admin(request, date_from, date_to):
    '''Update database between certain dates'''

    if not request.user.is_superuser:
        return render(request, 'users/error.html')

    update_database(date_from, date_to)

    context = {'message': f'Database updated from {str(date_from)} to {str(date_to)}'}
    print(f'[DEBUG] {context}')

    return render(request, 'charts/maintenance.html', context)
