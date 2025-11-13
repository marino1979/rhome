from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json

from listings.models import Listing
from calendar_rules.models import ClosureRule, PriceRule
from .models import Booking, BookingPayment, MultiBooking, Message


def listing_detail_with_booking(request, slug):
    """Vista dettaglio annuncio con form prenotazione"""
    listing = get_object_or_404(Listing, slug=slug, status='active')

    context = {
        'listing': listing,
        'amenities': listing.amenities.all(),
        'main_image': listing.main_image,
        'other_images': listing.other_images,
        'beds_summary': listing.count_beds_by_type(),
    }

    return render(request, 'bookings/listing_detail.html', context)


def check_availability(request):
    """API endpoint per verificare disponibilità"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)

    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(data.get('check_out'), '%Y-%m-%d').date()
        num_guests = int(data.get('num_guests', 1))

        listing = get_object_or_404(Listing, id=listing_id)

        # Validazioni base
        if check_in >= check_out:
            return JsonResponse({'error': 'Date non valide'}, status=400)

        if check_in < timezone.now().date():
            return JsonResponse({'error': 'Non puoi prenotare date passate'}, status=400)

        if num_guests > listing.max_guests:
            return JsonResponse({'error': f'Massimo {listing.max_guests} ospiti'}, status=400)

        # Usa CalendarManager per verifica completa
        from calendar_rules.managers import CalendarManager
        calendar = CalendarManager(listing)

        # Verifica disponibilità completa
        is_available, message = calendar.check_availability(check_in, check_out)
        if not is_available:
            return JsonResponse({'available': False, 'error': message})

        # Verifica conflitti prenotazioni
        conflicting_bookings = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )

        if conflicting_bookings.exists():
            return JsonResponse({'available': False, 'error': 'Date già prenotate'})

        # Calcola prezzi usando CalendarManager
        try:
            total_price = calendar.calculate_total_price(check_in, check_out, num_guests)
            total_nights = (check_out - check_in).days

            # Calcola breakdown dettagliato
            daily_prices = []
            subtotal = 0
            for i in range(total_nights):
                day_date = check_in + timedelta(days=i)
                day_price = calendar.get_price_per_day(day_date)
                daily_prices.append({
                    'date': day_date.isoformat(),
                    'price': float(day_price)
                })
                subtotal += day_price

            # Ospiti extra
            extra_guest_fee = 0
            if num_guests > listing.included_guests:
                extra_guests = num_guests - listing.included_guests
                extra_guest_fee = extra_guests * listing.extra_guest_fee * total_nights

            return JsonResponse({
                'available': True,
                'pricing': {
                    'base_price_per_night': float(subtotal / total_nights),
                    'total_nights': total_nights,
                    'subtotal': float(subtotal),
                    'cleaning_fee': float(listing.cleaning_fee),
                    'extra_guest_fee': float(extra_guest_fee),
                    'total_amount': float(total_price),
                    'daily_prices': daily_prices  # Nuovo: prezzi giornalieri dettagliati
                }
            })

        except ValueError as e:
            return JsonResponse({'available': False, 'error': str(e)})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_price_for_period(listing, check_in, check_out):
    """Ottiene il prezzo per un periodo specifico"""
    price_rules = PriceRule.objects.filter(
        listing=listing,
        start_date__lte=check_in,
        end_date__gte=check_out
    ).order_by('-start_date')

    if price_rules.exists():
        return price_rules.first().price

    return listing.base_price


@login_required
def create_booking(request):
    """Crea una nuova prenotazione"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)

    try:
        with transaction.atomic():
            data = json.loads(request.body)
            listing_id = data.get('listing_id')
            check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d').date()
            check_out = datetime.strptime(data.get('check_out'), '%Y-%m-%d').date()
            num_guests = int(data.get('num_guests', 1))
            num_adults = int(data.get('num_adults', num_guests))
            num_children = int(data.get('num_children', 0))

            listing = get_object_or_404(Listing, id=listing_id)

            # Crea prenotazione
            booking = Booking(
                listing=listing,
                guest=request.user,
                check_in_date=check_in,
                check_out_date=check_out,
                num_guests=num_guests,
                num_adults=num_adults,
                num_children=num_children,
                special_requests=data.get('special_requests', ''),
                guest_phone=data.get('guest_phone', ''),
                guest_email=data.get('guest_email', request.user.email)
            )

            # Validazione e calcolo prezzi automatici
            booking.full_clean()
            booking.save()

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'message': 'Prenotazione creata con successo'
            })

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Errore nella creazione della prenotazione'}, status=500)


@login_required
def booking_detail(request, booking_id):
    """Vista dettaglio prenotazione"""
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        guest=request.user
    )

    payments = booking.payments.all()

    context = {
        'booking': booking,
        'payments': payments,
        'can_cancel': booking.status in ['pending', 'confirmed'] and
                     booking.check_in_date > timezone.now().date() + timedelta(days=1)
    }

    return render(request, 'bookings/booking_detail.html', context)


@login_required
def booking_list(request):
    """Lista prenotazioni utente"""
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')

    context = {
        'bookings': bookings
    }

    return render(request, 'bookings/booking_list.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancella prenotazione"""
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        guest=request.user
    )

    if booking.status not in ['pending', 'confirmed']:
        messages.error(request, 'Non puoi cancellare questa prenotazione')
        return redirect('booking_detail', booking_id=booking_id)

    if booking.check_in_date <= timezone.now().date() + timedelta(days=1):
        messages.error(request, 'Troppo tardi per cancellare')
        return redirect('booking_detail', booking_id=booking_id)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Prenotazione cancellata')
        return redirect('booking_list')

    return render(request, 'bookings/cancel_booking.html', {'booking': booking})


def get_listing_calendar(request, listing_id):
    """API per ottenere calendario disponibilità"""
    listing = get_object_or_404(Listing, id=listing_id)

    # Ottieni date occupate
    bookings = Booking.objects.filter(
        listing=listing,
        status__in=['confirmed', 'pending']
    ).values('check_in_date', 'check_out_date')

    # Ottieni chiusure
    closures = ClosureRule.objects.filter(
        listing=listing
    ).values('start_date', 'end_date', 'reason')

    # Ottieni regole prezzi
    price_rules = PriceRule.objects.filter(
        listing=listing
    ).values('start_date', 'end_date', 'price')

    occupied_dates = []
    for booking in bookings:
        current_date = booking['check_in_date']
        while current_date < booking['check_out_date']:
            occupied_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)

    closed_dates = []
    for closure in closures:
        current_date = closure['start_date']
        while current_date <= closure['end_date']:
            closed_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)

    return JsonResponse({
        'occupied_dates': occupied_dates,
        'closed_dates': closed_dates,
        'price_rules': list(price_rules),
        'base_price': float(listing.base_price)
    })


def get_listing_calendar_by_slug(request, slug):
    """API per ottenere calendario disponibilità tramite slug"""
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # Usa CalendarManager per ottenere dati completi
    from calendar_rules.managers import CalendarManager
    calendar = CalendarManager(listing)
    
    # Ottieni dati per i prossimi 12 mesi
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=365)
    
    try:
        calendar_data = calendar.get_calendar_data(start_date, end_date)
        
        return JsonResponse({
            'success': True,
            'listing_id': listing.id,
            'listing_slug': listing.slug,
            'listing_title': listing.title,
            'base_price': float(listing.base_price),
            'max_guests': listing.max_guests,
            'min_stay': listing.min_stay or 1,
            'max_stay': listing.max_stay or 30,
            'gap_between_bookings': listing.gap_between_bookings or 0,
            'calendar_data': calendar_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'listing_id': listing.id,
            'listing_slug': listing.slug
        }, status=500)


def quick_availability_check(request):
    """API endpoint ottimizzato per verifica rapida disponibilità"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)

    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(data.get('check_out'), '%Y-%m-%d').date()
        num_guests = int(data.get('num_guests', 1))

        # Validazioni rapide
        if check_in >= check_out:
            return JsonResponse({'available': False, 'error': 'Date non valide'})

        if check_in < timezone.now().date():
            return JsonResponse({'available': False, 'error': 'Non puoi prenotare date passate'})

        listing = get_object_or_404(Listing, id=listing_id)
        
        if num_guests > listing.max_guests:
            return JsonResponse({'available': False, 'error': f'Massimo {listing.max_guests} ospiti'})

        # Verifica rapida conflitti prenotazioni (query ottimizzata)
        has_conflicts = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        ).exists()

        if has_conflicts:
            return JsonResponse({'available': False, 'error': 'Date già prenotate'})

        # Calcolo prezzo rapido
        nights = (check_out - check_in).days
        base_price = float(listing.base_price * nights)
        cleaning_fee = float(listing.cleaning_fee)
        
        extra_guest_fee = 0
        if num_guests > listing.included_guests:
            extra_guests = num_guests - listing.included_guests
            extra_guest_fee = float(extra_guests * listing.extra_guest_fee * nights)

        total_amount = base_price + cleaning_fee + extra_guest_fee

        return JsonResponse({
            'available': True,
            'pricing': {
                'base_price_per_night': float(listing.base_price),
                'total_nights': nights,
                'subtotal': base_price,
                'cleaning_fee': cleaning_fee,
                'extra_guest_fee': extra_guest_fee,
                'total_amount': total_amount
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON non valido'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Valore non valido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Errore interno: {str(e)}'}, status=500)


def find_combined_availability(check_in_date, check_out_date, total_guests):
    """
    Trova le combinazioni disponibili di appartamenti per ospitare il numero totale di ospiti
    Usa solo i gruppi di appartamenti definiti dall'host
    """
    from itertools import combinations, chain
    from calendar_rules.managers import CalendarManager
    from decimal import Decimal
    from listings.models import ListingGroup
    
    # Ottieni tutti i gruppi attivi di appartamenti
    groups = ListingGroup.objects.filter(is_active=True).prefetch_related('listings')
    
    all_combinations = []
    
    # Per ogni gruppo, trova le combinazioni valide (evitando duplicati)
    for group in groups:
        group_listings = list(group.listings.filter(status='active'))
        
        if not group_listings:
            continue
            
        # Ordina gli appartamenti per capacità (dal più piccolo al più grande)
        group_listings.sort(key=lambda x: x.max_guests)
        
        # Trova la combinazione ottimale per questo gruppo
        best_combo = None
        
        # Se il gruppo ha più di 1 appartamento, preferisci combinazioni multiple
        if len(group_listings) > 1:
            # Per gruppi con 3+ appartamenti, usa sempre tutti gli appartamenti
            if len(group_listings) >= 3:
                total_capacity = sum(l.max_guests for l in group_listings)
                if total_capacity >= total_guests:
                    best_combo = {
                        'combo': group_listings,
                        'group': group,
                        'type': 'all'
                    }
            else:
                # Per gruppi con 2 appartamenti, usa entrambi
                total_capacity = sum(l.max_guests for l in group_listings)
                if total_capacity >= total_guests:
                    best_combo = {
                        'combo': group_listings,
                        'group': group,
                        'type': 'double'
                    }
        else:
            # Se il gruppo ha solo 1 appartamento, usa quello
            if group_listings[0].max_guests >= total_guests:
                best_combo = {
                    'combo': [group_listings[0]],
                    'group': group,
                    'type': 'single'
                }
        
        
        # Aggiungi la migliore combinazione trovata per questo gruppo
        if best_combo is not None:
            all_combinations.append(best_combo)
    
    # Verifica disponibilità per ogni combinazione
    available_combinations = []
    
    for combo_info in all_combinations:
        combo = combo_info['combo']
        group = combo_info['group']
        combo_type = combo_info['type']
        
        combination_available = True
        total_price = Decimal('0.00')
        total_cleaning_fee = Decimal('0.00')
        combo_details = []
        
        for listing in combo:
            # Verifica disponibilità usando CalendarManager
            calendar = CalendarManager(listing)
            is_available, message = calendar.check_availability(check_in_date, check_out_date)
            
            if not is_available:
                combination_available = False
                break
            
            # Calcola prezzo per questo appartamento
            try:
                nights = (check_out_date - check_in_date).days
                
                # Calcola ospiti per questo appartamento (distribuzione ottimale)
                if len(combo) == 1:
                    # Solo un appartamento
                    guests_for_listing = total_guests
                else:
                    # Distribuzione ottimale: riempie gli appartamenti in ordine di capacità
                    listing_index = combo.index(listing)
                    
                    if listing_index == 0:
                        # Primo appartamento: prende il massimo possibile
                        guests_for_listing = min(listing.max_guests, total_guests)
                    else:
                        # Calcola ospiti già assegnati agli appartamenti precedenti
                        guests_already_assigned = 0
                        for i in range(listing_index):
                            prev_listing = combo[i]
                            prev_guests = min(prev_listing.max_guests, total_guests - guests_already_assigned)
                            guests_already_assigned += prev_guests
                        
                        # Assegna gli ospiti rimanenti
                        remaining_guests = total_guests - guests_already_assigned
                        guests_for_listing = min(listing.max_guests, max(1, remaining_guests))
                        
                        # Se non ci sono abbastanza ospiti per questo appartamento, salta la combinazione
                        if remaining_guests <= 0:
                            combination_available = False
                            break
                
                # Calcola prezzo usando CalendarManager
                listing_price = calendar.calculate_total_price(
                    check_in_date, 
                    check_out_date, 
                    guests_for_listing
                )
                
                # Calcola ospiti extra
                extra_guests = max(0, guests_for_listing - listing.included_guests)
                extra_guest_fee = extra_guests * listing.extra_guest_fee * nights
                
                # Il prezzo totale include il prezzo base + ospiti extra
                listing_total_price = Decimal(str(listing_price)) + Decimal(str(extra_guest_fee))
                
                total_price += listing_total_price
                total_cleaning_fee += listing.cleaning_fee
                
                combo_details.append({
                    'listing': {
                        'id': listing.id,
                        'title': listing.title,
                        'max_guests': listing.max_guests,
                        'bedrooms': listing.bedrooms,
                        'base_price': float(listing.base_price),
                        'cleaning_fee': float(listing.cleaning_fee),
                        'included_guests': listing.included_guests,
                        'extra_guest_fee': float(listing.extra_guest_fee)
                    },
                    'guests': guests_for_listing,
                    'extra_guests': extra_guests,
                    'price': float(listing_total_price),
                    'nights': nights
                })
                
            except Exception as e:
                combination_available = False
                break
        
        if combination_available:
            # Calcola totali combinati
            total_bedrooms = sum(l.bedrooms for l in combo)
            total_bathrooms = sum(1 for l in combo)  # Ogni appartamento ha 1 bagno
            
            # Genera nome della combinazione basato sul gruppo
            if combo_type == 'single':
                combo_name = f"{group.name} - {combo[0].title}"
            elif combo_type == 'double':
                combo_name = f"{group.name} - {combo[0].title} + {combo[1].title}"
            else:  # all
                combo_name = f"{group.name} - Tutti gli Appartamenti"
            
            available_combinations.append({
                'combination': combo_details,
                'group_name': group.name,
                'combo_name': combo_name,
                'combo_type': combo_type,
                'total_guests': total_guests,
                'total_price': float(total_price),
                'total_cleaning_fee': float(total_cleaning_fee),
                'total_bedrooms': total_bedrooms,
                'total_bathrooms': total_bathrooms,
                'nights': nights,
                'price_per_night': float(total_price / nights) if nights > 0 else 0,
                'savings': None  # Calcoleremo risparmi se necessario
            })
    
    return available_combinations


@csrf_exempt
def combined_availability(request):
    """API endpoint per ricerca disponibilità combinata"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non supportato'}, status=405)
    
    try:
        data = json.loads(request.body)
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        total_guests = int(data['total_guests'])
        
        # Validazioni base
        if check_in >= check_out:
            return JsonResponse({'error': 'Data check-out deve essere successiva al check-in'}, status=400)
        
        if check_in < timezone.now().date():
            return JsonResponse({'error': 'Non è possibile prenotare date passate'}, status=400)
        
        if total_guests < 1 or total_guests > 10:
            return JsonResponse({'error': 'Numero ospiti non valido'}, status=400)
        
        # Trova combinazioni disponibili
        combinations = find_combined_availability(check_in, check_out, total_guests)
        
        return JsonResponse({
            'success': True,
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'total_guests': total_guests,
            'nights': (check_out - check_in).days,
            'combinations': combinations,
            'total_combinations': len(combinations)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON non valido'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Campo mancante: {str(e)}'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Valore non valido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Errore interno: {str(e)}'}, status=500)


@csrf_exempt
def create_combined_booking(request):
    """API endpoint per creare una prenotazione combinata"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non supportato'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Verifica che l'utente sia autenticato
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Autenticazione richiesta'}, status=401)
        
        # Estrai dati dalla richiesta
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        total_guests = int(data['total_guests'])
        combination_data = data['combination']
        
        # Validazioni
        if check_in >= check_out:
            return JsonResponse({'error': 'Data check-out deve essere successiva al check-in'}, status=400)
        
        if check_in < timezone.now().date():
            return JsonResponse({'error': 'Non è possibile prenotare date passate'}, status=400)
        
        if not combination_data or len(combination_data) == 0:
            return JsonResponse({'error': 'Combinazione non valida'}, status=400)
        
        # Verifica disponibilità una volta di più prima di creare le prenotazioni
        combinations = find_combined_availability(check_in, check_out, total_guests)
        if not combinations:
            return JsonResponse({'error': 'Nessuna combinazione disponibile per queste date'}, status=400)
        
        # Trova la combinazione corrispondente
        selected_combination = None
        for combo in combinations:
            if len(combo['combination']) == len(combination_data):
                # Verifica che corrisponda
                combo_listing_ids = [item['listing']['id'] for item in combo['combination']]
                data_listing_ids = [item['listing_id'] for item in combination_data]
                if set(combo_listing_ids) == set(data_listing_ids):
                    selected_combination = combo
                    break
        
        if not selected_combination:
            return JsonResponse({'error': 'Combinazione non trovata o non più disponibile'}, status=400)
        
        # Crea la prenotazione combinata
        with transaction.atomic():
            # Crea MultiBooking
            multi_booking = MultiBooking.objects.create(
                guest=request.user,
                check_in_date=check_in,
                check_out_date=check_out,
                total_guests=total_guests,
                special_requests=data.get('special_requests', ''),
                guest_phone=data.get('guest_phone', ''),
                guest_email=data.get('guest_email', ''),
                status='pending'
            )
            
            # Crea i booking individuali
            individual_bookings = []
            for combo_item in selected_combination['combination']:
                listing = Listing.objects.get(id=combo_item['listing']['id'])
                guests_for_listing = combo_item['guests']
                
                # Crea booking individuale
                booking = Booking.objects.create(
                    listing=listing,
                    guest=request.user,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    num_guests=guests_for_listing,
                    num_adults=guests_for_listing,  # Semplificazione
                    num_children=0,
                    special_requests=data.get('special_requests', ''),
                    guest_phone=data.get('guest_phone', ''),
                    guest_email=data.get('guest_email', ''),
                    multi_booking=multi_booking,
                    status='pending'
                )
                
                individual_bookings.append(booking)
            
            # Aggiorna i prezzi totali della MultiBooking
            multi_booking.calculate_total_pricing()
            multi_booking.save()
        
        return JsonResponse({
            'success': True,
            'multi_booking_id': multi_booking.id,
            'message': 'Prenotazione combinata creata con successo',
            'individual_bookings': [
                {
                    'id': booking.id,
                    'listing': booking.listing.title,
                    'guests': booking.num_guests
                }
                for booking in individual_bookings
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON non valido'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Campo mancante: {str(e)}'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Valore non valido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Errore interno: {str(e)}'}, status=500)


@login_required
def booking_messages(request, booking_id):
    """Vista per visualizzare e inviare messaggi per una prenotazione"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Verifica che l'utente sia il guest o l'host
    is_guest = booking.guest == request.user
    # Per ora assumiamo che l'host sia qualsiasi utente che non è il guest
    # In futuro potresti aggiungere un campo owner al Listing
    is_host = not is_guest
    
    if not (is_guest or is_host):
        messages.error(request, 'Non hai accesso a questa conversazione')
        return redirect('account:dashboard')
    
    # Determina l'altra parte della conversazione
    if is_guest:
        # Guest sta parlando con l'host (per ora qualsiasi altro utente)
        # In futuro: other_party = booking.listing.owner
        other_party = None  # Sarà gestito diversamente
    else:
        other_party = booking.guest
    
    # Ottieni tutti i messaggi per questa prenotazione
    message_list = Message.objects.filter(booking=booking).order_by('created_at')
    
    # Marca i messaggi ricevuti come letti
    Message.objects.filter(
        booking=booking,
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    context = {
        'booking': booking,
        'messages': message_list,
        'is_guest': is_guest,
        'other_party': other_party
    }
    
    return render(request, 'bookings/booking_messages.html', context)


@login_required
def send_message(request, booking_id):
    """API endpoint per inviare un messaggio"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verifica che l'utente sia il guest o l'host
        is_guest = booking.guest == request.user
        is_host = not is_guest
        
        if not (is_guest or is_host):
            return JsonResponse({'error': 'Non hai accesso a questa conversazione'}, status=403)
        
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'error': 'Il messaggio non può essere vuoto'}, status=400)
        
        # Determina il destinatario
        if is_guest:
            # Guest invia all'host - per ora usiamo il primo admin o superuser
            # In futuro: recipient = booking.listing.owner
            from django.contrib.auth.models import User
            recipient = User.objects.filter(is_superuser=True).first()
            if not recipient:
                recipient = User.objects.filter(is_staff=True).first()
            if not recipient:
                return JsonResponse({'error': 'Host non trovato'}, status=400)
        else:
            # Host invia al guest
            recipient = booking.guest
        
        # Crea il messaggio
        message = Message.objects.create(
            booking=booking,
            sender=request.user,
            recipient=recipient,
            message=message_text
        )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'created_at': message.created_at.isoformat(),
            'sender_name': message.sender.get_full_name() or message.sender.username
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON non valido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def mark_messages_read(request, booking_id):
    """API endpoint per marcare i messaggi come letti"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verifica che l'utente sia il guest o l'host
        is_guest = booking.guest == request.user
        is_host = not is_guest
        
        if not (is_guest or is_host):
            return JsonResponse({'error': 'Non hai accesso a questa conversazione'}, status=403)
        
        # Marca i messaggi come letti
        updated = Message.objects.filter(
            booking=booking,
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'success': True,
            'updated_count': updated
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)