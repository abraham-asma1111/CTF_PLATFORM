#!/usr/bin/env python
"""
Simple test script to verify CTF platform functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from django.contrib.auth.models import User
from challenges.models import Challenge
from submissions.models import Submission
from users.models import UserProfile

def test_platform():
    print("🧪 Testing CTF Platform...")
    
    # Test 1: Check challenges
    challenges = Challenge.objects.all()
    print(f"✅ Found {challenges.count()} challenges")
    
    # Test 2: Check users
    users = User.objects.all()
    print(f"✅ Found {users.count()} users")
    
    # Test 3: Check submissions
    submissions = Submission.objects.all()
    print(f"✅ Found {submissions.count()} submissions")
    
    # Test 4: Check leaderboard data
    top_users = UserProfile.objects.filter(total_score__gt=0).order_by('-total_score')[:5]
    print(f"✅ Found {top_users.count()} users with scores")
    
    for i, profile in enumerate(top_users, 1):
        print(f"   {i}. {profile.user.username}: {profile.total_score} points")
    
    # Test 5: Test flag checking
    if challenges.exists():
        challenge = challenges.first()
        print(f"✅ Testing flag validation for '{challenge.title}'")
        
        # This should return False (wrong flag)
        result = challenge.check_flag("wrong_flag")
        print(f"   Wrong flag test: {'✅ PASS' if not result else '❌ FAIL'}")
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    test_platform()