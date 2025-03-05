from django.db import models
from listings.models import Listing  # aggiungi questo import
from rooms.models import Room  # Aggiungi questa importazione



class BedType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Tipo letto')
    description = models.CharField(max_length=255, blank=True, verbose_name='Descrizione')
    capacity = models.PositiveIntegerField(
        default=1,
        verbose_name='Numero posti letto',
        help_text='Numero di persone che può ospitare questo tipo di letto'
    )
    dimensions = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Dimensioni',
        help_text='Es: 160x200'
    )

    class Meta:
        verbose_name = 'Tipo di letto'
        verbose_name_plural = 'Tipi di letto'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.capacity} {'posto' if self.capacity == 1 else 'posti'})"

class Bed(models.Model):
    listing = models.ForeignKey(
        'listings.Listing', 
        on_delete=models.CASCADE, 
        related_name='beds',
        verbose_name="Appartamento"
    )
    room = models.ForeignKey(
        'rooms.Room', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='beds',
        verbose_name="Stanza"
    )
    bed_type = models.ForeignKey(
        BedType, 
        on_delete=models.PROTECT,
        verbose_name="Tipo letto"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantità"
    )
    
    class Meta:
        verbose_name = 'Letto'
        verbose_name_plural = 'Letti'

    def __str__(self):
        location = f"in {self.room.name}" if self.room else "senza stanza"
        return f"{self.quantity}x {self.bed_type.name} ({location})"