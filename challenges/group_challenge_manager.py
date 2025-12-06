"""
Group Challenge Manager for handling group challenge operations
"""
from django.db import models, DatabaseError, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import GroupChallenge, GroupSubmission, GroupEvent, PlatformMode
from teams.models import Team, TeamMembership
from .validators import (
    GroupEventValidator, 
    TeamMembershipValidator, 
    DatabaseConnectionValidator,
    GroupEventValidationError,
    TeamMembershipValidationError,
    DatabaseConnectionError,
    AccessDeniedError
)
import hashlib
import logging

logger = logging.getLogger(__name__)


class GroupChallengeManager:
    """Manager for group challenge operations in team section"""
    
    @staticmethod
    def get_active_group_event():
        """Get the currently active group event"""
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            return platform_mode.active_event
        except PlatformMode.DoesNotExist:
            return None
    
    @staticmethod
    def is_group_mode_active():
        """Check if group mode is currently active"""
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            return platform_mode.active_event is not None
        except PlatformMode.DoesNotExist:
            return False
    
    @staticmethod
    def get_team_challenges(team):
        """Get all group challenges for a team during active group event"""
        active_event = GroupChallengeManager.get_active_group_event()
        if not active_event:
            return GroupChallenge.objects.none()
        
        return GroupChallenge.objects.filter(event=active_event).order_by('difficulty', 'points')
    
    @staticmethod
    def get_team_submissions(team):
        """Get all submissions for a team during active group event"""
        active_event = GroupChallengeManager.get_active_group_event()
        if not active_event:
            return GroupSubmission.objects.none()
        
        return GroupSubmission.objects.filter(
            team=team,
            challenge__event=active_event
        ).select_related('challenge', 'submitted_by').order_by('-submitted_at')
    
    @staticmethod
    def get_team_solved_challenges(team):
        """Get challenges solved by the team"""
        return GroupChallengeManager.get_team_submissions(team).filter(is_correct=True)
    
    @staticmethod
    def can_user_access_group_challenges(user):
        """Check if user can access group challenges (must be in a team and group mode active)"""
        if not user.is_authenticated:
            return False
        
        # Check if group mode is active
        if not GroupChallengeManager.is_group_mode_active():
            return False
        
        # Check if user is in an accepted team
        return TeamMembership.objects.filter(
            user=user,
            status='accepted'
        ).exists()
    
    @staticmethod
    def get_user_team(user):
        """Get the user's current team"""
        try:
            membership = TeamMembership.objects.get(user=user, status='accepted')
            return membership.team
        except TeamMembership.DoesNotExist:
            return None
    
    @staticmethod
    def submit_solution(team, challenge, user, flag_submitted):
        """
        Submit a solution for a group challenge with comprehensive validation
        
        Args:
            team: Team submitting the solution
            challenge: GroupChallenge instance
            user: User submitting the solution
            flag_submitted: Submitted flag string
        
        Returns:
            dict: Submission result
        
        Raises:
            TeamMembershipValidationError: If team membership is invalid
            AccessDeniedError: If access is denied
            DatabaseConnectionError: If database is unavailable
        """
        try:
            # Validate database connection first
            DatabaseConnectionValidator.validate_database_connection()
            
            # Validate team membership
            TeamMembershipValidator.validate_team_access(user, team)
            
            # Validate group challenge access
            TeamMembershipValidator.validate_group_challenge_access(user)
            
            # Validate input
            if not flag_submitted or not flag_submitted.strip():
                raise AccessDeniedError(['Flag cannot be empty'])
            
            # Perform submission in transaction
            with transaction.atomic():
                # Check if team has exceeded max attempts
                attempt_count = GroupSubmission.objects.filter(
                    team=team,
                    challenge=challenge
                ).count()
                
                if attempt_count >= challenge.max_attempts_per_team:
                    return {
                        'success': False,
                        'message': f'Maximum attempts ({challenge.max_attempts_per_team}) exceeded for this challenge'
                    }
                
                # Check if challenge is already solved by this team
                existing_correct = GroupSubmission.objects.filter(
                    team=team,
                    challenge=challenge,
                    is_correct=True
                ).exists()
                
                if existing_correct:
                    return {
                        'success': False,
                        'message': 'Challenge already solved by your team'
                    }
                
                # Check flag
                is_correct = GroupChallengeManager._check_flag(challenge.flag, flag_submitted.strip())
                points_awarded = 0
                
                if is_correct:
                    # Calculate points (could include event multiplier)
                    points_awarded = int(challenge.points * challenge.event.point_multiplier)
                
                # Create submission
                submission = GroupSubmission.objects.create(
                    challenge=challenge,
                    team=team,
                    submitted_by=user,
                    flag_submitted=flag_submitted.strip(),
                    is_correct=is_correct,
                    points_awarded=points_awarded
                )
                
                # Update team score if correct using GroupScoring
                if is_correct:
                    GroupScoring.update_team_score(team, points_awarded)
                
                logger.info(f'Team {team.name} submitted solution for challenge {challenge.title}: {"correct" if is_correct else "incorrect"}')
                
                return {
                    'success': True,
                    'is_correct': is_correct,
                    'points_awarded': points_awarded,
                    'message': 'Correct! Well done!' if is_correct else 'Incorrect flag. Try again!',
                    'submission': submission
                }
        
        except TeamMembershipValidationError as e:
            logger.warning(f'Team membership validation failed for submission: {e.messages}')
            raise
        
        except AccessDeniedError as e:
            logger.warning(f'Access denied for group challenge submission: {e.args}')
            raise
        
        except DatabaseConnectionError as e:
            logger.error(f'Database connection error during submission: {str(e)}')
            raise
        
        except DatabaseError as e:
            logger.error(f'Database error during submission: {str(e)}')
            raise DatabaseConnectionError(f'Database operation failed: {str(e)}')
        
        except Exception as e:
            logger.error(f'Unexpected error during submission: {str(e)}')
            raise AccessDeniedError([f'Unexpected error during submission: {str(e)}'])
    
    @staticmethod
    def _check_flag(stored_flag, submitted_flag):
        """Check if submitted flag matches stored flag"""
        # Hash the submitted flag and compare
        hashed_submitted = 'sha256:' + hashlib.sha256(submitted_flag.encode()).hexdigest()
        return hashed_submitted == stored_flag
    
    @staticmethod
    def get_team_leaderboard():
        """Get team leaderboard for active group event"""
        return GroupScoring.get_group_leaderboard()
    
    @staticmethod
    def get_challenge_stats(challenge):
        """Get statistics for a specific challenge"""
        total_teams = Team.objects.filter(
            groupsubmission__challenge=challenge
        ).distinct().count()
        
        solved_teams = Team.objects.filter(
            groupsubmission__challenge=challenge,
            groupsubmission__is_correct=True
        ).distinct().count()
        
        total_attempts = GroupSubmission.objects.filter(challenge=challenge).count()
        
        return {
            'total_teams': total_teams,
            'solved_teams': solved_teams,
            'total_attempts': total_attempts,
            'solve_rate': (solved_teams / total_teams * 100) if total_teams > 0 else 0
        }
    
    @staticmethod
    def get_group_event_info(event):
        """Get information about a group event for display"""
        if not event:
            return None
        
        total_challenges = GroupChallenge.objects.filter(event=event).count()
        total_teams = Team.objects.filter(
            groupsubmission__challenge__event=event
        ).distinct().count()
        
        return {
            'name': event.name,
            'description': event.description,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'total_challenges': total_challenges,
            'total_teams': total_teams,
            'point_multiplier': event.point_multiplier,
            'max_teams': event.max_teams,
            'is_active': event.is_active
        }
    
    @staticmethod
    def activate_event(event, user):
        """
        Manually activate a group event with comprehensive validation
        
        Args:
            event: GroupEvent instance to activate
            user: User who is activating the event
        
        Returns:
            dict: Result of activation
        
        Raises:
            GroupEventValidationError: If validation fails
            DatabaseConnectionError: If database is unavailable
        """
        try:
            # Validate database connection first
            DatabaseConnectionValidator.validate_database_connection()
            
            # Validate event activation
            GroupEventValidator.validate_event_activation(event, user)
            
            # Perform activation in transaction
            with transaction.atomic():
                # Deactivate other events first
                GroupEvent.objects.exclude(pk=event.pk).update(is_active=False)
                
                # Activate the event
                event.is_active = True
                event.save()
                
                # Set platform mode
                platform_mode, created = PlatformMode.objects.get_or_create(
                    mode='group',
                    defaults={
                        'active_event': event,
                        'changed_by': user
                    }
                )
                
                if not created:
                    platform_mode.active_event = event
                    platform_mode.changed_by = user
                    platform_mode.save()
                
                logger.info(f'Event "{event.name}" activated successfully by user {user.username}')
                
                return {
                    'success': True,
                    'message': f'Event "{event.name}" activated successfully',
                    'event': event,
                    'platform_mode': platform_mode
                }
            
        except GroupEventValidationError as e:
            logger.warning(f'Event activation validation failed: {e.messages}')
            raise
        
        except DatabaseConnectionError as e:
            logger.error(f'Database connection error during event activation: {str(e)}')
            raise
        
        except DatabaseError as e:
            logger.error(f'Database error during event activation: {str(e)}')
            raise DatabaseConnectionError(f'Database operation failed: {str(e)}')
        
        except Exception as e:
            logger.error(f'Unexpected error during event activation: {str(e)}')
            raise GroupEventValidationError([f'Unexpected error activating event: {str(e)}'])
    
    @staticmethod
    def deactivate_event(event, user):
        """
        Manually deactivate a group event with comprehensive validation
        
        Args:
            event: GroupEvent instance to deactivate
            user: User who is deactivating the event
        
        Returns:
            dict: Result of deactivation
        
        Raises:
            GroupEventValidationError: If validation fails
            DatabaseConnectionError: If database is unavailable
        """
        try:
            # Validate database connection first
            DatabaseConnectionValidator.validate_database_connection()
            
            # Validate event deactivation
            GroupEventValidator.validate_event_deactivation(event, user)
            
            # Perform deactivation in transaction
            with transaction.atomic():
                # Deactivate the event
                event.is_active = False
                event.save()
                
                # Update platform mode if this was the active event
                try:
                    platform_mode = PlatformMode.objects.get(mode='group')
                    if platform_mode.active_event == event:
                        platform_mode.active_event = None
                        platform_mode.changed_by = user
                        platform_mode.save()
                except PlatformMode.DoesNotExist:
                    pass
                
                logger.info(f'Event "{event.name}" deactivated successfully by user {user.username}')
                
                return {
                    'success': True,
                    'message': f'Event "{event.name}" deactivated successfully',
                    'event': event
                }
            
        except GroupEventValidationError as e:
            logger.warning(f'Event deactivation validation failed: {e.messages}')
            raise
        
        except DatabaseConnectionError as e:
            logger.error(f'Database connection error during event deactivation: {str(e)}')
            raise
        
        except DatabaseError as e:
            logger.error(f'Database error during event deactivation: {str(e)}')
            raise DatabaseConnectionError(f'Database operation failed: {str(e)}')
        
        except Exception as e:
            logger.error(f'Unexpected error during event deactivation: {str(e)}')
            raise GroupEventValidationError([f'Unexpected error deactivating event: {str(e)}'])
    
    @staticmethod
    def get_event_lifecycle_status(event):
        """
        Get detailed lifecycle status for an event
        
        Args:
            event: GroupEvent instance
        
        Returns:
            dict: Detailed status information
        """
        from django.utils import timezone
        
        current_time = timezone.now()
        
        # Determine event phase
        if current_time < event.start_time:
            phase = 'upcoming'
            time_until_start = event.start_time - current_time
            time_info = f"Starts in {time_until_start}"
        elif current_time > event.end_time:
            phase = 'ended'
            time_since_end = current_time - event.end_time
            time_info = f"Ended {time_since_end} ago"
        else:
            phase = 'active'
            time_until_end = event.end_time - current_time
            time_info = f"Ends in {time_until_end}"
        
        # Check if event should be active based on time
        should_be_active = event.start_time <= current_time <= event.end_time
        
        # Check platform mode status
        is_platform_active = False
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            is_platform_active = platform_mode.active_event == event
        except PlatformMode.DoesNotExist:
            pass
        
        return {
            'event_id': event.id,
            'event_name': event.name,
            'phase': phase,
            'time_info': time_info,
            'is_active': event.is_active,
            'should_be_active': should_be_active,
            'is_platform_active': is_platform_active,
            'status_consistent': event.is_active == should_be_active,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'current_time': current_time
        }


class GroupScoring:
    """Handles group-specific scoring calculations"""
    
    @staticmethod
    def calculate_team_points(team, challenge):
        """Calculate points for a team solving a challenge"""
        base_points = challenge.points
        event_multiplier = challenge.event.point_multiplier
        
        # Apply event multiplier
        final_points = int(base_points * event_multiplier)
        
        return final_points
    
    @staticmethod
    def get_team_event_score(team, event):
        """Get team's total score for a specific event"""
        return GroupSubmission.objects.filter(
            team=team,
            challenge__event=event,
            is_correct=True
        ).aggregate(
            total=models.Sum('points_awarded')
        )['total'] or 0
    
    @staticmethod
    def get_team_event_progress(team, event):
        """Get team's progress in an event"""
        total_challenges = GroupChallenge.objects.filter(event=event).count()
        solved_challenges = GroupSubmission.objects.filter(
            team=team,
            challenge__event=event,
            is_correct=True
        ).values('challenge').distinct().count()
        
        return {
            'total_challenges': total_challenges,
            'solved_challenges': solved_challenges,
            'progress_percentage': (solved_challenges / total_challenges * 100) if total_challenges > 0 else 0
        }
    
    @staticmethod
    def get_group_leaderboard(event=None):
        """Get team leaderboard for group events (separate from regular leaderboard)"""
        if event is None:
            event = GroupChallengeManager.get_active_group_event()
        
        if not event:
            return []
        
        # Get teams that have made submissions in the event
        teams_with_submissions = Team.objects.filter(
            groupsubmission__challenge__event=event
        ).distinct()
        
        # Calculate scores for each team in the event
        team_scores = []
        for team in teams_with_submissions:
            event_score = GroupSubmission.objects.filter(
                team=team,
                challenge__event=event,
                is_correct=True
            ).aggregate(
                total_points=models.Sum('points_awarded'),
                challenges_solved=models.Count('challenge', distinct=True)
            )
            
            last_submission = GroupSubmission.objects.filter(
                team=team,
                challenge__event=event
            ).order_by('-submitted_at').first()
            
            team_scores.append({
                'team': team,
                'event_score': event_score['total_points'] or 0,
                'event_challenges_solved': event_score['challenges_solved'] or 0,
                'last_submission': last_submission.submitted_at if last_submission else None
            })
        
        # Sort by event score, then by last submission time (earlier is better for ties)
        team_scores.sort(
            key=lambda x: (-x['event_score'], x['last_submission'] or timezone.now())
        )
        
        return team_scores
    
    @staticmethod
    def update_team_score(team, points_awarded):
        """Update team score for group challenges (separate from regular scoring)"""
        # This method updates team scores specifically for group events
        # It's separate from regular challenge scoring to maintain independence
        team.total_score += points_awarded
        team.challenges_solved += 1
        team.last_submission = timezone.now()
        team.save()
        
        return team
    
    @staticmethod
    def get_team_ranking(team, event=None):
        """Get team's ranking in group event leaderboard"""
        if event is None:
            event = GroupChallengeManager.get_active_group_event()
        
        if not event:
            return None
        
        leaderboard = GroupScoring.get_group_leaderboard(event)
        
        for rank, team_data in enumerate(leaderboard, 1):
            if team_data['team'].id == team.id:
                return {
                    'rank': rank,
                    'total_teams': len(leaderboard),
                    'score': team_data['event_score'],
                    'challenges_solved': team_data['event_challenges_solved']
                }
        
        return None
    
    @staticmethod
    def is_scoring_separated_from_regular():
        """Verify that group scoring is completely separate from regular scoring"""
        # This method helps verify scoring separation for testing
        # Group scoring uses GroupSubmission model with points_awarded field
        # Regular scoring uses Submission model without points_awarded field
        
        group_submission_fields = set(field.name for field in GroupSubmission._meta.fields)
        
        # Import here to avoid circular imports
        from submissions.models import Submission
        regular_submission_fields = set(field.name for field in Submission._meta.fields)
        
        # Group submissions should have points_awarded, regular submissions should not
        has_group_points = 'points_awarded' in group_submission_fields
        has_regular_points = 'points_awarded' in regular_submission_fields
        
        # Group submissions should be linked to teams and group challenges
        has_group_team = 'team' in group_submission_fields
        has_group_challenge = 'challenge' in group_submission_fields
        
        return {
            'group_has_points_awarded': has_group_points,
            'regular_has_points_awarded': has_regular_points,
            'group_has_team_link': has_group_team,
            'group_has_challenge_link': has_group_challenge,
            'scoring_separated': has_group_points and not has_regular_points
        }

class GroupEventLifecycleManager:
    """Handles automatic group event lifecycle management"""
    
    @staticmethod
    def check_and_update_event_status():
        """
        Check all group events and automatically activate/deactivate based on time
        Returns a list of events that had their status changed
        """
        from django.utils import timezone
        
        current_time = timezone.now()
        changed_events = []
        
        # Get all group events
        all_events = GroupEvent.objects.all()
        
        for event in all_events:
            old_status = event.is_active
            new_status = GroupEventLifecycleManager._should_event_be_active(event, current_time)
            
            if old_status != new_status:
                event.is_active = new_status
                event.save()
                
                # Update platform mode if this event should be active
                if new_status:
                    GroupEventLifecycleManager._activate_group_mode(event)
                else:
                    # Check if this was the active event and deactivate if so
                    try:
                        platform_mode = PlatformMode.objects.get(mode='group')
                        if platform_mode.active_event == event:
                            GroupEventLifecycleManager._deactivate_group_mode()
                    except PlatformMode.DoesNotExist:
                        pass
                
                changed_events.append({
                    'event': event,
                    'old_status': old_status,
                    'new_status': new_status,
                    'action': 'activated' if new_status else 'deactivated'
                })
        
        return changed_events
    
    @staticmethod
    def _should_event_be_active(event, current_time):
        """
        Determine if an event should be active based on its time range
        """
        return event.start_time <= current_time <= event.end_time
    
    @staticmethod
    def _activate_group_mode(event):
        """
        Activate group mode for a specific event
        """
        platform_mode, created = PlatformMode.objects.get_or_create(
            mode='group',
            defaults={
                'active_event': event,
                'changed_by': event.created_by
            }
        )
        
        if not created:
            platform_mode.active_event = event
            platform_mode.changed_by = event.created_by
            platform_mode.save()
        
        return platform_mode
    
    @staticmethod
    def _deactivate_group_mode():
        """
        Deactivate group mode (return to individual mode)
        """
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            platform_mode.active_event = None
            platform_mode.save()
            return True
        except PlatformMode.DoesNotExist:
            return False
    
    @staticmethod
    def get_event_status_summary():
        """
        Get a summary of all group events and their current status
        """
        from django.utils import timezone
        
        current_time = timezone.now()
        events = GroupEvent.objects.all().order_by('start_time')
        
        summary = {
            'current_time': current_time,
            'total_events': events.count(),
            'active_events': [],
            'upcoming_events': [],
            'past_events': [],
            'current_platform_mode': None
        }
        
        # Get current platform mode
        try:
            platform_mode = PlatformMode.objects.get(mode='group')
            summary['current_platform_mode'] = {
                'active_event': platform_mode.active_event,
                'changed_at': platform_mode.changed_at,
                'changed_by': platform_mode.changed_by
            }
        except PlatformMode.DoesNotExist:
            pass
        
        # Categorize events
        for event in events:
            event_info = {
                'id': event.id,
                'name': event.name,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'is_active': event.is_active,
                'should_be_active': GroupEventLifecycleManager._should_event_be_active(event, current_time)
            }
            
            if current_time < event.start_time:
                summary['upcoming_events'].append(event_info)
            elif current_time > event.end_time:
                summary['past_events'].append(event_info)
            else:
                summary['active_events'].append(event_info)
        
        return summary
    
    @staticmethod
    def cleanup_expired_events(preserve_data=True):
        """
        Clean up expired events while preserving data
        
        Args:
            preserve_data (bool): If True, preserve all event data. If False, remove expired events.
        
        Returns:
            dict: Summary of cleanup actions
        """
        from django.utils import timezone
        
        current_time = timezone.now()
        expired_events = GroupEvent.objects.filter(end_time__lt=current_time)
        
        cleanup_summary = {
            'expired_events_count': expired_events.count(),
            'preserved_events': [],
            'removed_events': [],
            'data_preservation_enabled': preserve_data
        }
        
        for event in expired_events:
            if preserve_data:
                # Ensure event is marked as inactive but preserve all data
                if event.is_active:
                    event.is_active = False
                    event.save()
                
                # Remove from active platform mode if it's the active event
                try:
                    platform_mode = PlatformMode.objects.get(mode='group')
                    if platform_mode.active_event == event:
                        platform_mode.active_event = None
                        platform_mode.save()
                except PlatformMode.DoesNotExist:
                    pass
                
                cleanup_summary['preserved_events'].append({
                    'id': event.id,
                    'name': event.name,
                    'end_time': event.end_time,
                    'challenges_count': GroupChallenge.objects.filter(event=event).count(),
                    'submissions_count': GroupSubmission.objects.filter(challenge__event=event).count()
                })
            else:
                # This would remove the event and all related data
                # Note: This is generally not recommended as it loses historical data
                event_info = {
                    'id': event.id,
                    'name': event.name,
                    'end_time': event.end_time
                }
                
                # Remove related data (cascading delete should handle this)
                event.delete()
                
                cleanup_summary['removed_events'].append(event_info)
        
        return cleanup_summary
    
    @staticmethod
    def preserve_event_results(event):
        """
        Ensure event results are properly preserved for historical access
        
        Args:
            event: GroupEvent instance to preserve
        
        Returns:
            dict: Summary of preserved data
        """
        preservation_summary = {
            'event_id': event.id,
            'event_name': event.name,
            'preservation_timestamp': timezone.now(),
            'preserved_data': {}
        }
        
        # Count preserved challenges
        challenges = GroupChallenge.objects.filter(event=event)
        preservation_summary['preserved_data']['challenges_count'] = challenges.count()
        
        # Count preserved submissions
        submissions = GroupSubmission.objects.filter(challenge__event=event)
        preservation_summary['preserved_data']['submissions_count'] = submissions.count()
        
        # Count participating teams
        participating_teams = Team.objects.filter(
            groupsubmission__challenge__event=event
        ).distinct()
        preservation_summary['preserved_data']['participating_teams_count'] = participating_teams.count()
        
        # Generate final leaderboard
        final_leaderboard = GroupScoring.get_group_leaderboard(event)
        preservation_summary['preserved_data']['final_leaderboard'] = final_leaderboard
        
        # Calculate event statistics
        total_points_awarded = submissions.filter(is_correct=True).aggregate(
            total=models.Sum('points_awarded')
        )['total'] or 0
        
        preservation_summary['preserved_data']['statistics'] = {
            'total_points_awarded': total_points_awarded,
            'total_correct_submissions': submissions.filter(is_correct=True).count(),
            'total_incorrect_submissions': submissions.filter(is_correct=False).count(),
            'average_team_score': total_points_awarded / max(participating_teams.count(), 1)
        }
        
        return preservation_summary
    
    @staticmethod
    def get_event_history():
        """
        Get historical data for all group events
        
        Returns:
            list: List of all events with their preserved data
        """
        events = GroupEvent.objects.all().order_by('-end_time')
        history = []
        
        for event in events:
            event_data = GroupEventLifecycleManager.preserve_event_results(event)
            event_data['event_details'] = {
                'start_time': event.start_time,
                'end_time': event.end_time,
                'created_by': event.created_by.username,
                'created_at': event.created_at,
                'is_active': event.is_active,
                'point_multiplier': event.point_multiplier,
                'max_teams': event.max_teams
            }
            history.append(event_data)
        
        return history