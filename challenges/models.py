from django.db import models
from django.contrib.auth.models import User
import hashlib
import os

class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    CATEGORY_CHOICES = [
        ('web', 'Web'),
        ('crypto', 'Cryptography'),
        ('forensics', 'Forensics'),
        ('pwn', 'Binary Exploitation'),
        ('reverse', 'Reverse Engineering'),
        ('misc', 'Miscellaneous'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    flag = models.CharField(max_length=200)  # Store hashed flag
    points = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    # File upload for challenge resources (binaries, archives, etc.)
    challenge_file = models.FileField(
        upload_to='challenges/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Upload challenge file (binary, archive, etc.) for users to download'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Hash the flag before saving
        if self.flag and not self.flag.startswith('sha256:'):
            self.flag = 'sha256:' + hashlib.sha256(self.flag.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def check_flag(self, submitted_flag):
        """Check if submitted flag matches the stored flag"""
        hashed_submitted = 'sha256:' + hashlib.sha256(submitted_flag.encode()).hexdigest()
        return hashed_submitted == self.flag
    
    def get_file_name(self):
        """Get the filename of the uploaded challenge file"""
        if self.challenge_file:
            return os.path.basename(self.challenge_file.name)
        return None
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['difficulty', 'points']


class Hint(models.Model):
    """Hints for challenges that users can unlock"""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='hints')
    content = models.TextField(help_text='The hint text')
    cost = models.IntegerField(default=0, help_text='Points deducted when viewing this hint (0 for free)')
    order = models.IntegerField(default=1, help_text='Display order (1, 2, 3...)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['challenge', 'order']
    
    def __str__(self):
        return f"Hint {self.order} for {self.challenge.title}"


class HintView(models.Model):
    """Track which users have viewed which hints"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    points_deducted = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'hint']
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user.username} viewed hint for {self.hint.challenge.title}"
