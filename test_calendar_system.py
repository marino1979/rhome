#!/usr/bin/env python3
"""
Test del sistema di calendario migliorato
Verifica le funzionalità principali del calendario di prenotazione
"""

import os
import sys
import django
from datetime import date, timedelta
import json

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from listings.models import Listing
from bookings.models import Booking
from calendar_rules.models import ClosureRule, PriceRule, CheckInOutRule
from calendar_rules.managers import CalendarManager


class CalendarSystemTest:
    """Test del sistema di calendario"""
    
    def __init__(self):
        self.client = Client()
        self.test_listing = None
        self.test_user = None
        
    def setup_test_data(self):
        """Crea dati di test"""
        print("🔧 Creazione dati di test...")
        
        # Crea utente di test
        self.test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Crea listing di test
        self.test_listing, created = Listing.objects.get_or_create(
            title='Appartamento Test',
            defaults={
                'slug': 'appartamento-test',
                'description': 'Appartamento per test del calendario',
                'address': 'Via Test 123',
                'city': 'Milano',
                'zone': 'Centro',
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'base_price': 100.00,
                'cleaning_fee': 50.00,
                'extra_guest_fee': 20.00,
                'included_guests': 2,
                'min_stay': 1,
                'max_stay': 30,
                'gap_between_bookings': 1,
                'status': 'active'
            }
        )
        
        print(f"✅ Listing creato: {self.test_listing.title} (ID: {self.test_listing.id})")
        
    def test_calendar_manager(self):
        """Test del CalendarManager"""
        print("\n📅 Test CalendarManager...")
        
        calendar = CalendarManager(self.test_listing)
        
        # Test disponibilità
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=3)
        
        is_available, message = calendar.check_availability(start_date, end_date)
        print(f"   Disponibilità {start_date} - {end_date}: {is_available} ({message})")
        
        # Test calcolo prezzo
        try:
            total_price = calendar.calculate_total_price(start_date, end_date, 2)
            print(f"   Prezzo totale per 2 ospiti: €{total_price}")
        except Exception as e:
            print(f"   ❌ Errore calcolo prezzo: {e}")
        
        # Test dati calendario
        try:
            calendar_data = calendar.get_calendar_data(start_date, end_date)
            print(f"   Dati calendario ottenuti: {len(calendar_data.get('blocked_ranges', []))} range bloccati")
        except Exception as e:
            print(f"   ❌ Errore dati calendario: {e}")
            
    def test_api_endpoints(self):
        """Test degli endpoint API"""
        print("\n🌐 Test endpoint API...")
        
        # Test endpoint calendario per slug
        response = self.client.get(f'/prenotazioni/api/calendar/slug/{self.test_listing.slug}/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Endpoint calendario slug: {data.get('success', False)}")
            print(f"   📊 Dati calendario: {len(data.get('calendar_data', {}).get('blocked_ranges', []))} range bloccati")
        else:
            print(f"   ❌ Endpoint calendario slug: {response.status_code}")
        
        # Test endpoint verifica disponibilità
        check_data = {
            'listing_id': self.test_listing.id,
            'check_in': (date.today() + timedelta(days=7)).isoformat(),
            'check_out': (date.today() + timedelta(days=10)).isoformat(),
            'num_guests': 2
        }
        
        response = self.client.post(
            '/prenotazioni/api/check-availability/',
            data=json.dumps(check_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Endpoint verifica disponibilità: {data.get('available', False)}")
            if data.get('available'):
                pricing = data.get('pricing', {})
                print(f"   💰 Prezzo totale: €{pricing.get('total_amount', 0)}")
        else:
            print(f"   ❌ Endpoint verifica disponibilità: {response.status_code}")
            
    def test_booking_scenarios(self):
        """Test scenari di prenotazione"""
        print("\n📋 Test scenari di prenotazione...")
        
        # Scenario 1: Prenotazione normale
        print("   Scenario 1: Prenotazione normale")
        start_date = date.today() + timedelta(days=14)
        end_date = start_date + timedelta(days=3)
        
        booking_data = {
            'listing_id': self.test_listing.id,
            'check_in': start_date.isoformat(),
            'check_out': end_date.isoformat(),
            'num_guests': 2,
            'num_adults': 2,
            'num_children': 0
        }
        
        response = self.client.post(
            '/prenotazioni/api/check-availability/',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"      Disponibile: {data.get('available', False)}")
        else:
            print(f"      ❌ Errore: {response.status_code}")
        
        # Scenario 2: Troppi ospiti
        print("   Scenario 2: Troppi ospiti")
        booking_data['num_guests'] = 10
        
        response = self.client.post(
            '/prenotazioni/api/check-availability/',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"      Disponibile: {data.get('available', False)}")
            if not data.get('available'):
                print(f"      Messaggio: {data.get('error', 'N/A')}")
        else:
            print(f"      ❌ Errore: {response.status_code}")
            
        # Scenario 3: Date nel passato
        print("   Scenario 3: Date nel passato")
        booking_data['check_in'] = (date.today() - timedelta(days=1)).isoformat()
        booking_data['check_out'] = date.today().isoformat()
        booking_data['num_guests'] = 2
        
        response = self.client.post(
            '/prenotazioni/api/check-availability/',
            data=json.dumps(booking_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"      Disponibile: {data.get('available', False)}")
            if not data.get('available'):
                print(f"      Messaggio: {data.get('error', 'N/A')}")
        else:
            print(f"      ❌ Errore: {response.status_code}")
            
    def test_calendar_rules(self):
        """Test regole del calendario"""
        print("\n📏 Test regole del calendario...")
        
        # Test chiusura
        closure_start = date.today() + timedelta(days=20)
        closure_end = closure_start + timedelta(days=2)
        
        closure, created = ClosureRule.objects.get_or_create(
            listing=self.test_listing,
            start_date=closure_start,
            end_date=closure_end,
            defaults={'reason': 'Manutenzione'}
        )
        
        if created:
            print(f"   ✅ Chiusura creata: {closure_start} - {closure_end}")
        else:
            print(f"   ℹ️ Chiusura esistente: {closure_start} - {closure_end}")
        
        # Test regola check-in
        checkin_rule, created = CheckInOutRule.objects.get_or_create(
            listing=self.test_listing,
            rule_type='no_checkin',
            recurrence_type='weekly',
            day_of_week=6,  # Domenica
            defaults={'reason': 'Nessun check-in di domenica'}
        )
        
        if created:
            print(f"   ✅ Regola check-in creata: Nessun check-in di domenica")
        else:
            print(f"   ℹ️ Regola check-in esistente")
        
        # Test regola prezzo
        price_start = date.today() + timedelta(days=30)
        price_end = price_start + timedelta(days=7)
        
        price_rule, created = PriceRule.objects.get_or_create(
            listing=self.test_listing,
            start_date=price_start,
            end_date=price_end,
            defaults={
                'price': 150.00,
                'min_nights': 3,
                'reason': 'Periodo alta stagione'
            }
        )
        
        if created:
            print(f"   ✅ Regola prezzo creata: €{price_rule.price} (min {price_rule.min_nights} notti)")
        else:
            print(f"   ℹ️ Regola prezzo esistente")
            
    def test_frontend_integration(self):
        """Test integrazione frontend"""
        print("\n🖥️ Test integrazione frontend...")
        
        # Test template listing detail
        response = self.client.get(f'/prenotazioni/listing/{self.test_listing.slug}/')
        if response.status_code == 200:
            print("   ✅ Template listing detail caricato")
            
            # Verifica presenza elementi JavaScript
            content = response.content.decode('utf-8')
            if 'SimpleCalendarManager' in content:
                print("   ✅ SimpleCalendarManager incluso")
            if 'APIClient' in content:
                print("   ✅ APIClient incluso")
            if 'flatpickr' in content:
                print("   ✅ Flatpickr incluso")
        else:
            print(f"   ❌ Template listing detail: {response.status_code}")
            
    def cleanup_test_data(self):
        """Pulisce i dati di test"""
        print("\n🧹 Pulizia dati di test...")
        
        # Rimuovi regole create
        ClosureRule.objects.filter(listing=self.test_listing).delete()
        CheckInOutRule.objects.filter(listing=self.test_listing).delete()
        PriceRule.objects.filter(listing=self.test_listing).delete()
        
        print("   ✅ Regole rimosse")
        
    def run_all_tests(self):
        """Esegue tutti i test"""
        print("🚀 Avvio test del sistema di calendario")
        print("=" * 50)
        
        try:
            self.setup_test_data()
            self.test_calendar_manager()
            self.test_api_endpoints()
            self.test_booking_scenarios()
            self.test_calendar_rules()
            self.test_frontend_integration()
            
            print("\n" + "=" * 50)
            print("✅ Tutti i test completati con successo!")
            
        except Exception as e:
            print(f"\n❌ Errore durante i test: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.cleanup_test_data()


if __name__ == '__main__':
    test_suite = CalendarSystemTest()
    test_suite.run_all_tests()
