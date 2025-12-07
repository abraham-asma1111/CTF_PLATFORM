"""
WebSocket URL routing for CTF platform
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/event-status/$', consumers.EventStatusConsumer.as_asgi()),
    re_path(r'ws/leaderboard/$', consumers.LeaderboardConsumer.as_asgi()),
]
