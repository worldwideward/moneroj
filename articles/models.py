from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Article(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	date_added = models.DateTimeField(auto_now_add=True)
	date_updated = models.DateField(null=True, blank=True)
	date_published = models.DateField(null=True, blank=True)
	author = models.CharField(max_length=50)
	status = models.CharField(max_length=20)
	review = models.TextField(null=True, blank=True)
	url = models.CharField(max_length=200)
	#formular
	title = models.CharField(max_length=150)
	subtitle = models.CharField(max_length=100)
	thumbnail = models.CharField(max_length=100)
	text = models.TextField()

	class Meta:
		verbose_name_plural = 'articles'

	def __str__(self):
		return self.title