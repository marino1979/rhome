# calendar_rules/models.py
from django.db import models
from django.core.exceptions import ValidationError
from listings.models import Listing

class ClosureRule(models.Model):
    """Regola per chiudere la disponibilità in certi periodi"""
    listing = models.ForeignKey(
        'listings.Listing', 
        on_delete=models.CASCADE,
        related_name='closure_rules'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    is_external_booking = models.BooleanField(
        default=False,
        help_text="Se true, indica prenotazione da altra piattaforma"
    )

    class Meta:
        ordering = ['start_date']
        
    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("La data di inizio deve essere precedente alla data di fine")

class CheckInOutRule(models.Model):
    """Regola per gestire restrizioni su check-in e check-out"""
    RULE_TYPES = [
        ('no_checkin', 'No Check-in'),
        ('no_checkout', 'No Check-out'),
    ]
    RECURRENCE_TYPES = [
        ('specific_date', 'Data Specifica'),
        ('weekly', 'Settimanale'),
    ]
    
    listing = models.ForeignKey(
        'listings.Listing', 
        on_delete=models.CASCADE,
        related_name='checkinout_rules'
    )
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_TYPES)
    specific_date = models.DateField(null=True, blank=True)
    day_of_week = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="0=Lunedì, 6=Domenica"
    )

    class Meta:
        ordering = ['rule_type', 'recurrence_type']

    def clean(self):
        if self.recurrence_type == 'specific_date' and not self.specific_date:
            raise ValidationError("Data specifica richiesta per questo tipo di ricorrenza")
        if self.recurrence_type == 'weekly' and self.day_of_week is None:
            raise ValidationError("Giorno della settimana richiesto per ricorrenza settimanale")



class PriceRule(models.Model):
    listing = models.ForeignKey(
        'listings.Listing', 
        on_delete=models.CASCADE,
        related_name='price_rules'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_nights = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Soggiorno minimo per questo periodo"
    )
    
    class Meta:
        ordering = ['-start_date']

    def clean(self):
        if not self.start_date or not self.end_date:
            return
            
        if self.start_date > self.end_date:
            raise ValidationError("La data di inizio deve essere precedente alla data di fine")

        # La validazione delle sovrapposizioni è stata spostata nell'admin 
        # per gestire meglio l'interfaccia utente e le conferme
    
    def __str__(self):
        return f"{self.listing} - {self.start_date} → {self.end_date}: €{self.price}"