from django.db import models
from django.contrib.auth.models import User # Django의 기본 사용자 모델

# 사용자 소속 회사 (UserCompany) 모델 - 직원들의 소속 회사
class UserCompany(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="회사명")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "사용자 소속 회사"
        verbose_name_plural = "사용자 소속 회사 목록"
        ordering = ['name']

# 업체/학교 (Company) 모델 - 고객사
class Company(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="업체/학교명")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="생성자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "업체/학교"
        verbose_name_plural = "업체/학교 목록"
        ordering = ['name']

# 부서/연구실 (Department) 모델
class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name="업체/학교")
    name = models.CharField(max_length=100, verbose_name="부서/연구실명")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="생성자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "부서/연구실"
        verbose_name_plural = "부서/연구실 목록"
        unique_together = ['company', 'name']
        ordering = ['company__name', 'name']

# 사용자 프로필 (UserProfile) 모델 - 권한 관리
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin (최고권한자)'),
        ('manager', 'Manager (뷰어)'),
        ('salesman', 'SalesMan (실무자)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="사용자")
    company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, null=True, blank=True, verbose_name="소속 회사")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesman', verbose_name="권한")
    can_download_excel = models.BooleanField(default=False, verbose_name="엑셀 다운로드 권한")
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
    
    def can_excel_download(self):
        """엑셀 다운로드가 가능한지 확인 (관리자는 항상 가능, 다른 사용자는 개별 권한)"""
        return self.role == 'admin' or self.can_download_excel
    
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
        ('one_month', '한달'),
        ('three_months', '세달'),
        ('long_term', '장기'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자")
    user_company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, null=True, blank=True, verbose_name="담당자 소속 회사")
    customer_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="고객명")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='followup_companies', verbose_name="업체/학교명")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='followup_departments', verbose_name="부서/연구실명")
    manager = models.CharField(max_length=100, blank=True, null=True, verbose_name="책임자")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="핸드폰 번호")
    email = models.EmailField(blank=True, null=True, verbose_name="메일 주소")
    address = models.TextField(blank=True, null=True, verbose_name="상세주소")
    notes = models.TextField(blank=True, null=True, verbose_name="상세 내용")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="상태")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='long_term', verbose_name="우선순위")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        display_name = self.customer_name or "고객명 미정"
        company_name = self.company.name if self.company else "업체명 미정"
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
    
    ACTIVITY_TYPE_CHOICES = [
        ('customer_meeting', '고객 미팅'),
        ('delivery', '납품 일정'),
        ('service', '서비스'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자")
    company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, null=True, blank=True, verbose_name="소속 회사")
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='schedules', verbose_name="관련 팔로우업")
    visit_date = models.DateField(verbose_name="방문 날짜")
    visit_time = models.TimeField(verbose_name="방문 시간")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="장소")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="상태")
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES, default='customer_meeting', verbose_name="일정 유형")
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
        ('service', '서비스'),
        ('memo', '메모'),
    ]
    
    SERVICE_STATUS_CHOICES = [
        ('received', '접수'),
        ('in_progress', '진행중'),
        ('cancelled', '취소'),
        ('completed', '완료'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="활동 사용자")
    company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, null=True, blank=True, verbose_name="소속 회사")
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='histories', verbose_name="관련 고객 정보", blank=True, null=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, blank=True, null=True, related_name='histories', verbose_name="관련 일정")
    parent_history = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, 
                                     related_name='reply_memos', verbose_name="부모 히스토리",
                                     help_text="댓글 메모의 경우 원본 히스토리를 참조합니다")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="활동 유형")
    service_status = models.CharField(max_length=20, choices=SERVICE_STATUS_CHOICES, default='received', blank=True, null=True, verbose_name="서비스 상태", help_text="서비스 활동인 경우에만 해당")
    content = models.TextField(blank=True, null=True, verbose_name="내용")
    delivery_amount = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="납품 금액 (원)", help_text="납품 일정인 경우 금액을 입력하세요 (0원 입력 가능)")
    delivery_items = models.TextField(blank=True, null=True, verbose_name="납품 품목", help_text="납품 일정인 경우 품목을 입력하세요")
    delivery_date = models.DateField(blank=True, null=True, verbose_name="납품 날짜", help_text="납품 일정인 경우 실제 납품 날짜를 입력하세요")
    meeting_date = models.DateField(blank=True, null=True, verbose_name="미팅 날짜", help_text="고객 미팅인 경우 실제 미팅 날짜를 입력하세요")
    tax_invoice_issued = models.BooleanField(default=False, verbose_name="세금계산서 발행 여부")
    old_value = models.TextField(blank=True, null=True, verbose_name="이전 값")
    new_value = models.TextField(blank=True, null=True, verbose_name="새로운 값")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='created_histories', verbose_name="실제 작성자",
                                   help_text="매니저가 작성한 메모인 경우 매니저 정보가 저장됩니다")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="활동 시간")

    def __str__(self):
        followup_name = self.followup.customer_name if self.followup else "일반 메모"
        return f"{followup_name} - {self.get_action_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def get_files_summary(self):
        """첨부파일 요약 정보 반환"""
        file_count = self.files.count()
        if file_count == 0:
            return "파일: 없음"
        elif file_count == 1:
            first_file = self.files.first()
            return f'파일: "{first_file.original_filename}"'
        else:
            first_file = self.files.first()
            return f'파일: "{first_file.original_filename}" 외 {file_count - 1}개'
    
    def is_manager_memo(self):
        """매니저 메모인지 확인"""
        if not self.parent_history or self.action_type != 'memo':
            return False
        # created_by가 있고 실제 담당자와 다르면 매니저 메모
        return self.created_by and self.created_by != self.user
    
    def is_reply_memo(self):
        """답글 메모인지 확인 (매니저 메모 + 실무자 메모)"""
        return self.parent_history and self.action_type == 'memo'
    
    def get_memo_author(self):
        """메모 작성자 반환"""
        if self.is_manager_memo():
            return self.created_by
        return self.user

    class Meta:
        verbose_name = "활동 히스토리"
        verbose_name_plural = "활동 히스토리 목록"
        ordering = ['-created_at']

# 히스토리 첨부파일 (HistoryFile) 모델
class HistoryFile(models.Model):
    history = models.ForeignKey(History, on_delete=models.CASCADE, related_name='files', verbose_name="관련 히스토리")
    file = models.FileField(upload_to='history_files/%Y/%m/', verbose_name="첨부파일")
    original_filename = models.CharField(max_length=255, verbose_name="원본 파일명")
    file_size = models.PositiveIntegerField(verbose_name="파일 크기 (bytes)")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="업로드한 사용자")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드 시간")

    def __str__(self):
        return f"{self.original_filename} ({self.history})"

    def get_file_size_display(self):
        """파일 크기를 읽기 쉬운 형태로 표시"""
        size = self.file_size
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    class Meta:
        verbose_name = "히스토리 첨부파일"
        verbose_name_plural = "히스토리 첨부파일 목록"
        ordering = ['-uploaded_at']


class ScheduleFile(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='files', verbose_name="관련 일정")
    file = models.FileField(upload_to='schedule_files/%Y/%m/', verbose_name="첨부파일")
    original_filename = models.CharField(max_length=255, verbose_name="원본 파일명")
    file_size = models.PositiveIntegerField(verbose_name="파일 크기 (bytes)")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="업로드한 사용자")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드 시간")

    def __str__(self):
        return f"{self.original_filename} ({self.schedule})"

    def get_file_size_display(self):
        """파일 크기를 읽기 쉬운 형태로 표시"""
        size = self.file_size
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    class Meta:
        verbose_name = "일정 첨부파일"
        verbose_name_plural = "일정 첨부파일 목록"
        ordering = ['-uploaded_at']

# 납품 품목 (DeliveryItem) 모델
class DeliveryItem(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='delivery_items_set', verbose_name="일정", blank=True, null=True)
    history = models.ForeignKey(History, on_delete=models.CASCADE, related_name='delivery_items_set', verbose_name="히스토리", blank=True, null=True)
    item_name = models.CharField(max_length=200, verbose_name="품목명")
    quantity = models.PositiveIntegerField(verbose_name="수량")
    unit = models.CharField(max_length=50, default="개", verbose_name="단위")
    unit_price = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="단가")
    total_price = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="총액")
    tax_invoice_issued = models.BooleanField(default=False, verbose_name="세금계산서 발행여부")
    notes = models.TextField(blank=True, null=True, verbose_name="비고")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def save(self, *args, **kwargs):
        # 총액 자동 계산 (부가세 10% 포함)
        if self.unit_price and self.quantity:
            from decimal import Decimal
            subtotal = self.unit_price * self.quantity
            self.total_price = subtotal * Decimal('1.1')  # 부가세 10% 추가
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} ({self.quantity}{self.unit})"

    class Meta:
        verbose_name = "납품 품목"
        verbose_name_plural = "납품 품목 목록"
        ordering = ['created_at']
