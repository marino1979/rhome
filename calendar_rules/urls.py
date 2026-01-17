"""
URLs per il sistema calendario.

API Endpoints:
- /api/listings/{id}/calendar/ - Dati calendario completi
- /api/listings/{id}/check-availability/ - Verifica disponibilità
- /api/listings/{id}/calculate-price/ - Calcola prezzo
- /api/listings/{id}/info/ - Info listing
- /api/calendar/combined/ - Dati calendario combinato (tutti i gruppi)
"""

from django.urls import path
from . import api_views

app_name = 'calendar'

urlpatterns = [
    # API per frontend
    path('api/listings/<int:listing_id>/calendar/', api_views.calendar_data, name='calendar-data'),
    path('api/listings/<int:listing_id>/check-availability/', api_views.check_availability, name='check-availability'),
    path('api/listings/<int:listing_id>/calculate-price/', api_views.calculate_price, name='calculate-price'),
    path('api/listings/<int:listing_id>/info/', api_views.listing_info, name='listing-info'),

    # API calendario combinato
    path('api/calendar/combined/', api_views.combined_calendar_data, name='combined-calendar-data'),
]
