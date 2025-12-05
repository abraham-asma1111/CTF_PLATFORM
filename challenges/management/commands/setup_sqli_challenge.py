from django.core.management.base import BaseCommand
from challenges.models import Challenge
from challenges.sql_injection_challenge import SQLInjectionChallenge


class Command(BaseCommand):
    help = 'Set up SQL Injection challenge'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Setting up SQL Injection Challenge...')
        self.stdout.write('=' * 60)
        
        # Create challenge
        challenge, created = Challenge.objects.get_or_create(
            title='SQL Injection - SecureBank Login',
            defaults={
                'description': '''Welcome to SecureBank Online Banking!

Your mission: Bypass the login system and access the admin account to find the flag.

🎯 Objective:
- Exploit the SQL injection vulnerability in the login form
- Access the admin account without knowing the password
- Find and submit the flag

💡 Getting Started:
Visit the challenge at: /challenges/sqli/{challenge_id}/

🔗 Challenge URL will be shown below after setup.

Difficulty: Medium
Category: Web Security
Points: 75
''',
                'category': 'web',
                'difficulty': 'medium',
                'points': 75,
                'flag': 'CTF{sql_injection_master_2024}',
                'is_active': True
            }
        )
        
        challenge_id = challenge.id
        flag = challenge.flag
        
        # Setup database
        db_path = SQLInjectionChallenge.setup_database(challenge_id, flag)
        
        self.stdout.write(f'\n✅ Challenge Created!')
        self.stdout.write(f'   ID: {challenge_id}')
        self.stdout.write(f'   Title: {challenge.title}')
        self.stdout.write(f'   Flag: {flag}')
        self.stdout.write(f'   Database: {db_path}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SETUP COMPLETE!')
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'\n🌐 Access the challenge:')
        self.stdout.write(f'   http://127.0.0.1:8000/challenges/sqli/{challenge_id}/')
        
        self.stdout.write(f'\n📝 Challenge Page:')
        self.stdout.write(f'   http://127.0.0.1:8000/challenges/{challenge_id}/')
        
        self.stdout.write('\n💡 How to solve:')
        self.stdout.write('   1. Go to the SecureBank login page')
        self.stdout.write('   2. Try SQL injection in username field')
        self.stdout.write("   3. Example: admin' OR '1'='1' --")
        self.stdout.write('   4. Access admin account and find the flag')
        self.stdout.write('   5. Submit flag on main challenge page')
        
        self.stdout.write('\n🔐 Test Credentials:')
        self.stdout.write('   Username: guest')
        self.stdout.write('   Password: guest')
        
        self.stdout.write('\n')
