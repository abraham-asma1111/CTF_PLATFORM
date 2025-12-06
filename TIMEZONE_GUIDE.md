# CTF Platform Timezone Configuration Guide

## Overview

The CTF Platform has been configured to use **East Africa Time (EAT)** as the primary timezone for displaying times to users, while maintaining UTC storage in the database for consistency.

## Timezone Settings

- **Primary Timezone**: Africa/Nairobi (East Africa Time - EAT)
- **UTC Offset**: +03:00 (3 hours ahead of UTC)
- **Daylight Saving**: EAT does not observe daylight saving time
- **Database Storage**: All times are stored in UTC for consistency

## What This Means for Users

### 🕐 Time Display
- All times shown in the web interface are in **East Africa Time (EAT)**
- The footer displays the current time in EAT for reference
- Event schedules show start and end times in EAT

### 📅 Event Scheduling
- When creating events in the admin interface, times are entered and displayed in EAT
- The system automatically converts between UTC (database) and EAT (display)
- Event lifecycle management commands show times in EAT for better readability

### 🌍 Multi-Timezone Support
- While optimized for East Africa, the platform can be easily reconfigured for other timezones
- All timezone conversions are handled automatically by Django
- Database times remain in UTC for international compatibility

## Admin Interface

### Event Management
- **Start Time (EAT)** and **End Time (EAT)** columns show local times
- Hover over times to see the UTC equivalent
- Event status badges reflect the current EAT time

### Time Validation
- Events must be at least 1 hour long
- Start time cannot be more than 1 hour in the past (EAT)
- Overlapping events are prevented based on EAT times

## Management Commands

### Check Timezone Information
```bash
python manage.py timezone_info
```
Displays comprehensive timezone configuration and current time information.

### Event Lifecycle Management
```bash
python manage.py manage_group_event_lifecycle --status-summary
```
Shows event status with times in EAT for better readability.

## Technical Details

### Django Configuration
```python
TIME_ZONE = 'Africa/Nairobi'
USE_TZ = True
```

### Template Tags
Custom template tags are available for timezone conversion:
- `{% load timezone_tags %}`
- `{{ datetime|to_nairobi_time }}`
- `{{ datetime|format_nairobi_time }}`
- `{% current_nairobi_time %}`

### Database Storage
- All `DateTimeField` values are stored in UTC
- Django automatically handles timezone conversion
- No manual timezone conversion needed in most cases

## Benefits for East African Users

1. **Familiar Times**: All displayed times match local clocks
2. **No Confusion**: No need to calculate timezone differences
3. **Event Planning**: Easy to schedule events for local participants
4. **Consistent Experience**: All platform times use the same timezone

## Changing Timezone (If Needed)

To change the timezone for a different region:

1. Update `settings.py`:
   ```python
   TIME_ZONE = 'Your/Timezone'  # e.g., 'Europe/London', 'America/New_York'
   ```

2. Update template tags in `ctf_platform/templatetags/timezone_tags.py`

3. Update admin display methods in `challenges/admin.py`

4. Restart the Django application

## Troubleshooting

### Common Issues

**Times appear incorrect:**
- Check that `USE_TZ = True` in settings
- Verify the timezone is set to `Africa/Nairobi`
- Run `python manage.py timezone_info` to verify configuration

**Event scheduling problems:**
- Ensure times are entered in EAT (local time)
- Check for timezone-aware datetime objects
- Verify event validation logic accounts for EAT

**Admin interface shows wrong times:**
- Clear browser cache
- Check admin timezone display methods
- Verify template tag imports

### Getting Help

Run the timezone info command for diagnostic information:
```bash
python manage.py timezone_info
```

This will show:
- Current timezone configuration
- Time conversion examples
- Event timing information
- Best practices reminder

## Best Practices

1. **Always use timezone-aware datetimes** when working with the Django ORM
2. **Let Django handle conversions** - don't manually convert timezones
3. **Test event scheduling** with the lifecycle management commands
4. **Communicate timezone clearly** to users (EAT is shown in the footer)
5. **Use the timezone_info command** to verify configuration after changes

---

*This configuration optimizes the CTF platform for East African users while maintaining international compatibility through UTC database storage.*