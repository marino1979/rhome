# listings/templatetags/listing_filters.py

from django import template
from django.utils.safestring import mark_safe
import math

register = template.Library()

@register.filter
def multiply(value, arg):
    """Moltiplica il valore per l'argomento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def subtract(value, arg):
    """Sottrae l'argomento dal valore"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value
        
@register.filter
def currency(value):
    """Formatta il valore come valuta"""
    try:
        value = float(value)
        return f"€{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value
        
@register.filter
def add_class(field, css_class):
    """Aggiunge una classe CSS a un campo di un form"""
    return field.as_widget(attrs={"class": css_class})
    
@register.filter
def star_rating(value, max_stars=5):
    """Genera un rating a stelle HTML"""
    try:
        value = float(value)
        max_stars = int(max_stars)
        
        # Limita il valore tra 0 e max_stars
        value = max(0, min(value, max_stars))
        
        full_stars = math.floor(value)
        half_star = 0.5 if value - full_stars >= 0.3 and value - full_stars < 0.8 else 0
        empty_stars = max_stars - full_stars - (1 if half_star else 0)
        
        html = ''
        
        # Stelle piene
        for i in range(full_stars):
            html += '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>'
        
        # Mezza stella se necessaria
        if half_star:
            html += '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>'
        
        # Stelle vuote
        for i in range(empty_stars):
            html += '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-300" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>'
        
        return mark_safe(html)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    """Ottiene un elemento da un dizionario usando una chiave"""
    return dictionary.get(key, '')

@register.filter
def truncate_chars(value, max_length):
    """Tronca una stringa a un numero massimo di caratteri"""
    if not value:
        return ""
    
    max_length = int(max_length)
    if len(value) <= max_length:
        return value
    
    return value[:max_length] + "..."

@register.filter
def first_paragraph(text):
    """Estrae il primo paragrafo di un testo"""
    if not text:
        return ""
    
    paragraphs = text.split('\n\n')
    if paragraphs:
        return paragraphs[0]
    return text

@register.filter
def room_capacity(room):
    """Calcola la capacità totale di una stanza basata sui letti"""
    capacity = 0
    for bed in room.beds.all():
        capacity += bed.quantity * bed.bed_type.capacity
    return capacity

@register.filter
def image_url(image, size='medium'):
    """Genera l'URL di un'immagine di una dimensione specifica"""
    if not image:
        return ''
    
    if size == 'thumbnail':
        return image.get_thumbnail_url()
    elif size == 'medium':
        return image.get_medium_url()
    elif size == 'large':
        return image.get_large_url()
    return image.file.url

@register.simple_tag
def amenity_icon(amenity):
    """Genera l'HTML per un'icona di servizio"""
    if not amenity.icon:
        return ''
    
    if amenity.icon.icon_type == 'fa':
        return mark_safe(f'<i class="{amenity.icon.fa_class}"></i>')
    elif amenity.icon.icon_type == 'custom' and amenity.icon.custom_icon:
        return mark_safe(f'<img src="{amenity.icon.custom_icon.url}" alt="{amenity.name}" class="h-5 w-5">')
    return ''

@register.inclusion_tag('listings/tags/gallery_thumbnails.html')
def gallery_thumbnails(images, max_thumbnails=5):
    """Renderizza i thumbnails di una galleria"""
    return {
        'images': images[:max_thumbnails],
        'remaining': max(0, len(images) - max_thumbnails)
    }