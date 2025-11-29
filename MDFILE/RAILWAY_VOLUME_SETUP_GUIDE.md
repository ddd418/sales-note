# Railway Volume 설정 가이드

## 개요

Cloudinary 대신 Railway Volume을 사용하여 미디어 파일을 영구 저장하는 방법

---

## 1. Railway Volume 설정

### Railway 대시보드 설정

- **Volume Name**: `web-volume`
- **Mount Path**: `/data` (⚠️ `/data/media`가 아닌 `/data`로 설정)
- **용량**: 250GB

### 왜 Mount Path를 `/data`로 해야 하나?

```
✅ 올바른 설정:
   Mount Path: /data
   Django MEDIA_ROOT: /data/media
   → Django가 /data/media 폴더를 자유롭게 생성/관리

❌ 잘못된 설정:
   Mount Path: /data/media
   Django MEDIA_ROOT: /data/media
   → 권한 문제 발생 가능
```

---

## 2. Django 설정

### settings_production.py

```python
# Railway Volume 파일 저장소 설정
# Mount Path: /data (250GB)
MEDIA_URL = '/media/'
MEDIA_ROOT = '/data/media'

# 기본 파일 저장소 (로컬 파일 시스템)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# 파일 정리 정책 설정
FILE_CLEANUP_SETTINGS = {
    # 영구 보관 파일 (삭제하지 않음)
    'PERMANENT_PATHS': [
        'document_templates/',    # 서류 템플릿
        'business_card_logos/',   # 서명 관리 회사 로고
    ],
    # 영구 보관 최대 파일 크기 (5MB 이하는 영구 보관)
    'PERMANENT_MAX_SIZE_MB': 5,
    # 임시 파일 보관 기간 (100일)
    'TEMP_FILE_RETENTION_DAYS': 100,
}
```

### urls.py - 프로덕션 Media 파일 서빙

```python
from django.urls import path, include, re_path
from django.views.static import serve

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 프로덕션 환경에서 미디어 파일 서빙 (Railway Volume 사용)
# static() 함수는 DEBUG=True일 때만 작동하므로, re_path + serve 사용
if not settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
```

> ⚠️ **중요**: `static()` 함수는 `DEBUG=True`일 때만 작동합니다!
> 프로덕션에서는 반드시 `re_path` + `serve`를 사용해야 합니다.

---

## 3. 모델 필드 변경

### CloudinaryField → FileField/ImageField

**Before (Cloudinary):**

```python
from cloudinary.models import CloudinaryField

class DocumentTemplate(models.Model):
    file = CloudinaryField(resource_type='raw', folder='document_templates')

class BusinessCard(models.Model):
    logo = CloudinaryField(blank=True, null=True, folder='business_card_logos')
```

**After (FileField):**

```python
class DocumentTemplate(models.Model):
    file = models.FileField(upload_to='document_templates/%Y/')

class BusinessCard(models.Model):
    logo = models.ImageField(upload_to='business_card_logos/%Y/', blank=True, null=True)
```

### 마이그레이션

```bash
python manage.py makemigrations reporting --name cloudinary_to_filefield
python manage.py migrate
```

---

## 4. 파일 정리 정책

### 영구 보관 파일

| 조건                                | 보관 기간 |
| ----------------------------------- | --------- |
| `document_templates/` (서류 템플릿) | ♾️ 영구   |
| `business_card_logos/` (서명 로고)  | ♾️ 영구   |
| 5MB 이하 모든 파일                  | ♾️ 영구   |

### 자동 삭제 파일

| 조건               | 보관 기간     |
| ------------------ | ------------- |
| 5MB 초과 기타 파일 | 100일 후 삭제 |

### 자동 정리 명령어

```bash
# 미리보기 (삭제 안함)
python manage.py cleanup_old_files --dry-run

# 실제 삭제
python manage.py cleanup_old_files

# 옵션
python manage.py cleanup_old_files --days 100 --max-size 5.0
```

### Celery Beat 자동 실행

- **매일 새벽 3시** 자동 정리 실행 (Celery Beat 필요)

```python
# celery.py
app.conf.beat_schedule = {
    'cleanup-old-files-daily': {
        'task': 'reporting.tasks.cleanup_old_files_task',
        'schedule': crontab(hour=3, minute=0),
    },
}
```

---

## 5. Volume 폴더 구조

```
/data (Railway Volume - 250GB)
└── media/
    ├── document_templates/     # 서류 템플릿 (영구)
    │   └── 2025/
    ├── business_card_logos/    # 서명 로고 (영구)
    │   └── 2025/
    ├── email_images/           # 메일 이미지
    ├── schedule_files/         # 스케줄 파일
    │   └── 2025/
    └── history_files/          # 기타 파일
```

---

## 6. 문제 해결

### 문제 1: "Not Found: /media/..." 에러

**원인**: 프로덕션에서 `static()` 함수가 작동 안 함

**해결**: `re_path` + `serve` 사용

```python
if not settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
```

### 문제 2: 배포 후 파일 삭제됨

**원인**: Volume Mount Path가 잘못됨

**해결**: Mount Path를 `/data`로 설정 (Django MEDIA_ROOT는 `/data/media`)

### 문제 3: 파일 업로드는 되는데 표시 안 됨

**원인**: CloudinaryField가 여전히 사용 중

**해결**: 모델 필드를 FileField/ImageField로 변경 + 마이그레이션

---

## 7. Cloudinary 제거 체크리스트

- [x] `settings_production.py`에서 Cloudinary 설정 제거
- [x] `INSTALLED_APPS`에서 `cloudinary`, `cloudinary_storage` 제거
- [x] `models.py`에서 `CloudinaryField` → `FileField`/`ImageField` 변경
- [x] 마이그레이션 생성 및 적용
- [x] `urls.py`에 프로덕션 media 서빙 추가
- [ ] (선택) `requirements.txt`에서 cloudinary 패키지 제거

---

## 8. 참고 사항

### Volume vs Cloudinary 비교

| 항목      | Cloudinary        | Railway Volume     |
| --------- | ----------------- | ------------------ |
| 비용      | 무료 제한 후 유료 | 포함 (250GB)       |
| 속도      | CDN (빠름)        | 서버 직접 (적당)   |
| 복잡도    | 설정 필요         | 단순 (로컬 저장)   |
| 의존성    | 외부 서비스       | Railway 내부       |
| 배포 영향 | 없음              | 없음 (Volume 영구) |

### 주의사항

1. **기존 Cloudinary 파일**은 자동 이전되지 않음 → 수동 다운로드 후 재업로드 필요
2. **Celery Beat**를 실행해야 자동 파일 정리가 동작함
3. **Volume 백업**은 Railway에서 자동으로 제공되지 않음 → 필요시 수동 백업

---

_작성일: 2025-11-30_
_최종 수정: 2025-11-30_
