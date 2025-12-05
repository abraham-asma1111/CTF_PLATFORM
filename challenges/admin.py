from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Challenge, Hint, HintView


class HintInline(admin.TabularInline):
    """Inline admin for hints"""
    model = Hint
    extra = 1
    fields = ['order', 'content', 'cost']
    ordering = ['order']


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_badge', 'difficulty_badge', 'points', 'hints_count', 'status_badge', 'created_at']
    list_filter = ['category', 'difficulty', 'is_active', 'created_at']
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
