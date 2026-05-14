# React CRM Migration Plan

## Goal

Move every user-facing legacy Django CRM menu into the React CRM, then retire the Django frontend templates after React replacements are deployed and manually verified.

Django remains the backend for authentication, permissions, models, business rules, file handling, OAuth callbacks, downloads, and JSON APIs. React owns authenticated CRM product screens.

## Chosen Direction

- Migration style: 업무형 v1.
  - Each migrated menu must support the core real work in React.
  - Django legacy screens remain as fallback until production manual testing is complete.
- First wave: missing legacy menus.
  - ToDo/업무하달, 관리자/직원관리, 리포트, 프로필, 명함 관리 are the first migration group.
- Documentation location:
  - This document is the long-term source of truth.
  - `AGENT_PLAN.md` should reference this document for each implementation task.

## Current Legacy Menu Inventory

The current legacy sidebar source is `reporting/templates/reporting/base.html`. The following menu map is the working migration contract.

| Legacy menu | Legacy route | Current React state | Target React route | First action |
| --- | --- | --- | --- | --- |
| 대시보드 | `/reporting/dashboard/` | Exists | `/dashboard/` | Remove remaining legacy entry points after validation |
| 관리자, admin | `/reporting/users/` | Missing | `/settings/users/` | Build React user admin v1 |
| 관리자, manager | `/reporting/manager/users/` | Missing | `/settings/users/` | Build manager-scoped user list/create/edit v1 |
| 고객사 관리 | `/reporting/companies/` | Partial under customers | `/customers/companies/` | Add company/department management mode |
| 고객 | `/reporting/followups/`, `/reporting/customer-report/` | Exists | `/customers/` | Close customer-report and followup fallback gaps |
| 업무 하달 | `/todos/manager/` | Missing | `/tasks/manager/` | Build manager task assignment dashboard v1 |
| TODOLIST | `/todos/` | Missing | `/tasks/` | Build personal task list/detail/create v1 |
| AI | `/ai/` | Exists as AI workspace | `/ai-workspace/` | Fold useful legacy AI analysis links into AI workspace |
| 일정 캘린더 | `/reporting/schedules/calendar/` | Exists | `/schedules/calendar/` | Remove Django create/detail fallback after parity |
| 영업노트 | `/reporting/histories/` | Exists | `/notes/` | Remove Django detail/edit fallback after parity |
| 파이프라인 | `/reporting/funnel/pipeline/` | Exists at root pipeline | `/pipeline/` | Normalize React route and keep `/` as alias |
| 주간보고 | `/reporting/weekly-reports/` | Exists | `/weekly-reports/` | Remove Django list/detail/edit fallback after parity |
| 선결제 관리 | `/reporting/prepayment/` | Exists | `/prepayments/` | Remove Django management links after parity |
| 제품 관리 | `/reporting/products/` | Exists | `/products/` | Remove Django edit/list fallback after parity |
| 서류 관리 | `/reporting/documents/` | Exists | `/documents/` | Keep file download/generation endpoints backend-only |
| 메일함 | `/reporting/mailbox/inbox/` | Exists | `/mailbox/` | Remove Django mailbox/thread fallback after parity |
| 명함 관리 | `/reporting/business-cards/` | Missing | `/mailbox/business-cards/` | Build React business card CRUD v1 |
| 업체 조회, manager | `/reporting/manager/companies/` | Partial under customers | `/customers/companies/` | Add manager read-only company mode |
| 리포트 | `/reporting/analytics/` | Missing | `/reports/` | Build React analytics/report dashboard v1 |
| 프로필 관리 | `/reporting/profile/` | Missing | `/profile/` | Build React profile/email connection settings v1 |

## Target React Navigation

React navigation must be generated from authenticated user capabilities, not hardcoded only by path.

Common authenticated items:

- 대시보드: `/dashboard/`
- 고객: `/customers/`
- 파이프라인: `/pipeline/`
- 영업노트: `/notes/`
- 일정: `/schedules/calendar/`
- 업무: `/tasks/`
- 주간보고: `/weekly-reports/`
- 서류: `/documents/`
- 제품: `/products/`
- 선결제: `/prepayments/`
- 리포트: `/reports/`
- 프로필: `/profile/`

Conditional items:

- AI: show only when `UserProfile.can_use_ai` is true, target `/ai-workspace/`.
- 메일/명함: hide from manager role unless backend permissions explicitly allow it, targets `/mailbox/` and `/mailbox/business-cards/`.
- 직원관리: admin and manager only, target `/settings/users/`.
- 업무하달: manager only, target `/tasks/manager/`.
- 고객사 관리: admin and salesman as editable, manager as read-only, target `/customers/companies/`.

## API Boundary

Prefer new React-facing APIs under `/reporting/api/*` because the frontend production server already proxies `/reporting/*` to Django.

Minimum new or expanded APIs:

- `/reporting/api/navigation/`
  - Returns role, capability flags, visible menu items, and admin/manager filter context.
- `/reporting/api/tasks/*`
  - Personal task list/detail/create/edit/delete/status.
  - Manager assignment dashboard/detail/create/status/cancel.
- `/reporting/api/reports/*`
  - Analytics dashboard data and export links.
- `/reporting/api/users/*`
  - Admin/manager-scoped user list/create/edit/toggle-active/toggle-ai.
- `/reporting/api/profile/`
  - Profile detail/update and email connection status links.
- `/reporting/api/business-cards/*`
  - Business card list/create/edit/delete/set-default.
- `/reporting/api/companies/*`
  - Company/department management gaps not already covered by existing customer APIs.

API requirements:

- Preserve session authentication and CSRF behavior.
- Return JSON `401` for unauthenticated API requests where existing React APIs do so.
- Return `403` for authenticated users without permission.
- Preserve existing company/user scoping from `UserProfile`, admin filters, and manager filters.
- Do not expose internal sales data to anonymous users.
- Do not introduce model changes unless a task-specific plan explicitly approves them.

## Backend Routes That Remain

These routes are backend responsibilities and should not be deleted as part of frontend template retirement:

- `/admin/`
- `/reporting/login/` and `/reporting/logout/` until a React login replacement is planned and verified.
- `/reporting/api/*`
- File downloads and uploads, including note files, schedule files, document templates, generated documents, mailbox attachments, and editor image upload.
- Gmail and IMAP OAuth/connect/disconnect/callback routes.
- `/media/*` and static asset serving required by Django backend workflows.
- Privacy/terms pages unless a separate decision moves them to React/static content.

## Migration Waves

### Wave 0: Documentation and route contract

- Create and maintain this migration plan.
- Keep `AGENT_PLAN.md` focused on the current implementation task and link to this plan.
- For each wave, update the menu map with done, fallback, redirect, or delete status.

Exit criteria:

- The migration map exists in this document.
- `AGENT_PLAN.md` records the active migration task.
- No runtime deployment is required for docs-only changes.

### Wave 1: Missing menu React v1

Build React pages and APIs for:

- `/tasks/`
- `/tasks/manager/`
- `/settings/users/`
- `/reports/`
- `/profile/`
- `/mailbox/business-cards/`

Exit criteria:

- Each page supports core list/detail/create or update behavior needed for daily work.
- Role-based menu visibility works for admin, manager, and salesman.
- Legacy menu links can remain visible only as fallback actions, not primary navigation.
- Production manual testing is complete before any template deletion.

### Wave 2: Existing React page fallback closure

Close the remaining Django fallback links inside existing React pages:

- Customer report and company/department management from customers.
- Schedule create/detail/edit/delete gaps.
- Notes detail/edit/file/comment gaps.
- Mailbox thread/reply and Gmail settings gaps.
- Weekly report list/detail/edit gaps.
- Document, product, and prepayment management gaps.
- Pipeline route normalization to `/pipeline/`.

Exit criteria:

- Users can complete each workflow from React without jumping to a Django template.
- Backend download/OAuth/API endpoints remain available.
- Legacy GET routes are ready for redirect after production verification.

### Wave 3: Compatibility redirects

- Convert verified legacy template GET routes to redirects to the matching React route.
- Keep POST/API/download/OAuth endpoints intact.
- Add tests for important redirects and permission behavior.

Exit criteria:

- Old bookmarks land on React screens.
- Anonymous users still go to login or receive expected API protection.
- No verified workflow depends on a Django template page.

### Wave 4: Template and static cleanup

- Delete only templates and static assets with completed React replacements and redirect coverage.
- Search for every deleted template name in Django views/tests before removal.
- Keep `reporting` app and `/reporting/*` backend namespace.

Exit criteria:

- `python manage.py check` passes.
- Targeted Django tests pass.
- React build passes.
- Production smoke and manual server testing pass.
- `AGENT_REPORT.md` lists exactly what was removed and why.

## Per-Task Implementation Checklist

Before changing runtime code:

- Inspect the legacy URL, view, template, form, model, permission, POST behavior, file behavior, and existing API.
- Update `AGENT_PLAN.md` with the current task scope and whether DB migrations are expected.
- Prefer extending existing serializers/payload helpers and permission utilities.
- Keep React UI distinct from Django Bootstrap templates.
- Preserve fallback routes until manual production verification.

Before finishing a runtime task:

- Run `python manage.py check`.
- Run `python manage.py makemigrations --check --dry-run` unless model changes are intended.
- Run relevant Django tests.
- Run `cd frontend; npm run build`.
- Run `cd frontend; node --check server.mjs`.
- Run `git diff --check`.
- Commit, push, deploy affected Railway service(s), and record production smoke/manual test steps in `AGENT_REPORT.md`.

## Deletion Gate

A Django template or legacy frontend route is deletion-ready only when all conditions are true:

- React replacement is implemented and deployed.
- Permission behavior is equivalent or stricter.
- Data scoping is equivalent or stricter.
- Create/update/delete behavior is covered by React API tests where relevant.
- File upload/download behavior is preserved or explicitly moved to backend-only endpoints.
- Old GET route redirects to React or is proven unused.
- User completed production manual testing.
- `AGENT_REPORT.md` records the verification.

## Current Next Task

Wave 1 should start with the missing menu group because those are still visible in Django but absent from React navigation:

1. Add `/reporting/api/navigation/` and use it to drive React menu visibility.
2. Add React route shells for `/tasks/`, `/tasks/manager/`, `/settings/users/`, `/reports/`, `/profile/`, and `/mailbox/business-cards/`.
3. Implement ToDo/업무하달 APIs and React v1 first, because `todos` is a separate legacy app and currently has no React surface.
4. After ToDo v1 production verification, proceed to users, reports, profile, and business cards in separate scoped tasks.
