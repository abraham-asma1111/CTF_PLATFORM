"""
Management command to set up server-side flag challenges
"""
from django.core.management.base import BaseCommand
from challenges.models import Challenge
from challenges.server_flags import ServerFlagManager


class Command(BaseCommand):
    help = 'Set up server-side flags for CTF challenges'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Setting up server-side flag challenges...')
        self.stdout.write('=' * 60)
        
        # Get or create a challenge for testing
        challenge, created = Challenge.objects.get_or_create(
            title='Server-Side Flag Discovery',
            defaults={
                'description': '''This challenge contains flags hidden on the server.
                
Your mission: Find the flags using various techniques!

Hints:
- Try accessing /challenges/vulnerable/{challenge_id}/files
- Look for backup files
- Check for exposed .git directories
- Try path traversal attacks
- Look for information disclosure

The flag format is: CTF{...}
''',
                'category': 'web',
                'difficulty': 'medium',
                'points': 50,
                'flag': 'CTF{server_side_discovery_master}',
                'is_active': True
            }
        )
        
        challenge_id = challenge.id
        flag = 'CTF{server_side_discovery_master}'
        
        self.stdout.write(f'\n✅ Challenge ID: {challenge_id}')
        self.stdout.write(f'✅ Challenge: {challenge.title}')
        
        # Create various flag files
        self.stdout.write('\nCreating flag files...')
        
        # 1. Regular flag file
        ServerFlagManager.create_flag_file(challenge_id, flag, 'flag.txt')
        self.stdout.write('  ✅ Created flag.txt')
        
        # 2. Hidden flag file
        ServerFlagManager.create_flag_file(challenge_id, flag, 'secret_flag.txt', hidden=True)
        self.stdout.write('  ✅ Created .secret_flag.txt (hidden)')
        
        # 3. Backup file
        ServerFlagManager.create_backup_file(challenge_id, flag)
        self.stdout.write('  ✅ Created backup.txt.bak')
        
        # 4. Git exposed flag
        ServerFlagManager.create_git_exposed_flag(challenge_id, flag)
        self.stdout.write('  ✅ Created .git/logs/HEAD')
        
        # 5. Source code flag
        ServerFlagManager.create_source_code_flag(challenge_id, flag)
        self.stdout.write('  ✅ Created app.py with flag in comments')
        
        # List all created files
        files = ServerFlagManager.list_challenge_files(challenge_id)
        self.stdout.write(f'\n📁 Total files created: {len(files)}')
        for f in files:
            self.stdout.write(f'   - {f}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SETUP COMPLETE!')
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'\n🎯 Challenge URL: http://127.0.0.1:8000/challenges/{challenge_id}/')
        self.stdout.write('\n📚 Vulnerable Endpoints:')
        self.stdout.write(f'   - File Read: /challenges/vulnerable/{challenge_id}/read?file=flag.txt')
        self.stdout.write(f'   - Directory List: /challenges/vulnerable/{challenge_id}/files')
        self.stdout.write(f'   - Command Injection: /challenges/vulnerable/{challenge_id}/ping?host=localhost')
        self.stdout.write(f'   - SQL Injection: /challenges/vulnerable/{challenge_id}/login?username=admin')
        self.stdout.write(f'   - Info Disclosure: /challenges/vulnerable/{challenge_id}/debug?action=debug')
        self.stdout.write(f'   - Robots.txt: /challenges/vulnerable/{challenge_id}/robots.txt')
        
        self.stdout.write('\n💡 Try these attacks:')
        self.stdout.write('   1. Path Traversal: ?file=../../../flag.txt')
        self.stdout.write('   2. Directory Listing: Access /files endpoint')
        self.stdout.write("   3. SQL Injection: ?username=admin' OR '1'='1")
        self.stdout.write('   4. Command Injection: ?host=localhost; cat flag.txt')
        self.stdout.write('   5. Info Disclosure: ?action=debug')
        
        self.stdout.write('\n')
