from django.core.management.base import BaseCommand
from challenges.models import Challenge


class Command(BaseCommand):
    help = 'Create sample team challenges'

    def handle(self, *args, **options):
        team_challenges = [
            {
                'title': 'Team Coordination Challenge',
                'description': '''This challenge requires teamwork! Each team member will receive a different piece of the puzzle.
                
                Team Member 1: Find the hidden endpoint at /api/secret1
                Team Member 2: Decode the base64 message: VGVhbVdvcms=
                Team Member 3: Solve the cipher: WHDP FKDOOHQJH
                
                Combine all three pieces to get the flag format: flag{piece1_piece2_piece3}
                
                Minimum team size: 3 members required!''',
                'category': 'misc',
                'difficulty': 'medium',
                'flag': 'flag{secret_TeamWork_challenge}',
                'points': 200,
                'challenge_type': 'team',
                'min_team_size': 3,
                'max_team_size': 5,
                'team_points_multiplier': 1.5,
            },
            {
                'title': 'Distributed Web Exploitation',
                'description': '''A complex web application with multiple vulnerabilities that require different expertise:
                
                - SQL Injection in login form
                - XSS in comment section  
                - File upload bypass
                - Privilege escalation
                
                Each team member should focus on one vulnerability. Combine your findings!
                
                Team challenge with bonus points for collaboration.''',
                'category': 'web',
                'difficulty': 'hard',
                'flag': 'flag{distributed_web_pwned}',
                'points': 300,
                'challenge_type': 'team',
                'min_team_size': 2,
                'max_team_size': 4,
                'team_points_multiplier': 2.0,
            },
            {
                'title': 'Crypto Team Relay',
                'description': '''A multi-stage cryptography challenge:
                
                Stage 1: Caesar cipher (Team Member 1)
                Stage 2: Vigenère cipher using Stage 1 output (Team Member 2)  
                Stage 3: RSA decryption using Stage 2 output (Team Member 3)
                
                Each stage depends on the previous one. Perfect teamwork required!
                
                Encrypted message: Gur svefg fgrc vf gb qrpelcg guvf...''',
                'category': 'crypto',
                'difficulty': 'hard',
                'flag': 'flag{crypto_relay_complete}',
                'points': 250,
                'challenge_type': 'team',
                'min_team_size': 3,
                'max_team_size': 3,
                'team_points_multiplier': 1.8,
            },
            {
                'title': 'Individual Warm-up',
                'description': '''A simple challenge for individual players only.
                
                Find the flag hidden in this base64 string:
                ZmxhZ3tpbmRpdmlkdWFsX3dhcm11cH0=
                
                This challenge is only available to users not in teams.''',
                'category': 'misc',
                'difficulty': 'easy',
                'flag': 'flag{individual_warmup}',
                'points': 50,
                'challenge_type': 'individual',
                'min_team_size': 1,
                'max_team_size': 1,
                'team_points_multiplier': 1.0,
            },
            {
                'title': 'Flexible SQL Challenge',
                'description': '''A SQL injection challenge that works for both individuals and teams.
                
                Login form at: http://vulnerable-app.local/login
                
                Find a way to bypass authentication and retrieve the admin flag.
                
                Teams get bonus points for collaborative approach!''',
                'category': 'web',
                'difficulty': 'medium',
                'flag': 'flag{sql_injection_success}',
                'points': 150,
                'challenge_type': 'both',
                'min_team_size': 1,
                'max_team_size': 5,
                'team_points_multiplier': 1.3,
            },
        ]

        created_count = 0
        for challenge_data in team_challenges:
            challenge, created = Challenge.objects.get_or_create(
                title=challenge_data['title'],
                defaults=challenge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created challenge: {challenge.title} ({challenge.get_challenge_type_display()})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Challenge already exists: {challenge.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {created_count} new team challenges!')
        )
        self.stdout.write('Run the server and check /admin/ to manage challenges.')