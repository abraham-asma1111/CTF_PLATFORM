from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Team, TeamMembership, TeamInvitation
import json


@login_required
def team_list(request):
    """Display all teams"""
    teams = Team.objects.filter(is_active=True).prefetch_related('members')
    
    # Get user's current team if any
    user_membership = TeamMembership.objects.filter(
        user=request.user, 
        status='accepted'
    ).select_related('team').first()
    
    # Get user's pending requests
    pending_requests = TeamMembership.objects.filter(
        user=request.user,
        status='pending'
    ).select_related('team') if request.user.is_authenticated else []
    
    context = {
        'teams': teams,
        'user_membership': user_membership,
        'pending_requests': pending_requests,
    }
    return render(request, 'teams/team_list.html', context)


@login_required
def team_detail(request, team_id):
    """Display team details"""
    team = get_object_or_404(Team, id=team_id, is_active=True)
    members = team.members.filter(status='accepted').select_related('user')
    pending_requests = team.members.filter(status='pending').select_related('user')
    
    # Check if user is captain
    is_captain = team.captain == request.user
    
    # Check if user is member
    is_member = members.filter(user=request.user).exists()
    
    # Check if user has pending request
    has_pending_request = pending_requests.filter(user=request.user).exists()
    
    context = {
        'team': team,
        'members': members,
        'pending_requests': pending_requests if is_captain else None,
        'is_captain': is_captain,
        'is_member': is_member,
        'has_pending_request': has_pending_request,
    }
    return render(request, 'teams/team_detail.html', context)


@login_required
def create_team(request):
    """Create a new team"""
    # Check if user is already in an accepted team
    accepted_membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).first()
    
    if accepted_membership:
        messages.warning(request, 'You are already in a team. Leave your current team before creating a new one.')
        return redirect('teams:team_detail', team_id=accepted_membership.team.id)
    
    # Check if user has pending requests
    pending_requests = TeamMembership.objects.filter(
        user=request.user,
        status='pending'
    ).select_related('team')
    
    if pending_requests.exists():
        messages.warning(request, 'You have pending team join requests. Cancel them first before creating a new team.')
        context = {'pending_requests': pending_requests}
        return render(request, 'teams/create_team.html', context)
    
    if request.method == 'POST':
        team_name = request.POST.get('team_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not team_name:
            messages.error(request, 'Team name is required')
            return redirect('teams:create_team')
        
        # Check if team name already exists
        if Team.objects.filter(name=team_name).exists():
            messages.error(request, 'Team name already exists')
            return redirect('teams:create_team')
        
        # Double-check no accepted membership exists (safety check)
        if TeamMembership.objects.filter(user=request.user, status='accepted').exists():
            messages.error(request, 'You are already in a team. Cannot create a new team.')
            return redirect('teams:team_list')
        
        # Create team
        team = Team.objects.create(
            name=team_name,
            captain=request.user,
            description=description
        )
        
        # Add creator as member (this is critical!)
        try:
            team.ensure_captain_membership()
            
            # Cancel any pending requests since user is now in a team
            TeamMembership.objects.filter(
                user=request.user,
                status='pending'
            ).update(status='rejected')
            
            # Cancel any pending invitations
            TeamInvitation.objects.filter(
                to_user=request.user,
                status='pending'
            ).update(status='cancelled')
            
        except Exception as e:
            # If membership creation fails, delete the team to maintain consistency
            team.delete()
            messages.error(request, f'Failed to create team membership: {str(e)}')
            return redirect('teams:create_team')
        
        messages.success(request, f'Team "{team_name}" created successfully!')
        return redirect('teams:team_detail', team_id=team.id)
    
    return render(request, 'teams/create_team.html')


@login_required
@csrf_exempt
def join_team(request, team_id):
    """Request to join a team"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Check if user is already in an accepted team
    accepted_membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).first()
    
    if accepted_membership:
        return JsonResponse({
            'success': False, 
            'message': 'You are already in a team. Leave your current team first.'
        })
    
    # Additional check: prevent joining your own team
    if team.captain == request.user:
        return JsonResponse({
            'success': False,
            'message': 'You cannot join your own team - you are already the captain!'
        })
    
    # Check if team is full
    if team.is_full():
        return JsonResponse({
            'success': False,
            'message': 'Team is full'
        })
    
    # Check if already has pending request for this specific team
    existing_request = TeamMembership.objects.filter(
        team=team,
        user=request.user,
        status='pending'
    ).first()
    
    if existing_request:
        return JsonResponse({
            'success': False,
            'message': f'You already have a pending request for {team.name}'
        })
    
    # Create join request
    TeamMembership.objects.create(
        team=team,
        user=request.user,
        status='pending'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Join request sent to {team.name}'
    })


@login_required
@csrf_exempt
def approve_member(request, membership_id):
    """Approve a team join request"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    membership = get_object_or_404(TeamMembership, id=membership_id)
    
    # Only captain can approve
    if membership.team.captain != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Only team captain can approve members'
        })
    
    # Check if team is full
    if membership.team.is_full():
        return JsonResponse({
            'success': False,
            'message': 'Team is full'
        })
    
    membership.status = 'accepted'
    membership.save()
    
    # Cancel all other pending requests and invitations for this user
    TeamMembership.cancel_other_pending_requests(membership.user, membership.team)
    
    # Cancel any pending invitations for this user
    TeamInvitation.objects.filter(
        to_user=membership.user,
        status='pending'
    ).update(status='cancelled')
    
    return JsonResponse({
        'success': True,
        'message': f'{membership.user.username} added to team'
    })


@login_required
@csrf_exempt
def reject_member(request, membership_id):
    """Reject a team join request"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    membership = get_object_or_404(TeamMembership, id=membership_id)
    
    # Only captain can reject
    if membership.team.captain != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Only team captain can reject members'
        })
    
    membership.status = 'rejected'
    membership.save()
    
    return JsonResponse({
        'success': True,
        'message': f'{membership.user.username} request rejected'
    })


@login_required
@csrf_exempt
def remove_member(request, membership_id):
    """Remove a member from the team (Captain only)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    membership = get_object_or_404(TeamMembership, id=membership_id, status='accepted')
    
    # Only captain can remove members
    if membership.team.captain != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Only team captain can remove members'
        })
    
    # Captain cannot remove themselves
    if membership.user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'Captain cannot remove themselves. Transfer captaincy first or disband the team.'
        })
    
    username = membership.user.username
    membership.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'{username} removed from team'
    })


@login_required
@csrf_exempt
def transfer_captaincy(request, team_id):
    """Transfer team captaincy to another member"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        data = json.loads(request.body)
        new_captain_id = data.get('new_captain_id')
        
        if not new_captain_id:
            return JsonResponse({'success': False, 'message': 'New captain ID is required'})
        
        team = get_object_or_404(Team, id=team_id, is_active=True)
        
        # Only current captain can transfer
        if team.captain != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Only current captain can transfer captaincy'
            })
        
        # Get new captain
        new_captain = get_object_or_404(User, id=new_captain_id)
        
        # Check if new captain is a team member
        new_captain_membership = TeamMembership.objects.filter(
            team=team,
            user=new_captain,
            status='accepted'
        ).first()
        
        if not new_captain_membership:
            return JsonResponse({
                'success': False,
                'message': 'New captain must be a team member'
            })
        
        # Transfer captaincy
        team.captain = new_captain
        team.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Captaincy transferred to {new_captain.username}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@csrf_exempt
def cancel_join_request(request):
    """Cancel all pending join requests"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    pending_requests = TeamMembership.objects.filter(
        user=request.user,
        status='pending'
    )
    
    if not pending_requests.exists():
        return JsonResponse({
            'success': False,
            'message': 'You do not have any pending join requests'
        })
    
    count = pending_requests.count()
    pending_requests.delete()
    
    message = f'All {count} pending requests cancelled' if count > 1 else 'Join request cancelled'
    
    return JsonResponse({
        'success': True,
        'message': message
    })


@login_required
@csrf_exempt
def leave_team(request):
    """Leave current team"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).first()
    
    if not membership:
        return JsonResponse({
            'success': False,
            'message': 'You are not in a team'
        })
    
    team = membership.team
    
    # Captain cannot leave if there are other members
    if team.captain == request.user and team.member_count() > 1:
        return JsonResponse({
            'success': False,
            'message': 'Transfer captaincy before leaving or disband the team'
        })
    
    # If captain is last member, deactivate team
    if team.captain == request.user and team.member_count() == 1:
        team.is_active = False
        team.save()
    
    membership.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'You left the team'
    })


@login_required
def team_management(request, team_id):
    """Team management page for captains"""
    team = get_object_or_404(Team, id=team_id, is_active=True)
    
    # Only captain can access
    if team.captain != request.user:
        messages.error(request, 'Only team captain can access team management')
        return redirect('teams:team_detail', team_id=team_id)
    
    members = team.members.filter(status='accepted').select_related('user')
    pending_requests = team.members.filter(status='pending').select_related('user')
    sent_invitations = team.invitations.filter(status='pending').select_related('to_user')
    
    context = {
        'team': team,
        'members': members,
        'pending_requests': pending_requests,
        'sent_invitations': sent_invitations,
    }
    return render(request, 'teams/team_management.html', context)


@login_required
@csrf_exempt
def send_invitation(request, team_id):
    """Send email invitation to a user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        message_text = data.get('message', '').strip()
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        team = get_object_or_404(Team, id=team_id, is_active=True)
        
        # Only captain can send invitations
        if team.captain != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Only team captain can send invitations'
            })
        
        # Check if team is full
        if team.is_full():
            return JsonResponse({
                'success': False,
                'message': 'Team is full'
            })
        
        # Find user by email
        try:
            to_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No user found with this email'
            })
        
        # Check if user is already in a team or has pending requests
        existing_membership = TeamMembership.objects.filter(
            user=to_user
        ).first()
        
        if existing_membership:
            if existing_membership.status == 'accepted':
                return JsonResponse({
                    'success': False,
                    'message': f'{to_user.username} is already in a team'
                })
            elif existing_membership.status == 'pending':
                return JsonResponse({
                    'success': False,
                    'message': f'{to_user.username} already has a pending team request'
                })
        
        # Prevent inviting yourself
        if to_user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot invite yourself'
            })
        
        # Check if invitation already exists
        existing_invitation = TeamInvitation.objects.filter(
            team=team,
            to_user=to_user,
            status='pending'
        ).first()
        
        if existing_invitation:
            return JsonResponse({
                'success': False,
                'message': 'Invitation already sent to this user'
            })
        
        # Create invitation
        invitation = TeamInvitation.objects.create(
            team=team,
            from_user=request.user,
            to_user=to_user,
            message=message_text,
            status='pending'
        )
        
        # Send email
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f'Team Invitation: {team.name}'
        email_message = f"""
Hello {to_user.username},

{request.user.username} has invited you to join their team "{team.name}" on the CTF Platform!

{message_text if message_text else 'Join us and compete together!'}

Team Details:
- Team Name: {team.name}
- Captain: {team.captain.username}
- Current Members: {team.member_count()}/{team.max_members}
- Team Score: {team.total_score} points

To accept or decline this invitation, please log in to the platform and check your invitations.

Login here: {request.build_absolute_uri('/users/login/')}

Good luck!
CTF Platform Team
"""
        
        try:
            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [to_user.email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Invitation sent to {to_user.username}'
            })
        except Exception as e:
            # If email fails, still create the invitation
            return JsonResponse({
                'success': True,
                'message': f'Invitation created for {to_user.username} (email may not have been sent)'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@csrf_exempt
def cancel_invitation(request, invitation_id):
    """Cancel a sent invitation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    invitation = get_object_or_404(TeamInvitation, id=invitation_id)
    
    # Only captain can cancel invitations
    if invitation.team.captain != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Only team captain can cancel invitations'
        })
    
    if invitation.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'This invitation cannot be cancelled'
        })
    
    invitation.status = 'cancelled'
    invitation.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Invitation to {invitation.to_user.username} cancelled'
    })


@login_required
def my_invitations(request):
    """Display user's pending invitations"""
    invitations = TeamInvitation.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('team', 'from_user').order_by('-created_at')
    
    context = {
        'invitations': invitations,
    }
    return render(request, 'teams/my_invitations.html', context)


@login_required
@csrf_exempt
def accept_invitation(request, invitation_id):
    """Accept a team invitation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    invitation = get_object_or_404(TeamInvitation, id=invitation_id, to_user=request.user)
    
    if invitation.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'This invitation is no longer valid'
        })
    
    # Check if user is already in a team
    existing_membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).first()
    
    if existing_membership:
        return JsonResponse({
            'success': False,
            'message': 'You are already in a team. Leave your current team first.'
        })
    
    # Check if team is full
    if invitation.team.is_full():
        invitation.status = 'cancelled'
        invitation.save()
        return JsonResponse({
            'success': False,
            'message': 'Team is now full'
        })
    
    # Accept invitation
    invitation.status = 'accepted'
    invitation.save()
    
    # Create membership
    membership = TeamMembership.objects.create(
        team=invitation.team,
        user=request.user,
        status='accepted'
    )
    
    # Cancel all other pending requests and invitations for this user
    TeamMembership.cancel_other_pending_requests(request.user, invitation.team)
    
    # Cancel any other pending invitations for this user
    TeamInvitation.objects.filter(
        to_user=request.user,
        status='pending'
    ).exclude(id=invitation_id).update(status='cancelled')
    
    return JsonResponse({
        'success': True,
        'message': f'You joined {invitation.team.name}!',
        'team_id': invitation.team.id
    })


@login_required
@csrf_exempt
def decline_invitation(request, invitation_id):
    """Decline a team invitation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    invitation = get_object_or_404(TeamInvitation, id=invitation_id, to_user=request.user)
    
    if invitation.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'This invitation is no longer valid'
        })
    
    invitation.status = 'rejected'
    invitation.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Invitation declined'
    })


@login_required
def my_team(request):
    """Display user's current team"""
    membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).select_related('team').first()
    
    if not membership:
        messages.info(request, 'You are not in a team. Create or join one!')
        return redirect('teams:team_list')
    
    return redirect('teams:team_detail', team_id=membership.team.id)


@login_required
def team_leaderboard(request):
    """Display team leaderboard"""
    teams = Team.objects.filter(
        is_active=True
    ).prefetch_related('members').order_by('-total_score', 'last_submission')
    
    # Filter teams that can compete (at least 2 members)
    competing_teams = [team for team in teams if team.can_compete()]
    
    context = {
        'teams': competing_teams,
    }
    return render(request, 'teams/team_leaderboard.html', context)