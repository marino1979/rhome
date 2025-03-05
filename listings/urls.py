from django.urls import path
from . import views
from .views_wizard import ListingWizardView, RoomTypesView, BedTypesView, AmenityCategoriesView

app_name = 'listings'

urlpatterns = [
    path('', views.listing_list, name='listing_list'),
    path('create/', views.listing_create, name='listing_create'),  # SPOSTATO QUI
    path('<slug:slug>/', views.listing_detail, name='detail'),    # ORA VIENE DOPO
    path('api/listing/wizard/', ListingWizardView.as_view(), name='listing_wizard'),
    path('api/room-types/', RoomTypesView.as_view(), name='room_types'),
    path('api/bed-types/', BedTypesView.as_view(), name='bed_types'),
    path('api/amenity-categories/', AmenityCategoriesView.as_view(), name='amenity_categories'),
]