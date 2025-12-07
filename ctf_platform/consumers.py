"""
WebSocket consumers for real-time CTF platform updates
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class EventStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time event status updates
    Handles LIVE indicator, countdown timer, and event state changes
    """
    
    async def connect(self):
        """Accept WebSocket connection and join event status group"""
        self.group_name = 'event_status'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial event status
        event_status = await self.get_event_status()
        await self.send(text_data=json.dumps({
            'type': 'event_status',
            'data': event_status
        }))
    
    async def disconnect(self, close_code):
        """Leave event status group on disconnect"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_status':
            # Client requesting current event status
            event_status = await self.get_event_status()
            await self.send(text_data=json.dumps({
                'type': 'event_status',
                'data': event_status
            }))
    
    async def event_status_update(self, event):
        """
        Receive event status update from group broadcast
        Send to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'event_status',
            'data': event['data']
        }))
    
    async def event_activated(self, event):
        """Handle event activation broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'event_activated',
            'data': event['data']
        }))
    
    async def event_deactivated(self, event):
        """Handle event deactivation broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'event_deactivated',
            'data': event['data']
        }))
    
    async def event_time_update(self, event):
        """Handle event time update broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'event_time_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_event_status(self):
        """Get current event status from database"""
        from challenges.group_challenge_manager import GroupChallengeManager
        from challenges.models import GroupEvent, PlatformMode
        
        try:
            # Check if group mode is active
            platform_mode = PlatformMode.objects.filter(mode='group').first()
            if not platform_mode or not platform_mode.active_event:
                return {
                    'is_active': False,
                    'event': None
                }
            
            event = platform_mode.active_event
            current_time = timezone.now()
            
            # Determine if event is live (between start and end time)
            is_live = event.start_time <= current_time <= event.end_time
            
            # Calculate time remaining
            if current_time < event.start_time:
                time_status = 'upcoming'
                time_diff = (event.start_time - current_time).total_seconds()
            elif current_time > event.end_time:
                time_status = 'ended'
                time_diff = 0
            else:
                time_status = 'active'
                time_diff = (event.end_time - current_time).total_seconds()
            
            return {
                'is_active': True,
                'is_live': is_live,
                'event': {
                    'id': event.id,
                    'name': event.name,
                    'description': event.description,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'time_status': time_status,
                    'time_remaining': int(time_diff),
                }
            }
        except Exception as e:
            return {
                'is_active': False,
                'event': None,
                'error': str(e)
            }


class LeaderboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time leaderboard updates
    """
    
    async def connect(self):
        """Accept WebSocket connection and join leaderboard group"""
        self.group_name = 'leaderboard'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial leaderboard data
        leaderboard_data = await self.get_leaderboard()
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'data': leaderboard_data
        }))
    
    async def disconnect(self, close_code):
        """Leave leaderboard group on disconnect"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def leaderboard_update(self, event):
        """Receive leaderboard update from group broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_leaderboard(self):
        """Get current leaderboard from database"""
        from challenges.group_challenge_manager import GroupScoring
        
        try:
            leaderboard = GroupScoring.get_group_leaderboard()
            
            return {
                'teams': [
                    {
                        'rank': idx + 1,
                        'team_name': team_data['team'].name,
                        'score': team_data['event_score'],
                        'challenges_solved': team_data['event_challenges_solved'],
                    }
                    for idx, team_data in enumerate(leaderboard)
                ]
            }
        except Exception as e:
            return {
                'teams': [],
                'error': str(e)
            }
