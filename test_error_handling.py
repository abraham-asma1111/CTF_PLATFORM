"""
Unit tests for error handling and validation in group event management system
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from unittest.mock import patch, Mock
from challenges.models import GroupEvent, GroupChallenge, GroupSubmission, PlatformMode
from challenges.validators import (
    GroupEventValidator,
    TeamMembershipValidator,
    DatabaseConnectionValidator,
    GroupEventValidationError,
    TeamMembershipValidationError,
    DatabaseConnectionError,
    AccessDeniedError,
    ErrorMessageGenerator
)
from challenges.error_handlers import ErrorHandler
from challenges.group_challenge_manager import GroupChallengeManager
from teams.models import Team, TeamMembership
from datetime import timedelta


class GroupEventValidationTests(TestCase):
    """Test invalid event activation scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create test event
        self.start_time = timezone.now() + timedelta(hours=1)
        self.end_time = self.start_time + timedelta(hours=2)
        
        self.event = GroupEvent.objects.create(
            name='Test Event',
            description='Test Description',
            start_time=self.start_time,
            end_time=self.end_time,
            created_by=self.user
        )
    
    def test_invalid_event_creation_empty_name(self):
        """Test event creation with empty name fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='',
                description='Valid description',
                start_time=self.start_time,
                end_time=self.end_time,
                created_by=self.user
            )
        
        self.assertIn('Event name is required', str(context.exception))
    
    def test_invalid_event_creation_empty_description(self):
        """Test event creation with empty description fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='Valid Name',
                description='',
                start_time=self.start_time,
                end_time=self.end_time,
                created_by=self.user
            )
        
        self.assertIn('Event description is required', str(context.exception))
    
    def test_invalid_event_creation_start_after_end(self):
        """Test event creation with start time after end time fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='Valid Name',
                description='Valid description',
                start_time=self.end_time,
                end_time=self.start_time,
                created_by=self.user
            )
        
        self.assertIn('start time must be before end time', str(context.exception))
    
    def test_invalid_event_creation_duplicate_name(self):
        """Test event creation with duplicate name fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='Test Event',  # Same as existing event
                description='Valid description',
                start_time=self.start_time + timedelta(days=1),
                end_time=self.end_time + timedelta(days=1),
                created_by=self.user
            )
        
        self.assertIn('already exists', str(context.exception))
    
    def test_invalid_event_creation_overlapping_times(self):
        """Test event creation with overlapping times fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='Overlapping Event',
                description='Valid description',
                start_time=self.start_time + timedelta(minutes=30),
                end_time=self.end_time + timedelta(minutes=30),
                created_by=self.user
            )
        
        self.assertIn('overlaps with existing events', str(context.exception))
    
    def test_invalid_event_creation_too_short_duration(self):
        """Test event creation with duration less than 1 hour fails validation"""
        short_end = self.start_time + timedelta(minutes=30)
        
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_creation(
                name='Short Event',
                description='Valid description',
                start_time=self.start_time,
                end_time=short_end,
                created_by=self.user
            )
        
        self.assertIn('at least 1 hour long', str(context.exception))
    
    def test_invalid_event_activation_non_staff_user(self):
        """Test event activation by non-staff user fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_activation(self.event, self.regular_user)
        
        self.assertIn('Only staff members can activate', str(context.exception))
    
    def test_invalid_event_activation_past_event(self):
        """Test activation of past event fails validation"""
        past_event = GroupEvent.objects.create(
            name='Past Event',
            description='Past event description',
            start_time=timezone.now() - timedelta(hours=3),
            end_time=timezone.now() - timedelta(hours=1),
            created_by=self.user
        )
        
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_activation(past_event, self.user)
        
        self.assertIn('Cannot activate past event', str(context.exception))
    
    def test_invalid_event_activation_already_active(self):
        """Test activation of already active event fails validation"""
        self.event.is_active = True
        self.event.save()
        
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_activation(self.event, self.user)
        
        self.assertIn('already active', str(context.exception))
    
    def test_invalid_event_activation_no_challenges(self):
        """Test activation of event with no challenges fails validation"""
        with self.assertRaises(GroupEventValidationError) as context:
            GroupEventValidator.validate_event_activation(self.event, self.user)
        
        self.assertIn('has no challenges', str(context.exception))
    
    def test_valid_event_creation(self):
        """Test valid event creation passes validation"""
        result = GroupEventValidator.validate_event_creation(
            name='Valid Event',
            description='Valid description',
            start_time=self.start_time + timedelta(days=1),
            end_time=self.end_time + timedelta(days=1),
            created_by=self.user
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['validated_data']['name'], 'Valid Event')
    
    def test_valid_event_activation_with_challenges(self):
        """Test valid event activation passes validation"""
        # Add a challenge to the event
        GroupChallenge.objects.create(
            event=self.event,
            title='Test Challenge',
            description='Test challenge description',
            points=100,
            flag='test_flag',
            category='web',
            difficulty='easy'
        )
        
        result = GroupEventValidator.validate_event_activation(self.event, self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['event'], self.event)


class TeamMembershipValidationTests(TestCase):
    """Test team membership validation errors"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.captain = User.objects.create_user(
            username='captain',
            email='captain@test.com',
            password='testpass123'
        )
        
        self.team = Team.objects.create(
            name='Test Team',
            captain=self.captain,
            description='Test team description'
        )
        
        # Add captain to team
        TeamMembership.objects.create(
            team=self.team,
            user=self.captain,
            status='accepted'
        )
    
    def test_team_access_validation_unauthenticated_user(self):
        """Test team access validation fails for unauthenticated user"""
        anonymous_user = Mock()
        anonymous_user.is_authenticated = False
        
        with self.assertRaises(TeamMembershipValidationError) as context:
            TeamMembershipValidator.validate_team_access(anonymous_user)
        
        self.assertIn('must be authenticated', str(context.exception))
    
    def test_team_access_validation_user_not_in_team(self):
        """Test team access validation fails for user not in team"""
        with self.assertRaises(TeamMembershipValidationError) as context:
            TeamMembershipValidator.validate_team_access(self.user)
        
        self.assertIn('must be in a team', str(context.exception))
    
    def test_team_access_validation_user_not_in_specific_team(self):
        """Test team access validation fails for user not in specific team"""
        # Create another team and add user to it
        other_team = Team.objects.create(
            name='Other Team',
            captain=self.user,
            description='Other team description'
        )
        TeamMembership.objects.create(
            team=other_team,
            user=self.user,
            status='accepted'
        )
        
        with self.assertRaises(TeamMembershipValidationError) as context:
            TeamMembershipValidator.validate_team_access(self.user, self.team)
        
        self.assertIn('not a member of team', str(context.exception))
    
    def test_group_challenge_access_unauthenticated(self):
        """Test group challenge access fails for unauthenticated user"""
        anonymous_user = Mock()
        anonymous_user.is_authenticated = False
        
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_group_challenge_access(anonymous_user)
        
        self.assertIn('Authentication required', str(context.exception))
    
    def test_group_challenge_access_no_group_mode(self):
        """Test group challenge access fails when group mode is not active"""
        # Add user to team
        TeamMembership.objects.create(
            team=self.team,
            user=self.user,
            status='accepted'
        )
        
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_group_challenge_access(self.user)
        
        self.assertIn('not in group mode', str(context.exception))
    
    def test_group_challenge_access_user_not_in_team(self):
        """Test group challenge access fails for user not in team"""
        # Create group mode
        event = GroupEvent.objects.create(
            name='Test Event',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            created_by=self.captain,
            is_active=True
        )
        PlatformMode.objects.create(
            mode='group',
            active_event=event,
            changed_by=self.captain
        )
        
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_group_challenge_access(self.user)
        
        self.assertIn('must be in a team', str(context.exception))
    
    def test_group_challenge_access_team_too_small(self):
        """Test group challenge access fails for team that's too small"""
        # Create group mode
        event = GroupEvent.objects.create(
            name='Test Event',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            created_by=self.captain,
            is_active=True
        )
        PlatformMode.objects.create(
            mode='group',
            active_event=event,
            changed_by=self.captain
        )
        
        # Add user to team (team will have only 1 member - captain)
        TeamMembership.objects.create(
            team=self.team,
            user=self.user,
            status='accepted'
        )
        
        # Remove captain to make team too small
        TeamMembership.objects.filter(user=self.captain).delete()
        
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_group_challenge_access(self.user)
        
        self.assertIn('needs at least 2 members', str(context.exception))
    
    def test_captain_permissions_validation_not_captain(self):
        """Test captain permissions validation fails for non-captain"""
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_team_captain_permissions(self.user, self.team)
        
        self.assertIn('Only team captain can perform', str(context.exception))
    
    def test_captain_permissions_validation_inactive_team(self):
        """Test captain permissions validation fails for inactive team"""
        self.team.is_active = False
        self.team.save()
        
        with self.assertRaises(AccessDeniedError) as context:
            TeamMembershipValidator.validate_team_captain_permissions(self.captain, self.team)
        
        self.assertIn('not active', str(context.exception))
    
    def test_valid_team_access(self):
        """Test valid team access passes validation"""
        # Add user to team
        TeamMembership.objects.create(
            team=self.team,
            user=self.user,
            status='accepted'
        )
        
        result = TeamMembershipValidator.validate_team_access(self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user_team'], self.team)
    
    def test_valid_captain_permissions(self):
        """Test valid captain permissions pass validation"""
        result = TeamMembershipValidator.validate_team_captain_permissions(self.captain, self.team)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['team'], self.team)


class DatabaseConnectionTests(TestCase):
    """Test database connection failure handling"""
    
    def test_database_connection_validation_success(self):
        """Test successful database connection validation"""
        result = DatabaseConnectionValidator.validate_database_connection()
        
        self.assertTrue(result['success'])
        self.assertIn('healthy', result['message'])
    
    @patch('django.db.connection')
    def test_database_connection_validation_failure(self, mock_connection):
        """Test database connection validation failure"""
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = DatabaseError('Connection failed')
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with self.assertRaises(DatabaseConnectionError) as context:
            DatabaseConnectionValidator.validate_database_connection()
        
        self.assertIn('Database connection failed', str(context.exception))
    
    @patch('challenges.validators.DatabaseConnectionValidator.validate_database_connection')
    def test_safe_database_operation_success(self, mock_validate):
        """Test successful safe database operation"""
        mock_validate.return_value = {'success': True}
        
        def test_operation(x, y):
            return x + y
        
        result = DatabaseConnectionValidator.safe_database_operation(test_operation, 2, 3)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 5)
    
    @patch('challenges.validators.DatabaseConnectionValidator.validate_database_connection')
    def test_safe_database_operation_connection_failure(self, mock_validate):
        """Test safe database operation with connection failure"""
        mock_validate.side_effect = DatabaseConnectionError('Connection failed')
        
        def test_operation():
            return 'success'
        
        result = DatabaseConnectionValidator.safe_database_operation(test_operation)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'database_connection')
        self.assertIn('unavailable', result['message'])
    
    @patch('challenges.validators.DatabaseConnectionValidator.validate_database_connection')
    def test_safe_database_operation_database_error(self, mock_validate):
        """Test safe database operation with database error"""
        mock_validate.return_value = {'success': True}
        
        def test_operation():
            raise DatabaseError('Database operation failed')
        
        result = DatabaseConnectionValidator.safe_database_operation(test_operation)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'database_operation')
        self.assertIn('rolled back', result['message'])


class ErrorMessageGeneratorTests(TestCase):
    """Test error message generation"""
    
    def test_access_denied_message_not_authenticated(self):
        """Test access denied message for unauthenticated user"""
        message = ErrorMessageGenerator.get_access_denied_message('not_authenticated')
        
        self.assertIn('log in', message)
    
    def test_access_denied_message_not_in_team(self):
        """Test access denied message for user not in team"""
        message = ErrorMessageGenerator.get_access_denied_message('not_in_team')
        
        self.assertIn('must be in a team', message)
    
    def test_access_denied_message_with_context(self):
        """Test access denied message with context"""
        context = {'team_name': 'Test Team'}
        message = ErrorMessageGenerator.get_access_denied_message('team_not_active', context)
        
        self.assertIn('Test Team', message)
        self.assertIn('not active', message)
    
    def test_validation_error_message_single_error(self):
        """Test validation error message with single error"""
        errors = ['This is a validation error']
        message = ErrorMessageGenerator.get_validation_error_message(errors)
        
        self.assertEqual(message, 'This is a validation error')
    
    def test_validation_error_message_multiple_errors(self):
        """Test validation error message with multiple errors"""
        errors = ['Error 1', 'Error 2', 'Error 3']
        message = ErrorMessageGenerator.get_validation_error_message(errors)
        
        self.assertIn('Multiple validation errors', message)
        self.assertIn('Error 1', message)
        self.assertIn('Error 2', message)
        self.assertIn('Error 3', message)
    
    def test_database_error_message_connection(self):
        """Test database error message for connection error"""
        message = ErrorMessageGenerator.get_database_error_message('connection')
        
        self.assertIn('connect to the database', message)
    
    def test_database_error_message_unknown(self):
        """Test database error message for unknown error"""
        message = ErrorMessageGenerator.get_database_error_message('unknown')
        
        self.assertIn('database error occurred', message)


class GroupChallengeManagerErrorHandlingTests(TestCase):
    """Test error handling in GroupChallengeManager"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            is_staff=True
        )
        self.captain = User.objects.create_user(
            username='captain',
            email='captain@test.com',
            password='testpass123'
        )
        
        self.team = Team.objects.create(
            name='Test Team',
            captain=self.captain,
            description='Test team description'
        )
        
        # Add members to team
        TeamMembership.objects.create(
            team=self.team,
            user=self.captain,
            status='accepted'
        )
        TeamMembership.objects.create(
            team=self.team,
            user=self.user,
            status='accepted'
        )
        
        self.event = GroupEvent.objects.create(
            name='Test Event',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            created_by=self.user,
            is_active=True
        )
        
        self.challenge = GroupChallenge.objects.create(
            event=self.event,
            title='Test Challenge',
            description='Test challenge description',
            points=100,
            flag='sha256:' + 'test_flag',
            category='web',
            difficulty='easy'
        )
    
    def test_activate_event_validation_error(self):
        """Test event activation with validation error"""
        # Try to activate event without staff permissions
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(GroupEventValidationError):
            GroupChallengeManager.activate_event(self.event, regular_user)
    
    def test_deactivate_event_validation_error(self):
        """Test event deactivation with validation error"""
        # Try to deactivate inactive event
        self.event.is_active = False
        self.event.save()
        
        with self.assertRaises(GroupEventValidationError):
            GroupChallengeManager.deactivate_event(self.event, self.user)
    
    @patch('challenges.validators.DatabaseConnectionValidator.validate_database_connection')
    def test_activate_event_database_error(self, mock_validate):
        """Test event activation with database error"""
        mock_validate.side_effect = DatabaseConnectionError('Database unavailable')
        
        with self.assertRaises(DatabaseConnectionError):
            GroupChallengeManager.activate_event(self.event, self.user)
    
    def test_submit_solution_team_membership_error(self):
        """Test solution submission with team membership error"""
        # Create user not in team
        non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@test.com',
            password='testpass123'
        )
        
        # Set up group mode
        PlatformMode.objects.create(
            mode='group',
            active_event=self.event,
            changed_by=self.user
        )
        
        with self.assertRaises(TeamMembershipValidationError):
            GroupChallengeManager.submit_solution(self.team, self.challenge, non_member, 'test_flag')
    
    def test_submit_solution_access_denied_empty_flag(self):
        """Test solution submission with empty flag"""
        # Set up group mode
        PlatformMode.objects.create(
            mode='group',
            active_event=self.event,
            changed_by=self.user
        )
        
        with self.assertRaises(AccessDeniedError):
            GroupChallengeManager.submit_solution(self.team, self.challenge, self.user, '')
    
    @patch('challenges.validators.DatabaseConnectionValidator.validate_database_connection')
    def test_submit_solution_database_error(self, mock_validate):
        """Test solution submission with database error"""
        mock_validate.side_effect = DatabaseConnectionError('Database unavailable')
        
        with self.assertRaises(DatabaseConnectionError):
            GroupChallengeManager.submit_solution(self.team, self.challenge, self.user, 'test_flag')


class ErrorHandlerTests(TestCase):
    """Test ErrorHandler utility methods"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_handle_validation_error_json_request(self):
        """Test validation error handling for JSON request"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/test/', content_type='application/json')
        
        error = ValidationError(['Test validation error'])
        response = ErrorHandler.handle_validation_error(request, error)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('validation_error', response.content.decode())
    
    def test_handle_access_denied_json_request(self):
        """Test access denied handling for JSON request"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/test/', content_type='application/json')
        
        response = ErrorHandler.handle_access_denied(request, 'not_authenticated')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn('access_denied', response.content.decode())
    
    def test_handle_database_error_json_request(self):
        """Test database error handling for JSON request"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/test/', content_type='application/json')
        
        error = DatabaseError('Test database error')
        response = ErrorHandler.handle_database_error(request, error)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('database_error', response.content.decode())


if __name__ == '__main__':
    pytest.main([__file__])