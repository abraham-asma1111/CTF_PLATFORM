from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from teams.models import Team, TeamMembership
from chat.models import TeamMessage


class Command(BaseCommand):
    help = 'Create sample chat messages for testing'

    def handle(self, *args, **options):
        # Get or create test users
        try:
            user1 = User.objects.get(username='testuser1')
        except User.DoesNotExist:
            user1 = User.objects.create_user(
                username='testuser1',
                email='test1@example.com',
                password='testpass123'
            )
            self.stdout.write(f'Created user: {user1.username}')

        try:
            user2 = User.objects.get(username='testuser2')
        except User.DoesNotExist:
            user2 = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='testpass123'
            )
            self.stdout.write(f'Created user: {user2.username}')

        # Get or create test team
        team, created = Team.objects.get_or_create(
            name='Test Chat Team',
            defaults={
                'captain': user1,
                'description': 'A team for testing chat functionality'
            }
        )
        
        if created:
            self.stdout.write(f'Created team: {team.name}')
        
        # Ensure both users are team members
        team.ensure_captain_membership()
        TeamMembership.objects.get_or_create(
            team=team,
            user=user2,
            defaults={'status': 'accepted'}
        )

        # Create sample messages
        sample_messages = [
            (user1, "Hey team! Welcome to our chat room! 🎉"),
            (user2, "Thanks! This is awesome. Ready to tackle some challenges?"),
            (user1, "Absolutely! I found an interesting SQL injection challenge."),
            (user2, "Nice! Let's work on it together. What's the approach?"),
            (user1, "I think we should start by analyzing the input fields..."),
            (user2, "Good idea. I'll check for any client-side validation bypasses."),
            (user1, "Perfect! Let me know what you find. 👍"),
            (user2, "Found something! The login form doesn't properly sanitize inputs."),
            (user1, "Excellent work! Let's try some basic SQL injection payloads."),
            (user2, "Already on it! Testing ' OR '1'='1' -- first"),
        ]

        created_count = 0
        for sender, content in sample_messages:
            message, created = TeamMessage.objects.get_or_create(
                team=team,
                sender=sender,
                content=content,
                defaults={'message_type': 'text'}
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} sample messages for team "{team.name}"'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'You can now test the chat at: /chat/team/{team.id}/'
            )
        )