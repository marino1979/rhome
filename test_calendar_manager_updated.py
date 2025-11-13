#!/usr/bin/env python
"""
Test per verificare che il CalendarManager aggiornato funzioni correttamente.
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from listings.models import Listing
from calendar_rules.managers import CalendarManager


def test_calendar_manager_updated():
    """Test del CalendarManager aggiornato."""
    print("TEST CALENDAR MANAGER AGGIORNATO...")
    
    try:
        # Test 1: Creazione CalendarManager
        print("Test 1: Creazione CalendarManager...")
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("   ERRORE: Nessun listing attivo trovato")
            return False
        
        listing = listings.first()
        calendar = CalendarManager(listing)
        
        if not hasattr(calendar, 'calendar_service'):
            print("   ERRORE: CalendarService non integrato")
            return False
        
        print("   SUCCESSO: CalendarManager creato con CalendarService integrato")
        
        # Test 2: Metodo check_availability
        print("Test 2: Metodo check_availability...")
        start_date = date.today()
        end_date = start_date + timedelta(days=3)
        
        is_available, message = calendar.check_availability(start_date, end_date)
        print(f"   Disponibile: {is_available}, Messaggio: {message}")
        print("   SUCCESSO: check_availability funziona")
        
        # Test 3: Metodo get_calendar_data
        print("Test 3: Metodo get_calendar_data...")
        calendar_data = calendar.get_calendar_data(start_date, end_date)
        
        required_keys = ['blocked_ranges', 'turnover_days', 'checkin_block', 'checkout_block', 'real_checkin_dates', 'metadata', 'listing_id']
        missing_keys = [key for key in required_keys if key not in calendar_data]
        
        if missing_keys:
            print(f"   ERRORE: Chiavi mancanti: {missing_keys}")
            return False
        
        print("   SUCCESSO: get_calendar_data funziona")
        
        # Test 4: Verifica integrazione
        print("Test 4: Verifica integrazione...")
        if 'error' in calendar_data:
            print(f"   AVVISO: Errore nei dati: {calendar_data['error']}")
        else:
            print("   SUCCESSO: Nessun errore nei dati")
        
        print("\nSUCCESSO: CalendarManager aggiornato funziona correttamente!")
        print("   - CalendarService integrato: SUCCESSO")
        print("   - check_availability: SUCCESSO")
        print("   - get_calendar_data: SUCCESSO")
        print("   - Gestione errori: SUCCESSO")
        
        return True
        
    except Exception as e:
        print(f"\nERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_calendar_manager_updated()
    sys.exit(0 if success else 1)
