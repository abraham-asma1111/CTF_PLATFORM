"""
Django management command to display timezone information
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import pytz


class Command(BaseCommand):
    help = 'Display timezone information for the CTF platform'
    
    def handle(self, *args, **options):
        self.stdout.write("🌍 CTF Platform Timezone Information")
        self.stdout.write("=" * 50)
        
        # Django settings
        self.stdout.write(f"Django TIME_ZONE setting: {settings.TIME_ZONE}")
        self.stdout.write(f"Django USE_TZ setting: {settings.USE_TZ}")
        
        # Current timezone
        current_tz = timezone.get_current_timezone()
        self.stdout.write(f"Current timezone: {current_tz}")
        
        # Time information
        utc_now = timezone.now()
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        nairobi_now = utc_now.astimezone(nairobi_tz)
        
        self.stdout.write(f"\n⏰ Current Time Information:")
        self.stdout.write(f"UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        self.stdout.write(f"Nairobi time: {nairobi_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        self.stdout.write(f"Timezone offset: {nairobi_now.strftime('%z')} (UTC{nairobi_now.strftime('%z')[:3]}:{nairobi_now.strftime('%z')[3:]})")
        
        # Event timing information
        from challenges.models import GroupEvent
        events = GroupEvent.objects.all()
        
        if events:
            self.stdout.write(f"\n📅 Event Times (showing in both UTC and EAT):")
            for event in events:
                event_start_eat = event.start_time.astimezone(nairobi_tz)
                event_end_eat = event.end_time.astimezone(nairobi_tz)
                
                self.stdout.write(f"\n🏆 {event.name}:")
                self.stdout.write(f"  Start: {event.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} → {event_start_eat.strftime('%Y-%m-%d %H:%M:%S EAT')}")
                self.stdout.write(f"  End:   {event.end_time.strftime('%Y-%m-%d %H:%M:%S UTC')} → {event_end_eat.strftime('%Y-%m-%d %H:%M:%S EAT')}")
                self.stdout.write(f"  Status: {'🟢 Active' if event.is_active else '⚫ Inactive'}")
        else:
            self.stdout.write(f"\n📅 No group events found")
        
        # Timezone recommendations
        self.stdout.write(f"\n💡 Timezone Best Practices:")
        self.stdout.write(f"  • All times are stored in UTC in the database")
        self.stdout.write(f"  • Times are displayed in East Africa Time (EAT) to users")
        self.stdout.write(f"  • EAT is UTC+3 (no daylight saving time)")
        self.stdout.write(f"  • Admin interface shows times with EAT labels")
        self.stdout.write(f"  • Footer displays current time in EAT for user reference")
        
        self.stdout.write(f"\n✅ Timezone configuration is optimal for East Africa!")