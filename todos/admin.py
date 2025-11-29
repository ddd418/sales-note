from django.contrib import admin
from .models import Todo, TodoAttachment, TodoLog


class TodoAttachmentInline(admin.TabularInline):
    model = TodoAttachment
    extra = 0
    readonly_fields = ['file_size', 'uploaded_at', 'uploaded_by']


class TodoLogInline(admin.TabularInline):
    model = TodoLog
    extra = 0
    readonly_fields = ['actor', 'action_type', 'message', 'prev_status', 'new_status', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'source_type', 'created_by', 'assigned_to', 'due_date', 'created_at']
    list_filter = ['status', 'source_type', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'created_by__username', 'assigned_to__username']
    date_hierarchy = 'created_at'
    raw_id_fields = ['created_by', 'assigned_to', 'requested_by', 'related_client']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    inlines = [TodoAttachmentInline, TodoLogInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'description', 'status', 'source_type')
        }),
        ('담당자', {
            'fields': ('created_by', 'assigned_to', 'requested_by')
        }),
        ('일정', {
            'fields': ('expected_duration', 'due_date', 'completed_at')
        }),
        ('연결 정보', {
            'fields': ('related_client',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TodoAttachment)
class TodoAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'todo', 'file_size', 'uploaded_at', 'uploaded_by']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'todo__title']
    raw_id_fields = ['todo', 'uploaded_by']


@admin.register(TodoLog)
class TodoLogAdmin(admin.ModelAdmin):
    list_display = ['todo', 'action_type', 'actor', 'message', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['todo__title', 'message', 'actor__username']
    raw_id_fields = ['todo', 'actor']
    readonly_fields = ['todo', 'actor', 'action_type', 'message', 'prev_status', 'new_status', 'created_at']
