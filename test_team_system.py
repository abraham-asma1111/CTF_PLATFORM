"""
Test script for team competition system
Run with: python manage.py shell < test_team_system.py
"""

from django.contrib.auth.models import User
from teams.models import Team, TeamMembership, TeamInvitation
from challenges.models import Challenge
from submissions.models import Submission

print("=" * 50)
print("TEAM COMPETITION SYSTEM TEST")
print("=" * 50)

# Create test users
print("\n1. Creating test users...")
user1, _ = User.objects.get_or_create(username='captain1', email='captain1@test.com')
user2, _ = User.objects.get_or_create(username='member1', email='member1@test.com')
user3, _ = User.objects.get_or_create(username='member2', email='member2@test.com')
print(f"✓ Created users: {user1.username}, {user2.username}, {user3.username}")

# Create a team
print("\n2. Creating team...")
team, created = Team.objects.get_or_create(
    name='Test Team Alpha',
    captain=user1,
    defaults={'description': 'Test team for competition'}
)
print(f"✓ Team created: {team.name}")

# Add captain as member
print("\n3. Adding captain as member...")
membership1, _ = TeamMembership.objects.get_or_create(
    team=team,
    user=user1,
    defaults={'status': 'accepted'}
)
print(f"✓ Captain added: {user1.username}")

# Add second member
print("\n4. Adding second member...")
membership2, _ = TeamMembership.objects.get_or_create(
    team=team,
    user=user2,
    defaults={'status': 'accepted'}
)
print(f"✓ Member added: {user2.username}")

# Check team status
print("\n5. Checking team status...")
print(f"   Team members: {team.member_count()}")
print(f"   Can compete: {team.can_compete()}")
print(f"   Is full: {team.is_full()}")

# Create invitation
print("\n6. Creating invitation...")
invitation, _ = TeamInvitation.objects.get_or_create(
    team=team,
    from_user=user1,
    to_user=user3,
    defaults={'message': 'Join our team!', 'status': 'pending'}
)
print(f"✓ Invitation created for: {user3.username}")

# Test scoring (if challenges exist)
print("\n7. Testing team scoring...")
challenges = Challenge.objects.filter(is_active=True)[:1]
if challenges:
    challenge = challenges[0]
    print(f"   Using challenge: {challenge.title}")
    
    # Create team submission
    submission, created = Submission.objects.get_or_create(
        user=user1,
        challenge=challenge,
        team=team,
        defaults={
            'submitted_flag': challenge.flag,
            'is_correct': True
        }
    )
    
    if created:
        # Update team score
        team.total_score += challenge.points
        team.challenges_solved += 1
        team.save()
        print(f"✓ Team scored {challenge.points} points!")
    else:
        print(f"   Submission already exists")
else:
    print("   No challenges available for testing")

# Display final stats
print("\n8. Final Team Stats:")
print(f"   Team: {team.name}")
print(f"   Captain: {team.captain.username}")
print(f"   Members: {team.member_count()}/{team.max_members}")
print(f"   Score: {team.total_score}")
print(f"   Challenges Solved: {team.challenges_solved}")
print(f"   Can Compete: {team.can_compete()}")

print("\n" + "=" * 50)
print("TEST COMPLETED SUCCESSFULLY!")
print("=" * 50)
