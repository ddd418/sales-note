# Sales Note Handoff

Last updated: 2026-05-10 KST

## Current Goal

The long-term goal is to unify the CRM frontend into React while keeping Django as the backend/API layer.

- React should become the only user-facing CRM frontend after feature parity.
- Django should remain responsible for login, permissions, models, business logic, files, and JSON APIs.
- Django template pages must remain usable during the transition.
- Do not copy the old Django visual design into React. Build a distinct internal CRM interface.
- Remove Django frontend templates only after React feature parity, Railway deployment, and manual production testing are complete.

## Current Task

React mailbox reply quote cleanup.

Implemented locally, push/deploy pending:

- React mailbox thread display body now removes Gmail/Outlook quoted previous-message chains.
- Text quote markers handled include Korean Gmail `님이 작성:`, English `On ... wrote:`, Outlook `Original Message`, `보낸 사람:`, `From:`, `Sent:`, `To:` and common Outlook app footer markers.
- HTML quote containers handled include `gmail_quote`, Outlook reference containers, and blockquotes.
- Only React API display `bodyText` is trimmed; stored `EmailLog.body/body_html` remains intact, so AI analysis is not reduced.
- DB 변경 없음.

Validation:

```powershell
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=2
python -m py_compile reporting\gmail_views.py reporting\tests.py
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 5 React mailbox API tests OK.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Manual production test after deploy:

1. Open a multi-reply thread in `/mailbox/thread/<thread_id>/`.
2. Confirm each card only shows the new body for that email.
3. Confirm the original stored email remains available to backend/AI flows.

## Previous Task

React mailbox body linebreak fix.

Implemented locally, push/deploy pending:

- React mailbox thread `bodyText` now preserves original text newlines.
- HTML email bodies convert `<br>`, paragraph/div/list/table row endings into newlines before tag stripping.
- Mailbox list `preview` remains compact and single-line.
- Regression test added to ensure `/reporting/api/mailbox/thread/<thread_id>/` preserves blank lines and line breaks.
- DB 변경 없음.

Validation:

```powershell
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=2
python -m py_compile reporting\gmail_views.py reporting\tests.py
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend; npm run build
git diff --check
```

Results:

- 3 React mailbox API tests OK.
- Django check OK.
- No migration changes.
- React build OK.
- `git diff --check` OK with LF→CRLF warnings only.

Manual production test after deploy:

1. Open `https://sales-note-frontend-production.up.railway.app/mailbox/`.
2. Open a thread with multi-line customer email content.
3. Confirm paragraph breaks and newlines are preserved in `/mailbox/thread/<thread_id>/`.

## Previous Task

React mailbox first integration.

Implemented, pushed, and deployed to production:

- React sidebar now includes `메일`.
- React `/mailbox/` provides inbox/sent/starred/archived/trash tabs, search, sync, compose, customer selection, and mailbox actions.
- React `/mailbox/thread/<thread_id>/` provides thread detail, customer links, reply, star, and trash actions.
- Django now exposes `/reporting/api/mailbox/*` JSON APIs for list, thread, send, reply, sync, toggle star, archive, move to trash, restore, and delete.
- Existing Django Gmail/IMAP connection, send helper, `EmailLog` model, and `/reporting/mailbox/*` fallback screens remain available.
- DB 변경 없음.

Validation:

```powershell
python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.GmailMailboxThreadRegressionTests --verbosity=2
python -m py_compile reporting\gmail_views.py reporting\urls.py
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend; npm run build
cd frontend; node --check server.mjs
git diff --check
```

Results:

- 5 mailbox tests OK.
- Django check OK.
- No migration changes.
- React build OK, bundle `index-BtG-R--E.js` / `index-B6vJbiFg.css`.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment status:

- Runtime commit: `1501588 feat: add React mailbox`.
- Railway `web`: `b97fc890-33ef-400c-a67a-3f15a468f082` SUCCESS.
- Railway `sales-note-frontend`: `092cbf4d-4072-47e7-966c-7bef7372f479` SUCCESS.
- Production `/mailbox/` serves `index-BtG-R--E.js` / `index-B6vJbiFg.css`.
- Production anonymous `/reporting/api/mailbox/` redirects to login on both frontend proxy and backend.
- Production JS/CSS contain the new mailbox route, API path, and mailbox styles.
- Local preview server started at `http://localhost:4173`.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/mailbox/`.
2. Verify mailbox tabs, search, sync, and a customer thread.
3. Open `/mailbox/thread/<thread_id>/`, verify message body and customer links.
4. Test star/archive/trash and a reply from the React screen.
5. Confirm Django fallback `/reporting/mailbox/inbox/` still works until React redirect cleanup is approved.

## Previous Deployed Task

Urgent React dashboard logout button.

Implemented, pushed, and deployed to production:

- React 공통 `TopBar`에 `로그아웃` 버튼 추가.
- 버튼은 `/reporting/logout/`에 CSRF 포함 `POST` 요청을 보내고 `/reporting/login/`으로 이동.
- `/dashboard/` 포함 React CRM 전 화면에서 접근 가능.
- Django `/reporting/logout/`와 기존 인증/CSRF 정책 유지.
- DB 변경 없음.

Validation:

```powershell
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py check
git diff --check
```

Results:

- React build OK, bundle `index-cLy6Pc7s.js` / `index-D1AABLev.css`.
- `node --check server.mjs` OK.
- Django check OK.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment status:

- Runtime commit: `28a08db fix: add React logout button`.
- Railway `sales-note-frontend`: `58a3e89a-fbad-4bca-bf21-172229b095af` SUCCESS.
- Production `/dashboard/` serves `index-cLy6Pc7s.js` / `index-D1AABLev.css`.
- Production JS contains `로그아웃`, `/reporting/logout/`, `X-CSRFToken`, and `/reporting/login/`.
- Production CSS contains `logout-button`.
- Anonymous dashboard API smoke returns `401 login_required`.
- Manual production logout click test completed by the user on 2026-05-10.

## Earlier Deployed Task

React 고객 상세 선결제 요약 통합.

Implemented, pushed, and deployed to production:

- `/reporting/api/customers/<customer_id>/`에 `prepaymentSummary` 추가.
- 고객 상세와 같은 `scope_users` 범위로 해당 고객의 선결제만 집계.
- React `/customers/<id>/` 우측 패널에 총액/잔액/사용액/건수, 상태별 건수, 최근 선결제 5건 표시.
- React 고객별 선결제 전체 화면과 선결제 목록 링크 유지.
- DB 변경 없음.

Local validation:

```powershell
python -m py_compile reporting\views.py reporting\tests.py
cd frontend; node --check server.mjs
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
python manage.py test reporting.tests.PrepaymentCustomerApiTests reporting.tests.PrepaymentDetailApiTests --verbosity=1
cd frontend; npm run build
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 30 targeted tests OK.
- React build OK, bundle `index-VVc8nVTe.js` / `index-COYknf0t.css`.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment status:

- Runtime commit: `1b88b4f feat: add customer prepayment summary`.
- Deployment/reporting commit: `f7794db docs: record customer prepayment summary deployment block`.
- Railway `web`: `3e66177e-2ddb-4dd7-be56-6bfb6870ac18` SUCCESS.
- Railway `sales-note-frontend`: `eacfa822-cbd0-42ef-a2ff-418a7079329d` SUCCESS.
- Production frontend `/customers/1/` serves `index-VVc8nVTe.js` / `index-COYknf0t.css`.
- Production JS contains `prepaymentSummary`, `/prepayments/customer/`, and `선결제 요약`.
- Production CSS contains `customer-prepayment-card`, `customer-prepayment-metrics`, and `customer-prepayment-actions`.
- Anonymous frontend-proxy and backend API smoke returns `401 login_required` for `/reporting/api/customers/1/`.
- Manual production test is now pending from the user. Do not start the next feature task until the user confirms the server-side test or explicitly asks to proceed.

## Earlier Deployed Task

React 고객별/부서별 선결제 화면 전환.

Implemented:

- React `/prepayments/customer/<customer_id>/` 고객별/부서별 선결제 화면.
- `/reporting/api/prepayments/customer/<customer_id>/` 고객별/부서별 선결제 API.
- 선결제 item payload에 React 고객별 링크 `customerPrepaymentHref` 추가.
- 선결제 목록/상세의 `고객별` 링크를 React 경로로 전환.
- 기존 `/reporting/prepayment/customer/<customer_id>/` Django 고객별 화면 유지.
- 기존 `/reporting/prepayment/customer/<customer_id>/excel/` 엑셀 다운로드 유지.
- Django 기존 의미대로, 기준 고객에게 부서가 있으면 같은 부서 전체 고객의 선결제를 표시.
- Salesman 접근은 고객 담당자 또는 해당 고객에 본인이 등록한 선결제가 있는 경우만 허용.
- Manager/Admin 선택 사용자 세션 필터 유지, React 조회 사용자 선택 추가.

Validation:

```powershell
python manage.py test reporting.tests.PrepaymentCustomerApiTests --verbosity=1
python -m py_compile reporting\views.py reporting\tests.py
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 14 targeted tests OK.
- React build OK, bundle `index-C1Keut7B.js` / `index-BwpNmJt5.css`.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment status:

- Commit: `e918e7f feat: add React customer prepayments`
- `web`: `cad3948b-a777-4cc6-9984-992e34213ffd` SUCCESS
- `sales-note-frontend`: `8103ea72-d9a0-49bc-88ad-466a72a4e996` SUCCESS
- Production `/prepayments/customer/1/` serves bundle `index-C1Keut7B.js` / `index-BwpNmJt5.css`.
- Production JS contains `/prepayments/customer/`, `/reporting/api/prepayments/customer/`, and `고객별 선결제`.
- Production CSS contains `prepayment-customer-layout` and `prepayment-customer-table`.
- Anonymous `/reporting/api/prepayments/customer/1/` returns `401 login_required` on both frontend proxy and backend.
- Anonymous Django customer prepayment page/excel redirects to login.

Manual test status:

- Completed by user on 2026-05-10.

## Operating Rule From User

For each meaningful task:

1. Implement the scoped change.
2. Run local checks.
3. Commit and push.
4. Confirm Railway deployment for affected service(s).
5. Run production smoke checks.
6. Give the user a concrete manual server test process.
7. Continue with the next React integration work after the user confirms the test result.

The user has confirmed Railway access is available in this workspace.

## Production Services

- React frontend: `https://sales-note-frontend-production.up.railway.app`
- Django web/backend: `https://web-production-5096.up.railway.app`
- Railway project: `Sales-note`
- Railway environment: `production`
- Current Railway status at handoff:
  - `web`: Online
  - `sales-note-frontend`: Online
  - `Postgres`: Online

## Important Transition Decision

Until React integration is complete, keep Django pages open and usable.

The latest user clarification:

- Django pages must remain available for now.
- Django schedule calendar is a key operational page and must be easily accessible.
- React pages should have links back to Django pages while feature parity is incomplete.
- Only block/remove Django pages after the React replacement is complete and manually verified.

## Most Recent Confirmed Task

User confirmed manual test completion after the Django schedule calendar restoration.

Implemented behavior:

- Django sidebar `일정 캘린더` opens `/reporting/schedules/calendar/`.
- Django top quick action includes `일정 캘린더`.
- Django schedule list `/reporting/schedules/` includes `캘린더 보기` and `새 일정`.
- Existing schedule list and create/edit/detail behavior remains available.

Commits:

- `c0dc305 fix: restore Django schedule calendar entry`
- `3031ffd docs: record schedule calendar deployment`

Deployments:

- Functional deploy: `49085d5c-cd11-4dca-b9a3-35011ad7626d`
- Final online deploy after docs: `5fccc340-aa32-4a3c-b347-2e2ef73a4b6f`

Validation:

```powershell
python manage.py test reporting.tests.AuthenticationSmoke.test_schedule_calendar_authenticated reporting.tests.DashboardSmokeTests.test_django_sidebar_schedule_points_to_calendar reporting.tests.AnonymousAccessTests.test_schedule_calendar_blocked --verbosity=2
python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests reporting.tests.AnonymousAccessTests --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 3 targeted tests OK.
- 33 smoke/auth tests OK.
- Django check OK.
- No migration changes.
- Production anonymous calendar access redirects to login.

## Recent Emergency Fixes Already Completed

### Weekly report schedule import amounts

Problem:

- Weekly report create page loaded quote/delivery schedules without amounts.

Main changes:

- `reporting/views.py`
- `reporting/templates/reporting/weekly_report/form.html`
- tests in `reporting/tests.py`

Commit:

- `d006234 fix: include weekly report quote delivery amounts`

Deployment:

- `web`: `77680da9-7b6a-4619-ada2-c289527534af`

### Weekly report double-escaped rich text HTML

Problem:

- Weekly report fields were saved as escaped nested HTML like `<p>&lt;p&gt;...`.

Main changes:

- `reporting/utils_html.py`
- weekly report form normalization JS
- tests in `reporting/tests.py`

Commits:

- `aa73921 fix: normalize weekly report rich text html`
- `880bf1e docs: record weekly report urgent fixes`

Deployments:

- `web`: `56b8c632-14aa-4989-aeca-f422e06e7a43`
- final docs deployment: `3e09d3f7-5068-4544-84f2-f413b09ceded`

User result:

- User manually tested and said the result was good.

### Customer AI analysis quote/delivery context

Problem:

- React customer detail `/customers/454/` could run AI analysis, but GPT did not know about existing quote/delivery records when those records were stored as schedules and delivery items.

Main changes:

- `ai_chat/services.py`
- `ai_chat/tests.py`
- `reporting/templates/reporting/base.html`
- `AGENT_PLAN.md`
- `AGENT_REPORT.md`

Implemented behavior:

- AI quote/delivery context now includes:
  - `Quote` + `QuoteItem`
  - quote schedules: `Schedule(activity_type='quote')` + `DeliveryItem(schedule=...)`
  - quote histories: `History(action_type='quote')`
  - delivery histories: `History(action_type='delivery_schedule')`
  - delivery schedules: `Schedule(activity_type='delivery')` + `DeliveryItem(schedule=...)`
- Avoids double-counting delivery schedules already represented by linked histories.
- `gather_followup_data()` uses the same quote/delivery collection path for individual customer analysis.
- Prompt includes source labels, item names, amounts, and notes.

Commits:

- `dbf4f33 fix: include quote delivery data in AI analysis`
- `6fce7a8 docs: record AI quote delivery deployment`

Deployments:

- functional deploy: `1dcdd01e-1495-4f9f-80d6-c430da5bd876`
- final docs deploy: `101b9590-5b8b-4624-96d4-6efba599dd82`

Important limitation:

- Existing saved AI analysis results do not auto-refresh.
- The user must run AI analysis again from `/customers/<id>/` to generate a new result with quote/delivery context.

## AI Verification Memory Work Already Completed

Recent commits before the latest emergency tasks:

- `8c870ee feat: remember AI painpoint verification`
- `59e8ba4 docs: record AI verification memory deployment`
- `47679b7 feat: apply AI verification memory to insights`
- `b0c485b docs: record AI verification insights deployment`

Purpose:

- PainPoint verification notes are now remembered and used in GPT context.
- Verification memory should influence:
  - new AI analysis
  - summaries
  - next-action insights
  - repeated verification questions

Important follow-up:

- When continuing AI React migration, keep the verification memory visible and actionable in the React result/verification flow.

## Current Navigation Policy

Django common sidebar should point to Django pages during transition:

- Dashboard: `/reporting/dashboard/`
- Customers: `/reporting/followups/`
- AI: `/ai/`
- Schedule calendar: `/reporting/schedules/calendar/`
- Notes: `/reporting/histories/`
- Pipeline: `/reporting/funnel/pipeline/`

React remains accessible through top quick links such as `프론트 CRM`.

React pages should continue to expose Django fallback/original links until feature parity is done.

## Recommended Next Work

Current latest work:

- React customer/department searchable selection UX is implemented, pushed, and deployed.
- Runtime commit: `344f4a3 feat: add searchable CRM selectors`.
- Railway `sales-note-frontend`: `a373859f-06f2-407f-9321-f1baead50ef6` SUCCESS.
- Railway `web`: `44f73bb0-d3be-4346-bd3c-b2331e0912a9` SUCCESS from the same push.
- Deployed bundle: `assets/index-DGco8KN_.js` / `assets/index-B9odz52n.css`.
- Changed files: `frontend/src/App.tsx`, `frontend/src/styles.css`, `AGENT_PLAN.md`, `AGENT_REPORT.md`, `HANDOFF.md`.
- Local validation passed: `npm run build`, `node --check server.mjs`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `git diff --check`.
- Production smoke passed: frontend bundle contains `searchable-select`, protected customer API returns 401 anonymous, backend login page returns 200.

After the React prepayment detail/create/edit flow is deployed and manually verified, continue React unified frontend migration. Natural next slices are:

1. Move 선결제 삭제/취소/이관 into React while preserving Django `/reporting/prepayment/*`.
2. Move 견적/문서 생성 workflows into React.
3. Continue AI React migration only after confirming the latest customer AI manual tests remain good.

Alternative high-value slice:

- React schedule calendar parity audit and fallback links, because Django schedule calendar is heavily used. Do not remove Django calendar until React can cover the real operational workflow.

## Files To Read Before Continuing

Required project guidance:

1. `.github/copilot-instructions.md`
2. `PROJECT_BRIEF.md`
3. `SALES_CRM_SPEC.md`
4. `QA_CHECKLIST.md`
5. `AGENT_PLAN.md`
6. `AGENT_REPORT.md`

Likely implementation files:

- `ai_chat/services.py`
- `ai_chat/views.py`
- `ai_chat/urls.py`
- `ai_chat/tests.py`
- `reporting/views.py`
- `reporting/urls.py`
- `reporting/tests.py`
- `reporting/templates/reporting/base.html`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/styles.css`
- `frontend/README.md`
- `reporting/templates/reporting/prepayment/list.html`
- `reporting/templates/reporting/prepayment/detail.html`

## Validation Baseline

Use targeted tests first, then broader checks depending on scope.

Common commands:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test ai_chat.tests --verbosity=1
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests reporting.tests.AnonymousAccessTests --verbosity=1
```

For React frontend changes:

```powershell
Set-Location frontend
npm run build
node --check server.mjs
```

## Production Smoke Checklist

Anonymous protection:

```powershell
curl.exe -I -s https://web-production-5096.up.railway.app/reporting/schedules/calendar/
curl.exe -I -s https://web-production-5096.up.railway.app/reporting/login/
curl.exe -i -s https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
```

Expected:

- protected Django template pages redirect to `/reporting/login/`
- protected API routes return login-required behavior
- login page returns 200

Railway:

```powershell
railway status
railway deployment list --service web --environment production --limit 5 --json
railway deployment list --service sales-note-frontend --environment production --limit 5 --json
```

## Deployment Notes

- Backend/Django changes usually deploy through Railway service `web`.
- React bundle/server changes deploy through Railway service `sales-note-frontend`.
- Docs-only commits can still trigger Railway deploys. If pushed, wait for the final deployment to become `SUCCESS`.
- The latest runtime commit documented at handoff is:

```text
b8e65e9 feat: show department AI in pipeline panel
```

## Known Caveats

- Local PowerShell profile emits noisy `Set-PSReadLineOption` warnings in command output. These have not indicated task failure.
- Local environment may warn that `EMAIL_ENCRYPTION_KEY` is unset. This is expected locally unless testing IMAP/SMTP encryption paths.
- Some old README content still mentions older Node/Express planning text. Treat `.github/copilot-instructions.md`, `PROJECT_BRIEF.md`, and `SALES_CRM_SPEC.md` as higher priority.
- Do not expose CRM data publicly.
- Do not weaken authentication, CSRF, session, or AI permission checks.
- Do not remove Django templates yet.

## User Manual Test Status

Confirmed by user:

- React dashboard logout button: confirmed complete.
- Weekly report urgent fixes: good.
- Django schedule calendar restoration: confirmed complete.

Needs awareness:

- React pipeline department AI panel is deployed and can be manually tested.
- React customer detail prepayment summary is deployed and awaits user manual production testing.
- AI quote/delivery context fix is deployed, but existing stored AI results require rerun. If validating customer `454`, click AI analysis again and inspect the new output.
