# Railway 데이터베이스 백업 가이드

## 방법 1: Railway CLI 사용 (권장)

### 설치 및 로그인
```bash
npm install -g @railway/cli
railway login
```

### Django 데이터 백업
```bash
# 전체 데이터 백업
railway run python manage.py dumpdata --indent=2 > backup.json

# 특정 앱만 백업
railway run python manage.py dumpdata reporting --indent=2 > reporting_backup.json

# 미디어 파일 제외하고 백업
railway run python manage.py dumpdata --exclude=contenttypes --exclude=auth.permission --indent=2 > clean_backup.json
```

### PostgreSQL 직접 백업
```bash
# 데이터베이스 URL 확인
railway variables

# pg_dump 사용 (PostgreSQL 설치 필요)
pg_dump $DATABASE_URL > backup.sql

# 또는 Railway를 통해 실행
railway run pg_dump $DATABASE_URL > backup.sql
```

## 방법 2: Railway 웹 대시보드

1. **Railway.app에 로그인**
   - https://railway.app/login

2. **프로젝트 선택**
   - sales-note 프로젝트 클릭

3. **데이터베이스 서비스 클릭**
   - PostgreSQL 서비스 선택

4. **Connect 탭**
   - Database URL 복사

5. **로컬에서 백업**
   ```bash
   pg_dump "복사한_DATABASE_URL" > backup.sql
   ```

## 방법 3: 자동화된 백업 스크립트

### railway_backup.py 스크립트 사용
```bash
python railway_backup.py
```

이 스크립트는 다음을 수행합니다:
- Railway CLI 연결 확인
- Django dumpdata 백업
- PostgreSQL pg_dump 백업 (선택사항)
- 백업 정보 파일 생성

## 방법 4: Railway 환경에서 직접 실행

```bash
# Railway 환경에 접속
railway shell

# Django 백업
python manage.py dumpdata --indent=2 > backup.json

# 파일 다운로드 (별도 방법 필요)
```

## 백업 파일 종류

### 1. Django JSON 백업 (.json)
- **장점**: Django 모델과 완벽 호환, 쉬운 복원
- **단점**: PostgreSQL 전용 기능 제외
- **용도**: 개발/테스트 환경 복원

### 2. PostgreSQL SQL 백업 (.sql)
- **장점**: 전체 데이터베이스 구조 포함
- **단점**: PostgreSQL에서만 복원 가능
- **용도**: 운영 환경 백업/복원

## 복원 방법

### Django JSON 복원
```bash
# 로컬 환경
python manage.py loaddata backup.json

# Railway 환경
railway run python manage.py loaddata backup.json
```

### PostgreSQL SQL 복원
```bash
# 데이터베이스 초기화 후 복원
psql $DATABASE_URL < backup.sql

# 또는 Railway를 통해
railway run psql $DATABASE_URL < backup.sql
```

## 주의사항

1. **백업 전 서비스 중단 권장**
   - 데이터 일관성 보장

2. **백업 파일 보안**
   - 민감한 정보 포함 가능
   - 안전한 위치에 저장

3. **정기적 백업**
   - 중요한 변경 전 반드시 백업
   - 스케줄링 고려

4. **복원 테스트**
   - 백업 파일의 유효성 확인
   - 개발 환경에서 먼저 테스트

## 트러블슈팅

### "railway command not found"
```bash
npm install -g @railway/cli
```

### "pg_dump command not found"
```bash
# Windows
choco install postgresql

# macOS
brew install postgresql

# Ubuntu
sudo apt-get install postgresql-client
```

### 대용량 백업 시간 초과
```bash
# 타임아웃 설정 증가
railway run --timeout=3600 python manage.py dumpdata > backup.json
```
