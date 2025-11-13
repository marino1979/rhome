# calendar_rules/managers.py
from datetime import datetime, timedelta, date
from typing import Tuple, Dict, List
from decimal import Decimal

from .models import ClosureRule, CheckInOutRule, PriceRule
from .services import CalendarService, CalendarServiceError


class CalendarManager:
    """
    Classe per gestire la logica di disponibilità e prezzi.
    Integra il nuovo CalendarService per migliori performance e manutenibilità.
    """
    
    def __init__(self, listing):
        self.listing = listing
        self.calendar_service = CalendarService(listing)
    
    def check_availability(self, start_date, end_date) -> Tuple[bool, str]:
        """
        Verifica disponibilità per un periodo usando il nuovo CalendarService.
        
        Args:
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Tuple[bool, str]: (disponibile, messaggio)
        """
        try:
            # Usa il nuovo CalendarService per verificare disponibilità
            calendar_data = self.calendar_service.get_unavailable_dates(start_date, end_date)
            
            # Verifica se ci sono conflitti con il periodo richiesto
            from datetime import datetime
            
            # Converti le date in oggetti datetime per il confronto
            if isinstance(start_date, date):
                start_datetime = datetime.combine(start_date, datetime.min.time())
            else:
                start_datetime = start_date
                
            if isinstance(end_date, date):
                end_datetime = datetime.combine(end_date, datetime.min.time())
            else:
                end_datetime = end_date
            
            # Verifica se il periodo richiesto si sovrappone con range bloccati
            for blocked_range in calendar_data.get('blocked_ranges', []):
                blocked_start = datetime.fromisoformat(blocked_range['from'])
                blocked_end = datetime.fromisoformat(blocked_range['to'])
                
                # Se c'è sovrapposizione
                if start_datetime < blocked_end and end_datetime > blocked_start:
                    return False, "Periodo non disponibile per prenotazioni esistenti o regole di chiusura"
            
            # Verifica regole di check-in/out specifiche
            checkin_blocked_dates = calendar_data.get('checkin_block', {}).get('dates', [])
            checkout_blocked_dates = calendar_data.get('checkout_block', {}).get('dates', [])
            
            start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            
            if start_date_str in checkin_blocked_dates:
                return False, f"Check-in non consentito il {start_date_str}"
            
            if end_date_str in checkout_blocked_dates:
                return False, f"Check-out non consentito il {end_date_str}"
            
            return True, "Disponibile"
            
        except CalendarServiceError as e:
            return False, f"Errore nel controllo disponibilità: {str(e)}"
        except Exception as e:
            # Fallback alla logica originale in caso di errori
            return self._check_availability_fallback(start_date, end_date)
    
    def _check_availability_fallback(self, start_date, end_date) -> Tuple[bool, str]:
        """
        Metodo di fallback con la logica originale per verificare disponibilità.
        """
        # Verifica prenotazioni esistenti
        from bookings.models import Booking
        overlapping_bookings = Booking.objects.filter(
            listing=self.listing,
            status__in=['pending', 'confirmed'],
            check_out_date__gt=start_date,
            check_in_date__lt=end_date
        )
        
        if overlapping_bookings.exists():
            return False, "Periodo non disponibile per prenotazioni esistenti"
        
        # Verifica gap tra prenotazioni
        gap_days = self.listing.gap_between_bookings
        if gap_days > 0:
            # Verifica se il check-in cade nel gap dopo un check-out esistente
            gap_start = start_date - timedelta(days=gap_days)
            gap_end = start_date
            
            gap_conflicts = Booking.objects.filter(
                listing=self.listing,
                status__in=['pending', 'confirmed'],
                check_out_date__gt=gap_start,
                check_out_date__lte=gap_end
            )
            
            if gap_conflicts.exists():
                return False, f"Check-in non consentito: gap di {gap_days} giorni richiesto dopo il check-out"
            
            # Verifica se il check-out cade nel gap prima di un check-in esistente
            gap_start = end_date + timedelta(days=1)
            gap_end = end_date + timedelta(days=gap_days)
            
            gap_conflicts = Booking.objects.filter(
                listing=self.listing,
                status__in=['pending', 'confirmed'],
                check_in_date__gte=gap_start,
                check_in_date__lte=gap_end
            )
            
            if gap_conflicts.exists():
                return False, f"Check-out non consentito: gap di {gap_days} giorni richiesto prima del check-in"
        
        # Verifica regole di chiusura
        closure_rules = ClosureRule.objects.filter(
            listing=self.listing,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if closure_rules.exists():
            return False, "Periodo non disponibile per chiusura"
        
        # Verifica regole di check-in/out
        check_in_rules = CheckInOutRule.objects.filter(
            listing=self.listing,
            rule_type='no_checkin'
        )
        
        for rule in check_in_rules:
            if self._is_rule_applicable(rule, start_date):
                return False, f"Check-in non consentito il {start_date.strftime('%d/%m/%Y')}"
        
        check_out_rules = CheckInOutRule.objects.filter(
            listing=self.listing,
            rule_type='no_checkout'
        )
        
        for rule in check_out_rules:
            if self._is_rule_applicable(rule, end_date):
                return False, f"Check-out non consentito il {end_date.strftime('%d/%m/%Y')}"
        
        return True, "Disponibile"
    
    def get_calendar_data(self, start_date, end_date) -> Dict:
        """
        Ottiene i dati del calendario usando il nuovo CalendarService.
        
        Args:
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Dict: Dati del calendario
        """
        try:
            return self.calendar_service.get_unavailable_dates(start_date, end_date)
        except CalendarServiceError as e:
            # In caso di errore, restituisci dati di base
            return {
                'blocked_ranges': [],
                'turnover_days': [],
                'checkin_block': {'dates': [], 'weekdays': []},
                'checkout_block': {'dates': [], 'weekdays': []},
                'real_checkin_dates': [],
                'metadata': {
                    'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                    'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                    'window_days': (end_date - start_date).days if hasattr(end_date, '__sub__') else 0,
                    'min_stay': 1,
                    'max_stay': self.listing.max_booking_advance or 365,
                    'gap_between_bookings': self.listing.gap_between_bookings or 0,
                },
                'listing_id': self.listing.id,
                'error': str(e)
            }
        except Exception as e:
            # Fallback completo
            return {
                'blocked_ranges': [],
                'turnover_days': [],
                'checkin_block': {'dates': [], 'weekdays': []},
                'checkout_block': {'dates': [], 'weekdays': []},
                'real_checkin_dates': [],
                'metadata': {
                    'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                    'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                    'window_days': (end_date - start_date).days if hasattr(end_date, '__sub__') else 0,
                    'min_stay': 1,
                    'max_stay': self.listing.max_booking_advance or 365,
                    'gap_between_bookings': self.listing.gap_between_bookings or 0,
                },
                'listing_id': self.listing.id,
                'error': f'Errore interno: {str(e)}'
            }
    
    def _is_rule_applicable(self, rule, date):
        """Verifica se una regola si applica a una data specifica."""
        if rule.recurrence_type == 'specific_date':
            return rule.specific_date == date
        else:
            return rule.day_of_week == date.weekday()
    
    def get_price_per_day(self, date) -> Decimal:
        """
        Calcola il prezzo per un giorno specifico.
        
        Args:
            date: Data per cui calcolare il prezzo
            
        Returns:
            Decimal: Prezzo per il giorno specificato
        """
        # Cerca regole di prezzo per la data
        price_rules = PriceRule.objects.filter(
            listing=self.listing,
            start_date__lte=date,
            end_date__gte=date
        ).order_by('-start_date')
        
        if price_rules.exists():
            rule = price_rules.first()
            return rule.price
        
        # Usa il prezzo base dell'appartamento
        return self.listing.base_price
    
    def calculate_total_price(self, start_date, end_date, num_guests) -> Decimal:
        """
        Calcola il prezzo totale per un periodo.
        
        Args:
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            num_guests: Numero di ospiti
            
        Returns:
            Decimal: Prezzo totale per il periodo
            
        Raises:
            ValueError: Se il periodo non è disponibile
        """
        # Verifica disponibilità prima del calcolo
        is_available, message = self.check_availability(start_date, end_date)
        if not is_available:
            raise ValueError(f"Periodo non disponibile: {message}")
        
        # Calcola il prezzo per ogni giorno
        total_price = Decimal('0.00')
        current_date = start_date
        
        while current_date < end_date:
            daily_price = self.get_price_per_day(current_date)
            total_price += daily_price
            current_date += timedelta(days=1)
        
        # Aggiungi costi extra per ospiti
        if num_guests > self.listing.included_guests:
            extra_guests = num_guests - self.listing.included_guests
            extra_cost = extra_guests * self.listing.extra_guest_fee * (end_date - start_date).days
            total_price += extra_cost
        
        # Aggiungi costo pulizie
        total_price += self.listing.cleaning_fee
        
        return total_price
    
    def get_detailed_pricing(self, start_date, end_date, num_guests) -> Dict:
        """
        Ottiene informazioni dettagliate sui prezzi.
        
        Args:
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            num_guests: Numero di ospiti
            
        Returns:
            Dict: Informazioni dettagliate sui prezzi
        """
        # Verifica disponibilità
        is_available, message = self.check_availability(start_date, end_date)
        if not is_available:
            return {
                'available': False,
                'message': message,
                'total_price': Decimal('0.00')
            }
        
        # Calcola prezzi dettagliati
        daily_prices = []
        current_date = start_date
        total_price = Decimal('0.00')
        
        while current_date < end_date:
            daily_price = self.get_price_per_day(current_date)
            daily_prices.append({
                'date': current_date,
                'price': daily_price
            })
            total_price += daily_price
            current_date += timedelta(days=1)
        
        # Calcola costi extra
        extra_guest_cost = Decimal('0.00')
        if num_guests > self.listing.included_guests:
            extra_guests = num_guests - self.listing.included_guests
            extra_guest_cost = extra_guests * self.listing.extra_guest_fee * (end_date - start_date).days
        
        cleaning_cost = self.listing.cleaning_fee
        
        num_nights = (end_date - start_date).days
        average_price_per_night = total_price / num_nights if num_nights > 0 else Decimal('0.00')
        
        return {
            'available': True,
            'total': float(total_price + extra_guest_cost + cleaning_cost),
            'subtotal': float(total_price),
            'extras': {
                'cleaning': float(cleaning_cost),
                'extra_guests': float(extra_guest_cost)
            },
            'average_price_per_night': float(average_price_per_night),
            'daily_prices': daily_prices,
            'nights': num_nights,
            'num_guests': num_guests,
            # Mantieni anche i campi originali per compatibilità
            'total_price': str(total_price + extra_guest_cost + cleaning_cost),
            'base_price': str(total_price),
            'cleaning_fee': str(cleaning_cost),
            'extra_guest_cost': str(extra_guest_cost),
            'extra_guests_fee': str(extra_guest_cost),  # Alias per compatibilità API
            'cleaning_cost': str(cleaning_cost),
            'num_nights': num_nights
        }