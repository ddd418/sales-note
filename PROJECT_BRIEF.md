# PROJECT_BRIEF.md

## Project

Project name: Sales Note / 영업관리 시스템

Current deployed behavior:
- Root URL should lead users into the internal sales reporting system.
- Existing CRM/reporting system is under `/reporting/*`.
- Login page title: 영업 보고 시스템.

## This project is

A Django-based internal sales management system.

The target architecture is:

- React is the single user-facing CRM frontend.
- Django is the backend for authentication, permissions, database access, business rules, files, and JSON APIs.
- Existing Django template pages are legacy transition screens and should be replaced by React pages over time.
- The final cleanup phase should remove Django frontend templates only after the React replacements are deployed and manually verified.

## This project is not

- Public marketing website
- Product catalog website
- Brand showcase website
- B2B bio distributor homepage
- Quote landing page

## Primary users

1. 영업 담당자
2. 영업 관리자
3. 대표 / 임원
4. 내부 운영 담당자

## Primary business goals

- 영업노트 작성 편의성 개선
- 영업활동 이력 관리 강화
- 거래처별 히스토리 확인 개선
- 다음 연락 / 후속조치 누락 방지
- 관리자 대시보드 개선
- 영업 단계 / 상태 가시화
- 검색 / 필터 / 정렬 개선
- 모바일에서도 빠르게 영업보고 작성 가능하게 개선
- Django/React로 분리된 화면을 React CRM으로 통일
- Django를 백엔드/API 서버 역할로 축소
- Django 템플릿 프론트엔드는 React 대체 후 최종 삭제

## Current known system

Core app:
- reporting

Important routes:
- /reporting/login/
- /reporting/*
- React CRM routes such as /dashboard/, /customers/, /notes/, /schedules/, /ai-workspace/

Long-term route behavior:
- User-facing CRM work should happen in React routes.
- `/reporting/*` should remain for login, backend APIs, legacy fallback pages, and admin/compatibility paths until each area is migrated.
- Migrated Django template pages should redirect to React or be removed only after successful production testing.

Recently added but may be out of scope:
- public_site app
- public homepage
- inquiry/product/brand/document/support/about pages

The `public_site` work should not be expanded unless explicitly requested.

## Preferred root behavior

For an internal sales system:

- If user is not authenticated: redirect `/` to `/reporting/login/`
- If user is authenticated: redirect `/` to dashboard or reporting home

Do not expose internal CRM data publicly.

## Key CRM concepts

Use these concepts when improving UX:

- 거래처
- 고객
- 담당자
- 영업 담당자
- 영업노트
- 영업보고
- 영업활동
- 방문
- 통화
- 이메일
- 미팅
- 견적
- 계약 단계
- 예상 매출
- 수주 가능성
- 다음 액션
- 다음 연락일
- 후속조치
- 지연 항목
- 완료 항목

## Phase direction

Previous public-site phases are not the main project goal.

Correct phase direction:

### React CRM Migration

Primary direction:
- Build a distinct React CRM interface, not a copy of the Django template design.
- Move customer, note, schedule, prepayment, document, email, AI, weekly report, and admin workflows into React in controlled phases.
- Keep Django views as JSON APIs or compatibility views during transition.
- Record feature parity and deletion readiness before removing templates.

### Phase 4

Existing sales system audit and stabilization.

Focus:
- Preserve reporting app
- Review accidental public_site changes
- Fix root URL behavior if needed
- Improve sales dashboard
- Improve sales note list/detail/create/edit UX
- Improve search and filters
- Improve follow-up visibility

### Phase 5

Sales pipeline and follow-up management.

Focus:
- Pipeline status
- Next action tracking
- Overdue follow-ups
- Manager view
- Activity summary

### Phase 6

Reporting and export.

Focus:
- CSV/Excel export if feasible
- Date range reports
- Sales rep performance
- Customer activity reports

## Do not implement unless requested

- Product pages
- Brand pages
- Catalog pages
- Public inquiry pages
- Public homepage sections
- SEO landing pages

## Deployment and manual testing workflow

For every completed runtime task:

- Commit and push the task changes.
- Deploy the affected Railway services (`web` and/or `sales-note-frontend`).
- Verify the production bundle/API route at a smoke-test level.
- Provide the user with a concrete server-side manual test process.
- Wait for the user's test result or explicit instruction before starting the next feature task.
