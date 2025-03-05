from django.urls import path
from . import views

app_name = 'icons'

urlpatterns = [
    path('api/icons/', views.icon_list, name='icon_list'),
    path('api/icons/categories/', views.icon_categories, name='icon_categories'),
]