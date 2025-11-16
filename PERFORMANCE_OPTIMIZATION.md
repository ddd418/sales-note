# 🚀 서버 성능 최적화 가이드

## 현재 문제점

### 1. N+1 쿼리 문제 (심각)

- `customer_report_view`: 각 고객마다 History, Schedule, DeliveryItem 쿼리 반복
- 100개 고객 = 300~400개 쿼리 실행

### 2. 과도한 로깅 (성능 저하)

- views.py에 100개 이상의 logger 호출
- 매 요청마다 디스크 I/O 발생

### 3. 불필요한 계산 반복

- 중복 집계 쿼리
- 캐싱 미사용

## 즉시 적용 가능한 해결책

### A. 로깅 완전 제거 ✅

**효과**: 응답 속도 20-30% 개선

### B. 데이터베이스 쿼리 최적화 ✅

**효과**: 응답 속도 60-80% 개선

#### customer_report_view 최적화

```python
# 기존: N+1 쿼리 (느림)
for followup in followups:
    histories = History.objects.filter(followup=followup)  # 쿼리 1개씩
    schedules = Schedule.objects.filter(followup=followup)  # 쿼리 1개씩

# 최적화: 단일 쿼리로 모든 데이터 가져오기 (빠름)
followups = followups.prefetch_related(
    Prefetch('history_set', queryset=History.objects.filter(user__in=accessible_users)),
    Prefetch('schedule_set', queryset=Schedule.objects.filter(user__in=accessible_users)
        .prefetch_related('delivery_items_set'))
)
```

### C. 인덱스 추가

```python
# models.py에 추가
class History:
    class Meta:
        indexes = [
            models.Index(fields=['followup', 'user', 'action_type']),
            models.Index(fields=['delivery_date', 'action_type']),
        ]

class Schedule:
    class Meta:
        indexes = [
            models.Index(fields=['followup', 'user', 'activity_type', 'status']),
            models.Index(fields=['visit_date', 'status']),
        ]
```

## 장기 최적화

### 1. Redis 캐싱 도입

- 대시보드 통계 캐싱 (5분)
- 고객 리포트 캐싱 (10분)

### 2. 비동기 처리 (Celery)

- 대용량 엑셀 다운로드
- 이메일 발송

### 3. 페이지네이션 강화

- 고객 리포트: 50개씩
- 일정 목록: 30개씩

## 모니터링

### Django Debug Toolbar 설치

```bash
pip install django-debug-toolbar
```

### 느린 쿼리 로그

```python
# settings.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG' if DEBUG else 'INFO',
        }
    }
}
```

## 예상 성능 개선

- 로깅 제거: **20-30% 개선**
- 쿼리 최적화: **60-80% 개선**
- 인덱스 추가: **10-20% 개선**
- **총합: 2-4배 속도 향상**
