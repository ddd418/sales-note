from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    FollowUp, Schedule, History, UserProfile, HistoryFile, ScheduleFile, DeliveryItem,
    Product, Quote, QuoteItem, FunnelStage, OpportunityTracking, Prepayment, PrepaymentUsage,
    Company, Department, DocumentTemplate, EmailLog, BusinessCard, CustomerCategory
)

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

# Company 모델 관리자 설정
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_by', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 20

# Department 모델 관리자 설정
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'created_by', 'created_at')
    search_fields = ('name', 'company__name')
    list_filter = ('company', 'created_by', 'created_at')
    autocomplete_fields = ['company']
    date_hierarchy = 'created_at'
    list_per_page = 20

# CustomerCategory 모델 관리자 설정
@admin.register(CustomerCategory)
class CustomerCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'order', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('user', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 20

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

# DeliveryItem 모델 관리자 설정
@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'item_name', 'quantity', 'unit', 'unit_price', 'total_price', 'created_at')
    list_filter = ('schedule__activity_type', 'unit', 'created_at')
    search_fields = ('item_name', 'schedule__followup__customer_name', 'notes')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('schedule', 'schedule__followup') 


# ============================================
# 펀넬 관리 시스템 Admin
# ============================================

# Product 모델 관리자 설정
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'standard_price', 'is_promo', 'is_active', 'total_quoted', 'total_sold')
    list_filter = ('is_active', 'is_promo')
    search_fields = ('product_code', 'description')
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('product_code', 'description')
        }),
        ('가격 정보', {
            'fields': ('standard_price',)
        }),
        ('프로모션', {
            'fields': ('is_promo', 'promo_price', 'promo_start', 'promo_end'),
            'classes': ('collapse',)
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('통계', {
            'fields': ('total_quoted', 'total_sold'),
            'classes': ('collapse',)
        }),
        ('상세 정보', {
            'fields': ('specifications',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('total_quoted', 'total_sold')


# QuoteItem 인라인
class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'discount_rate', 'subtotal', 'description')
    readonly_fields = ('subtotal',)
    autocomplete_fields = ['product']


# Quote 모델 관리자 설정
@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'followup', 'user', 'stage', 'total_amount', 'probability', 'valid_until', 'converted_to_delivery', 'created_at')
    list_filter = ('stage', 'converted_to_delivery', 'user', 'quote_date')
    search_fields = ('quote_number', 'followup__customer_name', 'user__username')
    date_hierarchy = 'quote_date'
    autocomplete_fields = ['schedule', 'followup', 'user']
    inlines = [QuoteItemInline]
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('quote_number', 'schedule', 'followup', 'user', 'stage')
        }),
        ('일정', {
            'fields': ('quote_date', 'valid_until', 'expected_close_date')
        }),
        ('금액 정보', {
            'fields': ('subtotal', 'discount_rate', 'discount_amount', 'tax_amount', 'total_amount'),
            'description': '금액은 견적 항목 추가 시 자동 계산됩니다.'
        }),
        ('영업 예측', {
            'fields': ('probability', 'weighted_revenue')
        }),
        ('전환 추적', {
            'fields': ('converted_to_delivery', 'converted_history'),
            'classes': ('collapse',)
        }),
        ('메모', {
            'fields': ('notes', 'customer_feedback'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'weighted_revenue', 'quote_date')


# QuoteItem 모델 관리자 설정
@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('quote', 'product', 'quantity', 'unit_price', 'discount_rate', 'subtotal')
    list_filter = ('quote__stage',)
    search_fields = ('quote__quote_number', 'product__product_code')
    autocomplete_fields = ['quote', 'product']
    list_per_page = 20
    
    readonly_fields = ('subtotal',)


# FunnelStage 모델 관리자 설정
@admin.register(FunnelStage)
class FunnelStageAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'stage_order', 'default_probability', 'avg_duration_days', 'color', 'icon')
    list_editable = ('stage_order', 'default_probability', 'avg_duration_days')
    ordering = ('stage_order',)
    list_per_page = 20


# OpportunityTracking 모델 관리자 설정
@admin.register(OpportunityTracking)
class OpportunityTrackingAdmin(admin.ModelAdmin):
    list_display = ('followup', 'current_stage', 'expected_revenue', 'weighted_revenue', 'probability', 'expected_close_date', 'total_quotes_sent', 'total_meetings')
    list_filter = ('current_stage', 'followup__user', 'stage_entry_date')
    search_fields = ('followup__customer_name', 'followup__company__name')
    date_hierarchy = 'stage_entry_date'
    autocomplete_fields = ['followup']
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('followup', 'current_stage', 'stage_entry_date')
        }),
        ('예측 데이터', {
            'fields': ('expected_revenue', 'weighted_revenue', 'probability', 'expected_close_date')
        }),
        ('통계', {
            'fields': ('total_quotes_sent', 'total_meetings', 'avg_response_time_hours')
        }),
        ('결과', {
            'fields': ('won_date', 'lost_date', 'lost_reason', 'actual_revenue'),
            'classes': ('collapse',)
        }),
        ('단계 이력', {
            'fields': ('stage_history',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('stage_entry_date',)


# ============================================
# 선결제 관리 시스템 Admin
# ============================================

# PrepaymentUsage 인라인
class PrepaymentUsageInline(admin.TabularInline):
    model = PrepaymentUsage
    extra = 0
    fields = ('used_at', 'product_name', 'quantity', 'amount', 'remaining_balance', 'schedule')
    readonly_fields = ('used_at', 'remaining_balance')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# Prepayment 모델 관리자 설정
@admin.register(Prepayment)
class PrepaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'payment_date', 'amount', 'balance', 'payment_method', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_date', 'created_by')
    search_fields = ('customer__customer_name', 'company__name', 'payer_name', 'memo')
    date_hierarchy = 'payment_date'
    autocomplete_fields = ['customer', 'company', 'created_by']
    inlines = [PrepaymentUsageInline]
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('customer', 'company', 'created_by')
        }),
        ('금액 정보', {
            'fields': ('amount', 'balance')
        }),
        ('입금 정보', {
            'fields': ('payment_date', 'payment_method', 'payer_name')
        }),
        ('메모', {
            'fields': ('memo',)
        }),
        ('상태', {
            'fields': ('status',)
        }),
        ('취소 정보', {
            'fields': ('cancelled_at', 'cancel_reason'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.usages.exists():
            # 사용 내역이 있으면 금액 수정 불가
            return self.readonly_fields + ('amount', 'balance')
        return self.readonly_fields


# PrepaymentUsage 모델 관리자 설정
@admin.register(PrepaymentUsage)
class PrepaymentUsageAdmin(admin.ModelAdmin):
    list_display = ('prepayment', 'used_at', 'product_name', 'quantity', 'amount', 'remaining_balance', 'schedule')
    list_filter = ('used_at', 'prepayment__customer')
    search_fields = ('prepayment__customer__customer_name', 'product_name', 'memo')
    date_hierarchy = 'used_at'
    autocomplete_fields = ['prepayment', 'schedule', 'schedule_item']
    list_per_page = 20
    
    readonly_fields = ('used_at', 'remaining_balance')
    
    def has_add_permission(self, request):
        # Admin에서 직접 추가 불가 (뷰에서만 생성)
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 삭제 불가 (잔액 계산 무결성)
        return False


# DocumentTemplate 모델 관리자 설정
@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'document_type', 'file_type', 'is_default', 'is_active', 'created_by', 'created_at')
    list_filter = ('company', 'document_type', 'file_type', 'is_default', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'company__name')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('company', 'document_type', 'name', 'description')
        }),
        ('파일', {
            'fields': ('file', 'file_type')
        }),
        ('설정', {
            'fields': ('is_active', 'is_default')
        }),
        ('이메일 템플릿 (향후 사용)', {
            'fields': ('email_subject_template', 'email_body_template'),
            'classes': ('collapse',)
        }),
        ('메타 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# EmailLog 모델 관리자 설정
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'email_type', 'sender_email', 'recipient_email', 'status', 'is_read', 'sent_at', 'created_at')
    list_filter = ('email_type', 'status', 'is_read', 'sent_at', 'created_at')
    search_fields = ('subject', 'sender_email', 'recipient_email', 'body_text', 'gmail_message_id')
    date_hierarchy = 'sent_at'
    autocomplete_fields = ['followup', 'schedule', 'business_card', 'in_reply_to']
    list_per_page = 20
    
    readonly_fields = ('created_at', 'sent_at', 'gmail_message_id', 'gmail_thread_id')
    
    fieldsets = (
        ('이메일 유형', {
            'fields': ('email_type', 'is_read')
        }),
        ('발신/수신 정보', {
            'fields': ('sender', 'sender_email', 'recipient_email', 'recipient_name', 'cc_emails', 'bcc_emails')
        }),
        ('메일 내용', {
            'fields': ('subject', 'body_text', 'body_html')
        }),
        ('첨부 파일', {
            'fields': ('document_template', 'attachment')
        }),
        ('Gmail 정보', {
            'fields': ('gmail_message_id', 'gmail_thread_id', 'in_reply_to'),
            'classes': ('collapse',)
        }),
        ('명함', {
            'fields': ('business_card',),
            'classes': ('collapse',)
        }),
        ('연결 정보', {
            'fields': ('followup', 'schedule')
        }),
        ('발송 상태', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
        ('메타 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Admin에서 직접 추가 불가 (뷰에서만 생성)
        return False


# BusinessCard 모델 관리자 설정
@admin.register(BusinessCard)
class BusinessCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'full_name', 'title', 'company_name', 'email', 'is_default', 'is_active', 'created_at')
    list_filter = ('is_default', 'is_active', 'created_at')
    search_fields = ('name', 'full_name', 'email', 'company_name', 'user__username')
    autocomplete_fields = ['user']
    list_per_page = 20
    
    readonly_fields = ('created_at', 'updated_at', 'signature_html')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'name', 'is_default', 'is_active')
        }),
        ('개인 정보', {
            'fields': ('full_name', 'title', 'company_name')
        }),
        ('연락처', {
            'fields': ('phone', 'mobile', 'email', 'website')
        }),
        ('주소', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('이메일 서명', {
            'fields': ('signature_html',),
            'classes': ('collapse',),
            'description': '이메일 발송 시 자동으로 추가되는 서명 HTML (자동 생성됨)'
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
