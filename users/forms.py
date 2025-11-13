from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        label='Nome',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Inserisci il tuo nome'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        label='Cognome',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Inserisci il tuo cognome'
        })
    )
    email = forms.EmailField(
        max_length=254, 
        required=True, 
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'nome@esempio.com'
        }),
        help_text='La tua email sarà utilizzata per le comunicazioni importanti.'
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Numero di telefono',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '+39 123 456 7890'
        }),
        help_text='Inserisci il tuo numero di telefono con prefisso internazionale (es: +39 123 456 7890)'
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Scegli un username unico'
        }),
        help_text='150 caratteri o meno. Lettere, numeri e @/./+/-/_ sono permessi.'
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Inserisci una password sicura'
        })
    )
    password2 = forms.CharField(
        label='Conferma Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Conferma la password'
        })
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Il numero di telefono è obbligatorio.')
        
        # Rimuovi spazi e caratteri speciali per validazione
        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Verifica che contenga almeno 10 cifre (numero minimo)
        digits = ''.join(filter(str.isdigit, phone_clean))
        if len(digits) < 10:
            raise ValidationError('Il numero di telefono deve contenere almeno 10 cifre.')
        
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('L\'email è obbligatoria.')
        
        # Validazione formato email più rigorosa
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_pattern.match(email):
            raise ValidationError('Inserisci un indirizzo email valido.')
        
        # Verifica che l'email non sia già in uso
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Esiste già un account con questa email. Prova a fare il login o usa una email diversa.')
        
        return email.lower()  # Normalizza l'email in minuscolo

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Questo username è già in uso. Scegli un altro username.')
        return username
