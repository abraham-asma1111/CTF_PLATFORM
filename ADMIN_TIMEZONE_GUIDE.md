# Admin Timezone Guide

## Understanding Timezones in the CTF Platform

The platform is configured to use **East Africa Time (EAT)** which is **UTC+3**.

### Current Time Display

- **Your local time**: 1:28 PM (13:28 in 24-hour format)
- **Django admin shows**: 13:28:35 (24-hour format in EAT)
- **These are the SAME time!**

The Django admin uses 24-hour format (military time), so:
- 1:00 PM = 13:00
- 2:00 PM = 14:00
- 3:00 PM = 15:00
- etc.

## Creating Timed Events

### When Creating a Group Event

1. Go to Django Admin → Group Events → Add Group Event
2. Enter times in **24-hour format** in **EAT timezone**

### Example: 2-Hour Event Starting at 2:00 PM Today

If you want an event to:
- **Start**: Today at 2:00 PM (EAT)
- **End**: Today at 4:00 PM (EAT)

Enter in the admin:
- **Start time**: `2024-12-07 14:00:00` (14:00 = 2:00 PM)
- **End time**: `2024-12-07 16:00:00` (16:00 = 4:00 PM)

### Time Conversion Reference

| 12-Hour (AM/PM) | 24-Hour | Notes |
|-----------------|---------|-------|
| 12:00 AM | 00:00 | Midnight |
| 1:00 AM | 01:00 | |
| 2:00 AM | 02:00 | |
| 6:00 AM | 06:00 | |
| 9:00 AM | 09:00 | |
| 12:00 PM | 12:00 | Noon |
| 1:00 PM | 13:00 | |
| 2:00 PM | 14:00 | |
| 3:00 PM | 15:00 | |
| 4:00 PM | 16:00 | |
| 5:00 PM | 17:00 | |
| 6:00 PM | 18:00 | |
| 9:00 PM | 21:00 | |
| 11:00 PM | 23:00 | |

### Quick Conversion Formula

To convert PM times to 24-hour:
- **Add 12 to the hour** (except for 12:00 PM which stays as 12:00)
- Examples:
  - 1:00 PM → 1 + 12 = 13:00
  - 2:30 PM → 2 + 12 = 14:30
  - 5:45 PM → 5 + 12 = 17:45

## Verifying Event Times

### In Django Admin

When you view the Group Events list, you'll see:
- **Start Time (EAT)**: Shows the time in EAT with tooltip showing UTC
- **End Time (EAT)**: Shows the time in EAT with tooltip showing UTC

Hover over the times to see both EAT and UTC versions.

### On the Frontend

Users will see:
- Countdown timer showing time remaining
- Event dates displayed as: `2024-12-07 14:00 EAT`

## Creating Events via Django Shell

If you prefer using the Django shell:

```python
from challenges.models import GroupEvent
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

# Get admin user
admin = User.objects.filter(is_superuser=True).first()

# Get Nairobi timezone
nairobi_tz = pytz.timezone('Africa/Nairobi')

# Create event starting at 2:00 PM EAT today
start_time = nairobi_tz.localize(datetime(2024, 12, 7, 14, 0, 0))  # 2:00 PM
end_time = nairobi_tz.localize(datetime(2024, 12, 7, 16, 0, 0))    # 4:00 PM

event = GroupEvent.objects.create(
    name="Afternoon CTF Challenge",
    description="2-hour intensive competition",
    start_time=start_time,
    end_time=end_time,
    is_active=True,
    created_by=admin,
    point_multiplier=1.5
)

print(f"Event created!")
print(f"Start: {event.start_time.astimezone(nairobi_tz).strftime('%Y-%m-%d %I:%M %p EAT')}")
print(f"End: {event.end_time.astimezone(nairobi_tz).strftime('%Y-%m-%d %I:%M %p EAT')}")
```

### Alternative: Using Relative Times

```python
from django.utils import timezone
from datetime import timedelta

# Start event now
start_time = timezone.now()

# End event in 2 hours
end_time = start_time + timedelta(hours=2)

event = GroupEvent.objects.create(
    name="Quick Challenge",
    description="Starting now, 2 hours duration",
    start_time=start_time,
    end_time=end_time,
    is_active=True,
    created_by=admin
)
```

## Common Event Durations

### 30 Minutes
```python
end_time = start_time + timedelta(minutes=30)
```

### 1 Hour
```python
end_time = start_time + timedelta(hours=1)
```

### 2 Hours
```python
end_time = start_time + timedelta(hours=2)
```

### 4 Hours
```python
end_time = start_time + timedelta(hours=4)
```

### Full Day (24 hours)
```python
end_time = start_time + timedelta(days=1)
```

### Weekend Event (48 hours)
```python
end_time = start_time + timedelta(days=2)
```

## Checking Current Time

### Via Django Shell
```python
from django.utils import timezone
import pytz

# Get current time
now = timezone.now()
print(f"UTC: {now}")

# Convert to EAT
nairobi_tz = pytz.timezone('Africa/Nairobi')
eat_time = now.astimezone(nairobi_tz)
print(f"EAT: {eat_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"EAT (12-hour): {eat_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
```

### Via Management Command
```bash
python manage.py shell -c "from django.utils import timezone; import pytz; now = timezone.now(); eat = now.astimezone(pytz.timezone('Africa/Nairobi')); print(f'Current time: {eat.strftime(\"%Y-%m-%d %I:%M %p EAT\")}')"
```

## Troubleshooting

### "Event shows wrong time"

1. Check your Django settings:
   ```python
   TIME_ZONE = 'Africa/Nairobi'  # Should be set
   USE_TZ = True  # Should be True
   ```

2. Verify the event times in Django shell:
   ```python
   from challenges.models import GroupEvent
   import pytz
   
   event = GroupEvent.objects.get(name="Your Event Name")
   nairobi_tz = pytz.timezone('Africa/Nairobi')
   
   print(f"Start (EAT): {event.start_time.astimezone(nairobi_tz)}")
   print(f"End (EAT): {event.end_time.astimezone(nairobi_tz)}")
   ```

### "Countdown timer shows wrong time"

The countdown timer uses JavaScript which automatically uses the user's browser timezone. The times are converted correctly on the backend.

### "Admin form shows confusing times"

The Django admin datetime widget shows times in the configured timezone (EAT). When you enter a time, enter it in EAT (24-hour format).

## Best Practices

1. **Always use 24-hour format** in the admin to avoid AM/PM confusion
2. **Test events** with short durations first (e.g., 5 minutes) to verify timing
3. **Check the countdown timer** on the frontend after creating an event
4. **Use the lifecycle management command** to verify event status:
   ```bash
   python manage.py manage_group_event_lifecycle --status-summary
   ```

## Quick Reference

**Current timezone**: East Africa Time (EAT) = UTC+3

**Time format in admin**: 24-hour (HH:MM:SS)

**Example event times**:
- Morning event: 09:00 - 11:00 (9 AM - 11 AM)
- Afternoon event: 14:00 - 16:00 (2 PM - 4 PM)
- Evening event: 18:00 - 20:00 (6 PM - 8 PM)
- Night event: 21:00 - 23:00 (9 PM - 11 PM)
