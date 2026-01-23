"""
URLs per le API del pannello admin.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'listings', views.ListingViewSet, basename='listing')
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'room-types', views.RoomTypeViewSet, basename='roomtype')
router.register(r'price-rules', views.PriceRuleViewSet, basename='pricerule')
router.register(r'closure-rules', views.ClosureRuleViewSet, basename='closurerule')
router.register(r'external-calendars', views.ExternalCalendarViewSet, basename='externalcalendar')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'amenities', views.AmenityViewSet, basename='amenity')

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_panel_view, name='admin_panel'),
    path('api/', include(router.urls)),
]
