from django.db import models
from django.contrib.auth.models import User
from teams.models import Team
from django.utils import timezone


class TeamMessage(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Message types
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('system', 'System Message'),
        ('file', 'File Share'),
    ]
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return ""
    
    def can_edit(self, user):
        """Check if user can edit this message - only message sender"""
        return self.sender == user and self.message_type == 'text'
    
    def can_delete(self, user):
        """Check if user can delete this message - sender or team captain"""
        return self.sender == user or self.team.captain == user


class MessageReaction(models.Model):
    message = models.ForeignKey(TeamMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # Store emoji unicode
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'emoji']
        
    def __str__(self):
        return ""


class MessageRead(models.Model):
    """Track which messages have been read by which users"""
    message = models.ForeignKey(TeamMessage, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        
    def __str__(self):
        return ""