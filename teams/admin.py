from django.contrib import admin
from .models import Team, TeamMembership, TeamInvitation


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'captain', 'member_count', 'total_score', 'challenges_solved', 'can_compete', 'created_at']
    search_fields = ['name', 'captain__username']
    list_filter = ['is_active', 'created_at']
    
    def _delete_team_with_relations(self, team_ids):
        """Helper method to delete teams and their relations properly"""
        from django.db import transaction, connection
        from submissions.models import Submission
        from challenges.models import GroupSubmission
        from teams.models import TeamMembership, TeamInvitation
        
        with transaction.atomic():
            # Delete in the correct order to avoid constraint violations
            
            # 1. Delete chat messages (if chat table exists)
            with connection.cursor() as cursor:
                try:
                    # Delete message reactions first
                    cursor.execute("""
                        DELETE FROM chat_messagereaction 
                        WHERE message_id IN (
                            SELECT id FROM chat_teammessage WHERE team_id IN ({})
                        )
                    """.format(','.join(str(id) for id in team_ids)))
                    
                    # Delete message read status
                    cursor.execute("""
                        DELETE FROM chat_messageread 
                        WHERE message_id IN (
                            SELECT id FROM chat_teammessage WHERE team_id IN ({})
                        )
                    """.format(','.join(str(id) for id in team_ids)))
                    
                    # Delete chat messages
                    cursor.execute("""
                        DELETE FROM chat_teammessage WHERE team_id IN ({})
                    """.format(','.join(str(id) for id in team_ids)))
                except Exception:
                    # Chat tables might not exist, continue anyway
                    pass
            
            # 2. Group submissions (has FK to team with CASCADE)
            GroupSubmission.objects.filter(team_id__in=team_ids).delete()
            
            # 3. Regular submissions (has FK to team with SET_NULL)
            Submission.objects.filter(team_id__in=team_ids).update(team=None)
            
            # 4. Team memberships (has FK to team with CASCADE)
            TeamMembership.objects.filter(team_id__in=team_ids).delete()
            
            # 5. Team invitations (has FK to team with CASCADE)
            TeamInvitation.objects.filter(team_id__in=team_ids).delete()
            
            # 6. Finally delete the teams themselves
            Team.objects.filter(id__in=team_ids).delete()
    
    def delete_model(self, request, obj):
        """Override to handle single team deletion"""
        self._delete_team_with_relations([obj.id])
    
    def delete_queryset(self, request, queryset):
        """Override to handle bulk team deletion"""
        team_ids = list(queryset.values_list('id', flat=True))
        self._delete_team_with_relations(team_ids)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'status', 'joined_at']
    list_filter = ['status', 'joined_at']
    search_fields = ['user__username', 'team__name']


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ['team', 'from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['team__name', 'to_user__username']
