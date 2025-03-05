from django.apps import AppConfig

class BedsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'beds'

    def ready(self):
        import beds.signals