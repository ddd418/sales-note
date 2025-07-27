# Railway 이메일 알림 설정 가이드

## 📧 jhahn.hana@gmail.com 알림 활성화 방법

### 1. Gmail 앱 비밀번호 생성

#### 단계 1: Google 계정 보안 설정

1. https://myaccount.google.com/security 접속
2. **2단계 인증** 활성화 (필수)
3. **앱 비밀번호** 섹션으로 이동

#### 단계 2: 앱 비밀번호 생성

1. "앱 비밀번호" 클릭
2. 앱 선택: "기타(사용자 지정 이름)"
3. 이름 입력: "Sales Note Backup"
4. **생성** 클릭
5. 📝 **16자리 비밀번호 복사 및 안전하게 보관**

### 2. Railway 환경변수 설정

#### Railway 대시보드에서 설정:

1. https://railway.app/dashboard 접속
2. **sales-note** 프로젝트 선택
3. **Variables** 탭 클릭
4. 다음 환경변수들 추가:

```
# 이메일 알림 설정 (필수)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=jhahn.hana@gmail.com
SMTP_PASSWORD=[위에서 생성한 16자리 앱 비밀번호]

# Slack 알림 설정 (선택사항)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 3. 환경변수 입력 예시

**SMTP_USERNAME**:

```
jhahn.hana@gmail.com
```

**SMTP_PASSWORD**:

```
abcd efgh ijkl mnop
```

_실제로는 공백 없이 16자리_

**SMTP_SERVER**:

```
smtp.gmail.com
```

**SMTP_PORT**:

```
587
```

### 4. 설정 확인 방법

#### 수동 테스트:

1. Railway 대시보드에서 **Settings > Cron Jobs**
2. 백업 작업 찾기
3. **"Run Now"** 클릭
4. 몇 분 후 jhahn.hana@gmail.com 메일함 확인

#### 로그 확인:

Railway 로그에서 다음 메시지 확인:

```
📧 ✅ 성공 알림을 jhahn.hana@gmail.com으로 전송했습니다.
```

### 5. 이메일 알림 내용

#### 백업 성공 시:

```
제목: [자동] Sales Note DB 백업 완료 - 2025-07-27 08:00

내용:
안녕하세요,

Sales Note 데이터베이스 자동 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 완료 시간: 2025년 07월 27일 08시 00분
• 백업 파일: railway_backup_20250727_080000.sql
• 파일 크기: 2.34 MB
• 소요 시간: 45.2초

💾 백업 상태: ✅ 성공

이 백업은 7일간 보관된 후 자동으로 삭제됩니다.
```

#### 백업 실패 시:

```
제목: 🚨 [자동] Sales Note DB 백업 실패 - 2025-07-27 08:00

내용:
⚠️ 주의: Sales Note 데이터베이스 자동 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: 2025년 07월 27일 08시 00분
• 오류 메시지: Connection timeout

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_URL 환경변수 확인
3. 필요시 수동 백업 실행
```

## 🔧 문제 해결

### 이메일이 전송되지 않는 경우:

1. **2단계 인증 확인**

   - Google 계정에서 2단계 인증이 활성화되어 있는지 확인

2. **앱 비밀번호 재생성**

   - 기존 앱 비밀번호 삭제 후 새로 생성

3. **환경변수 재확인**

   - Railway에서 SMTP 관련 환경변수들이 정확히 설정되었는지 확인

4. **Railway 로그 확인**
   ```bash
   railway logs
   ```

### Gmail 보안 경고가 뜨는 경우:

1. **앱 비밀번호 사용 확인**

   - 일반 비밀번호가 아닌 앱 비밀번호를 사용해야 함

2. **계정 보안 검토**
   - Gmail에서 "보안 수준이 낮은 앱의 액세스" 차단된 경우 해제

## ✅ 최종 체크리스트

- [ ] Google 2단계 인증 활성화
- [ ] Gmail 앱 비밀번호 생성
- [ ] Railway 환경변수 4개 설정
- [ ] 수동 백업 테스트 실행
- [ ] jhahn.hana@gmail.com 메일함 확인
- [ ] Railway 로그에서 성공 메시지 확인

---

**📝 마지막 업데이트**: 2025년 7월 27일  
**📧 알림 대상**: jhahn.hana@gmail.com  
**⏰ 백업 시간**: 매일 오전 8시 (한국시간)
