from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, PasswordResetAttempt, BlockedPasswordReset

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'attempts', 'created_at', 'expires_at', 'is_used']
    search_fields = ['email', 'ip_address']
    list_filter = ['is_used', 'created_at']
    readonly_fields = ['created_at']


@admin.register(BlockedPasswordReset)
class BlockedPasswordResetAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'ip_address', 'reason', 'blocked_at', 'blocked_until', 'is_active_status']
    search_fields = ['email', 'username', 'ip_address']
    list_filter = ['blocked_at']
    readonly_fields = ['blocked_at']
    
    def is_active_status(self, obj):
        return obj.is_active()
    is_active_status.boolean = True
    is_active_status.short_description = 'Currently Blocked'
