from django.core.management.base import BaseCommand
from teams.models import Team, TeamMembership


class Command(BaseCommand):
    help = 'Fix teams where captains are missing membership records'

    def handle(self, *args, **options):
        self.stdout.write('Fixing captain memberships...')
        
        fixed_count = 0
        
        # Find all active teams
        teams = Team.objects.filter(is_active=True)
        
        for team in teams:
            # Check if captain has membership
            captain_membership = TeamMembership.objects.filter(
                team=team,
                user=team.captain
            ).first()
            
            if not captain_membership:
                # Captain is missing membership - create it
                TeamMembership.objects.create(
                    team=team,
                    user=team.captain,
                    status='accepted'
                )
                self.stdout.write(f'✓ Fixed team "{team.name}" - added captain membership')
                fixed_count += 1
            elif captain_membership.status != 'accepted':
                # Captain membership exists but wrong status
                captain_membership.status = 'accepted'
                captain_membership.save()
                self.stdout.write(f'✓ Fixed team "{team.name}" - corrected captain status')
                fixed_count += 1
        
        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS('No issues found - all teams are properly configured'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} team(s)')
            )