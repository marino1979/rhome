from django.contrib import admin
from .models import Listing
from rooms.models import Room
from beds.models import Bed
from images.models import Image

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
    fields = ("file", "title", "alt_text", "order", "is_main", "room")
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
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [RoomInline, BedInline,ImageInline]
    list_display = ['title', 'bedrooms', 'total_beds']

    def get_form(self, request, obj=None, **kwargs):
        # Passa l'oggetto listing alla inline
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)