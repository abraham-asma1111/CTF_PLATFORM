from django.utils import timezone
from teams.models import TeamMembership
from .models import TeamMessage


def chat_notifications(request):
    """Add chat notification data to template context"""
    if not request.user.is_authenticated:
        return {'unread_messages_count': 0}
    
    # Get user's teams
    user_teams = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).values_list('team_id', flat=True)
    
    if not user_teams:
        return {'unread_messages_count': 0}
    
    # Count unread messages from last 7 days
    unread_count = TeamMessage.objects.filter(
        team_id__in=user_teams,
        timestamp__gt=timezone.now() - timezone.timedelta(days=7)
    ).exclude(
        read_by__user=request.user
    ).count()
    
    return {
        'unread_messages_count': unread_count
    }