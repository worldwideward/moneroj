from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from .forms import *
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import datetime
from datetime import date, timedelta

###########################################
# General visitors' pages
###########################################

# Create your views here.
def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('charts:index'))
	
def register(request):
	user = request.user
	if user.is_authenticated:
		return HttpResponseRedirect(reverse('charts:index'))

	if request.method != 'POST':
		form = SignUpForm()
	else:
		form = SignUpForm(data=request.POST)
		if form.is_valid():
			user = form.save()
			user.refresh_from_db()
			user.profile.email = form.cleaned_data.get('email')
			user.profile.type = form.cleaned_data.get('type')
			user.save()
			try:
				block = BlockedEmail.objects.get(email=user.profile.email)
				if block:
					user.delete()
					context = {'form': form}
					return render(request, 'users/register.html', context)
			except:
				pass
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=password)
			login(request, user)
			return HttpResponseRedirect(reverse('users:contract'))
		else:
			context = {'form': form}
			return render(request, 'users/register.html', context)
			
	context = {'form': form}
	return render(request, 'users/register.html', context)

def update_visitors(index):
	try:
		today = datetime.datetime.strftime(date.today(), '%Y-%m-%d')
		pageviews = PageViews.objects.get(date=today)
		if index:
			pageviews.unique_visitors += 1
		pageviews.total_pageviews += 1
		pageviews.save()
	except:
		pageviews = PageViews() 
		pageviews.date = today
		if index:
			pageviews.unique_visitors = 1
		else:
			pageviews.unique_visitors = 0
		pageviews.total_pageviews = 1
		pageviews.save()

	#print(pageviews.unique_visitors)
	#print(pageviews.total_pageviews)
	
	return True

###########################################
# Required login - Users
###########################################

@login_required
def contract(request):
	context = {}
	return render(request, "users/contract.html", context)

###########################################
# Administrators 
###########################################

@login_required
def delete_user(request, identification):
	profile = Profile.objects.get(id=identification)
	user = User.objects.get(username=profile.user)
	user_aux = request.user
	if request.user.username != "Administrador" and request.user.username != "Morpheus" and user != user_aux:
		return render(request, 'users/error.html')

	profile.delete()
	user.delete()

	if request.user.username != "Administrador" or request.user.username != "Morpheus":
		return HttpResponseRedirect(reverse('users:users'))
	else:
		return HttpResponseRedirect(reverse('charts:index'))

@login_required
def block_user(request, identification):
	if request.user.username != "Administrador" and request.user.username != "Morpheus":
		return render(request, 'users/error.html')

	profile = Profile.objects.get(id=identification)
	user = User.objects.get(username=profile.user)
	block = BlockedEmail()
	block.email = user.email
	block.save()
	profile.delete()
	user.delete()

	if request.user.username != "Administrador" or request.user.username != "Morpheus":
		return HttpResponseRedirect(reverse('users:users'))
	else:
		return HttpResponseRedirect(reverse('charts:index'))

@login_required
def unblock_user(request, identification):
	if request.user.username != "Administrador" and request.user.username != "Morpheus":
		return render(request, 'users/error.html')

	blocked = BlockedEmail.objects.get(id=identification)
	blocked.delete()

	return HttpResponseRedirect(reverse('users:users'))

@login_required
def delete_subscriber(request, identification):
	if request.user.username != "Administrador" and request.user.username != "Morpheus":
		return render(request, 'users/error.html')

	subscriber = Subscriber.objects.get(id=identification)
	subscriber.delete()

	return HttpResponseRedirect(reverse('users:users'))

@login_required
def users(request):
	if request.user.username != "Administrador" and request.user.username != "Morpheus":
		return render(request, 'users/error.html')
			
	users = Profile.objects.order_by('id')
	for user in users:
		if user.user.username == 'Morpheus' or user.user.username == 'Administrador':
			user.type = 'admin'
			user.save()

	blocks = BlockedEmail.objects.order_by('id')
	subscribers = Subscriber.objects.order_by('id')

	context = {'users': users, 'blocks': blocks, 'subscribers': subscribers}
	return render(request, 'users/users.html', context)

@login_required
def edit_user(request, identification, type):
	if request.user.username != "Administrador" and request.user.username != "Morpheus":
		return render(request, 'users/error.html')
	
	profile = Profile.objects.get(id=identification)
	profile.type = type
	profile.save()

	return HttpResponseRedirect(reverse('users:users'))
