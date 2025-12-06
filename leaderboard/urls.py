from django.urls import path
from . import views

app_name = 'leaderboard'

urlpatterns = [
    path('', views.leaderboard, name='leaderboard'),
    path('api/', views.leaderboard_api, name='api'),
    path('group-api/', views.group_leaderboard_api, name='group_api'),
]