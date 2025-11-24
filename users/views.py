from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from submissions.models import Submission

def register(request):
    """User registration view"""
    from django.contrib.auth.models import User
    import re
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        
        # Validate username format (only letters, numbers, underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            messages.error(request, 'Username can only contain letters (uppercase/lowercase), numbers, and underscores.')
            form = UserCreationForm()
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username contains @ (email format)
        if '@' in username:
            messages.error(request, 'Username cannot be an email address. Please use letters, numbers, and underscores only.')
            form = UserCreationForm()
            return render(request, 'users/register.html', {'form': form})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered. Please use a different email or login.')
            form = UserCreationForm()
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken. Please choose a different username.')
            form = UserCreationForm()
            return render(request, 'users/register.html', {'form': form})
        
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Save additional profile information
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
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
    else:
        form = UserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    """User profile page showing progress and solved challenges"""
    profile = request.user.userprofile
    solved_challenges = Submission.objects.filter(
        user=request.user,
        is_correct=True
    ).select_related('challenge').order_by('-timestamp')
    
    context = {
        'profile': profile,
        'solved_challenges': solved_challenges,
    }
    return render(request, 'users/profile.html', context)
