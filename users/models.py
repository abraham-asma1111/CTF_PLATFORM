from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
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


class UserProfile(models.Model):
    EDUCATION_CHOICES = [
        ('high_school', 'High School'),
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Postgraduate'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('cyber_security', 'Cyber Security'),
        ('software_engineering', 'Software Engineering'),
        ('computer_science', 'Computer Science'),
        ('it', 'Information Technology'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_score = models.IntegerField(default=0)
    challenges_solved = models.IntegerField(default=0)
    last_submission = models.DateTimeField(null=True, blank=True)
    
    # New fields
    sex = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True, blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES, null=True, blank=True)
    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    verification_code_expires = models.DateTimeField(null=True, blank=True)
    
    # Profile photo
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.total_score} points"
    
    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo.url
        return None
    
    class Meta:
        ordering = ['-total_score', 'last_submission']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
