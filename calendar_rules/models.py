from django.db import models
from django.utils.translation import gettext_lazy as _


class ClosureRule(models.Model):
    """
    Regola per bloccare periodi specifici (chiusure, manutenzioni, ecc.)
    """
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='closure_rules',
        verbose_name='Appartamento'
    )
    start_date = models.DateField(verbose_name='Data inizio')
    end_date = models.DateField(verbose_name='Data fine')
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Motivo',
        help_text='Es: "Manutenzione", "Chiusura stagionale"'
    )
    is_external_booking = models.BooleanField(
        default=False,
        verbose_name='Prenotazione esterna',
        help_text='Se true, indica prenotazione da altra piattaforma (Airbnb, Booking.com, ecc.)'
    )
    
    class Meta:
        ordering = ['start_date']
        verbose_name = 'Regola di Chiusura'
        verbose_name_plural = 'Regole di Chiusura'
    
    def save(self, *args, **kwargs):
        """Override save per invalidare cache calendario"""
        super().save(*args, **kwargs)
        self._invalidate_calendar_cache()
    
    def delete(self, *args, **kwargs):
        """Override delete per invalidare cache calendario"""
        listing_id = self.listing_id
        super().delete(*args, **kwargs)
        if listing_id:
            self._invalidate_calendar_cache_for_listing(listing_id)
    
    def _invalidate_calendar_cache(self):
        """Invalida la cache del calendario per questo listing"""
        if self.listing_id:
            self._invalidate_calendar_cache_for_listing(self.listing_id)
    
    @staticmethod
    def _invalidate_calendar_cache_for_listing(listing_id):
        """Invalida cache calendario per un listing specifico"""
        try:
            from django.core.cache import cache
            from datetime import date, timedelta
            from django.utils import timezone
            
            today = timezone.now().date()
            start_date = today - timedelta(days=180)
            end_date = today + timedelta(days=365)
            
            current = start_date
            while current <= end_date:
                cache_key = f"calendar:{listing_id}:{current.isoformat()}:{(current + timedelta(days=30)).isoformat()}"
                cache.delete(cache_key)
                current += timedelta(days=30)
        except Exception:
            pass
    
    def __str__(self):
        return f"{self.listing.title} - {self.start_date} to {self.end_date}"


class CheckInOutRule(models.Model):
    """
    Regola per bloccare giorni specifici per check-in o check-out
    """
    RULE_TYPE_CHOICES = [
        ('no_checkin', 'No Check-in'),
        ('no_checkout', 'No Check-out'),
    ]
    
    RECURRENCE_TYPE_CHOICES = [
        ('specific_date', 'Data Specifica'),
        ('weekly', 'Settimanale'),
    ]
    
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='checkinout_rules',
        verbose_name='Appartamento'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        verbose_name='Tipo regola'
    )
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_TYPE_CHOICES,
        verbose_name='Tipo ricorrenza'
    )
    specific_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data specifica',
        help_text='Usato solo se ricorrenza = "Data Specifica"'
    )
    day_of_week = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Giorno settimana',
        help_text='0=Lunedì, 6=Domenica (usato solo se ricorrenza = "Settimanale")'
    )
    
    class Meta:
        ordering = ['rule_type', 'recurrence_type']
        verbose_name = 'Regola Check-in/Check-out'
        verbose_name_plural = 'Regole Check-in/Check-out'
    
    def save(self, *args, **kwargs):
        """Override save per invalidare cache calendario"""
        super().save(*args, **kwargs)
        ClosureRule._invalidate_calendar_cache_for_listing(self.listing_id)
    
    def delete(self, *args, **kwargs):
        """Override delete per invalidare cache calendario"""
        listing_id = self.listing_id
        super().delete(*args, **kwargs)
        if listing_id:
            ClosureRule._invalidate_calendar_cache_for_listing(listing_id)
    
    def __str__(self):
        if self.recurrence_type == 'specific_date':
            return f"{self.get_rule_type_display()} - {self.specific_date}"
        else:
            days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
            day_name = days[self.day_of_week] if self.day_of_week is not None else 'N/A'
            return f"{self.get_rule_type_display()} - ogni {day_name}"


class PriceRule(models.Model):
    """
    Regola per prezzi personalizzati per periodi specifici
    """
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='price_rules',
        verbose_name='Appartamento'
    )
    start_date = models.DateField(verbose_name='Data inizio')
    end_date = models.DateField(verbose_name='Data fine')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prezzo per notte'
    )
    min_nights = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Soggiorno minimo',
        help_text='Soggiorno minimo per questo periodo'
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Regola Prezzo'
        verbose_name_plural = 'Regole Prezzo'
    
    def save(self, *args, **kwargs):
        """Override save per invalidare cache calendario"""
        super().save(*args, **kwargs)
        ClosureRule._invalidate_calendar_cache_for_listing(self.listing_id)
    
    def delete(self, *args, **kwargs):
        """Override delete per invalidare cache calendario"""
        listing_id = self.listing_id
        super().delete(*args, **kwargs)
        if listing_id:
            ClosureRule._invalidate_calendar_cache_for_listing(listing_id)
    
    def __str__(self):
        return f"{self.listing.title} - {self.start_date} to {self.end_date}: €{self.price}/notte"


class ExternalCalendar(models.Model):
    """
    Modello per sincronizzare calendari esterni (Airbnb, Booking.com, etc.) tramite iCal.
    """
    PROVIDER_CHOICES = [
        ('airbnb', 'Airbnb'),
        ('booking', 'Booking.com'),
        ('expedia', 'Expedia'),
        ('other', 'Altro'),
    ]
    
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='external_calendars',
        verbose_name='Appartamento'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='Nome calendario',
        help_text='Es: "Airbnb Roma Centro", "Booking.com Appartamento 1"'
    )
    
    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default='other',
        verbose_name='Provider'
    )
    
    ical_url = models.URLField(
        verbose_name='URL iCal',
        help_text='URL del calendario iCal da sincronizzare (es: https://calendar.airbnb.com/ical/.../calendar.ics)'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Attivo',
        help_text='Se disattivato, questo calendario non verrà sincronizzato'
    )
    
    sync_interval_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name='Intervallo sincronizzazione (minuti)',
        help_text='Ogni quanti minuti sincronizzare questo calendario'
    )
    
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ultima sincronizzazione'
    )
    
    last_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Successo'),
            ('error', 'Errore'),
            ('pending', 'In attesa'),
        ],
        default='pending',
        verbose_name='Stato ultima sincronizzazione'
    )
    
    last_sync_error = models.TextField(
        blank=True,
        verbose_name='Ultimo errore',
        help_text='Messaggio di errore dell\'ultima sincronizzazione, se presente'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Calendario Esterno'
        verbose_name_plural = 'Calendari Esterni'
        ordering = ['listing', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.listing.title})"
    
    def needs_sync(self):
        """Verifica se il calendario necessita di sincronizzazione"""
        if not self.is_active:
            return False
        
        if not self.last_sync:
            return True
        
        from django.utils import timezone
        from datetime import timedelta
        
        next_sync = self.last_sync + timedelta(minutes=self.sync_interval_minutes)
        return timezone.now() >= next_sync
