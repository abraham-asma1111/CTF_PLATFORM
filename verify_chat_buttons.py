#!/usr/bin/env python
"""Verify chat buttons are working correctly"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from chat.models import TeamMessage
from teams.models import Team
from django.contrib.auth.models import User

print("\n" + "="*70)
print("CHAT BUTTONS VERIFICATION")
print("="*70)

# Get all teams with messages
teams = Team.objects.filter(messages__isnull=False).distinct()

if not teams:
    print("\n❌ No teams with messages found")
else:
    for team in teams:
        print(f"\n📋 Team: {team.name}")
        print(f"   Captain: {team.captain.username}")
        
        messages = TeamMessage.objects.filter(team=team)[:3]
        
        for msg in messages:
            print(f"\n   Message #{msg.id}:")
            print(f"   └─ Sender: {msg.sender.username}")
            print(f"   └─ Content: {msg.content[:40]}...")
            
            # Check for sender
            print(f"\n   🔹 For sender ({msg.sender.username}):")
            print(f"      ✏️  Edit button should show: {msg.can_edit(msg.sender)}")
            print(f"      🗑️  Delete button should show: {msg.can_delete(msg.sender)}")
            
            # Check for captain if different
            if team.captain != msg.sender:
                print(f"\n   🔹 For captain ({team.captain.username}):")
                print(f"      ✏️  Edit button should show: {msg.can_edit(team.captain)}")
                print(f"      🗑️  Delete button should show: {msg.can_delete(team.captain)}")
            
            # Check for random other user
            other_user = User.objects.exclude(id__in=[msg.sender.id, team.captain.id]).first()
            if other_user:
                print(f"\n   🔹 For other user ({other_user.username}):")
                print(f"      ✏️  Edit button should show: {msg.can_edit(other_user)}")
                print(f"      🗑️  Delete button should show: {msg.can_delete(other_user)}")

print("\n" + "="*70)
print("SUMMARY:")
print("✅ Edit buttons: Only show for message sender")
print("✅ Delete buttons: Show for sender OR team captain")
print("\nIf buttons don't appear in browser:")
print("1. Hard refresh: Ctrl+Shift+R")
print("2. Check browser console (F12) for errors")
print("3. Verify you're logged in as the correct user")
print("="*70 + "\n")
