# Event Management Workflow

## Complete Step-by-Step Guide for Managing CTF Events

### Scenario: You Want to Run a 2-Hour Competition

## Phase 1: Preparation (Before Competition Day)

### Step 1: Create the Event (Inactive)

```bash
python manage.py shell
```

```python
from challenges.models import GroupEvent, GroupChallenge
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

# Get admin user
admin = User.objects.filter(is_superuser=True).first()
nairobi_tz = pytz.timezone('Africa/Nairobi')

# Set event for specific date/time (e.g., Saturday at 2 PM)
start_time = nairobi_tz.localize(datetime(2024, 12, 14, 14, 0, 0))  # Dec 14, 2 PM
end_time = nairobi_tz.localize(datetime(2024, 12, 14, 16, 0, 0))    # Dec 14, 4 PM

event = GroupEvent.objects.create(
    name="Saturday CTF Challenge",
    description="2-hour intensive competition with 8 challenges",
    start_time=start_time,
    end_time=end_time,
    is_active=False,  # Keep inactive during preparation
    created_by=admin,
    point_multiplier=1.5,
    max_teams=20
)

print(f"✅ Event created: {event.name}")
print(f"📅 Start: {start_time.strftime('%Y-%m-%d %I:%M %p EAT')}")
print(f"📅 End: {end_time.strftime('%Y-%m-%d %I:%M %p EAT')}")
```

### Step 2: Add Challenges to the Event

```python
# Add 8 challenges
challenges_data = [
    {"title": "Web Exploit 1", "category": "web", "difficulty": "easy", "points": 100, "flag": "CTF{web_basic}"},
    {"title": "Crypto Challenge", "category": "crypto", "difficulty": "medium", "points": 200, "flag": "CTF{crypto_medium}"},
    {"title": "Forensics Hunt", "category": "forensics", "difficulty": "easy", "points": 150, "flag": "CTF{forensics_easy}"},
    {"title": "Binary Pwn", "category": "pwn", "difficulty": "hard", "points": 300, "flag": "CTF{pwn_hard}"},
    {"title": "Reverse Engineering", "category": "reverse", "difficulty": "medium", "points": 250, "flag": "CTF{reverse_medium}"},
    {"title": "Web Exploit 2", "category": "web", "difficulty": "hard", "points": 350, "flag": "CTF{web_advanced}"},
    {"title": "Crypto Advanced", "category": "crypto", "difficulty": "hard", "points": 400, "flag": "CTF{crypto_hard}"},
    {"title": "Misc Challenge", "category": "misc", "difficulty": "medium", "points": 200, "flag": "CTF{misc_fun}"},
]

for challenge_data in challenges_data:
    GroupChallenge.objects.create(
        event=event,
        title=challenge_data["title"],
        description=f"Solve this {challenge_data['category']} challenge!",
        category=challenge_data["category"],
        difficulty=challenge_data["difficulty"],
        points=challenge_data["points"],
        flag=challenge_data["flag"],  # Will be auto-hashed
        requires_collaboration=True,
        max_attempts_per_team=10
    )
    print(f"✅ Added: {challenge_data['title']}")

print(f"\n🎯 Total challenges added: {GroupChallenge.objects.filter(event=event).count()}")
```

### Step 3: Verify Event Setup

```python
# Check event details
print(f"\n📋 Event Summary:")
print(f"Name: {event.name}")
print(f"Challenges: {GroupChallenge.objects.filter(event=event).count()}")
print(f"Status: {'Active' if event.is_active else 'Inactive'}")
print(f"Start: {event.start_time.astimezone(nairobi_tz).strftime('%Y-%m-%d %I:%M %p EAT')}")
print(f"End: {event.end_time.astimezone(nairobi_tz).strftime('%Y-%m-%d %I:%M %p EAT')}")
```

## Phase 2: Competition Day - Before Start Time

### Option A: Activate Early (Teams See Countdown)

If you want teams to see the event and countdown before it starts:

**Via Django Admin:**
1. Go to http://127.0.0.1:8000/admin/challenges/groupevent/
2. Select your event
3. Click "Activate selected event (group mode)"
4. Teams will see: "Event Starts In: XX:XX:XX" (submissions blocked)

**Via Shell:**
```python
from challenges.models import GroupEvent
from challenges.group_challenge_manager import GroupChallengeManager
from django.contrib.auth.models import User

event = GroupEvent.objects.get(name="Saturday CTF Challenge")
admin = User.objects.filter(is_superuser=True).first()

result = GroupChallengeManager.activate_event(event, admin)
print(result['message'])
```

### Option B: Activate at Start Time

Keep the event inactive until the exact start time, then activate it.

## Phase 3: During Competition (Between Start and End Time)

### The Event is Now Live

Once current time passes the start_time:
- ✅ Timer shows "Event Time Remaining"
- ✅ Teams can submit flags
- ✅ Leaderboard updates in real-time
- ✅ Countdown shows time until end_time

### Monitor the Competition

```bash
# Check event status
python manage.py manage_group_event_lifecycle --status-summary

# View leaderboard
python manage.py shell
```

```python
from challenges.group_challenge_manager import GroupScoring

leaderboard = GroupScoring.get_group_leaderboard()
for i, team_data in enumerate(leaderboard, 1):
    print(f"{i}. {team_data['team'].name} - {team_data['event_score']} points")
```

## Phase 4: Competition Ends (After End Time)

### Automatic Behavior

When current time passes end_time:
- 🔒 Timer shows "TIME'S UP!"
- 🔒 All submit buttons disabled
- 🔒 Backend rejects any submissions
- 📊 Teams can only view leaderboard

### Deactivate the Event

```python
from challenges.models import GroupEvent
from challenges.group_challenge_manager import GroupChallengeManager
from django.contrib.auth.models import User

event = GroupEvent.objects.get(name="Saturday CTF Challenge")
admin = User.objects.filter(is_superuser=True).first()

result = GroupChallengeManager.deactivate_event(event, admin)
print(result['message'])
```

Or via Django Admin:
1. Go to Group Events
2. Select the event
3. Click "Deactivate selected events"

### Preserve Results

```bash
python manage.py manage_group_event_lifecycle --preserve-event <event_id>
```

## Quick Start: Event Starting NOW

If you want to start an event immediately:

```python
from challenges.models import GroupEvent
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

admin = User.objects.filter(is_superuser=True).first()

# Start NOW, end in 2 hours
event = GroupEvent.objects.create(
    name="Quick Challenge",
    description="Starting now!",
    start_time=timezone.now(),
    end_time=timezone.now() + timedelta(hours=2),
    is_active=True,  # Activate immediately
    created_by=admin
)

# Add challenges...
# (use the challenges_data loop from above)

print("🚀 Event is LIVE!")
```

## Important Notes

### The Timer is Based on start_time and end_time

- **NOT** based on when you activate/deactivate
- **NOT** based on the is_active flag
- **ONLY** based on the actual datetime values

### Example Timeline

```
Event: start_time = 2:00 PM, end_time = 4:00 PM

1:00 PM - Event inactive → Teams can't see it
1:30 PM - You activate event → Teams see "Event Starts In: 30m"
2:00 PM - Start time reached → Timer shows "Time Remaining: 2h", submissions allowed
3:00 PM - Still running → Timer shows "Time Remaining: 1h"
4:00 PM - End time reached → Timer shows "TIME'S UP!", submissions blocked
4:30 PM - You deactivate event → Event hidden from teams
```

### Best Practice Workflow

1. **Create event** with future start/end times (keep inactive)
2. **Add all challenges** while inactive
3. **Test everything** (verify times, challenges, etc.)
4. **Activate event** 10-15 minutes before start_time (teams see countdown)
5. **Let it run** - timer and blocking happen automatically
6. **Deactivate after** end_time when you're ready to hide it

## Troubleshooting

### "Timer is counting down but I haven't activated the event"

The timer is based on end_time, not activation status. If you don't want the timer to count yet, set start_time and end_time to future dates.

### "I want to pause the event"

You can't pause an event, but you can:
1. Deactivate it (hides from teams)
2. Create a new event with adjusted times

### "I want to extend the event"

```python
from challenges.models import GroupEvent
from datetime import timedelta

event = GroupEvent.objects.get(name="Your Event")
event.end_time = event.end_time + timedelta(hours=1)  # Add 1 hour
event.save()
print(f"Event extended to: {event.end_time}")
```

## Summary

**Key Concept**: The timer and submission blocking are controlled by **start_time** and **end_time**, not by the **is_active** flag.

- **is_active** = Whether the event is visible/active on the platform
- **start_time/end_time** = When submissions are actually allowed

Set your times correctly when creating the event, and the system handles everything automatically!
