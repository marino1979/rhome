from django.urls import path
from .views import BookingCalculatorView, CalculatePriceView

urlpatterns = [
    path('calculate-price/', CalculatePriceView.as_view(), name='calculate-price'),
    path('calculator/', BookingCalculatorView.as_view(), name='booking-calculator'),
]