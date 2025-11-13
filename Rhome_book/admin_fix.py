"""
Fix per disabilitare modeltranslation per i modelli non registrati nell'admin.
Questo previene l'errore 'super' object has no attribute 'dicts' in tutti i menu admin.
"""
import django
django.setup()

def disable_modeltranslation_for_unregistered():
    """
    Disabilita l'interferenza di modeltranslation per i modelli non registrati.
    """
    try:
        from modeltranslation.admin import TranslatableAdmin
        from django.contrib import admin
        from django.apps import apps
        from modeltranslation.translator import translator
        
        # Sostituisci il metodo get_formset di TranslatableAdmin
        # per non applicare la traduzione ai modelli non registrati
        original_get_formset = TranslatableAdmin.get_formset
        
        def patched_get_formset(self, request, obj=None, **kwargs):
            # Verifica se il modello è registrato per la traduzione
            model = self.model
            if model not in translator._registry:
                # Se non è registrato, usa l'admin standard senza traduzione
                from django.contrib.admin.options import ModelAdmin
                return ModelAdmin.get_formset(self, request, obj, **kwargs)
            # Se è registrato, usa il comportamento originale
            return original_get_formset(self, request, obj, **kwargs)
        
        # Applica il patch solo se necessario
        if not hasattr(TranslatableAdmin.get_formset, '_patched'):
            TranslatableAdmin.get_formset = patched_get_formset
            TranslatableAdmin.get_formset._patched = True
            
    except ImportError:
        # modeltranslation non è installato
        pass
    except Exception:
        # Se qualcosa va storto, non bloccare
        pass

# Esegui quando il modulo viene importato
disable_modeltranslation_for_unregistered()

