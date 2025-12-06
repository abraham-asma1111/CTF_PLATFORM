"""
Error handling utilities and decorators for group event management
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from .validators import (
    GroupEventValidationError, 
    TeamMembershipValidationError, 
    DatabaseConnectionError, 
    AccessDeniedError,
    ErrorMessageGenerator,
    TeamMembershipValidator,
    DatabaseConnectionValidator
)
import logging

logger = logging.getLogger(__name__)


def handle_group_event_errors(view_func):
    """
    Decorator to handle group event related errors
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        
        except GroupEventValidationError as e:
            error_message = ErrorMessageGenerator.get_validation_error_message(e.messages)
            logger.warning(f"Group event validation error: {error_message}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'validation_error',
                    'message': error_message,
                    'details': e.messages
                }, status=400)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
        
        except AccessDeniedError as e:
            error_message = ErrorMessageGenerator.get_access_denied_message('insufficient_permissions')
            if hasattr(e, 'messages') and e.messages:
                error_message = ErrorMessageGenerator.get_validation_error_message(e.messages)
            
            logger.warning(f"Access denied in group event operation: {error_message}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'access_denied',
                    'message': error_message
                }, status=403)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
        
        except DatabaseConnectionError as e:
            error_message = ErrorMessageGenerator.get_database_error_message('connection')
            logger.error(f"Database connection error in group event operation: {str(e)}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'database_error',
                    'message': error_message
                }, status=503)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
        
        except Exception as e:
            error_message = "An unexpected error occurred. Please try again or contact support."
            logger.error(f"Unexpected error in group event operation: {str(e)}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'unexpected_error',
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
    
    return wrapper


def require_team_membership(view_func):
    """
    Decorator to require team membership for accessing views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # Validate team access
            validation_result = TeamMembershipValidator.validate_team_access(request.user)
            
            # Add team to request for convenience
            request.user_team = validation_result.get('user_team')
            
            return view_func(request, *args, **kwargs)
        
        except TeamMembershipValidationError as e:
            error_message = ErrorMessageGenerator.get_validation_error_message(e.messages)
            logger.warning(f"Team membership validation error: {error_message}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'team_membership_required',
                    'message': error_message
                }, status=403)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
    
    return wrapper


def require_group_challenge_access(view_func):
    """
    Decorator to require group challenge access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # Validate group challenge access
            validation_result = TeamMembershipValidator.validate_group_challenge_access(request.user)
            
            # Add team to request for convenience
            request.user_team = validation_result.get('user_team')
            
            return view_func(request, *args, **kwargs)
        
        except AccessDeniedError as e:
            error_message = ErrorMessageGenerator.get_validation_error_message(e.args)
            logger.warning(f"Group challenge access denied: {error_message}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'group_challenge_access_denied',
                    'message': error_message
                }, status=403)
            else:
                messages.error(request, error_message)
                return redirect('teams:my_team')
    
    return wrapper


def require_team_captain(view_func):
    """
    Decorator to require team captain permissions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # Get team from URL parameter or user's team
            team_id = kwargs.get('team_id')
            if team_id:
                from teams.models import Team
                team = Team.objects.get(id=team_id, is_active=True)
            else:
                team = TeamMembershipValidator.get_user_team(request.user)
            
            # Validate captain permissions
            TeamMembershipValidator.validate_team_captain_permissions(request.user, team)
            
            # Add team to request for convenience
            request.user_team = team
            
            return view_func(request, *args, **kwargs)
        
        except AccessDeniedError as e:
            error_message = ErrorMessageGenerator.get_validation_error_message(e.args)
            logger.warning(f"Team captain access denied: {error_message}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'captain_permissions_required',
                    'message': error_message
                }, status=403)
            else:
                messages.error(request, error_message)
                return redirect('teams:my_team')
        
        except Exception as e:
            error_message = "Unable to verify team captain permissions."
            logger.error(f"Error validating team captain permissions: {str(e)}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'permission_validation_error',
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
    
    return wrapper


def safe_database_operation(view_func):
    """
    Decorator to handle database operations safely with error handling
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # Validate database connection
            DatabaseConnectionValidator.validate_database_connection()
            
            return view_func(request, *args, **kwargs)
        
        except DatabaseConnectionError as e:
            error_message = ErrorMessageGenerator.get_database_error_message('connection')
            logger.error(f"Database connection error: {str(e)}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'database_unavailable',
                    'message': error_message
                }, status=503)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
        
        except DatabaseError as e:
            error_message = ErrorMessageGenerator.get_database_error_message('unknown')
            logger.error(f"Database error: {str(e)}")
            
            if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'database_error',
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect('teams:team_list')
    
    return wrapper


class ErrorHandler:
    """Centralized error handling utilities"""
    
    @staticmethod
    def handle_validation_error(request, error, redirect_url='teams:team_list'):
        """
        Handle validation errors consistently
        
        Args:
            request: Django request object
            error: ValidationError or similar exception
            redirect_url: URL to redirect to for non-AJAX requests
        
        Returns:
            JsonResponse or redirect
        """
        if hasattr(error, 'messages'):
            error_message = ErrorMessageGenerator.get_validation_error_message(error.messages)
        else:
            error_message = str(error)
        
        logger.warning(f"Validation error: {error_message}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'validation_error',
                'message': error_message
            }, status=400)
        else:
            messages.error(request, error_message)
            return redirect(redirect_url)
    
    @staticmethod
    def handle_access_denied(request, error_type, context=None, redirect_url='teams:team_list'):
        """
        Handle access denied errors consistently
        
        Args:
            request: Django request object
            error_type: Type of access denial
            context: Additional context for the error
            redirect_url: URL to redirect to for non-AJAX requests
        
        Returns:
            JsonResponse or redirect
        """
        error_message = ErrorMessageGenerator.get_access_denied_message(error_type, context)
        logger.warning(f"Access denied ({error_type}): {error_message}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'access_denied',
                'message': error_message
            }, status=403)
        else:
            messages.error(request, error_message)
            return redirect(redirect_url)
    
    @staticmethod
    def handle_database_error(request, error, redirect_url='teams:team_list'):
        """
        Handle database errors consistently
        
        Args:
            request: Django request object
            error: Database error exception
            redirect_url: URL to redirect to for non-AJAX requests
        
        Returns:
            JsonResponse or redirect
        """
        error_message = ErrorMessageGenerator.get_database_error_message('unknown')
        logger.error(f"Database error: {str(error)}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'database_error',
                'message': error_message
            }, status=500)
        else:
            messages.error(request, error_message)
            return redirect(redirect_url)
    
    @staticmethod
    def handle_unexpected_error(request, error, redirect_url='teams:team_list'):
        """
        Handle unexpected errors consistently
        
        Args:
            request: Django request object
            error: Unexpected error exception
            redirect_url: URL to redirect to for non-AJAX requests
        
        Returns:
            JsonResponse or redirect
        """
        error_message = "An unexpected error occurred. Please try again or contact support."
        logger.error(f"Unexpected error: {str(error)}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'unexpected_error',
                'message': error_message
            }, status=500)
        else:
            messages.error(request, error_message)
            return redirect(redirect_url)


def graceful_database_fallback(fallback_func):
    """
    Decorator to provide graceful fallback when database is unavailable
    
    Args:
        fallback_func: Function to call when database is unavailable
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Try to validate database connection
                DatabaseConnectionValidator.validate_database_connection()
                return view_func(request, *args, **kwargs)
            
            except DatabaseConnectionError:
                # Database is unavailable, use fallback
                logger.warning("Database unavailable, using fallback function")
                return fallback_func(request, *args, **kwargs)
        
        return wrapper
    return decorator