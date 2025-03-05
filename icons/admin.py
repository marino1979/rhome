from django.contrib import admin
from django.utils.html import format_html
from .models import Icon, IconCategory

@admin.register(IconCategory)
class IconCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    search_fields = ['name']

@admin.register(Icon)
class IconAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'icon_preview', 'icon_type', 'is_active', 'updated_at']
    list_filter = ['category', 'icon_type', 'is_active']
    search_fields = ['name', 'fa_class']
    readonly_fields = ['created_at', 'updated_at', 'icon_preview']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'is_active', 'icon_type')
        }),
        ('Configurazione Icona', {
            'fields': ('fa_class', 'custom_icon', 'icon_preview'),
            'description': 'Il campo appropriato verrà mostrato in base al tipo di icona selezionato'
        }),
        ('Informazioni', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def icon_preview(self, obj):
        if not obj or not obj.icon_type:
            return '-'
        if obj.icon_type == 'fa':
            return format_html('<i class="{}" style="font-size: 20px;"></i>', obj.fa_class)
        elif obj.icon_type == 'custom' and obj.custom_icon:
            return format_html('<img src="{}" style="height: 20px; width: auto;">', obj.custom_icon.url)
        return '-'
    icon_preview.short_description = 'Anteprima'
    
    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.0/css/all.min.css',
                'admin/css/icon-picker.css',
            ]
        }
        js = [
            'admin/js/icon-picker.js'
        ]