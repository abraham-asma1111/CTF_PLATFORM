from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Challenge

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_badge', 'difficulty_badge', 'points', 'status_badge', 'created_at']
    list_filter = ['category', 'difficulty', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'flag']
    ordering = ['-created_at']
    actions = ['make_active', 'make_inactive']
    
    fieldsets = (
        ('Challenge Information', {
            'fields': ('title', 'description', 'category', 'difficulty')
        }),
        ('Flag & Points', {
            'fields': ('flag', 'points'),
            'description': 'Enter the plain text flag. It will be automatically hashed for security.'
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
    
    def save_model(self, request, obj, form, change):
        """Override save to add audit trail"""
        if not change:
            # New challenge created
            pass
        super().save_model(request, obj, form, change)
    
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
