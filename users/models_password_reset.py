from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class PasswordResetAttempt(models.Model):
    """Track password reset attempts for rate limiting"""
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    reset_code = models.CharField(max_length=6)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def increment_attempt(self):
        self.attempts += 1
        self.save()
    
    def __str__(self):
        return f"{self.email} - {self.attempts} attempts"


class BlockedPasswordReset(models.Model):
    """Track blocked IPs and emails from password reset"""
    email = models.EmailField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    reason = models.CharField(max_length=255)
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField()
    
    class Meta:
        ordering = ['-blocked_at']
    
    def is_active(self):
        return timezone.now() < self.blocked_until
    
    def __str__(self):
        return f"Blocked: {self.email or self.ip_address} until {self.blocked_until}"
