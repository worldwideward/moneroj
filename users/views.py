from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from .forms import *
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

# Create your views here.
def logout_view(request):
	logout(request)
	return HttpResponseRedirect(reverse('monerojnet:index'))
	
def register(request):
	user = request.user
	if user.is_authenticated:
		return HttpResponseRedirect(reverse('monerojnet:index'))

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

@login_required
def contract(request):
	context = {}
	return render(request, "users/contract.html", context)

@login_required
def delete_user(request, identification):
	profile = Profile.objects.get(id=identification)
	user = User.objects.get(username=profile.user)
	user_aux = request.user
	if request.user.username != "Administrador" and user != user_aux:
		return render(request, 'monerojnet/index.html')

	profile = Profile.objects.get(id=identification)
	user = User.objects.get(username=profile.user)
	profile.delete()
	user.delete()
	return HttpResponseRedirect(reverse('monerojnet:index'))