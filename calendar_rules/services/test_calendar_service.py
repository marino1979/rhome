# calendar_rules/services/test_calendar_service.py
"""
Test temporaneo per verificare il funzionamento del CalendarService.
Questo file verrà spostato in tests/ dopo aver completato il refactoring.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from listings.models import Listing
from bookings.models import Booking
from .calendar_service import CalendarService
from .exceptions import InvalidDateRangeError, CalendarServiceError


class CalendarServiceTest(TestCase):
    """Test per il CalendarService."""
    
    def setUp(self):
        """Setup per i test."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.listing = Listing.objects.create(
            title='Test Listing',
            slug='test-listing',
            description='Test description',
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1.0,
            address='Test Address',
            city='Test City',
            zone='Test Zone',
            base_price=100.00,
            gap_between_bookings=3
        )
        
        self.calendar_service = CalendarService(self.listing)
    
    def test_validate_date_range_valid(self):
        """Test validazione range date valido."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        # Non deve sollevare eccezioni
        self.calendar_service._validate_date_range(start_date, end_date)
    
    def test_validate_date_range_invalid_start_after_end(self):
        """Test validazione range date con start dopo end."""
        start_date = date.today()
        end_date = start_date - timedelta(days=1)
        
        with self.assertRaises(InvalidDateRangeError):
            self.calendar_service._validate_date_range(start_date, end_date)
    
    def test_validate_date_range_invalid_types(self):
        """Test validazione con tipi non validi."""
        start_date = "2025-01-01"  # Stringa invece di date
        end_date = date.today()
        
        with self.assertRaises(InvalidDateRangeError):
            self.calendar_service._validate_date_range(start_date, end_date)
    
    def test_get_unavailable_dates_basic(self):
        """Test base per get_unavailable_dates."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        result = self.calendar_service.get_unavailable_dates(start_date, end_date)
        
        # Verifica struttura response
        expected_keys = [
            'blocked_ranges', 'turnover_days', 'checkin_block', 
            'checkout_block', 'real_checkin_dates', 'metadata', 'listing_id'
        ]
        
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verifica metadata
        metadata = result['metadata']
        self.assertEqual(metadata['gap_between_bookings'], 3)
        self.assertEqual(result['listing_id'], self.listing.id)
    
    def test_get_unavailable_dates_with_booking(self):
        """Test con una prenotazione esistente."""
        # Crea una prenotazione
        check_in = date.today() + timedelta(days=5)
        check_out = check_in + timedelta(days=3)
        
        Booking.objects.create(
            listing=self.listing,
            guest=self.user,
            check_in_date=check_in,
            check_out_date=check_out,
            num_guests=2,
            status='confirmed'
        )
        
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        result = self.calendar_service.get_unavailable_dates(start_date, end_date)
        
        # Verifica che ci sia almeno un range bloccato
        self.assertGreater(len(result['blocked_ranges']), 0)
        
        # Verifica che il check-in sia nei real_checkin_dates
        self.assertIn(check_in.isoformat(), result['real_checkin_dates'])
    
    def test_get_unavailable_dates_invalid_range(self):
        """Test con range di date non valido."""
        start_date = date.today()
        end_date = start_date - timedelta(days=1)  # End prima di start
        
        with self.assertRaises(InvalidDateRangeError):
            self.calendar_service.get_unavailable_dates(start_date, end_date)


if __name__ == '__main__':
    import django
    django.setup()
    
    # Test rapido per verificare che il servizio funzioni
    print("Testing CalendarService...")
    
    # Crea listing di test
    listing = Listing.objects.create(
        title='Test Service',
        slug='test-service',
        description='Test',
        status='active',
        max_guests=2,
        bedrooms=1,
        bathrooms=1.0,
        address='Test',
        city='Test',
        zone='Test',
        base_price=50.00,
        gap_between_bookings=2
    )
    
    service = CalendarService(listing)
    
    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        result = service.get_unavailable_dates(start_date, end_date)
        print("✅ CalendarService funziona correttamente!")
        print(f"Response keys: {list(result.keys())}")
        print(f"Metadata: {result['metadata']}")
        
    except Exception as e:
        print(f"❌ Errore nel CalendarService: {e}")
        import traceback
        traceback.print_exc()

