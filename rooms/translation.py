# listings/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Room

@register(Room)
class RoomTranslationOptions(TranslationOptions):
    fields = ('description',)

