"""
Viste per il debug dettagliato del calendario.
Questo modulo fornisce endpoint API per visualizzare tutte le informazioni
di debug del calendario direttamente nel browser.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404, render
from datetime import date, timedelta
import json

from listings.models import Listing
from calendar_rules.services.calendar_service import CalendarService


@method_decorator(csrf_exempt, name='dispatch')
class CalendarDebugView(View):
    """
    Vista per il debug dettagliato del calendario.
    Mostra tutte le informazioni di debug in formato JSON per il browser.
    """
    
    def get(self, request, listing_id):
        """GET /api/calendar-debug/{listing_id}/"""
        try:
            # Ottieni il listing
            listing = get_object_or_404(Listing, id=listing_id)
            
            # Parametri opzionali dalla query string
            days = int(request.GET.get('days', 60))
            start_date_str = request.GET.get('start_date')
            
            if start_date_str:
                try:
                    start_date = date.fromisoformat(start_date_str)
                except ValueError:
                    return JsonResponse({'error': 'Formato data non valido. Usa YYYY-MM-DD'}, status=400)
            else:
                start_date = date.today()
            
            end_date = start_date + timedelta(days=days)
            
            # Crea il servizio calendario
            calendar_service = CalendarService(listing)
            
            # Usa il metodo principale per ottenere la nuova struttura
            calendar_result = calendar_service.get_unavailable_dates(start_date, end_date)
            
            # Ottieni anche i dati raw per l'analisi dettagliata
            calendar_data = calendar_service._get_optimized_calendar_data(start_date, end_date)
            
            # Prepara la response dettagliata
            debug_info = {
                'listing_info': {
                    'id': listing.id,
                    'title': listing.title,
                    'gap_between_bookings': listing.gap_between_bookings or 0,
                },
                'period_info': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_days': days,
                },
                'raw_data': {
                    'bookings': calendar_data['bookings'],
                    'closures': calendar_data['closures'],
                    'checkinout_rules': [
                        {
                            'id': rule.id,
                            'rule_type': rule.rule_type,
                            'recurrence_type': rule.recurrence_type,
                            'specific_date': rule.specific_date.isoformat() if rule.specific_date else None,
                            'day_of_week': rule.day_of_week,
                            'description': f"{'NO CHECK-IN' if rule.rule_type == 'no_checkin' else 'NO CHECK-OUT'} {'il ' + str(rule.specific_date) if rule.specific_date else 'ogni ' + ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'][rule.day_of_week] if rule.day_of_week is not None else 'N/A'}"
                        }
                        for rule in calendar_data['checkinout_rules']
                    ],
                    'price_rules': calendar_data['price_rules'],
                },
                'detailed_analysis': {
                    'bookings_analysis': self._analyze_bookings(calendar_data['bookings'], start_date, end_date, listing.gap_between_bookings or 0, calendar_data.get('min_nights', 1)),
                    'gap_days_analysis': self._analyze_gap_days(calendar_data['bookings'], start_date, end_date, listing.gap_between_bookings or 0),
                    'rules_analysis': self._analyze_rules(calendar_data['checkinout_rules'], start_date, end_date),
                },
                'results': {
                    # Nuova struttura separata
                    'blocked_ranges': [
                        {
                            'from': r['from'],
                            'to': r['to'],
                            'reason': 'Giorni occupati da prenotazioni esistenti'
                        }
                        for r in calendar_result['blocked_ranges']
                    ],
                    'checkin_dates': [
                        {
                            'date': d,
                            'reason': 'Data di arrivo (check-in) di una prenotazione'
                        }
                        for d in calendar_result['checkin_dates']
                    ],
                    'checkout_dates': [
                        {
                            'date': d,
                            'reason': 'Data di partenza (check-out) di una prenotazione'
                        }
                        for d in calendar_result['checkout_dates']
                    ],
                    'gap_days': [
                        {
                            'date': d,
                            'reason': 'Giorno di gap (pulizia/preparazione) tra prenotazioni'
                        }
                        for d in calendar_result['gap_days']
                    ],
                    'checkin_blocked_rules': {
                        'dates': [
                            {
                                'date': d,
                                'reason': 'Check-in bloccato da regola specifica'
                            }
                            for d in calendar_result['checkin_blocked_rules']['dates']
                        ],
                        'weekdays': calendar_result['checkin_blocked_rules']['weekdays'],
                        'weekdays_names': [['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'][wd] for wd in calendar_result['checkin_blocked_rules']['weekdays']]
                    },
                    'checkout_blocked_rules': {
                        'dates': [
                            {
                                'date': d,
                                'reason': 'Check-out bloccato da regola specifica'
                            }
                            for d in calendar_result['checkout_blocked_rules']['dates']
                        ],
                        'weekdays': calendar_result['checkout_blocked_rules']['weekdays'],
                        'weekdays_names': [['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'][wd] for wd in calendar_result['checkout_blocked_rules']['weekdays']]
                    },
                    'checkin_blocked_gap': [
                        {
                            'date': d,
                            'reason': 'Check-in bloccato da gap days + durata minima soggiorno'
                        }
                        for d in calendar_result['checkin_blocked_gap']
                    ],
                },
                'summary': {
                    'total_blocked_ranges': len(calendar_result['blocked_ranges']),
                    'total_checkin_dates': len(calendar_result['checkin_dates']),
                    'total_checkout_dates': len(calendar_result['checkout_dates']),
                    'total_gap_days': len(calendar_result['gap_days']),
                    'total_checkin_blocked_rules': len(calendar_result['checkin_blocked_rules']['dates']),
                    'total_checkout_blocked_rules': len(calendar_result['checkout_blocked_rules']['dates']),
                    'total_checkin_blocked_gap': len(calendar_result['checkin_blocked_gap']),
                    'gap_between_bookings': listing.gap_between_bookings or 0,
                    'min_stay': calendar_result['metadata']['min_stay'],
                }
            }
            
            return JsonResponse(debug_info, json_dumps_params={'indent': 2})
            
        except Exception as e:
            return JsonResponse({
                'error': f'Errore durante il debug: {str(e)}',
                'type': type(e).__name__
            }, status=500)
    
    def _analyze_bookings(self, bookings, start_date, end_date, gap_days, min_nights=1):
        """Analizza le prenotazioni e i loro effetti."""
        analysis = []
        
        for i, booking in enumerate(bookings, 1):
            check_in = booking['check_in_date']
            check_out = booking['check_out_date']
            
            booking_info = {
                'booking_number': i,
                'check_in': check_in.isoformat() if check_in else None,
                'check_out': check_out.isoformat() if check_out else None,
                'duration_days': (check_out - check_in).days if check_in and check_out else 0,
                'blocks_interior_days': [],
                'blocks_gap_days_before': [],
                'blocks_gap_days_after': [],
                'blocks_checkin_date': [],
                'provides_turnover_day': None,
            }
            
            if check_in and check_out:
                
                # 1. GIORNI INTERNI DELLA PRENOTAZIONE (escludendo check-in e check-out)
                interior_start = max(check_in + timedelta(days=1), start_date)
                interior_end = min(check_out - timedelta(days=1), end_date)
                current_date = interior_start
                while current_date <= interior_end:
                    booking_info['blocks_interior_days'].append(current_date.isoformat())
                    current_date += timedelta(days=1)
                
                # 2. ULTIMO GIORNO UTILE PER CHECK-OUT DELLA PRENOTAZIONE PRECEDENTE
                last_checkout_day = check_in - timedelta(days=gap_days)
                if last_checkout_day >= start_date:
                    booking_info['blocks_gap_days_before'] = [last_checkout_day.isoformat()]
                
                # 3. ULTIMO GIORNO DISPONIBILE PER CHECK-IN PRECEDENTE
                # Deve essere min_nights giorni prima dell'ultimo check-out precedente
                last_checkin_day = last_checkout_day - timedelta(days=min_nights)
                if last_checkin_day >= start_date:
                    booking_info['blocks_checkin_date'] = [last_checkin_day.isoformat()]
                
                # Gap days dopo il check-out (manteniamo per compatibilità)
                if gap_days > 0:
                    gap_start = check_out + timedelta(days=1)
                    gap_end = min(check_out + timedelta(days=gap_days), end_date)
                    current_date = gap_start
                    while current_date <= gap_end:
                        booking_info['blocks_gap_days_after'].append(current_date.isoformat())
                        current_date += timedelta(days=1)
                
                # Check-in della prenotazione stessa NON è bloccato
                
                # Turnover day (check-out disponibile per nuovi check-in)
                if start_date <= check_out <= end_date:
                    booking_info['provides_turnover_day'] = check_out.isoformat()
            
            analysis.append(booking_info)
        
        return analysis
    
    def _analyze_gap_days(self, bookings, start_date, end_date, gap_days):
        """Analizza l'impatto dei gap days."""
        if gap_days == 0:
            return {
                'gap_days_configured': 0,
                'message': 'Nessun gap day configurato',
                'total_gap_days_blocked': 0,
                'gap_days_details': []
            }
        
        total_gap_days = 0
        gap_details = []
        
        for i, booking in enumerate(bookings, 1):
            check_in = booking['check_in_date']
            check_out = booking['check_out_date']
            
            if check_in and check_out:
                # Gap prima del check-in
                gap_before_start = max(check_in - timedelta(days=gap_days), start_date)
                gap_before_end = check_in - timedelta(days=1)
                gap_before_days = []
                
                if gap_before_start <= gap_before_end:
                    current_date = gap_before_start
                    while current_date <= gap_before_end:
                        gap_before_days.append(current_date.isoformat())
                        total_gap_days += 1
                        current_date += timedelta(days=1)
                
                # Gap dopo il check-out
                gap_after_start = check_out + timedelta(days=1)
                gap_after_end = min(check_out + timedelta(days=gap_days), end_date)
                gap_after_days = []
                
                if gap_after_start <= gap_after_end:
                    current_date = gap_after_start
                    while current_date <= gap_after_end:
                        gap_after_days.append(current_date.isoformat())
                        total_gap_days += 1
                        current_date += timedelta(days=1)
                
                gap_details.append({
                    'booking_number': i,
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'gap_days_before': gap_before_days,
                    'gap_days_after': gap_after_days,
                    'total_gap_days_for_booking': len(gap_before_days) + len(gap_after_days)
                })
        
        return {
            'gap_days_configured': gap_days,
            'total_gap_days_blocked': total_gap_days,
            'gap_days_details': gap_details,
            'message': f'Gap di {gap_days} giorni configurato. Totale giorni bloccati dai gap: {total_gap_days}'
        }
    
    def _analyze_rules(self, rules, start_date, end_date):
        """Analizza le regole di check-in/out."""
        analysis = {
            'checkin_rules': [],
            'checkout_rules': [],
            'total_checkin_blocks': 0,
            'total_checkout_blocks': 0
        }
        
        for rule in rules:
            rule_info = {
                'id': rule.id,
                'rule_type': rule.rule_type,
                'recurrence_type': rule.recurrence_type,
                'description': f"{'NO CHECK-IN' if rule.rule_type == 'no_checkin' else 'NO CHECK-OUT'}",
                'blocks_dates': [],
                'blocks_weekdays': []
            }
            
            if rule.rule_type == 'no_checkin':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        rule_info['blocks_dates'].append(rule.specific_date.isoformat())
                        analysis['total_checkin_blocks'] += 1
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    rule_info['blocks_weekdays'].append(rule.day_of_week)
                    # Conta i giovedì nel periodo (esempio)
                    if rule.day_of_week == 3:  # Giovedì
                        current_date = start_date
                        while current_date <= end_date:
                            if current_date.weekday() == rule.day_of_week:
                                analysis['total_checkin_blocks'] += 1
                            current_date += timedelta(days=1)
                
                analysis['checkin_rules'].append(rule_info)
            
            elif rule.rule_type == 'no_checkout':
                if rule.recurrence_type == 'specific_date' and rule.specific_date:
                    if start_date <= rule.specific_date <= end_date:
                        rule_info['blocks_dates'].append(rule.specific_date.isoformat())
                        analysis['total_checkout_blocks'] += 1
                elif rule.recurrence_type == 'weekly' and rule.day_of_week is not None:
                    rule_info['blocks_weekdays'].append(rule.day_of_week)
                    # Conta i giovedì nel periodo (esempio)
                    if rule.day_of_week == 3:  # Giovedì
                        current_date = start_date
                        while current_date <= end_date:
                            if current_date.weekday() == rule.day_of_week:
                                analysis['total_checkout_blocks'] += 1
                            current_date += timedelta(days=1)
                
                analysis['checkout_rules'].append(rule_info)
        
        return analysis


@method_decorator(csrf_exempt, name='dispatch')
class CalendarDebugPageView(View):
    """
    Vista per la pagina HTML del debug del calendario.
    """
    
    def get(self, request, listing_id):
        """GET /calendar-debug/{listing_id}/"""
        try:
            listing = get_object_or_404(Listing, id=listing_id)
            return render(request, 'calendar_debug.html', {
                'listing_id': listing_id,
                'listing_title': listing.title or f'Listing {listing_id}'
            })
        except Exception as e:
            return render(request, 'calendar_debug.html', {
                'error': f'Errore: {str(e)}'
            })
