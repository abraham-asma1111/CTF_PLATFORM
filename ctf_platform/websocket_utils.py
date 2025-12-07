"""
Utility functions for broadcasting WebSocket messages
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_event_status(event_data):
    """
    Broadcast event status update to all connected clients
    
    Args:
        event_data: Dictionary containing event status information
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'event_status',
        {
            'type': 'event_status_update',
            'data': event_data
        }
    )


def broadcast_event_activated(event):
    """
    Broadcast event activation to all connected clients
    
    Args:
        event: GroupEvent instance that was activated
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'event_status',
        {
            'type': 'event_activated',
            'data': {
                'event_id': event.id,
                'event_name': event.name,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
            }
        }
    )


def broadcast_event_deactivated():
    """Broadcast event deactivation to all connected clients"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'event_status',
        {
            'type': 'event_deactivated',
            'data': {}
        }
    )


def broadcast_leaderboard_update(leaderboard_data):
    """
    Broadcast leaderboard update to all connected clients
    
    Args:
        leaderboard_data: Dictionary containing leaderboard information
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'leaderboard',
        {
            'type': 'leaderboard_update',
            'data': leaderboard_data
        }
    )
