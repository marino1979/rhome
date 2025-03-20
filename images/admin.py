from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Image
from listings.models import Listing  # Importa il modello Listing

# Non registrare nuovamente il modello Listing
# Registra solo l'admin delle immagini
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title', 'listing', 'room', 'order', 'is_main')
    list_filter = ('is_main', 'listing', 'room')
    
    def thumbnail(self, obj):
        if obj.file:
            return format_html('<img src="{}" width="100" height="auto" style="border-radius: 5px;" />', obj.file.url)
        return "No Image"
    
    thumbnail.short_description = 'Anteprima'

# Definisci il TabularInline per l'uso in ListingAdmin
class ImageInline(admin.TabularInline):
    model = Image
    extra = 0
    fields = ('thumbnail', 'file', 'title', 'alt_text', 'order', 'is_main')
    readonly_fields = ('thumbnail',)
    
    def thumbnail(self, obj):
        if obj.file:
            return format_html('<img src="{}" width="100" height="auto" style="border-radius: 5px;" />', obj.file.url)
        return "No Image"