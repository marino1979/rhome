from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Autenticazione e Autorizzazione'  # Unifica con il menu esistente
    
    def ready(self):
        """
        Escludi esplicitamente i modelli di allauth e auth da modeltranslation.
        Questo previene l'errore 'super' object has no attribute 'dicts'
        quando modeltranslation cerca di modificare questi modelli.
        """
        try:
            from modeltranslation.translator import translator
            from django.apps import apps
            
            # Lista delle app da escludere completamente
            excluded_apps = [
                'account',      # allauth.account
                'socialaccount', # allauth.socialaccount
                'auth',         # django.contrib.auth (User, Group, Permission)
                'sites',        # django.contrib.sites (Site)
            ]
            
            # Rimuovi i modelli dal registro di traduzione
            for app_name in excluded_apps:
                try:
                    app_config = apps.get_app_config(app_name)
                    
                    # Rimuovi tutti i modelli di questa app dal registro
                    for model in app_config.get_models():
                        # Rimuovi sia il modello che eventuali chiavi alternative
                        if model in translator._registry:
                            del translator._registry[model]
                        # Cerca anche per nome stringa
                        model_name = f"{app_name}.{model.__name__.lower()}"
                        if model_name in translator._registry:
                            del translator._registry[model_name]
                except LookupError:
                    # Se l'app non è ancora caricata, va bene
                    pass
                except Exception:
                    # Se qualcosa va storto, continua
                    pass
            
            # Escludi anche i modelli di allauth dalla lista di modelli da processare
            # Questo previene che modeltranslation li tocchi anche senza registrazione
            try:
                from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
                from allauth.account.models import EmailAddress
                
                excluded_models = [SocialAccount, SocialToken, SocialApp, EmailAddress]
                for model in excluded_models:
                    if model in translator._registry:
                        del translator._registry[model]
            except ImportError:
                pass
            except Exception:
                pass
                
        except ImportError:
            # modeltranslation non è installato, non fare nulla
            pass
        except Exception:
            # Se qualcosa va storto, non bloccare l'avvio
            pass
        
        # Importa la configurazione dell'admin dopo che tutto è pronto
        try:
            import Rhome_book.admin_config
        except ImportError:
            pass
        except Exception:
            pass
