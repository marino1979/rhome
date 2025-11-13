"""
Configurazione personalizzata dell'admin Django per organizzare meglio i menu.
"""
from django.contrib import admin
from django.contrib.sites.models import Site

# Nascondi Site dall'admin principale
try:
    admin.site.unregister(Site)
except admin.sites.NotRegistered:
    pass

# Nascondi completamente i menu account e socialaccount
# I modelli essenziali vengono mostrati nel menu auth
try:
    from allauth.account.models import EmailAddress
    from allauth.account.admin import EmailAddressAdmin as AllauthEmailAddressAdmin
    from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
    from allauth.socialaccount.admin import SocialAccountAdmin as AllauthSocialAccountAdmin, SocialAppAdmin as AllauthSocialAppAdmin
    
    # Nascondi tutti i modelli di account e socialaccount
    for model in [EmailAddress, SocialAccount, SocialToken, SocialApp]:
        try:
            admin.site.unregister(model)
        except admin.sites.NotRegistered:
            pass
    
    # Reregistra i modelli essenziali nel menu auth
    # Modifica l'app_label per farli apparire tutti nello stesso menu
    class SocialAppAdmin(AllauthSocialAppAdmin):
        pass
    
    class SocialAccountAdmin(AllauthSocialAccountAdmin):
        pass
    
    class EmailAddressAdmin(AllauthEmailAddressAdmin):
        pass
    
    # Registra i modelli
    admin.site.register(SocialApp, SocialAppAdmin)
    admin.site.register(SocialAccount, SocialAccountAdmin)
    admin.site.register(EmailAddress, EmailAddressAdmin)
    
    # Modifica l'app_label per raggruppare tutto in auth
    # Questo fa apparire i modelli nel menu "Autenticazione e Autorizzazione"
    if hasattr(SocialApp._meta, 'app_label'):
        SocialApp._meta.app_label = 'auth'
    if hasattr(SocialAccount._meta, 'app_label'):
        SocialAccount._meta.app_label = 'auth'
    if hasattr(EmailAddress._meta, 'app_label'):
        EmailAddress._meta.app_label = 'auth'
    
except ImportError:
    # Se non riesci a importare, usa admin semplici
    try:
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount, SocialApp
        
        for model in [EmailAddress, SocialAccount, SocialApp]:
            try:
                admin.site.unregister(model)
            except admin.sites.NotRegistered:
                pass
        
        # Reregistra con admin semplici
        @admin.register(SocialApp)
        class SimpleSocialAppAdmin(admin.ModelAdmin):
            list_display = ('name', 'provider', 'client_id')
            list_filter = ('provider',)
            search_fields = ('name', 'client_id')
        
        @admin.register(SocialAccount)
        class SimpleSocialAccountAdmin(admin.ModelAdmin):
            list_display = ('user', 'provider', 'uid', 'date_joined')
            list_filter = ('provider', 'date_joined')
            search_fields = ('user__username', 'user__email', 'uid')
            raw_id_fields = ('user',)
        
        @admin.register(EmailAddress)
        class SimpleEmailAddressAdmin(admin.ModelAdmin):
            list_display = ('email', 'user', 'verified', 'primary')
            list_filter = ('verified', 'primary')
            search_fields = ('email', 'user__username')
            raw_id_fields = ('user',)
        
        # Modifica app_label
        SocialApp._meta.app_label = 'auth'
        SocialAccount._meta.app_label = 'auth'
        EmailAddress._meta.app_label = 'auth'
        
    except Exception:
        pass
except Exception:
    pass

# Personalizza i nomi delle app nell'admin
admin.site.site_header = 'Rhome Book - Amministrazione'
admin.site.site_title = 'Rhome Book Admin'
admin.site.index_title = 'Pannello di Controllo'

# Nascondi completamente le app account e socialaccount dall'admin
# Modificando il verbose_name a stringa vuota, Django non le mostra nel menu
try:
    from django.apps import apps
    account_app = apps.get_app_config('account')
    account_app.verbose_name = ''  # Menu nascosto
    socialaccount_app = apps.get_app_config('socialaccount')
    socialaccount_app.verbose_name = ''  # Menu nascosto
except Exception:
    pass

