'''Views module'''

import locale

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage

####################################################################################
#   Set some parameters
####################################################################################
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

####################################################################################
#   Views
####################################################################################
def index(request):
    '''The main Charts view'''

    return render(request, 'charts/index.html')

def about(request):
    '''The about page'''

    return render(request, 'charts/about.html')
