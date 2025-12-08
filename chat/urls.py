"""
Chat URL Configuration
"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('<int:team_id>/', views.team_chat, name='team_chat'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
]
