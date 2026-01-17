from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm
from bookings.models import Booking, MultiBooking


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Salva l'utente prima di creare il profilo
            user.save()
            
            # Crea EmailAddress per django-allauth (se non esiste già)
            # Questo permette funzionalità future come verifica email
            try:
                from allauth.account.models import EmailAddress
                email = form.cleaned_data.get('email')
                if email:
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=email,
                        defaults={
                            'verified': False,  # Non verificata al momento della registrazione
                            'primary': True,    # Prima email = primaria
                        }
                    )
            except ImportError:
                # allauth non installato, salta
                pass
            except Exception:
                # Se fallisce, continua comunque
                pass
            
            # Salva il numero di telefono nel profilo
            phone = form.cleaned_data.get('phone')
            from .models import UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'phone': phone}
            )
            
            # Specifica il backend quando ci sono più authentication backends
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registrazione completata! Benvenuto/a.')
            return redirect('account:dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    from bookings.models import Message
    from django.utils import timezone
    from datetime import timedelta

    # Prendi SOLO le prenotazioni singole che NON fanno parte di un multi-booking
    single_bookings = Booking.objects.filter(
        guest=request.user,
        multi_booking__isnull=True  # Escludi quelle che fanno parte di combinazioni
    ).select_related('listing').prefetch_related('messages').order_by('-check_in_date')

    # Prendi tutte le multi-bookings
    multi_bookings = MultiBooking.objects.filter(
        guest=request.user
    ).prefetch_related('individual_bookings__listing').order_by('-check_in_date')

    # Crea una lista unificata di tutte le prenotazioni con un tipo identificativo
    all_bookings = []

    # Aggiungi multi-bookings
    for mb in multi_bookings:
        mb.booking_type = 'multi'
        # can_cancel è già una @property nel modello, non serve impostarlo
        all_bookings.append(mb)

    # Aggiungi single bookings con info messaggi
    for booking in single_bookings:
        booking.booking_type = 'single'
        booking.has_unread_messages = Message.objects.filter(
            booking=booking,
            recipient=request.user,
            is_read=False
        ).exists()
        # can_cancel è già una @property nel modello, non serve impostarlo
        all_bookings.append(booking)

    # Ordina tutto per data di check-in (più recente prima)
    all_bookings.sort(key=lambda x: x.check_in_date, reverse=True)

    return render(request, 'account/dashboard.html', {
        'all_bookings': all_bookings,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        # Aggiorna semplicemente i campi base dell'utente
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        email = request.POST.get('email', user.email)
        if email and email != user.email:
            if Booking.objects.filter(guest_email=email).exists():
                # non blocchiamo, ma segnaliamo
                messages.info(request, 'Nota: ci sono prenotazioni con questa email.')
            user.email = email
        user.save()
        
        # Aggiorna il profilo con il telefono
        from .models import UserProfile
        phone = request.POST.get('phone', '')
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save()
        
        messages.success(request, 'Profilo aggiornato correttamente.')
        return redirect('account:profile')

    # Carica il profilo per mostrare il telefono
    from .models import UserProfile
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    return render(request, 'account/profile.html', {
        'user_profile': user_profile
    })


def logout_view(request):
    """View personalizzata per il logout - gestisce GET e POST"""
    logout(request)
    messages.success(request, 'Logout effettuato con successo.')
    return redirect('home')
