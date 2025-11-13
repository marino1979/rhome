#!/usr/bin/env python
"""
Test diretto dell'API usando urllib.
"""

import os
import sys
import django
import json
import urllib.request
import urllib.parse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

def test_direct_api():
    """Test diretto dell'API."""
    print("TEST DIRETTO API...")
    
    try:
        # Test GET (dovrebbe restituire 405)
        print("Test 1: GET request...")
        try:
            response = urllib.request.urlopen('http://localhost:8000/api/calculate-price/')
            print(f"   ERRORE: GET non dovrebbe funzionare, status: {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == 405:
                print(f"   SUCCESSO: GET restituisce 405 come previsto")
            else:
                print(f"   ERRORE: GET restituisce {e.code} invece di 405")
                return False
        
        # Test POST con dati validi
        print("Test 2: POST request...")
        payload = {
            'listing_id': 3,
            'check_in': '2025-10-15',
            'check_out': '2025-10-17',
            'guests': 2
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:8000/api/calculate-price/',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            response = urllib.request.urlopen(req)
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            
            response_data = response.read().decode('utf-8')
            try:
                json_data = json.loads(response_data)
                print(f"   Response keys: {list(json_data.keys())}")
                print(f"   Total price: {json_data.get('total_price')}")
                print("   SUCCESSO: POST funziona correttamente!")
                return True
            except json.JSONDecodeError:
                print(f"   ERRORE: Response non è JSON valido")
                print(f"   Response: {response_data[:200]}")
                return False
                
        except urllib.error.HTTPError as e:
            print(f"   ERRORE: POST restituisce {e.code}")
            print(f"   Response: {e.read().decode('utf-8')[:200]}")
            return False
        
    except Exception as e:
        print(f"ERRORE durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_direct_api()
    sys.exit(0 if success else 1)
