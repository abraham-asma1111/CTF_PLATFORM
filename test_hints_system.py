#!/usr/bin/env python
"""
Test script for the hints system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from challenges.models import Challenge, Hint
from django.contrib.auth.models import User

def test_hints():
    print("=" * 60)
    print("TESTING HINTS SYSTEM")
    print("=" * 60)
    
    # Get a challenge to add hints to
    challenge = Challenge.objects.filter(is_active=True).first()
    
    if not challenge:
        print("❌ No active challenges found. Create a challenge first.")
        return
    
    print(f"\n1. Adding hints to challenge: {challenge.title}")
    
    # Clear existing hints for this challenge
    Hint.objects.filter(challenge=challenge).delete()
    
    # Add 3 hints
    hints_data = [
        {
            'order': 1,
            'content': 'Start by examining the source code carefully. Look for comments or hidden elements.',
            'cost': 0  # Free hint
        },
        {
            'order': 2,
            'content': 'The flag format is CTF{...}. Try using common web exploitation techniques.',
            'cost': 5  # Costs 5 points
        },
        {
            'order': 3,
            'content': f'The answer involves {challenge.category}. Check the challenge file if available.',
            'cost': 10  # Costs 10 points
        }
    ]
    
    for hint_data in hints_data:
        hint = Hint.objects.create(
            challenge=challenge,
            **hint_data
        )
        cost_str = f"{hint.cost} pts" if hint.cost > 0 else "Free"
        print(f"   ✅ Created Hint {hint.order} (Cost: {cost_str})")
    
    print(f"\n2. Challenge now has {challenge.hints.count()} hints")
    
    print("\n3. Hint details:")
    for hint in challenge.hints.all():
        print(f"   💡 Hint {hint.order}:")
        print(f"      Content: {hint.content[:50]}...")
        print(f"      Cost: {hint.cost} points")
    
    print("\n" + "=" * 60)
    print("HINTS SYSTEM TEST COMPLETE!")
    print("=" * 60)
    print(f"\nGo to: http://127.0.0.1:8000/challenges/{challenge.id}/")
    print("You should now see the hints section on the challenge page!")
    print("\nTo add more hints:")
    print("1. Go to Django Admin → Challenges → Select a challenge")
    print("2. Scroll down to the 'Hints' section")
    print("3. Add hints with order, content, and cost")

if __name__ == "__main__":
    test_hints()
