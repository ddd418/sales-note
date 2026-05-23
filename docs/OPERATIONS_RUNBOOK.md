# Operations Runbook

Sales Note 운영 배포, 점검, 백업/복구 리허설 절차입니다. 내부 CRM 데이터가 외부에 노출되지 않도록 health endpoint와 smoke test는 시스템 상태와 인증 보호 여부만 확인합니다.

## Healthcheck

- Backend liveness: `/healthz/`
  - Railway healthcheck용 공개 endpoint입니다.
  - DB를 조회하지 않고 service/status/environment/commit만 반환합니다.
- Backend readiness: `/readyz/`
  - 배포 후 smoke test용 endpoint입니다.
  - DB 연결과 pending migration 수만 확인하며 고객/영업 데이터는 반환하지 않습니다.
- Frontend liveness: `/healthz/`
  - Node static/proxy server가 직접 응답합니다.

Railway 설정:

```toml
[deploy]
healthcheckPath = "/healthz/"
healthcheckTimeout = 30
```

## Migration 포함 배포 절차

1. 로컬에서 Django/React 검사를 완료합니다.
2. 운영 DB 백업 또는 백업 상태를 확인합니다.
3. destructive migration은 expand-and-contract 방식으로 나눕니다.
4. backend는 `python manage.py migrate && gunicorn ...` 순서로 시작합니다.
5. frontend build와 static/proxy server healthcheck를 확인합니다.
6. 배포 직후 smoke test를 실행합니다.
7. Railway logs에서 migration, 4xx/5xx 증가, webhook alert를 확인합니다.

Post-deploy smoke:

```powershell
python scripts/post_deploy_smoke.py `
  --backend-url https://web-production-8a820.up.railway.app `
  --frontend-url https://sales-note-frontend-production.up.railway.app
```

운영 계정으로 인증 API까지 확인할 때:

```powershell
$env:SMOKE_USERNAME="..."
$env:SMOKE_PASSWORD="..."
python scripts/post_deploy_smoke.py
```

## Backup/Restore Rehearsal

dry-run:

```powershell
python scripts/backup_restore_rehearsal.py --dry-run
```

실제 리허설은 반드시 운영 DB와 다른 대상 DB를 사용합니다.

```powershell
$env:DATABASE_URL="postgresql://source..."
$env:RESTORE_REHEARSAL_DATABASE_URL="postgresql://target..."
python scripts/backup_restore_rehearsal.py --allow-target-reset
```

주의:

- source와 target URL이 같으면 즉시 실패합니다.
- `--allow-target-reset` 없이는 target DB를 지우지 않습니다.
- 출력에는 DB URL의 계정/비밀번호를 노출하지 않습니다.

수동 백업 command:

```powershell
python manage.py simple_backup --format=auto --keep=7
```

## Logs And Alerts

Railway 기본 로그는 stdout/stderr 기준입니다. Django 운영 로그 레벨은 `DJANGO_LOG_LEVEL`로 조정합니다.

선택적으로 `ERROR_ALERT_WEBHOOK_URL`을 설정하면 `reporting`, `django`, `django.request` ERROR 로그가 JSON webhook으로 전송됩니다. Payload는 service, environment, logger, path, status code 같은 메타 정보만 포함하고 request header, cookie, POST body, secret 값은 보내지 않습니다.

## Env And Security Audit

정기 점검:

```powershell
python manage.py audit_runtime_config --json
```

경고까지 실패로 볼 때:

```powershell
python manage.py audit_runtime_config --json --fail-on-warning
```

주요 점검 대상:

- `SECRET_KEY`
- `DATABASE_URL`
- `FRONTEND_PIPELINE_URL`
- `EMAIL_ENCRYPTION_KEY`
- `BACKUP_API_TOKEN`
- `ERROR_ALERT_WEBHOOK_URL`
- `SESSION_COOKIE_AGE`
- `SESSION_COOKIE_SECURE`
- `SESSION_COOKIE_HTTPONLY`
- `SESSION_COOKIE_SAMESITE`
- `CSRF_COOKIE_SECURE`
- `SECURE_SSL_REDIRECT`
- `HSTS_SECONDS`
- `SALES_NOTE_READONLY_TOKEN`

## Admin User Handling

배포 스크립트는 더 이상 고정 계정/비밀번호로 superuser를 만들지 않습니다. 관리자 계정 생성과 비밀번호 회전은 운영 환경별 runbook 또는 Django admin 절차로 처리합니다.
