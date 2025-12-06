from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .models import Challenge, Hint, HintView
from submissions.models import Submission
from users.models import UserProfile
import json

def home(request):
    """Home page with CTF overview"""
    total_challenges = Challenge.objects.filter(is_active=True).count()
    
    # Cybersecurity-themed blog posts with images
    blog_posts = [
        {
            'title': 'OPERATION: DIGITAL FORTRESS LAUNCHED',
            'date': '2024-11-24',
            'excerpt': 'Elite hackers wanted. Our advanced penetration testing platform is now live with military-grade challenges designed to test your limits.',
            'author': 'CYBER COMMAND',
            'image': '/static/images/blog-ctf-1.png'
        },
        {
            'title': 'ZERO-DAY EXPLOITATION TECHNIQUES',
            'date': '2024-11-20',
            'excerpt': 'Discover cutting-edge vulnerability research methods. New challenges featuring real-world attack vectors and advanced persistent threats.',
            'author': 'RED TEAM',
            'image': '/static/images/blog-ctf-2.png'
        },
        {
            'title': 'CLASSIFIED: ADVANCED THREAT HUNTING',
            'date': '2024-11-15',
            'excerpt': 'Master the art of digital forensics and incident response. Learn to track sophisticated adversaries through complex network infrastructures.',
            'author': 'BLUE TEAM',
            'image': '/static/images/blog-ctf-3.png'
        },
        {
            'title': 'HACKER SUMMIT 2024 RECAP',
            'date': '2024-11-10',
            'excerpt': 'Join us as we recap the most intense cybersecurity competition of the year. Witness elite teams battle for supremacy.',
            'author': 'INTEL DIVISION',
            'image': '/static/images/blog-ctf-4.png'
        },
        {
            'title': 'CRYPTOGRAPHY MASTERCLASS SERIES',
            'date': '2024-11-05',
            'excerpt': 'Unlock the secrets of modern encryption. Learn RSA, AES, and quantum-resistant algorithms through hands-on challenges.',
            'author': 'CRYPTO TEAM',
            'image': '/static/images/blog-ctf-5.png'
        }
    ]
    
    context = {
        'total_challenges': total_challenges,
        'blog_posts': blog_posts,
    }
    return render(request, 'home.html', context)

def challenge_list(request):
    """Display all active challenges"""
    from teams.models import TeamMembership
    
    user_solved = []
    
    if request.user.is_authenticated:
        # Check if user is in a team
        team_membership = TeamMembership.objects.filter(
            user=request.user,
            status='accepted'
        ).select_related('team').first()
        
        if team_membership:
            # User is in a team - show team and both challenges
            team = team_membership.team
            team_size = team.member_count()
            
            challenges = Challenge.objects.filter(
                is_active=True,
                challenge_type__in=['team', 'both']
            ).filter(
                min_team_size__lte=team_size,
                max_team_size__gte=team_size
            ).order_by('id')
            
            # Get team's solved challenges
            user_solved = list(Submission.objects.filter(
                team=team_membership.team,
                is_correct=True
            ).values_list('challenge_id', flat=True))
        else:
            # User not in team - show individual and both challenges
            challenges = Challenge.objects.filter(
                is_active=True,
                challenge_type__in=['individual', 'both']
            ).order_by('id')
            
            # Get individual solved challenges
            user_solved = list(Submission.objects.filter(
                user=request.user, 
                is_correct=True,
                team__isnull=True
            ).values_list('challenge_id', flat=True))
    else:
        # Not authenticated - show all challenges
        challenges = Challenge.objects.filter(is_active=True).order_by('id')
    
    # Get all categories
    categories = Challenge.CATEGORY_CHOICES
    
    context = {
        'challenges': challenges,
        'user_solved': user_solved,
        'categories': categories,
    }
    return render(request, 'challenges/list.html', context)

@login_required
def challenge_detail(request, challenge_id):
    """Display challenge details and submission form"""
    from teams.models import TeamMembership
    
    # If admin, show admin view
    if request.user.is_staff or request.user.is_superuser:
        return redirect('challenges:admin_detail', challenge_id=challenge_id)
    
    challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)
    
    # Check if user is in a team
    team_membership = TeamMembership.objects.filter(
        user=request.user,
        status='accepted'
    ).select_related('team').first()
    
    user_team = team_membership.team if team_membership else None
    
    # Check if user can access this challenge
    if user_team:
        team_size = user_team.member_count()
        if challenge.challenge_type == 'individual':
            messages.error(request, 'This is an individual-only challenge. Leave your team to access it.')
            return redirect('challenges:list')
        if team_size < challenge.min_team_size or team_size > challenge.max_team_size:
            messages.error(request, f'This challenge requires {challenge.min_team_size}-{challenge.max_team_size} team members. Your team has {team_size}.')
            return redirect('challenges:list')
    else:
        if challenge.challenge_type == 'team':
            messages.error(request, 'This is a team-only challenge. Join a team to access it.')
            return redirect('challenges:list')
    
    # Check if user/team already solved this challenge
    if user_team:
        user_solved = Submission.objects.filter(
            team=user_team,
            challenge=challenge,
            is_correct=True
        ).exists()
    else:
        user_solved = Submission.objects.filter(
            user=request.user,
            challenge=challenge,
            is_correct=True,
            team__isnull=True
        ).exists()
    
    # Get hints for this challenge
    hints = challenge.hints.all()
    
    # Check which hints user has viewed
    viewed_hints = HintView.objects.filter(
        user=request.user,
        hint__challenge=challenge
    ).values_list('hint_id', flat=True)
    
    # Check user's preference for showing hints
    show_hints = request.user.userprofile.show_hints
    
    context = {
        'challenge': challenge,
        'user_solved': user_solved,
        'hints': hints,
        'viewed_hints': list(viewed_hints),
        'show_hints': show_hints,
        'user_team': user_team,
    }
    return render(request, 'challenges/detail.html', context)

@login_required
def admin_challenge_detail(request, challenge_id):
    """Admin view for challenge details and editing"""
    # Only admins can access
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('challenges:detail', challenge_id=challenge_id)
    
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # Get submission stats for this challenge
    total_submissions = Submission.objects.filter(challenge=challenge).count()
    correct_submissions = Submission.objects.filter(challenge=challenge, is_correct=True).count()
    
    context = {
        'challenge': challenge,
        'total_submissions': total_submissions,
        'correct_submissions': correct_submissions,
    }
    return render(request, 'challenges/admin_detail.html', context)

@login_required
@csrf_exempt
def submit_flag(request, challenge_id):
    """Handle flag submission via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    # Prevent admins from solving challenges
    if request.user.is_staff or request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Admins cannot solve challenges.'})
    
    try:
        from teams.models import TeamMembership
        
        data = json.loads(request.body)
        submitted_flag = data.get('flag', '').strip()
        
        if not submitted_flag:
            return JsonResponse({'success': False, 'message': 'Flag cannot be empty'})
        
        challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)
        
        # Check if user is in a team
        team_membership = TeamMembership.objects.filter(
            user=request.user,
            status='accepted'
        ).select_related('team').first()
        
        user_team = team_membership.team if team_membership else None
        
        # Check if team/user already solved this challenge
        if user_team:
            # Check if team already solved this
            team_solved = Submission.objects.filter(
                team=user_team,
                challenge=challenge,
                is_correct=True
            ).exists()
            
            if team_solved:
                return JsonResponse({'success': False, 'message': 'Your team has already solved this challenge'})
        else:
            # Check if individual user already solved this
            user_solved = Submission.objects.filter(
                user=request.user,
                challenge=challenge,
                is_correct=True,
                team__isnull=True
            ).exists()
            
            if user_solved:
                return JsonResponse({'success': False, 'message': 'You have already solved this challenge'})
        
        # Check the flag
        is_correct = challenge.check_flag(submitted_flag)
        
        # Create submission record
        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            submitted_flag=submitted_flag,
            is_correct=is_correct,
            team=user_team
        )
        
        if submission.is_correct:
            if user_team:
                # Calculate team points (with multiplier)
                team_points = int(challenge.points * challenge.team_points_multiplier)
                
                # Update team score
                team = user_team
                team.total_score += team_points
                team.challenges_solved += 1
                team.last_submission = timezone.now()
                team.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Correct! Your team earned {team_points} points! (Base: {challenge.points} × {challenge.team_points_multiplier})',
                    'points': team_points,
                    'team_name': team.name
                })
            else:
                # Update individual score
                profile = request.user.userprofile
                profile.total_score += challenge.points
                profile.challenges_solved += 1
                profile.last_submission = timezone.now()
                profile.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Correct! You earned {challenge.points} points!',
                    'points': challenge.points
                })
        else:
            return JsonResponse({'success': False, 'message': 'Incorrect flag. Try again!'})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        import traceback
        print(f"Error in submit_flag: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@login_required
def download_challenge_file(request, challenge_id):
    """Download challenge file"""
    from django.http import FileResponse
    import os
    
    challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)
    
    if not challenge.challenge_file:
        return JsonResponse({'error': 'No file available for this challenge'}, status=404)
    
    file_path = challenge.challenge_file.path
    file_name = os.path.basename(file_path)
    
    try:
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except FileNotFoundError:
        return JsonResponse({'error': 'File not found'}, status=404)


@login_required
@csrf_exempt
def view_hint(request, hint_id):
    """View a hint and deduct points if applicable"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        hint = get_object_or_404(Hint, id=hint_id)
        
        # Check if user's preference allows hints
        if not request.user.userprofile.show_hints:
            return JsonResponse({
                'success': False, 
                'message': 'Hints are disabled in your settings. Enable them in Settings → Preferences.'
            })
        
        # Check if user already viewed this hint
        hint_view, created = HintView.objects.get_or_create(
            user=request.user,
            hint=hint,
            defaults={'points_deducted': hint.cost}
        )
        
        if created and hint.cost > 0:
            # Deduct points from user's profile
            profile = request.user.userprofile
            profile.total_score -= hint.cost
            if profile.total_score < 0:
                profile.total_score = 0
            profile.save()
            
            return JsonResponse({
                'success': True,
                'hint': hint.content,
                'cost': hint.cost,
                'message': f'Hint revealed! {hint.cost} points deducted.',
                'new_score': profile.total_score
            })
        else:
            # Already viewed or free hint
            return JsonResponse({
                'success': True,
                'hint': hint.content,
                'cost': 0,
                'message': 'Hint revealed!' if created else 'You already viewed this hint.',
                'new_score': request.user.userprofile.total_score
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
