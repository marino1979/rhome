from django.urls import path
from .views import (
    BookingCalculatorView, 
    calculate_price_api
)
from .views_debug import CalendarDebugView, CalendarDebugPageView

urlpatterns = [
    path('calculate-price/', calculate_price_api, name='calculate-price-api'),  # API endpoint
    path('calculator/', BookingCalculatorView.as_view(), name='booking-calculator'),
    # URL per debug dettagliato del calendario
    path('debug/<int:listing_id>/', CalendarDebugView.as_view(), name='calendar-debug'),
    path('debug-page/<int:listing_id>/', CalendarDebugPageView.as_view(), name='calendar-debug-page'),
]