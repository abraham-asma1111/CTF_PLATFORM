from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.middleware.csrf import get_token
from django.utils import timezone
from datetime import timedelta
from submissions.models import Submission
from .models import UserProfile
from .forms import CustomUserCreationForm
from challenges.models import Challenge
from django.contrib.auth.models import User

def custom_login(request):
    """Custom login view with email verification check"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Check if email is verified
                if not user.userprofile.email_verified:
                    messages.error(request, 'Please verify your email before logging in. Check your inbox for the verification code.')
                    return render(request, 'users/login.html', {
                        'form': form,
                        'show_resend': True,
                        'user_email': user.email
                    })
                
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def send_verification_code(email):
    """Send verification code to email"""
    import random
    from django.core.mail import send_mail
    from django.conf import settings
    
    code = str(random.randint(100000, 999999))
    
    try:
        send_mail(
            subject='CTF Platform - Email Verification Code',
            message=f'Your verification code is: {code}\n\nThis code will expire in 60 seconds. Please enter it quickly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        print(f"\n{'='*60}")
        print(f"VERIFICATION CODE FOR {email}: {code}")
        print(f"Expires in: 60 seconds")
        print(f"{'='*60}\n")
        return code
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print(f"\n{'='*60}")
        print(f"DEVELOPMENT MODE - VERIFICATION CODE FOR {email}: {code}")
        print(f"Expires in: 60 seconds")
        print(f"{'='*60}\n")
        return code

def register(request):
    """User registration view"""
    from django.contrib.auth.models import User
    import re
    from django.utils import timezone
    from datetime import timedelta
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Check if this is a verification code submission
        verification_code = request.POST.get('verification_code', '').strip()
        if verification_code:
            # Get registration data from session
            reg_data = request.session.get('pending_registration')
            if not reg_data:
                messages.error(request, 'Registration session expired. Please register again.')
                return redirect('users:register')
            
            # Verify the code matches and hasn't expired
            stored_code = reg_data.get('verification_code')
            expires_at = timezone.datetime.fromisoformat(reg_data.get('expires_at'))
            
            if verification_code != stored_code:
                messages.error(request, 'Invalid verification code.')
                form = CustomUserCreationForm()
                get_token(request)
                return render(request, 'users/register.html', {
                    'form': form,
                    'email': reg_data.get('email'),
                    'show_verification': True
                })
            
            if timezone.now() > expires_at:
                messages.error(request, 'Verification code expired. Please register again.')
                del request.session['pending_registration']
                return redirect('users:register')
            
            # Code is valid - create the user now
            try:
                user = User.objects.create_user(
                    username=reg_data['username'],
                    email=reg_data['email'],
                    password=reg_data['password']
                )
                user.first_name = reg_data['first_name']
                user.last_name = reg_data['last_name']
                user.save()
                
                # Update user profile
                profile = user.userprofile
                profile.sex = reg_data.get('sex', '')
                profile.education_level = reg_data.get('education_level', '')
                profile.department = reg_data.get('department', '')
                profile.email_verified = True
                profile.save()
                
                # Clear session data
                del request.session['pending_registration']
                
                messages.success(request, 'Email verified! Your account has been created. You can now login.')
                return redirect('users:login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                del request.session['pending_registration']
                return redirect('users:register')
        
        # Initial registration form submission
        # Validate first name (only alphabetic characters)
        if first_name and not re.match(r"^[a-zA-Z]+$", first_name):
            messages.error(request, 'First name can only contain letters.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Validate last name (only alphabetic characters)
        if last_name and not re.match(r"^[a-zA-Z]+$", last_name):
            messages.error(request, 'Last name can only contain letters.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Validate username format (only letters, numbers, underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            messages.error(request, 'Username can only contain letters (uppercase/lowercase), numbers, and underscores.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username contains @ (email format)
        if '@' in username:
            messages.error(request, 'Username cannot be an email address. Please use letters, numbers, and underscores only.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered. Please use a different email or login.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken. Please choose a different username.')
            form = CustomUserCreationForm()
            get_token(request)
            return render(request, 'users/register.html', {'form': form})
        
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Don't save user yet - store in session and send verification code
            password = form.cleaned_data['password1']
            
            # Send verification code (expires in 60 seconds)
            code = send_verification_code(email)
            if code:
                # Store registration data in session
                request.session['pending_registration'] = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'sex': request.POST.get('sex', ''),
                    'education_level': request.POST.get('education_level', ''),
                    'department': request.POST.get('department', ''),
                    'verification_code': code,
                    'expires_at': (timezone.now() + timedelta(seconds=60)).isoformat(),
                }
                
                messages.success(request, f'A verification code has been sent to {email}. Please enter it below to complete registration.')
                form = CustomUserCreationForm()
                get_token(request)
                return render(request, 'users/register.html', {
                    'form': form,
                    'email': email,
                    'show_verification': True
                })
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')
                form = CustomUserCreationForm()
                get_token(request)
                return render(request, 'users/register.html', {'form': form})
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            get_token(request)
    else:
        form = CustomUserCreationForm()
        get_token(request)  # Ensure CSRF token is generated
    
    return render(request, 'users/register.html', {'form': form})

def send_verification_email(request):
    """AJAX endpoint to resend verification code"""
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        
        # Check if there's a pending registration
        reg_data = request.session.get('pending_registration')
        if not reg_data or reg_data.get('email') != email:
            return JsonResponse({'success': False, 'message': 'No pending registration found for this email'})
        
        # Send new verification code (expires in 60 seconds)
        code = send_verification_code(email)
        if code:
            # Update session with new code and expiry
            reg_data['verification_code'] = code
            reg_data['expires_at'] = (timezone.now() + timedelta(seconds=60)).isoformat()
            request.session['pending_registration'] = reg_data
            
            return JsonResponse({
                'success': True,
                'message': f'New verification code sent to {email}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send verification code. Please try again.'
            })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

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


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_blocked(email, ip_address, username=None):
    """Check if email, IP, or username is blocked"""
    from .models import BlockedPasswordReset
    from django.db.models import Q
    
    blocks = BlockedPasswordReset.objects.filter(
        Q(email=email) | Q(ip_address=ip_address) | Q(username=username),
        blocked_until__gt=timezone.now()
    )
    
    return blocks.exists()


def block_user(email, ip_address, username, reason):
    """Block user from password reset for 15 minutes"""
    from .models import BlockedPasswordReset
    
    BlockedPasswordReset.objects.create(
        email=email,
        ip_address=ip_address,
        username=username,
        reason=reason,
        blocked_until=timezone.now() + timedelta(minutes=15)
    )


def forgot_password(request):
    """Forgot password - send verification code"""
    from .models import PasswordResetAttempt
    import random
    from django.db import models
    
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()  # email or username
        ip_address = get_client_ip(request)
        
        if not identifier:
            messages.error(request, 'Please enter your email or username.')
            return render(request, 'users/forgot_password.html')
        
        # Find user by email or username
        user = None
        if '@' in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()
        
        if not user:
            messages.error(request, 'No account found with that email or username.')
            return render(request, 'users/forgot_password.html')
        
        # Check if blocked
        if is_blocked(user.email, ip_address, user.username):
            messages.error(request, 'Too many failed attempts. You are temporarily blocked. Please try again in 15 minutes.')
            return render(request, 'users/forgot_password.html')
        
        # Check if this is a verification code submission
        verification_code = request.POST.get('verification_code', '').strip()
        if verification_code:
            # Find the reset attempt
            reset_attempt = PasswordResetAttempt.objects.filter(
                email=user.email,
                ip_address=ip_address,
                is_used=False
            ).order_by('-created_at').first()
            
            if not reset_attempt:
                messages.error(request, 'No active password reset request found.')
                return render(request, 'users/forgot_password.html')
            
            # Check if expired
            if reset_attempt.is_expired():
                messages.error(request, 'Verification code expired. Please request a new one.')
                return render(request, 'users/forgot_password.html')
            
            # Check if too many attempts
            if reset_attempt.attempts >= 3:
                block_user(user.email, ip_address, user.username, 'Too many failed password reset attempts')
                messages.error(request, 'Too many incorrect attempts. You have been blocked for 15 minutes.')
                return render(request, 'users/forgot_password.html')
            
            # Verify code
            if verification_code != reset_attempt.reset_code:
                reset_attempt.increment_attempt()
                remaining = 3 - reset_attempt.attempts
                
                if remaining <= 0:
                    block_user(user.email, ip_address, user.username, 'Too many failed password reset attempts')
                    messages.error(request, 'Too many incorrect attempts. You have been blocked for 15 minutes.')
                else:
                    messages.error(request, f'Invalid verification code. {remaining} attempts remaining.')
                
                return render(request, 'users/forgot_password.html', {
                    'show_verification': True,
                    'email': user.email,
                    'identifier': identifier
                })
            
            # Code is correct - mark as used and redirect to reset password
            reset_attempt.is_used = True
            reset_attempt.save()
            
            # Store user ID in session for password reset
            request.session['password_reset_user_id'] = user.id
            request.session['password_reset_verified'] = True
            
            messages.success(request, 'Verification successful! Please enter your new password.')
            return redirect('users:reset_password')
        
        # Initial request - send verification code
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Create reset attempt
        PasswordResetAttempt.objects.create(
            email=user.email,
            ip_address=ip_address,
            reset_code=code,
            expires_at=timezone.now() + timedelta(seconds=60)
        )
        
        # Send email
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                subject='CTF Platform - Password Reset Code',
                message=f'Your password reset code is: {code}\n\nThis code will expire in 60 seconds.\n\nIf you did not request this, please ignore this email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print(f"\n{'='*60}")
            print(f"PASSWORD RESET CODE FOR {user.email}: {code}")
            print(f"Expires in: 60 seconds")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - PASSWORD RESET CODE FOR {user.email}: {code}")
            print(f"Expires in: 60 seconds")
            print(f"{'='*60}\n")
        
        messages.success(request, f'A verification code has been sent to {user.email}. Please enter it below.')
        return render(request, 'users/forgot_password.html', {
            'show_verification': True,
            'email': user.email,
            'identifier': identifier
        })
    
    return render(request, 'users/forgot_password.html')


def reset_password(request):
    """Reset password after verification"""
    # Check if user has verified
    if not request.session.get('password_reset_verified'):
        messages.error(request, 'Please verify your identity first.')
        return redirect('users:forgot_password')
    
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'Invalid session. Please try again.')
        return redirect('users:forgot_password')
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('users:forgot_password')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if not password1 or not password2:
            messages.error(request, 'Please enter both password fields.')
            return render(request, 'users/reset_password.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/reset_password.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'users/reset_password.html')
        
        # Set new password
        user.set_password(password1)
        user.save()
        
        # Clear session
        del request.session['password_reset_verified']
        del request.session['password_reset_user_id']
        
        messages.success(request, 'Password reset successful! You can now login with your new password.')
        return redirect('users:login')
    
    return render(request, 'users/reset_password.html', {'user': user})



@login_required
def edit_profile(request):
    """Edit user profile"""
    from .forms import ProfileEditForm
    
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        
        if form.is_valid():
            # Update user fields
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save()
            
            # Save profile
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})
