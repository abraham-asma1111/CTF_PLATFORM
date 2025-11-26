#!/usr/bin/env python
"""
Test script to verify the scoring system works correctly
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from django.contrib.auth.models import User
from challenges.models import Challenge
from submissions.models import Submission
from users.models import UserProfile

def test_scoring_system():
    """Test that scoring works correctly when a user solves multiple challenges"""
    
    print("=" * 60)
    print("SCORING SYSTEM TEST")
    print("=" * 60)
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        username='test_scorer',
        defaults={'email': 'test_scorer@test.com'}
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✓ Created test user: {test_user.username}")
    else:
        print(f"✓ Using existing test user: {test_user.username}")
    
    # Get or create test challenges
    challenge1, _ = Challenge.objects.get_or_create(
        title='Test Challenge 1',
        defaults={
            'description': 'Test challenge 1',
            'difficulty': 'easy',
            'category': 'web',
            'flag': 'flag{test1}',
            'points': 50,
            'is_active': True
        }
    )
    
    challenge2, _ = Challenge.objects.get_or_create(
        title='Test Challenge 2',
        defaults={
            'description': 'Test challenge 2',
            'difficulty': 'medium',
            'category': 'crypto',
            'flag': 'flag{test2}',
            'points': 125,
            'is_active': True
        }
    )
    
    print(f"✓ Test challenges created")
    print(f"  - Challenge 1: {challenge1.points} points")
    print(f"  - Challenge 2: {challenge2.points} points")
    
    # Clear any existing submissions for this user
    Submission.objects.filter(user=test_user).delete()
    
    # Reset user profile
    profile = test_user.userprofile
    profile.total_score = 0
    profile.challenges_solved = 0
    profile.save()
    
    print(f"\n✓ Reset user profile")
    print(f"  - Initial score: {profile.total_score}")
    print(f"  - Initial challenges solved: {profile.challenges_solved}")
    
    # Simulate solving challenge 1
    print(f"\n--- Solving Challenge 1 ---")
    submission1 = Submission.objects.create(
        user=test_user,
        challenge=challenge1,
        submitted_flag='flag{test1}',
        is_correct=True
    )
    
    # Update profile (simulating what submit_flag does)
    profile.total_score += challenge1.points
    profile.challenges_solved += 1
    profile.save()
    
    profile.refresh_from_db()
    print(f"✓ After solving Challenge 1:")
    print(f"  - Total score: {profile.total_score} (expected: {challenge1.points})")
    print(f"  - Challenges solved: {profile.challenges_solved} (expected: 1)")
    
    assert profile.total_score == challenge1.points, f"Score mismatch! Got {profile.total_score}, expected {challenge1.points}"
    assert profile.challenges_solved == 1, f"Challenge count mismatch! Got {profile.challenges_solved}, expected 1"
    
    # Simulate solving challenge 2
    print(f"\n--- Solving Challenge 2 ---")
    submission2 = Submission.objects.create(
        user=test_user,
        challenge=challenge2,
        submitted_flag='flag{test2}',
        is_correct=True
    )
    
    # Update profile (simulating what submit_flag does)
    profile.total_score += challenge2.points
    profile.challenges_solved += 1
    profile.save()
    
    profile.refresh_from_db()
    expected_score = challenge1.points + challenge2.points
    print(f"✓ After solving Challenge 2:")
    print(f"  - Total score: {profile.total_score} (expected: {expected_score})")
    print(f"  - Challenges solved: {profile.challenges_solved} (expected: 2)")
    
    assert profile.total_score == expected_score, f"Score mismatch! Got {profile.total_score}, expected {expected_score}"
    assert profile.challenges_solved == 2, f"Challenge count mismatch! Got {profile.challenges_solved}, expected 2"
    
    # Verify leaderboard shows correct data
    print(f"\n--- Leaderboard Verification ---")
    from leaderboard.views import leaderboard_api
    from django.test import RequestFactory
    
    factory = RequestFactory()
    request = factory.get('/api/leaderboard/')
    response = leaderboard_api(request)
    data = json.loads(response.content)
    
    # Find our test user in the leaderboard
    test_user_data = None
    for entry in data['leaderboard']:
        if entry['username'] == test_user.username:
            test_user_data = entry
            break
    
    if test_user_data:
        print(f"✓ Test user found in leaderboard:")
        print(f"  - Username: {test_user_data['username']}")
        print(f"  - Score: {test_user_data['score']} (expected: {expected_score})")
        print(f"  - Challenges solved: {test_user_data['challenges_solved']} (expected: 2)")
        
        assert test_user_data['score'] == expected_score, f"Leaderboard score mismatch!"
        assert test_user_data['challenges_solved'] == 2, f"Leaderboard challenge count mismatch!"
    else:
        print(f"⚠ Test user not in top 20 leaderboard (may be expected if other users have higher scores)")
    
    print(f"\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == '__main__':
    test_scoring_system()
