# WebSocket Setup Guide

## Real-Time Features Implemented

The CTF platform now supports real-time updates via WebSockets:

✅ **LIVE Indicator** - Automatically shows/hides when event starts/ends  
✅ **Event Status** - Instant updates when admin activates/deactivates events  
✅ **Leaderboard** - Real-time score updates (ready for implementation)  
✅ **Countdown Timer** - Synchronized across all users  

## Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `channels>=4.0.0` - Django Channels for WebSocket support
- `channels-redis>=4.1.0` - Redis backend for production
- `daphne>=4.0.0` - ASGI server

### Step 2: Run Migrations (if needed)

```bash
python manage.py migrate
```

### Step 3: Run the Server

**Development (using Daphne):**
```bash
daphne -b 0.0.0.0 -p 8000 ctf_platform.asgi:application
```

**Or use Django's runserver (also supports ASGI now):**
```bash
python manage.py runserver
```

## How It Works

### WebSocket Endpoints

1. **Event Status**: `ws://localhost:8000/ws/event-status/`
   - Real-time event activation/deactivation
   - LIVE indicator updates
   - Event time changes

2. **Leaderboard**: `ws://localhost:8000/ws/leaderboard/`
   - Real-time score updates
   - Team ranking changes

### Message Flow

```
Admin activates event in Django Admin
         ↓
Admin save_model() calls broadcast_event_activated()
         ↓
WebSocket message sent to all connected clients
         ↓
JavaScript receives message and shows LIVE indicator
         ↓
All users see LIVE indicator instantly (no page refresh!)
```

## Testing WebSocket Connection

### Test 1: Check WebSocket Connection

Open browser console (F12) and you should see:
```
✅ WebSocket connected for event status
```

### Test 2: Activate Event

1. Go to Django Admin → Group Events
2. Select an event
3. Click "Activate selected event"
4. **All connected users** should see LIVE indicator appear instantly!

### Test 3: Deactivate Event

1. Go to Django Admin → Group Events
2. Select the active event
3. Click "Deactivate selected events"
4. **All connected users** should see LIVE indicator disappear instantly!

## Production Setup (Optional)

For production, use Redis as the channel layer backend:

### Step 1: Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### Step 2: Update settings.py

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### Step 3: Run with Daphne

```bash
daphne -b 0.0.0.0 -p 8000 ctf_platform.asgi:application
```

## Troubleshooting

### WebSocket Connection Failed

**Problem**: Console shows "WebSocket disconnected"

**Solutions**:
1. Make sure server is running with ASGI support (Daphne or Django 3.0+)
2. Check if port 8000 is accessible
3. Verify ASGI_APPLICATION is set in settings.py

### LIVE Indicator Not Showing

**Problem**: LIVE indicator doesn't appear

**Solutions**:
1. Check browser console for WebSocket errors
2. Verify event is active and within start/end time
3. Check if `is_group_mode_active` is True in template context

### Redis Connection Error (Production)

**Problem**: "Error connecting to Redis"

**Solutions**:
1. Make sure Redis server is running: `redis-cli ping` (should return "PONG")
2. Check Redis host/port in settings.py
3. For development, use InMemoryChannelLayer instead

## Features Ready for Enhancement

### 1. Real-Time Leaderboard Updates

When a team solves a challenge, broadcast to all users:

```python
from ctf_platform.websocket_utils import broadcast_leaderboard_update

# After successful submission
leaderboard_data = {
    'teams': [...],  # Updated leaderboard
    'last_solve': {
        'team': team.name,
        'challenge': challenge.title,
        'points': points
    }
}
broadcast_leaderboard_update(leaderboard_data)
```

### 2. Live Submission Notifications

Show toast notifications when teams solve challenges:

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    'event_status',
    {
        'type': 'challenge_solved',
        'data': {
            'team': team.name,
            'challenge': challenge.title,
            'points': points
        }
    }
)
```

### 3. Countdown Timer Sync

All users see the same countdown, synchronized via WebSocket.

## Benefits of WebSocket Implementation

✅ **Instant Updates** - No page refresh needed  
✅ **Synchronized Experience** - All users see changes at the same time  
✅ **Professional Feel** - Like real CTF platforms (CTFd, HackTheBox)  
✅ **Scalable** - Can handle many concurrent connections  
✅ **Extensible** - Easy to add more real-time features  

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run server: `python manage.py runserver` or `daphne ctf_platform.asgi:application`
3. Test WebSocket connection in browser console
4. Activate/deactivate events and watch LIVE indicator update in real-time!

Enjoy your real-time CTF platform! 🚀
