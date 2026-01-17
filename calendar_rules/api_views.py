"""
API Views per il sistema calendario.

Endpoints per frontend Airbnb-style:
- GET /api/listings/{id}/calendar/ - Dati calendario (disponibilità + prezzi)
- POST /api/listings/{id}/check-availability/ - Verifica disponibilità specifica
- POST /api/listings/{id}/calculate-price/ - Calcola prezzo per periodo
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from listings.models import Listing
from .availability import AvailabilityChecker
from .pricing import PriceCalculator


@require_http_methods(["GET"])
def calendar_data(request, listing_id):
    """
    Restituisce dati completi del calendario per il frontend.

    GET /api/listings/{listing_id}/calendar/?start=2025-01-01&end=2025-03-31

    Query Parameters:
        start: Data inizio (formato: YYYY-MM-DD)
        end: Data fine (formato: YYYY-MM-DD)

    Response:
        {
            "blocked_dates": ["2025-01-15", "2025-01-16", ...],
            "checkin_disabled": ["2025-01-20", ...],
            "checkout_disabled": ["2025-01-22", ...],
            "prices": {
                "2025-01-15": 100.00,
                "2025-01-16": 120.00,
                ...
            },
            "min_stay": 2,
            "gap_days": 1,
            "listing": {
                "id": 1,
                "title": "Appartamento Centro",
                "base_price": 100.00,
                "cleaning_fee": 50.00,
                "max_guests": 4,
                "included_guests": 2,
                "extra_guest_fee": 15.00
            }
        }
    """
    try:
        listing = get_object_or_404(Listing, pk=listing_id, status='active')

        # Parse date parameters
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')

        if not start_str or not end_str:
            return JsonResponse({
                'error': 'Parametri start e end richiesti'
            }, status=400)

        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'error': 'Formato date non valido. Usa YYYY-MM-DD'
            }, status=400)

        if start_date >= end_date:
            return JsonResponse({
                'error': 'La data di fine deve essere successiva alla data di inizio'
            }, status=400)

        # Limita range massimo a 1 anno per performance
        max_days = 365
        if (end_date - start_date).days > max_days:
            return JsonResponse({
                'error': f'Range massimo: {max_days} giorni'
            }, status=400)

        # Ottieni dati disponibilità
        availability_checker = AvailabilityChecker(listing)
        availability_data = availability_checker.get_calendar_data(start_date, end_date)

        # Ottieni prezzi
        price_calculator = PriceCalculator(listing)
        prices = price_calculator.get_calendar_prices(start_date, end_date)

        # Costruisci response
        response_data = {
            **availability_data,
            'prices': prices,
            'listing': {
                'id': listing.id,
                'title': listing.title,
                'slug': listing.slug,
                'base_price': float(listing.base_price),
                'cleaning_fee': float(listing.cleaning_fee),
                'max_guests': listing.max_guests,
                'included_guests': listing.included_guests,
                'extra_guest_fee': float(listing.extra_guest_fee),
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': f'Errore interno: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def check_availability(request, listing_id):
    """
    Verifica disponibilità per un periodo specifico.

    POST /api/listings/{listing_id}/check-availability/

    Body (JSON):
        {
            "check_in": "2025-01-15",
            "check_out": "2025-01-18"
        }

    Response:
        {
            "available": true/false,
            "message": "Disponibile" o "Motivo non disponibilità",
            "dates": {
                "check_in": "2025-01-15",
                "check_out": "2025-01-18",
                "nights": 3
            }
        }
    """
    try:
        listing = get_object_or_404(Listing, pk=listing_id, status='active')

        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON non valido'
            }, status=400)

        check_in_str = data.get('check_in')
        check_out_str = data.get('check_out')

        if not check_in_str or not check_out_str:
            return JsonResponse({
                'error': 'Parametri check_in e check_out richiesti'
            }, status=400)

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'error': 'Formato date non valido. Usa YYYY-MM-DD'
            }, status=400)

        # Verifica disponibilità
        availability_checker = AvailabilityChecker(listing)
        is_available, message = availability_checker.check_availability(check_in, check_out)

        nights = (check_out - check_in).days

        return JsonResponse({
            'available': is_available,
            'message': message,
            'dates': {
                'check_in': check_in_str,
                'check_out': check_out_str,
                'nights': nights
            }
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Errore interno: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def calculate_price(request, listing_id):
    """
    Calcola prezzo totale per un periodo specifico.

    POST /api/listings/{listing_id}/calculate-price/

    Body (JSON):
        {
            "check_in": "2025-01-15",
            "check_out": "2025-01-18",
            "num_guests": 3
        }

    Response:
        {
            "nights": 3,
            "nightly_prices": [100.00, 120.00, 100.00],
            "subtotal": 320.00,
            "cleaning_fee": 50.00,
            "extra_guest_fee": 30.00,
            "total": 400.00,
            "breakdown_by_night": {
                "2025-01-15": {"price": 100.00, "is_custom": false},
                "2025-01-16": {"price": 120.00, "is_custom": true},
                "2025-01-17": {"price": 100.00, "is_custom": false}
            },
            "price_per_night_avg": 106.67
        }
    """
    try:
        listing = get_object_or_404(Listing, pk=listing_id, status='active')

        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON non valido'
            }, status=400)

        check_in_str = data.get('check_in')
        check_out_str = data.get('check_out')
        num_guests = data.get('num_guests', 1)

        if not check_in_str or not check_out_str:
            return JsonResponse({
                'error': 'Parametri check_in e check_out richiesti'
            }, status=400)

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            num_guests = int(num_guests)
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'Formato parametri non valido'
            }, status=400)

        # Calcola prezzo
        price_calculator = PriceCalculator(listing)
        try:
            pricing_data = price_calculator.calculate_total(check_in, check_out, num_guests)
            return JsonResponse(pricing_data)
        except ValueError as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'error': f'Errore interno: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def listing_info(request, listing_id):
    """
    Restituisce informazioni base del listing per il calendario.

    GET /api/listings/{listing_id}/info/

    Response:
        {
            "id": 1,
            "title": "Appartamento Centro",
            "slug": "appartamento-centro",
            "description": "...",
            "base_price": 100.00,
            "cleaning_fee": 50.00,
            "max_guests": 4,
            "included_guests": 2,
            "extra_guest_fee": 15.00,
            "min_stay_nights": 2,
            "gap_between_bookings": 1,
            "checkin_from": "15:00",
            "checkin_to": "20:00",
            "checkout_time": "10:00",
            "main_image": "https://...",
            "city": "Roma",
            "zone": "Centro Storico"
        }
    """
    try:
        listing = get_object_or_404(Listing, pk=listing_id, status='active')

        return JsonResponse({
            'id': listing.id,
            'title': listing.title,
            'slug': listing.slug,
            'description': listing.description,
            'base_price': float(listing.base_price),
            'cleaning_fee': float(listing.cleaning_fee),
            'max_guests': listing.max_guests,
            'included_guests': listing.included_guests,
            'extra_guest_fee': float(listing.extra_guest_fee),
            'min_stay_nights': listing.min_stay_nights,
            'gap_between_bookings': listing.gap_between_bookings,
            'checkin_from': listing.checkin_from.strftime('%H:%M'),
            'checkin_to': listing.checkin_to.strftime('%H:%M'),
            'checkout_time': listing.checkout_time.strftime('%H:%M'),
            'main_image': listing.main_image.image.url if listing.main_image else None,
            'city': listing.city,
            'zone': listing.zone,
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Errore interno: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def combined_calendar_data(request):
    """
    Restituisce dati calendario combinato per tutti i gruppi attivi.
    Mostra disponibilità aggregata: una data è disponibile solo se
    TUTTI gli appartamenti di TUTTI i gruppi sono disponibili.

    GET /api/calendar/combined/?start=2025-01-01&end=2025-03-31

    Query Parameters:
        start: Data inizio (formato: YYYY-MM-DD)
        end: Data fine (formato: YYYY-MM-DD)

    Response:
        {
            "blocked_dates": ["2025-01-15", ...],  // Date in cui almeno 1 appartamento è bloccato
            "checkin_disabled": ["2025-01-20", ...],  // Date in cui almeno 1 appartamento non permette check-in
            "checkout_disabled": ["2025-01-22", ...],  // Date in cui almeno 1 appartamento non permette check-out
            "prices": {
                "2025-01-15": 250.00,  // Somma prezzi di tutti gli appartamenti
                ...
            },
            "min_stay": 3,  // Il massimo tra tutti i min_stay degli appartamenti
            "gap_days": 2,  // Il massimo tra tutti i gap degli appartamenti
            "groups": [
                {
                    "id": 1,
                    "name": "Appartamenti Centro",
                    "total_capacity": 8,
                    "listings": [...]
                }
            ]
        }
    """
    try:
        from listings.models import ListingGroup

        # Parse date parameters
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')

        if not start_str or not end_str:
            return JsonResponse({
                'error': 'Parametri start e end richiesti'
            }, status=400)

        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'error': 'Formato date non valido. Usa YYYY-MM-DD'
            }, status=400)

        if start_date >= end_date:
            return JsonResponse({
                'error': 'La data di fine deve essere successiva alla data di inizio'
            }, status=400)

        # Limita range massimo a 1 anno
        max_days = 365
        if (end_date - start_date).days > max_days:
            return JsonResponse({
                'error': f'Range massimo: {max_days} giorni'
            }, status=400)

        # Ottieni tutti i gruppi attivi
        groups = ListingGroup.objects.filter(is_active=True).prefetch_related('listings')

        if not groups.exists():
            return JsonResponse({
                'error': 'Nessun gruppo di appartamenti attivo'
            }, status=404)

        # Raccogli tutti gli appartamenti da TUTTI i gruppi
        all_listings = set()
        for group in groups:
            for listing in group.listings.filter(status='active'):
                all_listings.add(listing)

        if not all_listings:
            return JsonResponse({
                'error': 'Nessun appartamento attivo nei gruppi'
            }, status=404)

        # Inizializza strutture dati per aggregazione
        blocked_dates_sets = []  # Include tutte le date bloccate (gap, prenotazioni, chiusure)
        prices_per_listing = []
        min_stays = []
        gap_days_list = []

        # Per ogni appartamento, ottieni i suoi dati
        for listing in all_listings:
            # Ottieni dati completi di disponibilità (include gap rules, bookings, closures)
            availability_checker = AvailabilityChecker(listing)
            availability_data = availability_checker.get_calendar_data(start_date, end_date)

            # Aggrega tutte le date bloccate (include gap rules, prenotazioni, chiusure)
            blocked_dates_sets.append(set(availability_data['blocked_dates']))

            min_stays.append(availability_data['min_stay'])
            gap_days_list.append(availability_data['gap_days'])

            # Ottieni prezzi
            price_calculator = PriceCalculator(listing)
            listing_prices = price_calculator.get_calendar_prices(start_date, end_date)
            prices_per_listing.append(listing_prices)

        # Aggrega: include gap rules, prenotazioni, chiusure (UNION = se QUALSIASI è bloccato)
        aggregated_blocked = set.union(*blocked_dates_sets) if blocked_dates_sets else set()
        # In modalità combinata, non usiamo checkin/checkout disabled
        aggregated_checkin_disabled = set()
        aggregated_checkout_disabled = set()

        # Somma prezzi: nascondi prezzi per date bloccate
        aggregated_prices = {}
        current_date = start_date
        while current_date < end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            # Mostra prezzi solo per date disponibili (non bloccate)
            if date_str not in aggregated_blocked:
                total_price = sum(
                    prices.get(date_str, 0)
                    for prices in prices_per_listing
                )
                if total_price > 0:
                    aggregated_prices[date_str] = float(total_price)

            current_date += timedelta(days=1)

        # Usa il min_stay e gap più restrittivo (il massimo)
        max_min_stay = max(min_stays) if min_stays else 1
        max_gap_days = max(gap_days_list) if gap_days_list else 0

        # Serializza informazioni gruppi
        groups_data = []
        for group in groups:
            group_listings = group.listings.filter(status='active')
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'total_capacity': group.total_capacity,
                'total_bedrooms': group.total_bedrooms,
                'listing_count': group_listings.count(),
                'listings': [
                    {
                        'id': listing.id,
                        'title': listing.title,
                        'slug': listing.slug,
                        'max_guests': listing.max_guests,
                        'bedrooms': listing.bedrooms,
                        'base_price': float(listing.base_price),
                        'cleaning_fee': float(listing.cleaning_fee),
                    }
                    for listing in group_listings
                ]
            })

        response_data = {
            'blocked_dates': sorted(list(aggregated_blocked)),
            'checkin_disabled': sorted(list(aggregated_checkin_disabled)),
            'checkout_disabled': sorted(list(aggregated_checkout_disabled)),
            'prices': aggregated_prices,
            'min_stay': max_min_stay,
            'gap_days': max_gap_days,
            'groups': groups_data,
            'total_listings': len(all_listings),
        }

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Errore interno: {str(e)}'
        }, status=500)
