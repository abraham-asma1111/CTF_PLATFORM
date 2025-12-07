# Event Timer & Time-Based Submission Blocking

## Overview

The CTF platform now includes a **real-time countdown timer** and **automatic submission blocking** for group events. When an event's time expires, teams can no longer submit flags - they can only view the leaderboard and final results.

## Features

### 1. Real-Time Countdown Timer
- Displays hours, minutes, and seconds remaining
- Updates every second
- Visual indicators:
  - **Green** (🏆): Event is active, plenty of time
  - **Red** (⚠️): Less than 10 minutes remaining
  - **Locked** (🔒): Event has ended

### 2. Automatic Submission Blocking

#### Before Event Starts
- Timer shows "Event Starts In" with countdown
- All submit buttons are disabled
- Message: "Event has not started yet"

#### During Event
- Timer shows "Event Time Remaining"
- Submit buttons are enabled
- Teams can solve challenges normally

#### After Event Ends
- Timer shows "TIME'S UP!"
- All submit buttons are automatically disabled
- Submission attempts show: "Event has ended. Check the leaderboard for final results!"
- Backend also validates and rejects submissions

### 3. Backend Validation

The system validates submissions at multiple levels:

```python
# In GroupChallengeManager.submit_solution()
current_time = timezone.now()

# Check if event has expired
if current_time > challenge.event.end_time:
    return {
        'success': False,
        'message': 'Event has ended. Submissions are no longer accepted.'
    }

# Check if event hasn't started
if current_time < challenge.event.start_time:
    return {
        'success': False,
        'message': 'Event has not started yet.'
    }
```

## Admin Workflow

### Creating a Timed Event

1. **Create Group Event** (Django Admin or Management Command)
   ```bash
   python manage.py shell
   ```
   
   ```python
   from challenges.models import GroupEvent
   from django.contrib.auth.models import User
   from django.utils import timezone
   from datetime import timedelta
   
   admin = User.objects.filter(is_superuser=True).first()
   
   # Create 2-hour event starting now
   event = GroupEvent.objects.create(
       name="Cyber Challenge 2024",
       description="2-hour intensive CTF competition",
       start_time=timezone.now(),
       end_time=timezone.now() + timedelta(hours=2),
       is_active=True,
       created_by=admin,
       point_multiplier=1.5
   )
   ```

2. **Add Challenges to Event**
   ```python
   from challenges.models import GroupChallenge
   
   GroupChallenge.objects.create(
       event=event,
       title="Web Exploitation 101",
       description="Find the hidden flag in the web application",
       points=100,
       flag="CTF{example_flag}",  # Will be auto-hashed
       category="web",
       difficulty="easy"
   )
   ```

3. **Activate Event**
   ```python
   from challenges.group_challenge_manager import GroupChallengeManager
   
   result = GroupChallengeManager.activate_event(event, admin)
   print(result['message'])
   ```

### Event Duration Examples

```python
from datetime import timedelta

# 1 hour event
end_time = start_time + timedelta(hours=1)

# 2 hour event
end_time = start_time + timedelta(hours=2)

# 30 minute event
end_time = start_time + timedelta(minutes=30)

# 4 hour event
end_time = start_time + timedelta(hours=4)

# Full day event
end_time = start_time + timedelta(days=1)
```

## User Experience

### Active Event
```
⏱️ Event Time Remaining
   01h : 45m : 23s
   Start: 2024-12-07 14:00 • End: 2024-12-07 16:00
```

### Last 10 Minutes (Warning)
```
⚠️ Event Time Remaining
   00h : 08m : 45s  (in red)
   Start: 2024-12-07 14:00 • End: 2024-12-07 16:00
```

### Event Ended
```
🔒 Event Has Ended
   TIME'S UP!
   Start: 2024-12-07 14:00 • End: 2024-12-07 16:00
```

## Technical Implementation

### Frontend (JavaScript)
- Countdown updates every second
- Compares current time with event end time
- Automatically disables submit buttons when time expires
- Shows appropriate messages based on event status

### Backend (Python/Django)
- Validates submission time against event start/end times
- Returns error messages for out-of-time submissions
- Prevents database writes for invalid submissions

### Security
- Client-side blocking for UX (instant feedback)
- Server-side validation for security (prevents tampering)
- Timezone-aware using Django's timezone utilities

## Testing

### Test Event Expiration

```bash
python manage.py shell
```

```python
from challenges.models import GroupEvent, GroupChallenge
from teams.models import Team
from django.contrib.auth.models import User
from challenges.group_challenge_manager import GroupChallengeManager
from django.utils import timezone
from datetime import timedelta

# Create expired event
admin = User.objects.filter(is_superuser=True).first()
expired_event = GroupEvent.objects.create(
    name="Test Expired Event",
    description="This event has already ended",
    start_time=timezone.now() - timedelta(hours=3),
    end_time=timezone.now() - timedelta(hours=1),  # Ended 1 hour ago
    is_active=False,
    created_by=admin
)

# Add challenge
challenge = GroupChallenge.objects.create(
    event=expired_event,
    title="Test Challenge",
    description="Test",
    points=100,
    flag="test_flag",
    category="test",
    difficulty="easy"
)

# Try to submit (should fail)
team = Team.objects.first()
user = team.captain
result = GroupChallengeManager.submit_solution(team, challenge, user, "test_flag")
print(result)
# Output: {'success': False, 'message': 'Event has ended. Submissions are no longer accepted.'}
```

## Benefits

1. **Fair Competition**: Everyone has the same time limit
2. **Clear Deadlines**: Visual countdown creates urgency
3. **Automatic Enforcement**: No manual intervention needed
4. **Professional Experience**: Similar to real CTF competitions
5. **Prevents Late Submissions**: Ensures integrity of rankings

## Future Enhancements

- WebSocket integration for real-time updates across all clients
- Email notifications when event is about to end (10 min warning)
- Automatic leaderboard freeze when time expires
- Event history and replay functionality
- Multiple concurrent events support
