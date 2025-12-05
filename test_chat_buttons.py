#!/usr/bin/env python
"""Test script to verify chat button permissions"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from chat.models import TeamMessage
from django.contrib.auth.models import User

print("=" * 60)
print("CHAT BUTTON PERMISSIONS TEST")
print("=" * 60)

# Get all messages
messages = TeamMessage.objects.all()[:5]

if not messages:
    print("\n❌ No messages found in database")
    print("   Create some messages first to test permissions")
else:
    print(f"\n✅ Found {TeamMessage.objects.count()} total messages")
    print(f"   Testing first 5 messages:\n")
    
    for msg in messages:
        print(f"Message #{msg.id}")
        print(f"  Team: {msg.team.name}")
        print(f"  Sender: {msg.sender.username}")
        print(f"  Content: {msg.content[:40]}...")
        
        # Test for sender
        print(f"  Sender permissions:")
        print(f"    ✏️  can_edit: {msg.can_edit(msg.sender)}")
        print(f"    🗑️  can_delete: {msg.can_delete(msg.sender)}")
        
        # Test for team captain
        captain = msg.team.captain
        if captain != msg.sender:
            print(f"  Captain ({captain.username}) permissions:")
            print(f"    ✏️  can_edit: {msg.can_edit(captain)}")
            print(f"    🗑️  can_delete: {msg.can_delete(captain)}")
        
        print()

print("=" * 60)
print("If buttons don't appear in browser:")
print("1. Press Ctrl+Shift+R to hard refresh")
print("2. Clear browser cache")
print("3. Try incognito mode")
print("=" * 60)
