"""
API Views per il pannello admin esterno.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404, render
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile

from listings.models import Listing
from rooms.models import Room, RoomType
from images.models import Image
from bookings.models import Booking
from calendar_rules.models import PriceRule, ExternalCalendar, ClosureRule
from amenities.models import Amenity

from .serializers import (
    ListingSerializer, RoomSerializer, RoomTypeSerializer,
    ImageSerializer, PriceRuleSerializer, ClosureRuleSerializer,
    ExternalCalendarSerializer, BookingSerializer, AmenitySerializer
)


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet per la gestione degli annunci.
    Supporta CRUD completo e upload immagini.
    """
    queryset = Listing.objects.all().prefetch_related('images', 'rooms', 'amenities')
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, id=None):
        """Upload di un'immagine per un annuncio"""
        listing = self.get_object()
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'File non fornito'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_main = request.data.get('is_main', False) == 'true' or request.data.get('is_main', False) is True
        title = request.data.get('title', '')
        alt_text = request.data.get('alt_text', '')
        order = int(request.data.get('order', 0))
        
        # Se questa è l'immagine principale, rimuovi il flag dalle altre
        if is_main:
            Image.objects.filter(listing=listing, is_main=True).update(is_main=False)
        
        image = Image.objects.create(
            listing=listing,
            file=file,
            title=title,
            alt_text=alt_text,
            order=order,
            is_main=is_main
        )
        
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[0-9]+)')
    def delete_image(self, request, id=None, image_id=None):
        """Elimina un'immagine"""
        listing = self.get_object()
        image = get_object_or_404(Image, id=image_id, listing=listing)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='images/(?P<image_id>[0-9]+)/set-main')
    def set_main_image(self, request, id=None, image_id=None):
        """Imposta un'immagine come principale"""
        listing = self.get_object()
        image = get_object_or_404(Image, id=image_id, listing=listing)
        
        # Rimuovi il flag dalle altre immagini
        Image.objects.filter(listing=listing, is_main=True).update(is_main=False)
        
        # Imposta questa come principale
        image.is_main = True
        image.save()
        
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet per la gestione delle stanze.
    """
    queryset = Room.objects.all().prefetch_related('images')
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Room.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, id=None):
        """Upload di un'immagine per una stanza"""
        room = self.get_object()
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'File non fornito'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_main = request.data.get('is_main', False) == 'true' or request.data.get('is_main', False) is True
        title = request.data.get('title', '')
        alt_text = request.data.get('alt_text', '')
        order = int(request.data.get('order', 0))
        
        # Se questa è l'immagine principale, rimuovi il flag dalle altre
        if is_main:
            Image.objects.filter(room=room, is_main=True).update(is_main=False)
        
        image = Image.objects.create(
            room=room,
            listing=room.listing,
            file=file,
            title=title,
            alt_text=alt_text,
            order=order,
            is_main=is_main
        )
        
        serializer = ImageSerializer(image, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[0-9]+)')
    def delete_image(self, request, id=None, image_id=None):
        """Elimina un'immagine"""
        room = self.get_object()
        image = get_object_or_404(Image, id=image_id, room=room)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet per i tipi di stanza (solo lettura)"""
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class PriceRuleViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle regole di prezzo"""
    queryset = PriceRule.objects.all()
    serializer_class = PriceRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = PriceRule.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset.order_by('-start_date')


class ClosureRuleViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle regole di chiusura"""
    queryset = ClosureRule.objects.all()
    serializer_class = ClosureRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = ClosureRule.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset.order_by('start_date')


class ExternalCalendarViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione dei calendari esterni ICAL"""
    queryset = ExternalCalendar.objects.all()
    serializer_class = ExternalCalendarSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = ExternalCalendar.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset
    
    @action(detail=True, methods=['post'], url_path='sync')
    def sync_calendar(self, request, id=None):
        """Sincronizza manualmente un calendario ICAL"""
        calendar = self.get_object()
        
        try:
            from calendar_rules.services.ical_sync import ICalSyncService
            sync_service = ICalSyncService(calendar)
            success, error_message = sync_service.sync()
            
            if success:
                calendar.refresh_from_db()
                serializer = self.get_serializer(calendar)
                return Response({
                    'success': True,
                    'message': 'Sincronizzazione completata',
                    'calendar': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': error_message or 'Errore durante la sincronizzazione'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Errore: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle prenotazioni"""
    queryset = Booking.objects.all().select_related('listing', 'guest')
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Booking.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        status_filter = self.request.query_params.get('status', None)
        
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet per i servizi (solo lettura)"""
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


@staff_member_required
def admin_panel_view(request):
    """View per servire il pannello admin HTML"""
    return render(request, 'admin_panel/index.html')
