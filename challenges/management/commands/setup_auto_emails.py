from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Setup automatic challenge email broadcasting'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚩 CTF Platform - Automatic Challenge Email Broadcasting'))
        self.stdout.write('=' * 60)
        
        # Check if admin users exist
        admin_count = User.objects.filter(is_superuser=True).count()
        self.stdout.write(f'👑 Admin users: {admin_count}')
        
        if admin_count == 0:
            self.stdout.write(self.style.ERROR('❌ No admin users found! Create one with: python manage.py createsuperuser'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n✅ Automatic email broadcasting is set up!'))
        self.stdout.write('\n📋 How it works:')
        self.stdout.write('1. When admin creates a new challenge → Broadcast email is auto-created')
        self.stdout.write('2. Email content includes challenge details, difficulty, points')
        self.stdout.write('3. Recipients are chosen based on challenge type:')
        self.stdout.write('   • Team challenges → Team members only')
        self.stdout.write('   • Individual challenges → Individual users only')
        self.stdout.write('   • Both types → All users')
        
        self.stdout.write('\n📧 To send the emails:')
        self.stdout.write('   python manage.py auto_send_challenge_emails')
        self.stdout.write('   python manage.py auto_send_challenge_emails --dry-run  (test mode)')
        
        self.stdout.write('\n🔧 Manual control:')
        self.stdout.write('   python manage.py send_broadcast_email --broadcast-id <ID>')
        self.stdout.write('   Check /admin/users/broadcastemail/ for all broadcasts')
        
        self.stdout.write('\n🎯 Test the system:')
        self.stdout.write('1. Go to /admin/challenges/challenge/')
        self.stdout.write('2. Create a new challenge with is_active=True')
        self.stdout.write('3. Check /admin/users/broadcastemail/ for auto-created email')
        self.stdout.write('4. Run: python manage.py auto_send_challenge_emails')
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Ready to broadcast challenge notifications!'))