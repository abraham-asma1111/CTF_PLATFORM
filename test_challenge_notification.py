#!/usr/bin/env python
"""
Test script for challenge notification emails
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from challenges.models import Challenge
from users.models import UserProfile
from django.contrib.auth.models import User

def test_notification():
    print("=" * 60)
    print("TESTING CHALLENGE NOTIFICATION SYSTEM")
    print("=" * 60)
    
    # Check current notification settings
    print("\n1. Checking notification settings...")
    users_with_notifications = UserProfile.objects.filter(email_new_challenges=True)
    print(f"   Users with notifications enabled: {users_with_notifications.count()}")
    
    for profile in users_with_notifications:
        print(f"   - {profile.user.username} ({profile.user.email})")
    
    if users_with_notifications.count() == 0:
        print("\n⚠️  No users have email notifications enabled!")
        print("   Enable it in Settings → Notifications → 'New Challenges'")
        return
    
    # Create a test challenge
    print("\n2. Creating a test challenge...")
    test_challenge = Challenge.objects.create(
        title="Test Notification Challenge",
        description="This is a test challenge to verify email notifications are working correctly.",
        category="misc",
        difficulty="easy",
        points=10,
        flag="CTF{test_notification_123}",
        is_active=True
    )
    print(f"   ✅ Created challenge: {test_challenge.title}")
    
    print("\n3. Email notifications should be sent automatically!")
    print("   Check your email inbox for the notification.")
    
    # Clean up
    print("\n4. Cleaning up test challenge...")
    test_challenge.delete()
    print("   ✅ Test challenge deleted")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print("\nIf you received an email, the notification system is working! 🎉")
    print("If not, check:")
    print("  1. Email settings in .env file")
    print("  2. Gmail app password is correct")
    print("  3. Check spam folder")
    print("  4. Server logs for errors")

if __name__ == "__main__":
    test_notification()
