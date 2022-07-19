from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=150)
    type = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

class BlockedEmail(models.Model):
    email = models.EmailField(max_length=150)

    def __str__(self):
        return self.id
        
class Subscriber(models.Model):
    email = models.EmailField(max_length=150)

    def __str__(self):
        return self.email

class PageViews(models.Model):
	date = models.DateField()
	unique_visitors = models.IntegerField(null=True, blank=True)
	total_pageviews = models.IntegerField(null=True, blank=True)

	def __str__(self):
		return self.id

@receiver(post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
