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
    opportunity = models.ForeignKey('OpportunityTracking', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules', verbose_name="영업 기회")
    visit_date = models.DateField(verbose_name="방문 날짜")
    visit_time = models.TimeField(verbose_name="방문 시간")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="장소")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="상태")
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES, default='customer_meeting', verbose_name="일정 유형")
    notes = models.TextField(blank=True, null=True, verbose_name="메모")
    
    # 견적 관련 필드 (펀넬 시스템 연동)
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="예상 매출액", help_text="예상되는 거래 금액")
    probability = models.IntegerField(null=True, blank=True, verbose_name="성공 확률 (%)", help_text="0-100 사이의 값")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="예상 계약일", help_text="계약이 예상되는 날짜")
    
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


# ============================================
# 펀넬 관리 시스템 모델들
# ============================================

# 제품 (Product) 모델
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('equipment', '장비'),
        ('software', '소프트웨어'),
        ('service', '서비스'),
        ('maintenance', '유지보수'),
        ('consumable', '소모품'),
        ('other', '기타'),
    ]
    
    # 기본 정보
    product_code = models.CharField(max_length=50, unique=True, verbose_name="제품 코드")
    name = models.CharField(max_length=200, verbose_name="제품명")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="카테고리")
    
    # 가격
    standard_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="정상가")
    cost_price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="원가")
    
    # 프로모션
    is_promo = models.BooleanField(default=False, verbose_name="프로모션 여부")
    promo_price = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="프로모션 가격")
    promo_start = models.DateField(null=True, blank=True, verbose_name="프로모션 시작일")
    promo_end = models.DateField(null=True, blank=True, verbose_name="프로모션 종료일")
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name="판매 가능")
    
    # 설명
    description = models.TextField(blank=True, null=True, verbose_name="제품 설명")
    specifications = models.JSONField(default=dict, blank=True, verbose_name="제품 사양")
    
    # 통계
    total_quoted = models.IntegerField(default=0, verbose_name="총 견적 횟수")
    total_sold = models.IntegerField(default=0, verbose_name="총 판매 횟수")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return f"{self.name} ({self.product_code})"
    
    def get_current_price(self):
        """현재 적용 가격 반환 (프로모션 고려)"""
        from datetime import date
        if self.is_promo and self.promo_price:
            today = date.today()
            if self.promo_start and self.promo_end:
                if self.promo_start <= today <= self.promo_end:
                    return self.promo_price
        return self.standard_price
    
    class Meta:
        verbose_name = "제품"
        verbose_name_plural = "제품 목록"
        ordering = ['category', 'name']


# 견적 (Quote) 모델
class Quote(models.Model):
    STAGE_CHOICES = [
        ('draft', '초안'),
        ('sent', '발송완료'),
        ('review', '검토중'),
        ('negotiation', '협상중'),
        ('approved', '승인'),
        ('rejected', '거절'),
        ('expired', '만료'),
        ('converted', '계약전환'),
    ]
    
    # 기본 정보
    quote_number = models.CharField(max_length=50, unique=True, verbose_name="견적번호")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='quotes', verbose_name="관련 일정")
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='quotes', verbose_name="관련 고객")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자")
    
    # 견적 상세
    quote_date = models.DateField(auto_now_add=True, verbose_name="견적일")
    valid_until = models.DateField(verbose_name="유효기한")
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='draft', verbose_name="견적 상태")
    
    # 금액
    subtotal = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="소계")
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="할인율(%)")
    discount_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="할인액")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="부가세")
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="총액")
    
    # 영업 예측
    probability = models.IntegerField(default=50, verbose_name="성공 확률(%)")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="예상 계약일")
    weighted_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="가중 매출")
    
    # 전환 추적
    converted_to_delivery = models.BooleanField(default=False, verbose_name="납품 전환 여부")
    converted_history = models.ForeignKey(History, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name='source_quote', verbose_name="전환된 납품 기록")
    
    # 메모
    notes = models.TextField(blank=True, null=True, verbose_name="메모")
    customer_feedback = models.TextField(blank=True, null=True, verbose_name="고객 피드백")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # 할인액 계산
        if self.discount_rate > 0:
            self.discount_amount = self.subtotal * (Decimal(str(self.discount_rate)) / Decimal('100'))
        else:
            self.discount_amount = 0
        
        # 부가세 계산 (10%)
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = taxable_amount * Decimal('0.1')
        
        # 총액 계산
        self.total_amount = taxable_amount + self.tax_amount
        
        # 가중매출 계산
        self.weighted_revenue = self.total_amount * (Decimal(str(self.probability)) / Decimal('100'))
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quote_number} - {self.followup.customer_name}"
    
    class Meta:
        verbose_name = "견적"
        verbose_name_plural = "견적 목록"
        ordering = ['-quote_date']


# 견적 항목 (QuoteItem) 모델
class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items', verbose_name="견적")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="제품")
    
    # 수량 및 가격
    quantity = models.IntegerField(default=1, verbose_name="수량")
    unit_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="단가")
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="할인율(%)")
    subtotal = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="소계")
    
    # 메모
    description = models.TextField(blank=True, null=True, verbose_name="상세 설명")
    
    # 정렬
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # 소계 자동 계산
        base_amount = self.unit_price * self.quantity
        if self.discount_rate > 0:
            discount_amount = base_amount * (Decimal(str(self.discount_rate)) / Decimal('100'))
            self.subtotal = base_amount - discount_amount
        else:
            self.subtotal = base_amount
        
        super().save(*args, **kwargs)
        
        # 견적 총액 재계산
        quote = self.quote
        quote.subtotal = sum(item.subtotal for item in quote.items.all())
        quote.save()
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    class Meta:
        verbose_name = "견적 항목"
        verbose_name_plural = "견적 항목 목록"
        ordering = ['order', 'id']


# 펀넬 단계 (FunnelStage) 모델
class FunnelStage(models.Model):
    STAGE_CHOICES = [
        ('lead', '리드'),
        ('contact', '컨택'),
        ('quote', '견적'),
        ('negotiation', '협상'),
        ('closing', '클로징'),
        ('won', '수주'),
        ('lost', '실주'),
    ]
    
    name = models.CharField(max_length=20, choices=STAGE_CHOICES, unique=True, verbose_name="단계 코드")
    display_name = models.CharField(max_length=50, verbose_name="표시명")
    stage_order = models.IntegerField(unique=True, verbose_name="순서")
    
    # 통계 데이터
    default_probability = models.IntegerField(default=50, verbose_name="기본 확률(%)")
    avg_duration_days = models.IntegerField(default=7, verbose_name="평균 체류일")
    
    # UI
    color = models.CharField(max_length=20, default='#667eea', verbose_name="색상")
    icon = models.CharField(max_length=50, default='fa-circle', verbose_name="아이콘")
    
    # 설명
    description = models.TextField(blank=True, verbose_name="설명")
    success_criteria = models.TextField(blank=True, verbose_name="다음 단계 조건")
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        verbose_name = "펀넬 단계"
        verbose_name_plural = "펀넬 단계 목록"
        ordering = ['stage_order']


# 영업 기회 추적 (OpportunityTracking) 모델
class OpportunityTracking(models.Model):
    followup = models.OneToOneField(FollowUp, on_delete=models.CASCADE, related_name='opportunity', verbose_name="관련 고객")
    
    # 현재 상태
    current_stage = models.CharField(max_length=20, choices=FunnelStage.STAGE_CHOICES, default='lead', verbose_name="현재 단계")
    stage_entry_date = models.DateField(auto_now_add=True, verbose_name="단계 진입일")
    
    # 예측 데이터
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="예상 매출")
    weighted_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="가중 매출")
    probability = models.IntegerField(default=50, verbose_name="성공 확률(%)")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="예상 계약일")
    
    # 단계 이력 (JSON)
    stage_history = models.JSONField(default=list, verbose_name="단계 이력")
    
    # 통계
    total_quotes_sent = models.IntegerField(default=0, verbose_name="발송 견적 수")
    total_meetings = models.IntegerField(default=0, verbose_name="총 미팅 수")
    avg_response_time_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="평균 응답 시간(시간)")
    
    # 결과
    won_date = models.DateField(null=True, blank=True, verbose_name="수주일")
    lost_date = models.DateField(null=True, blank=True, verbose_name="실주일")
    lost_reason = models.TextField(blank=True, null=True, verbose_name="실주 사유")
    actual_revenue = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="실제 매출")
    
    # 타임스탬프
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def update_stage(self, new_stage):
        """단계 업데이트 및 이력 기록"""
        from datetime import date
        
        # 현재 단계 종료 처리
        if self.stage_history:
            for history in reversed(self.stage_history):
                if history.get('stage') == self.current_stage and not history.get('exited'):
                    history['exited'] = date.today().isoformat()
                    break
        
        # 새 단계 추가
        self.stage_history.append({
            'stage': new_stage,
            'entered': date.today().isoformat(),
            'exited': None
        })
        
        # 단계 정보 업데이트
        self.current_stage = new_stage
        self.stage_entry_date = date.today()
        
        # 단계별 기본 확률 설정
        try:
            stage_obj = FunnelStage.objects.get(name=new_stage)
            self.probability = stage_obj.default_probability
        except FunnelStage.DoesNotExist:
            pass
        
        self.save()
    
    def __str__(self):
        return f"{self.followup.customer_name} - {self.get_current_stage_display()}"
    
    class Meta:
        verbose_name = "영업 기회"
        verbose_name_plural = "영업 기회 목록"
