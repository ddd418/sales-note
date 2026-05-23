# Sales Note CRM

내부 영업 CRM/리포팅 시스템입니다. 현재 운영 방향은 Django가 인증, 권한, 데이터 모델, 업무 로직, 파일 처리, JSON API를 맡고 React가 사용자-facing CRM 화면을 맡는 구조입니다.

이 저장소는 공개 사이트가 아니라 사내 영업/납품/견적/선결제/서비스 기록을 다루는 업무 시스템입니다. 내부 고객 데이터와 메일/영업 기록이 외부에 노출되지 않도록 인증과 권한 범위를 유지해야 합니다.

## 현재 구조

- `reporting/`: Django CRM 핵심 앱. 고객, 부서/연구실, 일정, 납품, 견적, 선결제, 장비, A/S, 교정, 리포트 API를 포함합니다.
- `todos/`: 현재 사용 중인 TODO/업무 하달 Django 앱입니다. `/todos/`와 `/reporting/api/tasks/*` 흐름의 기준 앱입니다.
- `ai_chat/`: CRM 컨텍스트 기반 AI 답변 보조 로직입니다. 사실 판단은 reporting의 구조화 데이터와 공통 원장 helper를 우선해야 합니다.
- `frontend/`: React/TypeScript CRM 프론트엔드입니다. 고객, 일정, 납품, 선결제, 리포트, AI 워크스페이스 등 운영 화면을 담당합니다.
- `sales_project/settings.py`: 기본 Django settings 진입점입니다. Railway/DATABASE_URL 환경에서는 `settings_production.py`로 분기합니다.
- `sales_project/settings_production.py`: Railway 운영 배포용 settings입니다.
- `templates/`, `reporting/templates/`: 기존 Django 템플릿 화면입니다. React 기능 parity가 검증되기 전에는 삭제하지 않습니다.
- `AGENT_PLAN.md`, `AGENT_REPORT.md`: 작업 계획과 결과 기록입니다.

## 루트 정리 상태

다음 과거 산출물은 2026-05-23 기준으로 설정, URL, import, 배포 구성 참조 여부를 확인한 뒤 제거했습니다.

- `lovable/`: 독립 TSX/CSS UI prototype 산출물입니다. 현재 `frontend/` 빌드나 Django 설정에서 사용하지 않습니다.
- `sales-reporting-system/`: 초기 정적 HTML/CSV/이미지 기획 산출물입니다. 운영 앱과 연결되지 않습니다.
- `todolist/`: 미사용 Django 앱 skeleton입니다. 활성 업무 앱은 `todos/`입니다.
- `sales_project/settings_correct.py`: 중복/과거 settings 파일입니다. 실제 진입점은 `sales_project/settings.py`입니다.

추가 루트 정리는 같은 절차를 따릅니다. 먼저 `rg`로 참조 여부를 확인하고, `settings.py`, `settings_production.py`, `sales_project/urls.py`, Railway/Nixpacks 설정, 테스트 경로에 영향이 없는 경우에만 제거합니다.

## 중요한 업무 기준

- 고객 기준은 개별 담당자 `FollowUp`이 아니라 가능한 한 `Department` 즉 부서/연구실 계정 기준으로 봅니다.
- 같은 부서/연구실의 담당자들은 납품, 견적, 선결제, 장비, 서비스 기록을 공유합니다.
- 납품 결제 구분은 메모 추정이 아니라 구조화 데이터로 판단합니다.
- 선결제 차감 납품은 `Schedule.delivery_payment_type`, `Schedule.use_prepayment`, `Schedule.prepayment`, `Schedule.prepayment_amount`, `PrepaymentUsage` 같은 구조화 필드/내역으로만 확정합니다.
- `/reporting/*` 라우트와 기존 backend 기능은 유지합니다.

## 로컬 실행

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

React 개발 서버:

```powershell
cd frontend
npm install
npm run dev
```

운영 빌드 확인:

```powershell
cd frontend
npm run build
```

## 자주 쓰는 검사

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.ReactReportsProfileBusinessCardApiTests
cd frontend; npx tsc --noEmit --pretty false
cd frontend; npm run build
```

## 배포

운영 환경은 Railway를 사용합니다. 런타임 동작에 영향을 주는 변경은 테스트 후 commit/push하고, Railway 배포 상태와 운영 URL 수동 검수 결과를 `AGENT_REPORT.md`에 남깁니다.

문서/미사용 산출물 삭제처럼 런타임 동작에 영향이 없는 변경은 Railway 재배포 대상이 아닙니다. 그래도 Django 설정 검증과 핵심 smoke 테스트 결과는 `AGENT_REPORT.md`에 기록합니다.

운영 안정화 절차는 [Operations Runbook](docs/OPERATIONS_RUNBOOK.md)에 정리되어 있습니다.

자주 쓰는 운영 점검:

```powershell
python manage.py audit_runtime_config --json
python scripts/post_deploy_smoke.py --backend-url https://web-production-8a820.up.railway.app --frontend-url https://sales-note-frontend-production.up.railway.app
python scripts/backup_restore_rehearsal.py --dry-run
```

## 다음 개발 우선순위

1. 계정/prepayment/asset/AI API를 `reporting/api/` 하위 모듈로 단계적으로 분리합니다.
2. `frontend/src/App.tsx`의 계정, 선결제, 장비, AI 화면을 `pages/` 모듈로 계속 분리합니다.
3. 중복 담당자/부서 병합 및 잘못 연결된 납품/선결제 이관 도구를 안정화합니다.
4. `/reports/`를 계정별 현황표 중심으로 계속 고도화합니다.
5. `/assets/` 장비/A/S/교정 운영 수동 검수 후 접수 흐름과 고객 선택 자동완성을 보강합니다.
