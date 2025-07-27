# PostgreSQL 자동 백업 시스템 배포 가이드

## 📋 목차
1. [시스템 개요](#-시스템-개요)
2. [빠른 배포](#-빠른-배포)
3. [고급 설정](#-고급-설정)
4. [테스트 및 확인](#-테스트-및-확인)
5. [문제 해결](#-문제-해결)

## 🎯 시스템 개요

이 백업 시스템은 매일 오전 8시(한국시간)에 PostgreSQL 데이터베이스를 자동으로 백업합니다.

### 💡 주요 기능
- **자동 스케줄링**: Railway Cron Jobs로 매일 실행
- **압축 백업**: gzip으로 압축하여 저장공간 절약
- **자동 정리**: 7일 이상 된 백업 파일 자동 삭제
- **알림 시스템**: Slack 및 이메일 알림 지원
- **클라우드 저장**: AWS S3, Google Cloud Storage 지원
- **무결성 검증**: MD5 체크섬으로 백업 파일 검증

### 📁 파일 구조
```
sales-note/
├── railway_backup_scheduler.py      # 기본 백업 스크립트
├── advanced_backup_scheduler.py     # 고급 백업 스크립트 (클라우드 포함)
├── test_backup.py                   # 로컬 테스트 스크립트
├── railway.toml                     # Railway Cron Jobs 설정
├── BACKUP_GUIDE.md                 # 이 가이드 문서
└── requirements.txt                 # 필요한 패키지 (업데이트됨)
```

## 🚀 빠른 배포

### 단계 1: 백업 시스템 배포
```cmd
# 현재 디렉토리가 sales-note인지 확인
cd c:\Users\AnJaehyun\OneDrive\projects\sales-note

# 변경사항 커밋 및 푸시
git add .
git commit -m "Add PostgreSQL auto backup scheduler with Railway Cron Jobs"
git push
```

### 단계 2: Railway에서 Cron Jobs 활성화
1. [Railway 대시보드](https://railway.app/dashboard) 접속
2. sales-note 프로젝트 선택
3. Settings > Cron Jobs 탭으로 이동
4. `railway.toml` 파일이 자동으로 감지되어 Cron Job이 생성됨
5. 활성화 상태 확인

### 단계 3: 기본 알림 설정 (선택사항)
Railway 환경변수에 Slack 웹훅 URL 추가:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### ✅ 완료!
기본 백업 시스템이 활성화되었습니다. 매일 오전 8시에 자동 백업이 실행됩니다.

## 🔧 고급 설정

### AWS S3 백업 설정
고급 백업 스크립트를 사용하여 AWS S3에 백업을 저장할 수 있습니다.

#### 1. 환경변수 설정
Railway에서 다음 환경변수들을 추가하세요:
```
# AWS S3 설정
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-backup-bucket
S3_REGION=ap-northeast-2

# 고급 백업 활성화
USE_ADVANCED_BACKUP=true
```

#### 2. railway.toml 수정
고급 백업을 사용하려면 `railway.toml`에서 스크립트 경로를 변경:
```toml
[[services.cron]]
schedule = "0 23 * * *"  # 매일 오전 8시 (KST = UTC+9)
command = "python advanced_backup_scheduler.py"
```

### Google Cloud Storage 백업 설정
```
# Google Cloud Storage 설정
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_BUCKET_NAME=your-backup-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### 이메일 알림 설정
```
# SMTP 이메일 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
BACKUP_EMAIL_RECIPIENTS=admin@company.com,manager@company.com
```

## 🧪 테스트 및 확인

### 로컬 테스트
배포하기 전에 로컬에서 백업 기능을 테스트할 수 있습니다:

```cmd
# Railway DATABASE_URL 환경변수 설정
set DATABASE_URL=postgresql://postgres:password@host:port/database

# 백업 테스트 실행
python test_backup.py
```

### Railway에서 수동 실행
Cron Job이 정상 작동하는지 수동으로 테스트:

1. Railway 대시보드에서 프로젝트 선택
2. Settings > Cron Jobs에서 백업 작업 찾기
3. "Run Now" 버튼 클릭
4. 로그에서 실행 결과 확인

### 백업 파일 확인
Railway 파일 시스템에서 백업 파일 확인:
```bash
# Railway CLI로 접속 (옵션)
railway shell

# 백업 디렉토리 확인
ls -la /tmp/
```

## 🔍 모니터링 및 로그

### Railway 로그 확인
```bash
# Railway CLI로 로그 확인
railway logs

# 특정 시간 범위 로그 확인
railway logs --since 1h
```

### Slack 알림 예시
백업 성공 시:
```
✅ 데이터베이스 백업 완료
📅 2024-01-15 08:00:00 KST
📁 backup_20240115_080000.sql.gz (2.3 MB)
⏱️ 소요시간: 45초
```

백업 실패 시:
```
❌ 데이터베이스 백업 실패
📅 2024-01-15 08:00:00 KST
🚨 오류: Connection timeout
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. Cron Job이 실행되지 않음
**원인**: `railway.toml` 파일이 잘못되었거나 Railway에서 감지되지 않음
**해결책**:
- `railway.toml` 파일이 프로젝트 루트에 있는지 확인
- 파일 형식이 올바른지 확인
- Railway 대시보드에서 Cron Jobs 탭 확인

#### 2. 백업 파일이 생성되지 않음
**원인**: DATABASE_URL이 잘못되었거나 pg_dump 오류
**해결책**:
```python
# test_backup.py로 연결 테스트
python test_backup.py
```

#### 3. 디스크 공간 부족
**원인**: 오래된 백업 파일이 정리되지 않음
**해결책**:
- 백업 스크립트의 정리 로직 확인
- Railway 스토리지 사용량 모니터링

#### 4. 클라우드 업로드 실패
**원인**: 잘못된 자격증명 또는 권한 부족
**해결책**:
- AWS/GCP 자격증명 재확인
- 버킷 권한 설정 확인
- 환경변수 이름 정확성 확인

### 디버깅 방법

#### 1. 상세 로그 활성화
환경변수에 추가:
```
DEBUG_BACKUP=true
```

#### 2. 테스트 모드 실행
```
TEST_MODE=true
```

#### 3. 백업 스크립트 직접 실행
```bash
# Railway shell에서
python railway_backup_scheduler.py
```

## 📞 지원 및 연락처

문제가 지속되거나 추가 기능이 필요한 경우:
1. 먼저 이 가이드의 문제 해결 섹션을 확인
2. Railway 공식 문서 참조
3. GitHub Issues에 문제 보고

## 🔄 업데이트 및 유지보수

### 정기 점검 항목
- [ ] 매주 백업 로그 확인
- [ ] 매월 백업 파일 용량 모니터링
- [ ] 분기별 복구 테스트 수행
- [ ] 연 2회 백업 전략 검토

### 스크립트 업데이트
새로운 기능이나 버그 수정 시:
```cmd
git pull
git add .
git commit -m "Update backup system"
git push
```

---

**📝 마지막 업데이트**: 2024년 1월 15일  
**📋 버전**: 1.0.0  
**🔧 담당자**: 개발팀
