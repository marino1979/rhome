from django.db import models
import datetime
from django.utils.text import slugify
from amenities.models import Amenity
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count, Q
from decimal import Decimal

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
    min_stay_nights = models.PositiveIntegerField(
        default=1,
        help_text="Soggiorno minimo in notti (può essere sovrascritto da PriceRule per periodi specifici)"
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
    
    # Integrazioni
    airbnb_listing_url = models.URLField(
        blank=True,
        null=True,
        help_text='URL della pagina Airbnb per sincronizzazione automatica recensioni (es: https://www.airbnb.it/rooms/12345678)',
        verbose_name='URL Listing Airbnb'
    )
    airbnb_reviews_last_synced = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e ora dell'ultima sincronizzazione recensioni Airbnb",
        verbose_name='Ultima Sincronizzazione Recensioni'
    )
    
    # Medie aggregate per categoria da Airbnb (non dalle singole recensioni)
    airbnb_cleanliness_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Pulizia (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Pulizia'
    )
    airbnb_accuracy_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Precisione (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Precisione'
    )
    airbnb_checkin_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Check-in (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Check-in'
    )
    airbnb_communication_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Comunicazione (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Comunicazione'
    )
    airbnb_location_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Posizione (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Posizione'
    )
    airbnb_value_avg = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Media Rapporto Qualità-Prezzo (Airbnb)',
        help_text='Media aggregata da Airbnb per la categoria Rapporto Qualità-Prezzo'
    )
    
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
    
    # I campi total_beds, total_sleeps e max_guests vengono gestiti manualmente
    # dall'admin e non vengono più calcolati automaticamente dalle camere
    # Se vuoi calcolarli automaticamente, decommenta le righe qui sotto:
    # if self.pk:
    #     self.total_beds = self.count_total_beds()
    #     self.total_sleeps = self.count_total_sleeps()
    #     super().save(*args, **kwargs)
    
    # Salva normalmente
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_reviews_count(self):
        """Restituisce il numero totale di recensioni per questo listing"""
        return self.reviews.count()

    def get_average_rating(self):
        """Restituisce la media del rating complessivo"""
        avg = self.reviews.aggregate(Avg('overall_rating'))['overall_rating__avg']
        if avg is not None:
            return Decimal(str(round(avg, 2)))
        return None

    def get_reviews_stats(self):
        """
        Restituisce statistiche complete delle recensioni:
        - Media generale
        - Media per categoria (combinata: recensioni con categorie + medie aggregate Airbnb)
        - Conteggio totale
        - Distribuzione stelle
        - Numero recensioni Airbnb vs proprietarie
        """
        reviews = self.reviews.all()
        total_count = reviews.count()
        
        if total_count == 0:
            # Se non ci sono recensioni, usa solo le medie aggregate di Airbnb se disponibili
            category_averages = {}
            if self.airbnb_cleanliness_avg is not None:
                category_averages['cleanliness'] = self.airbnb_cleanliness_avg
            if self.airbnb_accuracy_avg is not None:
                category_averages['accuracy'] = self.airbnb_accuracy_avg
            if self.airbnb_checkin_avg is not None:
                category_averages['checkin'] = self.airbnb_checkin_avg
            if self.airbnb_communication_avg is not None:
                category_averages['communication'] = self.airbnb_communication_avg
            if self.airbnb_location_avg is not None:
                category_averages['location'] = self.airbnb_location_avg
            if self.airbnb_value_avg is not None:
                category_averages['value'] = self.airbnb_value_avg
            
            return {
                'total_count': 0,
                'average_rating': None,
                'category_averages': category_averages,
                'star_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'airbnb_count': 0,
                'own_count': 0,
            }
        
        # Media generale
        avg_rating = self.get_average_rating()
        
        # Media per categoria: calcola dalle recensioni che hanno categorie
        # Cerca recensioni che hanno almeno una categoria valorizzata
        from django.db.models import Q
        reviews_with_categories = reviews.filter(
            Q(cleanliness_rating__isnull=False) |
            Q(accuracy_rating__isnull=False) |
            Q(checkin_rating__isnull=False) |
            Q(communication_rating__isnull=False) |
            Q(location_rating__isnull=False) |
            Q(value_rating__isnull=False)
        )
        
        category_averages = {}
        
        # Calcola medie dalle recensioni che hanno categorie
        if reviews_with_categories.exists():
            category_averages = {
                'cleanliness': reviews_with_categories.aggregate(Avg('cleanliness_rating'))['cleanliness_rating__avg'],
                'accuracy': reviews_with_categories.aggregate(Avg('accuracy_rating'))['accuracy_rating__avg'],
                'checkin': reviews_with_categories.aggregate(Avg('checkin_rating'))['checkin_rating__avg'],
                'communication': reviews_with_categories.aggregate(Avg('communication_rating'))['communication_rating__avg'],
                'location': reviews_with_categories.aggregate(Avg('location_rating'))['location_rating__avg'],
                'value': reviews_with_categories.aggregate(Avg('value_rating'))['value_rating__avg'],
            }
        else:
            # Se non ci sono recensioni con categorie, usa le medie aggregate di Airbnb
            if self.airbnb_cleanliness_avg is not None:
                category_averages['cleanliness'] = self.airbnb_cleanliness_avg
            if self.airbnb_accuracy_avg is not None:
                category_averages['accuracy'] = self.airbnb_accuracy_avg
            if self.airbnb_checkin_avg is not None:
                category_averages['checkin'] = self.airbnb_checkin_avg
            if self.airbnb_communication_avg is not None:
                category_averages['communication'] = self.airbnb_communication_avg
            if self.airbnb_location_avg is not None:
                category_averages['location'] = self.airbnb_location_avg
            if self.airbnb_value_avg is not None:
                category_averages['value'] = self.airbnb_value_avg
        
        # Arrotonda le medie a 2 decimali
        for key, value in category_averages.items():
            if value is not None:
                category_averages[key] = Decimal(str(round(value, 2)))
            else:
                category_averages[key] = None
        
        # Distribuzione stelle
        star_distribution = {
            1: reviews.filter(overall_rating__gte=1, overall_rating__lt=2).count(),
            2: reviews.filter(overall_rating__gte=2, overall_rating__lt=3).count(),
            3: reviews.filter(overall_rating__gte=3, overall_rating__lt=4).count(),
            4: reviews.filter(overall_rating__gte=4, overall_rating__lt=5).count(),
            5: reviews.filter(overall_rating=5).count(),
        }
        
        # Conteggio recensioni Airbnb vs proprietarie
        airbnb_count = reviews.filter(airbnb_review_id__isnull=False).count()
        own_count = reviews.filter(airbnb_review_id__isnull=True).count()
        
        return {
            'total_count': total_count,
            'average_rating': avg_rating,
            'category_averages': category_averages,
            'star_distribution': star_distribution,
            'airbnb_count': airbnb_count,
            'own_count': own_count,
        }

    class Meta:
        verbose_name = 'Annuncio'
        verbose_name_plural = 'Annunci'


class ListingGroup(models.Model):
    """
    Gruppo di appartamenti che possono essere prenotati insieme
    """
    name = models.CharField(
        max_length=200, 
        verbose_name='Nome del gruppo',
        help_text='Es. "Appartamenti Centro", "Suite Familiari"'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrizione',
        help_text='Descrizione del gruppo di appartamenti'
    )
    listings = models.ManyToManyField(
        'Listing',
        verbose_name='Appartamenti',
        help_text='Seleziona gli appartamenti che possono essere prenotati insieme'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Attivo',
        help_text='Se disattivo, questo gruppo non apparirà nelle ricerche combinate'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.listings.count()} appartamenti)"

    @property
    def total_capacity(self):
        """Capacità totale del gruppo (somma di tutti gli appartamenti)"""
        return sum(listing.max_guests for listing in self.listings.all())

    @property
    def total_bedrooms(self):
        """Totale camere da letto del gruppo"""
        return sum(listing.bedrooms for listing in self.listings.all())

    @property
    def total_bathrooms(self):
        """Totale bagni del gruppo"""
        from decimal import Decimal
        total = sum(float(listing.bathrooms) for listing in self.listings.all())
        return Decimal(str(total)).quantize(Decimal('0.1'))

    class Meta:
        verbose_name = 'Gruppo di Appartamenti'
        verbose_name_plural = 'Gruppi di Appartamenti'
        ordering = ['name']


class Review(models.Model):
    """
    Modello per le recensioni degli annunci.
    Supporta recensioni da Airbnb (con airbnb_review_id) e recensioni proprietarie del sito.
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Appartamento'
    )
    
    # Informazioni recensore
    reviewer_name = models.CharField(max_length=200, verbose_name='Nome recensore')
    reviewer_location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Es: "Roma, Italia"',
        verbose_name='Località recensore'
    )
    reviewer_avatar_url = models.URLField(
        blank=True,
        help_text='URL immagine profilo',
        verbose_name='Avatar recensore'
    )
    
    # Date
    review_date = models.DateField(verbose_name='Data recensione')
    stay_date = models.DateField(
        blank=True,
        null=True,
        help_text='Data del soggiorno recensito',
        verbose_name='Data soggiorno'
    )
    
    # Contenuto recensione
    review_text = models.TextField(verbose_name='Testo recensione')
    host_response = models.TextField(
        blank=True,
        help_text="Risposta dell'host alla recensione",
        verbose_name='Risposta host'
    )
    host_response_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data risposta host'
    )
    
    # Rating
    overall_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        help_text='Da 1.0 a 5.0',
        verbose_name='Valutazione complessiva'
    )
    cleanliness_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Da 1.0 a 5.0',
        verbose_name='Pulizia'
    )
    accuracy_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Corrispondenza con l'annuncio (1.0-5.0)",
        verbose_name='Precisione'
    )
    checkin_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Facilità di check-in (1.0-5.0)',
        verbose_name='Check-in'
    )
    communication_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Comunicazione con l'host (1.0-5.0)",
        verbose_name='Comunicazione'
    )
    location_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Qualità della posizione (1.0-5.0)',
        verbose_name='Posizione'
    )
    value_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        blank=True,
        null=True,
        help_text='Valore per il prezzo pagato (1.0-5.0)',
        verbose_name='Rapporto qualità-prezzo'
    )
    
    # Metadati Airbnb
    airbnb_review_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text='ID univoco della recensione su Airbnb (per evitare duplicati)',
        verbose_name='ID Recensione Airbnb'
    )
    airbnb_listing_url = models.URLField(
        blank=True,
        help_text='URL della pagina Airbnb da cui è stata importata',
        verbose_name='URL Listing Airbnb'
    )
    
    # Flag e metadati
    is_verified = models.BooleanField(
        default=False,
        help_text='Recensione verificata da soggiorno effettivo',
        verbose_name='Verificata'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data creazione')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data aggiornamento')
    last_synced = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data dell'ultima sincronizzazione automatica",
        verbose_name='Ultima sincronizzazione'
    )
    
    @property
    def is_airbnb_review(self):
        """Restituisce True se è una recensione da Airbnb"""
        return self.airbnb_review_id is not None and self.airbnb_review_id != ''
    
    @property
    def is_own_review(self):
        """Restituisce True se è una recensione proprietaria del sito"""
        return not self.is_airbnb_review
    
    def __str__(self):
        source = "Airbnb" if self.is_airbnb_review else "Sito"
        return f"{self.reviewer_name} - {self.overall_rating}⭐ ({source})"
    
    class Meta:
        verbose_name = 'Recensione'
        verbose_name_plural = 'Recensioni'
        ordering = ['-review_date', '-created_at']
        indexes = [
            models.Index(fields=['listing', '-review_date']),
            models.Index(fields=['airbnb_review_id']),
        ]