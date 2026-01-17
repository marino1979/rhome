from django.contrib import admin
from django.urls import path  # Aggiunto import di path
from django.contrib import messages  # Aggiunto import di messages
from django.shortcuts import redirect, render, get_object_or_404  # Aggiunto import di redirect e render
from django.http import JsonResponse
from django.utils.html import format_html
from datetime import date, timedelta
from .models import Listing, ListingGroup, Review
from rooms.models import Room
from beds.models import Bed
from images.models import Image
from listings.services.review_sync import AirbnbReviewSync, AirbnbReviewSyncError
# Temporaneamente disabilitato per risolvere errore di compatibilità
# from modeltranslation.admin import TranslationAdmin,TabbedTranslationAdmin


class BedInline(admin.TabularInline):
    model = Bed
    extra = 1
    fields = ['bed_type', 'quantity', 'room']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            if request._obj_ is not None:  # se stiamo modificando un annuncio esistente
                kwargs["queryset"] = Room.objects.filter(listing=request._obj_)
            else:  # se stiamo creando un nuovo annuncio
                kwargs["queryset"] = Room.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RoomInline(admin.StackedInline):
    model = Room
    extra = 1
    can_delete = True
    show_change_link = True


class ImageInline(admin.TabularInline):  # Usa StackedInline se preferisci un layout verticale
    model = Image
    extra = 1
    fields = ("thumbnail", "file", "title", "alt_text", "order", "is_main", "room")  # Aggiungi thumbnail
    readonly_fields = ("thumbnail",)  # Dichiara thumbnail come campo readonly
    ordering = ("order",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            # Ottieni l'annuncio (listing) corrente
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                kwargs["queryset"] = Room.objects.filter(listing_id=obj_id)
            else:
                kwargs["queryset"] = Room.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
    def thumbnail(self, obj):
        if obj.file:
            return format_html('<img src="{}" width="100" height="auto" style="border-radius: 5px;" />', obj.file.url)
        return "No Image"


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ('reviewer_name', 'overall_rating', 'review_date', 'is_airbnb_review', 'review_text_preview')
    readonly_fields = ('reviewer_name', 'overall_rating', 'review_date', 'is_airbnb_review', 'review_text_preview')
    can_delete = False
    show_change_link = True
    
    def review_text_preview(self, obj):
        if obj.review_text:
            return obj.review_text[:100] + "..." if len(obj.review_text) > 100 else obj.review_text
        return "-"
    review_text_preview.short_description = 'Anteprima'
    
    def is_airbnb_review(self, obj):
        return "✓" if obj.is_airbnb_review else "✗"
    is_airbnb_review.short_description = 'Airbnb'
    
    def has_add_permission(self, request, obj=None):
        # Le recensioni Airbnb vengono aggiunte solo tramite sincronizzazione
        # Le recensioni proprietarie possono essere aggiunte manualmente
        return True

class ListingAdmin(admin.ModelAdmin):
    inlines = [RoomInline, BedInline, ImageInline, ReviewInline]
    list_display = ['title', 'bedrooms', 'total_beds', 'reviews_count_display']
    change_form_template = 'admin/listing_change_form.html'
    
    def reviews_count_display(self, obj):
        count = obj.get_reviews_count()
        avg = obj.get_average_rating()
        if avg:
            return f"{count} recensioni ({avg}⭐)"
        return f"{count} recensioni"
    reviews_count_display.short_description = 'Recensioni'
    
    def get_queryset(self, request):
        """Override per gestire eventuali record orfani"""
        from django.db import models
        qs = super().get_queryset(request)
        # Usa select_related e prefetch_related per ottimizzare le query
        # ma evita di fare join che potrebbero causare problemi
        return qs
   
     # Aggiungi questi metodi per distinguere tra add_view e change_view
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_image_upload'] = False  # Nascondi il pulsante in fase di creazione
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_image_upload'] = True  # Mostra il pulsante in fase di modifica
        return super().change_view(request, object_id, form_url, extra_context)
    
    def changelist_view(self, request, extra_context=None):
        """Override per gestire errori di integrità durante la visualizzazione della lista"""
        from django.db import IntegrityError, connection
        from django.contrib import messages
        import traceback
        
        try:
            # Se è una richiesta POST (azione bulk), gestisci prima le azioni
            if request.method == 'POST':
                # Verifica se c'è un'azione selezionata
                action = request.POST.get('action')
                if action and action != 'delete_selected':
                    # Per azioni diverse dalla cancellazione, procedi normalmente
                    return super().changelist_view(request, extra_context)
                # Per la cancellazione, usa il nostro metodo personalizzato
                if action == 'delete_selected':
                    from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
                    selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
                    if selected:
                        queryset = self.get_queryset(request).filter(pk__in=selected)
                        self.delete_queryset(request, queryset)
                        # Dopo la cancellazione, redirect invece di mostrare la lista
                        from django.shortcuts import redirect
                        return redirect(request.path)
            
            return super().changelist_view(request, extra_context)
        except IntegrityError as e:
            # Se c'è un errore di integrità, mostra un messaggio più chiaro
            error_details = traceback.format_exc()
            error_msg = str(e)
            
            # Prova a estrarre informazioni più dettagliate dall'errore
            if 'FOREIGN KEY constraint failed' in error_msg:
                # Cerca di capire quale tabella sta causando il problema
                messages.error(
                    request, 
                    f'Errore di integrità del database: una foreign key constraint è fallita. '
                    f'Questo potrebbe essere causato da record orfani nel database. '
                    f'Errore: {error_msg[:200]}'
                )
            
            # Log dell'errore completo per debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'IntegrityError in changelist_view: {error_details}')
            
            # Stampa anche nella console per debugging immediato
            print("=" * 60)
            print("INTEGRITY ERROR DETTAGLIATO:")
            print("=" * 60)
            print(error_details)
            print("=" * 60)
            
            raise
        except Exception as e:
            # Altri errori
            error_details = traceback.format_exc()
            messages.error(request, f'Errore imprevisto: {str(e)}')
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error in changelist_view: {error_details}')
            raise
    
    def delete_queryset(self, request, queryset):
        """Override per gestire correttamente la cancellazione di più listing"""
        from beds.models import Bed
        from rooms.models import Room
        from images.models import Image
        from bookings.models import Booking
        from calendar_rules.models import CheckInOutRule, ClosureRule, PriceRule, ExternalCalendar
        from django.db import connection, transaction
        
        count = queryset.count()
        try:
            # Disabilita temporaneamente i foreign key constraints per SQLite
            with connection.cursor() as cursor:
                # Per SQLite, disabilita i foreign key checks
                cursor.execute("PRAGMA foreign_keys = OFF")
            
            with transaction.atomic():
                for listing in queryset:
                    # Rimuovi le relazioni ManyToMany prima
                    listing.amenities.clear()
                    
                    # Cancella TUTTE le relazioni manualmente in ordine
                    # 1. Bed (che hanno SET_NULL su room)
                    Bed.objects.filter(listing=listing).delete()
                    
                    # 2. Room
                    Room.objects.filter(listing=listing).delete()
                    
                    # 3. Images
                    Image.objects.filter(listing=listing).delete()
                    
                    # 4. Calendar rules
                    CheckInOutRule.objects.filter(listing=listing).delete()
                    ClosureRule.objects.filter(listing=listing).delete()
                    PriceRule.objects.filter(listing=listing).delete()
                    ExternalCalendar.objects.filter(listing=listing).delete()
                    
                    # 5. Reviews (se esiste il modello)
                    try:
                        from listings.models import Review
                        Review.objects.filter(listing=listing).delete()
                    except:
                        pass
                    
                    # 6. Bookings e le loro relazioni
                    bookings = Booking.objects.filter(listing=listing)
                    for booking in bookings:
                        # Cancella prima i Message associati
                        try:
                            from bookings.models import Message
                            Message.objects.filter(booking=booking).delete()
                        except:
                            pass
                        # Cancella i Payment associati
                        try:
                            from bookings.models import Payment
                            Payment.objects.filter(booking=booking).delete()
                        except:
                            pass
                    # Poi cancella i Booking
                    bookings.delete()
                    
                    # 7. Infine cancella il Listing stesso
                    listing.delete()
            
            # Riabilita i foreign key constraints
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = ON")
            
            messages.success(request, f'{count} annuncio/i cancellato/i con successo.')
        except Exception as e:
            # Assicurati di riabilitare i constraint anche in caso di errore
            try:
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA foreign_keys = ON")
            except:
                pass
            messages.error(request, f'Errore durante la cancellazione: {str(e)}')
            import traceback
            print("=" * 60)
            print("ERRORE DURANTE CANCELLAZIONE:")
            print("=" * 60)
            print(traceback.format_exc())
            print("=" * 60)
            raise
    
    def delete_model(self, request, obj):
        """Override per gestire correttamente la cancellazione di un singolo listing"""
        from beds.models import Bed
        from rooms.models import Room
        from images.models import Image
        from bookings.models import Booking
        from calendar_rules.models import CheckInOutRule, ClosureRule, PriceRule, ExternalCalendar
        from django.db import connection, transaction
        
        listing_title = obj.title
        try:
            # Disabilita temporaneamente i foreign key constraints per SQLite
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = OFF")
            
            with transaction.atomic():
                # Rimuovi le relazioni ManyToMany prima
                obj.amenities.clear()
                
                # Cancella TUTTE le relazioni manualmente in ordine
                # 1. Bed
                Bed.objects.filter(listing=obj).delete()
                
                # 2. Room
                Room.objects.filter(listing=obj).delete()
                
                # 3. Images
                Image.objects.filter(listing=obj).delete()
                
                # 4. Calendar rules
                CheckInOutRule.objects.filter(listing=obj).delete()
                ClosureRule.objects.filter(listing=obj).delete()
                PriceRule.objects.filter(listing=obj).delete()
                ExternalCalendar.objects.filter(listing=obj).delete()
                
                # 5. Reviews (se esiste il modello)
                try:
                    from listings.models import Review
                    Review.objects.filter(listing=obj).delete()
                except:
                    pass
                
                # 6. Bookings e le loro relazioni
                bookings = Booking.objects.filter(listing=obj)
                for booking in bookings:
                    # Cancella prima i Message associati
                    try:
                        from bookings.models import Message
                        Message.objects.filter(booking=booking).delete()
                    except:
                        pass
                    # Cancella i Payment associati
                    try:
                        from bookings.models import Payment
                        Payment.objects.filter(booking=booking).delete()
                    except:
                        pass
                # Poi cancella i Booking
                bookings.delete()
                
                # 7. Infine cancella il Listing
                obj.delete()
            
            # Riabilita i foreign key constraints
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = ON")
            
            messages.success(request, f'Annuncio "{listing_title}" cancellato con successo.')
        except Exception as e:
            # Assicurati di riabilitare i constraint anche in caso di errore
            try:
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA foreign_keys = ON")
            except:
                pass
            messages.error(request, f'Errore durante la cancellazione: {str(e)}')
            import traceback
            print("=" * 60)
            print("ERRORE DURANTE CANCELLAZIONE:")
            print("=" * 60)
            print(traceback.format_exc())
            print("=" * 60)
            raise
    

    
    fieldsets = (
        ('📍 Posizione', {
            'fields': ('address', 'city', 'zone')
        }),
        ('🏠 Proprietà', {
            'fields': (
                'title',
                'description',
                'total_square_meters', 'outdoor_square_meters',
                'bedrooms', 'bathrooms', 'total_beds', 'total_sleeps',
                'max_guests', 'included_guests',
                'amenities'
            )
        }),
        ('💶 Prezzi e prenotazione', {
            'fields': (
                'base_price', 'cleaning_fee', 'extra_guest_fee',
                'min_stay_nights', 'gap_between_bookings',
                'min_booking_advance', 'max_booking_advance'
            )
        }),
        ('🕒 Regole della casa', {
            'fields': (
                'checkin_from', 'checkin_to', 'checkout_time',
                'allow_parties', 'allow_photos', 'allow_smoking',
                'checkin_notes',
                'checkout_notes',
                'parties_notes', 'photos_notes', 'smoking_notes'
            )
        }),
        ('🔗 Integrazioni', {
            'fields': (
                'airbnb_listing_url',
                'airbnb_reviews_last_synced',
                'sync_reviews_button',
                'airbnb_cleanliness_avg',
                'airbnb_accuracy_avg',
                'airbnb_checkin_avg',
                'airbnb_communication_avg',
                'airbnb_location_avg',
                'airbnb_value_avg',
            ),
            'description': 'URL dell\'annuncio su Airbnb per sincronizzazione recensioni. Le medie aggregate possono essere inserite manualmente o sincronizzate da Airbnb.'
        }),
        ('⚙️ Sistema', {
            'fields': ('slug', 'status', 'created_at', 'updated_at')
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'airbnb_reviews_last_synced', 'sync_reviews_button')
    
    def sync_reviews_button(self, obj):
        """Pulsante per sincronizzare le recensioni"""
        if obj and obj.pk:
            from django.utils.html import format_html
            from django.urls import reverse
            url = reverse('admin:listing-sync-airbnb-reviews', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" style="background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 5px;">'
                '🔄 Sincronizza Recensioni Airbnb</a>',
                url
            )
        return "-"
    sync_reviews_button.short_description = 'Sincronizza Recensioni'
    sync_reviews_button.allow_tags = True
    def get_form(self, request, obj=None, **kwargs):
        # Passa l'oggetto listing alla inline
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:listing_id>/upload-images/', self.admin_site.admin_view(self.multiple_images_upload_view), name='listing-upload-images'),
            path('<int:listing_id>/sync-airbnb-reviews/', self.admin_site.admin_view(self.sync_airbnb_reviews_view), name='listing-sync-airbnb-reviews'),
        ]
        return custom_urls + urls

    
    def multiple_images_upload_view(self, request, listing_id):
        listing = self.get_object(request, listing_id)
        
        # Ottieni tutte le stanze dell'annuncio
        rooms = Room.objects.filter(listing=listing)
        
        if request.method == 'POST':
            files = request.FILES.getlist('images')
            room_id = request.POST.get('room', None)  # Ottieni la stanza selezionata
            
            try:
                room = Room.objects.get(id=room_id) if room_id else None
            except Room.DoesNotExist:
                room = None
            
            for index, f in enumerate(files):
                highest_order = Image.objects.filter(listing=listing).order_by('-order').first()
                start_order = (highest_order.order + 1) if highest_order else 0
                
                Image.objects.create(
                    file=f,
                    listing=listing,
                    room=room,  # Associa la stanza
                    order=start_order + index,
                    title=f.name
                )
            
            messages.success(request, f'{len(files)} immagini caricate con successo')
            return redirect('admin:listings_listing_change', listing_id)
            
        context = {
            'title': f'Upload multiple immagini per {listing}',
            'listing': listing,
            'rooms': rooms,  # Passa le stanze al template
            'opts': self.model._meta,
            'original': listing,
    }
        return render(request, 'admin/multiple_images_upload.html', context)
    
    def sync_airbnb_reviews_view(self, request, listing_id):
        """View per sincronizzare le recensioni da Airbnb"""
        listing = get_object_or_404(Listing, pk=listing_id)
        
        if request.method == 'POST':
            try:
                # Ottieni parametri dal form
                airbnb_url = request.POST.get('airbnb_url') or listing.airbnb_listing_url
                language = request.POST.get('language', 'it')
                min_rating = request.POST.get('min_rating')
                date_filter = request.POST.get('date_filter', 'last_year')
                proxy_url = request.POST.get('proxy_url', '')
                
                if not airbnb_url:
                    messages.error(request, "URL Airbnb non specificato. Inseriscilo nel campo 'URL Listing Airbnb' o nel form.")
                    return redirect('admin:listings_listing_change', listing_id)
                
                # Converti min_rating
                min_rating_float = None
                if min_rating and min_rating != 'all':
                    try:
                        min_rating_float = float(min_rating)
                    except ValueError:
                        pass
                
                # Calcola date_from in base al filtro
                date_from = None
                if date_filter == 'last_year':
                    date_from = date.today() - timedelta(days=365)
                elif date_filter == 'last_6_months':
                    date_from = date.today() - timedelta(days=180)
                elif date_filter == 'last_3_months':
                    date_from = date.today() - timedelta(days=90)
                # 'all' = None (nessun filtro data)
                
                # Log per debug
                if date_from:
                    messages.info(request, f"Filtro data applicato: solo recensioni dal {date_from.strftime('%d/%m/%Y')} in poi")
                else:
                    messages.info(request, "Nessun filtro data: sincronizzazione di tutte le recensioni disponibili")
                
                # Esegui sincronizzazione
                sync_service = AirbnbReviewSync(
                    listing=listing,
                    airbnb_url=airbnb_url,
                    language=language,
                    proxy_url=proxy_url
                )
                
                stats = sync_service.sync_reviews(
                    min_rating=min_rating_float,
                    date_from=date_from
                )
                
                # Messaggio di successo
                created_msg = f"{stats.get('created', 0)} create" if stats.get('created', 0) > 0 else ""
                updated_msg = f"{stats.get('updated', 0)} aggiornate" if stats.get('updated', 0) > 0 else ""
                sync_details = ", ".join(filter(None, [created_msg, updated_msg]))
                
                # Controlla se ci sono categorie salvate
                from listings.models import Review
                categories_count = Review.objects.filter(
                    listing=listing,
                    cleanliness_rating__isnull=False
                ).count()
                
                message = (
                    f"Sincronizzazione completata: {stats['synced']} recensioni sincronizzate"
                    + (f" ({sync_details})" if sync_details else "") +
                    f", {stats['skipped']} saltate, {stats['errors']} errori. "
                    f"Totale trovate: {stats['total_found']}"
                )
                
                if categories_count == 0:
                    message += " ⚠️ ATTENZIONE: Nessuna recensione con categorie salvata! Controlla il terminale del server per i dettagli."
                else:
                    message += f" ✅ Recensioni con categorie: {categories_count}"
                
                messages.success(request, message)
                
            except AirbnbReviewSyncError as e:
                messages.error(request, f"Errore durante sincronizzazione: {str(e)}")
            except Exception as e:
                messages.error(request, f"Errore imprevisto: {str(e)}")
            
            return redirect('admin:listings_listing_change', listing_id)
        
        # GET: mostra form
        context = {
            'title': f'Sincronizza Recensioni Airbnb - {listing.title}',
            'listing': listing,
            'opts': self.model._meta,
            'original': listing,
            'has_view_permission': True,
            'has_change_permission': True,
        }
        return render(request, 'admin/sync_airbnb_reviews.html', context)

class ListingGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'listings_count', 'total_capacity', 'total_bedrooms', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['listings']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informazioni Gruppo', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Appartamenti', {
            'fields': ('listings',),
            'description': 'Seleziona gli appartamenti che possono essere prenotati insieme'
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def listings_count(self, obj):
        return obj.listings.count()
    listings_count.short_description = 'Num. Appartamenti'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('listings')
    
    def get_readonly_fields(self, request, obj=None):
        # I campi statistiche sono readonly solo per oggetti esistenti
        if obj:  # Modifica di un oggetto esistente
            return ['created_at', 'updated_at', 'total_capacity', 'total_bedrooms', 'total_bathrooms']
        else:  # Creazione di un nuovo oggetto
            return ['created_at', 'updated_at']
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # Aggiungi le statistiche solo per oggetti esistenti
        if obj:
            # Trova il fieldset Sistema e aggiungi le statistiche prima
            new_fieldsets = []
            for name, options in fieldsets:
                if name == 'Sistema':
                    # Aggiungi statistiche prima del sistema
                    new_fieldsets.append(('Statistiche', {
                        'fields': ('total_capacity', 'total_bedrooms', 'total_bathrooms'),
                        'classes': ('collapse',)
                    }))
                new_fieldsets.append((name, options))
            return new_fieldsets
        
        return fieldsets

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer_name', 'listing', 'overall_rating', 'review_date', 'is_airbnb_review_display', 'is_verified']
    list_filter = ['review_date', 'overall_rating', 'is_verified', 'listing']
    search_fields = ['reviewer_name', 'review_text', 'listing__title']
    readonly_fields = ['airbnb_review_id', 'airbnb_listing_url', 'created_at', 'updated_at', 'last_synced']
    date_hierarchy = 'review_date'
    
    fieldsets = (
        ('Recensore', {
            'fields': ('reviewer_name', 'reviewer_location', 'reviewer_avatar_url')
        }),
        ('Contenuto', {
            'fields': ('review_text', 'review_date', 'stay_date')
        }),
        ('Rating', {
            'fields': (
                'overall_rating',
                ('cleanliness_rating', 'accuracy_rating', 'checkin_rating'),
                ('communication_rating', 'location_rating', 'value_rating')
            )
        }),
        ('Risposta Host', {
            'fields': ('host_response', 'host_response_date'),
            'classes': ('collapse',)
        }),
        ('Metadati Airbnb', {
            'fields': ('airbnb_review_id', 'airbnb_listing_url', 'last_synced'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('listing', 'is_verified', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_airbnb_review_display(self, obj):
        return "✓ Airbnb" if obj.is_airbnb_review else "✗ Sito"
    is_airbnb_review_display.short_description = 'Fonte'
    
    def get_readonly_fields(self, request, obj=None):
        # Se è una recensione Airbnb, rendi readonly anche alcuni campi
        if obj and obj.is_airbnb_review:
            # Converte readonly_fields in lista, aggiunge i campi, e ritorna come tupla
            readonly_list = list(self.readonly_fields) + ['reviewer_name', 'review_text', 'overall_rating', 'review_date']
            return tuple(readonly_list)
        return self.readonly_fields


# Registra correttamente il modello (senza il decoratore)
admin.site.register(Listing, ListingAdmin)
admin.site.register(ListingGroup, ListingGroupAdmin)
admin.site.register(Review, ReviewAdmin)