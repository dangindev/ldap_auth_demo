
from django.contrib import admin
from .models import LDAPLoginLog, UserProfile

@admin.register(LDAPLoginLog)
class LDAPLoginLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'timestamp', 'success', 'error_code')
    list_filter = ('success', 'error_code', 'timestamp')
    search_fields = ('username', 'error_message')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'title', 'mobile', 'last_ldap_sync')
    search_fields = ('user__username', 'employee_id', 'title')