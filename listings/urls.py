from django.urls import path
from . import views
from . import views_test
from .views_wizard import ListingWizardView, RoomTypesView, BedTypesView, AmenityCategoriesView

app_name = 'listings'

urlpatterns = [
    path('', views.listing_list, name='listing_list'),
    path('create/', views.listing_create, name='listing_create'),  # SPOSTATO QUI

    # Test calendar (deve venire prima di <slug:slug>)
    path('calendar-test/', views_test.calendar_test_page, name='calendar_test'),
    path('calendar-test/<slug:slug>/', views_test.calendar_test_page, name='calendar_test_detail'),
    path('calendar-test/<slug:slug>/api/', views_test.calendar_test_api, name='calendar_test_api'),

    path('wizard/', ListingWizardView.as_view(), name='listing_wizard'),
    path('room-types/', RoomTypesView.as_view(), name='room_types'),
    path('bed-types/', BedTypesView.as_view(), name='bed_types'),
    path('amenity-categories/', AmenityCategoriesView.as_view(), name='amenity_categories'),

    # Rotte generiche basate sullo slug (devono essere in fondo)
    path('<slug:slug>/', views.listing_detail, name='detail'),    # ORA VIENE DOPO
    path('<slug:slug>/check-availability/', views.check_availability, name='check_availability'),
    path('<slug:slug>/unavailable-dates/', views.get_unavailable_dates, name='unavailable_dates'),
]