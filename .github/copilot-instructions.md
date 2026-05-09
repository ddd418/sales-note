# Copilot Instructions

## Project type

This repository is a Django-based Sales Note / Sales Management System.

It is NOT a public B2B product homepage.
It is NOT a bio/life-science distributor marketing website.
Do not create product/brand/catalog/landing-page features unless explicitly requested.

The existing core app is `reporting`, mounted under `/reporting/*`.

Primary purpose:
- Manage sales reports
- Manage sales notes
- Manage customers/accounts
- Track sales activities
- Track follow-up actions
- Support sales managers and sales reps
- Improve visibility of sales pipeline and activity history

## Current business context

The system is used as an internal sales management tool.

Primary users:
1. Sales representatives
2. Sales managers
3. Executives or admins reviewing sales activity
4. Internal operations staff

Main goals:
- Make sales notes easier to write and review
- Make customer/account activity history easier to understand
- Improve follow-up management
- Improve dashboard visibility
- Reduce manual reporting work
- Improve search, filtering, and reporting
- Keep existing CRM/reporting functionality stable

## Important scope rule

Preserve the existing `/reporting/*` CRM system.

Do not replace it with a public homepage.
Do not create public product, brand, document, catalog, or quote pages unless explicitly requested.

If a `public_site` app exists from a previous phase, treat it as secondary and do not expand it unless explicitly requested.

If the project should remain an internal sales system, root `/` should preferably redirect to `/reporting/login/` or the appropriate dashboard depending on authentication state.

## Ultimate frontend/backend direction

The long-term goal is to unify all user-facing CRM screens in React.

- React should become the only CRM frontend.
- Django should remain as the backend for login, permissions, models, business logic, files, and JSON APIs.
- Existing Django templates are legacy transition screens.
- Do not copy the Django template design into React as the final UI; build a distinct internal CRM product interface.
- Remove Django frontend templates only after React feature parity, Railway deployment, and manual server testing are complete.
- Keep `/reporting/*` stable for backend/API/login/legacy compatibility during the migration.

## Domain rules

This is a sales management system.

Use terms such as:
- 영업관리
- 영업노트
- 영업보고
- 거래처
- 고객
- 담당자
- 영업활동
- 후속조치
- 다음 연락일
- 계약 단계
- 견적
- 수주
- 실주
- 파이프라인
- 대시보드

Avoid unrelated terms such as:
- 제품 카테고리
- 브랜드 상세
- 카탈로그 다운로드
- 공식 대리점
- 바이오 실험장비
- 기술지원/AS
unless these already exist in the actual sales system domain.

## UX principles

Prioritize:
- Fast data entry
- Clear sales activity history
- Easy search and filtering
- Quick follow-up tracking
- Dashboard summary
- Mobile-friendly sales note entry
- Clear status badges
- Minimal clicks for common sales tasks
- Stable authenticated workflow

Every major authenticated page should make it easy to answer:

1. What customer/account is this?
2. What happened recently?
3. What is the current sales status?
4. What is the next action?
5. Who is responsible?
6. When should we follow up?
7. Is there any overdue action?

## Sales note requirements

When improving sales note/report features, consider fields such as:

- 거래처 / 고객
- 담당자
- 영업 담당자
- 방문/통화/메일/미팅 등 활동 유형
- 활동일
- 제목
- 내용
- 영업 단계
- 예상 금액
- 견적 여부
- 수주 가능성
- 다음 액션
- 다음 연락일
- 첨부파일 if existing or feasible
- 상태
- 작성자
- 수정일

Do not add database fields blindly.
Before adding or changing models, inspect existing models and migrations.
If schema change is needed, explain it in AGENT_PLAN.md before implementation.

## Dashboard requirements

A useful sales dashboard should include, where feasible:

- 오늘의 영업활동
- 최근 영업노트
- 예정된 후속조치
- 지연된 후속조치
- 담당자별 활동 수
- 단계별 영업 건수
- 이번 주 / 이번 달 활동 현황
- 최근 업데이트된 거래처
- 빠른 작성 버튼

## Search and filtering requirements

Improve list pages with practical filters where feasible:

- 날짜 범위
- 거래처
- 담당자
- 영업 담당자
- 활동 유형
- 상태
- 영업 단계
- 다음 연락일
- 키워드 검색
- 지연/예정 후속조치

## Security and permissions

Preserve authentication and authorization.

Do not expose internal sales data publicly.
Do not make authenticated pages public.
Do not weaken login, session, CSRF, or permission checks.
Do not commit secrets or credentials.

If permissions are unclear, preserve existing behavior and document concerns in AGENT_REPORT.md.

## Development rules

Follow the existing Django structure.

Before making major changes:
1. Inspect models, views, forms, URLs, templates, static files, and settings.
2. Create or update AGENT_PLAN.md.
3. Keep changes scoped.
4. Prefer incremental improvements.
5. Avoid unrelated large refactors.
6. Preserve existing URLs unless there is a clear reason.
7. Run validation commands.
8. For runtime changes, commit, push, deploy affected Railway service(s), and provide manual production test steps before starting the next task.

## Validation

Before finishing any implementation, run available checks such as:

- python manage.py check
- python manage.py test if tests exist
- python manage.py makemigrations --check --dry-run if model changes are not intended
- URL smoke checks if possible
- Form POST checks if possible

Document commands and results in AGENT_REPORT.md.

## Deliverables

At the end of each task, create or update AGENT_REPORT.md with:

1. Summary of changes
2. Files changed
3. Existing functionality preserved
4. New CRM/sales-management improvements
5. Commands run and results
6. Known limitations
7. Risks
8. Recommended next phase
9. Railway deployment status when applicable
10. Manual server test process
