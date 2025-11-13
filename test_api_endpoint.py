#!/usr/bin/env python
"""
Test per verificare che l'endpoint API funzioni correttamente.
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from django.test import Client

def test_api_endpoint():
    """Test dell'endpoint API."""
    print("TEST ENDPOINT API...")
    
    try:
        client = Client()
        
        # Test 1: Verifica che l'endpoint esista
        print("Test 1: Verifica endpoint...")
        response = client.get('/api/calculate-price/')
        print(f"   Status GET: {response.status_code}")
        
        # Test 2: POST con dati validi
        print("Test 2: POST con dati validi...")
        payload = {
            'listing_id': 3,
            'check_in': '2025-10-15',
            'check_out': '2025-10-17',
            'guests': 2
        }
        
        response = client.post(
            '/api/calculate-price/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        print(f"   Status POST: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                print(f"   Response keys: {list(data.keys())}")
                print(f"   Total price: {data.get('total_price')}")
                print("   SUCCESSO: API endpoint funziona!")
                return True
            except json.JSONDecodeError:
                print(f"   ERRORE: Response non è JSON valido")
                print(f"   Response: {response.content.decode()[:200]}")
                return False
        else:
            print(f"   ERRORE: Status code non 200")
            print(f"   Response: {response.content.decode()[:200]}")
            return False
        
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_api_endpoint()
    sys.exit(0 if success else 1)
