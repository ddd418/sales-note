# 🚀 Sales Note 서버 배포 가이드

## 📋 배포 전 준비사항

### 1. 로컬 테스트 완료 확인
- [ ] 새로운 Company/Department 모델 테스트 완료
- [ ] 팔로우업 검색 기능 테스트 완료
- [ ] 일정 캘린더 삭제 기능 테스트 완료
- [ ] 모든 마이그레이션 파일 정상 적용 확인

### 2. 서버 데이터 백업
```bash
# 현재 서버 데이터 백업
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# SQLite인 경우
cp db.sqlite3 db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

## 🔄 단계별 배포 프로세스

### Phase 1: 서버 상태 확인
```bash
# 1. 서버에 접속하여 현재 상태 확인
python pre_deployment_check.py

# 2. 서비스 상태 확인 (필요시)
systemctl status your-app-name
```

### Phase 2: 코드 배포
```bash
# 1. 기존 서비스 중단 (무중단 배포가 아닌 경우)
systemctl stop your-app-name

# 2. 코드 업데이트
git pull origin main

# 또는 직접 파일 업로드
# scp -r ./sales-note user@server:/path/to/app/
```

### Phase 3: 데이터베이스 마이그레이션
```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 의존성 업데이트 (필요시)
pip install -r requirements.txt

# 3. 마이그레이션 파일 생성 및 적용
python manage.py makemigrations
python manage.py migrate

# 4. 기존 데이터 마이그레이션 실행
python migrate_existing_data.py
```

### Phase 4: 데이터 검증
```bash
# 1. Django 쉘에서 데이터 확인
python manage.py shell

# 쉘에서 실행:
from reporting.models import Company, Department, FollowUp

print(f"회사: {Company.objects.count()}개")
print(f"부서: {Department.objects.count()}개") 
print(f"팔로우업: {FollowUp.objects.count()}개")

# 샘플 데이터 확인
sample = FollowUp.objects.first()
if sample:
    print(f"샘플 - 회사: {sample.company}, 부서: {sample.department}")
```

### Phase 5: 서비스 재시작 및 테스트
```bash
# 1. 정적 파일 수집 (필요시)
python manage.py collectstatic --noinput

# 2. 서비스 재시작
systemctl start your-app-name
systemctl status your-app-name

# 3. 로그 확인
tail -f logs/app.log
```

## ⚠️ 위험 요소 및 대응 방안

### 1. 데이터 손실 위험
**대응책:**
- 반드시 백업 생성 후 진행
- 단계별로 진행하며 각 단계마다 검증
- 롤백 계획 준비

### 2. 서비스 중단 시간
**대응책:**
- 사용량이 적은 시간대에 배포
- Blue-Green 배포 고려 (가능한 경우)

### 3. 마이그레이션 실패
**대응책:**
```bash
# 롤백 프로세스
systemctl stop your-app-name
cp db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
git checkout previous-version
systemctl start your-app-name
```

## 🔧 트러블슈팅

### 문제 1: Company/Department 외래키 오류
```bash
# 해결: 수동으로 기본 데이터 생성
python manage.py shell

from reporting.models import Company, Department, User
user = User.objects.first()
company = Company.objects.create(name="기본 업체", created_by=user)
department = Department.objects.create(company=company, name="기본 부서", created_by=user)
```

### 문제 2: 마이그레이션 충돌
```bash
# 해결: 마이그레이션 상태 확인 및 수동 해결
python manage.py showmigrations
python manage.py migrate --fake-initial
```

### 문제 3: 기존 데이터 참조 오류
```bash
# 해결: 임시로 nullable 설정 후 데이터 정리
# models.py에서 필드에 null=True, blank=True 추가
# 마이그레이션 적용 후 데이터 정리
# 다시 필수 필드로 변경
```

## ✅ 배포 완료 체크리스트

- [ ] 백업 파일 생성 확인
- [ ] 마이그레이션 정상 적용
- [ ] Company/Department 데이터 생성 확인
- [ ] FollowUp 관계 연결 확인
- [ ] 웹 페이지 정상 접속
- [ ] 팔로우업 목록 정상 표시
- [ ] 일정 캘린더 정상 동작
- [ ] 검색 기능 정상 동작
- [ ] 새 팔로우업 생성 기능 확인
- [ ] 일정 삭제 기능 확인

## 📞 비상 연락처

배포 중 문제 발생시:
1. 즉시 서비스 중단
2. 백업으로 롤백
3. 로그 수집 및 분석
4. 필요시 개발팀 연락

---

**⚠️ 중요: 이 가이드를 단계별로 신중하게 따라주세요. 각 단계마다 검증을 거쳐야 합니다.**
