from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Max
from teams.models import Team, TeamMembership
from .models import TeamMessage, MessageReaction, MessageRead
import json


@login_required
def team_chat(request, team_id):
    """Main team chat interface"""
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Check if user is a team member
    membership = TeamMembership.objects.filter(
        team=team,
        user=request.user,
        status='accepted'
    ).first()
    
    if not membership:
        messages.error(request, 'You must be a team member to access the chat.')
        return redirect('teams:team_detail', team_id=team_id)
    
    # Get recent messages (last 50)
    chat_messages = TeamMessage.objects.filter(
        team=team
    ).select_related('sender', 'sender__userprofile').prefetch_related('reactions', 'read_by').order_by('-timestamp')[:50]
    
    # Reverse to show oldest first
    chat_messages = list(reversed(chat_messages))
    
    # Add permission properties to each message
    for message in chat_messages:
        message.can_edit = message.can_edit(request.user)
        message.can_delete = message.can_delete(request.user)
    
    # Mark messages as read
    unread_messages = TeamMessage.objects.filter(
        team=team,
        timestamp__gt=timezone.now() - timezone.timedelta(hours=24)
    ).exclude(
        read_by__user=request.user
    )
    
    # Bulk create read records
    read_records = [
        MessageRead(message=msg, user=request.user)
        for msg in unread_messages
    ]
    MessageRead.objects.bulk_create(read_records, ignore_conflicts=True)
    
    # Get team members for @mentions
    team_members = User.objects.filter(
        team_memberships__team=team,
        team_memberships__status='accepted'
    ).values('id', 'username')
    
    context = {
        'team': team,
        'messages': chat_messages,
        'team_members': team_members,
        'is_captain': team.captain == request.user,
    }
    
    response = render(request, 'chat/team_chat.html', context)
    # Prevent caching and logging
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['Last-Modified'] = timezone.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response['ETag'] = f'"{timezone.now().timestamp()}"'
    response['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'
    return response


@login_required
@csrf_exempt
def send_message(request, team_id):
    """Send a new message to team chat"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Check if user is a team member
    membership = TeamMembership.objects.filter(
        team=team,
        user=request.user,
        status='accepted'
    ).first()
    
    if not membership:
        return JsonResponse({
            'success': False,
            'message': 'You must be a team member to send messages'
        })
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'message': 'Message content cannot be empty'
            })
        
        if len(content) > 1000:
            return JsonResponse({
                'success': False,
                'message': 'Message too long (max 1000 characters)'
            })
        
        # Create message
        message = TeamMessage.objects.create(
            team=team,
            sender=request.user,
            content=content,
            message_type='text'
        )
        
        # Mark as read by sender
        MessageRead.objects.create(message=message, user=request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Message sent',
            'message_data': {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'can_edit': True,
                'can_delete': True
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@csrf_exempt
def edit_message(request, message_id):
    """Edit an existing message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    message = get_object_or_404(TeamMessage, id=message_id)
    
    # Check permissions
    if not message.can_edit(request.user):
        return JsonResponse({
            'success': False,
            'message': 'You can only edit your own text messages'
        })
    
    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({
                'success': False,
                'message': 'Message content cannot be empty'
            })
        
        if len(new_content) > 1000:
            return JsonResponse({
                'success': False,
                'message': 'Message too long (max 1000 characters)'
            })
        
        # Update message
        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message updated',
            'new_content': message.content
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@csrf_exempt
def delete_message(request, message_id):
    """Delete a message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    message = get_object_or_404(TeamMessage, id=message_id)
    
    # Check permissions
    if not message.can_delete(request.user):
        return JsonResponse({
            'success': False,
            'message': 'You can only delete your own messages or you must be team captain'
        })
    
    message.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Message deleted'
    })


@login_required
@csrf_exempt
def react_to_message(request, message_id):
    """Add or remove reaction to a message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    message = get_object_or_404(TeamMessage, id=message_id)
    
    # Check if user is team member
    membership = TeamMembership.objects.filter(
        team=message.team,
        user=request.user,
        status='accepted'
    ).first()
    
    if not membership:
        return JsonResponse({
            'success': False,
            'message': 'You must be a team member to react to messages'
        })
    
    try:
        data = json.loads(request.body)
        emoji = data.get('emoji', '').strip()
        
        if not emoji:
            return JsonResponse({
                'success': False,
                'message': 'Emoji is required'
            })
        
        # Check if reaction already exists
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).first()
        
        if existing_reaction:
            # Remove reaction
            existing_reaction.delete()
            action = 'removed'
        else:
            # Add reaction
            MessageReaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            action = 'added'
        
        # Get updated reaction counts
        reactions = MessageReaction.objects.filter(message=message).values('emoji').annotate(
            count=Count('id')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Reaction {action}',
            'reactions': list(reactions)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@csrf_exempt
def get_messages(request, team_id):
    """Get messages for real-time updates"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Check if user is team member
    membership = TeamMembership.objects.filter(
        team=team,
        user=request.user,
        status='accepted'
    ).first()
    
    if not membership:
        return JsonResponse({
            'success': False,
            'message': 'You must be a team member to view messages'
        })
    
    # Get timestamp from query params for incremental loading
    since = request.GET.get('since')
    if since:
        try:
            since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            messages_query = TeamMessage.objects.filter(
                team=team,
                timestamp__gt=since_dt
            )
        except ValueError:
            messages_query = TeamMessage.objects.filter(team=team)
    else:
        # Get last 50 messages
        messages_query = TeamMessage.objects.filter(team=team).order_by('-timestamp')[:50]
    
    messages_data = []
    for msg in messages_query.select_related('sender').prefetch_related('reactions'):
        reactions = {}
        for reaction in msg.reactions.all():
            if reaction.emoji not in reactions:
                reactions[reaction.emoji] = []
            reactions[reaction.emoji].append(reaction.user.username)
        
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_edited': msg.is_edited,
            'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
            'message_type': msg.message_type,
            'reactions': reactions,
            'can_edit': msg.can_edit(request.user),
            'can_delete': msg.can_delete(request.user)
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })


@login_required
def chat_notifications(request):
    """Get unread message count for user's teams"""
    user_teams = Team.objects.filter(
        members__user=request.user,
        members__status='accepted',
        is_active=True
    )
    
    notifications = {}
    for team in user_teams:
        unread_count = TeamMessage.objects.filter(
            team=team,
            timestamp__gt=timezone.now() - timezone.timedelta(days=7)
        ).exclude(
            read_by__user=request.user
        ).count()
        
        if unread_count > 0:
            notifications[team.id] = {
                'team_name': team.name,
                'unread_count': unread_count
            }
    
    return JsonResponse({
        'success': True,
        'notifications': notifications
    })