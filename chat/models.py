"""
Team Chat Models
"""
from django.db import models
from django.contrib.auth.models import User
from teams.models import Team


class TeamMessage(models.Model):
    """Messages sent in team chat"""
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('system', 'System Message'),
        ('file', 'File Attachment'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_teammessage'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} in {self.team.name}: {self.content[:50]}"


class MessageRead(models.Model):
    """Track which users have read which messages"""
    message = models.ForeignKey(TeamMessage, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messageread'
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class MessageReaction(models.Model):
    """Emoji reactions to messages"""
    message = models.ForeignKey(TeamMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messagereaction'
        unique_together = ['message', 'user', 'emoji']
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"
