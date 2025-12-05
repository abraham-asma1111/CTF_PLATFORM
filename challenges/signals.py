from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Challenge
from users.models import UserProfile


@receiver(post_save, sender=Challenge)
def notify_new_challenge(sender, instance, created, **kwargs):
    """Send email notifications when a new challenge is created"""
    if created and instance.is_active:
        # Get all users who want to be notified about new challenges
        profiles = UserProfile.objects.filter(email_new_challenges=True)
        
        for profile in profiles:
            user = profile.user
            
            # Prepare email content
            subject = f'🎯 New Challenge Available: {instance.title}'
            
            message = f"""
Hello {user.username},

A new challenge has been added to the CTF platform!

Challenge: {instance.title}
Category: {instance.category}
Difficulty: {instance.difficulty}
Points: {instance.points}

{instance.description[:200]}{'...' if len(instance.description) > 200 else ''}

Login to the platform to start solving it!

Good luck!

---
CTF Platform
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                print(f"✅ Sent notification to {user.email}")
            except Exception as e:
                print(f"❌ Failed to send email to {user.email}: {e}")
