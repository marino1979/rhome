from django.contrib import admin
from django.urls import path  # Aggiunto import di path
from django.contrib import messages  # Aggiunto import di messages
from django.shortcuts import redirect, render  # Aggiunto import di redirect e render
from .models import Listing
from rooms.models import Room
from beds.models import Bed
from images.models import Image
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin,TabbedTranslationAdmin


class BedInline(admin.TabularInline):
    model = Bed
    extra = 1
    fields = ['bed_type', 'quantity', 'room']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            if request._obj_ is not None:  # se stiamo modificando un annuncio esistente
                kwargs["queryset"] = Room.objects.filter(listing=request._obj_)
            else:  # se stiamo creando un nuovo annuncio
                kwargs["queryset"] = Room.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RoomInline(admin.StackedInline):
    model = Room
    extra = 1
    can_delete = True
    show_change_link = True


class ImageInline(admin.TabularInline):  # Usa StackedInline se preferisci un layout verticale
    model = Image
    extra = 1
    fields = ("thumbnail", "file", "title", "alt_text", "order", "is_main", "room")  # Aggiungi thumbnail
    readonly_fields = ("thumbnail",)  # Dichiara thumbnail come campo readonly
    ordering = ("order",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            # Ottieni l'annuncio (listing) corrente
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                kwargs["queryset"] = Room.objects.filter(listing_id=obj_id)
            else:
                kwargs["queryset"] = Room.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
    def thumbnail(self, obj):
        if obj.file:
            return format_html('<img src="{}" width="100" height="auto" style="border-radius: 5px;" />', obj.file.url)
        return "No Image"

class ListingAdmin(TabbedTranslationAdmin):
    inlines = [RoomInline, BedInline, ImageInline]
    list_display = ['title', 'bedrooms', 'total_beds']
    change_form_template = 'admin/listing_change_form.html'
   
     # Aggiungi questi metodi per distinguere tra add_view e change_view
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_image_upload'] = False  # Nascondi il pulsante in fase di creazione
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_image_upload'] = True  # Mostra il pulsante in fase di modifica
        return super().change_view(request, object_id, form_url, extra_context)
    

    
    fieldsets = (
        ('📍 Posizione', {
            'fields': ('address', 'city', 'zone')
        }),
        ('🏠 Proprietà', {
            'fields': (
                'title',
                'description',
                'total_square_meters', 'outdoor_square_meters',
                'bedrooms', 'bathrooms', 'total_beds', 'total_sleeps',
                'max_guests', 'included_guests',
                'amenities'
            )
        }),
        ('💶 Prezzi e prenotazione', {
            'fields': (
                'base_price', 'cleaning_fee', 'extra_guest_fee',
                'min_booking_advance', 'max_booking_advance', 'gap_between_bookings'
            )
        }),
        ('🕒 Regole della casa', {
            'fields': (
                'checkin_from', 'checkin_to', 'checkout_time',
                'allow_parties', 'allow_photos', 'allow_smoking',
                'checkin_notes',
                'checkout_notes',
                'parties_notes', 'photos_notes', 'smoking_notes'
            )
        }),
        ('⚙️ Sistema', {
            'fields': ('slug', 'status', 'created_at', 'updated_at')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
    def get_form(self, request, obj=None, **kwargs):
        # Passa l'oggetto listing alla inline
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:listing_id>/upload-images/', self.admin_site.admin_view(self.multiple_images_upload_view), name='listing-upload-images'),
        ]
        return custom_urls + urls

    
    def multiple_images_upload_view(self, request, listing_id):
        listing = self.get_object(request, listing_id)
        
        # Ottieni tutte le stanze dell'annuncio
        rooms = Room.objects.filter(listing=listing)
        
        if request.method == 'POST':
            files = request.FILES.getlist('images')
            room_id = request.POST.get('room', None)  # Ottieni la stanza selezionata
            
            try:
                room = Room.objects.get(id=room_id) if room_id else None
            except Room.DoesNotExist:
                room = None
            
            for index, f in enumerate(files):
                highest_order = Image.objects.filter(listing=listing).order_by('-order').first()
                start_order = (highest_order.order + 1) if highest_order else 0
                
                Image.objects.create(
                    file=f,
                    listing=listing,
                    room=room,  # Associa la stanza
                    order=start_order + index,
                    title=f.name
                )
            
            messages.success(request, f'{len(files)} immagini caricate con successo')
            return redirect('admin:listings_listing_change', listing_id)
            
        context = {
            'title': f'Upload multiple immagini per {listing}',
            'listing': listing,
            'rooms': rooms,  # Passa le stanze al template
            'opts': self.model._meta,
            'original': listing,
    }
        return render(request, 'admin/multiple_images_upload.html', context)

# Registra correttamente il modello (senza il decoratore)
admin.site.register(Listing, ListingAdmin)