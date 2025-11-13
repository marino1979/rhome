#!/usr/bin/env python
"""
Test per verificare che l'API di calcolo prezzi funzioni correttamente.
"""

import os
import sys
import django
import requests
import json
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from listings.models import Listing

BASE_URL = "http://localhost:8000"

def test_price_api():
    """Test dell'API di calcolo prezzi."""
    print("TEST API CALCOLO PREZZI...")
    
    try:
        # Trova un listing attivo
        listings = Listing.objects.filter(status='active')
        if not listings.exists():
            print("   ERRORE: Nessun listing attivo trovato")
            return False
        
        listing = listings.first()
        print(f"   Testing con listing: {listing.title} (ID: {listing.id})")
        
        # Test 1: Calcolo prezzo valido
        print("Test 1: Calcolo prezzo valido...")
        check_in = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        payload = {
            'listing_id': listing.id,
            'check_in': check_in,
            'check_out': check_out,
            'guests': 2
        }
        
        response = requests.post(
            f"{BASE_URL}/api/calculate-price/",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ERRORE: Status code non 200. Response: {response.text}")
            return False
        
        try:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            
            required_keys = ['available', 'total_price', 'base_price', 'num_nights']
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                print(f"   ERRORE: Chiavi mancanti: {missing_keys}")
                return False
            
            print(f"   Disponibile: {data.get('available')}")
            print(f"   Prezzo totale: {data.get('total_price')}")
            print(f"   Notte: {data.get('num_nights')}")
            print("   SUCCESSO: Calcolo prezzo funziona")
            
        except json.JSONDecodeError as e:
            print(f"   ERRORE: JSON non valido: {e}")
            print(f"   Response: {response.text}")
            return False
        
        # Test 2: Parametri mancanti
        print("Test 2: Parametri mancanti...")
        response = requests.post(
            f"{BASE_URL}/api/calculate-price/",
            json={'listing_id': listing.id},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 400:
            print(f"   ERRORE: Dovrebbe restituire 400 per parametri mancanti")
            return False
        
        print("   SUCCESSO: Gestione errori parametri mancanti")
        
        # Test 3: Listing non esistente
        print("Test 3: Listing non esistente...")
        response = requests.post(
            f"{BASE_URL}/api/calculate-price/",
            json={
                'listing_id': 99999,
                'check_in': check_in,
                'check_out': check_out,
                'guests': 2
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 404:
            print(f"   ERRORE: Dovrebbe restituire 404 per listing non esistente")
            return False
        
        print("   SUCCESSO: Gestione errore listing non esistente")
        
        print("\nSUCCESSO: API calcolo prezzi funziona correttamente!")
        print("   - Calcolo prezzo valido: SUCCESSO")
        print("   - Gestione parametri mancanti: SUCCESSO")
        print("   - Gestione listing non esistente: SUCCESSO")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("ERRORE: Impossibile connettersi al server Django. Assicurati che sia in esecuzione.")
        return False
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_price_api()
    sys.exit(0 if success else 1)
