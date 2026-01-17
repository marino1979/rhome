from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from listings.models import Listing
from calendar_rules.models import PriceRule


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('confirmed', 'Confermata'),
        ('cancelled', 'Cancellata'),
        ('completed', 'Completata'),
        ('no_show', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('partial', 'Parziale'),
        ('paid', 'Pagato'),
        ('refunded', 'Rimborsato'),
    ]

    # Relazioni
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    guest = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Date prenotazione
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Ospiti
    num_guests = models.PositiveIntegerField()
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)

    # Prezzi
    base_price_per_night = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_nights = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cleaning_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    extra_guest_fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Stati
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # Informazioni aggiuntive
    special_requests = models.TextField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)

    # Richieste di modifica da parte dell'utente
    change_requested = models.BooleanField(default=False)
    change_request_note = models.TextField(blank=True)
    change_request_created_at = models.DateTimeField(null=True, blank=True)

    # Codici di accesso
    check_in_code = models.CharField(max_length=10, blank=True)
    wifi_password = models.CharField(max_length=50, blank=True)

    # Note interne
    host_notes = models.TextField(blank=True)

    # Relazione con prenotazioni combinate (opzionale)
    multi_booking = models.ForeignKey(
        'MultiBooking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='individual_bookings'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prenotazione'
        verbose_name_plural = 'Prenotazioni'

    def clean(self):
        """Validazione del modello usando CalendarManager"""
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("La data di check-out deve essere successiva al check-in")

        if self.check_in_date < timezone.now().date():
            raise ValidationError("Non è possibile prenotare date passate")

        if self.num_guests > self.listing.max_guests:
            raise ValidationError(f"Numero ospiti eccede il massimo consentito ({self.listing.max_guests})")

        # Usa CalendarManager per validazioni avanzate, ma escludiamo questa prenotazione
        # per evitare loop infiniti quando modifichiamo prenotazioni esistenti
        from calendar_rules.managers import CalendarManager

        # Escludiamo temporaneamente questa prenotazione dalla validazione
        excluded_booking_id = self.pk if self.pk else None

        # Per ora validiamo solo regole e chiusure, non le prenotazioni
        # Le prenotazioni sono validate separatamente sotto
        calendar = CalendarManager(self.listing)

        # Verifica solo limiti di anticipo e regole (non prenotazioni)
        today = timezone.now().date()
        advance_days = (self.check_in_date - today).days
        if advance_days < self.listing.min_booking_advance or \
           advance_days > self.listing.max_booking_advance:
            raise ValidationError("Periodo fuori dai limiti di anticipo prenotazione")

        # Verifica chiusure - solo per date di check-in e check-out
        from calendar_rules.models import ClosureRule

        # Verifica se check-in cade in periodo chiuso
        checkin_closures = self.listing.closure_rules.filter(
            start_date__lte=self.check_in_date,
            end_date__gte=self.check_in_date
        )
        if checkin_closures.exists():
            raise ValidationError("Check-in non permesso: struttura chiusa")

        # Verifica se check-out cade in periodo chiuso
        checkout_closures = self.listing.closure_rules.filter(
            start_date__lte=self.check_out_date,
            end_date__gte=self.check_out_date
        )
        if checkout_closures.exists():
            raise ValidationError("Check-out non permesso: struttura chiusa")

        # Verifica soggiorno minimo per periodo specifico
        from calendar_rules.models import PriceRule
        price_rules_with_min_nights = PriceRule.objects.filter(
            listing=self.listing,
            start_date__lte=self.check_in_date,
            end_date__gte=self.check_out_date,
            min_nights__isnull=False
        )

        nights = (self.check_out_date - self.check_in_date).days
        for rule in price_rules_with_min_nights:
            if nights < rule.min_nights:
                raise ValidationError(f"Soggiorno minimo richiesto: {rule.min_nights} notti per questo periodo")

        # Verifica gap tra prenotazioni
        if self.listing.gap_between_bookings > 0:
            nearby_bookings = Booking.objects.filter(
                listing=self.listing,
                status__in=['confirmed', 'pending']
            ).exclude(pk=self.pk if self.pk else None)

            for booking in nearby_bookings:
                # Gap prima del check-in
                days_before = (self.check_in_date - booking.check_out_date).days
                if 0 < days_before < self.listing.gap_between_bookings:
                    raise ValidationError(f"Gap minimo richiesto: {self.listing.gap_between_bookings} giorni tra prenotazioni")

                # Gap dopo il check-out
                days_after = (booking.check_in_date - self.check_out_date).days
                if 0 < days_after < self.listing.gap_between_bookings:
                    raise ValidationError(f"Gap minimo richiesto: {self.listing.gap_between_bookings} giorni tra prenotazioni")

        # Verifica conflitti con altre prenotazioni usando la stessa logica del CalendarManager
        conflicting_bookings = Booking.objects.filter(
            listing=self.listing,
            check_in_date__lt=self.check_out_date,      # Prenotazione inizia prima del nostro check-out
            check_out_date__gt=self.check_in_date,       # Prenotazione finisce dopo il nostro check-in
            status__in=['confirmed', 'pending']
        ).exclude(pk=self.pk if self.pk else None)

        # Filtro manuale per permettere check-out = check-in stesso giorno
        real_conflicts = []
        for booking in conflicting_bookings:
            # Conflitto REALE solo se c'è sovrapposizione effettiva
            # Permetti: check-out di una prenotazione = check-in della nuova
            if not (booking.check_out_date <= self.check_in_date or booking.check_in_date >= self.check_out_date):
                real_conflicts.append(booking)

        if real_conflicts:
            booking = real_conflicts[0]
            raise ValidationError(f"Conflitto con prenotazione esistente dal {booking.check_in_date} al {booking.check_out_date}")

    def calculate_pricing(self):
        """Calcola automaticamente tutti i prezzi usando CalendarManager"""
        if not all([self.check_in_date, self.check_out_date, self.listing]):
            return

        from calendar_rules.managers import CalendarManager
        calendar = CalendarManager(self.listing)

        # Calcola notti
        self.total_nights = (self.check_out_date - self.check_in_date).days

        # Validazione: almeno 1 notte
        if self.total_nights <= 0:
            # Fallback per date non valide
            self.base_price_per_night = self.listing.base_price
            self.subtotal = self.listing.base_price
            self.cleaning_fee = self.listing.cleaning_fee
            self.extra_guest_fee = Decimal('0.00')
            self.total_amount = self.listing.base_price + self.listing.cleaning_fee
            return

        # Usa CalendarManager per calcolo avanzato
        try:
            total_price = calendar.calculate_total_price(
                self.check_in_date,
                self.check_out_date,
                self.num_guests
            )

            # Calcola prezzo medio per notte (per visualizzazione) - con protezione overflow
            price_without_cleaning = total_price - self.listing.cleaning_fee
            if price_without_cleaning > 0:
                calculated_price = Decimal(str(price_without_cleaning)) / self.total_nights

                # Limita a un valore ragionevole per evitare overflow
                max_reasonable_price = Decimal('99999.99')  # Solo 7 cifre totali per sicurezza
                self.base_price_per_night = min(calculated_price, max_reasonable_price)
            else:
                self.base_price_per_night = self.listing.base_price

            # Breakdown dei costi
            subtotal_without_extras = sum(
                calendar.get_price_per_day(self.check_in_date + timedelta(days=i))
                for i in range(self.total_nights)
            )

            self.subtotal = Decimal(str(subtotal_without_extras))
            self.cleaning_fee = self.listing.cleaning_fee

            # Ospiti extra
            if self.num_guests > self.listing.included_guests:
                extra_guests = self.num_guests - self.listing.included_guests
                self.extra_guest_fee = extra_guests * self.listing.extra_guest_fee * self.total_nights
            else:
                self.extra_guest_fee = Decimal('0.00')

            self.total_amount = Decimal(str(total_price))

        except ValueError as e:
            # Fallback se CalendarManager fallisce
            self.base_price_per_night = self.listing.base_price
            self.subtotal = self.base_price_per_night * self.total_nights
            self.cleaning_fee = self.listing.cleaning_fee
            self.extra_guest_fee = Decimal('0.00')
            self.total_amount = self.subtotal + self.cleaning_fee

    def get_price_for_period(self):
        """Ottiene il prezzo considerando le regole di pricing personalizzate"""
        # Cerca regole di prezzo specifiche per il periodo
        price_rules = PriceRule.objects.filter(
            listing=self.listing,
            start_date__lte=self.check_in_date,
            end_date__gte=self.check_out_date
        ).order_by('-start_date')

        if price_rules.exists():
            return price_rules.first().price

        return self.listing.base_price

    def is_available(self):
        """Verifica se le date sono disponibili"""
        from calendar_rules.models import ClosureRule

        # Verifica chiusure - solo per date di check-in e check-out
        # Verifica se check-in cade in periodo chiuso
        checkin_closures = ClosureRule.objects.filter(
            listing=self.listing,
            start_date__lte=self.check_in_date,
            end_date__gte=self.check_in_date
        )
        if checkin_closures.exists():
            return False

        # Verifica se check-out cade in periodo chiuso
        checkout_closures = ClosureRule.objects.filter(
            listing=self.listing,
            start_date__lte=self.check_out_date,
            end_date__gte=self.check_out_date
        )
        if checkout_closures.exists():
            return False

        # Verifica conflitti prenotazioni
        try:
            self.clean()
            return True
        except ValidationError:
            return False

    def generate_check_in_code(self):
        """Genera codice di accesso automatico"""
        import random
        import string
        self.check_in_code = ''.join(random.choices(string.digits, k=6))

    def save(self, *args, **kwargs):
        """Override save per calcoli automatici e validazioni"""
        # Esegui sempre le validazioni prima del salvataggio
        self.full_clean()

        try:
            # Se base_price_per_night è già stato inserito dall'admin, non ricalcolarlo
            preserve_manual_price = self.base_price_per_night and self.base_price_per_night > 0

            self.calculate_pricing()

            # Se era stato inserito manualmente, ripristinalo
            if preserve_manual_price:
                self.base_price_per_night = preserve_manual_price

        except Exception as e:
            # Fallback: usa valori base senza calcoli avanzati
            if hasattr(self, 'check_in_date') and hasattr(self, 'check_out_date'):
                self.total_nights = max(1, (self.check_out_date - self.check_in_date).days)
            # Se non è stato inserito manualmente, usa il prezzo del listing
            if not self.base_price_per_night or self.base_price_per_night <= 0:
                self.base_price_per_night = self.listing.base_price if self.listing else Decimal('100.00')
            self.subtotal = self.base_price_per_night * self.total_nights
            self.cleaning_fee = self.listing.cleaning_fee if self.listing else Decimal('50.00')
            self.extra_guest_fee = Decimal('0.00')
            self.total_amount = self.subtotal + self.cleaning_fee

        if not self.check_in_code and self.status == 'confirmed':
            self.generate_check_in_code()

        super().save(*args, **kwargs)
        
        # Invalida cache calendario per questo listing dopo il salvataggio
        self._invalidate_calendar_cache()
    
    def _invalidate_calendar_cache(self):
        """Invalida la cache del calendario per questo listing"""
        try:
            from django.core.cache import cache
            from datetime import timedelta
            from django.utils import timezone
            
            # Invalida tutte le cache per questo listing
            # Pattern: calendar:{listing_id}:*
            # Django cache non supporta delete_pattern nativamente, quindi invalidiamo manualmente
            # Per ora invalidiamo tutte le cache (in produzione si può usare redis con pattern delete)
            listing_id = getattr(self, 'listing_id', None) or (self.listing.id if hasattr(self, 'listing') and self.listing else None)
            
            if listing_id:
                # Invalida cache per un range ampio di date (ultimi 6 mesi e prossimi 12 mesi)
                today = timezone.now().date()
                start_date = today - timedelta(days=180)  # 6 mesi fa
                end_date = today + timedelta(days=365)     # 12 mesi avanti
                
                # Invalida cache per range di date comuni (ogni 30 giorni)
                current = start_date
                while current <= end_date:
                    cache_key = f"calendar:{listing_id}:{current.isoformat()}:{(current + timedelta(days=30)).isoformat()}"
                    cache.delete(cache_key)
                    current += timedelta(days=30)
        except Exception:
            # Se la cache fallisce, non bloccare il salvataggio
            pass

    @property
    def can_cancel(self):
        """Indica se l'utente può richiedere la cancellazione"""
        if self.status not in ['pending', 'confirmed']:
            return False
        return self.check_in_date > timezone.now().date() + timedelta(days=1)

    @property
    def can_request_change(self):
        """Indica se l'utente può richiedere modifiche alla prenotazione"""
        if self.status not in ['pending', 'confirmed']:
            return False
        return self.check_in_date > timezone.now().date() + timedelta(days=1)

    @property
    def change_request_status(self):
        if not self.change_requested:
            return 'none'
        return 'pending'

    def __str__(self):
        return f"{self.listing.title} - {self.guest.get_full_name() or self.guest.username} ({self.check_in_date} to {self.check_out_date})"


class BookingPayment(models.Model):
    """Modello per tracciare i pagamenti delle prenotazioni"""
    PAYMENT_TYPES = [
        ('deposit', 'Caparra'),
        ('balance', 'Saldo'),
        ('full', 'Pagamento Completo'),
        ('refund', 'Rimborso'),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.booking} - €{self.amount} ({self.payment_type})"


class MultiBooking(models.Model):
    """Prenotazione combinata che può coinvolgere più appartamenti"""
    STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('confirmed', 'Confermata'),
        ('cancelled', 'Cancellata'),
        ('completed', 'Completata'),
        ('no_show', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('partial', 'Parziale'),
        ('paid', 'Pagato'),
        ('refunded', 'Rimborsato'),
    ]

    # Informazioni base
    guest = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='multi_bookings'
    )
    
    # Date e ospiti
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_guests = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Prezzi totali
    total_nights = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cleaning_fee_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    extra_guest_fee_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Stati
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # Informazioni aggiuntive
    special_requests = models.TextField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)

    # Richieste di modifica
    change_requested = models.BooleanField(default=False)
    change_request_note = models.TextField(blank=True)
    change_request_created_at = models.DateTimeField(null=True, blank=True)

    # Note interne
    host_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prenotazione Combinata'
        verbose_name_plural = 'Prenotazioni Combinate'

    def clean(self):
        """Validazione del modello"""
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("La data di check-out deve essere successiva al check-in")

        if self.check_in_date < timezone.now().date():
            raise ValidationError("Non è possibile prenotare date passate")

        # Verifica che ci siano booking individuali collegati (solo se l'oggetto esiste già)
        if self.pk and not self.individual_bookings.exists():
            raise ValidationError("Una prenotazione combinata deve avere almeno un booking individuale")

    def calculate_total_pricing(self):
        """Calcola il prezzo totale sommando i prezzi dei booking individuali"""
        individual_bookings = self.individual_bookings.all()
        
        if not individual_bookings.exists():
            return

        self.total_nights = (self.check_out_date - self.check_in_date).days
        
        # Somma tutti i prezzi dei booking individuali
        self.subtotal = sum(booking.subtotal for booking in individual_bookings)
        self.cleaning_fee_total = sum(booking.cleaning_fee for booking in individual_bookings)
        self.extra_guest_fee_total = sum(booking.extra_guest_fee for booking in individual_bookings)
        self.total_amount = sum(booking.total_amount for booking in individual_bookings)

    def get_listings(self):
        """Restituisce la lista degli appartamenti coinvolti"""
        return [booking.listing for booking in self.individual_bookings.all()]

    def get_listings_names(self):
        """Restituisce i nomi degli appartamenti coinvolti"""
        return [booking.listing.title for booking in self.individual_bookings.all()]

    def is_available(self):
        """Verifica se tutti i booking individuali sono disponibili"""
        return all(booking.is_available() for booking in self.individual_bookings.all())

    def save(self, *args, **kwargs):
        """Override save per calcoli automatici"""
        self.full_clean()
        
        # Salva l'oggetto
        super().save(*args, **kwargs)
        
        # Poi calcola i prezzi se ci sono booking individuali
        if self.pk and self.individual_bookings.exists():
            self.calculate_total_pricing()
            # Aggiorna solo i campi di prezzo senza ricreare l'oggetto
            super().save(update_fields=[
                'total_nights', 'subtotal', 'cleaning_fee_total', 
                'extra_guest_fee_total', 'total_amount'
            ])

    def __str__(self):
        listings = ", ".join(self.get_listings_names())
        return f"Multi: {listings} - {self.guest.get_full_name() or self.guest.username} ({self.check_in_date} to {self.check_out_date})"

    @property
    def can_cancel(self):
        if self.status not in ['pending', 'confirmed']:
            return False
        return self.check_in_date > timezone.now().date() + timedelta(days=1)

    @property
    def can_request_change(self):
        """Indica se l'utente può richiedere modifiche alla prenotazione combinata"""
        if self.status not in ['pending', 'confirmed']:
            return False
        return self.check_in_date > timezone.now().date() + timedelta(days=1)


class Message(models.Model):
    """
    Modello per la messaggistica tra guest e host per una prenotazione.
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    message = models.TextField(verbose_name='Messaggio')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data invio')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Data lettura')
    is_read = models.BooleanField(default=False, verbose_name='Letto')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Messaggio'
        verbose_name_plural = 'Messaggi'
        indexes = [
            models.Index(fields=['booking', 'created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def mark_as_read(self):
        """Marca il messaggio come letto"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def get_other_party(self, user):
        """Restituisce l'altra parte della conversazione (guest o host)"""
        if user == self.sender:
            return self.recipient
        return self.sender

    def __str__(self):
        return f"Messaggio da {self.sender.username} a {self.recipient.username} - Prenotazione #{self.booking.id}"