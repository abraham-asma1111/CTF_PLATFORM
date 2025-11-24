from django.db import models
from django.contrib.auth.models import User
from challenges.models import Challenge

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    submitted_flag = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'challenge']  # One correct submission per user per challenge
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} - {'✓' if self.is_correct else '✗'}"
