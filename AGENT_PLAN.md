# AGENT_PLAN.md

## 2026-05-18 React tasks/TODO v2 detail plan

**Background**:

- User completed manual verification for React Tasks/TODO v1.
- V1 covers list/create/request/status/manager assignment, but task rows still fall back to Django for detail, edit/delete, logs, and attachments.
- Existing `todos` models already include `TodoAttachment` and `TodoLog`, so v2 can extend React without DB changes.

**DB change required**: No.

**Implementation scope**:

- Backend:
  - Add React task detail API for `/tasks/<id>/`.
  - Return task metadata, attachments, and recent activity logs.
  - Add scoped update, delete, and attachment upload APIs.
  - Preserve existing `/todos/*` legacy screens as fallback.
- Frontend:
  - Add `/tasks/<id>/` React detail route.
  - Link task cards to React detail.
  - Show task summary, description, related customer, people, attachments, logs, status actions, edit form, and delete/upload actions when permitted.
- Tests:
  - Add focused API coverage for task detail permissions, update/delete, and attachment upload.

**Validation plan**:

- `python -m py_compile todos\views.py todos\tests.py reporting\urls.py`
- Focused `todos.tests.ReactTasksApiTests` detail/update/delete/upload tests.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, and push complete. Railway platform outage caused failed deployments and temporary edge fallback 404. Production availability was restored after `sales-note-frontend` existing-image redeploy and user-triggered `web` deploy. `web` is running commit `1469a9e`; frontend is serving the previous stable image, so deploy the latest frontend bundle only after the user confirms production is stable.

## 2026-05-18 Scheduled email automatic dispatch plan

**Background**:

- User completed manual verification for scheduled mailbox detail.
- Scheduled email creation/list/detail/cancel now works, but production still needs an always-on execution path for due scheduled email dispatch.
- Current Railway services are `web`, `sales-note-frontend`, and `Postgres`; there is no dedicated worker/beat service.

**DB change required**: No.

**Implementation scope**:

- Backend:
  - Add a guarded inline scheduled-email dispatcher loop that can run inside the production web process only when explicitly enabled by environment variable.
  - Extend `process_scheduled_emails` management command with `--loop` and `--interval` so a future Railway worker/cron service can run the same logic without code changes.
  - Preserve existing Celery task path.
- Production:
  - Enable the inline dispatcher on the `web` service with a non-secret environment variable.
  - Keep this documented as a pragmatic bridge until a dedicated worker/cron service is added.

**Validation plan**:

- `python -m py_compile reporting\apps.py reporting\scheduled_email_worker.py reporting\management\commands\process_scheduled_emails.py`
- Focused scheduled email tests.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway deployment, production environment enablement, and production smoke complete. User production manual verification is next.

## 2026-05-18 Scheduled mailbox detail route fix plan

**Background**:

- User reported that clicking a scheduled email row on `/mailbox/?box=scheduled` navigates back to the same scheduled mailbox list.
- Root cause: scheduled email list items use `/mailbox/?box=scheduled` as their `threadHref` because no detail route/API existed.

**DB change required**: No.

**Implementation scope**:

- Backend:
  - Add a scheduled email detail API returning the same thread-like payload shape React already uses for email detail pages.
  - Change scheduled list item `threadHref` to `/mailbox/scheduled/<id>/`.
- Frontend:
  - Detect `/mailbox/scheduled/<id>/`.
  - Load scheduled email detail data.
  - Reuse the thread detail page but hide reply/star/trash actions and show cancel action for pending scheduled mail.
- Tests:
  - Add regression coverage for scheduled list row detail href and scheduled detail API.

**Validation plan**:

- `python -m py_compile reporting\gmail_views.py reporting\urls.py reporting\tests.py`
- Focused scheduled mailbox list/detail API tests.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- Local preview smoke for `/mailbox/scheduled/<id>/` route rendering.
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway backend/frontend deployment, and production smoke complete. User production manual verification is next.

## 2026-05-18 Scheduled mailbox disconnected view fix plan

**Background**:

- User reported that the scheduled email view shows the generic Gmail/IMAP connection message and prevents checking scheduled emails.
- Scheduled email review/cancel should be available even when the provider connection is missing; only actual sending requires Gmail or IMAP.

**DB change required**: No.

**Implementation scope**:

- Frontend:
  - Hide the generic connection-required banner on `box=scheduled`.
  - Show a scheduled-mail-specific status message.
  - Disable compose when no mail provider is connected.
- Tests:
  - Add backend regression coverage that scheduled mail API returns pending scheduled emails even without a connected provider.

**Validation plan**:

- `python -m py_compile reporting\tests.py`
- Focused scheduled mailbox API regression test.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- Local preview smoke for `/mailbox/?box=scheduled`.
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway backend/frontend deployment, and production smoke complete.
- User production manual verification pending.

## 2026-05-18 AI mini-only + scheduled email plan

**Background**:

- User asked to remove GPT-5.5 from AI model selection and center AI question answering on GPT-5.4 mini.
- User also asked to add scheduled email sending after Gmail re-authentication.
- These affect runtime behavior in both Django APIs and the React CRM frontend.

**DB change required**: Yes.

- AI model cleanup does not need a migration.
- Scheduled email needs pending outbound mail to persist before sending, so add a separate `ScheduledEmail` queue model instead of overloading delivered `EmailLog` rows.

**Implementation scope**:

- Backend:
  - Limit AI workspace question model choices/defaults to `gpt-5.4-mini`.
  - Keep old/stale client values from breaking by normalizing invalid AI model ids to the default mini model.
  - Add scheduled email persistence and due-send execution path.
  - Keep delivered mail in `EmailLog`; create `EmailLog` only after a scheduled email is actually sent.
  - Add a Celery task and management command so production can send due scheduled emails through a worker/beat or Railway cron process.
- Frontend:
  - Remove GPT-5.5 from AI model choice fallbacks and defaults.
  - Add send-now vs scheduled-send controls to the mailbox compose panel.
  - Show scheduled/pending status in mailbox lists.
- Tests:
  - Add focused coverage for mini-only AI selection.
  - Add focused coverage for scheduling an email without immediate provider send and sending due scheduled mail later.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\gmail_views.py reporting\tasks.py sales_project\celery.py reporting\tests.py`
- Focused Django tests for AI workspace model selection and scheduled email APIs/tasks.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway backend/frontend deployment, and production smoke complete.
- User production manual verification pending.

## 2026-05-18 React tasks/TODO v1 + navigation API plan

**Background**:

- User completed manual verification for the weekly report line-break fixes and asked to continue.
- The agreed next React migration task is `업무/TODO React v1 + 권한 기반 메뉴 기반 정리`.
- Existing legacy TODO workflow lives in the `todos` app under `/todos/*` and already has models for `Todo`, `TodoCategory`, `TodoAttachment`, and `TodoLog`.

**DB change required**: No.

- Reuse existing `todos` models.
- Do not add migrations.

**Locked v1 scope**:

- Include:
  - Personal tasks list: my tasks, received tasks, requested tasks.
  - Task creation.
  - Peer task request.
  - Status actions: approve, reject, ongoing, on hold, done.
  - Manager-only task assignment and manager task status updates.
  - Backend navigation API and React dynamic navigation fallback.
- Exclude for v1:
  - Attachments.
  - Edit/delete.
  - Category CRUD.
  - Full task detail migration.
  - Legacy template deletion.

**Permission defaults**:

- Personal `/tasks/` is available to authenticated users.
- Manager assignment `/tasks/manager/` is available only to role `manager`, matching legacy TODO behavior.
- Same-company scoping must be preserved for peer assignees, manager assignees, and customer search.

**Implementation scope**:

- Backend:
  - Add `/reporting/api/navigation/`.
  - Add React-facing task APIs under `/reporting/api/tasks/*`.
  - Keep `/todos/*` legacy screens as fallback.
  - Add focused API tests in `todos/tests.py`.
- Frontend:
  - Add `/tasks/` and `/tasks/manager/` route handling.
  - Add navigation loader with existing static nav fallback.
  - Add task list/create/status UI and manager assignment UI.
- Documentation:
  - Update `AGENT_REPORT.md` after validation/deployment.

**Validation plan**:

- `python -m py_compile todos\views.py todos\tests.py reporting\views.py reporting\urls.py`
- Focused `todos.tests` API tests.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`

**Current status**:

- Implemented, locally validated, committed, pushed, and deployed. User production manual verification pending.

## 2026-05-18 Weekly report paragraph spacing fix plan

**Background**:

- User manually checked the previous weekly report line-break fix and reported a remaining issue:
  entries separated by a blank line in the textarea are saved/displayed as visually adjacent blocks on `/weekly-reports/3/`.
- React weekly report saving already converts blank lines into separate `<p>` blocks, but the React detail CSS made adjacent paragraphs appear too tight to read as an intentional blank line.

**DB change required**: No.

**Implementation scope**:

- Backend:
  - Preserve adjacent paragraph boundaries in the safe fallback renderer used when full `bleach` CSS sanitization is unavailable.
- Backend tests:
  - Add regression coverage that schedule-like blocks separated by blank lines are saved as distinct paragraphs and round-trip to textarea text with blank lines intact.
- Frontend:
  - Adjust React weekly report detail paragraph spacing so adjacent `<p>` blocks show a clear blank-line gap.

**Validation plan**:

- `python -m py_compile reporting\tests.py`
- Focused weekly report paragraph spacing regression test.
- `python manage.py test reporting.tests.WeeklyReportReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway backend/frontend deployment, and production smoke complete.
- Waiting for user production manual verification.

## 2026-05-18 Weekly report line break rendering fix plan

**Background**:

- User reported that line breaks are not applied on React weekly report detail: `/weekly-reports/3/`.
- The React page renders sanitized report HTML from Django API.
- Existing renderer treated rich-text HTML as HTML only when the content started with an HTML tag, so mixed text like `첫 줄<br>둘째 줄` could be escaped and displayed without actual line breaks.

**DB change required**: No.

**Implementation scope**:

- Backend:
  - Update weekly report HTML detection to recognize allowed rich-text tags anywhere in the field, not only at the start.
  - Preserve sanitization before rendering.
- Tests:
  - Add regression coverage for inline `<br>` and escaped `&lt;br&gt;` content in weekly report detail API.

**Validation plan**:

- `python -m py_compile reporting\utils_html.py reporting\tests.py`
- Focused weekly report line-break tests.
- `python manage.py test reporting.tests.WeeklyReportReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway backend deployment, and production smoke complete.
- Waiting for user production manual verification.

## 2026-05-18 Customer asset directory / search v1 plan

**Background**:

- User manually verified customer asset/service/calibration v1 and asked to continue.
- V1 lets users manage equipment from a single customer detail page, but there is no React screen to search across all owned customer assets.
- React migration direction favors a dedicated CRM workflow over sending users back to Django admin or per-customer pages.

**DB change required**: No.

- Reuse `CustomerAsset`, `ServiceCase`, and `CalibrationRecord`.
- Add read-only list/search API and React page only.

**Implementation scope**:

- Backend:
  - Add `/reporting/api/customer-assets/` JSON API.
  - Scope records by existing dashboard/user visibility rules.
  - Support keyword, status, owner, service state, and calibration due filters.
  - Return metrics, filter options, latest service/calibration payloads, and links to React customer detail.
- Frontend:
  - Add `/assets/` route and navigation item.
  - Add React asset directory page with KPI cards, filters, and a dense asset table/card list.
  - Keep asset creation/editing in customer detail v1; list rows deep-link to `/customers/<id>/`.
- Tests:
  - Add API login, scope, search/filter, and manager visibility tests.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- Focused customer asset directory API tests.
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- Local smoke for `/assets/` where feasible.
- `git diff --check`

**Current status**:

- Implementation, local validation, commit, push, Railway deployment, and production smoke complete.
- Waiting for user production manual verification.

## 2026-05-18 Customer asset / service / calibration v1 plan

**Background**:

- User chose the hybrid direction: keep React migration moving, but start the global CRM expansion as a React-first workflow.
- The benchmark gap analysis identified customer-owned equipment, A/S cases, and calibration records as the largest life-science CRM gap.
- Current React customer detail already has customer summary, notes, schedules, prepayments, and AI context, so v1 should attach the new workflow there instead of creating a separate menu first.

**DB change required**: Yes.

- Add `CustomerAsset`, `ServiceCase`, and `CalibrationRecord` models in `reporting`.
- Ownership model:
  - Asset belongs to `Company` and `Department`.
  - Optional primary `FollowUp` links the asset to a specific 담당자/customer detail.
  - Records keep `created_by` and timestamps for permission scope and traceability.
- v1 intentionally does not force serial-number uniqueness because legacy/field data can be incomplete or duplicated.

**Implementation scope**:

- Backend:
  - Add models, admin registration, and migration.
  - Add customer-detail asset summary payload.
  - Add JSON APIs for creating/updating assets, service cases, and calibration records from React.
  - Reuse existing login, company/user scope, and manager read-only rules.
- Frontend:
  - Extend React customer detail API types and normalization.
  - Add a customer-detail `장비/A/S/교정` section with empty state, compact metrics, recent assets, and inline create/edit forms.
  - Do not add a separate navigation item in v1.
- Existing behavior:
  - Keep `/reporting/*` Django template routes as fallback.
  - Do not delete legacy templates or change public routes.
  - Do not connect this to AI recommendations yet.

**Validation plan**:

- `python -m py_compile reporting\models.py reporting\views.py reporting\urls.py reporting\admin.py reporting\tests.py`
- Focused Django tests for customer asset summary and mutation permissions.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- Local browser smoke for customer detail asset/service/calibration forms where feasible.
- `git diff --check`

**Current status**:

- Implemented, locally verified, committed, pushed, and deployed to Railway `web` and `sales-note-frontend`.
- Railway `web` deployment `0cbdaf15-58f9-4f72-9e9f-bc6c2e704cf6` is SUCCESS.
- Railway `sales-note-frontend` deployment `fd28bb07-8fd4-49da-bc1b-691fff53059d` is SUCCESS.
- Production smoke passed: backend login 200, frontend `/customers/` 200 with bundle `assets/index-DW6PG7yO.js`, protected customers/AI APIs anonymous 401.

## 2026-05-18 AI Workspace email CRM context fix plan

**Background**:

- User reported that `/ai-workspace/?department_id=146` does not use email history even when explicitly asked to reference mail.
- Current AI Workspace action queue can surface `email_waiting`, but department/all-scope question context did not include recent `EmailLog` subjects or bodies.
- AI answers must be able to reference mail as part of CRM evidence, while still staying inside the authenticated user's CRM scope.

**DB change required**: No.

- Reused existing `EmailLog` links to `FollowUp` and `Schedule`.
- No model or migration changes.

**Implementation scope**:

- Backend:
  - Added a scoped recent-email context payload for AI Workspace questions.
  - Included sent/received date, subject, body excerpt, contact, customer/company/department, thread link, and attachment filenames.
  - Added `recentEmails` to both selected-department and all-department question contexts.
  - Updated prompt rules so explicit mail/email requests must use `crmContext.recentEmails` or state that no matching email exists.
  - Returned `recentEmailCount` in the question response context for verification/debugging.
- Tests:
  - Added focused tests proving department-scope question prompts include recent email body/subject.
  - Added a fallback test proving explicit mail questions can answer from recent email context when OpenAI is unavailable.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- Focused AI Workspace email-context tests.
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

**Current status**:

- Implemented, locally verified, committed, pushed, and deployed to Railway `web`.
- Railway `web` deployment `f06d55db-ece2-4146-8ab9-327b639ece5e` is SUCCESS.
- Production smoke passed: backend login 200, AI Workspace API anonymous 401, frontend AI Workspace page 200.

## 2026-05-18 CRM global benchmark gap analysis plan

**Background**:

- User provided a global CRM benchmark report covering customer DB, pipeline, activities, quotes, products/orders, service, assets/calibration, marketing, analytics, workflow, AI, and security.
- Current code inspection shows strong existing coverage in customer/activity/pipeline/product/quote/delivery/mail/weekly-report/AI areas.
- The largest business-specific gaps are customer-owned equipment/assets, serial/warranty/calibration history, formal A/S service cases/SLA, campaign/consent, and domain audit logging.

**DB change required**: No.

- This task is documentation and roadmap analysis only.
- No runtime behavior, model, API, React route, migration, or deployment change is required.

**Implementation scope**:

- Add a CRM benchmark gap analysis document that maps the provided global CRM 12-axis framework to the current Sales Note implementation.
- Classify each axis as strong, partial, weak, or missing using current model/API/frontend evidence.
- Identify business risk, benchmarkable improvements, and recommended P0/P1/P2 priorities.
- Highlight the next recommended implementation candidate: customer asset + service/calibration CRM groundwork.
- Update `AGENT_REPORT.md` with summary, files changed, validation, deployment status, and recommended next task.

**Validation plan**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

**Current status**:

- Completed as documentation-only benchmark analysis in `CRM_BENCHMARK_GAP_ANALYSIS.md`.

## 2026-05-17 AI Workspace all-department question plan

**Background**:

- User requested AI Workspace questions that cover all departments, not only the selected department.
- Model selection must remain available for both GPT-5.5 and GPT-5.4 mini.
- Current backend already supports no-`departmentId` question requests by building global CRM context and saving `AIWorkspaceQuestionLog(scope_type='all', department=NULL)`, but the React UI blocks submitting without a department and the history payload only returns department history.

**DB change required**: No.

- Saving all-department answers is recommended because AI answers can affect sales decisions and should be auditable.
- Store them in the existing `AIWorkspaceQuestionLog` table with `scope_type='all'` and `department=NULL`.
- This keeps one history/detail/delete model while allowing department history and all-department history to be filtered separately.

**Implementation scope**:

- Backend:
  - Add `question_scope=all|department` support to the AI Workspace summary API.
  - Return all-department question history from existing `AIWorkspaceQuestionLog` when `question_scope=all`.
  - Make question API accept explicit `scopeType='all'` and save the answer as an all-scope log.
  - Update all-scope back links to return to `/ai-workspace/?question_scope=all`.
- Frontend:
  - Add a question scope segmented control: selected department vs all departments.
  - Keep GPT-5.5 / GPT-5.4 mini selection unchanged.
  - For all-department scope, submit without `departmentId`, show all-department counts, refresh all-scope history, and keep the URL query in sync.
  - Keep department detail links, deletion, and pagination working per selected scope.
- Tests:
  - Add backend tests for all-scope question save and all-scope history filtering.
  - Add local UI smoke for all-department scope question/history/delete rendering with mocked data.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_records_all_scope_question_log reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_summary_includes_all_scope_question_history --verbosity=1`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- Local Playwright smoke for department/all question scope and history delete UI.
- `git diff --check`

## 2026-05-17 AI Workspace question history delete plan

**Background**:

- 운영 `/ai-workspace/?department_id=10` 수동 검수 후, 사용자가 질문/답변 기록 리스트에서 개별 기록 삭제 기능을 요청했다.
- 현재 질문 기록은 `AIWorkspaceQuestionLog`에 저장되고, React 리스트 항목은 `/ai-workspace/questions/<id>/` 상세 링크로만 동작한다.

**DB change required**: No.

- 기존 `AIWorkspaceQuestionLog` row를 삭제한다.
- 새 필드, migration, soft-delete 상태는 이번 범위에 추가하지 않는다.

**Implementation scope**:

- Backend:
  - 현재 사용자 소유 + `can_use_ai` 권한을 확인하는 질문 로그 삭제 API를 추가한다.
  - 다른 사용자 기록은 404로 차단한다.
  - 삭제 성공 시 삭제된 기록 id와 돌아갈 AI Workspace 링크를 JSON으로 반환한다.
- Frontend:
  - 질문/답변 기록 리스트 카드에 아이콘 삭제 버튼을 추가한다.
  - 삭제 버튼 클릭은 상세 링크 이동과 충돌하지 않도록 이벤트 전파를 막는다.
  - 삭제 중 상태, confirm, 성공/실패 메시지, 삭제 후 현재 페이지 refresh를 처리한다.
- Existing behavior:
  - 질문 기록 상세 페이지, 질문 실행, 페이지네이션, 기존 AI 권한/로그인 보호는 유지한다.

**Validation plan**:

- 소유자 삭제 성공, 다른 사용자 기록 삭제 차단, AI 권한 없는 사용자 삭제 차단 테스트 추가.
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_log_delete_api_deletes_owner_log reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_log_delete_api_blocks_other_users_log reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_log_delete_api_requires_ai_permission --verbosity=1`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- Local browser smoke for AI Workspace question history delete UI.
- `git diff --check`

## 2026-05-17 AI Workspace product-code grounding fix plan

**Background**:

- AI Workspace 부서 질문 답변에서 `P4345N00` 제품을 `튜브(P4345N00)`처럼 실제 제품 성격과 맞지 않게 표현하는 문제가 확인됐다.
- 로컬 제품 마스터 기준 `P4345N00`은 `RLD-1250NS, 1250 µL Low Retention Paradigm Refills, Benchtop, 8 x 96 / pk`, 규격 `5 pk / CS`, 단위 `pk`로 등록되어 있다.
- 현재 AI 질문 컨텍스트의 견적/납품 품목은 대부분 `product` 코드만 전달하고 제품 설명/규격/단위가 빠져, 모델이 코드만 보고 임의 분류를 붙일 수 있다.

**DB change required**: No.

- 기존 `Product.description`, `Product.specification`, `Product.unit`을 읽기만 한다.
- 새 필드, migration, 데이터 보정 스크립트는 추가하지 않는다.

**Implementation scope**:

- AI용 견적/납품 품목 payload에 제품 마스터의 `productCode`, `productDescription`, `productSpecification`, `productUnit`, `productLabel`을 추가한다.
- AI Workspace 부서 질문 컨텍스트에 코드별 `productFacts`를 포함해 제품 마스터 설명/규격/단위를 명시한다.
- 질문 프롬프트 rules에 “제품 코드는 식별자이며, productFacts/제품 설명에 없는 품목 유형을 새로 붙이지 말라”는 규칙을 추가한다.
- OpenAI 응답 정규화 후 제품 코드 주변의 `튜브(P4345N00)` 같은 unsupported label을 제품 마스터 label 또는 `P4345N00 품목`으로 치환하는 deterministic guard를 추가한다.
- 기존 `/reporting/*`, AI 권한, 부서 접근 권한, React UI는 유지한다.

**Validation plan**:

- 제품 마스터가 연결된 납품 품목에서 AI context가 제품 설명/규격/단위/productFacts를 포함하는지 테스트한다.
- OpenAI 응답이 unsupported label을 붙여도 정규화 단계에서 제품 마스터 label로 치환되는지 테스트한다.
- `python -m py_compile ai_chat\services.py reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_context_includes_product_master_facts reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_product_guard_replaces_unsupported_label --verbosity=1`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

**Current status**:

- 구현, 로컬 검증, 커밋/푸시 완료: `2045f77 fix: ground AI product code labels`.
- Railway `web` GitHub 자동 배포 완료: `f6bc2817-10a8-4291-8d69-64504029dc86` SUCCESS.
- 운영 smoke 완료: backend login 200, AI Workspace API anonymous 401, logs startup OK.

## Current task — AI Workspace 질문 중심 단순화와 부서별 Q&A 기록

**목표**: AI Workspace의 과도한 추천/분석 섹션을 화면에서 줄이고, 부서 선택 기반의 질문 흐름과 부서별 질문/답변 기록, 현재 답변 방향만 남겨 사용자가 판단에 집중할 수 있게 한다.

### 확인된 범위

- 화면에서 숨김: AI 추천 실행 목록, AI 실행 피드백, 고객 분석 대상, 추천 질문, 추천 목표 및 관련 요약 패널.
- 화면에 유지: 부서 상황 질문, 부서 분석 대상.
- 기존 AI 추천 실행/피드백/목표/질문 API와 데이터는 삭제하지 않고 보존한다.
- 부서별 질문과 답변 스냅샷은 사용자별로 기록하고, 선택한 부서 아래에서 페이지네이션으로 보여준다.
- 답변 방향성은 사용자+부서별 현재 값 하나만 저장하며, 변경 시 덮어쓴다.
- 현재 답변 방향성은 이후 질문 프롬프트에 사용자 선호로 반영하되 CRM 사실로 취급하지 않는다.
- 부서 질문을 보낼 때마다 사용자가 `GPT-5.5` 또는 `GPT-5.4 mini` 모델을 선택할 수 있게 한다.

### 구현 계획

- `AIWorkspaceQuestionLog`, `AIWorkspaceAnswerDirection` 모델과 migration을 추가한다.
- AI Workspace summary/question API에 선택 부서의 질문 기록과 현재 답변 방향성을 포함한다.
- 질문 답변 생성 성공 시 질문/답변 스냅샷을 저장한다.
- 현재 답변 방향성을 저장/수정하는 API를 추가한다.
- 질문 API에 선택 모델 검증과 응답/기록 스냅샷 반영을 추가한다.
- React API 타입과 클라이언트를 갱신한다.
- React AI Workspace 화면을 부서 목록, 부서 질문 패널, 모델 선택, 현재 답변 방향성, 질문/답변 기록으로 단순화한다.
- Django 테스트, check, migration dry-run, frontend 타입체크/빌드, diff check를 실행한다.
- `AGENT_REPORT.md`를 갱신하고 커밋/푸시/배포 후 운영 smoke와 수동 검증 절차를 제공한다.

### 검증 계획

- 질문 API가 질문 기록을 생성하고 응답에 로그 정보를 포함하는지 확인한다.
- summary API가 현재 사용자와 선택 부서의 질문 기록만 페이지네이션으로 반환하는지 확인한다.
- 방향성 API가 AI 권한과 부서 접근 권한을 검증하고, 사용자+부서별 현재 값 하나만 유지하는지 확인한다.
- 현재 답변 방향성이 질문 생성 컨텍스트에 포함되는지 확인한다.
- 질문 API가 허용 모델만 받고 선택 모델을 응답과 기록에 남기는지 확인한다.
- React 빌드 결과에 삭제 대상 섹션명이 표시되지 않는지 확인한다.

### 현재 상태

- `AIWorkspaceQuestionLog`, `AIWorkspaceAnswerDirection` 모델, migration, admin 등록 구현 완료.
- AI Workspace summary/question API에 질문 기록, 답변 방향, 모델 선택 payload 반영 완료.
- 질문 생성 시 선택 모델 검증, 응답 모델 라벨, 질문/답변 스냅샷 기록 구현 완료.
- 답변 방향 저장 API 구현 완료.
- React AI Workspace 화면을 `부서 분석 대상`과 `부서 상황 질문` 중심으로 단순화 완료.
- 질문 모델 선택, 현재 답변 방향 저장, 질문/답변 기록 페이지네이션 UI 구현 완료.
- Django AI Workspace 전체 테스트, check, migration dry-run, frontend 타입체크/빌드, 로컬 Playwright smoke, diff check 통과.
- 커밋/푸시 완료: `1f8878e feat: simplify ai workspace questions`.
- Railway `web` 배포 완료: `875c6e05-2ff9-47cf-91b3-47be2b2698f7` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `c0132d9b-bc90-45a1-909e-5020a147e0bf` SUCCESS.
- 운영 smoke 완료: 최신 프론트 번들, migration 적용, backend anonymous auth response 확인.

---

## Current task — AI Workspace 저장형 질문 피드백 루프

**목표**: AI Workspace 질문 답변에 대한 사용자의 평가와 수정 코멘트를 저장하고, 이후 같은 사용자의 질문 답변 컨텍스트에 반영해 답변 톤과 판단 품질을 점진적으로 개선한다.

### 확인된 상태

- `AIWorkspaceActionFeedback`은 추천 실행 목록에 대한 현장 답변과 AI 판단 결과를 저장한다.
- 부서/전체 질문 API(`/reporting/api/ai-workspace/question/`)는 현재 질문과 CRM 컨텍스트를 기반으로 JSON 답변을 생성하지만, 질문 답변 자체에 대한 사용자 평가를 저장하지 않는다.
- React AI Workspace 질문 패널은 답변을 표시하지만, 답변이 좋았는지/어떤 방향으로 수정해야 하는지 기록하는 UI가 없다.
- 기존 액션 피드백과 질문 답변 피드백은 목적이 다르므로 별도 모델이 필요하다.

### 구현 계획

- `AIWorkspaceQuestionFeedback` 모델과 migration을 추가한다.
- 저장 항목은 사용자, 부서, 범위 유형, 질문, 답변 스냅샷, source, 평가값, 수정 코멘트, 생성/수정 시각으로 제한한다.
- `POST /reporting/api/ai-workspace/question/feedback/` API를 추가하고 로그인 및 `can_use_ai` 권한을 유지한다.
- `rating`은 `helpful`, `needs_style`, `incorrect`만 허용하고, `needs_style`/`incorrect`는 코멘트를 필수로 검증한다.
- 질문 답변 컨텍스트에 현재 사용자 본인의 최근 질문 피드백만 포함한다.
- OpenAI 프롬프트에는 질문 피드백을 CRM 사실이 아니라 답변 방식 선호/오류 회피 기준으로만 사용하도록 규칙을 추가한다.
- React 질문 답변 카드 아래에 평가 버튼과 코멘트 입력/저장 상태를 추가한다.
- 회사 전체 공유, 관리자 승인형 좋은 답변 라이브러리, fine-tuning은 이번 범위에서 제외한다.

### 검증 계획

- `python -m py_compile reporting\models.py reporting\views.py reporting\urls.py reporting\admin.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_feedback_api_requires_ai_permission reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_feedback_api_records_feedback reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_feedback_api_requires_comment_for_negative_rating reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_context_includes_only_own_question_feedback --verbosity=1`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- `AIWorkspaceQuestionFeedback` 모델, migration, admin 등록 구현 완료.
- 질문 피드백 저장 API와 URL 추가 완료.
- 질문 답변 컨텍스트에 현재 사용자 본인의 최근 질문 피드백만 포함하도록 구현 완료.
- OpenAI 프롬프트에 질문 피드백을 답변 방식 선호/오류 회피 기준으로만 쓰도록 규칙 추가 완료.
- React AI Workspace 질문 답변 카드에 `답변 피드백` 평가/코멘트/저장 UI 추가 완료.
- 집중 테스트 4건, AI Workspace 전체 테스트 52건, Django check, migration dry-run, frontend 타입체크/빌드, node syntax check, diff check 통과.
- 로컬 Playwright smoke에서 질문 답변 후 `방향 수정` 피드백 저장 UI와 API payload, 성공 메시지, 콘솔 오류 없음 확인.
- 커밋/푸시 완료: `cd6ac20 feat: add ai question feedback loop`.
- Railway `web` 배포 완료: `22388975-3692-4d8a-9b6f-9fabac311e79` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `e99e2be2-10b1-42be-96fc-2640b0c56d1b` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 최신 번들 `assets/index-DNG2AEtn.js`에 `답변 피드백`/새 API 클라이언트 포함, AI Workspace summary anonymous 401, question feedback POST without auth/CSRF 403.

---

## Completed task — AI Workspace 선택지형 질문 결론 강화

**목표**: AI Workspace 질문이 “할까/말까”, “A가 좋을까 B가 좋을까”처럼 선택지형일 때, CRM 브리핑보다 먼저 추천 선택을 명확히 제시하고 버릴 선택과 예외 조건을 함께 보여준다.

### 확인된 상태

- 질문 답변 API는 `summary`, `actionItems`, `perspective`, `evidence`를 반환한다.
- 직전 작업으로 고객 입장 추정은 표시되지만, 선택지형 질문에서 결론이 여전히 부드럽게 보일 수 있다.
- React Department Q&A 답변 카드는 `summary` 아래에 고객 관점 섹션을 표시한다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 질문 답변 JSON 계약에 optional `decision` 객체를 추가한다.
- `decision`에는 `recommendedChoice`, `rejectedChoice`, `reason`, `exception`을 담는다.
- OpenAI 프롬프트에 “선택지형 질문이면 반드시 하나를 고르고 decision을 채운다” 규칙을 추가한다.
- 샘플/재견적/피드백 fallback은 “샘플 피드백을 다시 캐묻지 말고, 재견적 설명 끝에 조건 확인처럼 짧게 묻기”를 추천 판단으로 반환한다.
- 스케일업 fallback은 “같은 품목 업셀보다 소모 속도/다음 실험/동반 소모품 확인”을 추천 판단으로 반환한다.
- React 답변 카드 최상단에 `추천 판단` 박스를 추가한다.
- 기존 `/reporting/*`, AI 권한, 로그인 보호, 데이터 스코프는 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_normalizes_decision reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_requote_sample_feedback_uses_customer_perspective reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_scale_up_uses_customer_perspective --verbosity=1`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- 백엔드/프론트 구현은 긴급 고객 API 핫픽스 전 작업본에서 복구 완료.
- 핫픽스 commit `6026cf4`, docs commit `631010b` 이후 main 위에서 충돌 정리 완료.
- 백엔드 `decision` 정규화, OpenAI 프롬프트 규칙, 샘플/재견적/스케일업 fallback 추천 판단 구현 완료.
- React AI Workspace 질문 답변 카드에 `추천 판단` 박스와 `버릴 선택`/`판단 이유`/`예외 조건` 표시 완료.
- 질문 응답 context가 비어도 UI가 깨지지 않도록 React context 접근을 방어적으로 보강 완료.
- 집중 테스트 3건, AI Workspace 전체 테스트 48건, Django check, migration dry-run, frontend 타입체크/빌드, diff check 통과.
- 로컬 Playwright smoke에서 모킹된 AI Workspace 질문 응답의 `추천 판단`/`버릴 선택`/`판단 이유`/`예외 조건`/`고객 입장 추정`/`말문 예시` 렌더링과 콘솔 오류 없음 확인.
- 커밋/푸시 완료: `449b378 feat: add decisive ai workspace answers`.
- Railway `web` 배포 완료: `270c242e-b5ce-4006-9fbf-74a87bdcc09d` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `8cc2ad82-4610-4b59-8448-0cf5aa808d07` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 200, latest bundle `assets/index-6cgphG4x.js`에 `추천 판단`/`버릴 선택` 포함, AI Workspace API 로그인/CSRF 보호 확인.
- 사용자 운영 계정 수동검수 완료. 현재 답변 품질은 사용자가 만족한다고 확인함.

---

## Completed task — Customers API 500 긴급 복구

**목표**: 운영 React 고객 목록(`/customers/`)에서 `/reporting/api/customers/`가 500을 반환해 `Customers API unavailable: 500`이 뜨는 문제를 즉시 복구한다.

### 확인된 상태

- 운영 프론트 `/customers/` HTML은 정상 200으로 내려온다.
- 운영 백엔드 로그에서 `/reporting/api/customers/`가 `_customers_schedule_payload()` 내부 `followup` 미정의 참조로 `NameError`를 발생시키는 것을 확인했다.
- 문제는 예정 일정이 있는 고객 payload의 `createHistoryHref` 생성 과정에서 발생한다.
- 인증/권한/CSRF 문제가 아니라 서버 코드 예외다.
- DB 모델 변경과 migration은 필요 없다.

### 현재 상태

- 운영 로그에서 `NameError: name 'followup' is not defined` 원인 확인 완료.
- `_customers_schedule_payload()`가 `schedule.followup_id`로 보고 작성 링크를 생성하도록 수정 완료.
- 고객 API 일정 snapshot 테스트에 React 보고 링크와 Django 보고 생성 링크 검증 추가 완료.
- `CustomersSummaryApiTests` 22건, Django check, migration dry-run, diff check 통과.
- 커밋/푸시 완료: `6026cf4 fix: repair customers schedule payload`.
- Railway `web` 최종 배포 완료: `e54ed6f9-51c0-46d7-b64c-8eb5aa7611c4` SUCCESS.
- 운영 smoke 완료: `/customers/` 200, anonymous `/reporting/api/customers/` 401 login_required, latest `web` logs clean.
- 사용자 운영 계정 수동검수 완료.

---

## Current task — AI Workspace 고객 관점 답변 구조화

**목표**: AI Workspace 질문 답변이 CRM 사실 요약에 머물지 않고, CRM 근거 기반 `고객 입장 추정`과 `영업 판단`, 자연스러운 말문 예시를 함께 제공하게 한다.

### 확인된 상태

- `/reporting/api/ai-workspace/question/`는 부서 또는 전체 범위 CRM 컨텍스트를 모아 OpenAI JSON 답변 또는 서버 fallback을 반환한다.
- 현재 프롬프트는 “CRM 사실만 사용”, “데이터가 없으면 추측하지 않음”을 강하게 요구해 고객 관점 추론보다 CRM 브리핑이 앞선다.
- React 답변 카드는 `summary`, `actionItems`, `bullets`, `evidence`, 마지막 주문/납품을 표시한다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 질문 답변 JSON 계약에 optional `perspective` 객체를 추가한다.
- `perspective`에는 `customerPerspective`, `salesJudgment`, `recommendedApproach`, `talkTrack`, `caution`을 담는다.
- OpenAI 프롬프트는 근거 없는 단정을 금지하되, CRM 근거 기반 고객 입장 추정은 명확히 라벨링해 허용한다.
- 서버 fallback은 샘플/재견적/피드백 질문과 스케일업 질문에서 고객 입장 추정과 영업 판단을 생성한다.
- React API 타입과 답변 카드에 고객 관점 섹션을 추가하고 기존 표시 구조는 유지한다.
- 기존 `/reporting/*`, AI 권한, 로그인 보호, 데이터 스코프는 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_uses_recent_feedback_as_completed_sample_context reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_requote_sample_feedback_uses_customer_perspective reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_scale_up_uses_customer_perspective reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_normalizes_perspective --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- 백엔드 질문 답변 `perspective` 정규화 및 OpenAI 프롬프트 규칙 추가 완료.
- 샘플/재견적/피드백 질문과 스케일업 질문 fallback에 고객 입장 추정, 영업 판단, 추천 접근, 말문 예시, 주의점 추가 완료.
- React AI Workspace 답변 카드에 고객 관점 섹션 표시 완료.
- AI Workspace 전체 테스트 클래스 47건 통과. Django check, migration dry-run, frontend 타입체크/빌드, node syntax check, diff check 통과.
- 로컬 Playwright smoke에서 모킹된 AI Workspace 질문 응답의 `고객 입장 추정`/`영업 판단`/`말문 예시` 렌더링과 콘솔 오류 없음 확인.
- 런타임 커밋/푸시 완료: `1046222 feat: add customer perspective to ai workspace answers`.
- Railway `web` 배포 완료: `46c28289-582f-44c8-be31-ff9e03af260c` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `c02dfa17-3d05-474a-b0c0-79558dfb7e9b` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 최신 번들 반영, 번들 내 `고객 입장 추정`/`말문 예시` 포함, AI Workspace API 로그인/CSRF 보호 확인.

---

## Current task — AI Workspace 현장 답변 기반 추천 목표 보강

**목표**: AI Workspace 추천 액션에 남긴 최근 현장 답변을 `recommendedGoals`와 추천 질문 프롬프트 맥락에 보수적으로 반영해, 오래된 분석보다 최신 영업 상황을 더 잘 따르게 한다.

### 확인된 상태

- `AIWorkspaceActionFeedback`은 추천 액션 답변, AI 판단 결과, 연결 고객, 상태, 생성된 영업노트를 이미 저장한다.
- 현재 답변은 액션 숨김/이력/질문 컨텍스트에는 쓰이지만, `/reporting/api/ai-workspace/`의 `recommendedGoals`와 prompt target에는 충분히 반영되지 않는다.
- React 추천 목표 카드는 title/description/reason/customer/priorityLabel 중심으로 표시된다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 최근 30일 이내의 사용자 소유 `AIWorkspaceActionFeedback`만 추천 신호로 사용한다.
- `next_action` 상태와, `answered` 중 `follow_up_needed`, `positive_buying_signal`, `email_waiting` 의도만 추천 목표로 승격한다.
- `resolved`, `dismissed`, `resolved_no_purchase`, `shouldHide`, `decision=hide`는 추천 목표와 프롬프트 맥락에서 제외한다.
- 현장 답변 기반 목표는 `최근 현장 답변 기반`으로 표시하고 기존 분석 기반 추천을 완전히 대체하지 않고 앞쪽에 보강한다.
- 부서 상세 모드에서는 해당 부서의 고객 답변만, 전체 모드에서는 현재 사용자 소유 고객 답변만 사용한다.
- 부서/고객/PainPoint 추천 프롬프트의 context에도 최근 현장 답변을 짧게 포함한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_summary_promotes_recent_field_feedback_to_recommended_goals reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_detail_feedback_goals_and_prompts_scope_to_requested_department --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- 현장 답변 추천 적합성 판정 helper 추가 완료.
- 최근 현장 답변 기반 `recommendedGoals` 보강과 prompt context 반영 완료.
- React 추천 목표 카드에 `최근 현장 답변 기반` 출처 표시 추가 완료.
- 새 집중 테스트 2건과 기존 AI Workspace 핵심 테스트 4건 통과.
- Django checks, migration dry-run, frontend 타입체크/빌드 통과.
- 커밋/푸시 완료: `38d474e feat: use field feedback in AI goals`.
- Railway `web` 배포 완료: `284c9f4f-8e26-4d3c-8ff6-13704e940a55` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `709404e3-1662-44fc-9a50-6a44b7e984b4` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 최신 번들 반영 및 AI Workspace API 로그인 보호 확인.

---

## Current task — AI Workspace PI/담당자 이름 기반 부서 검색

**목표**: React AI Workspace의 분석 대상 부서 검색에서 회사/부서/고객/요약뿐 아니라 기존 FollowUp의 `manager`(PI/담당자) 이름으로도 부서를 찾을 수 있게 한다.

### 확인된 상태

- `/reporting/api/ai-workspace/`는 현재 로그인 사용자의 FollowUp만 대상으로 부서 payload를 만든다.
- 부서별 검색 후보는 `customer_name` 중심으로만 구성되어 `manager` 필드가 React 검색 대상에 포함되지 않는다.
- React `AIWorkspaceDepartmentList`는 `company`, `name`, `summary`, `customerPreview`만 검색한다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- AI Workspace summary API에서 부서별 `searchText` optional 필드를 추가한다.
- `searchText`에는 현재 사용자 소유 FollowUp의 고객명과 `manager` 값을 중복 제거해 포함한다.
- React `AIWorkspaceDepartment` 타입에 `searchText`를 추가하고 부서 검색 필터에 반영한다.
- 검색 placeholder와 안내 문구를 PI/담당자 검색 가능 상태로 갱신한다.
- 기존 `/reporting/*`, AI 권한, 로그인 보호, legacy Django templates는 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_summary_department_search_text_includes_own_manager_names_only --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- 백엔드 AI Workspace 부서 payload에 `searchText` optional 필드 추가 완료.
- React 부서 검색 필터가 `searchText`를 사용하도록 타입/UI 문구 수정 완료.
- 사용자 소유 PI/담당자명만 검색 텍스트에 포함되는 집중 테스트 통과.
- Django checks, migration dry-run, frontend 타입체크/빌드 통과.
- 커밋/푸시 완료: `2ab4f06 feat: search AI departments by PI name`.
- Railway `web` 배포 완료: `76e8a75e-4932-42cb-96a5-5d868f396c0e` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `d37621b2-596d-462a-b335-e517f0d55333` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 최신 번들 반영 및 AI Workspace API 로그인 보호 확인.
- 운영 수동검수 완료.

---

## Current task — AI Workspace 작업별 상세 답변 개선

**목표**: AI Workspace 질문 답변이 짧은 요약/불릿으로 잘려 보이지 않도록, 고객별 추천 작업의 판단 이유, 다음 액션, 확인 시점, CRM 근거를 구조화해서 보여준다.

### 확인된 상태

- `/reporting/api/ai-workspace/question/`는 기존에 `summary`, `bullets`, `evidence` 중심으로 답변을 내려준다.
- React 답변 UI는 요약을 굵은 문장으로 표시하고, 불릿과 근거를 짧은 목록으로만 렌더링한다.
- OpenAI 프롬프트는 상세 답변을 요구하지만 JSON 스키마에 고객별 실행 항목 필드가 없어 출력이 압축된다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 답변 API에 기존 필드는 유지하고 `answer.actionItems`를 추가한다.
- `actionItems`는 순위, 고객/회사/부서, 우선순위, 판단 이유, 다음 액션, 확인 시점, CRM 근거를 포함한다.
- OpenAI 출력 토큰과 정규화 문자 제한을 늘려 장문 이유/액션이 잘리지 않게 한다.
- OpenAI 실패 fallback도 전체 범위 추천 액션/미완료 후속조치에서 `actionItems`를 생성한다.
- React AI 질문 답변 영역에 작업별 상세 블록을 추가하고 기존 summary/bullets/evidence fallback은 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_answers_global_action_search_without_department reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_normalizes_action_items --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke 확인.

### 현재 상태

- 백엔드 `actionItems` 정규화, OpenAI 프롬프트/토큰 한도 조정, 전체 범위 fallback 상세 작업 생성 완료.
- React AI 질문 답변 상세 블록과 타입/스타일 추가 완료.
- 로컬 집중 테스트, Django checks, frontend 타입체크/빌드 통과.
- 전체 `AIWorkspaceSummaryApiTests` 실행 중 기존 날짜 의존 `weekly_report` 기대값 실패 1건 확인.
- 커밋/푸시 완료: `7b21380 feat: structure ai workspace action answers`.
- 문서 상태 커밋/푸시 완료: `9043770 docs: record ai answer deployment status`.
- Railway `web` 최신 main 자동 배포 완료 확인.
- Railway `sales-note-frontend` 배포 완료: `fd0ac57d-bfa6-4f1c-a673-bbe7a7a01c98` SUCCESS.
- 운영 smoke 완료: `/ai-workspace/` 최신 번들 반영 및 API 로그인 보호 확인.

---

## Current task — 일정 상세 영업노트 작성 및 AI 질문 확장

**목표**: React 일정 상세에서 영업노트를 바로 작성할 수 있게 하고, 영업노트 수정 포맷을 `활동 내용`/`다음 액션` 중심으로 단순화한다. AI Workspace는 전체 부서 범위 질문과 최신 피드백 기반 맥락 판단, 최신 외부 정보 검색 보조를 지원한다.

### 확인된 상태

- `History` 모델에는 legacy 미팅 구조화 필드가 남아 있지만, React 최종 방향은 단순 영업노트 UI다.
- 기존 React 노트 생성 화면은 이미 `활동 내용`과 `다음 액션` 중심이지만, 노트 수정 화면에는 미팅 구조화 필드 5개가 남아 있다.
- 일정 상세 API는 기존 Django `create-from-schedule` 링크만 내려주고, React 일정 상세 안에는 노트 작성 폼이 없다.
- AI 부서 질문 API는 `departmentId`를 필수로 요구하고, 답변 프롬프트도 짧은 답변 중심이다.
- AI 질문 컨텍스트는 최신 `AIWorkspaceActionFeedback`을 포함하지 않아 과거 일정 계획과 최신 완료 답변이 충돌할 수 있다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- `notes_create_api`가 `scheduleId`를 받아 현재 사용자 일정과 고객이 일치할 때 `History.schedule`에 연결하도록 한다.
- 일정 상세 API의 React 노트 작성 링크와 Django fallback 링크를 분리한다.
- React 일정 상세에 일정 연결 영업노트 작성 폼을 추가한다.
- React 영업노트 상세/수정 화면에서 미팅 구조화 필드 5개를 제거하고 서버 저장 시 해당 필드는 비운다.
- 기존 legacy 미팅 필드는 과거 데이터 표시 fallback으로만 사용한다.
- AI 질문 컨텍스트에 최근 노트, 최근 일정, 최근 AI 실행 피드백을 포함한다.
- `departmentId`가 없으면 전체 부서 컨텍스트를 만들어 전체 범위 질문에 답한다.
- 최신 외부 정보가 필요한 질문은 OpenAI Responses API `web_search` 도구를 사용할 수 있게 한다.
- 답변 프롬프트를 단답형에서 판단/이유/다음 액션/타이밍/근거 중심으로 강화한다.

### 검증 계획

- `python manage.py test reporting.tests.NotesSummaryApiTests`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_answers_global_action_search_without_department reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_question_uses_recent_feedback_as_completed_sample_context`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_department_question_answers_last_order_from_delivery_context`
- `python manage.py check`
- `cd frontend; npm run build`
- Playwright CLI local smoke: 일정 상세 노트 작성, 노트 수정 필드 단순화, AI 전체 부서 질문 렌더링/답변 확인.
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke 확인.

### 현재 상태

- 백엔드 일정 연결 노트 생성, 노트 구조화 필드 정리, AI 전역 질문/최신 피드백 컨텍스트 구현 완료.
- React 일정 상세 노트 작성 폼, 노트 수정 단순화, AI 전체/선택 부서 질문 UI 구현 완료.
- 로컬 테스트와 빌드, Playwright CLI smoke 통과.
- 커밋/푸시 완료: `4b4d764 feat: add schedule notes and broaden AI questions`.
- Railway `web` 배포 완료: `80deff19-74e4-4285-9705-dc68580f2c6e` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `27f3892c-87c7-4d51-ac43-777fd235f0b2` SUCCESS.
- 운영 smoke 완료: `/schedules/907/`, `/ai-workspace/` 최신 번들 반영 및 API 로그인 보호 확인.

---

## Current task — React 매출 지표 및 파이프라인 날짜별 금액 보정

**목표**: React 대시보드에서 현재 로그인 범위 기준 당해년도 전체 매출과 현재 분기 매출을 바로 확인할 수 있게 하고, 메인 파이프라인 카드 금액이 고객 전체 누적 매출로 부풀지 않도록 날짜별 기준 금액을 사용한다.

### 확인된 상태

- `/reporting/api/dashboard/`는 이미 `monthlyRevenue`를 납품 일정(`activity_type='delivery'`)의 `DeliveryItem.total_price` 합계로 계산한다.
- 권한 범위는 `_dashboard_scope_users()`를 통해 실무자는 본인, 매니저/관리자는 허용 범위 사용자를 기준으로 잡는다.
- `/reporting/api/pipeline/`는 한 고객의 견적 일정/활동 또는 완료 납품을 여러 날짜에 걸쳐 모두 합산해 카드 금액으로 내려줄 수 있다.
- 그 결과 파이프라인 대표 금액과 단계 합계가 최신 카드 기준 금액이 아니라 누적 매출처럼 보일 수 있다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 대시보드 API에 당해년도 매출과 현재 분기 매출을 기존 월 매출과 같은 납품 일정 기준으로 추가한다.
- API payload에 매출 기간 메타데이터를 함께 내려 React 카드 상세 문구에 사용할 수 있게 한다.
- React `DashboardData` 타입과 fallback 데이터를 확장한다.
- 대시보드 핵심 지표 카드에 `당해년도 전체 매출`, `현재 분기 매출`, `이번 달 매출`을 표시한다.
- 파이프라인 금액 산정은 최신 기준일의 견적/납품만 사용하고, 같은 날짜에 여러 건이 있으면 그 날짜 묶음만 합산한다.
- 파이프라인 상세 패널에는 금액 기준일을 표시한다.
- 대시보드 API 회귀 테스트로 본인 범위/기간별 매출 합계를 검증한다.
- 파이프라인 API 회귀 테스트로 서로 다른 날짜 금액이 누적 합산되지 않는지 검증한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python -m py_compile reporting\funnel_views.py`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke 확인.

### 현재 상태

- 대시보드 API 연/분기 매출 payload 추가 완료.
- React 대시보드 매출 카드 추가 완료.
- 파이프라인 카드 금액을 최신 기준일별 금액으로 보정 완료.
- 파이프라인 상세 기준일 표시 완료.
- 로컬 백엔드 테스트, Django checks, frontend 타입체크/빌드 통과.
- 커밋/푸시 완료: `f011bc9 fix: use dated revenue for pipeline cards`.
- Railway `web` 배포 완료: `bc76b797-eb67-407b-987b-77c81c0d9f8b` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `90d787cc-e7dd-4c03-8366-4d1c4571c9d2` SUCCESS.
- 운영 smoke 완료: `/`, `/dashboard/` 최신 번들 `assets/index-Cw_brbov.js` 반영 및 API 로그인 보호 확인.

---

## Previous task — 납품 품목 할인단가 빈값 합계 0원 긴급 수정

**목표**: `/schedules/903/`에서 견적 품목 선택 적용 후 기준단가가 보이는데도 선결제 영역이 `차감할 납품 품목 합계가 없습니다`로 남는 문제를 해결한다.

### 확인된 상태

- 견적 품목 적용 후 row에는 기준단가가 정상 표시된다.
- 그러나 `할인단가`가 빈칸이면 `parsePositiveFormNumber('')`가 `0`을 반환해, 합계 계산에서 빈 할인단가를 0원 할인단가로 오인한다.
- 그 결과 기준단가가 있어도 `scheduleDeliveryEditRowsTotal()` 결과가 0원이 되어 선결제 차감이 차단된다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 프론트 숫자 파서가 빈 문자열/공백을 `null`로 반환하도록 수정한다.
- 빈 할인단가는 “미입력”으로 유지하고 기준단가를 합계 계산에 사용한다.
- 프론트 타입체크/빌드 후 운영 프론트 재배포한다.

### 현재 상태

- 빈 할인단가가 0원으로 계산되는 프론트 파싱 버그 수정 완료.
- frontend 타입체크/빌드/server.mjs 체크 통과.
- 커밋/푸시 완료: `e3d2d90 fix: treat empty discount unit price as blank`.
- Railway `sales-note-frontend` 배포 완료: `3ce950f1-f99d-4315-9dec-61808c9f1dff` SUCCESS.
- Railway `web` 배포 완료: `1c6a9e90-44cc-4d09-b90b-850d4f15889a` SUCCESS.
- 운영 smoke 완료: `/schedules/903/` 최신 번들 및 빈값 파싱 guard 반영 확인.

### 검증 계획

- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/schedules/903/` smoke 확인.

---

## Previous task — 견적 선택 적용 후 선결제 합계 0원 긴급 수정

**목표**: `/schedules/903/`에서 견적 품목을 선택 적용했는데도 선결제 영역이 `차감할 납품 품목 합계가 없습니다`로 남는 문제를 해결한다.

### 확인된 상태

- 견적 품목 선택 적용 자체는 되었지만, 가져온 품목의 단가가 0원/빈 값이면 프론트 납품 합계가 계속 0원으로 계산된다.
- 일부 레거시 견적 품목은 `unit_price`가 비어 있고 `total_price`만 남아 있을 수 있다.
- 기존 quote-items API는 품목별 총액/잔여액을 내려주지 않고, `unit_price`가 없으면 `unitPrice: 0`을 내려줘 프론트가 금액을 복원할 수 없다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 백엔드 quote-items API에서 품목별 `totalPrice`, `remainingAmount`, `quotedAmount`, `deliveredAmount`를 내려준다.
- `unit_price`가 없는 레거시 품목은 `total_price / quantity / 1.1`로 단가를 복원해 내려준다.
- 프론트는 견적 품목의 단가가 0이어도 품목 총액 또는 단일 견적 잔여금액으로 단가를 복원해 납품 편집 row를 만든다.
- 레거시 총액만 있는 견적 품목 회귀 테스트를 추가한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke 확인.

### 현재 상태

- 백엔드 quote-items API 품목별 총액/잔여액 payload 확장 완료.
- `unit_price`가 없는 레거시 품목의 단가 복원 구현 완료.
- 프론트 견적 품목 적용 시 총액 기반 단가 fallback 구현 완료.
- 로컬 백엔드 테스트, Django checks, frontend 타입체크/빌드 통과.
- 커밋/푸시 완료: `eba7dc6 fix: recover quote item prices for prepayment caps`.
- Railway `web` 배포 완료: `1b7c3300-3733-4890-9614-9e5a5483b276` SUCCESS.
- Railway `sales-note-frontend` 배포 완료: `c9a04d49-b003-4c67-8d6c-d05c1f3a68f6` SUCCESS.
- 운영 smoke 완료: `/schedules/903/` 최신 번들 및 quote-items API 로그인 보호 확인.

---

## Previous task — 납품 선결제 차감 품목 합계 0원 표시 긴급 수정

**목표**: React 일정 상세 `/schedules/903/`에서 선결제 차감 시 납품/견적 품목이 아직 반영되지 않았는데도 `품목 상한 ₩0 · 최대 차감 ₩0`으로 표시되어 사용자가 품목을 못 가져온 것으로 보이는 문제를 해결한다.

### 확인된 상태

- 선결제 목록은 정상 로드되지만, 납품 품목 편집 rows의 합계가 0원이면 선결제 차감 한도도 0원으로 계산된다.
- 현재 UI는 품목 합계가 0원이어도 선결제 row 체크와 차감 입력을 열어 사용자가 정상 차감 가능 상태로 오해할 수 있다.
- 견적 품목을 가져온 뒤에만 선결제 차감 한도를 계산할 수 있으므로, 품목 합계 0원 상태에서는 선결제 선택을 차단하고 견적 품목 불러오기 CTA를 보여줘야 한다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 납품 품목 합계가 0원일 때 선결제 차감 row 선택/금액 입력/전체 차감 버튼을 비활성화한다.
- 같은 상태에서 “먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하라”는 안내와 `견적 품목 불러오기` 버튼을 선결제 영역에 표시한다.
- 저장 시에도 선결제 사용이 켜져 있는데 납품 품목 합계가 0원이면 서버 요청 전 오류로 차단한다.
- 견적 품목을 가져오면 기존 계산식으로 즉시 품목 상한/최대 차감/실결제 금액이 갱신되게 유지한다.

### 검증 계획

- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/schedules/903/` smoke 확인.

### 현재 상태

- 납품 품목 합계 0원 상태에서 선결제 row 선택/차감 입력/전체 차감 버튼 비활성화 구현 완료.
- 선결제 영역에 `견적 품목 불러오기` CTA 추가 완료.
- 저장 전 선결제 차감 합계 0원 차단 구현 완료.
- frontend 타입체크/빌드/server.mjs 체크/diff 체크 통과.
- 커밋/푸시 완료: `c6adaea fix: require delivery items before prepayment deduction`.
- Railway `sales-note-frontend` 배포 완료: `60a43508-8e09-465a-adbf-7e85677b0afd` SUCCESS.
- 운영 smoke 완료: `/schedules/903/` 최신 JS/CSS 번들 및 새 안내 문구 반영 확인.

---

## Previous task — 견적 품목 불러오기 API 502 긴급 수정

**목표**: React 일정 상세 `/schedules/903/`의 `견적 품목 불러오기`에서 `/reporting/api/followups/<id>/quote-items/` 호출이 502로 실패하는 문제를 해결한다.

### 확인된 상태

- React는 `loadFollowupQuoteItems()`에서 `/reporting/api/followups/<followupId>/quote-items/`를 호출하고, JSON이 아닌 502 응답이면 `Quote items API unavailable: 502`를 표시한다.
- 운영 익명 smoke에서는 프론트 프록시와 백엔드 직접 URL 모두 302 로그인 리다이렉트가 정상이라 프록시 전체 장애는 아니다.
- 해당 Django API는 같은 부서의 견적 일정을 순회하면서 각 견적 일정마다 납품 반영 수량을 별도 DB 조회로 계산한다.
- 특정 부서/고객에 견적/납품 데이터가 많으면 요청 시간이 길어져 프론트 프록시 또는 Railway edge에서 502로 보일 수 있다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 견적 일정 목록 전체에 대해 원 견적 품목별 납품 반영 수량을 bulk query로 한 번에 계산하는 helper를 추가한다.
- 기존 단일 일정 계산 helper는 유지해 다른 저장/검증 경로의 동작을 보존한다.
- `followup_quote_items_api`만 bulk helper를 사용하도록 바꿔 다중 견적/부분 납품 계산을 빠르게 처리한다.
- 여러 completed 견적의 legacy 납품 매칭도 기존 의미를 유지하되 bulk 계산으로 처리한다.
- API가 정상 JSON을 반환하도록 회귀 테스트를 추가한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 API smoke 확인.

### 현재 상태

- bulk progress helper 구현 완료.
- `followup_quote_items_api`가 다중 견적 일정의 납품 반영 수량을 bulk 계산하도록 변경 완료.
- 로컬 회귀 테스트 및 Django checks 통과.
- 커밋/푸시 완료: `f424ebc fix: bulk load quote item progress`.
- Railway `web` 배포 완료: `768f6950-9790-4ea5-a92c-a0fa5de01d27` SUCCESS.
- 운영 익명 smoke 완료: `/schedules/903/` 200, quote-items API 302 login redirect.

---

## Previous task — 일정 상세 납품품목 선결제 차감 + AI 액션 오류 긴급 수정

**목표**: React 일정 상세 `/schedules/<id>/`에서 납품품목을 저장할 때 같은 고객/부서의 선결제를 선택해 잔액에서 차감할 수 있게 한다. 이어서 AI Workspace 부서 상세 액션에서 `action_not_found`가 뜨는 경로를 막고, 중복 실행 패널을 제거한다. 납품 일정의 `견적 불러오기`는 여러 견적을 한 번에 선택해 가져올 수 있게 한다.

### 추가 긴급 요청 — 선결제 차감 상한 안내

- `/schedules/903/` 납품 품목 편집에서 선결제 차감 금액을 직접 입력할 때 납품 품목 금액 상한과 입력 후 남은 금액을 즉시 보여준다.
- `전체 차감` 버튼을 추가해 해당 선결제에서 입력 가능한 최대 차감액을 자동 입력한다.
- 여러 선결제를 동시에 선택해도 합산 차감액이 납품 합계를 넘지 않도록 프론트 저장 전 검증한다.
- 구현/빌드/운영 배포 완료: `70d9eb3`, frontend `6bf4a51e-fe21-4db1-a6fb-707b294c08c3`, web `a691e80d-1776-4488-89e3-10aa8ab41622`.

### 확인된 상태

- `Schedule`에는 이미 `use_prepayment`, `prepayment`, `prepayment_amount` 필드가 있다.
- `Prepayment`와 `PrepaymentUsage` 모델 및 일정 수정 API의 선결제 적용/복구 헬퍼가 이미 존재한다.
- React 일정 상세의 "일정 수정" 폼에는 선결제 사용 UI가 있지만, "납품 품목" 편집 폼에는 선결제 선택/차감 UI가 없다.
- 납품품목 저장 API `/reporting/api/schedules/<id>/delivery-items/update/`는 품목 저장과 견적 일정 완료 처리는 하지만 선결제 적용 요청을 처리하지 않는다.
- AI Workspace 초안/답변 API는 전역 action queue를 다시 구성한 뒤 action id를 찾는데, 부서 상세에서만 보이는 하위순위 액션은 전역 queue 제한 때문에 누락될 수 있다.
- 기존 직접 재구성 fallback은 `email_waiting:<id>`만 지원해 `quote:<id>`, `followup:<id>` 등에서 `action_not_found`가 발생할 수 있다.
- `/ai-workspace/?department_id=14` 형태의 부서 상세에서 왼쪽 실행 목록과 오른쪽 보조 패널의 PainPoint/추천 항목이 중복 노출된다.
- 일정 상세 `견적 불러오기`는 기존 단일 적용 버튼만 있어 여러 견적을 한 번에 가져올 수 없다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- 기존 `_schedules_apply_prepayments()` / `_schedules_restore_prepayments()` 헬퍼를 납품품목 저장 API에서도 재사용한다.
- 납품품목 저장 payload에 `usePrepayment`와 `prepayments` 선택 목록을 받도록 확장한다.
- React 납품품목 편집 폼에 선결제 차감 체크, 선결제 목록, 차감 금액 입력, 납품 합계/차감/실결제 요약을 추가한다.
- 기존 일정 수정 폼의 선결제 로직, 권한, 같은 부서 선결제 조회 정책은 유지한다.
- 견적 일정(`activity_type=quote`) 품목 편집에는 선결제 차감 UI를 노출하지 않는다.
- AI Workspace action id 직접 재구성 fallback을 `quote`, `quote_schedule`, `delivery`, `followup`, `painpoint`, `weekly_report`까지 확장한다.
- 이미 완료/숨김 처리된 action은 기존 feedback 숨김 정책으로 계속 차단한다.
- AI Workspace 오른쪽 보조 실행/PainPoint 패널은 제거하고 중앙 실행 목록만 남긴다.
- `견적 불러오기` 카드에 체크박스를 추가하고 선택한 여러 견적을 한 번에 적용한다.

### 검증 계획

- 납품품목 저장 API가 품목 저장과 동시에 선결제를 차감하고, 재저장 시 기존 차감을 복구 후 재적용하는 회귀 테스트 추가.
- 부서 상세에는 보이지만 전역 queue에는 밀려난 견적/후속 액션의 초안 생성과 현장 답변 저장이 200으로 처리되는 회귀 테스트 추가.
- 부서 상세에는 보이지만 전역 queue에는 밀려난 PainPoint 액션의 현장 답변 저장이 200으로 처리되는 회귀 테스트 추가.
- `python -m py_compile reporting\views.py reporting\tests.py`
- 관련 일정/선결제/AI Workspace 테스트 실행.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke 확인.

### 현재 상태

- AI 워크스페이스 진행 중 변경은 `wip-ai-workspace-global-question` stash로 보관했다.
- 기존 선결제 헬퍼와 React 일정 상세 구조를 확인했다.
- React 일정 상세 납품품목 선결제 UI/API 구현 완료.
- AI Workspace `action_not_found` fallback 확장 완료.
- AI Workspace 오른쪽 중복 실행 패널 제거 완료.
- React 일정 상세 견적 불러오기 다중 선택 UI 구현 완료.
- DB 모델 변경과 migration 없음 확인.
- 로컬 API 테스트, 타입체크, 빌드, Playwright smoke 통과.
- 커밋/푸시 완료: `4f01d95`, `3b04d91`.
- Railway `web`, `sales-note-frontend` 운영 배포 및 익명 smoke 완료.

---

## Completed task — React CRM legacy frontend migration documentation

**목표**: 기존 Django 레거시 메뉴를 React CRM으로 순차 이관하고, 운영 검수 후 Django 템플릿 프론트를 제거하기 위한 장기 실행 계획을 문서화한다.

### 확인된 상태

- Django 레거시 사용자 메뉴의 원천은 `reporting/templates/reporting/base.html` 사이드바이다.
- React에는 대시보드, 고객, 파이프라인, 영업노트, 일정, 메일, 주간보고, 서류, 제품, 선결제, AI가 이미 있다.
- React에 아직 없는 주요 레거시 메뉴는 ToDo/업무하달, 관리자/직원관리, 리포트, 프로필, 명함 관리이다.
- 기존 지침상 Django 템플릿은 React 대체 구현, Railway 배포, 운영 수동 검수 완료 전 삭제하지 않는다.
- 이번 작업은 문서화만 수행하므로 DB 모델 변경과 Railway 배포는 필요 없다.

### 구현 계획

- `REACT_MIGRATION_PLAN.md`를 새로 만들어 장기 전환 계획의 단일 기준 문서로 보관한다.
- Django 레거시 메뉴, 기존 route, React 목표 route, 1차 작업을 표로 정리한다.
- React 권한 기반 내비게이션, API boundary, backend로 남겨야 하는 route, wave별 이관 순서, 삭제 gate를 명시한다.
- 다음 구현 작업은 Wave 1 누락 메뉴 중 ToDo/업무하달 React v1로 제안한다.

### 검증 계획

- `git diff --check`
- 문서 diff 확인
- 런타임 변경 없음과 배포 불필요 여부 확인

### 현재 상태

- `REACT_MIGRATION_PLAN.md` 작성 완료.
- `git diff --check` 통과.
- 런타임 변경 없음. Railway 배포 불필요.
- `AGENT_REPORT.md` 기록, 커밋/푸시 완료.
- Commit: `debc3f4 docs: add React migration plan`

## Completed task — 견적서 생성 텍스트 잘림 방지 + 내부직원 참조 선택 UX

**목표**: 견적서/거래명세서/납품서 생성 시 엑셀 템플릿의 치환 텍스트가 셀 폭보다 길어 PDF 또는 XLSX에서 잘려 보이지 않도록 한다. React 메일 작성 화면의 내부직원 참조는 긴 전체 이메일 목록 노출 대신 검색해서 한 명씩 선택하거나 전체 선택할 수 있게 한다.

### 확인된 상태

- 서류 생성 경로는 `reporting:generate_document_pdf_format`이며 실제 구현은 `reporting.views.generate_document_pdf`이다.
- 기존 `_expand_xlsx_item_note_rows()`는 `품목N_적요/비고` 변수만 줄바꿈과 행 높이를 보정한다.
- `업체명`, `부서명`, `품목명`, `규격`, `설명`, `메모`, `기타사항`처럼 다른 텍스트 변수가 좁은 셀에 들어가면 잘릴 수 있다.
- React 메일 작성 화면은 `create.internalCcEmails` 전체 이메일 목록을 체크박스 설명으로 그대로 노출한다.
- 현재 내부직원 참조는 전체 포함 여부만 있고, 특정 직원만 검색/선택하는 흐름이 없다.
- DB 모델 변경과 migration은 필요 없다.

### 구현 계획

- XLSX ZIP XML을 직접 수정하는 기존 방식을 유지해 이미지/서식을 최대한 보존한다.
- 치환 대상 변수 전체를 분석하는 일반 헬퍼를 추가하고, 셀 폭보다 긴 텍스트 또는 줄바꿈 포함 텍스트는 `wrapText`와 `vertical=top` 스타일을 적용한다.
- 병합 셀은 병합 범위의 합산 폭을 기준으로 행 높이를 계산한다.
- 기존 `품목N_적요/비고` 전용 헬퍼는 호환 wrapper로 유지한다.
- 견적서 생성 흐름에서 새 일반 헬퍼를 호출한다.
- 메일 API는 내부직원 참조 후보를 `{id, name, email}` 연락처 목록으로 내려준다.
- 메일 발송 API는 `include_internal_cc` 전체 참조와 `internal_cc_emails` 선택 참조를 모두 지원한다.
- React 메일 작성/답장 패널은 내부직원 검색, 선택 칩, 전체 참조 버튼을 제공하고 긴 목록은 최대 8개만 표시한다.

### 검증 계획

- 텍스트 잘림 방지 헬퍼 회귀 테스트 추가.
- 내부직원 전체 참조 기존 동작과 선택 참조 회귀 테스트 추가.
- `python -m py_compile reporting\views.py reporting\tests.py`
- 관련 테스트 클래스 또는 개별 테스트 실행.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`

### 현재 상태

- 백엔드/React 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `c498758 fix: wrap quote text and select internal cc`
- Railway `web`: `65a472f0-5315-49e2-8945-05cb01e82cd8` SUCCESS
- Railway `sales-note-frontend`: `4c2e3ba7-1b97-4d48-8ac7-9b817b4c9b71` SUCCESS
- 운영 smoke OK:
  - 제공된 `/mailbox/?compose=1&schedule_id=899&followup_id=4...` URL 200, 최신 frontend assets 로드 확인.
  - `/reporting/login/` 200.
  - anonymous `/reporting/api/mailbox/?schedule_id=899` 302 login redirect.
- 사용자 수동 검수 완료: 2026-05-13 운영 검수 완료 확인.
- 다음 행동: 사용자가 명시적으로 요청하는 다음 CRM 작업을 진행한다.

---

## Completed task — 견적 일정 연결 납품 노트 금액 보정

**목표**: 운영 `/notes/741/`처럼 `delivery_schedule` 노트가 실제 납품 일정이 아니라 견적 일정에 연결된 경우, 견적 일정의 전체 품목 합계가 납품 금액으로 표시되지 않게 한다. 같은 견적의 실제 납품 일정이 있으면 납품 일정 품목만 표시하고, 앞으로 견적 품목 저장 시 납품 노트가 생성/갱신되지 않게 한다.

### 확인된 상태

- 운영 `History 741`은 `action_type=delivery_schedule`이지만 연결된 `Schedule 880`은 `activity_type=quote`이다.
- `Schedule 880`에는 견적 품목 2개가 있고, `History 741.delivery_amount`에는 두 품목 합계 402,600원이 저장되어 있다.
- 같은 고객의 실제 납품 일정 `Schedule 883`에는 `56722` 1개, 33,000원만 저장되어 있고 `History 743`도 33,000원이다.
- 현재 `_history_effective_delivery_summary()`는 연결 일정이 `delivery`일 때만 실제 일정 품목을 우선하므로, quote 일정에 잘못 연결된 납품 노트는 stale `History.delivery_amount`를 그대로 표시한다.
- 모델/마이그레이션 변경은 필요 없다.

### 구현 계획

- `delivery_schedule` 노트가 quote 일정에 연결된 경우, 같은 고객의 실제 납품 일정 중 견적 품목과 연결되었거나 품목 정체성이 일치하는 납품 품목만 요약에 사용한다.
- 실제 납품 품목을 찾지 못하면 quote 일정의 전체 견적 품목을 납품으로 표시하지 않고 0원/빈 품목으로 처리한다.
- React 일정 품목 저장 API와 legacy 일정 품목 저장 view가 quote 일정 저장 시 `delivery_schedule` History를 생성/갱신하지 않도록 제한한다.
- 기존 납품 일정(`activity_type=delivery`)의 History 동기화와 `/reporting/*` route는 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- 관련 회귀 테스트 추가 후 `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build` (프론트 변경이 없더라도 배포 smoke 기준 확인)
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포, 운영 `/notes/741/` 및 로그인 보호 smoke 확인

### 현재 상태

- 구현, 로컬 검증, 커밋/푸시, Railway `web` 배포 완료.
- 운영 DB 읽기 전용 계산 확인: `History 741` 보정 결과 `56722: 1EA (33,000원)`.
- DB 모델 변경 없음.
- Runtime commit: `7e6a6c5 fix: correct quote-linked delivery note amounts`
- Railway `web`: `ee0976c6-2542-4c87-b8d8-dcfd58f62dee` SUCCESS
- Railway `sales-note-frontend`: 변경 없음, 기존 `de5f5a66-4ff8-4558-812c-1b74f39c2eab` SUCCESS 유지
- 운영 smoke OK:
  - `/notes/741/` 200
  - anonymous `/reporting/api/notes/741/` 401 login-required JSON
  - `/reporting/login/` 200
- 사용자 수동 검수 완료: 2026-05-13 운영 `/notes/741/` 검수 완료 확인.
- 다음 행동: 사용자가 명시적으로 요청하는 다음 CRM 작업을 진행한다.

---

## Previous task — 납품 견적 불러오기 후 원 견적 일정 자동 완료 복구

**목표**: 납품 일정에서 `견적 불러오기`로 품목을 가져와 저장하면, 불러온 원본 견적 일정이 자동으로 `완료됨` 상태가 되도록 React 일정 상세 화면과 Django 레거시 일정 등록/수정 화면을 함께 보강한다.

### 확인된 상태

- `/reporting/api/followups/<id>/quote-items/`는 견적 선택지에 `scheduleId`/`schedule_id`를 내려준다.
- React 납품 품목 저장 요청은 원본 견적 일정 ID를 `/reporting/api/schedules/<id>/delivery-items/update/`로 전달하지 않아 백엔드가 완료 처리 대상을 알 수 없다.
- Django 레거시 일정 폼에는 `from_quote_schedule_id` 히든 필드가 있으나, 견적 선택 JS가 camelCase `scheduleId` fallback을 보장하지 않아 값이 비는 경로가 있다.
- 기존 DB 모델로 해결 가능하며 모델/마이그레이션 변경은 필요 없다.

### 구현 계획

- 납품 품목 저장 API가 `sourceQuoteScheduleIds`와 item-level `sourceQuoteScheduleId`를 받아 원본 견적 일정을 완료 처리하게 한다.
- 완료 처리 대상은 본인이 작성한 견적 일정이며, 납품 일정의 동일 고객 또는 동일 부서/연구실 견적으로 제한한다.
- React 견적 불러오기 적용 시 각 납품 행에 원본 견적 일정 ID를 보존하고 저장 payload에 함께 보낸다.
- Django 레거시 일정 폼의 견적 선택 JS가 `schedule_id`, `scheduleId`, `id`를 모두 인식해 히든 필드를 채우게 한다.
- 견적 불러오기 API는 완료된 견적 일정을 다시 선택지로 노출하지 않도록 `scheduled` 견적만 반환한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/<id>/`, `/reporting/login/`, 관련 API smoke check

### 현재 상태

- 백엔드/React/레거시 템플릿 수정, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `439fe00 fix: complete imported quote schedules`
- Railway `web`: SUCCESS (runtime commit deployed; latest web deployment success verified after docs-only commit)
- Railway `sales-note-frontend`: `2ae20d51-54bf-415b-b6c4-1a094503e8d2` SUCCESS
- 운영 smoke OK:
  - `/schedules/calendar/` 200 with `assets/index-5Pldkc-g.js`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/schedules/999999/` 401 login-required JSON
- 다음 행동: 사용자가 운영에서 테스트 데이터로 견적 불러오기 후 원본 견적 일정 완료 처리를 수동 검수한다.

---

## Previous task — React 개인 일정 등록/수정 API 전환

**목표**: React `/schedules/calendar/`에서 개인 일정을 Django 레거시 화면으로 이동하지 않고 등록, 수정, 삭제할 수 있게 한다. 기존 `/reporting/personal-schedules/*` 화면과 `/reporting/*` route는 fallback으로 보존한다.

### 확인된 상태

- React 캘린더는 고객 일정 등록/수정/삭제/상태변경을 이미 처리한다.
- 개인 일정은 캘린더 목록에 함께 표시되지만 `canEdit=false`로 내려오며, 등록은 Django 링크로 이동한다.
- 기존 `PersonalSchedule` 모델과 legacy create/edit/delete view가 있으므로 DB 모델 변경은 필요 없다.
- React 개인 일정 API는 owner-only 조작으로 제한하고, manager/동료는 기존처럼 조회만 가능하게 하는 것이 안전하다.

### 구현 계획

- `/reporting/api/personal-schedules/create/`, detail, update, delete JSON API를 추가한다.
- 개인 일정 생성 시 기존 legacy 흐름처럼 `History` 메인 기록을 생성한다.
- 캘린더 payload의 개인 일정 item에 owner-only `canEdit`, `deleteHref`, `djangoEditHref`를 제공한다.
- 캘린더 `create` payload에 개인 일정 등록 submit URL과 Django fallback URL을 추가한다.
- React 캘린더 선택일 패널에 개인 일정 등록 폼을 추가한다.
- 개인 일정 카드의 수정/삭제 버튼을 React API로 연결하고, 저장/삭제 후 월간 데이터를 다시 불러온다.
- 고객 일정 흐름, 상태 변경, 기존 Django fallback 링크는 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\personal_schedule_views.py reporting\tests.py`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/`, `/reporting/login/`, `/reporting/api/schedules/calendar/` smoke check

### 현재 상태

- 백엔드/React 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `a4b30a4 feat: manage personal schedules in calendar`
- Railway `web`: `391d16e5-dbd8-4d26-a05d-ec18f71ce972` SUCCESS
- Railway `sales-note-frontend`: `d5230ae9-011f-45db-a5a6-b838e01af236` SUCCESS
- 운영 smoke OK:
  - `/schedules/calendar/` 200 with `assets/index-sevkHjR9.js`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/schedules/calendar/` 401 login-required JSON
  - anonymous `/reporting/api/personal-schedules/999999/` 401 login-required JSON
- 로컬 브라우저 smoke 완료:
  - 테스트 계정 `codex_calendar_smoke`와 테스트 개인 일정으로 등록/수정/삭제 확인.
  - 로컬 테스트 계정, 회사, 개인 일정 데이터 삭제 완료.
- 다음 행동: 사용자가 운영에서 테스트 데이터로 개인 일정 등록/수정/삭제를 수동 검수한다.

---

## Previous task — React 일정 캘린더 고급 조작 parity

**목표**: React 일정 캘린더에서 고객 일정을 조회만 하지 않고, 선택한 날짜 기준으로 고객 일정 등록, 상세 수정, 삭제, 상태 변경까지 처리할 수 있게 한다. Django 캘린더와 `/reporting/*` 레거시 화면은 fallback으로 보존한다.

### 확인된 상태

- `/schedules/calendar/` React 화면은 월간 조회, 날짜 선택, 상태 변경, 상세/보고/Django 링크를 제공한다.
- `/reporting/api/schedules/calendar/`는 일정 목록과 필터 payload를 제공하지만, 빠른 등록에 필요한 `create` 설정은 내려주지 않는다.
- 고객 일정 등록/수정/삭제 API와 React 상세 화면의 수정 폼 로직은 이미 존재한다.
- 개인 일정 등록/수정은 아직 Django 레거시 화면을 사용한다. 이번 범위에서는 고객 일정 캘린더 조작을 React 안에서 닫고, 개인 일정은 기존 링크를 유지한다.
- DB 모델 변경 없이 API payload 보강과 React 캘린더 UI 상태/폼 추가로 구현 가능하다.

### 구현 계획

- 캘린더 API에 고객 일정 빠른 등록 설정을 추가한다.
  - `canCreate`, `submitUrl`, 활동 유형, 담당 고객 목록을 일정 목록 API와 동일한 권한 기준으로 제공한다.
- 캘린더 선택 날짜 패널에서 React 고객 일정 등록 폼을 열고, 선택 날짜를 기본 방문일로 채운다.
- 캘린더 일정 카드에서 본인 고객 일정은 React 수정 패널을 열 수 있게 한다.
  - 기존 상세 API를 불러와 수정 권한, 상태/활동 유형/고객 옵션, submit URL을 그대로 사용한다.
  - 수정 저장 후 캘린더 월간 데이터를 다시 불러온다.
- 캘린더 일정 카드에서 본인 고객 일정은 React 삭제 버튼을 제공한다.
  - 기존 AJAX 삭제 엔드포인트를 사용하고, 관련 활동 기록 삭제 경고를 유지한다.
- 상태 변경/등록/수정/삭제 성공 및 오류 메시지를 캘린더 패널 안에서 표시한다.
- 개인 일정은 이번 단계에서 기존 Django 등록/상세/수정 링크를 fallback으로 유지한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/`, `/reporting/login/`, `/reporting/api/schedules/calendar/` smoke check

### 현재 상태

- 백엔드/React 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `4f3fe64 feat: manage schedules from calendar`
- Railway `web`: `80ec251c-6984-4563-815d-81be2235a253` SUCCESS
- Railway `sales-note-frontend`: `90e461be-5ff3-4617-b6c3-dc499bea6920` SUCCESS
- 운영 smoke OK:
  - `/schedules/calendar/` 200 with `assets/index-BvRdieLP.js` / `assets/index-DC8BCCea.css`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/schedules/calendar/` 401 login-required JSON
- 운영 수동 검수 완료(2026-05-13):
  - 테스트 고객 `466`과 테스트 일정 `886`으로 캘린더 고객 일정 등록/수정/삭제를 확인했다.
  - 등록 후 카드와 월간 집계에 반영됐고, 수정 후 카드 메모가 갱신됐으며, 삭제 후 캘린더 API에서 사라지는 것을 확인했다.
  - 테스트 일정 `886`과 테스트 고객 `466`은 삭제 완료.

---

## Previous task — 일정 메일 거래명세서 자동첨부 및 자동첨부 제거

**목표**: 일정에서 메일을 보낼 때 견적 일정은 견적서 PDF, 납품 일정은 거래명세서 PDF를 자동 첨부하고, React 메일 작성 화면에서 사용자가 자동 첨부 예정 문서를 발송 전에 제거할 수 있게 한다.

### 확인된 상태

- 현재 `mailbox_api_send`와 Django 일정 메일 발송은 `schedule_id`가 있는 경우에도 견적 일정의 견적서 PDF만 자동 첨부한다.
- 거래명세서 PDF 생성과 `DocumentGenerationLog` 등록 기능은 이미 존재한다.
- React 일정 상세의 `메일 발송` 링크는 `/mailbox/?compose=1&schedule_id=...`로 이동하지만 메일 작성 API payload에는 자동 첨부 예정 문서 목록이 없다.
- 현재 React 메일 작성 화면은 업로드 첨부파일만 제거할 수 있고, 견적서 자동 첨부는 안내 문구만 보여준다.
- DB 모델 변경 없이 백엔드 자동첨부 타입 확장, create payload 보강, React 제외 목록 전송으로 구현 가능하다.

### 구현 계획

- 백엔드 자동첨부 로직을 문서 타입 단위로 일반화한다.
  - 견적 일정: `quotation` PDF 자동 첨부
  - 납품 일정: `transaction_statement` PDF 자동 첨부
  - 등록 PDF가 있으면 기존 파일을 첨부하고, 없으면 발송 시 PDF를 생성한다.
- React 메일함 create payload에 `schedule_id` 기준 자동 첨부 예정 목록을 내려준다.
- React 메일 작성 패널에 자동 첨부 예정 문서 목록을 표시하고, 문서별 제거 버튼을 제공한다.
- 제거한 자동 첨부는 `excluded_auto_attachment_keys`로 발송 API에 전달해 백엔드가 해당 등록 문서 또는 생성 예정 문서를 제외한다.
- Django legacy 일정 메일 폼에도 자동 첨부 체크박스를 추가해 견적서/거래명세서 자동첨부를 발송 전에 해제할 수 있게 한다.

### 검증 계획

- `python -m py_compile reporting\gmail_views.py reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_returns_documents_for_delivery_and_quote reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_splits_quotation_documents_by_quote_group --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/882/`, `/mailbox/`, `/reporting/login/` smoke check

### 현재 상태

- 백엔드/React 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `7033da7 feat: auto attach schedule documents in mail`
- Railway `sales-note-frontend`: `1eb864cd-e715-488b-b13d-2391ee1821a3` SUCCESS
- Railway `web`: `f29edf24-7a3f-4d91-af7b-4641211bec7e` SUCCESS
- 운영 smoke OK:
  - `/mailbox/` 200 with `assets/index-C6-0bFJk.js` / `assets/index-BFbWQzPN.css`
  - `/schedules/882/` 200 with `assets/index-C6-0bFJk.js` / `assets/index-BFbWQzPN.css`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/schedules/882/` 401 login-required JSON
- 운영 수동 검수 완료(2026-05-13):
  - 테스트 고객 `466`, 견적 테스트 일정 `884`, 납품 테스트 일정 `885`를 생성해 확인했다.
  - 납품 일정 메일 작성 화면에서 `거래명세서 PDF 자동 생성` 자동첨부 후보와 제거 후 `자동 첨부를 모두 제외했습니다.` 상태를 확인했다.
  - 견적 일정 메일 작성 화면에서 `견적서 PDF 자동 생성` 자동첨부 후보와 제거 후 제외 상태를 확인했다.
  - 실제 메일 발송은 하지 않았다.
  - 테스트 일정 `884`, `885`와 테스트 고객 `466`은 삭제 완료.

---

## Previous task — 제품 삭제 차단 품목 개별 대체 처리

**목표**: React 제품관리에서 사용 중인 제품 삭제가 차단됐을 때 제품 하나 전체를 한 번에 대체하지 않고, 견적/납품에 사용된 개별 품목을 사용자에게 보여준 뒤 각 품목마다 어떤 제품으로 대체할지 선택해 하나씩 옮기게 한다. 마지막 참조가 옮겨져 데이터 무결성이 확인되면 원제품을 삭제한다.

### 확인된 상태

- 현재 React 제품 삭제는 사용 중인 제품이 차단되면 제품 단위 대체 제품을 하나 선택하고, 서버가 해당 제품의 모든 `DeliveryItem`/`QuoteItem` 참조를 한 번에 이동한다.
- 참조가 많은 제품은 처리 시간이 길고, 사용자가 품목별로 대체 제품을 다르게 선택할 수 없다.
- 기존 `products_bulk_delete_api`는 차단 결과에 참조 상세 목록을 내려주지 않는다.
- DB 모델 변경 없이 차단 payload와 개별 참조 이동 API를 추가하면 된다.

### 구현 계획

- 제품 삭제 차단 결과에 참조 목록을 추가한다.
  - React 일정 품목(`DeliveryItem`)은 일정 ID, 활동 유형, 고객명, 품목명, 수량, 단위, 견적서 구분을 표시한다.
  - 레거시 견적 품목(`QuoteItem`)은 견적 ID/번호, 고객명, 품목명, 수량을 표시한다.
- 제품 단위 전체 대체 삭제 UI를 제거하고, 참조 행별 대체 제품 선택 + `이 품목 대체` 버튼으로 바꾼다.
- 새 API `/reporting/api/products/replace-reference/`를 추가해 참조 1건만 대체 제품으로 옮긴다.
- 참조 1건 이동 후 원제품에 참조가 더 남아 있으면 차단 상태를 다시 내려주고, 참조가 없으면 원제품을 삭제한다.
- 기존 제품 일괄 삭제는 사용 중인 제품을 계속 차단만 하고, 대체 처리는 새 개별 API로만 진행한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.ProductManagementReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/products/`, `/reporting/login/` smoke check

### 현재 상태

- 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 예정 없음.

---

## Previous task — React 납품 견적 불러오기 구분별 선택 보강

**목표**: React 납품 일정에서 `견적 불러오기`를 사용할 때, 같은 견적 일정 안에 `보상판매`, `수리`처럼 여러 견적서 구분이 있으면 전체 품목을 한 번에 가져오지 않고 사용자가 가져올 견적서를 선택할 수 있게 한다.

### 확인된 상태

- 현재 `/reporting/api/followups/<id>/quote-items/`는 견적 일정 하나를 선택지 하나로 반환한다.
- 각 품목에는 `quoteGroup`/`quoteGroupLabel`이 이미 내려가지만, 상위 견적 선택지는 구분별로 나뉘지 않는다.
- React UI는 여러 견적 일정 선택 카드는 표시하지만, 같은 일정 안의 여러 견적서 구분은 한 카드 안에 묶어 표시하고 `적용` 시 모든 품목을 가져온다.
- DB 모델 변경 없이 API payload와 React 선택 UI만 보강하면 된다.

### 구현 계획

- 견적 품목 API에서 한 견적 일정의 품목을 `quote_group`별로 묶어 선택지를 만든다.
- 선택지 payload에 `optionId`, `quoteGroup`, `quoteGroupLabel`을 추가하고, 각 선택지의 `items`와 `expectedRevenue`는 해당 구분 품목만 포함한다.
- React API 타입/정규화 함수에 선택지 식별자와 구분 라벨을 추가한다.
- React 견적 불러오기 카드에 견적서 구분 라벨과 고객/일정 정보를 함께 표시하고, 같은 일정 안의 여러 구분도 각각 선택할 수 있게 한다.
- 적용 메시지도 선택한 견적서 구분을 명확히 표시한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/882/`, `/reporting/login/` smoke check

### 현재 상태

- 구현/로컬 검증/커밋/푸시/운영 배포/익명 smoke 완료.
- DB 모델 변경 없음.
- Runtime commit: `6c041e4 fix: split quote imports by group`
- Railway `web`: `50a1e21c-1197-4a28-83fd-007b3129f740` SUCCESS
- Railway `sales-note-frontend`: `3fd13701-e681-4fed-8614-5c783993ad10` SUCCESS
- 운영 smoke OK:
  - `/schedules/882/` 200 with `assets/index-B6kDhHX8.js` / `assets/index-2AirpMI9.css`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/schedules/882/` 401 login-required JSON
  - anonymous `/reporting/api/followups/1/quote-items/` 302 login redirect
- 다음 행동: 사용자가 운영에서 수동 검수한다. 검수 결과 확인 전에는 다음 구현 작업을 시작하지 않는다.

---

## Previous task — React 납품 일정 견적 품목 불러오기, 일정 삭제, 제품 삭제 대체 처리

**목표**: React 일정 상세에서 납품 일정이 기존 견적 일정의 품목을 끌어와 납품 품목으로 저장할 수 있게 한다. 같은 화면에서 일정 삭제도 가능하게 하고, React 제품관리 목록 깨짐을 수정한다. 제품 일괄 삭제 시 견적/납품에 사용되어 차단된 제품은 대체 제품으로 품목 연결을 옮긴 뒤 데이터 무결성이 확인되면 삭제되게 한다.

### 확인된 상태

- 기존 Django 일정 폼에는 `/reporting/api/followups/<followup_id>/quote-items/` 기반 견적 품목 불러오기가 있으나 React 일정 상세에는 UI가 없었다.
- React 일정 상세는 납품/견적 품목 편집과 저장 API는 갖고 있으므로, 견적 품목 조회 API 응답을 React 편집 행으로 매핑하면 DB 모델 변경 없이 구현 가능하다.
- 기존 `schedule_delete_view()`는 AJAX POST 삭제를 지원하지만 React 상세 payload에는 삭제 URL이 내려오지 않았다.
- React 제품 목록은 표와 사이드 패널이 한 행에 배치되어 운영 화면 폭에서 표가 좁아지고, 일부 table cell 스타일이 표 렌더링을 흔들 수 있었다.
- 기존 제품 일괄 삭제 API는 `DeliveryItem`/`QuoteItem` 참조가 있는 제품을 무조건 차단한다.

### 구현 계획

- 견적 품목 API를 React에서 쓰기 좋게 camelCase 필드, 제품 연결값, 할인단가, 견적서 구분, 적요까지 반환하도록 보강한다.
- React 일정 상세 납품 품목 패널에 `견적 불러오기` 버튼과 견적 선택 패널을 추가한다.
- 선택한 견적의 품목을 납품 품목 편집 행으로 가져오고, 저장 버튼을 눌러 기존 납품 품목 저장 API에 반영한다.
- React 일정 상세 payload에 `deleteSchedule` 링크를 추가하고, 삭제 버튼은 기존 Django AJAX 삭제 뷰를 호출한 뒤 일정 목록으로 이동한다.
- 제품 목록 CSS를 고정 테이블 레이아웃/반응형 사이드 패널 구조로 조정해 운영 화면에서 깨지지 않게 한다.
- 제품 일괄 삭제 API에 `replacements` payload를 추가해 차단 제품의 `DeliveryItem`/`QuoteItem` 참조를 대체 제품으로 옮긴 뒤 참조가 남아 있지 않을 때만 원제품을 삭제한다.
- React 제품 삭제 패널에서 차단된 제품별 대체 제품 선택 UI를 제공한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_returns_detail_and_edit_config reporting.tests.SchedulesSummaryApiTests.test_schedules_detail_api_manager_read_only_and_other_company_blocked reporting.tests.SchedulesSummaryApiTests.test_schedule_delete_ajax_allows_owner_and_removes_related_history reporting.tests.SchedulesSummaryApiTests.test_schedule_delete_ajax_blocks_non_owner reporting.tests.ProductManagementReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- 로컬 React UI smoke: `/products/`, `/schedules/882/` 목 API 기반 렌더링 확인
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/products/`, `/schedules/882/`, `/reporting/login/` smoke check

### 현재 상태

- 구현/로컬 검증/커밋/푸시/운영 배포/익명 smoke 완료.
- DB 모델 변경 없음.
- Runtime commit: `f1d7b42 feat: import quote items into deliveries`
- Railway `web`: `2241be62-11b5-472d-92b6-4f469179f61c` SUCCESS
- Railway `sales-note-frontend`: `cba176c5-cebc-4ba7-8989-e298b0cbfb1c` SUCCESS
- 운영 smoke OK:
  - `/products/` 200 with `assets/index-2OWdxLkM.js` / `assets/index-2AirpMI9.css`
  - `/schedules/882/` 200
  - `/reporting/login/` 200
  - anonymous `/reporting/api/products/manage/` 302 login redirect
  - anonymous `/reporting/api/schedules/882/` 401 login-required JSON
- 다음 행동: 사용자가 운영에서 수동 검수한다. 검수 결과 확인 전에는 다음 구현 작업을 시작하지 않는다.

---

## Previous task — 제품관리 React 전환, Ecount upsert, 엑셀 다운로드/일괄삭제, 프로모션 제거

**목표**: 기존 Django 제품관리 화면을 React CRM 화면으로 옮기고, Ecount 제품 데이터를 붙여넣어 신규/기존 제품을 일괄 upsert할 수 있게 한다. 전체 제품 Excel 다운로드와 붙여넣기 기반 일괄 삭제를 제공하고, 제품관리의 프로모션 설정 기능은 제거한다.

### 확인된 상태

- `Product` 모델은 `product_code`, `unit`, `specification`, `standard_price`, `is_active`, `description`, `created_by`를 중심으로 사용한다.
- 기존 Django 제품관리 URL은 `/reporting/products/`, `/reporting/products/create/`, `/reporting/products/bulk-create/`, `/reporting/products/<id>/edit/`, `/reporting/products/<id>/delete/`다.
- 기존 React에는 일정 품목 선택용 `loadProducts()`만 있고, 제품관리 전용 React 화면/API는 없다.
- 기존 `product_bulk_create()`는 중복 제품을 업데이트하려는 의도는 있으나 React 관리 화면에서는 사용할 수 없고, 프로모션 필드도 여전히 노출된다.
- DB 모델 변경 없이 구현 가능하다. 프로모션 컬럼은 호환성을 위해 남기되 제품관리/가격 계산에서는 사용하지 않게 한다.

### 구현 계획

- 제품관리 전용 API를 추가한다.
  - 목록/검색/상태/정렬/페이지네이션
  - 단일 생성/수정
  - Ecount 붙여넣기 일괄 upsert
  - 붙여넣기 기반 일괄 삭제
  - 전체 제품 XLSX 다운로드
- 중복 제품 upsert는 품번 기준으로 기존 제품을 찾고, 설명/규격/단위/기준단가/활성 상태가 달라졌을 때 업데이트한다.
- 삭제는 기존 단일 삭제 규칙을 유지해 견적/납품에 사용된 제품은 삭제하지 않고 차단 내역으로 반환한다.
- `Product.get_current_price()`와 제품 API는 기준단가를 그대로 반환하게 하여 프로모션 가격 기능을 비활성화한다.
- 기존 Django 제품 폼/목록에서도 프로모션 설정/현재가 표시를 제거한다.
- React `/products/` 화면과 사이드바 메뉴를 추가하고, 제품 목록/등록/수정/붙여넣기 upsert/붙여넣기 삭제/Excel 다운로드를 한 화면에서 제공한다.

### 검증 계획

- `python -m py_compile reporting\models.py reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.ProductSpecificationSaveTests reporting.tests.ProductManagementReactApiTests reporting.tests.SchedulesSummaryApiTests.test_product_api_list_returns_accessible_product_master_data --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/products/`, `/reporting/products/`, `/reporting/api/products/manage/` smoke check

### 현재 상태

- 구현/로컬 검증/커밋/푸시/운영 배포/익명 smoke 완료.
- Runtime commit: `126fd3b feat: migrate product management to react`
- Railway `web`: `c36d7e71-7379-45f2-9dca-3d7af93525de` SUCCESS
- Railway `sales-note-frontend`: `3bb14e78-8f7d-4d58-8e76-125bf65d8418` SUCCESS
- 운영 smoke OK: `/products/` 200 with latest assets, `/reporting/login/` 200, anonymous `/reporting/api/products/manage/` 302 login redirect, anonymous `/reporting/products/` 302 login redirect.
- 다음 행동: 사용자가 운영 `/products/`에서 제품관리 수동 검수를 완료한다. 검수 결과 확인 전에는 다음 구현 작업을 시작하지 않는다.

### 다음 대기 작업

- 납품 생성/수정 React 화면에서도 기존 견적 품목을 끌어와 납품 품목으로 사용할 수 있게 한다.
- 제품관리 운영 검수 완료 후 시작한다.

---

## Previous task — React 메일 리치 에디터 링크 표시 텍스트 핫픽스

**목표**: 사용자가 링크 버튼을 누를 때 URL 자체가 본문에 들어가는 것이 아니라, 원하는 표시 문구를 링크 텍스트로 넣을 수 있게 한다. 선택한 본문 텍스트가 있으면 해당 텍스트를 기본 표시 문구로 사용하고, URL 입력 후 선택 영역을 링크로 교체한다.

### 확인된 상태

- React 메일 리치 에디터의 기존 링크 버튼은 선택 텍스트가 있을 때 `document.execCommand('createLink')`를 사용한다.
- 선택 텍스트가 없을 때는 URL 문자열 자체를 `<a>` 텍스트로 삽입한다.
- 사용자가 원하는 동작은 “표시할 텍스트”와 “URL”을 분리해서 입력하는 방식이다.

### 구현 계획

- 에디터 내부 현재 selection range를 저장/복원하는 helper를 추가한다.
- 링크 버튼 클릭 시 표시할 텍스트를 먼저 입력받고, 선택 텍스트가 있으면 기본값으로 제공한다.
- URL을 normalize한 뒤 저장한 range를 복원하고 `<a href="...">표시문구</a>`로 삽입한다.

### 검증 계획

- `cd frontend; npm run build`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/mailbox/` smoke check

### 현재 상태

- 구현/프론트 빌드/푸시/운영 배포/스모크 완료, 사용자 운영 수동 검수 완료.
- Runtime commit: `9fc5522 fix: insert mail links with custom text`
- Railway `sales-note-frontend`: `e5f407b8-d513-4dcc-82ca-736e9964cf7f` SUCCESS
- Railway `web`: `36758e7b-1f37-4d91-a3a1-2585d5a5eb33` SUCCESS (문서 커밋 자동 배포)
- 운영 smoke OK: `/reporting/login/`, `/mailbox/`
- 수동 검수 결과: 완료. 사용자가 2026-05-12 KST에 확인했다.

---

## Previous task — React 메일 리치 에디터 및 AI Workspace 상세 추천 스코프

**목표**: React 메일 작성/답장 본문을 일반 textarea가 아니라 서식 있는 에디터로 전환한다. 볼드, 기울임, 밑줄, 글씨체/크기/색상, 목록, 링크, 사진 삽입을 지원하고, 발송 API는 HTML 본문을 안전하게 sanitize해서 Gmail/SMTP로 발송한다. 동시에 `/ai-workspace/?department_id=...` 상세 페이지에서는 추천 질문/프롬프트가 해당 부서 고객 기준으로만 나오게 제한한다.

### 확인된 상태

- Django 레거시 메일 작성 화면은 Quill 기반 HTML 에디터와 `body_html` hidden input을 이미 사용한다.
- React 메일 작성/답장 폼은 `textarea`의 plain text만 `body_text`로 전송한다.
- backend `GmailService.send_email()` 및 SMTP 발송 경로는 이미 `body_html`을 받을 수 있다.
- React AI Workspace는 `department_id` 요청 시 featured panel과 추천 목표는 선택 부서를 쓰지만, 추천 질문 `promptTargets`는 전체 painpoint/followup/department 후보를 섞어 만들 수 있다.

### 구현 계획

- React `MailComposePanel` 본문을 contenteditable 기반 rich editor로 교체한다.
- toolbar에 굵게/기울임/밑줄, 글씨체, 크기, 글자색/배경색, 목록, 링크, 이미지, 서식 지우기를 추가한다.
- 기존 `/reporting/upload-image/` endpoint를 React에서도 사용해 본문 이미지를 업로드 후 `<img>`로 삽입한다.
- 메일 발송 payload에 `bodyHtml`을 추가하고 `body_html` FormData로 전송한다.
- server-side HTML sanitize helper를 추가해 script/style/event handler/javascript URL을 제거하고 허용된 이메일 서식만 보낸다.
- AI Workspace API에서 접근 가능한 `department_id`가 요청된 경우 painpoint, followup, department prompt 후보를 해당 부서로만 제한한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\gmail_views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.ReactMailboxApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/?department_id=81`, `/ai-workspace/`, `/mailbox/` smoke check

### 현재 상태

- 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 운영 수동 검수 대기.
- Runtime commit: `eb7e0fc feat: add rich mail editor and scope ai prompts`
- Railway `web`: `fc0b97e2-b144-4133-8171-2ca1be4375cd` SUCCESS
- Railway `sales-note-frontend`: `1053e2a3-603d-472c-8aea-159f0a5cf130` SUCCESS
- 운영 smoke OK: `/reporting/login/`, `/ai-workspace/`, `/ai-workspace/?department_id=81`, `/mailbox/`
- 다음 행동: 사용자가 운영에서 AI Workspace 상세 추천 질문 스코프와 메일 리치 에디터 발송을 수동 검수한다. 검수 전에는 다음 구현 작업을 시작하지 않는다.

---

## Previous task — 견적 구분별 기타사항, 메일 참조 선택, 서류/PDF/메일함 핫픽스

**목표**: 운영 검수 중 확인된 견적/메일 문제를 우선 해결한다. 같은 일정의 견적서 구분마다 기타사항을 따로 저장/치환하고, 메일 발송 시 내부 직원 참조 포함 여부를 사용자가 선택하게 한다. 견적서/거래명세서 생성 시 템플릿의 볼드체를 제거하고, 품목 적요가 긴 경우 PDF에서 잘리지 않도록 행 높이를 보정한다. 받은 메일 상세에서는 CSS 잔여 텍스트가 보이지 않게 하며, 상대가 보낸 첨부파일을 React 메일함에서 확인/다운로드할 수 있게 한다.

### 확인된 상태

- 기존 `Schedule.quote_extra_notes`는 일정 단위 1개 필드라 `보상판매`, `수리`처럼 견적서 구분이 여러 개인 경우 기타사항이 통합되어 표시된다.
- React 일정 상세는 품목별 `quote_group`을 저장하지만, 구분별 기타사항 저장 구조는 없다.
- 메일 작성/답장 API는 수동 CC만 받으며, 같은 회사 내부 직원 이메일을 CC에 넣을지 선택하는 옵션이 없다.
- 받은 메일 본문 표시에서 HTML `<style>` 또는 본문 앞 CSS 조각인 `p{margin-top:0px;margin-bottom:0px;}`가 텍스트로 남을 수 있다.
- Gmail 동기화는 본문과 기본 헤더만 저장하고 첨부파일 메타데이터/다운로드 식별자를 저장하지 않는다. React 스레드 상세도 `attachments` 목록을 렌더링하지 않는다.
- 견적서/거래명세서 PDF 생성은 엑셀 템플릿의 볼드 스타일을 그대로 유지한다.
- 견적서 품목 `적요`가 길면 PDF 변환 시 셀 높이가 늘어나지 않아 텍스트가 잘릴 수 있다.
- 구분별 기타사항 저장을 위해 DB migration이 필요하다.

### 구현 계획

- `ScheduleQuoteGroupNote` 모델과 migration을 추가해 일정+견적서 구분별 기타사항을 저장하고, 기존 일정 단위 기타사항은 기본 구분으로 이관한다.
- 일정 상세/품목 저장 API에 `quoteGroupNotes` payload를 추가하고, 문서 변수 `기타사항`/`견적기타사항`은 선택한 견적서 구분의 기타사항을 사용하게 한다.
- React 일정 상세 품목 편집에 견적서 구분별 기타사항 입력란을 표시하고, 저장/조회/읽기 전용 표시를 구분별로 나눈다.
- 같은 회사 활성 사용자 이메일을 메일 작성 옵션으로 내려주고, React 작성/답장 폼에 “내부 직원 참조 포함” 체크박스를 추가한다. 체크된 경우만 서버에서 내부 직원 이메일을 CC에 병합한다.
- Gmail/IMAP 메일 본문 표시 전에 HTML style/script와 CSS 선언 잔여 텍스트를 제거한다.
- Gmail 메시지 상세 파서가 첨부파일 `attachmentId`, 파일명, MIME, 크기를 수집해 `EmailLog.attachments_info`에 저장하게 하고, 인증된 다운로드 API에서 Gmail attachment API로 원본 파일을 내려준다.
- React 메일 목록/스레드 상세에서 첨부 개수와 다운로드 링크를 표시한다.
- 견적서/거래명세서 XLSX 생성 후 PDF 변환 전 스타일 XML과 rich text에서 `<b>` 노드를 제거한다.
- `{{품목N_적요}}`/`{{품목N_비고}}` 셀에는 줄바꿈 스타일과 계산된 행 높이를 적용해 긴 적요가 PDF에서 잘리지 않게 한다.

### 검증 계획

- `python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\gmail_utils.py reporting\tests.py`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.ReactMailboxApiTests --verbosity=1`
- `python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/880/`, `/mailbox/`, `/reporting/login/` smoke check

### 현재 상태

- 구현/로컬 검증/푸시/운영 배포 완료, 사용자 운영 수동 검수 대기.
- Runtime commits: `14606a4 fix: repair quote notes and mailbox attachments`, `97513a5 fix: expand quote item note rows`
- Railway `web`: `f1c117d4-f7cc-41ca-81f1-3630c7238a4e` SUCCESS
- Railway `sales-note-frontend`: `a159b40a-4105-4473-bea3-580e69f08e1d` SUCCESS
- 제품관리 React 전환 WIP는 링크 핫픽스 검수 완료 후 현재 작업으로 적용해 진행 중이다.

---

## Previous task — 견적서 담당자 이름 순서 보정

**목표**: 사용자 이름이 `이름=재현`, `성=안`으로 설정되어 있으면 견적서 서류 변수/PDF에서 `안재현`으로 표시되게 한다. 과거 사용자 생성/수정 화면의 성/이름 라벨이 Django 필드 의미와 반대로 되어 있던 계정도 문서 생성 시 보정한다.

### 확인된 상태

- 견적서 데이터 생성과 PDF 생성은 `schedule.user.last_name + schedule.user.first_name`을 직접 조합한다.
- 프로필 수정 폼은 `first_name=이름`, `last_name=성`으로 정상 저장하지만, 관리자/매니저 사용자 생성 및 편집 폼은 `first_name=성`, `last_name=이름`으로 라벨/placeholder가 반대로 되어 있다.
- 따라서 기존 계정은 필드가 정상이어도, 과거 화면에서 저장된 계정은 필드가 뒤집혀 있을 수 있다.
- DB 모델 변경은 필요하지 않다.

### 구현 계획

- 문서 생성 전용 담당자명 helper를 추가해 정상 저장(`first_name=재현`, `last_name=안`)과 과거 역저장(`first_name=안`, `last_name=재현`)을 모두 `안재현`으로 보정한다.
- `get_document_template_data()`와 `generate_document_pdf()`의 담당자 변수(`실무자`, `영업담당자`, `담당영업`)가 해당 helper를 사용하게 한다.
- 관리자/매니저 사용자 생성/수정 폼의 `first_name`/`last_name` 라벨과 placeholder를 Django 의미에 맞게 `이름`/`성`으로 바로잡아 신규 오입력을 막는다.
- 문서 템플릿 API 테스트에 정상/역저장 한글 이름 회귀 케이스를 추가한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/login/`, `/reporting/api/documents/` 보호 smoke check

### 완료 상태

- Runtime commit: `9b24fcf fix: normalize quote salesperson name order`
- Railway `web`: `5d6450fb-896a-4e89-b851-c99b083785bf` SUCCESS
- `sales-note-frontend`: 변경 없음.
- 로컬 검증 OK: 문서 템플릿 API 12개 테스트, Django check, migration dry-run, diff check.
- 운영 smoke OK: `/reporting/login/` 200, `/reporting/api/documents/` 401, `/documents/` 200, `/schedules/879/` 200.
- 다음 행동: 사용자가 운영에서 견적서 PDF 담당자명이 `안재현`으로 표시되는지 수동 검수한다. 검수 전에는 다음 구현 작업을 시작하지 않는다.

### 이후 대기 작업

- 모든 현재 작업이 끝난 뒤 제품관리 Django 화면을 React로 전환한다.
- 제품관리 신규 제품 등록 시 Ecount 데이터를 가져오면서 기존 등록 제품과 중복되면 가격/규격 등 변경값을 비교해 기존 제품을 갱신한다.
- 전체 제품 엑셀 다운로드와 엑셀 데이터 붙여넣기 기반 일괄 삭제를 제공한다.
- 제품관리의 프로모션 설정 기능을 제거한다.

---

## Previous task — 일정 내 복수 견적서 구분 등록 및 메일 자동 첨부 보정

**목표**: 한 quote 일정 안에서 `보상판매`, `수리`처럼 서로 다른 견적서 구분을 2개 이상 만들고, 각 구분의 품목만 담은 견적서 PDF를 별도로 등록/다운로드할 수 있게 한다. 일정 메일 발송 시 등록된 견적서 PDF들을 자동 첨부하는 기존 흐름은 유지한다.

### 확인된 상태

- 직전 구현은 `DocumentGenerationLog`에 견적서 PDF 파일을 여러 개 저장할 수 있게 했지만, 모든 PDF가 같은 일정의 전체 품목을 사용한다.
- 사용자가 요구한 것은 같은 일정에서 “보상판매 견적서 1부”, “수리 견적서 1부”처럼 품목 묶음이 다른 견적서 여러 부를 만드는 기능이다.
- 현재 React 일정 품목 편집은 `DeliveryItem` 목록을 저장하므로, 여기에 견적서 구분 필드를 추가하면 기존 일정/품목 흐름을 유지하면서 견적서별 품목 분리가 가능하다.
- 서류 생성 API는 query string으로 견적서 구분을 받아 해당 구분의 품목만 치환하고, 생성 로그에도 구분명을 남겨야 한다.
- DB migration이 필요하다.

### 구현 계획

- `DeliveryItem.quote_group`을 추가해 각 품목이 속한 견적서 구분명을 저장한다.
- `DocumentGenerationLog.quote_group`을 추가해 생성/등록된 견적서 PDF가 어떤 구분의 견적서인지 남긴다.
- 일정 상세 API의 `deliveryItems`, 문서 action, 등록 견적서 payload에 견적서 구분 정보를 포함한다.
- quote 일정의 문서 action은 전체 견적서 1개가 아니라 견적서 구분별 action으로 내려준다.
- `get_document_template_data()`와 `generate_document_pdf()`가 `quote_group` query/post 값을 받아 해당 구분 품목만 사용하도록 한다.
- React 일정 품목 편집 UI에 `견적서 구분` 입력을 추가하고, 문서 패널에서 구분별 `PDF 등록/다운로드` 버튼을 제공한다.
- 메일 자동 첨부는 등록된 구분별 견적서 PDF를 모두 첨부한다. 등록된 PDF가 하나도 없으면 구분별 PDF를 생성해 첨부한다.
- 이어서 사용자가 요청한 등록 서류 삭제 기능을 추가한다. 파일로 등록된 생성 서류는 견적서/거래명세서/납품서 모두 일정 상세에서 삭제할 수 있게 하되, 메일 자동 첨부는 견적서 PDF로만 유지한다.

### 검증 계획

- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\tests.py`
- `python manage.py check`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke check

### 완료 상태

- Runtime commit: `0384e13 feat: split schedule quote documents by group`
- Railway `web`: `b191502b-10bc-4e9b-973f-756bb2c5b3c0` SUCCESS
- Railway `sales-note-frontend`: `3fb901ec-e5ec-49f8-aa2d-5d568f018ede` SUCCESS
- 운영 migration `reporting.0097_quote_document_groups` 적용 OK.
- 운영 smoke OK: `/schedules/879/`, `/mailbox/`, `/documents/`, 새 JS/CSS asset, `/reporting/login/`, 보호 API/삭제 POST.
- 다음 행동: 사용자가 운영에서 구분별 견적서 등록/삭제/메일 자동첨부를 수동 검수한다. 검수 전에는 다음 구현 작업을 시작하지 않는다.

---

## Previous task — 일정 견적서 PDF 다중 등록 및 메일 자동 첨부

**목표**: 견적 일정에서 견적서 PDF를 여러 개 등록/보관할 수 있게 하고, 해당 일정에서 메일을 보낼 때 등록된 견적서 PDF만 자동 첨부한다. 거래명세서/납품서나 일반 첨부파일은 자동 첨부 대상에서 제외한다.

**상태**: 구현/로컬 검증/푸시/Railway `web` 및 `sales-note-frontend` 운영 배포/스모크 완료. 사용자 운영 수동검수 대기.

### 확인된 상태

- 현재 일정 서류 생성은 `generate_document_pdf()`에서 파일을 즉시 다운로드만 하고, 생성된 PDF를 일정에 보관하지 않는다.
- `DocumentGenerationLog`는 일정/서류종류/거래번호/출력형식 이력을 이미 저장하지만 실제 생성 파일은 저장하지 않는다.
- `Schedule`은 하나의 일정에 여러 `DocumentGenerationLog`를 가질 수 있어, 이 로그에 파일 필드를 추가하면 한 일정에 여러 견적서 PDF를 등록할 수 있다.
- 기존 Django 일정 상세에는 “이메일 발송” 경로가 있고, React 일정 상세에는 서류 다운로드 패널과 메일함이 분리되어 있다.
- 메일 발송 공통 로직 `_handle_email_send()`는 수동 첨부파일만 처리하며, 일정 기반 자동 첨부는 없다.
- DB migration이 필요하다.

### 구현 계획

- `DocumentGenerationLog`에 생성 파일, 원본 파일명, 파일 크기 메타를 추가한다.
- 견적서 PDF 생성 성공 시 생성된 PDF bytes를 `DocumentGenerationLog.file`에 저장해 “등록된 견적서”로 남긴다.
- 일정 상세 API의 `documents` payload에 해당 일정의 등록된 견적서 PDF 목록과 다운로드 링크를 추가한다.
- 등록된 견적서 파일 다운로드 전용 인증/권한 보호 endpoint를 추가한다.
- Django/React 일정 상세의 견적서 PDF 버튼 문구를 “PDF 등록/다운로드” 흐름으로 맞추고, React 일정 상세에서 등록된 견적서 목록을 보여준다.
- React 일정 상세에서 “메일 발송” 진입을 제공하고, 메일 작성 payload에 `schedule_id`를 함께 보낼 수 있게 한다.
- `mailbox_api_send`와 Django 일정 메일 발송에서 quote 일정이면 등록된 견적서 PDF만 자동 첨부한다.
- quote 일정인데 등록된 견적서가 없으면 메일 발송 직전에 견적서 PDF를 한 번 생성/등록한 뒤 첨부한다. PDF 생성이 실패하거나 Excel fallback만 가능하면 메일 발송을 중단하고 오류를 반환한다.
- 답장 메일에는 기존 동작을 유지하고 자동 견적서 첨부를 적용하지 않는다.

### 검증 계획

- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.DocumentTemplatesReactApiTests --verbosity=1`
- `python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\tests.py`
- `python manage.py check`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/`, `/mailbox/`, `/reporting/login/` smoke check

### 완료 상태

- Runtime commit: `95aeec7 feat: auto attach quote pdfs to schedule mail`
- Railway `web`: `2d1dd812-3fe5-4c3b-953e-870ca5c88baf` SUCCESS
- Railway `sales-note-frontend`: `05a56e6c-3067-4500-8ae0-6383ff40d91f` SUCCESS
- Production smoke OK: `/schedules/` 200, `/mailbox/` 200, new JS/CSS assets 200, `/reporting/login/` 200, protected API/download unauthenticated responses OK.
- Next action: user manual production test for quote schedule multiple PDF registration and automatic mail attachment.

---

## Previous task — 견적서 PDF A4 자동 맞춤

**목표**: 견적서 PDF 다운로드 시 엑셀 템플릿 인쇄 영역이 A4보다 크게 잡혀 PDF가 잘리는 문제를 막는다. PDF 변환 직전 생성된 XLSX의 워크시트 인쇄 설정을 A4, 1페이지 너비 맞춤, 축소 여백으로 보정해 LibreOffice/unoconv 변환 결과가 A4에 맞게 나오도록 한다.

### 확인된 상태

- 서류 다운로드는 업로드된 XLSX 템플릿을 ZIP 레벨에서 변수 치환한 뒤 `unoconv`로 PDF 변환한다.
- 기존 변환 경로는 템플릿의 인쇄 설정을 그대로 사용하므로, 템플릿에 큰 인쇄 영역/기본 용지/배율이 남아 있으면 PDF가 A4보다 크게 잘릴 수 있다.
- DB 모델 변경은 필요하지 않다.

### 구현 계획

- PDF/엑셀 반환 직전 생성된 XLSX 내부 `xl/worksheets/sheet*.xml`에 A4 인쇄 설정을 적용한다.
- 각 시트에 `fitToPage=1`, `paperSize=9(A4)`, `fitToWidth=1`, `fitToHeight=0`을 설정하고 기존 `scale`은 제거한다.
- 인쇄 여백을 줄여 템플릿 내용이 A4 PDF에 안정적으로 들어오게 한다.
- XML 레벨 보정 helper를 테스트해 PDF 변환 전 XLSX가 A4 맞춤 설정을 갖는지 회귀 검증한다.

### 검증 계획

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/login/`, `/reporting/api/documents/` 보호 smoke check

---

## Current task — 견적 할인단가/적요/기타사항, React 서류 변수 복사, AI 추천목표 고객명/우선순위

**목표**: 견적 품목에서 기준단가는 기존처럼 직접 조절할 수 있게 유지하면서, 별도의 할인율 또는 할인단가를 입력해 최종 견적 단가를 계산할 수 있게 한다. 품목별 적요와 전체 견적 기타사항을 저장하고, 새 변수까지 포함한 사용 가능한 서류 템플릿 변수를 React 서류 등록 화면에서 확인/복사할 수 있게 한다. 이어서 React AI Workspace 추천 목표에 명확한 고객명을 포함하고, AI 분석 실행 때마다 AI 판단 결과로 고객 우선순위를 다시 산정한다.

### 확인된 상태

- 현재 견적/납품 품목은 `DeliveryItem` 모델을 공통으로 사용하며, `unit_price`가 단가와 총액 계산 기준이다.
- 품목별 비고는 기존 `DeliveryItem.notes`에 저장되고 있으므로 새 DB 필드 없이 React/Django UI에서 `적요`로 노출하고 `품목N_적요` 변수로 연결할 수 있다.
- 할인 단가/할인율은 별도 저장 필드가 없고, 사용자는 현재 기준단가를 낮추는 방식으로 할인 효과를 내고 있다.
- 전체 견적 기타사항은 Schedule의 일반 `notes`와 분리된 필드가 없어 새 `Schedule.quote_extra_notes` 필드가 필요하다.
- React 일정 상세의 서류 변수 미리보기는 특정 일정의 실제 변수값만 보여준다. React `/documents/` 서류 템플릿 등록 화면에는 Django 템플릿처럼 사용 가능한 변수 목록/복사 UI가 없다.
- 신규 DB migration이 필요하다.
- AI Workspace 추천 목표는 부서 중심 제목만 내려올 수 있어 실제 실행 대상 고객명이 불명확하다.
- 부서/고객 AI 분석 결과는 다음 액션을 만들지만 CRM `FollowUp.priority`를 분석 결과 기준으로 다시 저장하지 않는다.

### 구현 계획

- `DeliveryItem`에 `discount_rate`, `discount_unit_price` 필드를 추가하고, 총액 계산은 할인단가가 있으면 할인단가, 없으면 할인율, 둘 다 없으면 기준단가를 사용하도록 정리한다.
- `Schedule`에 `quote_extra_notes` 필드를 추가한다.
- React 일정 상세 품목 편집 UI에 기준단가, 할인율, 할인단가, 적요를 표시하고 할인율/할인단가 양방향 입력을 지원한다.
- React 품목 저장 API payload와 Django `save_delivery_items` 파서를 할인 필드/적요/전체 기타사항까지 저장하도록 확장한다.
- 서류 데이터 생성/다운로드 변수에 `기타사항`, `견적기타사항`, `품목N_기준단가`, `품목N_할인율`, `품목N_할인단가`, `품목N_적요` 등을 추가하고 기존 `품목N_단가`/금액은 최종 적용단가 기준으로 유지한다.
- React `/documents/`에 사용 가능한 템플릿 변수 목록과 복사 버튼을 추가하고, Django 변수 도움말 partial에도 새 변수를 추가한다.
- AI 분석 JSON 스키마에 고객별 추천 목표와 고객별 우선순위 추천을 추가하고, 누락 시 고객 단계 컨텍스트로 보정한다.
- 부서 AI 분석 실행 후 해당 부서 고객의 `FollowUp.priority`를 `urgent/followup/scheduled/long_term`으로 다시 산정해 저장한다.
- 개별 고객 AI 분석 실행 후 해당 고객의 우선순위도 AI 결과 또는 거래 가능성/리스크 기준으로 갱신한다.
- React AI Workspace 추천 목표 카드에 고객명/우선순위 라벨을 표시한다.
- 관련 API/문서/React 테스트를 보강한다.

### 검증 계획

- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.AIWorkspaceSummaryApiTests ai_chat.tests.AIDepartmentPromptLogicTests ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python -m py_compile reporting\models.py reporting\views.py reporting\tests.py ai_chat\services.py ai_chat\views.py ai_chat\department_prompt.py ai_chat\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/documents/`, `/schedules/<id>/`, `/ai-workspace/`/API 보호 smoke check

---

## Current task — React AI 요약/파이프라인/추천질문/메일 컨텍스트 보강

**목표**: React CRM에서 부서 AI 요약이 중간에 잘리지 않게 하고, 파이프라인 선택 고객 패널에서도 고객 상세/AI Workspace 수준의 AI 실행·결과·PainPoint 검증을 사용할 수 있게 한다. 또한 AI 추천 질문을 React에서 별도 목록으로 모두 확인/복사할 수 있게 하고, AI 분석 입력에 고객 답장과 함께 최근 사용자 발신 메일 맥락을 최대 2건까지 포함한다.

### 확인된 상태

- 고객 상세, AI Workspace, 파이프라인의 AI 상단 요약은 Django API에서 `[:180]`으로 잘려 내려가는 지점이 있다.
- React 파이프라인 API의 `aiDepartment` payload는 현재 compact summary/count/link 중심이라, React 파이프라인 안에서 AI 결과 본문, 추천 액션, 추천 질문, PainPoint 검증을 온전히 사용할 수 없다.
- React `CustomerAiResultPanel`은 missing info 질문과 PainPoint 검증 질문을 일부 보여주지만, 질문을 한 곳에서 모두 확인/복사하는 전용 목록은 없다.
- AI 프롬프트용 메일 수집은 수신 메일을 우선하고 발신 메일을 보조로 일부 포함할 수 있으나, “고객 답장 + 사용자가 보낸 최근 메일”을 스레드 세트로 명확히 묶지 않는다.
- 신규 DB 필드나 migration은 필요하지 않다. 기존 `AIDepartmentAnalysis`, `PainPointCard`, `EmailLog` 데이터를 재사용한다.

### 구현 계획

- 고객 상세/AI Workspace/파이프라인 AI top summary payload의 180자 truncation을 제거해 전체 요약을 내려준다.
- 파이프라인 API의 `aiDepartment`에 기존 고객 상세 AI 결과 payload(`meetingInsights`, `quoteDelivery`, `nextActions`, `missingInfo`, `painpoints` 등)를 포함한다.
- React 파이프라인 상세 패널에서 AI 분석 실행, 결과 펼침, PainPoint 검증 메모 저장을 지원하고, 실행/검증 후 파이프라인 데이터를 다시 불러온다.
- AI 결과 payload에 `recommendedQuestions`를 추가해 missing info 질문, 검증 인사이트의 다음 질문, PainPoint 검증 질문을 중복 제거해 전달한다.
- React `CustomerAiResultPanel`에 추천 질문 섹션과 질문 복사 버튼을 추가해 고객 상세, AI Workspace, 파이프라인에서 공통으로 사용한다.
- AI 메일 컨텍스트 수집에서 고객 수신 메일은 유지하고, 같은 스레드의 사용자 발신 메일 또는 최근 사용자 발신 메일을 전체 최대 2건까지 포함한다. 고객 답장에는 관련 발신 메일을 nested context로 묶어 프롬프트에 전달한다.

### 검증 계획

- `python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.PipelineApiTests ai_chat.tests.AIEmailAndStageActionContextTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\funnel_views.py ai_chat\services.py reporting\tests.py ai_chat\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/`, `/ai-workspace/`, `/reporting/api/pipeline/` 보호/응답 smoke check

---

## Current task — 메일 발송 줄바꿈 과다 간격 수정

**목표**: React `/mailbox/`에서 메일을 보낼 때 사용자가 입력한 줄바꿈이 실제 수신 메일에서 2~3배로 벌어지지 않게, plain text 본문을 HTML 메일로 변환하는 공통 발송 로직을 정규화한다.

### 확인된 상태

- React 메일 작성/답장은 `body_text`만 `FormData`로 전송하고 `body_html`은 보내지 않는다.
- Django `_handle_email_send()`는 `body_html`이 없으면 `body_text.replace('\n', '<br>')`로 HTML을 만든 뒤 `white-space: pre-wrap` 스타일을 함께 적용한다.
- multipart/form-data를 거친 textarea 줄바꿈은 `\r\n`으로 들어올 수 있어 현재 변환은 `\r<br>`를 남기며, HTML 메일 클라이언트에서 줄바꿈이 중복될 수 있다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- 메일 발송 공통 로직에서 `body_text`의 `\r\n`, `\r`을 먼저 `\n`으로 정규화한다.
- plain text → HTML 변환 helper를 추가해 HTML escape 후 `\n`만 `<br>`로 변환한다.
- 변환 HTML에서는 `white-space: pre-wrap`을 제거하고 line-height/margin만 지정해 `<br>`이 줄바꿈을 단독으로 담당하게 한다.
- Gmail API/IMAP SMTP 발송, EmailLog 저장, 첨부파일/명함 서명/답장 흐름은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1`
- `python -m py_compile reporting\gmail_views.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/mailbox/`/메일 API 보호 smoke check

---

## Current task — React 일정 메뉴 캘린더 우선 진입

**목표**: React 공통 사이드바에서 `일정`을 클릭하면 목록 화면(`/schedules/`)이 아니라 캘린더 화면(`/schedules/calendar/`)으로 먼저 진입하게 한다.

### 확인된 상태

- React route metadata의 일정 대표 링크는 이미 캘린더를 가리킨다.
- 공통 사이드바 `NAV_ITEMS`의 `일정` 링크만 `/schedules/`로 남아 있다.
- 일정 목록 화면과 `/schedules/` 라우트는 계속 유지해 기존 목록 접근을 보존한다.

### 구현 계획

- `frontend/src/App.tsx`의 `NAV_ITEMS` 일정 href를 `/schedules/calendar/`로 변경한다.
- 기존 일정 목록, 일정 상세, 캘린더 API, Django fallback은 변경하지 않는다.
- 이전 커밋의 캘린더 보고 내용 표시와 함께 운영 배포한다.

### 검증 계획

- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/` smoke check

---

## Current task — React 일정 캘린더 보고 내용 표시

**목표**: React `/schedules/calendar/`에서 날짜를 선택해 일정 카드를 볼 때, 해당 일정에 연결된 최근 영업보고 내용도 카드 안에서 바로 확인할 수 있게 한다.

### 확인된 상태

- React 캘린더 선택일 카드에는 일정 메모, 상태, 상세/고객/보고/Django fallback 액션이 표시된다.
- 일정 상세 API는 `relatedNotes`로 연결된 영업보고 기록을 이미 보여주지만, 캘린더 API payload에는 보고 내용이 없다.
- `History` 모델은 일정 연결(`schedule`)과 구조화된 미팅 필드/납품 보고 필드를 이미 가지고 있다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- 캘린더 API에서 고객 일정 queryset에 연결된 최신 영업보고를 prefetch한다.
- 일정 payload에 최근 보고 요약/본문/미팅 구조화 필드/납품 품목/다음 액션/보고 상세 링크를 포함한 `reports` 배열을 추가한다.
- React `ScheduleItem` 타입을 확장하고 선택일 카드 안에 `보고 내용` 블록을 추가한다.
- 보고가 없으면 기존 카드 크기를 불필요하게 키우지 않고, 보고가 있을 때만 내용을 노출한다.
- 개인 일정과 Django fallback, 기존 상태 변경 동선은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/` smoke check

---

## 프로젝트 개요

**세일즈 노트** — 한국 영업팀을 위한 내부 CRM/SFA 시스템 (Django 5.2.3)

이 시스템은 **공개 마케팅 사이트가 아닙니다**.  
제품 카탈로그, 브랜드 페이지, 공개 홈페이지는 이 프로젝트의 범위 밖입니다.

---

## Current task — React 일정 캘린더 선택일 작업 보강

**목표**: React `/schedules/calendar/` 선택일 패널에서 일정 상세 확인, 고객 이동, 보고 작성, Django fallback뿐 아니라 본인 고객 일정의 상태를 바로 변경할 수 있게 해 Django 캘린더에 남아 있던 핵심 운영 동선을 React로 옮긴다.

### 확인된 상태

- React `/schedules/calendar/`는 월간 grid, 데이터 범위 필터, 선택일 일정 목록, 일정 등록/Django fallback 링크를 제공한다.
- 선택일 목록은 현재 간단한 링크 목록이라 일정 상태 변경이나 관련 작업으로 바로 이어지기 어렵다.
- 기존 Django `schedule_status_update_api`는 `scheduled/completed/cancelled` 상태 변경, 권한 체크, 견적 일정 완료 차단 로직을 이미 제공한다.
- React 일정 상세 API는 편집 권한과 상태 선택지를 제공하지만, 캘린더 API payload에는 상태 변경용 메타가 없다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- 캘린더/일정 API payload의 고객 일정 항목에 `canEdit`, `statusUpdateHref`, `djangoEditHref`, `statusOptions`를 추가한다.
- 같은 회사 전체/직원 선택 범위에서도 본인 일정만 `canEdit=true`가 되게 하고, Manager/타인 일정은 읽기 전용으로 유지한다.
- React API client에 기존 Django 상태 변경 endpoint를 호출하는 `updateScheduleStatus()`를 추가한다.
- React 캘린더 선택일 패널을 카드형 작업 목록으로 바꾸고, 각 일정에 React 상세, 고객, 보고 작성, Django 상세/수정 fallback, 빠른 상태 버튼을 노출한다.
- 상태 변경 성공 후 캘린더 데이터를 다시 불러와 지표와 월간 grid를 동기화한다.

### 검증 계획

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/` smoke check

---

## Current task — React 서류 생성 이력 노출

**목표**: React `/documents/`에서 서류 템플릿 관리뿐 아니라 최근 서류 생성/다운로드 이력을 확인할 수 있게 해 견적/거래명세서/납품서 생성 workflow의 추적성을 높인다.

### 확인된 상태

- 기존 `DocumentGenerationLog` 모델이 서류 종류, 일정, 생성자, 거래번호, 출력 형식, 생성일을 기록한다.
- 일정 상세 React 화면은 이미 일정 기반 서류 미리보기/다운로드를 제공하고, 다운로드 시 기존 Django 생성 로직이 `DocumentGenerationLog`를 저장한다.
- React `/documents/` API는 현재 템플릿 목록/요약만 반환해 최근 어떤 서류가 생성됐는지 알 수 없다.
- 회사 범위 권한은 템플릿 API와 동일하게 유지하면 되고, 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- `/reporting/api/documents/` payload에 최근 서류 생성 이력 `recentGenerations`를 추가한다.
- 각 이력에는 거래번호, 서류 종류, 출력 형식, 생성일, 생성자, 회사, 연결 일정/고객/부서, React 일정 상세 링크와 Django fallback 링크를 포함한다.
- `type` 필터가 선택되면 생성 이력도 같은 서류 종류로 제한한다.
- React 타입/빈 상태를 확장하고 `/documents/` 오른쪽 패널에 최근 생성 이력 목록을 추가한다.
- 기존 템플릿 등록/수정/삭제/기본 설정, 일정 상세 서류 생성, Django fallback은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/documents/` smoke check

---

## Current task — React 메일 발송 첨부파일 지원

**목표**: React `/mailbox/`의 새 메일 작성과 `/mailbox/thread/<id>/` 답장에서 첨부파일을 선택해 발송할 수 있게 한다.

### 확인된 상태

- Django 메일 작성/답장 템플릿은 이미 `enctype="multipart/form-data"`와 `attachments` file input을 사용한다.
- `_handle_email_send()`는 `request.FILES.getlist('attachments')`를 읽어 Gmail API와 SMTP 발송 양쪽에 첨부파일을 전달하고, `EmailLog.attachments_info`에 파일명/크기/MIME 정보를 저장한다.
- React `MailboxSendPayload`와 `postMailboxForm()`은 현재 `URLSearchParams`만 전송해 파일을 보낼 수 없다.
- React `MailComposePanel`은 새 메일과 답장에 공통 사용되지만 파일 선택 UI가 없다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- React 메일 작성 상태에 `attachments: File[]`를 추가한다.
- `MailComposePanel`에 다중 파일 선택 input과 선택 파일 목록/삭제 버튼을 추가한다.
- 메일 발송/답장 API client가 payload를 `FormData`로 보내고, 각 파일을 `attachments` 필드로 append하게 한다.
- 발송 성공 후 첨부 상태를 초기화하고, 기존 고객 선택/명함 서명/본문/답장 흐름은 유지한다.
- Django API 회귀 테스트로 multipart 첨부가 `_handle_email_send()`까지 전달되고 `attachments_info`에 기록되는지 검증한다.

### 검증 계획

- `python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1`
- `python -m py_compile reporting\gmail_views.py reporting\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/mailbox/` smoke check

---

## Current task — React 일정 캘린더 선택일 등록 동선 보강

**목표**: React `/schedules/calendar/`에서 날짜를 선택한 뒤 `일정 등록`을 누르면 Django 화면으로 이동하지 않고 React `/schedules/?create=1&date=YYYY-MM-DD` 빠른 등록 패널이 열리며, 선택한 날짜가 방문 날짜로 자동 입력되게 한다. 기존 Django 일정 등록/개인 일정 등록 fallback은 선택 날짜를 포함해 유지한다.

### 확인된 상태

- React 일정 캘린더는 월간 grid, 선택일 패널, Django 캘린더 fallback을 이미 제공한다.
- 현재 캘린더 상단 `일정 등록`은 Django `/reporting/schedules/create/`로 이동해 React CRM 전환 흐름이 끊긴다.
- Django 고객 일정 생성과 개인 일정 생성은 이미 `?date=YYYY-MM-DD` 초기값을 지원한다.
- React 일정 빠른 등록은 `?create=1`과 `?customer=`만 처리하고 `?date=`는 읽지 않는다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- React URL helper에 `date` query 검증 함수를 추가한다.
- React `/schedules/?create=1&date=YYYY-MM-DD`에서 빠른 등록 패널의 방문 날짜를 query 날짜로 초기화한다.
- React 캘린더 상단 `일정 등록`과 선택일 패널의 `고객 일정 등록`은 React 빠른 등록 링크로 연결한다.
- 선택일 패널의 `개인 일정 등록`과 `Django 상세 등록` fallback은 기존 Django URL에 선택 날짜 query를 붙인다.
- `/reporting/*` 일정/개인 일정 fallback과 API 권한 정책은 그대로 유지한다.

### 검증 계획

- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/schedules/calendar/`, `/schedules/?create=1&date=YYYY-MM-DD` smoke check

---

## Current task — AI 납품 품목 노출, 리스트 최신순, 주간보고 상세 저장 줄바꿈 보존

**목표**: React `/ai-workspace/?department_id=10`의 Department AI 패널에서 최근 납품 제품/수량을 확인하게 하고, React CRM 주요 리스트의 기본 정렬을 최신순으로 맞춘다. 이어서 `/weekly-reports/<id>/` 수정 저장 시 textarea 줄바꿈이 사라지지 않게 한다.

### 확인된 상태

- 부서 AI 분석 수집 로직은 `quote_delivery_data.deliveries`에 최근 납품 일정과 품목(product, quantity, unit_price, total_price)을 이미 저장한다.
- React 고객형 AI 패널은 총 견적/납품 지표와 제품 통계만 표시하고, 최근 납품 품목 상세는 payload/type/UI에서 빠져 있다.
- `/reporting/api/schedules/`의 기본 일정 목록은 오름차순 날짜 정렬이며, 고객 목록도 우선순위/AI점수 우선 정렬이라 기본 리스트가 최신순으로 느껴지지 않는다.
- React 주간보고 수정 화면은 저장 후 상세로 이동하지만, HTML을 다시 textarea 텍스트로 변환하는 과정에서 일부 줄바꿈이 보존되지 않을 수 있다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- AI 부서/고객 상세 payload의 `quoteDelivery`에 `recentDeliveries`를 추가한다.
  - 최근 납품일 기준으로 최대 몇 건만 내려주고, 각 납품의 제품명/수량/금액/고객/출처를 포함한다.
  - 기존 총계, 제품 통계, PainPoint 검증 payload는 유지한다.
- React 타입과 빈 payload 정규화를 확장하고 `CustomerAiResultPanel`의 견적/납품 분석 섹션에 `최근 납품 품목` 리스트를 추가한다.
- `/reporting/api/schedules/` 기본 목록과 주요 React 고객 목록을 최신 수정/일자 기준 내림차순으로 조정한다.
  - 캘린더/다가오는 일정처럼 시간 흐름이 중요한 보조 목록은 기존 의도를 훼손하지 않는다.
- 주간보고 HTML→textarea 변환이 `<br>` 및 문단 경계를 안정적으로 줄바꿈으로 복원하게 보강한다.
- 관련 API 회귀 테스트를 추가/보강한다.

### 검증 계획

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.CustomersSummaryApiTests reporting.tests.SchedulesSummaryApiTests reporting.tests.WeeklyReportReactApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/?department_id=10`, `/schedules/`, `/weekly-reports/2/` smoke check

---

## Previous task — React 주간보고 줄바꿈 표시 보존

**목표**: React `/weekly-reports/`에서 주간보고를 저장한 뒤 상세 화면에서 사용자가 입력한 줄바꿈이 그대로 보이게 한다.

### 확인된 상태

- React 주간보고 작성/수정 화면은 일반 `textarea`로 `activityNotes`, `quoteDeliveryNotes`, `otherNotes`를 저장한다.
- Django React API는 plain text 줄바꿈을 `<br>`/`<p>` HTML로 정규화해 저장하고, 상세 payload에 `activityNotesHtml` 등으로 내려준다.
- React 상세 화면은 `dangerouslySetInnerHTML`로 주간보고 본문을 렌더링하지만, CSS가 raw newline text node와 관리자 코멘트 줄바꿈을 보존하도록 명시하지 않는다.
- DB 변경은 필요하지 않다.

### 구현 계획

- 주간보고 본문 표시 CSS에 `white-space: pre-wrap`을 적용해 저장 HTML 안의 raw newline도 접히지 않게 한다.
- 관리자 검토 코멘트 `<p>`도 같은 방식으로 줄바꿈을 보존한다.
- React API 회귀 테스트에 저장 응답/상세 응답의 `<br>` 보존 확인을 추가한다.
- 기존 Django 주간보고 fallback, API 권한, 저장 방식은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.WeeklyReportReactApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/weekly-reports/` smoke check

---

## Current task — AI Workspace 부서 선택 React 전환

**목표**: React `/ai-workspace/`의 `부서 분석 대상` 클릭이 Django AI 허브로 이동하지 않고, 같은 React 화면 오른쪽 `Department AI` 패널을 해당 부서 분석 결과로 전환하게 한다.

### 확인된 상태

- 현재 `AIWorkspaceDepartmentList`는 부서 행을 `department.hubHref` 링크로 렌더링해 클릭 시 `/ai/?department=...` Django 화면으로 이동한다.
- `/reporting/api/ai-workspace/`는 최신 분석 부서를 `featuredDepartment`로 내려주지만, 특정 부서를 선택하는 query parameter는 없다.
- 부서 데이터 범위는 현재 요청자 본인 FollowUp 기반으로 제한되어 있으며, 이 권한 범위는 유지해야 한다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- `/reporting/api/ai-workspace/`에 `department_id` query parameter를 추가한다.
  - 요청자가 접근 가능한 부서 ID일 때만 해당 부서를 `featuredDepartment`로 내려준다.
  - 접근 불가/잘못된 ID는 기존 최신 분석 부서 fallback을 유지해 내부 데이터 노출을 막는다.
- React API client `loadAIWorkspaceData`가 선택 부서 ID를 query string으로 전달하게 한다.
- React `/ai-workspace/`가 URL의 `department_id` 초기값을 읽고, 부서 행 클릭 시 `history.replaceState`와 API refresh로 같은 화면에서 오른쪽 패널만 바꾸게 한다.
- 선택된 부서 행은 시각적으로 표시하고, 기존 Django fallback 링크/명시적 실행 버튼은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke check

---

## Current task — AI Workspace 작업 큐 보조화

**목표**: React `/ai-workspace/`의 `AI 작업 큐`를 메인 상단에서 내리고, 오른쪽 `Department AI` 결과 패널 중심의 흐름을 유지한다.

### 확인된 상태

- 기존 `AI 작업 큐`는 자동 실행 큐가 아니라 복사해서 활용하는 프롬프트 카드 목록이다.
- 현재는 지표 바로 아래 상단에 크게 노출되어 오른쪽 AI 결과 패널보다 먼저 보인다.
- 사용자는 오른쪽 고객형 AI 환경을 선호하고, 부서 분석 대상은 이미 검색/5개 제한으로 정리했다.
- DB/API 변경은 필요하지 않고 React 배치와 명칭만 조정하면 된다.

### 구현 계획

- 상단의 `AI 작업 큐` 패널을 제거한다.
- 같은 `AIWorkspacePromptQueue` 기능은 왼쪽 본문 하단의 보조 섹션으로 유지한다.
- 표시 명칭을 `추천 질문`으로 바꾸어 복사 프롬프트 성격을 분명히 한다.
- 기존 복사 버튼, 카드 내용, API payload는 유지한다.

### 검증 계획

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke check

---

## Current task — AI Workspace 부서 분석 대상 검색/5개 제한

**목표**: React `/ai-workspace/`의 `Department analysis / 부서 분석 대상` 목록을 화면상 5개로 제한하고 검색으로 필요한 부서를 찾게 한다.

### 확인된 상태

- `/reporting/api/ai-workspace/`는 사용자의 AI 분석 대상 부서를 모두 내려준다.
- React `AIWorkspaceDepartmentList`는 현재 전달받은 부서를 전부 렌더링한다.
- DB/API 변경은 필요하지 않고 프론트 표시 로직만 조정하면 된다.

### 구현 계획

- `AIWorkspaceDepartmentList`에 검색 input을 추가한다.
- 회사명, 부서명, 고객 preview, AI 요약을 검색 대상으로 삼는다.
- 검색 결과는 항상 상위 5개만 표시한다.
- 전체/검색 결과/표시 건수를 작은 메타 텍스트로 보여준다.

### 검증 계획

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke check

---

## Current task — React AI 업무도구 고객형 AI 패널 정리

**목표**: 운영 `/ai-workspace/` 화면을 고객 상세 오른쪽 AI 패널과 같은 형태로 정리해, 최근 부서 AI 분석 결과와 PainPoint 검증 메모를 한 화면에서 판단하게 한다.

### 확인된 상태

- React `/ai-workspace/`는 현재 AI 작업 큐, 부서 목록, 검증 대기 PainPoint 목록 중심의 업무 대시보드다.
- React 고객 상세 오른쪽 AI 영역은 `CustomerAiResultPanel`로 분석 기간, 미팅/견적/납품 인사이트, 검증 기반 인사이트, 다음 액션, 확인 필요 사항, PainPoint 검증 메모를 한 흐름으로 보여준다.
- `/reporting/api/ai-workspace/`는 부서/작업 큐/검증 대기 목록은 제공하지만 고객 상세 AI 패널에 필요한 대표 부서 분석 상세 payload는 제공하지 않는다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- `/reporting/api/ai-workspace/` 응답에 최신 부서 AI 분석을 `featuredDepartment`로 추가한다.
  - 기존 고객 상세 AI payload helper를 재사용해 미팅/견적/납품/검증/다음 액션/PainPoint 데이터를 동일한 구조로 내려준다.
  - 최신 분석이 없으면 첫 분석 대상 부서를 빈 AI 결과 payload로 내려주고, AI 권한이 없거나 대상 부서가 없으면 `featuredDepartment: null`을 반환한다.
- React API 타입에 `AIWorkspaceFeaturedDepartment`를 추가하고 `/ai-workspace/` loader에서 정규화한다.
- React `/ai-workspace/` 화면 오른쪽에 고객 상세와 동일한 `CustomerAiResultPanel`을 배치한다.
  - PainPoint 검증은 기존 단일 `확인` 메모 저장 API를 그대로 사용한다.
  - 저장 후 `/ai-workspace/` 데이터를 새로고침해 검증 상태를 즉시 반영한다.
- 기존 부서 목록, 작업 큐, 전체 검증 대기 목록은 보존해 업무 대시보드 기능을 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` smoke check

---

## Current task — React 서류 템플릿 관리 1차 통합

**목표**: 기존 Django `/reporting/documents/` 서류 템플릿 관리 화면을 fallback으로 유지하면서 React CRM에 `/documents/` 관리 화면을 추가해 일정 상세의 서류 다운로드 workflow를 React 안에서 완결한다.

### 긴급 인터럽트 반영 — AI PainPoint 검증 메모 단일화

- PainPoint 검증 UI/API에서 사용자가 `확인`/`부정`을 고르지 않게 한다.
- 사용자는 검증 메모만 저장하고, AI가 다음 재분석에서 메모 내용을 읽어 사실 확인/반박/대체 원인을 판단한다.
- 기존 DB의 `verification_status` 컬럼은 호환성을 위해 유지하지만, 프롬프트와 서버 fallback은 더 이상 `confirmed`/`denied` 의미를 해석하지 않는다.
- 기존 `denied` 카드도 재분석 메모리에서는 `검증 메모`로 취급해 과거 데이터가 부정/확정 의미로 고정되지 않게 한다.
- React 고객 상세와 Django fallback 부서 분석 화면 모두 버튼을 `확인` 하나로 정리한다.

### 긴급 인터럽트 반영 — AI 부서 미팅 범위

- 확인 결과 `ai_chat.services.gather_meeting_data()`가 `department + user` 조건으로 요청자 개인 담당 고객 미팅만 수집하고 있었다.
- 부서 AI 분석 의도에 맞게 `department` 전체 FollowUp의 고객 미팅을 수집하도록 수정한다.
- 부서 전체 미팅이 프롬프트에 섞일 때 출처가 흐려지지 않도록 미팅 항목 제목에 담당자명을 표시한다.
- 견적/납품/메일 수집 범위는 이번 긴급 요청 범위가 아니므로 기존 정책을 유지한다.
- 회귀 테스트로 같은 부서의 동료 담당 고객 미팅이 수집 및 AI 프롬프트에 포함되는지 검증한다.

### 확인된 상태

- 기존 서류 템플릿은 `DocumentTemplate` 모델을 사용하며 `quotation`, `transaction_statement`, `delivery_note` 3종류를 지원한다.
- 기존 Django 목록/등록/수정/삭제/기본 설정/다운로드 URL은 `/reporting/documents/*`에 있다.
- 등록/수정/삭제는 admin/manager 권한이며, 목록/다운로드는 같은 회사 범위에서 조회한다.
- React 일정 상세는 문서 미리보기와 PDF/Excel 생성을 지원하지만 템플릿 관리는 Django fallback 링크로만 이동한다.
- 신규 DB 필드나 migration은 필요하지 않다.

### 구현 계획

- `/reporting/api/documents/` React용 JSON API를 추가한다.
  - 서류 종류 필터, 회사 범위, 유형별/기본 템플릿 수, 관리 가능 여부, Django fallback 링크를 반환한다.
- `/reporting/api/documents/create/`, `/reporting/api/documents/<id>/update/`, `/reporting/api/documents/<id>/delete/`, `/reporting/api/documents/<id>/toggle-default/` API를 추가한다.
  - 기존 `DocumentTemplate` 파일 업로드, soft delete, 기본 템플릿 단일화 정책을 재사용한다.
  - 인증/회사 범위/역할 권한을 유지한다.
- React API client에 문서 템플릿 타입, 목록 로더, 생성/수정/삭제/기본 설정 mutation을 추가한다.
- React `/documents/` route와 사이드바 메뉴를 추가한다.
  - 유형별 필터, 요약 카드, 템플릿 목록, 다운로드, 기본 설정, 등록/수정 패널, 삭제 버튼을 제공한다.
  - 기존 Django `/reporting/documents/` 링크를 fallback으로 유지한다.
- React 일정 상세의 템플릿 관리 링크는 `/documents/`로 전환하고, React 문서 화면에서 Django fallback을 제공한다.

### 검증 계획

- `python manage.py test reporting.tests.DocumentTemplatesReactApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/documents/` bundle/API smoke check

---

## Current task — React 일정 상세 문서 생성 1차 통합

**목표**: 기존 Django 일정 상세의 견적서/거래명세서/납품서 생성 workflow를 React 일정 상세(`/schedules/<id>/`)에 추가한다. Django 서류 템플릿 관리와 생성 endpoint는 backend/fallback으로 유지한다.

### 확인된 상태

- 기존 Django 일정 상세(`/reporting/schedules/<id>/`)에는 활동 유형에 따라 견적서, 거래명세서, 납품서 PDF/Excel 생성 버튼과 변수 미리보기가 있다.
- 서류 템플릿은 `DocumentTemplate`, 생성 로그는 `DocumentGenerationLog`, 품목은 `DeliveryItem`을 사용한다.
- 기존 생성 endpoint는 `/reporting/documents/generate/<document_type>/<schedule_id>/<output_format>/`이고, 변수 미리보기 endpoint는 `/reporting/documents/template-data/<document_type>/<schedule_id>/`이다.
- React 일정 상세는 납품 품목/첨부파일/선결제 편집은 지원하지만 서류 생성 UI가 없다.
- 이번 작업은 React UI/API client와 일정 상세 payload 확장이다. DB 모델 변경은 필요하지 않다.

### 구현 계획

- React 일정 상세 API payload에 활동 유형별 문서 생성 action을 추가한다.
  - 견적 일정(`quote`): 견적서
  - 납품 일정(`delivery`): 거래명세서, 납품서
  - 각 문서별 PDF/Excel 생성 URL과 변수 미리보기 URL을 내려준다.
- React API client에 문서 다운로드 POST와 변수 미리보기 GET helper를 추가한다.
- React 일정 상세 오른쪽 패널에 문서 생성 섹션을 추가한다.
  - PDF/Excel 다운로드 버튼을 제공한다.
  - 변수 미리보기는 React 패널에서 템플릿 변수, 값, 품목 개수를 확인하게 한다.
  - 서류 템플릿 관리 Django fallback 링크를 유지한다.
- 기존 Django 서류 생성 endpoint와 템플릿 관리 화면은 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/<id>/` bundle/API smoke check

---

## Current task — React 일정 캘린더 1차 통합

**목표**: 기존 Django `/reporting/schedules/calendar/` 화면을 fallback으로 유지하면서 React CRM에 `/schedules/calendar/` 캘린더 route를 추가해 일정 업무의 프론트 통합 범위를 넓힌다.

### 확인된 상태

- React 일정 목록/상세/빠른 등록 화면은 이미 `/schedules/`와 `/schedules/<id>/`에서 동작한다.
- 기존 Django 캘린더는 `/reporting/schedules/calendar/`와 `/reporting/schedules/api/`를 사용하며 고객 일정과 개인 일정을 함께 표시한다.
- React 일정 목록 API(`/reporting/api/schedules/`)는 목록용 80건 제한 payload라 월간 캘린더에는 별도 날짜 범위 API가 필요하다.
- 기존 모델(`Schedule`, `PersonalSchedule`)로 충분하며 DB 모델 변경은 필요하지 않다.

### 구현 계획

- `/reporting/api/schedules/calendar/` 읽기 API를 추가한다.
  - `start`, `end`, `data_filter`, `filter_user`를 받아 월간 캘린더 날짜 범위의 고객 일정/개인 일정을 반환한다.
  - 기존 Django 캘린더와 동일하게 본인, 같은 회사 전체, 특정 직원 필터를 지원한다.
  - 일정 목록과 동일한 React payload helper를 재사용해 상세/고객/legacy 링크를 유지한다.
- React API client에 캘린더 데이터 타입과 loader를 추가한다.
- React `/schedules/calendar/` route를 추가한다.
  - 월 이동, 오늘 이동, 본인/전체/직원 필터, 월간 grid, 선택 일자 목록을 제공한다.
  - 고객 일정은 React 상세로, 개인 일정은 기존 Django 개인 일정 상세로 연결한다.
  - Django 캘린더 링크는 fallback으로 유지한다.
- 기존 일정 목록의 캘린더 링크를 React route로 전환하되 Django 일정 목록/캘린더 fallback 링크를 함께 보존한다.

### 검증 계획

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/schedules/calendar/`, `/reporting/api/schedules/calendar/` smoke check

---

## Current task — React 주간보고 1차 통합

**목표**: 기존 Django `/reporting/weekly-reports/*` 화면을 유지하면서 React CRM에 주간보고 목록, 상세, 작성, 수정 route를 추가해 프론트 통합 범위를 넓힌다.

### 확인된 상태

- 주간보고 모델(`WeeklyReport`)과 Django 템플릿 목록/작성/수정/상세 화면은 운영 중이다.
- 일정 불러오기, 견적/납품 금액 포함, AI 초안, 관리자 검토 코멘트 API는 이미 Django에 있다.
- React CRM은 대시보드/고객/파이프라인/노트/일정/메일/선결제/AI를 담당하지만 주간보고 독립 route가 없다.
- 이번 작업은 React 통합과 JSON API 추가이며 DB 모델 변경은 필요하지 않다.

### 구현 계획

- `/reporting/api/weekly-reports/` 목록 API를 추가한다.
  - 기존 목록 권한과 동일하게 실무자는 본인 보고서만, 관리자/어드민은 같은 회사 사용자의 보고서를 조회한다.
  - 연도, 월, 작성자 필터와 검토/미검토 지표, 작성자 선택 옵션을 반환한다.
- `/reporting/api/weekly-reports/create/`, `/reporting/api/weekly-reports/<id>/`, `/update/`, `/delete/` API를 추가한다.
  - 작성/수정은 본인 보고서만 허용한다.
  - 관리자 검토 코멘트 API는 기존 경로를 계속 사용한다.
  - React textarea 입력은 서버에서 안전한 HTML 문단으로 변환해 줄바꿈 가독성을 보존한다.
- React에 `/weekly-reports/`, `/weekly-reports/new/`, `/weekly-reports/<id>/`, `/weekly-reports/<id>/edit/` route를 추가한다.
  - 목록 필터, 상세 HTML 렌더링, 관리자 검토, 작성/수정 폼, 일정 불러오기, AI 초안 버튼을 제공한다.
  - 기존 Django 주간보고 화면 링크는 보조/fallback으로 유지한다.
- 대시보드, 영업노트, 일정, AI 업무도구에서 주간보고 링크를 React route로 전환한다.

### 검증 계획

- `python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportReactApiTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/weekly-reports/` smoke check

---

## Current task — React 고객/부서 검색 선택 UX

**목표**: React CRM의 메일 작성, 고객 등록/수정, 영업노트 작성/수정, 일정 작성/수정, 선결제 등록/수정에서 고객·업체·부서를 Django 화면처럼 검색해서 선택하게 한다.

### 확인된 상태

- 기존 React 주요 작성/수정 폼은 고객·부서 선택에 기본 `<select>`를 사용해 목록이 길어질수록 선택이 어렵다.
- Django 운영 화면은 select2/search 기반 선택 UX가 있어 고객/부서 검색이 가능했다.
- 이번 작업은 React UI 컴포넌트 교체이며, API payload와 DB 모델 변경은 필요하지 않다.

### 구현 계획

- React 공통 `SearchableSelect` 컴포넌트를 추가한다.
- 고객, 업체/학교, 부서/연구실 option 변환 helper를 만들어 화면별 payload 차이를 흡수한다.
- 다음 화면의 고객·업체·부서 선택을 검색형으로 교체한다.
  - 메일 작성의 연결 고객
  - 고객 빠른 등록/고객 상세 수정의 업체·부서
  - 영업노트 빠른 작성/상세 수정의 고객
  - 일정 빠른 등록/상세 수정의 고객
  - 선결제 등록/수정의 고객
- 필터/상태/활동유형처럼 단순 범주 선택은 기존 select를 유지한다.

### 검증 계획

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 번들 smoke check

---

## Current task — React 메일함 1차 통합

**목표**: 프론트 통합 로드맵의 1단계로 고객 메일함을 React CRM에 추가하고, 기존 Django Gmail/IMAP/EmailLog 로직은 API/backend 역할로 유지한다.

### 확인된 상태

- 기존 메일함은 `reporting.gmail_views`의 Django 템플릿 화면과 `EmailLog` 모델을 중심으로 동작한다.
- Gmail/IMAP 연결, 발송, 답장, 중요표시, 보관, 휴지통, 삭제 로직은 이미 Django에 있다.
- React는 대시보드/고객/노트/일정/선결제/AI/파이프라인을 담당하지만 메일함 route는 없었다.
- DB 모델 변경 및 migration 필요 없음.

### 구현 계획

- `/reporting/api/mailbox/*` JSON API를 추가해 목록, 스레드 상세, 발송, 답장, 동기화, 중요표시/보관/휴지통/복원/삭제 액션을 제공한다.
- API 권한은 본인이 보낸 메일, 본인 고객/일정에 연결된 메일만 대상으로 제한한다.
- React에 `/mailbox/` 목록, `/mailbox/thread/<thread_id>/` 상세/답장 화면을 추가한다.
- 공통 사이드바에 `메일` 메뉴를 추가하고, 메일 작성/동기화/고객 연결/명함 선택을 React에서 처리한다.
- 기존 Django 메일함은 fallback으로 유지하고, 운영 검수 전 강제 redirect는 적용하지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.GmailMailboxThreadRegressionTests --verbosity=2`
- `python -m py_compile reporting\gmail_views.py reporting\urls.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/mailbox/` smoke check

---

## Current urgent task — Railway 메일 스레드 500 복구

**목표**: Railway 운영 로그에서 발생 중인 `/reporting/mailbox/thread/<thread_id>/` 500 오류를 제거해 Gmail/메일함 스레드 상세 화면이 다시 렌더링되게 한다.

### 확인된 상태

- Railway `web`, `sales-note-frontend` 배포 상태는 SUCCESS/Online.
- 실제 오류는 백엔드 Django 템플릿 렌더링 단계의 `TemplateSyntaxError: Unclosed tag on line 321: 'block'`이다.
- 같은 요청 흐름에서 Gmail 스레드 신규 메시지 동기화 시 `reporting.imap_utils.save_email_to_db` import 실패도 반복된다.
- DB 필드 변경 및 migration 필요 없음.
- 구현/로컬 검증/푸시/Railway `web` 운영 배포 완료.
- Railway `web`의 `EMAIL_ENCRYPTION_KEY` 미설정 error 로그도 환경변수 설정으로 제거했다.

### 구현 계획

- `reporting/templates/reporting/gmail/thread_detail.html`의 미종료 JS/template block을 정상 종료한다.
- Gmail thread 동기화용 `save_email_to_db()` helper를 기존 `EmailLog` 모델 필드에 맞게 구현한다.
- Gmail 메시지 본문 저장 시 `body_text`/`snippet` fallback을 사용해 빈 본문 저장을 줄인다.
- 템플릿 컴파일과 Gmail 메시지 저장 회귀 테스트를 추가한다.

### 검증 계획

- `python manage.py test reporting.tests.GmailMailboxThreadRegressionTests --verbosity=2`
- `python -m py_compile reporting\imap_utils.py reporting\gmail_views.py reporting\tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/mailbox/thread/.../` 500 로그 재발 여부 확인

---

## Current urgent task — PainPoint 검수 메모 AI 요약 반영

**목표**: 사용자가 PainPoint 검수 단계에서 남긴 확인/부정 메모가 다음 부서 AI 재분석 결과의 `department_summary`에 반드시 포함되게 한다.

### 확인된 상태

- 기존 구현은 검증 메모리를 GPT 프롬프트, `verification_insights`, `next_actions`, `missing_info`에 반영한다.
- 시스템 프롬프트도 `department_summary`에 검증 메모를 반영하라고 지시한다.
- 다만 GPT가 요약에서 검증 메모를 약하게 반영하거나 누락할 경우 서버 fallback이 `department_summary`까지 보정하지는 않는다.
- DB 변경 필요 없음.
- 구현/로컬 검증/푸시/Railway `web` 운영 배포 완료.
- 운영 anonymous `/ai/`는 `/reporting/login/?next=/ai/`로 redirect되어 인증 보호 유지 확인.

### 구현 계획

- `ai_chat.services.apply_verification_memory_to_analysis_result()`에서 검증 메모 핵심 문장을 `department_summary`에 deterministic fallback으로 추가한다.
- 이미 요약에 해당 검증 메모가 포함되어 있으면 중복으로 덧붙이지 않는다.
- confirmed/denied 상태를 구분해 "확인된 사항" 또는 "부정된 가설"로 요약에 반영한다.
- 기존 `verification_insights`, `next_actions`, `missing_info` 보정 흐름은 유지한다.

### 검증 계획

- `python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python -m py_compile ai_chat/services.py ai_chat/tests.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 AI API login 보호 smoke check

---

## Current urgent task — 고객 메일 AI 분석 컨텍스트 반영

**목표**: 고객과 주고받은 메일, 특히 고객이 보낸 답장/문의 메일을 부서 AI 분석 근거에 포함해 PainPoint, 요약, 다음 액션 판단에 활용한다.

### 확인할 상태

- 기존 Gmail/IMAP/EmailLog 저장 모델과 FollowUp/Department 연결 방식을 먼저 확인한다.
- 메일 본문은 AI 프롬프트에 넣기 전 제목/방향/발신자/수신자/일시/요약 본문만 제한 길이로 정리한다.
- 내부 영업 데이터와 인증/권한 범위는 기존 부서 AI 권한 정책을 유지한다.
- 신규 DB 필드가 필요한지 확인하되, 우선 기존 메일 로그 저장 데이터를 활용한다.
- 구현/로컬 검증/푸시/Railway `web` 운영 배포 완료. `EmailLog`의 `followup`/`schedule.followup` 연결을 통해 사용자 담당 고객 범위 안에서만 수집한다.

### 구현 계획

- `EmailLog` 또는 기존 메일 저장 모델에서 선택 고객/부서와 연결된 최근 메일을 수집하는 helper를 추가한다.
- 고객 inbound 메일을 우선 정렬/강조하고, outbound 메일은 맥락 보조 자료로 제한한다.
- 부서 AI 프롬프트에 `고객 메일/답장 컨텍스트` 섹션을 추가한다.
- GPT 응답 계약 또는 서버 fallback에 메일 기반 다음 액션이 누락되지 않도록 보정한다.
- 단위 테스트로 inbound 메일 문구가 AI 프롬프트와 다음 액션 판단 근거에 포함되는지 검증한다.

### 검증 계획

- `python manage.py test ai_chat.tests --verbosity=1`
- 필요 시 `python manage.py test reporting.tests.*Email* --verbosity=1`
- `python -m py_compile ai_chat/services.py reporting/models.py`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 login 보호 smoke check

---

## Current urgent task — 고객 단계별 다음 액션 AI 보고

**목표**: AI 분석 시 고객 단계에 따라 다음 액션을 다르게 산출한다. 락인 고객은 수주 관련 다음 액션, 견적 고객은 견적/미팅/메일 답장 기반 다음 액션, 미팅만 한 고객은 미팅/메일 답장 기반 다음 액션을 보고한다.

### 구현 계획

- FollowUp `pipeline_stage`와 연결 견적/미팅/메일 기록으로 고객 분석 단계를 판별한다.
- `won`/락인 성격 고객은 수주 이후 확장, 납품, 후속 구매, 리텐션 중심 액션을 우선한다.
- 견적 단계 고객은 견적 내용, 미팅 내용, 고객 메일 답장을 함께 보고 가격/조건/일정/의사결정자 확인 액션을 만든다.
- 미팅만 있는 고객은 미팅 기록과 메일 답장을 기반으로 요구사항 확인, 자료 전달, 다음 미팅/견적화 액션을 만든다.
- 검증 메시지는 분석 이후에도 우선 근거로 활용하며, 기존 검증 메모 summary fallback과 충돌하지 않게 통합한다.
- 구현/로컬 검증/푸시/Railway `web` 운영 배포 완료. 부서 AI는 `next_actions`, 개별 고객 AI는 `next_best_actions`에 단계별 fallback 액션을 보강한다.

### 검증 계획

- 고객 단계별 AI 프롬프트/서버 fallback 테스트 추가
- `python manage.py test ai_chat.tests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Current urgent task — React 파이프라인 우측 부서 AI 노출

**목표**: React 파이프라인에서 고객 카드를 선택했을 때 우측 상세 패널에 해당 고객의 부서 AI 분석 요약을 표시한다.

### 확인된 상태

- 파이프라인 데이터는 `/reporting/api/pipeline/`의 deal payload로 우측 패널을 구성한다.
- 고객 상세 API에는 이미 부서 AI 분석 권한/요약/링크 payload가 있다.
- 이번 작업은 파이프라인 우측 패널에 compact AI 요약을 추가하는 작업이며, AI 실행/검증 전체 UI는 고객 상세 화면과 AI 허브에 계속 둔다.
- DB 변경 필요 없음.
- 구현/로컬 검증/푸시/Railway `web`, `sales-note-frontend` 운영 배포 완료.
- 운영 번들 `assets/index-CLXRI0TH.js` / `assets/index-AuyH7qvg.css`에서 `Department AI`, `aiDepartment`, `pipeline-ai-card`, `pipeline-ai-alert` 확인 완료.

### 구현 계획

- `pipeline_command_center_api`의 각 deal payload에 `aiDepartment` compact payload를 추가한다.
- 권한은 기존 고객 상세 AI 정책과 동일하게 `can_use_ai`와 본인 담당 부서 여부를 기준으로 한다.
- React `Deal` 타입에 `aiDepartment` 필드를 추가한다.
- React `DetailPanel`에서 고객 선택 시 `Department AI` 카드, 분석 요약, 미팅/견적/납품/PainPoint 카운트, AI 허브/Django 보기 링크를 표시한다.
- 기존 파이프라인 단계 이동, 견적/납품 금액, Django 고객 상세 링크는 유지한다.

### 검증 계획

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/dashboard/`/파이프라인 번들 smoke check

---

## Current urgent task — React 대시보드 로그아웃 버튼 추가

**목표**: 운영 React `/dashboard/` 및 공통 CRM 화면에서 사용자가 바로 로그아웃할 수 있게 한다.

### 확인된 상태

- Django 로그아웃 URL은 기존 `/reporting/logout/`로 제공된다.
- React production frontend는 `/reporting/*` 요청을 같은 프론트 도메인에서 Django backend로 프록시한다.
- Django 5 로그아웃은 GET 링크보다 CSRF 포함 POST가 안전하므로 React 버튼에서 POST 요청으로 처리한다.
- DB 변경 필요 없음.
- 구현/로컬 검증/푸시/Railway `sales-note-frontend` 운영 배포 완료.
- 운영 번들 `assets/index-cLy6Pc7s.js` / `assets/index-D1AABLev.css`에서 `로그아웃`, `/reporting/logout/`, `X-CSRFToken`, `logout-button` 확인 완료.
- 사용자 운영 수동검수 완료: 2026-05-10.

### 구현 계획

- React 공통 `TopBar`에 로그아웃 아이콘 버튼을 추가해 `/dashboard/` 포함 모든 React CRM 화면에서 접근 가능하게 한다.
- `csrftoken` 쿠키를 읽어 `/reporting/logout/`에 `POST` 요청을 보내고, 성공/리다이렉트 후 `/reporting/login/`으로 이동한다.
- 로그아웃 요청 실패 시에도 로그인 페이지로 보내되, 오류는 콘솔에만 남겨 운영 UI를 막지 않는다.
- 기존 Django `/reporting/*` 로그아웃 경로와 인증 흐름은 유지한다.

### 검증 계획

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `git diff --check`
- 커밋/푸시 후 Railway `sales-note-frontend` 배포 및 운영 `/dashboard/` 번들 smoke check

---

## Current task — React 고객 상세 선결제 요약 통합

**목표**: React 고객 상세(`/customers/<customer_id>/`)에서 해당 고객의 선결제 총액, 사용액, 잔액, 최근 선결제 이력을 바로 확인하게 한다.

### 진행 상태

- 구현, 로컬 검증, GitHub push, Railway `web`/`sales-note-frontend` 운영 배포 완료.
- 배포된 운영 번들: `assets/index-VVc8nVTe.js` / `assets/index-COYknf0t.css`.
- 운영 비로그인 API smoke: `/reporting/api/customers/1/`는 frontend proxy와 backend 모두 `401 login_required`.
- 사용자 운영 수동검수 대기 중.
- 수동검수 확인 전에는 다음 React 전환 구현을 시작하지 않는다.

### 확인된 상태

- React 선결제 목록, 등록, 상세, 수정, 취소, 삭제, 이관, 고객별/부서별 화면은 배포 후 사용자가 수동검수를 완료했다.
- 고객 상세 API는 이미 `can_access_followup()` 권한 확인 후 같은 사용자 범위(`scope_users`)의 노트/일정을 집계한다.
- 고객별 선결제 전체 화면은 `/prepayments/customer/<customer_id>/`로 제공되며 Django fallback `/reporting/prepayment/customer/<customer_id>/`와 엑셀 다운로드는 유지된다.
- 이번 작업은 고객 상세의 요약 노출이며, 선결제 모델/DB 필드 추가는 필요하지 않다.

### 구현 계획

- `/reporting/api/customers/<customer_id>/` payload에 `prepaymentSummary`를 추가한다.
  - 고객 상세에서 이미 검증한 고객만 대상으로 한다.
  - 선결제 데이터는 해당 고객 + `scope_users` 범위로 제한한다.
  - 총액, 잔액, 사용액, 전체/활성/소진/취소 건수와 최근 선결제 목록을 반환한다.
  - React 고객별 선결제, React 선결제 목록, Django 고객별 선결제 링크를 함께 반환한다.
- React `CustomerDetailData` 타입과 fallback 데이터를 확장한다.
- React 고객 상세 우측 영역에 선결제 요약 패널을 추가한다.
  - 총액/잔액/사용액/건수 요약.
  - 최근 선결제 5건, 상태, 결제일, 입금자, 잔액 표시.
  - 고객별 선결제 전체 화면 및 Django fallback 링크 제공.
- 신규 migration은 만들지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.PrepaymentCustomerApiTests reporting.tests.PrepaymentDetailApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Previous task — React 고객별/부서별 선결제 화면 전환

**목표**: 기존 Django `/reporting/prepayment/customer/<customer_id>/` 운영 화면을 유지하면서 React CRM에서 고객별(실제로는 같은 부서 전체) 선결제 현황을 확인할 수 있게 한다.

### 확인된 상태

- React 선결제 목록, 등록, 상세, 수정, 취소, 삭제, 이관은 배포 후 사용자가 수동검수를 완료했다.
- 기존 Django `prepayment_customer_view`는 URL의 고객을 기준으로 부서를 찾고, 부서가 있으면 같은 부서 전체 고객의 선결제를 보여준다.
- Salesman 접근 규칙은 고객 담당자이거나 해당 고객에 본인이 등록한 선결제가 있는 경우만 허용한다.
- Admin/Manager는 접근 가능하며, `selected_user_id` 세션 필터가 있으면 해당 접근 가능 사용자의 선결제를 본다.
- 기존 Django 엑셀 다운로드 `/reporting/prepayment/customer/<customer_id>/excel/`은 유지한다.
- DB 필드 추가는 필요하지 않다.

### 구현 계획

- React용 고객별 선결제 API를 추가한다.
  - `/reporting/api/prepayments/customer/<customer_id>/`
  - 권한 규칙은 기존 Django view와 동일하게 유지한다.
  - 기준 고객, 회사/부서, 부서 내 고객 목록, target owner, 상태별/금액별 지표, 선결제 목록, Django fallback/엑셀 링크를 반환한다.
- React 라우팅을 추가한다.
  - `/prepayments/customer/<customer_id>/`
  - 선결제 목록과 상세 화면의 `고객별` 링크를 React 경로로 전환한다.
  - Django 고객별/엑셀 fallback 링크는 별도 유지한다.
- 고객별 화면 UI를 추가한다.
  - 부서/고객 컨텍스트, 총액/사용액/잔액/건수, 상태별 카운트, 같은 부서 고객 목록, 선결제 테이블.
  - 각 선결제는 React 상세와 Django 상세로 이동 가능.
- 신규 migration은 만들지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentCustomerApiTests --verbosity=1`
- `python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Previous task — React 선결제 삭제/취소/이관 전환

**목표**: 기존 Django `/reporting/prepayment/*` 운영 화면을 유지하면서 React 선결제 상세 화면에서 삭제, 취소, 이관까지 처리할 수 있게 한다.

### 확인된 상태

- React 선결제 목록, 등록, 상세, 수정은 배포 후 사용자가 수동검수를 완료했다.
- 기존 Django `prepayment_delete_view`는 등록자 본인만 취소/삭제 가능하다.
  - `action=cancel`이면 사용 내역 여부와 관계없이 `status=cancelled`, `cancelled_at`, `cancel_reason`을 저장한다.
  - 삭제는 사용 내역이 있으면 차단하고, 사용 내역이 없는 선결제만 hard delete한다.
- 기존 Django `prepayment_transfer_view`는 등록자 본인만 같은 회사 다른 영업사원에게 이관할 수 있다.
- DB 필드 추가는 필요하지 않다.

### 구현 계획

- 선결제 상세 API payload에 React action config를 추가한다.
  - 취소 가능 여부, 삭제 가능 여부, 이관 가능 여부
  - 이관 대상 사용자 목록
  - 각 React API submit URL
- React용 API를 추가한다.
  - `/reporting/api/prepayments/<id>/cancel/`
  - `/reporting/api/prepayments/<id>/delete/`
  - `/reporting/api/prepayments/<id>/transfer/`
- 기존 Django 권한/운영 규칙을 유지한다.
  - 같은 회사 사용자는 조회 가능하지만 수정/취소/삭제/이관은 등록자 본인만 가능
  - 사용 내역이 있으면 hard delete 차단
  - 이관 후 메모에 이관 기록을 남김
- React 상세 화면에 작업 패널을 추가한다.
  - 취소 사유 입력 후 취소
  - 사용 내역 없는 건만 영구 삭제
  - 같은 회사 동료 선택 후 이관
  - Django 삭제/취소/이관 fallback 링크 유지
- 신규 migration은 만들지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentDetailApiTests --verbosity=1`
- `python manage.py test reporting.tests.PrepaymentsSummaryApiTests reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Previous task — React 선결제 상세/등록/수정 전환

**목표**: 기존 Django `/reporting/prepayment/*` 화면을 유지하면서 React CRM에서 선결제 상세 조회, 신규 등록, 기본 정보 수정을 처리할 수 있게 한다.

### 확인된 상태

- React `/prepayments/` 목록 화면과 `/reporting/api/prepayments/` 목록 API는 이미 배포되어 있다.
- 기존 Django 선결제 상세/등록/수정/삭제/이관 URL은 운영 fallback으로 유지해야 한다.
- 선결제 모델은 `Prepayment`와 `PrepaymentUsage`이며, 이번 작업에서 DB 필드 추가는 필요하지 않다.
- 기존 Django 수정 정책은 본인이 등록한 선결제만 수정 가능하고, 같은 회사 사용자의 선결제는 조회만 가능하다.

### 구현 계획

- `/reporting/api/prepayments/<id>/` 단건 조회 API를 추가한다.
  - 같은 회사/접근 가능 사용자 범위만 조회 허용.
  - 기본 정보, 금액 요약, 사용 내역, Django fallback 링크, 수정 가능 여부, 폼 옵션을 반환한다.
- `/reporting/api/prepayments/create/` 등록 API를 추가한다.
  - 기존 Django 등록과 동일하게 고객, 금액, 결제일, 결제방법, 입금자, 메모를 저장한다.
  - 초기 잔액은 입금액과 동일하게 설정한다.
  - 고객 선택 범위는 기존 회사/사용자 접근 범위를 유지한다.
- `/reporting/api/prepayments/<id>/update/` 수정 API를 추가한다.
  - 본인이 등록한 선결제만 수정 가능하게 유지한다.
  - 금액, 잔액, 결제일, 결제방법, 상태, 메모를 검증한다.
  - 사용 내역이 있는 선결제도 기존 Django처럼 기본 정보 수정은 허용하되, 잔액이 금액을 초과하지 않게 서버 검증한다.
- React 라우팅을 확장한다.
  - `/prepayments/new/`: React 선결제 등록 화면.
  - `/prepayments/<id>/`: React 선결제 상세 화면.
  - `/prepayments/<id>/edit/`: React 선결제 수정 화면.
  - 목록 행의 `상세`, `수정`, 상단 `선결제 등록`은 React 경로로 이동하고 Django 원본 링크는 별도 fallback으로 유지한다.
- 신규 migration은 만들지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Previous task — React 선결제 목록 전환

**목표**: 기존 Django 선결제 관리 화면을 유지하면서 React CRM에 `/prepayments/` 읽기 전용 선결제 현황 화면을 추가한다.

### 확인된 상태

- Django 선결제 원본 화면은 `/reporting/prepayment/` 이하에서 동작한다.
- 일정 상세 React 편집 패널은 이미 `/reporting/api/prepayments/?customer_id=...&schedule_id=...`를 사용해 고객/일정별 선결제 선택 목록을 불러온다.
- React CRM 좌측 내비게이션에는 아직 선결제 현황 진입점이 없다.

### 구현 계획

- 기존 `/reporting/api/prepayments/` API를 확장한다.
  - `customer_id`가 있으면 기존 일정 편집용 응답을 그대로 유지한다.
  - `customer_id`가 없으면 React 선결제 목록용 요약/필터/목록 payload를 반환한다.
- 목록 API는 기존 Django 선결제 목록의 데이터 범위 규칙을 보존한다.
  - 기본값은 본인 등록 선결제.
  - `data_filter=all` 또는 `data_filter=user`는 기존 Django 화면과 같은 회사 사용자 기준으로 처리한다.
- React `/prepayments/` 화면을 추가한다.
  - 총 선결제 금액, 잔액, 사용 금액, 활성 건수 요약
  - 검색, 상태, 데이터 범위 필터
  - 선결제 행별 고객/부서/업체/입금자/금액/잔액/상태/담당자/원본 상세 링크
  - Django 선결제 등록/목록/엑셀 링크 유지
- 신규 DB 필드와 migration은 추가하지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentsSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`

---

## Current urgent task — Django 일정 캘린더 운영 진입점 복구

**목표**: React 통합 완료 전까지 기존 Django 일정 캘린더(`/reporting/schedules/calendar/`)를 운영자가 계속 가장 쉽게 사용할 수 있게 한다.

### 확인된 문제

- Django 일정 캘린더는 존재하지만 공통 사이드바의 `일정` 메뉴가 일정 목록(`/reporting/schedules/`)을 우선 열고 있다.
- 일정 캘린더가 실제 운영에서 가장 많이 쓰이는 화면이므로, 전환 기간에는 Django 메뉴의 일정 주 진입점을 캘린더로 유지해야 한다.

### 구현 계획

- Django 공통 사이드바의 `일정` 주 메뉴를 `schedule_calendar`로 변경한다.
- 상단 빠른 작업에도 `일정 캘린더` 링크를 노출한다.
- 일정 목록 화면에는 캘린더로 돌아가는 버튼을 추가해 목록과 캘린더를 같이 사용할 수 있게 한다.
- 일정 목록 URL과 기존 Django 기능은 유지하고, 인증/권한/DB 모델은 변경하지 않는다.
- 회귀 테스트로 인증된 사용자의 캘린더 접근과 Django 메뉴 링크를 검증한다.

---

## Previous urgent task — 고객 AI 분석 견적/납품 컨텍스트 누락 수정

**목표**: React 고객 상세(`/customers/<id>/`)에서 실행하는 부서 AI 분석이 실제 CRM의 견적/납품 기록을 빠짐없이 입력 컨텍스트로 사용하게 한다.

### 확인된 문제

- 기존 부서 AI 분석 수집 로직은 `Quote` 모델과 `History(action_type='delivery_schedule')` 위주로 견적/납품을 읽는다.
- 운영 데이터에는 견적/납품이 `Schedule(activity_type='quote'/'delivery')`와 `DeliveryItem(schedule=...)` 조합으로 저장되는 경우가 있다.
- 이 경우 고객 상세 AI 분석 프롬프트에 견적/납품 금액과 품목이 누락되어 GPT가 이미 나간 견적을 모르는 문제가 발생한다.

### 구현 계획

- `ai_chat.services.gather_quote_delivery_data()`를 확장해 다음 소스를 함께 수집한다.
  - `Quote` + `QuoteItem`
  - 견적 일정(`Schedule.activity_type='quote'`) + 일정 품목(`DeliveryItem.schedule`)
  - 견적 히스토리(`History.action_type='quote'`) + 히스토리 품목(`DeliveryItem.history`)
  - 납품 히스토리(`History.action_type='delivery_schedule'`) + 히스토리/일정 품목
  - 납품 일정(`Schedule.activity_type='delivery'`) + 일정 품목
- 이미 히스토리와 연결된 납품 일정은 중복 집계하지 않는다.
- 개별 고객 AI 분석(`gather_followup_data`)도 같은 수집 경로를 사용하게 맞춘다.
- DB 모델 변경 및 마이그레이션은 하지 않는다.
- 테스트는 일정 기반 견적/납품 품목이 AI 프롬프트에 포함되는지 검증한다.
- React 통합 완료 전까지 Django 기존 메뉴/페이지는 계속 접근 가능하게 유지한다. Django 사이드바의 고객/일정/영업노트/AI/파이프라인 메뉴는 Django URL을 가리키고, React CRM은 별도 진입 링크로 유지한다.

---

## Phase 0 — 보안 정리 및 잘못된 앱 제거 ✅ 완료

### 완료 내용

- ✅ `public_site` 앱 완전 제거 (디렉터리, INSTALLED_APPS, urls.py)
- ✅ 루트 URL `/` → `reporting:dashboard` 리디렉션
- ✅ `@csrf_exempt` 브라우저 AJAX 뷰 전체 제거
- ✅ `reporting/backup_api.py` — Bearer Token 인증 API는 @csrf_exempt 유지 (적절)

---

## Phase 1+2 — 대시보드 위젯 개선 + 영업보고 UX ✅ 완료

- ✅ 오늘 일정, 미검토 보고서, 지연 후속 조치 위젯
- ✅ `History` 모델: `next_action`, `next_action_date`, `reviewed_at`, `reviewer` 필드 추가
- ✅ 관리자 검토 완료 버튼 (AJAX 토글, `history_toggle_reviewed`)

---

## Phase 3 — 검색/필터/정렬 개선 ✅ 완료

- ✅ 거래처 목록: q, priority, grade, pipeline_stage, company, user 필터
- ✅ 영업보고 목록: 날짜 범위, 거래처, 담당자, 활동 유형 필터
- ✅ 일정 캘린더 뷰 (`/schedules/calendar/`)

---

## Phase 4 — 폼 UX 개선 ✅ 완료

- ✅ 다크모드 CSS 변수 (`var(--primary)`, `var(--surface)`) 전체 템플릿 적용
- ✅ 전역 JS `is-invalid` 클래스 자동 적용 (base.html)
- ✅ 한국어 에러 라벨 (`schedule_form.html`, `user_edit.html` 등)
- ✅ 필수 필드 `*` 빨간 표시 (user_edit.html)

---

## Phase 5 — 보안/개인정보 검토 ✅ 완료

- ✅ `SECRET_KEY` 하드코딩 fallback → RuntimeError
- ✅ 프로덕션 템플릿 `debug: True` 제거
- ✅ `ALLOWED_HOSTS` 와일드카드 `"*"` 제거 (개발환경)
- ✅ `validate_file_upload()` 단일 소스 — `.hwp/.hwpx` 추가, 인라인 코드 통일

---

## Phase 6 — 최종 QA 검토 ✅ 완료

- ✅ `manage.py check` → 0 이슈
- ✅ `manage.py test` → Ran 0 tests (스텁만 존재, 정상)
- ✅ `makemigrations --check` → No changes
- ✅ `collectstatic` → 완료
- 잔여 이슈 7개 기록 (아래 Phase 7에서 해결 예정)

---

## 1. 현재 Django 앱 구조

| 앱          | 설명                                           | 마운트 경로    |
| ----------- | ---------------------------------------------- | -------------- |
| `reporting` | 핵심 CRM 앱 — 영업보고, 거래처, 일정, 히스토리 | `/reporting/*` |
| `todos`     | 할 일 관리                                     | `/todos/*`     |
| `ai_chat`   | AI 채팅 및 분석                                | `/ai/*`        |

**제거된 앱**: `public_site` — Phase 0에서 완전 제거 (INSTALLED_APPS, urls.py, 디렉터리)

---

## 2. 기존 /reporting/\* CRM 기능

### FollowUp (고객/거래처)

- 고객 목록, 상세, 생성, 수정, 삭제
- 고객별 영업 히스토리 연결
- 우선순위, 단계, 등급, AI 점수 관리
- Excel 다운로드

### History (영업보고/활동)

- 영업보고 목록, 상세, 생성, 수정, 삭제
- 매니저 검토 (`reviewed_at`, `reviewer`) 기능
- 구조화된 회의 메모 (상황, 견적, 사실, 장애물, 다음 액션)
- 파일 첨부 (HistoryFile)
- 다음 액션/다음 연락일 필드

### Schedule (일정)

- 일정 목록, 달력, 상세, 생성, 수정, 삭제
- 활동 유형: 방문/통화/이메일/미팅/견적/납품/서비스
- 납품 항목 (DeliveryItem) 관리
- 파일 첨부 (ScheduleFile)

### Company/Department (고객사/부서)

- 고객사 목록, 상세, 생성, 수정
- 부서/연구실 관리
- 메모 기능

### Opportunity/Funnel (영업기회)

- 기회 목록, 상세 조회
- FunnelStage: lead→contact→quote→closing→won→quote_lost→excluded
- ⚠️ 생성/수정 프론트엔드 없음 (admin 전용)

### Quote (견적)

- Quote 모델 존재 (quote_number, stage, amounts)
- 8개 단계: draft→sent→review→negotiation→approved→rejected→expired→converted
- ⚠️ 독립 CRUD 뷰 없음 (API 전용)

### 기타

- 선결제(Prepayment) 관리
- 제품(Product) 목록
- 주간보고(WeeklyReport)
- 문서 템플릿 (PDF 변환 포함)
- Gmail OAuth2 / IMAP 이메일 통합
- 관리자 대시보드, 매니저 대시보드
- AI 고객 등급 분석

---

## 3. 현재 URL 동작

```
/ → reporting:dashboard (미인증 시 /reporting/login/ 리디렉션)
```

| 경로                             | 뷰                      | 역할            |
| -------------------------------- | ----------------------- | --------------- |
| `/reporting/login/`              | CustomLoginView         | 로그인          |
| `/reporting/dashboard/`          | dashboard_view          | 메인 대시보드   |
| `/reporting/followups/`          | followup_list_view      | 거래처 목록     |
| `/reporting/followups/<pk>/`     | followup_detail_view    | 거래처 상세     |
| `/reporting/followups/create/`   | followup_create_view    | 거래처 등록     |
| `/reporting/histories/`          | history_list_view       | 영업보고 목록   |
| `/reporting/histories/<pk>/`     | history_detail_view     | 영업보고 상세   |
| `/reporting/schedules/`          | schedule_list_view      | 일정 목록       |
| `/reporting/schedules/calendar/` | schedule_calendar_view  | 캘린더 뷰       |
| `/reporting/opportunities/`      | opportunity_list_view   | 영업기회 목록   |
| `/reporting/opportunities/<pk>/` | opportunity_detail_view | 영업기회 상세   |
| `/reporting/companies/`          | company_list_view       | 고객사 목록     |
| `/reporting/manager/`            | manager_dashboard       | 관리자 대시보드 |

---

## 4. public_site 영향도

**현황**: ✅ 완전 제거됨 (Phase 0 완료)

- `public_site` 디렉터리 없음
- INSTALLED_APPS에 없음
- `sales_project/urls.py`에서 제거됨
- 루트 `/`는 `reporting:dashboard`로 리디렉션

**영향**: 없음

---

## 5. 기존 모델 및 폼

### 핵심 모델

| 모델                  | 주요 필드                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------- |
| `UserProfile`         | role(admin/manager/salesman), company(FK), can_download_excel                                                 |
| `Company`             | name, created_by, created_at                                                                                  |
| `Department`          | company(FK), name, category(FK)                                                                               |
| `FollowUp`            | user, company, department, customer_name, manager, status, priority, pipeline_stage, customer_grade, ai_score |
| `Schedule`            | followup(FK), visit_date, activity_type, status, expected_revenue                                             |
| `History`             | followup(FK), schedule(FK), action_type, content, next_action, next_action_date, reviewed_at, reviewer        |
| `HistoryFile`         | history(FK), file, original_filename, file_size                                                               |
| `Quote`               | followup(FK), quote_number, stage, subtotal, discount_rate, tax_amount, total_amount                          |
| `QuoteItem`           | quote(FK), product(FK), quantity, unit_price, discount_rate, subtotal                                         |
| `OpportunityTracking` | followup(FK), current_stage, backlog_amount, probability, expected_close_date                                 |
| `FunnelStage`         | name, order, color                                                                                            |
| `Prepayment`          | company(FK?), amount, remaining, created_date                                                                 |
| `Product`             | product_code, name, unit, standard_price, is_active                                                           |

### 폼 클래스 (views.py 내)

- `FollowUpForm` — 거래처 생성/수정, `clean_company()` + `clean_department()` 서버 검증
- `HistoryForm` — 영업보고 생성/수정
- `ScheduleForm` — 일정 생성/수정
- `CompanyForm` — 고객사 생성/수정
- `UserEditForm` — 사용자 수정

---

## 6. 기존 영업노트/보고 워크플로우

### 영업보고 작성 흐름

1. 사용자 로그인 → 대시보드
2. 거래처(FollowUp) 선택 또는 일정(Schedule)에서 바로 보고 작성
3. History 생성: 활동 유형, 내용, 결과, 다음 액션, 다음 연락일 입력
4. 파일 첨부 가능 (10MB 이하, `.pdf/.doc/.xls/.hwp/.hwpx` 등 14종)
5. 매니저가 `history_toggle_reviewed`로 검토 완료 표시 (POST, admin/manager 전용)

### 거래처 관리 흐름

1. `/reporting/followups/` 목록에서 검색/필터
2. 상세 페이지: 고객 정보 + 관련 Schedule + History 목록
3. 빠른 새 보고 작성 버튼

---

## 7. 기존 대시보드/목록/상세/생성/수정 페이지

| 페이지             | 템플릿                  | 상태                                              |
| ------------------ | ----------------------- | ------------------------------------------------- |
| 메인 대시보드      | dashboard.html          | ✅ 완비 (역할별 필터링, 통계 카드, 모바일 반응형) |
| 매니저 대시보드    | manager_dashboard.html  | ✅ 완비                                           |
| 거래처 목록        | followup_list.html      | ✅ 완비 (검색+필터+empty-state)                   |
| 거래처 상세        | followup_detail.html    | ✅ 완비                                           |
| 거래처 생성/수정   | followup_form.html      | ✅ 완비                                           |
| 영업보고 목록      | history_list.html       | ⚠️ empty-state 없음                               |
| 영업보고 상세      | history_detail.html     | ✅ 완비                                           |
| 영업보고 작성      | history_form.html       | ✅ 완비                                           |
| 일정 목록          | schedule_list.html      | ⚠️ empty-state 없음                               |
| 일정 달력          | schedule_calendar.html  | ✅ 완비                                           |
| 일정 생성/수정     | schedule_form.html      | ✅ 완비                                           |
| 영업기회 목록      | opportunity_list.html   | ✅ 완비                                           |
| 영업기회 상세      | opportunity_detail.html | ✅ 완비                                           |
| 영업기회 생성/수정 | (없음)                  | ❌ 미구현                                         |
| 고객사 목록        | company_list.html       | ✅ 완비                                           |
| 로그인             | login.html              | ✅ 완비                                           |

---

## 8. 현재 인증/권한 동작

### 인증

- Django `LoginView` 서브클래스 (`CustomLoginView`)
- 모든 내부 뷰: `@login_required` 적용 (100+ 뷰)
- 미인증 접근: `/reporting/login/?next=...` 리디렉션
- 세션 쿠키: 프로덕션에서 `SESSION_COOKIE_SECURE=True`

### 권한 체계

| 역할       | 접근 범위                                              |
| ---------- | ------------------------------------------------------ |
| `admin`    | 전체 — 모든 사용자 데이터, 설정, 사용자 관리           |
| `manager`  | 팀 — 같은 회사 팀원 데이터, 매니저 대시보드, 검토 기능 |
| `salesman` | 본인 — 본인이 작성한 보고서와 담당 거래처              |

### 권한 헬퍼

| 함수                                  | 역할                                 |
| ------------------------------------- | ------------------------------------ |
| `role_required(roles)`                | 뷰 데코레이터 — 역할 기반 접근 제어  |
| `can_access_user_data(user, target)`  | 소속 회사 기반 데이터 접근 허용 여부 |
| `can_modify_user_data(user, target)`  | 수정/삭제 권한                       |
| `can_access_followup(user, followup)` | 거래처 접근 권한                     |
| `can_excel_download(user)`            | Excel 다운로드 권한                  |

### 보안 현황 (Phase 5 완료)

- `SECRET_KEY` 하드코딩 제거 → RuntimeError
- 프로덕션 템플릿 `debug:True` 제거
- `ALLOWED_HOSTS` 와일드카드 제거
- `validate_file_upload()` 단일 소스 (`.hwp/.hwpx` 포함)
- `subprocess.run()`: `shell=False`, 사용자 입력 없음
- CSRF: 미들웨어 전체 적용, `@csrf_exempt` 없음

---

## 9. 권장 다음 단계 — Phase 7

> **주의**: 이 시스템은 내부 영업관리 시스템입니다.  
> 제품 카탈로그, 브랜드 상세, 공개 페이지는 추가하지 않습니다.

### Phase 7C — 잔여 이슈 정리 (빠른 작업, 먼저 권장)

- [ ] `history_list.html` — `{% empty %}` + `.empty-state-card` 추가
- [ ] `schedule_list.html` — `{% empty %}` + `.empty-state-card` 추가
- [ ] `railway.toml` startCommand에서 `fix_quote_770.py`, `reset_ai_chat_tables.py` 제거 또는 one-time job 분리
- [ ] `css/dist/styles.css` 중복 경고 해결 (STATICFILES_DIRS 경로 정리)

### Phase 7A — 영업기회 CRUD 프론트엔드 구현

**목표**: 영업담당자가 Django admin 없이도 영업기회를 생성/수정할 수 있게 한다.

**작업 목록**:

- [ ] `OpportunityForm` 폼 클래스 작성 (views.py 내)
- [ ] `opportunity_create_view` 구현
- [ ] `opportunity_edit_view` 구현
- [ ] 템플릿 `opportunity_form.html` 작성 (다크모드 CSS 변수 적용)
- [ ] `reporting/urls.py`에 create/edit URL 추가
- [ ] `followup_detail.html` — "영업기회 추가" 버튼 연결
- [ ] `opportunity_detail.html` — "편집" 버튼 추가

**폼 필드 (OpportunityTracking)**:

| 필드                | 설명                 | 필수 |
| ------------------- | -------------------- | ---- |
| followup            | 거래처 연결 (FK)     | ✅   |
| current_stage       | FunnelStage 선택     | ✅   |
| backlog_amount      | 예상 금액 (원)       | -    |
| probability         | 수주 가능성 (%)      | -    |
| expected_close_date | 예상 계약일          | -    |
| product             | 연결 제품 (optional) | -    |
| quote               | 연결 견적 (optional) | -    |

**추가 URL**:

```
opportunities/create/          → opportunity_create_view
opportunities/<pk>/edit/       → opportunity_edit_view
```

**DB 변경**: 없음 (`OpportunityTracking` 모델 이미 존재)

### Phase 7B — 기본 자동화 테스트 작성

**목표**: CI 안전망 확보 (현재 `Ran 0 tests`)

**작업 목록**:

- [ ] `reporting/tests.py`:
  - 로그인/로그아웃 smoke test
  - 미인증 시 login 리디렉션 확인
  - `followup_list_view` 200 응답 확인
  - `followup_create` POST 성공 케이스
  - `validate_file_upload()` 단위 테스트 (허용/차단 확장자)
  - 권한 없는 사용자 접근 차단 (salesman→admin 전용 뷰)

---

## 10. 변경 예정 파일

### Phase 7C

| 파일                                               | 변경 | 내용                 |
| -------------------------------------------------- | ---- | -------------------- |
| `reporting/templates/reporting/history_list.html`  | 수정 | empty-state 추가     |
| `reporting/templates/reporting/schedule_list.html` | 수정 | empty-state 추가     |
| `railway.toml`                                     | 수정 | 일회성 스크립트 제거 |

### Phase 7A

| 파일                                                    | 변경 | 내용                                   |
| ------------------------------------------------------- | ---- | -------------------------------------- |
| `reporting/views.py`                                    | 수정 | `OpportunityForm`, create/edit 뷰 추가 |
| `reporting/urls.py`                                     | 수정 | create/edit URL 패턴 추가              |
| `reporting/templates/reporting/opportunity_form.html`   | 신규 | 생성/수정 폼 템플릿                    |
| `reporting/templates/reporting/followup_detail.html`    | 수정 | "영업기회 추가" 버튼                   |
| `reporting/templates/reporting/opportunity_detail.html` | 수정 | "편집" 버튼                            |

### Phase 7B

| 파일                 | 변경 | 내용            |
| -------------------- | ---- | --------------- |
| `reporting/tests.py` | 수정 | smoke test 추가 |

---

## 11. 검증 명령어

```bash
# 기본 체크
python manage.py check
python manage.py makemigrations --check --dry-run

# 테스트 (Phase 7B 이후)
python manage.py test

# 정적 파일
python manage.py collectstatic --noinput

# 배포 사전 체크
python pre_deployment_check.py
```

---

## 완료된 Phase 이력

| Phase     | 내용                                              | 날짜       |
| --------- | ------------------------------------------------- | ---------- |
| Phase 0   | 보안 정리 — public_site 제거, @csrf_exempt 제거   | 2026-04-25 |
| Phase 1+2 | 대시보드 위젯 개선 + 영업보고 UX                  | 2026-04-25 |
| Phase 3   | 검색/필터/정렬 개선                               | 2026-04-25 |
| Phase 4   | 폼 UX 개선 — 다크모드, 한국어 에러 라벨           | 2026-04-25 |
| Phase 5   | 보안/개인정보 검토 — SECRET_KEY, 파일 업로드 통일 | 2026-04-25 |
| Phase 6   | 최종 QA 검토                                      | 2026-04-25 |

---

## 기술 스택

| 항목      | 값                                                       |
| --------- | -------------------------------------------------------- |
| Framework | Django 5.2.3                                             |
| DB (prod) | PostgreSQL (Railway)                                     |
| DB (dev)  | SQLite                                                   |
| CSS       | Bootstrap 5.3.0 (CDN), Font Awesome 6.4.0                |
| 다크모드  | CSS 변수 (`var(--primary)`, `var(--surface)` 등)         |
| Async     | Celery + Redis                                           |
| Media     | Cloudinary (prod) / FileSystem (dev)                     |
| Email     | Gmail OAuth2 + IMAP/SMTP (Fernet 암호화)                 |
| AI        | OpenAI GPT                                               |
| Deploy    | Railway (nixpacks.toml, gunicorn)                        |
| Python    | `C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe` |

---

## 현재 단계

**Phase 6.5-1 완료** (2026-04-27)

### Phase 6.5-1 — 모달 클릭/입력 버그 수정

**목표**: Bootstrap 중첩 모달 및 stacking context 문제로 인한 입력 불가/모달 소멸 문제 해결.

**작업 범위**:

- 캘린더 일정 상세 모달의 고객 활동 기록: 중첩 Bootstrap Modal 제거, Offcanvas/인라인 패널 방식 사용
- 캘린더 일정 상세 모달의 부서 메모: 일정 상세 모달을 유지한 상태로 메모 입력 가능하게 처리
- 대시보드 영업노트 작성 모달: backdrop/z-index/focus 문제로 필드 클릭이 막히지 않게 처리

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DepartmentMemo` 모델과 API를 그대로 사용.

**검증 계획**:

- `python manage.py check` — 완료
- `python manage.py makemigrations --check --dry-run` — 완료, 변경 없음
- `python manage.py test` — 완료, 9개 통과
- 템플릿 정적 점검 — 완료: 중첩 모달 제거, 중복 ID 없음, 전역 backdrop 숨김 없음, CSRF 제출 유지
- Playwright 브라우저 점검 — 완료: 캘린더 일정 모달 유지 상태에서 부서 메모/고객 활동기록 Offcanvas 입력 및 닫기 가능, 대시보드 영업노트 모달 필드 입력 가능

---

**다음 권장 단계**: Phase 7 계획 재개

권장 실행 순서: Phase 7C (빠른 정리) → Phase 7A (영업기회 CRUD) → Phase 7B (테스트)

---

## Phase 10 — 서버 응답 속도 개선 1차

**목표**: 모델 변경 없이 현재 주요 화면의 반복 쿼리를 줄여 개발/운영 서버 응답 시간을 안정화한다.

**작업 범위**:

- `/ai/` 부서 선택 허브의 부서별 팔로우업 조회 N+1 제거
- `/reporting/followups/` 업체 필터 목록의 업체별 팔로우업 카운트 N+1 제거
- `/reporting/dashboard/` 반복 집계 일부를 날짜/월 단위 grouped query로 축소

**DB 변경 필요 여부**: 없음. 이번 단계는 view/query 최적화만 수행하며 migration은 만들지 않는다.

**검증 계획**:

- 최적화 전후 URL별 응답 시간/쿼리 수 비교: `/ai/`, `/reporting/followups/`, `/reporting/dashboard/`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test ai_chat`
- `python manage.py test reporting`
- `python manage.py test`
- `git diff --check`

**2차 추가 범위**:

- 대시보드 월간/연간 일정 카운트를 `aggregate()` 결과로 재사용
- 대시보드 선결제 통계를 단일 aggregate로 축소
- 오늘/이번 주 일정 목록은 리스트 평가 결과 길이를 사용해 추가 count 제거
- 고객사별 매출 분포의 전체 합계를 별도 aggregate 없이 기존 grouped query 결과에서 계산

---

## Phase 11 — 주요 CRM 조회 경로 DB 인덱스 추가

**목표**: Phase 10에서 남은 체감 지연 가능 구간을 줄이기 위해 대시보드, 팔로우업, AI 부서 허브에서 반복적으로 사용하는 필터 조합에 복합 인덱스를 추가한다.

**작업 범위**:

- `Schedule`: 사용자/방문일/상태/활동유형 기반 대시보드 집계와 오늘·이번 주 일정 조회 최적화
- `History`: 사용자/작성일/활동유형/다음 액션 기반 최근 활동, 지연 후속, 팀 활동 조회 최적화
- `FollowUp`: 사용자/생성일/파이프라인/부서 기반 고객 목록, 대시보드, AI 부서 허브 조회 최적화
- `Prepayment`: 등록자/결제일/상태 기반 선결제 월간·요약 조회 최적화
- `PersonalSchedule`: 사용자/일정일/시간 기반 대시보드 개인 일정 조회 최적화

**DB 변경 필요 여부**: 있음. 신규 필드 없이 `models.Index`만 추가하며 migration을 생성한다.

**검증 계획**:

- `python manage.py makemigrations --check --dry-run`로 migration 상태 확인
- `python manage.py migrate --plan`으로 적용 계획 확인
- `python manage.py check`
- `python manage.py test reporting`
- `python manage.py test`
- 주요 URL 쿼리 수 재측정: `/reporting/dashboard/`, `/reporting/followups/`, `/ai/`
- `git diff --check`

**추가 확인된 병목**:

- `/reporting/dashboard/` 첫 요청 지연은 쿼리 수가 아니라 URL resolver가 `ai_chat.services`, Gmail/IMAP view 모듈을 한꺼번에 import하는 cold start 비용이 큼.
- `ai_chat.services`는 OpenAI 관련 의존성을 포함하므로 `/reporting/dashboard/` 요청에서는 즉시 필요하지 않음.
- Gmail/IMAP view는 대시보드 요청과 무관하므로 URL 매칭 시점까지 lazy import로 늦춘다.

**추가 작업 범위**:

- `ai_chat.views`: AI 분석 실행 함수에서만 `ai_chat.services`를 import하도록 변경
- `reporting.urls`: Gmail/IMAP view callable을 lazy wrapper로 연결해 대시보드 cold start import 비용 축소

---

## Hotfix — 영업기회 목록 기본 데이터 범위 제한

**목표**: `/reporting/opportunities/`에서 기본 목록은 현재 로그인 사용자 담당 영업기회만 보여주고, 같은 회사 직원의 영업기회는 사용자가 담당자를 명시 선택했을 때만 보여준다.

**작업 범위**:

- `opportunity_list_view` 기본 필터를 접근 가능 사용자 전체가 아니라 `request.user`로 변경
- 같은 회사/접근 가능 사용자 선택 드롭다운 제공
- `data_filter=all` 우회 요청도 영업기회 목록에서는 기본 `me`로 처리
- 단계/마감/페이지네이션 링크가 선택된 데이터 범위를 유지하도록 수정
- 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. view/template/test 변경만 수행한다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.OpportunityListDataScopeTests`
- `python manage.py test`
- `git diff --check`

---

## Hotfix — 별도 영업기회 화면 제거 및 상단 파이프라인 진입점 정리

**목표**: 최종 영업 흐름을 `/reporting/funnel/` 파이프라인 화면으로 단일화하고, 별도 `/reporting/opportunities/` 화면과 관련 UI를 제거한다.

**작업 범위**:

- `/reporting/opportunities/` 및 하위 생성/상세/수정 URL 제거
- 영업기회 전용 view/form/template 제거
- 상단 quick action의 `견적` 버튼을 `/reporting/funnel/`로 이동하는 `파이프라인` 버튼으로 변경
- 팔로우업 상세의 영업기회 생성/상세/수정 링크를 제거하고 파이프라인 목록 안내로 대체
- `/reporting/opportunities/` 제거와 상단 파이프라인 링크 회귀 테스트 추가/수정

**DB 변경 필요 여부**: 없음. `OpportunityTracking` 데이터/모델은 파이프라인 및 기존 자동 동기화에서 사용할 수 있으므로 삭제하지 않는다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests`
- `python manage.py test`
- `git diff --check`

---

## Frontend Pilot — React 파이프라인 Command Center 시안

**목표**: Django template의 디자인 자유도 한계를 줄이기 위해 별도 `/frontend` Vite React 파일럿을 만들고, `/reporting/funnel/` 대체 후보가 될 파이프라인 Command Center mock 화면을 구현한다.

**작업 범위**:

- `/frontend` 독립 Vite + React + TypeScript 프로젝트 생성
- Django API 연결 전 mock data 기반 파이프라인 화면 구현
- 좌측 CRM 내비게이션, 상단 검색/액션, KPI strip, 파이프라인 board/list 전환, 고객 상세 패널 구성
- 내부 CRM 업무툴 기준의 밝고 정돈된 디자인 시스템 적용
- 기존 Django 라우트/DB/권한/모델은 변경하지 않음

**DB 변경 필요 여부**: 없음. 이번 단계는 프론트 시안 프로젝트만 추가한다.

**검증 계획**:

- `npm install`
- `npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Prepayment Editing — 일정 선결제 입력 전환

**목표**: React `/schedules/<id>/` 일정 상세 수정 패널에서 납품 일정의 선결제 선택과 차감 금액을 저장하게 만들어 Django 일정 수정 폼 왕복을 줄인다.

**시간 단위 진행 루트**:

- 0~1시간: 기존 `Schedule`, `Prepayment`, `PrepaymentUsage` 모델과 Django 일정 생성/수정 폼의 선결제 복원/차감 흐름을 확인한다.
- 1~2시간: 작업 범위, DB 변경 여부, 검증 계획을 `AGENT_PLAN.md`에 기록한다.
- 2~4시간: 일정 상세/수정 API에 선결제 사용 여부, 선택 목록, 잔액 검증, 기존 사용분 복원 후 재차감 로직을 추가한다.
- 4~6시간: React 일정 상세 수정 패널에 선결제 사용 체크, 선택 가능한 선결제 목록, 차감 금액 입력, 합계 표시를 연결한다.
- 6~7시간: Django API 테스트, React build, Django check, migration check, diff check를 실행한다.
- 7~8시간: `AGENT_REPORT.md`를 갱신하고 커밋/푸시 후 Railway `web`과 `sales-note-frontend` 운영 배포 및 번들/API 보호 상태를 확인한다.

**작업 범위**:

- `/reporting/api/prepayments/` 응답에 React 편집에 필요한 기존 선택 금액과 사용 가능 잔액을 추가한다.
- `/reporting/api/schedules/<id>/` 상세 API에 선결제 사용 내역과 선결제 목록 URL을 제공한다.
- `/reporting/api/schedules/<id>/update/`가 `usePrepayment`, `prepayments` payload를 받아 기존 사용분을 복원한 뒤 선택 금액을 재차감한다.
- 선결제는 기존 정책대로 납품 일정에서만 사용하고, 같은 부서 고객의 활성 선결제 및 현재 일정에서 이미 사용 중인 선결제만 선택 가능하게 한다.
- React 수정 패널은 선결제 사용 체크박스, 선택 목록, 금액 입력, 납품 합계 대비 차감/실결제 금액을 표시한다.
- 기존 Django 선결제 목록/상세/일정 수정 화면과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `Prepayment`, `PrepaymentUsage`, `DeliveryItem` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Department AI Analysis — 고객 상세 부서 AI 분석 연결

**목표**: React `/customers/<id>/` 고객 상세 화면에서 해당 고객의 부서 AI 분석 상태를 확인하고, 권한이 있는 사용자는 고객 화면에서 바로 분석을 실행하거나 결과 화면으로 이동할 수 있게 한다.

**시간 단위 진행 루트**:

- 0~1시간: 기존 고객 상세 API/UI와 `ai_chat` 부서 분석 조회/실행 URL을 확인한다.
- 1~2시간: 작업 범위, DB 변경 여부, 검증 계획을 `AGENT_PLAN.md`에 기록한다.
- 2~4시간: 고객 상세 API에 부서 AI 분석 가능 여부, 분석 요약, 실행 URL, 결과 URL을 추가한다.
- 4~6시간: React 고객 상세 사이드 영역에 부서 AI 분석 카드, 실행 버튼, 결과 이동 링크, 실행 상태 메시지를 추가한다.
- 6~7시간: 고객 상세 API 테스트, React build, Django check, migration check, diff check를 실행한다.
- 7~8시간: `AGENT_REPORT.md`를 갱신하고 커밋/푸시 후 Railway `web`과 `sales-note-frontend` 운영 배포 및 번들/API 보호 상태를 확인한다.

**작업 범위**:

- 기존 `ai_chat:department_analysis`, `ai_chat:run_analysis`, `ai_chat:department_list` URL을 재사용한다.
- 고객 상세 API가 고객의 `department` 기준으로 AI 분석 상태와 링크를 내려준다.
- 기존 AI 권한 정책을 유지해 `can_use_ai` 권한이 없거나 해당 부서에 본인 담당 고객이 없는 사용자는 실행 버튼을 비활성화한다.
- React 고객 상세에 부서명, 분석 여부, 최근 요약, 미팅/견적/납품/PainPoint 카운트, 분석 실행/결과 보기 액션을 표시한다.
- 기존 Django AI 분석 화면, 고객 상세 화면, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `Department`, `AIDepartmentAnalysis`, `PainPointCard` 모델만 조회/사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 읽기 API 연결

**목표**: React 파일럿이 mock data만 사용하는 상태에서 벗어나, 기존 Django 권한 정책을 타는 읽기 전용 파이프라인 API를 우선 조회하도록 연결한다.

**작업 범위**:

- `/reporting/api/pipeline/` GET API 추가
- `funnel_views._get_accessible_followups()`를 재사용해 현재 사용자 권한 범위만 반환
- API 응답에 stages, deals, metrics, priorityTasks 포함
- Vite dev server에서 `/reporting/*` 요청을 Django `127.0.0.1:8000`으로 proxy
- React 파일럿은 API 성공 시 실제 데이터, 실패/미로그인/서버 미실행 시 mock fallback 사용
- API 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. 읽기 전용 endpoint와 프론트 연결만 수행한다.

**검증 계획**:

- `npm run build`
- `npm audit --audit-level=moderate`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests`
- `git diff --check`

---

## Frontend Pilot — 잠재 고객 컬럼 밀도 축소

**목표**: 파이프라인 보드에서 `잠재` 고객이 과도하게 많아지는 문제를 줄이기 위해, DB 단계 변경 없이 API/프론트에서 우선순위 높은 잠재 고객만 먼저 보여준다.

**작업 범위**:

- API deal payload에 `attentionScore`, `attentionReason`, `isPotentialOverflow` 추가
- 잠재 고객은 점수순으로 정렬하고 보드에서는 TOP 10만 기본 노출
- React 보드의 `잠재` 컬럼은 기본 접힘 상태로 표시
- 접힌 상태에서는 우선 대응 잠재 고객 요약과 펼치기 버튼 제공
- 리스트 탭에서는 전체 잠재 고객 유지

**DB 변경 필요 여부**: 없음. 기존 `pipeline_stage` 값을 그대로 사용하고 화면/API 표현만 조정한다.

**검증 계획**:

- `npm run build`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 상세 패널 확장

**목표**: 카드 클릭 시 우측 상세 패널이 단순 금액/다음 액션을 넘어서, 실제 영업 판단에 필요한 최근 활동·견적·일정 요약과 기존 Django 상세 바로가기를 제공하도록 개선한다.

**작업 범위**:

- API deal payload에 `recentActivities`, `latestQuote`, `nextSchedule`, `stageLabel` 추가
- 우측 상세 패널에 핵심 상태, 다음 액션, 최근 활동, 최근 견적, 다음 일정, 기존 고객 상세 링크 표시
- mock data에도 상세 패널용 필드 추가
- API 테스트에서 상세 필드 응답 검증

**DB 변경 필요 여부**: 없음. 기존 prefetch된 History/Quote/Schedule 데이터만 읽는다.

**검증 계획**:

- `npm run build`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 단계 변경 API 연결

**목표**: React 파일럿 상세 패널에서 기존 Django 파이프라인 단계 이동 API를 호출해, 선택 고객의 영업 단계를 변경하고 최신 파이프라인 데이터를 다시 불러온다.

**작업 범위**:

- React API helper에 CSRF 토큰 포함 POST 함수 추가
- 상세 패널에 단계 변경 버튼과 저장 상태/오류 메시지 표시
- Django API 데이터 연결 상태에서만 단계 변경 활성화, mock fallback 상태에서는 비활성 안내
- 기존 `reporting:funnel_pipeline_move` 권한 정책과 수동 단계 설정 로직 재사용
- 파이프라인 이동 API 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. 기존 `FollowUp.pipeline_stage`, `pipeline_manually_set` 필드만 갱신한다.

**검증 계획**:

- `npm run build`
- `npm audit --audit-level=moderate`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — Railway 프론트 서비스 배포 준비

**목표**: React 파일럿을 Railway 별도 프론트 서비스로 배포할 수 있도록, 정적 파일 서빙과 기존 Django `/reporting/*` proxy를 제공하는 최소 Node 서버를 추가한다.

**작업 범위**:

- `frontend/server.mjs` 추가
- `npm start`로 Railway `$PORT`에서 React `dist` 정적 파일 서빙
- `/reporting/*` 요청은 기존 Django Railway 서버로 proxy
- 프론트 README에 Railway build/start/env 설정 기록
- Railway CLI 인증 상태 확인 및 서비스 생성 시도

**DB 변경 필요 여부**: 없음.

**검증 계획**:

- `npm run build`
- `node --check server.mjs`
- `npm audit --audit-level=moderate`
- 로컬 `node server.mjs`로 `/`, `/reporting/login/` 200 확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — Django 대시보드 디자인 톤 정렬

**목표**: React 파이프라인 파일럿이 기존 `/reporting/dashboard/`와 다른 별도 제품처럼 보이지 않도록, Django 대시보드의 다크 CRM 디자인 시스템을 따라간다.

**작업 범위**:

- `reporting/base.html` 및 `dashboard.html`의 핵심 토큰을 기준으로 프론트 색상 체계 정리
- 다크 남색 배경, 다크 사이드바, 표면 카드, 파란색/보라색 그라데이션 포인트 반영
- KPI 카드, 필터 rail, 파이프라인 보드, 우측 상세 패널의 border/shadow/hover 톤 정렬
- 기존 클릭 동작, Django proxy, 파이프라인 API 연결은 유지

**DB 변경 필요 여부**: 없음. CSS 중심의 프론트 디자인 변경이다.

**검증 계획**:

- `npm run build`
- `node --check server.mjs`
- 로컬 또는 배포 URL smoke 확인
- `git diff --check`

---

## Frontend Pilot — 라이트 CRM 톤 재정렬 및 백엔드 복귀 링크

**목표**: React 파이프라인 화면을 운영 `/reporting/dashboard/`에 적용된 CRM light UI 토큰과 맞추고, Django 백엔드 화면에서 React 파이프라인으로 돌아오는 명확한 동선을 추가한다.

**작업 범위**:

- React 파이프라인 CSS를 `crm-ui.css` 기준의 화이트 모드로 재정렬
- 카드, 사이드바, 보드, 상세 패널, 상태 배지의 white-on-light/low contrast 여부 점검
- Django 공통 context에 프론트 파이프라인 URL 제공
- Django 사이드바와 상단 빠른 액션에 `신규 파이프라인` 링크 추가
- 기존 `/reporting/*` 라우트, 인증, CSRF, 파이프라인 API는 유지

**DB 변경 필요 여부**: 없음. UI/CSS와 template/context 설정 변경만 수행한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 배포 URL smoke 확인

---

## Frontend Hotfix — 프록시된 Django 정적 자산 라우팅

**목표**: 프론트 Railway 도메인에서 `/reporting/*` Django 화면으로 이동했을 때 `crm-ui.css` 라이트 테마가 정상 로드되어 모든 CRM 화면이 화이트 모드로 보이게 한다.

**원인**:

- `frontend/server.mjs`는 `/reporting/*`와 `/ai/*` HTML/API 요청만 Django로 proxy한다.
- Django 템플릿이 참조하는 `/static/reporting/css/crm-ui.css` 요청은 프론트 React fallback으로 처리되어 CSS 대신 `index.html`이 내려간다.
- 그 결과 `base.html`의 기존 inline dark token만 적용되고 schedules 화면이 다크 모드로 보인다.

**작업 범위**:

- 프론트 Node 서버에서 `/static/*` 요청을 Django 백엔드로 proxy한다.
- 첨부/업로드 자산을 위해 `/media/*` 요청도 Django 백엔드로 proxy한다.
- React 빌드 자산인 `/assets/*`는 기존처럼 프론트 서비스가 직접 서빙한다.
- DB, migration, Django 인증/CSRF 정책은 변경하지 않는다.

**검증 계획**:

- `cd frontend && node --check server.mjs`
- `cd frontend && npm run build`
- 로컬 프론트 서버에서 `/static/reporting/css/crm-ui.css`가 HTML이 아니라 CSS로 반환되는지 확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- Railway 프론트 배포 후 운영 프론트 도메인의 `/static/reporting/css/crm-ui.css`와 `/reporting/login/` smoke 확인

---

## UI Hotfix — 프로필 화면 라이트 CRM 테마 정리

**목표**: `/reporting/profile/`와 `/reporting/profile/edit/`가 공통 CRM 라이트 테마를 따르도록 페이지 전용 다크 CSS를 제거한다.

**원인**:

- `profile.html`과 `profile_edit.html`에 `hsl(222, 47%, 14%)`, `hsl(210, 40%, 98%)` 기반의 페이지 전용 다크 모드 CSS가 남아 있다.
- 이 스타일이 공통 `crm-ui.css` 라이트 토큰보다 늦게 적용되어 프로필 카드/입력 필드가 다크 모드로 보인다.

**작업 범위**:

- 프로필 보기 화면의 카드, 본문, 읽기 전용 필드, 이메일 연동 카드, alert 스타일을 라이트 CRM 토큰으로 변경한다.
- 프로필 수정 화면의 카드, 폼 필드, 안내 alert, 계정 정보 필드를 라이트 CRM 토큰으로 변경한다.
- 인증/권한, view, model, migration은 변경하지 않는다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- 로그인된 로컬 클라이언트로 `/reporting/profile/`, `/reporting/profile/edit/` 200 확인
- 템플릿에 프로필 전용 다크 HSL 토큰이 남지 않았는지 확인
- `git diff --check`

---

## UI Hotfix — 화이트 모드 잔여 흰 텍스트/다크 토큰 정리

**목표**: CRM이 화이트 모드로 확정된 상태에서 라이트 배경 위 흰 텍스트 또는 다크 모드 잔여 토큰이 보이는 화면을 정리한다.

**작업 범위**:

- `base.html`의 기본 CSS 변수와 Bootstrap 변수 기본값을 라이트 CRM 토큰으로 정규화한다.
- `crm-ui.css`에 페이지별 다크 CSS, Select2, Quill, 파일 input, 인라인 다크 HSL 스타일을 라이트 표면/텍스트로 보정하는 공통 규칙을 추가한다.
- 팔로우업 삭제/상세 화면처럼 인라인 다크 스타일이 강한 템플릿은 직접 라이트 스타일로 교체한다.
- 버튼, 배지, 위험/성공 헤더처럼 색상 배경 위에서 흰 텍스트가 필요한 요소는 유지한다.

**DB 변경 필요 여부**: 없음. CSS/template 표시 수정만 수행한다.

**검증 계획**:

- 흰 텍스트/다크 HSL 패턴 재스캔
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## UI Hotfix — 고객 리포트 흰 텍스트 정리

**목표**: `/reporting/customer-report/` 화면의 고객명 배지에서 라이트 배경 위 흰 텍스트가 남는 문제를 수정한다.

**원인**:

- `customer_report_list.html`에 `.badge.bg-secondary.text-decoration-none { color: #ffffff !important; }` 규칙이 남아 있다.
- 공통 `crm-ui.css`는 `bg-secondary` 배지를 라이트 배경으로 바꾸지만, 페이지 전용 selector의 specificity가 더 높아 흰 텍스트가 유지된다.

**작업 범위**:

- 고객명 링크 배지를 라이트 회색 배경/슬레이트 텍스트/hover 상태로 변경한다.
- 버튼/활성 드롭다운처럼 색상 배경 위 흰 텍스트가 필요한 요소는 유지한다.

**DB 변경 필요 여부**: 없음. 템플릿 CSS 수정만 수행한다.

**검증 계획**:

- `customer_report_list.html` 흰 텍스트 패턴 재확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `git diff --check`

---

## Frontend Migration — CRM Shell 단일 진입점 1차 정리

**목표**: React 프론트를 CRM의 메인 진입점으로 세우고, 대시보드/고객/파이프라인/영업노트/일정/AI 핵심 메뉴를 프론트 Shell에서 소유하게 한다.

**작업 범위**:

- React 앱에 `/dashboard/`, `/customers/`, `/pipeline/`, `/notes/`, `/schedules/`, `/ai-workspace/` 라우트형 화면을 추가한다.
- 아직 완전 이관 전인 기능은 프론트 Shell 안에서 운영 Django 화면으로 이어지는 명확한 작업 버튼을 제공한다.
- Django context에 프론트 핵심 메뉴 URL을 공통 제공한다.
- Django sidebar의 핵심 CRM 메뉴는 프론트 URL로 연결하고, 중복되는 Django 메뉴 노출을 줄인다.
- 기존 Django `/reporting/*`, `/ai/*` route, 인증, CSRF, API, DB 모델은 유지한다.

**DB 변경 필요 여부**: 없음. 프론트 라우팅/UI와 Django template/context 변경만 수행한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Dashboard 실제 데이터 연결

**목표**: React `/dashboard/` placeholder를 Django CRM 데이터 기반 업무 대시보드로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/dashboard/` JSON API를 추가한다.
- API는 기존 `FollowUp`, `Schedule`, `History`, `PersonalSchedule` 데이터를 사용해 KPI, 오늘 일정, 이번 주 일정, 지연 후속조치, 최근 영업노트, 우선순위 고객, 파이프라인 요약을 반환한다.
- 권한 범위는 기존 대시보드/파이프라인 패턴을 따른다. Salesman은 본인 데이터, Manager는 같은 회사 실무자, Admin은 기존 관리자 필터가 있으면 필터를 반영하고 없으면 전체 데이터를 본다.
- React `/dashboard/`는 새 API를 호출해 실제 KPI/오늘 일정/최근 활동/우선 고객을 표시하고, 저장/상세 작업은 기존 Django 운영 화면 링크로 연결한다.
- `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/`는 이번 작업에서 확장하지 않는다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Customers 실제 데이터 연결

**목표**: React `/customers/` placeholder를 Django CRM 고객 데이터 기반 화면으로 교체한다.

**작업 범위**:

- 대시보드 API의 미로그인 HTML 200 문제를 방지하기 위해 React용 JSON API는 미인증 시 401 JSON을 반환하도록 보정한다.
- Django에 인증이 필요한 읽기 전용 `/reporting/api/customers/` JSON API를 추가한다.
- API는 기존 `FollowUp`, `Company`, `Department`, `History` 데이터를 사용해 고객 목록, 우선순위 고객, 검색/담당자/우선순위 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 기존 dashboard API와 동일하게 유지한다.
- React `/customers/`는 고객 검색, 담당자 필터, 우선순위 필터, 우선 고객 리스트, 실제 고객 리스트를 표시하고 기존 Django 상세/등록/리포트 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Notes 실제 데이터 연결

**목표**: React `/notes/` placeholder를 Django CRM 영업노트/활동 히스토리 데이터 기반 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/notes/` JSON API를 추가한다.
- API는 기존 `History`, `FollowUp`, `Schedule`, `User` 데이터를 사용해 영업노트 목록, 지연/예정 다음 액션, 미검토 노트, 활동 유형/담당자 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 dashboard/customers API와 동일하게 유지한다.
- React `/notes/`는 키워드 검색, 담당자 필터, 활동 유형 필터, 검토 상태 필터, 다음 액션 필터와 실제 영업노트 목록을 표시하고 기존 Django 상세/작성 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Schedules 실제 데이터 연결

**목표**: React `/schedules/` placeholder를 Django CRM 일정 데이터 기반 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/schedules/` JSON API를 추가한다.
- API는 기존 `Schedule`, `PersonalSchedule`, `FollowUp`, `History`, `User` 데이터를 사용해 일정 목록, 오늘 일정, 이번 주 일정, 지연 일정, 상태/활동유형/담당자 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 dashboard/customers/notes API와 동일하게 유지한다.
- React `/schedules/`는 키워드 검색, 담당자 필터, 상태 필터, 활동 유형 필터, 기간 필터와 실제 일정 목록을 표시하고 기존 Django 상세/등록/캘린더/보고 작성 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 현재 `/schedules/` 실제 데이터 연결 및 검증: 약 1~2시간.
- 로그인된 운영 브라우저 왕복 동선 확인과 배포까지 포함하면 추가 20~40분.
- `/schedules/` 이후 남은 React shell 전환 핵심 작업은 `/ai-workspace/`이며, 범위 확정 후 약 2~4시간 예상.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React AI Workspace 실제 데이터 연결

**목표**: React `/ai-workspace/` placeholder를 기존 Django AI 운영 기능 상태를 보여주는 실제 업무 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/ai-workspace/` JSON API를 추가한다.
- API는 기존 `ai_chat`의 `AIDepartmentAnalysis`, `PainPointCard`, `AIFollowUpAnalysis`와 reporting의 `FollowUp`, `WeeklyReport` 데이터를 사용한다.
- 권한은 기존 AI 정책을 유지한다. 로그인은 필수이며, `can_use_ai=False` 사용자는 AI 데이터 없이 권한 없음 상태만 받는다.
- React `/ai-workspace/`는 AI 권한 상태, 부서 분석 대상, 분석 완료 현황, 미검증 PainPoint, 고객 분석 대상, 주간보고 AI 초안 링크를 표시하고 기존 Django AI 운영 화면으로 연결한다.
- 새 AI 생성/외부 API 호출은 하지 않는다. 분석 실행, 프롬프트 생성, 주간보고 초안 생성은 기존 Django 운영 화면/API로 연결한다.
- 기존 `/ai/*`, `/reporting/*`, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 현재 `/ai-workspace/` 실제 데이터 연결 및 검증: 약 2~4시간.
- 운영 로그인 세션에서 AI 권한 사용자/비권한 사용자 육안 확인과 배포까지 포함하면 추가 30~60분.
- 이 작업 완료 후 목표한 React shell 핵심 메뉴 실제 데이터 연결은 1차 완료 상태로 볼 수 있다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test ai_chat --verbosity=1`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Pipeline Pricing — 견적/협상/수주 단계 가격 반영

**목표**: React 파이프라인과 Django 파이프라인 보드에서 견적 제출, 협상, 수주 단계 고객의 금액을 기존 Quote 데이터에서 정확히 끌어온다.

**작업 범위**:

- `/reporting/api/pipeline/`가 파이프라인 단계에 맞는 Quote를 가격 기준으로 선택하도록 보정한다.
- `quote` 단계는 발송/검토/초안 등 진행 중 견적을 우선 사용한다.
- `negotiation` 단계는 협상중 견적을 우선 사용한다.
- `won` 단계는 계약전환/승인/납품전환 견적을 우선 사용한다.
- 최신 견적이 거절/만료 등 현재 단계와 맞지 않아도 단계에 맞는 견적 금액이 있으면 그 금액을 우선 반영한다.
- 기존 `/reporting/funnel/pipeline/` Django 보드도 같은 가격 기준을 사용한다.
- 인증, 권한 범위, 기존 `/reporting/*` 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Quote` 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 구현 및 테스트: 약 1~2시간.
- 운영 배포 및 미로그인/로그인 smoke 포함: 추가 20~40분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test reporting --verbosity=1`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Schedules Navigation — 일정 캘린더 우선 동선

**목표**: 프론트 `/schedules/` 진입 시 목록 화면 대신 기존 Django 일정 캘린더를 기본 업무 화면으로 연다.

**작업 범위**:

- 프론트 운영 서버에서 `/schedules/`와 `/schedules` 요청을 `/reporting/schedules/calendar/`로 리디렉션한다.
- React 런타임에서도 `/schedules/` 진입 시 일정 캘린더로 이동하게 보정한다.
- 일정 메뉴의 문구와 README를 캘린더 우선 동선으로 정리한다.
- 기존 Django 일정 목록, 일정 API, 일정 등록/상세/캘린더 기능은 유지한다.

**DB 변경 필요 여부**: 없음.

**예상 소요**:

- 구현 및 검증: 약 30~60분.
- 운영 배포 및 smoke 포함: 추가 20~40분.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- 운영/로컬에서 `/schedules/`가 `/reporting/schedules/calendar/`로 이동하는지 확인

---

## Pipeline Pricing — 실제 견적/납품 품목 기준 보강

**목표**: React 파이프라인과 Django 파이프라인 보드의 카드 금액을 운영에서 실제 입력하는 견적/납품 품목 데이터 기준으로 표시한다.

**작업 범위**:

- `quote`, `negotiation` 단계는 `Schedule(activity_type='quote')`의 `DeliveryItem` 금액을 우선 사용한다.
- 견적 일정에 품목 금액이 없으면 `History(action_type='quote')`에 직접 연결된 `DeliveryItem` 금액을 사용한다.
- 위 실제 업무 품목 데이터가 없을 때만 기존 `Quote` 모델 금액으로 fallback한다.
- `won` 단계는 완료된 납품 일정의 `DeliveryItem` 금액을 우선 합산한다.
- 납품 일정 품목이 없으면 연결된 납품 히스토리의 `DeliveryItem` 또는 `delivery_amount`를 사용한다.
- 일정 없이 등록된 납품 히스토리 품목/금액도 실제 납품 매출로 합산한다.
- 기존 `/reporting/*` 운영 화면, 인증/권한, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 필드만 조회한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Pipeline Won Cards — 견적 대비 실제 납품 매출 차이 표시

**목표**: 수주 단계 카드에서 대표 금액은 실제 납품 매출로 유지하되, 기준 견적 금액과 차액/차이율을 함께 보여준다.

**작업 범위**:

- `won` 단계 카드에 실제 납품 매출과 비교할 기준 견적 데이터를 계산한다.
- 기준 견적은 기존 운영 데이터 우선순위를 따른다: 견적 일정 품목 → 견적 히스토리 품목 → 승인/전환된 Quote → 진행/최근 Quote fallback.
- React `/` 파이프라인 상세 패널과 리스트, Django `/reporting/funnel/pipeline/` 보드에 견적 대비 차이를 표시한다.
- API 응답에 `quoteComparison`을 추가해 `quotedAmount`, `actualAmount`, `deltaAmount`, `deltaRate`, `status`, `source`를 내려준다.
- 기존 파이프라인 대표 금액, 단계 이동, 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 조회만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 배포와 운영 smoke까지 포함하면 추가 30~60분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Customers Page — 실제 고객 데이터 연결 보강

**목표**: React `/customers/` 화면을 기존 Django 고객/팔로우업 운영 데이터에 더 직접 연결해, 검색/담당자/우선순위 필터뿐 아니라 실제 활동 이력과 예정 일정까지 한 화면에서 확인한다.

**작업 범위**:

- `/reporting/api/customers/` payload에 고객별 활동 수, 일정 수, 예정 일정 수, 지연 후속 수, 다음 예정 일정 정보를 추가한다.
- 고객 목록에서 연락처, 최근 활동, 다음 액션, 예정 일정, 활동/일정 카운트를 함께 표시한다.
- 우선 고객 패널에서 지연 후속과 예정 일정 정보를 바로 볼 수 있게 한다.
- 기존 고객 상세, 고객 등록, 일정 등록, 고객 리포트 링크는 Django 운영 화면으로 유지한다.
- 인증/권한 범위는 기존 대시보드 scope 규칙을 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `History`, `Schedule` 조회와 annotate/prefetch만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Quote Loading — 부서 내 여러 견적 누락 보정

**목표**: 같은 부서/연구실에 견적이 여러 건 있을 때 한 건만 불러오는 문제를 해결한다.

**작업 범위**:

- 납품 일정 작성의 `견적에서 품목 불러오기` API가 선택 고객 1명 기준이 아니라 같은 부서의 접근 가능한 본인 견적 일정 전체를 반환하게 한다.
- 같은 부서의 여러 견적을 구분할 수 있도록 고객명, 업체/부서명, 일정 ID, 견적일, 금액을 payload와 모달에 표시한다.
- 고객 기록 API도 `Quote` 모델뿐 아니라 견적 일정의 품목/예상금액까지 포함해 부서 기준 견적 목록을 누락 없이 보여준다.
- 파이프라인 가격 기준은 동일 고객에 여러 견적 일정/견적 활동/Quote가 있으면 대표 1건이 아니라 같은 우선순위 소스의 금액을 합산해 표시한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 조회만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 고객 화면 배포와 함께 운영 smoke까지 포함하면 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Notes Page — 미검토/지연 노트 검토 동선 보강

**목표**: React `/notes/` 화면에서 단순 조회를 넘어, 관리자/매니저가 미검토 영업노트를 빠르게 확인하고 검토 완료 처리까지 할 수 있게 한다.

**작업 범위**:

- `/reporting/api/notes/` payload에 검토 가능 여부, 검토자/검토 시각, 검토 토글 URL, 첨부/댓글 수를 추가한다.
- React 노트 목록에 첨부/댓글 수, 검토 상태 상세, 검토 처리 버튼을 표시한다.
- 관리자/매니저 권한이 있는 경우에만 React에서 검토 완료/해제 POST를 노출한다.
- 검토 처리 후 현재 필터 조건으로 노트 데이터를 다시 불러와 미검토/지연 지표를 갱신한다.
- 기존 Django 영업노트 상세, 작성, 관리자 메모 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `HistoryFile`, `reply_memos`, `reviewed_at`, `reviewer` 조회와 기존 검토 토글 view만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Notes Review Permission — 회사별 매니저 기준 보정

**목표**: React `/notes/` 검토 완료/해제 권한을 최고권한자/admin이 아니라 각 소속 회사의 `manager` 계정 기준으로 제한한다.

**작업 범위**:

- `/reporting/api/notes/`의 `scope.canReview`, 노트별 `canReview`, `reviewToggleHref`를 `UserProfile.is_manager()` 기준으로 보정한다.
- `history_toggle_reviewed` POST도 `manager` 역할만 허용하고, 기존 같은 회사 접근 검사를 유지한다.
- React 문구 중 노트 검토 저장 뷰의 "관리자 검토" 표현을 "매니저 검토"로 수정한다.
- admin, salesman, 타회사 manager 차단 테스트를 추가한다.

**DB 변경 필요 여부**: 없음. 권한 조건과 테스트만 수정한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 30~60분.
- 배포와 운영 smoke 포함: 추가 30~60분.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI Workspace — 실제 대상 기반 프롬프트 큐 추가

**목표**: React `/ai-workspace/`가 단순 현황판이 아니라, 실제 부서/고객/PainPoint 데이터를 골라 외부 AI 작업에 바로 사용할 수 있는 프롬프트 큐를 제공하게 한다.

**작업 범위**:

- `/reporting/api/ai-workspace/`에 `promptTargets` payload를 추가한다.
- 부서 분석, 고객 분석, 미검증 PainPoint를 실제 데이터 기반 프롬프트 후보로 생성한다.
- React `/ai-workspace/`에 프롬프트 큐 패널과 복사 버튼을 추가한다.
- AI 권한이 없는 사용자는 기존처럼 빈 상태와 권한 안내만 받게 유지한다.
- 기존 `ai_chat` 분석 화면, 주간보고 AI 초안 API, 고객/노트 링크는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `AIDepartmentAnalysis`, `AIFollowUpAnalysis`, `PainPointCard` 조회 결과만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1.5~3시간.
- 전체 빌드/check와 운영 배포 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI Workspace — 프롬프트 문맥 확장

**목표**: `/ai-workspace/`의 AI 작업 큐 프롬프트가 실제 최근 활동과 금액 맥락을 더 잘 반영하도록 보강한다.

**작업 범위**:

- 부서/고객/PainPoint 프롬프트에 최근 영업노트 최대 3건을 추가한다.
- 열린 견적 건수/금액과 수주 금액 요약을 프롬프트에 추가한다.
- 열린 견적은 기존 `Quote`와 견적 일정의 `expected_revenue`를 사용하되, 동일 `Quote`가 있는 일정 금액은 중복 집계하지 않는다.
- 수주 금액은 `OpportunityTracking.current_stage='won'`의 실제 매출을 우선 사용하고, 없으면 전환 견적/납품 기록을 fallback으로 사용한다.
- React 화면 구조와 기존 AI 분석/주간보고 링크는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `Quote`, `Schedule`, `OpportunityTracking` 조회만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Frontend Auth Redirect — 미로그인 루트 진입 차단

**목표**: `https://sales-note-frontend-production.up.railway.app/`에 미로그인 상태로 접속하면 React mock/fallback 화면을 보여주지 않고 Django 로그인 화면으로 이동시킨다.

**작업 범위**:

- 프론트 API 호출이 Django 로그인 페이지로 리다이렉트된 HTML 응답을 받으면 `/reporting/login/`으로 이동한다.
- JSON API가 `401 {"error": "login_required"}`를 반환해도 동일하게 로그인 화면으로 이동한다.
- 루트 파이프라인뿐 아니라 dashboard/customers/notes/schedules/AI workspace API에도 같은 인증 처리 helper를 적용한다.
- 백엔드 인증/권한 정책은 변경하지 않는다.

**DB 변경 필요 여부**: 없음. 프론트 인증 응답 처리만 변경한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## CRM Shell Navigation — 프론트 중심 동선 안정화

**목표**: React 프론트와 Django 템플릿을 오가며 사용자가 길을 잃는 문제를 줄이고, 프론트를 주 CRM Shell로 고정한다.

**작업 범위**:

- 로그인 성공 기본 이동지를 Django 대시보드가 아니라 프론트 `/dashboard/`로 변경한다.
- Django 백엔드 루트(`/`)도 인증된 사용자는 프론트 대시보드로 보낸다.
- Django 공통 상단 바에 "프론트 CRM" 복귀 버튼과 "Django 작업 화면" 표시를 추가한다.
- React 상단/route 액션에서 Django 대시보드로 불필요하게 이동시키는 링크를 프론트 화면 중심으로 정리한다.
- 기존 Django 작성/상세/관리 화면은 유지하고, 저장/작성 작업에 필요한 링크만 Django로 남긴다.

**DB 변경 필요 여부**: 없음. URL/템플릿/프론트 링크 정리만 수행한다.

**검증 계획**:

- `python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Notes Create — 영업노트 빠른 작성

**목표**: React `/notes/` 화면에서 기본 영업노트를 바로 작성하게 만들어 Django 대시보드 모달 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/notes/`에 React 작성 폼용 고객/활동유형/저장 URL 정보를 추가한다.
- `/reporting/api/notes/create/` POST API를 추가한다.
- 작성 권한은 기존 정책을 보존해 manager는 차단하고, salesman/admin은 본인 담당 고객에만 작성 가능하게 제한한다.
- React `/notes/`에 빠른 작성 패널을 추가하고 저장 후 목록/지표를 새로고침한다.
- 첨부파일, 납품 품목, 상세 일정 기반 작성은 기존 Django 화면을 계속 사용한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedules List — 일정 화면 프론트 전환

**목표**: `/schedules/`를 기존 Django 캘린더로 즉시 이동시키지 않고 React 일정 목록 화면으로 열어 프론트 중심 CRM Shell을 강화한다.

**작업 범위**:

- React `SchedulesPage`가 이미 가진 필터/목록/오늘 일정/지연 일정 UI를 실제 `/reporting/api/schedules/` 데이터에 연결한다.
- 프론트 서버의 `/schedules/` 강제 Django 캘린더 리다이렉트를 제거한다.
- 기존 Django 일정 캘린더, 일정 등록, 개인 일정 등록, 일정 상세/보고 작성 링크는 React 화면의 보조 작업 링크로 유지한다.
- `/reporting/*` 경로와 기존 Django 일정 기능은 삭제하지 않는다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `PersonalSchedule`, `History`, `FollowUp` 조회 API만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedules Quick Create — 일정 빠른 등록

**목표**: React `/schedules/` 화면에서 기본 고객 일정을 바로 등록하게 만들어 Django 일정 생성 폼 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/schedules/`에 React 빠른 등록 폼용 고객/활동유형/저장 URL 정보를 추가한다.
- `/reporting/api/schedules/create/` POST API를 추가한다.
- 작성 권한은 기존 정책을 보존해 manager는 차단하고, salesman/admin은 본인 담당 고객 일정만 빠르게 등록하게 제한한다.
- React `/schedules/`에 빠른 등록 패널을 추가하고 저장 후 일정 목록/지표를 새로고침한다.
- 납품 품목, 선결제, 첨부, 고급 편집은 기존 Django 일정 폼을 계속 사용한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Detail — 고객 상세/이력 프론트 전환

**목표**: 고객 목록에서 Django 상세 화면으로 바로 넘어가지 않고 React 안에서 고객별 최근 영업노트, 예정 일정, 지연 후속을 확인하게 만든다.

**작업 범위**:

- `/reporting/api/customers/<id>/` 고객 상세 요약 API를 추가한다.
- API는 기존 권한 규칙을 유지해 로그인/회사/담당자 범위 밖 고객 데이터 노출을 막는다.
- React `/customers/<id>/` route를 추가하고 고객 요약, 최근 노트, 예정 일정, 지연 후속, Django 상세 링크를 표시한다.
- 고객 목록/우선 고객 링크를 React 상세 route로 변경한다.
- 일정 빠른 등록 저장 후 Django 일정 상세로 들어갈 수 있는 링크를 성공 메시지에 표시한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `History`, `Schedule` 조회만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Notes Customer Prefill — 고객 상세 노트 작성 연결

**목표**: React 고객 상세에서 영업노트 작성으로 바로 이동하고, `/notes/?create=1&customer=<id>` 진입 시 해당 고객을 빠른 작성 폼에 자동 선택한다.

**작업 범위**:

- React 고객 상세 상단 작업에 `노트 작성` 링크를 추가한다.
- React 노트 빠른 작성 폼이 `customer` query parameter를 읽어 허용된 고객이면 우선 선택한다.
- 저장 후 폼 초기화에서도 고객 상세에서 넘어온 고객 선택을 유지한다.
- 기존 Django 영업노트 상세/작성 기능과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp` 모델과 노트 생성 API만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Quick Create — 고객 빠른 등록

**목표**: React `/customers/` 목록에서 Django 고객 생성 폼으로 빠지지 않고 기본 고객 정보를 바로 등록한다.

**작업 범위**:

- `/reporting/api/customers/`에 고객 빠른 등록용 업체/부서/우선순위/저장 URL 정보를 추가한다.
- 기존 `/reporting/api/followups/create/` AJAX 생성 API를 React에서 재사용한다.
- Manager 생성 차단과 업체 접근 권한 검증은 기존 정책을 유지한다.
- React 고객 화면에 빠른 등록 패널을 추가하고 저장 후 고객 목록/지표를 새로고침한다.
- 업체/부서 신규 생성, 고급 필드, 삭제/수정은 기존 Django 화면을 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Company`, `Department`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Inline Company/Department Create — 고객 등록 업체/부서 연결

**목표**: React 고객 빠른 등록 화면에서 기존 업체/부서가 없을 때 Django 관리 화면으로 이동하지 않고 바로 업체와 부서를 추가한다.

**작업 범위**:

- 기존 `/reporting/api/companies/create/`, `/reporting/api/departments/create/` API를 React에서 호출한다.
- 회사/부서 생성 API도 Manager 생성 차단과 업체 접근 권한을 보강한다.
- React 고객 빠른 등록 패널에 새 업체/학교, 새 부서/연구실 입력과 추가 버튼을 배치한다.
- 업체/부서 추가 후 고객 등록 폼 선택값을 방금 만든 항목으로 자동 갱신한다.
- 기존 Django 업체/부서 관리 화면은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Company`, `Department` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Detail Edit — 고객 상세 수정 전환

**목표**: React `/customers/<id>/` 상세 화면에서 Django 고객 수정 화면으로 이동하지 않고 고객 기본정보를 바로 수정한다.

**작업 범위**:

- `/reporting/api/customers/<id>/` 상세 API에 수정 가능 여부, 저장 URL, 업체/부서/상태/우선순위/파이프라인 옵션을 추가한다.
- `/reporting/api/customers/<id>/update/` POST API를 추가해 고객명, 업체, 부서, 책임자, 연락처, 이메일, 주소, 메모, 상태, 우선순위, 파이프라인 단계를 저장한다.
- 기존 권한 정책을 유지해 manager는 수정 불가, salesman은 본인 고객만 수정 가능, admin은 수정 가능하게 한다.
- React 고객 상세에 수정 패널을 추가하고 저장 후 상세 데이터를 다시 불러온다.
- 기존 Django `/reporting/followups/<id>/edit/` 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `Company`, `Department` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Sales Note Detail Edit — 영업노트 상세/수정 전환

**목표**: React `/notes/<id>/`에서 영업노트 상세를 확인하고, 권한이 있는 사용자는 Django 수정 화면으로 이동하지 않고 주요 노트 내용을 바로 수정한다.

**작업 범위**:

- `/reporting/api/notes/<id>/` 상세 API를 추가해 기존 `History` 기반 영업노트 상세, 고객/일정 연결, 검토 상태, 첨부/댓글 요약, 수정 옵션을 제공한다.
- `/reporting/api/notes/<id>/update/` POST API를 추가해 활동 유형, 고객, 활동일, 내용, 다음 액션, 다음 예정일, 미팅/납품/서비스 관련 필드를 저장한다.
- 기존 권한 정책을 유지해 manager는 상세 조회와 검토만 가능하고 수정은 차단하며, salesman은 본인 노트만 수정 가능하게 한다.
- React `/notes/<id>/` route를 추가하고 목록/고객 상세의 영업노트 링크가 React 상세로 이어지게 한다.
- 기존 Django `/reporting/histories/<id>/` 상세/수정 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp`, `Schedule`, `HistoryFile` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Detail Edit — 일정 상세/수정 전환

**목표**: React `/schedules/<id>/`에서 고객 일정 상세를 확인하고, 권한이 있는 사용자는 Django 수정 화면으로 이동하지 않고 주요 일정 정보를 바로 수정한다.

**작업 범위**:

- `/reporting/api/schedules/<id>/` 상세 API를 추가해 기존 `Schedule` 기반 일정 상세, 연결 고객/영업노트/납품 항목, 수정 옵션을 제공한다.
- `/reporting/api/schedules/<id>/update/` POST API를 추가해 고객 연결, 일정일/시간, 활동 유형, 상태, 장소, 메모, 예상 매출, 확률, 예상 종료일을 저장한다.
- 기존 권한 정책을 유지해 manager는 상세 조회만 가능하고 수정은 차단하며, salesman은 본인 일정만 수정 가능하게 한다.
- React `/schedules/<id>/` route를 추가하고 일정 목록의 고객 일정 링크가 React 상세로 이어지게 한다.
- 기존 Django `/reporting/schedules/<id>/` 상세/수정 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `FollowUp`, `History`, `DeliveryItem` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Attachments — 일정 상세 첨부파일 전환

**목표**: React `/schedules/<id>/` 상세 화면에서 일정 첨부파일을 업로드하고 삭제하게 만들어 Django 상세 화면 왕복을 줄인다.

**작업 범위**:

- 일정 상세 API에 첨부파일 업로드 URL과 파일별 삭제 URL을 제공한다.
- 기존 일정 파일 업로드/삭제 뷰의 권한을 React 일정 수정 정책과 맞춰 manager는 조작 불가, 담당자는 본인 일정만 조작 가능하게 보강한다.
- React 일정 상세의 첨부파일 섹션에 다중 파일 업로드, 삭제 버튼, 진행/성공/오류 상태를 추가한다.
- 기존 Django `/reporting/schedules/<id>/files/upload/`, 다운로드, 삭제 URL과 `/reporting/*` 상세 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `ScheduleFile` 모델과 파일 저장 정책만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Note Attachments — 영업노트 상세 첨부파일 전환

**목표**: React `/notes/<id>/` 상세 화면에서 영업노트 첨부파일을 업로드하고 삭제하게 만들어 Django 영업노트 수정 화면 왕복을 줄인다.

**작업 범위**:

- 영업노트 상세 API에 첨부파일 업로드 URL과 파일별 삭제 URL을 제공한다.
- `/reporting/api/notes/<id>/files/upload/` POST API를 추가해 기존 `HistoryFile` 모델로 다중 파일 업로드를 처리한다.
- 기존 파일 다운로드/삭제 URL은 유지하고 React 파일 목록에서 다운로드 링크와 삭제 버튼을 분리한다.
- 권한은 기존 영업노트 수정 정책을 유지해 manager는 파일 조작 불가, salesman은 본인 노트만 조작 가능하게 한다.
- 기존 Django `/reporting/histories/<id>/` 상세/수정과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `HistoryFile` 모델과 파일 검증 정책만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Note Replies — 영업노트 댓글/매니저 메모 전환

**목표**: React `/notes/<id>/` 상세 화면에서 댓글과 매니저 메모를 작성·삭제하게 만들어 Django 영업노트 상세 화면 왕복을 줄인다.

**작업 범위**:

- 영업노트 상세 API에 댓글 작성 URL, 댓글별 삭제 URL, 삭제 가능 여부를 제공한다.
- 기존 `/reporting/api/histories/<id>/add-manager-memo/`, `/reporting/api/histories/<id>/delete-manager-memo/` API를 React에서 호출한다.
- 기존 권한 정책을 유지해 manager는 같은 회사 노트에 매니저 메모를 작성할 수 있고, 실무자는 본인 노트에 댓글을 작성할 수 있게 한다.
- 댓글 삭제는 기존 정책대로 작성자 본인만 가능하게 유지한다.
- 기존 Django `/reporting/histories/<id>/` 상세와 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History.parent_history` 댓글 구조를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Delivery Items — 일정 납품 품목 편집 전환

**목표**: React `/schedules/<id>/` 상세 화면에서 납품 품목을 추가/수정/삭제하게 만들어 Django 일정 상세 모달 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/schedules/<id>/delivery-items/update/` POST API를 추가해 기존 `DeliveryItem` 모델을 저장한다.
- 기존 권한 정책을 유지해 manager는 편집 불가, salesman은 본인 일정만 편집 가능하게 한다.
- 납품 품목 저장 후 연결된 납품 History의 `delivery_items`/`delivery_amount` 요약도 기존 Django 흐름처럼 동기화한다.
- React 일정 상세 API에 납품 품목 저장 URL을 내려준다.
- React `/schedules/<id>/` 납품 품목 섹션에 편집 패널, 품목 추가, 행 삭제, 세금계산서 체크, 저장 상태를 추가한다.
- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 상세/수정 화면과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `DeliveryItem`, `Schedule`, `History` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Delivery Product Selection — 납품 품목 제품 마스터 선택 전환

**목표**: React `/schedules/<id>/` 납품 품목 편집 패널에서 기존 제품 마스터를 검색·선택해 품번, 단위, 현재 단가를 자동 반영하게 만든다.

**작업 범위**:

- 기존 `/reporting/api/products/` 응답에 React 납품 품목 편집에 필요한 단위와 규격 정보를 포함한다.
- 제품 목록 조회와 저장 권한은 기존 회사/부서/담당자 접근 범위를 유지한다.
- `/reporting/api/schedules/<id>/delivery-items/update/` 저장 payload에 `productId`를 허용하고 접근 가능한 제품만 연결한다.
- 제품을 선택한 납품 품목은 기존 `DeliveryItem.product` 관계를 저장하고, 모델의 기존 저장 정책대로 품번/단위/현재 단가를 반영한다.
- React 납품 품목 편집 행에 제품 검색/선택 UI를 추가하고, 수기 품목 입력 흐름은 유지한다.
- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 제품 관리 화면, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Product`와 `DeliveryItem.product` 필드를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer AI Result Verification — 고객 상세 AI 결과/검증 전환

**목표**: React `/customers/<id>/` 고객 상세 화면에서 부서 AI 분석 실행 후 결과 요약, 추천 액션, PainPoint 카드 검증까지 이어서 처리하게 만든다.

**작업 범위**:

- 기존 `AIDepartmentAnalysis`, `PainPointCard` 모델만 사용하고 신규 DB 필드는 추가하지 않는다.
- 고객 상세 API의 `aiDepartment` payload에 분석 기간, 미팅/견적/납품 인사이트, 추천 액션, 확인 필요 사항, PainPoint 카드 목록을 추가한다.
- PainPoint 검증 저장은 기존 `ai_chat:verify_card` POST API를 React에서 호출하도록 연결한다.
- 검증 권한은 기존 `can_use_ai` + 본인 담당 부서 분석 소유자 정책을 유지한다.
- React 고객 상세의 부서 AI 카드에서 결과를 펼쳐보고 미검증 PainPoint를 확인/부정 처리할 수 있게 한다.
- 기존 Django `/ai/department/<id>/`, `/ai/card/<id>/verify/`, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 AI 분석/카드 모델과 검증 상태 필드를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI PainPoint Verification Memory — 재분석 검증 메모리 반영

**목표**: 부서 AI 재분석 시 기존 PainPoint 검증 상태와 검증 메모를 GPT 입력 컨텍스트에 포함해 이미 확인/부정한 내용을 다시 묻지 않게 한다.

**작업 범위**:

- 기존 `PainPointCard.verification_status`, `verification_note`, `verified_at` 필드를 메모리 소스로 사용한다.
- 기존 `AIDepartmentAnalysis.analysis_data` JSON에 검증 메모리 사본을 저장해 재분석 후에도 다음 분석에서 사용할 수 있게 한다.
- 부서 분석 프롬프트에 `기존 PainPoint 검증 메모리` 섹션을 추가한다.
- 재분석 시 미검증 카드만 교체하고, 확인됨/부정됨 카드는 기존 검증 결과와 메모를 보존한다.
- GPT가 같은 가설/질문을 다시 반환해도 기존 검증 메모리와 중복되는 카드는 저장하지 않는다.
- 신규 DB 필드나 migration은 추가하지 않는다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드와 JSON payload만 사용한다.

**검증 계획**:

- `python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/api/customers/454/` login 보호 smoke check

---

## AI Verification-Based Insights — 검증 메모 분석 반영 강화

**목표**: 사용자가 PainPoint 검증 때 남긴 메모를 단순 저장/중복 방지용이 아니라 GPT의 요약, PainPoint, 다음 액션, 추가 검증 질문에 반영되는 분석 근거로 승격한다.

**작업 범위**:

- 기존 `PainPointCard.verification_status`, `verification_note`, `verified_at`와 `AIDepartmentAnalysis.analysis_data` JSON만 사용한다.
- 부서 AI 프롬프트에서 검증 메모리를 미팅 기록과 동급의 분석 근거로 명시한다.
- GPT 응답 계약에 `verification_insights`를 추가하고, GPT가 누락해도 서버에서 검증 메모 기반 fallback 인사이트/다음 액션/추가 질문을 저장한다.
- 고객 상세 API의 `aiDepartment` payload에 `verificationInsights`를 추가한다.
- React 고객 상세 AI 결과에 `검증 기반 인사이트` 섹션을 추가해 검증 메모가 다음 검증/액션으로 이어지는지 확인할 수 있게 한다.
- 기존 Django `/ai/*`, React 고객 상세, `/reporting/*` 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드와 JSON payload만 사용한다.

**검증 계획**:

- `python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py test ai_chat.tests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke check

---

## Project Direction Documentation — React 단일 CRM 프론트 목표 문서화

**목표**: 프로젝트의 최종 방향을 "React 단일 CRM 프론트 + Django 백엔드/API"로 명확히 문서화하고, 작업마다 Railway 배포 후 사용자 수동검수를 받는 운영 방식을 표준화한다.

**작업 범위**:

- `AGENTS.md`, `.github/copilot-instructions.md`에 최종 아키텍처와 작업 후 Railway 배포/수동검수 규칙을 추가한다.
- `PROJECT_BRIEF.md`에 React CRM 통일, Django backend-only, Django 템플릿 최종 삭제 방향을 추가한다.
- `SALES_CRM_SPEC.md`에 React 마이그레이션 요구사항과 UI 방향을 명시한다.
- `QA_CHECKLIST.md`에 React migration, React build, Railway deployment, manual server test 항목을 추가한다.
- `AGENT_REPORT.md`에 문서 업데이트와 배포 상태를 기록한다.

**DB 변경 필요 여부**: 없음. 문서 변경만 수행한다.

**검증 계획**:

- `git diff --check`
- `python manage.py check`
- `cd frontend && npm run build` (현재 작업 트리에 React runtime 변경도 포함되어 있어 함께 확인)
- Railway 배포가 필요한 runtime 변경이 포함된 경우 `web`, `sales-note-frontend` 배포 후 운영 smoke check

---

## Urgent Weekly Report Quote/Delivery Amount Loading — 주간보고 견적/납품 금액 포함

**목표**: 운영 주간보고 작성 화면(`/reporting/weekly-reports/create/`)에서 `일정 불러오기`로 견적 제출 및 납품 기록을 가져올 때 금액도 카드와 삽입 텍스트에 함께 포함한다.

**작업 범위**:

- 기존 `weekly_report_load_schedules` JSON API에 견적/납품 일정 금액 필드를 추가한다.
- 견적 금액은 연결 `Quote.total_amount`를 우선 사용하고, 견적 일정에 Quote가 없으면 `DeliveryItem` 합계 또는 `Schedule.expected_revenue`를 fallback으로 사용한다.
- 납품 금액은 연결 `DeliveryItem.total_price` 합계를 우선 사용하고, 없으면 연결 `History.delivery_amount`, 없으면 `Schedule.expected_revenue`를 fallback으로 사용한다.
- 기존 인증 조건(`@login_required`)과 본인 일정만 조회하는 데이터 범위를 유지한다.
- 기존 Django 템플릿 화면에서 API로 받은 금액을 카드에 표시하고, 선택 삽입 시 `견적 금액`/`납품 금액` 줄을 포함한다.
- 페이지 최초 진입 시에도 최신 API 기반 카드가 렌더링되도록 초기 로드에서 `loadSchedules()`를 실행한다.

**DB 변경 필요 여부**: 없음. 기존 `Quote`, `DeliveryItem`, `History`, `Schedule.expected_revenue`만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 서비스 배포 및 운영 `/reporting/weekly-reports/create/` 수동검수 절차 제공

---

## Urgent Weekly Report Rich Text HTML Normalization — 주간보고 HTML 이중 escape 방지

**목표**: 주간보고 작성/수정 저장 시 Quill HTML이 `<p>&lt;p&gt;...` 형태로 이중 escape되어 저장/표시되는 문제를 막는다.

**작업 범위**:

- 주간보고 HTML 정화 유틸에 escaped rich text 입력을 정상 HTML로 되돌리는 정규화 단계를 추가한다.
- `<p>&lt;p&gt;...&lt;/p&gt;</p>`처럼 이미 깨진 저장값도 상세 렌더링 시 정상 문단으로 보정한다.
- `bleach` fallback 환경에서도 HTML 태그 문자열이 그대로 보이지 않도록 plain text 문단으로 변환한다.
- 주간보고 생성 POST 회귀 테스트로 저장값과 상세 렌더링에 `&lt;p&gt;`가 남지 않는지 검증한다.

**DB 변경 필요 여부**: 없음. 기존 `WeeklyReport` 텍스트 필드와 HTML 정화 유틸만 수정한다.

**검증 계획**:

- `python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 서비스 배포 및 운영 `/reporting/weekly-reports/create/` 수동검수 절차 제공

---

## M1 Commercial Schedule Consistency Panel — 일정 상세 정합성 패널

**목표**: React 일정 상세 화면에서 견적/납품/서류/메일 자동첨부 상태를 한눈에 확인할 수 있는 읽기 전용 정합성 패널을 추가한다.

**작업 범위**:

- 기존 `/reporting/api/schedules/<id>/` 응답에 `commercialChecks` 객체를 추가한다.
- `commercialChecks`는 기존 `Schedule`, `DeliveryItem`, `DocumentGenerationLog`, `DocumentTemplate`, `EmailLog` 데이터를 읽어 계산한다.
- 견적 일정은 견적서 구분별 품목 수/금액, 등록 견적서 PDF 수, 자동첨부 후보 상태, 납품 반영 금액/잔여 금액, 완료 견적의 재불러오기 후보 잔류 여부를 표시한다.
- 납품 일정은 납품 품목 총액, 연결된 원본 견적 수, 등록 거래명세서 PDF, 자동첨부 후보 상태, 납품 노트 금액 불일치 가능성을 표시한다.
- React 일정 상세에 경고/정상/정보 상태를 표시하는 별도 내부 CRM 패널을 추가한다.
- 기존 품목 저장, 서류 생성, 메일 발송 링크와 `/reporting/*` legacy fallback은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델과 생성 로그/첨부 상태만 읽어 계산한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 API/React 일정 상세 smoke check

---

## M2 Quote Import and Partial Delivery Guards — 견적 불러오기/부분 납품 방어 강화

**목표**: React 일정 상세의 `견적 불러오기`에서 남은 견적 품목과 부분 납품 상태를 더 명확히 보여주고, 서버 저장 단계에서 같은 견적 품목이 중복 또는 초과 납품으로 저장되지 않도록 막는다.

**작업 범위**:

- 기존 `Schedule`, `DeliveryItem`, `History`, `ScheduleQuoteGroupNote` 모델만 사용하고 신규 DB 필드는 추가하지 않는다.
- `/reporting/api/followups/<id>/quote-items/` 응답에 원 견적 수량, 이미 납품 반영된 수량, 남은 수량, 부분 납품 여부를 품목/견적 구분 단위로 추가한다.
- React `견적 불러오기` 카드에서 남은 수량 기준임을 표시하고, 부분 납품/남은 품목 상태를 사용자가 저장 전 확인할 수 있게 한다.
- `/reporting/api/schedules/<id>/delivery-items/update/` 저장 시 `sourceQuoteItemId` 기준으로 이미 다른 납품 일정에 반영된 수량과 현재 저장 요청 수량의 합이 원 견적 수량을 넘으면 400으로 차단한다.
- 같은 저장 요청 안에서 동일 `sourceQuoteItemId`가 중복 행으로 들어오면 400으로 차단하고, 부분 납품은 한 행의 수량 조정으로 처리하게 안내한다.
- 기존 납품 일정의 견적 연결 품목을 제거하거나 수동 품목으로 바꾸는 경우에도 기존 원본 견적 일정 상태를 재계산해 미납 품목이 남으면 `scheduled`로 되돌린다.
- 기존 `/reporting/*` legacy fallback, 인증/권한 정책, 문서 생성/메일 발송 흐름은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `DeliveryItem.source_quote_schedule`, `DeliveryItem.source_quote_item`, `quantity`, `status` 필드와 계산 로직만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 API/React 일정 상세 smoke check

---

## AI Workspace 2.0 Action Center — AI 영업 지휘석 1단계

**목표**: React `/ai-workspace/`를 단순 AI 분석/프롬프트 허브에서 매일 실행할 영업 우선순위, 근거, AI 초안 생성을 한 화면에서 처리하는 내부 CRM 액션센터로 확장한다.

**작업 범위**:

- 기존 `/reporting/api/ai-workspace/` 응답에 `dailyBrief`와 `actionQueue`를 추가하고 기존 필드는 유지한다.
- `actionQueue`는 기존 `FollowUp`, `History`, `Schedule`, `Quote`, `DeliveryItem`, `WeeklyReport`, `PainPointCard`만 읽어 계산한다.
- 우선순위 후보는 미전환 견적 후속, 부분 납품/납품 예정 리스크, 지연 또는 날짜 미정 후속조치, 미검증 PainPoint, 이번 주 주간보고 누락으로 구성한다.
- 각 액션은 고객/회사/부서, 금액 영향, 기한, 우선순위 점수, 추천 행동, 근거, 관련 React/Django 링크, 생성 가능한 초안 유형을 포함한다.
- 신규 `POST /reporting/api/ai-workspace/actions/draft/` API를 추가해 action id와 draft type 기준으로 메일/영업노트/질문/주간보고 초안을 생성한다.
- 초안 API는 사용자가 승인하기 전에는 CRM 데이터를 저장하거나 메일을 발송하지 않는다.
- OpenAI 호출 실패 또는 키 미설정 시에는 입력 근거 기반의 안전한 로컬 fallback 초안을 반환한다.
- React `/ai-workspace/` 상단에 Daily Brief와 Action Queue를 추가하고, 액션 카드에서 초안 생성/복사/관련 화면 이동을 지원한다.
- 기존 Django AI 허브, 부서 분석 실행, PainPoint 검증, `/reporting/*` 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 1단계는 계산형 action queue와 비저장 초안 API만 추가한다. AI 사용 로그/ROI 추적용 `AIActionLog`는 다음 단계에서 별도 migration으로 검토한다.

**검증 계획**:

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/`, `/reporting/api/ai-workspace/`, `/reporting/api/ai-workspace/actions/draft/` smoke check

---

## AI Workspace Sold Quote Exclusion Hotfix — 완료/판매 견적 지휘석 제외

**목표**: 이미 완료/판매 처리된 견적 일정이 AI 지휘석의 `견적 후속` 액션으로 다시 표시되지 않게 한다.

**작업 범위**:

- `Quote.converted_to_delivery=False`가 남아 있어도 연결 견적 일정 `Schedule.status='completed'`이면 AI action queue의 견적 후속 후보에서 제외한다.
- Quote 객체가 없는 fallback 견적 일정 후보도 `status='scheduled'`인 경우만 AI action queue에 포함한다.
- AI 프롬프트용 열린 견적 금액 계산에서도 완료된 견적 일정과 완료 일정에 연결된 Quote를 제외한다.
- schedule `415`처럼 이미 판매 완료된 견적이 다시 후속 대상으로 뜨는 회귀 케이스를 테스트로 고정한다.

**DB 변경 필요 여부**: 없음. 기존 상태 필터만 보정한다.

**검증 계획**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/api/ai-workspace/` 비로그인 401 smoke check

---

## AI Workspace Action Feedback Loop — 추천실행목록 현장 답변 기록

**목표**: React `/ai-workspace/`의 `AI 추천 실행 목록`에서 사용자가 현장 답변을 직접 남기면, CRM 이력에 기록하고 AI가 다음 액션 유지/정리 여부를 판단해 추천 목록을 갱신한다.

**작업 범위**:

- 추천 액션별 사용자 답변, AI 판단 결과, 액션 스냅샷, 연결 영업노트 이력을 저장하는 `AIWorkspaceActionFeedback` 모델과 migration을 추가한다.
- 기존 action queue 생성 payload에 `followupId`와 저장된 feedback 요약을 포함한다.
- 저장된 feedback이 `resolved` 또는 `dismissed`로 판단된 액션은 다음 `/reporting/api/ai-workspace/` 조회에서 추천 목록에서 제외한다.
- 신규 `POST /reporting/api/ai-workspace/actions/feedback/` API를 추가한다.
- feedback API는 기존 `can_use_ai` 권한을 유지하고, action id가 현재 사용자 큐에 있는지 확인한 뒤 처리한다.
- API는 사용자가 입력한 답변을 `History(action_type='memo')`로 남기고, AI 판단 결과를 feedback 모델에 저장한다.
- OpenAI 호출 실패 또는 키 미설정 시에도 로컬 규칙으로 `종료/다음 액션`을 판단한다.
- React 액션 카드에 `현장 답변 기록` 입력창과 `기록하고 AI 판단` 버튼을 추가하고, 기존 `질문/메일/노트/고객/AI` 같은 짧은 버튼명은 `질문 초안`, `고객 보기`, `AI 분석`처럼 의미가 드러나게 바꾼다.
- 기존 초안 생성 API는 유지하되, 답변 저장 흐름이 기본 동작이 되도록 배치를 조정한다.
- 기존 `/reporting/*`, AI 허브, PainPoint 검증, 초안 생성, 로그인/권한 정책은 유지한다.

**DB 변경 필요 여부**: 있음. 추천 액션 응답을 운영 이력으로 재사용하기 위해 `AIWorkspaceActionFeedback` 신규 모델과 migration을 추가한다. 기존 `History` 모델에는 필드를 추가하지 않는다.

**검증 계획**:

- `python manage.py makemigrations reporting`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 로컬 브라우저 smoke check 후 커밋/푸시
- Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/`, feedback API login 보호 smoke check

---

## AI Workspace Feedback Performance View — AI 실행 피드백 이력/성과

**목표**: React `/ai-workspace/`에서 추천 실행 목록에 남긴 현장 답변이 `기록됨`, `종료됨`, `다음 액션 전환됨` 중 어디로 갔는지 볼 수 있게 하고, AI 추천이 실제 영업노트/후속조치로 이어지는 흐름을 확인한다.

**작업 범위**:

- 기존 `AIWorkspaceActionFeedback` 모델만 읽어 계산한다. 신규 DB 필드는 추가하지 않는다.
- `/reporting/api/ai-workspace/` 응답에 `feedbackHistory` 객체를 추가하고 기존 응답 필드는 유지한다.
- `feedbackHistory`는 현재 사용자 기준으로 최근 30일/누적 답변 수, 종료/다음 액션/단순 기록/목록 제외 수, 영업노트 연결 수, 액션 유형별 건수를 포함한다.
- Manager/Admin은 기존 React dashboard scope 규칙을 사용해 접근 가능한 사용자 범위의 feedback을 볼 수 있게 하고, salesman은 본인 feedback만 본다.
- 최근 feedback 이력에는 담당자, 고객/회사/부서, 액션 유형/제목, 사용자가 남긴 답변, AI 요약, 다음 액션, CRM 메모 링크를 포함한다.
- React `/ai-workspace/`에 `AI 실행 피드백` 패널을 추가해 성과 지표와 최근 이력을 한 화면에서 볼 수 있게 한다.
- 기존 action queue, feedback 저장 API, 초안 생성 API, AI 허브, `/reporting/*` 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `AIWorkspaceActionFeedback`, `History`, `FollowUp`, `UserProfile`만 조회한다.

**검증 계획**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 로컬 browser/Playwright smoke check 후 커밋/푸시
- Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/` bundle/API smoke check

---

## AI Situation Sync / CRM State Reconciliation — AI 상황 입력 기반 CRM 상태 동기화

**인수인계 우선순위**: 사용자가 다음 작업으로 명시했습니다. 기존 권장 작업인 `M2 Quote Import and Partial Delivery Guards`보다 먼저 검토/구현합니다. 단, 새 구현을 시작하기 전에는 기존 규칙대로 `git status --short`, `git log --oneline -3` 확인 후 진행합니다.

**사용자 의도**:

- 사용자가 AI에게 “이런 상황입니다”라고 말하면, AI는 단순히 메모만 남기는 것이 아니라 CRM의 실제 상태를 같이 정리해야 합니다.
- 예: “홍철화 연구원은 견적을 줬지만 아직 안산대요”라고 입력하면 해당 견적/고객 관련 후속조치가 계속 `팔로우업`이나 `AI 추천 실행 목록`에 떠 있으면 안 됩니다.
- 예: “관심 있다고 하고 다음주에 다시 연락달래요”라면 기존 후속조치를 종료하지 말고 다음주 후속조치를 만들거나 갱신해야 합니다.
- 예: “메일 보냈는데 아직 답장이 안왔어요”라면 고객/견적/메일 대기 상태를 기록하고, 일정 기간 후 미응답 follow-up 추천으로 이어져야 합니다.

**목표**: `AI 추천 실행 목록`의 현장 답변 저장 흐름을 `CRM 상태 동기화`로 확장해, 사용자의 자연어 상황 입력이 `History`, `FollowUp`, AI 추천 숨김/유지, 알림/대시보드 노출 상태에 일관되게 반영되게 한다.

**작업 범위 1단계 — 수동 상황 입력 기반 동기화**:

- 기존 `POST /reporting/api/ai-workspace/actions/feedback/` 저장 후 AI 판단 결과를 실제 CRM 객체에 적용한다.
- AI 판단 결과를 표준 intent/status로 정규화한다.
  - `resolved_no_purchase`: 구매 의사 없음/당분간 안 삼/실패/보류. 기존 관련 FollowUp 종료 또는 보류, 추천실행목록 숨김.
  - `follow_up_needed`: 다음 연락/자료 요청/다음달 검토. 기존 FollowUp 갱신 또는 신규 FollowUp 생성.
  - `positive_buying_signal`: 긍정/구매 의향/승인 예정. FollowUp 우선순위 유지 또는 높은 우선순위 다음 액션 생성.
  - `email_waiting`: 메일 발송 후 답장 대기. 답장 대기 FollowUp 생성 또는 갱신.
  - `needs_human_review`: AI 확신 부족. CRM 메모만 남기고 자동 상태 변경은 하지 않음.
- 같은 고객/견적/action에 이미 열린 FollowUp이 있으면 새로 만들지 않고 갱신한다.
- 관련 FollowUp을 종료/보류/갱신할 때는 삭제하지 말고 audit 가능한 기록을 남긴다.
- `History(action_type='memo')`에는 사용자의 원문, AI 요약, 적용된 CRM 변경사항을 남긴다.
- AI가 적용한 변경 결과를 feedback 응답 payload에 포함해 React에서 “무엇이 바뀌었는지” 보여준다.
- React 액션 카드 저장 성공 메시지에 `후속조치 종료됨`, `다음 후속조치 생성됨`, `메일 답장 대기 등록됨`, `검토 필요` 같은 적용 결과를 표시한다.
- 기존 추천실행목록 생성 로직은 동기화 결과를 반영해 종료/보류된 항목을 다시 띄우지 않는다.
- 기존 `/reporting/*`, 인증/권한, CSRF, 영업노트, AI 초안 생성, feedback 이력 패널은 유지한다.

**작업 범위 2단계 — 메일 미응답 자동 감지 준비**:

- 현재는 Gmail/Microsoft 365 실메일 자동 조회가 제품 런타임에 붙어 있다는 전제가 없습니다. 1단계에서는 사용자가 “메일 보냈는데 답장 없음”이라고 입력한 상황을 기반으로 `email_waiting` 상태를 만든다.
- 코드베이스에 기존 메일 발송 로그, 수신 메일 모델, Gmail/Microsoft 365 연동 흔적이 있는지 먼저 확인한다.
- 기존 메일 데이터가 있으면 고객/이메일/견적 기준으로 “발송 후 N일 무응답” 후보를 AI action queue에 추가한다.
- 기존 메일 데이터가 없으면 이번 단계에서 외부 메일 연동을 새로 만들지 말고, `email_waiting` FollowUp/History 구조만 안정화한다.

**DB 변경 필요 여부**:

- 시작 전 반드시 `FollowUp`, `History`, `AIWorkspaceActionFeedback`, 알림/대시보드 관련 모델을 확인합니다.
- 1단계는 가능한 한 기존 `FollowUp` 상태/날짜/메모 필드와 `AIWorkspaceActionFeedback.ai_result` 또는 유사 JSON 저장 구조를 사용합니다.
- 기존 모델에 “AI가 어떤 FollowUp을 닫거나 만들었는지”를 충분히 추적할 필드가 없으면 migration을 검토합니다. 단, 필드를 추가하기 전 AGENT_PLAN에 구체 사유를 갱신하고 테스트 범위를 확정합니다.

**구현 시작 전 확인할 파일/로직**:

- `reporting/models.py`: `FollowUp`, `History`, `AIWorkspaceActionFeedback`, 고객/일정/견적 연결 구조
- `reporting/views.py`: `_build_ai_workspace_action_queue`, feedback 저장 API, followup 생성/수정 view, dashboard/alarm API
- `reporting/tests.py`: `AIWorkspaceSummaryApiTests`, followup/schedule 관련 테스트
- `frontend/src/api.ts`: feedback API 응답 타입
- `frontend/src/App.tsx`: AI action card 저장 UI, feedback performance panel
- `frontend/src/styles.css`: action card 상태 표시 스타일

**검증 계획**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- 필요 시 FollowUp 관련 테스트 클래스 추가 실행
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- migration 추가 시 `python manage.py makemigrations reporting` 후 migration 파일 검토
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 로컬 browser/Playwright smoke check 후 커밋/푸시
- Railway `web`, `sales-note-frontend` 배포 및 운영 `/ai-workspace/`, feedback API, followup 반영 smoke check

**수동검수 시나리오**:

1. `AI 추천 실행 목록`에서 견적 후속 액션을 고릅니다.
2. `홍철화 연구원은 견적을 줬지만 아직 안산대요`처럼 구매 의사 없음 답변을 저장합니다.
3. 해당 추천 액션이 사라지고, 관련 열린 FollowUp이 종료/보류 처리되며, 고객 영업노트에 적용 내용이 남는지 확인합니다.
4. 같은 고객/견적이 새로고침 후 다시 후속조치로 뜨지 않는지 확인합니다.
5. 다른 액션에 `관심 있다고 하고 다음주에 다시 연락달래요`라고 저장합니다.
6. 기존 FollowUp이 갱신되거나 다음주 FollowUp이 생성되는지 확인합니다.
7. `메일 보냈는데 아직 답장이 안왔어요`라고 저장합니다.
8. 답장 대기 FollowUp/History가 생성되고, 이후 AI 추천에서 미응답 follow-up으로 이어질 수 있는지 확인합니다.
9. AI 확신이 낮은 표현은 자동 변경 없이 `검토 필요`로 남는지 확인합니다.

### 2026-05-14 구현 계획 갱신

**확인 결과**:

- `FollowUp`은 고객/거래처 레코드이고, 실제 후속 할 일은 `History.next_action`, `History.next_action_date`, `History.reviewed_at` 조합으로 관리된다.
- `AIWorkspaceActionFeedback`에는 `ai_result` JSON 필드가 있어 intent, CRM 동기화 결과, audit 정보를 migration 없이 저장할 수 있다.
- 메일 런타임에는 `EmailLog`가 있으며 Gmail/IMAP 발송·수신 동기화 모델과 API가 존재한다. 단, 외부 메일 자동 조회를 새로 붙이지 않고 기존 저장 로그를 읽는 범위로 제한한다.
- 기존 AI feedback API는 메모 `History`를 만들고 추천 숨김만 처리하며, 원래 후속 History/Quote/Schedule/FollowUp 상태는 정리하지 않는다.

**DB 변경 필요 여부**: 없음. 기존 `History.reviewed_at/reviewer`, `History.next_action/next_action_date`, `FollowUp.status/priority/pipeline_stage`, `Schedule.status`, `Quote.stage`, `AIWorkspaceActionFeedback.ai_result`만 사용한다.

**구현 범위**:

- feedback 판단 결과를 `intent`로 정규화한다.
  - `resolved_no_purchase`, `follow_up_needed`, `positive_buying_signal`, `email_waiting`, `needs_human_review`.
- `resolved_no_purchase`는 관련 열린 `History` 후속조치를 검토 완료 처리하고, 견적/견적 일정은 거절 또는 취소 상태로 정리하며, 고객은 보류/장기 또는 lost 단계로 낮춘다.
- `follow_up_needed`, `positive_buying_signal`, `email_waiting`은 기존 열린 후속 History를 갱신하거나 새 후속 History를 생성한다.
- `needs_human_review`는 audit 메모만 남기고 상태 자동 변경을 하지 않는다.
- 적용된 변경사항을 `ai_result.crmSync`와 생성 메모 내용, React feedback 응답에 포함한다.
- 기존 `EmailLog`의 발신 후 미수신 스레드를 읽어 `email_waiting` AI action 후보를 추가한다.
- dashboard/API/AI action queue에서 `reviewed_at`으로 종료된 후속조치가 열린 할 일처럼 다시 뜨지 않도록 관련 필터를 보강한다.

**검증 계획**:

- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- 필요 시 dashboard/mailbox 관련 회귀 테스트 일부 실행
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
- 로컬 smoke 후 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 및 운영 smoke

**현재 상태 (2026-05-14)**:

- 백엔드/React 구현, 로컬 검증, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포 완료.
- DB 모델 변경 없음.
- Runtime commit: `6cae206 feat: sync AI situation feedback with CRM state`
- Railway `web`: `272ceafc-98a7-484c-9f7d-e282378eb339` SUCCESS
- Railway `sales-note-frontend`: `e528a8b0-4edd-4a36-a8e0-735384f6b8cf` SUCCESS
- 운영 smoke OK:
  - `/ai-workspace/` 200 with `assets/index-gjBpo90j.js` / `assets/index-Dztpo0tz.css`
  - `/reporting/login/` 200
  - anonymous `/reporting/api/ai-workspace/` 401 login-required JSON on frontend proxy and backend
  - anonymous feedback POST 403 CSRF
- 다음 행동: 사용자가 운영에서 AI 상황 입력 기반 CRM 상태 동기화를 수동 검수한다.

## 2026-05-14 레거시 AI 피드백 소급 동기화 계획

**배경**:

- 운영에서 홍철화 고객의 `quote_schedule:870` AI 피드백은 `resolved`로 저장되어 있었지만, 이번 CRM 동기화 배포 전에 생성된 기록이라 `ai_result.intent`와 `ai_result.crmSync`가 없다.
- 대시보드 지연 후속조치는 같은 고객의 과거 `History.reviewed_at IS NULL` 행에서 나오므로, 기존 레거시 피드백을 새 동기화 규칙으로 소급 적용해야 한다.
- 사용자가 AI에 상황을 보고하면 시스템 전체의 고객 긴급도도 함께 조정되어야 한다. 소급 처리도 현재 AI CRM 동기화 함수의 `FollowUp.priority/status/pipeline_stage` 갱신 경로를 그대로 사용한다.

**DB 변경 필요 여부**: 없음.

- 기존 `AIWorkspaceActionFeedback.ai_result` JSON에 `intent`/`crmSync`를 보강한다.
- 기존 `History.reviewed_at/reviewer`, `FollowUp.status/priority/pipeline_stage`, `Schedule.status`, `Quote.stage`만 갱신한다.

**구현 범위**:

- `reporting` 관리 명령을 추가해 `ai_result.crmSync`가 없는 기존 `AIWorkspaceActionFeedback`을 탐색한다.
- 기본 실행은 dry-run으로 하며, `--apply`가 있을 때만 실제 CRM 상태와 feedback JSON을 갱신한다.
- action snapshot 또는 저장된 followup/action id를 기반으로 동기화 action payload를 재구성한다.
- 기존 `ai_result`가 intent를 갖고 있지 않으면 현재 정규화 규칙으로 intent/status를 보강한다.
- 소급 대상은 기본적으로 `status`가 `resolved`, `next_action`, `answered`인 레거시 기록이며, `dismissed`는 CRM 자동 변경 없이 필요한 경우 JSON 보강만 검토한다.
- 운영 실행 전 dry-run 결과를 확인하고, 실제 적용 후 홍철화 고객의 지연 후속조치가 사라지는지 확인한다.

**검증 계획**:

- 레거시 resolved feedback이 열린 후속조치를 닫고 고객 긴급도를 `long_term`으로 낮추는 테스트 추가.
- 레거시 positive/next_action feedback이 고객 긴급도를 `urgent` 또는 `followup`으로 조정하는 테스트 추가.
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python -m py_compile reporting\views.py reporting\management\commands\backfill_ai_feedback_crm_sync.py reporting\tests.py`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포.
- 운영에서 `backfill_ai_feedback_crm_sync --dry-run --feedback-id 1`로 홍철화 대상 변경 내역 확인 후 `--apply --feedback-id 1` 적용, 필요 시 전체 레거시 건 dry-run 검토.

## 2026-05-14 메일 답장 HTML 원문 노출 수정 계획

**배경**:

- React 메일 스레드/답장 화면에서 수신 메일 본문이 `<html><head><style>...</style></head><body>...` 형태로 그대로 표시되는 사례가 남아 있다.
- 기존 `_email_body_text()`는 `EmailLog.body_html`이 있을 때만 HTML을 제거하고, HTML 문서가 일반 `EmailLog.body`에 저장된 경우에는 plain text로 간주해 그대로 내려보낼 수 있다.
- 답장 작성 중 HTML 문서 원문이 텍스트로 섞여 발송되는 경우도 같은 증상으로 이어질 수 있다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- 메일 본문 표시 helper에서 일반 `body` 필드에 들어온 실제/escaped HTML 문서를 감지해 스타일/스크립트/태그를 제거한 표시용 텍스트로 변환한다.
- outgoing 메일 처리에서 `body_text`에 HTML 문서가 들어온 경우 표시용 텍스트로 정리하고, escaped HTML이 `body_html`에 같이 들어온 경우 plain HTML로 다시 생성한다.
- React 스레드 API와 legacy Django 스레드/답장 화면 모두 정리된 표시용 본문을 사용하도록 한다.
- 기존 rich HTML 편집 본문은 유지하고, script/style/unsafe attribute 제거 로직은 그대로 보존한다.

**검증 계획**:

- `EmailLog.body`에 HTML 문서가 저장된 케이스에서 React thread API `bodyText`가 태그 없이 본문만 반환하는 테스트 추가.
- escaped HTML 문서가 `body`에 저장된 케이스도 태그 없이 표시되는 테스트 추가.
- 답장 API에 HTML 문서가 `body_text`로 들어와도 Gmail 발송 payload와 저장 로그가 정리되는 테스트 추가.
- `python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python -m py_compile reporting\gmail_views.py reporting\tests.py`
- `git diff --check`
- React 코드 변경 시 `cd frontend && npx tsc --noEmit --pretty false && npm run build`

## 2026-05-14 AI 보고 기반 고객 긴급도 세분화 계획

**배경**:

- 사용자가 AI 추천 실행 목록에 현장 상황을 보고하면 `FollowUp.priority`가 대시보드, 고객 목록, 파이프라인의 공통 고객 긴급도 기준이 된다.
- 이전 동기화는 intent 단위로 일부 긴급도를 조정하지만, 사용자가 직접 “긴급”, “오늘 처리”, “급하지 않음”, “장기”, “보류”처럼 말한 긴급도 신호를 별도 구조로 저장하지 않는다.
- 특히 기존 고객이 `urgent`인 상태에서 “나중에/장기/급하지 않음”으로 보고하면 후속조치 내용은 바뀌어도 고객 긴급도가 계속 높게 남을 수 있다.

**DB 변경 필요 여부**: 없음.

- 기존 `AIWorkspaceActionFeedback.ai_result` JSON에 `prioritySignal`을 저장한다.
- 기존 `FollowUp.priority` 필드만 갱신한다.

**구현 범위**:

- AI feedback fallback/OpenAI 판단 결과에 `prioritySignal`을 추가한다.
  - 지원 값: `urgent`, `followup`, `scheduled`, `long_term`, 없음.
- fallback 키워드로 명시적 긴급도 신호를 감지한다.
  - 긴급/오늘/즉시/빨리 → `urgent`
  - 후속/다음주/재연락/확인 필요 → `followup`
  - 예정/일정 확정 → `scheduled`
  - 장기/보류/나중/급하지 않음/다음달/내년 → `long_term`
- `_ai_workspace_update_followup_for_sync()`가 intent 기본값보다 명시적 `prioritySignal`을 우선 반영하게 한다.
- `crmSync.changes`에 고객 우선순위 변경 내역을 남겨 프론트의 AI feedback 응답과 감사 메모에서 확인 가능하게 한다.
- `needs_human_review`는 이전처럼 CRM 상태를 자동 변경하지 않는다.
- `/ai-workspace/?department_id=<id>`처럼 부서 상세 컨텍스트가 있는 경우 `AI 추천 실행 목록`은 해당 부서의 고객/견적/일정/메일/후속/PainPoint 액션만 반환한다.
- `/ai-workspace/`처럼 부서 파라미터가 없는 일반 화면은 기존 전체 action queue를 유지한다.

**검증 계획**:

- AI 보고에 “긴급/오늘 처리”가 들어오면 `follow_up_needed`라도 고객 `FollowUp.priority`가 `urgent`로 올라가는 테스트 추가.
- AI 보고에 “장기/보류/급하지 않음”이 들어오면 기존 `urgent` 고객도 `long_term`으로 내려가고 대시보드 우선 고객 목록에서 빠지는 테스트 추가.
- 부서 상세 `department_id` 요청에서는 다른 부서 action이 `actionQueue`에 섞이지 않고, 일반 요청에서는 기존처럼 전체 action이 유지되는 테스트 추가.
- 기존 positive/resolved/email_waiting 테스트가 깨지지 않는지 `AIWorkspaceSummaryApiTests` 전체 실행.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 프론트 타입/빌드는 API shape 후방 호환이면 변경 없음. 필요 시 `cd frontend && npx tsc --noEmit --pretty false && npm run build`.

## 2026-05-14 AI 워크스페이스 부서 검색 UI 개선 계획

**배경**:

- 운영 `/ai-workspace/` 화면에서 `Department analysis / 부서 분석 대상` 섹션이 `AI 추천 실행 목록` 아래에 있어, 부서 상세 탐색보다 추천 실행 목록이 먼저 보인다.
- 부서 분석 대상 리스트가 기본으로 전체 부서를 모두 보여줘 화면이 길어지고, 사용자는 검색한 결과만 보고 싶어 한다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- React AI 워크스페이스 화면에서 `부서 분석 대상` 섹션을 `AI 추천 실행 목록`보다 위로 이동한다.
- `AIWorkspaceDepartmentList`는 검색어가 없으면 전체 부서 리스트를 렌더링하지 않고 검색 안내만 표시한다.
- 검색어가 있을 때만 필터링된 부서 결과를 보여준다.
- 검색 결과가 없을 때는 빈 상태 문구를 표시한다.
- 백엔드 API shape와 `/reporting/*` 경로는 변경하지 않는다.

**검증 계획**:

- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- Railway `sales-note-frontend` 배포 후 운영 `/ai-workspace/` smoke 확인.

## 2026-05-14 AI 추천 실행 답변 action_not_found 수정 계획

**배경**:

- 운영 `AI 추천 실행 목록`의 `메일 답장 대기` 카드에서 사용자가 현장 답변을 입력하면 `action_not_found`가 반환되는 케이스가 발생했다.
- 부서 상세 화면은 `department_id` 기준으로 해당 부서의 오래된 메일 답장 대기 액션을 보여줄 수 있지만, 답변 저장 API는 전역 action queue만 다시 만들어 action id를 찾는다.
- 전역 queue에는 메일 답장 대기 액션이 최근 발송 메일 상위/최대 5건으로 제한되어 있어, 부서 상세에 보였던 오래된 액션이 저장 시점에 누락될 수 있다.
- 사용자의 답변처럼 “보상판매는 장기, 현재 팁 불만 해결이 급선무”인 경우 장기/긴급 신호가 함께 들어와도 고객의 현재 긴급도와 다음 액션이 잘 반영되어야 한다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- `_ai_workspace_find_action()`가 현재 queue에서 action을 못 찾으면 action id prefix와 소유권을 기준으로 액션 스냅샷을 직접 재구성하는 fallback을 추가한다.
- 우선 `email_waiting:<EmailLog.id>` 직접 재구성을 지원해, 부서 상세/오래된 메일 액션도 답변 저장과 초안 생성이 가능하게 한다.
- 직접 재구성은 반드시 `EmailLog.user == request.user`, `email_type='sent'`, `status='sent'`, `sent_at` 존재, 관련 `followup` 존재를 검증한다.
- fallback 판단 키워드에 `장기`, `허락 못받음`, `불만`, `클레임`, `급선무` 등 실제 현장 표현을 보강한다.
- 장기 보류와 현재 긴급 이슈가 함께 적힌 답변은 “현재/급선무/불만” 신호를 우선해 고객 긴급도를 `urgent`로 반영하도록 한다.

**검증 계획**:

- 부서 상세 action queue에는 보이지만 전역 queue에는 누락되는 오래된 `email_waiting` 액션에 답변을 저장하면 200이 반환되고 CRM sync가 적용되는 테스트 추가.
- “보상판매는 장기, 현재 팁 불만 해결이 급선무” 답변이 fallback에서도 `follow_up_needed` + `urgent` prioritySignal로 처리되는 테스트 추가.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 추천 실행 피드백 구체화 계획

**배경**:

- `문새롬 메일 답장 확인` 답변 저장은 정상 동작했지만, AI가 생성한 다음 액션이 “팁에 대한 불만 사항을 해결하기 위한 조치를 취하세요”처럼 너무 일반적이었다.
- 운영자가 바로 실행하려면 고객 불만의 확인 항목, 해결안 선택지, 회신 기준, 장기 이슈 분리 기준이 함께 나와야 한다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- 불만/클레임/급선무 유형의 사용자 답변에서 핵심 이슈명을 추출한다. 예: `팁에대한 불만` → `팁`.
- `보상판매 : ... 장기`처럼 장기 분리 대상이 함께 적힌 경우 별도 장기 후속으로 분리하라는 실행문을 포함한다.
- OpenAI가 일반적인 `nextAction`을 반환하더라도 서버 정규화 단계에서 더 구체적인 실행문으로 보정한다.
- OpenAI system rule에도 “조치를 취하세요” 수준의 일반 문장을 피하고 확인 항목/회신 기준을 포함하라는 지시를 추가한다.

**검증 계획**:

- OpenAI가 일반적인 다음 액션을 반환하는 테스트 더블을 넣어도 API 응답의 `nextAction`이 `팁`, `제품 규격`, `처리 예정 시간`, `보상판매`를 포함하는지 확인한다.
- 기존 fallback/부서 scoped email feedback 테스트가 같은 구체 실행문을 반환하는지 확인한다.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 실행 피드백 표시/상세 스코프 수정 계획

**배경**:

- React `/ai-workspace/`의 `AI 실행 피드백` 섹션에서 답변/판단/다음 액션 문구가 API excerpt 기준으로 짧게 잘려 보인다.
- `department_id`가 있는 상세 진입 화면에서도 피드백 히스토리는 전체 범위 기준으로 내려와, 해당 부서/고객 맥락과 다른 피드백이 함께 보일 수 있다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- `AI 실행 피드백` API payload에서 답변/판단/다음 액션/근거를 240~260자 단위로 자르지 않고 표시용 정제만 적용한다.
- `/reporting/api/ai-workspace/?department_id=<id>` 요청에서 선택 부서가 유효하면 `feedbackHistory`도 해당 부서에 연결된 고객 피드백만 집계/노출한다.
- React `AI 실행 피드백` 카드 제목과 본문이 한 줄 말줄임/좁은 영역 때문에 잘리지 않도록 줄바꿈 스타일을 보강한다.
- 일반 `/ai-workspace/`는 기존처럼 사용자/팀 범위의 피드백 히스토리를 유지한다.

**검증 계획**:

- 상세 `department_id` 요청에서 다른 부서 피드백이 제외되는 테스트 추가.
- 긴 답변/판단/다음 액션 문구가 API에서 잘리지 않고 내려오는 테스트 추가.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 추천 질문 프롬프트 절단 수정 계획

**배경**:

- `/ai-workspace/`의 `추천 질문` 카드에서 복사되는 프롬프트의 `최근 영업노트` 내용이 `...`로 잘려 나온다.
- 원인은 `_ai_workspace_recent_note_context()`가 영업노트 본문을 150자, 다음 액션을 80자로 줄여 promptTargets의 `prompt` 자체에 축약문을 넣는 구조다.
- 프론트 카드 제목/컨텍스트 칩도 말줄임 처리와 낮은 preview 높이 때문에 사용자가 prompt가 잘린 것으로 보기 쉽다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- AI workspace prompt context의 최근 영업노트와 다음 액션은 prompt용 표시 정제만 하고 길이 절단을 제거한다.
- 이메일/연락처/HTML 태그 제거는 유지한다.
- `추천 질문` 프론트 카드 제목과 컨텍스트 칩은 줄바꿈되도록 수정한다.
- prompt preview 영역은 더 넓게 보여주되, 과도하게 긴 경우 스크롤 가능한 상태를 유지한다.

**검증 계획**:

- 긴 최근 영업노트가 있는 고객의 promptTargets `prompt`에 끝문장이 포함되고 `...` 축약이 들어가지 않는 테스트 추가.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI/CRM stale 견적 제출 후속조치 정리 계획

**배경**:

- 운영 대시보드의 `Follow-up 지연 후속조치`에 이미 견적서/비교표가 제출된 고객의 과거 `견적서 및 비교표 제출` 후속조치가 계속 남는 케이스가 확인됐다.
- React 대시보드 API와 AI 워크스페이스 액션 큐가 모두 `History.next_action_date`와 `reviewed_at`만 보고 미처리 후속조치를 노출해, 견적 일정/견적서 생성/견적 모델 상태가 이미 제출 완료를 가리켜도 과거 할 일이 남을 수 있다.
- 이전 AI 상황 동기화는 사용자가 AI에게 보고한 이후 고객 상태와 우선순위를 쓰기 동기화하지만, 이번 케이스처럼 기존 데이터의 완료 증거가 이미 있는 경우 읽기 화면에서도 같은 기준으로 stale 액션을 제외해야 한다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- `견적서/비교표 제출/발송/송부/전달`류의 `History.next_action`을 제출형 견적 후속조치로 판정하는 공통 helper를 추가한다.
- 해당 History 이후 같은 고객/담당자의 견적 모델(`Quote.stage != draft/rejected/expired`) 또는 견적서 생성 로그(`DocumentGenerationLog.document_type='quotation'`)가 있으면 stale 완료 증거로 본다.
- React 대시보드 API의 지연 후속조치 목록/카운트/우선 고객 overdue 판정에서 stale 제출 후속조치를 제외한다.
- React 고객 목록/상세 API의 `지연 후속` 카운트와 overdue 액션 목록에서도 같은 stale 제출 후속조치를 제외한다.
- AI 워크스페이스 액션 큐의 `customer_followup` 액션에서도 같은 stale 제출 후속조치를 제외한다.
- 실제 데이터는 GET 요청에서 자동 수정하지 않고, 화면/추천 목록의 노출 기준을 일관화한다.

**검증 계획**:

- 대시보드 API에서 견적서 생성 로그가 있는 과거 `견적서 및 비교표 제출` 후속조치가 `overdueActions`와 metric에서 제외되는 테스트 추가.
- AI 워크스페이스 actionQueue에서 같은 stale History가 `followup:<history_id>` 액션으로 나오지 않는 테스트 추가.
- 일반 `견적 검토 여부 확인`처럼 제출 이후 확인해야 하는 후속조치는 계속 노출되는지 테스트로 보존한다.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.DashboardSummaryApiTests reporting.tests.CustomersSummaryApiTests reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 현장 답변 이슈별 후속조치 분리 계획

**배경**:

- AI 추천 실행 답변에서 “보상판매는 장기, 현재 팁 불만 해결이 급선무”처럼 서로 다른 주제가 한 번에 보고될 수 있다.
- 현재 로직은 고객 긴급도는 `urgent`로 잘 반영하지만, CRM 후속조치는 하나의 `History.next_action`에 긴급 이슈와 장기 이슈를 함께 적는다.
- 운영자가 실제로 실행하려면 “오늘 처리할 긴급 불만”과 “다음 확인일만 잡을 장기 보상판매”가 별도 후속조치로 보여야 한다.

**DB 변경 필요 여부**: 없음.

- 기존 `History` 후속조치를 사용한다.
- 기존 `AIWorkspaceActionFeedback.ai_result.crmSync` JSON에 생성된 이슈별 후속조치 ID를 저장해 같은 답변을 다시 저장해도 중복 생성하지 않는다.

**구현 범위**:

- 불만/클레임/급선무 답변에서 기존처럼 긴급 이슈명과 장기 분리 주제를 추출한다.
- 긴급 이슈는 기존 메인 AI 상황 동기화 후속조치로 저장하되, 메인 `next_action`은 오늘 처리할 긴급 불만 중심으로 유지한다.
- 장기 주제가 함께 있으면 별도 `History`를 생성해 장기 후속조치로 저장하고, 예정일은 장기 확인용으로 여유 있게 지정한다.
- 같은 `action_id`에 다시 답변을 저장하는 경우 기존 장기 후속조치를 갱신하고 중복 생성하지 않는다.
- `crmSync.changes`에 메인 후속조치와 이슈별 장기 후속조치 생성/갱신 내역을 모두 남긴다.

**검증 계획**:

- “보상판매는 장기, 현재 팁 불만 해결이 급선무” 답변 저장 시 메인 후속조치는 `팁` 긴급 대응만 담고, 별도 장기 후속조치가 `보상판매` 내용으로 생성되는 테스트 추가.
- 같은 action에 다시 답변을 저장해도 장기 후속조치가 중복 생성되지 않고 기존 항목이 갱신되는 테스트 추가.
- 기존 AI workspace feedback 테스트 전체 실행.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 추천 실행 메일 답장 대기 중복 제거 계획

**배경**:

- 운영 AI 추천 실행 목록에서 같은 김미선 고객의 `메일 답장 확인` 카드가 3개 표시됐다.
- 원인은 같은 메일 대화의 원문/답장/재답장이 각각 `EmailLog(email_type='sent')`로 저장되어 있고, AI action queue가 이를 모두 독립 `email_waiting` 액션으로 생성하기 때문이다.
- 같은 고객, 같은 메일 thread 또는 같은 답장 제목의 미회신 메일은 운영자 입장에서는 하나의 “회신 여부 확인” 액션이다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- AI workspace `email_waiting` action 생성 단계에서 대화 단위 중복 제거를 추가한다.
- 우선 `gmail_thread_id`/`thread_id`가 있으면 같은 고객 + 같은 thread 기준으로 하나만 표시한다.
- thread id가 없으면 `Re:`, `[RE]`, `FW:` 같은 답장 접두어를 제거한 제목과 수신자 기준으로 하나만 표시한다.
- 같은 대화에서는 최신 발송 메일만 action으로 남기고 이전 발송 로그는 추천 목록에서 제외한다.
- 기존 수신 회신 존재 여부 검사는 유지한다.

**검증 계획**:

- 같은 고객/같은 thread에 원문, `Re:`, `[RE]` 발송 로그가 3개 있어도 `email_waiting` action은 1개만 내려오는 테스트 추가.
- 서로 다른 thread 또는 다른 수신자는 기존처럼 별도 action으로 남는지 기존 테스트를 유지한다.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_action_queue_dedupes_email_waiting_by_thread --verbosity=2`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-14 AI 추천 실행 메일 답장 대기 제목 중복 제거 보강 계획

**배경**:

- 1차 중복 제거 후에도 김미선 고객의 `메일 답장 확인` 카드가 2개 남았다.
- 남은 중복은 원문 제목과 `Re: [RE]...` 답장 제목이 같은 견적 안내임에도 서로 다른 Gmail thread id로 저장된 케이스다.
- 기존 구현은 thread id가 있으면 thread 기준으로만 우선 판단하고, 제목/수신자 기준은 thread id 없는 보조 케이스처럼 동작해 운영 화면의 실제 중복을 완전히 제거하지 못했다.

**DB 변경 필요 여부**: 없음.

**구현 범위**:

- `email_waiting` 중복 키를 단일 키가 아니라 복수 키 목록으로 만든다.
- 각 발송 메일에 대해 thread 키와 `정규화 제목 + 수신자 + 고객` 키를 모두 등록한다.
- 최신 발송 메일을 먼저 처리하므로, 같은 견적 안내 묶음에서는 최신 1건만 action으로 남긴다.
- 같은 고객의 별도 제목/별도 주제 메일은 기존처럼 별도 action으로 유지한다.

**검증 계획**:

- 원문과 `Re: [RE]...` 발송 로그가 서로 다른 Gmail thread id를 가져도 `email_waiting` action은 1개만 내려오는 테스트로 보강한다.
- 별도 납품 일정 확인 메일은 같은 고객이라도 별도 action으로 유지되는지 확인한다.
- `python -m py_compile reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_action_queue_dedupes_email_waiting_by_thread_or_subject --verbosity=2`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-15 AI 워크스페이스 부서 실행 요약 계획

**배경**:

- 최근 AI Workspace 작업으로 `/ai-workspace/?department_id=<id>` 상세 화면의 `AI 추천 실행 목록`은 해당 부서 기준으로 필터링된다.
- 다만 운영자가 부서 상세로 들어갔을 때 카드 목록을 훑기 전까지 이 부서에 긴급/메일대기/견적후속/고객후속이 몇 건인지, 금액 영향이 있는지 한눈에 보기 어렵다.

**DB 변경 필요 여부**: 없음.

- 기존 `/reporting/api/ai-workspace/`의 `actionQueue`, `feedbackHistory.scope`, `week`, `featuredDepartment` payload만 사용한다.
- 새 모델, migration, 외부 연동은 추가하지 않는다.

**구현 범위**:

- React AI Workspace에 부서 상세 범위에서만 표시되는 `부서 실행 요약` 패널을 추가한다.
- 현재 부서 `actionQueue`를 기준으로 전체 액션 수, 긴급 액션 수, 이번 주 기한 액션 수, 예상 금액 영향 합계를 계산해 표시한다.
- 액션 유형별 건수/비중과 우선 처리 액션 상위 3개를 함께 보여준다.
- action이 없으면 부서 범위에 처리할 추천 실행 항목이 없다는 빈 상태를 표시한다.
- 기존 `AI 추천 실행 목록`, 답변 저장, 초안 생성, 부서 검색, `/reporting/*` fallback, 인증/권한 정책은 유지한다.

**검증 계획**:

- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

## 2026-05-15 AI 워크스페이스 부서 질문 답변 계획

**배경**:

- 운영자가 `/ai-workspace/?department_id=<id>`처럼 특정 부서 상세 화면에 들어갔을 때 “해당 연구실에서 우리에게 마지막으로 주문한 날짜가 언제지?” 같은 즉석 질문을 하고 싶다.
- 현재 화면에는 부서 실행 요약과 AI 분석/프롬프트는 있지만, 선택 부서의 CRM 데이터에 대해 자연어 질문을 바로 던지는 입력 흐름은 없다.

**DB 변경 필요 여부**: 없음.

- 기존 `FollowUp`, `History`, `Schedule`, `Quote`, `DeliveryItem` 데이터만 읽는다.
- 질문/응답은 영구 저장하지 않고 즉시 응답 payload로만 반환한다.
- 새 모델, migration, 파일 저장은 추가하지 않는다.

**구현 범위**:

- `/reporting/api/ai-workspace/department-question/` POST API를 추가한다.
- 기존 AI workspace와 동일하게 로그인, CSRF, `UserProfile.can_use_ai` 권한을 요구한다.
- `departmentId`는 현재 로그인 사용자가 담당 중인 `FollowUp.department` 범위에 있을 때만 접근 가능하게 한다.
- 부서별 고객, 최근 영업노트, 일정, 견적/납품 요약을 제한된 컨텍스트로 수집한다.
- OpenAI 사용이 가능하면 수집한 CRM 컨텍스트만 근거로 답변하고, 사용 불가/실패 시 deterministic fallback으로 마지막 납품/주문일 같은 핵심 질문에 답한다.
- React `/ai-workspace/?department_id=<id>` 화면에 부서 질문 입력 패널과 답변/evidence 표시를 추가한다.
- 기존 `/reporting/*` 라우트, AI 추천 실행 목록, 답변 저장, 초안 생성, 부서 분석 실행은 변경하지 않는다.

**검증 계획**:

- 접근 가능한 부서에 “마지막 주문 날짜” 질문 시 최신 납품 일정/활동 날짜가 응답되는 테스트 추가.
- AI 권한 없는 사용자는 403, 담당하지 않는 부서는 404로 차단되는 테스트 추가.
- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`

## 2026-05-15 납품 품목 선결제 저장/할인단가 0 수정 계획

**배경**:

- `/schedules/903/`에서 견적 품목을 불러오면 할인단가가 사용자가 입력하지 않은 `0`으로 표시된다.
- 같은 화면에서 선결제 차감과 함께 납품 품목 저장 시 `납품 품목 저장 중 오류가 발생했습니다.`가 표시된다.
- 운영 로그 확인 결과 저장 실패의 직접 원인은 PostgreSQL에서 `FOR UPDATE`와 `DISTINCT`를 함께 쓴 쿼리(`FOR UPDATE is not allowed with DISTINCT clause`)다.
- 할인단가 0은 과거/레거시 데이터의 `discount_unit_price=0, discount_rate=0` 조합이 “할인 없음”이 아니라 “0원 할인단가”로 해석되는 문제다.

**DB 변경 필요 여부**: 없음.

- 기존 `DeliveryItem.discount_unit_price` 값을 마이그레이션하지 않고, 읽기/저장/계산 단계에서 `할인율 0 + 할인단가 0 + 기준단가 있음`은 할인 없음으로 정규화한다.

**구현 범위**:

- React 납품 품목 저장 API에서 기존 원본 견적 일정 ID 수집 시 `select_for_update().distinct()` 조합을 제거하고 Python에서 중복 제거한다.
- `DeliveryItem` 계산/저장 로직에서 할인율 없는 0원 할인단가를 빈 할인단가로 취급한다.
- 견적 품목 불러오기 API와 일정 상세 API의 payload도 같은 기준으로 `discountUnitPrice: null`, 정상 기준단가/총액을 내려준다.
- React 견적 품목 정규화와 import row 생성에서도 방어적으로 같은 값을 할인 없음으로 처리한다.
- 선결제 차감 저장 시 납품 품목 합계보다 큰 선결제 차감액은 서버에서도 차단한다.

**검증 계획**:

- 견적 품목 API가 레거시 `discount_unit_price=0`을 빈 할인단가로 반환하는 테스트 추가.
- 납품 품목 저장 API가 `discountUnitPrice: "0"` 입력을 빈 할인단가로 저장하고 정상 총액을 계산하는 테스트 추가.
- PostgreSQL 오류 원인이 된 `DISTINCT` 원본 견적 ID 잠금 쿼리가 사라졌는지 쿼리 캡처 테스트 추가.
- `python -m py_compile reporting\models.py reporting\views.py reporting\tests.py`
- `python manage.py test reporting.tests.QuoteItemsApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`
## 2026-05-16 Schedule-linked notes and AI workspace answer upgrade plan

**Background**:

- User requested that `/schedules/907/` and other React schedule detail pages allow writing a sales note directly from the schedule.
- Sales note editing currently exposes structured meeting fields (`오늘 상황`, `연구원 발언`, `확인한 사실`, `장애물/반대`, `미팅 다음 액션`) that should be removed from the user-facing React format. The remaining note format should be `활동 내용` and `다음 액션`.
- AI Workspace department Q&A is currently too terse, department-only, and does not include the recent field-feedback records that can supersede older schedule/note context.
- User also requested whole-department/global AI questions such as finding departments that need next action.

**DB change required**: No.

- Reuse existing `History.schedule`, `History.content`, `History.next_action`, `History.next_action_date`, `Schedule`, `FollowUp`, and `AIWorkspaceActionFeedback`.
- Keep legacy structured meeting fields in the model for backwards compatibility and legacy Django screens, but stop exposing them as separate React editing fields.

**Implementation scope**:

- Backend notes API:
  - Allow `notes_create_api` to accept an optional `scheduleId`.
  - Validate that the schedule belongs to the current user and matches the selected followup before linking the created `History`.
  - Keep managers read-only and preserve current customer ownership checks.
  - Require `content` for all React note edits, including customer meetings.
  - On React note update, clear legacy structured meeting fields so edited notes use the simplified format.
  - Use legacy structured field text only as a read/display fallback for old notes whose `content` is empty.
- Backend schedules API:
  - Point schedule note creation links to React note creation with `customer` and `schedule` query parameters while keeping Django schedule/detail routes intact.
- React notes UI:
  - Remove structured meeting fields from the note edit form and note detail display.
  - Keep `활동 내용`, `다음 액션`, and next action date as the visible note format.
  - Carry optional `scheduleId` through quick note creation when opened from a schedule link.
- React schedule detail UI:
  - Add an inline schedule-fixed `영업노트 작성` panel.
  - Prefill activity type and activity date from the schedule.
  - Submit through the React note create API and link the created note back to the schedule.
- AI Workspace:
  - Add all-department/global question support when no department is selected.
  - Include recent `AIWorkspaceActionFeedback` in question context so newer “done/resolved/gave sample” feedback can override older action suggestions.
  - Make answers longer and operational: direct judgment, why, next step, timing, and evidence.
  - Use OpenAI Responses API web search when the user explicitly asks for latest/current/external information, with a fallback to the existing Chat Completions path and deterministic fallback.
  - Avoid sending internal CRM details as web-search query instructions; CRM context remains the answer basis.

**Validation plan**:

- Add/update focused tests for:
  - Creating a React note linked to a schedule.
  - Blocking schedule-linked note creation when the schedule does not belong to the current user or does not match the selected followup.
  - React note update clearing structured meeting fields while preserving simplified content/next action.
  - AI question API accepting all-department scope.
  - AI question context using recent AI feedback to avoid stale sample/action duplication.
- Run:
  - `python -m py_compile reporting\views.py reporting\tests.py`
  - `python manage.py test reporting.tests.NotesSummaryApiTests reporting.tests.SchedulesSummaryApiTests reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
  - `python manage.py check`
  - `python manage.py makemigrations --check --dry-run`
  - `cd frontend && npx tsc --noEmit --pretty false`
  - `cd frontend && npm run build`
  - `cd frontend && node --check server.mjs`
  - `git diff --check`

## 2026-05-17 AI Workspace CRM strategy prompt and answer direction plan

**Background**:

- The previous AI Workspace deployment was manually verified in production.
- The user provided a default CRM strategy architect prompt that should guide department Q&A answers.
- The `현재 답변 방향` UI currently stores only the user's free-form direction and is blank when no direction has been saved.
- The desired behavior is that the current answer direction is always stated briefly: default direction when no user preference exists, and a modified/current direction when the user saves a preference.

**DB change required**: No.

- Reuse `AIWorkspaceAnswerDirection.direction` for the user's saved direction text.
- Add computed API fields only, such as an effective/current direction label, without migrations.

**Implementation scope**:

- Backend AI Workspace question generation:
  - Add the provided CRM strategy architect prompt as the default role/process/style guidance for department Q&A.
  - Preserve the existing JSON-only response contract so React parsing and history snapshots remain stable.
  - Keep existing CRM-data-only safety rules and permission boundaries.
- Answer direction API payload:
  - Return a default `effectiveDirection` when no saved direction exists.
  - Return an `effectiveDirection` that explicitly incorporates the saved user direction when one exists.
  - Include this effective direction in the prompt context so the model sees the exact current direction.
- React AI Workspace:
  - Display the effective/current answer direction as a short read-only statement above the editable direction textarea.
  - Keep the textarea for the user's desired adjustment, not as the only source of the current direction.
  - After saving, refresh and show the updated effective direction.

**Validation plan**:

- Add/update focused tests for:
  - Default answer direction payload includes a non-empty effective direction.
  - Saved direction payload includes both the raw saved direction and the computed current direction.
  - OpenAI department Q&A system prompt includes the CRM strategy architect guidance while preserving JSON output.
- Run:
  - `python -m py_compile reporting\views.py reporting\tests.py`
  - `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
  - `python manage.py check`
  - `python manage.py makemigrations --check --dry-run`
  - `cd frontend && npx tsc --noEmit --pretty false`
  - `cd frontend && npm run build`
  - `cd frontend && node --check server.mjs`
  - `git diff --check`

## 2026-05-17 AI Workspace fixed system prompt and direction removal plan

**Background**:

- User clarified that the CRM strategy architect prompt must be fixed exactly as the system prompt.
- The answer-direction free-form control makes the workflow harder to use and should be removed.

**DB change required**: No.

- Do not delete existing `AIWorkspaceAnswerDirection` table/migration in this runtime task.
- Stop using answer-direction data in the API context and React UI.

**Implementation scope**:

- Backend:
  - Replace the AI Workspace department Q&A system prompt with the user-provided fixed prompt text.
  - Keep JSON response parsing stable by moving the app's JSON response contract into the user payload rules instead of modifying the system prompt.
  - Remove `answerDirection` from department/global question context, summary payload, question response context, and prompt rules.
  - Remove the answer-direction API route/view from active runtime routes.
- Frontend:
  - Remove the `현재 답변 방향` UI section, state, save handler, API client, and related CSS.
  - Keep department selection, model selection, question execution, question history, and pagination.
- Tests:
  - Update prompt tests to assert the fixed system prompt and absence of answer-direction context.
  - Remove answer-direction API/UI payload expectations.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- Local Playwright smoke for `/ai-workspace/`
- `git diff --check`

## 2026-05-17 AI Workspace question history detail plan

**Background**:

- User manually confirmed the fixed prompt and answer-direction removal deployment.
- Next queued task: clicking a question/answer history item should open a detail page that shows the full chat in `질문` / `답변` format, not only the list summary.

**DB change required**: No.

- Reuse `AIWorkspaceQuestionLog.question` and `AIWorkspaceQuestionLog.answer_snapshot`.
- Improve new question-log snapshots to preserve richer answer fields in the existing JSON column.

**Implementation scope**:

- Backend:
  - Add an owner-scoped AI Workspace question-log detail API.
  - Return the selected log with full answer snapshot and an AI Workspace back link.
  - Keep permission checks aligned with existing AI Workspace APIs.
- Frontend:
  - Add `/ai-workspace/questions/<id>/` React detail route.
  - Make history list items clickable links to the detail route.
  - Render exactly two main sections: `질문` and `답변`.
- Tests:
  - Add API tests for owner access, full answer payload, and cross-user blocking.

**Validation plan**:

- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npx tsc --noEmit --pretty false`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- Local Playwright smoke for history click/detail route
- `git diff --check`
