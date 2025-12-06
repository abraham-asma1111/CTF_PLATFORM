from django.contrib.auth.models import User
from challenges.models import Challenge
from challenges.group_challenge_manager import GroupChallengeManager


def footer_stats(request):
    """
    Context processor to provide dynamic footer statistics
    """
    return {
        'total_challenges': Challenge.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
    }


def group_event_info(request):
    """
    Context processor to provide group event information to all templates
    """
    # Get active group event information
    is_group_mode_active = GroupChallengeManager.is_group_mode_active()
    active_group_event = GroupChallengeManager.get_active_group_event()
    
    # Get user's team information if authenticated
    user_team = None
    can_access_group_challenges = False
    
    if request.user.is_authenticated:
        user_team = GroupChallengeManager.get_user_team(request.user)
        can_access_group_challenges = GroupChallengeManager.can_user_access_group_challenges(request.user)
    
    # Get group event details if active
    group_event_details = None
    if active_group_event:
        group_event_details = GroupChallengeManager.get_group_event_info(active_group_event)
    
    return {
        'is_group_mode_active': is_group_mode_active,
        'active_group_event': active_group_event,
        'group_event_details': group_event_details,
        'user_team': user_team,
        'can_access_group_challenges': can_access_group_challenges,
    }
