from django.contrib import admin
from .models import TeamMessage, MessageReaction, MessageRead


@admin.register(TeamMessage)
class TeamMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'message_type', 'timestamp', 'is_edited']
    list_filter = ['message_type', 'timestamp', 'is_edited', 'team']
    search_fields = ['sender__username', 'team__name']
    readonly_fields = ['timestamp', 'edited_at']
    



@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'emoji', 'timestamp']
    list_filter = ['emoji', 'timestamp']
    search_fields = ['user__username']
    
    def message_preview(self, obj):
        return f"Message {obj.message.id}"
    message_preview.short_description = 'Message'


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['id', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username']
    
    def message_preview(self, obj):
        return f"Message {obj.message.id}"
    message_preview.short_description = 'Message'