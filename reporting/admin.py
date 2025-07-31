from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import FollowUp, Schedule, History, UserProfile, HistoryFile, ScheduleFile

# UserProfile 인라인 관리자
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '사용자 프로필'
    fk_name = 'user'  # 메인 User와 연결되는 필드 지정

# User 모델 확장 관리자
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__role')
    
    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except UserProfile.DoesNotExist:
            return '프로필 없음'
    get_role.short_description = '권한'

# 기존 User 관리자 해제 후 새로운 관리자 등록
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# UserProfile 모델 관리자 설정
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_by', 'created_at')
    list_filter = ('role', 'created_by')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'created_at'
    list_per_page = 20

# FollowUp 모델 관리자 설정
@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'company', 'user', 'status', 'priority', 'created_at', 'updated_at')
    list_filter = ('status', 'priority', 'user')
    search_fields = ('customer_name', 'company', 'user__username')
    date_hierarchy = 'created_at'
    list_per_page = 20

# Schedule 모델 관리자 설정
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('followup', 'user', 'visit_date', 'visit_time', 'location', 'status', 'created_at')
    list_filter = ('status', 'user', 'visit_date')
    search_fields = ('followup__customer_name', 'followup__company', 'user__username', 'location')
    date_hierarchy = 'visit_date'
    autocomplete_fields = ['followup', 'user'] # ForeignKey 필드 검색 기능 향상
    list_per_page = 20

# History 모델 관리자 설정
@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('followup', 'user', 'action_type', 'service_status', 'delivery_amount', 'delivery_items_short', 'created_at_formatted', 'schedule')
    list_filter = ('action_type', 'service_status', 'user', 'created_at', 'tax_invoice_issued')
    search_fields = ('followup__customer_name', 'user__username', 'content', 'delivery_items')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['followup', 'user', 'schedule']
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'followup', 'schedule', 'action_type', 'service_status', 'content', 'created_at')
        }),
        ('납품 관련 정보', {
            'fields': ('delivery_amount', 'delivery_items', 'delivery_date', 'tax_invoice_issued'),
            'classes': ('collapse',),
            'description': '활동 유형이 "납품 일정"인 경우에만 해당'
        }),
        ('미팅 관련 정보', {
            'fields': ('meeting_date',),
            'classes': ('collapse',),
            'description': '활동 유형이 "고객 미팅"인 경우에만 해당'
        }),
        ('변경 추적', {
            'fields': ('old_value', 'new_value'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.admin_order_field = 'created_at'
    created_at_formatted.short_description = '활동 시간'
    
    def delivery_items_short(self, obj):
        if obj.delivery_items:
            return obj.delivery_items[:50] + '...' if len(obj.delivery_items) > 50 else obj.delivery_items
        return '-'
    delivery_items_short.short_description = '납품 품목'

# HistoryFile 모델 관리자 설정
@admin.register(HistoryFile)
class HistoryFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'history', 'file_size_display', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_by', 'uploaded_at')
    search_fields = ('original_filename', 'history__followup__customer_name', 'uploaded_by__username')
    date_hierarchy = 'uploaded_at'
    autocomplete_fields = ['history', 'uploaded_by']
    readonly_fields = ('file_size', 'uploaded_at')
    list_per_page = 20
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '파일 크기'


# ScheduleFile 모델 관리자 설정
@admin.register(ScheduleFile)
class ScheduleFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'schedule', 'file_size_display', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_by', 'uploaded_at')
    search_fields = ('original_filename', 'schedule__followup__customer_name', 'uploaded_by__username')
    date_hierarchy = 'uploaded_at'
    autocomplete_fields = ['schedule', 'uploaded_by']
    readonly_fields = ('file_size', 'uploaded_at')
    list_per_page = 20
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '파일 크기'
