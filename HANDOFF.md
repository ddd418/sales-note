# Sales Note Handoff

Last updated: 2026-05-15 KST

Workspace: `D:\projects\sales-note`

## Immediate State

- Branch: `main`
- Last pushed commit: `b07f888 docs: record pipeline revenue deployment`
- Runtime commit for latest functional change: `f011bc9 fix: use dated revenue for pipeline cards`
- Worktree was clean before this handoff update.
- Current production frontend: `https://sales-note-frontend-production.up.railway.app/`
- Latest frontend bundle confirmed in production: `assets/index-Cw_brbov.js`

## Non-Negotiable Project Rules

- This is an internal Django + React CRM, not a public website.
- Preserve the existing `reporting` app and `/reporting/*` routes.
- React is the target CRM frontend; Django remains backend/auth/permissions/API/business logic.
- Do not weaken authentication or expose internal sales data publicly.
- Do not remove Django templates/routes until React parity, deployment, and manual production testing are complete.
- For major runtime work: update `AGENT_PLAN.md`, implement, test, update `AGENT_REPORT.md`, commit, push, deploy affected Railway services, then provide manual production test steps.
- If runtime behavior changes, deploy Railway. If docs-only, no Railway deploy is needed.

## Latest Completed Task

### Dashboard revenue metrics and pipeline date-based amounts

Goal:

- Show current user's current-year total revenue and current-quarter revenue on the React dashboard.
- Fix `/` pipeline card/stage amounts so they do not sum all historical customer revenue across dates.

Implemented:

- `reporting/views.py`
  - `dashboard_summary_api` now returns:
    - `metrics.yearRevenue`
    - `metrics.quarterRevenue`
    - `metrics.monthlyRevenue`
    - `revenuePeriod`
  - Revenue basis matches the existing dashboard monthly revenue logic: delivery schedules and `DeliveryItem.total_price`.
- `reporting/funnel_views.py`
  - Pipeline amount selection now uses the latest basis date only.
  - Same-date multiple quotes/deliveries are still summed.
  - Different-date older quotes/deliveries are excluded from the card amount.
  - Pipeline payload now includes `latestQuote.basisDate`.
- `frontend/src/App.tsx`
  - Dashboard cards added:
    - `당해년도 전체 매출`
    - `현재 분기 매출`
    - `이번 달 매출`
  - Pipeline detail panel shows `기준일`.
- `frontend/src/api.ts`, `frontend/src/mockData.ts`
  - Types and fallback normalization updated.
- `reporting/tests.py`
  - Dashboard period revenue regression test added.
  - Pipeline latest-date quote/delivery amount tests added.

Validation passed:

```text
python -m py_compile reporting\views.py reporting\funnel_views.py reporting\tests.py
python manage.py test reporting.tests.PipelineApiTests --verbosity=1
python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend; npx tsc --noEmit --pretty false
cd frontend; npm run build
cd frontend; node --check server.mjs
git diff --check
```

Results:

- Pipeline API tests: 13 tests OK.
- Dashboard API tests: 6 tests OK.
- Django check OK with expected `EMAIL_ENCRYPTION_KEY` warning only.
- Migration dry-run: no changes detected.
- Frontend build OK: `assets/index-Cw_brbov.js` / `assets/index-GdZLLCy-.css`.
- `git diff --check` OK with CRLF normalization warnings only.

Deployment:

- GitHub runtime commit pushed: `f011bc9`
- GitHub docs/report commit pushed: `b07f888`
- Railway `web`:
  - Runtime deploy: `bc76b797-eb67-407b-987b-77c81c0d9f8b` SUCCESS
  - Latest docs auto-deploy: `26b02d2a-5b4b-468e-bb54-3df0c2695eda` SUCCESS
- Railway `sales-note-frontend`:
  - `90d787cc-e7dd-4c03-8366-4d1c4571c9d2` SUCCESS

Production smoke passed:

```text
GET /
-> 200, assets/index-Cw_brbov.js

GET /dashboard/
-> 200, assets/index-Cw_brbov.js

GET /assets/index-Cw_brbov.js
-> contains "당해년도 전체 매출", "현재 분기 매출", "basisDate", "기준일"

GET /reporting/api/pipeline/ anonymous
-> 302 /reporting/login/?next=/reporting/api/pipeline/

GET /reporting/api/dashboard/ anonymous
-> 401 login_required JSON

GET /reporting/login/
-> 200
```

Manual production test still needed from user:

1. Open `/dashboard/`.
2. Confirm `당해년도 전체 매출`, `현재 분기 매출`, and `이번 달 매출` cards display.
3. Open `/`.
4. Pick a customer with quote/delivery data across multiple dates.
5. Confirm the card amount is the latest basis date amount, not a sum of all historical dates.
6. Confirm the right detail panel shows `기준일`.

## Recently Resolved Urgent Work

These are already implemented, tested, deployed, and recorded in `AGENT_REPORT.md`.

- `/schedules/903/` delivery items save with prepayment deduction.
- Prepayment deduction UI in delivery-item editor:
  - multiple prepayments
  - item cap
  - available balance
  - manual amount validation
  - `전체 차감`
- Quote-item import API 502 mitigation by bulk-loading quote progress.
- Quote-item import supports multiple quote selections.
- Legacy quote items with missing `unit_price` recover price from `total_price`.
- Empty discount unit price no longer becomes 0 KRW.
- Delivery item save error after prepayment work was fixed.
- AI Workspace `action_not_found` fallback was extended for department-detail actions.
- AI Workspace right-side duplicate action panel was removed.

## Still Pending / User-Requested Backlog

Do not start these until the latest dashboard/pipeline production manual test is confirmed, unless the user explicitly says to proceed.

1. AI Workspace global question entry
   - URL: `/ai-workspace/`
   - User wants to ask questions across all CRM features/data.
   - Request wording: "CRM기능 전부 검색해서 질문에 답변하는 AI".
   - Need inspect existing AI Workspace APIs and prompt context before implementing.

2. AI Workspace department target search by PI name
   - URL: `/ai-workspace/`
   - User wants `부서 분석 대상` search to find departments when only PI name is entered.
   - There is a related customer/department autocomplete test in `reporting.tests.CustomersSummaryApiTests`, but this may not cover AI Workspace target search.

3. AI Workspace field answers should influence Prompt goals / 추천 목표
   - User said answers left in `AI 추천 실행 목록` / `현장 답변` must be reflected by AI in Prompt goals.
   - Need inspect `AIWorkspaceActionFeedback`, prompt goal generation, and AI workspace summary APIs.

4. Mailbox bulk automation
   - URL: `/mailbox/`
   - User wants to paste email rows from Excel and send one-by-one.
   - Template variables like `{name}`, `{position}` should be substituted per recipient.
   - Must be very careful with send confirmation and anti-accidental-send UX.

## High-Value Code Locations

- `reporting/views.py`
  - `dashboard_summary_api`
  - schedule detail/update/delivery item APIs
  - mailbox APIs
  - AI Workspace APIs around the AI workspace sections
- `reporting/funnel_views.py`
  - `pipeline_command_center_api`
  - `_select_pipeline_pricing`
  - `_select_quote_reference_pricing`
  - `_actual_delivery_revenue`
- `reporting/tests.py`
  - `DashboardSummaryApiTests`
  - `PipelineApiTests`
  - `QuoteItemsApiTests`
  - schedule/prepayment tests
  - AI Workspace tests
- `frontend/src/App.tsx`
  - dashboard page
  - pipeline page/detail panel
  - schedule detail / delivery item editor
  - AI Workspace UI
  - mailbox UI
- `frontend/src/api.ts`
  - API types, loaders, mutation calls, fallback normalization
- `frontend/src/mockData.ts`
  - shared pipeline types
- `ai_chat/`
  - department analysis and prompt logic

## Standard Validation Commands

Backend:

```text
python -m py_compile reporting\views.py reporting\funnel_views.py reporting\tests.py
python manage.py test reporting.tests.<TargetTestClass> --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Frontend:

```text
cd frontend
npx tsc --noEmit --pretty false
npm run build
node --check server.mjs
```

Expected harmless warning:

```text
EMAIL_ENCRYPTION_KEY 환경변수가 설정되지 않았습니다. IMAP/SMTP 비밀번호 암호화가 비활성화됩니다.
```

## Deployment Notes

Backend usually auto-deploys to Railway `web` when `main` is pushed.

Check backend:

```text
railway deployment list --service web --limit 3 --json
```

Frontend requires manual deploy when `frontend/` changes:

```text
railway up .\frontend --path-as-root --service sales-note-frontend --detach --message "<message>"
railway deployment list --service sales-note-frontend --limit 3 --json
```

Production smoke examples:

```text
Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/ -UseBasicParsing
Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/dashboard/ -UseBasicParsing
Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/login/ -UseBasicParsing
Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/dashboard/ -UseBasicParsing -SkipHttpErrorCheck
```

## Suggested Next Worker Start

1. Run `git status --short --branch`.
2. Read current `AGENT_PLAN.md`, `AGENT_REPORT.md`, and this `HANDOFF.md`.
3. Ask whether the latest dashboard/pipeline production manual test passed if the user has not already confirmed.
4. If user explicitly proceeds, start with AI Workspace PI-name search or global CRM question, whichever the user prioritizes.
5. Keep changes scoped and deploy only affected services.
