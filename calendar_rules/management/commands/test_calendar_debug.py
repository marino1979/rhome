from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from listings.models import Listing
from calendar_rules.services.calendar_service import CalendarService


class Command(BaseCommand):
    help = 'Testa il debug del calendario per un listing specifico'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listing-id',
            type=int,
            help='ID del listing da testare (se non specificato, usa il primo disponibile)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Numero di giorni da analizzare (default: 30)',
        )

    def handle(self, *args, **options):
        listing_id = options.get('listing_id')
        days = options.get('days')
        
        if listing_id:
            try:
                listing = Listing.objects.get(id=listing_id)
            except Listing.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Listing con ID {listing_id} non trovato')
                )
                return
        else:
            listing = Listing.objects.first()
            if not listing:
                self.stdout.write(
                    self.style.ERROR('Nessun listing trovato nel database')
                )
                return
        
        self.stdout.write(
            self.style.SUCCESS(f'Testando debug calendario per Listing ID: {listing.id}')
        )
        
        # Definisci il periodo di test
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        self.stdout.write(f'Periodo di test: {start_date} -> {end_date}')
        self.stdout.write('=' * 60)
        
        # Crea il servizio calendario e chiama il metodo
        calendar_service = CalendarService(listing)
        result = calendar_service.get_unavailable_dates(start_date, end_date)
        
        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS('Debug completato! Controlla la console o calendar_debug.log per i dettagli.')
        )
        self.stdout.write(f'Risultato finale:')
        self.stdout.write(f'  - Range bloccati: {len(result["blocked_ranges"])}')
        self.stdout.write(f'  - Check-in bloccati: {len(result["checkin_block"]["dates"])}')
        self.stdout.write(f'  - Check-out bloccati: {len(result["checkout_block"]["dates"])}')
        self.stdout.write(f'  - Turnover days: {len(result["turnover_days"])}')
        self.stdout.write(f'  - Gap tra prenotazioni: {result["metadata"]["gap_between_bookings"]}')
