#!/usr/bin/env python
"""
Test per i servizi specializzati del calendario.
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from listings.models import Listing
from calendar_rules.services import GapCalculator, RangeConsolidator, QueryOptimizer


def test_gap_calculator():
    """Test del GapCalculator."""
    print("Testing GapCalculator...")
    
    try:
        # Test con gap di 3 giorni
        gap_calc = GapCalculator(gap_days=3)
        
        # Test gap dopo check-out
        checkout_date = date(2025, 10, 15)
        start_date = date(2025, 10, 10)
        end_date = date(2025, 10, 25)
        
        after_ranges = gap_calc.calculate_gap_days_after_checkout(
            checkout_date, start_date, end_date
        )
        
        print(f"   Gap dopo check-out {checkout_date}: {after_ranges}")
        
        # Test gap prima di check-in
        checkin_date = date(2025, 10, 20)
        before_ranges = gap_calc.calculate_gap_days_before_checkin(
            checkin_date, start_date, end_date
        )
        
        print(f"   Gap prima di check-in {checkin_date}: {before_ranges}")
        
        # Test booking completo
        booking = {
            'check_in_date': date(2025, 10, 20),
            'check_out_date': date(2025, 10, 15)
        }
        
        all_gaps = gap_calc.calculate_gap_days_for_booking(
            booking, start_date, end_date
        )
        
        print(f"   Tutti i gap per booking: {all_gaps}")
        
        print("   SUCCESSO: GapCalculator funziona")
        return True
        
    except Exception as e:
        print(f"   ERRORE: {e}")
        return False


def test_range_consolidator():
    """Test del RangeConsolidator."""
    print("Testing RangeConsolidator...")
    
    try:
        consolidator = RangeConsolidator()
        
        # Test range sovrapposti
        ranges = [
            (date(2025, 10, 1), date(2025, 10, 5)),
            (date(2025, 10, 3), date(2025, 10, 7)),  # Sovrapposto
            (date(2025, 10, 10), date(2025, 10, 15)),  # Separato
            (date(2025, 10, 14), date(2025, 10, 18)),  # Sovrapposto
        ]
        
        consolidated = consolidator.consolidate_ranges(ranges)
        print(f"   Range originali: {len(ranges)}")
        print(f"   Range consolidati: {len(consolidated)}")
        
        # Test con metadata
        with_metadata = consolidator.consolidate_ranges_with_metadata(ranges)
        print(f"   Con metadata: {len(with_metadata)} range")
        
        # Test statistiche
        stats = consolidator.get_range_statistics(ranges)
        print(f"   Statistiche: {stats['total_ranges']} range, {stats['total_days']} giorni totali")
        
        print("   SUCCESSO: RangeConsolidator funziona")
        return True
        
    except Exception as e:
        print(f"   ERRORE: {e}")
        return False


def test_query_optimizer():
    """Test del QueryOptimizer."""
    print("Testing QueryOptimizer...")
    
    try:
        optimizer = QueryOptimizer()
        
        # Verifica che ci sia almeno un listing
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("   ERRORE: Nessun listing attivo trovato.")
            return False
        
        listing = listings.first()
        
        # Test dati ottimizzati
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        calendar_data = optimizer.get_optimized_calendar_data(
            listing, start_date, end_date
        )
        
        print(f"   Dati calendario ottimizzati:")
        print(f"     - Bookings: {len(calendar_data['bookings'])}")
        print(f"     - Closures: {len(calendar_data['closures'])}")
        print(f"     - Check-in/out rules: {len(calendar_data['checkinout_rules'])}")
        print(f"     - Price rules: {len(calendar_data['price_rules'])}")
        
        # Test riepilogo prenotazioni
        bookings_summary = optimizer.get_bookings_summary(
            listing, start_date, end_date
        )
        
        print(f"   Riepilogo prenotazioni:")
        print(f"     - Totale: {bookings_summary['summary']['total_bookings']}")
        
        # Test ottimizzazione range
        large_start = date.today()
        large_end = large_start + timedelta(days=400)
        
        optimized_ranges = optimizer.optimize_date_range_queries(
            large_start, large_end, max_range_days=100
        )
        
        print(f"   Range ottimizzati: {len(optimized_ranges)} range per periodo di 400 giorni")
        
        print("   SUCCESSO: QueryOptimizer funziona")
        return True
        
    except Exception as e:
        print(f"   ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_services():
    """Test di tutti i servizi specializzati."""
    print("Testing tutti i servizi specializzati...")
    
    success = True
    
    success &= test_gap_calculator()
    success &= test_range_consolidator()
    success &= test_query_optimizer()
    
    if success:
        print("\nSUCCESSO: Tutti i servizi specializzati funzionano correttamente!")
    else:
        print("\nERRORE: Alcuni servizi hanno fallito i test")
    
    return success


if __name__ == '__main__':
    success = test_all_services()
    sys.exit(0 if success else 1)

