# Sales Note Handoff

Last updated: 2026-05-10 KST

## Current Goal

The long-term goal is to unify the CRM frontend into React while keeping Django as the backend/API layer.

- React should become the only user-facing CRM frontend after feature parity.
- Django should remain responsible for login, permissions, models, business logic, files, and JSON APIs.
- Django template pages must remain usable during the transition.
- Do not copy the old Django visual design into React. Build a distinct internal CRM interface.
- Remove Django frontend templates only after React feature parity, Railway deployment, and manual production testing are complete.

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

Continue React unified frontend migration. The most natural next slice is:

1. Move the AI analysis result screen and PainPoint verification flow into React.
2. Preserve Django AI pages as fallback during the transition.
3. Ensure React result/verification UI uses:
   - quote/delivery context
   - verification memory
   - PainPoint verification notes
   - next-action insights
4. Add or extend Django JSON APIs instead of scraping templates.
5. Keep permissions identical to existing Django AI policy:
   - login required
   - AI permission required
   - own assigned department/customer constraints preserved

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
- The latest pushed commit at handoff is:

```text
3031ffd docs: record schedule calendar deployment
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

- Weekly report urgent fixes: good.
- Django schedule calendar restoration: confirmed complete.

Needs awareness:

- AI quote/delivery context fix is deployed, but existing stored AI results require rerun. If validating customer `454`, click AI analysis again and inspect the new output.

