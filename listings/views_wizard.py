from django.views import View
from django.http import JsonResponse
from django.db import transaction
from django.core.files.storage import default_storage
from PIL import Image
import json
import os

from .models import Listing
from rooms.models import Room, RoomType
from beds.models import Bed, BedType
from amenities.models import AmenityCategory, Amenity

# View per il wizard multi-step
class ListingWizardView(View):
    STEPS = {
        1: {'name': 'basic_info', 'fields': ['title', 'description'], 'required': ['title', 'description']},
        2: {'name': 'location', 'fields': ['address', 'total_square_meters', 'outdoor_square_meters'], 'required': ['address', 'total_square_meters']},
        3: {'name': 'rooms', 'fields': ['rooms'], 'required': ['rooms']},
        4: {'name': 'amenities', 'fields': ['amenities'], 'required': []},
        5: {'name': 'photos', 'fields': ['photos'], 'required': []},
        6: {'name': 'pricing', 'fields': ['base_price', 'cleaning_fee'], 'required': ['base_price']}
    }

    def get(self, request):
        if 'last_activity' not in request.session:
            request.session['listing_wizard'] = {
                'current_step': 1,
                'data': {}
            }
        wizard_data = request.session.get('listing_wizard', {})
        return JsonResponse({
            'current_step': wizard_data.get('current_step', 1),
            'data': wizard_data.get('data', {})
        })

    def post(self, request):
        step = int(request.POST.get('step', 1))
        action = request.POST.get('action', 'next')
        
        if action == 'save':
            return self._handle_save(request)

        wizard_data = request.session.get('listing_wizard', {})
        step_data = self._get_step_data(request, step)
        
        if not self._validate_step(step_data, step):
            return JsonResponse({'success': False, 'error': 'Compila tutti i campi obbligatori prima di proseguire.'}, status=400)
        
        if not wizard_data.get('data'):
            wizard_data['data'] = {}
        wizard_data['data'].update(step_data)
        
        if action == 'next':
            wizard_data['current_step'] = min(step + 1, 6)
        elif action == 'prev':
            wizard_data['current_step'] = max(step - 1, 1)
        
        request.session['listing_wizard'] = wizard_data
        return JsonResponse({'success': True, 'current_step': wizard_data['current_step']})

    def _validate_step(self, step_data, step):
        required_fields = self.STEPS[step].get('required', [])
        return all(step_data.get(field) for field in required_fields)

    def _get_step_data(self, request, step):
        if step == 3:
            rooms_data = json.loads(request.POST.get('rooms', '[]'))
            return {'rooms': rooms_data} if rooms_data else {}
        elif step == 4:
            amenities = request.POST.getlist('amenities[]', [])
            return {'amenities': amenities}
        elif step == 5:
            photos = request.FILES.getlist('photos[]', [])
            return {'photos': photos}
        else:
            return {field: request.POST.get(field) for field in self.STEPS[step]['fields']}

    def _handle_save(self, request):
        wizard_data = request.session.get('listing_wizard', {}).get('data', {})
        try:
            with transaction.atomic():
                listing = Listing.objects.create(
                    title=wizard_data.get('title'),
                    description=wizard_data.get('description'),
                    address=wizard_data.get('address'),
                    total_square_meters=wizard_data.get('total_square_meters'),
                    outdoor_square_meters=wizard_data.get('outdoor_square_meters'),
                )
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
                amenity_ids = wizard_data.get('amenities', [])
                listing.amenities.set(amenity_ids)
                if 'photos' in wizard_data:
                    self._handle_photos(listing, wizard_data['photos'])
                del request.session['listing_wizard']
                return JsonResponse({'success': True, 'listing_id': listing.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def _handle_photos(self, listing, photos):
        for index, photo in enumerate(photos):
            try:
                filename = f"listing_{listing.id}_{index}{os.path.splitext(photo.name)[1]}"
                path = os.path.join('listings', str(listing.id), filename)
                img = Image.open(photo)
                img.thumbnail((1200, 1200))
                with default_storage.open(path, 'wb') as f:
                    img.save(f, quality=85, optimize=True)
                listing.images.create(
                    file=path,
                    order=index,
                    is_main=(index == 0)
                )
            except Exception as e:
                continue
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
