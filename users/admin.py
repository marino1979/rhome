from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin per il profilo utente"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profilo'
    fields = ('phone',)


class UserAdmin(BaseUserAdmin):
    """Admin personalizzato per User con profilo inline"""
    inlines = (UserProfileInline,)


# Reregistra UserAdmin con il profilo inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# UserProfile è già visibile inline in User, quindi non lo registriamo separatamente
# Se vuoi vederlo separatamente, decommenta il codice qui sotto:
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     """Admin per UserProfile"""
#     list_display = ('user', 'phone', 'created_at', 'updated_at')
#     list_filter = ('created_at', 'updated_at')
#     search_fields = ('user__username', 'user__email', 'phone')
#     raw_id_fields = ('user',)

