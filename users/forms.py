from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=150, help_text='E-mail')
    type = forms.CharField(max_length=100, help_text='Contributor or user?')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'type') 