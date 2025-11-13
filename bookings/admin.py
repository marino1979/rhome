from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Booking, BookingPayment, MultiBooking, Message


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id',
        'listing_link',
        'guest_name',
        'check_in_date',
        'check_out_date',
        'total_nights',
        'num_guests',
        'multi_booking_link',
        'status_badge',
        'payment_status_badge',
        'total_amount',
        'created_at'
    ]

    list_filter = [
        'status',
        'payment_status',
        'check_in_date',
        'created_at',
        'listing'
    ]

    search_fields = [
        'guest__username',
        'guest__email',
        'guest__first_name',
        'guest__last_name',
        'listing__title',
        'guest_email',
        'guest_phone'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'total_nights',
        'subtotal',
        'total_amount',
        'check_in_code'
    ]

    fieldsets = (
        ('Informazioni Base', {
            'fields': (
                'listing',
                'guest',
                'status',
                'payment_status'
            )
        }),
        ('Date e Ospiti', {
            'fields': (
                'check_in_date',
                'check_out_date',
                'total_nights',
                'num_guests',
                'num_adults',
                'num_children'
            )
        }),
        ('Prezzi', {
            'fields': (
                'base_price_per_night',
                'subtotal',
                'cleaning_fee',
                'extra_guest_fee',
                'total_amount'
            )
        }),
        ('Contatti Ospite', {
            'fields': (
                'guest_email',
                'guest_phone'
            )
        }),
        ('Accesso e Note', {
            'fields': (
                'check_in_code',
                'wifi_password',
                'special_requests',
                'host_notes'
            )
        }),
        ('Timestamp', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def booking_id(self, obj):
        return f"#{obj.pk}"
    booking_id.short_description = "ID"

    def listing_link(self, obj):
        url = reverse('admin:listings_listing_change', args=[obj.listing.pk])
        return format_html('<a href="{}">{}</a>', url, obj.listing.title)
    listing_link.short_description = "Annuncio"

    def guest_name(self, obj):
        return obj.guest.get_full_name() or obj.guest.username
    guest_name.short_description = "Ospite"

    def multi_booking_link(self, obj):
        if obj.multi_booking:
            url = reverse('admin:bookings_multibooking_change', args=[obj.multi_booking.pk])
            return format_html('<a href="{}">Multi#{}</a>', url, obj.multi_booking.pk)
        return "-"
    multi_booking_link.short_description = "Prenotazione Combinata"

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'cancelled': 'red',
            'completed': 'blue',
            'no_show': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Stato"

    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'partial': 'blue',
            'paid': 'green',
            'refunded': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Pagamento"

    def save_model(self, request, obj, form, change):
        """Override per calcolare prezzi al salvataggio"""
        obj.calculate_pricing()
        super().save_model(request, obj, form, change)

    actions = ['confirm_bookings', 'cancel_bookings']

    def confirm_bookings(self, request, queryset):
        updated = queryset.update(status='confirmed')
        # Genera codici di accesso per le prenotazioni confermate
        for booking in queryset:
            if not booking.check_in_code:
                booking.generate_check_in_code()
                booking.save()

        self.message_user(request, f'{updated} prenotazioni confermate.')
    confirm_bookings.short_description = "Conferma prenotazioni selezionate"

    def cancel_bookings(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} prenotazioni cancellate.')
    cancel_bookings.short_description = "Cancella prenotazioni selezionate"


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'booking_link',
        'amount',
        'payment_type',
        'payment_date',
        'payment_method',
        'transaction_id'
    ]

    list_filter = [
        'payment_type',
        'payment_date',
        'payment_method'
    ]

    search_fields = [
        'booking__guest__username',
        'booking__listing__title',
        'transaction_id'
    ]

    def booking_link(self, obj):
        url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
        return format_html('<a href="{}">#{}</a>', url, obj.booking.pk)
    booking_link.short_description = "Prenotazione"


@admin.register(MultiBooking)
class MultiBookingAdmin(admin.ModelAdmin):
    list_display = [
        'multi_booking_id',
        'guest_name',
        'check_in_date',
        'check_out_date',
        'total_nights',
        'total_guests',
        'listings_summary',
        'status_badge',
        'payment_status_badge',
        'total_amount',
        'created_at'
    ]

    list_filter = [
        'status',
        'payment_status',
        'check_in_date',
        'created_at'
    ]

    search_fields = [
        'guest__username',
        'guest__email',
        'guest__first_name',
        'guest__last_name',
        'guest_email',
        'guest_phone'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'total_nights',
        'subtotal',
        'cleaning_fee_total',
        'extra_guest_fee_total',
        'total_amount',
        'individual_bookings_list'
    ]

    fieldsets = (
        ('Informazioni Base', {
            'fields': (
                'guest',
                'status',
                'payment_status'
            )
        }),
        ('Date e Ospiti', {
            'fields': (
                'check_in_date',
                'check_out_date',
                'total_nights',
                'total_guests'
            )
        }),
        ('Prezzi Totali', {
            'fields': (
                'subtotal',
                'cleaning_fee_total',
                'extra_guest_fee_total',
                'total_amount'
            )
        }),
        ('Contatti Ospite', {
            'fields': (
                'guest_email',
                'guest_phone'
            )
        }),
        ('Note', {
            'fields': (
                'special_requests',
                'host_notes'
            )
        }),
        ('Prenotazioni Individuali', {
            'fields': (
                'individual_bookings_list',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def multi_booking_id(self, obj):
        return f"Multi#{obj.pk}"
    multi_booking_id.short_description = "ID"

    def guest_name(self, obj):
        return obj.guest.get_full_name() or obj.guest.username
    guest_name.short_description = "Ospite"

    def listings_summary(self, obj):
        listings = obj.get_listings_names()
        if len(listings) <= 2:
            return ", ".join(listings)
        else:
            return f"{listings[0]}, {listings[1]}, +{len(listings)-2} altri"
    listings_summary.short_description = "Appartamenti"

    def individual_bookings_list(self, obj):
        bookings = obj.individual_bookings.all()
        if not bookings.exists():
            return "Nessuna prenotazione individuale"
        
        html = "<ul>"
        for booking in bookings:
            url = reverse('admin:bookings_booking_change', args=[booking.pk])
            html += f'<li><a href="{url}" target="_blank">#{booking.pk} - {booking.listing.title} ({booking.num_guests} ospiti)</a></li>'
        html += "</ul>"
        return format_html(html)
    individual_bookings_list.short_description = "Prenotazioni Individuali"

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'cancelled': 'red',
            'completed': 'blue',
            'no_show': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Stato"

    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'partial': 'blue',
            'paid': 'green',
            'refunded': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Pagamento"

    def save_model(self, request, obj, form, change):
        """Override per calcolare prezzi al salvataggio"""
        obj.calculate_total_pricing()
        super().save_model(request, obj, form, change)

    actions = ['confirm_multi_bookings', 'cancel_multi_bookings', 'cleanup_incomplete_bookings']

    def confirm_multi_bookings(self, request, queryset):
        """Conferma tutte le prenotazioni combinate selezionate"""
        updated_count = 0
        for multi_booking in queryset:
            # Conferma la prenotazione combinata
            multi_booking.status = 'confirmed'
            multi_booking.save()
            
            # Conferma tutte le prenotazioni individuali
            individual_bookings = multi_booking.individual_bookings.all()
            for booking in individual_bookings:
                booking.status = 'confirmed'
                if not booking.check_in_code:
                    booking.generate_check_in_code()
                booking.save()
            
            updated_count += 1
        
        self.message_user(request, f'{updated_count} prenotazioni combinate confermate.')
    confirm_multi_bookings.short_description = "Conferma prenotazioni combinate selezionate"

    def cancel_multi_bookings(self, request, queryset):
        """Cancella tutte le prenotazioni combinate selezionate"""
        updated_count = 0
        for multi_booking in queryset:
            # Cancella la prenotazione combinata
            multi_booking.status = 'cancelled'
            multi_booking.save()
            
            # Cancella tutte le prenotazioni individuali
            individual_bookings = multi_booking.individual_bookings.all()
            for booking in individual_bookings:
                booking.status = 'cancelled'
                booking.save()
            
            updated_count += 1
        
        self.message_user(request, f'{updated_count} prenotazioni combinate cancellate.')
    cancel_multi_bookings.short_description = "Cancella prenotazioni combinate selezionate"

    def cleanup_incomplete_bookings(self, request, queryset):
        """Elimina prenotazioni combinate senza booking individuali"""
        incomplete_count = 0
        for multi_booking in queryset:
            if not multi_booking.individual_bookings.exists():
                multi_booking.delete()
                incomplete_count += 1
        
        if incomplete_count > 0:
            self.message_user(request, f'{incomplete_count} prenotazioni incomplete eliminate.')
        else:
            self.message_user(request, 'Nessuna prenotazione incompleta trovata.')
    cleanup_incomplete_bookings.short_description = "Elimina prenotazioni incomplete (senza booking individuali)"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'message_id',
        'booking_link',
        'sender_name',
        'recipient_name',
        'message_preview',
        'is_read',
        'created_at'
    ]

    list_filter = [
        'is_read',
        'created_at',
        'booking'
    ]

    search_fields = [
        'sender__username',
        'sender__email',
        'recipient__username',
        'recipient__email',
        'message',
        'booking__id'
    ]

    readonly_fields = [
        'created_at',
        'read_at'
    ]

    fieldsets = (
        ('Informazioni Base', {
            'fields': (
                'booking',
                'sender',
                'recipient'
            )
        }),
        ('Messaggio', {
            'fields': (
                'message',
            )
        }),
        ('Stato Lettura', {
            'fields': (
                'is_read',
                'read_at',
                'created_at'
            )
        })
    )

    def message_id(self, obj):
        return f"#{obj.pk}"
    message_id.short_description = "ID"

    def booking_link(self, obj):
        url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
        return format_html('<a href="{}">#{}</a>', url, obj.booking.pk)
    booking_link.short_description = "Prenotazione"

    def sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username
    sender_name.short_description = "Mittente"

    def recipient_name(self, obj):
        return obj.recipient.get_full_name() or obj.recipient.username
    recipient_name.short_description = "Destinatario"

    def message_preview(self, obj):
        preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return preview
    message_preview.short_description = "Anteprima"