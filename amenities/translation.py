# listings/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Amenity, AmenityCategory

@register(Amenity)
class AmenitiesTranslationOptions(TranslationOptions):
    fields = ('name','description',)
@register(AmenityCategory)
class AmenityCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)