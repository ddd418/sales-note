# Sales Note 쓰기 프록시 (Write MCP) 설계 문서

작성일: 2026-07-10
상태: **설계 단계 (구현/배포 전)**
결정된 방향: **전면 쓰기 프록시** — 단, 인증/권한은 절대 약화하지 않고, 고위험 액션은 확인·감사·레이트리밋으로 게이팅한다.
저장소: `D:\projects\sales-note`

> 이 문서는 코드 변경이 아니라 설계다. 아직 어떤 런타임도 바뀌지 않았고 배포하지 않았다.
> 근거는 2026-07-10 실행한 `write-surface-inventory` 인벤토리(뷰 190여 개 + 인증 모델 + 업무규칙 + 보안 gaps)다.

---

## 0. 한 줄 요약

Claude Code(및 클로드)가 Sales Note CRM을 **읽고 쓸 수 있게** 하려면 두 가지를 새로 만들어야 한다.

1. **백엔드 쓰기 인증 경로** (이 저장소) — 기존 `readonly_api.py`(GET 전용 bearer)의 **쓰기 버전**. 단, 실제 비-특권 유저로 행위하고, CSRF/역할/scope 검사를 전부 유지한다.
2. **호스티드 쓰기 MCP 커넥터** (이 저장소 밖) — 현재 `salesnote-readonly` 커넥터의 쓰기 대응물. 고위험 액션에 대해 **미리보기 → 확인** 2단계 프로토콜을 얹는다.

지금 제공되는 것은 `salesnote-readonly`(읽기 전용) 하나뿐이다. 쓰기는 아무것도 없다.

---

## 1. 배경: 지금 어떻게 되어 있나

### 1.1 현재 있는 것 — 읽기 전용 MCP

- 커넥터 이름: **`salesnote-readonly`** (claude.ai 호스티드 원격 커넥터, 도구 정의는 **이 저장소에 없음**).
- 노출 도구: `salesnote_get_dashboard`, `salesnote_get_customers_summary`, `salesnote_get_followups`, `salesnote_get_pipeline`, `salesnote_get_reports`, `salesnote_list_endpoints`, `salesnote_read_endpoint`.
- 호출 대상: `https://sales-note-frontend-production.up.railway.app/reporting/api/` (프론트가 Django `web` 서비스로 프록시).
- 인증: `Authorization: Bearer <SALES_NOTE_READONLY_TOKEN>` (Railway 환경변수).
- 강제 지점: [reporting/readonly_api.py:49](reporting/readonly_api.py:49) `authenticate_readonly_bearer()`
  - (a) `request.method != "GET"` 이면 즉시 거부 → **쓰기 불가**
  - (b) `resolver_match.url_name` 이 `READONLY_ALLOWED_URL_NAMES`(33개 GET) 안에 있어야 함
  - (c) `secrets.compare_digest` 상수시간 비교
- 유저 매핑: [reporting/readonly_api.py:81](reporting/readonly_api.py:81) `get_readonly_api_user()` → env → **없으면 첫 admin/superuser로 폴백**.

### 1.2 쓰기가 지금 안 되는 이유 (구조적)

- 모든 쓰기 뷰(약 190개)는 **POST**이고, **Django 세션 쿠키 + CSRF 토큰**을 요구한다.
- 인증 백엔드는 커스텀 `OptimizedAuthBackend` (세션 기반), DRF 없음.
- 권한은 **역할(role)** 로 구동: `UserProfile.role ∈ {admin, manager, salesman}`.
  - 핵심 쓰기 게이트: [reporting/views.py:355](reporting/views.py:355) `can_modify_user_data(actor, target)` → admin=전부, **manager=읽기전용(거부)**, salesman=본인 데이터만.
  - 데이터 범위: `_dashboard_scope_users` / `get_accessible_users` ([reporting/views.py:416](reporting/views.py:416))로 만든 `scope_users` QuerySet으로 모든 쿼리를 제한.
  - `CompanyFilterMiddleware` ([reporting/middleware.py](reporting/middleware.py))가 `request.is_admin`, `admin_filter_*`, `user_company`를 세팅.
- readonly bearer는 GET 전용이라 이 경로에 **절대 닿을 수 없다** → 지금 상태는 안전.

### 1.3 쓰기 표면 규모 (인벤토리 결과)

| 위치 | 뷰 수 | 성격 |
|---|---|---|
| `reporting/views.py` | ~95 | schedules, notes/histories, customers/departments/companies, products, employees, profile 등 |
| `reporting/api/*.py` | 15 | prepayments(5) + receivables(1) + demos(3) + data-quality(2) + 레거시 prepayment HTML(4) |
| 보조 모듈 | ~80 | funnel(파이프라인), personal_schedules, gmail/imap(메일), business_cards, todos |
| **합계** | **~190** | 라우팅 기준 `reporting/urls.py`에 150+ POST 라우트 |

- **동사는 전부 POST.** create/update/**delete** 모두 POST (`@require_POST` / `@require_http_methods(["POST"])`). PATCH/DELETE HTTP 동사는 안 씀.
- CSRF: CRM 경로에 `@csrf_exempt` **없음** (유일한 예외는 `backup_api.py` — 아래 위험 항목 참조).

---

## 2. 설계 원칙 (타협 불가)

1. **인증/권한 절대 약화 금지.** 쓰기 토큰은 실제 유저처럼 `can_modify_user_data`, `scope_users`, per-object 검사, CSRF를 **그대로** 통과해야 한다. 우회(bypass) 추가 금지.
2. **readonly의 admin 폴백을 재사용하지 않는다.** 쓰기 토큰이 admin/superuser로 매핑되면 모든 scope 검사가 무력화된다. 쓰기 유저는 **명시적·실재·비-staff·비-admin**이어야 한다.
3. **화이트리스트 + POST 전용.** 쓰기 가능한 `url_name`은 명시적 allowlist로만. 와일드카드 금지.
4. **세션 사용자의 CSRF는 계속 강제.** CSRF 우회는 오직 "유효한 쓰기 토큰으로 인증된 요청"에만 적용한다. 뷰에 `@csrf_exempt`를 붙이면 브라우저 세션 호출자까지 무방비가 되므로 **절대 금지**.
5. **고위험은 자동 실행 금지.** 삭제(캐스케이드), 메일 발송, 선결제/금액 변경, 계정/권한 변경은 자동 경로에서 제외하거나 human-in-the-loop 확인 뒤에만.
6. **모든 토큰 쓰기는 감사 로그.** 최소 `acting_user_id + url_name`, 금융/고객 변경은 before/after diff.

---

## 3. 백엔드 쓰기 인증 설계

### 3.1 핵심 난점 — CSRF 미들웨어 순서

`CsrfViewMiddleware.process_view`는 **뷰 실행 전**에 돈다. 그래서 readonly처럼 "뷰 안에서 `request.user`를 세팅"하는 방식은 POST의 CSRF를 통과하지 못한다. → 쓰기 인증은 **미들웨어**에서 처리하고, 유효한 쓰기 토큰일 때만 `request._dont_enforce_csrf_checks = True`를 세팅한다(DRF가 쓰는 검증된 방식). 세션/쿠키 요청은 이 플래그를 절대 건드리지 않아 CSRF가 그대로 유지된다.

### 3.2 구성 요소

**환경변수 (Railway):**
- `SALES_NOTE_WRITE_TOKEN` — 시크릿 (readonly 토큰과 별개).
- `SALES_NOTE_WRITE_USER_ID` — **반드시 실재·활성·비-staff 유저**로 resolve. readonly의 admin 폴백([readonly_api.py:95](reporting/readonly_api.py:95)) **복사 금지**.
- (선택) 토큰별 유저 매핑 — "salesman 토큰", "manager 토큰"을 나눠 각 토큰이 딱 그 유저의 역할/scope를 상속하도록.

**새 모듈 `reporting/write_api.py` (readonly_api.py를 구조적으로 미러링):**
- `WRITE_ALLOWED_URL_NAMES` — 쓰기 허용 `url_name`의 **작은** 집합 (POST 전용, 5절 정책 반영).
- `authenticate_write_bearer(request)`:
  1. 메서드 게이트 — POST만 (PATCH/DELETE 라우트가 실제로 생기기 전엔 POST만).
  2. `resolver_match.url_name ∈ WRITE_ALLOWED_URL_NAMES`.
  3. `Authorization: Bearer` 파싱 + `secrets.compare_digest`.
  4. 성공 시 `request.user = acting_user` (비-staff 실유저), `request.salesnote_write_api = True`.

**새 미들웨어 `WriteBearerMiddleware`:**
- `AuthenticationMiddleware` **다음** (진짜 세션 유저를 덮어쓰지 않도록 — bearer가 검증됐을 때만 교체).
- `reporting.middleware.CompanyFilterMiddleware` **앞** (`request.is_admin`/`admin_filter_*`/`user_company`가 acting 유저 기준으로 계산되도록).
- 검증 성공 시에만 `request._dont_enforce_csrf_checks = True`.

**심층 방어 데코레이터 `write_bearer_or_login_required`:**
- opt-in한 각 POST 뷰에 부착. `request.salesnote_write_api`가 참이면 `url_name`을 allowlist와 재대조. 미들웨어 설정이 흘러도 표면이 조용히 넓어지지 않게.

### 3.3 왜 이러면 안전한가

`request.user`가 **실재·정확한 역할의 유저**이므로, 기존 뷰의 `_api_login_required_response`, `can_modify_user_data`, `_can_manage_department_account`, `scope_users`, `_demo_resolve_mutation_payload` 재검증이 **브라우저 세션과 동일하게** 발동한다. manager 토큰은 읽기전용, salesman 토큰은 본인 레코드만. 어떤 검사도 새로 우회하지 않는다.

---

## 4. 노출 정책 — "전면"을 안전하게 계층화

전면 프록시라도 모든 것을 **자동 실행**시키지 않는다. 3계층으로 나눈다.

### Tier A — 자동 허용 (저위험, 되돌리기 쉬움)
- 노트/활동 생성·수정: `notes_create_api`, `notes_update_api`, `schedule_add_memo_api`, `history_update_memo`
- 일정 생성·수정·상태(취소 제외)·이동: `schedules_create_api`, `schedules_update_api`, `schedule_move_api`
- 고객/연락처 생성·수정(삭제 제외): `followup_create_ajax`, `customer_update_api`, `account_contact_save_api`
- 자산/서비스/교정 기록: `customer_asset_save_api`, `customer_service_case_save_api`, `customer_calibration_save_api`
- 태스크/할일: `tasks_*` (React 변형, same-company 제한 있는 것만)
- 파이프라인 수동 이동: `funnel_pipeline_move` (단, department fan-out + `pipeline_manually_set=True` 유지 — 6절)
- 데모/대여 기록, 명함, 개인 일정, 펀넬 타깃

### Tier B — 확인·감사 필수 (고위험, 금액/파괴/대량)
- **선결제/금액**: `prepayment_create/update/cancel/delete/transfer_api`, `receivable_item_status_api`
- **납품 품목 교체(replace-all)**: `schedules_delivery_items_update_api` ([views.py:13232](reporting/views.py:13232) — 최대 blast radius)
- **일정 취소**: `schedule_status_update_api`의 `cancelled` (납품 History 삭제 + won 강등 위험 — 6절)
- **제품 대량**: `products_bulk_upsert_api`, `products_bulk_delete_api`, `products_excel_import_api`, `product_replace_reference_api`
- **계정 구조 변경**: `account_update_api`, `department_update_api`(회사 이동 캐스케이드), `data_quality_contact_assign_account_api`

→ MCP 커넥터 레벨에서 **미리보기(dry-run) → 사용자 확인 → 실행** 2단계로만 노출.

### Tier C — 자동 경로에서 제외 (기본값: 아예 안 열기)
- **외부 메일 발송 전부**: `mailbox_api_send/reply/send_scheduled_now`, `send_email_from_schedule/mailbox`, `reply_email`, `send_email_imap` — 되돌릴 수 없고 외부로 나감, 견적/납품 PDF 자동첨부(정보 유출 벡터).
- **유저/권한 변경 전부**: `employees_*`, `user_*`, `manager_user_*`, 특히 `api_change_company_creator`(회사 소유자=가시성 범위 재지정).
- **하드 캐스케이드 삭제**: `customer_delete_api`(블로커 검사 없음), `schedule_delete_view`, `company/department_delete_*`, `user_delete`, `mailbox_api_delete`/`delete_email`.
- **Django admin(`/admin/`)**, **`backup_api`**, **관리 커맨드/cron** — 프록시 범위 밖 (7절).

> "전면"의 의미: 제외되지 않은 모든 쓰기 `url_name`이 도달 가능. 단 Tier B는 확인 게이트, Tier C는 기본 비활성(사용자가 명시적으로 켜야 함).

---

## 5. 업무규칙 가드 (쓰기가 깨면 안 되는 불변식)

인벤토리에서 확정된, DB 제약이 아니라 **뷰 코드에만** 존재하는 불변식들. 프록시가 raw PK로 우회 쓰기하면 깨진다.

1. **계정(Department) 기준 그룹핑** — FollowUp/Schedule/Prepayment 생성·이동 시 `department_id`가 null이거나 틀리면 한 연구실이 orphan 카드로 쪼개짐. `FollowUp.department` 재지정은 그 연락처의 납품/견적/선결제 이력 전체를 다른 계정으로 옮김.
2. **선결제는 구조화 필드로만** — `Schedule.notes`에 "선결제"를 써도 안 잡힘. `use_prepayment`/`prepayment_amount`만 세팅하고 `PrepaymentUsage` 없이 두면 돈은 안 움직였는데 매출/외상이 오분류됨.
3. **PrepaymentUsage / balance 무결성** — `balance >= 0` **DB 제약 없음**. row lock 없이, 짝이 되는 `PrepaymentLedgerEntry` 없이, 또는 restore 없이 재적용하면 **이중 차감/음수 잔액/미정산**.
4. **선결제 cross-tenant 금지** — 다른 계정/회사/유저의 선결제를 차감하거나 견적/미팅 일정에 붙이면 돈이 테넌트 경계를 넘음.
5. **일정→파이프라인 단방향** — 파이프라인 이동을 연결된 Schedule(날짜/상태/매출)로 역미러링하면 source of truth 오염 + 피드백 루프.
6. **`won` 보호 — ⚠️ 기존 버그 있음** — Kanban은 won/lost를 보호하지만, `signals.update_opportunity_on_schedule_change`는 견적 일정 취소 시 `current_stage=='won'` 검사 **없이** `quote_lost`로 강등한다. 프록시가 견적 일정을 취소하면 성사 기록이 파괴될 수 있음. **노출 전에 이 시그널 가드를 먼저 고쳐야 함.**
7. **DeliveryItem/Quote 합계 재계산** — `total_price`를 직접 쓰거나 `bulk_update`/`queryset.update()`를 쓰면 `save()`를 우회해 매출·선결제 상한 계산이 desync.
8. **cancelled 제외** — 취소 납품을 completed로 되돌리면 매출이 조용히 다시 더해짐. 삭제 대신 취소로만.

**노출 전 먼저 고쳐야 하는 기존 권한 구멍 (프록시가 버그를 기계 규모로 증폭):**
- `department_memo_api` ([views.py:36052](reporting/views.py:36052)) — `@login_required`만, **아무 인증 유저나 아무 부서 메모 덮어쓰기 가능**.
- `personal_schedule_add_comment` ([personal_schedule_views.py:430](reporting/personal_schedule_views.py:430)) — 소유권/가시성 검사 **없음**.
- `department_assign_category` — 부서에 연락처가 0명이면 검사 없음.
- 레거시 `todo_request_to_peer`/`todo_delegate` — same-company 제한 없음(React 변형은 있음).

---

## 6. 인벤토리에 안 잡히는 위험 표면 (반드시 프록시 밖)

1. **Django admin (`reporting/admin.py`)** — 가장 큰 미인벤토리 쓰기 표면. Prepayment/DeliveryItem/User/UserProfile 등 ~30개 모델 풀 CRUD + 기본 대량삭제. 뷰 레이어 가드가 **하나도** 안 걸림. `is_staff` 세션이면 도달. → **쓰기 유저는 반드시 `is_staff=False`**, `/admin/`은 프록시 범위 밖.
2. **`reporting/backup_api.py`** — `@csrf_exempt` + 별도 `BACKUP_API_TOKEN` + **비-상수시간 비교**([backup_api.py:32](reporting/backup_api.py:32)). DB 덤프를 메일로 보냄(유출급). 프록시 밖이지만 토큰 모델이 다름을 문서화.
3. **관리 커맨드/cron** — `process_scheduled_emails`(실제 고객 메일 발송), `sync_schedule_pipeline`(대량 스테이지 쓰기), `simple_backup`(DB 덤프+메일). → 프록시가 `ScheduledEmail`을 만들면 **나중에 cron이 발송**한다. 실행 시점엔 재확인 없음.
4. **write-on-GET 엔드포인트** — `mailbox_api_thread`(읽음 처리), `mailbox_thread`(GET에서 EmailLog 생성+Gmail 호출), `imap_disconnect`/`sync_imap_emails`(GET에서 뮤테이션). readonly 토큰의 "GET=안전" 가정은 **allowlist 한 줄이면 깨짐**. → 규칙: **write-on-GET url_name은 절대 readonly allowlist에 넣지 않는다** (테스트로 강제).
5. **외부 효과 compute 엔드포인트** — AI/LLM 호출(`ai_workspace_department_question_api`는 CRM 내용으로 웹검색까지), 메일 발송. 되돌릴 수 없는 외부 side effect + 비용. 레이트/코스트 리밋 필요.

---

## 7. MCP 커넥터 쪽 (이 저장소 밖)

- 현 `salesnote-readonly`는 **호스티드 claude.ai 커넥터** (도구 정의 repo에 없음). 쓰기도 대응하는 커넥터가 필요.
- 형태 후보:
  - (A) `salesnote-readonly`를 확장해 `salesnote_write_endpoint(url_name, payload)` 추가.
  - (B) 별도 `salesnote-write` 커넥터 — 권장. 읽기/쓰기 자격을 분리, 쓰기 토큰을 격리.
- **2단계 프로토콜**: Tier B 액션은 `preview`(서버가 before/after diff 반환) → 사용자 확인 → `commit`. 근저 Django 뷰엔 dry-run이 없으므로 커넥터/얇은 preview 엔드포인트가 합성해야 함.
- **idempotency 키** — 모든 쓰기가 POST이고 자연 유니크 제약이 적음. `quick_add_customer` 등은 재시도 시 Company/Department **중복 생성**. 커넥터가 idempotency-key 또는 per-action dedup을 소유.

---

## 8. 데이터 안전 장치

- **감사 로그**: 토큰 쓰기마다 `acting_user_id + url_name + timestamp`. Tier B(금융/고객)는 before/after diff 필수. 저장 위치·열람 권한 결정 필요.
- **레이트/동시성 리밋**: 토큰별. 메일/AI/대량 op에 특히.
- **dry-run/미리보기**: Tier B 필수.
- **deferred side effect**: `ScheduledEmail` 생성을 프록시에 허용할지 자체가 결정 사항(발송이 인증 경계 밖에서 일어남).

---

## 9. 사용자 결정 필요 (Open Questions)

1. **토큰→유저 매핑**: 공용 머신 유저 1개 vs 토큰별 실유저(역할/scope 상속) — 후자 권장. 매핑 유저가 `is_staff=False`·비-admin임을 무엇으로 보장?
2. **"전면"의 경계**: Django admin / backup / 메일발송 / 유저·권한 / `api_change_company_creator` — in/out? (권장: 전부 out)
3. **확인 정책**: ~30개 `risk:high` 중 어느 것을 human-in-the-loop로?
4. **기존 권한 구멍**(5절 하단): 노출 전 수정 vs allowlist에서 제외?
5. **idempotency**: 프록시 소유 vs 호출자 책임?
6. **감사 granularity**: url_name+user만 vs before/after diff?
7. **레이트/코스트 리밋** 수치?
8. **deferred 발송**(`ScheduledEmail`) 허용 여부?
9. **CSRF-bypass blast radius**: `_dont_enforce_csrf_checks`가 토큰 검증된 요청에만 걸리는지 보장하는 테스트?

---

## 10. 구현 로드맵 (배포 전 순서 제안)

- **Phase 0 — 사전 수정 (노출과 무관하게 옳은 일):**
  - `won→quote_lost` 시그널 가드 추가.
  - `department_memo_api` / `personal_schedule_add_comment` / `department_assign_category` / 레거시 todo 위임 권한 검사 보강.
  - write-on-GET url_name이 readonly allowlist에 없음을 검증하는 회귀 테스트.
- **Phase 1 — 쓰기 인증 기반:**
  - `reporting/write_api.py` + `WriteBearerMiddleware` + 데코레이터, `SALES_NOTE_WRITE_TOKEN`/`SALES_NOTE_WRITE_USER_ID`(비-staff).
  - 미들웨어 순서·CSRF 플래그 테스트, "세션 요청엔 절대 플래그 안 걸림" 테스트.
- **Phase 2 — Tier A allowlist 노출** (저위험 create/update), 감사 로그.
- **Phase 3 — Tier B 확인·감사·dry-run·레이트리밋.**
- **Phase 4 — MCP 쓰기 커넥터** 배선(호스티드), 스모크, 운영 수동 확인.

각 Phase는 인수인계서 배포 절차(§8: plan → 코드 → 테스트 → check/build → report → 커밋 → Railway 확인 → smoke → 수동 확인)를 따른다.

---

## 11. 리스크 요약

| 리스크 | 원인 | 완화 |
|---|---|---|
| 권한 붕괴 | 쓰기 토큰이 admin으로 매핑 | 비-staff·비-admin 실유저, readonly 폴백 미복사 |
| CSRF 우회 확대 | 뷰 `@csrf_exempt` | 미들웨어에서 토큰 검증 요청에만 플래그 |
| 표면 확대 | allowlist 드리프트 | 미들웨어 + per-view 데코레이터 이중 대조, POST 전용 |
| 금액 손상 | balance/usage 직접 쓰기 | Tier B 확인+감사, 기존 뷰 경유(락/원장 유지) |
| 성사 기록 파괴 | won→lost 시그널 버그 | Phase 0에서 가드 수정 |
| 외부 유출/비용 | 메일·AI 자동 호출 | Tier C 제외, 레이트/코스트 리밋 |
| 중복 생성 | idempotency 부재 | 커넥터 idempotency 키 |
| 미인벤토리 표면 | admin/backup/cron/write-on-GET | 프록시 범위 밖 + 문서화 + 테스트 |
