"""
Unit tests for team section integration with group competitions
Tests team section rendering, team management functionality, and collaboration features
"""

import unittest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from teams.models import Team, TeamMembership
from challenges.models import GroupEvent, GroupChallenge, GroupSubmission, PlatformMode
from challenges.group_challenge_manager import GroupChallengeManager, GroupScoring


class TeamSectionIntegrationTestCase(TestCase):
    """Base test case with common setup for team section integration tests"""
    
    def setUp(self):
        """Set up test data for team section integration tests"""
        # Create test users
        self.captain = User.objects.create_user(
            username='captain',
            email='captain@test.com',
            password='testpass123'
        )
        
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='testpass123'
        )
        
        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='testpass123'
        )
        
        self.non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@test.com',
            password='testpass123'
        )
        
        # Create test team
        self.team = Team.objects.create(
            name='Test Team',
            captain=self.captain,
            description='Test team for integration tests',
            max_members=5
        )
        
        # Add team members
        TeamMembership.objects.create(
            team=self.team,
            user=self.captain,
            status='accepted'
        )
        
        TeamMembership.objects.create(
            team=self.team,
            user=self.member1,
            status='accepted'
        )
        
        TeamMembership.objects.create(
            team=self.team,
            user=self.member2,
            status='accepted'
        )
        
        # Create group event
        self.group_event = GroupEvent.objects.create(
            name='Test Group Competition',
            description='Test group competition for integration tests',
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=23),
            is_active=True,
            created_by=self.captain,
            point_multiplier=1.5,
            max_teams=10
        )
        
        # Create group challenges
        self.group_challenge1 = GroupChallenge.objects.create(
            event=self.group_event,
            title='Group Challenge 1',
            description='First group challenge',
            points=100,
            flag='sha256:' + 'test_flag_1'.encode().hex(),
            category='web',
            difficulty='easy',
            requires_collaboration=True,
            max_attempts_per_team=5
        )
        
        self.group_challenge2 = GroupChallenge.objects.create(
            event=self.group_event,
            title='Group Challenge 2',
            description='Second group challenge',
            points=200,
            flag='sha256:' + 'test_flag_2'.encode().hex(),
            category='crypto',
            difficulty='medium',
            requires_collaboration=True,
            max_attempts_per_team=3
        )
        
        # Set up platform mode for group competition
        self.platform_mode = PlatformMode.objects.create(
            mode='group',
            active_event=self.group_event,
            changed_by=self.captain
        )
        
        self.client = Client()


class TeamDetailIntegrationTest(TeamSectionIntegrationTestCase):
    """Test team detail page integration with group competitions"""
    
    def test_team_detail_renders_group_event_banner_for_members(self):
        """Test that team detail page shows group event banner for team members"""
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:team_detail', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group Competition')
        self.assertContains(response, 'Active Competition')
        self.assertContains(response, 'Access Group Challenges')
        self.assertContains(response, 'Team Collaboration Dashboard')
    
    def test_team_detail_shows_join_prompt_for_non_members(self):
        """Test that team detail page shows join prompt for non-members during group events"""
        self.client.login(username='nonmember', password='testpass123')
        
        response = self.client.get(reverse('teams:team_detail', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group Competition')
        self.assertContains(response, 'Join this team to participate')
        self.assertNotContains(response, 'Access Group Challenges')
        # Non-members shouldn't see collaboration dashboard
        self.assertNotContains(response, 'Real-time team progress')
    
    def test_team_detail_includes_group_event_progress_data(self):
        """Test that team detail page includes group event progress data"""
        # Create some team submissions
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150  # 100 * 1.5 multiplier
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:team_detail', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that progress data is included
        self.assertIn('team_progress', response.context)
        self.assertIn('team_ranking', response.context)
        self.assertIn('team_event_score', response.context)
        self.assertIn('recent_team_submissions', response.context)
        
        # Verify progress data
        team_progress = response.context['team_progress']
        self.assertEqual(team_progress['solved_challenges'], 1)
        self.assertEqual(team_progress['total_challenges'], 2)
        self.assertEqual(team_progress['progress_percentage'], 50.0)
        
        # Verify event score
        team_event_score = response.context['team_event_score']
        self.assertEqual(team_event_score, 150)
    
    def test_team_detail_without_group_event_active(self):
        """Test team detail page when no group event is active"""
        # Deactivate group event
        self.platform_mode.active_event = None
        self.platform_mode.save()
        
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:team_detail', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Active Competition')
        # Should not show collaboration dashboard when no group event
        self.assertNotContains(response, 'Real-time team progress')
        self.assertIsNone(response.context.get('team_progress'))
        self.assertIsNone(response.context.get('team_ranking'))


class TeamManagementIntegrationTest(TeamSectionIntegrationTestCase):
    """Test team management page integration with group competitions"""
    
    def test_team_management_renders_group_event_section(self):
        """Test that team management page shows group event management section"""
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Group Competition Management')
        self.assertContains(response, 'Test Group Competition')
        self.assertContains(response, 'Team Competition Readiness')
        self.assertContains(response, 'Event Progress')
    
    def test_team_management_shows_readiness_check(self):
        """Test that team management shows team readiness check for group competition"""
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        
        # Team should be ready (has 3 members, minimum is 2)
        self.assertContains(response, 'Team Can Compete')
        self.assertContains(response, 'Ready to Compete!')
        self.assertContains(response, 'Access Group Challenges')
    
    def test_team_management_shows_not_ready_for_small_team(self):
        """Test team management shows not ready status for teams with insufficient members"""
        # Remove members to make team too small
        TeamMembership.objects.filter(team=self.team, user=self.member1).delete()
        TeamMembership.objects.filter(team=self.team, user=self.member2).delete()
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Action Required')
        self.assertContains(response, 'needs at least 2 members')
        self.assertNotContains(response, 'Ready to Compete!')
    
    def test_team_management_includes_event_statistics(self):
        """Test that team management includes group event statistics"""
        # Create team submissions for statistics
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member2,
            flag_submitted='wrong_flag',
            is_correct=False,
            points_awarded=0
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that event statistics are included
        self.assertIn('team_progress', response.context)
        self.assertIn('team_ranking', response.context)
        self.assertIn('team_event_score', response.context)
        
        # Verify statistics
        team_progress = response.context['team_progress']
        self.assertEqual(team_progress['solved_challenges'], 1)
        
        team_event_score = response.context['team_event_score']
        self.assertEqual(team_event_score, 150)
    
    def test_team_management_access_control(self):
        """Test that only team captains can access team management with group features"""
        # Test non-captain access
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        
        # Should redirect to team detail
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('teams:team_detail', args=[self.team.id]))


class GroupChallengesIntegrationTest(TeamSectionIntegrationTestCase):
    """Test group challenges page integration and collaboration features"""
    
    def test_group_challenges_renders_collaboration_tab(self):
        """Test that group challenges page includes collaboration tab"""
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Collaboration')
        self.assertContains(response, 'Team Collaboration Tools')
        self.assertContains(response, 'Team Members')
        self.assertContains(response, 'Challenge Distribution')
    
    def test_group_challenges_includes_team_member_data(self):
        """Test that group challenges page includes team member collaboration data"""
        # Create submissions from different team members
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member2,
            flag_submitted='wrong_flag',
            is_correct=False,
            points_awarded=0
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check team members data
        self.assertIn('team_members', response.context)
        team_members = response.context['team_members']
        self.assertEqual(len(team_members), 3)  # captain, member1, member2
        
        # Check that submission counts are calculated
        member1_data = next(m for m in team_members if m.user.username == 'member1')
        self.assertEqual(member1_data.submissions_count, 1)
        
        member2_data = next(m for m in team_members if m.user.username == 'member2')
        self.assertEqual(member2_data.submissions_count, 1)
    
    def test_group_challenges_includes_challenge_categories(self):
        """Test that group challenges page includes challenge category distribution"""
        # Create a submission to have some solved challenges
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,  # web category
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check challenge categories data
        self.assertIn('challenge_categories', response.context)
        challenge_categories = response.context['challenge_categories']
        
        # Should have web and crypto categories
        self.assertIn('web', challenge_categories)
        self.assertIn('crypto', challenge_categories)
        
        # Web category should have 1 solved out of 1 total
        web_data = challenge_categories['web']
        self.assertEqual(web_data['total'], 1)
        self.assertEqual(web_data['solved'], 1)
        self.assertEqual(web_data['percentage'], 100.0)
        
        # Crypto category should have 0 solved out of 1 total
        crypto_data = challenge_categories['crypto']
        self.assertEqual(crypto_data['total'], 1)
        self.assertEqual(crypto_data['solved'], 0)
        self.assertEqual(crypto_data['percentage'], 0.0)
    
    def test_group_challenges_includes_team_metrics(self):
        """Test that group challenges page includes team performance metrics"""
        # Create various submissions for metrics calculation
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='wrong_flag',
            is_correct=False,
            points_awarded=0
        )
        
        GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member2,
            flag_submitted='test_flag_2',
            is_correct=True,
            points_awarded=300
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check team metrics data
        self.assertIn('team_metrics', response.context)
        team_metrics = response.context['team_metrics']
        
        # Success rate: 2 correct out of 3 total = 66.7%
        self.assertEqual(team_metrics['success_rate'], 66.7)
        
        # Attempts per solve: 3 attempts / 2 solves = 1.5
        self.assertEqual(team_metrics['attempts_per_solve'], 1.5)
        
        # Collaboration score: 2 active members out of 3 total = 66.7%
        self.assertEqual(team_metrics['collaboration_score'], 66.7)
    
    def test_group_challenges_access_control_for_non_team_members(self):
        """Test that non-team members cannot access group challenges"""
        self.client.login(username='nonmember', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        # Should redirect to team list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('teams:team_list'))
    
    def test_group_challenges_access_control_when_no_group_event(self):
        """Test that group challenges are not accessible when no group event is active"""
        # Deactivate group event
        self.platform_mode.active_event = None
        self.platform_mode.save()
        
        self.client.login(username='member1', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        # Should redirect to my team (which then redirects to team detail)
        self.assertEqual(response.status_code, 302)
        # Follow the redirect chain
        final_response = self.client.get(reverse('teams:group_challenges'), follow=True)
        self.assertEqual(final_response.status_code, 200)
        # Should end up at team detail page
        self.assertContains(final_response, self.team.name)


class TeamCollaborationFeaturesTest(TeamSectionIntegrationTestCase):
    """Test specific team collaboration features"""
    
    def test_team_activity_timeline_rendering(self):
        """Test that team activity timeline renders correctly"""
        # Create submissions with different timestamps
        submission1 = GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        submission2 = GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member2,
            flag_submitted='wrong_flag',
            is_correct=False,
            points_awarded=0
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Activity Timeline')
        self.assertContains(response, 'Group Challenge 1')
        self.assertContains(response, 'Group Challenge 2')
        self.assertContains(response, 'member1')
        self.assertContains(response, 'member2')
        self.assertContains(response, 'Solved (+150 points)')
        self.assertContains(response, 'Attempted')
    
    def test_team_progress_tracking_accuracy(self):
        """Test that team progress tracking is accurate across different views"""
        # Create submissions
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        self.client.login(username='captain', password='testpass123')
        
        # Check team detail progress
        detail_response = self.client.get(reverse('teams:team_detail', args=[self.team.id]))
        detail_progress = detail_response.context['team_progress']
        
        # Check team management progress
        management_response = self.client.get(reverse('teams:team_management', args=[self.team.id]))
        management_progress = management_response.context['team_progress']
        
        # Check group challenges progress
        challenges_response = self.client.get(reverse('teams:group_challenges'))
        challenges_progress = challenges_response.context['team_progress']
        
        # All should show the same progress
        self.assertEqual(detail_progress['solved_challenges'], 1)
        self.assertEqual(management_progress['solved_challenges'], 1)
        self.assertEqual(challenges_progress['solved_challenges'], 1)
        
        self.assertEqual(detail_progress['progress_percentage'], 50.0)
        self.assertEqual(management_progress['progress_percentage'], 50.0)
        self.assertEqual(challenges_progress['progress_percentage'], 50.0)
    
    def test_team_collaboration_score_calculation(self):
        """Test that team collaboration score is calculated correctly"""
        # Only member1 makes submissions (1 out of 3 members active)
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_1',
            is_correct=True,
            points_awarded=150
        )
        
        GroupSubmission.objects.create(
            challenge=self.group_challenge2,
            team=self.team,
            submitted_by=self.member1,
            flag_submitted='test_flag_2',
            is_correct=True,
            points_awarded=300
        )
        
        self.client.login(username='captain', password='testpass123')
        
        response = self.client.get(reverse('teams:group_challenges'))
        
        team_metrics = response.context['team_metrics']
        
        # Collaboration score: 1 active member out of 3 total = 33.3%
        self.assertEqual(team_metrics['collaboration_score'], 33.3)
        
        # Now add submission from another member
        GroupSubmission.objects.create(
            challenge=self.group_challenge1,
            team=self.team,
            submitted_by=self.member2,
            flag_submitted='wrong_flag',
            is_correct=False,
            points_awarded=0
        )
        
        response = self.client.get(reverse('teams:group_challenges'))
        team_metrics = response.context['team_metrics']
        
        # Collaboration score: 2 active members out of 3 total = 66.7%
        self.assertEqual(team_metrics['collaboration_score'], 66.7)


if __name__ == '__main__':
    unittest.main()