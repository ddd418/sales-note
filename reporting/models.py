from django.db import models
from django.contrib.auth.models import User # Django의 기본 사용자 모델
from django.db.models import Sum

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
    
    # AI 기능 사용 권한
    can_use_ai = models.BooleanField(default=False, verbose_name="AI 기능 사용 권한", 
                                      help_text="AI 이메일 생성, 고객 분석, 자동 요약 등 GPT 기능 사용 가능 여부")
    
    # Gmail 연동 정보
    gmail_token = models.JSONField(null=True, blank=True, verbose_name="Gmail OAuth 토큰", help_text="암호화된 토큰 저장")
    gmail_email = models.EmailField(blank=True, verbose_name="연결된 Gmail 주소")
    gmail_connected_at = models.DateTimeField(null=True, blank=True, verbose_name="Gmail 연결 일시")
    gmail_last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name="마지막 동기화 일시")
    
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
        ('urgent', '긴급'),
        ('followup', '팔로업'),
        ('scheduled', '예정'),
        ('long_term', '장기'),
    ]
    
    CUSTOMER_GRADE_CHOICES = [
        ('VIP', 'VIP (최우수 고객)'),
        ('A', 'A (우수 고객)'),
        ('B', 'B (일반 고객)'),
        ('C', 'C (잠재 고객)'),
        ('D', 'D (저관심 고객)'),
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
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='scheduled', verbose_name="우선순위")
    
    # AI 기반 고객 등급 시스템
    customer_grade = models.CharField(
        max_length=10, 
        choices=CUSTOMER_GRADE_CHOICES, 
        default='C', 
        verbose_name="고객 등급",
        help_text="AI가 자동 산정하는 고객 등급 (VIP/A/B/C/D)"
    )
    ai_score = models.IntegerField(
        default=50,
        verbose_name="AI 점수",
        help_text="0-100점, 거래 실적/수주율/응답성 등 종합 평가"
    )
    grade_metrics = models.JSONField(
        default=dict,
        verbose_name="등급 산정 기준",
        help_text="등급이 어떻게 계산되었는지 저장 (투명성)"
    )
    last_grade_updated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="등급 갱신일",
        help_text="마지막으로 AI 등급이 계산된 시점"
    )
    
    # AI 등급 상세 정보 (새로운 AI 시스템용)
    ai_grade_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="AI 등급 점수",
        help_text="GPT 기반 등급 점수 (0-100)"
    )
    ai_grade_reasoning = models.TextField(
        null=True,
        blank=True,
        verbose_name="AI 등급 평가 근거",
        help_text="GPT가 생성한 등급 평가 근거"
    )
    ai_grade_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="AI 등급 갱신일",
        help_text="GPT 기반 등급이 마지막으로 업데이트된 시점"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        display_name = self.customer_name or "고객명 미정"
        company_name = self.company.name if self.company else "업체명 미정"
        return f"{display_name} ({company_name}) - {self.user.username}"
    
    def calculate_customer_grade(self):
        """
        AI 기반 고객 등급 자동 산정
        펀넬 데이터, 거래 실적, 활동 이력을 종합하여 계산
        """
        from datetime import datetime, timedelta
        from django.db.models import Sum, Count, Avg, Q
        from decimal import Decimal
        
        metrics = {
            'total_revenue': 0,  # 총 매출액
            'won_count': 0,  # 수주 건수
            'lost_count': 0,  # 실주 건수
            'win_rate': 0,  # 수주율 (%)
            'avg_deal_size': 0,  # 평균 거래액
            'total_quotes': 0,  # 총 견적 수
            'total_meetings': 0,  # 총 미팅 수
            'avg_response_time': 0,  # 평균 응답 시간
            'recent_activity': 0,  # 최근 활동 점수
            'growth_rate': 0,  # 성장률
        }
        
        score = 0
        
        # 1. 펀넬 데이터 분석 (OpportunityTracking)
        opportunities = self.opportunities.all()
        won_opps = opportunities.filter(current_stage='won')
        lost_opps = opportunities.filter(current_stage__in=['lost', 'quote_lost'])
        
        if opportunities.exists():
            metrics['won_count'] = won_opps.count()
            metrics['lost_count'] = lost_opps.count()
            
            total_opps = metrics['won_count'] + metrics['lost_count']
            if total_opps > 0:
                metrics['win_rate'] = round((metrics['won_count'] / total_opps) * 100, 1)
            
            # 실제 매출 합계
            total_revenue = won_opps.aggregate(
                total=Sum('actual_revenue')
            )['total'] or 0
            metrics['total_revenue'] = float(total_revenue)
            
            if metrics['won_count'] > 0:
                metrics['avg_deal_size'] = metrics['total_revenue'] / metrics['won_count']
            
            # 평균 응답 시간
            avg_response = opportunities.aggregate(
                avg=Avg('avg_response_time_hours')
            )['avg']
            if avg_response:
                metrics['avg_response_time'] = float(avg_response)
            
            # 견적 및 미팅 수
            metrics['total_quotes'] = opportunities.aggregate(
                total=Sum('total_quotes_sent')
            )['total'] or 0
            metrics['total_meetings'] = opportunities.aggregate(
                total=Sum('total_meetings')
            )['total'] or 0
        
        # 2. 최근 3개월 활동 분석
        three_months_ago = datetime.now().date() - timedelta(days=90)
        recent_schedules = self.schedules.filter(
            visit_date__gte=three_months_ago,
            status='completed'
        ).count()
        metrics['recent_activity'] = recent_schedules
        
        # 3. 성장률 계산 (최근 3개월 vs 이전 3개월)
        six_months_ago = datetime.now().date() - timedelta(days=180)
        
        recent_revenue = won_opps.filter(
            won_date__gte=three_months_ago
        ).aggregate(total=Sum('actual_revenue'))['total'] or 0
        
        old_revenue = won_opps.filter(
            won_date__gte=six_months_ago,
            won_date__lt=three_months_ago
        ).aggregate(total=Sum('actual_revenue'))['total'] or 0
        
        if old_revenue > 0:
            metrics['growth_rate'] = round(((float(recent_revenue) - float(old_revenue)) / float(old_revenue)) * 100, 1)
        elif recent_revenue > 0:
            metrics['growth_rate'] = 100  # 신규 고객
        
        # 4. AI 점수 계산 (0-100점)
        
        # 매출액 점수 (0-30점)
        if metrics['total_revenue'] >= 100000000:  # 1억 이상
            score += 30
        elif metrics['total_revenue'] >= 50000000:  # 5천만 이상
            score += 25
        elif metrics['total_revenue'] >= 10000000:  # 1천만 이상
            score += 20
        elif metrics['total_revenue'] >= 5000000:  # 500만 이상
            score += 15
        elif metrics['total_revenue'] > 0:
            score += 10
        
        # 수주율 점수 (0-25점)
        if metrics['win_rate'] >= 70:
            score += 25
        elif metrics['win_rate'] >= 50:
            score += 20
        elif metrics['win_rate'] >= 30:
            score += 15
        elif metrics['win_rate'] > 0:
            score += 10
        
        # 최근 활동 점수 (0-20점)
        if metrics['recent_activity'] >= 10:
            score += 20
        elif metrics['recent_activity'] >= 5:
            score += 15
        elif metrics['recent_activity'] >= 3:
            score += 10
        elif metrics['recent_activity'] > 0:
            score += 5
        
        # 성장률 점수 (0-15점)
        if metrics['growth_rate'] >= 50:
            score += 15
        elif metrics['growth_rate'] >= 20:
            score += 12
        elif metrics['growth_rate'] >= 0:
            score += 8
        elif metrics['growth_rate'] >= -20:
            score += 4
        
        # 거래 빈도 점수 (0-10점)
        if metrics['won_count'] >= 10:
            score += 10
        elif metrics['won_count'] >= 5:
            score += 8
        elif metrics['won_count'] >= 3:
            score += 6
        elif metrics['won_count'] > 0:
            score += 4
        
        # 5. 등급 산정
        if score >= 80:
            grade = 'VIP'
        elif score >= 65:
            grade = 'A'
        elif score >= 45:
            grade = 'B'
        elif score >= 25:
            grade = 'C'
        else:
            grade = 'D'
        
        # 6. 저장
        from django.utils import timezone
        self.ai_score = score
        self.customer_grade = grade
        self.grade_metrics = metrics
        self.last_grade_updated = timezone.now()
        self.save(update_fields=['ai_score', 'customer_grade', 'grade_metrics', 'last_grade_updated'])
        
        return {
            'grade': grade,
            'score': score,
            'metrics': metrics
        }
    
    def get_grade_badge_color(self):
        """등급별 뱃지 색상 반환"""
        colors = {
            'VIP': '#FFD700',  # 금색
            'A': '#C0C0C0',    # 은색
            'B': '#CD7F32',    # 동색
            'C': '#4A90E2',    # 파랑
            'D': '#95A5A6',    # 회색
        }
        return colors.get(self.customer_grade, '#95A5A6')
    
    def get_priority_score(self):
        """
        우선순위 점수 계산 (종합 점수용)
        긴급: 30점, 팔로업: 20점, 예정: 10점
        """
        priority_scores = {
            'urgent': 30,
            'followup': 20,
            'scheduled': 10,
        }
        return priority_scores.get(self.priority, 0)
    
    def get_combined_score(self):
        """
        고객 등급(AI 점수)과 우선순위를 결합한 종합 점수
        - AI 점수 (0-100점): 70% 가중치
        - 우선순위 점수 (0-30점): 30% 가중치
        최종 점수: 0-100점
        """
        ai_component = self.ai_score * 0.7  # AI 점수의 70%
        priority_component = self.get_priority_score()  # 우선순위 점수 (최대 30점)
        
        total_score = ai_component + priority_component
        return round(min(100, total_score), 1)
    
    def get_priority_level(self):
        """
        종합 점수 기반 우선순위 레벨
        """
        score = self.get_combined_score()
        
        if score >= 85:
            return {
                'level': 'critical',
                'label': '최우선',
                'color': '#dc3545',  # 빨강
                'icon': '🔥',
                'action': '즉시 대응'
            }
        elif score >= 70:
            return {
                'level': 'high',
                'label': '높음',
                'color': '#fd7e14',  # 주황
                'icon': '⚡',
                'action': '24시간 내'
            }
        elif score >= 50:
            return {
                'level': 'medium',
                'label': '중간',
                'color': '#ffc107',  # 노랑
                'icon': '⭐',
                'action': '주간 관리'
            }
        elif score >= 30:
            return {
                'level': 'low',
                'label': '낮음',
                'color': '#28a745',  # 초록
                'icon': '📋',
                'action': '월간 관리'
            }
        else:
            return {
                'level': 'minimal',
                'label': '최소',
                'color': '#6c757d',  # 회색
                'icon': '📌',
                'action': '분기 관리'
            }

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
        ('quote', '견적 제출'),
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
    purchase_confirmed = models.BooleanField(default=False, verbose_name="구매 확정", help_text="구매가 확정된 경우 체크 (클로징 단계로 전환)")
    
    # 선결제 관련 필드
    use_prepayment = models.BooleanField(default=False, verbose_name="선결제 사용", help_text="선결제 잔액에서 차감하는 경우 체크")
    prepayment = models.ForeignKey('Prepayment', on_delete=models.SET_NULL, null=True, blank=True, related_name='used_schedules', verbose_name="사용한 선결제")
    prepayment_amount = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="선결제 사용 금액", help_text="선결제에서 차감된 금액")
    
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
        ('quote', '견적'),
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
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, blank=True, null=True, related_name='histories', verbose_name="관련 일정")
    personal_schedule = models.ForeignKey('PersonalSchedule', on_delete=models.CASCADE, blank=True, null=True, related_name='histories', verbose_name="관련 개인 일정", help_text="개인 일정에 대한 댓글")
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
    
    # 제품 마스터 연동 (기존 데이터 호환성을 위해 null 허용)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='delivery_items', verbose_name="제품")
    
    # 기존 필드들 (product가 없을 때 직접 입력)
    item_name = models.CharField(max_length=200, verbose_name="품목명")
    quantity = models.PositiveIntegerField(verbose_name="수량")
    unit = models.CharField(max_length=50, default="EA", verbose_name="단위")
    unit_price = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="단가")
    total_price = models.DecimalField(max_digits=15, decimal_places=0, blank=True, null=True, verbose_name="총액")
    tax_invoice_issued = models.BooleanField(default=False, verbose_name="세금계산서 발행여부")
    notes = models.TextField(blank=True, null=True, verbose_name="비고")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def save(self, *args, **kwargs):
        # product가 선택된 경우 제품 정보로 자동 채우기
        if self.product:
            self.item_name = self.product.product_code
            
            # 단위 자동 설정
            if hasattr(self.product, 'unit') and self.product.unit:
                self.unit = self.product.unit
            
            # 단가가 명시적으로 None인 경우에만 제품 가격 사용 (0 포함 모든 숫자는 유지)
            if self.unit_price is None:
                self.unit_price = self.product.get_current_price()
        
        # 총액 자동 계산 (부가세 10% 포함)
        # unit_price가 None이 아니고 quantity가 있을 때만 계산 (0도 유효)
        if self.unit_price is not None and self.quantity:
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
    # 기본 정보
    product_code = models.CharField(max_length=50, unique=True, verbose_name="제품 코드 (품번)")
    
    # 규격 및 단위
    unit = models.CharField(max_length=50, default="EA", verbose_name="단위")
    specification = models.CharField(max_length=200, blank=True, verbose_name="규격")
    
    # 가격
    standard_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="정상가 (단가)")
    
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
    
    # 생성자 정보 (회사별 제품 구분용)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return self.product_code
    
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
        ordering = ['product_code']


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
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='quoteitems', verbose_name="제품")
    
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
        ('closing', '클로징'),
        ('won', '수주'),
        ('quote_lost', '견적실패'),
        ('excluded', '펀넬제외'),
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


# 영업 기회 라벨 (OpportunityLabel) 모델
class OpportunityLabel(models.Model):
    """영업 기회를 분류하기 위한 라벨"""
    name = models.CharField(max_length=50, verbose_name="라벨명")
    color = models.CharField(max_length=7, default='#667eea', verbose_name="색상", help_text="HEX 색상 코드 (예: #667eea)")
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name="설명")
    user_company = models.ForeignKey('UserCompany', on_delete=models.CASCADE, related_name='opportunity_labels', verbose_name="소속 회사", null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    is_active = models.BooleanField(default=True, verbose_name="활성화")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "영업 기회 라벨"
        verbose_name_plural = "영업 기회 라벨 목록"
        ordering = ['name']
        unique_together = ['name', 'user_company']


# 영업 기회 추적 (OpportunityTracking) 모델
class OpportunityTracking(models.Model):
    followup = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='opportunities', verbose_name="관련 고객")
    
    # 영업 기회 제목 (구분용)
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="영업 기회 제목", help_text="예: '장비 A 구매', '소모품 정기 공급' 등")
    
    # 라벨 (분류용)
    label = models.ForeignKey(OpportunityLabel, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name="라벨")
    
    # 현재 상태
    current_stage = models.CharField(max_length=20, choices=FunnelStage.STAGE_CHOICES, default='lead', verbose_name="현재 단계")
    stage_entry_date = models.DateField(auto_now_add=True, verbose_name="단계 진입일")
    
    # 예측 데이터
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="예상 매출")
    weighted_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="가중 매출")
    probability = models.IntegerField(default=50, verbose_name="성공 확률(%)")
    expected_close_date = models.DateField(null=True, blank=True, verbose_name="예상 계약일")
    
    # 수주 추적
    backlog_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="수주 금액", help_text="예정된 일정의 총 매출액")
    
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def save(self, *args, **kwargs):
        """저장 시 수주/실주 확정되면 고객 등급 자동 갱신"""
        old_stage = None
        if self.pk:
            old_instance = OpportunityTracking.objects.filter(pk=self.pk).first()
            if old_instance:
                old_stage = old_instance.current_stage
        
        super().save(*args, **kwargs)
        
        # 수주 또는 실주로 전환된 경우 고객 등급 갱신
        if old_stage != self.current_stage and self.current_stage in ['won', 'lost']:
            try:
                self.followup.calculate_customer_grade()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"고객 등급 자동 갱신 실패 (Opportunity {self.id}): {e}")
    
    def update_stage(self, new_stage):
        """단계 업데이트 및 이력 기록 (중간 단계 자동 채움)"""
        from datetime import date
        
        # 단계 순서 정의 (협상 단계 제거, lost 추가)
        stage_order = ['lead', 'contact', 'quote', 'closing', 'won', 'lost', 'quote_lost']
        
        try:
            current_index = stage_order.index(self.current_stage)
            new_index = stage_order.index(new_stage)
        except ValueError:
            # 잘못된 단계명이면 그냥 업데이트
            current_index = -1
            new_index = -1
        
        # 현재 단계 종료 처리
        if self.stage_history:
            for history in reversed(self.stage_history):
                if history.get('stage') == self.current_stage and not history.get('exited'):
                    history['exited'] = date.today().isoformat()
                    break
        
        # 중간 단계를 건너뛰는 경우 (정방향만), 자동으로 중간 단계 추가
        if current_index != -1 and new_index != -1 and new_index > current_index + 1:
            # 건너뛴 중간 단계들을 모두 추가 (won, lost, quote_lost 제외)
            for i in range(current_index + 1, new_index):
                skipped_stage = stage_order[i]
                if skipped_stage not in ['won', 'lost', 'quote_lost']:  # 종료 단계는 건너뛰지 않음
                    self.stage_history.append({
                        'stage': skipped_stage,
                        'entered': date.today().isoformat(),
                        'exited': date.today().isoformat(),
                        'note': '자동 추가됨 (단계 건너뛰기)'
                    })
        
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
    
    def update_revenue_amounts(self):
        """관련 일정들로부터 수주 금액과 실제 매출 계산"""
        from decimal import Decimal
        from django.db.models import Sum
        
        # backlog_amount: closing 단계일 때만 예정된 납품 일정들의 DeliveryItem 합계
        # (won 단계에서는 이미 실제 매출로 전환되므로 backlog에 포함 안 함)
        if self.current_stage == 'closing':
            from .models import DeliveryItem
            
            # 예정된(scheduled) 납품 일정만 조회
            backlog_schedules = self.schedules.filter(
                status='scheduled',
                activity_type='delivery'
            )
            
            # DeliveryItem의 total_price 합산
            backlog_total = DeliveryItem.objects.filter(
                schedule__in=backlog_schedules
            ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
            
            self.backlog_amount = backlog_total
        else:
            # closing이 아닌 단계에서는 backlog_amount를 0으로 설정
            self.backlog_amount = Decimal('0')
        
        # 실제 매출: won 단계이고 완료됨(completed) 상태의 납품 일정들의 DeliveryItem 총액
        if self.current_stage == 'won':
            from .models import DeliveryItem
            completed_schedules = self.schedules.filter(
                status='completed',
                activity_type='delivery'
            )
            
            # DeliveryItem에서 실제 납품 금액 계산
            delivery_total = DeliveryItem.objects.filter(
                schedule__in=completed_schedules
            ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
            
            # expected_revenue가 있으면 그것도 고려
            schedule_revenue = sum(
                s.expected_revenue for s in completed_schedules if s.expected_revenue
            ) or Decimal('0')
            
            # 둘 중 큰 값 사용 (DeliveryItem이 더 정확함)
            self.actual_revenue = delivery_total if delivery_total > 0 else schedule_revenue
        else:
            # won 단계가 아니면 actual_revenue는 None
            self.actual_revenue = None
        
        self.save()
    
    def save(self, *args, **kwargs):
        """저장 시 가중 매출 자동 계산 및 고객 등급 갱신"""
        from decimal import Decimal
        
        # 가중 매출 계산: 예상 매출 × (확률 / 100)
        if self.expected_revenue and self.probability is not None:
            self.weighted_revenue = self.expected_revenue * (Decimal(str(self.probability)) / Decimal('100'))
        else:
            self.weighted_revenue = 0
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 수주(won) 또는 실주(lost) 단계로 변경된 경우 고객 등급 재계산
        if not is_new and self.current_stage in ['won', 'lost', 'quote_lost']:
            try:
                self.followup.calculate_customer_grade()
            except Exception as e:
                # 등급 계산 실패해도 저장은 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to calculate customer grade for followup {self.followup.id}: {e}")
    
    def __str__(self):
        if self.title:
            return f"{self.followup.customer_name} - {self.title} ({self.get_current_stage_display()})"
        return f"{self.followup.customer_name} - {self.get_current_stage_display()}"
    
    class Meta:
        verbose_name = "영업 기회"
        verbose_name_plural = "영업 기회 목록"


# 선결제 (Prepayment) 모델
class Prepayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', '현금'),
        ('transfer', '계좌이체'),
        ('card', '카드'),
    ]
    
    STATUS_CHOICES = [
        ('active', '활성'),
        ('depleted', '소진'),
        ('cancelled', '취소'),
    ]
    
    customer = models.ForeignKey(FollowUp, on_delete=models.CASCADE, related_name='prepayments', verbose_name="고객")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="업체/학교")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="선결제 금액")
    balance = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="잔액")
    payment_date = models.DateField(verbose_name="입금 날짜")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='transfer', verbose_name="입금 방법")
    payer_name = models.CharField(max_length=100, blank=True, verbose_name="입금자명")
    memo = models.TextField(blank=True, verbose_name="메모")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="상태")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="등록자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일시")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="취소일시")
    cancel_reason = models.TextField(blank=True, verbose_name="취소 사유")
    
    def __str__(self):
        return f"{self.customer.customer_name} - {self.payment_date} ({self.balance:,}원)"
    
    class Meta:
        verbose_name = "선결제"
        verbose_name_plural = "선결제 목록"
        ordering = ['-payment_date', '-created_at']


# 선결제 사용 내역 (PrepaymentUsage) 모델
class PrepaymentUsage(models.Model):
    prepayment = models.ForeignKey(Prepayment, on_delete=models.CASCADE, related_name='usages', verbose_name="선결제")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True, related_name='prepayment_usages', verbose_name="납품 일정")
    schedule_item = models.ForeignKey(DeliveryItem, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="납품 품목")
    product_name = models.CharField(max_length=200, verbose_name="품목명")
    quantity = models.IntegerField(default=1, verbose_name="수량")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="차감 금액")
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="사용 후 잔액")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="사용 일시")
    memo = models.TextField(blank=True, verbose_name="메모")
    
    def __str__(self):
        return f"{self.prepayment.customer.customer_name} - {self.product_name} ({self.amount:,}원)"
    
    class Meta:
        verbose_name = "선결제 사용 내역"
        verbose_name_plural = "선결제 사용 내역 목록"
        ordering = ['-used_at']


# 개인 일정 (PersonalSchedule) 모델 - 팔로우업 없는 일반 일정
class PersonalSchedule(models.Model):
    """
    팔로우업과 연결되지 않은 개인 일정
    - 일정 제목과 내용만 기록
    - History를 통해 댓글(메모) 작성 가능
    - 캘린더에 회색으로 표시
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="담당자", related_name='personal_schedules')
    company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, null=True, blank=True, verbose_name="소속 회사")
    title = models.CharField(max_length=200, verbose_name="일정 제목")
    content = models.TextField(blank=True, null=True, verbose_name="일정 내용")
    schedule_date = models.DateField(verbose_name="일정 날짜")
    schedule_time = models.TimeField(verbose_name="일정 시간")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return f"{self.title} ({self.schedule_date} {self.schedule_time.strftime('%H:%M')})"
    
    class Meta:
        verbose_name = "개인 일정"
        verbose_name_plural = "개인 일정 목록"
        ordering = ['-schedule_date', '-schedule_time']


# 서류 템플릿 (DocumentTemplate) 모델 - 회사별 견적서/거래명세서 등
class DocumentTemplate(models.Model):
    """
    회사별 서류 템플릿 관리
    - 견적서, 거래명세서 등의 양식을 엑셀/PDF로 업로드
    - 견적/수주 단계에서 다운로드 가능
    - 향후 이메일 발송 기능에도 사용
    """
    DOCUMENT_TYPE_CHOICES = [
        ('quotation', '견적서'),
        ('transaction_statement', '거래명세서'),
        ('delivery_note', '납품서'),
    ]
    
    company = models.ForeignKey(
        UserCompany, 
        on_delete=models.CASCADE, 
        related_name='document_templates',
        verbose_name="소속 회사"
    )
    document_type = models.CharField(
        max_length=50, 
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name="서류 종류"
    )
    name = models.CharField(max_length=200, verbose_name="서류명")
    file = models.FileField(
        upload_to='document_templates/%Y/',
        verbose_name="파일"
    )
    file_type = models.CharField(
        max_length=10,
        choices=[('xlsx', 'Excel'), ('pdf', 'PDF')],
        verbose_name="파일 형식"
    )
    description = models.TextField(blank=True, verbose_name="설명")
    is_active = models.BooleanField(default=True, verbose_name="활성 여부")
    is_default = models.BooleanField(default=False, verbose_name="기본 템플릿 여부")
    
    # 이메일 발송용 필드 (향후 사용)
    email_subject_template = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="이메일 제목 템플릿",
        help_text="예: {customer_name}님께 {document_type} 발송"
    )
    email_body_template = models.TextField(
        blank=True,
        verbose_name="이메일 본문 템플릿",
        help_text="향후 이메일 발송 시 사용될 본문 템플릿"
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="생성자"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return f"{self.company.name} - {self.get_document_type_display()} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 같은 회사의 같은 document_type에서 기본 템플릿은 하나만
        if self.is_default:
            DocumentTemplate.objects.filter(
                company=self.company,
                document_type=self.document_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "서류 템플릿"
        verbose_name_plural = "서류 템플릿 목록"
        ordering = ['-is_default', '-created_at']
        # unique_together 제거 - 같은 이름으로 여러 버전 등록 가능


# 이메일 발송 로그 (EmailLog) 모델 - Gmail 연동
class EmailLog(models.Model):
    """
    이메일 발송/수신 기록
    - Gmail API를 통한 이메일 발송/수신 기록
    - 일정 또는 팔로우업과 연결
    - 스레드 추적 기능
    """
    STATUS_CHOICES = [
        ('pending', '발송 대기'),
        ('sent', '발송 완료'),
        ('received', '수신'),
        ('failed', '발송 실패'),
    ]
    
    TYPE_CHOICES = [
        ('sent', '발신'),
        ('received', '수신'),
    ]
    
    # Gmail 정보
    gmail_message_id = models.CharField(max_length=255, blank=True, verbose_name="Gmail 메시지 ID", db_index=True)
    gmail_thread_id = models.CharField(max_length=255, blank=True, verbose_name="Gmail 스레드 ID", db_index=True)
    
    email_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='sent', verbose_name="메일 타입")
    
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_emails',
        verbose_name="발신자 (CRM 사용자)"
    )
    sender_email = models.EmailField(blank=True, verbose_name="발신자 이메일 주소")
    
    recipient_email = models.EmailField(verbose_name="수신자 이메일")
    recipient_name = models.CharField(max_length=100, blank=True, verbose_name="수신자명")
    
    # CC, BCC
    cc_emails = models.TextField(blank=True, verbose_name="참조 (CC)", help_text="쉼표로 구분")
    bcc_emails = models.TextField(blank=True, verbose_name="숨은 참조 (BCC)", help_text="쉼표로 구분")
    
    subject = models.CharField(max_length=500, verbose_name="제목")
    body = models.TextField(verbose_name="본문")
    body_html = models.TextField(blank=True, verbose_name="HTML 본문")
    
    # 첨부 서류
    document_template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="첨부 서류 템플릿"
    )
    attachment = models.FileField(
        upload_to='email_attachments/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="첨부 파일"
    )
    
    # 첨부파일 정보 (JSON 형식: [{'filename': str, 'size': int, 'mimetype': str}, ...])
    attachments_info = models.JSONField(
        default=list,
        blank=True,
        verbose_name="첨부파일 목록"
    )
    
    # 연결 정보
    followup = models.ForeignKey(
        'FollowUp',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails',
        verbose_name="관련 팔로우업"
    )
    schedule = models.ForeignKey(
        'Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails',
        verbose_name="관련 일정"
    )
    
    # 답장 관계
    in_reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="답장 대상 메일"
    )
    
    # 명함
    business_card = models.ForeignKey(
        'BusinessCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="사용된 명함"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="발송 상태"
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="발송 일시", db_index=True)
    received_at = models.DateTimeField(null=True, blank=True, verbose_name="수신 일시", db_index=True)
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")
    
    # 읽음 여부 (수신 메일의 경우)
    is_read = models.BooleanField(default=False, verbose_name="읽음 여부")
    
    # 메일 상태 플래그
    is_starred = models.BooleanField(default=False, verbose_name="중요 표시", db_index=True)
    is_archived = models.BooleanField(default=False, verbose_name="보관됨", db_index=True)
    is_trashed = models.BooleanField(default=False, verbose_name="휴지통", db_index=True)
    trashed_at = models.DateTimeField(null=True, blank=True, verbose_name="삭제 일시")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        type_str = "발신" if self.email_type == 'sent' else "수신"
        return f"[{type_str}] {self.subject} → {self.recipient_email}"
    
    class Meta:
        verbose_name = "이메일"
        verbose_name_plural = "이메일 목록"
        ordering = ['-sent_at', '-received_at', '-created_at']
        indexes = [
            models.Index(fields=['-sent_at', '-received_at']),
            models.Index(fields=['gmail_thread_id']),
        ]


# 명함 관리 (BusinessCard) 모델
class BusinessCard(models.Model):
    """
    이메일 서명용 명함 관리
    - 사용자별로 여러 명함 생성 가능
    - 기본 명함 설정 기능
    - 이메일 발송 시 하단에 자동 삽입
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_cards',
        verbose_name="소유자"
    )
    
    name = models.CharField(max_length=100, verbose_name="명함 이름", help_text="예: 기본 명함, 영문 명함")
    
    # 명함 정보
    full_name = models.CharField(max_length=100, verbose_name="이름")
    title = models.CharField(max_length=100, blank=True, verbose_name="직책")
    company_name = models.CharField(max_length=200, verbose_name="회사명")
    department = models.CharField(max_length=100, blank=True, verbose_name="부서")
    
    # 연락처
    phone = models.CharField(max_length=50, blank=True, verbose_name="전화번호")
    mobile = models.CharField(max_length=50, blank=True, verbose_name="휴대폰")
    email = models.EmailField(verbose_name="이메일")
    
    # 주소 및 웹사이트
    address = models.CharField(max_length=300, blank=True, verbose_name="주소")
    website = models.URLField(blank=True, verbose_name="웹사이트")
    
    # 추가 정보
    fax = models.CharField(max_length=50, blank=True, verbose_name="팩스")
    logo = models.ImageField(upload_to='business_card_logos/%Y/', blank=True, null=True, verbose_name="로고")
    logo_url = models.URLField(blank=True, verbose_name="로고 이미지 URL", help_text="로고를 클릭했을 때 이동할 URL")
    logo_link_url = models.URLField(blank=True, verbose_name="로고 링크 URL", help_text="로고를 클릭했을 때 이동할 URL")
    
    # HTML 서명
    signature_html = models.TextField(blank=True, verbose_name="HTML 서명", help_text="커스텀 HTML 서명")
    
    # 기본 명함 설정
    is_default = models.BooleanField(default=False, verbose_name="기본 명함")
    is_active = models.BooleanField(default=True, verbose_name="활성 여부")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 같은 사용자의 기본 명함은 하나만
        if self.is_default:
            BusinessCard.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def generate_signature(self, request=None):
        """HTML 서명 자동 생성"""
        if self.signature_html:
            return self.signature_html
        
        # 로고 HTML 생성
        logo_html = ''
        if self.logo or self.logo_url:
            # 로고 URL 생성 (절대 URL로 변환)
            if self.logo:
                logo_src = self.logo.url
                # request가 있으면 절대 URL로 변환
                if request:
                    logo_src = request.build_absolute_uri(logo_src)
                else:
                    # request가 없으면 settings에서 도메인 가져오기
                    from django.conf import settings
                    base_url = getattr(settings, 'SITE_DOMAIN', 'http://127.0.0.1:8000')
                    logo_src = base_url + logo_src
            else:
                logo_src = self.logo_url
            
            logo_img = f'<img src="{logo_src}" alt="{self.company_name} 로고" style="max-width: 150px; max-height: 60px; margin-bottom: 3px;">'
            
            if self.logo_link_url:
                logo_html = f'<a href="{self.logo_link_url}" target="_blank" style="display: inline-block;">{logo_img}</a>'
            else:
                logo_html = logo_img
        
        signature = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; color: #333; line-height: 1.2;">
            {f'<div style="margin-bottom: 2px;">{logo_html}</div>' if logo_html else ''}
            <p style="margin: 0; padding: 0;">
                <strong style="font-size: 14px;">{self.full_name}</strong>
                {f' | {self.title}' if self.title else ''}
            </p>
            <p style="margin: 1px 0 0 0; padding: 0; color: #666;">
                {self.company_name}
                {f' | {self.department}' if self.department else ''}
            </p>
            <p style="margin: 1px 0 0 0; padding: 0; color: #666;">
                {f'전화: {self.phone} | ' if self.phone else ''}
                {f'휴대폰: {self.mobile} | ' if self.mobile else ''}
                이메일: <a href="mailto:{self.email}" style="color: #0066cc; text-decoration: none;">{self.email}</a>
            </p>
            {f'<p style="margin: 1px 0 0 0; padding: 0; color: #666;">{self.address}</p>' if self.address else ''}
            {f'<p style="margin: 1px 0 0 0; padding: 0;"><a href="{self.website}" style="color: #0066cc; text-decoration: none;">{self.website}</a></p>' if self.website else ''}
        </div>
        """
        return signature
    
    class Meta:
        verbose_name = "명함"
        verbose_name_plural = "명함 목록"
        ordering = ['-is_default', '-created_at']


# 서류 생성 로그 (DocumentGenerationLog) 모델
class DocumentGenerationLog(models.Model):
    """
    서류 생성(다운로드) 기록
    - 견적서, 거래명세서 등 서류 생성 시마다 로그 저장
    - 날짜별 거래번호 순서를 추적하기 위해 사용
    """
    company = models.ForeignKey(
        UserCompany,
        on_delete=models.CASCADE,
        related_name='document_logs',
        verbose_name="소속 회사"
    )
    document_type = models.CharField(
        max_length=50,
        choices=DocumentTemplate.DOCUMENT_TYPE_CHOICES,
        verbose_name="서류 종류"
    )
    schedule = models.ForeignKey(
        'Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="관련 일정"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="생성자"
    )
    transaction_number = models.CharField(max_length=50, verbose_name="거래번호")
    output_format = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('xlsx', 'Excel')],
        verbose_name="출력 형식"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일", db_index=True)
    
    def __str__(self):
        return f"{self.transaction_number} - {self.get_document_type_display()}"
    
    class Meta:
        verbose_name = "서류 생성 로그"
        verbose_name_plural = "서류 생성 로그"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['document_type', 'created_at']),
        ]
