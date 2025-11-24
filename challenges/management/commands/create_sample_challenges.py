from django.core.management.base import BaseCommand
from challenges.models import Challenge

class Command(BaseCommand):
    help = 'Create sample CTF challenges'

    def handle(self, *args, **options):
        challenges_data = [
            {
                'title': 'Welcome to CTF',
                'description': 'This is your first challenge! The flag is hidden in plain sight. Look at the source code of this page.',
                'difficulty': 'easy',
                'category': 'misc',
                'flag': 'CTF{welcome_to_the_game}',
                'points': 50,
            },
            {
                'title': 'Basic Web Challenge',
                'description': 'Find the hidden directory on our web server. The flag is in a file called flag.txt.',
                'difficulty': 'easy',
                'category': 'web',
                'flag': 'CTF{hidden_directories_are_fun}',
                'points': 100,
            },
            {
                'title': 'Caesar Cipher',
                'description': 'Decode this message: "PGS{pnrfne_pvCure_vf_rnfl}". The shift is 13.',
                'difficulty': 'easy',
                'category': 'crypto',
                'flag': 'CTF{caesar_cipher_is_easy}',
                'points': 75,
            },
            {
                'title': 'SQL Injection',
                'description': 'Our login form seems vulnerable. Can you bypass the authentication? Username: admin',
                'difficulty': 'medium',
                'category': 'web',
                'flag': 'CTF{sql_injection_master}',
                'points': 200,
            },
            {
                'title': 'Buffer Overflow',
                'description': 'This binary has a buffer overflow vulnerability. Exploit it to get the flag.',
                'difficulty': 'hard',
                'category': 'pwn',
                'flag': 'CTF{buffer_overflow_pwned}',
                'points': 300,
            },
            {
                'title': 'Reverse Engineering',
                'description': 'Analyze this binary and find the correct password to get the flag.',
                'difficulty': 'medium',
                'category': 'reverse',
                'flag': 'CTF{reverse_engineering_rocks}',
                'points': 250,
            },
            {
                'title': 'Digital Forensics',
                'description': 'Examine this disk image and find the hidden flag in the deleted files.',
                'difficulty': 'medium',
                'category': 'forensics',
                'flag': 'CTF{forensics_detective}',
                'points': 180,
            },
            {
                'title': 'Advanced Crypto',
                'description': 'This RSA implementation has a weakness. Can you find it and decrypt the message?',
                'difficulty': 'hard',
                'category': 'crypto',
                'flag': 'CTF{rsa_weakness_found}',
                'points': 400,
            },
        ]

        for challenge_data in challenges_data:
            challenge, created = Challenge.objects.get_or_create(
                title=challenge_data['title'],
                defaults=challenge_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created challenge: {challenge.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Challenge already exists: {challenge.title}')
                )

        self.stdout.write(
            self.style.SUCCESS('Sample challenges creation completed!')
        )