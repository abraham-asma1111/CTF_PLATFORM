from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.middleware.csrf import get_token
from submissions.models import Submission
from .models import UserProfile
from challenges.models import Challenge

def register(request):
    """User registration view"""
    from django.contrib.auth.models import User
    import re
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validate first name (only alphabetic characters)
        if first_name and not re.match(r"^[a-zA-Z]+$", first_name):
            messages.error(request, 'First name can only contain letters.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Validate last name (only alphabetic characters)
        if last_name and not re.match(r"^[a-zA-Z]+$", last_name):
            messages.error(request, 'Last name can only contain letters.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Validate username format (only letters, numbers, underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            messages.error(request, 'Username can only contain letters (uppercase/lowercase), numbers, and underscores.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username contains @ (email format)
        if '@' in username:
            messages.error(request, 'Username cannot be an email address. Please use letters, numbers, and underscores only.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered. Please use a different email or login.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken. Please choose a different username.')
            form = UserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Save additional profile information
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            # Update user profile with additional fields
            profile = user.userprofile
            profile.sex = request.POST.get('sex', '')
            profile.education_level = request.POST.get('education_level', '')
            profile.department = request.POST.get('department', '')
            profile.save()
            
            messages.success(request, 'Registration successful! Please login with your credentials.')
            return redirect('users:login')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            get_token(request)
    else:
        form = UserCreationForm()
        get_token(request)  # Ensure CSRF token is generated
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def manage_users(request):
    """Admin page for managing users"""
    from django.contrib.auth.models import User
    
    # Only admins can access
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('users:profile')
    
    # Get all users with pagination
    from django.core.paginator import Paginator
    all_users = User.objects.filter(is_staff=False, is_superuser=False).select_related('userprofile').order_by('-userprofile__total_score')
    
    paginator = Paginator(all_users, 25)  # 25 users per page
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users_page': users_page,
        'total_users': all_users.count(),
    }
    return render(request, 'users/manage_users.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard for managing challenges"""
    from django.db.models import Count, Sum
    from django.contrib.auth.models import User
    
    # Only admins can access
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('users:profile')
    
    # Get statistics
    total_challenges = Challenge.objects.count()
    active_challenges = Challenge.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_staff=False, is_superuser=False).count()
    total_submissions = Submission.objects.count()
    correct_submissions = Submission.objects.filter(is_correct=True).count()
    
    # Get challenges by category
    category_stats = {}
    for category, display_name in Challenge.CATEGORY_CHOICES:
        count = Challenge.objects.filter(category=category).count()
        category_stats[category] = {
            'display_name': display_name,
            'count': count,
        }
    
    # Get recent submissions
    recent_submissions = Submission.objects.select_related(
        'user', 'challenge'
    ).order_by('-timestamp')[:10]
    
    # Get all challenges
    all_challenges = Challenge.objects.all().order_by('-created_at')
    
    # Calculate success rate
    success_rate = 0
    if total_submissions > 0:
        success_rate = round((correct_submissions / total_submissions) * 100, 1)
    
    context = {
        'total_challenges': total_challenges,
        'active_challenges': active_challenges,
        'total_users': total_users,
        'total_submissions': total_submissions,
        'correct_submissions': correct_submissions,
        'success_rate': success_rate,
        'category_stats': category_stats,
        'recent_submissions': recent_submissions,
        'all_challenges': all_challenges,
    }
    return render(request, 'users/admin_dashboard.html', context)

@login_required
def profile(request):
    """User profile page showing progress and solved challenges"""
    from django.db.models import Count
    from django.shortcuts import redirect
    
    # Redirect admins to admin dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('users:admin_dashboard')
    
    profile = request.user.userprofile
    solved_challenges = Submission.objects.filter(
        user=request.user,
        is_correct=True
    ).select_related('challenge').order_by('-timestamp')
    
    # Calculate user rank
    user_rank = UserProfile.objects.filter(
        total_score__gt=profile.total_score
    ).count() + 1
    
    # Get category stats
    category_stats = {}
    for category, display_name in Challenge.CATEGORY_CHOICES:
        category_challenges = Challenge.objects.filter(category=category, is_active=True)
        solved_count = solved_challenges.filter(challenge__category=category).count()
        total_points = sum(c.points for c in category_challenges)
        user_points = sum(s.challenge.points for s in solved_challenges.filter(challenge__category=category))
        
        category_stats[category] = {
            'display_name': display_name,
            'total_challenges': category_challenges.count(),
            'solved_challenges': solved_count,
            'total_points': total_points,
            'user_points': user_points,
        }
    
    context = {
        'profile': profile,
        'solved_challenges': solved_challenges,
        'user_rank': user_rank,
        'category_stats': category_stats,
    }
    return render(request, 'users/profile.html', context)
