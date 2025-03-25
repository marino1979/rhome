from django.db import models
import datetime
from django.utils.text import slugify
from amenities.models import Amenity
from django.utils.translation import gettext_lazy as _

class Listing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Bozza'),
        ('active', 'Attivo'),
        ('inactive', 'Non attivo'),
    ]

    # Campi base
    title = models.CharField(max_length=200, verbose_name='Titolo')
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(verbose_name='Descrizione')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='Stato'
    )
  
    amenities = models.ManyToManyField('amenities.Amenity', blank=True, verbose_name='Servizi')
    # Dettagli proprietà
    max_guests = models.IntegerField( verbose_name=_("Numero massimo ospiti"))
    bedrooms = models.PositiveIntegerField(
        verbose_name=_("Camere da letto"),
        default=1
    )
    bathrooms = models.DecimalField(
        max_digits=2, 
        decimal_places=1,
        verbose_name='Numero bagni'
    )

    # Posizione
    address = models.CharField(max_length=255, verbose_name='Indirizzo')
    city = models.CharField(max_length=100, verbose_name='Città')
    zone = models.CharField(max_length=100, verbose_name='Zona')  # es. Trastevere, Centro Storico

    # Prezzi
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_("Prezzo base per")
    )
    cleaning_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Costo pulizie'
    )
    # Aggiungi questi campi
    total_square_meters = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name='Metri Quadri Totali',
        null=True,  # Permette valori null
        blank=True  # Permette valori vuoti nel form
    )
    outdoor_square_meters = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        null=True, 
        blank=True,
        verbose_name='Metri Quadri Esterni'
    )
    total_beds = models.PositiveIntegerField(
        default=0,
        verbose_name='Totale letti'
    )
    total_sleeps = models.PositiveIntegerField(
        default=0,
        verbose_name='Totale posti letto'
    )
    included_guests = models.PositiveIntegerField(
        help_text="Numero di ospiti inclusi nel prezzo base",
         default=1,
    )
    extra_guest_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
         default=0,
        help_text="Costo per ogni ospite extra per notte"
    )
    min_booking_advance = models.PositiveIntegerField(
        help_text="Giorni minimi di anticipo per prenotare",
         default=0,

    )
    max_booking_advance = models.PositiveIntegerField(
        help_text="Giorni massimi di anticipo per prenotare",
         default=365,
    )
    gap_between_bookings = models.PositiveIntegerField(
        default=0,
        help_text="Giorni minimi richiesti tra due prenotazioni"
    )
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first()
    
    @property
    def other_images(self):
        return self.images.filter(is_main=False)
    def count_total_beds(self):
        return sum(bed.quantity for bed in self.beds.all())

    def count_total_sleeps(self):
        return sum(bed.quantity * bed.bed_type.capacity for bed in self.beds.all())

    def count_beds_by_type(self):
        beds_summary = {}
        for bed in self.beds.all():
            bed_type = bed.bed_type.name
            if bed_type in beds_summary:
                beds_summary[bed_type] += bed.quantity
            else:
                beds_summary[bed_type] = bed.quantity
        return beds_summary
    
     # Campi per le regole standard
    checkin_from = models.TimeField(default=datetime.time(15, 0), verbose_name="Check-in dalle")
    checkin_to = models.TimeField(default=datetime.time(20, 0), verbose_name="Check-in fino alle")
    checkout_time = models.TimeField(default=datetime.time(10, 0), verbose_name="Check-out entro le")
    
    # Regole booleane
    allow_parties = models.BooleanField(default=False, verbose_name="Feste consentite")
    allow_photos = models.BooleanField(default=True, verbose_name="Foto/Video consentiti")
    allow_smoking = models.BooleanField(default=False, verbose_name="Consentito fumare")
    
    # Note aggiuntive per le regole
    checkin_notes = models.TextField(blank=True, verbose_name="Note check-in")
    checkout_notes = models.TextField(blank=True, verbose_name="Note check-out")
    parties_notes = models.TextField(blank=True, verbose_name="Note feste")
    photos_notes = models.TextField(blank=True, verbose_name="Note foto/video")
    smoking_notes = models.TextField(blank=True, verbose_name="Note fumo")
    # Metadati
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def get_unassigned_beds(self):
        return self.beds.filter(room__isnull=True)
    def save(self, *args, **kwargs):
    # Genera lo slug se non esiste
        if not self.slug:
            self.slug = slugify(self.title)
    
    # Se è un nuovo oggetto (non ha ancora un ID)
        if not self.pk:  # o if not self.id:
        # Prima salva l'oggetto
         super().save(*args, **kwargs)
    
    # Aggiorna i totali solo se l'oggetto esiste già
        if self.pk:
            self.total_beds = self.count_total_beds()
            self.total_sleeps = self.count_total_sleeps()
            super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Annuncio'
        verbose_name_plural = 'Annunci'
