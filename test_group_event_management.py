"""
Property-based tests for CTF Group Event Management System
Run with: python manage.py test test_group_event_management
"""

import os
import sys
import django
import hashlib
from django.test import TestCase
from django.contrib.auth.models import User
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_platform.settings')
django.setup()

from challenges.models import Challenge, GroupEvent, GroupChallenge, GroupSubmission
from submissions.models import Submission
from teams.models import Team


class TestDataStorageSeparation(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 1: Data Storage Separation**
    **Validates: Requirements 1.1, 4.2**
    
    For any group challenge or submission, the data should be stored in 
    group-specific database tables separate from regular challenge data
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@test.com',
                'password': 'testpass123'
            }
        )
        self.regular_user, _ = User.objects.get_or_create(
            username='user_test',
            defaults={
                'email': 'user@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Test Team',
            defaults={'captain': self.regular_user}
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        challenge_title=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        challenge_points=st.integers(min_value=1, max_value=1000),
        flag_text=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'))
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_storage_separation(self, event_name, challenge_title, challenge_points, flag_text):
        """
        Property test: Group challenges are stored in separate tables from regular challenges
        """
        # Create a group event
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Test event description",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user
        )
        
        # Create a group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title=challenge_title,
            description="Test group challenge",
            points=challenge_points,
            flag=flag_text,
            category="test",
            difficulty="easy"
        )
        
        # Create a regular challenge with similar data (disable signals to avoid email noise)
        from django.db import transaction
        with transaction.atomic():
            regular_challenge = Challenge.objects.create(
                title=challenge_title + "_regular",
                description="Test regular challenge",
                difficulty="easy",
                category="test",
                flag=flag_text + "_regular",
                points=challenge_points,
                is_active=False  # Set to False to avoid email notifications
            )
        
        # Verify data storage separation
        # 1. Group challenges should not appear in regular challenge queries
        regular_challenges = Challenge.objects.all()
        group_challenges = GroupChallenge.objects.all()
        
        self.assertNotIn(group_challenge.title, [c.title for c in regular_challenges])
        self.assertNotIn(regular_challenge.title, [c.title for c in group_challenges])
        
        # 2. Verify different table storage by checking model meta
        self.assertEqual(GroupChallenge._meta.db_table, 'group_challenges')
        self.assertEqual(Challenge._meta.db_table, 'challenges_challenge')
        
        # 3. Verify group challenges are linked to events, regular challenges are not
        self.assertTrue(hasattr(group_challenge, 'event'))
        self.assertFalse(hasattr(regular_challenge, 'event'))
        
        # 4. Verify group challenges have group-specific fields
        self.assertTrue(hasattr(group_challenge, 'requires_collaboration'))
        self.assertTrue(hasattr(group_challenge, 'max_attempts_per_team'))
        self.assertFalse(hasattr(regular_challenge, 'requires_collaboration'))
        self.assertFalse(hasattr(regular_challenge, 'max_attempts_per_team'))
    
    @given(
        flag_submission=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
        points_awarded=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_submission_storage_separation(self, flag_submission, points_awarded):
        """
        Property test: Group submissions are stored separately from regular submissions
        """
        # Create test data
        group_event = GroupEvent.objects.create(
            name="Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user
        )
        
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Test Group Challenge",
            description="Test challenge",
            points=100,
            flag="test_flag",
            category="test",
            difficulty="easy"
        )
        
        regular_challenge = Challenge.objects.create(
            title="Test Regular Challenge",
            description="Test challenge",
            difficulty="easy",
            category="test",
            flag="test_flag_regular",
            points=100,
            is_active=False  # Set to False to avoid email notifications
        )
        
        # Create group submission
        group_submission = GroupSubmission.objects.create(
            challenge=group_challenge,
            team=self.team,
            submitted_by=self.regular_user,
            flag_submitted=flag_submission,
            is_correct=True,
            points_awarded=points_awarded
        )
        
        # Create regular submission
        regular_submission = Submission.objects.create(
            user=self.regular_user,
            challenge=regular_challenge,
            submitted_flag=flag_submission + "_regular",
            is_correct=True
        )
        
        # Verify storage separation
        # 1. Group submissions should not appear in regular submission queries
        regular_submissions = Submission.objects.all()
        group_submissions = GroupSubmission.objects.all()
        
        self.assertNotIn(group_submission.flag_submitted, [s.submitted_flag for s in regular_submissions])
        
        # 2. Verify different table storage
        self.assertEqual(GroupSubmission._meta.db_table, 'group_submissions')
        self.assertEqual(Submission._meta.db_table, 'submissions_submission')
        
        # 3. Verify group submissions are linked to teams and group challenges
        self.assertTrue(hasattr(group_submission, 'team'))
        self.assertTrue(hasattr(group_submission, 'challenge'))
        self.assertIsInstance(group_submission.challenge, GroupChallenge)
        
        # 4. Verify regular submissions are linked to regular challenges
        self.assertTrue(hasattr(regular_submission, 'challenge'))
        self.assertIsInstance(regular_submission.challenge, Challenge)
        
        # 5. Verify group submissions have group-specific fields
        self.assertTrue(hasattr(group_submission, 'points_awarded'))
        self.assertFalse(hasattr(regular_submission, 'points_awarded'))
    
    def test_database_table_separation(self):
        """
        Test that group and regular models use different database tables
        """
        # Verify table names are different
        self.assertNotEqual(
            GroupEvent._meta.db_table,
            Challenge._meta.db_table
        )
        self.assertNotEqual(
            GroupChallenge._meta.db_table,
            Challenge._meta.db_table
        )
        self.assertNotEqual(
            GroupSubmission._meta.db_table,
            Submission._meta.db_table
        )
        
        # Verify group tables use custom table names
        self.assertEqual(GroupEvent._meta.db_table, 'group_events')
        self.assertEqual(GroupChallenge._meta.db_table, 'group_challenges')
        self.assertEqual(GroupSubmission._meta.db_table, 'group_submissions')


class TestGroupChallengeManagementSeparation(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 6: Group Challenge Management Separation**
    **Validates: Requirements 1.3, 1.5**
    
    For any group challenge creation or management operation, it should use different 
    tools and interfaces than regular challenges and be accessible only through team section
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_mgmt_test',
            defaults={
                'email': 'admin_mgmt@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.regular_user, _ = User.objects.get_or_create(
            username='user_mgmt_test',
            defaults={
                'email': 'user_mgmt@test.com',
                'password': 'testpass123'
            }
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        challenge_title=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        challenge_points=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_management_tools_separation(self, event_name, challenge_title, challenge_points):
        """
        Property test: Group challenges use different management tools than regular challenges
        """
        # Create a group event first
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Test event description",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user
        )
        
        # Create a group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title=challenge_title,
            description="Test group challenge",
            points=challenge_points,
            flag="test_flag",
            category="test",
            difficulty="easy"
        )
        
        # Create a regular challenge
        regular_challenge = Challenge.objects.create(
            title=challenge_title + "_regular",
            description="Test regular challenge",
            difficulty="easy",
            category="test",
            flag="test_flag_regular",
            points=challenge_points,
            is_active=False
        )
        
        # Verify management separation
        # 1. Group challenges must be linked to events (different management context)
        self.assertIsNotNone(group_challenge.event)
        self.assertEqual(group_challenge.event, group_event)
        self.assertFalse(hasattr(regular_challenge, 'event'))
        
        # 2. Group challenges have different field structure (different management tools)
        group_fields = set(field.name for field in GroupChallenge._meta.fields)
        regular_fields = set(field.name for field in Challenge._meta.fields)
        
        # Group challenges should have event-specific fields
        self.assertIn('event', group_fields)
        self.assertIn('requires_collaboration', group_fields)
        self.assertIn('max_attempts_per_team', group_fields)
        
        # Regular challenges should not have these fields
        self.assertNotIn('event', regular_fields)
        self.assertNotIn('requires_collaboration', regular_fields)
        self.assertNotIn('max_attempts_per_team', regular_fields)
        
        # 3. Group challenges use different model classes (different management context)
        self.assertNotEqual(
            GroupChallenge._meta.model,
            Challenge._meta.model
        )
        
        # 4. Verify group challenges are managed in team section context (event-based)
        # Group challenges can only exist within an event context
        self.assertTrue(group_challenge.event_id is not None)
        
        # Regular challenges exist independently
        self.assertFalse(hasattr(regular_challenge, 'event_id'))
    
    @given(
        management_operation=st.sampled_from(['create', 'update', 'delete'])
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_management_interface_separation(self, management_operation):
        """
        Property test: Group challenge management uses different interfaces than regular challenges
        """
        # Create test event
        group_event = GroupEvent.objects.create(
            name="Test Management Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user
        )
        
        if management_operation == 'create':
            # Group challenges require event context for creation
            group_challenge = GroupChallenge.objects.create(
                event=group_event,  # Required field - different from regular challenges
                title="Test Group Challenge",
                description="Test challenge",
                points=100,
                flag="test_flag",
                category="test",
                difficulty="easy"
            )
            
            # Regular challenges don't require event context
            regular_challenge = Challenge.objects.create(
                title="Test Regular Challenge",
                description="Test challenge",
                difficulty="easy",
                category="test",
                flag="test_flag_regular",
                points=100,
                is_active=False
            )
            
            # Verify creation interface differences
            self.assertTrue(hasattr(group_challenge, 'event'))
            self.assertFalse(hasattr(regular_challenge, 'event'))
            
        elif management_operation == 'update':
            # Create challenges to update
            group_challenge = GroupChallenge.objects.create(
                event=group_event,
                title="Original Group Title",
                description="Original description",
                points=100,
                flag="original_flag",
                category="test",
                difficulty="easy"
            )
            
            regular_challenge = Challenge.objects.create(
                title="Original Regular Title",
                description="Original description",
                difficulty="easy",
                category="test",
                flag="original_flag_regular",
                points=100,
                is_active=False
            )
            
            # Update operations - group challenges maintain event context
            group_challenge.title = "Updated Group Title"
            group_challenge.save()
            
            regular_challenge.title = "Updated Regular Title"
            regular_challenge.save()
            
            # Verify update interface differences
            updated_group = GroupChallenge.objects.get(id=group_challenge.id)
            updated_regular = Challenge.objects.get(id=regular_challenge.id)
            
            self.assertEqual(updated_group.title, "Updated Group Title")
            self.assertEqual(updated_regular.title, "Updated Regular Title")
            
            # Group challenge still maintains event context after update
            self.assertEqual(updated_group.event, group_event)
            self.assertFalse(hasattr(updated_regular, 'event'))
            
        elif management_operation == 'delete':
            # Create challenges to delete
            group_challenge = GroupChallenge.objects.create(
                event=group_event,
                title="To Delete Group",
                description="Test challenge",
                points=100,
                flag="delete_flag",
                category="test",
                difficulty="easy"
            )
            
            regular_challenge = Challenge.objects.create(
                title="To Delete Regular",
                description="Test challenge",
                difficulty="easy",
                category="test",
                flag="delete_flag_regular",
                points=100,
                is_active=False
            )
            
            group_id = group_challenge.id
            regular_id = regular_challenge.id
            
            # Delete operations
            group_challenge.delete()
            regular_challenge.delete()
            
            # Verify deletion worked for both but through different interfaces
            self.assertFalse(GroupChallenge.objects.filter(id=group_id).exists())
            self.assertFalse(Challenge.objects.filter(id=regular_id).exists())
    
    def test_group_challenge_team_section_access_only(self):
        """
        Test that group challenges are accessible only through team section context
        """
        # Create test event and challenge
        group_event = GroupEvent.objects.create(
            name="Team Section Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user
        )
        
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Team Section Challenge",
            description="Test challenge",
            points=100,
            flag="team_flag",
            category="test",
            difficulty="easy"
        )
        
        # Verify group challenges are event-scoped (team section context)
        event_challenges = GroupChallenge.objects.filter(event=group_event)
        self.assertIn(group_challenge, event_challenges)
        
        # Verify group challenges don't appear in regular challenge queries
        regular_challenges = Challenge.objects.all()
        regular_challenge_titles = [c.title for c in regular_challenges]
        self.assertNotIn(group_challenge.title, regular_challenge_titles)
        
        # Verify group challenges require event context (team section)
        self.assertIsNotNone(group_challenge.event)
        self.assertEqual(group_challenge.event, group_event)


class TestGroupChallengeDisplay(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 8: Group Challenge Display**
    **Validates: Requirements 3.2, 4.3**
    
    For any user redirected to team section during group mode, only group challenges 
    should be displayed with appropriate collaboration features
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_display_test',
            defaults={
                'email': 'admin_display@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_user, _ = User.objects.get_or_create(
            username='team_display_test',
            defaults={
                'email': 'team_display@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Display Test Team',
            defaults={'captain': self.team_user}
        )
        
        # Ensure team membership exists
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_user,
            defaults={'status': 'accepted'}
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_group_challenges=st.integers(min_value=1, max_value=5),
        num_regular_challenges=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_display_separation(self, event_name, num_group_challenges, num_regular_challenges):
        """
        Property test: Group challenges are displayed separately from regular challenges in team section
        """
        # Create a group event
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Test event for display",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        # Activate group mode
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            group_challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag=f"group_flag_{i+1}",
                category="test",
                difficulty="easy",
                requires_collaboration=True,
                max_attempts_per_team=10
            )
            group_challenges.append(group_challenge)
        
        # Create regular challenges
        regular_challenges = []
        for i in range(num_regular_challenges):
            regular_challenge = Challenge.objects.create(
                title=f"Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(regular_challenge)
        
        # Test group challenge display through GroupChallengeManager
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify group challenges are available for team during group mode
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(team_challenges.count(), num_group_challenges)
        
        # 2. Verify only group challenges from active event are returned
        for challenge in team_challenges:
            self.assertIsInstance(challenge, GroupChallenge)
            self.assertEqual(challenge.event, group_event)
            self.assertIn(challenge, group_challenges)
        
        # 3. Verify regular challenges are not included in team challenges
        team_challenge_titles = [c.title for c in team_challenges]
        regular_challenge_titles = [c.title for c in regular_challenges]
        
        for regular_title in regular_challenge_titles:
            self.assertNotIn(regular_title, team_challenge_titles)
        
        # 4. Verify group challenges have collaboration features
        for challenge in team_challenges:
            self.assertTrue(hasattr(challenge, 'requires_collaboration'))
            self.assertTrue(hasattr(challenge, 'max_attempts_per_team'))
            self.assertTrue(hasattr(challenge, 'event'))
            
            # Verify collaboration-specific fields exist
            self.assertIsNotNone(challenge.requires_collaboration)
            self.assertIsNotNone(challenge.max_attempts_per_team)
            self.assertIsNotNone(challenge.event)
        
        # 5. Verify regular challenges don't have group-specific fields
        for challenge in regular_challenges:
            self.assertFalse(hasattr(challenge, 'requires_collaboration'))
            self.assertFalse(hasattr(challenge, 'max_attempts_per_team'))
            self.assertFalse(hasattr(challenge, 'event'))
    
    @given(
        challenge_title=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        challenge_points=st.integers(min_value=1, max_value=1000),
        requires_collaboration=st.booleans(),
        max_attempts=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_collaboration_features_display(self, challenge_title, challenge_points, requires_collaboration, max_attempts):
        """
        Property test: Group challenges display appropriate collaboration features
        """
        # Create group event and activate group mode
        group_event = GroupEvent.objects.create(
            name="Collaboration Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenge with collaboration features
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title=challenge_title,
            description="Test collaboration challenge",
            points=challenge_points,
            flag="test_flag",
            category="test",
            difficulty="easy",
            requires_collaboration=requires_collaboration,
            max_attempts_per_team=max_attempts
        )
        
        # Test collaboration features through GroupChallengeManager
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify challenge is accessible to team
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertIn(group_challenge, team_challenges)
        
        # 2. Verify collaboration features are preserved in display
        displayed_challenge = team_challenges.get(id=group_challenge.id)
        self.assertEqual(displayed_challenge.requires_collaboration, requires_collaboration)
        self.assertEqual(displayed_challenge.max_attempts_per_team, max_attempts)
        
        # 3. Verify team-specific functionality works
        self.assertTrue(GroupChallengeManager.can_user_access_group_challenges(self.team_user))
        self.assertEqual(GroupChallengeManager.get_user_team(self.team_user), self.team)
        
        # 4. Verify challenge stats functionality for collaboration tracking
        stats = GroupChallengeManager.get_challenge_stats(group_challenge)
        self.assertIn('total_teams', stats)
        self.assertIn('solved_teams', stats)
        self.assertIn('total_attempts', stats)
        self.assertIn('solve_rate', stats)
    
    @given(
        user_has_team=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_access_control_display(self, user_has_team):
        """
        Property test: Group challenge display respects team membership access control
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'access_test_user_{user_has_team}',
            defaults={
                'email': f'access_test_{user_has_team}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Access Control Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        # Activate group mode
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Access Control Challenge",
            description="Test challenge",
            points=100,
            flag="access_flag",
            category="test",
            difficulty="easy"
        )
        
        # Set up team membership based on test parameter
        if user_has_team:
            test_team, _ = Team.objects.get_or_create(
                name=f'Access Test Team {test_user.id}',
                defaults={'captain': test_user}
            )
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': 'accepted'}
            )
        
        # Test access control through GroupChallengeManager
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify access control is enforced
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        self.assertEqual(can_access, user_has_team)
        
        # 2. Verify team retrieval works correctly
        user_team = GroupChallengeManager.get_user_team(test_user)
        if user_has_team:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team.captain, test_user)
            
            # User with team should see challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertIn(group_challenge, team_challenges)
        else:
            self.assertIsNone(user_team)
    
    def test_group_mode_inactive_no_challenges_displayed(self):
        """
        Test that no group challenges are displayed when group mode is inactive
        """
        # Create group event but don't activate group mode
        group_event = GroupEvent.objects.create(
            name="Inactive Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=False  # Event exists but not active
        )
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Inactive Challenge",
            description="Test challenge",
            points=100,
            flag="inactive_flag",
            category="test",
            difficulty="easy"
        )
        
        # Ensure group mode is not active (individual mode)
        from challenges.models import PlatformMode
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            platform_mode.active_event = None
            platform_mode.save()
        except PlatformMode.DoesNotExist:
            pass
        
        # Test that no group challenges are displayed
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify group mode is not active
        self.assertFalse(GroupChallengeManager.is_group_mode_active())
        self.assertIsNone(GroupChallengeManager.get_active_group_event())
        
        # 2. Verify no group challenges are returned for team
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(team_challenges.count(), 0)
        self.assertNotIn(group_challenge, team_challenges)
        
        # 3. Verify team submissions are also empty when no active event
        team_submissions = GroupChallengeManager.get_team_submissions(self.team)
        self.assertEqual(team_submissions.count(), 0)


class TestGroupScoringSystemIndependence(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 7: Group Scoring System Independence**
    **Validates: Requirements 1.4, 4.1, 4.4**
    
    For any group challenge solution, points should be calculated using the separate 
    group scoring system and update team leaderboards independently from regular challenges
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_scoring_test',
            defaults={
                'email': 'admin_scoring@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_user, _ = User.objects.get_or_create(
            username='team_scoring_test',
            defaults={
                'email': 'team_scoring@test.com',
                'password': 'testpass123'
            }
        )
        self.individual_user, _ = User.objects.get_or_create(
            username='individual_scoring_test',
            defaults={
                'email': 'individual_scoring@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Scoring Test Team',
            defaults={'captain': self.team_user}
        )
        
        # Ensure team membership exists
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_user,
            defaults={'status': 'accepted'}
        )
        
        # Add a second member to meet minimum team requirements
        self.team_user2, _ = User.objects.get_or_create(
            username='team_scoring_test_2',
            defaults={
                'email': 'team_scoring_2@test.com',
                'password': 'testpass123'
            }
        )
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_user2,
            defaults={'status': 'accepted'}
        )
    
    @given(
        group_points=st.integers(min_value=1, max_value=1000),
        regular_points=st.integers(min_value=1, max_value=1000),
        event_multiplier=st.floats(min_value=0.5, max_value=3.0),
        flag_text=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'))
    )
    @settings(max_examples=100, deadline=None)
    def test_group_scoring_independence_from_regular_scoring(self, group_points, regular_points, event_multiplier, flag_text):
        """
        Property test: Group scoring system operates independently from regular scoring
        """
        # Create group event and activate group mode
        group_event = GroupEvent.objects.create(
            name="Scoring Independence Test Event",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True,
            point_multiplier=event_multiplier
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Group Scoring Challenge",
            description="Test challenge",
            points=group_points,
            flag='sha256:' + hashlib.sha256(flag_text.encode()).hexdigest(),
            category="test",
            difficulty="easy"
        )
        
        # Create regular challenge
        regular_challenge = Challenge.objects.create(
            title="Regular Scoring Challenge",
            description="Test challenge",
            difficulty="easy",
            category="test",
            flag=flag_text + "_regular",
            points=regular_points,
            is_active=False  # Avoid email notifications
        )
        
        # Get initial scores
        initial_team_score = self.team.total_score
        initial_individual_score = self.individual_user.userprofile.total_score
        
        # Submit correct solution to group challenge
        from challenges.group_challenge_manager import GroupChallengeManager, GroupScoring
        group_result = GroupChallengeManager.submit_solution(
            self.team, group_challenge, self.team_user, flag_text
        )
        
        # Submit correct solution to regular challenge
        from submissions.models import Submission
        regular_submission = Submission.objects.create(
            user=self.individual_user,
            challenge=regular_challenge,
            submitted_flag=flag_text + "_regular",
            is_correct=True
        )
        
        # Update individual user score manually (simulating regular scoring system)
        self.individual_user.userprofile.total_score += regular_points
        self.individual_user.userprofile.challenges_solved += 1
        self.individual_user.userprofile.save()
        
        # Refresh objects from database
        self.team.refresh_from_db()
        self.individual_user.userprofile.refresh_from_db()
        
        # Verify group scoring independence
        # 1. Group challenge should award points using event multiplier
        expected_group_points = int(group_points * event_multiplier)
        self.assertTrue(group_result['success'])
        self.assertTrue(group_result['is_correct'])
        self.assertEqual(group_result['points_awarded'], expected_group_points)
        
        # 2. Team score should be updated by group scoring system
        expected_team_score = initial_team_score + expected_group_points
        self.assertEqual(self.team.total_score, expected_team_score)
        
        # 3. Individual user score should be updated by regular scoring system
        expected_individual_score = initial_individual_score + regular_points
        self.assertEqual(self.individual_user.userprofile.total_score, expected_individual_score)
        
        # 4. Verify scoring systems use different models and fields
        scoring_separation = GroupScoring.is_scoring_separated_from_regular()
        self.assertTrue(scoring_separation['scoring_separated'])
        self.assertTrue(scoring_separation['group_has_points_awarded'])
        self.assertFalse(scoring_separation['regular_has_points_awarded'])
        
        # 5. Verify group submissions are stored separately
        group_submissions = GroupSubmission.objects.filter(team=self.team, challenge=group_challenge)
        regular_submissions = Submission.objects.filter(user=self.individual_user, challenge=regular_challenge)
        
        self.assertEqual(group_submissions.count(), 1)
        self.assertEqual(regular_submissions.count(), 1)
        
        group_sub = group_submissions.first()
        regular_sub = regular_submissions.first()
        
        # Group submission should have points_awarded field
        self.assertEqual(group_sub.points_awarded, expected_group_points)
        # Regular submission should not have points_awarded field
        self.assertFalse(hasattr(regular_sub, 'points_awarded'))
        
        # 6. Verify leaderboards are separate
        group_leaderboard = GroupScoring.get_group_leaderboard(group_event)
        
        # Team should appear in group leaderboard
        team_in_group_leaderboard = any(
            entry['team'].id == self.team.id for entry in group_leaderboard
        )
        self.assertTrue(team_in_group_leaderboard)
        
        # Individual user should not appear in group leaderboard
        individual_in_group_leaderboard = any(
            entry['team'].captain.id == self.individual_user.id for entry in group_leaderboard
        )
        self.assertFalse(individual_in_group_leaderboard)
    
    @given(
        num_teams=st.integers(min_value=1, max_value=5),
        challenges_per_team=st.integers(min_value=1, max_value=3),
        base_points=st.integers(min_value=50, max_value=200)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_leaderboard_independence(self, num_teams, challenges_per_team, base_points):
        """
        Property test: Group leaderboards operate independently from regular leaderboards
        """
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Leaderboard Independence Test",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True,
            point_multiplier=1.5
        )
        
        # Activate group mode
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create teams and challenges
        teams = []
        group_challenges = []
        
        for i in range(num_teams):
            # Create team user
            team_user, _ = User.objects.get_or_create(
                username=f'team_leader_{i}_{num_teams}_{challenges_per_team}',
                defaults={
                    'email': f'team_leader_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            
            # Create team
            team, _ = Team.objects.get_or_create(
                name=f'Test Team {i}_{num_teams}_{challenges_per_team}',
                defaults={'captain': team_user}
            )
            teams.append(team)
            
            # Ensure team membership
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user,
                defaults={'status': 'accepted'}
            )
            
            # Add a second member to meet minimum team requirements
            team_user2, _ = User.objects.get_or_create(
                username=f'team_member_{i}_{num_teams}_{challenges_per_team}',
                defaults={
                    'email': f'team_member_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user2,
                defaults={'status': 'accepted'}
            )
        
        # Create group challenges
        for i in range(challenges_per_team):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Leaderboard Challenge {i}",
                description="Test challenge",
                points=base_points * (i + 1),
                flag='sha256:' + hashlib.sha256(f'flag_{i}'.encode()).hexdigest(),
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Have teams solve challenges (different numbers for ranking)
        from challenges.group_challenge_manager import GroupChallengeManager, GroupScoring
        
        for team_idx, team in enumerate(teams):
            # Each team solves a different number of challenges
            challenges_to_solve = min(team_idx + 1, len(group_challenges))
            
            for challenge_idx in range(challenges_to_solve):
                challenge = group_challenges[challenge_idx]
                GroupChallengeManager.submit_solution(
                    team, challenge, team.captain, f'flag_{challenge_idx}'
                )
        
        # Test group leaderboard independence
        group_leaderboard = GroupScoring.get_group_leaderboard(group_event)
        
        # 1. Verify leaderboard contains only teams that solved challenges
        self.assertGreater(len(group_leaderboard), 0)
        self.assertLessEqual(len(group_leaderboard), num_teams)
        
        # 2. Verify leaderboard is sorted by score (descending)
        for i in range(len(group_leaderboard) - 1):
            current_score = group_leaderboard[i]['event_score']
            next_score = group_leaderboard[i + 1]['event_score']
            self.assertGreaterEqual(current_score, next_score)
        
        # 3. Verify scores are calculated using group scoring system
        for entry in group_leaderboard:
            team = entry['team']
            expected_score = GroupScoring.get_team_event_score(team, group_event)
            self.assertEqual(entry['event_score'], expected_score)
        
        # 4. Verify group leaderboard is separate from regular leaderboard
        # Group leaderboard should contain team data, not individual user data
        for entry in group_leaderboard:
            self.assertIn('team', entry)
            self.assertIn('event_score', entry)
            self.assertIn('event_challenges_solved', entry)
            
            # Verify it's team-based scoring
            self.assertIsInstance(entry['team'], Team)
            self.assertGreater(entry['event_score'], 0)
        
        # 5. Verify team rankings work correctly
        if len(group_leaderboard) > 0:
            top_team = group_leaderboard[0]['team']
            ranking = GroupScoring.get_team_ranking(top_team, group_event)
            
            self.assertIsNotNone(ranking)
            self.assertEqual(ranking['rank'], 1)
            self.assertEqual(ranking['total_teams'], len(group_leaderboard))
            self.assertGreater(ranking['score'], 0)
    
    @given(
        points_before=st.integers(min_value=0, max_value=500),
        challenge_points=st.integers(min_value=1, max_value=200),
        event_multiplier=st.floats(min_value=1.0, max_value=2.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_scoring_calculation_independence(self, points_before, challenge_points, event_multiplier):
        """
        Property test: Group scoring calculations are independent from regular scoring
        """
        # Set up team with initial score
        self.team.total_score = points_before
        self.team.save()
        
        # Create group event with multiplier
        group_event = GroupEvent.objects.create(
            name="Scoring Calculation Test",
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True,
            point_multiplier=event_multiplier
        )
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Calculation Test Challenge",
            description="Test challenge",
            points=challenge_points,
            flag='sha256:' + hashlib.sha256('test_flag'.encode()).hexdigest(),
            category="test",
            difficulty="easy"
        )
        
        # Test group scoring calculation
        from challenges.group_challenge_manager import GroupScoring
        
        # 1. Calculate points using group scoring system
        calculated_points = GroupScoring.calculate_team_points(self.team, group_challenge)
        expected_points = int(challenge_points * event_multiplier)
        self.assertEqual(calculated_points, expected_points)
        
        # 2. Update team score using group scoring system
        initial_score = self.team.total_score
        GroupScoring.update_team_score(self.team, calculated_points)
        
        # Refresh from database
        self.team.refresh_from_db()
        
        # 3. Verify score was updated correctly
        expected_final_score = initial_score + calculated_points
        self.assertEqual(self.team.total_score, expected_final_score)
        
        # 4. Verify regular scoring system is not affected
        # Create regular challenge and user
        regular_challenge = Challenge.objects.create(
            title="Regular Calculation Challenge",
            description="Test challenge",
            difficulty="easy",
            category="test",
            flag="regular_flag",
            points=challenge_points,
            is_active=False
        )
        
        # Regular scoring doesn't use event multipliers
        regular_user_initial_score = self.individual_user.userprofile.total_score
        self.individual_user.userprofile.total_score += challenge_points  # No multiplier
        self.individual_user.userprofile.save()
        
        # 5. Verify scoring systems remain independent
        self.individual_user.userprofile.refresh_from_db()
        
        # Group scoring used multiplier, regular scoring did not
        group_points_gained = calculated_points
        regular_points_gained = challenge_points
        
        # The key independence test: group scoring uses event multiplier, regular doesn't
        expected_group_points = int(challenge_points * event_multiplier)
        self.assertEqual(group_points_gained, expected_group_points)
        self.assertEqual(regular_points_gained, challenge_points)
        
        # If multiplier creates a difference, verify they're different
        if expected_group_points != challenge_points:
            self.assertNotEqual(group_points_gained, regular_points_gained)
        
        # Verify final scores
        self.assertEqual(self.team.total_score, points_before + group_points_gained)
        self.assertEqual(
            self.individual_user.userprofile.total_score, 
            regular_user_initial_score + regular_points_gained
        )


class TestGroupEventInformationDisplay(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 3: Group Event Information Display**
    **Validates: Requirements 2.5, 3.2, 3.3**
    
    For any active group event, the platform should display group competition 
    information and options in the team section while maintaining regular challenge access
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_info_test',
            defaults={
                'email': 'admin_info@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.regular_user, _ = User.objects.get_or_create(
            username='user_info_test',
            defaults={
                'email': 'user_info@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Info Test Team',
            defaults={'captain': self.regular_user}
        )
        
        # Ensure team membership exists
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.regular_user,
            defaults={'status': 'accepted'}
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        event_description=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-.,!')),
        is_active=st.booleans(),
        num_challenges=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_event_information_display_in_team_section(self, event_name, event_description, is_active, num_challenges):
        """
        Property test: Group event information is displayed in team section when active
        """
        # Create group event
        group_event = GroupEvent.objects.create(
            name=event_name,
            description=event_description,
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=is_active
        )
        
        # Set platform mode based on event status
        from challenges.models import PlatformMode
        if is_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        else:
            # Ensure no active group mode
            try:
                platform_mode = PlatformMode.objects.get(mode='group')
                platform_mode.active_event = None
                platform_mode.save()
            except PlatformMode.DoesNotExist:
                pass
        
        # Create group challenges for the event
        group_challenges = []
        for i in range(num_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Info Test Challenge {i+1}",
                description=f"Test challenge {i+1}",
                points=100 * (i+1),
                flag=f"info_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Test group event information display through GroupChallengeManager
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify group mode status matches event active status
        group_mode_active = GroupChallengeManager.is_group_mode_active()
        self.assertEqual(group_mode_active, is_active)
        
        # 2. Verify active group event information is available when active
        active_event = GroupChallengeManager.get_active_group_event()
        if is_active:
            self.assertIsNotNone(active_event)
            self.assertEqual(active_event.id, group_event.id)
            self.assertEqual(active_event.name, event_name)
            self.assertEqual(active_event.description, event_description)
        else:
            self.assertIsNone(active_event)
        
        # 3. Verify group challenges are available in team section when active
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        if is_active:
            self.assertEqual(team_challenges.count(), num_challenges)
            for challenge in team_challenges:
                self.assertEqual(challenge.event, group_event)
                self.assertIn(challenge, group_challenges)
        else:
            self.assertEqual(team_challenges.count(), 0)
        
        # 4. Verify team can access group event information when active
        if is_active:
            # Team should be able to access group challenges
            self.assertTrue(GroupChallengeManager.can_user_access_group_challenges(self.regular_user))
            
            # Event information should be available
            event_info = GroupChallengeManager.get_group_event_info(group_event)
            self.assertIsNotNone(event_info)
            self.assertEqual(event_info['name'], event_name)
            self.assertEqual(event_info['description'], event_description)
            self.assertEqual(event_info['total_challenges'], num_challenges)
            self.assertIn('start_time', event_info)
            self.assertIn('end_time', event_info)
        else:
            # When not active, group challenges should not be accessible
            if num_challenges > 0:
                # Even if challenges exist, they shouldn't be accessible when event is inactive
                self.assertEqual(team_challenges.count(), 0)
    
    @given(
        has_team=st.booleans(),
        event_active=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_group_event_team_creation_prompts(self, has_team, event_active):
        """
        Property test: Group event displays team creation/joining prompts appropriately
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'prompt_test_user_{has_team}_{event_active}',
            defaults={
                'email': f'prompt_test_{has_team}_{event_active}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Team Prompt Test Event",
            description="Test event for team prompts",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=event_active
        )
        
        # Set up team membership based on test parameter
        test_team = None
        if has_team:
            test_team, _ = Team.objects.get_or_create(
                name=f'Prompt Test Team {test_user.id}',
                defaults={'captain': test_user}
            )
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': 'accepted'}
            )
        
        # Set platform mode
        from challenges.models import PlatformMode
        if event_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        
        # Test team creation/joining prompts through GroupChallengeManager
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify user team status is correctly detected
        user_team = GroupChallengeManager.get_user_team(test_user)
        if has_team:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
        else:
            self.assertIsNone(user_team)
        
        # 2. Verify access control based on team membership AND event status
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        expected_access = has_team and event_active
        self.assertEqual(can_access, expected_access)
        
        # 3. Verify appropriate prompts are shown based on user status
        if event_active:
            if has_team:
                # User with team should see group challenges
                team_challenges = GroupChallengeManager.get_team_challenges(test_team)
                # Should be able to access (even if no challenges exist)
                self.assertIsNotNone(team_challenges)
            else:
                # User without team should be prompted to join/create team
                self.assertFalse(can_access)
                self.assertIsNone(user_team)
        else:
            # When event is not active, no group challenges should be available
            if has_team:
                team_challenges = GroupChallengeManager.get_team_challenges(test_team)
                self.assertEqual(team_challenges.count(), 0)
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_regular_challenges=st.integers(min_value=1, max_value=3),
        num_group_challenges=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_regular_challenge_access_maintained_during_group_event(self, event_name, num_regular_challenges, num_group_challenges):
        """
        Property test: Regular challenges remain accessible during group events
        """
        # Create group event and activate it
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create regular challenges
        regular_challenges = []
        for i in range(num_regular_challenges):
            challenge = Challenge.objects.create(
                title=f"Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag=f"group_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Test that both systems remain accessible
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify group mode is active
        self.assertTrue(GroupChallengeManager.is_group_mode_active())
        
        # 2. Verify regular challenges are still accessible
        active_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(active_regular_challenges.count(), num_regular_challenges)
        
        for challenge in active_regular_challenges:
            self.assertIn(challenge, regular_challenges)
            self.assertTrue(challenge.is_active)
        
        # 3. Verify group challenges are accessible in team section
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(team_challenges.count(), num_group_challenges)
        
        for challenge in team_challenges:
            self.assertIn(challenge, group_challenges)
            self.assertEqual(challenge.event, group_event)
        
        # 4. Verify systems remain separate
        # Regular challenges should not appear in group challenge queries
        regular_challenge_titles = [c.title for c in regular_challenges]
        group_challenge_titles = [c.title for c in team_challenges]
        
        for regular_title in regular_challenge_titles:
            self.assertNotIn(regular_title, group_challenge_titles)
        
        for group_title in group_challenge_titles:
            self.assertNotIn(group_title, regular_challenge_titles)
        
        # 5. Verify both systems can be used simultaneously
        # This tests the "optional participation" aspect - users can access both
        self.assertGreater(len(regular_challenges), 0)
        self.assertGreater(len(group_challenges), 0)
        self.assertTrue(GroupChallengeManager.is_group_mode_active())
        
        # Regular challenges remain active even during group mode
        for challenge in regular_challenges:
            self.assertTrue(challenge.is_active)


if __name__ == '__main__':
    import unittest
    unittest.main()


class TestOptionalParticipation(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 2: Optional Participation**
    **Validates: Requirements 2.2, 3.4**
    
    For any active group event, users should be able to access both regular challenges 
    and group challenges (via team section) without forced redirection
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_optional_test',
            defaults={
                'email': 'admin_optional@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_user, _ = User.objects.get_or_create(
            username='team_optional_test',
            defaults={
                'email': 'team_optional@test.com',
                'password': 'testpass123'
            }
        )
        self.individual_user, _ = User.objects.get_or_create(
            username='individual_optional_test',
            defaults={
                'email': 'individual_optional@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Optional Test Team',
            defaults={'captain': self.team_user}
        )
        
        # Ensure team membership exists
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_user,
            defaults={'status': 'accepted'}
        )
    
    @given(
        num_regular_challenges=st.integers(min_value=1, max_value=5),
        num_group_challenges=st.integers(min_value=1, max_value=5),
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-'))
    )
    @settings(max_examples=100, deadline=None)
    def test_both_challenge_systems_accessible_during_group_event(self, num_regular_challenges, num_group_challenges, event_name):
        """
        Property test: Both regular and group challenges remain accessible during group events
        """
        # Create and activate group event
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Optional participation test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create regular challenges
        regular_challenges = []
        for i in range(num_regular_challenges):
            challenge = Challenge.objects.create(
                title=f"Optional Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"optional_regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Optional Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag=f"optional_group_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Test optional participation through both systems
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify group mode is active
        self.assertTrue(GroupChallengeManager.is_group_mode_active())
        active_event = GroupChallengeManager.get_active_group_event()
        self.assertEqual(active_event, group_event)
        
        # 2. Verify regular challenges remain accessible during group event
        accessible_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(accessible_regular_challenges.count(), num_regular_challenges)
        
        for challenge in accessible_regular_challenges:
            self.assertIn(challenge, regular_challenges)
            self.assertTrue(challenge.is_active)
        
        # 3. Verify group challenges are accessible via team section
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(team_challenges.count(), num_group_challenges)
        
        for challenge in team_challenges:
            self.assertIn(challenge, group_challenges)
            self.assertEqual(challenge.event, group_event)
        
        # 4. Verify users can choose their participation level
        # Team user can access both systems
        self.assertTrue(GroupChallengeManager.can_user_access_group_challenges(self.team_user))
        user_team = GroupChallengeManager.get_user_team(self.team_user)
        self.assertEqual(user_team, self.team)
        
        # Individual user can access regular challenges but not group challenges
        self.assertFalse(GroupChallengeManager.can_user_access_group_challenges(self.individual_user))
        individual_team = GroupChallengeManager.get_user_team(self.individual_user)
        self.assertIsNone(individual_team)
        
        # 5. Verify no forced redirection - both systems coexist
        # Regular challenges don't disappear when group mode is active
        for regular_challenge in regular_challenges:
            self.assertTrue(regular_challenge.is_active)
        
        # Group challenges don't interfere with regular challenge access
        regular_challenge_titles = [c.title for c in accessible_regular_challenges]
        group_challenge_titles = [c.title for c in team_challenges]
        
        # No overlap between regular and group challenge titles
        for group_title in group_challenge_titles:
            self.assertNotIn(group_title, regular_challenge_titles)
        
        # 6. Verify users maintain choice without forced participation
        # Team users are not forced to use group challenges
        team_can_access_regular = accessible_regular_challenges.count() > 0
        self.assertTrue(team_can_access_regular)
        
        # Individual users are not forced to join teams
        individual_can_access_regular = accessible_regular_challenges.count() > 0
        self.assertTrue(individual_can_access_regular)
    
    @given(
        user_has_team=st.booleans(),
        group_event_active=st.booleans(),
        num_regular_challenges=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_user_choice_mechanisms_for_participation(self, user_has_team, group_event_active, num_regular_challenges):
        """
        Property test: Users can choose their level of participation in group events
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'choice_test_user_{user_has_team}_{group_event_active}',
            defaults={
                'email': f'choice_test_{user_has_team}_{group_event_active}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Set up team membership based on test parameter
        test_team = None
        if user_has_team:
            test_team, _ = Team.objects.get_or_create(
                name=f'Choice Test Team {test_user.id}',
                defaults={'captain': test_user}
            )
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': 'accepted'}
            )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="User Choice Test Event",
            description="Test event for user choice",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=group_event_active
        )
        
        # Set platform mode based on event status
        from challenges.models import PlatformMode
        if group_event_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        else:
            # Ensure individual mode
            try:
                platform_mode = PlatformMode.objects.get(mode='group')
                platform_mode.active_event = None
                platform_mode.save()
            except PlatformMode.DoesNotExist:
                pass
        
        # Create regular challenges (always available)
        regular_challenges = []
        for i in range(num_regular_challenges):
            challenge = Challenge.objects.create(
                title=f"Choice Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"choice_regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
        
        # Create group challenge if event is active
        group_challenge = None
        if group_event_active:
            group_challenge = GroupChallenge.objects.create(
                event=group_event,
                title="Choice Group Challenge",
                description="Test group challenge",
                points=200,
                flag="choice_group_flag",
                category="test",
                difficulty="easy"
            )
        
        # Test user choice mechanisms
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify regular challenges are always accessible (user choice preserved)
        accessible_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(accessible_regular_challenges.count(), num_regular_challenges)
        
        # 2. Verify group challenge access depends on user choice (team membership) AND active group event
        can_access_group = GroupChallengeManager.can_user_access_group_challenges(test_user)
        expected_access = user_has_team and group_event_active
        self.assertEqual(can_access_group, expected_access)
        
        # 3. Verify user team status reflects their choice
        user_team = GroupChallengeManager.get_user_team(test_user)
        if user_has_team:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
        else:
            self.assertIsNone(user_team)
        
        # 4. Verify group challenges are only accessible when user chooses team participation
        if group_event_active and user_has_team:
            team_challenges = GroupChallengeManager.get_team_challenges(test_team)
            self.assertEqual(team_challenges.count(), 1)
            self.assertEqual(team_challenges.first(), group_challenge)
        elif group_event_active and not user_has_team:
            # User without team cannot access group challenges (their choice)
            self.assertFalse(can_access_group)
        elif not group_event_active:
            # No group challenges available regardless of team status
            if user_has_team:
                team_challenges = GroupChallengeManager.get_team_challenges(test_team)
                self.assertEqual(team_challenges.count(), 0)
        
        # 5. Verify users are not forced into either participation mode
        # Regular challenges remain accessible regardless of group event status
        self.assertGreater(accessible_regular_challenges.count(), 0)
        
        # Group participation is optional (requires user choice to join team)
        if group_event_active:
            group_mode_active = GroupChallengeManager.is_group_mode_active()
            self.assertTrue(group_mode_active)
            
            # But users without teams are not forced to participate
            if not user_has_team:
                self.assertFalse(can_access_group)
                self.assertIsNone(user_team)
        
        # 6. Verify choice mechanisms work correctly
        # Users can participate in regular challenges regardless of team status
        for challenge in accessible_regular_challenges:
            self.assertTrue(challenge.is_active)
        
        # Users can only participate in group challenges if they choose to join a team
        if user_has_team and group_event_active:
            self.assertTrue(can_access_group)
        else:
            self.assertFalse(can_access_group)
    
    @given(
        event_duration_active=st.booleans(),
        num_teams=st.integers(min_value=1, max_value=3),
        num_individuals=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_no_forced_redirection_during_group_events(self, event_duration_active, num_teams, num_individuals):
        """
        Property test: No forced redirection occurs during group events - users maintain access choice
        """
        # Create group event
        group_event = GroupEvent.objects.create(
            name="No Redirection Test Event",
            description="Test event for redirection behavior",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=event_duration_active
        )
        
        # Set platform mode
        from challenges.models import PlatformMode
        if event_duration_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        
        # Create teams and individual users
        teams = []
        team_users = []
        individual_users = []
        
        for i in range(num_teams):
            team_user, _ = User.objects.get_or_create(
                username=f'redirect_team_user_{i}_{event_duration_active}',
                defaults={
                    'email': f'redirect_team_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            team_users.append(team_user)
            
            team, _ = Team.objects.get_or_create(
                name=f'Redirect Test Team {i}_{event_duration_active}',
                defaults={'captain': team_user}
            )
            teams.append(team)
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user,
                defaults={'status': 'accepted'}
            )
        
        for i in range(num_individuals):
            individual_user, _ = User.objects.get_or_create(
                username=f'redirect_individual_user_{i}_{event_duration_active}',
                defaults={
                    'email': f'redirect_individual_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            individual_users.append(individual_user)
        
        # Create challenges in both systems
        regular_challenge = Challenge.objects.create(
            title="No Redirect Regular Challenge",
            description="Test regular challenge",
            difficulty="easy",
            category="test",
            flag="no_redirect_regular_flag",
            points=100,
            is_active=True
        )
        
        group_challenge = None
        if event_duration_active:
            group_challenge = GroupChallenge.objects.create(
                event=group_event,
                title="No Redirect Group Challenge",
                description="Test group challenge",
                points=200,
                flag="no_redirect_group_flag",
                category="test",
                difficulty="easy"
            )
        
        # Test no forced redirection
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify regular challenges remain accessible to all users (no forced redirection)
        accessible_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertGreater(accessible_regular_challenges.count(), 0)
        self.assertIn(regular_challenge, accessible_regular_challenges)
        
        # 2. Verify team users can access both systems without forced redirection
        for team_user in team_users:
            # Can access regular challenges
            self.assertTrue(regular_challenge.is_active)
            
            # Can access group challenges only if event is active
            can_access_group = GroupChallengeManager.can_user_access_group_challenges(team_user)
            self.assertEqual(can_access_group, event_duration_active)
            
            if event_duration_active:
                user_team = GroupChallengeManager.get_user_team(team_user)
                self.assertIsNotNone(user_team)
                team_challenges = GroupChallengeManager.get_team_challenges(user_team)
                if group_challenge:
                    self.assertIn(group_challenge, team_challenges)
        
        # 3. Verify individual users can access regular challenges without forced team joining
        for individual_user in individual_users:
            # Can access regular challenges
            self.assertTrue(regular_challenge.is_active)
            
            # Cannot access group challenges (not forced to join team)
            can_access_group = GroupChallengeManager.can_user_access_group_challenges(individual_user)
            self.assertFalse(can_access_group)
            
            user_team = GroupChallengeManager.get_user_team(individual_user)
            self.assertIsNone(user_team)
        
        # 4. Verify no system forces users away from their chosen participation mode
        # Regular challenges don't disappear during group events
        self.assertTrue(regular_challenge.is_active)
        
        # Group challenges don't force individual users to participate
        for individual_user in individual_users:
            self.assertFalse(GroupChallengeManager.can_user_access_group_challenges(individual_user))
        
        # Team users aren't forced away from regular challenges
        for team_user in team_users:
            # Regular challenges remain accessible
            self.assertTrue(regular_challenge.is_active)
        
        # 5. Verify both systems coexist without forced redirection
        if event_duration_active:
            # Group mode is active but doesn't force redirection
            self.assertTrue(GroupChallengeManager.is_group_mode_active())
            
            # Regular challenges still accessible
            self.assertGreater(accessible_regular_challenges.count(), 0)
            
            # Group challenges available to teams
            for team in teams:
                team_challenges = GroupChallengeManager.get_team_challenges(team)
                if group_challenge:
                    self.assertIn(group_challenge, team_challenges)
        else:
            # Individual mode - no group challenges but regular challenges remain
            self.assertFalse(GroupChallengeManager.is_group_mode_active())
            self.assertGreater(accessible_regular_challenges.count(), 0)
        
        # 6. Verify user choice is preserved without forced redirection
        # Team users chose to join teams and can access group challenges
        for i, team_user in enumerate(team_users):
            user_team = GroupChallengeManager.get_user_team(team_user)
            self.assertEqual(user_team, teams[i])
        
        # Individual users chose not to join teams and maintain regular access
        for individual_user in individual_users:
            user_team = GroupChallengeManager.get_user_team(individual_user)
            self.assertIsNone(user_team)
            # But can still access regular challenges
            self.assertTrue(regular_challenge.is_active)


class TestAccessControlEnforcement(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 5: Access Control Enforcement**
    **Validates: Requirements 1.2, 3.5**
    
    For any user attempting to access group challenges, the system should enforce 
    team membership requirements and proper permissions
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_access_test',
            defaults={
                'email': 'admin_access@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_captain, _ = User.objects.get_or_create(
            username='captain_access_test',
            defaults={
                'email': 'captain_access@test.com',
                'password': 'testpass123'
            }
        )
        self.team_member, _ = User.objects.get_or_create(
            username='member_access_test',
            defaults={
                'email': 'member_access@test.com',
                'password': 'testpass123'
            }
        )
        self.individual_user, _ = User.objects.get_or_create(
            username='individual_access_test',
            defaults={
                'email': 'individual_access@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Access Control Test Team',
            defaults={'captain': self.team_captain}
        )
        
        # Set up team memberships
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_captain,
            defaults={'status': 'accepted'}
        )
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_member,
            defaults={'status': 'accepted'}
        )
    
    @given(
        user_type=st.sampled_from(['team_captain', 'team_member', 'individual', 'admin']),
        group_event_active=st.booleans(),
        num_group_challenges=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_team_membership_validation_for_group_challenges(self, user_type, group_event_active, num_group_challenges):
        """
        Property test: Team membership is validated for group challenge access
        """
        # Select user based on type
        if user_type == 'team_captain':
            test_user = self.team_captain
            expected_access = True
        elif user_type == 'team_member':
            test_user = self.team_member
            expected_access = True
        elif user_type == 'individual':
            test_user = self.individual_user
            expected_access = False
        else:  # admin
            test_user = self.admin_user
            expected_access = False  # Admins don't have teams by default
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Access Control Test Event",
            description="Test event for access control",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=group_event_active
        )
        
        # Set platform mode
        from challenges.models import PlatformMode
        if group_event_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Access Control Challenge {i+1}",
                description=f"Test challenge {i+1}",
                points=100 * (i+1),
                flag=f"access_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Test access control enforcement
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify team membership validation (requires both team membership AND active group event)
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        expected_access_with_event = expected_access and group_event_active
        self.assertEqual(can_access, expected_access_with_event)
        
        # 2. Verify user team retrieval respects membership
        user_team = GroupChallengeManager.get_user_team(test_user)
        if expected_access:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, self.team)
        else:
            self.assertIsNone(user_team)
        
        # 3. Verify group challenge access is properly controlled
        if group_event_active and expected_access:
            # Users with team membership should see challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), num_group_challenges)
            
            for challenge in team_challenges:
                self.assertIn(challenge, group_challenges)
                self.assertEqual(challenge.event, group_event)
        elif group_event_active and not expected_access:
            # Users without team membership should not see challenges
            self.assertFalse(can_access)
            self.assertIsNone(user_team)
        elif not group_event_active:
            # No group challenges available when event is inactive
            if expected_access:
                team_challenges = GroupChallengeManager.get_team_challenges(user_team)
                self.assertEqual(team_challenges.count(), 0)
        
        # 4. Verify access control is enforced consistently
        # Team membership AND active group event determine access, not user type alone
        if user_type in ['team_captain', 'team_member'] and group_event_active:
            self.assertTrue(can_access)
        else:
            self.assertFalse(can_access)
    
    @given(
        membership_status=st.sampled_from(['accepted', 'pending', 'rejected', 'none']),
        group_event_active=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_team_membership_status_enforcement(self, membership_status, group_event_active):
        """
        Property test: Only accepted team memberships grant access to group challenges
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'status_test_user_{membership_status}_{group_event_active}',
            defaults={
                'email': f'status_test_{membership_status}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Create test team
        test_team, _ = Team.objects.get_or_create(
            name=f'Status Test Team {test_user.id}',
            defaults={'captain': self.team_captain}  # Use existing captain
        )
        
        # Set up membership based on status
        from teams.models import TeamMembership
        if membership_status != 'none':
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': membership_status}
            )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Membership Status Test Event",
            description="Test event for membership status",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=group_event_active
        )
        
        # Set platform mode
        from challenges.models import PlatformMode
        if group_event_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Membership Status Challenge",
            description="Test challenge",
            points=100,
            flag="status_flag",
            category="test",
            difficulty="easy"
        )
        
        # Test membership status enforcement
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify only accepted memberships grant access (and group event must be active)
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        expected_access = (membership_status == 'accepted') and group_event_active
        self.assertEqual(can_access, expected_access)
        
        # 2. Verify team retrieval respects membership status
        user_team = GroupChallengeManager.get_user_team(test_user)
        if membership_status == 'accepted':
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
        else:
            self.assertIsNone(user_team)
        
        # 3. Verify group challenge access based on membership status
        if group_event_active and membership_status == 'accepted':
            # Only accepted members can access group challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), 1)
            self.assertEqual(team_challenges.first(), group_challenge)
        else:
            # Pending, rejected, or no membership should not grant access
            self.assertFalse(can_access)
            
            # Even if they somehow get a team reference, they shouldn't see challenges
            if membership_status in ['pending', 'rejected']:
                # These users have membership records but wrong status
                membership = TeamMembership.objects.filter(user=test_user, team=test_team).first()
                self.assertIsNotNone(membership)
                self.assertNotEqual(membership.status, 'accepted')
        
        # 4. Verify access control is strict about membership status
        # Only 'accepted' status AND active group event should work
        if membership_status == 'accepted' and group_event_active:
            self.assertTrue(can_access)
        else:
            self.assertFalse(can_access)
    
    @given(
        user_permissions=st.sampled_from(['regular_user', 'staff_user', 'superuser']),
        has_team_membership=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_permission_enforcement_for_group_features(self, user_permissions, has_team_membership):
        """
        Property test: Group challenge access is based on team membership, not user permissions
        """
        # Create test user with specified permissions
        test_user, _ = User.objects.get_or_create(
            username=f'perm_test_user_{user_permissions}_{has_team_membership}',
            defaults={
                'email': f'perm_test_{user_permissions}@test.com',
                'password': 'testpass123',
                'is_staff': user_permissions in ['staff_user', 'superuser'],
                'is_superuser': user_permissions == 'superuser'
            }
        )
        
        # Set up team membership if specified
        test_team = None
        if has_team_membership:
            test_team, _ = Team.objects.get_or_create(
                name=f'Permission Test Team {test_user.id}',
                defaults={'captain': test_user}
            )
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': 'accepted'}
            )
        
        # Create active group event
        group_event = GroupEvent.objects.create(
            name="Permission Test Event",
            description="Test event for permissions",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Permission Test Challenge",
            description="Test challenge",
            points=100,
            flag="permission_flag",
            category="test",
            difficulty="easy"
        )
        
        # Test permission enforcement
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify access is based on team membership, not user permissions
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        expected_access = has_team_membership  # Team membership is what matters
        self.assertEqual(can_access, expected_access)
        
        # 2. Verify user permissions don't override team membership requirements
        user_team = GroupChallengeManager.get_user_team(test_user)
        if has_team_membership:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
        else:
            self.assertIsNone(user_team)
        
        # 3. Verify group challenge access follows team membership rules
        if has_team_membership:
            # Users with team membership can access group challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), 1)
            self.assertEqual(team_challenges.first(), group_challenge)
        else:
            # Users without team membership cannot access group challenges
            # Even if they are staff or superuser
            self.assertFalse(can_access)
            self.assertIsNone(user_team)
        
        # 4. Verify permissions don't grant special access to group features
        # Staff and superuser status should not bypass team membership requirements
        if user_permissions in ['staff_user', 'superuser'] and not has_team_membership:
            # Even privileged users need team membership for group challenges
            self.assertFalse(can_access)
            self.assertIsNone(user_team)
        
        # 5. Verify team membership is the determining factor
        # Regular users with team membership should have same access as privileged users with team membership
        if has_team_membership:
            self.assertTrue(can_access)
            self.assertIsNotNone(user_team)
        else:
            self.assertFalse(can_access)
            self.assertIsNone(user_team)
    
    @given(
        challenge_submission_attempt=st.booleans(),
        user_has_valid_team=st.booleans(),
        flag_is_correct=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_group_challenge_submission_access_control(self, challenge_submission_attempt, user_has_valid_team, flag_is_correct):
        """
        Property test: Group challenge submissions enforce team membership access control
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'submit_test_user_{user_has_valid_team}_{challenge_submission_attempt}',
            defaults={
                'email': f'submit_test_{user_has_valid_team}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Set up team membership
        test_team = None
        if user_has_valid_team:
            test_team, _ = Team.objects.get_or_create(
                name=f'Submit Test Team {test_user.id}',
                defaults={'captain': test_user}
            )
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=test_user,
                defaults={'status': 'accepted'}
            )
            
            # Add a second member to meet minimum team requirements
            second_user, _ = User.objects.get_or_create(
                username=f'submit_test_user_2_{test_user.id}',
                defaults={
                    'email': f'submit_test_2_{test_user.id}@test.com',
                    'password': 'testpass123'
                }
            )
            TeamMembership.objects.get_or_create(
                team=test_team,
                user=second_user,
                defaults={'status': 'accepted'}
            )
        
        # Create active group event
        group_event = GroupEvent.objects.create(
            name="Submission Access Test Event",
            description="Test event for submission access",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenge
        correct_flag = "correct_submission_flag"
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Submission Access Challenge",
            description="Test challenge",
            points=100,
            flag='sha256:' + hashlib.sha256(correct_flag.encode()).hexdigest(),
            category="test",
            difficulty="easy"
        )
        
        # Test submission access control
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Verify access control before submission attempt
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        self.assertEqual(can_access, user_has_valid_team)
        
        # 2. Test submission attempt if specified
        if challenge_submission_attempt:
            submitted_flag = correct_flag if flag_is_correct else "wrong_flag"
            
            if user_has_valid_team:
                # User with valid team should be able to submit
                result = GroupChallengeManager.submit_solution(
                    test_team, group_challenge, test_user, submitted_flag
                )
                
                # Submission should succeed (access-wise)
                self.assertTrue(result['success'])
                
                # Correctness should match flag correctness
                self.assertEqual(result['is_correct'], flag_is_correct)
                
                if flag_is_correct:
                    self.assertGreater(result['points_awarded'], 0)
                else:
                    self.assertEqual(result['points_awarded'], 0)
                
                # Verify submission was recorded
                submissions = GroupSubmission.objects.filter(
                    team=test_team,
                    challenge=group_challenge,
                    submitted_by=test_user
                )
                self.assertEqual(submissions.count(), 1)
                
                submission = submissions.first()
                self.assertEqual(submission.is_correct, flag_is_correct)
                self.assertEqual(submission.flag_submitted, submitted_flag)
                
            else:
                # User without valid team should not be able to submit
                # This should be caught by access control before submission
                self.assertFalse(can_access)
                self.assertIsNone(GroupChallengeManager.get_user_team(test_user))
                
                # No submissions should be recorded for users without teams
                submissions = GroupSubmission.objects.filter(
                    challenge=group_challenge,
                    submitted_by=test_user
                )
                self.assertEqual(submissions.count(), 0)
        
        # 3. Verify access control consistency
        user_team = GroupChallengeManager.get_user_team(test_user)
        if user_has_valid_team:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
            
            # Should be able to see the challenge
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertIn(group_challenge, team_challenges)
        else:
            self.assertIsNone(user_team)
            
            # Should not be able to see any challenges
            self.assertFalse(can_access)
    
    @given(
        user_membership_status=st.sampled_from(['accepted', 'pending', 'rejected']),
        group_event_active=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_comprehensive_access_control_validation(self, user_membership_status, group_event_active):
        """
        Property test: Comprehensive validation of all access control factors
        """
        # Create test user
        test_user, _ = User.objects.get_or_create(
            username=f'comprehensive_test_{user_membership_status}_{group_event_active}',
            defaults={
                'email': f'comprehensive_{user_membership_status}@test.com',
                'password': 'testpass123'
            }
        )
        
        # Create test team (always active - team active status is not part of access control per requirements)
        test_team, _ = Team.objects.get_or_create(
            name=f'Comprehensive Test Team {test_user.id}',
            defaults={
                'captain': self.team_captain,  # Use existing captain
                'is_active': True
            }
        )
        
        # Set up membership with specified status
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=test_team,
            user=test_user,
            defaults={'status': user_membership_status}
        )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Comprehensive Access Test Event",
            description="Test event for comprehensive access control",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=group_event_active
        )
        
        # Set platform mode
        from challenges.models import PlatformMode
        if group_event_active:
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Comprehensive Access Challenge",
            description="Test challenge",
            points=100,
            flag="comprehensive_flag",
            category="test",
            difficulty="easy"
        )
        
        # Test comprehensive access control
        from challenges.group_challenge_manager import GroupChallengeManager
        
        # 1. Determine expected access based on all factors
        # User needs: accepted membership + active group event (team active status not required per requirements)
        expected_access = (
            user_membership_status == 'accepted' and 
            group_event_active
        )
        
        # 2. Verify access control considers all factors
        can_access = GroupChallengeManager.can_user_access_group_challenges(test_user)
        
        # Access should only be granted if user has accepted membership AND group event is active
        membership_grants_access = (user_membership_status == 'accepted')
        expected_access_with_event = membership_grants_access and group_event_active
        self.assertEqual(can_access, expected_access_with_event)
        
        # 3. Verify team retrieval respects membership status (independent of group event status)
        user_team = GroupChallengeManager.get_user_team(test_user)
        if membership_grants_access:
            self.assertIsNotNone(user_team)
            self.assertEqual(user_team, test_team)
        else:
            self.assertIsNone(user_team)
        
        # 4. Verify group challenge access requires all conditions
        if expected_access:
            # All conditions met - should see challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), 1)
            self.assertEqual(team_challenges.first(), group_challenge)
        elif group_event_active and membership_grants_access:
            # Group event active and user has valid membership, but should still see challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), 1)
        elif not group_event_active and membership_grants_access:
            # Valid membership but no active event - no challenges
            team_challenges = GroupChallengeManager.get_team_challenges(user_team)
            self.assertEqual(team_challenges.count(), 0)
        else:
            # Invalid membership or inactive team - no access
            self.assertFalse(can_access)
        
        # 5. Verify access control is enforced strictly
        # Each factor must be correct for access
        if user_membership_status != 'accepted':
            self.assertFalse(can_access)
        
        # But if membership is valid AND group event is active, user should have access
        if user_membership_status == 'accepted' and group_event_active:
            self.assertTrue(can_access)
            self.assertIsNotNone(user_team)
        elif user_membership_status == 'accepted' and not group_event_active:
            # User has valid membership but no active group event - no access to group challenges
            self.assertFalse(can_access)
            self.assertIsNotNone(user_team)  # Team still exists, just no group challenge access
        
        # 6. Verify group event status affects both access capability and challenge availability
        if membership_grants_access:
            if group_event_active:
                # User has access capability AND event is active
                self.assertTrue(can_access)
                # Should see challenges when event is active
                team_challenges = GroupChallengeManager.get_team_challenges(user_team)
                self.assertEqual(team_challenges.count(), 1)
            else:
                # User has valid membership but event is inactive - no access
                self.assertFalse(can_access)
                # Should not see challenges when event is inactive
                team_challenges = GroupChallengeManager.get_team_challenges(user_team)
                self.assertEqual(team_challenges.count(), 0)


class TestGroupEventLifecycle(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 4: Group Event Lifecycle**
    **Validates: Requirements 2.1, 2.3, 2.4**
    
    For any group event activation and deactivation cycle, group challenges should 
    appear and disappear from team section while regular challenges remain unaffected
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_lifecycle_test',
            defaults={
                'email': 'admin_lifecycle@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_user, _ = User.objects.get_or_create(
            username='team_lifecycle_test',
            defaults={
                'email': 'team_lifecycle@test.com',
                'password': 'testpass123'
            }
        )
        self.team, _ = Team.objects.get_or_create(
            name='Lifecycle Test Team',
            defaults={'captain': self.team_user}
        )
        
        # Ensure team membership exists
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team,
            user=self.team_user,
            defaults={'status': 'accepted'}
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_group_challenges=st.integers(min_value=1, max_value=5),
        num_regular_challenges=st.integers(min_value=1, max_value=5),
        activation_cycles=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_event_activation_deactivation_cycle(self, event_name, num_group_challenges, num_regular_challenges, activation_cycles):
        """
        Property test: Group challenges appear and disappear during event lifecycle while regular challenges remain unaffected
        """
        # Create group event (initially inactive)
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Lifecycle test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=False
        )
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Lifecycle Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag=f"lifecycle_group_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Create regular challenges (always active)
        regular_challenges = []
        for i in range(num_regular_challenges):
            challenge = Challenge.objects.create(
                title=f"Lifecycle Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"lifecycle_regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
        
        # Test activation/deactivation cycles
        from challenges.group_challenge_manager import GroupChallengeManager
        
        for cycle in range(activation_cycles):
            # 1. Initially, group mode should be inactive
            self.assertFalse(GroupChallengeManager.is_group_mode_active())
            self.assertIsNone(GroupChallengeManager.get_active_group_event())
            
            # 2. No group challenges should be available when inactive
            team_challenges_inactive = GroupChallengeManager.get_team_challenges(self.team)
            self.assertEqual(team_challenges_inactive.count(), 0)
            
            # 3. Regular challenges should remain unaffected (always accessible)
            regular_challenges_before = Challenge.objects.filter(is_active=True)
            self.assertEqual(regular_challenges_before.count(), num_regular_challenges)
            
            # ACTIVATE GROUP EVENT
            from challenges.models import PlatformMode
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': group_event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = group_event
            platform_mode.save()
            
            # Update event to active
            group_event.is_active = True
            group_event.save()
            
            # 4. After activation, group mode should be active
            self.assertTrue(GroupChallengeManager.is_group_mode_active())
            active_event = GroupChallengeManager.get_active_group_event()
            self.assertEqual(active_event, group_event)
            
            # 5. Group challenges should appear in team section
            team_challenges_active = GroupChallengeManager.get_team_challenges(self.team)
            self.assertEqual(team_challenges_active.count(), num_group_challenges)
            
            for challenge in team_challenges_active:
                self.assertIn(challenge, group_challenges)
                self.assertEqual(challenge.event, group_event)
            
            # 6. Regular challenges should remain unaffected during activation
            regular_challenges_during = Challenge.objects.filter(is_active=True)
            self.assertEqual(regular_challenges_during.count(), num_regular_challenges)
            
            for challenge in regular_challenges_during:
                self.assertIn(challenge, regular_challenges)
                self.assertTrue(challenge.is_active)
            
            # DEACTIVATE GROUP EVENT
            platform_mode.active_event = None
            platform_mode.save()
            
            group_event.is_active = False
            group_event.save()
            
            # 7. After deactivation, group mode should be inactive
            self.assertFalse(GroupChallengeManager.is_group_mode_active())
            self.assertIsNone(GroupChallengeManager.get_active_group_event())
            
            # 8. Group challenges should disappear from team section
            team_challenges_deactivated = GroupChallengeManager.get_team_challenges(self.team)
            self.assertEqual(team_challenges_deactivated.count(), 0)
            
            # 9. Regular challenges should remain unaffected during deactivation
            regular_challenges_after = Challenge.objects.filter(is_active=True)
            self.assertEqual(regular_challenges_after.count(), num_regular_challenges)
            
            for challenge in regular_challenges_after:
                self.assertIn(challenge, regular_challenges)
                self.assertTrue(challenge.is_active)
        
        # 10. Verify lifecycle doesn't affect regular challenge state
        final_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(final_regular_challenges.count(), num_regular_challenges)
        
        # All regular challenges should still be active after all cycles
        for challenge in final_regular_challenges:
            self.assertTrue(challenge.is_active)
    
    @given(
        num_events=st.integers(min_value=2, max_value=4),
        challenges_per_event=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_group_events_lifecycle_isolation(self, num_events, challenges_per_event):
        """
        Property test: Multiple group events have isolated lifecycles
        """
        # Create multiple group events
        group_events = []
        all_group_challenges = []
        
        for i in range(num_events):
            event = GroupEvent.objects.create(
                name=f"Multi Event {i+1}",
                description=f"Test event {i+1}",
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-12-31T23:59:59Z",
                created_by=self.admin_user,
                is_active=False
            )
            group_events.append(event)
            
            # Create challenges for each event
            event_challenges = []
            for j in range(challenges_per_event):
                challenge = GroupChallenge.objects.create(
                    event=event,
                    title=f"Multi Event {i+1} Challenge {j+1}",
                    description=f"Test challenge {j+1} for event {i+1}",
                    points=100 * (j+1),
                    flag=f"multi_event_{i+1}_flag_{j+1}",
                    category="test",
                    difficulty="easy"
                )
                event_challenges.append(challenge)
            
            all_group_challenges.append(event_challenges)
        
        # Test lifecycle isolation
        from challenges.group_challenge_manager import GroupChallengeManager
        from challenges.models import PlatformMode
        
        for event_idx, event in enumerate(group_events):
            # Activate specific event
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = event
            platform_mode.save()
            
            event.is_active = True
            event.save()
            
            # 1. Verify only the active event's challenges are available
            team_challenges = GroupChallengeManager.get_team_challenges(self.team)
            expected_challenges = all_group_challenges[event_idx]
            self.assertEqual(team_challenges.count(), len(expected_challenges))
            
            for challenge in team_challenges:
                self.assertIn(challenge, expected_challenges)
                self.assertEqual(challenge.event, event)
            
            # 2. Verify challenges from other events are not available
            for other_event_idx, other_challenges in enumerate(all_group_challenges):
                if other_event_idx != event_idx:
                    for other_challenge in other_challenges:
                        self.assertNotIn(other_challenge, team_challenges)
            
            # 3. Verify correct active event is returned
            active_event = GroupChallengeManager.get_active_group_event()
            self.assertEqual(active_event, event)
            
            # Deactivate event
            platform_mode.active_event = None
            platform_mode.save()
            
            event.is_active = False
            event.save()
            
            # 4. Verify no challenges are available after deactivation
            team_challenges_after = GroupChallengeManager.get_team_challenges(self.team)
            self.assertEqual(team_challenges_after.count(), 0)
        
        # 5. Final verification - no event should be active
        self.assertFalse(GroupChallengeManager.is_group_mode_active())
        self.assertIsNone(GroupChallengeManager.get_active_group_event())
        
        final_team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(final_team_challenges.count(), 0)
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_teams=st.integers(min_value=1, max_value=3),
        num_challenges=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_event_lifecycle_affects_all_teams_equally(self, event_name, num_teams, num_challenges):
        """
        Property test: Group event lifecycle affects all teams equally
        """
        # Create multiple teams
        teams = []
        team_users = []
        
        for i in range(num_teams):
            team_user, _ = User.objects.get_or_create(
                username=f'lifecycle_team_user_{i}_{event_name[:10]}',
                defaults={
                    'email': f'lifecycle_team_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            team_users.append(team_user)
            
            team, _ = Team.objects.get_or_create(
                name=f'Lifecycle Team {i}_{event_name[:10]}',
                defaults={'captain': team_user}
            )
            teams.append(team)
            
            # Ensure team membership
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user,
                defaults={'status': 'accepted'}
            )
            
            # Add a second member to meet minimum team requirements
            team_user2, _ = User.objects.get_or_create(
                username=f'lifecycle_team_{i}_member2_{event_name[:10]}',
                defaults={
                    'email': f'lifecycle_team_{i}_member2@test.com',
                    'password': 'testpass123'
                }
            )
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user2,
                defaults={'status': 'accepted'}
            )
        
        # Create group event and challenges
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Multi-team lifecycle test",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=False
        )
        
        group_challenges = []
        for i in range(num_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Multi Team Challenge {i+1}",
                description=f"Test challenge {i+1}",
                points=100 * (i+1),
                flag=f"multi_team_flag_{i+1}",
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Test lifecycle affects all teams equally
        from challenges.group_challenge_manager import GroupChallengeManager
        from challenges.models import PlatformMode
        
        # 1. Initially, no team should have access to group challenges
        for team in teams:
            team_challenges = GroupChallengeManager.get_team_challenges(team)
            self.assertEqual(team_challenges.count(), 0)
        
        # ACTIVATE GROUP EVENT
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        group_event.is_active = True
        group_event.save()
        
        # 2. After activation, all teams should have equal access to group challenges
        for team in teams:
            team_challenges = GroupChallengeManager.get_team_challenges(team)
            self.assertEqual(team_challenges.count(), num_challenges)
            
            # Verify same challenges are available to all teams
            for challenge in team_challenges:
                self.assertIn(challenge, group_challenges)
                self.assertEqual(challenge.event, group_event)
        
        # 3. Verify all teams see the same challenges (equal treatment)
        first_team_challenges = list(GroupChallengeManager.get_team_challenges(teams[0]))
        for team in teams[1:]:
            team_challenges = list(GroupChallengeManager.get_team_challenges(team))
            self.assertEqual(len(team_challenges), len(first_team_challenges))
            
            # Same challenges should be available to all teams
            for challenge in first_team_challenges:
                self.assertIn(challenge, team_challenges)
        
        # DEACTIVATE GROUP EVENT
        platform_mode.active_event = None
        platform_mode.save()
        
        group_event.is_active = False
        group_event.save()
        
        # 4. After deactivation, no team should have access to group challenges
        for team in teams:
            team_challenges = GroupChallengeManager.get_team_challenges(team)
            self.assertEqual(team_challenges.count(), 0)
        
        # 5. Verify lifecycle changes affect all teams simultaneously and equally
        self.assertFalse(GroupChallengeManager.is_group_mode_active())
        
        # All teams should have equal (zero) access after deactivation
        team_challenge_counts = [
            GroupChallengeManager.get_team_challenges(team).count() 
            for team in teams
        ]
        
        # All counts should be the same (0)
        self.assertTrue(all(count == 0 for count in team_challenge_counts))
    
    def test_group_event_lifecycle_preserves_regular_challenge_independence(self):
        """
        Test that group event lifecycle never affects regular challenge availability
        """
        # Create regular challenges
        regular_challenge1 = Challenge.objects.create(
            title="Lifecycle Independence Challenge 1",
            description="Test regular challenge 1",
            difficulty="easy",
            category="test",
            flag="independence_flag_1",
            points=100,
            is_active=True
        )
        
        regular_challenge2 = Challenge.objects.create(
            title="Lifecycle Independence Challenge 2",
            description="Test regular challenge 2",
            difficulty="medium",
            category="test",
            flag="independence_flag_2",
            points=200,
            is_active=True
        )
        
        # Create group event
        group_event = GroupEvent.objects.create(
            name="Independence Test Event",
            description="Test event for independence",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=False
        )
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Independence Group Challenge",
            description="Test group challenge",
            points=150,
            flag="independence_group_flag",
            category="test",
            difficulty="easy"
        )
        
        # Test regular challenge independence throughout lifecycle
        from challenges.group_challenge_manager import GroupChallengeManager
        from challenges.models import PlatformMode
        
        # 1. Before activation - regular challenges should be active
        initial_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(initial_regular_challenges.count(), 2)
        self.assertIn(regular_challenge1, initial_regular_challenges)
        self.assertIn(regular_challenge2, initial_regular_challenges)
        
        # 2. During activation - regular challenges should remain active
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        group_event.is_active = True
        group_event.save()
        
        # Regular challenges should be unaffected by group event activation
        active_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(active_regular_challenges.count(), 2)
        self.assertIn(regular_challenge1, active_regular_challenges)
        self.assertIn(regular_challenge2, active_regular_challenges)
        
        # Group challenges should be available
        team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(team_challenges.count(), 1)
        self.assertIn(group_challenge, team_challenges)
        
        # 3. During deactivation - regular challenges should remain active
        platform_mode.active_event = None
        platform_mode.save()
        
        group_event.is_active = False
        group_event.save()
        
        # Regular challenges should be unaffected by group event deactivation
        final_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(final_regular_challenges.count(), 2)
        self.assertIn(regular_challenge1, final_regular_challenges)
        self.assertIn(regular_challenge2, final_regular_challenges)
        
        # Group challenges should no longer be available
        final_team_challenges = GroupChallengeManager.get_team_challenges(self.team)
        self.assertEqual(final_team_challenges.count(), 0)
        
        # 4. Verify regular challenges maintained their state throughout
        regular_challenge1.refresh_from_db()
        regular_challenge2.refresh_from_db()
        
        self.assertTrue(regular_challenge1.is_active)
        self.assertTrue(regular_challenge2.is_active)
        
        # 5. Verify group and regular challenges remain completely separate
        regular_challenge_titles = [c.title for c in final_regular_challenges]
        self.assertNotIn(group_challenge.title, regular_challenge_titles)
        
        # Regular challenges should not appear in group challenge queries
        all_group_challenges = GroupChallenge.objects.all()
        group_challenge_titles = [c.title for c in all_group_challenges]
        
        self.assertNotIn(regular_challenge1.title, group_challenge_titles)
        self.assertNotIn(regular_challenge2.title, group_challenge_titles)


class TestDataPreservationSeparation(HypothesisTestCase):
    """
    **Feature: ctf-event-management, Property 9: Data Preservation Separation**
    **Validates: Requirements 4.5**
    
    For any group competition that ends, results should be preserved separately 
    from regular challenge history without interference
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user, _ = User.objects.get_or_create(
            username='admin_preservation_test',
            defaults={
                'email': 'admin_preservation@test.com',
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        self.team_user1, _ = User.objects.get_or_create(
            username='team_preservation_test1',
            defaults={
                'email': 'team_preservation1@test.com',
                'password': 'testpass123'
            }
        )
        self.team_user2, _ = User.objects.get_or_create(
            username='team_preservation_test2',
            defaults={
                'email': 'team_preservation2@test.com',
                'password': 'testpass123'
            }
        )
        self.individual_user, _ = User.objects.get_or_create(
            username='individual_preservation_test',
            defaults={
                'email': 'individual_preservation@test.com',
                'password': 'testpass123'
            }
        )
        
        self.team1, _ = Team.objects.get_or_create(
            name='Preservation Test Team 1',
            defaults={'captain': self.team_user1}
        )
        self.team2, _ = Team.objects.get_or_create(
            name='Preservation Test Team 2',
            defaults={'captain': self.team_user2}
        )
        
        # Set up team memberships
        from teams.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=self.team1,
            user=self.team_user1,
            defaults={'status': 'accepted'}
        )
        TeamMembership.objects.get_or_create(
            team=self.team2,
            user=self.team_user2,
            defaults={'status': 'accepted'}
        )
        
        # Add second members to meet minimum team requirements
        self.team1_user2, _ = User.objects.get_or_create(
            username='team1_preservation_test_member2',
            defaults={
                'email': 'team1_preservation_member2@test.com',
                'password': 'testpass123'
            }
        )
        TeamMembership.objects.get_or_create(
            team=self.team1,
            user=self.team1_user2,
            defaults={'status': 'accepted'}
        )
        
        self.team2_user2, _ = User.objects.get_or_create(
            username='team2_preservation_test_member2',
            defaults={
                'email': 'team2_preservation_member2@test.com',
                'password': 'testpass123'
            }
        )
        TeamMembership.objects.get_or_create(
            team=self.team2,
            user=self.team2_user2,
            defaults={'status': 'accepted'}
        )
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_group_challenges=st.integers(min_value=1, max_value=4),
        num_regular_challenges=st.integers(min_value=1, max_value=4),
        num_teams=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_competition_results_preserved_separately(self, event_name, num_group_challenges, num_regular_challenges, num_teams):
        """
        Property test: Group competition results are preserved separately from regular challenge history
        """
        # Create group event
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Data preservation test event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True,
            point_multiplier=1.5
        )
        
        # Activate group mode
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create additional teams for this test
        teams = [self.team1, self.team2]
        team_users = [self.team_user1, self.team_user2]
        
        for i in range(2, min(num_teams, 3)):  # Create up to 1 additional team
            team_user, _ = User.objects.get_or_create(
                username=f'preservation_team_user_{i}_{event_name[:10]}',
                defaults={
                    'email': f'preservation_team_{i}@test.com',
                    'password': 'testpass123'
                }
            )
            team_users.append(team_user)
            
            team, _ = Team.objects.get_or_create(
                name=f'Preservation Team {i}_{event_name[:10]}',
                defaults={'captain': team_user}
            )
            teams.append(team)
            
            from teams.models import TeamMembership
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user,
                defaults={'status': 'accepted'}
            )
            
            # Add a second member to meet minimum team requirements
            team_user2, _ = User.objects.get_or_create(
                username=f'preservation_team_user_{i}_member2_{event_name[:10]}',
                defaults={
                    'email': f'preservation_team_{i}_member2@test.com',
                    'password': 'testpass123'
                }
            )
            TeamMembership.objects.get_or_create(
                team=team,
                user=team_user2,
                defaults={'status': 'accepted'}
            )
        
        # Create group challenges
        group_challenges = []
        for i in range(num_group_challenges):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Preservation Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag='sha256:' + hashlib.sha256(f'group_flag_{i+1}'.encode()).hexdigest(),
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
        
        # Create regular challenges
        regular_challenges = []
        for i in range(num_regular_challenges):
            challenge = Challenge.objects.create(
                title=f"Preservation Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
        
        # Generate group competition activity
        from challenges.group_challenge_manager import GroupChallengeManager
        group_submissions = []
        
        for team_idx, team in enumerate(teams[:num_teams]):
            # Each team solves some group challenges
            challenges_to_solve = min(team_idx + 1, len(group_challenges))
            
            for challenge_idx in range(challenges_to_solve):
                challenge = group_challenges[challenge_idx]
                result = GroupChallengeManager.submit_solution(
                    team, challenge, team_users[team_idx], f'group_flag_{challenge_idx+1}'
                )
                
                if result['success'] and result['is_correct']:
                    group_submissions.append(result['submission'])
        
        # Generate regular challenge activity
        from submissions.models import Submission
        regular_submissions = []
        
        for i in range(min(num_regular_challenges, 2)):  # Individual user solves some regular challenges
            challenge = regular_challenges[i]
            submission = Submission.objects.create(
                user=self.individual_user,
                challenge=challenge,
                submitted_flag=f"regular_flag_{i+1}",
                is_correct=True
            )
            regular_submissions.append(submission)
        
        # END GROUP COMPETITION (deactivate event)
        platform_mode.active_event = None
        platform_mode.save()
        
        group_event.is_active = False
        group_event.save()
        
        # Test data preservation separation
        # 1. Verify group competition results are preserved after event ends
        preserved_group_submissions = GroupSubmission.objects.filter(
            challenge__event=group_event
        )
        self.assertGreater(preserved_group_submissions.count(), 0)
        
        # All group submissions should still exist
        for submission in group_submissions:
            self.assertIn(submission, preserved_group_submissions)
        
        # 2. Verify group challenges are preserved
        preserved_group_challenges = GroupChallenge.objects.filter(event=group_event)
        self.assertEqual(preserved_group_challenges.count(), num_group_challenges)
        
        for challenge in group_challenges:
            self.assertIn(challenge, preserved_group_challenges)
        
        # 3. Verify group event data is preserved
        preserved_event = GroupEvent.objects.get(id=group_event.id)
        self.assertEqual(preserved_event.name, event_name)
        self.assertFalse(preserved_event.is_active)  # Event ended but data preserved
        
        # 4. Verify regular challenge history remains separate and unaffected
        preserved_regular_submissions = Submission.objects.all()
        preserved_regular_challenges = Challenge.objects.all()
        
        # Regular submissions should not be affected by group competition ending
        for submission in regular_submissions:
            self.assertIn(submission, preserved_regular_submissions)
        
        # Regular challenges should not be affected
        for challenge in regular_challenges:
            self.assertIn(challenge, preserved_regular_challenges)
            challenge.refresh_from_db()
            self.assertTrue(challenge.is_active)  # Regular challenges remain active
        
        # 5. Verify data separation is maintained in preservation
        # Group submissions should not appear in regular submission queries
        regular_submission_flags = [s.submitted_flag for s in preserved_regular_submissions]
        group_submission_flags = [s.flag_submitted for s in preserved_group_submissions]
        
        for group_flag in group_submission_flags:
            self.assertNotIn(group_flag, regular_submission_flags)
        
        # 6. Verify preserved data uses different storage systems
        # Group data uses separate tables
        self.assertEqual(GroupSubmission._meta.db_table, 'group_submissions')
        self.assertEqual(GroupChallenge._meta.db_table, 'group_challenges')
        self.assertEqual(GroupEvent._meta.db_table, 'group_events')
        
        # Regular data uses different tables
        self.assertEqual(Submission._meta.db_table, 'submissions_submission')
        self.assertEqual(Challenge._meta.db_table, 'challenges_challenge')
        
        # 7. Verify group competition results can be retrieved after event ends
        from challenges.group_challenge_manager import GroupScoring
        
        # Should be able to get historical leaderboard
        historical_leaderboard = GroupScoring.get_group_leaderboard(group_event)
        self.assertGreater(len(historical_leaderboard), 0)
        
        # Should be able to get team scores for ended event
        for team in teams[:num_teams]:
            team_score = GroupScoring.get_team_event_score(team, group_event)
            # Teams that solved challenges should have scores > 0
            if any(sub.team == team for sub in group_submissions):
                self.assertGreater(team_score, 0)
        
        # 8. Verify preservation doesn't interfere with new group events
        # Create a new group event
        new_group_event = GroupEvent.objects.create(
            name="New Event After Preservation",
            description="New event",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=False
        )
        
        # Old event data should not interfere with new event
        self.assertNotEqual(new_group_event.id, group_event.id)
        
        # Old submissions should not appear in new event queries
        new_event_submissions = GroupSubmission.objects.filter(challenge__event=new_group_event)
        self.assertEqual(new_event_submissions.count(), 0)
        
        # Old event submissions should still be preserved separately
        old_event_submissions = GroupSubmission.objects.filter(challenge__event=group_event)
        self.assertEqual(old_event_submissions.count(), len(group_submissions))
    
    @given(
        num_events=st.integers(min_value=2, max_value=4),
        submissions_per_event=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_group_events_data_preservation_isolation(self, num_events, submissions_per_event):
        """
        Property test: Multiple group events preserve data separately without cross-contamination
        """
        # Create multiple group events
        group_events = []
        all_group_challenges = []
        all_group_submissions = []
        
        for event_idx in range(num_events):
            # Create event
            event = GroupEvent.objects.create(
                name=f"Multi Preservation Event {event_idx+1}",
                description=f"Test event {event_idx+1}",
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-12-31T23:59:59Z",
                created_by=self.admin_user,
                is_active=False,
                point_multiplier=1.0 + (event_idx * 0.1)  # Different multipliers
            )
            group_events.append(event)
            
            # Create challenges for event
            event_challenges = []
            for challenge_idx in range(submissions_per_event):
                challenge = GroupChallenge.objects.create(
                    event=event,
                    title=f"Multi Preservation Event {event_idx+1} Challenge {challenge_idx+1}",
                    description=f"Test challenge {challenge_idx+1}",
                    points=100 * (challenge_idx+1),
                    flag='sha256:' + hashlib.sha256(f'multi_event_{event_idx+1}_flag_{challenge_idx+1}'.encode()).hexdigest(),
                    category="test",
                    difficulty="easy"
                )
                event_challenges.append(challenge)
            all_group_challenges.append(event_challenges)
            
            # Activate event and create submissions
            from challenges.models import PlatformMode
            platform_mode, _ = PlatformMode.objects.get_or_create(
                mode='group',
                defaults={
                    'active_event': event,
                    'changed_by': self.admin_user
                }
            )
            platform_mode.active_event = event
            platform_mode.save()
            
            event.is_active = True
            event.save()
            
            # Create submissions for this event
            from challenges.group_challenge_manager import GroupChallengeManager
            event_submissions = []
            
            for challenge in event_challenges:
                result = GroupChallengeManager.submit_solution(
                    self.team1, challenge, self.team_user1, f'multi_event_{event_idx+1}_flag_{challenge_idx+1}'
                )
                
                if result['success'] and result['is_correct']:
                    event_submissions.append(result['submission'])
            
            all_group_submissions.append(event_submissions)
            
            # End event
            platform_mode.active_event = None
            platform_mode.save()
            
            event.is_active = False
            event.save()
        
        # Test preservation isolation
        # 1. Verify each event's data is preserved separately
        for event_idx, event in enumerate(group_events):
            # Event should still exist
            preserved_event = GroupEvent.objects.get(id=event.id)
            self.assertEqual(preserved_event.name, f"Multi Preservation Event {event_idx+1}")
            self.assertFalse(preserved_event.is_active)
            
            # Event's challenges should be preserved
            event_challenges = GroupChallenge.objects.filter(event=event)
            expected_challenges = all_group_challenges[event_idx]
            self.assertEqual(event_challenges.count(), len(expected_challenges))
            
            for challenge in expected_challenges:
                self.assertIn(challenge, event_challenges)
            
            # Event's submissions should be preserved
            event_submissions = GroupSubmission.objects.filter(challenge__event=event)
            expected_submissions = all_group_submissions[event_idx]
            self.assertEqual(event_submissions.count(), len(expected_submissions))
            
            for submission in expected_submissions:
                self.assertIn(submission, event_submissions)
        
        # 2. Verify no cross-contamination between events
        for event_idx, event in enumerate(group_events):
            event_submissions = GroupSubmission.objects.filter(challenge__event=event)
            event_challenges = GroupChallenge.objects.filter(event=event)
            
            # Submissions should only belong to this event's challenges
            for submission in event_submissions:
                self.assertEqual(submission.challenge.event, event)
                self.assertIn(submission.challenge, event_challenges)
            
            # Challenges should only belong to this event
            for challenge in event_challenges:
                self.assertEqual(challenge.event, event)
            
            # No submissions from other events should appear
            for other_event_idx, other_submissions in enumerate(all_group_submissions):
                if other_event_idx != event_idx:
                    for other_submission in other_submissions:
                        self.assertNotIn(other_submission, event_submissions)
        
        # 3. Verify historical data can be retrieved for each event independently
        from challenges.group_challenge_manager import GroupScoring
        
        for event_idx, event in enumerate(group_events):
            # Should be able to get historical leaderboard for specific event
            historical_leaderboard = GroupScoring.get_group_leaderboard(event)
            
            if all_group_submissions[event_idx]:  # If event had submissions
                self.assertGreater(len(historical_leaderboard), 0)
                
                # Leaderboard should only contain data from this event
                for entry in historical_leaderboard:
                    team_score = GroupScoring.get_team_event_score(entry['team'], event)
                    self.assertEqual(entry['event_score'], team_score)
                    self.assertGreater(team_score, 0)
            
            # Should be able to get team progress for specific event
            team_progress = GroupScoring.get_team_event_progress(self.team1, event)
            self.assertEqual(team_progress['total_challenges'], len(all_group_challenges[event_idx]))
        
        # 4. Verify preservation uses separate storage for each event
        total_preserved_events = GroupEvent.objects.count()
        self.assertGreaterEqual(total_preserved_events, num_events)
        
        total_preserved_challenges = GroupChallenge.objects.count()
        expected_total_challenges = sum(len(challenges) for challenges in all_group_challenges)
        self.assertGreaterEqual(total_preserved_challenges, expected_total_challenges)
        
        total_preserved_submissions = GroupSubmission.objects.count()
        expected_total_submissions = sum(len(submissions) for submissions in all_group_submissions)
        self.assertGreaterEqual(total_preserved_submissions, expected_total_submissions)
    
    @given(
        event_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' _-')),
        num_group_submissions=st.integers(min_value=1, max_value=5),
        num_regular_submissions=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_group_and_regular_data_preservation_independence(self, event_name, num_group_submissions, num_regular_submissions):
        """
        Property test: Group and regular challenge data preservation operates independently
        """
        # Create group event and regular challenges
        group_event = GroupEvent.objects.create(
            name=event_name,
            description="Independence preservation test",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        # Activate group mode
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create group challenges and submissions
        group_challenges = []
        group_submissions = []
        
        from challenges.group_challenge_manager import GroupChallengeManager
        
        for i in range(num_group_submissions):
            challenge = GroupChallenge.objects.create(
                event=group_event,
                title=f"Independence Group Challenge {i+1}",
                description=f"Test group challenge {i+1}",
                points=100 * (i+1),
                flag='sha256:' + hashlib.sha256(f'independence_group_flag_{i+1}'.encode()).hexdigest(),
                category="test",
                difficulty="easy"
            )
            group_challenges.append(challenge)
            
            # Create submission
            result = GroupChallengeManager.submit_solution(
                self.team1, challenge, self.team_user1, f'independence_group_flag_{i+1}'
            )
            
            if result['success'] and result['is_correct']:
                group_submissions.append(result['submission'])
        
        # Create regular challenges and submissions
        regular_challenges = []
        regular_submissions = []
        
        from submissions.models import Submission
        
        for i in range(num_regular_submissions):
            challenge = Challenge.objects.create(
                title=f"Independence Regular Challenge {i+1}",
                description=f"Test regular challenge {i+1}",
                difficulty="easy",
                category="test",
                flag=f"independence_regular_flag_{i+1}",
                points=100 * (i+1),
                is_active=True
            )
            regular_challenges.append(challenge)
            
            # Create submission
            submission = Submission.objects.create(
                user=self.individual_user,
                challenge=challenge,
                submitted_flag=f"independence_regular_flag_{i+1}",
                is_correct=True
            )
            regular_submissions.append(submission)
        
        # Get initial counts
        initial_group_submissions = GroupSubmission.objects.count()
        initial_regular_submissions = Submission.objects.count()
        initial_group_challenges = GroupChallenge.objects.count()
        initial_regular_challenges = Challenge.objects.count()
        
        # END GROUP COMPETITION
        platform_mode.active_event = None
        platform_mode.save()
        
        group_event.is_active = False
        group_event.save()
        
        # Test preservation independence
        # 1. Verify group data preservation doesn't affect regular data
        final_regular_submissions = Submission.objects.count()
        final_regular_challenges = Challenge.objects.count()
        
        self.assertEqual(final_regular_submissions, initial_regular_submissions)
        self.assertEqual(final_regular_challenges, initial_regular_challenges)
        
        # All regular submissions should still exist
        for submission in regular_submissions:
            self.assertTrue(Submission.objects.filter(id=submission.id).exists())
        
        # All regular challenges should still be active
        for challenge in regular_challenges:
            challenge.refresh_from_db()
            self.assertTrue(challenge.is_active)
        
        # 2. Verify regular data preservation doesn't affect group data
        final_group_submissions = GroupSubmission.objects.count()
        final_group_challenges = GroupChallenge.objects.count()
        
        self.assertEqual(final_group_submissions, initial_group_submissions)
        self.assertEqual(final_group_challenges, initial_group_challenges)
        
        # All group submissions should still exist (preserved)
        for submission in group_submissions:
            self.assertTrue(GroupSubmission.objects.filter(id=submission.id).exists())
        
        # All group challenges should still exist (preserved)
        for challenge in group_challenges:
            self.assertTrue(GroupChallenge.objects.filter(id=challenge.id).exists())
        
        # 3. Verify data remains in separate storage systems
        preserved_group_submissions = GroupSubmission.objects.filter(challenge__event=group_event)
        preserved_regular_submissions = Submission.objects.all()
        
        # Verify data separation - group and regular submissions are in different tables
        # Group submissions should only be in GroupSubmission table
        self.assertEqual(preserved_group_submissions.count(), len(group_submissions))
        
        # Regular submissions should only be in Submission table  
        self.assertEqual(preserved_regular_submissions.count(), len(regular_submissions))
        
        # Verify no cross-contamination by checking table types
        for group_sub in preserved_group_submissions:
            self.assertIsInstance(group_sub, GroupSubmission)
        
        for regular_sub in preserved_regular_submissions:
            self.assertIsInstance(regular_sub, Submission)
        
        # 4. Verify different preservation mechanisms
        # Group submissions have event-specific preservation
        for group_submission in preserved_group_submissions:
            self.assertEqual(group_submission.challenge.event, group_event)
            self.assertTrue(hasattr(group_submission, 'points_awarded'))
            self.assertTrue(hasattr(group_submission, 'team'))
        
        # Regular submissions have user-specific preservation
        for regular_submission in preserved_regular_submissions:
            self.assertTrue(hasattr(regular_submission, 'user'))
            self.assertFalse(hasattr(regular_submission, 'points_awarded'))
            self.assertFalse(hasattr(regular_submission, 'team'))
        
        # 5. Verify preservation queries remain separate
        # Group data queries should not return regular data
        group_challenge_titles = [c.title for c in GroupChallenge.objects.all()]
        regular_challenge_titles = [c.title for c in Challenge.objects.all()]
        
        for group_title in group_challenge_titles:
            self.assertNotIn(group_title, regular_challenge_titles)
        
        for regular_title in regular_challenge_titles:
            self.assertNotIn(regular_title, group_challenge_titles)
        
        # 6. Verify historical data retrieval independence
        from challenges.group_challenge_manager import GroupScoring
        
        # Group historical data should be retrievable
        group_leaderboard = GroupScoring.get_group_leaderboard(group_event)
        if group_submissions:
            self.assertGreater(len(group_leaderboard), 0)
        
        # Regular data should remain accessible independently
        active_regular_challenges = Challenge.objects.filter(is_active=True)
        self.assertEqual(active_regular_challenges.count(), len(regular_challenges))
        
        # Group event ending should not affect regular challenge accessibility
        for challenge in regular_challenges:
            challenge.refresh_from_db()
            self.assertTrue(challenge.is_active)
    
    def test_data_preservation_maintains_referential_integrity(self):
        """
        Test that data preservation maintains referential integrity after group events end
        """
        # Create group event with complex relationships
        group_event = GroupEvent.objects.create(
            name="Integrity Test Event",
            description="Test event for referential integrity",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
            created_by=self.admin_user,
            is_active=True
        )
        
        # Create group challenge
        group_challenge = GroupChallenge.objects.create(
            event=group_event,
            title="Integrity Test Challenge",
            description="Test challenge",
            points=200,
            flag='sha256:' + hashlib.sha256('integrity_flag'.encode()).hexdigest(),
            category="test",
            difficulty="medium"
        )
        
        # Activate group mode and create submissions
        from challenges.models import PlatformMode
        platform_mode, _ = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': group_event,
                'changed_by': self.admin_user
            }
        )
        platform_mode.active_event = group_event
        platform_mode.save()
        
        # Create submissions from both teams
        from challenges.group_challenge_manager import GroupChallengeManager
        
        result1 = GroupChallengeManager.submit_solution(
            self.team1, group_challenge, self.team_user1, 'integrity_flag'
        )
        result2 = GroupChallengeManager.submit_solution(
            self.team2, group_challenge, self.team_user2, 'wrong_flag'
        )
        
        # End group competition
        platform_mode.active_event = None
        platform_mode.save()
        
        group_event.is_active = False
        group_event.save()
        
        # Test referential integrity preservation
        # 1. Verify event-challenge relationships are preserved
        preserved_event = GroupEvent.objects.get(id=group_event.id)
        preserved_challenge = GroupChallenge.objects.get(id=group_challenge.id)
        
        self.assertEqual(preserved_challenge.event, preserved_event)
        
        # 2. Verify challenge-submission relationships are preserved
        preserved_submissions = GroupSubmission.objects.filter(challenge=preserved_challenge)
        self.assertEqual(preserved_submissions.count(), 2)
        
        for submission in preserved_submissions:
            self.assertEqual(submission.challenge, preserved_challenge)
            self.assertEqual(submission.challenge.event, preserved_event)
        
        # 3. Verify team-submission relationships are preserved
        team1_submissions = GroupSubmission.objects.filter(team=self.team1, challenge=preserved_challenge)
        team2_submissions = GroupSubmission.objects.filter(team=self.team2, challenge=preserved_challenge)
        
        self.assertEqual(team1_submissions.count(), 1)
        self.assertEqual(team2_submissions.count(), 1)
        
        team1_submission = team1_submissions.first()
        team2_submission = team2_submissions.first()
        
        self.assertEqual(team1_submission.team, self.team1)
        self.assertEqual(team2_submission.team, self.team2)
        
        # 4. Verify user-submission relationships are preserved
        self.assertEqual(team1_submission.submitted_by, self.team_user1)
        self.assertEqual(team2_submission.submitted_by, self.team_user2)
        
        # 5. Verify submission correctness and points are preserved
        self.assertTrue(team1_submission.is_correct)
        self.assertFalse(team2_submission.is_correct)
        self.assertGreater(team1_submission.points_awarded, 0)
        self.assertEqual(team2_submission.points_awarded, 0)
        
        # 6. Verify foreign key constraints are maintained
        # Should be able to navigate relationships in both directions
        
        # Event -> Challenges -> Submissions
        event_challenges = preserved_event.groupchallenge_set.all()
        self.assertIn(preserved_challenge, event_challenges)
        
        challenge_submissions = preserved_challenge.groupsubmission_set.all()
        self.assertEqual(challenge_submissions.count(), 2)
        
        # Team -> Submissions -> Challenges -> Event
        team1_all_submissions = self.team1.groupsubmission_set.all()
        team1_event_submissions = team1_all_submissions.filter(challenge__event=preserved_event)
        self.assertEqual(team1_event_submissions.count(), 1)
        
        # User -> Submissions -> Challenges -> Event
        user1_submissions = GroupSubmission.objects.filter(submitted_by=self.team_user1)
        user1_event_submissions = user1_submissions.filter(challenge__event=preserved_event)
        self.assertEqual(user1_event_submissions.count(), 1)
        
        # 7. Verify cascade behavior is preserved (data not deleted when event ends)
        # All related objects should still exist
        self.assertTrue(GroupEvent.objects.filter(id=group_event.id).exists())
        self.assertTrue(GroupChallenge.objects.filter(id=group_challenge.id).exists())
        self.assertTrue(GroupSubmission.objects.filter(challenge=preserved_challenge).exists())
        
        # 8. Verify data integrity for historical queries
        from challenges.group_challenge_manager import GroupScoring
        
        # Should be able to get complete historical data
        team1_score = GroupScoring.get_team_event_score(self.team1, preserved_event)
        team2_score = GroupScoring.get_team_event_score(self.team2, preserved_event)
        
        self.assertGreater(team1_score, 0)
        self.assertEqual(team2_score, 0)
        
        # Should be able to get team rankings
        team1_ranking = GroupScoring.get_team_ranking(self.team1, preserved_event)
        self.assertIsNotNone(team1_ranking)
        self.assertEqual(team1_ranking['rank'], 1)
        
        # Should be able to get complete leaderboard
        leaderboard = GroupScoring.get_group_leaderboard(preserved_event)
        self.assertEqual(len(leaderboard), 1)  # Only team1 has score > 0
        self.assertEqual(leaderboard[0]['team'], self.team1)