#!/usr/bin/env python3
"""
Test the automatic broadcast email system
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from challenges.models import Challenge
from users.models import BroadcastEmail
from django.contrib.auth.models import User

def test_broadcast_system():
    print("🚩 CTF Platform - Broadcast Email System Test")
    print("=" * 60)
    
    # Check current state
    total_users = User.objects.filter(is_active=True).count()
    total_challenges = Challenge.objects.filter(is_active=True).count()
    draft_broadcasts = BroadcastEmail.objects.filter(status='draft').count()
    
    print(f"👥 Total Users: {total_users}")
    print(f"🎯 Active Challenges: {total_challenges}")
    print(f"📧 Draft Broadcasts: {draft_broadcasts}")
    
    # Create a test challenge to trigger broadcast
    print("\n🔧 Creating test challenge...")
    
    test_challenge = Challenge.objects.create(
        title="Broadcast Test Challenge",
        description="This challenge was created to test the automatic broadcast email system!",
        category="misc",
        difficulty="easy",
        flag="flag{broadcast_test}",
        points=100,
        challenge_type="both",
        is_active=True
    )
    
    print(f"✅ Created challenge: {test_challenge.title}")
    
    # Check if broadcast was created
    new_broadcasts = BroadcastEmail.objects.filter(
        title__contains="Broadcast Test Challenge"
    )
    
    if new_broadcasts.exists():
        broadcast = new_broadcasts.first()
        recipients = list(broadcast.get_recipients())
        
        print(f"📧 Broadcast email created!")
        print(f"   Title: {broadcast.title}")
        print(f"   Recipients: {len(recipients)} users")
        print(f"   Type: {broadcast.get_recipient_type_display()}")
        print(f"   Status: {broadcast.status}")
        
        print(f"\n🚀 To send the broadcast:")
        print(f"   python manage.py send_broadcast_email --broadcast-id {broadcast.id}")
        print(f"   python manage.py auto_send_challenge_emails")
        
        print(f"\n📋 Admin panel:")
        print(f"   http://127.0.0.1:8000/admin/users/broadcastemail/")
        
    else:
        print("❌ No broadcast email was created. Check the signal.")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")

if __name__ == '__main__':
    test_broadcast_system()