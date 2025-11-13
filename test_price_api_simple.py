#!/usr/bin/env python
"""
Test semplice per verificare che l'API di calcolo prezzi funzioni.
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

def test_price_calculation():
    """Test del calcolo prezzi usando CalendarManager."""
    print("TEST CALCOLO PREZZI...")
    
    try:
        # Trova un listing attivo
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("   ERRORE: Nessun listing attivo trovato")
            return False
        
        listing = listings.first()
        print(f"   Testing con listing: {listing.title} (ID: {listing.id})")
        
        # Test calcolo prezzi
        calendar = CalendarManager(listing)
        
        check_in_date = date.today() + timedelta(days=7)
        check_out_date = date.today() + timedelta(days=10)
        guests = 2
        
        print(f"   Periodo: {check_in_date} - {check_out_date}")
        print(f"   Ospiti: {guests}")
        
        # Test disponibilità
        is_available, message = calendar.check_availability(check_in_date, check_out_date)
        print(f"   Disponibile: {is_available}")
        if not is_available:
            print(f"   Messaggio: {message}")
            return True  # Non è un errore se non è disponibile
        
        # Test calcolo prezzi dettagliato
        pricing_data = calendar.get_detailed_pricing(check_in_date, check_out_date, guests)
        
        print(f"   Prezzo totale: {pricing_data.get('total_price')}")
        print(f"   Prezzo base: {pricing_data.get('base_price')}")
        print(f"   Notte: {pricing_data.get('num_nights')}")
        print(f"   Prezzo medio per notte: {pricing_data.get('average_price_per_night')}")
        
        if pricing_data.get('available'):
            print("   SUCCESSO: Calcolo prezzi funziona correttamente!")
        else:
            print(f"   AVVISO: Periodo non disponibile: {pricing_data.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_price_calculation()
    sys.exit(0 if success else 1)
