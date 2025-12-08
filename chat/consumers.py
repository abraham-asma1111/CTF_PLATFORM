"""
WebSocket consumer for real-time team chat
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class TeamChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for team chat
    Handles real-time messaging, typing indicators, and read receipts
    """
    
    async def connect(self):
        """Accept WebSocket connection and join team chat room"""
        self.team_id = self.scope['url_route']['kwargs']['team_id']
        self.room_group_name = f'team_chat_{self.team_id}'
        self.user = self.scope['user']
        
        # Join team chat group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send recent messages
        messages = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'message_history',
            'messages': messages
        }))
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        """Leave team chat room on disconnect"""
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'username': self.user.username
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            # Save message to database
            message = await self.save_message(data.get('message'))
            
            # Broadcast to team
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message['id'],
                        'content': message['content'],
                        'sender': message['sender'],
                        'timestamp': message['timestamp'],
                    }
                }
            )
        
        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', True)
                }
            )
        
        elif message_type == 'mark_read':
            # Mark message as read
            message_id = data.get('message_id')
            await self.mark_message_read(message_id)
        
        elif message_type == 'add_reaction':
            # Add emoji reaction
            message_id = data.get('message_id')
            emoji = data.get('emoji')
            await self.add_reaction(message_id, emoji)
            
            # Broadcast reaction
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'emoji': emoji,
                    'username': self.user.username
                }
            )
    
    async def chat_message(self, event):
        """Receive chat message from group broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Receive typing indicator from group broadcast"""
        # Don't send typing indicator to the user who is typing
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def user_joined(self, event):
        """Receive user joined notification"""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'username': event['username']
            }))
    
    async def user_left(self, event):
        """Receive user left notification"""
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'username': event['username']
            }))
    
    async def message_reaction(self, event):
        """Receive message reaction from group broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'username': event['username']
        }))
    
    @database_sync_to_async
    def get_recent_messages(self):
        """Get recent messages from database"""
        from chat.models import TeamMessage
        
        messages = TeamMessage.objects.filter(
            team_id=self.team_id
        ).select_related('sender').prefetch_related('reactions__user').order_by('-timestamp')[:50]
        
        return [
            {
                'id': msg.id,
                'content': msg.content,
                'sender': msg.sender.username,
                'timestamp': msg.timestamp.isoformat(),
                'is_edited': msg.is_edited,
                'reactions': [
                    {
                        'emoji': reaction.emoji,
                        'username': reaction.user.username
                    }
                    for reaction in msg.reactions.all()
                ]
            }
            for msg in reversed(messages)
        ]
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        from chat.models import TeamMessage
        from teams.models import Team
        
        team = Team.objects.get(id=self.team_id)
        message = TeamMessage.objects.create(
            team=team,
            sender=self.user,
            content=content,
            message_type='text'
        )
        
        return {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'timestamp': message.timestamp.isoformat(),
        }
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        from chat.models import MessageRead, TeamMessage
        
        try:
            message = TeamMessage.objects.get(id=message_id)
            MessageRead.objects.get_or_create(
                message=message,
                user=self.user
            )
        except TeamMessage.DoesNotExist:
            pass
    
    @database_sync_to_async
    def add_reaction(self, message_id, emoji):
        """Add emoji reaction to message"""
        from chat.models import MessageReaction, TeamMessage
        
        try:
            message = TeamMessage.objects.get(id=message_id)
            MessageReaction.objects.get_or_create(
                message=message,
                user=self.user,
                emoji=emoji
            )
        except TeamMessage.DoesNotExist:
            pass
