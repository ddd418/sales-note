# Legacy Template Retirement Plan

Sales Note CRM의 최종 구조는 사용자 CRM 화면은 React가 맡고, Django는 login/auth/API/file/admin backend를 맡는 것입니다. Django template 삭제는 React parity, 권한 검증, 운영 수동 확인 후 작은 단위로 진행합니다.

## Runtime Policy

- Auth/login, admin, API, file/download, generated document/PDF, legal/support 화면은 Django backend에 남길 수 있습니다.
- React parity가 완료된 legacy page의 `GET`/`HEAD`는 React route로 `302` redirect합니다.
- React parity가 완료된 legacy form action의 `POST`/mutation method는 `410 Gone`으로 닫고 `Location` header에 React route를 제공합니다.
- React replacement가 없거나 업무상 폐기된 route는 별도 공지 후 `404` 또는 `410`으로 닫습니다.
- URL name과 `/reporting/*` namespace는 login/API/legacy redirect compatibility를 위해 필요한 동안 유지합니다.

## Intentionally Retained Django Templates

- `reporting/login.html`: Django session login.
- `reporting/404.html`, `reporting/500.html`: backend error pages.
- `reporting/document_pdf_template.html`: server-side PDF/document rendering.
- `reporting/privacy_policy.html`, `reporting/terms_of_service.html`: legal/support pages.
- `reporting/base.html`: remaining legacy/support templates share it during the transition; remove only after the final template audit.
- Django admin templates: framework-provided backend administration.

## First Retirement Unit

Weekly reports are the first deletion unit because React already owns:

- `/weekly-reports/`
- `/weekly-reports/new/`
- `/weekly-reports/<id>/`
- `/weekly-reports/<id>/edit/`

Django remains the weekly-report API server:

- `/reporting/api/weekly-reports/`
- `/reporting/api/weekly-reports/create/`
- `/reporting/api/weekly-reports/<id>/`
- `/reporting/api/weekly-reports/<id>/update/`
- `/reporting/api/weekly-reports/<id>/delete/`
- `/reporting/api/weekly-reports/schedules/`
- `/reporting/api/weekly-reports/ai-draft/`
- `/reporting/api/weekly-reports/<id>/manager-comment/`

Deleted templates in this unit:

- `reporting/templates/reporting/weekly_report/list.html`
- `reporting/templates/reporting/weekly_report/form.html`
- `reporting/templates/reporting/weekly_report/detail.html`

Legacy route policy in this unit:

- `/reporting/weekly-reports/` -> `/weekly-reports/`
- `/reporting/weekly-reports/create/` -> `/weekly-reports/new/`
- `/reporting/weekly-reports/<id>/` -> `/weekly-reports/<id>/`
- `/reporting/weekly-reports/<id>/edit/` -> `/weekly-reports/<id>/edit/`
- `/reporting/weekly-reports/<id>/delete/` -> `/weekly-reports/<id>/`
- old non-GET form actions -> `410 Gone`

Reference evidence:

- `rg -n "weekly_report_(list|create|detail|edit|delete)|reporting/weekly_report|weekly-reports" reporting/views.py reporting/urls.py reporting/templates frontend/server.mjs README.md docs -g "*"`
- Before deletion, active template references were the weekly-report legacy render functions and the weekly-report URL routes.
- After this unit, URL routes are handled by `react_page_retired`, frontend legacy requests redirect before proxying when possible, and the removed templates are only mentioned in historical docs/report entries.

## Candidate PR Sequence

1. Weekly reports: completed by the first retirement unit.
2. Core CRM pages already GET-redirected: customers/followups, notes/histories, schedules, calendar, customer report, dashboard, reports, data cleanup, downloads.
3. Account/employee/profile/supporting operations: companies, departments, users, manager user views, profile.
4. Commercial operations: prepayments, products, document templates, generated document helper pages.
5. Mail and pipeline: mailbox, Gmail compose/reply legacy screens, business cards, funnel.
6. Tasks and AI helper templates: `todos/templates/*`, `ai_chat/templates/*`.
7. Final shell cleanup: remove transitional base/legacy includes only after all remaining retained templates are confirmed.

Each PR must include:

- React replacement route and API parity note.
- `rg` reference search for URL names, template paths, and direct links.
- GET/HEAD redirect test and non-GET retirement or preserved API test.
- Permission check for anonymous, salesman, manager, and admin when applicable.
- Backup/rollback note and production manual test steps.

## Backup And Rollback

Before a deletion PR reaches production:

1. Confirm Railway deployment target and latest successful commit.
2. Run or verify a recent backup:

   ```powershell
   python manage.py simple_backup --format=auto --keep=7
   python scripts/backup_restore_rehearsal.py --dry-run
   ```

3. Confirm `/readyz/` reports no pending migrations.
4. Deploy the deletion PR.
5. Run `scripts/post_deploy_smoke.py` against backend and frontend.
6. Manually open the React replacement route and the old `/reporting/*` route.
7. If a deleted template is unexpectedly needed, revert the PR or redeploy the previous Railway commit. Template-only rollback does not require DB restoration.

## Final Target Shape

At the end of Z:

- Users navigate CRM work through React only.
- Django renders only login, admin, error/legal/support, and server-generated document/PDF helper templates.
- Django handles authentication, permissions, database models, business logic, JSON APIs, file upload/download/delete, Excel/PDF generation, and admin.
- `/reporting/*` remains for protected backend/API/file routes and intentional legacy redirects, not as the user-facing CRM UI.
