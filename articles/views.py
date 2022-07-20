from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from .forms import *
from users.models import *
from users.forms import *
from users.views import update_visitors
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import datetime
from datetime import date, timedelta

###########################################
# General visitors' pages
###########################################

def articles(request):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)

    articles = Article.objects.filter(status="Published").order_by('-id')
    first = True
    thumbnail = ''
    count = 0
    for article in articles:
        if first:
            thumbnail = article.thumbnail
            thumbnail = thumbnail.replace('400x300', '1920x1080')
            first = False
        article.thumbnail = 'img/articles/' + article.thumbnail
        if len(article.title) > 100:
            article.title = article.title[:100] + '...'
        article.count = count
        if count != 5 and count != 0:
            article.text = article.text[:400] + '...'
        else:
            article.text = article.text[:600] + '...'
        count += 1

    if request.method != 'POST':
		#no data, go back to articles section
        form = SubscriberForm()
        message = False
    else:
        #e-mail submitted
        form = SubscriberForm(data=request.POST)
        if form.is_valid():
            new_subscriber = form.save(commit=False)
            new_subscriber.save()
            message = 'Subscription successful!'
        else:
            message = 'Something went wrong!'

    print(thumbnail)

    context = {'page': 'article', 'articles': articles, 'form': form, 'message': message, 'thumbnail': thumbnail}
    return render(request, 'articles/articles.html', context)

def article(request, identification):
    if request.user.username != "Administrador" and request.user.username != "Morpheus":
        update_visitors(False)

    try:
        article = Article.objects.get(id=identification)
    except:
        try:
            identification = identification.replace('-', ' ')
            article = Article.objects.get(title=identification)
        except:
            return render(request, 'users/error.html')
    
    article.thumbnail = article.thumbnail.replace('400x300', '1920x1080')

    if article.status == 'Published':
        context = {'page': 'article', 'article': article}
        return render(request, 'articles/article.html', context)
    else:
        if request.user.username != "Administrador" and request.user.username != "Morpheus" and request.user != article.owner and request.user.profile.type != 'editor':
            return render(request, 'users/error.html')
        else:
            context = {'page': 'article', 'article': article}
            return render(request, 'articles/article.html', context)

###########################################
# Required login - Users
###########################################

@login_required
def images(request):
    context = {'page': 'article'}
    return render(request, 'articles/images.html', context)

@login_required
def write(request):
    articles = Article.objects.filter(author=request.user).order_by('-id')
    for article in articles:
        try:
            article.date_added = datetime.datetime.strftime(article.date_added, '%d/%m/%Y')
            article.date_updated = datetime.datetime.strftime(article.date_updated, '%d/%m/%Y')
        except:
            pass
        try:
            article.date_published = datetime.datetime.strftime(article.date_published, '%d/%m/%Y')
        except:
            pass
        article.title = article.title[:50] + '...'

    if request.user.profile.type == 'editor':
        reviews = Article.objects.filter(status="Pending approval").exclude(author=request.user)
        for review in reviews:
            try:
                review.date_added = datetime.datetime.strftime(review.date_added, '%d/%m/%Y')
                review.date_updated = datetime.datetime.strftime(review.date_updated, '%d/%m/%Y')
            except:
                pass
            try:
                review.date_published = datetime.datetime.strftime(review.date_published, '%d/%m/%Y')
            except:
                pass
            review.title = review.title[:50] + '...'
        
        context = {'page': 'article', 'articles': articles, 'reviews': reviews}

    if request.user.profile.type == "admin":
        reviews = Article.objects.filter(status="Pending approval")
        for review in reviews:
            try:
                review.date_added = datetime.datetime.strftime(review.date_added, '%d/%m/%Y')
                review.date_updated = datetime.datetime.strftime(review.date_updated, '%d/%m/%Y')
            except:
                pass
            try:
                review.date_published = datetime.datetime.strftime(review.date_published, '%d/%m/%Y')
            except:
                pass
            review.title = review.title[:50] + '...'

        published = Article.objects.filter(status="Published")
        for publish in published:
            try:
                publish.date_added = datetime.datetime.strftime(publish.date_added, '%d/%m/%Y')
                publish.date_updated = datetime.datetime.strftime(publish.date_updated, '%d/%m/%Y')
            except:
                pass
            try:
                publish.date_published = datetime.datetime.strftime(publish.date_published, '%d/%m/%Y')
            except:
                pass
            publish.title = publish.title[:50] + '...'
        
        context = {'page': 'article', 'articles': articles, 'reviews': reviews, 'published': published}
    
    else:
        context = {'page': 'article', 'articles': articles}
    return render(request, 'articles/write.html', context)

@login_required
def new_article(request):
    if request.method != 'POST':
        #create new page with blank form
        form = ArticleForm()
    else:
        #process data and submit article
        form = ArticleForm(data=request.POST)
        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.author = request.user.username
            articles = Article.objects.filter(author=new_article.author).filter(status='Pending approval')
            count = 0
            if articles:
                for article in articles:
                    count += 1
            if count >= 5:
                return HttpResponseRedirect(reverse('articles:write'))
            new_article.date_updated = datetime.datetime.now()
            new_article.owner = request.user
            new_article.url = new_article.title.replace(' ', '-')
            new_article.status = 'Pending approval'
            new_article.save()
            return HttpResponseRedirect(reverse('articles:write'))

    context = {'form': form, 'page': 'article'}
    return render(request, 'articles/new_article.html', context)

@login_required
def edit_article(request, identification):
    try:
        article = Article.objects.get(id=identification)
    except:
        return render(request, 'users/error.html')
    if request.user.profile.type != "admin" and request.user != article.owner:
        return render(request, 'users/error.html')
	
    if request.method != 'POST':
        #no data submitted, load saved data
        form = ArticleForm(instance=article)
    else:
        #data submitted, now save it
        form = ArticleForm(instance=article, data=request.POST)
        if form.is_valid():
            new_article = form.save(commit=False)
            new_article.author = request.user.username
            new_article.date_updated = date.today()
            new_article.owner = request.user
            new_article.url = new_article.title.replace(' ', '-')
            new_article.status = 'Pending approval'
            new_article.save()
            return HttpResponseRedirect(reverse('articles:write'))

    context = {'form': form, 'article': article, 'page': 'article'}
    return render(request, 'articles/edit_article.html', context)

@login_required
def delete_article(request, identification):
    try:
        article = Article.objects.get(id=identification)
    except:
        return render(request, 'users/error.html')
    if request.user.profile.type != "admin" and request.user != article.owner:
        return render(request, 'users/error.html')

    article.delete()
    return HttpResponseRedirect(reverse('articles:write'))

@login_required
def publish_article(request, identification):
    try:
        article = Article.objects.get(id=identification)
    except:
        return render(request, 'users/error.html')
    if request.user.profile.type != "admin" and request.user.profile.type != "editor":
        return render(request, 'users/error.html')

    if request.user.profile.type == article.owner.profile.type and request.user.profile.type != 'admin':
        return render(request, 'users/error.html')

    article.status = 'Published'
    article.date_published = date.today()
    article.save()
    return HttpResponseRedirect(reverse('articles:write'))