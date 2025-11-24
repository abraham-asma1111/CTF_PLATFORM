from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'is_correct', 'timestamp']
    list_filter = ['is_correct', 'challenge__category', 'timestamp']
    search_fields = ['user__username', 'challenge__title']
    readonly_fields = ['timestamp']
