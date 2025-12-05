from django.core.management.base import BaseCommand
from teams.models import TeamMembership
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Clean up duplicate team memberships'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up team memberships...')
        
        # Find users with multiple memberships
        users_with_multiple = []
        for user in User.objects.all():
            memberships = TeamMembership.objects.filter(user=user)
            if memberships.count() > 1:
                users_with_multiple.append(user)
        
        cleaned_count = 0
        for user in users_with_multiple:
            memberships = TeamMembership.objects.filter(user=user).order_by('-joined_at')
            
            # Keep the most recent accepted membership, or the most recent one if none are accepted
            accepted_memberships = memberships.filter(status='accepted')
            
            if accepted_memberships.exists():
                # Keep the most recent accepted membership
                keep_membership = accepted_memberships.first()
                # Delete all others
                to_delete = memberships.exclude(id=keep_membership.id)
            else:
                # Keep the most recent membership
                keep_membership = memberships.first()
                # Delete all others
                to_delete = memberships.exclude(id=keep_membership.id)
            
            deleted_count = to_delete.count()
            if deleted_count > 0:
                self.stdout.write(f'User {user.username}: keeping membership {keep_membership.id}, deleting {deleted_count} others')
                to_delete.delete()
                cleaned_count += deleted_count
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {cleaned_count} duplicate memberships')
        )