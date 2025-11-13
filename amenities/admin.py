from django.contrib import admin
from django.utils.html import format_html
from .models import Amenity, AmenityCategory
from .widgets import IconSelectWidget
# Temporaneamente disabilitato per risolvere errore di compatibilità
# from modeltranslation.admin import TabbedTranslationAdmin
@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    search_fields = ['name']
    ordering = ['order', 'name']

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['amenity_name_with_icon', 'category', 'is_popular', 'order']
    list_filter = ['category', 'is_popular']
    search_fields = ['name', 'description']
    ordering = ['category', 'order', 'name']
    list_editable = ['is_popular', 'order']
    fields = ['icon_preview', 'icon', 'name', 'description', 'category', 'is_popular', 'order']
    readonly_fields = ['icon_preview']  # Aggiunto il campo di sola lettura

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'icon':
            kwargs['widget'] = IconSelectWidget()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def amenity_name_with_icon(self, obj):
        if obj.icon:
            if obj.icon.icon_type == 'fa':  # Font Awesome
                return format_html(
                    '<div class="amenity_name_with_icon"><i class="{}" style="margin-right: 8px;"></i>{}</div>',
                    obj.icon.fa_class, obj.name
                )
            elif obj.icon.icon_type == 'custom' and obj.icon.custom_icon:  # Custom icon
                return format_html(
                    '<div class="amenity_name_with_icon"><img src="{}" style="height: 1.2em; margin-right: 8px;">{}</div>',
                    obj.icon.custom_icon.url, obj.name
                )
        return obj.name

    amenity_name_with_icon.short_description = 'Nome'

    def icon_preview(self, obj):
        """Mostra un'anteprima dell'icona associata."""
        if obj.icon:
            if obj.icon.icon_type == 'fa':  # Font Awesome
                return format_html('<i class="{}" style="font-size: 24px;"></i>', obj.icon.fa_class)
            elif obj.icon.icon_type == 'custom' and obj.icon.custom_icon:  # Custom icon
                return format_html('<img src="{}" style="height: 24px;">', obj.icon.custom_icon.url)
        return "Nessuna icona associata"

    icon_preview.short_description = "Icona attuale"

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.0/css/all.min.css',)
        }
