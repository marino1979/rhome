from django.apps import AppConfig

class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'
    verbose_name = 'Gestione annunci'

    def ready(self):
        print(">>> ListingsConfig ready() chiamato")
        import listings.translation