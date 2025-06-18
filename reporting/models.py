from django.db import models
from django.contrib.auth.models import User # Django의 기본 사용자 모델

# 사용자 프로필 (UserProfile) 모델 - 권한 관리
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin (최고권한자)'),
        ('manager', 'Manager (뷰어)'),
        ('salesman', 'SalesMan (실무자)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="사용자")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesman', verbose_name="권한")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_users', verbose_name="계정 생성자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_salesman(self):
        return self.role == 'salesman'
    
    def can_view_all_users(self):
        """모든 사용자 데이터를 볼 수 있는지 확인"""
        return self.role in ['admin', 'manager']
    
    def can_create_users(self):
        """사용자를 생성할 수 있는지 확인"""
        return self.role == 'admin'
    
    def can_edit_user(self, target_user):
        """특정 사용자를 편집할 수 있는지 확인"""
        if self.role == 'admin':
            return True
        return self.user == target_user
    
    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필 목록"
        ordering = ['role', 'user__username']

# 팔로우업 (FollowUp) 모델
class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('active', '진행중'),
        ('completed', '완료'),
        ('paused', '일시중지'),
    ]
    PRIORITY_CHOICES = [
        ('high', '높음'),
        ('medium', '보통'),
        ('low', '낮음'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자")
    customer_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="고객명")
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name="업체/학교명")
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="부서/연구실명")
    manager = models.CharField(max_length=100, blank=True, null=True, verbose_name="책임자")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="핸드폰 번호")
    email = models.EmailField(blank=True, null=True, verbose_name="메일 주소")
    address = models.TextField(blank=True, null=True, verbose_name="상세주소")
    notes = models.TextField(blank=True, null=True, verbose_name="상세 내용")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="상태")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="우선순위")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        display_name = self.customer_name or "고객명 미정"
        company_name = self.company or "업체명 미정"
        return f"{display_name} ({company_name}) - {self.user.username}"

    class Meta:
        verbose_name = "팔로우업"
        verbose_name_plural = "팔로우업 목록"
        ordering = ['-created_at']

# 일정 (Schedule) 모델
class Schedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '예정됨'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자")
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='schedules', verbose_name="관련 팔로우업")
    visit_date = models.DateField(verbose_name="방문 날짜")
    visit_time = models.TimeField(verbose_name="방문 시간")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="장소")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="상태")
    notes = models.TextField(blank=True, null=True, verbose_name="메모")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return f"{self.followup.customer_name} 방문 - {self.visit_date} {self.visit_time}"

    class Meta:
        verbose_name = "일정"
        verbose_name_plural = "일정 목록"
        ordering = ['visit_date', 'visit_time']

# 히스토리 (History) 모델
class History(models.Model):
    ACTION_CHOICES = [
        ('customer_meeting', '고객 미팅'),
        ('delivery_schedule', '납품 일정'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="활동 사용자")
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='histories', verbose_name="관련 고객 정보")
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, blank=True, null=True, related_name='histories', verbose_name="관련 일정")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="활동 유형")
    content = models.TextField(blank=True, null=True, verbose_name="내용")
    delivery_amount = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="납품 금액 (원)", help_text="납품 일정인 경우 금액을 입력하세요 (0원 입력 가능)")
    delivery_items = models.TextField(blank=True, null=True, verbose_name="납품 품목", help_text="납품 일정인 경우 품목을 입력하세요")
    delivery_date = models.DateField(blank=True, null=True, verbose_name="납품 날짜", help_text="납품 일정인 경우 실제 납품 날짜를 입력하세요")
    meeting_date = models.DateField(blank=True, null=True, verbose_name="미팅 날짜", help_text="고객 미팅인 경우 실제 미팅 날짜를 입력하세요")
    tax_invoice_issued = models.BooleanField(default=False, verbose_name="세금계산서 발행 여부")
    old_value = models.TextField(blank=True, null=True, verbose_name="이전 값")
    new_value = models.TextField(blank=True, null=True, verbose_name="새로운 값")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="활동 시간")

    def __str__(self):
        return f"{self.followup.customer_name} - {self.get_action_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "활동 히스토리"
        verbose_name_plural = "활동 히스토리 목록"
        ordering = ['-created_at']
