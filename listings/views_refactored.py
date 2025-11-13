"""
Views refactorizzate per il sistema di calendario.
Queste views utilizzano il nuovo CalendarService per la gestione della disponibilità.
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Listing
from calendar_rules.services import CalendarService, CalendarServiceError
from calendar_rules.managers import CalendarManager


def get_unavailable_dates_refactored(request, slug):
    """
    API endpoint refactorizzato per ottenere le date non disponibili.
    
    Questa versione usa il nuovo CalendarService invece della logica monolitica
    precedente. Mantiene la stessa interfaccia API per compatibilità.
    
    Args:
        request: Django HttpRequest
        slug: Slug del listing
        
    Returns:
        JsonResponse con le date non disponibili nel formato standard
    """
    listing = get_object_or_404(Listing, slug=slug, status='active')

    try:
        # Calcola range di date
        start_date = date.today()
        booking_window_days = listing.max_booking_advance or 365
        end_date = start_date + timedelta(days=booking_window_days)
        
        # Usa il nuovo CalendarService
        calendar_service = CalendarService(listing)
        result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        return JsonResponse(result)

    except CalendarServiceError as e:
        # Errori specifici del calendario
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        # Altri errori
        return JsonResponse({'error': 'Errore interno del server'}, status=500)


def compare_old_vs_new_calendar_logic(request, slug):
    """
    API endpoint per confrontare la logica vecchia vs nuova del calendario.
    
    Utile per testing e debugging durante la migrazione al nuovo sistema.
    Mostra le differenze tra i risultati della logica vecchia e nuova.
    
    Args:
        request: Django HttpRequest
        slug: Slug del listing
        
    Returns:
        JsonResponse con confronto dei risultati
    """
    listing = get_object_or_404(Listing, slug=slug, status='active')

    try:
        # Calcola range di date
        start_date = date.today()
        booking_window_days = listing.max_booking_advance or 365
        end_date = start_date + timedelta(days=booking_window_days)
        
        # Logica vecchia (CalendarManager)
        calendar_manager = CalendarManager(listing)
        old_result = {
            'blocked_ranges': [],
            'checkin_dates': [],
            'checkout_dates': [],
        }
        
        # Cerca prenotazioni nel periodo
        from bookings.models import Booking
        bookings = Booking.objects.filter(
            listing=listing,
            check_out__gte=start_date,
            check_in__lte=end_date,
            status__in=['confirmed', 'pending']
        )
        
        for booking in bookings:
            if booking.check_in <= end_date and booking.check_out >= start_date:
                old_result['blocked_ranges'].append({
                    'from': max(booking.check_in, start_date).isoformat(),
                    'to': min(booking.check_out, end_date).isoformat()
                })
                old_result['checkin_dates'].append(booking.check_in.isoformat())
                old_result['checkout_dates'].append(booking.check_out.isoformat())
        
        # Logica nuova (CalendarService)
        calendar_service = CalendarService(listing)
        new_result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        # Confronta i risultati
        old_ranges_count = len(old_result['blocked_ranges'])
        new_ranges = new_result.get('blocked_ranges', [])
        new_ranges_count = len(new_ranges)
        
        # Confronto semplice (può essere migliorato)
        comparison = {
            'old_ranges': old_ranges_count,
            'new_ranges': new_ranges_count,
            'match': old_ranges_count == new_ranges_count,
            'differences': {
                'old_ranges': old_ranges_count,
                'new_ranges': new_ranges_count,
                'match': old_ranges_count == new_ranges_count
            }
        }
        
        return JsonResponse({
            'success': True,
            'comparison': comparison,
            'old_result': old_result,
            'new_result': {
                'blocked_ranges': new_ranges,
                'turnover_days': new_result.get('turnover_days', []),
                'checkin_block': new_result.get('checkin_block', []),
                'checkout_block': new_result.get('checkout_block', []),
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

