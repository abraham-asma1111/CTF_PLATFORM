"""
WebSocket URL routing for CTF platform
"""
from django.urls import re_path
from . import consumers
from chat import consumers as chat_consumers

websocket_urlpatterns = [
    re_path(r'ws/event-status/$', consumers.EventStatusConsumer.as_asgi()),
    re_path(r'ws/leaderboard/$', consumers.LeaderboardConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<team_id>\d+)/$', chat_consumers.TeamChatConsumer.as_asgi()),
]
