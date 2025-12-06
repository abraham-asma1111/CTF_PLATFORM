"""
Django management command for group event lifecycle management
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from challenges.group_challenge_manager import GroupEventLifecycleManager


class Command(BaseCommand):
    help = 'Manage group event lifecycle - check and update event status based on time'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-status',
            action='store_true',
            help='Check and update event status based on current time'
        )
        
        parser.add_argument(
            '--status-summary',
            action='store_true',
            help='Display status summary of all group events'
        )
        
        parser.add_argument(
            '--cleanup-expired',
            action='store_true',
            help='Clean up expired events (preserves data by default)'
        )
        
        parser.add_argument(
            '--preserve-data',
            action='store_true',
            default=True,
            help='Preserve event data during cleanup (default: True)'
        )
        
        parser.add_argument(
            '--event-history',
            action='store_true',
            help='Display historical data for all events'
        )
        
        parser.add_argument(
            '--preserve-event',
            type=int,
            help='Preserve results for a specific event ID'
        )
    
    def handle(self, *args, **options):
        if options['check_status']:
            self.check_and_update_status()
        
        if options['status_summary']:
            self.display_status_summary()
        
        if options['cleanup_expired']:
            self.cleanup_expired_events(options['preserve_data'])
        
        if options['event_history']:
            self.display_event_history()
        
        if options['preserve_event']:
            self.preserve_specific_event(options['preserve_event'])
    
    def check_and_update_status(self):
        """Check and update event status based on current time"""
        self.stdout.write("🔄 Checking group event status...")
        
        changed_events = GroupEventLifecycleManager.check_and_update_event_status()
        
        if not changed_events:
            self.stdout.write(
                self.style.SUCCESS("✅ No event status changes needed")
            )
            return
        
        for change in changed_events:
            event = change['event']
            action = change['action']
            
            if action == 'activated':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"🟢 Activated event: {event.name} (ID: {event.id})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"🔴 Deactivated event: {event.name} (ID: {event.id})"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Updated {len(changed_events)} events")
        )
    
    def display_status_summary(self):
        """Display status summary of all group events"""
        self.stdout.write("📊 Group Event Status Summary")
        self.stdout.write("=" * 50)
        
        summary = GroupEventLifecycleManager.get_event_status_summary()
        
        # Display times in EAT for better readability
        import pytz
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        current_eat = summary['current_time'].astimezone(nairobi_tz)
        
        self.stdout.write(f"Current Time: {current_eat.strftime('%Y-%m-%d %H:%M:%S EAT')} (UTC: {summary['current_time'].strftime('%H:%M:%S')})")
        self.stdout.write(f"Total Events: {summary['total_events']}")
        
        # Current platform mode
        if summary['current_platform_mode']:
            mode_info = summary['current_platform_mode']
            active_event = mode_info['active_event']
            if active_event:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"🎯 Active Group Event: {active_event.name} (ID: {active_event.id})"
                    )
                )
            else:
                self.stdout.write("🎯 Group Mode: Inactive")
        else:
            self.stdout.write("🎯 Platform Mode: Individual")
        
        # Active events
        if summary['active_events']:
            self.stdout.write("\n🟢 Currently Active Events:")
            for event in summary['active_events']:
                status_icon = "✅" if event['is_active'] else "⚠️"
                start_eat = event['start_time'].astimezone(nairobi_tz)
                end_eat = event['end_time'].astimezone(nairobi_tz)
                self.stdout.write(
                    f"  {status_icon} {event['name']} (ID: {event['id']}) - "
                    f"{start_eat.strftime('%Y-%m-%d %H:%M EAT')} to {end_eat.strftime('%Y-%m-%d %H:%M EAT')}"
                )
        
        # Upcoming events
        if summary['upcoming_events']:
            self.stdout.write("\n🔵 Upcoming Events:")
            for event in summary['upcoming_events']:
                start_eat = event['start_time'].astimezone(nairobi_tz)
                self.stdout.write(
                    f"  📅 {event['name']} (ID: {event['id']}) - "
                    f"Starts: {start_eat.strftime('%Y-%m-%d %H:%M EAT')}"
                )
        
        # Past events
        if summary['past_events']:
            self.stdout.write("\n⚫ Past Events:")
            for event in summary['past_events'][:5]:  # Show last 5
                end_eat = event['end_time'].astimezone(nairobi_tz)
                self.stdout.write(
                    f"  📜 {event['name']} (ID: {event['id']}) - "
                    f"Ended: {end_eat.strftime('%Y-%m-%d %H:%M EAT')}"
                )
            
            if len(summary['past_events']) > 5:
                self.stdout.write(f"  ... and {len(summary['past_events']) - 5} more")
    
    def cleanup_expired_events(self, preserve_data=True):
        """Clean up expired events"""
        self.stdout.write("🧹 Cleaning up expired events...")
        
        cleanup_summary = GroupEventLifecycleManager.cleanup_expired_events(preserve_data)
        
        if cleanup_summary['expired_events_count'] == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ No expired events to clean up")
            )
            return
        
        if preserve_data:
            self.stdout.write(
                self.style.SUCCESS(
                    f"📦 Preserved data for {len(cleanup_summary['preserved_events'])} expired events"
                )
            )
            
            for event in cleanup_summary['preserved_events']:
                self.stdout.write(
                    f"  📜 {event['name']} - "
                    f"Challenges: {event['challenges_count']}, "
                    f"Submissions: {event['submissions_count']}"
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"🗑️ Removed {len(cleanup_summary['removed_events'])} expired events"
                )
            )
    
    def display_event_history(self):
        """Display historical data for all events"""
        self.stdout.write("📚 Group Event History")
        self.stdout.write("=" * 50)
        
        history = GroupEventLifecycleManager.get_event_history()
        
        if not history:
            self.stdout.write("No group events found")
            return
        
        for event_data in history:
            details = event_data['event_details']
            preserved = event_data['preserved_data']
            stats = preserved.get('statistics', {})
            
            self.stdout.write(f"\n📋 {event_data['event_name']} (ID: {event_data['event_id']})")
            self.stdout.write(f"   Duration: {details['start_time']} to {details['end_time']}")
            self.stdout.write(f"   Created by: {details['created_by']}")
            self.stdout.write(f"   Status: {'🟢 Active' if details['is_active'] else '⚫ Inactive'}")
            
            self.stdout.write(f"   📊 Statistics:")
            self.stdout.write(f"      Challenges: {preserved['challenges_count']}")
            self.stdout.write(f"      Teams: {preserved['participating_teams_count']}")
            self.stdout.write(f"      Submissions: {preserved['submissions_count']}")
            self.stdout.write(f"      Total Points: {stats.get('total_points_awarded', 0)}")
            
            # Show top 3 teams if available
            leaderboard = preserved.get('final_leaderboard', [])
            if leaderboard:
                self.stdout.write(f"   🏆 Top Teams:")
                for i, team_data in enumerate(leaderboard[:3], 1):
                    self.stdout.write(
                        f"      {i}. {team_data['team'].name} - "
                        f"{team_data['event_score']} points"
                    )
    
    def preserve_specific_event(self, event_id):
        """Preserve results for a specific event"""
        try:
            from challenges.models import GroupEvent
            event = GroupEvent.objects.get(id=event_id)
            
            self.stdout.write(f"📦 Preserving results for event: {event.name}")
            
            preservation_summary = GroupEventLifecycleManager.preserve_event_results(event)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Preserved data for event {event.name} (ID: {event_id})"
                )
            )
            
            preserved = preservation_summary['preserved_data']
            self.stdout.write(f"   Challenges: {preserved['challenges_count']}")
            self.stdout.write(f"   Submissions: {preserved['submissions_count']}")
            self.stdout.write(f"   Teams: {preserved['participating_teams_count']}")
            
            stats = preserved.get('statistics', {})
            self.stdout.write(f"   Total Points: {stats.get('total_points_awarded', 0)}")
            
        except GroupEvent.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Event with ID {event_id} not found")
            )