from django.contrib import admin
from .models import Image

class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "listing", "room", "order", "is_main", "created_at")
    list_filter = ("listing", "room", "is_main")
    search_fields = ("title", "listing__name", "room__name")
    ordering = ("listing", "room", "order")
    # Rimuovi i campi non più presenti nel modello
    readonly_fields = ()  # Lascia vuoto se non ci sono campi readonly

#admin.site.register(Image, ImageAdmin)
