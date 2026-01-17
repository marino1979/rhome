# calendar_rules/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ClosureRule, CheckInOutRule, PriceRule, ExternalCalendar
# PriceRuleForm rimosso - non più utilizzato
from django.contrib import messages  # Questo è l'import corretto
from datetime import timedelta, date  # aggiungiamo l'import di timedelta

@admin.register(ClosureRule)
class ClosureRuleAdmin(admin.ModelAdmin):
    list_display = ['listing', 'start_date', 'end_date', 'is_external_booking', 'reason']
    list_filter = ['is_external_booking', 'listing']
    search_fields = ['listing__title', 'reason']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('listing', ('start_date', 'end_date'))
        }),
        ('Dettagli', {
            'fields': ('is_external_booking', 'reason')
        }),
    )

@admin.register(CheckInOutRule)
class CheckInOutRuleAdmin(admin.ModelAdmin):
    list_display = ['listing', 'rule_type', 'recurrence_type', 'get_restriction_display']
    list_filter = ['rule_type', 'recurrence_type', 'listing']
    search_fields = ['listing__title']
    
    fieldsets = (
        (None, {
            'fields': ('listing', 'rule_type')
        }),
        ('Ricorrenza', {
            'fields': ('recurrence_type', 'specific_date', 'day_of_week'),
            'description': 'Scegli se la regola si applica a una data specifica o a un giorno della settimana'
        }),
    )

    def get_restriction_display(self, obj):
        if obj.recurrence_type == 'specific_date':
            return f"Data: {obj.specific_date}"
        else:
            days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
            return f"Giorno: {days[obj.day_of_week]}"
    get_restriction_display.short_description = 'Restrizione'

@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    # form = PriceRuleForm  # Rimosso - usando ModelForm standard di Django
    list_display = ['listing', 'start_date', 'end_date', 'price', 'min_nights']
    list_filter = ['listing', 'start_date']
    search_fields = ['listing__title']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('listing',)
        }),
        ('Periodo', {
            'fields': (('start_date', 'end_date'),),
            'description': 'Definisci il periodo di validità della regola'
        }),
        ('Prezzo', {
            'fields': ('price',),
            'description': 'Prezzo per notte per questo periodo'
        }),
        ('Regole', {
            'fields': ('min_nights',),
            'classes': ('collapse',),
            'description': 'Soggiorno minimo per questo periodo'
        }),
    )

@admin.register(ExternalCalendar)
class ExternalCalendarAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'listing', 'provider', 'is_active', 
        'last_sync_status_display', 'last_sync'
    ]
    list_filter = ['provider', 'is_active', 'last_sync_status', 'listing']
    search_fields = ['name', 'listing__title', 'ical_url']
    readonly_fields = ['last_sync', 'last_sync_status', 'last_sync_error', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('listing', 'name', 'provider')
        }),
        ('Configurazione iCal', {
            'fields': ('ical_url', 'is_active', 'sync_interval_minutes')
        }),
        ('Stato Sincronizzazione', {
            'fields': ('last_sync', 'last_sync_status', 'last_sync_error'),
            'classes': ('collapse',)
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_selected_calendars']
    
    def last_sync_status_display(self, obj):
        """Mostra lo stato della sincronizzazione con colori"""
        colors = {
            'success': 'green',
            'error': 'red',
            'pending': 'orange',
        }
        color = colors.get(obj.last_sync_status, 'gray')
        status_display = obj.get_last_sync_status_display()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_display
        )
    last_sync_status_display.short_description = 'Stato'
    
    def sync_selected_calendars(self, request, queryset):
        """Azione per sincronizzare i calendari selezionati"""
        from calendar_rules.services.ical_sync import ICalSyncService
        
        synced = 0
        errors = 0
        
        for calendar in queryset:
            if not calendar.is_active:
                self.message_user(
                    request,
                    f'Calendario {calendar.name} non è attivo, saltato.',
                    level=messages.WARNING
                )
                continue
            
            service = ICalSyncService(calendar)
            success, error = service.sync()
            
            if success:
                synced += 1
                self.message_user(
                    request,
                    f'Calendario {calendar.name} sincronizzato con successo.',
                    level=messages.SUCCESS
                )
            else:
                errors += 1
                self.message_user(
                    request,
                    f'Errore sincronizzazione {calendar.name}: {error}',
                    level=messages.ERROR
                )
        
        if synced > 0:
            self.message_user(
                request,
                f'{synced} calendario/i sincronizzato/i con successo.',
                level=messages.SUCCESS
            )
        if errors > 0:
            self.message_user(
                request,
                f'{errors} errore/i durante la sincronizzazione.',
                level=messages.ERROR
            )
    
    sync_selected_calendars.short_description = 'Sincronizza calendari selezionati'