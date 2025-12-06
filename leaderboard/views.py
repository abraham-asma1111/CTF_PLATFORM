from django.shortcuts import render
from django.http import JsonResponse
from users.models import UserProfile
from challenges.group_challenge_manager import GroupChallengeManager, GroupScoring

def leaderboard(request):
    """Display the leaderboard"""
    top_users = UserProfile.objects.filter(
        total_score__gt=0
    ).select_related('user').order_by('-total_score', 'last_submission')[:50]
    
    # Check if group mode is active for group leaderboard
    is_group_mode = GroupChallengeManager.is_group_mode_active()
    group_leaderboard = []
    
    if is_group_mode:
        group_leaderboard = GroupScoring.get_group_leaderboard()[:20]
    
    context = {
        'top_users': top_users,
        'is_group_mode': is_group_mode,
        'group_leaderboard': group_leaderboard,
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

def group_leaderboard_api(request):
    """API endpoint for group event leaderboard updates"""
    if not GroupChallengeManager.is_group_mode_active():
        return JsonResponse({'error': 'Group mode not active'}, status=400)
    
    group_leaderboard = GroupScoring.get_group_leaderboard()[:20]
    
    data = []
    for i, team_data in enumerate(group_leaderboard, 1):
        data.append({
            'rank': i,
            'team_name': team_data['team'].name,
            'captain': team_data['team'].captain.username,
            'score': team_data['event_score'],
            'challenges_solved': team_data['event_challenges_solved'],
            'last_submission': team_data['last_submission'].isoformat() if team_data['last_submission'] else None,
            'member_count': team_data['team'].member_count(),
        })
    
    return JsonResponse({'group_leaderboard': data})
