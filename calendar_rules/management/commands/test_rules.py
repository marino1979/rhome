# calendar_rules/management/commands/test_rules.py
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from calendar_rules.managers import CalendarManager
from calendar_rules.models import ClosureRule, CheckInOutRule, PriceRule
from listings.models import Listing
from django.db.models import Q

class Command(BaseCommand):
    help = 'Test delle regole del calendario'

    def add_arguments(self, parser):
        parser.add_argument('listing_id', type=int)
        parser.add_argument('--date', type=str, help='Data di inizio test (YYYY-MM-DD)', required=False)

    def handle(self, *args, **options):
        listing = Listing.objects.get(id=options['listing_id'])
        
        if options['date']:
            start_date = date.fromisoformat(options['date'])
        else:
            start_date = date.today()

        self.stdout.write(self.style.SUCCESS(f"\nTest regole per listing: {listing.title}"))
        self.stdout.write("=" * 50)

        # 1. Verifica regole sovrapposte
        self.check_overlapping_rules(listing, start_date)
        
        # 2. Test availability per i prossimi 30 giorni
        self.test_availability(listing, start_date)
        
        # 3. Test prezzi per i prossimi 7 giorni
        self.test_prices(listing, start_date)

    def check_overlapping_rules(self, listing, start_date):
        self.stdout.write("\n1. VERIFICA REGOLE SOVRAPPOSTE:")
        self.stdout.write("-" * 30)

        # Controlla chiusure sovrapposte
        closures = ClosureRule.objects.filter(
            listing=listing,
            end_date__gte=start_date
        )
        
        overlapping_closures = []
        for c1 in closures:
            for c2 in closures:
                if c1.id < c2.id:  # evita duplicati
                    if (c1.start_date <= c2.end_date and 
                        c2.start_date <= c1.end_date):
                        overlapping_closures.append((c1, c2))
        
        if overlapping_closures:
            self.stdout.write(self.style.WARNING("Trovate chiusure sovrapposte:"))
            for c1, c2 in overlapping_closures:
                self.stdout.write(f"- {c1.start_date} → {c1.end_date} sovrapposta con")
                self.stdout.write(f"  {c2.start_date} → {c2.end_date}")
        else:
            self.stdout.write(self.style.SUCCESS("Nessuna chiusura sovrapposta"))

        # Controlla prezzi sovrapposti
        prices = PriceRule.objects.filter(
            listing=listing,
            end_date__gte=start_date
        )
        
        overlapping_prices = []
        for p1 in prices:
            for p2 in prices:
                if p1.id < p2.id:  # evita duplicati
                    if (p1.start_date <= p2.end_date and 
                        p2.start_date <= p1.end_date):
                        overlapping_prices.append((p1, p2))
        
        if overlapping_prices:
            self.stdout.write(self.style.WARNING("\nTrovate regole prezzo sovrapposte:"))
            for p1, p2 in overlapping_prices:
                self.stdout.write(f"- {p1.start_date} → {p1.end_date} (€{p1.price})")
                self.stdout.write(f"  {p2.start_date} → {p2.end_date} (€{p2.price})")
        else:
            self.stdout.write(self.style.SUCCESS("\nNessuna regola prezzo sovrapposta"))

    def test_availability(self, listing, start_date):
        self.stdout.write("\n2. TEST DISPONIBILITÀ:")
        self.stdout.write("-" * 30)
        
        calendar = CalendarManager(listing)
        
        # Test periodi di 3 giorni per i prossimi 30 giorni
        current = start_date
        while current < start_date + timedelta(days=30):
            end = current + timedelta(days=3)
            available, message = calendar.check_availability(current, end)
            
            status = "✓" if available else "✗"
            self.stdout.write(
                f"{status} {current} → {end}: "
                f"{self.style.SUCCESS('Disponibile') if available else self.style.ERROR(message)}"
            )
            
            current += timedelta(days=3)

    def test_prices(self, listing, start_date):
        self.stdout.write("\n3. TEST PREZZI:")
        self.stdout.write("-" * 30)
        
        calendar = CalendarManager(listing)
        
        # Mostra prezzi per i prossimi 7 giorni
        current = start_date
        while current < start_date + timedelta(days=7):
            price = calendar.get_price_per_day(current)
            diff = price - listing.base_price
            
            if diff == 0:
                price_str = f"€{price} (prezzo base)"
            else:
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                price_str = f"€{price} ({diff_str}€ dal base)"
            
            self.stdout.write(f"{current}: {price_str}")
            current += timedelta(days=1)

        # Test prezzo totale per una settimana
        try:
            total = calendar.calculate_total_price(
                start_date,
                start_date + timedelta(days=7),
                2  # test con 2 ospiti
            )
            self.stdout.write(f"\nPrezzo totale 7 giorni (2 ospiti): €{total}")
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"\nErrore calcolo prezzo: {e}"))