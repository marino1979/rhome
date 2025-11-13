# calendar_rules/services/query_optimizer.py
"""
Servizio specializzato per l'ottimizzazione delle query database.

Responsabilità:
- Ottimizzazione query per calendario
- Prefetch delle relazioni
- Caching dei risultati
- Riduzione query N+1
"""

from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from django.db.models import QuerySet, Prefetch
from .exceptions import QueryOptimizationError


class QueryOptimizer:
    """
    Servizio per ottimizzare le query del calendario.
    """
    
    def __init__(self):
        """Inizializza l'ottimizzatore."""
        pass
    
    def get_optimized_calendar_data(self, listing, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Ottiene tutti i dati del calendario con query ottimizzate.
        
        Args:
            listing: Istanza del modello Listing
            start_date: Data di inizio del periodo
            end_date: Data di fine del periodo
            
        Returns:
            Dict con tutti i dati ottimizzati
            
        Raises:
            QueryOptimizationError: Se le query falliscono
        """
        try:
            # Calcola date estese per gap days
            gap_lookback_days = getattr(listing, 'gap_between_bookings', 0) or 0
            gap_start_date = start_date - timedelta(days=gap_lookback_days)
            
            # Query ottimizzata per bookings con prefetch
            bookings_query = self._get_optimized_bookings_query(
                listing, gap_start_date, end_date
            )
            
            # Query ottimizzata per closure rules
            closures_query = self._get_optimized_closures_query(
                listing, start_date, end_date
            )
            
            # Query ottimizzata per check-in/out rules
            checkinout_rules = self._get_optimized_checkinout_rules(listing)
            
            # Query ottimizzata per price rules
            price_rules = self._get_optimized_price_rules(
                listing, start_date, end_date
            )
            
            return {
                'bookings': list(bookings_query),
                'closures': list(closures_query),
                'checkinout_rules': list(checkinout_rules),
                'price_rules': list(price_rules),
                'gap_days': gap_lookback_days,
                'start_date': start_date,
                'end_date': end_date,
                'gap_start_date': gap_start_date,
            }
            
        except Exception as e:
            raise QueryOptimizationError(f"Errore durante l'ottimizzazione query: {str(e)}")
    
    def _get_optimized_bookings_query(self, listing, gap_start_date: date, end_date: date) -> QuerySet:
        """
        Ottiene query ottimizzata per i bookings.
        
        Args:
            listing: Istanza del modello Listing
            gap_start_date: Data di inizio considerando gap
            end_date: Data di fine
            
        Returns:
            QuerySet ottimizzato
        """
        from bookings.models import Booking
        
        return Booking.objects.filter(
            listing=listing,
            status__in=['pending', 'confirmed'],
            check_out_date__gte=gap_start_date,
            check_in_date__lte=end_date
        ).select_related('guest').only(
            'check_in_date', 'check_out_date', 'status'
        ).values('check_in_date', 'check_out_date', 'status')
    
    def _get_optimized_closures_query(self, listing, start_date: date, end_date: date) -> QuerySet:
        """
        Ottiene query ottimizzata per le closure rules.
        
        Args:
            listing: Istanza del modello Listing
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            QuerySet ottimizzato
        """
        from calendar_rules.models import ClosureRule
        
        return ClosureRule.objects.filter(
            listing=listing,
            end_date__gte=start_date,
            start_date__lte=end_date
        ).only(
            'start_date', 'end_date', 'reason'
        ).values('start_date', 'end_date', 'reason')
    
    def _get_optimized_checkinout_rules(self, listing) -> QuerySet:
        """
        Ottiene query ottimizzata per le check-in/out rules.
        
        Args:
            listing: Istanza del modello Listing
            
        Returns:
            QuerySet ottimizzato
        """
        from calendar_rules.models import CheckInOutRule
        
        return CheckInOutRule.objects.filter(
            listing=listing
        ).only(
            'rule_type', 'recurrence_type', 'specific_date', 'day_of_week'
        )
    
    def _get_optimized_price_rules(self, listing, start_date: date, end_date: date) -> QuerySet:
        """
        Ottiene query ottimizzata per le price rules.
        
        Args:
            listing: Istanza del modello Listing
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            QuerySet ottimizzato
        """
        from calendar_rules.models import PriceRule
        
        return PriceRule.objects.filter(
            listing=listing,
            end_date__gte=start_date,
            start_date__lte=end_date
        ).only(
            'start_date', 'end_date', 'price', 'min_nights'
        ).values('start_date', 'end_date', 'price', 'min_nights')
    
    def get_listing_with_prefetched_rules(self, listing_id: int) -> Any:
        """
        Ottiene un listing con tutte le regole precaricate.
        
        Args:
            listing_id: ID del listing
            
        Returns:
            Listing con regole precaricate
        """
        from listings.models import Listing
        from calendar_rules.models import ClosureRule, CheckInOutRule, PriceRule
        
        try:
            return Listing.objects.select_related().prefetch_related(
                Prefetch(
                    'closure_rules',
                    queryset=ClosureRule.objects.only('start_date', 'end_date', 'reason')
                ),
                Prefetch(
                    'checkinout_rules',
                    queryset=CheckInOutRule.objects.only(
                        'rule_type', 'recurrence_type', 'specific_date', 'day_of_week'
                    )
                ),
                Prefetch(
                    'price_rules',
                    queryset=PriceRule.objects.only(
                        'start_date', 'end_date', 'price', 'min_nights'
                    )
                )
            ).get(id=listing_id)
            
        except Listing.DoesNotExist:
            raise QueryOptimizationError(f"Listing con ID {listing_id} non trovato")
    
    def get_bookings_summary(self, listing, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Ottiene un riepilogo ottimizzato delle prenotazioni.
        
        Args:
            listing: Istanza del modello Listing
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            Dict con riepilogo prenotazioni
        """
        from bookings.models import Booking
        from django.db.models import Count, Min, Max
        
        try:
            # Query aggregata per statistiche
            stats = Booking.objects.filter(
                listing=listing,
                status__in=['pending', 'confirmed'],
                check_in_date__lte=end_date,
                check_out_date__gte=start_date
            ).aggregate(
                total_bookings=Count('id'),
                earliest_checkin=Min('check_in_date'),
                latest_checkout=Max('check_out_date')
            )
            
            # Query per prenotazioni dettagliate
            bookings = self._get_optimized_bookings_query(listing, start_date, end_date)
            
            return {
                'summary': stats,
                'bookings': list(bookings),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            raise QueryOptimizationError(f"Errore durante il riepilogo prenotazioni: {str(e)}")
    
    def batch_process_bookings(self, bookings: List[Dict[str, Any]], 
                             batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Processa i bookings in batch per ottimizzare le performance.
        
        Args:
            bookings: Lista di bookings da processare
            batch_size: Dimensione del batch
            
        Returns:
            Lista di bookings processati
        """
        processed_bookings = []
        
        for i in range(0, len(bookings), batch_size):
            batch = bookings[i:i + batch_size]
            
            # Processa il batch
            for booking in batch:
                # Aggiungi validazioni o trasformazioni qui se necessario
                processed_booking = {
                    'check_in_date': booking.get('check_in_date'),
                    'check_out_date': booking.get('check_out_date'),
                    'status': booking.get('status', 'confirmed')
                }
                processed_bookings.append(processed_booking)
        
        return processed_bookings
    
    def optimize_date_range_queries(self, start_date: date, end_date: date, 
                                  max_range_days: int = 365) -> List[Dict[str, date]]:
        """
        Ottimizza le query dividendo range di date troppo grandi.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            max_range_days: Massimo numero di giorni per range
            
        Returns:
            Lista di range ottimizzati
        """
        total_days = (end_date - start_date).days
        
        if total_days <= max_range_days:
            return [{'start': start_date, 'end': end_date}]
        
        ranges = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=max_range_days - 1), end_date)
            ranges.append({'start': current_start, 'end': current_end})
            current_start = current_end + timedelta(days=1)
        
        return ranges

