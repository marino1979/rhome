"""
Views per il testing del calendario frontend.
Permette di vedere come il calendario reagisce alle varie indisponibilità.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta
from .models import Listing
from calendar_rules.services import CalendarService, CalendarServiceError
from bookings.models import Booking


def calendar_test_page(request, slug=None):
    """
    Pagina di test per verificare il comportamento del calendario frontend.
    Mostra tutte le informazioni di disponibilità in modo dettagliato.
    """
    # Se non c'è slug, mostra la lista di listings
    if not slug:
        listings = Listing.objects.filter(status='active')
        return render(request, 'listings/calendar_test_list.html', {
            'listings': listings
        })
    
    # Altrimenti mostra il test per il listing specifico
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # Calcola range di date
    start_date = date.today()
    booking_window_days = listing.max_booking_advance or 365
    end_date = start_date + timedelta(days=booking_window_days)
    
    # Ottieni tutti i dati di disponibilità
    try:
        calendar_service = CalendarService(listing)
        calendar_data = calendar_service._get_optimized_calendar_data(start_date, end_date)
        unavailable_data = calendar_service.get_unavailable_dates(start_date, end_date)
    except Exception as e:
        unavailable_data = {'error': str(e)}
        calendar_data = {}
    
    # Ottieni tutte le prenotazioni
    bookings = Booking.objects.filter(
        listing=listing,
        status__in=['pending', 'confirmed']
    ).order_by('check_in_date')
    
    # Ottieni tutte le chiusure
    closures = listing.closure_rules.all().order_by('start_date')
    
    # Ottieni tutte le regole check-in/out
    checkinout_rules = listing.checkinout_rules.all()
    
    context = {
        'listing': listing,
        'start_date': start_date,
        'end_date': end_date,
        'unavailable_data': unavailable_data,
        'calendar_data': calendar_data,
        'bookings': bookings,
        'closures': closures,
        'checkinout_rules': checkinout_rules,
    }
    
    return render(request, 'listings/calendar_test.html', context)


@require_http_methods(["GET"])
def calendar_test_api(request, slug):
    """
    API endpoint per il test del calendario.
    Restituisce i dati di disponibilità in formato JSON.
    """
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    try:
        start_date = date.today()
        booking_window_days = listing.max_booking_advance or 365
        end_date = start_date + timedelta(days=booking_window_days)
        
        calendar_service = CalendarService(listing)
        result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        return JsonResponse({
            'success': True,
            'data': result,
            'metadata': {
                'listing_id': listing.id,
                'listing_title': listing.title,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


