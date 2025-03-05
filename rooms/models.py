from django.db import models
from listings.models import Listing

class RoomType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    can_have_beds = models.BooleanField(default=False, verbose_name="Può contenere letti")
    
    class Meta:
        verbose_name = 'Tipo Stanza'
        verbose_name_plural = 'Tipi Stanza'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Room(models.Model):
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    square_meters = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")  # Aggiungo default=0
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first()
    
    def __str__(self):
        return self.name
    
    def count_room_beds(self):
        """Conta il numero totale di letti nella stanza"""
        return sum(bed.quantity for bed in self.beds.all())
    count_room_beds.short_description = 'Numero letti'
    
    def count_room_sleeps(self):
        """Conta il numero totale di posti letto nella stanza"""
        return sum(bed.quantity * bed.bed_type.capacity for bed in self.beds.all())
    count_room_sleeps.short_description = 'Posti letto'

    class Meta:
        verbose_name = 'Stanza'
        verbose_name_plural = 'Stanze'
        ordering = ['order']  # Le stanze verranno ordinate per il campo order