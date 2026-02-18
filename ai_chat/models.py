"""
AI 부서 분석 - 모델
부서별 6개월 미팅 종합 분석 + 견적/납품 패턴 분석
"""
from django.db import models
from django.contrib.auth.models import User
from reporting.models import Department


class AIDepartmentAnalysis(models.Model):
    """부서(연구실)별 AI 종합 분석"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="분석 요청자")
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE,
        related_name='ai_analyses', verbose_name="분석 대상 부서"
    )

    # 분석 결과 저장
    analysis_data = models.JSONField(
        null=True, blank=True, verbose_name="AI 분석 결과",
        help_text="PainPoint, 요약, 시그널, CRM 추천 등 전체 분석 JSON"
    )
    quote_delivery_data = models.JSONField(
        null=True, blank=True, verbose_name="견적/납품 분석 결과",
        help_text="견적→납품 전환율, 납품 주기, 제품 패턴 등"
    )

    # 분석에 사용된 데이터 범위
    meeting_count = models.IntegerField(default=0, verbose_name="분석된 미팅 수")
    quote_count = models.IntegerField(default=0, verbose_name="분석된 견적 수")
    delivery_count = models.IntegerField(default=0, verbose_name="분석된 납품 수")
    analysis_period_start = models.DateField(null=True, blank=True, verbose_name="분석 기간 시작")
    analysis_period_end = models.DateField(null=True, blank=True, verbose_name="분석 기간 종료")

    token_usage = models.IntegerField(default=0, verbose_name="토큰 사용량")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "AI 부서 분석"
        verbose_name_plural = "AI 부서 분석 목록"
        ordering = ['-updated_at']
        unique_together = ['user', 'department']

    def __str__(self):
        return f"{self.department.company.name} / {self.department.name} - AI 분석"


class PainPointCard(models.Model):
    """PainPoint 가설 카드"""
    CATEGORY_CHOICES = [
        ('budget', '예산/가격'),
        ('purchase_process', '결재/구매 프로세스'),
        ('switching_cost', '전환 비용/재고 고착'),
        ('performance', '성능/정확도'),
        ('compatibility', '호환성/사용성'),
        ('delivery', '납기/재고'),
        ('trust', '신뢰/리스크'),
        ('priority', '우선순위/관심'),
    ]

    CONFIDENCE_CHOICES = [
        ('high', 'High'),
        ('med', 'Med'),
        ('low', 'Low'),
    ]

    ATTRIBUTION_CHOICES = [
        ('individual', '개인(연구원)'),
        ('lab', '랩'),
        ('purchase_route', '구매루트(거래처)'),
        ('institution', '기관'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('unverified', '미검증'),
        ('confirmed', '확인됨'),
        ('denied', '부정됨'),
    ]

    analysis = models.ForeignKey(
        AIDepartmentAnalysis, on_delete=models.CASCADE,
        related_name='painpoint_cards', verbose_name="부서 분석"
    )

    # 카드 필수 필드
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name="카테고리")
    hypothesis = models.TextField(verbose_name="가설 (한 줄)")
    confidence = models.CharField(max_length=5, choices=CONFIDENCE_CHOICES, verbose_name="확신도")
    confidence_score = models.IntegerField(
        default=50, verbose_name="확신도 점수 (0-100)"
    )
    evidence = models.JSONField(
        verbose_name="근거 (Evidence)",
        help_text='[{"type": "quote|fact|guess", "text": "...", "source_section": "..."}]'
    )
    attribution = models.CharField(max_length=20, choices=ATTRIBUTION_CHOICES, verbose_name="귀속")

    # 검증 질문
    verification_question = models.TextField(verbose_name="검증 질문")
    action_if_yes = models.TextField(verbose_name="맞으면 (대응 패키지)")
    action_if_no = models.TextField(verbose_name="아니면 (다음 단계)")
    caution = models.TextField(blank=True, verbose_name="주의 문장")

    # 검증 상태
    verification_status = models.CharField(
        max_length=15, choices=VERIFICATION_STATUS_CHOICES,
        default='unverified', verbose_name="검증 상태"
    )
    verification_note = models.TextField(blank=True, verbose_name="검증 메모")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="검증일")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "PainPoint 카드"
        verbose_name_plural = "PainPoint 카드 목록"
        ordering = ['-confidence_score', '-created_at']

    def __str__(self):
        return f"[{self.get_confidence_display()}] {self.get_category_display()} - {self.hypothesis[:40]}"
