from django.views import View
from django.http import JsonResponse
from django.db import transaction
from django.core.files.storage import default_storage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image
import json
import os
import logging
from typing import Dict, Any, List
from decimal import Decimal

from .models import Listing
from rooms.models import Room, RoomType
from beds.models import Bed, BedType
from amenities.models import AmenityCategory, Amenity

logger = logging.getLogger(__name__)

# View per il wizard multi-step
class ListingWizardView(LoginRequiredMixin, View):
    STEPS = {
        1: {'name': 'basic_info', 'fields': ['title', 'description'], 'required': ['title', 'description']},
        2: {'name': 'location', 'fields': ['address', 'total_square_meters', 'outdoor_square_meters'], 'required': ['address', 'total_square_meters']},
        3: {'name': 'rooms', 'fields': ['rooms'], 'required': ['rooms']},
        4: {'name': 'amenities', 'fields': ['amenities'], 'required': []},
        5: {'name': 'photos', 'fields': ['photos'], 'required': []},
        6: {'name': 'pricing', 'fields': ['base_price', 'cleaning_fee'], 'required': ['base_price']}
    }

    MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']

    def get(self, request):
        if 'last_activity' not in request.session:
            request.session['listing_wizard'] = {
                'current_step': 1,
                'data': {},
                'last_activity': request.session.get('last_activity')
            }
        wizard_data = request.session.get('listing_wizard', {})
        return JsonResponse({
            'current_step': wizard_data.get('current_step', 1),
            'data': wizard_data.get('data', {})
        })

    def post(self, request):
        try:
            step = int(request.POST.get('step', 1))
            action = request.POST.get('action', 'next')
            
            if action == 'save':
                return self._handle_save(request)

            wizard_data = request.session.get('listing_wizard', {})
            step_data = self._get_step_data(request, step)
            
            if not self._validate_step(step_data, step):
                return JsonResponse({
                    'success': False, 
                    'error': 'Compila tutti i campi obbligatori prima di proseguire.',
                    'code': 'VALIDATION_ERROR'
                }, status=400)
            
            if not wizard_data.get('data'):
                wizard_data['data'] = {}
            wizard_data['data'].update(step_data)
            wizard_data['last_activity'] = request.session.get('last_activity')
            
            if action == 'next':
                wizard_data['current_step'] = min(step + 1, 6)
            elif action == 'prev':
                wizard_data['current_step'] = max(step - 1, 1)
            
            request.session['listing_wizard'] = wizard_data
            return JsonResponse({'success': True, 'current_step': wizard_data['current_step']})
        except Exception as e:
            logger.error(f"Errore nel wizard: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Si è verificato un errore durante l\'elaborazione della richiesta.',
                'code': 'INTERNAL_ERROR'
            }, status=500)

    def _validate_step(self, step_data: Dict[str, Any], step: int) -> bool:
        required_fields = self.STEPS[step].get('required', [])
        
        # Validazione base dei campi obbligatori
        if not all(step_data.get(field) for field in required_fields):
            return False

        # Validazione specifica per tipo di dati
        if step == 2:  # Location step
            try:
                total_sqm = Decimal(str(step_data.get('total_square_meters', 0)))
                if total_sqm <= 0:
                    return False
                outdoor_sqm = Decimal(str(step_data.get('outdoor_square_meters', 0)))
                if outdoor_sqm < 0:
                    return False
            except (ValueError, TypeError):
                return False

        return True

    def _get_step_data(self, request, step: int) -> Dict[str, Any]:
        try:
            if step == 3:
                rooms_data = json.loads(request.POST.get('rooms', '[]'))
                return {'rooms': rooms_data} if rooms_data else {}
            elif step == 4:
                amenities = request.POST.getlist('amenities[]', [])
                return {'amenities': [int(aid) for aid in amenities if aid.isdigit()]}
            elif step == 5:
                photos = request.FILES.getlist('photos[]', [])
                return {'photos': self._validate_photos(photos)}
            else:
                return {field: request.POST.get(field) for field in self.STEPS[step]['fields']}
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            logger.error(f"Errore nel recupero dei dati dello step {step}: {str(e)}")
            return {}

    def _validate_photos(self, photos: List) -> List:
        valid_photos = []
        for photo in photos:
            if photo.size > self.MAX_PHOTO_SIZE:
                continue
            if photo.content_type not in self.ALLOWED_PHOTO_TYPES:
                continue
            valid_photos.append(photo)
        return valid_photos

    def _handle_save(self, request):
        wizard_data = request.session.get('listing_wizard', {}).get('data', {})
        uploaded_files = []
        
        try:
            with transaction.atomic():
                listing = Listing.objects.create(
                    title=wizard_data.get('title'),
                    description=wizard_data.get('description'),
                    address=wizard_data.get('address'),
                    total_square_meters=wizard_data.get('total_square_meters'),
                    outdoor_square_meters=wizard_data.get('outdoor_square_meters'),
                    user=request.user
                )

                # Gestione delle stanze
                for room_data in wizard_data.get('rooms', []):
                    room = Room.objects.create(
                        listing=listing,
                        name=room_data['name'],
                        room_type_id=room_data['room_type'],
                        square_meters=room_data.get('square_meters')
                    )
                    for bed_data in room_data.get('beds', []):
                        Bed.objects.create(
                            room=room,
                            bed_type_id=bed_data['bed_type'],
                            quantity=bed_data['quantity']
                        )

                # Gestione delle amenità
                amenity_ids = wizard_data.get('amenities', [])
                listing.amenities.set(amenity_ids)

                # Gestione delle foto
                if 'photos' in wizard_data:
                    uploaded_files = self._handle_photos(listing, wizard_data['photos'])

                del request.session['listing_wizard']
                return JsonResponse({'success': True, 'listing_id': listing.id})

        except Exception as e:
            # Pulizia dei file caricati in caso di errore
            for file_path in uploaded_files:
                try:
                    default_storage.delete(file_path)
                except Exception as cleanup_error:
                    logger.error(f"Errore nella pulizia dei file: {str(cleanup_error)}")
            
            logger.error(f"Errore nel salvataggio del listing: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Si è verificato un errore durante il salvataggio.',
                'code': 'SAVE_ERROR'
            }, status=500)

    def _handle_photos(self, listing, photos):
        uploaded_files = []
        for index, photo in enumerate(photos):
            try:
                filename = f"listing_{listing.id}_{index}{os.path.splitext(photo.name)[1]}"
                path = os.path.join('listings', str(listing.id), filename)
                
                img = Image.open(photo)
                img.thumbnail((1200, 1200))
                
                with default_storage.open(path, 'wb') as f:
                    img.save(f, quality=85, optimize=True)
                
                uploaded_files.append(path)
                
                listing.images.create(
                    file=path,
                    order=index,
                    is_main=(index == 0)
                )
            except Exception as e:
                logger.error(f"Errore nel salvataggio della foto {index}: {str(e)}")
                # Se c'è un errore, eliminiamo il file appena caricato
                if path in uploaded_files:
                    try:
                        default_storage.delete(path)
                    except Exception as cleanup_error:
                        logger.error(f"Errore nella pulizia del file {path}: {str(cleanup_error)}")
                continue
        return uploaded_files

# Views per le API di supporto
class RoomTypesView(View):
    def get(self, request):
        room_types = RoomType.objects.all()
        return JsonResponse([{
            'id': rt.id,
            'name': rt.name,
            'can_have_beds': rt.can_have_beds
        } for rt in room_types], safe=False)

class BedTypesView(View):
    def get(self, request):
        bed_types = BedType.objects.all()
        return JsonResponse([{
            'id': bt.id,
            'name': bt.name,
            'capacity': bt.capacity
        } for bt in bed_types], safe=False)

class AmenityCategoriesView(View):
    def get(self, request):
        categories = AmenityCategory.objects.all()
        return JsonResponse([{
            'id': cat.id,
            'name': cat.name,
            'amenities': [{
                'id': amenity.id,
                'name': amenity.name,
                # Rimuoviamo icon per ora o convertiamolo in stringa
                'icon': str(amenity.icon) if amenity.icon else ''  # convertiamo in stringa
            } for amenity in Amenity.objects.filter(category=cat)]
        } for cat in categories], safe=False)
