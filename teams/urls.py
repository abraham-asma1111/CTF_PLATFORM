from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.create_team, name='create_team'),
    path('my-team/', views.my_team, name='my_team'),
    path('my-invitations/', views.my_invitations, name='my_invitations'),
    path('leaderboard/', views.team_leaderboard, name='team_leaderboard'),
    path('<int:team_id>/', views.team_detail, name='team_detail'),
    path('<int:team_id>/manage/', views.team_management, name='team_management'),
    path('<int:team_id>/join/', views.join_team, name='join_team'),
    path('<int:team_id>/invite/', views.send_invitation, name='send_invitation'),
    path('<int:team_id>/transfer-captaincy/', views.transfer_captaincy, name='transfer_captaincy'),
    path('membership/<int:membership_id>/approve/', views.approve_member, name='approve_member'),
    path('membership/<int:membership_id>/reject/', views.reject_member, name='reject_member'),
    path('membership/<int:membership_id>/remove/', views.remove_member, name='remove_member'),
    path('invitation/<int:invitation_id>/accept/', views.accept_invitation, name='accept_invitation'),
    path('invitation/<int:invitation_id>/decline/', views.decline_invitation, name='decline_invitation'),
    path('invitation/<int:invitation_id>/cancel/', views.cancel_invitation, name='cancel_invitation'),
    path('cancel-request/', views.cancel_join_request, name='cancel_join_request'),
    path('leave/', views.leave_team, name='leave_team'),
    path('group-challenges/', views.group_challenges, name='group_challenges'),
    path('group-challenges/<int:challenge_id>/submit/', views.submit_group_flag, name='submit_group_flag'),
]
