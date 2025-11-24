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
