from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.contrib import messages
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


# Broadcast Email Admin will be added after migration
try:
    from .models import BroadcastEmail, EmailLog
    
    @admin.register(BroadcastEmail)
    class BroadcastEmailAdmin(admin.ModelAdmin):
        list_display = ['title', 'recipient_type_badge', 'status_badge', 'total_recipients', 'emails_sent', 'emails_failed', 'created_by', 'created_at']
        list_filter = ['recipient_type', 'status', 'created_at']
        search_fields = ['title', 'content']
        ordering = ['-created_at']
        readonly_fields = ['created_by', 'created_at', 'sent_at', 'total_recipients', 'emails_sent', 'emails_failed']
        
        fieldsets = (
            ('Email Content', {
                'fields': ('title', 'content')
            }),
            ('Recipients', {
                'fields': ('recipient_type', 'custom_recipients'),
                'description': 'Choose who will receive this email'
            }),
            ('Status & Statistics', {
                'fields': ('status', 'total_recipients', 'emails_sent', 'emails_failed', 'created_by', 'created_at', 'sent_at'),
                'classes': ('collapse',)
            }),
        )
        
        def save_model(self, request, obj, form, change):
            if not change:  # New object
                obj.created_by = request.user
            super().save_model(request, obj, form, change)
        
        def recipient_type_badge(self, obj):
            colors = {
                'all_users': '#3498db',
                'team_captains': '#e74c3c',
                'team_members': '#2ecc71',
                'individual_users': '#f39c12',
                'top_performers': '#9b59b6',
                'custom': '#95a5a6',
            }
            color = colors.get(obj.recipient_type, '#95a5a6')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                color,
                obj.get_recipient_type_display()
            )
        recipient_type_badge.short_description = 'Recipients'
        
        def status_badge(self, obj):
            colors = {
                'draft': '#95a5a6',
                'sending': '#f39c12',
                'sent': '#2ecc71',
                'failed': '#e74c3c',
            }
            color = colors.get(obj.status, '#95a5a6')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                color,
                obj.get_status_display()
            )
        status_badge.short_description = 'Status'
        
        actions = ['send_broadcast_emails']
        
        def send_broadcast_emails(self, request, queryset):
            """Custom action to send broadcast emails"""
            draft_broadcasts = queryset.filter(status='draft')
            if not draft_broadcasts.exists():
                self.message_user(request, 'No draft broadcasts selected.', messages.WARNING)
                return
            
            for broadcast in draft_broadcasts:
                recipients = list(broadcast.get_recipients())
                broadcast.total_recipients = len(recipients)
                broadcast.save()
                
                self.message_user(
                    request, 
                    f'Broadcast "{broadcast.title}" prepared with {len(recipients)} recipients. Use: python manage.py send_broadcast_email --broadcast-id {broadcast.id}',
                    messages.SUCCESS
                )
        
        send_broadcast_emails.short_description = 'Prepare selected broadcasts for sending'


    @admin.register(EmailLog)
    class EmailLogAdmin(admin.ModelAdmin):
        list_display = ['broadcast', 'recipient_email', 'success_badge', 'sent_at', 'error_message']
        list_filter = ['success', 'sent_at', 'broadcast']
        search_fields = ['recipient_email', 'broadcast__title']
        ordering = ['-sent_at']
        readonly_fields = ['broadcast', 'recipient_email', 'sent_at', 'success', 'error_message']
        
        def success_badge(self, obj):
            if obj.success:
                return format_html('<span style="color: #2ecc71; font-weight: bold;">✓ Sent</span>')
            else:
                return format_html('<span style="color: #e74c3c; font-weight: bold;">✗ Failed</span>')
        success_badge.short_description = 'Status'
        
        def has_add_permission(self, request):
            return False

except ImportError:
    # Models not yet migrated
    pass