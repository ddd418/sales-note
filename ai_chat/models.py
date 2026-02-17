"""
AI PainPoint 생성기 - 모델
부서별 AI 채팅방 + PainPoint 가설 카드 저장
"""
from django.db import models
from django.contrib.auth.models import User
from reporting.models import FollowUp


class AIChatRoom(models.Model):
    """부서(팔로우업)별 AI 채팅방"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="소유자")
    followup = models.ForeignKey(
        FollowUp, on_delete=models.CASCADE,
        related_name='ai_chatrooms', verbose_name="관련 팔로우업"
    )
    title = models.CharField(max_length=200, verbose_name="채팅방 제목")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "AI 채팅방"
        verbose_name_plural = "AI 채팅방 목록"
        ordering = ['-updated_at']
        unique_together = ['user', 'followup']

    def __str__(self):
        return f"{self.followup} - AI 분석"


class AIChatMessage(models.Model):
    """채팅 메시지 (사용자 입력 + AI 응답)"""
    ROLE_CHOICES = [
        ('user', '사용자'),
        ('assistant', 'AI'),
        ('system', '시스템'),
    ]

    room = models.ForeignKey(
        AIChatRoom, on_delete=models.CASCADE,
        related_name='messages', verbose_name="채팅방"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="역할")
    content = models.TextField(verbose_name="메시지 내용")
    
    # AI 응답의 경우 구조화된 데이터 저장
    structured_data = models.JSONField(
        null=True, blank=True, verbose_name="구조화 데이터",
        help_text="엔티티 추출, PainPoint 카드 등 파싱된 데이터"
    )
    
    # 어떤 히스토리(미팅록)를 기반으로 분석했는지
    source_history = models.ForeignKey(
        'reporting.History', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ai_analyses',
        verbose_name="소스 미팅록"
    )
    
    token_usage = models.IntegerField(default=0, verbose_name="토큰 사용량")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "AI 채팅 메시지"
        verbose_name_plural = "AI 채팅 메시지 목록"
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_role_display()}] {self.content[:50]}"


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

    message = models.ForeignKey(
        AIChatMessage, on_delete=models.CASCADE,
        related_name='painpoint_cards', verbose_name="소스 메시지"
    )
    room = models.ForeignKey(
        AIChatRoom, on_delete=models.CASCADE,
        related_name='painpoint_cards', verbose_name="채팅방"
    )

    # 카드 필수 필드
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name="카테고리")
    hypothesis = models.TextField(verbose_name="가설 (한 줄)")
    confidence = models.CharField(max_length=5, choices=CONFIDENCE_CHOICES, verbose_name="확신도")
    confidence_score = models.IntegerField(
        default=50, verbose_name="확신도 점수 (0-100)",
        help_text="내부 저장용 점수"
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

    # 검증 상태 (영업사원이 현장에서 업데이트)
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
