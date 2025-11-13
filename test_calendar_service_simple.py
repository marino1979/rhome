#!/usr/bin/env python
"""
Test semplice per verificare che il CalendarService funzioni.
Esegui questo script dalla root del progetto Django.
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from listings.models import Listing
from calendar_rules.services import CalendarService, CalendarServiceError


def test_calendar_service():
    """Test base del CalendarService."""
    print("Testing CalendarService...")
    
    try:
        # Verifica che ci sia almeno un listing
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("ERRORE: Nessun listing attivo trovato. Crea un listing per testare.")
            return False
        
        listing = listings.first()
        print(f"Testing con listing: {listing.title}")
        
        # Crea il servizio
        calendar_service = CalendarService(listing)
        print("SUCCESSO: CalendarService creato con successo")
        
        # Test con date di default
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        print(f"Testing range: {start_date} to {end_date}")
        
        # Test principale
        result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        # Verifica struttura
        required_keys = [
            'blocked_ranges', 'turnover_days', 'checkin_block', 
            'checkout_block', 'real_checkin_dates', 'metadata', 'listing_id'
        ]
        
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            print(f"ERRORE: Chiavi mancanti nella response: {missing_keys}")
            return False
        
        print("SUCCESSO: Struttura response corretta")
        
        # Verifica metadata
        metadata = result['metadata']
        expected_metadata_keys = ['start', 'end', 'window_days', 'min_stay', 'max_stay', 'gap_between_bookings']
        missing_metadata = [key for key in expected_metadata_keys if key not in metadata]
        
        if missing_metadata:
            print(f"ERRORE: Chiavi mancanti nei metadata: {missing_metadata}")
            return False
        
        print("SUCCESSO: Metadata corretti")
        
        # Verifica listing_id
        if result['listing_id'] != listing.id:
            print(f"ERRORE: listing_id non corrisponde: expected {listing.id}, got {result['listing_id']}")
            return False
        
        print("SUCCESSO: listing_id corretto")
        
        # Test validazione date
        print("Testing validazione date...")
        
        # Test date invalide
        try:
            calendar_service.get_unavailable_dates(end_date, start_date)  # End prima di start
            print("ERRORE: Dovrebbe sollevare InvalidDateRangeError")
            return False
        except CalendarServiceError:
            print("SUCCESSO: Validazione date funziona")
        
        print("\nCalendarService funziona correttamente!")
        print(f"Dati test:")
        print(f"   - Blocked ranges: {len(result['blocked_ranges'])}")
        print(f"   - Turnover days: {len(result['turnover_days'])}")
        print(f"   - Check-in blocked dates: {len(result['checkin_block']['dates'])}")
        print(f"   - Check-out blocked dates: {len(result['checkout_block']['dates'])}")
        print(f"   - Real check-in dates: {len(result['real_checkin_dates'])}")
        print(f"   - Gap between bookings: {metadata['gap_between_bookings']}")
        
        return True
        
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        print(f"   Tipo errore: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_calendar_service()
    sys.exit(0 if success else 1)
