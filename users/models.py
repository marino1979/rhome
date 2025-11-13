from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Modello esteso per informazioni aggiuntive dell'utente"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Numero di telefono',
        help_text='Formato: +39 123 456 7890 o 123-456-7890'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profilo Utente'
        verbose_name_plural = 'Profili Utenti'
    
    def __str__(self):
        return f'Profilo di {self.user.username}'

