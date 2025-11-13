#!/usr/bin/env python
"""
Test per verificare che le views refactorizzate funzionino correttamente.
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from django.test import RequestFactory
from listings.models import Listing
from listings import views_refactored


def test_refactored_views():
    """Test delle views refactorizzate."""
    print("Testing views refactorizzate...")
    
    try:
        # Verifica che ci sia almeno un listing
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("ERRORE: Nessun listing attivo trovato.")
            return False
        
        listing = listings.first()
        print(f"Testing con listing: {listing.title}")
        
        # Setup request factory
        factory = RequestFactory()
        
        # Test 1: get_unavailable_dates_refactored
        print("Test 1: get_unavailable_dates_refactored...")
        request = factory.get(f'/listings/{listing.slug}/unavailable-dates-new/')
        
        try:
            response = views_refactored.get_unavailable_dates_refactored(request, listing.slug)
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 200:
                import json
                data = json.loads(response.content)
                print(f"   Response keys: {list(data.keys())}")
                print("   SUCCESSO: View refactorizzata funziona")
            else:
                print(f"   ERRORE: Status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERRORE: {e}")
            return False
        
        # Test 2: compare_old_vs_new_calendar_logic
        print("Test 2: compare_old_vs_new_calendar_logic...")
        request = factory.get(f'/listings/{listing.slug}/compare-calendar-logic/')
        
        try:
            response = views_refactored.compare_old_vs_new_calendar_logic(request, listing.slug)
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 200:
                import json
                data = json.loads(response.content)
                comparison = data.get('comparison', {})
                differences = comparison.get('differences', {})
                
                print(f"   Old ranges: {differences.get('old_ranges', 0)}")
                print(f"   New ranges: {differences.get('new_ranges', 0)}")
                print(f"   Match: {differences.get('match', False)}")
                print("   SUCCESSO: Confronto logica funziona")
            else:
                print(f"   ERRORE: Status code {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ERRORE: {e}")
            return False
        
        print("\nSUCCESSO: Tutte le views refactorizzate funzionano!")
        return True
        
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_refactored_views()
    sys.exit(0 if success else 1)

