"""
TODOLIST 시스템 모델
- 실무자/매니저 협업형 TODO 관리
- AI 추천, 동료 요청, 매니저 하달 통합
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Todo(models.Model):
    """통합 TODO 모델"""
    
    # 상태
    class Status(models.TextChoices):
        PENDING = 'pending', '승인 대기'
        ONGOING = 'ongoing', '진행중'
        ON_HOLD = 'on_hold', '보류'
        DONE = 'done', '완료'
        REJECTED = 'rejected', '반려'
    
    # 출처 유형
    class SourceType(models.TextChoices):
        SELF = 'self', '직접 생성'
        AI_SUGGESTED = 'ai_suggested', 'AI 추천'
        PEER_REQUEST = 'peer_request', '동료 요청'
        MANAGER_ASSIGN = 'manager_assign', '매니저 하달'
    
    # 예상 소요 시간 (분)
    class Duration(models.IntegerChoices):
        MIN_15 = 15, '15분'
        MIN_30 = 30, '30분'
        HOUR_1 = 60, '1시간'
        HOUR_2 = 120, '2시간'
        HOUR_4 = 240, '4시간 (반나절)'
        DAY_1 = 480, '1일'
        DAY_2 = 960, '2일'
        DAY_3 = 1440, '3일'
        WEEK_1 = 2400, '1주일'
        WEEK_2 = 4800, '2주일'
        MONTH_1 = 9600, '1개월'
    
    # 기본 필드
    title = models.CharField(max_length=200, verbose_name="제목")
    description = models.TextField(blank=True, verbose_name="상세 내용")
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ONGOING,
        verbose_name="상태"
    )
    source_type = models.CharField(
        max_length=20, 
        choices=SourceType.choices, 
        default=SourceType.SELF,
        verbose_name="출처"
    )
    
    # 사용자 관계
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_todos',
        verbose_name="생성자"
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='assigned_todos',
        null=True, blank=True,
        verbose_name="담당자"
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='requested_todos',
        null=True, blank=True,
        verbose_name="요청자"
    )
    
    # 관련 고객 (선택)
    related_client = models.ForeignKey(
        'reporting.FollowUp',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="관련 고객"
    )
    
    # 일정
    expected_duration = models.IntegerField(
        choices=Duration.choices,
        null=True, blank=True,
        verbose_name="예상 소요시간(분)"
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="마감일")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료일시")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'todo'
        ordering = ['-created_at']
        verbose_name = 'TODO'
        verbose_name_plural = 'TODO 목록'
        indexes = [
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['source_type']),
        ]
    
    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"
    
    def complete(self, user):
        """TODO 완료 처리"""
        self.status = self.Status.DONE
        self.completed_at = timezone.now()
        self.save()
        
        TodoLog.objects.create(
            todo=self,
            actor=user,
            action_type=TodoLog.ActionType.COMPLETED,
            message="완료 처리됨",
            prev_status='ongoing',
            new_status='done'
        )
    
    def approve(self, user):
        """승인 처리 (pending → ongoing)"""
        prev_status = self.status
        self.status = self.Status.ONGOING
        self.save()
        
        TodoLog.objects.create(
            todo=self,
            actor=user,
            action_type=TodoLog.ActionType.APPROVED,
            message="승인됨",
            prev_status=prev_status,
            new_status='ongoing'
        )
    
    def reject(self, user, reason=""):
        """반려 처리"""
        prev_status = self.status
        self.status = self.Status.REJECTED
        self.save()
        
        TodoLog.objects.create(
            todo=self,
            actor=user,
            action_type=TodoLog.ActionType.REJECTED,
            message=reason or "반려됨",
            prev_status=prev_status,
            new_status='rejected'
        )
    
    @property
    def is_overdue(self):
        """마감일 초과 여부"""
        if self.due_date and self.status not in [self.Status.DONE, self.Status.REJECTED]:
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def source_badge_class(self):
        """출처 유형별 배지 색상"""
        badge_map = {
            'self': 'bg-secondary',
            'ai_suggested': 'bg-info',
            'peer_request': 'bg-warning',
            'manager_assign': 'bg-primary',
        }
        return badge_map.get(self.source_type, 'bg-secondary')
    
    @property
    def status_badge_class(self):
        """상태별 배지 색상"""
        badge_map = {
            'pending': 'bg-warning',
            'ongoing': 'bg-primary',
            'on_hold': 'bg-secondary',
            'done': 'bg-success',
            'rejected': 'bg-danger',
        }
        return badge_map.get(self.status, 'bg-secondary')


class TodoAttachment(models.Model):
    """TODO 첨부파일"""
    
    todo = models.ForeignKey(
        Todo, on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='todo_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    class Meta:
        db_table = 'todo_attachment'
        verbose_name = 'TODO 첨부파일'
        verbose_name_plural = 'TODO 첨부파일'
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.filename:
                self.filename = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)


class TodoLog(models.Model):
    """TODO 변경 로그"""
    
    class ActionType(models.TextChoices):
        CREATED = 'created', '생성'
        UPDATED = 'updated', '수정'
        STATUS_CHANGED = 'status_changed', '상태 변경'
        ASSIGNED = 'assigned', '담당자 지정'
        APPROVED = 'approved', '승인'
        REJECTED = 'rejected', '반려'
        COMPLETED = 'completed', '완료'
        DELEGATED = 'delegated', '업무 요청'
        COMMENTED = 'commented', '코멘트'
    
    todo = models.ForeignKey(
        Todo, on_delete=models.CASCADE,
        related_name='logs'
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True
    )
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    message = models.TextField(blank=True)
    prev_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'todo_log'
        ordering = ['-created_at']
        verbose_name = 'TODO 로그'
        verbose_name_plural = 'TODO 로그'
        indexes = [
            models.Index(fields=['todo', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.todo.title} - {self.get_action_type_display()}"
