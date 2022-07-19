from articles.models import *
from django import forms

class ArticleForm(forms.ModelForm):
	class Meta:
		model = Article
		fields = ['title', 'subtitle', 'thumbnail', 'text']
