"""
Management command per sincronizzare le recensioni Airbnb da terminale.
Utile per cron job o sincronizzazione batch.
"""
from django.core.management.base import BaseCommand, CommandError
from listings.models import Listing
from listings.services.review_sync import AirbnbReviewSync, AirbnbReviewSyncError
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Sincronizza le recensioni Airbnb per uno o più annunci'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listing-id',
            type=int,
            help='ID dell\'annuncio da sincronizzare (opzionale, se non specificato sincronizza tutti)',
        )
        parser.add_argument(
            '--min-rating',
            type=float,
            help='Rating minimo (es. 4.0 per solo 4+ stelle)',
        )
        parser.add_argument(
            '--date-filter',
            type=str,
            choices=['last_year', 'last_6_months', 'last_3_months', 'all'],
            default='last_year',
            help='Filtro data per le recensioni',
        )
        parser.add_argument(
            '--language',
            type=str,
            default='it',
            help='Lingua per le recensioni (default: it)',
        )
        parser.add_argument(
            '--proxy-url',
            type=str,
            default='',
            help='URL proxy opzionale',
        )

    def handle(self, *args, **options):
        listing_id = options.get('listing_id')
        min_rating = options.get('min_rating')
        date_filter = options.get('date_filter')
        language = options.get('language')
        proxy_url = options.get('proxy_url', '')

        # Calcola date_from in base al filtro
        date_from = None
        if date_filter == 'last_year':
            date_from = date.today() - timedelta(days=365)
        elif date_filter == 'last_6_months':
            date_from = date.today() - timedelta(days=180)
        elif date_filter == 'last_3_months':
            date_from = date.today() - timedelta(days=90)

        # Ottieni i listing da sincronizzare
        if listing_id:
            try:
                listings = [Listing.objects.get(pk=listing_id)]
            except Listing.DoesNotExist:
                raise CommandError(f'Listing con ID {listing_id} non trovato')
        else:
            # Sincronizza tutti i listing con URL Airbnb
            listings = Listing.objects.filter(airbnb_listing_url__isnull=False).exclude(airbnb_listing_url='')
            if not listings.exists():
                self.stdout.write(self.style.WARNING('Nessun listing con URL Airbnb trovato'))
                return

        total_synced = 0
        total_skipped = 0
        total_errors = 0

        for listing in listings:
            if not listing.airbnb_listing_url:
                self.stdout.write(
                    self.style.WARNING(f'Listing {listing.id} ({listing.title}) non ha URL Airbnb, saltato')
                )
                continue

            self.stdout.write(f'Sincronizzazione recensioni per: {listing.title} (ID: {listing.id})...')

            try:
                sync_service = AirbnbReviewSync(
                    listing=listing,
                    airbnb_url=listing.airbnb_listing_url,
                    language=language,
                    proxy_url=proxy_url
                )

                stats = sync_service.sync_reviews(
                    min_rating=min_rating,
                    date_from=date_from
                )

                total_synced += stats['synced']
                total_skipped += stats['skipped']
                total_errors += stats['errors']

                # Controlla categorie salvate
                from listings.models import Review
                categories_count = Review.objects.filter(
                    listing=listing,
                    cleanliness_rating__isnull=False
                ).count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {stats["synced"]} sincronizzate, '
                        f'{stats["skipped"]} saltate, {stats["errors"]} errori'
                    )
                )
                
                if categories_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Recensioni con categorie salvate: {categories_count}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('  ⚠️ ATTENZIONE: Nessuna recensione con categorie salvata!')
                    )

            except AirbnbReviewSyncError as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Errore: {str(e)}')
                )
                total_errors += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Errore imprevisto: {str(e)}')
                )
                total_errors += 1

        # Riepilogo finale
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Riepilogo Sincronizzazione'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Totale sincronizzate: {total_synced}')
        self.stdout.write(f'Totale saltate: {total_skipped}')
        self.stdout.write(f'Totale errori: {total_errors}')
        self.stdout.write(self.style.SUCCESS('=' * 50))

