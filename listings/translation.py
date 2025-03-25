# listings/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Listing

@register(Listing)
class ListingTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'checkin_notes', 'checkout_notes')

