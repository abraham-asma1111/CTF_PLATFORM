from django.contrib import admin
from .models import Team, TeamMembership, TeamInvitation


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'captain', 'member_count', 'total_score', 'challenges_solved', 'can_compete', 'created_at']
    search_fields = ['name', 'captain__username']
    list_filter = ['is_active', 'created_at']


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
