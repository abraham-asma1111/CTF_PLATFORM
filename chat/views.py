"""
Chat views
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from teams.models import Team, TeamMembership
from .models import TeamMessage
import json


@login_required
def team_chat(request, team_id):
    """Team chat page"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is a member of the team
    is_member = TeamMembership.objects.filter(
        team=team,
        user=request.user,
        status='accepted'
    ).exists()
    
    if not is_member:
        return JsonResponse({'error': 'You are not a member of this team'}, status=403)
    
    # Get team members
    members = TeamMembership.objects.filter(
        team=team,
        status='accepted'
    ).select_related('user')
    
    context = {
        'team': team,
        'members': members,
        'is_captain': team.captain == request.user,
    }
    
    return render(request, 'chat/team_chat.html', context)


@login_required
@require_http_methods(["POST"])
def edit_message(request, message_id):
    """Edit a chat message"""
    try:
        message = get_object_or_404(TeamMessage, id=message_id)
        
        # Check if user is the sender
        if message.sender != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You can only edit your own messages'
            }, status=403)
        
        # Parse request body
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({
                'success': False,
                'error': 'Message content cannot be empty'
            }, status=400)
        
        if len(new_content) > 1000:
            return JsonResponse({
                'success': False,
                'error': 'Message is too long (max 1000 characters)'
            }, status=400)
        
        # Update message
        message.content = new_content
        message.edited_at = timezone.now()
        message.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message updated successfully',
            'content': new_content,
            'edited_at': message.edited_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_message(request, message_id):
    """Delete a chat message"""
    try:
        message = get_object_or_404(TeamMessage, id=message_id)
        
        # Check if user is the sender or team captain
        team = message.team
        is_sender = message.sender == request.user
        is_captain = team.captain == request.user
        
        if not (is_sender or is_captain):
            return JsonResponse({
                'success': False,
                'error': 'You can only delete your own messages or you must be team captain'
            }, status=403)
        
        # Delete the message
        message.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Message deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
