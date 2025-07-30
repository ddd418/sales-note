# Railway 환경 변수 설정 가이드

## 필수 환경 변수

### 1. 백업 API 인증 토큰
```
BACKUP_API_TOKEN=your_secure_random_token_here
```
- 추천: 32자 이상의 랜덤 문자열
- 예시: `openssl rand -base64 32` 명령으로 생성

### 2. 이메일 설정 (기존)
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=jhahn.hana@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=jhahn.hana@gmail.com
```

## GitHub Repository Secrets 설정

### GitHub 저장소의 Settings > Secrets and variables > Actions에서 설정:

1. **BACKUP_API_TOKEN**
   - Railway에서 설정한 것과 동일한 값

2. **RAILWAY_APP_URL**
   - Railway 앱의 URL (예: https://your-app.railway.app)

## 설정 확인 방법

1. Railway 배포 후 백업 상태 확인:
   ```
   curl https://your-app.railway.app/backup/status/
   ```

2. 수동 백업 테스트:
   ```
   curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-app.railway.app/backup/database/
   ```

3. GitHub Actions에서 수동 워크플로우 실행 테스트

## 백업 스케줄
- 매일 오전 8시 (한국시간)
- GitHub Actions가 Railway API를 호출
- 백업 완료 후 이메일 알림 전송

## 장점
1. Railway의 제한사항 우회
2. 외부 스케줄링으로 안정성 확보
3. GitHub Actions 로그로 백업 이력 추적
4. 실패 시 자동 알림
