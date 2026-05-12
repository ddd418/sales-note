# Sales Note Handoff

Last updated: 2026-05-12 KST

## Current Goal

The long-term goal is to unify the CRM frontend into React while keeping Django as the backend/API layer.

- React should become the only user-facing CRM frontend after feature parity.
- Django should remain responsible for login, permissions, models, business logic, files, and JSON APIs.
- Django template pages must remain usable during the transition.
- Do not copy the old Django visual design into React. Build a distinct internal CRM interface.
- Remove Django frontend templates only after React feature parity, Railway deployment, and manual production testing are complete.

## Current Task

React delivery quote import, schedule delete, product list layout fix, and product replacement delete are implemented, locally verified, pushed, deployed to production, and smoke-tested. User manual production testing is pending.

Runtime commit:

```text
f1d7b42 feat: import quote items into deliveries
```

Current implementation:

- React delivery schedule details now have a `견적 불러오기` flow that pulls quote items from the same follow-up/customer context into editable delivery item rows.
- Quote item API now returns React-friendly quote/item data including product linkage, unit, base price, discount rate/unit price, tax invoice flag, quote group, and item notes.
- React schedule detail now exposes a schedule delete button that calls the existing Django AJAX delete view and then redirects to the schedule list.
- React `/products/` table layout was adjusted so the list and side panels do not break at production viewport widths.
- Product bulk delete now supports replacement mapping for blocked products. `DeliveryItem` and legacy `QuoteItem` references move to the replacement product, integrity is checked, then the original product is deleted.
- No database model changes or migrations.

Validation:

```text
python -m py_compile reporting\views.py reporting\tests.py
python manage.py test reporting.tests.QuoteItemsApiTests reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_returns_detail_and_edit_config reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_manager_read_only_and_other_company_blocked reporting.tests.SchedulesSummaryApiTests.test_schedule_delete_ajax_allows_owner_and_removes_related_history reporting.tests.SchedulesSummaryApiTests.test_schedule_delete_ajax_blocks_non_owner reporting.tests.ProductManagementReactApiTests --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend; npm run build
cd frontend; node --check server.mjs
git diff --check
```

Results:

- Targeted schedule/quote/product regression tests OK: 12 tests.
- Django check OK with `EMAIL_ENCRYPTION_KEY` warning only.
- Migration dry-run OK: no changes detected.
- React build OK: `assets/index-2OWdxLkM.js` / `assets/index-2AirpMI9.css`.
- Node syntax check OK.
- Local Playwright smoke OK with mocked APIs: `/products/` renders table and blocked replacement delete panel; `/schedules/882/` renders delete and quote import controls.
- `git diff --check` OK.

Deployment:

- GitHub push complete: runtime commit `f1d7b42` is on `main`.
- Railway `web`: `2241be62-11b5-472d-92b6-4f469179f61c` SUCCESS.
- Railway `sales-note-frontend`: `cba176c5-cebc-4ba7-8989-e298b0cbfb1c` SUCCESS.
- Production smoke OK:
  - `/products/` 200 with latest frontend assets `index-2OWdxLkM.js` / `index-2AirpMI9.css`.
  - `/schedules/882/` 200.
  - `/reporting/login/` 200.
  - Anonymous `/reporting/api/products/manage/` redirects to login.
  - Anonymous `/reporting/api/schedules/882/` returns 401 login-required JSON.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/schedules/882/`.
2. In the delivery item section, click `견적 불러오기`, choose a quote, and confirm rows import with unit, price, discount, quote group, and notes.
3. Save the imported delivery rows and confirm they remain after refresh.
4. Confirm the schedule detail `삭제` button appears. Test actual deletion only with a disposable schedule.
5. Open `https://sales-note-frontend-production.up.railway.app/products/` and confirm the product table is not visually broken.
6. Bulk delete an unused test product and confirm normal deletion.
7. Bulk delete a used test product, confirm it is blocked, choose a replacement product, run replacement delete, and confirm the original product is removed while quote/delivery rows point to the replacement.

Manual test result:

- Pending user confirmation.

Next queued after this task is manually verified:

- Confirm whether quote import is also needed in any separate delivery creation flow beyond the React schedule detail editor.
- Continue the remaining queued CRM work only after the user confirms production manual testing.

## Previous Task

Product management React migration is implemented, locally verified, pushed, deployed to production, smoke-tested, and user manual production testing was later followed by the delivery/product follow-up work above.

Runtime commit:

```text
126fd3b feat: migrate product management to react
```

Deployment:

- Railway `web`: `c36d7e71-7379-45f2-9dca-3d7af93525de` SUCCESS.
- Railway `sales-note-frontend`: `3bb14e78-8f7d-4d58-8e76-125bf65d8418` SUCCESS.
- Production smoke OK: `/products/` 200, `/reporting/login/` 200, protected product APIs require login.

## Previous Task

React mail rich editor link text hotfix is implemented, frontend-build verified, pushed, deployed to production, smoke-tested, and user manual production testing is complete.

Runtime commit:

```text
9fc5522 fix: insert mail links with custom text
```

Deployment:

- Railway `sales-note-frontend`: `e5f407b8-d513-4dcc-82ca-736e9964cf7f` SUCCESS.
- Railway `web`: `36758e7b-1f37-4d91-a3a1-2585d5a5eb33` SUCCESS (docs commit automatic deploy).
- Production smoke OK: backend `/reporting/login/` 200, frontend `/mailbox/` 200.

Manual test result:

- Complete: user confirmed production manual test completion on 2026-05-12 KST.

## Previous Task

React rich mail editor and AI Workspace detail prompt scoping are implemented, locally verified, pushed, deployed to production, and smoke-tested. User manual production testing was pending when the link-text hotfix was requested.

Runtime commit:

```text
eb7e0fc feat: add rich mail editor and scope ai prompts
```

Deployment:

- Railway `web`: `fc0b97e2-b144-4133-8171-2ca1be4375cd` SUCCESS, later superseded by docs/runtime automatic deployments.
- Railway `sales-note-frontend`: `1053e2a3-603d-472c-8aea-159f0a5cf130` SUCCESS, later superseded by `e5f407b8-d513-4dcc-82ca-736e9964cf7f`.

Next queued after product management is manually verified:

- Continue queued CRM tasks only after the user confirms product management production testing.

## Previous Task

Quote document grouping, generated document registration, automatic quote mail attachment, and registered document deletion are implemented, locally verified, pushed, deployed to production, smoke-tested, and user manual production testing was requested before this hotfix.

Runtime commit:

```text
0384e13 feat: split schedule quote documents by group
```

Quote PDF A4 auto-fit hotfix is implemented, locally verified, pushed, deployed to production, smoke-tested, and user manual PDF output testing is complete.

Runtime commit:

```text
0c70596 fix: fit document pdf exports to a4
```

Implemented:

- Generated XLSX files are patched before PDF conversion so each worksheet uses A4 paper size.
- Worksheet print settings now use fit-to-page with one-page width and unlimited page height.
- Margins are reduced to keep quotation templates inside the printable A4 area.
- Existing variable replacement, media restoration, XLSX downloads, and PDF fallback behavior are preserved.
- No DB model or migration changes.
- No frontend deployment is needed.

Validation:

```text
python -m py_compile reporting\views.py reporting\tests.py
python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 10 document template tests OK.
- Python compile OK.
- Django check OK with `EMAIL_ENCRYPTION_KEY` warning only.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- GitHub push complete: runtime commit `0c70596` is on `main`; deployment report docs may create a newer web deployment because GitHub autodeploy is enabled.
- Railway `web`: `1cfaeab1-26ef-428e-89b5-67a1a98dfd11` SUCCESS.
- `sales-note-frontend` deployment not needed because frontend files did not change.
- Production `/reporting/login/` returns 200.
- Production `/documents/` returns 200 through the React frontend.
- Anonymous frontend-proxied and direct backend `/reporting/api/documents/` return `401 Unauthorized`.

Manual production test:

1. Open a quote schedule in production.
2. Download the quotation PDF.
3. Confirm the PDF fits A4 width without right-side or bottom clipping.
4. For a quote with many items, confirm the PDF continues to the next page vertically instead of shrinking unreadably or clipping.

Manual test result:

- Complete: user confirmed production manual test completion on 2026-05-12 KST.

## Previous Task

Quote discount unit price, item note, quote extra notes, React document variable copy, and AI recommended-goal customer/priority updates are implemented, locally verified, pushed, deployed to production, smoke-tested, and user manual production testing is complete.

Runtime commit:

```text
b09acf7 feat: expand quote discounts and ai goals
```

Implemented:

- `DeliveryItem.discount_rate` and `DeliveryItem.discount_unit_price` were added.
- `Schedule.quote_extra_notes` was added for whole-quote extra notes.
- Quote/delivery item totals and document variables use final effective unit price: discount unit price first, then discount rate, then base unit price.
- React schedule detail edit UI supports base unit price, discount rate, discount unit price, item note, and quote extra notes.
- Document variables now include `기타사항`, `견적기타사항`, `품목N_적요`, `품목N_기준단가`, `품목N_할인율`, `품목N_할인단가`.
- React `/documents/` template registration shows grouped usable variables and copies tokens to the clipboard.
- AI Workspace recommended goals include an explicit customer name and priority label.
- Department AI analysis updates each department customer's CRM priority from AI recommendations, with customer-stage fallback.
- Individual customer AI analysis updates that customer's CRM priority from AI recommendation or risk/probability fallback.
- New DB migration: `reporting/migrations/0095_deliveryitem_discount_rate_and_more.py`.

Validation:

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.AIWorkspaceSummaryApiTests ai_chat.tests.AIDepartmentPromptLogicTests ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
python -m py_compile ai_chat\services.py ai_chat\views.py ai_chat\department_prompt.py reporting\views.py reporting\tests.py ai_chat\tests.py
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 50 quote/document/AI workspace/AI priority tests OK.
- Python compile OK.
- React build OK: `assets/index-DJaKKt6c.js` / `assets/index-DHLL1LUc.css`.
- Node syntax check OK.
- Django check OK with `EMAIL_ENCRYPTION_KEY` warning only.
- `makemigrations --check --dry-run` reports no changes after migration file creation.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- GitHub push complete: runtime commit `b09acf7` is on `main`; deployment report docs may create a newer web deployment because GitHub autodeploy is enabled.
- Railway `web`: `73d90eea-de63-499a-b19d-a7bcc3da409a` SUCCESS.
- Railway `sales-note-frontend`: `4f2dacfe-792e-447c-ad71-d46944452f53` SUCCESS.
- Production `/documents/`, `/schedules/`, `/ai-workspace/` return 200 and serve `assets/index-DJaKKt6c.js` / `assets/index-DHLL1LUc.css`.
- Production JS contains `할인단가`, `templateVariableGroups`, `우선순위 갱신`, `추천 목표`.
- Production CSS contains `document-variable-panel`, `ai-goal-card-meta`, `schedule-quote-extra-notes`.
- Production `/reporting/login/` returns 200.
- Anonymous frontend-proxied and direct backend `/reporting/api/documents/` return `401 Unauthorized`.
- Anonymous frontend-proxied and direct backend `/reporting/api/ai-workspace/` return `401 Unauthorized`.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/schedules/` and go to a quote schedule detail.
2. Edit quote items with base unit price, discount rate, discount unit price, and item note; save and refresh.
3. Confirm final totals use discount unit price when present, or auto-calculated discount unit price when only discount rate is entered.
4. Save whole-quote extra notes and confirm they persist after refresh.
5. Generate or preview quotation document data and confirm the new variables render: `견적기타사항`, `품목1_적요`, `품목1_기준단가`, `품목1_할인율`, `품목1_할인단가`.
6. Open `https://sales-note-frontend-production.up.railway.app/documents/`, open the template registration form, and copy new variables from the variable panel.
7. Open `https://sales-note-frontend-production.up.railway.app/ai-workspace/` and confirm recommended goal cards show a concrete customer name.
8. Run department AI analysis and confirm CRM customer priority is recalculated and displayed after refresh.

Manual test result:

- Complete: user confirmed production manual test completion on 2026-05-12 KST.

## Older Task

React AI summary, pipeline AI controls, recommended questions, and email context expansion are implemented, locally verified, pushed, deployed to production, and smoke-tested. User manual production testing is pending.

Runtime commit:

```text
fcb7eeb feat: expand react ai workflow
```

- Customer detail, AI Workspace, and pipeline AI summaries no longer truncate the top AI summary at 160/180 characters.
- Pipeline `aiDepartment` payload now includes the full customer AI result payload used by customer detail and AI Workspace.
- React pipeline detail panel can run department AI, open the full AI result, and save PainPoint verification notes.
- React AI result panels show a dedicated `추천 질문` list gathered from missing info, verification insights, and PainPoint verification questions.
- Recommended questions can be copied from React.
- AI email context includes customer inbound replies plus at most two user-sent outbound emails.
- Same-thread outbound emails are nested under customer replies so the AI evaluates the reply and sent email as a set.
- No DB model or migration changes.

## Older Task

React mailbox email line break normalization is implemented, locally verified, pushed, deployed to production, and smoke-tested. User manual production testing is pending.

Runtime commit:

```text
329cb0d fix: normalize mailbox email line breaks
```

- `_handle_email_send()` now normalizes `body_text` line endings from `\r\n`/`\r` to `\n` before validation, MIME send, HTML conversion, and EmailLog storage.
- Plain text → HTML conversion now escapes text and uses `<br>` for line breaks without `white-space: pre-wrap`.
- This removes the `\r<br>` + pre-wrap combination that could make one textarea newline render as multiple visual breaks in email clients.
- React mailbox send/reply, Gmail API, IMAP/SMTP, attachments, business card signatures, and EmailLog storage are preserved.
- No DB model or migration changes.

Validation:

```powershell
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1
python -m py_compile reporting\gmail_views.py reporting\tests.py
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 7 React mailbox API tests OK.
- Python compile OK.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- GitHub push complete: `main` updated to `329cb0d`.
- Railway `web`: `af9f5751-3896-445c-bf7e-9c3cba56d154` SUCCESS.
- `sales-note-frontend` deployment not needed because frontend files did not change.
- Production `/mailbox/` returns 200.
- Production `/reporting/login/` returns 200.
- Anonymous frontend-proxied and backend `GET /reporting/api/mailbox/` redirect to `/reporting/login/`.
- Anonymous frontend-proxied and backend `POST /reporting/api/mailbox/send/` are blocked by CSRF with `403 Forbidden`.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/mailbox/`.
2. Compose a test email with a body that has a single Enter line break and one intentional blank line.
3. Send it to yourself or a test recipient.
4. Confirm one Enter does not render as 2-3 blank lines in the received email.
5. Confirm an intentional paragraph blank line remains about one blank line.
6. Repeat from a mailbox thread reply.
7. Confirm attachments/signature still work if selected.

Manual test result:

- Pending user confirmation.

## Previous Task

React schedule calendar report content and nav-first calendar entry.

Implemented, pushed, deployed, and smoke-tested on 2026-05-11. User manual production testing was pending when the mailbox line-break fix was requested:

- `/reporting/api/schedules/calendar/` customer schedule payloads include recent linked report `reports`.
- React `/schedules/calendar/` selected-day cards show `보고 내용` and `보고 상세`.
- React sidebar `일정` opens `/schedules/calendar/` first.
- Runtime commits:
  - `c96f7d5 feat: show schedule reports in calendar`
  - `d455127 feat: open schedule nav on calendar`
- Deployment/report commit:
  - `0cc9345 docs: record schedule calendar reports deployment`
- Railway `web`: `1969669f-d1c8-4bda-8fe6-d1d3d06c15c0` Deploy complete.
- Railway `sales-note-frontend`: `bee0b840-3a45-4cbd-be0f-0cbf9badcfe6` Deploy complete.
- Production `/schedules/calendar/` returns 200 and serves `assets/index-rK47uPvT.js` / `assets/index--s--1gtx.css`.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`.
2. Select a date that has a customer schedule with linked sales notes/reports.
3. Confirm the selected-day card shows `보고 내용`.
4. Confirm report content, meeting situation, confirmed facts, and next action are visible when present.
5. Click `보고 상세` and confirm it opens the React note detail.
6. Click the left sidebar `일정` and confirm it opens `/schedules/calendar/`.
7. Confirm schedules without reports still show the existing schedule memo/status/actions only.

Manual test result:

- Pending user confirmation.

## Previous Task

React schedule calendar selected-day status actions.

Implemented, pushed, deployed, and smoke-tested on 2026-05-11. User manual production testing was pending when the report-content follow-up was requested:

- `/reporting/api/schedules/calendar/` customer schedule payloads include `canEdit`, `statusUpdateHref`, `djangoEditHref`, and `statusOptions`.
- Edit permission is computed per customer schedule using existing owner/manager/admin rules.
- Personal schedule payloads remain read-only and expose no status options.
- React `/schedules/calendar/` selected-day panel uses schedule cards instead of a compact link list.
- Selected-day cards expose `상세`, `고객`, `보고`, `Django 상세`, and `Django 수정` actions when available.
- Editable own customer schedules can be changed directly from the React calendar with the existing Django status update API.
- Calendar data reloads after a status change so the grid, selected-day list, and metrics stay in sync.
- No DB model or migration changes.

Validation:

```powershell
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
python -m py_compile reporting\views.py reporting\tests.py
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 28 React schedule API tests OK.
- React build OK: `assets/index-C1R5m0RT.js` / `assets/index-Bxi4eBNz.css`.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- Railway `web`: `d7eba974-f6db-4e90-a53c-5097ccad0164` Deploy complete.
- Railway `sales-note-frontend`: `898c94ca-cf72-4dba-b329-35304d8c4979` Deploy complete.
- Production `/schedules/calendar/` returns 200 and serves `assets/index-C1R5m0RT.js` / `assets/index-Bxi4eBNz.css`.
- Frontend JS contains `statusUpdateHref` and schedule status update UI strings.
- Frontend CSS contains `schedule-calendar-selected-card` and `schedule-calendar-status-actions`.
- Anonymous frontend-proxied and backend `/reporting/api/schedules/calendar/` return `401 Unauthorized`.

## Previous Task

React document generation history.

Implemented, pushed, deployed, smoke-tested, and user manual production testing completed on 2026-05-11:

- `/reporting/api/documents/` now includes recent `DocumentGenerationLog` entries as `recentGenerations`.
- The API returns document type, transaction number, output format, created date, creator, company, schedule, customer, and department metadata.
- The API keeps the same company scope as the existing document template API.
- React `/documents/` right panel now shows `오늘 생성`, `최근 이력`, and a `최근 생성 이력` list.
- Generation history cards link back to the React schedule detail when the linked schedule still exists.
- Document type filters apply to both templates and generation history.
- No DB model or migration changes.

Validation:

```powershell
python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
python -m py_compile reporting\views.py reporting\tests.py
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 8 React document API tests OK.
- React build OK: `assets/index-Bmhj4oJQ.js` / `assets/index-CsWuSGWH.css`.
- Django check OK.
- No migration changes.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- Railway `web`: `280b8be1-c1c0-48cc-80a1-37707d4c9cba` SUCCESS.
- Railway `sales-note-frontend`: `0da257af-9ca9-48b3-bcd5-bfd1767a9bf6` SUCCESS.
- Production `/documents/` returns 200 and serves `assets/index-Bmhj4oJQ.js` / `assets/index-CsWuSGWH.css`.
- Frontend JS contains `recentGenerations` and `최근 생성 이력`.
- Frontend CSS contains `document-generation-card`.
- Anonymous frontend-proxied and backend `/reporting/api/documents/` return `401 Unauthorized`.

Manual production test:

1. Open `https://sales-note-frontend-production.up.railway.app/documents/`.
2. Confirm the right summary shows `오늘 생성` and `최근 이력`.
3. Confirm `최근 생성 이력` shows transaction number, document type, output format, creator, customer, and department.
4. Click a generation history card and confirm it opens the linked React schedule detail.
5. Change the document type filter and confirm both templates and generation history follow the filter.
6. Generate a schedule document from React schedule detail, then return to `/documents/` and confirm a new history entry appears.

Manual test result:

- Completed by user on 2026-05-11.

## Previous Task

React mailbox send attachments.

Implemented, pushed, deployed, and user manual production testing completed on 2026-05-11:

- React `/mailbox/` compose and `/mailbox/thread/<id>/` reply forms can send multiple attachments.
- Selected file names and sizes are visible before sending, with per-file remove controls.
- Mailbox send/reply API client now posts `FormData` with `attachments`.
- Existing Django Gmail/SMTP attachment handling and `EmailLog.attachments_info` logging are reused.
- DB 변경 없음.

Validation:

```powershell
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1
python -m py_compile reporting\gmail_views.py reporting\tests.py
cd frontend; npm run build
cd frontend; node --check server.mjs
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Results:

- 6 React mailbox API tests OK.
- Django check OK.
- No migration changes.
- React build OK: `assets/index-BVsunKYp.js` / `assets/index-BPeRJO55.css`.
- `git diff --check` OK with LF→CRLF warnings only.

Deployment:

- Railway `sales-note-frontend`: `d55ba8c7-62a7-4237-b26e-9b456f7a7787` SUCCESS.
- Production `/mailbox/` returns 200 and serves `assets/index-BVsunKYp.js` / `assets/index-BPeRJO55.css`.
- User manually confirmed the attachment workflow on 2026-05-11.

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

- React weekly reports first integration is implemented, pushed, deployed, and smoke-tested.
- Runtime commit: `8c9fdb6 feat: add React weekly reports`.
- Railway `web`: `4216824a-7d1f-4850-8624-11dca0b40b26` SUCCESS.
- Railway `sales-note-frontend`: `fd8547fc-63f8-4962-92de-88b182eb7984` SUCCESS.
- Deployed bundle: `assets/index-D6rGbRO3.js` / `assets/index-CjVBFS4u.css`.
- Changed files: `AGENT_PLAN.md`, `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/styles.css`, `reporting/views.py`, `reporting/urls.py`, `reporting/tests.py`.
- Local validation passed: weekly report tests, `npm run build`, `node --check server.mjs`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `git diff --check`.
- Production smoke passed: `/weekly-reports/` returns 200, protected weekly report APIs return 401 anonymous, deployed JS/CSS contain the weekly report route/styles.

Wait for user manual production verification before starting the next implementation task. Natural next slices after confirmation are:

1. Move 견적/문서 생성 workflows into React.
2. React schedule calendar parity audit and fallback links.
3. Continue customer AI result verification UI in React.

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
b345687 fix: simplify AI painpoint verification
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
- React schedule calendar: confirmed complete.
- React schedule documents: confirmed complete.

Needs awareness:

- React mailbox email line-break normalization is deployed and awaits user manual production testing.
- React schedule calendar report content/nav-first calendar entry is deployed and awaits user manual production testing.
- AI PainPoint verification memo confirm-only change is deployed and awaits user manual production testing.
- React document template management `/documents/` is deployed and awaits user manual production testing.
- AI department meeting scope fix is deployed; existing stored AI analysis results require rerun to include coworker department meetings.
- React pipeline department AI panel is deployed and can be manually tested.
- React customer detail prepayment summary is deployed and awaits user manual production testing.
- AI quote/delivery context fix is deployed, but existing stored AI results require rerun. If validating customer `454`, click AI analysis again and inspect the new output.

## Previous Completed Work: React Schedule Calendar

User confirmed the weekly report flow works except the `일정 불러오기` button needed to be on the right. That position fix was implemented first, built, committed previously as `2d02547 fix: move weekly schedule loader panel`, pushed, deployed to `sales-note-frontend` deployment `c9d534dd-8e6b-4943-8af2-89f9d643f004`, and smoke-tested (`/weekly-reports/new/` 200, JS/CSS bundle contains `weekly-schedule-load`).

The next implementation completed is React schedule calendar first integration:

- Added `/reporting/api/schedules/calendar/` authenticated JSON API.
- Added date range parsing, same-company data filters (`me`, `all`, `user`), user options, and calendar metrics.
- Added React API type/loader `ScheduleCalendarData` and `loadScheduleCalendarData`.
- Added React `/schedules/calendar/` route with month navigation, data filter, monthly grid, selected-day panel, and Django fallback links.
- Changed React schedule calendar links from `/reporting/schedules/calendar/` to `/schedules/calendar/` where React screens own the UX.
- Kept Django `/reporting/schedules/calendar/` and `/reporting/schedules/api/` intact.
- No DB model changes.

Validation passed before commit:

```powershell
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests reporting.tests.AnonymousAccessTests --verbosity=1
python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py
python manage.py check
python manage.py makemigrations --check --dry-run
cd frontend; npm run build
cd frontend; node --check server.mjs
git diff --check
```

Runtime commit and deployments:

- Runtime commit: `07d0776 feat: add React schedule calendar`
- Railway `web`: `ffa1cb41-76f6-4c82-9cf8-6731ebda092d` SUCCESS
- Railway `sales-note-frontend`: `5126b81d-e0ba-4da7-9711-d9f8248a8f25` SUCCESS

Deployed frontend assets:

- `dist/assets/index-CTcLLIQe.js`
- `dist/assets/index-BJ8JCI1J.css`

Production smoke passed:

- `https://sales-note-frontend-production.up.railway.app/schedules/calendar/` returns 200.
- deployed JS contains `schedule-calendar-page`, `/reporting/api/schedules/calendar/`, and `weekly-schedule-load`.
- deployed CSS contains `.schedule-calendar-grid`, `.schedule-calendar-day`, and `.weekly-schedule-load`.
- anonymous frontend-proxied API and direct backend API `/reporting/api/schedules/calendar/` return `401 login_required`.

Manual test requested from user:

1. Open `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`.
2. Verify month navigation and today highlight.
3. Verify `내 일정`, `회사 전체`, `직원 선택` filters.
4. Click a scheduled date and verify right-side selected-day list.
5. Open a customer schedule and a personal schedule from the list.
6. Confirm `Django 캘린더` fallback still works.
7. Recheck `/weekly-reports/new/` has `일정 불러오기` in the right schedule panel.
