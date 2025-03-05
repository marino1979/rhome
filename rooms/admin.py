from django.contrib import admin
from .models import RoomType  # Rimuovi Room dall'import
from beds.models import Bed

# Rimuovi tutta la parte RoomAdmin e BedInline

# Lascia solo RoomType
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_have_beds']