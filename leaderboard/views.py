from django.shortcuts import render
from django.http import JsonResponse
from users.models import UserProfile

def leaderboard(request):
    """Display the leaderboard"""
    top_users = UserProfile.objects.filter(
        total_score__gt=0
    ).select_related('user').order_by('-total_score', 'last_submission')[:50]
    
    context = {
        'top_users': top_users,
    }
    return render(request, 'leaderboard/leaderboard.html', context)

def leaderboard_api(request):
    """API endpoint for live leaderboard updates"""
    top_users = UserProfile.objects.filter(
        total_score__gt=0
    ).select_related('user').order_by('-total_score', 'last_submission')[:20]
    
    data = []
    for i, profile in enumerate(top_users, 1):
        data.append({
            'rank': i,
            'username': profile.user.username,
            'score': profile.total_score,
            'challenges_solved': profile.challenges_solved,
        })
    
    return JsonResponse({'leaderboard': data})
