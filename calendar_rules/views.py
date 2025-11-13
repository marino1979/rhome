# calendar_rules/views.py
"""
Views per calendar_rules app.
Include view per testing CalendarService e view di base per compatibilità.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView


class BookingCalculatorView(TemplateView):
    """
    View per il calcolatore di prenotazioni.
    Placeholder per compatibilità con URL esistenti.
    """
    template_name = 'calendar_rules/calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Calcolatore Prenotazioni'
        return context


class CalculatePriceView(TemplateView):
    """
    View per il calcolo prezzi.
    Placeholder per compatibilità con URL esistenti.
    """
    template_name = 'calendar_rules/calculate_price.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Calcolo Prezzi'
        return context


@csrf_exempt
def calculate_price_api(request):
    """
    API endpoint per calcolare i prezzi di una prenotazione.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        listing_id = data.get('listing_id')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        guests = data.get('guests', 1)
        
        if not all([listing_id, check_in, check_out]):
            return JsonResponse({'error': 'Parametri mancanti'}, status=400)
        
        from listings.models import Listing
        from datetime import datetime
        
        listing = Listing.objects.get(id=listing_id)
        
        # Converti le stringhe in date
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # Usa CalendarManager per calcolare i prezzi
        from calendar_rules.managers import CalendarManager
        calendar = CalendarManager(listing)
        
        pricing_data = calendar.get_detailed_pricing(check_in_date, check_out_date, guests)
        
        return JsonResponse(pricing_data)
        
    except Listing.DoesNotExist:
        return JsonResponse({'error': 'Listing non trovato'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': f'Errore formato data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Errore interno: {str(e)}'}, status=500)

