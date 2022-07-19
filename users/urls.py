from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Pages URLs
    # Everyone can use these,
    path('register/',  views.register, name="register"),
    path('login/',  auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    
    # URLs pages users might want to visit
    # Only registered users can use these 
    path('contract/',  views.contract, name="contract"),
    path('logout/', views.logout_view, name="logout"),

    # URLs administration pages
    # Only admins can use these 
    path('edit_user/<str:identification>/<str:type>/',  views.edit_user, name="edit_user"),
    path('delete_user/<str:identification>/',  views.delete_user, name="delete_user"),
    path('block_user/<str:identification>/',  views.block_user, name="block_user"),
    path('unblock_user/<str:identification>/',  views.unblock_user, name="unblock_user"),
    path('delete_subscriber/<str:identification>/',  views.delete_subscriber, name="delete_subscriber"),
    path('users/',  views.users, name="users"),
]