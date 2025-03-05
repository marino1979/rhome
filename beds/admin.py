from django.contrib import admin
from .models import Bed, BedType

@admin.register(BedType)
class BedTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity']

