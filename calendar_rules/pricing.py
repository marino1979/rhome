"""
Sistema di calcolo prezzi per prenotazioni.

Logica chiara:
1. Prezzo per data specifica (se esiste PriceRule)
2. Altrimenti prezzo base del listing
3. Calcolo ospiti extra
4. Totale con cleaning fee
"""

from datetime import date, timedelta
from typing import Dict, List
from decimal import Decimal


class PriceCalculator:
    """
    Calcola prezzi per prenotazioni con supporto per:
    - Prezzi dinamici per periodo (PriceRule)
    - Prezzi specifici per singola data (importati da tool esterni)
    - Ospiti extra
    - Cleaning fee
    """

    def __init__(self, listing):
        self.listing = listing

    def get_price_for_date(self, target_date: date) -> Decimal:
        """
        Ottiene il prezzo per una singola notte.

        Priorità:
        1. PriceRule per questa data specifica (importato da tool esterno)
        2. PriceRule per periodo che include questa data
        3. Prezzo base del listing

        Args:
            target_date: Data per cui calcolare il prezzo

        Returns:
            Prezzo per notte in Decimal
        """
        from .models import PriceRule

        # Cerca prima una regola di prezzo che copre esattamente questa data
        # Ordina per specificità: date ranges più piccoli hanno priorità
        price_rules = PriceRule.objects.filter(
            listing=self.listing,
            start_date__lte=target_date,
            end_date__gte=target_date
        ).order_by('start_date', '-end_date')  # Più specifico prima

        if price_rules.exists():
            return price_rules.first().price

        # Nessuna regola trovata, usa prezzo base
        return self.listing.base_price

    def get_prices_for_range(self, check_in: date, check_out: date) -> Dict[str, Decimal]:
        """
        Ottiene i prezzi per ogni notte in un range.

        Args:
            check_in: Data di check-in
            check_out: Data di check-out

        Returns:
            Dict con date ISO come chiavi e prezzi come valori
            Es: {'2025-01-15': Decimal('100.00'), '2025-01-16': Decimal('120.00'), ...}
        """
        prices = {}
        current = check_in

        # Il check-out non è incluso nel calcolo (la struttura è libera quel giorno)
        while current < check_out:
            prices[current.isoformat()] = self.get_price_for_date(current)
            current += timedelta(days=1)

        return prices

    def calculate_total(self, check_in: date, check_out: date, num_guests: int) -> Dict:
        """
        Calcola il prezzo totale per una prenotazione.

        Args:
            check_in: Data di check-in
            check_out: Data di check-out
            num_guests: Numero di ospiti

        Returns:
            Dict con breakdown completo:
            {
                'nights': 3,
                'nightly_prices': [100.00, 120.00, 100.00],
                'subtotal': 320.00,
                'cleaning_fee': 50.00,
                'extra_guest_fee': 30.00,
                'total': 400.00,
                'breakdown_by_night': {
                    '2025-01-15': {'price': 100.00, 'is_custom': False},
                    '2025-01-16': {'price': 120.00, 'is_custom': True},
                    '2025-01-17': {'price': 100.00, 'is_custom': False},
                }
            }
        """
        if check_in >= check_out:
            raise ValueError("La data di check-out deve essere successiva al check-in")

        if num_guests < 1:
            raise ValueError("Il numero di ospiti deve essere almeno 1")

        if num_guests > self.listing.max_guests:
            raise ValueError(f"Numero massimo di ospiti superato ({self.listing.max_guests})")

        # Calcola notti
        nights = (check_out - check_in).days

        # Ottieni prezzi per ogni notte
        prices_by_date = self.get_prices_for_range(check_in, check_out)
        nightly_prices = list(prices_by_date.values())

        # Calcola subtotal (somma prezzi per notte)
        subtotal = sum(nightly_prices)

        # Cleaning fee (una tantum)
        cleaning_fee = self.listing.cleaning_fee

        # Ospiti extra
        extra_guest_fee = Decimal('0.00')
        if num_guests > self.listing.included_guests:
            extra_guests = num_guests - self.listing.included_guests
            # Fee per ospite extra per notte
            extra_guest_fee = extra_guests * self.listing.extra_guest_fee * nights

        # Totale
        total = subtotal + cleaning_fee + extra_guest_fee

        # Breakdown dettagliato per ogni notte (utile per mostrare nel frontend)
        breakdown_by_night = {}
        for date_str, price in prices_by_date.items():
            # Verifica se è un prezzo personalizzato o base
            is_custom = price != self.listing.base_price
            breakdown_by_night[date_str] = {
                'price': float(price),
                'is_custom': is_custom
            }

        return {
            'nights': nights,
            'nightly_prices': [float(p) for p in nightly_prices],
            'subtotal': float(subtotal),
            'cleaning_fee': float(cleaning_fee),
            'extra_guest_fee': float(extra_guest_fee),
            'total': float(total),
            'breakdown_by_night': breakdown_by_night,
            'price_per_night_avg': float(subtotal / nights) if nights > 0 else 0,
        }

    def get_calendar_prices(self, start_date: date, end_date: date) -> Dict[str, float]:
        """
        Genera mappa di prezzi per il calendario frontend.

        Args:
            start_date: Data inizio
            end_date: Data fine

        Returns:
            Dict con date ISO come chiavi e prezzi come valori
            Es: {'2025-01-15': 100.00, '2025-01-16': 120.00, ...}
        """
        prices = {}
        current = start_date

        while current <= end_date:
            price = self.get_price_for_date(current)
            prices[current.isoformat()] = float(price)
            current += timedelta(days=1)

        return prices


class PriceImporter:
    """
    Tool per importare prezzi da fonti esterne (es. CSV, API, etc.).

    Questo permette di impostare prezzi specifici per singole date,
    creando o aggiornando PriceRule con range di 1 giorno.
    """

    def __init__(self, listing):
        self.listing = listing

    def import_prices_from_dict(self, prices: Dict[date, Decimal], overwrite=False) -> Dict:
        """
        Importa prezzi da un dizionario.

        Args:
            prices: Dict con date come chiavi e prezzi come valori
                   Es: {date(2025, 1, 15): Decimal('120.00'), ...}
            overwrite: Se True, sovrascrive prezzi esistenti

        Returns:
            Dict con statistiche import:
            {
                'created': 10,
                'updated': 5,
                'skipped': 2,
                'errors': []
            }
        """
        from .models import PriceRule

        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        for target_date, price in prices.items():
            try:
                # Cerca se esiste già una regola per questo giorno specifico
                existing = PriceRule.objects.filter(
                    listing=self.listing,
                    start_date=target_date,
                    end_date=target_date
                ).first()

                if existing:
                    if overwrite:
                        existing.price = price
                        existing.save()
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # Crea nuova regola per singolo giorno
                    PriceRule.objects.create(
                        listing=self.listing,
                        start_date=target_date,
                        end_date=target_date,
                        price=price
                    )
                    stats['created'] += 1

            except Exception as e:
                stats['errors'].append({
                    'date': target_date.isoformat(),
                    'error': str(e)
                })

        return stats

    def import_prices_from_csv(self, csv_content: str, overwrite=False) -> Dict:
        """
        Importa prezzi da CSV.

        Formato CSV atteso:
        date,price
        2025-01-15,120.00
        2025-01-16,130.00

        Args:
            csv_content: Contenuto del file CSV
            overwrite: Se True, sovrascrive prezzi esistenti

        Returns:
            Dict con statistiche import
        """
        import csv
        from io import StringIO
        from datetime import datetime

        prices = {}

        try:
            reader = csv.DictReader(StringIO(csv_content))
            for row in reader:
                date_str = row.get('date')
                price_str = row.get('price')

                if not date_str or not price_str:
                    continue

                # Parse date
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                # Parse price
                price = Decimal(price_str)

                prices[target_date] = price

        except Exception as e:
            return {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': [{'error': f'Errore parsing CSV: {str(e)}'}]
            }

        return self.import_prices_from_dict(prices, overwrite)

    def clear_prices_for_range(self, start_date: date, end_date: date) -> int:
        """
        Rimuove tutte le regole di prezzo in un range specifico.

        Utile per "pulire" prima di un re-import.

        Args:
            start_date: Data inizio
            end_date: Data fine

        Returns:
            Numero di regole eliminate
        """
        from .models import PriceRule

        deleted = PriceRule.objects.filter(
            listing=self.listing,
            start_date__gte=start_date,
            end_date__lte=end_date
        ).delete()

        return deleted[0] if deleted else 0
