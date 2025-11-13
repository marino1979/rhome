# calendar_rules/services/gap_calculator.py
"""
Servizio specializzato per il calcolo dei gap days tra prenotazioni.

Responsabilità:
- Calcolo gap days dopo check-out
- Calcolo gap days prima di check-in  
- Gestione regole gap complesse
- Validazione gap days
"""

from datetime import date, timedelta
from typing import List, Set, Tuple, Dict, Any
from .exceptions import GapCalculationError


class GapCalculator:
    """
    Servizio per calcolare i gap days tra prenotazioni.
    
    Un gap day è un periodo di tempo richiesto tra la fine di una prenotazione
    e l'inizio di un'altra prenotazione per lo stesso listing.
    """
    
    def __init__(self, gap_days: int = 0):
        """
        Inizializza il calcolatore con il numero di gap days.
        
        Args:
            gap_days: Numero di giorni di gap richiesti (default: 0)
        """
        if gap_days < 0:
            raise GapCalculationError("Il numero di gap days non può essere negativo")
        
        self.gap_days = gap_days
    
    def calculate_gap_days_after_checkout(self, 
                                        checkout_date: date, 
                                        start_date: date, 
                                        end_date: date) -> List[Tuple[date, date]]:
        """
        Calcola i giorni di gap dopo un check-out.
        
        Args:
            checkout_date: Data di check-out della prenotazione esistente
            start_date: Data di inizio del periodo di analisi
            end_date: Data di fine del periodo di analisi
            
        Returns:
            Lista di tuple (start, end) per i range di gap days
            
        Raises:
            GapCalculationError: Se le date non sono valide
        """
        if not self.gap_days:
            return []
        
        if not isinstance(checkout_date, date):
            raise GapCalculationError(f"checkout_date deve essere una data, ricevuto: {type(checkout_date)}")
        
        if start_date >= end_date:
            raise GapCalculationError("start_date deve essere precedente a end_date")
        
        gap_ranges = []
        
        # Gap days iniziano il giorno dopo il check-out
        gap_start = checkout_date + timedelta(days=1)
        gap_end = min(checkout_date + timedelta(days=self.gap_days), end_date)
        
        # Solo se il gap cade nel periodo di analisi
        if gap_start <= end_date and gap_end >= start_date:
            # Tronca il range al periodo di analisi
            actual_start = max(gap_start, start_date)
            actual_end = min(gap_end, end_date)
            
            if actual_start <= actual_end:
                gap_ranges.append((actual_start, actual_end))
        
        return gap_ranges
    
    def calculate_gap_days_before_checkin(self, 
                                        checkin_date: date, 
                                        start_date: date, 
                                        end_date: date) -> List[Tuple[date, date]]:
        """
        Calcola i giorni di gap prima di un check-in.
        
        Args:
            checkin_date: Data di check-in della prenotazione esistente
            start_date: Data di inizio del periodo di analisi
            end_date: Data di fine del periodo di analisi
            
        Returns:
            Lista di tuple (start, end) per i range di gap days
            
        Raises:
            GapCalculationError: Se le date non sono valide
        """
        if not self.gap_days:
            return []
        
        if not isinstance(checkin_date, date):
            raise GapCalculationError(f"checkin_date deve essere una data, ricevuto: {type(checkin_date)}")
        
        if start_date >= end_date:
            raise GapCalculationError("start_date deve essere precedente a end_date")
        
        gap_ranges = []
        
        # Gap days finiscono il giorno prima del check-in
        gap_end = checkin_date - timedelta(days=1)
        gap_start = max(checkin_date - timedelta(days=self.gap_days), start_date)
        
        # Solo se il gap cade nel periodo di analisi
        if gap_start <= end_date and gap_end >= start_date:
            # Tronca il range al periodo di analisi
            actual_start = max(gap_start, start_date)
            actual_end = min(gap_end, end_date)
            
            if actual_start <= actual_end:
                gap_ranges.append((actual_start, actual_end))
        
        return gap_ranges
    
    def calculate_gap_days_for_booking(self, 
                                     booking: Dict[str, Any], 
                                     start_date: date, 
                                     end_date: date) -> List[Tuple[date, date]]:
        """
        Calcola tutti i gap days per una prenotazione (sia prima che dopo).
        
        Args:
            booking: Dict con 'check_in_date' e 'check_out_date'
            start_date: Data di inizio del periodo di analisi
            end_date: Data di fine del periodo di analisi
            
        Returns:
            Lista di tuple (start, end) per tutti i range di gap days
        """
        gap_ranges = []
        
        checkout_date = booking.get('check_out_date')
        checkin_date = booking.get('check_in_date')
        
        # Gap dopo check-out
        if checkout_date:
            after_ranges = self.calculate_gap_days_after_checkout(checkout_date, start_date, end_date)
            gap_ranges.extend(after_ranges)
        
        # Gap prima di check-in
        if checkin_date:
            before_ranges = self.calculate_gap_days_before_checkin(checkin_date, start_date, end_date)
            gap_ranges.extend(before_ranges)
        
        return gap_ranges
    
    def get_gap_blocked_dates_for_checkin(self, 
                                        bookings: List[Dict[str, Any]], 
                                        start_date: date, 
                                        end_date: date) -> Set[date]:
        """
        Ottiene tutti i giorni bloccati per check-in a causa dei gap days.
        
        Args:
            bookings: Lista di prenotazioni esistenti
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Set di date bloccate per check-in
        """
        blocked_dates = set()
        
        for booking in bookings:
            gap_ranges = self.calculate_gap_days_for_booking(booking, start_date, end_date)
            
            for gap_start, gap_end in gap_ranges:
                current_date = gap_start
                while current_date <= gap_end:
                    blocked_dates.add(current_date)
                    current_date += timedelta(days=1)
        
        return blocked_dates
    
    def validate_booking_gap(self, 
                           new_checkin: date, 
                           new_checkout: date, 
                           existing_bookings: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Valida se una nuova prenotazione rispetta le regole gap.
        
        Args:
            new_checkin: Data di check-in della nuova prenotazione
            new_checkout: Data di check-out della nuova prenotazione
            existing_bookings: Lista di prenotazioni esistenti
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not self.gap_days:
            return True, ""
        
        for booking in existing_bookings:
            existing_checkin = booking.get('check_in_date')
            existing_checkout = booking.get('check_out_date')
            
            if not existing_checkin or not existing_checkout:
                continue
            
            # Verifica gap prima del nuovo check-in
            days_before = (new_checkin - existing_checkout).days
            if 0 < days_before < self.gap_days:
                return False, f"Gap minimo di {self.gap_days} giorni richiesto dopo check-out {existing_checkout}"
            
            # Verifica gap dopo il nuovo check-out
            days_after = (existing_checkin - new_checkout).days
            if 0 < days_after < self.gap_days:
                return False, f"Gap minimo di {self.gap_days} giorni richiesto prima di check-in {existing_checkin}"
        
        return True, ""
    
    def get_gap_summary(self, 
                       bookings: List[Dict[str, Any]], 
                       start_date: date, 
                       end_date: date) -> Dict[str, Any]:
        """
        Ottiene un riepilogo completo dei gap days per il periodo.
        
        Args:
            bookings: Lista di prenotazioni esistenti
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Dict con riepilogo dei gap days
        """
        gap_ranges = []
        blocked_dates = set()
        
        for booking in bookings:
            booking_gaps = self.calculate_gap_days_for_booking(booking, start_date, end_date)
            gap_ranges.extend(booking_gaps)
            
            for gap_start, gap_end in booking_gaps:
                current_date = gap_start
                while current_date <= gap_end:
                    blocked_dates.add(current_date)
                    current_date += timedelta(days=1)
        
        return {
            'gap_days': self.gap_days,
            'total_gap_ranges': len(gap_ranges),
            'gap_ranges': gap_ranges,
            'blocked_dates_count': len(blocked_dates),
            'blocked_dates': sorted(blocked_dates),
            'period_start': start_date,
            'period_end': end_date,
        }

