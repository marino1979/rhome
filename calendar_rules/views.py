from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from datetime import timedelta
from decimal import Decimal
from .models import PriceRule
from listings.models import Listing
from .managers import CalendarManager

class PriceCalculatorRequestSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1)

class CalculatePriceView(APIView):
    def post(self, request):
        # Validazione input
        serializer = PriceCalculatorRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Recupera dati validati
        data = serializer.validated_data
        try:
            listing = Listing.objects.get(id=data['listing_id'])
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Listing non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Inizializza il calendar manager
        calendar = CalendarManager(listing)
        
        # Verifica disponibilità
        is_available, message = calendar.check_availability(
            data['check_in'], 
            data['check_out']
        )
        if not is_available:
            return Response(
                {'error': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcola prezzi giornalieri
        daily_prices = []
        current_date = data['check_in']
        while current_date < data['check_out']:
            price = calendar.get_price_per_day(current_date)
            note = 'Prezzo base' if price == listing.base_price else 'Prezzo speciale'
            daily_prices.append({
                'date': current_date,
                'price': Decimal(str(price)),  # Convertiamo in Decimal
                'note': note
            })
            current_date += timedelta(days=1)

        # Calcola extra
        extra_guests = max(0, data['guests'] - listing.included_guests)
        extra_guests_fee = Decimal(str(extra_guests)) * listing.extra_guest_fee * len(daily_prices)
        
        extras = {
            'cleaning': listing.cleaning_fee,  # Già Decimal dal modello
            'extra_guests': extra_guests_fee   # Convertito in Decimal
        }

        # Calcola totale mantenendo tutto in Decimal
        total = sum(day['price'] for day in daily_prices) + \
                extras['cleaning'] + \
                extras['extra_guests']

        # Prepara la risposta convertendo i Decimal in float per il JSON
        response_data = {
            'daily_prices': [{
                'date': day['date'],
                'price': float(day['price']),
                'note': day['note']
            } for day in daily_prices],
            'extras': {
                'cleaning': float(extras['cleaning']),
                'extra_guests': float(extras['extra_guests'])
            },
            'total': float(total)
        }

        return Response(response_data)

class BookingCalculatorView(TemplateView):
    template_name = 'calendar_rules/booking_calculator.html'