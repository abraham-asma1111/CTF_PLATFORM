import base64
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Challenge

# Secret key for JWT (intentionally weak for the challenge)
JWT_SECRET = "super_secret_key_123"

def jwt_challenge_home(request, challenge_id):
    """
    JWT Challenge - Home page
    Users start here and need to discover the hidden flag
    """
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    context = {
        'challenge': challenge,
        'challenge_id': challenge_id,
    }
    return render(request, 'challenges/jwt_home.html', context)


def jwt_challenge_redirect(request, challenge_id):
    """
    Redirect page that sets the flag in a cookie (base64 encoded)
    """
    # Get the challenge from database to use the actual flag
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # The flag in the database is hashed, but we need the plain text flag
    # For this challenge, we'll use the flag you entered: 
    # CTF{jwt_cracking_learns-you_how crypthography ....works!_1253@788Gh!@@90--!&*#00}
    # Note: In production, you'd store the plain flag separately or retrieve it differently
    flag = "CTF{jwt_cracking_learns-you_how crypthography ....works!_1253@788Gh!@@90--!&*#00}"
    
    # Encode the flag in base64
    encoded_flag = base64.b64encode(flag.encode()).decode()
    
    # Create response
    response = render(request, 'challenges/jwt_secret.html', {
        'challenge_id': challenge_id,
        'message': 'Welcome to the secret area! Can you find the flag?'
    })
    
    # Set the encoded flag as a cookie
    response.set_cookie(
        'secret_data',
        encoded_flag,
        max_age=3600,  # 1 hour
        httponly=False  # Allow JavaScript access for easier discovery
    )
    
    # Also set it in localStorage via JavaScript in the template
    return response


def jwt_challenge_verify(request):
    """
    Verify the submitted flag
    """
    if request.method == 'POST':
        submitted_flag = request.POST.get('flag', '').strip()
        correct_flag = "CTF{jwt_cracking_learns-you_how crypthography ....works!_1253@788Gh!@@90--!&*#00}"
        
        if submitted_flag == correct_flag:
            return HttpResponse("Correct! Well done!")
        else:
            return HttpResponse("Incorrect flag. Keep looking!")
    
    return redirect('jwt_challenge_home')
