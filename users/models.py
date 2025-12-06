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


class BroadcastEmail(models.Model):
    """Broadcast email system for admins"""
    RECIPIENT_CHOICES = [
        ('all_users', 'All Users'),
        ('team_captains', 'Team Captains Only'),
        ('team_members', 'Team Members Only'),
        ('individual_users', 'Individual Users (No Team)'),
        ('top_performers', 'Top 10 Users'),
        ('custom', 'Custom Recipients'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    title = models.CharField(max_length=200, help_text='Email subject line')
    content = models.TextField(help_text='Email content (HTML supported)')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES)
    custom_recipients = models.TextField(
        blank=True, 
        help_text='Email addresses separated by commas (for custom recipients)'
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='broadcast_emails')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_failed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_recipient_type_display()} ({self.status})"
    
    def get_recipients(self):
        """Get list of email addresses based on recipient type"""
        from teams.models import Team, TeamMembership
        
        if self.recipient_type == 'all_users':
            return User.objects.filter(is_active=True).values_list('email', flat=True)
        
        elif self.recipient_type == 'team_captains':
            return User.objects.filter(
                captained_teams__is_active=True
            ).distinct().values_list('email', flat=True)
        
        elif self.recipient_type == 'team_members':
            return User.objects.filter(
                team_memberships__status='accepted',
                team_memberships__team__is_active=True
            ).distinct().values_list('email', flat=True)
        
        elif self.recipient_type == 'individual_users':
            # Users not in any team
            team_users = TeamMembership.objects.filter(
                status='accepted'
            ).values_list('user_id', flat=True)
            return User.objects.filter(
                is_active=True
            ).exclude(id__in=team_users).values_list('email', flat=True)
        
        elif self.recipient_type == 'top_performers':
            return User.objects.filter(
                is_active=True,
                userprofile__total_score__gt=0
            ).order_by('-userprofile__total_score')[:10].values_list('email', flat=True)
        
        elif self.recipient_type == 'custom':
            if self.custom_recipients:
                emails = [email.strip() for email in self.custom_recipients.split(',')]
                return [email for email in emails if email]
            return []
        
        return []


class EmailLog(models.Model):
    """Log individual email sends"""
    broadcast = models.ForeignKey(BroadcastEmail, on_delete=models.CASCADE, related_name='email_logs')
    recipient_email = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.recipient_email} - {self.broadcast.title}"


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
    
    # Preferences
    theme = models.CharField(max_length=10, default='dark', choices=[('dark', 'Dark'), ('light', 'Light'), ('auto', 'Auto')])
    language = models.CharField(max_length=5, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    show_hints = models.BooleanField(default=True)
    show_on_leaderboard = models.BooleanField(default=True)
    
    # Notifications
    email_new_challenges = models.BooleanField(default=True)
    email_rank_changes = models.BooleanField(default=True)
    email_achievements = models.BooleanField(default=False)
    email_weekly_summary = models.BooleanField(default=False)
    
    # Privacy
    profile_public = models.BooleanField(default=True)
    show_solved_challenges = models.BooleanField(default=True)
    show_email_public = models.BooleanField(default=False)
    
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