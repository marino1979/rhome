# calendar_rules/managers.py
from datetime import datetime, timedelta
from .models import ClosureRule, CheckInOutRule, PriceRule

class CalendarManager:
    """Classe per gestire la logica di disponibilità e prezzi"""
    
    def __init__(self, listing):
        self.listing = listing
    
    def check_availability(self, start_date, end_date):
        """Verifica disponibilità per un periodo"""
        # 1. Verifica se il periodo è dentro i limiti di anticipo
        today = datetime.now().date()
        advance_days = (start_date - today).days
        if advance_days < self.listing.min_booking_advance or \
           advance_days > self.listing.max_booking_advance:
            return False, "Periodo fuori dai limiti di anticipo prenotazione"
            
        # 2. Verifica chiusure
        closures = self.listing.closure_rules.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        if closures.exists():
            return False, "Periodo non disponibile (chiuso)"
            
        # 3. Verifica regole check-in/out
        checkin_rules = self.listing.checkinout_rules.filter(
            rule_type='no_checkin'
        )
        checkout_rules = self.listing.checkinout_rules.filter(
            rule_type='no_checkout'
        )
        
        # Verifica regole check-in per il giorno di arrivo
        for rule in checkin_rules:
            if (rule.recurrence_type == 'specific_date' and rule.specific_date == start_date) or \
               (rule.recurrence_type == 'weekly' and start_date.weekday() == rule.day_of_week):
                return False, "Check-in non permesso in questa data"
                
        # Verifica regole check-out per il giorno di partenza
        for rule in checkout_rules:
            if (rule.recurrence_type == 'specific_date' and rule.specific_date == end_date) or \
               (rule.recurrence_type == 'weekly' and end_date.weekday() == rule.day_of_week):
                return False, "Check-out non permesso in questa data"
        
        return True, "Disponibile"
    
    def get_price_per_day(self, date):
        """Calcola il prezzo per un giorno specifico"""
        price_rules = self.listing.price_rules.filter(
            start_date__lte=date,
            end_date__gte=date
        ).order_by('-start_date')  # Prende la regola più recente in caso di sovrapposizioni
        
        if price_rules.exists():
            return price_rules.first().price
        
        return self.listing.base_price
        
    def calculate_total_price(self, start_date, end_date, num_guests):
        """Calcola il prezzo totale per un periodo"""
        if not self.check_availability(start_date, end_date)[0]:
            raise ValueError("Periodo non disponibile")
            
        # Calcola giorni
        nights = (end_date - start_date).days
        
        # Calcola prezzo base per ogni giorno
        total = sum(self.get_price_per_day(start_date + timedelta(days=i)) 
                   for i in range(nights))
        
        # Aggiungi extra per ospiti aggiuntivi
        if num_guests > self.listing.included_guests:
            extra_guests = num_guests - self.listing.included_guests
            total += extra_guests * self.listing.extra_guest_fee * nights
            
        # Aggiungi pulizie
        total += self.listing.cleaning_fee
        
        return total