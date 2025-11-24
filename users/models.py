from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    
    def __str__(self):
        return f"{self.user.username} - {self.total_score} points"
    
    class Meta:
        ordering = ['-total_score', 'last_submission']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
