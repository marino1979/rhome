# calendar_rules/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ClosureRule, CheckInOutRule, PriceRule
from .forms import PriceRuleForm
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
            return f"Ogni {days[obj.day_of_week]}"
    get_restriction_display.short_description = 'Restrizione'

    class Media:
        js = ('admin/js/calendar_rules.js',)  # Per gestire la visualizzazione condizionale dei campi

@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    form = PriceRuleForm
    list_display = ['listing', 'start_date', 'end_date', 'get_price_display', 'min_nights']
    list_filter = ['listing']
    search_fields = ['listing__title']

    def save_model(self, request, obj, form, change):
        try:
            # Verifica sovrapposizioni esatte
            existing_exact = PriceRule.objects.filter(
                listing=obj.listing,
                start_date=obj.start_date,
                end_date=obj.end_date
            )
            if obj.pk:
                existing_exact = existing_exact.exclude(pk=obj.pk)

            if existing_exact.exists() and not form.cleaned_data.get('confirm_override'):
                messages.warning(
                    request,
                    'Esiste già una regola per questo periodo. '
                    'Spunta "Sovrascrivi regole esistenti" per procedere.'
                )
                return

            # Verifica sovrapposizioni parziali
            overlapping = PriceRule.objects.filter(
                listing=obj.listing,
                start_date__lte=obj.end_date,
                end_date__gte=obj.start_date
            )
            if obj.pk:
                overlapping = overlapping.exclude(pk=obj.pk)

            if overlapping.exists():
                if form.cleaned_data.get('confirm_override'):
                    self.handle_overlapping_rules(obj, overlapping)
                    messages.success(
                        request,
                        'Regola salvata. Le regole sovrapposte sono state aggiornate.'
                    )
                else:
                    overlap_msg = "Questa regola si sovrappone con:\n"
                    for rule in overlapping:
                        overlap_msg += f"• {rule.start_date} - {rule.end_date}: €{rule.price}\n"
                    overlap_msg += "\nSpunta 'Sovrascrivi regole esistenti' per procedere."
                    messages.warning(request, overlap_msg)
                    return

            super().save_model(request, obj, form, change)

        except Exception as e:
            messages.error(request, f"Errore nel salvare la regola: {str(e)}")

    def handle_overlapping_rules(self, new_rule, overlapping_rules):
        """Gestisce le regole sovrapposte"""
        for old_rule in overlapping_rules:
            # Se la vecchia regola inizia prima
            if old_rule.start_date < new_rule.start_date:
                old_rule.end_date = new_rule.start_date - timedelta(days=1)
                old_rule.save()
                
            # Se la vecchia regola finisce dopo
            if old_rule.end_date > new_rule.end_date:
                PriceRule.objects.create(
                    listing=old_rule.listing,
                    start_date=new_rule.end_date + timedelta(days=1),
                    end_date=old_rule.end_date,
                    price=old_rule.price,
                    min_nights=old_rule.min_nights
                )
            
            # Se la vecchia regola è completamente contenuta
            if (old_rule.start_date >= new_rule.start_date and 
                old_rule.end_date <= new_rule.end_date):
                old_rule.delete()

    def get_price_display(self, obj):
        base_price = obj.listing.base_price
        difference = obj.price - base_price
        color = 'green' if difference > 0 else 'red' if difference < 0 else 'black'
        return format_html(
            '€{} <span style="color: {};">({}€ {})</span>',
            obj.price,
            color,
            abs(difference),
            '+' if difference > 0 else '-'
        )
    get_price_display.short_description = 'Prezzo (differenza)'