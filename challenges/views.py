from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .models import Challenge
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
    challenges = Challenge.objects.filter(is_active=True)
    user_solved = []
    
    if request.user.is_authenticated:
        user_solved = list(Submission.objects.filter(
            user=request.user, 
            is_correct=True
        ).values_list('challenge_id', flat=True))
    
    context = {
        'challenges': challenges,
        'user_solved': user_solved,
    }
    return render(request, 'challenges/list.html', context)

@login_required
def challenge_detail(request, challenge_id):
    """Display challenge details and submission form"""
    challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)
    
    # Check if user already solved this challenge
    user_solved = Submission.objects.filter(
        user=request.user,
        challenge=challenge,
        is_correct=True
    ).exists()
    
    context = {
        'challenge': challenge,
        'user_solved': user_solved,
    }
    return render(request, 'challenges/detail.html', context)

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
        data = json.loads(request.body)
        submitted_flag = data.get('flag', '').strip()
        
        if not submitted_flag:
            return JsonResponse({'success': False, 'message': 'Flag cannot be empty'})
        
        challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)
        
        # Check if user already solved this challenge
        existing_submission = Submission.objects.filter(
            user=request.user,
            challenge=challenge,
            is_correct=True
        ).first()
        
        if existing_submission:
            return JsonResponse({'success': False, 'message': 'You have already solved this challenge'})
        
        # Check the flag
        is_correct = challenge.check_flag(submitted_flag)
        
        # Create submission record
        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            submitted_flag=submitted_flag,
            is_correct=is_correct
        )
        
        if is_correct:
            # Update user profile
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
        return JsonResponse({'success': False, 'message': 'An error occurred'})


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
