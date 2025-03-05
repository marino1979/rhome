from django.db import models
from django.core.exceptions import ValidationError
import os

def validate_svg(value):
    ext = os.path.splitext(value.name)[1]
    if ext.lower() != '.svg':
        raise ValidationError('Il file deve essere in formato SVG')

class IconCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Categoria Icona"
        verbose_name_plural = "Categorie Icone"
        ordering = ['order', 'name']
        
    def __str__(self):
        return self.name

class Icon(models.Model):
    ICON_TYPES = [
        ('fa', 'Font Awesome'),
        ('custom', 'Icona Personalizzata')
    ]
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(IconCategory, on_delete=models.CASCADE, related_name='icons')
    icon_type = models.CharField(max_length=10, choices=ICON_TYPES, default='fa')
    fa_class = models.CharField(
        max_length=50, 
        blank=True, 
        help_text='Classe Font Awesome (es. fa-home)'
    )
    custom_icon = models.FileField(
        upload_to='icons/', 
        validators=[validate_svg],
        blank=True,
        help_text='File SVG per icona personalizzata'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Icona"
        verbose_name_plural = "Icone"
        ordering = ['category', 'name']
        
    def clean(self):
        if self.icon_type == 'fa' and not self.fa_class:
            raise ValidationError('Per Font Awesome è richiesta la classe')
        if self.icon_type == 'custom' and not self.custom_icon:
            raise ValidationError('Per icone personalizzate è richiesto il file SVG')
            
    def __str__(self):
        return f"{self.name} ({self.get_icon_type_display()})"

    def get_icon_html(self):
        if self.icon_type == 'fa':
            return f'<i class="fas {self.fa_class}"></i>'
        return f'<img src="{self.custom_icon.url}" alt="{self.name}" class="custom-icon" />'