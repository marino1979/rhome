"""
Patch per disabilitare modeltranslation per i modelli non registrati.
Questo previene l'errore 'super' object has no attribute 'dicts' in tutti i menu admin.
"""
from django.contrib import admin
from django.apps import apps

# Applica la patch dopo che Django è completamente caricato
def patch_modeltranslation_admin():
    """
    Disabilita l'interferenza di modeltranslation per i modelli non registrati.
    """
    try:
        from modeltranslation.translator import translator
        
        # Lista di app che NON devono essere processate da modeltranslation
        excluded_apps = [
            'auth',
            'sites',
            'account',
            'socialaccount',
            'admin',
            'contenttypes',
            'sessions',
            'messages',
        ]
        
        # Per ogni app esclusa, rimuovi i modelli dal registro
        for app_label in excluded_apps:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    # Rimuovi dal registro se presente
                    if model in translator._registry:
                        del translator._registry[model]
            except LookupError:
                pass
            except Exception:
                pass
        
        # Rimuovi anche i modelli di allauth direttamente
        try:
            from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
            from allauth.account.models import EmailAddress
            
            for model in [SocialAccount, SocialToken, SocialApp, EmailAddress]:
                if model in translator._registry:
                    del translator._registry[model]
        except ImportError:
            pass
        except Exception:
            pass
            
    except ImportError:
        # modeltranslation non è installato
        pass
    except Exception:
        # Se qualcosa va storto, non bloccare
        pass

# Esegui la patch quando questo modulo viene importato
patch_modeltranslation_admin()

