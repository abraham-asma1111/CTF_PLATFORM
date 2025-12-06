from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    
    CHALLENGE_TYPE_CHOICES = [
        ('individual', 'Individual Challenge'),
        ('team', 'Team Challenge'),
        ('both', 'Both Individual & Team'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    flag = models.CharField(max_length=200)  # Store hashed flag
    points = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    # Team challenge settings
    challenge_type = models.CharField(
        max_length=20, 
        choices=CHALLENGE_TYPE_CHOICES, 
        default='both',
        help_text='Who can access this challenge'
    )
    min_team_size = models.IntegerField(
        default=1,
        help_text='Minimum team size required (for team challenges)'
    )
    max_team_size = models.IntegerField(
        default=5,
        help_text='Maximum team size allowed (for team challenges)'
    )
    team_points_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiply points for team challenges (e.g., 1.5 for 50% bonus)'
    )
    
    # Team challenge settings
    challenge_type = models.CharField(
        max_length=20, 
        choices=[
            ('individual', 'Individual Challenge'),
            ('team', 'Team Challenge'),
            ('both', 'Both Individual & Team'),
        ], 
        default='both',
        help_text='Who can access this challenge'
    )
    min_team_size = models.IntegerField(
        default=1,
        help_text='Minimum team size required (for team challenges)'
    )
    max_team_size = models.IntegerField(
        default=5,
        help_text='Maximum team size allowed (for team challenges)'
    )
    team_points_multiplier = models.FloatField(
        default=1.0,
        help_text='Multiply points for team challenges (e.g., 1.5 for 50% bonus)'
    )
    
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


# Signal to automatically create broadcast email when new challenge is created
@receiver(post_save, sender=Challenge)
def create_challenge_broadcast(sender, instance, created, **kwargs):
    """Automatically create broadcast email when new challenge is published"""
    if created and instance.is_active:
        from users.models import BroadcastEmail
        from django.contrib.auth.models import User
        
        # Get the admin user who created the challenge (or first superuser)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            return
        
        # Create broadcast email content
        challenge_type_text = ""
        if instance.challenge_type == 'team':
            challenge_type_text = f"🏆 **Team Challenge** (Requires {instance.min_team_size}-{instance.max_team_size} members)"
        elif instance.challenge_type == 'individual':
            challenge_type_text = "👤 **Individual Challenge**"
        else:
            challenge_type_text = "🎯 **Challenge** (Individual or Team)"
        
        points_text = f"{instance.points} points"
        if instance.team_points_multiplier != 1.0:
            team_points = int(instance.points * instance.team_points_multiplier)
            points_text += f" (Teams: {team_points} points)"
        
        email_content = f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #2c3e50; color: #fff; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #34495e; border-radius: 10px; padding: 30px;">
        <h1 style="color: #00ff88; text-align: center; margin-bottom: 30px;">
            🚩 New Challenge Available!
        </h1>
        
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #FFD700; margin-top: 0;">{instance.title}</h2>
            <p style="color: #00ff88; font-weight: bold;">{challenge_type_text}</p>
            <p style="margin: 15px 0;"><strong>Category:</strong> {instance.get_category_display()}</p>
            <p style="margin: 15px 0;"><strong>Difficulty:</strong> {instance.get_difficulty_display()}</p>
            <p style="margin: 15px 0;"><strong>Points:</strong> {points_text}</p>
        </div>
        
        <div style="background-color: #2c3e50; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
            <h3 style="color: #00ff88; margin-top: 0;">Challenge Description:</h3>
            <p style="line-height: 1.6;">{instance.description[:200]}{'...' if len(instance.description) > 200 else ''}</p>
        </div>
        
        <div style="text-align: center;">
            <a href="http://127.0.0.1:8000/challenges/{instance.id}/" 
               style="background: linear-gradient(135deg, #00ff88, #00dd77); 
                      color: #000; 
                      padding: 15px 30px; 
                      text-decoration: none; 
                      border-radius: 25px; 
                      font-weight: bold; 
                      display: inline-block;">
                🎯 Solve Challenge Now
            </a>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #00ff88; text-align: center; color: #999;">
            <p>Good luck and happy hacking!</p>
            <p><strong>CTF Platform Team</strong></p>
        </div>
    </div>
</body>
</html>
        """
        
        # Determine recipient type based on challenge type
        if instance.challenge_type == 'team':
            recipient_type = 'team_members'
        elif instance.challenge_type == 'individual':
            recipient_type = 'individual_users'
        else:
            recipient_type = 'all_users'
        
        # Create broadcast email
        broadcast = BroadcastEmail.objects.create(
            title=f"🚩 New Challenge: {instance.title}",
            content=email_content,
            recipient_type=recipient_type,
            created_by=admin_user,
            status='draft'  # Created as draft, admin can send manually
        )
        
        print(f"✅ Broadcast email created for challenge: {instance.title}")
        print(f"📧 Recipients: {broadcast.get_recipient_type_display()}")
        print(f"🔗 Admin can send via: python manage.py send_broadcast_email --broadcast-id {broadcast.id}")


# Signal to create broadcast when challenge is activated
@receiver(post_save, sender=Challenge)
def challenge_activated_broadcast(sender, instance, **kwargs):
    """Create broadcast when existing challenge is activated"""
    if not kwargs.get('created', False):  # Not a new challenge
        # Check if challenge was just activated
        if instance.is_active:
            try:
                # Get previous state from database
                old_instance = Challenge.objects.get(pk=instance.pk)
                if hasattr(old_instance, '_state') and not old_instance.is_active:
                    # Challenge was just activated
                    create_challenge_broadcast(sender, instance, created=True, **kwargs)
            except Challenge.DoesNotExist:
                pass


# Group Event Models for separate challenge system
class GroupEvent(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Event-specific settings
    point_multiplier = models.FloatField(default=1.0)
    max_teams = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'group_events'
    
    def __str__(self):
        return self.name


class GroupChallenge(models.Model):
    event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    points = models.IntegerField()
    flag = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)
    
    # Group-specific fields
    requires_collaboration = models.BooleanField(default=True)
    max_attempts_per_team = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'group_challenges'
    
    def __str__(self):
        return f"{self.title} (Group Event: {self.event.name})"


class GroupSubmission(models.Model):
    challenge = models.ForeignKey(GroupChallenge, on_delete=models.CASCADE)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    flag_submitted = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'group_submissions'
    
    def __str__(self):
        return f"{self.team.name} - {self.challenge.title} - {'✓' if self.is_correct else '✗'}"


class PlatformMode(models.Model):
    mode = models.CharField(max_length=20, choices=[
        ('individual', 'Individual Mode'),
        ('group', 'Group Mode')
    ], default='individual')
    active_event = models.ForeignKey(GroupEvent, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'platform_mode'
    
    def __str__(self):
        return f"{self.mode} mode"