from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Challenge, Hint, HintView, GroupEvent, GroupChallenge, GroupSubmission, PlatformMode
from .group_challenge_manager import GroupChallengeManager


class HintInline(admin.TabularInline):
    """Inline admin for hints"""
    model = Hint
    extra = 1
    fields = ['order', 'content', 'cost']
    ordering = ['order']


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_badge', 'difficulty_badge', 'challenge_type_badge', 'points', 'team_multiplier', 'hints_count', 'status_badge', 'created_at']
    list_filter = ['category', 'difficulty', 'challenge_type', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'flag']
    ordering = ['-created_at']
    actions = ['make_active', 'make_inactive']
    inlines = [HintInline]
    
    fieldsets = (
        ('Challenge Information', {
            'fields': ('title', 'description', 'category', 'difficulty')
        }),
        ('Flag & Points', {
            'fields': ('flag', 'points'),
            'description': 'Enter the plain text flag. It will be automatically hashed for security.'
        }),
        ('Team Settings', {
            'fields': ('challenge_type', 'min_team_size', 'max_team_size', 'team_points_multiplier'),
            'description': 'Configure who can access this challenge and team requirements.',
        }),
        ('Challenge File', {
            'fields': ('challenge_file',),
            'description': 'Upload challenge file (binary, archive, etc.) for users to download. Optional.',
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def category_badge(self, obj):
        """Display category with color badge"""
        colors = {
            'web': '#3498db',
            'crypto': '#e74c3c',
            'forensics': '#2ecc71',
            'pwn': '#f39c12',
            'reverse': '#9b59b6',
            'misc': '#95a5a6',
        }
        color = colors.get(obj.category, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def difficulty_badge(self, obj):
        """Display difficulty with color badge"""
        colors = {
            'easy': '#2ecc71',
            'medium': '#f39c12',
            'hard': '#e74c3c',
        }
        color = colors.get(obj.difficulty, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_difficulty_display()
        )
    difficulty_badge.short_description = 'Difficulty'
    
    def status_badge(self, obj):
        """Display active status with badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">Inactive</span>'
            )
    status_badge.short_description = 'Status'
    
    def hints_count(self, obj):
        """Display number of hints"""
        count = obj.hints.count()
        if count > 0:
            return format_html(
                '<span style="color: #f39c12; font-weight: bold;">💡 {}</span>',
                count
            )
        return format_html('<span style="color: #95a5a6;">-</span>')
    hints_count.short_description = 'Hints'
    
    def challenge_type_badge(self, obj):
        """Display challenge type with color badge"""
        colors = {
            'individual': '#3498db',
            'team': '#e74c3c',
            'both': '#2ecc71',
        }
        color = colors.get(obj.challenge_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_challenge_type_display()
        )
    challenge_type_badge.short_description = 'Type'
    
    def team_multiplier(self, obj):
        """Display team points multiplier"""
        if obj.team_points_multiplier != 1.0:
            return format_html(
                '<span style="color: #f39c12; font-weight: bold;">×{}</span>',
                obj.team_points_multiplier
            )
        return '-'
    team_multiplier.short_description = 'Team Bonus'
    
    def save_model(self, request, obj, form, change):
        """Override save to add audit trail and trigger broadcast emails"""
        super().save_model(request, obj, form, change)
        
        # Show message about broadcast email
        if obj.is_active:
            if not change:
                self.message_user(
                    request, 
                    f'Challenge "{obj.title}" created! Broadcast email prepared. Use: python manage.py auto_send_challenge_emails',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f'Challenge "{obj.title}" updated! If activated, broadcast email may be created.',
                    messages.INFO
                )
    
    def make_active(self, request, queryset):
        """Bulk action to activate challenges"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} challenge(s) activated and now visible to users.')
    make_active.short_description = '✓ Activate selected challenges (make visible to users)'
    
    def make_inactive(self, request, queryset):
        """Bulk action to deactivate challenges"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} challenge(s) deactivated and hidden from users.', messages.WARNING)
    make_inactive.short_description = '✗ Deactivate selected challenges (hide from users)'


@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ['hint_label', 'challenge', 'cost', 'order', 'views_count']
    list_filter = ['challenge__category', 'cost']
    search_fields = ['challenge__title', 'content']
    ordering = ['challenge', 'order']
    
    def hint_label(self, obj):
        return f"Hint {obj.order}"
    hint_label.short_description = 'Hint'
    
    def views_count(self, obj):
        count = HintView.objects.filter(hint=obj).count()
        return format_html(
            '<span style="color: #3498db; font-weight: bold;">{} views</span>',
            count
        )
    views_count.short_description = 'Views'


@admin.register(HintView)
class HintViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'hint', 'points_deducted', 'viewed_at']
    list_filter = ['viewed_at', 'hint__challenge']
    search_fields = ['user__username', 'hint__challenge__title']
    ordering = ['-viewed_at']
    readonly_fields = ['user', 'hint', 'viewed_at', 'points_deducted']
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation


@admin.register(GroupEvent)
class GroupEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'status_badge', 'lifecycle_status', 'start_time_eat', 'end_time_eat', 'max_teams', 'point_multiplier', 'created_by', 'created_at']
    list_filter = ['is_active', 'start_time', 'end_time', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    actions = ['activate_event', 'deactivate_event', 'check_lifecycle_status', 'preserve_event_results']
    readonly_fields = ['created_by', 'created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'description')
        }),
        ('Event Schedule', {
            'fields': ('start_time', 'end_time'),
            'description': 'Set the event time range. Events cannot overlap.'
        }),
        ('Event Settings', {
            'fields': ('point_multiplier', 'max_teams'),
            'description': 'Configure event-specific settings.'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Only one event can be active at a time.'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save to add validation and set created_by"""
        if not change:  # New object
            obj.created_by = request.user
        
        # Validate time ranges
        if obj.start_time >= obj.end_time:
            raise ValidationError("Start time must be before end time.")
        
        # Check for overlapping events if activating
        if obj.is_active:
            overlapping = GroupEvent.objects.filter(
                is_active=True,
                start_time__lt=obj.end_time,
                end_time__gt=obj.start_time
            ).exclude(pk=obj.pk)
            
            if overlapping.exists():
                raise ValidationError(f"Event conflicts with active event: {overlapping.first().name}")
        
        super().save_model(request, obj, form, change)
        
        # Update platform mode if event is activated
        if obj.is_active:
            # Deactivate other events
            GroupEvent.objects.exclude(pk=obj.pk).update(is_active=False)
            
            # Set platform to group mode
            platform_mode, created = PlatformMode.objects.get_or_create(
                defaults={'mode': 'group', 'active_event': obj, 'changed_by': request.user}
            )
            if not created:
                platform_mode.mode = 'group'
                platform_mode.active_event = obj
                platform_mode.changed_by = request.user
                platform_mode.save()
            
            self.message_user(
                request,
                f'Group event "{obj.name}" activated! Platform is now in group mode.',
                messages.SUCCESS
            )
        else:
            # Check if this was the active event
            try:
                platform_mode = PlatformMode.objects.get()
                if platform_mode.active_event == obj:
                    platform_mode.mode = 'individual'
                    platform_mode.active_event = None
                    platform_mode.changed_by = request.user
                    platform_mode.save()
                    
                    self.message_user(
                        request,
                        f'Group event "{obj.name}" deactivated! Platform returned to individual mode.',
                        messages.INFO
                    )
            except PlatformMode.DoesNotExist:
                pass
    
    def status_badge(self, obj):
        """Display active status with badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">🟢 Active</span>'
            )
        else:
            # Check if event is in the future, current, or past
            now = timezone.now()
            if obj.start_time > now:
                return format_html(
                    '<span style="background-color: #3498db; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">🔵 Scheduled</span>'
                )
            elif obj.end_time < now:
                return format_html(
                    '<span style="background-color: #95a5a6; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">⚫ Ended</span>'
                )
            else:
                return format_html(
                    '<span style="background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">🟡 Inactive</span>'
                )
    status_badge.short_description = 'Status'
    
    def start_time_eat(self, obj):
        """Display start time in East Africa Time"""
        import pytz
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        local_time = obj.start_time.astimezone(nairobi_tz)
        return format_html(
            '<span title="UTC: {}">{}</span>',
            obj.start_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            local_time.strftime('%Y-%m-%d %H:%M:%S EAT')
        )
    start_time_eat.short_description = 'Start Time (EAT)'
    start_time_eat.admin_order_field = 'start_time'
    
    def end_time_eat(self, obj):
        """Display end time in East Africa Time"""
        import pytz
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        local_time = obj.end_time.astimezone(nairobi_tz)
        return format_html(
            '<span title="UTC: {}">{}</span>',
            obj.end_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            local_time.strftime('%Y-%m-%d %H:%M:%S EAT')
        )
    end_time_eat.short_description = 'End Time (EAT)'
    end_time_eat.admin_order_field = 'end_time'
    
    def activate_event(self, request, queryset):
        """Bulk action to activate events"""
        if queryset.count() > 1:
            self.message_user(request, 'Can only activate one event at a time.', messages.ERROR)
            return
        
        event = queryset.first()
        if event:
            # Validate time ranges
            now = timezone.now()
            if event.end_time < now:
                self.message_user(request, f'Cannot activate past event "{event.name}".', messages.ERROR)
                return
            
            # Deactivate other events
            GroupEvent.objects.exclude(pk=event.pk).update(is_active=False)
            event.is_active = True
            event.save()
            
            # Update platform mode
            platform_mode, created = PlatformMode.objects.get_or_create(
                defaults={'mode': 'group', 'active_event': event, 'changed_by': request.user}
            )
            if not created:
                platform_mode.mode = 'group'
                platform_mode.active_event = event
                platform_mode.changed_by = request.user
                platform_mode.save()
            
            self.message_user(request, f'Event "{event.name}" activated! Platform is now in group mode.', messages.SUCCESS)
    
    activate_event.short_description = '🟢 Activate selected event (group mode)'
    
    def deactivate_event(self, request, queryset):
        """Bulk action to deactivate events"""
        updated = queryset.update(is_active=False)
        
        # Return platform to individual mode if any active event was deactivated
        try:
            platform_mode = PlatformMode.objects.get()
            if platform_mode.mode == 'group' and not GroupEvent.objects.filter(is_active=True).exists():
                platform_mode.mode = 'individual'
                platform_mode.active_event = None
                platform_mode.changed_by = request.user
                platform_mode.save()
                
                self.message_user(request, f'{updated} event(s) deactivated! Platform returned to individual mode.', messages.INFO)
            else:
                self.message_user(request, f'{updated} event(s) deactivated.', messages.INFO)
        except PlatformMode.DoesNotExist:
            self.message_user(request, f'{updated} event(s) deactivated.', messages.INFO)
    
    deactivate_event.short_description = '🔴 Deactivate selected events'
    
    def lifecycle_status(self, obj):
        """Display lifecycle status information"""
        status = GroupChallengeManager.get_event_lifecycle_status(obj)
        
        phase_colors = {
            'upcoming': '#3498db',
            'active': '#2ecc71',
            'ended': '#95a5a6'
        }
        
        color = phase_colors.get(status['phase'], '#95a5a6')
        
        if not status['status_consistent']:
            # Status inconsistency warning
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">⚠️ {}</span>',
                status['phase'].title()
            )
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            status['phase'].title()
        )
    lifecycle_status.short_description = 'Lifecycle'
    
    def check_lifecycle_status(self, request, queryset):
        """Check and update lifecycle status for selected events"""
        updated_events = []
        
        for event in queryset:
            status = GroupChallengeManager.get_event_lifecycle_status(event)
            
            if not status['status_consistent']:
                # Update event status to match time-based status
                event.is_active = status['should_be_active']
                event.save()
                
                if status['should_be_active']:
                    # Activate group mode
                    GroupEventLifecycleManager._activate_group_mode(event)
                else:
                    # Deactivate if this was the active event
                    try:
                        platform_mode = PlatformMode.objects.get(mode='group')
                        if platform_mode.active_event == event:
                            GroupEventLifecycleManager._deactivate_group_mode()
                    except PlatformMode.DoesNotExist:
                        pass
                
                updated_events.append(event.name)
        
        if updated_events:
            self.message_user(
                request,
                f'Updated lifecycle status for: {", ".join(updated_events)}',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                'All selected events have consistent lifecycle status.',
                messages.INFO
            )
    
    check_lifecycle_status.short_description = '🔄 Check & update lifecycle status'
    
    def preserve_event_results(self, request, queryset):
        """Preserve results for selected events"""
        preserved_events = []
        
        for event in queryset:
            preservation_summary = GroupEventLifecycleManager.preserve_event_results(event)
            preserved_data = preservation_summary['preserved_data']
            
            preserved_events.append(
                f"{event.name} ({preserved_data['challenges_count']} challenges, "
                f"{preserved_data['submissions_count']} submissions, "
                f"{preserved_data['participating_teams_count']} teams)"
            )
        
        if preserved_events:
            self.message_user(
                request,
                f'Preserved results for: {"; ".join(preserved_events)}',
                messages.SUCCESS
            )
    
    preserve_event_results.short_description = '📦 Preserve event results'


@admin.register(GroupChallenge)
class GroupChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'category_badge', 'difficulty_badge', 'points', 'requires_collaboration', 'max_attempts_per_team', 'created_at']
    list_filter = ['event', 'category', 'difficulty', 'requires_collaboration']
    search_fields = ['title', 'description', 'event__name']
    ordering = ['-event__created_at', 'difficulty', 'points']
    
    fieldsets = (
        ('Challenge Information', {
            'fields': ('event', 'title', 'description', 'category', 'difficulty')
        }),
        ('Flag & Points', {
            'fields': ('flag', 'points'),
            'description': 'Enter the plain text flag for group challenges.'
        }),
        ('Group Challenge Settings', {
            'fields': ('requires_collaboration', 'max_attempts_per_team'),
            'description': 'Configure group-specific challenge settings.'
        }),
    )
    
    def get_queryset(self, request):
        """Filter to show only group challenges"""
        qs = super().get_queryset(request)
        return qs.select_related('event')
    
    def category_badge(self, obj):
        """Display category with color badge"""
        colors = {
            'web': '#3498db',
            'crypto': '#e74c3c',
            'forensics': '#2ecc71',
            'pwn': '#f39c12',
            'reverse': '#9b59b6',
            'misc': '#95a5a6',
        }
        color = colors.get(obj.category.lower(), '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.category.title()
        )
    category_badge.short_description = 'Category'
    
    def difficulty_badge(self, obj):
        """Display difficulty with color badge"""
        colors = {
            'easy': '#2ecc71',
            'medium': '#f39c12',
            'hard': '#e74c3c',
        }
        color = colors.get(obj.difficulty.lower(), '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.difficulty.title()
        )
    difficulty_badge.short_description = 'Difficulty'
    
    def save_model(self, request, obj, form, change):
        """Override save to add validation"""
        # Validate that the event exists and is appropriate for group challenges
        if not obj.event:
            raise ValidationError("Group challenges must be associated with a group event.")
        
        super().save_model(request, obj, form, change)
        
        if not change:  # New challenge
            self.message_user(
                request,
                f'Group challenge "{obj.title}" created for event "{obj.event.name}"!',
                messages.SUCCESS
            )


@admin.register(GroupSubmission)
class GroupSubmissionAdmin(admin.ModelAdmin):
    list_display = ['team', 'challenge', 'submitted_by', 'is_correct_badge', 'points_awarded', 'submitted_at']
    list_filter = ['is_correct', 'submitted_at', 'challenge__event', 'challenge__category']
    search_fields = ['team__name', 'challenge__title', 'submitted_by__username']
    ordering = ['-submitted_at']
    readonly_fields = ['team', 'challenge', 'submitted_by', 'flag_submitted', 'is_correct', 'submitted_at', 'points_awarded']
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('team', 'challenge', 'challenge__event', 'submitted_by')
    
    def is_correct_badge(self, obj):
        """Display submission result with badge"""
        if obj.is_correct:
            return format_html(
                '<span style="background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">✓ Correct</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">✗ Incorrect</span>'
            )
    is_correct_badge.short_description = 'Result'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent editing


@admin.register(PlatformMode)
class PlatformModeAdmin(admin.ModelAdmin):
    list_display = ['mode_badge', 'active_event', 'changed_by', 'changed_at']
    list_filter = ['mode', 'changed_at']
    readonly_fields = ['changed_at']
    
    fieldsets = (
        ('Platform Mode', {
            'fields': ('mode', 'active_event'),
            'description': 'Control the platform competition mode. Only one mode can be active at a time.'
        }),
        ('Metadata', {
            'fields': ('changed_by', 'changed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mode_badge(self, obj):
        """Display mode with color badge"""
        colors = {
            'individual': '#3498db',
            'group': '#e74c3c',
        }
        color = colors.get(obj.mode, '#95a5a6')
        icon = '👤' if obj.mode == 'individual' else '👥'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_mode_display()
        )
    mode_badge.short_description = 'Current Mode'
    
    def save_model(self, request, obj, form, change):
        """Override save to add validation and user tracking"""
        obj.changed_by = request.user
        
        # Validate mode consistency
        if obj.mode == 'group' and not obj.active_event:
            raise ValidationError("Group mode requires an active event.")
        elif obj.mode == 'individual' and obj.active_event:
            obj.active_event = None
        
        # Ensure only one PlatformMode instance exists
        if not change:
            PlatformMode.objects.all().delete()
        
        super().save_model(request, obj, form, change)
        
        # Update event status if needed
        if obj.mode == 'group' and obj.active_event:
            GroupEvent.objects.exclude(pk=obj.active_event.pk).update(is_active=False)
            obj.active_event.is_active = True
            obj.active_event.save()
        elif obj.mode == 'individual':
            GroupEvent.objects.update(is_active=False)
        
        mode_name = obj.get_mode_display()
        self.message_user(
            request,
            f'Platform mode set to {mode_name}!',
            messages.SUCCESS
        )
    
    def has_add_permission(self, request):
        # Only allow one PlatformMode instance
        return not PlatformMode.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion