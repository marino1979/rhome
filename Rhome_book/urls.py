"""
URL configuration for Rhome_book project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # aggiungi questo import
from django.conf.urls.static import static  # aggiungi questo import
from django.shortcuts import render
def chi_siamo(request):
    return render(request, 'chi-siamo.html')
def contatti(request):
    return render(request, 'contatti.html')
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]
def home(request):
    return render(request, 'listings/listing_list.html')

urlpatterns += [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('appartamenti/', include('listings.urls')),
    path('icons/', include('icons.urls')),
    path('api/', include('calendar_rules.urls')),  # per le API - include /api/calculate-price/
    path('calendar/', include('calendar_rules.urls')),  # per le viste web
    path('i18n/', include('django.conf.urls.i18n')),
    path('chi-siamo/', chi_siamo, name='about_us'),
    path('contatti/', contatti, name='contacts'),
    path('prenotazioni/', include('bookings.urls')),
    path('accounts/', include('users.urls')),
    path('accounts/', include('allauth.urls')),  # Django Allauth URLs (deve essere prima di django.contrib.auth.urls)
    path('accounts/', include('django.contrib.auth.urls')),
]

# Aggiungi questa parte per servire i file media in sviluppo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)