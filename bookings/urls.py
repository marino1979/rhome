from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Viste pubbliche
    path('listing/<slug:slug>/', views.listing_detail_with_booking, name='listing_detail'),

    # API endpoints
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/quick-availability/', views.quick_availability_check, name='quick_availability_check'),
    path('api/combined-availability/', views.combined_availability, name='combined_availability'),
    path('api/combined-booking/', views.create_combined_booking, name='create_combined_booking'),
    path('api/calendar/<int:listing_id>/', views.get_listing_calendar, name='listing_calendar'),
    path('api/calendar/slug/<slug:slug>/', views.get_listing_calendar_by_slug, name='listing_calendar_by_slug'),

    # Gestione prenotazioni (richiede login)
    path('create/', views.create_booking, name='create_booking'),
    path('my-bookings/', views.booking_list, name='booking_list'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # Messaggistica (richiede login)
    path('booking/<int:booking_id>/messages/', views.booking_messages, name='booking_messages'),
    path('booking/<int:booking_id>/send-message/', views.send_message, name='send_message'),
    path('booking/<int:booking_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
]