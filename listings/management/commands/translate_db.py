from django.core.management.base import BaseCommand
from listings.models import Listing
from rooms.models import Room
from amenities.models import Amenity,AmenityCategory
import requests

DEEPL_API_KEY = 'dee4f3b5-ef0c-4819-a840-ccecc390e001:fx'
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'

def translate_text(text, target_lang):
    if not text:
        return ''
    response = requests.post(DEEPL_API_URL, data={
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'source_lang': 'IT',
        'target_lang': target_lang
    })
    response.raise_for_status()
    return response.json()['translations'][0]['text']

def translate_listings():
    print("▶️ Traducendo Listings...")
    for obj in Listing.objects.all():
        if obj.title and not obj.title_en:
            obj.title_en = translate_text(obj.title, 'EN')
        if obj.title and not obj.title_es:
            obj.title_es = translate_text(obj.title, 'ES')

        if obj.description and not obj.description_en:
            obj.description_en = translate_text(obj.description, 'EN')
        if obj.description and not obj.description_es:
            obj.description_es = translate_text(obj.description, 'ES')

        if obj.checkin_notes and not obj.checkin_notes_en:
            obj.checkin_notes_en = translate_text(obj.checkin_notes, 'EN')
        if obj.checkin_notes and not obj.checkin_notes_es:
            obj.checkin_notes_es = translate_text(obj.checkin_notes, 'ES')

        if obj.checkout_notes and not obj.checkout_notes_en:
            obj.checkout_notes_en = translate_text(obj.checkout_notes, 'EN')
        if obj.checkout_notes and not obj.checkout_notes_es:
            obj.checkout_notes_es = translate_text(obj.checkout_notes, 'ES')

        obj.save()

def translate_rooms():
    print("▶️ Traducendo Rooms...")
    for obj in Room.objects.all():
        if obj.description and not obj.description_en:
            obj.description_en = translate_text(obj.description, 'EN')
        if obj.description and not obj.description_es:
            obj.description_es = translate_text(obj.description, 'ES')
        obj.save()

def translate_amenities():
    print("▶️ Traducendo Amenities...")
    for obj in Amenity.objects.all():
        if obj.name and not obj.name_en:
            obj.name_en = translate_text(obj.name, 'EN')
        if obj.name and not obj.name_es:
            obj.name_es = translate_text(obj.name, 'ES')

        if obj.description and not obj.description_en:
            obj.description_en = translate_text(obj.description, 'EN')
        if obj.description and not obj.description_es:
            obj.description_es = translate_text(obj.description, 'ES')

        obj.save()
def translate_amenitiescategory():
    print("▶️ Traducendo Amenities Category...")
    for obj in AmenityCategory.objects.all():
        if obj.name and not obj.name_en:
            obj.name_en = translate_text(obj.name, 'EN')
        if obj.name and not obj.name_es:
            obj.name_es = translate_text(obj.name, 'ES')

       

        obj.save()
class Command(BaseCommand):
    help = 'Traduce automaticamente i campi multilingua usando DeepL API'

    def handle(self, *args, **kwargs):
        translate_listings()
        translate_rooms()
        translate_amenities()
        translate_amenitiescategory()
        self.stdout.write(self.style.SUCCESS("✅ Traduzioni completate con successo!"))
