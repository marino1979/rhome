from django.db import models

class AmenityCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome Categoria')
    order = models.IntegerField(default=0, help_text='Ordine di visualizzazione')

    class Meta:
        verbose_name = 'Categoria Servizi'
        verbose_name_plural = 'Categorie Servizi'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    category = models.ForeignKey(
        AmenityCategory, 
        on_delete=models.CASCADE,
        related_name='amenities',
        verbose_name='Categoria'
    )
    icon = models.ForeignKey(
        'icons.Icon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Icona',
        related_name='amenities'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Descrizione',
        help_text='Breve descrizione del servizio'
    )
    is_popular = models.BooleanField(
        default=False, 
        verbose_name='Popolare',
        help_text='Indica se è un servizio molto richiesto'
    )
    order = models.IntegerField(
        default=0, 
        help_text='Ordine di visualizzazione'
    )

    class Meta:
        verbose_name = 'Servizio'
        verbose_name_plural = 'Servizi'
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"