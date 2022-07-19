from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Pages URLs
    # Everyone can use these
    path('articles/', views.articles, name="articles"),
    path('article/<str:identification>/', views.article, name="article"),

    # URLs to articles writing and edit, etc
    # Only registered users can use these 
    path('write/', views.write, name="write"),
    path('new_article/', views.new_article, name="new_article"),
    path('images/', views.images, name="images"),
    path('edit_article/<str:identification>/', views.edit_article, name="edit_article"),
    path('publish_article/<str:identification>/', views.publish_article, name="publish_article"),
    path('delete_article/<str:identification>/', views.delete_article, name="delete_article"),

]