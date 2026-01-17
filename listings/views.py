from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Listing
from calendar_rules.managers import CalendarManager

def listing_list(request):
    """Vista per mostrare tutti gli annunci attivi"""
    listings = Listing.objects.filter(status='active')
    return render(request, 'listings/listing_list.html', {
        'listings': listings,
        'user': request.user  # Assicura che user sia disponibile nel template
    })

def listing_detail(request, slug):
    """Vista per mostrare il dettaglio di un singolo annuncio"""
    listing = get_object_or_404(Listing, slug=slug, status='active')

    # Crea la lista di opzioni per gli ospiti
    guest_options = range(1, listing.max_guests + 1)

    # Inizializza CalendarManager per controlli di disponibilità
    calendar = CalendarManager(listing)

    # Calcola prezzi per i prossimi 7 giorni come esempio
    today = date.today()
    sample_prices = []
    for i in range(7):
        check_date = today + timedelta(days=i)
        price = calendar.get_price_per_day(check_date)
        sample_prices.append({
            'date': check_date,
            'price': float(price)
        })

    # Trova il prezzo minimo e massimo per il periodo
    prices = [p['price'] for p in sample_prices]
    min_price = min(prices) if prices else listing.base_price
    max_price = max(prices) if prices else listing.base_price

    # Recensioni e statistiche
    reviews = listing.reviews.all().order_by('-review_date', '-created_at')
    reviews_stats = listing.get_reviews_stats()
    
    # Filtro recensioni se richiesto
    review_filter = request.GET.get('review_filter', 'all')
    if review_filter == 'airbnb':
        reviews = reviews.filter(airbnb_review_id__isnull=False)
    elif review_filter == 'own':
        reviews = reviews.filter(airbnb_review_id__isnull=True)

    return render(request, 'listings/listing_detail.html', {
        'listing': listing,
        'guest_options': guest_options,
        'sample_prices': sample_prices,
        'min_price': min_price,
        'max_price': max_price,
        'has_dynamic_pricing': min_price != max_price,
        'reviews': reviews,
        'reviews_stats': reviews_stats,
        'review_filter': review_filter,
    })

def check_availability(request, slug):
    """API endpoint per verificare disponibilità in tempo reale"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)

    listing = get_object_or_404(Listing, slug=slug, status='active')

    try:
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        if not check_in or not check_out:
            return JsonResponse({'error': 'Date mancanti'}, status=400)

        # Converti stringhe in date
        from datetime import datetime
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

        if check_in_date >= check_out_date:
            return JsonResponse({'error': 'Date non valide'}, status=400)

        # Usa CalendarManager per verificare disponibilità
        calendar = CalendarManager(listing)
        is_available, message = calendar.check_availability(check_in_date, check_out_date)

        return JsonResponse({
            'available': is_available,
            'message': message,
            'dates': {
                'check_in': check_in,
                'check_out': check_out
            }
        })

    except ValueError as e:
        return JsonResponse({'error': 'Formato date non valido'}, status=400)

def booking_calendar_demo(request, slug):
    """Vista demo per il nuovo calendario di prenotazione"""
    listing = get_object_or_404(Listing, slug=slug, status='active')
    return render(request, 'listings/booking_calendar_demo.html', {
        'listing': listing
    })


def get_unavailable_dates(request, slug):
    """
    API endpoint per calendario booking - REFACTORIZZATO con CalendarService.
    
    Questa versione usa il nuovo CalendarService per separare la logica business
    dalla gestione delle richieste HTTP.
    """
    listing = get_object_or_404(Listing, slug=slug, status='active')

    try:
        # Calcola range di date
        start_date = date.today()
        booking_window_days = listing.max_booking_advance or 365
        end_date = start_date + timedelta(days=booking_window_days)
        
        # Usa il nuovo CalendarService
        from calendar_rules.services import CalendarService, CalendarServiceError
        calendar_service = CalendarService(listing)
        result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        return JsonResponse(result)

    except CalendarServiceError as e:
        # Errori specifici del calendario
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        # Altri errori
        return JsonResponse({'error': 'Errore interno del server'}, status=500)


def listing_create(request):
    return render(request, 'listing_create.html')


#
