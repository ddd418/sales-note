# 데이터베이스 백업 및 복원 가이드

영업 보고 시스템의 데이터베이스를 안전하게 백업하고 복원하는 Django 관리 명령어들입니다.

## 📋 명령어 목록

### 1. 데이터베이스 백업 (`backup_db`)

데이터베이스를 JSON 형태로 백업합니다.

```bash
# 기본 백업
python manage.py backup_db

# 옵션을 사용한 백업
python manage.py backup_db --output-dir=my_backups --include-media --compress
```

**옵션:**

- `--output-dir`: 백업 파일을 저장할 디렉토리 (기본값: `backups`)
- `--include-media`: 미디어 파일도 함께 백업
- `--compress`: 백업 파일을 ZIP으로 압축

### 2. 데이터베이스 복원 (`restore_db`)

백업된 데이터베이스를 복원합니다.

```bash
# 백업 디렉토리에서 복원
python manage.py restore_db backups/sales_db_backup_20241218_143000

# ZIP 파일에서 복원
python manage.py restore_db backups/sales_db_backup_20241218_143000.zip

# 기존 데이터를 모두 삭제하고 복원 (주의!)
python manage.py restore_db backups/sales_db_backup_20241218_143000 --clear-existing --force
```

**옵션:**

- `--clear-existing`: 기존 데이터를 모두 삭제하고 복원 ⚠️ **주의: 모든 데이터가 삭제됩니다!**
- `--restore-media`: 미디어 파일도 함께 복원
- `--force`: 확인 없이 강제 실행

### 3. 자동 백업 (`auto_backup`)

자동 백업을 실행하고 오래된 백업 파일을 정리합니다.

```bash
# 기본 자동 백업
python manage.py auto_backup

# 옵션을 사용한 자동 백업
python manage.py auto_backup --backup-dir=daily_backups --keep-days=7 --compress --include-media
```

**옵션:**

- `--backup-dir`: 백업 디렉토리 (기본값: `backups`)
- `--keep-days`: 보관할 백업 파일 일수 (기본값: 30일)
- `--compress`: 백업 파일 압축
- `--include-media`: 미디어 파일 포함

## 📁 백업 파일 구조

백업 파일은 다음과 같은 구조로 생성됩니다:

```
sales_db_backup_YYYYMMDD_HHMMSS/
├── backup_info.json      # 백업 정보
├── users.json           # 사용자 데이터
├── userprofiles.json    # 사용자 프로필
├── followups.json       # 고객 정보
├── schedules.json       # 일정 데이터
├── histories.json       # 활동 기록
├── db.sqlite3          # SQLite 데이터베이스 파일 (SQLite 사용 시)
└── media/              # 미디어 파일들 (--include-media 옵션 사용 시)
```

## 🔄 일반적인 사용 시나리오

### 1. 정기 백업 설정

Windows 작업 스케줄러나 Linux cron을 사용하여 정기 백업을 설정할 수 있습니다.

**Windows 배치 파일 예시 (`daily_backup.bat`):**

```batch
@echo off
cd /d "C:\Users\AnJaehyun\OneDrive\projects\sales-note"
python manage.py auto_backup --compress --keep-days=30
```

**Linux cron 예시:**

```bash
# 매일 새벽 2시에 백업 실행
0 2 * * * cd /path/to/sales-note && python manage.py auto_backup --compress --keep-days=30
```

### 2. 서버 이전 시 데이터 마이그레이션

```bash
# 기존 서버에서 백업
python manage.py backup_db --include-media --compress

# 새 서버에서 복원
python manage.py restore_db backup_file.zip --clear-existing --restore-media --force
```

### 3. 개발/테스트 환경 데이터 동기화

```bash
# 운영 서버에서 백업
python manage.py backup_db --compress

# 개발 환경에서 복원
python manage.py restore_db production_backup.zip --clear-existing --force
```

## ⚠️ 주의사항

### 1. 데이터 손실 방지

- `--clear-existing` 옵션은 **모든 기존 데이터를 삭제**합니다.
- 복원 전에 현재 데이터의 백업을 생성하는 것을 강력히 권장합니다.
- `--force` 옵션 없이 실행하면 확인 메시지가 표시됩니다.

### 2. 권한 및 보안

- 백업 파일에는 사용자 정보와 비밀번호 해시가 포함됩니다.
- 백업 파일을 안전한 장소에 보관하세요.
- 프로덕션 환경에서는 백업 파일을 암호화하는 것을 권장합니다.

### 3. 대용량 데이터

- `--include-media` 옵션은 모든 미디어 파일을 복사하므로 시간이 오래 걸릴 수 있습니다.
- 압축 옵션을 사용하면 백업 파일 크기를 줄일 수 있습니다.

## 🛠️ 문제 해결

### 1. 백업 실패

```bash
# 상세한 오류 메시지 확인
python manage.py backup_db --verbosity=2
```

### 2. 복원 실패

- 외래키 제약 조건 오류: 복원 순서 문제일 수 있습니다. `--clear-existing` 옵션을 사용해보세요.
- 권한 오류: Django 프로젝트 디렉토리에 쓰기 권한이 있는지 확인하세요.

### 3. 백업 파일 확인

```bash
# 백업 정보 확인 (backup_info.json 파일 내용 확인)
cat backups/sales_db_backup_YYYYMMDD_HHMMSS/backup_info.json
```

## 📊 백업 모니터링

자동 백업 실행 후 로그를 확인하여 백업 상태를 모니터링할 수 있습니다:

```bash
# 백업 상태 확인
python manage.py auto_backup --backup-dir=backups
```

이 명령어는 다음 정보를 제공합니다:

- 총 백업 개수
- 총 사용 용량
- 최근 백업 파일 목록

---

**💡 팁:** 중요한 데이터 변경 전에는 항상 백업을 먼저 생성하세요!
