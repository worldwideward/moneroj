'''Views module'''

import locale

from datetime import date
from datetime import datetime
from django.shortcuts import render
from django.conf import settings

from charts.models import Dread

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

####################################################################################
#   Views
####################################################################################

def dread_subscribers(request):
    '''Dread Subscribes (Darknet forum)'''

    dates = []
    bitcoin_subscribers = []
    monero_subscribers = []

    data = Dread.objects.order_by('date')

    for item in data:

        dates.append(datetime.strftime(item.date, "%Y-%m-%d"))
        bitcoin_subscribers.append(item.bitcoin_subscriber_count)
        monero_subscribers.append(item.monero_subscriber_count)

    context = {
            'dates': dates,
            'data1': bitcoin_subscribers,
            'data2': monero_subscribers
            }

    return render(request, 'charts/dread_subscribers.html', context)
