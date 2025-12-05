from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captained_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    total_score = models.IntegerField(default=0)
    challenges_solved = models.IntegerField(default=0)
    last_submission = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Team settings
    max_members = models.IntegerField(default=5)
    is_open = models.BooleanField(default=True)  # Open for join requests
    description = models.TextField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-total_score', 'last_submission']
    
    def __str__(self):
        return f"{self.name} ({self.member_count()}/{self.max_members})"
    
    def member_count(self):
        return self.members.filter(status='accepted').count()
    
    def can_compete(self):
        """Team needs at least 2 members to compete"""
        return self.member_count() >= 2
    
    def is_full(self):
        return self.member_count() >= self.max_members
    
    def can_add_member(self):
        return not self.is_full()
    
    def ensure_captain_membership(self):
        """Ensure the captain has an accepted membership"""
        membership, created = TeamMembership.objects.get_or_create(
            team=self,
            user=self.captain,
            defaults={'status': 'accepted'}
        )
        if not created and membership.status != 'accepted':
            membership.status = 'accepted'
            membership.save()
        return membership


class TeamMembership(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['team', 'user']  # One request per team per user
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.status})"
    
    @classmethod
    def cancel_other_pending_requests(cls, user, accepted_team):
        """Cancel all other pending requests when user joins a team"""
        cls.objects.filter(
            user=user,
            status='pending'
        ).exclude(team=accepted_team).update(status='rejected')


class TeamInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['team', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.team.name} -> {self.to_user.username} ({self.status})"
