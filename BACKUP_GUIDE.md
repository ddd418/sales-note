# 🔄 PostgreSQL 자동 백업 설정 가이드

Railway에서 PostgreSQL 데이터베이스를 자동으로 백업하는 시스템 설정 방법입니다.

## 📋 개요

- **스케줄**: 매일 한국시간 오전 8시 (UTC 23시)
- **백업 방식**: PostgreSQL pg_dump 사용
- **저장 위치**: 로컬 임시 저장 + 클라우드 스토리지 (선택사항)
- **압축**: gzip으로 압축하여 저장 공간 절약
- **보관 기간**: 로컬 7일, 클라우드는 설정에 따라

## 🚀 설정 방법

### 1. Railway에서 Cron Jobs 활성화

Railway 프로젝트 설정에서 다음 환경변수를 추가하세요:

```bash
# Railway에서 자동 설정되는 변수 (확인용)
DATABASE_URL=postgresql://user:password@host:port/database

# 선택사항: 알림 설정
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ADMIN_EMAIL=admin@yourcompany.com

# 선택사항: 이메일 알림 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 선택사항: AWS S3 백업
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BACKUP_BUCKET=your-backup-bucket

# 선택사항: Google Cloud Storage 백업
GCS_BACKUP_BUCKET=your-gcs-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 2. Railway 프로젝트에 파일 배포

다음 파일들을 프로젝트에 추가하고 배포하세요:

- `railway_backup_scheduler.py` - 기본 백업 스크립트
- `advanced_backup_scheduler.py` - 고급 백업 스크립트 (클라우드 업로드 포함)
- `railway.toml` - Railway Cron Jobs 설정
- `railway.cron` - 크론 설정 파일 (참고용)

### 3. 배포 및 확인

```bash
# 로컬에서 테스트
python railway_backup_scheduler.py

# Railway에 배포
git add .
git commit -m "Add PostgreSQL auto backup scheduler"
git push
```

## 📁 백업 스크립트 종류

### 기본 백업 스크립트 (`railway_backup_scheduler.py`)

**특징:**
- PostgreSQL 덤프 생성
- 로컬 임시 저장
- 기본 알림 (슬랙)
- 7일 후 자동 삭제

**사용법:**
```bash
python railway_backup_scheduler.py
```

### 고급 백업 스크립트 (`advanced_backup_scheduler.py`)

**특징:**
- 압축된 백업 파일 생성
- AWS S3 또는 Google Cloud Storage 업로드
- 이메일 알림
- 백업 무결성 검증 (MD5 체크섬)
- 상세한 로깅

**사용법:**
```bash
python advanced_backup_scheduler.py
```

## ⏰ 크론 표현식 설명

```
0 23 * * *
│ │  │ │ │
│ │  │ │ └─── 요일 (0-6, 일요일=0)
│ │  │ └───── 월 (1-12)
│ │  └─────── 일 (1-31)
│ └────────── 시 (0-23)
└──────────── 분 (0-59)
```

**시간대 변환:**
- UTC 23:00 = 한국시간 08:00
- UTC 00:00 = 한국시간 09:00
- UTC 12:00 = 한국시간 21:00

## 🔧 고급 설정

### AWS S3 백업 설정

1. AWS IAM에서 S3 접근 권한이 있는 사용자 생성
2. S3 버킷 생성
3. Railway 환경변수에 AWS 설정 추가
4. `requirements.txt`에서 boto3 주석 해제

### Google Cloud Storage 백업 설정

1. GCP 프로젝트에서 Storage 버킷 생성
2. 서비스 계정 생성 및 키 다운로드
3. Railway 환경변수에 GCS 설정 추가
4. `requirements.txt`에서 google-cloud-storage 주석 해제

### 이메일 알림 설정

Gmail 사용 시:
1. Gmail에서 앱 비밀번호 생성
2. Railway 환경변수에 SMTP 설정 추가

### 슬랙 알림 설정

1. 슬랙에서 Incoming Webhook 생성
2. Webhook URL을 `SLACK_WEBHOOK_URL` 환경변수에 추가

## 📊 모니터링

### 백업 성공 확인 방법

1. **Railway 로그 확인:**
   ```bash
   railway logs
   ```

2. **슬랙 알림 확인:**
   - 백업 성공/실패 시 자동 알림

3. **이메일 알림 확인:**
   - 백업 상태 및 파일 정보 포함

4. **클라우드 스토리지 확인:**
   - S3 또는 GCS 버킷에서 백업 파일 확인

### 백업 파일 복원 방법

#### 로컬 백업 파일에서 복원:
```bash
# 압축 해제
gunzip railway_sales_backup_20250127_080000.sql.gz

# PostgreSQL 복원
psql -h host -U user -d database -f railway_sales_backup_20250127_080000.sql
```

#### 클라우드에서 다운로드 후 복원:
```bash
# S3에서 다운로드
aws s3 cp s3://your-bucket/sales-note-backups/backup.sql.gz ./

# 압축 해제 및 복원
gunzip backup.sql.gz
psql -h host -U user -d database -f backup.sql
```

## 🚨 문제 해결

### 일반적인 문제들

1. **pg_dump 명령어를 찾을 수 없음:**
   - Railway에는 PostgreSQL 클라이언트가 기본 설치되어 있습니다.

2. **권한 오류:**
   - DATABASE_URL이 올바른지 확인
   - Railway 환경변수 설정 확인

3. **타임아웃 오류:**
   - 큰 데이터베이스의 경우 타임아웃 시간 증가
   - `timeout=600`을 더 큰 값으로 변경

4. **디스크 공간 부족:**
   - 백업 후 즉시 클라우드 업로드 및 로컬 삭제
   - 압축 사용으로 공간 절약

### 로그 분석

백업 스크립트는 다음과 같은 로그를 출력합니다:

```
🔄 PostgreSQL 덤프 생성 시작...
✅ 덤프 생성 완료: railway_sales_backup_20250127_080000.sql.gz
📁 파일 크기: 2.35 MB
🔐 체크섬: a1b2c3d4e5f6...
☁️ AWS S3에 업로드 중: my-backup-bucket
✅ S3 업로드 완료: s3://my-backup-bucket/sales-note-backups/...
📧 이메일 알림 전송 완료
🎉 백업이 성공적으로 완료되었습니다.
```

## 📈 백업 전략 권장사항

1. **다중 백업:**
   - 로컬 + 클라우드 이중 백업
   - 서로 다른 클라우드 제공업체 사용

2. **보관 정책:**
   - 일일 백업: 7일 보관
   - 주간 백업: 4주 보관
   - 월간 백업: 12개월 보관

3. **테스트:**
   - 정기적으로 백업 파일 복원 테스트
   - 백업 무결성 확인

4. **보안:**
   - 백업 파일 암호화
   - 접근 권한 최소화
   - 정기적인 키 rotation

## 🔗 관련 문서

- [Railway Cron Jobs 공식 문서](https://docs.railway.app/deploy/cron-jobs)
- [PostgreSQL pg_dump 매뉴얼](https://www.postgresql.org/docs/current/app-pgdump.html)
- [AWS S3 백업 가이드](https://docs.aws.amazon.com/s3/)
- [Google Cloud Storage 가이드](https://cloud.google.com/storage/docs)
