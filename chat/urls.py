from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('team/<int:team_id>/', views.team_chat, name='team_chat'),
    path('team/<int:team_id>/send/', views.send_message, name='send_message'),
    path('team/<int:team_id>/messages/', views.get_messages, name='get_messages'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('notifications/', views.chat_notifications, name='notifications'),
]