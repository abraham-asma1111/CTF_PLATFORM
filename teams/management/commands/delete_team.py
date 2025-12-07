"""
Management command to safely delete teams
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from teams.models import Team
from submissions.models import Submission
from challenges.models import GroupSubmission


class Command(BaseCommand):
    help = 'Safely delete a team by handling all foreign key relationships'

    def add_arguments(self, parser):
        parser.add_argument('team_id', type=int, help='ID of the team to delete')

    def handle(self, *args, **options):
        team_id = options['team_id']
        
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Team with ID {team_id} does not exist'))
            return
        
        team_name = team.name
        
        # Confirm deletion
        self.stdout.write(self.style.WARNING(f'About to delete team: {team_name} (ID: {team_id})'))
        
        try:
            with transaction.atomic():
                # Handle submissions
                submission_count = Submission.objects.filter(team=team).count()
                if submission_count > 0:
                    Submission.objects.filter(team=team).update(team=None)
                    self.stdout.write(f'  - Set team=NULL for {submission_count} regular submissions')
                
                # Handle group submissions
                group_submission_count = GroupSubmission.objects.filter(team=team).count()
                if group_submission_count > 0:
                    GroupSubmission.objects.filter(team=team).delete()
                    self.stdout.write(f'  - Deleted {group_submission_count} group submissions')
                
                # Delete the team (will cascade delete memberships and invitations)
                team.delete()
                
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted team: {team_name}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deleting team: {str(e)}'))
