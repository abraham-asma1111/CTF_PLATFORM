"""
Chat admin interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import TeamMessage, MessageRead, MessageReaction


@admin.register(TeamMessage)
class TeamMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'team_link', 'sender_link', 'content_preview', 'message_type', 'reaction_count', 'timestamp', 'is_edited']
    list_filter = ['message_type', 'timestamp', 'team', 'edited_at']
    search_fields = ['content', 'sender__username', 'team__name']
    readonly_fields = ['timestamp', 'edited_at', 'reaction_summary', 'read_count']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    actions = ['delete_selected_messages', 'mark_as_system_message']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('team', 'sender', 'content', 'message_type')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'edited_at', 'reaction_summary', 'read_count'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show message preview with length indicator"""
        preview = obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
        return format_html(
            '<span style="font-family: monospace;">{}</span> <small style="color: #888;">({} chars)</small>',
            preview,
            len(obj.content)
        )
    content_preview.short_description = 'Message'
    
    def team_link(self, obj):
        """Clickable team link"""
        return format_html(
            '<a href="/admin/teams/team/{}/change/" style="color: #00ff88; font-weight: bold;">🛡️ {}</a>',
            obj.team.id,
            obj.team.name
        )
    team_link.short_description = 'Team'
    
    def sender_link(self, obj):
        """Clickable sender link"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="color: #007bff;">👤 {}</a>',
            obj.sender.id,
            obj.sender.username
        )
    sender_link.short_description = 'Sender'
    
    def reaction_count(self, obj):
        """Show reaction count with emoji"""
        count = obj.reactions.count()
        if count > 0:
            return format_html(
                '<span style="background: rgba(0, 255, 136, 0.2); padding: 2px 8px; border-radius: 10px; font-weight: bold;">❤️ {}</span>',
                count
            )
        return format_html('<span style="color: #888;">—</span>')
    reaction_count.short_description = 'Reactions'
    
    def is_edited(self, obj):
        """Show if message was edited"""
        if obj.edited_at:
            return format_html(
                '<span style="color: #ffa500;" title="Edited at {}">✏️ Yes</span>',
                obj.edited_at.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: #888;">—</span>')
    is_edited.short_description = 'Edited'
    
    def reaction_summary(self, obj):
        """Show all reactions with counts"""
        reactions = obj.reactions.values('emoji').annotate(count=Count('emoji')).order_by('-count')
        if reactions:
            summary = ' '.join([f"{r['emoji']} ({r['count']})" for r in reactions])
            return format_html('<span style="font-size: 1.2rem;">{}</span>', summary)
        return "No reactions"
    reaction_summary.short_description = 'Reaction Summary'
    
    def read_count(self, obj):
        """Show how many users read the message"""
        count = obj.read_by.count()
        total = obj.team.members.filter(status='accepted').count()
        percentage = (count / total * 100) if total > 0 else 0
        return format_html(
            '{} / {} members ({}%)',
            count,
            total,
            round(percentage, 1)
        )
    read_count.short_description = 'Read Status'
    
    def delete_selected_messages(self, request, queryset):
        """Bulk delete messages"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Successfully deleted {count} message(s).')
    delete_selected_messages.short_description = 'Delete selected messages'
    
    def mark_as_system_message(self, request, queryset):
        """Mark messages as system messages"""
        count = queryset.update(message_type='system')
        self.message_user(request, f'Marked {count} message(s) as system messages.')
    mark_as_system_message.short_description = 'Mark as system message'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('team', 'sender').prefetch_related('reactions', 'read_by')


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['id', 'message_preview', 'user_link', 'team_name', 'read_at']
    list_filter = ['read_at', 'message__team']
    search_fields = ['user__username', 'message__content', 'message__team__name']
    readonly_fields = ['read_at', 'message_details']
    ordering = ['-read_at']
    date_hierarchy = 'read_at'
    list_per_page = 50
    
    fieldsets = (
        ('Read Information', {
            'fields': ('message', 'user', 'read_at')
        }),
        ('Message Details', {
            'fields': ('message_details',),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """Show message preview"""
        preview = obj.message.content[:40] + '...' if len(obj.message.content) > 40 else obj.message.content
        return format_html('<span style="font-family: monospace;">{}</span>', preview)
    message_preview.short_description = 'Message'
    
    def user_link(self, obj):
        """Clickable user link"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="color: #007bff;">👤 {}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'
    
    def team_name(self, obj):
        """Show team name"""
        return format_html(
            '<a href="/admin/teams/team/{}/change/" style="color: #00ff88;">🛡️ {}</a>',
            obj.message.team.id,
            obj.message.team.name
        )
    team_name.short_description = 'Team'
    
    def message_details(self, obj):
        """Show full message details"""
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
            '<strong>From:</strong> {}<br>'
            '<strong>Team:</strong> {}<br>'
            '<strong>Sent:</strong> {}<br>'
            '<strong>Content:</strong><br><pre style="margin-top: 5px;">{}</pre>'
            '</div>',
            obj.message.sender.username,
            obj.message.team.name,
            obj.message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            obj.message.content
        )
    message_details.short_description = 'Full Message'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('message__team', 'message__sender', 'user')


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'emoji_display', 'message_preview', 'user_link', 'team_name', 'created_at']
    list_filter = ['emoji', 'created_at', 'message__team']
    search_fields = ['user__username', 'message__content', 'message__team__name']
    readonly_fields = ['created_at', 'message_details']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Reaction Information', {
            'fields': ('message', 'user', 'emoji', 'created_at')
        }),
        ('Message Details', {
            'fields': ('message_details',),
            'classes': ('collapse',)
        }),
    )
    
    def emoji_display(self, obj):
        """Show emoji larger"""
        return format_html(
            '<span style="font-size: 1.5rem; background: rgba(0, 255, 136, 0.1); padding: 5px 10px; border-radius: 10px;">{}</span>',
            obj.emoji
        )
    emoji_display.short_description = 'Emoji'
    
    def message_preview(self, obj):
        """Show message preview"""
        preview = obj.message.content[:40] + '...' if len(obj.message.content) > 40 else obj.message.content
        return format_html('<span style="font-family: monospace;">{}</span>', preview)
    message_preview.short_description = 'Message'
    
    def user_link(self, obj):
        """Clickable user link"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="color: #007bff;">👤 {}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'
    
    def team_name(self, obj):
        """Show team name"""
        return format_html(
            '<a href="/admin/teams/team/{}/change/" style="color: #00ff88;">🛡️ {}</a>',
            obj.message.team.id,
            obj.message.team.name
        )
    team_name.short_description = 'Team'
    
    def message_details(self, obj):
        """Show full message details"""
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
            '<strong>From:</strong> {}<br>'
            '<strong>Team:</strong> {}<br>'
            '<strong>Sent:</strong> {}<br>'
            '<strong>Content:</strong><br><pre style="margin-top: 5px;">{}</pre>'
            '</div>',
            obj.message.sender.username,
            obj.message.team.name,
            obj.message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            obj.message.content
        )
    message_details.short_description = 'Full Message'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('message__team', 'message__sender', 'user')
