"""
Validation utilities for group event management system
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction, DatabaseError
from .models import GroupEvent, GroupChallenge, PlatformMode
from teams.models import Team, TeamMembership
import logging

logger = logging.getLogger(__name__)


class GroupEventValidationError(ValidationError):
    """Custom exception for group event validation errors"""
    pass


class TeamMembershipValidationError(ValidationError):
    """Custom exception for team membership validation errors"""
    pass


class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass


class AccessDeniedError(Exception):
    """Custom exception for access denied scenarios"""
    pass


class GroupEventValidator:
    """Validator for group event creation and management"""
    
    @staticmethod
    def validate_event_creation(name, description, start_time, end_time, created_by, point_multiplier=1.0, max_teams=None):
        """
        Validate group event creation parameters
        
        Args:
            name: Event name
            description: Event description
            start_time: Event start datetime
            end_time: Event end datetime
            created_by: User creating the event
            point_multiplier: Point multiplier for the event
            max_teams: Maximum number of teams allowed
        
        Returns:
            dict: Validation result with success status and messages
        
        Raises:
            GroupEventValidationError: If validation fails
        """
        errors = []
        
        # Validate required fields
        if not name or not name.strip():
            errors.append("Event name is required and cannot be empty")
        
        if not description or not description.strip():
            errors.append("Event description is required and cannot be empty")
        
        if not start_time:
            errors.append("Event start time is required")
        
        if not end_time:
            errors.append("Event end time is required")
        
        if not created_by or not isinstance(created_by, User):
            errors.append("Valid user is required to create event")
        
        # Validate name uniqueness
        if name and GroupEvent.objects.filter(name=name.strip()).exists():
            errors.append(f"Event with name '{name.strip()}' already exists")
        
        # Validate time ranges
        if start_time and end_time:
            if start_time >= end_time:
                errors.append("Event start time must be before end time")
            
            # Check minimum event duration (at least 1 hour)
            duration = end_time - start_time
            if duration.total_seconds() < 3600:  # 1 hour
                errors.append("Event must be at least 1 hour long")
            
            # Check if start time is not too far in the past
            current_time = timezone.now()
            if start_time < current_time - timezone.timedelta(hours=1):
                errors.append("Event start time cannot be more than 1 hour in the past")
        
        # Validate point multiplier
        if point_multiplier is not None:
            if not isinstance(point_multiplier, (int, float)) or point_multiplier <= 0:
                errors.append("Point multiplier must be a positive number")
            if point_multiplier > 10.0:
                errors.append("Point multiplier cannot exceed 10.0")
        
        # Validate max teams
        if max_teams is not None:
            if not isinstance(max_teams, int) or max_teams <= 0:
                errors.append("Maximum teams must be a positive integer")
            if max_teams > 1000:
                errors.append("Maximum teams cannot exceed 1000")
        
        # Check for overlapping events
        if start_time and end_time:
            overlapping_events = GroupEvent.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            if overlapping_events.exists():
                overlapping_names = [event.name for event in overlapping_events]
                errors.append(f"Event time range overlaps with existing events: {', '.join(overlapping_names)}")
        
        if errors:
            raise GroupEventValidationError(errors)
        
        return {
            'success': True,
            'message': 'Event validation passed',
            'validated_data': {
                'name': name.strip(),
                'description': description.strip(),
                'start_time': start_time,
                'end_time': end_time,
                'created_by': created_by,
                'point_multiplier': point_multiplier or 1.0,
                'max_teams': max_teams
            }
        }
    
    @staticmethod
    def validate_event_activation(event, user):
        """
        Validate event activation
        
        Args:
            event: GroupEvent instance to activate
            user: User attempting to activate the event
        
        Returns:
            dict: Validation result
        
        Raises:
            GroupEventValidationError: If validation fails
        """
        errors = []
        
        if not event:
            errors.append("Event is required for activation")
        
        if not user or not isinstance(user, User):
            errors.append("Valid user is required for event activation")
        
        if event:
            # Check if user has permission to activate events
            if not user.is_staff and not user.is_superuser:
                errors.append("Only staff members can activate group events")
            
            # Check if event is already active
            if event.is_active:
                errors.append(f"Event '{event.name}' is already active")
            
            # Check time constraints
            current_time = timezone.now()
            if current_time > event.end_time:
                errors.append(f"Cannot activate past event '{event.name}' (ended {event.end_time})")
            
            # Check for other active events
            other_active_events = GroupEvent.objects.filter(is_active=True).exclude(pk=event.pk)
            if other_active_events.exists():
                active_names = [e.name for e in other_active_events]
                errors.append(f"Cannot activate event while other events are active: {', '.join(active_names)}")
            
            # Check if event has challenges
            challenge_count = GroupChallenge.objects.filter(event=event).count()
            if challenge_count == 0:
                errors.append(f"Event '{event.name}' has no challenges and cannot be activated")
        
        if errors:
            raise GroupEventValidationError(errors)
        
        return {
            'success': True,
            'message': f"Event '{event.name}' can be activated",
            'event': event
        }
    
    @staticmethod
    def validate_event_deactivation(event, user):
        """
        Validate event deactivation
        
        Args:
            event: GroupEvent instance to deactivate
            user: User attempting to deactivate the event
        
        Returns:
            dict: Validation result
        
        Raises:
            GroupEventValidationError: If validation fails
        """
        errors = []
        
        if not event:
            errors.append("Event is required for deactivation")
        
        if not user or not isinstance(user, User):
            errors.append("Valid user is required for event deactivation")
        
        if event:
            # Check if user has permission to deactivate events
            if not user.is_staff and not user.is_superuser:
                errors.append("Only staff members can deactivate group events")
            
            # Check if event is already inactive
            if not event.is_active:
                errors.append(f"Event '{event.name}' is already inactive")
        
        if errors:
            raise GroupEventValidationError(errors)
        
        return {
            'success': True,
            'message': f"Event '{event.name}' can be deactivated",
            'event': event
        }


class TeamMembershipValidator:
    """Validator for team membership operations"""
    
    @staticmethod
    def validate_team_access(user, team=None):
        """
        Validate if user can access team-related features
        
        Args:
            user: User to validate
            team: Optional specific team to check access for
        
        Returns:
            dict: Validation result
        
        Raises:
            TeamMembershipValidationError: If validation fails
        """
        errors = []
        
        if not user or not user.is_authenticated:
            errors.append("User must be authenticated to access team features")
        
        if user and user.is_authenticated:
            # Check if user is in a team
            try:
                membership = TeamMembership.objects.get(user=user, status='accepted')
                user_team = membership.team
                
                # If specific team is provided, check if user is member
                if team and user_team != team:
                    errors.append(f"User is not a member of team '{team.name}'")
                
            except TeamMembership.DoesNotExist:
                errors.append("User must be in a team to access team features")
        
        if errors:
            raise TeamMembershipValidationError(errors)
        
        return {
            'success': True,
            'message': 'Team access validation passed',
            'user_team': TeamMembershipValidator.get_user_team(user) if user.is_authenticated else None
        }
    
    @staticmethod
    def validate_group_challenge_access(user):
        """
        Validate if user can access group challenges
        
        Args:
            user: User to validate
        
        Returns:
            dict: Validation result
        
        Raises:
            AccessDeniedError: If access is denied
        """
        errors = []
        
        if not user or not user.is_authenticated:
            errors.append("Authentication required to access group challenges")
        
        if user and user.is_authenticated:
            # Check if group mode is active
            try:
                platform_mode = PlatformMode.objects.get(mode='group')
                if not platform_mode.active_event:
                    errors.append("No group competition is currently active")
            except PlatformMode.DoesNotExist:
                errors.append("Platform is not in group mode")
            
            # Check if user is in an accepted team
            try:
                membership = TeamMembership.objects.get(user=user, status='accepted')
                team = membership.team
                
                # Check if team is active
                if not team.is_active:
                    errors.append(f"Your team '{team.name}' is not active")
                
                # Check if team meets minimum requirements
                if not team.can_compete():
                    errors.append(f"Your team '{team.name}' needs at least 2 members to compete")
                
            except TeamMembership.DoesNotExist:
                errors.append("You must be in a team to access group challenges")
        
        if errors:
            raise AccessDeniedError(errors)
        
        return {
            'success': True,
            'message': 'Group challenge access granted',
            'user_team': TeamMembershipValidator.get_user_team(user)
        }
    
    @staticmethod
    def get_user_team(user):
        """
        Get user's current team
        
        Args:
            user: User to get team for
        
        Returns:
            Team instance or None
        """
        try:
            membership = TeamMembership.objects.get(user=user, status='accepted')
            return membership.team
        except TeamMembership.DoesNotExist:
            return None
    
    @staticmethod
    def validate_team_captain_permissions(user, team):
        """
        Validate if user has captain permissions for a team
        
        Args:
            user: User to validate
            team: Team to check captain permissions for
        
        Returns:
            dict: Validation result
        
        Raises:
            AccessDeniedError: If access is denied
        """
        errors = []
        
        if not user or not user.is_authenticated:
            errors.append("Authentication required for team management")
        
        if not team:
            errors.append("Team is required for permission validation")
        
        if user and team:
            if team.captain != user:
                errors.append(f"Only team captain can perform this action on team '{team.name}'")
            
            if not team.is_active:
                errors.append(f"Team '{team.name}' is not active")
        
        if errors:
            raise AccessDeniedError(errors)
        
        return {
            'success': True,
            'message': f'Captain permissions validated for team {team.name}',
            'team': team
        }


class DatabaseConnectionValidator:
    """Validator for database connection and transaction handling"""
    
    @staticmethod
    def validate_database_connection():
        """
        Validate database connection is available
        
        Returns:
            dict: Validation result
        
        Raises:
            DatabaseConnectionError: If database is not accessible
        """
        try:
            # Test database connection with a simple query
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                'success': True,
                'message': 'Database connection is healthy'
            }
        
        except DatabaseError as e:
            logger.error(f"Database connection error: {str(e)}")
            raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise DatabaseConnectionError(f"Unexpected database error: {str(e)}")
    
    @staticmethod
    def safe_database_operation(operation_func, *args, **kwargs):
        """
        Execute database operation with error handling and rollback
        
        Args:
            operation_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            dict: Operation result
        """
        try:
            # Validate database connection first
            DatabaseConnectionValidator.validate_database_connection()
            
            # Execute operation in transaction
            with transaction.atomic():
                result = operation_func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'message': 'Database operation completed successfully'
                }
        
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error during operation: {str(e)}")
            return {
                'success': False,
                'error': 'database_connection',
                'message': 'Database connection is currently unavailable. Please try again later.',
                'technical_details': str(e)
            }
        
        except DatabaseError as e:
            logger.error(f"Database error during operation: {str(e)}")
            return {
                'success': False,
                'error': 'database_operation',
                'message': 'A database error occurred. The operation has been rolled back.',
                'technical_details': str(e)
            }
        
        except Exception as e:
            logger.error(f"Unexpected error during database operation: {str(e)}")
            return {
                'success': False,
                'error': 'unexpected',
                'message': 'An unexpected error occurred. Please contact support if this persists.',
                'technical_details': str(e)
            }


class ErrorMessageGenerator:
    """Generate user-friendly error messages for different scenarios"""
    
    @staticmethod
    def get_access_denied_message(error_type, context=None):
        """
        Generate user-friendly access denied messages
        
        Args:
            error_type: Type of access denial
            context: Additional context for the error
        
        Returns:
            str: User-friendly error message
        """
        messages = {
            'not_authenticated': 'Please log in to access this feature.',
            'not_in_team': 'You must be in a team to access group challenges. Join or create a team first.',
            'team_not_active': 'Your team is not active. Please contact your team captain.',
            'not_captain': 'Only team captains can perform this action.',
            'group_mode_inactive': 'No group competition is currently active. Group challenges are not available.',
            'team_too_small': 'Your team needs at least 2 members to participate in group competitions.',
            'team_full': 'This team is full and cannot accept new members.',
            'already_in_team': 'You are already in a team. Leave your current team before joining another.',
            'event_not_found': 'The requested group event was not found or is no longer available.',
            'challenge_not_found': 'The requested challenge was not found or is not available.',
            'insufficient_permissions': 'You do not have permission to perform this action.',
            'database_unavailable': 'The system is temporarily unavailable. Please try again in a few moments.',
            'invalid_request': 'The request is invalid or malformed. Please check your input and try again.'
        }
        
        base_message = messages.get(error_type, 'Access denied. Please contact support if you believe this is an error.')
        
        if context:
            if error_type == 'team_not_active' and 'team_name' in context:
                return f"Team '{context['team_name']}' is not active. Please contact your team captain."
            elif error_type == 'not_captain' and 'team_name' in context:
                return f"Only the captain of team '{context['team_name']}' can perform this action."
            elif error_type == 'team_full' and 'team_name' in context:
                return f"Team '{context['team_name']}' is full and cannot accept new members."
        
        return base_message
    
    @staticmethod
    def get_validation_error_message(validation_errors):
        """
        Generate user-friendly validation error messages
        
        Args:
            validation_errors: List of validation error messages
        
        Returns:
            str: Formatted error message
        """
        if not validation_errors:
            return "Validation failed."
        
        if len(validation_errors) == 1:
            return validation_errors[0]
        
        return "Multiple validation errors occurred:\n• " + "\n• ".join(validation_errors)
    
    @staticmethod
    def get_database_error_message(error_type):
        """
        Generate user-friendly database error messages
        
        Args:
            error_type: Type of database error
        
        Returns:
            str: User-friendly error message
        """
        messages = {
            'connection': 'Unable to connect to the database. Please try again in a few moments.',
            'timeout': 'The operation timed out. Please try again with a smaller request.',
            'constraint': 'The operation violates data constraints. Please check your input.',
            'integrity': 'Data integrity error. The operation cannot be completed.',
            'permission': 'Database permission error. Please contact support.',
            'unknown': 'A database error occurred. Please contact support if this persists.'
        }
        
        return messages.get(error_type, messages['unknown'])