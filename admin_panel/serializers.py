"""
Serializers per le API del pannello admin.
"""
from rest_framework import serializers
from listings.models import Listing
from rooms.models import Room, RoomType
from images.models import Image
from bookings.models import Booking
from calendar_rules.models import PriceRule, ExternalCalendar, ClosureRule
from amenities.models import Amenity


class ImageSerializer(serializers.ModelSerializer):
    """Serializer per le immagini"""
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Image
        fields = ['id', 'file', 'url', 'title', 'alt_text', 'order', 'is_main', 'listing', 'room', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer per i tipi di stanza"""
    class Meta:
        model = RoomType
        fields = ['id', 'name', 'can_have_beds']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer per le stanze"""
    images = ImageSerializer(many=True, read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'listing', 'room_type', 'room_type_name', 'name', 'square_meters', 
                  'description', 'order', 'images']
        read_only_fields = ['id']


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer per i servizi"""
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'category']


class ListingSerializer(serializers.ModelSerializer):
    """Serializer per gli annunci"""
    images = ImageSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    amenities_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Amenity.objects.all(),
        source='amenities',
        write_only=True,
        required=False
    )
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'slug', 'description', 'status',
            'max_guests', 'bedrooms', 'bathrooms',
            'address', 'city', 'zone',
            'base_price', 'cleaning_fee', 'extra_guest_fee', 'included_guests',
            'total_square_meters', 'outdoor_square_meters', 'total_beds', 'total_sleeps',
            'min_booking_advance', 'max_booking_advance', 'gap_between_bookings', 'min_stay_nights',
            'checkin_from', 'checkin_to', 'checkout_time',
            'allow_parties', 'allow_photos', 'allow_smoking',
            'checkin_notes', 'checkout_notes', 'parties_notes', 'photos_notes', 'smoking_notes',
            'images', 'rooms', 'amenities', 'amenities_ids', 'main_image_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_main_image_url(self, obj):
        main_image = obj.main_image
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.file.url)
            return main_image.file.url
        return None


class PriceRuleSerializer(serializers.ModelSerializer):
    """Serializer per le regole di prezzo"""
    class Meta:
        model = PriceRule
        fields = ['id', 'listing', 'start_date', 'end_date', 'price', 'min_nights']
        read_only_fields = ['id']


class ClosureRuleSerializer(serializers.ModelSerializer):
    """Serializer per le regole di chiusura"""
    class Meta:
        model = ClosureRule
        fields = ['id', 'listing', 'start_date', 'end_date', 'reason', 'is_external_booking']
        read_only_fields = ['id']


class ExternalCalendarSerializer(serializers.ModelSerializer):
    """Serializer per i calendari esterni ICAL"""
    last_sync_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ExternalCalendar
        fields = [
            'id', 'listing', 'name', 'provider', 'ical_url',
            'is_active', 'sync_interval_minutes',
            'last_sync', 'last_sync_status', 'last_sync_error',
            'last_sync_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync', 'last_sync_status', 'last_sync_error', 'created_at', 'updated_at']
    
    def get_last_sync_display(self, obj):
        if obj.last_sync:
            return obj.last_sync.strftime('%d/%m/%Y %H:%M')
        return 'Mai sincronizzato'


class BookingSerializer(serializers.ModelSerializer):
    """Serializer per le prenotazioni"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    guest_name = serializers.SerializerMethodField()
    guest_email = serializers.CharField(source='guest.email', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_title', 'guest', 'guest_name', 'guest_email',
            'check_in_date', 'check_out_date', 'num_guests', 'num_adults', 'num_children',
            'base_price_per_night', 'total_nights', 'subtotal', 'cleaning_fee',
            'extra_guest_fee', 'total_amount',
            'status', 'payment_status',
            'special_requests', 'guest_phone', 'guest_email',
            'change_requested', 'change_request_note',
            'check_in_code', 'wifi_password', 'host_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'base_price_per_night', 'total_nights', 'subtotal', 'cleaning_fee',
            'extra_guest_fee', 'total_amount', 'listing_title', 'guest_name', 'guest_email'
        ]
    
    def get_guest_name(self, obj):
        if obj.guest:
            return obj.guest.get_full_name() or obj.guest.username
        return None
