"""
Patch per fixare l'errore 'super' object has no attribute 'dicts'
che si verifica quando modeltranslation interferisce con Django Context.
"""
import django
from django.template import context

# Patch per il Context di Django per evitare l'errore con modeltranslation
def patch_django_context():
    """
    Patcha il metodo __copy__ del Context di Django per evitare l'errore
    'super' object has no attribute 'dicts' quando modeltranslation è attivo.
    """
    original_copy = context.Context.__copy__
    
    def patched_copy(self):
        """Versione patchata di __copy__ che gestisce il caso di super() senza dicts"""
        try:
            # Prova il metodo originale
            return original_copy(self)
        except AttributeError as e:
            if "'super' object has no attribute 'dicts'" in str(e):
                # Se fallisce per questo errore, crea una copia manuale
                duplicate = context.Context()
                # Copia i dicts direttamente se esistono
                if hasattr(self, 'dicts'):
                    duplicate.dicts = self.dicts[:] if hasattr(self.dicts, '__getitem__') else list(self.dicts)
                else:
                    duplicate.dicts = []
                # Copia altri attributi se esistono
                for attr in ['autoescape', 'current_app', 'use_l10n', 'use_tz']:
                    if hasattr(self, attr):
                        setattr(duplicate, attr, getattr(self, attr))
                return duplicate
            else:
                # Se è un altro errore, rilanciarlo
                raise
    
    # Applica il patch solo se non è già stato applicato
    if not hasattr(context.Context.__copy__, '_patched'):
        context.Context.__copy__ = patched_copy
        context.Context.__copy__._patched = True

# Esegui il patch quando il modulo viene importato
try:
    patch_django_context()
except Exception:
    # Se il patch fallisce, non bloccare l'avvio
    pass

# Importa la configurazione dell'admin (dopo che Django è configurato)
# Questo viene fatto in users/apps.py ready() per essere sicuri che Django sia pronto
