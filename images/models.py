from django.db import models
from listings.models import Listing
from rooms.models import Room
from django.core.validators import FileExtensionValidator
from PIL import Image as PILImage
import os

class Image(models.Model):
    file = models.ImageField(
        upload_to='listings/%Y/%m/',  # Rimuovi 'images/' dal percorso
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    title = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images", blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images", blank=True, null=True)
    def clean(self):
        if self.room and self.listing and self.room.listing != self.listing:
            raise ValidationError("La stanza deve appartenere all'annuncio associato.")
    class Meta:
        ordering = ['order', '-created_at']

    def save(self, *args, **kwargs):
        # Assicura che un solo `is_main` per oggetto
        if self.is_main:
            Image.objects.filter(
                listing=self.listing,
                room=self.room,
                is_main=True
            ).update(is_main=False)
        super().save(*args, **kwargs)
