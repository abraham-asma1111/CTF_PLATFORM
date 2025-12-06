"""
Template tags for timezone handling
"""
from django import template
from django.utils import timezone
import pytz

register = template.Library()

@register.filter
def to_nairobi_time(value):
    """Convert UTC datetime to Nairobi timezone"""
    if not value:
        return value
    
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    if timezone.is_aware(value):
        return value.astimezone(nairobi_tz)
    else:
        # If naive datetime, assume it's UTC
        utc_value = pytz.utc.localize(value)
        return utc_value.astimezone(nairobi_tz)

@register.filter
def format_nairobi_time(value):
    """Format datetime in Nairobi timezone with timezone indicator"""
    if not value:
        return value
    
    nairobi_time = to_nairobi_time(value)
    return nairobi_time.strftime('%Y-%m-%d %H:%M:%S EAT')

@register.simple_tag
def current_nairobi_time():
    """Get current time in Nairobi timezone"""
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    return timezone.now().astimezone(nairobi_tz)

@register.simple_tag
def timezone_info():
    """Get timezone information for display"""
    return {
        'name': 'East Africa Time (EAT)',
        'abbreviation': 'EAT',
        'offset': '+03:00'
    }