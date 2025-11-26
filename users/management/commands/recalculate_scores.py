from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from submissions.models import Submission
from users.models import UserProfile

class Command(BaseCommand):
    help = 'Recalculate all user scores and challenge counts based on correct submissions'

    def handle(self, *args, **options):
        self.stdout.write('Starting score recalculation...')
        
        # Get all users
        users = User.objects.filter(is_staff=False, is_superuser=False)
        
        for user in users:
            # Get all correct submissions for this user
            correct_submissions = Submission.objects.filter(
                user=user,
                is_correct=True
            ).select_related('challenge')
            
            # Calculate total score and challenges solved
            total_score = sum(submission.challenge.points for submission in correct_submissions)
            challenges_solved = correct_submissions.count()
            
            # Get the latest submission timestamp
            latest_submission = correct_submissions.order_by('-timestamp').first()
            last_submission = latest_submission.timestamp if latest_submission else None
            
            # Update user profile
            profile = user.userprofile
            profile.total_score = total_score
            profile.challenges_solved = challenges_solved
            profile.last_submission = last_submission
            profile.save()
            
            self.stdout.write(
                f'Updated {user.username}: {challenges_solved} challenges, {total_score} points'
            )
        
        self.stdout.write(self.style.SUCCESS('Score recalculation completed successfully!'))
