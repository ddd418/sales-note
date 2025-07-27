# Railway 서버 Activity Type 수정 가이드

## 문제 상황

- 데이터베이스에 `meeting` 값이 있어서 필터링이 제대로 작동하지 않음
- `meeting` → `customer_meeting`으로 변경 필요

## 해결 방법

### 1단계: 코드 배포

현재 수정 사항을 Railway에 배포:

```bash
git add .
git commit -m "Add fix_activity_types management command"
git push origin main
```

### 2단계: Railway 콘솔에서 데이터 확인

Railway 대시보드 → 프로젝트 → Variables 탭에서 다음 명령어 실행:

#### 먼저 현재 상태 확인 (dry-run):

```bash
python manage.py fix_activity_types --dry-run
```

#### 실제 수정 실행:

```bash
python manage.py fix_activity_types --confirm
```

### 3단계: 결과 확인

수정 후 일정 목록 페이지에서 필터링이 정상 작동하는지 확인

## 주의사항

- `--dry-run`으로 먼저 확인 후 `--confirm`으로 실행
- 데이터 백업 후 진행 권장
- 작업 중 오류 발생 시 트랜잭션 롤백됨

## 예상 결과

- `meeting` → `customer_meeting` 변경
- `delivery_schedule` → `delivery` 변경 (있다면)
- 일정 목록 페이지의 미팅 필터가 정상 작동
