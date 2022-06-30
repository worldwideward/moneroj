from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
	#login page
    path('login/',  auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
	
	#logou page
    path('logout/', views.logout_view, name="logout"),
	
	#new user register
    path('register/',  views.register, name="register"),
	
    #contract page
    path('contract/',  views.contract, name="contract"),

    #contract page
    path('delete_user/<str:identification>/',  views.delete_user, name="delete_user")
]