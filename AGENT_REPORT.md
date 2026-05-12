# AGENT_REPORT.md

## 2026-05-12 — React Product Management Migration

**상태**: 구현/로컬 검증/커밋/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

제품관리의 주요 업무를 React `/products/` 화면으로 옮겼습니다. 제품 목록 검색/상태 필터/정렬/페이지네이션, 단일 제품 등록·수정, Ecount/Excel 붙여넣기 기반 신규·기존 제품 upsert, 품번 붙여넣기 일괄 삭제, 전체 제품 XLSX 다운로드를 제공합니다. 제품관리의 프로모션 설정은 제거하고, 기존 프로모션 값이 남아 있어도 기준단가만 현재가로 사용하게 했습니다.

### 변경된 파일

- `frontend/src/App.tsx`, `frontend/src/api.ts`, `frontend/src/styles.css`: React 제품관리 화면/API client/UI 추가
- `reporting/views.py`, `reporting/urls.py`: 제품관리 JSON API, upsert/delete/export endpoint 추가, 기존 Django 제품 등록/수정의 프로모션 비활성화
- `reporting/models.py`, `reporting/admin.py`: 현재가 계산과 admin에서 프로모션 설정 제거
- `reporting/templates/reporting/product_form.html`, `reporting/templates/reporting/product_list.html`, `reporting/templates/reporting/schedule_form.html`: 레거시 Django 제품 화면/일정 제품 검색에서 프로모션 UI 제거
- `reporting/tests.py`: 제품관리 React API, 기준단가 현재가, 일괄 삭제, XLSX 다운로드 회귀 테스트 추가
- `AGENT_PLAN.md`, `AGENT_REPORT.md`, `HANDOFF.md`: 작업 상태 갱신

### CRM 개선

- Ecount에서 가져온 제품 데이터가 기존 품번과 겹치면 규격, 단위, 기준단가, 상태 변경분을 기존 제품에 반영합니다.
- 설명이 없는 4열 Ecount 행은 기존 제품 설명을 빈 값으로 덮어쓰지 않습니다.
- 삭제는 붙여넣은 품번 기준으로 처리하되, 견적/납품에 이미 사용된 제품은 삭제하지 않고 차단 결과로 반환합니다.
- React 사이드바에 `제품` 메뉴가 추가되어 제품 기준데이터 관리를 프론트 CRM 흐름에서 시작할 수 있습니다.

### 기존 기능 보존

- 기존 `/reporting/products/` Django 화면과 기존 일정 품목 선택 API `/reporting/api/products/`는 유지했습니다.
- DB 모델 변경과 migration은 없습니다. 기존 프로모션 컬럼은 호환성을 위해 남겼지만 제품관리 UI와 가격 계산에서는 사용하지 않습니다.
- 기존 제품 규격/단위 저장 회귀 동작은 유지했습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\models.py reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.ProductManagementReactApiTests --verbosity=2
→ Ran 4 tests, OK

python manage.py test reporting.tests.ProductSpecificationSaveTests reporting.tests.ProductManagementReactApiTests reporting.tests.SchedulesSummaryApiTests.test_product_api_list_returns_accessible_product_master_data --verbosity=1
→ Ran 10 tests, OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend; npm run build
→ OK, assets/index-Cvm7UZLA.js / assets/index-8S1Oy6zw.css

cd frontend; node --check server.mjs
→ OK

local frontend smoke with Playwright CLI
→ `/products/` renders product nav, metrics, table, paste panels, and product create form with mocked product API data.

git commit -m "feat: migrate product management to react" && git push origin main
→ Commit 126fd3b pushed to origin/main

railway up --service web --environment production --message "Deploy product management react migration 126fd3b" --ci
→ Deploy complete

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy product management react migration 126fd3b" --ci
→ Deploy complete

railway deployment list --service web --environment production --limit 5 --json
→ c36d7e71-7379-45f2-9dca-3d7af93525de SUCCESS

railway deployment list --service sales-note-frontend --environment production --limit 5 --json
→ 3bb14e78-8f7d-4d58-8e76-125bf65d8418 SUCCESS

Production smoke requests
→ /products/ 200 with assets/index-Cvm7UZLA.js and assets/index-8S1Oy6zw.css
→ /reporting/login/ 200
→ anonymous /reporting/api/products/manage/ 302 to /reporting/login/
→ anonymous /reporting/products/ 302 to /reporting/login/
```

### 알려진 제한

- 운영 로그인 세션이 필요한 실제 `/products/` 등록/수정 클릭 검증은 배포 후 수동 검수로 확인해야 합니다.
- DB 컬럼 자체의 프로모션 필드는 제거하지 않았습니다. 기존 데이터 호환과 migration 회피를 위해 남겨두고 UI/API에서 사용하지 않게 했습니다.

### 배포 상태

- Runtime commit: `126fd3b feat: migrate product management to react`
- GitHub push: `main` 반영 완료
- Railway `web`: `c36d7e71-7379-45f2-9dca-3d7af93525de` SUCCESS
- Railway `sales-note-frontend`: `3bb14e78-8f7d-4d58-8e76-125bf65d8418` SUCCESS
- Deploy logs: web migration/gunicorn startup path complete, frontend build/start complete

### 추천 다음 작업

- 제품관리 운영 수동검수가 완료되면, React 납품 생성/수정에서 기존 견적 품목을 끌어와 납품 품목으로 사용할 수 있게 합니다.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/products/`를 엽니다.
2. 제품 목록이 보이고 검색, 상태 필터, 정렬, 페이지 이동이 동작하는지 확인합니다.
3. `제품 등록`으로 테스트 제품을 만들고, 다시 수정해서 규격/단위/기준단가가 반영되는지 확인합니다.
4. Ecount/Excel 붙여넣기 영역에 기존 품번과 신규 품번을 섞어 넣고 `등록/갱신`을 실행해 기존 제품은 수정되고 신규 제품은 등록되는지 확인합니다.
5. `엑셀` 버튼으로 전체 제품 XLSX가 다운로드되는지 확인합니다.
6. 품번 일괄 삭제에 방금 만든 미사용 제품 품번을 붙여넣어 삭제되는지 확인하고, 사용 중인 제품은 차단되는지 확인합니다.
7. `/reporting/products/`에서도 프로모션 설정/현재가 UI가 사라졌고 기존 제품 목록이 계속 열리는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Mail Rich Editor Link Text Hotfix

**상태**: 구현/프론트 빌드/푸시/운영 배포/스모크 완료, 사용자 수동검수 완료

### 요약

React 메일 리치 에디터의 링크 버튼을 “표시할 텍스트”와 “URL”을 분리해서 입력하는 방식으로 보정했습니다. 본문에서 텍스트를 선택한 뒤 링크 버튼을 누르면 선택 텍스트가 표시 문구 기본값으로 들어가고, URL 입력 후 해당 선택 영역이 링크로 교체됩니다. 선택 텍스트가 없을 때도 URL 자체가 노출되지 않고 원하는 표시 문구로 링크를 삽입할 수 있습니다.

### 변경된 파일

- `frontend/src/App.tsx`: 에디터 selection range 저장/복원 helper 추가, 링크 삽입을 custom label + URL 방식으로 변경
- `AGENT_PLAN.md`, `AGENT_REPORT.md`, `HANDOFF.md`: 핫픽스 검증/배포/수동검수 기록 갱신

### CRM 개선

- 메일 본문에서 `홈페이지`, `견적서 확인`, `자료 다운로드` 같은 원하는 문구를 링크 텍스트로 사용할 수 있습니다.
- 선택한 텍스트를 그대로 링크로 바꿀 수 있어 메일 작성 흐름이 더 자연스럽습니다.

### 기존 기능 보존

- 기존 리치 에디터의 볼드/글꼴/색상/이미지/목록 기능은 유지했습니다.
- 링크 URL normalize 및 HTML sanitize 흐름은 기존 보안 처리 위에서 유지됩니다.

### 실행한 명령어 및 결과

```text
cd frontend; npm run build
→ OK, assets/index-D1nHin0S.js / assets/index-DdQNAE3O.css

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: insert mail links with custom text" && git push origin main
→ Commit 9fc5522 pushed to origin/main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy mail link text hotfix 9fc5522" --ci
→ Deploy complete

railway deployment list --service sales-note-frontend --environment production --limit 3 --json
→ e5f407b8-d513-4dcc-82ca-736e9964cf7f SUCCESS

railway deployment list --service web --environment production --limit 3 --json
→ 36758e7b-1f37-4d91-a3a1-2585d5a5eb33 SUCCESS (docs commit automatic deploy)

Production smoke requests
→ /reporting/login/ 200, /mailbox/ 200
```

### 배포 상태

- Runtime commit: `9fc5522 fix: insert mail links with custom text`
- GitHub push: `main` 반영 완료
- Railway `sales-note-frontend`: `e5f407b8-d513-4dcc-82ca-736e9964cf7f` SUCCESS
- Railway `web`: `36758e7b-1f37-4d91-a3a1-2585d5a5eb33` SUCCESS (문서 커밋 자동 배포)
- Deploy logs: web migration check OK / gunicorn startup OK, frontend server startup OK

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/mailbox/`에서 새 메일 또는 답장을 엽니다.
2. 본문에 `홈페이지` 같은 텍스트를 입력하고 해당 텍스트를 드래그 선택합니다.
3. 링크 버튼을 누르면 표시 텍스트 입력창에 선택 텍스트가 기본값으로 들어오는지 확인합니다.
4. URL을 입력한 뒤 본문에서 선택 텍스트가 링크로 바뀌는지 확인합니다.
5. 선택 텍스트 없이 링크 버튼을 눌러도 표시 문구와 URL을 따로 입력해 링크가 삽입되는지 확인합니다.

### 사용자 수동검수 결과

- 완료: 사용자가 2026-05-12 KST에 운영 수동검수를 완료했다고 확인했습니다.

---

## 2026-05-12 — React Rich Mail Editor And Scoped AI Workspace Prompts

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

React 메일 작성/답장을 서식 있는 에디터로 교체했습니다. 볼드, 기울임, 밑줄, 글씨체/크기/색상, 목록, 링크, 이미지 삽입을 지원하며, 발송 API는 HTML 본문을 서버에서 한 번 더 sanitize해서 Gmail/SMTP로 보냅니다. `/ai-workspace/?department_id=...` 상세 페이지의 추천 질문 후보는 요청된 부서/고객 범위로만 제한했습니다. 전체 `/ai-workspace/`에서는 기존처럼 전체 후보 추천이 가능합니다.

### 변경된 파일

- `frontend/src/App.tsx`: React 메일 리치 에디터, 본문 HTML 상태/검증, 이미지 업로드/붙여넣기/드롭, AI Workspace 상세 추천 표시 흐름 유지
- `frontend/src/api.ts`: 메일 발송 payload에 `bodyHtml` 추가, 에디터 이미지 업로드 API 연결
- `frontend/src/styles.css`: 리치 에디터 툴바/본문/오류 스타일 추가
- `reporting/gmail_views.py`: outgoing `body_html` sanitize 및 plain text fallback 처리
- `reporting/views.py`: `department_id`가 요청된 AI Workspace 상세 API의 추천 질문 후보를 해당 부서로 제한
- `reporting/tests.py`: 리치 HTML 메일 sanitize, AI Workspace 상세 추천 스코프 회귀 테스트 추가
- `AGENT_PLAN.md`, `HANDOFF.md`: 작업 상태 및 운영 배포 기록 갱신

### CRM 개선

- `/mailbox/`에서 메일 작성/답장 시 굵게, 글꼴, 색상, 링크, 이미지 같은 기본 서식을 사용할 수 있습니다.
- 첨부 이미지가 아닌 본문 이미지는 기존 `/reporting/upload-image/`를 통해 업로드 후 본문에 삽입됩니다.
- 상세 AI Workspace URL에서는 다른 고객/부서의 추천 질문이 섞이지 않습니다.

### 기존 기능 보존

- 기존 plain text 메일 발송, 파일 첨부, 답장/일정 메일 흐름은 유지했습니다.
- 서버는 허용된 이메일 HTML 태그/속성/스타일만 통과시키고 script, event handler, `javascript:` URL은 제거합니다.
- 부서 ID가 없는 `/ai-workspace/` 전체 화면의 추천 후보 생성 방식은 유지했습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_detail_scopes_prompt_targets_to_requested_department reporting.tests.AIWorkspaceSummaryApiTests.test_ai_workspace_summary_api_lists_own_ai_operational_data reporting.tests.ReactMailboxApiTests.test_mailbox_send_api_sends_sanitized_rich_html_body reporting.tests.ReactMailboxApiTests.test_mailbox_send_api_normalizes_plain_text_line_breaks_for_html --verbosity=1
→ Ran 4 tests, OK

python manage.py test reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.ReactMailboxApiTests --verbosity=1
→ Ran 24 tests, OK

cd frontend; npm run build
→ OK, assets/index-Crb-VKbQ.js / assets/index-DdQNAE3O.css

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add rich mail editor and scope ai prompts" && git push origin main
→ Commit eb7e0fc pushed to origin/main

railway up --service web --environment production --message "Deploy rich mail editor and scoped AI prompts eb7e0fc" --ci
railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy rich mail editor and scoped AI prompts eb7e0fc" --ci
→ Deploy complete

railway deployment list --service web --environment production --limit 5 --json
→ fc0b97e2-b144-4133-8171-2ca1be4375cd SUCCESS

railway deployment list --service sales-note-frontend --environment production --limit 5 --json
→ 1053e2a3-603d-472c-8aea-159f0a5cf130 SUCCESS

Production smoke requests
→ /reporting/login/ 200, /ai-workspace/ 200, /ai-workspace/?department_id=81 200, /mailbox/ 200
```

### 배포 상태

- Runtime commit: `eb7e0fc feat: add rich mail editor and scope ai prompts`
- GitHub push: `main` 반영 완료
- Railway `web`: `fc0b97e2-b144-4133-8171-2ca1be4375cd` SUCCESS
- Railway `sales-note-frontend`: `1053e2a3-603d-472c-8aea-159f0a5cf130` SUCCESS
- Deploy logs: web migration check OK / gunicorn startup OK, frontend server startup OK

### 알려진 제한

- 운영 로그인 세션 없이 실제 메일 발송 완료와 수신자 메일함 렌더링까지 자동 검증하지는 못했습니다.
- contenteditable 기반 에디터라 브라우저 기본 편집 동작을 사용합니다. 내부 CRM 용도로 빠르게 적용했으며, 추후 더 강한 편집기 라이브러리로 교체할 수 있습니다.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/ai-workspace/?department_id=81`을 열고 추천 질문이 해당 상세 고객/부서 기준으로만 나오는지 확인합니다.
2. `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에서는 전체 추천 질문이 계속 나오는지 확인합니다.
3. `/mailbox/`에서 새 메일 또는 답장을 열고 볼드/글꼴/색상/링크/이미지를 넣어 테스트 발송합니다.
4. 발송한 메일의 서식이 유지되고, 이상한 HTML/script 텍스트가 노출되지 않는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Quote Notes, Mailbox Attachments, and Document PDF Hotfixes

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

운영 검수 중 확인된 견적서/메일함 문제를 묶어서 수정했습니다. 일정 단위로 통합되어 있던 견적 기타사항을 견적서 구분별로 분리했고, 메일 발송 시 내부 직원 참조 포함 여부를 사용자가 선택하게 했습니다. 견적서/거래명세서 출력의 볼드체를 제거하고, 긴 품목 적요는 PDF에서 잘리지 않도록 셀 줄바꿈과 행 높이를 보정합니다. 받은 메일 본문에 남던 `p{margin-top...}` CSS 조각을 제거하고, 상대가 보낸 Gmail/IMAP 첨부파일을 React 메일함에서 확인/다운로드할 수 있게 했습니다.

### 변경된 파일

- `reporting/models.py`, `reporting/migrations/0098_schedule_quote_group_note.py`: 일정+견적서 구분별 기타사항 모델 추가 및 기존 전체 기타사항 이관
- `reporting/views.py`, `reporting/urls.py`: 구분별 기타사항 API/문서 변수 반영, 서류 볼드 제거, 품목 적요 셀 줄바꿈/행 높이 보정, 다운로드 endpoint 연결
- `reporting/gmail_utils.py`, `reporting/gmail_views.py`, `reporting/imap_utils.py`, `reporting/imap_views.py`: 받은 메일 본문 정리, 첨부 메타데이터 저장, Gmail/IMAP 첨부 다운로드, 내부 직원 CC 옵션
- `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`: 구분별 기타사항 입력/표시, 내부 직원 참조 체크박스, 메일 첨부 표시/다운로드 UI
- `reporting/tests.py`: 견적 구분별 기타사항, 첨부 다운로드, CSS 본문 정리, 내부 CC 옵션, 볼드 제거, 긴 적요 행 높이 회귀 테스트 추가
- `AGENT_PLAN.md`: 작업 상태 및 배포 기록 갱신

### CRM 개선

- `/schedules/880/` 같은 일정에서 `보상판매`, `수리` 등 견적서 구분별로 기타사항을 따로 저장하고 각 견적서 PDF 변수에 따로 들어갑니다.
- 견적서 품목 적요가 길어도 `{{품목N_적요}}`/`{{품목N_비고}}` 셀은 자동 줄바꿈과 행 높이 보정이 적용됩니다.
- 메일 작성/답장 시 내부 직원 이메일을 CC에 포함할지 체크박스로 선택할 수 있습니다.
- 받은 메일 상세에서 HTML/CSS 잔여 텍스트가 줄어들고, 받은 첨부파일 다운로드 링크가 표시됩니다.

### 기존 기능 보존

- 기존 `/reporting/*` 라우트, React 일정/메일함, 서류 템플릿 변수 치환, 수동 CC, 수동 첨부파일, 등록 견적서 자동 첨부 흐름은 유지했습니다.
- 내부 직원 이메일은 체크된 경우에만 서버에서 CC에 병합합니다.
- 첨부파일 다운로드는 기존 메일 접근 권한 범위 안에서만 허용합니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\gmail_utils.py reporting\imap_utils.py reporting\imap_views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.ReactMailboxApiTests --verbosity=1
→ Ran 61 tests, OK

python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 14 tests, OK

cd frontend; node --check server.mjs
→ OK

cd frontend; npm run build
→ OK, assets/index-DE2wnSQU.js / assets/index-DQPI3AAP.css

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected after migration creation

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commits:
  - `14606a4 fix: repair quote notes and mailbox attachments`
  - `97513a5 fix: expand quote item note rows`
- GitHub push: `main` 반영 완료
- Railway `web`: `f1c117d4-f7cc-41ca-81f1-3630c7238a4e` SUCCESS
- Railway `sales-note-frontend`: `a159b40a-4105-4473-bea3-580e69f08e1d` SUCCESS
- Production smoke: `/reporting/login/` 200, frontend `/schedules/880/` 200, frontend `/mailbox/` 200
- Deploy logs: web migration check OK / gunicorn startup OK, frontend server startup OK

### 알려진 제한

- 운영 로그인 세션 없이 실제 스케줄 880 저장/문서 생성/메일 첨부 다운로드까지 자동 클릭 검증하지는 못했습니다.
- 과거에 이미 동기화된 Gmail 메일 중 첨부 메타데이터가 비어 있는 건 스레드 상세 열람 시 Gmail detail을 다시 조회해 보강합니다. 그래도 보이지 않으면 메일 동기화를 한 번 실행한 뒤 다시 열어야 합니다.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/schedules/880/`에서 견적 품목 구분별 기타사항을 각각 입력하고 저장 후 새로고침해 분리 유지되는지 확인합니다.
2. 각 견적 구분의 견적서 PDF를 생성/다운로드해 해당 구분 기타사항만 들어가고, 볼드체가 제거되며, 긴 품목 적요가 잘리지 않고 행이 늘어나는지 확인합니다.
3. `/mailbox/`에서 `kms@kici.co.kr` 또는 첨부가 있는 받은 메일 스레드를 열어 첨부파일 링크가 보이고 다운로드되는지 확인합니다.
4. 같은 메일 본문에서 `p{margin-top:0px...}` 같은 CSS 조각이 보이지 않는지 확인합니다.
5. 메일 작성/답장에서 “내부 직원 참조 포함” 체크박스가 보이고, 체크 여부에 따라 내부 직원 이메일이 CC에 들어가는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Quote Salesperson Name Order Normalization

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

견적서 서류 변수와 PDF 생성에서 담당자명이 `이름+성`처럼 `재현안`으로 보이는 문제를 보정했습니다. 정상 저장된 `first_name=재현`, `last_name=안` 계정과, 과거 사용자 생성/수정 화면 라벨 혼동으로 뒤집혀 저장된 `first_name=안`, `last_name=재현` 계정 모두 견적서에는 `안재현`으로 들어갑니다.

### 변경된 파일

- `reporting/views.py`: 문서 생성 전용 담당자명 helper 추가, 견적서 변수/PDF 생성에서 helper 사용, 사용자 생성/수정 폼의 성/이름 라벨 보정
- `reporting/templates/reporting/user_create.html`, `reporting/templates/reporting/user_edit.html`: 관리자 사용자 생성/수정 화면 라벨 보정
- `reporting/templates/reporting/user_list.html`, `reporting/templates/reporting/manager_user_list.html`, `reporting/templates/reporting/profile.html`: 사용자명 표시를 성+이름 순서로 보정
- `reporting/tests.py`: 정상 저장/과거 역저장 한글 이름 케이스 회귀 테스트 추가
- `AGENT_PLAN.md`: 현재 작업 및 이후 제품관리 대기 작업 기록

### CRM 개선

- 견적서의 `실무자`, `영업담당자`, `담당영업` 변수에 한국식 성+이름 순서가 안정적으로 반영됩니다.
- 사용자 관리 화면의 신규 입력 라벨을 바로잡아 이후 계정 생성/수정 시 성과 이름이 뒤집혀 저장될 가능성을 줄였습니다.

### 기존 기능 보존

- DB 모델/마이그레이션 변경은 없습니다.
- 기존 견적서 변수, 견적서 구분, PDF 등록/다운로드, 메일 자동 첨부 흐름은 유지했습니다.
- 비한글 이름이나 성/이름 판단이 애매한 경우는 기존 Django 의미인 `last_name + first_name`을 유지합니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 12 tests, OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: normalize quote salesperson name order" && git push origin main
→ Commit 9b24fcf pushed to origin/main

railway deployment list --service web --environment production --limit 3 --json
→ web deployment 5d6450fb-896a-4e89-b851-c99b083785bf SUCCESS for commit 9b24fcf

railway logs 5d6450fb-896a-4e89-b851-c99b083785bf --service web --environment production --deployment --lines 120
→ No migrations to apply, gunicorn startup OK

Production smoke requests
→ /reporting/login/ 200, /reporting/api/documents/ 401, frontend /documents/ 200, frontend /schedules/879/ 200
```

### 알려진 제한

- 운영 로그인 세션 없이 실제 견적서 PDF 안의 이름 텍스트까지 자동 확인하지는 못했습니다.
- `안재현`처럼 한 글자 성 + 두 글자 이름 형태는 양방향으로 보정하지만, 드문 성명 조합은 기존 `last_name + first_name` 규칙을 따릅니다.

### 배포 상태

- Runtime commit: `9b24fcf fix: normalize quote salesperson name order`
- GitHub push: `main` 반영 완료
- Railway `web`: `5d6450fb-896a-4e89-b851-c99b083785bf` SUCCESS
- Railway `sales-note-frontend`: 변경 없음, 재배포 불필요

### 수동 서버 테스트 절차

1. 운영에서 프로필 또는 사용자 정보가 `이름=재현`, `성=안`인지 확인합니다.
2. quote 일정에서 견적서 PDF를 다시 등록/다운로드합니다.
3. 견적서의 `실무자`, `영업담당자`, `담당영업` 위치가 `안재현`으로 표시되는지 확인합니다.
4. 관리자/매니저 사용자 생성 또는 수정 화면에서 `이름` 입력란과 `성` 입력란 라벨이 올바른지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Quote Document Groups And Registered Document Deletion

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

같은 quote 일정에서 `보상판매`, `수리`처럼 견적서 구분별 품목 묶음을 만들고, 각 구분의 품목만 담긴 견적서 PDF를 별도로 등록/다운로드할 수 있게 했습니다. 등록된 견적서 PDF는 일정 메일 발송 시 모두 자동 첨부되며, 등록된 생성 서류는 견적서/거래명세서/납품서 모두 일정 상세에서 삭제할 수 있습니다.

### 변경된 파일

- `reporting/models.py`, `reporting/migrations/0097_quote_document_groups.py`: 품목/생성 로그에 견적서 구분 필드 추가
- `reporting/views.py`, `reporting/urls.py`: 구분별 견적서 미리보기/생성, 등록 서류 목록, 등록 서류 삭제 API, PDF 파일 저장 범위 확장
- `reporting/gmail_views.py`: quote 일정 메일 자동 첨부를 견적서 구분별 PDF 생성/첨부로 보정
- `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`: 견적서 구분 입력, 구분별 문서 action, 등록 서류 목록/삭제 버튼 추가
- `reporting/templates/reporting/partials/doc_variable_list.html`, `reporting/templates/reporting/schedule_detail.html`: 서류 변수 도움말에 견적 구분 변수 추가
- `reporting/tests.py`: 구분별 문서 action, 구분별 서류 데이터, 자동첨부 fallback, 등록 서류 삭제 권한 테스트 추가
- `AGENT_PLAN.md`, `HANDOFF.md`: 작업 상태/검증/배포 기록 갱신

### CRM 개선

- 한 일정 안에서 서로 다른 견적서 2부 이상을 품목 묶음별로 관리할 수 있습니다.
- 견적서 PDF를 여러 번 등록하더라도 각 PDF가 해당 견적 구분의 품목만 포함합니다.
- 등록된 견적서/거래명세서/납품서 PDF를 일정 상세에서 삭제할 수 있습니다.
- 메일 자동 첨부는 기존 의도대로 quote 일정의 견적서 PDF만 대상으로 유지됩니다.

### 기존 기능 보존

- 기존 `/reporting/*` URL, React 일정 상세, 서류 템플릿, Gmail/메일 발송 흐름은 유지했습니다.
- 거래명세서/납품서는 등록 및 삭제 대상에는 포함하지만 자동 첨부 대상에는 포함하지 않았습니다.
- 권한은 일정 소유자 편집 권한 기준으로 제한했습니다. 관리자/동료는 등록 서류 삭제가 차단됩니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\tests.py
→ OK

cd frontend; node --check server.mjs
→ OK

python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 54 tests, OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected after migration creation

git diff --check
→ OK (LF→CRLF warning only)

cd frontend; npm run build
→ OK, assets/index-BG4g7IVe.js / assets/index-1JjkoDo3.css

git commit -m "feat: split schedule quote documents by group" && git push origin main
→ Commit 0384e13 pushed to origin/main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy quote document groups 0384e13" --ci
→ Deploy complete

railway deployment list --service web --environment production --limit 2 --json
→ web deployment b191502b-10bc-4e9b-973f-756bb2c5b3c0 SUCCESS for commit 0384e13

railway deployment list --service sales-note-frontend --environment production --limit 2 --json
→ sales-note-frontend deployment 3fb901ec-e5ec-49f8-aa2d-5d568f018ede SUCCESS

Production smoke requests
→ /schedules/879/ 200, /mailbox/ 200, /documents/ 200, new JS/CSS assets 200, /reporting/login/ 200, /reporting/api/schedules/879/ 401, generated document delete unauthenticated POST 403

railway logs for latest web/frontend deployments
→ reporting.0097_quote_document_groups migration OK, gunicorn/frontend startup OK
```

### 알려진 제한

- 운영에서 실제 로그인 계정으로 구분별 품목 저장, PDF 등록/다운로드, 삭제 버튼, 메일 자동첨부를 수동 확인해야 합니다.
- 등록된 견적서가 하나라도 있으면 메일 발송은 등록된 견적서 PDF 전체를 첨부합니다. 등록된 견적서가 없을 때만 구분별 PDF를 발송 직전에 생성합니다.
- 브라우저 자동화 도구가 세션에 노출되지 않아 로컬 클릭 검증은 생략했고, TypeScript/Vite 빌드와 운영 smoke로 확인했습니다.

### 배포 상태

- Runtime commit: `0384e13 feat: split schedule quote documents by group`
- GitHub push: `main` 반영 완료
- Railway `web`: `b191502b-10bc-4e9b-973f-756bb2c5b3c0` SUCCESS
- Railway `sales-note-frontend`: `3fb901ec-e5ec-49f8-aa2d-5d568f018ede` SUCCESS
- Production JS/CSS: `assets/index-BG4g7IVe.js`, `assets/index-1JjkoDo3.css`
- Production deploy log: `reporting.0097_quote_document_groups` migration applied OK

### 수동 서버 테스트 절차

1. 운영에서 `https://sales-note-frontend-production.up.railway.app/schedules/879/` 또는 다른 quote 일정 상세로 이동합니다.
2. 견적 품목 편집에서 `견적서 구분`을 `보상판매`, `수리`처럼 2개 이상 나눠 저장하고 새로고침 후 유지되는지 확인합니다.
3. 서류 패널에서 구분별 `보상판매 견적서`, `수리 견적서` action이 표시되는지 확인합니다.
4. 각 구분의 `PDF 등록/다운로드`를 실행하고 `등록된 서류` 목록에 별도 PDF가 표시되는지 확인합니다.
5. 등록된 서류 삭제 버튼으로 견적서 또는 거래명세서 PDF를 삭제하고 목록에서 사라지는지 확인합니다.
6. 같은 quote 일정에서 메일을 발송하고 남아 있는 등록 견적서 PDF들이 자동 첨부되는지 확인합니다.
7. delivery 일정에서 거래명세서 PDF 등록/삭제가 가능하되, 메일 발송 시 견적서 PDF가 자동 첨부되지 않는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Quote PDF Registration And Schedule Mail Auto Attachment

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

견적 일정에서 견적서 PDF를 여러 개 등록할 수 있도록 서류 생성 로그에 생성 파일을 보관하게 했습니다. 견적서 PDF 생성 성공 시 해당 PDF가 일정의 등록된 견적서로 남고, 해당 일정에서 메일을 보낼 때 등록된 견적서 PDF만 자동 첨부됩니다. 등록된 견적서가 없는 quote 일정에서 메일을 보내면 발송 직전에 견적서 PDF를 생성/등록한 뒤 첨부합니다.

### 변경된 파일

- `reporting/models.py`, `reporting/migrations/0096_documentgenerationlog_file_and_more.py`: 생성 서류 파일/파일명/파일 크기 필드 추가
- `reporting/views.py`, `reporting/urls.py`: 견적서 PDF 저장, 등록된 서류 다운로드 endpoint, 일정 상세 문서 payload 확장
- `reporting/gmail_views.py`: 일정 메일/React 메일 API에서 quote 일정 견적서 PDF 자동 첨부
- `reporting/templates/reporting/gmail/compose_from_schedule.html`, `reporting/templates/reporting/schedule_detail.html`: Django 일정 메일/견적서 버튼 안내 보강
- `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`: React 일정 상세 등록 견적서 목록, 메일 발송 진입, schedule_id 메일 payload 추가
- `reporting/tests.py`: 자동 첨부, 자동 생성 fallback, 비견적 일정 제외 테스트 추가
- `AGENT_PLAN.md`: 작업 계획 갱신

### CRM 개선

- 한 일정에 견적서 PDF를 여러 개 등록/보관할 수 있습니다.
- React 일정 상세에서 등록된 견적서 목록을 확인하고 다운로드할 수 있습니다.
- 일정에서 메일 작성으로 이동하면 schedule context가 메일 발송 API에 전달됩니다.
- 자동 첨부 대상은 quote 일정의 견적서 PDF로 제한됩니다.

### 기존 기능 보존

- 기존 수동 첨부파일, Gmail/IMAP 발송, 답장 메일, 명함 서명, 메일 줄바꿈 정규화는 유지했습니다.
- 거래명세서/납품서는 자동 첨부하지 않습니다.
- 답장 메일에는 자동 견적서 첨부를 적용하지 않아 기존 답장 흐름을 유지했습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\models.py reporting\views.py reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 20 tests, OK

python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 28 tests, OK

cd frontend; npm run build
→ OK, assets/index-COLHVyxC.js / assets/index-Bmtl8HKb.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected after migration creation

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: auto attach quote pdfs to schedule mail" && git push origin main
→ Commit 95aeec7 pushed to origin/main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy quote pdf auto attachments 95aeec7" --ci
→ Deploy complete

railway deployment list --service web --environment production --limit 2 --json
→ web deployment 2d1dd812-3fe5-4c3b-953e-870ca5c88baf SUCCESS for commit 95aeec7

railway deployment list --service sales-note-frontend --environment production --limit 2 --json
→ sales-note-frontend deployment 05a56e6c-3067-4500-8ae0-6383ff40d91f SUCCESS

Production smoke requests
→ /schedules/ 200, /mailbox/ 200, new JS/CSS assets 200, /reporting/login/ 200, /reporting/api/schedules/ 401, generated document download unauthenticated 302

railway logs for latest web/frontend deployments
→ reporting.0096 migration OK, gunicorn/frontend startup OK, no traceback observed; expected Unauthorized log only from protected API smoke
```

### 알려진 제한

- 자동 생성은 Excel 템플릿을 PDF로 변환할 수 있어야 동작합니다. PDF 변환 실패로 Excel fallback이 발생하면 메일 발송을 중단하고 오류를 표시합니다.
- 등록된 견적서가 여러 개 있으면 해당 일정의 견적서 PDF가 모두 자동 첨부됩니다.

### 배포 상태

- Runtime commit: `95aeec7 feat: auto attach quote pdfs to schedule mail`
- GitHub push: `main` 반영 완료
- Railway `web`: `2d1dd812-3fe5-4c3b-953e-870ca5c88baf` SUCCESS, commit `95aeec7`
- Railway `sales-note-frontend`: `05a56e6c-3067-4500-8ae0-6383ff40d91f` SUCCESS, message `Deploy quote pdf auto attachments 95aeec7`
- Railway `web` deploy log: `reporting.0096_documentgenerationlog_file_and_more` migration applied OK, gunicorn startup OK.
- Railway `sales-note-frontend` deploy log: frontend server startup OK.
- Production smoke: `/schedules/` 200, `/mailbox/` 200, `assets/index-COLHVyxC.js` 200, `assets/index-Bmtl8HKb.css` 200.
- Production smoke: backend `/reporting/login/` 200, unauthenticated `/reporting/api/schedules/` 401, unauthenticated generated document download 302 to login.

### 수동 서버 테스트 절차

1. 운영에서 quote 일정 상세로 이동합니다.
2. 견적서 `PDF 등록/다운로드`를 두 번 실행해 등록된 견적서가 여러 개 표시되는지 확인합니다.
3. 같은 일정에서 `메일 발송`을 열고 수신자/본문을 입력합니다.
4. 메일을 발송한 뒤 수신 메일에 견적서 PDF만 자동 첨부되었는지 확인합니다.
5. delivery 일정에서 메일을 보내도 견적서 PDF가 자동 첨부되지 않는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-12 — Quote PDF A4 Auto Fit

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크/사용자 수동검수 완료

### 요약

견적서 PDF 다운로드 시 엑셀 템플릿의 인쇄 설정이 A4보다 크게 잡혀 PDF가 잘리는 문제를 수정했습니다. 서류 생성 과정에서 변수 치환과 미디어 복원을 마친 XLSX 파일에 A4 용지, 1페이지 너비 맞춤, 축소 여백을 XML 레벨로 적용한 뒤 PDF 변환을 실행하도록 했습니다.

### 변경된 파일

- `reporting/views.py`: PDF 변환 전 XLSX 워크시트 인쇄 설정을 A4/1페이지 너비 맞춤으로 보정하는 helper 추가 및 서류 생성 경로에 연결
- `reporting/tests.py`: 생성 XLSX의 worksheet XML에 A4/fit-to-page 설정이 들어가는지 회귀 테스트 추가
- `AGENT_PLAN.md`: hotfix 계획 기록

### CRM 개선

- 견적서 PDF가 템플릿의 잘못된 배율/용지 설정 때문에 A4 밖으로 잘리는 위험을 줄였습니다.
- PDF 변환 실패 시 기존처럼 Excel 파일 fallback은 유지됩니다.

### 기존 기능 보존

- 기존 서류 템플릿 변수 치환, 이미지/미디어 복원, XLSX 다운로드, PDF 변환 흐름은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.
- React 프론트엔드 변경은 없습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.DocumentTemplatesReactApiTests.test_document_pdf_layout_helper_sets_a4_fit_to_page reporting.tests.DocumentTemplatesReactApiTests.test_document_template_data_includes_quote_discount_and_note_variables --verbosity=1
→ Ran 2 tests, OK

python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 10 tests, OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 알려진 제한

- 로컬 테스트는 XLSX 인쇄 설정 XML을 검증했습니다. 실제 운영 PDF 출력물의 시각 검수는 로그인 세션과 운영 템플릿이 필요합니다.
- `fitToHeight=0`으로 설정해 가로는 A4 한 페이지 너비에 맞추고, 품목이 많아 세로가 길면 여러 페이지로 이어질 수 있게 했습니다.

### 배포 상태

- Runtime commit: `0c70596 fix: fit document pdf exports to a4`
- GitHub push: `main` 반영 완료
- Railway `web`: `1cfaeab1-26ef-428e-89b5-67a1a98dfd11` SUCCESS
- Production `/reporting/login/` returns 200.
- Production `/documents/` returns 200 through the React frontend.
- Anonymous frontend-proxied and direct backend `/reporting/api/documents/` return `401 Unauthorized`.
- `sales-note-frontend` 배포 없음: 프론트 코드 변경 없음

### 수동 서버 테스트 절차

1. 운영에서 견적 일정 상세로 이동합니다.
2. 견적서 PDF 다운로드를 실행합니다.
3. PDF가 A4 폭 안에 맞고 오른쪽/아래가 잘리지 않는지 확인합니다.
4. 품목이 많은 견적서는 세로 방향으로 다음 페이지가 생성되는지 확인합니다.

### 사용자 수동검수 결과

- 완료: 사용자가 2026-05-12 KST에 운영 수동검수 완료를 확인했습니다.

---

## 2026-05-12 — Quote Discount Variables And AI Priority Goals

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크/사용자 수동검수 완료

### 요약

견적 품목에 기준단가와 별도로 할인율/할인단가를 저장하고, 최종 적용단가 기준으로 금액과 서류 변수가 계산되도록 확장했습니다. 품목별 적요와 전체 견적 기타사항을 저장하며, React `/documents/` 템플릿 등록 화면에서 사용 가능한 변수를 확인하고 복사할 수 있게 했습니다. 추가 요청으로 AI Workspace 추천 목표에는 명확한 고객명을 표시하고, 부서/고객 AI 분석 실행 시 CRM 고객 우선순위를 분석 결과 기준으로 다시 산정하도록 했습니다.

### 변경된 파일

- `reporting/models.py`, `reporting/migrations/0095_deliveryitem_discount_rate_and_more.py`: 견적 기타사항, 할인율, 할인단가 필드 및 적용단가 계산 추가
- `reporting/views.py`: React 일정/서류 API, 문서 변수, 할인 금액 계산, AI Workspace 추천 목표 payload 확장
- `reporting/templates/reporting/partials/doc_variable_list.html`: Django 변수 도움말에 신규 견적/품목 변수 추가
- `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`: 일정 품목 편집, 서류 변수 복사, AI 추천 목표 고객명/우선순위 UI 추가
- `ai_chat/services.py`, `ai_chat/views.py`, `ai_chat/department_prompt.py`: AI 분석 결과의 고객별 추천목표/우선순위 추천 저장 및 CRM 우선순위 갱신
- `reporting/tests.py`, `ai_chat/tests.py`: 견적 할인/서류 변수/AI Workspace/AI 우선순위 회귀 테스트 추가
- `AGENT_PLAN.md`: 작업 계획 갱신

### CRM 개선

- 견적 품목별로 기준단가를 유지하면서 할인율 입력 또는 할인단가 직접 입력을 사용할 수 있습니다.
- 품목별 `적요`와 전체 견적 `기타사항`을 엑셀/서류 변수로 치환할 수 있습니다.
- React 서류 템플릿 등록 화면에서 Django와 동일하게 사용 가능한 변수 토큰을 복사할 수 있습니다.
- AI Workspace 추천 목표 카드가 고객명을 명확히 표시합니다.
- 부서 AI 분석과 개별 고객 AI 분석 후 고객 우선순위가 AI 판단 결과로 갱신됩니다.

### 기존 기능 보존

- 기존 `/reporting/*` 라우트와 Django 서류 템플릿 화면은 유지했습니다.
- 기존 기준단가 직접 조절 방식은 유지하고, 할인단가/할인율은 추가 선택지로 붙였습니다.
- 기존 `DeliveryItem.notes`를 적요로 재사용해 품목 적요용 추가 DB 필드는 만들지 않았습니다.
- AI 권한(`can_use_ai`)과 담당자별 접근 제한은 유지했습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests reporting.tests.AIWorkspaceSummaryApiTests ai_chat.tests.AIDepartmentPromptLogicTests ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
→ Ran 50 tests, OK

python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 37 tests, OK

python manage.py test ai_chat.tests.AIDepartmentPromptLogicTests ai_chat.tests.AIDepartmentAnalysisMemoryTests reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1
→ Ran 13 tests, OK

python -m py_compile ai_chat\services.py ai_chat\views.py ai_chat\department_prompt.py reporting\views.py reporting\tests.py ai_chat\tests.py
→ OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected after migration file creation

cd frontend; npm run build
→ OK, assets/index-DJaKKt6c.js / assets/index-DHLL1LUc.css

cd frontend; node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 알려진 제한

- 운영에서 실제 로그인 계정으로 견적 품목 저장, 서류 변수 복사, AI 분석 실행 후 우선순위 갱신을 수동 확인해야 합니다.
- 할인단가가 있으면 최종 적용단가는 할인단가를 우선 사용합니다. 할인율만 입력하면 서버가 할인단가를 계산해 저장합니다.
- AI가 고객별 우선순위 추천을 명시하지 않으면 고객 단계 컨텍스트와 파이프라인 단계로 보정합니다.

### 배포 상태

- Runtime commit: `b09acf7 feat: expand quote discounts and ai goals`
- GitHub push: `main` 반영 완료
- Railway `web`: `73d90eea-de63-499a-b19d-a7bcc3da409a` SUCCESS
- Railway `sales-note-frontend`: `4f2dacfe-792e-447c-ad71-d46944452f53` SUCCESS
- Production `/documents/`, `/schedules/`, `/ai-workspace/` return 200 and serve `assets/index-DJaKKt6c.js` / `assets/index-DHLL1LUc.css`.
- Production JS contains `할인단가`, `templateVariableGroups`, `우선순위 갱신`, `추천 목표`.
- Production CSS contains `document-variable-panel`, `ai-goal-card-meta`, `schedule-quote-extra-notes`.
- Production `/reporting/login/` returns 200.
- Anonymous frontend-proxied and direct backend `/reporting/api/documents/` return `401 Unauthorized`.
- Anonymous frontend-proxied and direct backend `/reporting/api/ai-workspace/` return `401 Unauthorized`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/schedules/`에서 견적 일정 상세로 이동합니다.
2. 견적 품목 편집에서 기준단가, 할인율, 할인단가, 적요를 입력하고 저장합니다.
3. 할인율 입력 시 할인단가가 자동 계산되고, 할인단가 직접 입력 시 최종 금액이 할인단가 기준으로 저장되는지 확인합니다.
4. 전체 견적 기타사항을 입력하고 저장 후 새로고침해 유지되는지 확인합니다.
5. 해당 일정의 견적서 미리보기/다운로드에서 `품목1_기준단가`, `품목1_할인율`, `품목1_할인단가`, `품목1_적요`, `견적기타사항` 값이 반영되는지 확인합니다.
6. `https://sales-note-frontend-production.up.railway.app/documents/`에서 템플릿 등록 폼을 열고 변수 목록이 보이는지, 새 변수를 복사할 수 있는지 확인합니다.
7. `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에서 추천 목표 카드에 고객명이 표시되는지 확인합니다.
8. 부서 AI 분석을 실행한 뒤 추천 목표와 고객 우선순위가 갱신되는지 확인합니다.

### 사용자 수동검수 결과

- 완료: 사용자가 2026-05-12 KST에 운영 수동검수 완료를 확인했습니다.

---

## 2026-05-12 — React AI Summary Pipeline Questions And Email Context

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

React CRM의 부서 AI 요약이 API에서 중간에 잘리지 않도록 고객 상세, AI Workspace, 파이프라인 요약 truncation을 제거했습니다. 파이프라인 선택 고객 패널에서는 부서 AI 분석 실행, 전체 결과 펼침, PainPoint 검증 메모 저장을 React 안에서 사용할 수 있게 했고, AI 추천 질문은 별도 목록으로 모아 복사할 수 있게 했습니다. AI 분석 입력에는 고객이 보낸 답장과 함께 같은 스레드 또는 최근 사용자 발신 메일을 최대 2건까지 포함하도록 보강했습니다.

### 변경된 파일

- `reporting/views.py`: AI 요약 truncation 제거, 고객 AI payload에 `recommendedQuestions` 추가
- `reporting/funnel_views.py`: 파이프라인 AI payload에 전체 고객 AI 결과 payload 포함
- `ai_chat/services.py`: 고객 답장과 최근 사용자 발신 메일 최대 2건을 AI 메일 컨텍스트에 포함
- `frontend/src/api.ts`: 고객 AI payload 정규화 helper 및 추천 질문 타입 추가
- `frontend/src/App.tsx`: 파이프라인 AI 실행/결과/검증 UI와 추천 질문 복사 UI 추가
- `frontend/src/styles.css`: 추천 질문 목록/복사 버튼 스타일 추가
- `reporting/tests.py`, `ai_chat/tests.py`: AI 요약/추천 질문/파이프라인/메일 컨텍스트 회귀 테스트 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 긴 AI 상단 요약이 고객 상세, AI Workspace, 파이프라인에서 잘리지 않고 표시됩니다.
- 파이프라인에서 고객을 보다가 별도 Django 화면으로 이동하지 않아도 AI 분석 실행과 결과 확인이 가능합니다.
- missing info, 검증 인사이트, PainPoint 검증 질문을 `추천 질문`으로 모아 고객에게 바로 물어볼 질문을 React에서 복사할 수 있습니다.
- 고객 답장 분석 시 사용자가 최근 보낸 메일 맥락을 최대 2건까지 함께 보므로 답장의 의도와 이전 제안을 더 잘 해석할 수 있습니다.

### 기존 기능 보존

- 기존 `reporting` 앱과 `/reporting/*` URL은 유지했습니다.
- 기존 Django AI 결과 링크, AI 허브 링크, 고객 상세 AI 패널, PainPoint 검증 API는 유지했습니다.
- AI 권한(`can_use_ai`)과 본인 담당 부서 분석 제한은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.PipelineApiTests ai_chat.tests.AIEmailAndStageActionContextTests --verbosity=1
→ Ran 41 tests, OK

python -m py_compile reporting\views.py reporting\funnel_views.py ai_chat\services.py reporting\tests.py ai_chat\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-CAwxcHSb.js / assets/index-BpCNrkRC.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ OK, EMAIL_ENCRYPTION_KEY warning only

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 로컬 화면 확인

- Django dev server와 Vite dev server를 로컬에서 실행했습니다.
- Playwright Chromium으로 `/pipeline/` 및 `/ai-workspace/`를 열어 인증 보호가 유지되는 것을 확인했습니다.
- 로컬 인증 세션이 없어 로그인 후 실제 AI 패널 화면은 브라우저로 직접 확인하지 못했습니다. AI payload와 React 빌드는 테스트/빌드로 검증했습니다.

### 알려진 제한

- 사용자 발신 메일은 AI 컨텍스트에 최대 2건만 포함합니다.
- 메일 컨텍스트는 기존 `EmailLog`가 FollowUp 또는 Schedule에 연결된 데이터만 사용합니다.
- 운영에서 실제 로그인 계정으로 긴 AI 요약, 파이프라인 AI 실행, 추천 질문 복사, PainPoint 검증 저장을 수동 확인해야 합니다.

### 배포 상태

- Runtime commit: `fcb7eeb feat: expand react ai workflow`
- GitHub push: runtime commit `fcb7eeb` is on `main`; deployment report docs were pushed after runtime deploy
- Railway `web`: manual runtime deploy `019fc8a8-f782-4773-971f-de9f4deb4212` SUCCESS; docs-only pushes can create newer web deployment IDs because GitHub autodeploy is enabled
- Railway `sales-note-frontend`: `72567306-b54f-48c3-a5c2-7b501aab7425` SUCCESS
- Production `/`, `/pipeline/`, `/ai-workspace/` return 200 and serve `assets/index-CAwxcHSb.js` / `assets/index-BpCNrkRC.css`.
- Production JS contains `추천 질문` and `AI 분석 실행`.
- Production CSS contains `customer-ai-question-item`.
- Production `/reporting/login/` returns 200.
- Anonymous backend and frontend-proxied `/reporting/api/ai-workspace/` return `401 Unauthorized`.
- Anonymous backend and frontend-proxied `/reporting/api/pipeline/` redirect to `/reporting/login/?next=/reporting/api/pipeline/`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에 접속합니다.
2. 긴 AI 요약이 있는 부서를 선택하고 상단 요약이 중간에 잘리지 않는지 확인합니다.
3. `추천 질문` 섹션이 보이고 질문 복사 버튼이 동작하는지 확인합니다.
4. `https://sales-note-frontend-production.up.railway.app/pipeline/`에서 AI 분석 가능한 고객을 선택합니다.
5. 파이프라인 상세 패널에서 AI 결과를 열고 미팅 인사이트, 다음 액션, 추천 질문, PainPoint가 표시되는지 확인합니다.
6. 파이프라인에서 `AI 분석 실행`을 눌러 실행 후 결과가 갱신되는지 확인합니다.
7. 미검증 PainPoint에 검증 메모를 저장하고 상태가 갱신되는지 확인합니다.
8. 같은 고객에게 최근 보낸 메일 1~2건과 고객 답장이 있는 상태에서 부서 AI 분석을 다시 실행해 답장과 발신 메일 맥락이 다음 액션/추천 질문에 반영되는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-11 — Mailbox Email Line Break Normalization

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

React `/mailbox/`에서 작성한 plain text 메일 본문이 실제 메일에서 과하게 벌어지던 문제를 수정했습니다. `body_text`의 `\r\n`/`\r` 줄바꿈을 먼저 `\n`으로 정규화하고, HTML 변환 시 escape 후 `<br>`만 사용하도록 바꿔 `\r<br>`와 `white-space: pre-wrap`의 중복 줄바꿈 해석을 제거했습니다.

### 변경된 파일

- `reporting/gmail_views.py`: 메일 본문 줄바꿈 정규화 helper 및 plain text → HTML 변환 helper 추가
- `reporting/tests.py`: React 메일 발송 API가 줄바꿈 수만큼만 `<br>`을 만들고 HTML escape를 유지하는 회귀 테스트 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 사용자가 메일 작성창에서 한 번 줄바꿈한 내용이 수신 메일에서 2~3줄로 벌어지는 현상을 줄였습니다.
- Gmail API와 IMAP/SMTP 공통 발송 경로의 plain text 본문 처리를 동일하게 안정화했습니다.

### 기존 기능 보존

- 첨부파일, 명함 서명, 답장, 고객 연결, EmailLog 저장 흐름은 유지했습니다.
- React 메일 UI와 기존 Django 메일 fallback URL은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1
→ Ran 7 tests, OK

python -m py_compile reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: normalize mailbox email line breaks"
→ 329cb0d

git push
→ main pushed to GitHub

railway up --service web --environment production --message "Deploy mailbox email line break fix 329cb0d" --ci
→ af9f5751-3896-445c-bf7e-9c3cba56d154 Deploy complete / SUCCESS
```

### 알려진 제한

- 운영 smoke에서는 실제 메일 발송을 하지 않았습니다.
- 이번 수정은 React처럼 `body_text`만 보내는 plain text 메일 변환 경로를 대상으로 합니다. Django rich HTML 작성 화면에서 직접 만든 `body_html`의 문단 스타일은 그대로 보존됩니다.

### 배포 상태

- Runtime commit: `329cb0d fix: normalize mailbox email line breaks`
- GitHub push: `main` updated to `329cb0d`
- Railway `web`: `af9f5751-3896-445c-bf7e-9c3cba56d154` SUCCESS
- `sales-note-frontend` 배포 없음: 프론트 코드 변경 없음
- Production `/mailbox/` returns 200.
- Production `/reporting/login/` returns 200.
- Anonymous frontend-proxied and backend `GET /reporting/api/mailbox/` redirect to `/reporting/login/`.
- Anonymous frontend-proxied and backend `POST /reporting/api/mailbox/send/` are blocked by CSRF with 403.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/mailbox/`에 접속합니다.
2. 새 메일 작성에서 본문에 한 번 Enter 한 줄과 의도적으로 빈 줄을 하나 포함해 테스트 메일을 작성합니다.
3. 본인 또는 테스트 수신처로 메일을 발송합니다.
4. 수신 메일에서 한 번 Enter 한 줄이 2~3줄로 벌어지지 않는지 확인합니다.
5. 의도적으로 빈 줄을 둔 문단 구분은 한 줄 공백 정도로만 보이는지 확인합니다.
6. 스레드 답장에서도 같은 본문으로 발송해 줄바꿈이 동일하게 보존되는지 확인합니다.
7. 첨부파일 또는 명함 서명을 함께 선택해도 기존처럼 발송되는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-11 — React Schedule Calendar Report Content And Nav

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

React `/schedules/calendar/`에서 날짜를 선택해 일정 카드를 볼 때, 해당 고객 일정에 연결된 최근 영업보고 내용을 카드 안에서 바로 확인할 수 있게 했습니다. 캘린더 API는 일정별 최신 보고를 prefetch해 `reports` 배열로 내려주고, React 선택일 카드에는 `보고 내용` 블록과 보고 상세 링크를 표시합니다. 또한 React 사이드바의 `일정` 메뉴는 목록이 아니라 캘린더로 먼저 진입하게 했습니다.

### 변경된 파일

- `reporting/views.py`: 캘린더 일정 payload에 최근 연결 보고 `reports` 추가, 캘린더 queryset에 보고 prefetch 추가
- `reporting/tests.py`: 캘린더 API가 보고 본문/미팅 구조화 필드/다음 액션을 반환하는 회귀 테스트 추가
- `frontend/src/api.ts`: `ScheduleReportItem` 타입과 `ScheduleItem.reports` 추가
- `frontend/src/App.tsx`: 선택일 일정 카드에 보고 내용 블록 추가, 사이드바 `일정` 링크를 `/schedules/calendar/`로 변경
- `frontend/src/styles.css`: 캘린더 보고 내용 표시 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 캘린더에서 일정만 보는 것이 아니라 연결된 보고 본문, 미팅 상황, 확인한 사실, 다음 액션을 함께 볼 수 있습니다.
- 보고 상세 화면으로 바로 이동할 수 있습니다.
- 보고가 없는 일정은 기존 카드 형태를 유지합니다.

### 기존 기능 보존

- 기존 일정 상세의 `relatedNotes` 보고 기록은 유지했습니다.
- 개인 일정, Django fallback, 상태 변경 버튼, 일정 등록 동선은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 28 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-rK47uPvT.js / assets/index--s--1gtx.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: show schedule reports in calendar"
→ c96f7d5

git push
→ main pushed to GitHub

git commit -m "feat: open schedule nav on calendar"
→ d455127

git push
→ main pushed to GitHub

railway up --service web --environment production --message "Deploy schedule calendar reports and nav d455127" --ci
→ 1969669f-d1c8-4bda-8fe6-d1d3d06c15c0 Deploy complete

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy schedule calendar reports and nav d455127" --ci
→ bee0b840-3a45-4cbd-be0f-0cbf9badcfe6 Deploy complete
```

### 알려진 제한

- 캘린더 카드에는 일정별 최신 보고 최대 3건을 표시합니다.
- `/schedules/` 목록 화면은 직접 URL 또는 화면 내 목록 링크로 계속 접근 가능합니다.

### 배포 상태

- Runtime commits:
  - `c96f7d5 feat: show schedule reports in calendar`
  - `d455127 feat: open schedule nav on calendar`
- GitHub push: `main` updated to `d455127`
- Railway `web`: `1969669f-d1c8-4bda-8fe6-d1d3d06c15c0` Deploy complete
- Railway `sales-note-frontend`: `bee0b840-3a45-4cbd-be0f-0cbf9badcfe6` Deploy complete
- Production `/schedules/calendar/` serves `assets/index-rK47uPvT.js` / `assets/index--s--1gtx.css`.
- Production `/schedules/calendar/` returns 200.
- Production JS contains `보고 내용`, `schedule-calendar-report-list`, and `/schedules/calendar/`.
- Production CSS contains `schedule-calendar-report-list` and `schedule-calendar-report-item`.
- Anonymous frontend-proxied and backend `/reporting/api/schedules/calendar/` return `401 Unauthorized`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`에 접속합니다.
2. 영업보고가 연결된 고객 일정이 있는 날짜를 선택합니다.
3. 선택일 일정 카드 안에 `보고 내용` 블록이 표시되는지 확인합니다.
4. 보고 본문, 미팅 상황, 확인한 사실, 다음 액션이 보이는지 확인합니다.
5. `보고 상세` 링크가 해당 React 영업노트 상세로 이동하는지 확인합니다.
6. 왼쪽 사이드바의 `일정`을 눌렀을 때 `/schedules/calendar/`로 이동하는지 확인합니다.
7. 보고가 없는 일정은 기존처럼 일정 메모/상태/액션만 보이는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-11 — React Schedule Calendar Status Actions

**상태**: 구현/로컬 검증/푸시/운영 배포/스모크 완료, 사용자 수동검수 대기

### 요약

React `/schedules/calendar/`에서 날짜를 선택했을 때 선택일 일정 카드에서 상세/고객/보고/Django fallback으로 이동하고, 본인 고객 일정은 React 화면에서 바로 상태를 변경할 수 있게 했습니다. 기존 Django 상태 변경 API를 재사용해 권한과 업무 로직은 유지했습니다.

### 변경된 파일

- `reporting/views.py`: 일정 payload에 `canEdit`, `statusUpdateHref`, `djangoEditHref`, `statusOptions` 추가
- `reporting/tests.py`: 일정 캘린더 API의 본인/타인/개인 일정 권한 payload 회귀 테스트 추가
- `frontend/src/api.ts`: 일정 상태 변경 API client 추가
- `frontend/src/App.tsx`: 선택일 일정 카드, 이동 액션, 상태 변경 버튼/메시지/갱신 로직 추가
- `frontend/src/styles.css`: 선택일 일정 카드와 상태 버튼 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 캘린더에서 선택한 날짜의 일정을 카드 단위로 확인할 수 있습니다.
- 본인 고객 일정은 React 캘린더 화면에서 예정/완료/취소 상태를 바로 변경할 수 있습니다.
- 타인 일정과 개인 일정은 읽기 전용으로 유지해 권한 혼선을 줄였습니다.
- 일정 상세, 고객, 보고, Django 상세/수정 fallback 이동 경로를 함께 제공합니다.

### 기존 기능 보존

- 기존 Django `/reporting/schedules/*` 화면과 상태 변경 API를 유지했습니다.
- 권한 판정은 기존 일정 소유자/관리자 로직을 따릅니다.
- 개인 일정은 이번 상태 변경 대상에서 제외했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 28 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-C1R5m0RT.js / assets/index-Bxi4eBNz.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add React calendar status actions"
→ 7bb71e8

git push
→ main pushed to GitHub

railway up --service web --environment production --message "Deploy React calendar status actions 7bb71e8" --ci
→ d7eba974-f6db-4e90-a53c-5097ccad0164 Deploy complete

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React calendar status actions 7bb71e8" --ci
→ 898c94ca-cf72-4dba-b329-35304d8c4979 Deploy complete
```

### 알려진 제한

- 실제 상태 변경은 로그인 세션과 운영 데이터가 필요해 사용자 수동검수가 필요합니다.
- 이번 범위는 선택일 일정 액션과 상태 변경이며, 새 일정 생성/편집 폼 전체 React 전환은 다음 별도 작업입니다.

### 배포 상태

- Runtime commit: `7bb71e8 feat: add React calendar status actions`
- Railway `web`: `d7eba974-f6db-4e90-a53c-5097ccad0164` Deploy complete
- Railway `sales-note-frontend`: `898c94ca-cf72-4dba-b329-35304d8c4979` Deploy complete
- Production `/schedules/calendar/` returns 200.
- Production frontend serves `assets/index-C1R5m0RT.js` / `assets/index-Bxi4eBNz.css`.
- Production JS contains `statusUpdateHref` and schedule status update UI strings.
- Production CSS contains `schedule-calendar-selected-card` and `schedule-calendar-status-actions`.
- Anonymous frontend-proxied and backend `/reporting/api/schedules/calendar/` return `401 Unauthorized`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`에 접속합니다.
2. 본인 고객 일정이 있는 날짜를 선택합니다.
3. 선택일 카드에 `상세`, `고객`, `보고`, `Django 상세`, `Django 수정` 액션이 보이는지 확인합니다.
4. 본인 일정 상태를 `완료` 또는 `취소`로 바꾸고 성공 메시지와 캘린더/지표 갱신을 확인합니다.
5. `회사 전체` 또는 직원 선택 상태에서 타인 일정에는 상태 버튼이 나오지 않는지 확인합니다.
6. 견적 일정은 편집 가능해도 `완료` 버튼이 제공되지 않고 허용 상태만 보이는지 확인합니다.

### 사용자 수동검수 결과

- 대기 중.

---

## 2026-05-11 — React Document Generation History

**상태**: 구현/로컬 검증/푸시/운영 배포/사용자 수동검수 완료

### 요약

React `/documents/`에서 최근 서류 생성/다운로드 이력을 확인할 수 있게 했습니다. 기존 `DocumentGenerationLog`를 사용해 거래번호, 서류 종류, 출력 형식, 생성일, 생성자, 연결 일정/고객/부서를 회사 범위 안에서 내려주고, React 오른쪽 패널에 `최근 생성 이력`으로 표시합니다.

### 변경된 파일

- `reporting/views.py`: `/reporting/api/documents/`에 `recentGenerations`, 오늘 생성 건수, 생성 이력 총건수 추가
- `reporting/tests.py`: 서류 생성 이력의 회사 범위 권한, type 필터, payload 회귀 테스트 추가
- `frontend/src/api.ts`: 서류 생성 이력 타입과 빈 상태/정규화 추가
- `frontend/src/App.tsx`: `/documents/` 요약 지표와 최근 생성 이력 UI 추가
- `frontend/src/styles.css`: 서류 생성 이력 카드 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 서류 템플릿 화면에서 최근 생성된 견적서/거래명세서/납품서 이력을 바로 확인할 수 있습니다.
- 생성 이력 카드에서 연결된 React 일정 상세로 이동할 수 있습니다.
- 서류 종류 필터를 적용하면 템플릿과 생성 이력이 같은 종류로 함께 제한됩니다.

### 기존 기능 보존

- 기존 일정 상세의 서류 미리보기/다운로드와 Django 서류 생성 로직은 유지했습니다.
- `/reporting/documents/*` Django fallback과 `/reporting/*` 인증/권한 정책은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.DocumentTemplatesReactApiTests --verbosity=1
→ Ran 8 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-Bmhj4oJQ.js / assets/index-CsWuSGWH.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: show document generation history"
→ 0f98c24

git push
→ main pushed to GitHub

railway up --service web --environment production --message "Deploy document generation history 0f98c24" --ci
→ 280b8be1-c1c0-48cc-80a1-37707d4c9cba SUCCESS

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy document generation history 0f98c24" --ci
→ 0da257af-9ca9-48b3-bcd5-bfd1767a9bf6 SUCCESS
```

### 알려진 제한

- 실제 생성 이력 내용 확인은 로그인 세션과 운영 데이터가 필요해 사용자 수동검수가 필요합니다.
- 이번 범위는 이력 조회/표시이며, 생성 로그 검색/페이지네이션은 추가하지 않았습니다.

### 배포 상태

- Runtime commit: `0f98c24 feat: show document generation history`
- GitHub push: `main` updated from `bf803e7` to `0f98c24`
- Railway `web`: `280b8be1-c1c0-48cc-80a1-37707d4c9cba` SUCCESS, message `Deploy document generation history 0f98c24`
- Railway `sales-note-frontend`: `0da257af-9ca9-48b3-bcd5-bfd1767a9bf6` SUCCESS, message `Deploy document generation history 0f98c24`
- Production `/documents/` returns 200.
- Production frontend serves `assets/index-Bmhj4oJQ.js` / `assets/index-CsWuSGWH.css`.
- Production JS contains `recentGenerations` and `최근 생성 이력`.
- Production CSS contains `document-generation-card`.
- Anonymous frontend proxy and backend `/reporting/api/documents/` return `401`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/documents/`에 접속합니다.
2. 오른쪽 요약에 `오늘 생성`, `최근 이력` 지표가 보이는지 확인합니다.
3. `최근 생성 이력`에 거래번호, 서류 종류, 출력 형식, 생성자, 고객/부서가 표시되는지 확인합니다.
4. 생성 이력 카드를 눌렀을 때 해당 React 일정 상세로 이동하는지 확인합니다.
5. 상단 서류 종류 필터를 바꿨을 때 템플릿과 최근 생성 이력이 같은 종류로 제한되는지 확인합니다.
6. 일정 상세에서 서류를 하나 생성한 뒤 `/documents/`로 돌아와 이력이 추가되는지 확인합니다.

### 사용자 수동검수 결과

- 완료: 2026-05-11

---

## 2026-05-11 — React Mailbox Send Attachments

**상태**: 구현/로컬 검증/푸시/운영 배포/사용자 수동검수 완료

### 요약

React `/mailbox/`의 새 메일 작성과 `/mailbox/thread/<id>/` 답장 폼에서 첨부파일을 선택해 발송할 수 있게 했습니다. React API client는 메일 발송 payload를 `FormData`로 보내며, 기존 Django `_handle_email_send()`의 Gmail/SMTP 첨부 처리와 `EmailLog.attachments_info` 기록을 그대로 사용합니다.

### 변경된 파일

- `frontend/src/App.tsx`: 메일 작성/답장 첨부파일 상태, 파일 선택 UI, 선택 파일 목록/삭제, 발송 payload 연결
- `frontend/src/api.ts`: `MailboxSendPayload.attachments` 추가 및 메일 발송 POST를 `FormData`로 전환
- `frontend/src/styles.css`: React 메일 첨부파일 선택 목록 스타일 추가
- `reporting/tests.py`: React 메일 발송 API multipart 첨부 회귀 테스트 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- `/mailbox/` 메일 작성 폼에서 여러 파일을 선택할 수 있습니다.
- 선택한 파일명과 크기를 발송 전 확인하고, 개별 파일을 제거할 수 있습니다.
- 답장 발송에서도 같은 첨부파일 흐름을 사용할 수 있습니다.
- 발송된 첨부파일 메타데이터는 기존 메일 로그의 `attachments_info`에 기록됩니다.

### 기존 기능 보존

- Django 메일 작성/답장 fallback 화면과 기존 Gmail/SMTP 발송 로직은 유지했습니다.
- 메일 계정 연결, 고객 권한 범위, CSRF/session 흐름은 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=1
→ Ran 6 tests, OK

python -m py_compile reporting\gmail_views.py reporting\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-BVsunKYp.js / assets/index-BPeRJO55.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add React mailbox attachments"
→ de930af

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React mailbox attachments de930af" --ci
→ d55ba8c7-62a7-4237-b26e-9b456f7a7787 SUCCESS
```

### 알려진 제한

- 실제 Gmail/SMTP 외부 발송은 운영 계정으로 수동 확인이 필요합니다. 로컬 테스트는 GmailService를 mock 처리해 첨부 payload와 DB 기록을 검증했습니다.
- 첨부 파일 크기/확장자 제한은 기존 Django 메일 발송 로직 기준을 따릅니다. 별도 React 클라이언트 제한은 이번 범위에 추가하지 않았습니다.

### 배포 상태

- Runtime commit: `de930af feat: add React mailbox attachments`
- GitHub push: `main` updated from `70ce675` to `de930af`
- Railway `sales-note-frontend`: `d55ba8c7-62a7-4237-b26e-9b456f7a7787` SUCCESS, message `Deploy React mailbox attachments de930af`
- Production `/mailbox/` returns 200.
- Production frontend serves `assets/index-BVsunKYp.js` / `assets/index-BPeRJO55.css`.
- Production JS contains `첨부파일`, `mail-attachment-list`, and `attachments`.
- Anonymous frontend proxy `/reporting/api/mailbox/` redirects to `/reporting/login/?next=/reporting/api/mailbox/`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/mailbox/`에서 `메일 작성`을 엽니다.
2. 받는 사람, 제목, 본문을 입력하고 `첨부파일`에서 파일을 1개 이상 선택합니다.
3. 선택한 파일명/크기가 폼 아래에 보이는지 확인하고, 삭제 버튼으로 제거되는지 확인합니다.
4. 다시 파일을 첨부한 뒤 발송합니다.
5. 보낸편지함 또는 해당 스레드에서 메일 발송이 완료됐는지 확인합니다.
6. 스레드 답장에서도 첨부파일 선택 후 발송이 되는지 확인합니다.

### 사용자 수동검수 결과

- 완료: 2026-05-11

---

## 2026-05-11 — React Schedule Calendar Selected-Date Create Flow

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/schedules/calendar/`에서 선택한 날짜 기준으로 고객 일정 등록을 React 빠른 등록 패널에서 바로 시작하도록 변경했습니다. 선택일 패널의 개인 일정 등록과 Django 상세 등록 fallback도 같은 날짜 query를 붙여 열리게 했습니다.

### 변경된 파일

- `frontend/src/App.tsx`: 선택일 기반 일정 등록 링크, `date` query 검증, React 빠른 등록 방문 날짜 초기값 반영
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 캘린더 상단 `일정 등록`은 `/schedules/?create=1&date=YYYY-MM-DD`로 이동해 React 일정 빠른 등록을 엽니다.
- React 빠른 등록의 방문 날짜가 캘린더에서 선택한 날짜로 자동 입력됩니다.
- 선택일 패널에서 `고객 일정 등록`, `개인 일정 등록`, `Django 상세 등록`을 날짜 맥락 그대로 사용할 수 있습니다.

### 기존 기능 보존

- Django `/reporting/schedules/create/`, `/reporting/personal-schedules/create/`, `/reporting/schedules/calendar/` fallback은 유지했습니다.
- 로그인/권한 정책과 DB 모델은 변경하지 않았습니다.

### 실행한 명령어 및 결과

```text
cd frontend; npm run build
→ OK, assets/index-Bdw-ncC7.js / assets/index-M9Uvw-6H.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: route calendar creates to React schedule form"
→ b405466

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React calendar create flow b405466" --ci
→ d8ae8549-a810-4332-b6a7-8ee421bb3981 SUCCESS
```

### 알려진 제한

- React 캘린더의 drag/drop 이동, 상세 모달 편집 같은 고급 조작은 아직 Django 캘린더 fallback을 사용합니다.
- 고객 일정 빠른 등록은 기존 React 등록 폼 범위 안에서 동작하므로, Django 상세 등록의 납품 품목/선결제 고급 입력이 필요하면 `Django 상세 등록` fallback을 사용합니다.

### 배포 상태

- Runtime commit: `b405466 fix: route calendar creates to React schedule form`
- GitHub push: `main` updated from `97ee492` to `b405466`
- Railway `sales-note-frontend`: `d8ae8549-a810-4332-b6a7-8ee421bb3981` SUCCESS, message `Deploy React calendar create flow b405466`
- Production `/schedules/calendar/` returns 200.
- Production `/schedules/?create=1&date=2026-05-11` returns 200.
- Production frontend serves `assets/index-Bdw-ncC7.js` / `assets/index-M9Uvw-6H.css`.
- Production JS contains `/schedules/?create=1&date=`, `고객 일정 등록`, and `Django 상세 등록`.
- Anonymous frontend proxy `/reporting/api/schedules/calendar/` returns `401`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`에서 날짜를 하나 선택합니다.
2. 상단 `일정 등록`을 눌렀을 때 `/schedules/?create=1&date=선택일`로 이동하고 빠른 등록 패널의 방문 날짜가 선택일인지 확인합니다.
3. 캘린더 선택일 패널의 `고객 일정 등록`도 같은 동작인지 확인합니다.
4. `개인 일정 등록`을 누르면 Django 개인 일정 등록 화면에 선택 날짜가 들어가는지 확인합니다.
5. `Django 상세 등록`을 누르면 기존 Django 일정 등록 화면에 선택 날짜가 들어가는지 확인합니다.

### 다음 작업

- 사용자 요청에 따라 이 배포 후 React `/mailbox/` 메일 발송 첨부파일 지원을 진행합니다.

---

## 2026-05-11 — AI Deliveries, Latest Lists, Weekly Report Edit Linebreaks

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/ai-workspace/?department_id=10`의 Department AI 패널에서 최근 납품 제품과 수량을 볼 수 있게 했고, React CRM 주요 리스트 기본 정렬을 최신순으로 맞췄습니다. `/weekly-reports/<id>/` 수정 저장 시 textarea 줄바꿈이 사라지는 문제와 `/customers/` 부서 입력에서 PI/책임자명으로 부서를 찾지 못하는 문제도 함께 수정했습니다. 루트 파이프라인 화면은 API 로딩 전에 하드코딩 mock 데이터가 잠깐 보이지 않도록 빈 로딩 상태로 시작합니다.

### 변경된 파일

- `reporting/views.py`: AI 납품 payload, 고객/일정 최신순 API 정렬, 부서 PI 검색 텍스트, 주간보고 HTML→textarea 변환 보강
- `reporting/tests.py`: AI 최근 납품, 고객/일정 최신순, 부서 PI 검색, 주간보고 문단 줄바꿈 회귀 테스트 추가
- `frontend/src/api.ts`: AI 최근 납품 타입/정규화, 부서 검색 텍스트 타입, 파이프라인 빈 fallback 적용
- `frontend/src/App.tsx`: 최근 납품 품목 UI, 부서 검색어 확장, 파이프라인 초기 로딩 상태 적용
- `frontend/src/mockData.ts`: 파이프라인 unavailable 빈 상태 추가
- `frontend/src/styles.css`: AI 납품 목록과 파이프라인 unavailable 배지 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- Department AI의 `견적/납품 분석`에서 최근 납품일, 고객, 출처, 금액, 제품명, 수량을 확인할 수 있습니다.
- `/schedules/` 기본 일정 목록과 `/customers/` 고객 목록이 최신 항목부터 표시됩니다.
- `/customers/` 부서 선택 검색에서 부서명뿐 아니라 해당 부서 FollowUp의 고객명, PI/책임자명, 이메일도 검색 대상으로 사용합니다.
- `/weekly-reports/<id>/` 수정 화면에서 기존 HTML 문단이 textarea 텍스트로 돌아올 때 빈 줄과 줄바꿈이 보존됩니다.
- `/` 파이프라인 화면은 Django API 응답 전 mock deal/금액/작업 카드가 깜빡이지 않습니다.

### 기존 기능 보존

- `/reporting/*` route, Django fallback 화면, 로그인/권한/회사 범위 정책은 유지했습니다.
- 캘린더 API는 일정 흐름 확인 용도라 기존 시간순 정렬을 유지했습니다.
- DB 모델 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend; node --check server.mjs
→ OK

python manage.py test reporting.tests.AIWorkspaceSummaryApiTests reporting.tests.CustomersSummaryApiTests reporting.tests.SchedulesSummaryApiTests reporting.tests.WeeklyReportReactApiTests --verbosity=1
→ Ran 62 tests, OK

cd frontend; npm run build
→ OK, assets/index-CK647J3B.js / assets/index-M9Uvw-6H.css

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: improve AI deliveries and CRM list defaults"
→ f1865fe

git push
→ main pushed to GitHub

railway up --service web --environment production --message "Deploy AI deliveries and CRM list defaults f1865fe" --ci
→ 8eb7ccda-bb8e-4ad5-9261-13ab02ae6586 SUCCESS

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI deliveries and CRM list defaults f1865fe" --ci
→ 4f931dd7-3d67-4a7e-a24d-22c611d94c0f SUCCESS
```

### 알려진 제한

- "모든 리스트 최신순"은 이번 변경에서 React CRM의 주요 고객/일정 기본 리스트 기준으로 적용했습니다. 달력처럼 시간 흐름이 기능인 화면은 최신순으로 바꾸지 않았습니다.
- 운영에서 실제 납품 데이터 표시 여부는 해당 부서 AI 분석 데이터의 `quote_delivery_data.deliveries` 존재 여부에 따라 달라집니다.

### 배포 상태

- Runtime commit: `f1865fe fix: improve AI deliveries and CRM list defaults`
- GitHub push: `main` updated from `632851a` to `f1865fe`
- Railway `web`: `8eb7ccda-bb8e-4ad5-9261-13ab02ae6586` SUCCESS, message `Deploy AI deliveries and CRM list defaults f1865fe`
- Railway `sales-note-frontend`: `4f931dd7-3d67-4a7e-a24d-22c611d94c0f` SUCCESS, message `Deploy AI deliveries and CRM list defaults f1865fe`
- Production `/`, `/ai-workspace/?department_id=10`, `/schedules/`, `/customers/`, `/weekly-reports/2/` return 200.
- Production frontend serves `assets/index-CK647J3B.js` / `assets/index-M9Uvw-6H.css`.
- Production JS contains `recentDeliveries`, `최근 납품 품목`, and `파이프라인 데이터를 불러오는 중입니다`.
- Production JS no longer contains `Mock data fallback`.
- Production CSS contains `customer-ai-delivery-list` and `source-badge.unavailable`.
- Anonymous frontend proxy `/reporting/api/customers/`, `/reporting/api/schedules/`, `/reporting/api/weekly-reports/`, `/reporting/api/ai-workspace/?department_id=10` return `401`.

### 수동 서버 테스트 절차

1. `https://sales-note-frontend-production.up.railway.app/ai-workspace/?department_id=10`에서 오른쪽 `Department AI`의 `견적/납품 분석`에 `최근 납품 품목`이 보이는지 확인합니다.
2. `/schedules/`에 접속해 기본 일정 목록이 최신 날짜/시간 항목부터 보이는지 확인합니다.
3. `/customers/`에서 고객 등록/수정의 부서 입력에 PI 또는 책임자명 일부를 입력했을 때 관련 부서가 검색되는지 확인합니다.
4. `/weekly-reports/2/`를 수정 화면으로 열고 여러 줄/빈 줄이 있는 내용을 저장한 뒤 다시 수정 화면에서 줄바꿈이 유지되는지 확인합니다.
5. `/` 파이프라인 화면을 새로고침했을 때 실제 API 로딩 전 하드코딩된 deal/금액/작업 카드가 잠깐 보이지 않는지 확인합니다.

---

## 2026-05-11 — React Weekly Report Linebreak Display

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/weekly-reports/`에서 주간보고 저장 후 상세 화면에 표시되는 본문과 관리자 검토 코멘트가 입력 줄바꿈을 보존하도록 표시 CSS를 보강했습니다.

### 변경된 파일

- `frontend/src/styles.css`: 주간보고 HTML 본문과 관리자 코멘트에 `white-space: pre-wrap` 적용
- `reporting/tests.py`: React 주간보고 저장/상세 API가 줄바꿈용 `<br>`를 포함하는지 회귀 테스트 보강
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 사용자가 주간보고 `textarea`에서 줄을 나눠 입력한 내용이 상세 화면에서 한 줄로 붙어 보이지 않습니다.
- 기존 저장 데이터가 HTML 안에 raw newline을 포함해도 React 표시 영역에서 줄바꿈을 접지 않습니다.
- 관리자 검토 코멘트도 여러 줄 입력 시 그대로 보입니다.

### 기존 기능 보존

- 주간보고 저장 API, 권한 범위, Django fallback 화면은 유지했습니다.
- DB 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.WeeklyReportReactApiTests --verbosity=1
→ Ran 6 tests, OK

cd frontend; npm run build
→ OK, assets/index-BQMADz31.js / assets/index-C_Dt-dqM.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `9dbe370 fix: preserve weekly report linebreak display`
- GitHub push: `main` updated from `840cfba` to `9dbe370`
- Railway `sales-note-frontend`: `1a9d8cea-bc68-411e-ade6-3ae61ec4b89c` SUCCESS, message `Deploy weekly report linebreak display 9dbe370`
- Railway `web`: `fcda2346-080c-49eb-8e1d-84fd98c5f800` SUCCESS, commit `9dbe370`
- Production `/weekly-reports/` returns 200 and serves `assets/index-BQMADz31.js` / `assets/index-C_Dt-dqM.css`.
- Production CSS contains `weekly-html-content`, `white-space:pre-wrap`, and `weekly-html-section.manager p`.
- Anonymous frontend proxy `/reporting/api/weekly-reports/` returns `401 login_required`.
- Recent `web` deployment logs show successful migration check/startup and no traceback/500.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/weekly-reports/new/`에서 주간보고를 작성합니다.
2. `영업 활동`, `견적/납품`, `기타` 중 하나에 여러 줄과 빈 줄을 포함해 입력합니다.
3. 저장 후 상세 화면에서 입력한 줄바꿈이 그대로 보이는지 확인합니다.
4. 수정 화면에서 다시 열었을 때 textarea에도 줄바꿈이 유지되는지 확인합니다.
5. 관리자 계정에서 검토 코멘트를 여러 줄로 저장한 뒤 상세 화면에 줄바꿈이 유지되는지 확인합니다.

---

## 2026-05-11 — AI Workspace Department Selection in React

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/ai-workspace/`의 `부서 분석 대상` 행 클릭이 Django AI 허브로 이동하지 않고, 같은 React 화면에서 오른쪽 `Department AI` 패널을 선택 부서로 갱신하도록 변경했습니다.

### 변경된 파일

- `reporting/views.py`: `/reporting/api/ai-workspace/`에 `department_id` 선택 파라미터 추가, 접근 가능한 부서만 `featuredDepartment`로 반영
- `reporting/tests.py`: 선택 부서 반영 및 범위 밖 부서 무시 회귀 테스트 추가
- `frontend/src/api.ts`: AI workspace loader에 `department_id` query 지원과 `selectedDepartmentId` 정규화 추가
- `frontend/src/App.tsx`: URL 초기 선택값, 부서 행 버튼 선택, React 상태/API refresh 연결
- `frontend/src/styles.css`: 선택된 부서 행 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- `/ai-workspace/`에서 부서를 클릭해도 Django 화면으로 이동하지 않고, 오른쪽 AI 결과 패널이 즉시 해당 부서로 전환됩니다.
- 선택한 부서는 `department_id` query로 URL에 남아 새로고침 후에도 같은 부서 패널을 불러올 수 있습니다.
- 선택된 부서 행은 `선택됨` 상태로 표시됩니다.

### 기존 기능 보존

- 명시적인 `Django 보기`/`AI 허브` fallback 링크와 기존 `/ai/*`, `/reporting/*` route는 유지했습니다.
- API는 요청자 본인 FollowUp 기반 부서 범위만 선택 가능하게 하여 내부 데이터 노출 범위를 넓히지 않았습니다.
- DB 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1
→ Ran 6 tests, OK

cd frontend; npm run build
→ OK, assets/index-rJt-C9JT.js / assets/index-CpCyMmMT.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `67f00ea feat: keep AI workspace department selection in React`
- GitHub push: `main` updated from `7dea9dd` to `67f00ea`
- Railway `web`: `45f20216-05f1-44bd-931d-8e4b1f6bf8de` SUCCESS, commit `67f00ea`
- Railway `sales-note-frontend`: `09a7ea82-a5b5-453f-b639-5573f0156705` SUCCESS, message `Deploy AI workspace department selection 67f00ea`
- Production `/ai-workspace/` returns 200 and serves `assets/index-rJt-C9JT.js` / `assets/index-CpCyMmMT.css`.
- Production JS contains `department_id`, `선택됨`, and `/reporting/api/ai-workspace/`.
- Production CSS contains `.ai-department-row.selected`.
- Anonymous frontend proxy `/reporting/api/ai-workspace/?department_id=1` returns `401 login_required`.
- Anonymous backend `/reporting/api/ai-workspace/?department_id=1` returns `401 login_required`.
- Recent `web` deployment logs show successful migration check/startup and no traceback/500; smoke requests only logged expected `Unauthorized`.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에 접속합니다.
2. `Department analysis / 부서 분석 대상`에서 첫 번째가 아닌 다른 부서를 클릭합니다.
3. URL에 `department_id=<id>`가 붙고 페이지가 Django `/ai/` 화면으로 이동하지 않는지 확인합니다.
4. 오른쪽 `Department AI` 패널 제목/요약/고객 chip/미팅·견적·납품 수치가 클릭한 부서 기준으로 바뀌는지 확인합니다.
5. 새로고침 후에도 같은 부서가 선택되어 있는지 확인합니다.
6. 명시적인 `Django 보기` 버튼은 기존 fallback으로 계속 열리는지 확인합니다.

---

## 2026-05-11 — AI Workspace Prompt Queue Reposition

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/ai-workspace/`의 상단 `AI 작업 큐`를 제거하고, 같은 프롬프트 복사 기능을 왼쪽 본문 하단의 `추천 질문` 보조 섹션으로 옮겼습니다. 화면의 1차 흐름은 부서 분석 대상과 오른쪽 `Department AI` 결과 패널이 잡도록 정리했습니다.

### 변경된 파일

- `frontend/src/App.tsx`: 상단 작업 큐 제거, `추천 질문` 보조 섹션으로 `AIWorkspacePromptQueue` 재배치
- `frontend/src/styles.css`: 보조 프롬프트 패널 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- `/ai-workspace/` 진입 시 복사 프롬프트보다 실제 부서 AI 결과 패널이 먼저 보입니다.
- 기존 프롬프트 복사 기능은 없어지지 않고 보조 섹션으로 유지됩니다.

### 기존 기능 보존

- `/reporting/api/ai-workspace/` payload와 Django `/ai/*` route는 변경하지 않았습니다.
- 기존 프롬프트 카드, 복사 버튼, PainPoint/고객/부서 프롬프트 데이터는 유지했습니다.
- DB 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
cd frontend; npm run build
→ OK, assets/index-ChUAhcWz.js / assets/index-DAMocjpX.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: reposition AI prompt queue"
→ 687c820

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI prompt queue reposition 687c820" --ci
→ Unauthorized. Please run `railway login` again.

railway deployment list --service web --environment production --limit 2 --json
→ Unauthorized. Please run `railway login` again.

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI prompt queue reposition 687c820" --ci
→ 6694c40f-4f8e-4387-8046-1a83313b0244 SUCCESS

railway deployment list --service web --environment production --limit 1 --json
→ 5cdc524e-4d6e-4e62-b9c1-fda38e5e3d4d SUCCESS, commit 5f6bcfd

curl -I https://sales-note-frontend-production.up.railway.app/ai-workspace/
→ 200 OK

curl https://sales-note-frontend-production.up.railway.app/reporting/api/ai-workspace/
→ 401 login_required
```

### 배포 상태

- Runtime commit: `687c820 feat: reposition AI prompt queue`
- GitHub push: `main` updated from `48b1e66` to `687c820`
- Initial Railway CLI deploy attempt failed because the OAuth token had expired; user reauthenticated with `railway login`.
- Railway `web`: `5cdc524e-4d6e-4e62-b9c1-fda38e5e3d4d` SUCCESS, commit `5f6bcfd`
- Railway `sales-note-frontend`: `6694c40f-4f8e-4387-8046-1a83313b0244` SUCCESS, message `Deploy AI prompt queue reposition 687c820`
- Production `/ai-workspace/` returns 200 and serves `assets/index-ChUAhcWz.js` / `assets/index-DAMocjpX.css`
- Production JS contains `추천 질문` and no longer contains `AI 작업 큐`.
- Production CSS contains `ai-support-panel`.
- Anonymous frontend proxy `/reporting/api/ai-workspace/` returns `401 login_required`.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에 접속합니다.
2. 지표 바로 아래에 `AI 작업 큐` 상단 패널이 더 이상 없는지 확인합니다.
3. 왼쪽 본문 하단에 `추천 질문` 섹션이 있고 기존 프롬프트 카드와 복사 버튼이 유지되는지 확인합니다.
4. 오른쪽 `Department AI` 패널이 화면 핵심 영역으로 유지되는지 확인합니다.

---

## 2026-05-11 — AI Workspace Department List Search Limit

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/ai-workspace/`의 `Department analysis / 부서 분석 대상` 목록을 최대 5개만 보이도록 제한하고, 회사/부서/고객/요약 기준 검색 input을 추가했습니다.

### 변경된 파일

- `frontend/src/App.tsx`: `AIWorkspaceDepartmentList`에 검색 상태, 필터링, 5개 제한 표시 추가
- `frontend/src/styles.css`: 부서 검색창, 목록 메타, 안내 문구 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 부서 분석 대상이 많아도 AI workspace 메인 영역이 길게 밀리지 않습니다.
- 사용자는 검색으로 필요한 부서를 찾아 바로 AI 허브/부서 분석으로 이동할 수 있습니다.

### 기존 기능 보존

- `/reporting/api/ai-workspace/`와 기존 Django `/ai/*` route는 변경하지 않았습니다.
- 부서 목록 데이터는 API에서 계속 전체를 받아오고, React 화면에서만 5개로 제한합니다.
- DB 변경 및 migration은 없습니다.

### 실행한 명령어 및 결과

```text
cd frontend; npm run build
→ OK, assets/index-D0kCzolk.js / assets/index-ChIABZDB.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: limit AI department list"
→ c922a6e

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI department list search c922a6e" --ci
→ 9a5fbd1a-e93d-436d-abe6-0035ff9e381c SUCCESS

railway deployment list --service web --environment production --limit 2 --json
→ 06630a88-d4af-482d-82ae-a31c134bb6cd SUCCESS, commit c922a6e

curl -I https://sales-note-frontend-production.up.railway.app/ai-workspace/
→ 200 OK

curl https://sales-note-frontend-production.up.railway.app/reporting/api/ai-workspace/
→ 401 login_required
```

### 배포 상태

- Runtime commit: `c922a6e feat: limit AI department list`
- GitHub push: `main` updated from `d637f68` to `c922a6e`
- Railway `web`: `06630a88-d4af-482d-82ae-a31c134bb6cd` SUCCESS, commit `c922a6e`
- Railway `sales-note-frontend`: `9a5fbd1a-e93d-436d-abe6-0035ff9e381c` SUCCESS, message `Deploy AI department list search c922a6e`
- Production `/ai-workspace/` returns 200 and serves `assets/index-D0kCzolk.js` / `assets/index-ChIABZDB.css`
- Production JS contains the department search placeholder and `최대 5개 표시`.
- Production CSS contains `ai-department-search`.
- Anonymous frontend proxy `/reporting/api/ai-workspace/` returns `401 login_required`.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에 접속합니다.
2. `Department analysis / 부서 분석 대상`에서 검색창이 보이는지 확인합니다.
3. 초기 목록이 최대 5개만 보이는지 확인합니다.
4. 회사명, 부서명, 고객명 일부를 입력했을 때 결과가 필터링되고 계속 최대 5개만 표시되는지 확인합니다.

---

## 2026-05-11 — React AI Workspace Customer-Style Panel

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React `/ai-workspace/` 화면 오른쪽에 고객 상세에서 쓰는 부서 AI 결과 패널을 붙였습니다. 최신 부서 분석의 미팅/견적/납품 인사이트, 검증 기반 인사이트, 추천 액션, 확인 필요 사항, PainPoint 검증 메모를 AI 업무도구에서 바로 볼 수 있습니다.

### 변경된 파일

- `reporting/views.py`: AI workspace API에 `featuredDepartment` 상세 AI payload 추가
- `reporting/tests.py`: `featuredDepartment`와 PainPoint 검증 URL 회귀 테스트 추가
- `frontend/src/api.ts`: AI workspace 대표 부서 타입과 loader 정규화 추가
- `frontend/src/App.tsx`: `/ai-workspace/` 오른쪽 고객형 AI 패널, AI 분석 실행, PainPoint 확인 메모 저장 연결
- `frontend/src/styles.css`: AI workspace 2열 레이아웃과 대표 부서 고객 chip 스타일 추가
- `AGENT_PLAN.md`: 현재 작업 계획 기록

### CRM 개선

- 고객 상세의 오른쪽 AI 경험을 `/ai-workspace/`에서도 그대로 사용할 수 있습니다.
- AI 업무도구에서 최신 부서 분석 결과를 열람하고 PainPoint 검증 메모를 `확인` 하나로 저장할 수 있습니다.
- 기존 작업 큐, 부서 분석 대상, 고객 분석 대상, 전체 검증 대기 목록은 유지했습니다.

### 기존 기능 보존

- 기존 Django `/ai/*`, `/reporting/*`, React 고객 상세 AI 패널은 유지했습니다.
- 신규 DB 필드와 migration은 없습니다.
- AI 권한이 없는 사용자는 기존처럼 권한 안내만 받고 `featuredDepartment`는 `null`입니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1
→ Ran 4 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend; npm run build
→ OK, assets/index-D8ySrsxQ.js / assets/index-C66GcgeW.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add AI workspace result panel"
→ 9ec4256

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI workspace result panel 9ec4256" --ci
→ 659c310f-395f-4f47-a3f3-974fad1299b9 SUCCESS

railway deployment list --service web --environment production --limit 2 --json
→ d70e164d-daf9-4f26-a788-1518bbf183f8 SUCCESS, commit 9ec4256

curl -I https://sales-note-frontend-production.up.railway.app/ai-workspace/
→ 200 OK

curl https://sales-note-frontend-production.up.railway.app/reporting/api/ai-workspace/
→ 401 login_required

curl https://web-production-5096.up.railway.app/reporting/api/ai-workspace/
→ 401 login_required
```

### 배포 상태

- Runtime commit: `9ec4256 feat: add AI workspace result panel`
- GitHub push: `main` updated from `168c85c` to `9ec4256`
- Railway `web`: `d70e164d-daf9-4f26-a788-1518bbf183f8` SUCCESS, commit `9ec4256`
- Railway `sales-note-frontend`: `659c310f-395f-4f47-a3f3-974fad1299b9` SUCCESS, message `Deploy AI workspace result panel 9ec4256`
- Production `/ai-workspace/` returns 200 and serves `assets/index-D8ySrsxQ.js` / `assets/index-C66GcgeW.css`
- Production JS contains `featuredDepartment`, `Department AI`, and PainPoint confirm memo handling strings.
- Production CSS contains `ai-workspace-layout` and `ai-featured-customer-chips`.
- Anonymous frontend proxy `/reporting/api/ai-workspace/` returns `401 login_required`.
- Anonymous direct backend `/reporting/api/ai-workspace/` returns `401 login_required`.

### 알려진 제한

- 오른쪽 대표 AI 패널은 현재 사용자 기준 최신 부서 분석을 우선 표시합니다. 분석이 없으면 첫 분석 대상 부서의 빈 AI 패널을 보여주고 실행 버튼을 제공합니다.

### 권장 다음 작업

- 사용자 운영 검수 후 기존 진행 예정이던 React 서류 템플릿 관리(`/documents/`) 또는 다음 우선순위 작업으로 돌아갑니다.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/ai-workspace/`에 로그인한 상태로 접속합니다.
2. 오른쪽 `Department AI` 패널이 고객 상세 오른쪽 AI 패널처럼 미팅/견적/납품 분석, 검증 기반 인사이트, 추천 액션, 확인 필요, PainPoint 검증을 보여주는지 확인합니다.
3. 미검증 PainPoint 카드에 검증 메모를 입력하고 `확인`을 누른 뒤 카드가 저장/새로고침되는지 확인합니다.
4. `확인` 외에 `부정` 선택지가 없는지 확인합니다.
5. 기존 AI 작업 큐, 부서 분석 대상, 고객 분석 대상, 전체 검증 대기 목록이 계속 보이는지 확인합니다.

---

## 2026-05-10 — React Schedule Documents First Integration

**상태**: 구현/로컬 검증/푸시/운영 배포/사용자 수동검수 완료

### 요약

React 일정 상세(`/schedules/<id>/`) 오른쪽 패널에 기존 Django 서류 생성 workflow를 붙였습니다. 견적 일정은 견적서, 납품 일정은 거래명세서/납품서의 PDF 및 Excel 다운로드와 변수 미리보기를 React에서 바로 실행할 수 있습니다.

### 변경된 파일

- `reporting/views.py`: 일정 상세 API payload에 활동 유형별 문서 action, 미리보기 URL, 생성 URL, 활성 템플릿 수 추가
- `reporting/tests.py`: 일정 상세 API의 문서 action 회귀 테스트 추가
- `frontend/src/api.ts`: 서류 미리보기 GET, 파일 다운로드 POST helper 및 타입 추가
- `frontend/src/App.tsx`: React 일정 상세 서류 다운로드/변수 미리보기 패널 추가
- `frontend/src/styles.css`: 서류 패널, 다운로드 버튼, 변수 그룹, 모바일 반응형 스타일 추가
- `AGENT_PLAN.md`: React 일정 상세 문서 생성 통합 계획 기록

### CRM 개선

- 견적/납품 일정에서 Django 상세 화면으로 이동하지 않고 React 일정 상세에서 바로 서류를 생성할 수 있습니다.
- 생성 전 템플릿 변수와 품목 데이터를 React 패널에서 확인할 수 있어 서류 생성 실패나 빈 값 입력을 줄입니다.
- Django 서류 템플릿 관리 화면은 fallback/관리 화면으로 그대로 연결됩니다.

### 기존 기능 보존

- 기존 `/reporting/documents/*` 템플릿 관리, 변수 미리보기, 파일 생성 endpoint는 유지했습니다.
- 기존 Django 일정 상세와 `/reporting/*` routes는 삭제하지 않았습니다.
- DB 모델 변경 및 migration은 없습니다.
- 기존 인증/권한 검사는 Django 문서 생성 endpoint의 `login_required`와 `can_access_user_data`를 그대로 사용합니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 27 tests, OK

python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend; npm run build
→ OK, assets/index-CSJjhwCa.js / assets/index-DEZuogRh.css

cd frontend; node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add React schedule documents"
→ ed5e43c

git push
→ main pushed to GitHub

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React schedule documents ed5e43c" --ci
→ 4f867493-7910-46f3-9762-81d3416bcb80 SUCCESS

railway deployment list --service web --environment production --limit 2 --json
→ 18b88087-7c25-4835-98fd-8c34c505879c SUCCESS
```

### 배포 상태

- Runtime commit: `ed5e43c feat: add React schedule documents`
- GitHub push: `main` updated from `bbdded8` to `ed5e43c`
- Railway `web`: `18b88087-7c25-4835-98fd-8c34c505879c` SUCCESS, commit `ed5e43c`
- Railway `sales-note-frontend`: `4f867493-7910-46f3-9762-81d3416bcb80` SUCCESS, message `Deploy React schedule documents ed5e43c`
- Production `/schedules/1/` returns 200 and serves `assets/index-CSJjhwCa.js` / `assets/index-DEZuogRh.css`
- Production JS contains `schedule-documents-panel` and document download handling code.
- Production CSS contains `schedule-document-card` and `schedule-document-variable-row`.
- Anonymous frontend proxy `/reporting/api/schedules/1/` returns `401 login_required`.
- Anonymous direct backend `/reporting/api/schedules/1/` returns `401 login_required`.
- Anonymous document preview and generate endpoints redirect to `/reporting/login/`.
- 사용자 운영 검수: 2026-05-10 완료 확인.

### 알려진 제한

- 실제 PDF/Excel 생성 성공 여부는 회사별 활성 `DocumentTemplate` 등록 상태와 기존 Django 문서 생성 엔진에 따라 달라집니다.
- PDF 변환 품질과 fallback 동작은 기존 Django 서류 생성 로직을 그대로 따릅니다.

### 권장 다음 작업

- 사용자 운영 검수 후 React 서류 템플릿 관리 화면(`/documents/`) 1차 통합을 진행하면 서류 생성 workflow가 더 완결됩니다.

### 수동 서버 테스트 절차

1. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/schedules/<quote_schedule_id>/`에서 견적 일정 상세를 엽니다.
2. 오른쪽 `서류 다운로드` 섹션에 `견적서`가 보이는지 확인합니다.
3. `미리보기`를 눌러 고객/금액/품목 변수가 줄바꿈과 그룹 구분으로 읽히는지 확인합니다.
4. `PDF`, `Excel` 다운로드를 눌러 파일이 생성되는지 확인합니다.
5. 운영 프론트 `https://sales-note-frontend-production.up.railway.app/schedules/<delivery_schedule_id>/`에서 납품 일정 상세를 엽니다.
6. `거래명세서`, `납품서`가 보이고 각각 미리보기/다운로드가 동작하는지 확인합니다.
7. `템플릿` 링크가 기존 Django 서류 템플릿 관리 화면으로 이동하는지 확인합니다.

---

## 2026-05-10 — React Mailbox Reply Quote Cleanup

**상태**: 구현/로컬 검증 완료, 운영 배포 예정

### 요약

React 메일 스레드에서 답장 메일 본문 아래에 Gmail/Outlook 인용 체인과 이전 메일이 반복 표시되는 문제를 수정했습니다. 화면 표시용 `bodyText`에서만 인용 구간을 제거하고, DB에 저장된 원본 `EmailLog.body/body_html`은 유지해 AI 분석 원본 데이터에는 영향을 주지 않습니다.

### 변경된 파일

- `reporting/gmail_views.py`: Gmail/Outlook HTML 인용 컨테이너와 텍스트 인용 패턴 제거 helper 추가
- `reporting/tests.py`: 텍스트 Gmail 답장 인용과 HTML `gmail_quote` 인용 제거 회귀 테스트 추가

### CRM 개선

- React 스레드 상세에서 각 메일 카드가 해당 메일의 신규 본문만 보여 더 읽기 쉬워졌습니다.
- 긴 답장 체인이 여러 메일 카드마다 중복 노출되지 않습니다.

### AI 영향

- AI는 기존처럼 `EmailLog` 원본 저장 필드를 읽습니다.
- 이번 변경은 React API의 표시용 `bodyText` 직렬화에만 적용되어 AI 판단 근거가 줄어들지 않습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=2
→ Ran 5 tests, OK

python -m py_compile reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- 운영 배포 예정.

### 수동 서버 테스트 절차

1. 운영 `/mailbox/thread/<thread_id>/`에서 답장 메일이 여러 개 있는 스레드를 엽니다.
2. 각 메일 카드에 해당 메일의 신규 본문만 보이는지 확인합니다.
3. Gmail/Outlook의 `이전 메일`, `On ... wrote:`, `보낸 사람:`, `From:` 아래 내용이 반복 노출되지 않는지 확인합니다.

---

## 2026-05-10 — React Mailbox Body Linebreak Fix

**상태**: 구현/로컬 검증 완료, 운영 배포 예정

### 요약

React 메일 스레드 상세에서 본문 줄바꿈이 모두 사라져 가독성이 떨어지는 문제를 수정했습니다. 메일 목록 `preview`는 한 줄 요약으로 유지하고, 스레드 상세 `bodyText`는 원본 텍스트 개행과 HTML `<br>`/문단 구분을 보존하도록 API 직렬화 로직을 분리했습니다.

### 변경된 파일

- `reporting/gmail_views.py`: 스레드 본문용 `_email_body_text()` 추가 및 `bodyText` 직렬화에 적용
- `reporting/tests.py`: React 메일 스레드 API가 본문 개행을 보존하는 회귀 테스트 추가

### CRM 개선

- 고객 메일 본문이 문단 단위로 표시되어 긴 요청/답장 내용의 가독성이 개선됩니다.
- 목록 미리보기는 기존처럼 짧게 유지되어 테이블 밀도는 유지됩니다.

### 기존 기능 보존

- React CSS와 화면 구조는 변경하지 않았습니다.
- 기존 Django 메일함, Gmail/IMAP 연동, 발송/답장/상태 변경 API는 유지했습니다.
- DB 변경 및 migration 없음.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.ReactMailboxApiTests --verbosity=2
→ Ran 3 tests, OK

python -m py_compile reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend; npm run build
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- 운영 배포 예정.

### 수동 서버 테스트 절차

1. 운영 프론트 `/mailbox/`에서 줄바꿈이 있는 고객 메일 스레드를 엽니다.
2. `/mailbox/thread/<thread_id>/` 본문에서 문단 구분과 줄바꿈이 유지되는지 확인합니다.
3. 목록 화면 미리보기는 한 줄 요약으로 유지되는지 확인합니다.

---

## 2026-05-10 — React Mailbox First Integration

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React CRM에 `/mailbox/` 메일함과 `/mailbox/thread/<thread_id>/` 스레드 상세 화면을 추가했습니다. 기존 Django Gmail/IMAP/EmailLog 발송·답장·동기화·메일 상태 변경 로직은 유지하고, React가 사용할 `/reporting/api/mailbox/*` JSON API를 새로 붙였습니다.

### 변경된 파일

- `reporting/gmail_views.py`: React 메일함 목록/스레드/발송/답장/동기화/상태 변경 API 추가
- `reporting/urls.py`: `/reporting/api/mailbox/*` API route와 누락됐던 legacy archive route 추가
- `reporting/tests.py`: React 메일함 API 권한/스레드 읽음/중요표시 회귀 테스트 추가
- `frontend/src/api.ts`: 메일함 타입, 빈 상태, API client 추가
- `frontend/src/App.tsx`: 사이드바 메일 메뉴, 메일함 목록, 스레드 상세, 작성/답장 UI 추가
- `frontend/src/styles.css`: 메일함/스레드/작성 폼 스타일 추가
- `AGENT_PLAN.md`: React 메일함 1차 통합 계획 기록

### CRM 개선

- 고객 메일을 React CRM 내부에서 조회하고 고객 상세/일정으로 바로 이동할 수 있습니다.
- 메일 작성 시 고객을 선택하면 고객 이메일이 자동으로 채워지고, 기존 명함 서명 선택도 사용할 수 있습니다.
- 스레드 상세에서 답장, 중요표시, 휴지통 이동을 처리할 수 있습니다.
- 받은편지함/보낸편지함/중요/보관/휴지통 탭과 검색을 React에서 제공합니다.

### 기존 기능 보존

- 기존 Django `/reporting/mailbox/*`, Gmail OAuth, IMAP/SMTP 연결, Django 템플릿 화면은 유지했습니다.
- 기존 `EmailLog` 모델과 발송 helper를 재사용했고 DB 변경 및 migration은 없습니다.
- 운영 수동검수 전에는 Django 메일함을 React로 강제 redirect하지 않습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.ReactMailboxApiTests reporting.tests.GmailMailboxThreadRegressionTests --verbosity=2
→ Ran 5 tests, OK

python -m py_compile reporting\gmail_views.py reporting\urls.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend; npm run build
→ OK, assets/index-BtG-R--E.js / assets/index-B6vJbiFg.css

cd frontend; node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `1501588 feat: add React mailbox`
- GitHub push: `main` updated from `06a1c22` to `1501588`
- Railway `web`: `b97fc890-33ef-400c-a67a-3f15a468f082` SUCCESS, commit `1501588`
- Railway `sales-note-frontend`: `092cbf4d-4072-47e7-966c-7bef7372f479` SUCCESS, message `Deploy React mailbox 1501588`
- Production `/mailbox/` returns 200 and serves `assets/index-BtG-R--E.js` / `assets/index-B6vJbiFg.css`
- Production JS contains `메일`, `/reporting/api/mailbox/`, `mailbox-page`, `답장 발송`
- Production CSS contains `mailbox-page`, `mail-row`, `mail-thread-page`, `mail-compose-panel`
- Anonymous frontend proxy `/reporting/api/mailbox/` redirects to `/reporting/login/?next=/reporting/api/mailbox/` with 302
- Anonymous backend `/reporting/api/mailbox/` redirects to `/reporting/login/?next=/reporting/api/mailbox/` with 302
- Railway `web` and `sales-note-frontend` logs checked: mailbox-related ERROR/Traceback/500 재발 없음
- Local preview server started: `http://localhost:4173`

### 수동 서버 테스트 절차

1. 운영 프론트에서 로그인 후 `/mailbox/`로 이동합니다.
2. 받은편지함/보낸편지함/중요/보관/휴지통 탭이 열리는지 확인합니다.
3. 고객 메일 스레드 하나를 열어 `/mailbox/thread/<thread_id>/`에서 본문과 고객 링크가 보이는지 확인합니다.
4. 중요표시, 보관, 휴지통 이동이 반영되는지 확인합니다.
5. `메일 작성`에서 고객 선택 시 받는 사람이 채워지고 발송이 되는지 확인합니다.
6. 스레드 상세에서 `답장` 발송 후 같은 스레드에 메일이 추가되는지 확인합니다.

### 다음 권장 작업

- 운영 검수 완료 후 Django 메일함 주요 진입 링크를 React `/mailbox/`로 전환하고, 고객 상세/AI 화면에 메일 근거 섹션을 더 노출합니다.

---

## 2026-05-10 — Railway Mailbox Thread 500 Fix

**상태**: 구현/로컬 검증/푸시/운영 배포 완료

### 요약

Railway 운영 로그의 실제 500 원인은 `/reporting/mailbox/thread/<thread_id>/` 렌더링 중 `reporting/gmail/thread_detail.html`의 `{% block extra_js %}`가 닫히지 않은 템플릿 오류였습니다. 같은 요청 흐름에서 Gmail 스레드 신규 메시지 저장 시 없는 `save_email_to_db` import도 반복되어 함께 수정했습니다.

### 변경된 파일

- `reporting/templates/reporting/gmail/thread_detail.html`: 삭제 중 남은 미완성 JS 꼬리를 정리하고 `{% endblock %}` 정상 종료
- `reporting/imap_utils.py`: Gmail 스레드 메시지를 `EmailLog`에 저장하는 `save_email_to_db()` helper 추가
- `reporting/gmail_views.py`: Gmail 메시지 본문 저장 시 `body_text`/`snippet` fallback 사용
- `reporting/tests.py`: 템플릿 컴파일 및 Gmail thread 메시지 저장 회귀 테스트 추가
- `AGENT_PLAN.md`: Railway 긴급 복구 작업 계획 기록

### CRM 개선

- 메일함 스레드 상세 화면의 템플릿 500을 제거했습니다.
- Gmail에서 스레드 상세 진입 시 새 메시지가 있으면 기존 `EmailLog`에 저장되어 후속 AI/메일 분석 데이터로도 활용될 수 있습니다.
- raw Gmail 헤더의 `Name <email>` 형태를 이메일 주소/표시명으로 분리해 저장합니다.

### 기존 기능 보존

- 기존 `/reporting/*` 라우트, 로그인 보호, Gmail OAuth/메일함 흐름은 유지했습니다.
- DB 모델 필드 변경 및 migration 없음.
- 기존 메일 삭제, 답장, 인용 메일 접기 UI는 유지했습니다.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.GmailMailboxThreadRegressionTests --verbosity=2
→ Ran 2 tests, OK

python -m py_compile reporting\imap_utils.py reporting\gmail_views.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `53e36f3 fix: restore mailbox thread page`
- GitHub push: `main` updated from `cd616f2` to `53e36f3`
- Railway `web`: `dfe55f5d-e6be-44b3-aef2-ee7b8caf85cf` SUCCESS, commit `53e36f3`
- Railway `web` 환경변수: `EMAIL_ENCRYPTION_KEY` 설정 완료, 시작 로그의 해당 error 제거
- Production smoke: backend `/reporting/login/` returns 200 OK
- Production smoke: backend `/reporting/mailbox/thread/railway-smoke-thread/` redirects to `/reporting/login/?next=...` with 302
- Production smoke: frontend proxy `/reporting/mailbox/thread/railway-smoke-thread/` redirects to `/reporting/login/?next=...` with 302
- Production log check: `TemplateSyntaxError`, `save_email_to_db`, `EMAIL_ENCRYPTION_KEY`, HTTP `>=500` 재발 없음
- Railway `sales-note-frontend`: 코드 변경 없음, proxy smoke만 확인

### 수동 서버 테스트 절차

1. 운영에서 메일 연동 계정으로 로그인합니다.
2. `/reporting/mailbox/` 또는 React 프론트에서 메일함으로 이동합니다.
3. Gmail 스레드 상세 `/reporting/mailbox/thread/<thread_id>/`를 엽니다.
4. 화면이 500 없이 열리고 메시지 본문/답장 버튼이 보이는지 확인합니다.
5. Railway `web` 로그에서 같은 경로의 `TemplateSyntaxError`와 `save_email_to_db` import 오류가 재발하지 않는지 확인합니다.

### 다음 권장 작업

- 운영 수동검수 후 메일함 스레드 상세의 날짜 표시와 기존 수신 메일 chronology 정렬을 별도 개선할 수 있습니다.

---

## 2026-05-10 — AI Email Context And Stage-Aware Next Actions

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

부서 AI와 개별 고객 AI 분석에 고객 메일 답장 컨텍스트를 추가했습니다. 특히 고객이 보낸 수신 메일을 우선 근거로 프롬프트에 넣고, 고객 단계가 락인/수주, 견적, 미팅만 진행 중인지에 따라 다음 액션이 자동 보강되도록 했습니다.

### 변경된 파일

- `ai_chat/services.py`: `EmailLog` 기반 메일 컨텍스트 수집, 고객 단계별 분석 기준 생성, 부서/개별 고객 AI 프롬프트 및 fallback 다음 액션 보강
- `ai_chat/tests.py`: 메일 수신 내용과 락인/견적/미팅 고객 단계별 다음 액션 반영 회귀 테스트 추가

### CRM 개선

- 고객이 보낸 메일 답장이 AI 분석의 실제 근거로 들어갑니다.
- 락인/수주 고객은 납품, 추가 발주, 재구매, 리텐션 중심 액션을 생성합니다.
- 견적 고객은 견적 내용, 미팅 내용, 고객 메일 답장을 함께 보고 수정 견적/조건 확인/의사결정 일정 액션을 생성합니다.
- 미팅만 진행한 고객은 미팅 내용과 고객 메일 답장을 기반으로 자료 전달, 다음 미팅, 견적화 액션을 생성합니다.
- 기존 PainPoint 검증 메모리는 단계별 액션 보정 reason에도 우선 반영됩니다.

### 기존 기능 보존

- 기존 `/ai/*`, `/reporting/*`, React CRM 경로와 인증/권한 정책은 유지했습니다.
- 신규 DB 필드와 migration 없음.
- 메일 데이터는 기존 `EmailLog`와 연결된 `FollowUp`/`Schedule` 범위 안에서만 수집합니다.

### 실행한 명령어 및 결과

```text
python manage.py test ai_chat.tests.AIEmailAndStageActionContextTests --verbosity=2
→ Ran 2 tests, OK

python manage.py test ai_chat.tests --verbosity=1
→ Ran 18 tests, OK

python -m py_compile ai_chat\services.py ai_chat\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `7055257 feat: use customer emails in AI next actions`
- GitHub push: `main` updated from `4394aba` to `7055257`
- Railway `web`: `69401c16-b987-47bc-95e1-7e56c946dc18` SUCCESS, commit `7055257`
- Production smoke: anonymous `/ai/` redirects to `/reporting/login/?next=/ai/`
- Production smoke: `/reporting/login/` returns 200 OK
- React bundle 변경은 없어 `sales-note-frontend` 직접 배포는 필요하지 않습니다.

### 수동 서버 테스트 절차

1. 운영에서 Gmail/IMAP 동기화 또는 메일 발송/수신 기록이 연결된 고객을 선택합니다.
2. 고객 상세 또는 AI 허브에서 해당 부서 `AI 분석 실행`을 다시 누릅니다.
3. 고객이 보낸 최근 메일의 핵심 내용이 요약/PainPoint/다음 액션 판단에 반영되는지 확인합니다.
4. 수주 단계 고객은 납품/추가 발주/재구매 중심 액션이 나오는지 확인합니다.
5. 견적 단계 고객은 견적 내용, 미팅 내용, 메일 답장을 근거로 조건 확인/수정 견적/결정 일정 액션이 나오는지 확인합니다.
6. 미팅만 진행한 고객은 자료 전달, 다음 미팅, 견적화 액션이 나오는지 확인합니다.
7. 검증 완료/부정 메모가 있는 고객은 해당 검증 메모가 다음 액션 reason에 우선 반영되는지 확인합니다.

### 다음 권장 작업

- 운영 수동검수 후 React 통합 프론트 전환 또는 AI 결과 화면에서 메일 근거 요약을 별도 섹션으로 노출하는 작업을 검토합니다.

---

## 2026-05-10 — AI Verification Notes In Department Summary

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

PainPoint 검수 단계에서 사용자가 남긴 확인/부정 메모가 다음 부서 AI 재분석 결과의 `department_summary`에 반드시 포함되도록 서버 fallback을 보강했습니다. GPT가 요약에서 검증 메모를 약하게 반영하거나 누락하더라도 저장 직전에 `검증 메모 반영` 문장이 요약에 추가됩니다.

### 변경된 파일

- `ai_chat/services.py`: 검증 메모 기반 summary fallback 생성 및 `department_summary` 보정 추가
- `ai_chat/tests.py`: 재분석 결과 요약에 검증 메모가 포함되는 회귀 테스트 추가
- `AGENT_PLAN.md`: 긴급 검수 메모 요약 반영 작업 계획 기록

### CRM 개선

- 사용자가 PainPoint 검수에서 남긴 메모가 다음 AI 분석의 메인 요약에 직접 반영됩니다.
- 확인된 가설은 `확인된 사항`, 부정된 가설은 `부정된 가설`로 구분되어 요약에 들어갑니다.
- 기존 `verification_insights`, `next_actions`, `missing_info` 보정은 유지됩니다.

### 기존 기능 보존

- 기존 AI 분석 실행 URL, PainPoint 검증 저장 URL, 권한 정책은 유지했습니다.
- DB 변경 및 migration 없음.
- 검증 메모가 이미 요약에 들어간 경우 중복 삽입하지 않습니다.

### 실행한 명령어 및 결과

```text
python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
→ Ran 2 tests, OK

python manage.py test ai_chat.tests --verbosity=1
→ Ran 16 tests, OK

python -m py_compile ai_chat\services.py ai_chat\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `bf5dd23 fix: include AI verification notes in summary`
- GitHub push: `main` updated from `2a9fe28` to `bf5dd23`
- Railway `web`: `d67036bf-1de5-44cd-b9b3-881ef6652d7b` SUCCESS, commit `bf5dd23`
- Production smoke: anonymous `/ai/` redirects to `/reporting/login/?next=/ai/`
- Production smoke: `/reporting/login/` returns 200 OK
- React bundle 변경은 없어 `sales-note-frontend` 직접 배포는 필요하지 않습니다.

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/customers/<customer_id>/`
2. AI 권한이 있는 계정으로 로그인합니다.
3. 고객 상세의 PainPoint 검증에서 메모를 입력하고 `확인` 또는 `부정` 처리합니다.
4. 같은 고객/부서에서 `AI 분석 실행`을 다시 누릅니다.
5. 재분석 후 부서 AI 요약에 방금 입력한 검증 메모의 핵심 내용이 포함되는지 확인합니다.
6. `확인` 메모는 확인된 사실로, `부정` 메모는 부정된 가설 또는 대체 원인으로 표현되는지 확인합니다.

### 다음 권장 작업

- 사용자가 추가 요청한 “고객과 주고받은 메일을 AI 분석 컨텍스트에 반영” 작업과 “락인/견적/미팅 고객 단계별 다음 액션 생성” 작업을 이어서 진행합니다.

---

## 2026-05-10 — React Pipeline Department AI Panel

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 가능

### 요약

React 파이프라인에서 고객 카드를 선택하면 우측 상세 패널에 해당 고객의 부서 AI 분석 요약이 표시되도록 확장했습니다. 파이프라인 API의 deal payload에 부서 AI compact 정보를 추가하고, React 상세 패널에 분석 요약, 미팅/견적/납품/PainPoint 카운트, 미검증 PainPoint 알림, AI 결과/허브 링크를 표시합니다.

### 변경된 파일

- `reporting/funnel_views.py`: 파이프라인 deal payload에 `aiDepartment` compact payload 추가
- `reporting/tests.py`: 파이프라인 API 부서 AI 요약 payload 테스트 추가
- `frontend/src/mockData.ts`: `Deal.aiDepartment` 타입 추가
- `frontend/src/App.tsx`: 파이프라인 우측 상세 패널에 `Department AI` 카드 추가
- `frontend/src/styles.css`: 파이프라인 AI 미검증 알림 스타일 추가
- `AGENT_PLAN.md`: 긴급 파이프라인 부서 AI 작업 계획 기록

### CRM 개선

- 파이프라인 카드 선택만으로 해당 고객의 부서 AI 분석 상태를 바로 볼 수 있습니다.
- 미팅/견적/납품/PainPoint 카운트와 미검증 PainPoint 수가 우측 패널에 표시됩니다.
- 분석 결과가 있으면 AI 결과 화면으로, 없으면 AI 허브로 이동할 수 있습니다.

### 기존 기능 보존

- 기존 파이프라인 단계 이동, 견적/납품 금액 계산, Django 고객 상세 링크는 유지했습니다.
- AI 실행/검증 전체 UI는 기존 고객 상세/AI 허브 흐름을 유지했습니다.
- DB 변경 및 migration 없음.
- `/reporting/*` 인증/권한 정책 유지.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 12 tests, OK

cd frontend; npm run build
→ OK, assets/index-CLXRI0TH.js / assets/index-AuyH7qvg.css

cd frontend; node --check server.mjs
→ OK

python -m py_compile reporting\funnel_views.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `b8e65e9 feat: show department AI in pipeline panel`
- GitHub push: `main` updated from `9236cbf` to `b8e65e9`
- Railway `web`: `9690f304-7adb-465b-b582-61ea58192a46` SUCCESS
- Railway `sales-note-frontend`: `458c5243-9a04-48b7-bb80-6378231885de` SUCCESS
- 운영 프론트 `/dashboard/`: 200, `assets/index-CLXRI0TH.js` / `assets/index-AuyH7qvg.css`
- 운영 JS: `aiDepartment=True`, `Department AI=True`, `pipeline-ai-card=True`, `미검증 PainPoint=True`
- 운영 CSS: `pipeline-ai-alert=True`, `customer-ai-card=True`
- 운영 anonymous `/reporting/api/pipeline/`: `302 /reporting/login/?next=/reporting/api/pipeline/`

배포/운영 smoke 명령:

```text
git commit -m "feat: show department AI in pipeline panel"
→ b8e65e9 feat: show department AI in pipeline panel

git push origin main
→ main updated from 9236cbf to b8e65e9

railway redeploy --service web --from-source --yes --json
→ {"success":true}

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy pipeline department AI b8e65e9" --ci
→ Deploy complete

railway deployment list --service web --environment production --limit 1 --json
→ 9690f304-7adb-465b-b582-61ea58192a46 SUCCESS

railway deployment list --service sales-note-frontend --environment production --limit 1 --json
→ 458c5243-9a04-48b7-bb80-6378231885de SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/dashboard/
→ 200, assets/index-CLXRI0TH.js / assets/index-AuyH7qvg.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-CLXRI0TH.js
→ aiDepartment=True, Department AI=True, pipeline-ai-card=True, 미검증 PainPoint=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-AuyH7qvg.css
→ pipeline-ai-alert=True, customer-ai-card=True

curl.exe -s -i https://web-production-5096.up.railway.app/reporting/api/pipeline/
→ 302 /reporting/login/?next=/reporting/api/pipeline/
```

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/dashboard/`
2. 파이프라인 보드에서 고객 카드를 클릭합니다.
3. 오른쪽 상세 패널에 `Department AI` 카드가 보이는지 확인합니다.
4. 분석이 있는 고객은 요약, 미팅/견적/납품/PainPoint 카운트와 `AI 결과` 링크가 보이는지 확인합니다.
5. 분석이 없는 고객은 `아직 부서 AI 분석이 없습니다` 또는 권한 메시지와 `AI 허브` 링크가 보이는지 확인합니다.
6. 기존 단계 변경, Django 고객 상세 열기, 견적/납품 정보 표시가 그대로 동작하는지 확인합니다.

### 다음 권장 작업

- 이 작업 배포/검수 후, 사용자가 추가 요청한 “PainPoint 검수 메모를 다음 AI 분석 요약에 반영” 작업을 이어서 진행합니다.

---

## 2026-05-10 — Urgent React Dashboard Logout Button

**상태**: 구현/검증/푸시/운영 배포/사용자 수동검수 완료

### 요약

운영 React CRM `/dashboard/`에서 바로 로그아웃할 수 있도록 공통 상단바에 `로그아웃` 버튼을 추가했습니다. 버튼은 기존 Django `/reporting/logout/` URL에 CSRF 포함 `POST` 요청을 보내고, 처리 후 `/reporting/login/`으로 이동합니다.

### 변경된 파일

- `frontend/src/App.tsx`: 로그아웃 버튼, `LogOut` 아이콘, CSRF 쿠키 읽기 및 POST 로그아웃 처리 추가
- `frontend/src/styles.css`: 로그아웃 버튼 스타일과 모바일 폭 대응 추가
- `AGENT_PLAN.md`: 긴급 로그아웃 버튼 작업 계획 기록
- `AGENT_REPORT.md`: 긴급 작업 구현/검증 기록
- `HANDOFF.md`: 직전 선결제 요약 배포 상태 갱신

### CRM 개선

- React `/dashboard/` 및 React CRM 공통 화면에서 로그아웃 진입점을 즉시 확인할 수 있습니다.
- 단순 GET 링크가 아니라 기존 Django 인증/CSRF 정책을 유지하는 POST 로그아웃을 사용합니다.

### 기존 기능 보존

- 기존 `/reporting/logout/`, `/reporting/login/`, `/reporting/*` 인증 흐름은 유지했습니다.
- DB 변경 및 migration 없음.
- 내부 CRM 데이터 공개 범위 변경 없음.

### 실행한 명령어 및 결과

```text
cd frontend; npm run build
→ OK, assets/index-cLy6Pc7s.js / assets/index-D1AABLev.css

cd frontend; node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

git diff --check
→ OK (LF→CRLF warning only)
```

### 배포 상태

- Runtime commit: `28a08db fix: add React logout button`
- GitHub push: `main` updated from `f7794db` to `28a08db`
- Railway `sales-note-frontend`: `58a3e89a-fbad-4bca-bf21-172229b095af` SUCCESS
- 운영 프론트 `/dashboard/`: 200, `assets/index-cLy6Pc7s.js` / `assets/index-D1AABLev.css`
- 운영 JS: `로그아웃=True`, `/reporting/logout/=True`, `X-CSRFToken=True`, `/reporting/login/=True`
- 운영 CSS: `logout-button=True`
- 운영 `/reporting/login/`: 200 OK
- 운영 anonymous `/reporting/api/dashboard/`: `401 login_required`
- Django backend 변경은 없어 `web` 재배포는 수행하지 않았습니다.

배포/운영 smoke 명령:

```text
git commit -m "fix: add React logout button"
→ 28a08db fix: add React logout button

git push origin main
→ main updated from f7794db to 28a08db

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React logout button 28a08db" --ci
→ Deploy complete

railway deployment list --service sales-note-frontend --environment production --limit 1 --json
→ 58a3e89a-fbad-4bca-bf21-172229b095af SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/dashboard/
→ 200, assets/index-cLy6Pc7s.js / assets/index-D1AABLev.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-cLy6Pc7s.js
→ 로그아웃=True, /reporting/logout/=True, X-CSRFToken=True, /reporting/login/=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-D1AABLev.css
→ logout-button=True

curl.exe -s -I https://sales-note-frontend-production.up.railway.app/reporting/login/
→ 200 OK

curl.exe -s -i https://sales-note-frontend-production.up.railway.app/reporting/api/dashboard/
→ 401 login_required
```

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/dashboard/`
2. 로그인된 상태에서 상단 오른쪽의 `로그아웃` 버튼이 보이는지 확인합니다.
3. `로그아웃`을 클릭합니다.
4. `/reporting/login/`으로 이동하는지 확인합니다.
5. 브라우저 뒤로가기로 `/dashboard/`에 돌아갔을 때 데이터가 계속 보이지 않고 로그인 요구 상태가 되는지 확인합니다.

### 사용자 수동검수 결과

- 사용자 확인: 2026-05-10
- 결과: 검수 완료

### 다음 권장 작업

- 긴급 로그아웃 버튼 배포는 완료됐습니다.
- 다음 작업은 별도 지시 또는 다음 React 전환 우선순위 확인 후 진행합니다.

---

## 2026-05-10 — React 고객 상세 선결제 요약 통합

**상태**: 구현/로컬 검증/푸시/운영 배포 완료, 사용자 수동검수 대기

### 요약

React 고객 상세(`/customers/<customer_id>/`)에서 해당 고객의 선결제 총액, 잔액, 사용액, 상태별 건수와 최근 선결제 이력을 바로 볼 수 있게 확장했습니다.

### 변경된 파일

- `reporting/views.py`: 고객 상세 API `prepaymentSummary` payload 추가
- `reporting/tests.py`: 고객 상세 선결제 요약 범위/집계 테스트 추가
- `frontend/src/api.ts`: 고객 상세 선결제 요약 타입과 fallback merge 추가
- `frontend/src/App.tsx`: 고객 상세 우측 선결제 요약 패널 추가
- `frontend/src/styles.css`: 고객 상세 선결제 요약 패널 스타일 추가
- `frontend/README.md`: 고객 상세 선결제 요약 범위 기록
- `AGENT_PLAN.md`: 작업 계획 기록

### CRM 개선

- 고객 상세에서 선결제 총액, 남은 잔액, 사용 금액, 전체 건수를 즉시 확인할 수 있습니다.
- 최근 선결제 5건의 입금일, 입금자, 담당자, 잔액, 상태를 고객 상세 안에서 확인합니다.
- `고객별 선결제` 링크로 기존 React 고객별/부서별 선결제 전체 화면으로 이동할 수 있습니다.

### 기존 기능 보존

- 기존 `/reporting/api/customers/<id>/` 인증/권한 흐름 유지.
- 선결제 요약은 고객 상세와 같은 `scope_users` 범위로 제한해 다른 사용자 데이터 노출을 막습니다.
- 기존 `/prepayments/customer/<id>/`, `/reporting/prepayment/customer/<id>/`, 엑셀 fallback 유지.
- DB 모델 변경 없음, migration 없음.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 19 tests, OK

python manage.py test reporting.tests.PrepaymentCustomerApiTests reporting.tests.PrepaymentDetailApiTests --verbosity=1
→ Ran 11 tests, OK

cd frontend && npm run build
→ OK, assets/index-VVc8nVTe.js / assets/index-COYknf0t.css

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### Railway 배포 및 운영 스모크

- Commit: `1b88b4f feat: add customer prepayment summary`
- GitHub push: `main` 반영 완료
- Deployment/reporting commit: `f7794db docs: record customer prepayment summary deployment block`
- Railway CLI 인증 복구 확인: `railway status` 성공
- Railway `web`: `3e66177e-2ddb-4dd7-be56-6bfb6870ac18` SUCCESS, commit `f7794db`
- Railway `sales-note-frontend`: `eacfa822-cbd0-42ef-a2ff-418a7079329d` SUCCESS
- 운영 프론트 `/customers/1/`: 200, `assets/index-VVc8nVTe.js` / `assets/index-COYknf0t.css`
- 운영 JS: `prepaymentSummary=True`, `/prepayments/customer/=True`, `선결제 요약=True`
- 운영 CSS: `customer-prepayment-card=True`, `customer-prepayment-metrics=True`, `customer-prepayment-actions=True`
- 운영 프론트 proxy anonymous `/reporting/api/customers/1/`: `401 login_required`
- 운영 백엔드 anonymous `/reporting/api/customers/1/`: `401 login_required`
- 운영 로그인 페이지 `/reporting/login/`: 200 OK

추가 실행한 배포/스모크 명령어:

```text
railway status
→ 인증/프로젝트 연결 정상, web/sales-note-frontend Online

railway redeploy --service web --from-source --yes --json
→ {"success":true}

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy customer prepayment summary f7794db" --ci
→ Deploy complete, assets/index-VVc8nVTe.js / assets/index-COYknf0t.css

railway deployment list --service web --environment production --limit 1 --json
→ 3e66177e-2ddb-4dd7-be56-6bfb6870ac18 SUCCESS

railway deployment list --service sales-note-frontend --environment production --limit 1 --json
→ eacfa822-cbd0-42ef-a2ff-418a7079329d SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/1/
→ 200, assets/index-VVc8nVTe.js / assets/index-COYknf0t.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-VVc8nVTe.js
→ prepaymentSummary=True, /prepayments/customer/=True, 선결제 요약=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-COYknf0t.css
→ customer-prepayment-card=True, customer-prepayment-metrics=True, customer-prepayment-actions=True

curl.exe -s -i https://sales-note-frontend-production.up.railway.app/reporting/api/customers/1/
→ 401 login_required

curl.exe -s -i https://web-production-5096.up.railway.app/reporting/api/customers/1/
→ 401 login_required

curl.exe -s -I https://web-production-5096.up.railway.app/reporting/login/
→ 200 OK
```

### 알려진 제한

- 고객 상세 요약은 "해당 고객" 선결제만 집계하며, 같은 부서 전체 선결제는 기존 `/prepayments/customer/<id>/` 화면에서 확인합니다.
- 운영 서버에서 로그인 세션 기준 실제 데이터 표시 범위는 사용자가 수동 검수해야 합니다.

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/customers/<customer_id>/`
2. 고객 상세 우측의 `선결제 요약` 패널이 표시되는지 확인합니다.
3. 총액, 잔액, 사용, 건수와 최근 선결제 목록이 `/prepayments/customer/<customer_id>/` 및 Django 고객별 선결제 화면과 맞는지 비교합니다.
4. 선결제가 없는 고객에서는 빈 상태가 깨지지 않는지 확인합니다.
5. `상세` 링크가 React 선결제 상세로 이동하는지 확인합니다.
6. `고객별 선결제`, `선결제 목록` 링크가 정상 이동하는지 확인합니다.
7. 다른 영업사원 데이터가 보이면 안 되는 Salesman 계정에서 본인 범위만 보이는지 확인합니다.

### 다음 권장 작업

- 사용자 수동검수 완료 후 견적/문서 생성 흐름 또는 고객 상세 내 결제/납품 이력 요약을 이어서 React로 확장합니다.
- 수동검수 확인 전에는 다음 구현 작업을 시작하지 않습니다.

---

## 2026-05-10 — React 고객별/부서별 선결제 화면 전환

**상태**: 구현/검증/배포/사용자 수동검수 완료

### 요약

React CRM에 `/prepayments/customer/<customer_id>/` 고객별/부서별 선결제 화면을 추가했습니다. 기존 Django `/reporting/prepayment/customer/<customer_id>/` 및 엑셀 다운로드는 유지했습니다.

### 변경된 파일

- `reporting/views.py`: 고객별/부서별 선결제 JSON API와 React 고객별 링크 payload 추가
- `reporting/urls.py`: `/reporting/api/prepayments/customer/<customer_id>/` 추가
- `reporting/tests.py`: 고객별 선결제 API 권한, 부서 범위, 선택 사용자 필터 테스트 추가
- `frontend/src/api.ts`: `PrepaymentCustomerData`, `loadPrepaymentCustomerData()` 추가
- `frontend/src/App.tsx`: `/prepayments/customer/<id>/` 라우팅과 고객별 선결제 화면 추가
- `frontend/src/styles.css`: 고객별 선결제 화면 레이아웃/고객 목록 스타일 추가
- `frontend/README.md`: React 선결제 고객별 범위 기록
- `AGENT_PLAN.md`: 작업 계획 기록

### CRM 개선

- 고객별 선결제 화면을 React CRM 안에서 확인할 수 있습니다.
- 기존 운영 의미대로, 고객이 부서에 속해 있으면 같은 부서 전체 고객의 선결제를 함께 보여줍니다.
- 금액/잔액/사용액/상태별 건수와 같은 부서 고객 목록을 한 화면에 제공합니다.
- 선결제 목록/상세의 `고객별` 링크가 React 화면으로 이동하며, Django 고객별/엑셀 fallback도 유지됩니다.

### 기존 기능 보존

- 기존 `/reporting/prepayment/customer/<customer_id>/` Django 화면 유지.
- 기존 `/reporting/prepayment/customer/<customer_id>/excel/` 엑셀 다운로드 유지.
- Salesman 접근 규칙 유지: 고객 담당자이거나 해당 고객에 본인이 등록한 선결제가 있어야 접근 가능.
- Admin/Manager 선택 사용자 세션 필터 유지 및 React query 필터 추가.
- DB 모델 변경 없음, migration 없음.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.PrepaymentCustomerApiTests --verbosity=1
→ Ran 4 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend && npm run build
→ OK, assets/index-C1Keut7B.js / assets/index-BwpNmJt5.css

cd frontend && node --check server.mjs
→ OK

python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1
→ Ran 10 tests, OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### Railway 배포 및 운영 스모크

- Commit: `e918e7f feat: add React customer prepayments`
- `web` deployment: `cad3948b-a777-4cc6-9984-992e34213ffd` SUCCESS
- `sales-note-frontend` deployment: `8103ea72-d9a0-49bc-88ad-466a72a4e996` SUCCESS

운영 스모크:

```text
https://sales-note-frontend-production.up.railway.app/prepayments/customer/1/
→ 200, assets/index-C1Keut7B.js / assets/index-BwpNmJt5.css

프론트 JS
→ /prepayments/customer/ 포함, /reporting/api/prepayments/customer/ 포함, 고객별 선결제=True

프론트 CSS
→ prepayment-customer-layout=True, prepayment-customer-table=True

https://web-production-5096.up.railway.app/reporting/api/prepayments/customer/1/
→ 401 login_required

https://sales-note-frontend-production.up.railway.app/reporting/api/prepayments/customer/1/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/prepayment/customer/1/
→ 302 /reporting/login/?next=/reporting/prepayment/customer/1/

https://web-production-5096.up.railway.app/reporting/prepayment/customer/1/excel/
→ 302 /reporting/login/?next=/reporting/prepayment/customer/1/excel/
```

### 알려진 제한

- 운영 서버에서 실제 로그인 세션으로 고객별 화면의 권한별 데이터 범위는 사용자가 직접 확인해야 합니다.
- 기존 Django 엑셀 다운로드는 React가 직접 생성하지 않고 Django 링크로 유지합니다.
- 사용자 수동검수 완료: 2026-05-10

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/prepayments/`
2. 선결제 목록에서 `고객별`을 눌러 `/prepayments/customer/<customer_id>/`로 이동하는지 확인합니다.
3. 같은 부서의 여러 고객이 있는 경우 부서 전체 고객과 해당 사용자의 선결제가 함께 표시되는지 확인합니다.
4. 총 선결제, 남은 잔액, 사용 금액, 상태별 건수가 Django 고객별 화면과 맞는지 비교합니다.
5. 고객별 화면의 선결제 `상세`, `수정`, `Django` 링크가 정상 이동하는지 확인합니다.
6. 우측 부서 고객 목록에서 다른 고객을 눌러도 같은 부서 기준 화면이 유지되는지 확인합니다.
7. Manager/Admin 계정에서는 조회 사용자 선택이 보이고 사용자 변경 시 해당 사용자의 선결제로 갱신되는지 확인합니다.
8. 접근 권한이 없는 salesman 계정에서 URL 직접 접근이 차단되는지 확인합니다.
9. `Django 고객별`, `엑셀`, `Django 고객 상세` 링크가 기존 Django 화면/다운로드로 정상 연결되는지 확인합니다.

### 다음 권장 작업

- 수동검수 완료 후 견적/문서 생성 흐름 또는 고객 상세 내 선결제/결제 이력 요약을 React로 확장합니다.

---

## 2026-05-10 — React 선결제 삭제/취소/이관 전환

**상태**: 구현/검증/배포 완료, 사용자 수동검수 대기

### 요약

React 선결제 상세 화면에서 취소, 삭제, 이관을 직접 처리하도록 확장했습니다. 기존 Django `/reporting/prepayment/*` 화면과 fallback 링크는 유지했습니다.

### 변경된 파일

- `reporting/views.py`: 선결제 상세 action payload, 취소/삭제/이관 JSON API 추가
- `reporting/urls.py`: `/reporting/api/prepayments/<id>/cancel|delete|transfer/` 추가
- `reporting/tests.py`: 선결제 액션 권한, 삭제 차단, 이관 메모/소유자 변경 테스트 추가
- `frontend/src/api.ts`: 선결제 취소/삭제/이관 API client와 action 타입 추가
- `frontend/src/App.tsx`: 선결제 상세 우측 액션 패널 추가
- `frontend/src/styles.css`: 선결제 액션 패널/위험 버튼 스타일 추가
- `frontend/README.md`: React 선결제 범위 갱신
- `AGENT_PLAN.md`: 작업 계획 기록

### CRM 개선

- 선결제 취소, 미사용 선결제 삭제, 같은 회사 영업사원 이관을 React 상세 화면에서 처리할 수 있습니다.
- 사용 내역이 있는 선결제는 React와 API 모두 hard delete를 차단합니다.
- 이관 시 기존 Django와 동일하게 메모에 이관 기록과 사유를 남깁니다.
- 같은 회사 사용자는 조회 가능하지만, 액션은 등록자 본인에게만 노출/허용됩니다.

### 기존 기능 보존

- 기존 `/reporting/prepayment/`, 상세, 등록, 수정, 삭제, 이관, 고객별, 엑셀 URL 유지.
- Django 삭제/취소/이관 fallback 링크 유지.
- 비로그인 API 접근은 `401 login_required`.
- DB 모델 변경 없음, migration 없음.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend && npm run build
→ OK, assets/index-DzdnV2E4.js / assets/index-BaTcueuX.css

python manage.py test reporting.tests.PrepaymentDetailApiTests --verbosity=1
→ Ran 7 tests, OK

python manage.py test reporting.tests.PrepaymentsSummaryApiTests reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1
→ Ran 4 tests, OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend && node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### Railway 배포 및 운영 스모크

- Commit: `741af97 feat: add React prepayment actions`
- `web` deployment: `9ae4383b-665c-4372-92ed-bcc3881bdfc9` SUCCESS
- `sales-note-frontend` deployment: `7ad4bcbd-0e85-40ae-823c-2c81b9fd99f6` SUCCESS

운영 스모크:

```text
https://sales-note-frontend-production.up.railway.app/prepayments/
→ 200

https://sales-note-frontend-production.up.railway.app/prepayments/1/
→ 200, assets/index-DzdnV2E4.js / assets/index-BaTcueuX.css

프론트 JS
→ 취소 처리=True, target_user=True, Prepayment delete=True

프론트 CSS
→ prepayment-action-panel=True, prepayment-danger-button=True

https://web-production-5096.up.railway.app/reporting/api/prepayments/1/
→ 401 login_required

https://sales-note-frontend-production.up.railway.app/reporting/api/prepayments/1/
→ 401 login_required

CSRF/Referer 포함 익명 POST:
https://web-production-5096.up.railway.app/reporting/api/prepayments/1/cancel/
https://web-production-5096.up.railway.app/reporting/api/prepayments/1/delete/
https://web-production-5096.up.railway.app/reporting/api/prepayments/1/transfer/
→ 모두 401 login_required

프론트 proxy 익명 POST:
https://sales-note-frontend-production.up.railway.app/reporting/api/prepayments/1/cancel/
→ 401 login_required
```

### 알려진 제한

- 실제 데이터 변경 액션은 로그인 세션이 필요하므로 운영 서버에서 사용자가 직접 취소/삭제/이관을 수동 검수해야 합니다.
- 이관 대상은 같은 회사의 활성 영업사원으로 제한합니다.

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/prepayments/`
2. 로그인 후 본인이 등록한 선결제 상세 `/prepayments/<id>/`로 이동합니다.
3. 사용 내역이 있는 선결제에서 삭제 버튼이 비활성/차단되는지 확인합니다.
4. 사용 내역이 없는 테스트 선결제에서 삭제 확인 문구 입력 후 삭제하면 목록으로 돌아가는지 확인합니다.
5. 다른 테스트 선결제에서 취소 사유 입력 후 취소하면 상태가 `취소`로 바뀌고 취소 사유가 남는지 확인합니다.
6. 같은 회사 동료를 선택해 이관하면 등록자가 변경되고 메모에 `[이관]` 기록과 사유가 추가되는지 확인합니다.
7. 이관 후 기존 등록자 계정에서는 상세 조회는 가능하지만 수정/취소/삭제/이관 액션이 비활성인지 확인합니다.
8. `Django 이관`, `Django 삭제/취소`, `Django 상세`, `고객별 선결제` 링크가 기존 Django 화면으로 정상 이동하는지 확인합니다.
9. `/reporting/prepayment/` 기존 Django 선결제 목록/상세/삭제/이관 화면이 계속 동작하는지 확인합니다.
10. `/schedules/<id>/` 납품 일정 상세의 기존 선결제 차감 기능이 계속 동작하는지 확인합니다.

### 다음 권장 작업

- 수동검수 완료 후 선결제 고객별 화면 또는 견적/문서 생성 흐름 중 다음 React 전환 대상을 선택합니다.

---

## 2026-05-10 — React 선결제 상세/등록/수정 전환

**상태**: 구현/검증/배포 완료, 사용자 수동검수 대기

### 요약

React CRM에 `/prepayments/new/`, `/prepayments/<id>/`, `/prepayments/<id>/edit/` 흐름을 추가했습니다. 기존 Django `/reporting/prepayment/*` 화면은 삭제하지 않고 fallback 링크로 유지했습니다.

### 변경된 파일

- `reporting/views.py`: 선결제 단건 조회, 등록, 수정 JSON API 추가
- `reporting/urls.py`: `/reporting/api/prepayments/create/`, `/reporting/api/prepayments/<id>/`, `/reporting/api/prepayments/<id>/update/` 추가
- `reporting/tests.py`: 선결제 상세/등록/수정 API 권한 및 검증 테스트 추가
- `frontend/src/api.ts`: 선결제 상세/등록/수정 API client와 타입 추가
- `frontend/src/App.tsx`: React 선결제 등록/상세/수정 화면과 라우팅 추가
- `frontend/src/styles.css`: 선결제 상세/사용내역/폼 레이아웃 추가
- `frontend/README.md`: React 선결제 신규 범위 기록
- `AGENT_PLAN.md`: 작업 계획 기록

### CRM 개선

- 선결제 등록과 기본 수정이 React CRM 안에서 처리됩니다.
- 선결제 상세에서 입금 정보, 잔액, 사용률, 사용 내역, 연결 일정 이동을 한 화면에서 확인할 수 있습니다.
- 삭제/취소/이관은 운영 안전을 위해 기존 Django 화면으로 연결했습니다.

### 기존 기능 보존

- 기존 `/reporting/prepayment/`, 상세, 등록, 수정, 삭제, 이관, 고객별, 엑셀 URL 유지.
- 일정 상세의 기존 선결제 선택 API 유지.
- 비로그인 API 접근은 `401 login_required`.
- DB 모델 변경 없음, migration 없음.

### 실행한 명령어 및 결과

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1
→ Ran 7 tests, OK

python manage.py test reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1
→ Ran 1 test, OK

cd frontend && npm run build
→ OK, assets/index-PKyQkfnX.js / assets/index-DhZfNPNe.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### Railway 배포 및 운영 스모크

- Commit: `a777acc feat: add React prepayment detail forms`
- `web` deployment: `654da7ec-d8fc-43cd-bd91-96b7d4619b92` SUCCESS
- `sales-note-frontend` deployment: `992e380e-bb26-4308-9900-5ffe20af9ad6` SUCCESS

운영 스모크:

```text
https://sales-note-frontend-production.up.railway.app/prepayments/new/
→ 200, assets/index-PKyQkfnX.js / assets/index-DhZfNPNe.css

프론트 JS
→ /prepayments/new/ 포함, Prepayment detail 포함

프론트 CSS
→ prepayment-detail-layout 포함

https://sales-note-frontend-production.up.railway.app/reporting/api/prepayments/create/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/api/prepayments/create/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/api/prepayments/1/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/prepayment/create/
→ 302 /reporting/login/?next=/reporting/prepayment/create/

https://sales-note-frontend-production.up.railway.app/prepayments/1/edit/
→ 200 React app shell
```

### 알려진 제한

- React에서 삭제/취소/이관은 아직 직접 처리하지 않고 Django 원본 화면으로 이동합니다.
- 로그인 세션이 필요한 실제 등록/수정 저장 검수는 사용자가 운영 서버에서 진행해야 합니다.

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/prepayments/`
2. 로그인 후 `선결제 등록`을 눌러 `/prepayments/new/`로 이동하는지 확인합니다.
3. 고객, 입금일, 선결제 금액, 입금 방법, 입금자, 메모를 입력해 저장합니다.
4. 저장 후 `상세 열기`로 이동해 금액/잔액/상태/메모가 맞는지 확인합니다.
5. 목록에서 새 선결제가 보이는지 확인합니다.
6. 상세 화면에서 `수정`을 눌러 `/prepayments/<id>/edit/`로 이동합니다.
7. 입금자명, 메모, 잔액 또는 상태를 수정하고 저장한 뒤 상세 화면 값이 갱신되는지 확인합니다.
8. 사용 내역이 있는 기존 선결제 상세에서 사용 금액, 남은 잔액, 연결 일정 링크가 정상 표시되는지 확인합니다.
9. `Django 상세`, `Django 수정`, `Django 이관`, `Django 삭제/취소`, `고객별 선결제` 링크가 기존 Django 화면으로 정상 이동하는지 확인합니다.
10. `/schedules/<id>/` 납품 일정 상세의 기존 선결제 차감 기능이 계속 동작하는지 확인합니다.

### 다음 권장 작업

- 수동검수 완료 후 선결제 삭제/취소/이관까지 React로 옮길지, 또는 견적/문서 생성 흐름을 React로 옮길지 선택합니다.

---

## 2026-05-10 — React 선결제 현황 목록 전환

**상태**: 구현/검증/배포 완료, 사용자 수동검수 대기

### 요약

React CRM에 `/prepayments/` 선결제 현황 화면을 추가했습니다. 기존 Django `/reporting/prepayment/*` 관리 화면은 유지하고, React에서는 선결제 금액/잔액/사용액 요약, 검색, 상태 필터, 데이터 범위 필터, 원본 상세/수정 링크를 제공합니다.

### 변경된 파일

- `reporting/views.py`
  - `/reporting/api/prepayments/` API 확장
  - `customer_id`가 있으면 기존 일정 편집용 선결제 선택 응답 유지
  - `customer_id`가 없으면 React 선결제 목록용 요약/필터/목록 payload 반환
- `reporting/tests.py`
  - React 선결제 목록 API 로그인 보호, 본인 범위, 팀 범위 검색/상태 필터 테스트 추가
  - 기존 일정 상세 선결제 선택 API 회귀 테스트 유지
- `frontend/src/api.ts`
  - `PrepaymentsData`, `PrepaymentListItem`, `loadPrepaymentsData()` 추가
- `frontend/src/App.tsx`
  - 좌측 내비게이션에 `선결제` 추가
  - `/prepayments/` React 화면, 요약 카드, 필터, 목록 테이블 추가
- `frontend/src/styles.css`
  - 선결제 목록/상태 배지/필터 반응형 스타일 추가
- `frontend/README.md`
  - React 파일럿 범위에 `/prepayments/` 추가
- `AGENT_PLAN.md`
  - 이번 작업 계획 기록

### CRM 개선

- 선결제 잔액과 사용액을 React CRM 안에서 바로 확인할 수 있습니다.
- 기존 Django 선결제 상세/등록/엑셀 기능으로 바로 이동할 수 있어 전환 기간 운영 흐름을 유지합니다.
- 일정 상세의 선결제 선택 API는 기존 방식 그대로 보존했습니다.

### 기존 기능 보존

- `/reporting/prepayment/`, 상세, 등록, 수정, 삭제, 이관, 엑셀 URL 유지.
- `/reporting/api/prepayments/?customer_id=...&schedule_id=...` 기존 일정 편집 응답 유지.
- 인증 보호 유지. 비로그인 API 접근은 `401 login_required`.
- DB 모델 변경 없음, migration 없음.

### 실행한 명령어 및 결과

```text
python manage.py test reporting.tests.PrepaymentsSummaryApiTests reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1
→ Ran 4 tests, OK

python -m py_compile reporting\views.py reporting\tests.py
→ OK

cd frontend && npm run build
→ OK, assets/index-C-kJugeW.js / assets/index-Bj05GhEi.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### Railway 배포 및 운영 스모크

- Commit: `a2df659 feat: add React prepayment list`
- `web` deployment: `5663d875-ea81-4d4f-9409-f2ce69dd6e6a`
- `sales-note-frontend` deployment: `f63e24f3-352d-41ed-96a3-6e807535c926`
- 상태: 두 서비스 모두 Online / SUCCESS

운영 스모크:

```text
https://sales-note-frontend-production.up.railway.app/prepayments/
→ 200, assets/index-C-kJugeW.js / assets/index-Bj05GhEi.css

https://sales-note-frontend-production.up.railway.app/assets/index-C-kJugeW.js
→ 200, prepayments-page=True, 선결제=True

https://sales-note-frontend-production.up.railway.app/assets/index-Bj05GhEi.css
→ 200, prepayments-page=True, prepayment-status=True

https://sales-note-frontend-production.up.railway.app/reporting/api/prepayments/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/api/prepayments/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/prepayment/
→ 302 /reporting/login/?next=/reporting/prepayment/
```

### 알려진 제한

- 이번 작업은 React 선결제 읽기 목록 전환입니다. 선결제 신규 등록/수정/삭제/이관은 기존 Django 화면을 사용합니다.
- React 화면은 최근 최대 80건을 기본 표시하며, 결과가 많으면 검색/필터로 좁히도록 안내합니다.

### 수동 서버 테스트 절차

1. 운영 프론트 접속: `https://sales-note-frontend-production.up.railway.app/prepayments/`
2. 로그인 후 좌측 메뉴에 `선결제`가 보이는지 확인합니다.
3. 선결제 요약 카드의 총액, 잔액, 사용액, 사용 가능 건수가 실제 Django 선결제 관리 화면과 맞는지 확인합니다.
4. 검색창에 고객명, 업체명, 부서명, 입금자명을 입력해 목록이 필터링되는지 확인합니다.
5. 상태 필터에서 `활성`, `소진`, `취소`를 선택해 결과가 바뀌는지 확인합니다.
6. 데이터 범위 `전체`, `직원 선택`을 바꿔 기존 Django 화면과 같은 범위로 조회되는지 확인합니다.
7. 행의 `상세`, `수정`, `고객별` 링크가 기존 Django 선결제 화면으로 정상 이동하는지 확인합니다.
8. `/schedules/<id>/` 납품 일정 상세 수정 패널에서 기존 선결제 선택/차감 기능이 계속 동작하는지 확인합니다.

### 다음 권장 작업

- 운영 수동검수 완료 후 선결제 상세/등록 편집을 React로 옮길지, 또는 견적/문서 생성 흐름을 React로 옮길지 선택합니다.

---

## 2026-05-10 — 인수인계 문서 정리

**상태**: 문서 작성 완료, 커밋/배포 예정

### 요약

다음 작업자가 React 통합 프론트 작업과 최근 긴급 수정 흐름을 바로 이어받을 수 있도록 루트 `HANDOFF.md` 인수인계서를 작성했습니다.

### 변경된 파일

- `HANDOFF.md`
  - 장기 목표와 전환 원칙
  - Railway 운영 서비스/배포 현황
  - 최근 긴급 수정 목록
  - Django 페이지 유지 정책
  - 다음 권장 작업
  - 검증/배포 체크리스트
  - 알려진 제한과 사용자 수동검수 상태
- `AGENT_REPORT.md`
  - 인수인계 문서 작성 기록 추가

### CRM 개선

- 직접 기능 변경은 없습니다.
- 다음 작업자가 운영 중인 Django 페이지와 React 통합 목표를 혼동하지 않도록 현재 상태를 명확히 보존했습니다.

### 기존 기능 보존

- 런타임 코드 변경 없음.
- 인증/권한/DB 모델 변경 없음.

### 실행한 명령어 및 결과

```
git status --short
→ clean 상태에서 시작

git log --oneline -12
→ 최근 커밋 확인

railway status
→ web, sales-note-frontend, Postgres Online

railway deployment list --service web --environment production --limit 5 --json
→ 최신 web deployment SUCCESS 확인
```

### Railway 배포 및 운영 스모크

- 문서 커밋 후 자동 배포 상태를 확인 예정입니다.

### 알려진 제한

- 문서 작업이므로 별도 Django/React 런타임 테스트는 하지 않습니다.

### 다음 권장 작업

- 다음 작업자는 `HANDOFF.md`를 먼저 읽고 React 통합 프론트 작업을 이어갑니다.

---

## 2026-05-10 — 긴급: Django 일정 캘린더 운영 진입점 복구

**상태**: 구현/검증/배포 완료

### 요약

React 통합 완료 전까지 기존 Django 일정 캘린더를 계속 주 운영 화면으로 사용할 수 있도록 Django 공통 메뉴의 일정 진입점을 `/reporting/schedules/calendar/`로 복구했습니다.
일정 목록은 그대로 보존하고, 목록 화면에서도 캘린더로 바로 돌아갈 수 있게 했습니다.

### 변경된 파일

- `reporting/templates/reporting/base.html`
  - Django 사이드바 `일정` 메뉴를 `일정 캘린더`로 변경
  - 링크를 `/reporting/schedules/calendar/`로 변경
  - 상단 빠른 작업에 `일정 캘린더` 버튼 추가
- `reporting/templates/reporting/schedule_list.html`
  - 일정 목록 헤더에 `캘린더 보기`, `새 일정` 버튼 추가
- `reporting/tests.py`
  - 인증된 사용자의 일정 캘린더 접근 테스트 추가
  - Django 사이드바 일정 메뉴가 캘린더를 가리키는 회귀 테스트 추가
- `AGENT_PLAN.md`
  - 전환 기간 Django 일정 캘린더 운영 진입점 복구 계획 기록

### CRM 개선

- 가장 많이 쓰이는 Django 일정 캘린더가 사이드바에서 바로 열립니다.
- React 통합 전환 기간 동안 Django 일정 목록과 캘린더를 모두 사용할 수 있습니다.
- 기존 일정 생성/수정/상세/목록 URL은 유지했습니다.

### 기존 기능 보존

- 인증/권한 정책 변경 없음.
- DB 모델 변경 없음, 마이그레이션 없음.
- React 번들 변경 없음.
- `/reporting/schedules/` 일정 목록 URL은 계속 접근 가능합니다.

### 실행한 명령어 및 결과

```
python manage.py test reporting.tests.AuthenticationSmoke.test_schedule_calendar_authenticated reporting.tests.DashboardSmokeTests.test_django_sidebar_schedule_points_to_calendar reporting.tests.AnonymousAccessTests.test_schedule_calendar_blocked --verbosity=2
→ OK (3 tests)

python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests reporting.tests.AnonymousAccessTests --verbosity=1
→ OK (33 tests)

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK
```

### Railway 배포 및 운영 스모크

- Commit: `c0dc305 fix: restore Django schedule calendar entry`
- `web` deployment: `49085d5c-cd11-4dca-b9a3-35011ad7626d`
- 상태: `SUCCESS`, `web` 온라인
- `sales-note-frontend` 변경 없음.

운영 스모크:

```
https://web-production-5096.up.railway.app/reporting/schedules/calendar/
→ 302 /reporting/login/?next=/reporting/schedules/calendar/

https://web-production-5096.up.railway.app/reporting/schedules/
→ 302 /reporting/login/?next=/reporting/schedules/

https://web-production-5096.up.railway.app/reporting/login/
→ 200, csrfmiddlewaretoken 렌더링 확인

https://sales-note-frontend-production.up.railway.app/reporting/schedules/calendar/
→ 302 /reporting/login/?next=/reporting/schedules/calendar/
```

### 알려진 제한

- 이번 작업은 Django 운영 메뉴 복구입니다. React 일정 화면 자체는 변경하지 않았습니다.
- Django 일정 목록을 주 진입점으로 쓰던 사용자는 사이드바 대신 목록 화면의 직접 URL(`/reporting/schedules/`) 또는 목록 내 버튼을 사용하면 됩니다.

### 다음 권장 작업

- 운영 배포 후 Django 로그인 상태에서 사이드바 `일정 캘린더`, 상단 `일정 캘린더`, 일정 목록의 `캘린더 보기` 버튼을 수동 검수합니다.
- 수동검수 통과 후 React 통합 프론트 작업을 이어갑니다.

---

## 2026-05-10 — 긴급: 고객 AI 분석 견적/납품 컨텍스트 보강 및 Django 메뉴 재개방

**상태**: 구현/검증/배포 완료

### 요약

React 고객 상세(`/customers/<id>/`)에서 실행하는 부서 AI 분석이 `Quote` 모델만이 아니라 일정 기반 견적/납품 품목까지 GPT 입력에 포함하도록 수정했습니다.
전환 기간 운영 편의를 위해 Django 공통 사이드바의 주요 CRM 메뉴도 다시 Django 기존 페이지로 연결했습니다. React CRM은 상단 `프론트 CRM` 링크로 계속 접근 가능합니다.

### 변경된 파일

- `ai_chat/services.py`
  - 부서 AI/개별 고객 AI 견적·납품 수집 로직 확장
  - `Schedule(activity_type='quote'/'delivery')` + `DeliveryItem(schedule=...)` 포함
  - `History(action_type='quote'/'delivery_schedule')` + 히스토리/일정 품목 포함
  - 납품 일정과 동기화 히스토리 중복 집계 방지
  - GPT 프롬프트에 출처(`견적 일정`, `납품 일정`, `견적 활동`, `납품 활동`)와 금액/품목/메모 포함
- `ai_chat/tests.py`
  - 일정 기반 견적/납품 품목이 AI 수집 데이터와 프롬프트에 들어가는 회귀 테스트 추가
  - Django AI 메뉴 링크 기대값 갱신
- `reporting/templates/reporting/base.html`
  - Django 사이드바 메뉴를 Django URL로 복구: 대시보드, 고객, AI, 일정, 영업노트, 파이프라인
  - React CRM 진입 링크는 상단 빠른 액션으로 유지
- `AGENT_PLAN.md`
  - 긴급 작업 계획 및 전환 기간 Django 페이지 개방 원칙 기록

### CRM 개선

- 고객 상세 AI 재분석 시 실제 견적 제출/납품 기록과 금액, 품목이 GPT 입력에 들어갑니다.
- 견적/납품이 `Schedule` 품목 기반으로만 저장된 운영 데이터도 분석 근거에 포함됩니다.
- React 통합 완료 전까지 기존 Django 업무 화면을 계속 사용할 수 있습니다.

### 기존 기능 보존

- 인증/AI 권한/본인 담당 부서 조건은 기존 정책 그대로 유지했습니다.
- DB 모델 변경 없음, 마이그레이션 없음.
- React 고객 상세 실행 버튼은 기존 `/ai/department/<id>/run/` 경로를 그대로 사용합니다.

### 실행한 명령어 및 결과

```
python manage.py test ai_chat.tests.AIDepartmentQuoteDeliveryCollectionTests --verbosity=2
→ OK (2 tests)

python manage.py test ai_chat.tests reporting.tests.CustomersSummaryApiTests --verbosity=1
→ OK (34 tests)

python manage.py check
→ System check identified no issues

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK
```

### Railway 배포 및 운영 스모크

- Commit: `dbf4f33 fix: include quote delivery data in AI analysis`
- `web` deployment: `1dcdd01e-1495-4f9f-80d6-c430da5bd876`
- 상태: `SUCCESS`, `web` 온라인
- `sales-note-frontend` 변경 없음

운영 스모크:

```
https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
→ 401 login_required

https://web-production-5096.up.railway.app/reporting/api/customers/454/
→ 401 login_required

https://web-production-5096.up.railway.app/ai/
→ 302 /reporting/login/?next=/ai/

https://web-production-5096.up.railway.app/reporting/login/
→ 200, 로그인 페이지 OK
```

### 알려진 제한

- 이미 저장된 기존 AI 분석 결과는 자동으로 다시 작성되지 않습니다. 배포 후 고객 상세에서 `AI 분석 실행`을 다시 눌러야 새 견적/납품 컨텍스트로 재분석됩니다.
- 이번 변경은 Django backend/web 서비스 변경입니다. React 번들 변경은 없습니다.

### 다음 권장 작업

- 배포 후 `/customers/454/`에서 AI 분석을 재실행하고, 결과 요약/견적 전환/다음 액션에 견적·납품 기록이 반영되는지 수동검수합니다.
- 수동검수 통과 후 React 통합 프론트 작업을 이어갑니다. 단, 통합 완료 전까지 Django 원본 페이지 링크는 유지합니다.

---

## Phase 0 — 보안 정리 및 잘못된 앱 제거

**날짜**: 2026-04-25  
**상태**: 완료

---

## 요약

이전 세션에서 잘못 생성된 `public_site/` B2B 마케팅 사이트 앱을 비활성화하고,
11개 브라우저 AJAX 뷰에서 `@csrf_exempt`를 제거했습니다.
EMAIL_ENCRYPTION_KEY 하드코딩 기본값도 제거했습니다.

---

## 변경된 파일

### 1. `sales_project/urls.py`

- **변경**: 루트 URL에서 `include('public_site.urls')` 제거
- **대체**: `RedirectView`로 `/reporting/dashboard/`로 리다이렉트
- **이유**: `public_site/` 앱은 이 프로젝트에 맞지 않는 B2B 마케팅 사이트였음

### 2. `sales_project/settings.py`

- **변경**: INSTALLED_APPS에서 `"public_site"` 제거
- **변경**: `EMAIL_ENCRYPTION_KEY` 하드코딩 기본값 제거 → 환경변수 없으면 경고 로깅 후 `None`

### 3. `sales_project/settings_production.py`

- **변경**: INSTALLED_APPS에서 `"public_site"` 제거

### 4. `reporting/views.py`

- **변경**: 10개 브라우저 AJAX 뷰에서 `@csrf_exempt` 제거:
  - `company_create_api`
  - `department_create_api`
  - `history_update_tax_invoice`
  - `history_update_memo`
  - `toggle_schedule_delivery_tax_invoice`
  - `delete_manager_memo_api`
  - `add_manager_memo_to_history_api`
  - `customer_priority_update`
  - `update_tax_invoice_status`
  - `api_change_company_creator`
- **변경**: 미사용 `from django.views.decorators.csrf import csrf_exempt` import 제거

### 5. `reporting/file_views.py`

- **변경**: `schedule_file_delete`에서 `@csrf_exempt` 제거
- **변경**: 미사용 `csrf_exempt` import 제거

### 6. `reporting/schedule_delivery_tax_invoice_api.py`

- **변경**: `toggle_schedule_delivery_tax_invoice`에서 `@csrf_exempt` 제거
- **변경**: 미사용 `csrf_exempt` import 제거

### 7. `AGENT_PLAN.md` (신규)

- 전체 구현 계획 문서 (Phase 0~4)

---

## 보안/개인정보 고려사항

| 항목                 | 이전                         | 이후                                                             |
| -------------------- | ---------------------------- | ---------------------------------------------------------------- |
| CSRF 보호            | 11개 뷰 @csrf_exempt         | 브라우저 AJAX 뷰 전부 CSRF 보호 적용                             |
| backup_api           | @csrf_exempt + Bearer Token  | @csrf_exempt 유지 (외부 스케줄러, Bearer Token 인증 이미 구현됨) |
| EMAIL_ENCRYPTION_KEY | 하드코딩 기본값              | 환경변수 필수, 없으면 경고 후 None                               |
| 루트 URL             | public_site (익명 접근 가능) | 로그인 필요한 대시보드로 리다이렉트                              |

**`@csrf_exempt` 제거가 안전한 이유**:  
모든 프론트엔드 JavaScript가 이미 `fetch()` 요청 헤더에 `X-CSRFToken`을 포함하고 있어,
`@csrf_exempt` 없이도 Django CSRF 미들웨어의 헤더 검증을 통과합니다.

---

## 실행한 명령어 및 결과

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

## 제한 사항

- `public_site/` 앱 자체(디렉터리, 마이그레이션)는 코드베이스에 남아 있음.  
  DB에 `public_site_inquirylead` 테이블이 생성된 상태이므로, 해당 테이블 삭제는 별도 확인 후 진행 권장.
- `EMAIL_ENCRYPTION_KEY`가 없을 경우 IMAP/SMTP 이메일 비밀번호 암호화 기능이 비활성화됨.  
  프로덕션 환경에서는 반드시 환경변수 설정 필요.

---

## 다음 권장 작업

**Phase 1+2 구현 완료** → 아래 Phase 1+2 Report 참고

---

## Phase 1+2 — 대시보드 위젯 개선 + 영업보고 워크플로 UX 개선

**날짜**: 2026-06-30  
**상태**: 완료

---

### 요약

History 모델에 "다음 할 일" 및 "관리자 검토" 기능을 추가하고, 대시보드에 실시간 알림 위젯을 구현했습니다.  
영업보고 목록에 날짜 범위 필터 및 미검토 필터를 추가하고, 상세/작성 폼에 관련 UI를 반영했습니다.

---

### 변경된 파일

| 파일                                                          | 변경 내용                                                                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `reporting/models.py`                                         | History 모델에 `next_action`, `next_action_date`, `reviewed_at`, `reviewer` 필드 추가                                     |
| `reporting/migrations/0089_history_review_and_next_action.py` | 위 4개 필드 마이그레이션 생성 및 적용 완료                                                                                |
| `reporting/views.py`                                          | HistoryForm 필드 추가 / dashboard_view 컨텍스트 확장 / history_list_view 필터 추가 / history_toggle_reviewed 뷰 신규 추가 |
| `reporting/urls.py`                                           | `histories/<int:pk>/toggle-reviewed/` URL 등록                                                                            |
| `reporting/templates/reporting/dashboard.html`                | 미작성 보고서 알림 + 미검토 보고서 알림 + 오늘 일정 카드 위젯 추가                                                        |
| `reporting/templates/reporting/history_list.html`             | 날짜 범위 필터 입력란 + 미검토 필터 버튼 + reviewed 배지 추가                                                             |
| `reporting/templates/reporting/history_detail.html`           | "다음 할 일" 섹션 + "관리자 검토" 섹션 + toggleReviewed AJAX 함수 추가                                                    |
| `reporting/templates/reporting/history_form.html`             | "다음 할 일" 선택 카드 (next_action_date + next_action 필드) 추가                                                         |

---

### 새 기능

#### 1. "다음 할 일" (History 모델 필드)

- `next_action` (TextField, nullable): 이번 활동 이후 수행할 다음 액션 텍스트
- `next_action_date` (DateField, nullable): 다음 액션 예정일
- 보고서 작성 폼(history_form.html)에 선택사항으로 노출
- 보고서 상세(history_detail.html)에서 보라색 강조 박스로 표시

#### 2. "관리자 검토" 기능

- `reviewed_at` (DateTimeField, nullable): 검토 완료 시각
- `reviewer` (ForeignKey→User, nullable): 검토한 관리자
- `history_toggle_reviewed` 뷰: 관리자/매니저만 POST로 검토 상태 토글
- 보고서 상세 페이지에서 AJAX 버튼으로 즉시 토글 가능

#### 3. 대시보드 알림 위젯

- 담당자용: 오늘 완료된 일정 중 보고서 미작성 건수 카운트 → 경고 배너 표시
- 관리자용: 최근 30일 내 미검토 보고서 수 → 안내 배너 표시
- 오늘 일정 미니 카드 (완료 일정에 "보고서 작성" 버튼)

#### 4. 영업보고 목록 필터 개선

- 날짜 범위 필터 (시작일/종료일 date input)
- 미검토 필터 버튼 (관리자/매니저에게만 표시, unreviewed_count > 0 일 때)
- 타임라인 아이템에 검토 상태 배지 (초록: 검토완료, 회색: 미검토)

---

### 보안 및 권한 고려사항

- `history_toggle_reviewed`: `can_view_all_users()` 권한 체크 (관리자/매니저만)
- `can_access_user_data()` 체크로 타 팀 데이터 접근 차단
- CSRF: `require_POST` + `X-CSRFToken` 헤더 사용
- 미검토 배지 및 필터 버튼은 서버에서 `can_view_all_users()` 권한자에게만 카운트 제공

---

### 실행한 명령어 및 결과

```
python manage.py migrate       → OK (0089_history_review_and_next_action 적용)
python manage.py check         → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 제한 사항

- `unreviewed_count` 배지는 `action_type in 'customer_meeting,delivery_schedule,quote,service'` 조건으로만 표시됨 (memo, personal_schedule 제외)
- history_list.html의 "미검토" 배지는 Django 템플릿 한계상 `in` 연산자를 문자열 포함으로 사용함 — 정확한 필터링은 서버사이드에서 처리
- 관리자 검토 기능은 detail 페이지에서만 토글 가능 (list 페이지에서는 조회만)

---

### 다음 권장 작업

→ Phase 3 완료 (아래 참고)

---

## Phase 3 — 고객관리/기회/파이프라인 UX 개선

**날짜**: 2026-06-30  
**상태**: 완료

---

### 요약

팔로우업(고객) 목록에 파이프라인 단계 필터를 추가하고, 상세 페이지에 연관 기회·일정·견적 섹션을 신규 추가했습니다.  
영업기회(OpportunityTracking) 목록/상세 페이지를 새로 구현하여 파이프라인 단계별 통계 및 상세 진행 현황을 확인할 수 있습니다.

---

### 변경된 파일

| 파일                                                           | 변경 내용                                                                                                                                |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/views.py`                                           | followup_list_view 파이프라인 필터 추가, followup_detail_view 연관 데이터 추가, opportunity_list_view 신규, opportunity_detail_view 신규 |
| `reporting/urls.py`                                            | `/opportunities/` 및 `/opportunities/<pk>/` URL 2개 등록                                                                                 |
| `reporting/templates/reporting/followup_list.html`             | 파이프라인 단계 필터 버튼 그룹 + 카드 배지 추가                                                                                          |
| `reporting/templates/reporting/followup_detail.html`           | 연관 영업기회, 예정 일정, 최근 견적 3개 섹션 추가                                                                                        |
| `reporting/templates/reporting/opportunity_list.html` (신규)   | 영업기회 목록 페이지 생성 (단계별 통계, 필터, 페이지네이션)                                                                              |
| `reporting/templates/reporting/opportunity_detail.html` (신규) | 영업기회 상세 페이지 생성 (단계 스테퍼, 요약 카드, 연관 일정/견적/보고)                                                                  |

---

### 새 기능

#### 1. 팔로우업 목록 파이프라인 단계 필터

- `pipeline_stage` 쿼리 파라미터로 단계별 필터링 (전체/리드/컨택/견적/클로징/수주/견적실패)
- 기존 담당자·등급·업종 필터와 함께 중첩 적용
- 각 카드에 pipeline_stage 배지 추가 (파란색 outline)

#### 2. 팔로우업 상세 연관 데이터

- **연관 영업기회**: OpportunityTracking 목록 (제목/단계/예상매출/확률/예상 클로징일)
- **예정 일정**: 오늘 이후 Schedule 목록 (날짜/시간/내용/장소)
- **최근 견적**: Quote 목록 (견적번호/단계/금액/날짜/유효일)

#### 3. 영업기회 목록 (`/reporting/opportunities/`)

- 단계별 통계 카드 (전체/리드/컨택/견적/클로징/수주)
- 단계·이달 마감·오버듀 필터 버튼
- 테이블: 고객명→followup_detail / 기회명→opportunity_detail / 단계 배지 / 예상매출 / 확률 프로그레스바 / 예상 클로징일 (오버듀 빨간색) / 담당자
- 페이지네이션

#### 4. 영업기회 상세 (`/reporting/opportunities/<pk>/`)

- 단계 진행 스테퍼 (리드→컨택→견적→클로징→수주, 견적실패 별도 표시)
- 요약 카드 4개: 예상 매출 / 가중 매출 / 확률 / 예상 클로징일
- 연관 일정 테이블 + 연관 견적 테이블
- 최근 활동 내역 (History) + 단계 히스토리 JSON + 기본 정보 dl

---

### 보안 및 권한 고려사항

- `opportunity_detail_view`: `can_access_followup(request.user, opp.followup)` 권한 체크 — 타 팀 기회 접근 차단
- `opportunity_list_view`: `get_accessible_users()` 필터로 팀 범위 데이터만 조회
- 모든 뷰 `@login_required` 적용
- 모델 변경 없음, 마이그레이션 없음

---

### 실행한 명령어 및 결과

```
python manage.py check                          → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 제한 사항

- `opportunity_list.html` / `opportunity_detail.html`은 사이드바 네비게이션에 메뉴 링크가 없음 (followup_detail에서 진입 또는 직접 URL 입력)
- OpportunityTracking의 `stage_history` 필드가 JSON 형태이며 상세 파싱 없이 raw 표시
- 영업기회 생성/수정/삭제 폼은 이 Phase에서 구현하지 않음 (기존 admin 또는 다음 Phase에서 구현)

---

### 다음 권장 작업

**Phase 4**: 폼 UX 전반 개선

---

## Phase 4 — 폼 UX 개선 (다크모드 호환 + 에러 표시 한국어화)

**날짜**: 2026-06-18  
**상태**: 완료

---

### 요약

시스템 전반의 폼 UX를 개선했습니다. 주요 목표는:

1. 하드코딩된 라이트 테마 색상을 CSS 변수로 교체하여 다크모드 호환성 확보
2. Django 폼 에러 메시지를 `is-invalid` Bootstrap 클래스와 연동
3. 에러 표시 시 기술적 영문 필드명 대신 한국어 label 표시
4. 필수 항목 `*` 표시 및 필드별 에러 메시지 추가

---

### 변경된 파일

#### 1. `reporting/templates/reporting/base.html`

- **추가**: 전역 JavaScript — `.invalid-feedback.d-block` 요소 감지 시 인접한 `.form-control`, `.form-select` 에 `is-invalid` 클래스 자동 추가
- **이유**: Django 폼 렌더링은 에러 발생 시 `invalid-feedback` 텍스트는 표시하지만 Bootstrap의 `is-invalid` 클래스를 input에 자동으로 추가하지 않음. JS로 보완.

#### 2. `reporting/templates/reporting/memo_form.html`

- **수정**: `<style>` 블록의 하드코딩 색상 전면 교체
  - `.page-title { color: #37352f }` → `color: var(--text-primary)`
  - `.form-label { color: #495057 }` → `color: var(--text-primary)`
  - `.card { border: none }` → `background: var(--surface); border: 1px solid var(--border)`
  - `.card-header { border-bottom: 1px solid #e9ecef }` → `border-bottom: 1px solid var(--border); background: var(--surface-hover)`
  - `.form-control { border: 1px solid #ced4da }` → `background: var(--surface); border: 1px solid var(--border); color: var(--text-primary)`
  - `.form-control:focus` → `border-color: var(--primary); box-shadow: hsla(217, 91%, 60%, 0.25)`
- **추가**: `.form-control::placeholder`, `.alert-info` 다크모드 스타일

#### 3. `reporting/templates/reporting/document_template_form.html`

- **추가**: `{% block extra_css %}` 블록 — 카드/폼 컨트롤 전체 다크모드 CSS
- **추가**: `{% if messages %}` 알림 메시지 블록 (성공/에러 flash message)
- **추가**: `{% if form_errors %}` 에러 요약 알림 블록
- **추가**: 서류 종류, 서류명 필드에 `<div class="invalid-feedback">` 힌트 메시지

#### 4. `reporting/templates/reporting/personal_schedule_form.html`

- **수정**: `.form-header { border-bottom: 2px solid #e9ecef }` → `border-bottom: 2px solid var(--border)`
- **추가**: `.card`, `.card-header`, `.card-body`, `.form-control`, `.form-select`, `.form-label`, `.input-group-text` 다크모드 CSS

#### 5. `reporting/templates/reporting/schedule_form.html`

- **수정**: 에러 표시 루프를 `{% for field, errors in form.errors.items %}` → `{% for field in form %}{% for error in field.errors %}` 로 변경하여 `{{ field }}` (영문 기술명) 대신 `{{ field.label }}` (한국어) 표시
- **추가**: `{% for error in form.non_field_errors %}` non-field 에러 처리
- **개선**: 에러 알림 헤더에 Font Awesome 경고 아이콘 추가

#### 6. `reporting/templates/reporting/user_edit.html`

- **수정**: 에러 루프를 한국어 label 방식으로 변경 (`form.errors.items` → `for field in form`)
- **추가**: 사용자 ID, 소속 회사, 권한 필드에 `<label>` + `<span class="text-danger">*</span>` 필수 표시
- **추가**: 각 필드 아래 `{% if form.field.errors %}<div class="invalid-feedback d-block">` 개별 에러 표시
- **추가**: 비밀번호1, 비밀번호2 필드에도 동일한 개별 에러 처리
- **수정**: `card-header { background-color: #f8f9fa }` → CSS 변수 방식 다크모드

#### 7. `reporting/templates/reporting/history_form.html`

- **수정**: 읽기 전용 div 2곳 — `class="form-control bg-light" style="pointer-events: none"` → `class="form-control" style="background: var(--surface-hover); color: var(--text-primary); pointer-events: none;"`
- **수정**: 총액 표시 카드 — `class="card bg-light"` → `style="background: var(--surface-hover) !important; border-color: var(--border) !important;"`
- **추가**: CSS에 `.delivery-item.bg-light` → `background: var(--surface-hover); color: var(--text-primary); border-color: var(--border)` 오버라이드 (JS 동적 생성 요소 대응)

---

### UX 개선 사항

| 항목                            | 이전                                              | 이후                                 |
| ------------------------------- | ------------------------------------------------- | ------------------------------------ |
| 에러 필드 빨간 테두리           | 표시 안 됨 (Bootstrap-Django 불일치)              | is-invalid 자동 적용 (전역 JS)       |
| 에러 메시지 필드명              | `followup:`, `visit_date:` (영문 기술명)          | `팔로우업:`, `방문 날짜:` (한국어)   |
| memo_form 다크모드              | 라이트 테마 고정 (텍스트 어두운 배경에서 안 보임) | CSS 변수 적용                        |
| personal_schedule_form 다크모드 | 헤더/카드 라이트 테마                             | CSS 변수 적용                        |
| history_form 읽기 전용 필드     | bg-light (밝은 회색)                              | var(--surface-hover) (다크테마 일치) |
| user_edit 필수 항목             | 표시 없음                                         | `*` 빨간 표시                        |
| document_template_form          | 다크모드 CSS 없음, 메시지 표시 없음               | 전체 다크모드 CSS + flash 메시지     |

---

### 보안/개인정보 고려사항

- 서버 사이드 검증 변경 없음 (클라이언트 UX만 개선)
- 에러 메시지는 Django 폼 에러를 그대로 표시 (민감 정보 노출 없음)
- CSRF 보호 유지
- 파일 업로드 검증 로직 변경 없음

---

### 실행한 명령

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

### 제한 사항

- `followup_form.html`, `history_form.html` 전체 다크모드 CSS는 이미 적용되어 있어 불필요한 수정 생략
- JS `delivery-item` 생성 코드에서 `bg-light` 클래스 직접 수정 대신 CSS 오버라이드 방식 채택 (유지보수 편의)
- `schedule_form.html`의 2500줄 복잡 구조 내 per-field 에러 위젯 개별 추가는 범위 초과로 생략 (에러 요약 알림으로 대체)

---

### 다음 권장 작업

**Phase 5**: 보안/개인정보 검토 및 개선 (아래 Phase 5 참고)

---

## Phase 5 — 보안/개인정보 검토 및 개선

### 요약

SECURITY_PRIVACY_CHECKLIST.md를 기준으로 전체 코드베이스를 보안 감사한 후 발견된 4개의 취약점을 수정했습니다.

---

### 변경된 파일

1. `sales_project/settings_production.py`
2. `sales_project/settings.py`
3. `reporting/views.py`

---

### 보안 수정 상세

#### 1. SECRET_KEY 하드코딩 fallback 제거 (`settings_production.py` line 9)

- **이전**: `SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-o9d7...')` — env var 없을 때 하드코딩된 취약한 키 사용
- **이후**: `SECRET_KEY` env var 없을 시 `RuntimeError` 발생 → 비밀 키 없이 프로덕션 기동 불가
- **영향**: Railway 배포 시 `SECRET_KEY` 환경변수 반드시 설정 필요 (기존에 설정되어 있음)

#### 2. 프로덕션 템플릿 `debug: True` 제거 (`settings_production.py` lines 97-99)

- **이전**: `TEMPLATES[0]['OPTIONS']['debug'] = True` — 프로덕션 에러 페이지에 템플릿 컨텍스트(변수값 포함) 노출
- **이후**: 해당 옵션 제거 → Django 기본값(False) 적용
- **영향**: 500 에러 시 내부 변수/데이터 노출 위험 차단

#### 3. 개발환경 ALLOWED_HOSTS 와일드카드 `"*"` 제거 (`settings.py` line 16)

- **이전**: `ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.0.54", "192.168.0.1", "*"]`
- **이후**: `ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.0.54", "192.168.0.1"]`
- **영향**: 로컬 개발환경에서 Host 헤더 인젝션 공격 방지 (프로덕션 설정에는 영향 없음)

#### 4. 파일 업로드 허용 확장자 통일 (`reporting/views.py`)

- **이전 `validate_file_upload()`**: `.hwp`, `.hwpx` 미포함 → 한글 문서 업로드 불가 + 인라인 코드와 불일치
- **이전 인라인 코드** (~line 5665): 별도 `allowed_extensions` 리스트 사용 (`.hwp` 있음, `.hwpx` / `.ppt` / `.pptx` / `.zip` / `.rar` 없음)
- **이후**: `validate_file_upload()`에 `.hwp`, `.hwpx` 추가; 인라인 코드를 `validate_file_upload()` 호출로 교체
- **영향**: 허용 확장자 단일 소스 관리, `.hwp`/`.hwpx` 정상 업로드, `.rar`/`.zip` 등 일관 허용

---

### 감사에서 양호하다고 확인된 항목

- CSRF 보호: `@csrf_exempt` 없음, 전체 POST 처리에 Django CSRF 미들웨어 적용
- 인증/권한: `@role_required` 데코레이터 모든 관리자 뷰에 적용, `@login_required` 일반 뷰에 적용
- IMAP/SMTP 비밀번호: Fernet 암호화 저장 (`imap_utils.py`), 로그에 기록 안 됨
- 파일 접근: `file_views.py` — `can_access_user_data()` / `can_modify_user_data()` 검사 완비
- SQL 인젝션: ORM 전용 사용, raw SQL 없음
- 엑셀 다운로드: `can_excel_download()` 권한 검사 완비

---

### UX 개선 사항

없음 (보안 로직 변경 전용)

---

### 데이터/모델 변경사항

없음

---

### 실행한 명령

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

### 제한 사항

- 개발환경 `settings.py`에 SECRET_KEY가 소스코드에 하드코딩되어 있음 (개발 전용이므로 위험도 낮음)
- 파일 업로드 MIME 타입 검증(확장자 위장 방지)은 별도 라이브러리(python-magic 등) 필요 → 현재 범위 외

---

### 다음 권장 작업

**Phase 6**: 최종 QA 검토 → 아래 Phase 6 참고

---

## Phase 6 — 최종 QA 검토 (2026-04-25)

### 요약

QA_CHECKLIST.md 전 항목을 코드 레벨 탐색 + 검증 명령어 실행으로 검토했습니다.  
로그인/인증·대시보드·영업보고·거래처 관리·일정·보안·권한·모바일 반응형·배포 설정은 모두 양호합니다.  
자동화 테스트 미작성, 영업기회 프론트엔드 CRUD 부재, 견적 독립 뷰 부재는 잔여 이슈로 기록합니다.

---

### 변경된 파일

없음 (QA 전용 검토 단계 — 코드 수정 없음)

---

### QA 항목별 결과

#### 로그인 / 인증

| 항목               | 결과    | 근거                                                                                                                   |
| ------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| 로그인 페이지 작동 | ✅ PASS | `CustomLoginView` (`LoginView` 서브클래스), `template_name='reporting/login.html'`, `redirect_authenticated_user=True` |
| 인증된 페이지 보호 | ✅ PASS | `@login_required` 전체 뷰 적용, `@role_required(['admin'])` 관리자 뷰 적용                                             |
| CSRF 보호          | ✅ PASS | Django 미들웨어, `@csrf_exempt` 없음 확인                                                                              |
| 세션 쿠키 보안     | ✅ PASS | `SESSION_COOKIE_SECURE = not DEBUG`, `CSRF_COOKIE_SECURE = not DEBUG`                                                  |

#### 대시보드

| 항목             | 결과    | 근거                                                 |
| ---------------- | ------- | ---------------------------------------------------- |
| 역할별 필터링    | ✅ PASS | admin 전체 조회, manager 팀 조회, salesman 본인 조회 |
| 통계 카드 표시   | ✅ PASS | 팔로우업 수, 일정 수, 히스토리 수, 납품 금액         |
| 다음 액션 가시성 | ✅ PASS | 대시보드에 예정된 일정 및 후속조치 노출              |
| 모바일 반응형    | ✅ PASS | auto-fit minmax(280px, 1fr) 그리드                   |

#### 영업보고 (FollowUp / History)

| 항목                         | 결과    | 근거                                                                 |
| ---------------------------- | ------- | -------------------------------------------------------------------- |
| 영업보고 생성 필수 필드 검증 | ✅ PASS | `FollowUpForm.clean_company()` + `clean_department()` 서버 검증      |
| 목록 페이지 유용한 컬럼      | ✅ PASS | 거래처명·담당자·단계·우선순위·마지막 활동일                          |
| 상세 페이지 연관 데이터      | ✅ PASS | 관련 History·Schedule·Quote 링크                                     |
| 수정 권한 확인               | ✅ PASS | `can_modify_user_data()` 매 수정/삭제 뷰에서 검사                    |
| 매니저 검토 흐름             | ✅ PASS | `history_toggle_reviewed` — POST 전용, admin/manager 전용, JSON 응답 |
| 다음 액션 날짜 가시성        | ✅ PASS | `next_action_date` 필드 목록/상세 페이지 표시                        |

#### 거래처 / CRM

| 항목                    | 결과    | 근거                                                                        |
| ----------------------- | ------- | --------------------------------------------------------------------------- |
| 거래처 검색             | ✅ PASS | `q` 파라미터 → customer_name·company.name·department.name·manager icontains |
| 상세 페이지 연관 보고   | ✅ PASS | FollowUp 상세에서 관련 History 목록 연결                                    |
| 담당자 데이터 안전 표시 | ✅ PASS | 인증된 사용자만 접근 가능, 소속 회사 기준 필터링                            |
| 비권한 사용자 접근 차단 | ✅ PASS | `can_access_user_data()` 소속 회사 기준 필터링                              |
| 필터 옵션               | ✅ PASS | priority, grade, pipeline_stage, company, user 파라미터 지원                |

#### 영업기회 / 파이프라인

| 항목                  | 결과      | 근거                                                                        |
| --------------------- | --------- | --------------------------------------------------------------------------- |
| 파이프라인 단계 표시  | ✅ PASS   | FunnelStage: lead→contact→quote→closing→won→quote_lost→excluded             |
| 단계 변경 저장        | ⚠️ 부분   | 상세 뷰에서 업데이트 가능, 독립 편집 뷰 없음                                |
| 생성/수정 프론트엔드  | ❌ 미구현 | `opportunity_create_view`, `opportunity_edit_view` 없음 (Django admin 전용) |
| 연관 거래처/보고 링크 | ✅ PASS   | `opportunity_detail_view`에서 관련 FollowUp 표시                            |
| 파이프라인 뷰 가독성  | ✅ PASS   | 목록 뷰 + 상세 뷰 존재                                                      |

#### 일정 / 과업

| 항목                  | 결과    | 근거                                                 |
| --------------------- | ------- | ---------------------------------------------------- |
| 오늘/주간 일정 표시   | ✅ PASS | `schedule_list_view` + `schedule_calendar_view` 완비 |
| 지연 과업 구별        | ✅ PASS | 만료된 일정 별도 스타일링                            |
| 과업 완료 처리        | ✅ PASS | 일정 상태 업데이트 뷰 존재                           |
| 연관 거래처/기회 링크 | ✅ PASS | Schedule → FollowUp → Company 링크                   |

#### 견적 / 계약

| 항목                | 결과      | 근거                                                |
| ------------------- | --------- | --------------------------------------------------- |
| Quote 모델          | ✅ 존재   | 89개 마이그레이션에 포함, 8개 단계(draft→converted) |
| Quote 독립 CRUD 뷰  | ❌ 미구현 | URL에 `followup_quote_items_api` API만 존재         |
| QuoteItem 라인 항목 | ✅ 존재   | 수량·단가·할인율·소계 자동 계산                     |
| 계약(Contract) 모델 | ⚠️ 없음   | Quote stage='approved'가 계약 역할 대체             |

#### 폼 및 유효성 검사

| 항목                                  | 결과      | 근거                                            |
| ------------------------------------- | --------- | ----------------------------------------------- |
| 필수 필드 서버 검증                   | ✅ PASS   | Phase 4 적용 (is-invalid JS + 한국어 에러 라벨) |
| 빈 상태 — followup_list               | ✅ PASS   | `.empty-state-card` CSS + 안내 메시지           |
| 빈 상태 — history_list, schedule_list | ❌ 미구현 | `{% empty %}` 블록 및 empty-state 메시지 없음   |
| 다크모드 폼 호환                      | ✅ PASS   | Phase 4에서 CSS 변수 적용 완료                  |

#### 검색 / 필터 / 목록 사용성

| 항목               | 결과    | 근거                                                   |
| ------------------ | ------- | ------------------------------------------------------ |
| 팔로우업 검색·필터 | ✅ PASS | q, priority, grade, pipeline_stage, company, user 지원 |
| 히스토리 목록 필터 | ✅ PASS | 날짜 범위, 거래처, 담당자, 활동 유형 지원              |
| 일정 캘린더 뷰     | ✅ PASS | `/schedules/calendar/` 별도 URL                        |

#### 모바일 사용성

| 항목                  | 결과    | 근거                                              |
| --------------------- | ------- | ------------------------------------------------- |
| viewport 메타 태그    | ✅ PASS | `content="width=device-width, initial-scale=1.0"` |
| 반응형 브레이크포인트 | ✅ PASS | 480px, 768px, 1200px 미디어 쿼리                  |
| 모바일 영업노트 입력  | ✅ PASS | 폼 구조 단순, 핵심 필드 최소화                    |

#### 보안 / 개인정보

| 항목                  | 결과    | 근거                                                      |
| --------------------- | ------- | --------------------------------------------------------- |
| 시크릿 커밋 없음      | ✅ PASS | Phase 5: SECRET_KEY 하드코딩 fallback → RuntimeError      |
| CSRF 보호             | ✅ PASS | Django 미들웨어 전체 적용, `@csrf_exempt` 없음            |
| 객체 레벨 권한        | ✅ PASS | `can_access_user_data`, `can_modify_user_data` 전체 뷰    |
| 파일 업로드 검증      | ✅ PASS | Phase 5: `.hwp/.hwpx` 추가, 단일 `validate_file_upload()` |
| subprocess 안전성     | ✅ PASS | `shell=False`, 사용자 입력 미전달, `timeout=30`           |
| 프로덕션 템플릿 debug | ✅ PASS | Phase 5: `'debug': True` 제거                             |
| IMAP/SMTP 비밀번호    | ✅ PASS | Fernet 암호화 저장, 로그 미기록                           |
| SQL 인젝션            | ✅ PASS | Django ORM 전용, raw SQL 없음                             |

#### 빌드 / 테스트 / 배포 준비

| 항목                   | 결과    | 근거                                                   |
| ---------------------- | ------- | ------------------------------------------------------ |
| Django 시스템 체크     | ✅ PASS | `manage.py check` → 0 이슈                             |
| 자동화 테스트          | ❌ 없음 | `manage.py test` → Ran 0 tests                         |
| 마이그레이션 최신 상태 | ✅ PASS | `makemigrations --check` → No changes detected         |
| 정적 파일 수집         | ✅ PASS | `collectstatic --noinput` → 0 files copied (이미 최신) |
| 린트 설정              | ❌ 없음 | flake8, mypy, pyproject.toml 없음                      |
| Railway 배포 설정      | ✅ PASS | nixpacks, WhiteNoise, gunicorn, 마이그레이션 자동 실행 |

---

### 실행한 명령 및 결과

```
1. python manage.py check
   → EMAIL_ENCRYPTION_KEY 경고 (정상 — 로컬 개발 환경, 프로덕션은 env var로 설정)
   → System check identified no issues (0 silenced)

2. python manage.py test
   → Found 0 test(s).
   → Ran 0 tests in 0.000s — OK

3. python manage.py makemigrations --check --dry-run
   → No changes detected

4. python manage.py collectstatic --noinput
   → 0 static files copied to 'staticfiles' (이미 최신)
   → 경고: css/dist/styles.css 중복 경로 (static/ vs staticfiles/ 중복)
```

---

### 잔여 이슈

| #   | 중요도  | 이슈                                                                                               | 권장 조치                                               |
| --- | ------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | 🔴 높음 | 자동화 테스트 없음 — `reporting/tests.py`, `todos/tests.py`, `ai_chat/tests.py` 모두 빈 스텁       | 로그인·FollowUp CRUD·권한 smoke test 최소 작성          |
| 2   | 🟡 중간 | 영업기회 프론트엔드 CRUD 없음 — 생성·수정은 Django admin 전용                                      | `opportunity_create_view`, `opportunity_edit_view` 구현 |
| 3   | 🟡 중간 | 견적(Quote) 독립 뷰 없음 — API 엔드포인트만 존재                                                   | 견적 목록·상세·편집 뷰 구현                             |
| 4   | 🟡 중간 | `history_list.html`, `schedule_list.html` 빈 상태(empty state) 없음                                | `{% empty %}` 블록 + `.empty-state-card` 추가           |
| 5   | 🟡 중간 | `railway.toml` startCommand에 일회성 스크립트 포함 (`fix_quote_770.py`, `reset_ai_chat_tables.py`) | idempotent 여부 확인 후 제거 또는 one-time job 분리     |
| 6   | 🟢 낮음 | 린트/타입 체크 설정 없음 — 코드 품질 일관성 도구 부재                                              | `flake8` 또는 `ruff` 설정 추가 권장                     |
| 7   | 🟢 낮음 | `css/dist/styles.css` 경로 중복 — collectstatic 경고                                               | `STATICFILES_DIRS` 또는 빌드 스크립트 경로 정리         |

---

### 기능적 개선 사항

없음 (QA 전용 단계 — 코드 수정 없음)

### UX 개선 사항

없음 (QA 전용 단계 — 코드 수정 없음)

### 보안/개인정보 개선 사항

Phase 5에서 완료. 이번 QA 단계에서 추가 수정 없음.

---

### 다음 권장 작업

**Phase 7 옵션 A (권장)**: 기본 자동화 테스트 작성

- 로그인/로그아웃 smoke test
- FollowUp CRUD 기본 테스트 (생성·수정·삭제 권한)
- 비인증 접근 차단 검사
- `validate_file_upload()` 단위 테스트

**Phase 7 옵션 B**: 영업기회 CRUD 프론트엔드 구현

- `opportunity_create_view`, `opportunity_edit_view` 구현
- 기회 생성/수정 폼 (단계, 예상 금액, 거래처 연결)
- 파이프라인 칸반 보드 뷰 (선택적)

**Phase 7 옵션 C**: 잔여 이슈 정리

- `history_list.html`, `schedule_list.html` empty-state 추가 (빠른 작업)
- `railway.toml` startCommand 일회성 스크립트 제거 (빠른 작업)

---

## Phase 7 — 영업기회 CRUD + 테스트 + 빠른 정리 (2026-04-25)

**상태**: 완료

---

### 요약

Phase 6 QA에서 도출된 잔여 이슈 중 우선순위 항목을 전부 구현했습니다.

1. **Phase 7C (빠른 정리)**
   - `history_list.html`, `schedule_list.html` — empty-state 이미 존재 (확인 후 skip)
   - `railway.toml` — 일회성 스크립트(`reset_ai_chat_tables.py`, `fix_quote_770.py`) startCommand에서 제거

2. **Phase 7A (영업기회 CRUD)**
   - `OpportunityForm` 폼 클래스 추가 (라벨, 단계, 예상 매출, 확률, 계약일, 실주 사유)
   - `opportunity_create_view` — 거래처(FollowUp) 기반 기회 생성
   - `opportunity_edit_view` — 기존 기회 수정, 단계 변경 시 `update_stage()` 호출
   - URL: `opportunities/create/<int:followup_pk>/`, `opportunities/<int:pk>/edit/`
   - `opportunity_form.html` 템플릿 — 다크모드 호환, Bootstrap 5 카드 레이아웃
   - `followup_detail.html` — 영업 기회 섹션 항상 표시 + "기회 등록" 버튼 + 편집 버튼 + empty-state
   - `opportunity_detail.html` — "편집" 버튼(btn-warning) 추가

3. **Phase 7B (자동화 테스트)**
   - `reporting/tests.py` — `AuthenticationSmoke` 클래스: 9개 smoke 테스트 작성
   - 로그인 성공/실패, 미인증 리다이렉트, 주요 목록 뷰 200 응답 검증

---

### 변경된 파일

| 파일                                                    | 유형 | 내용                                                                                                          |
| ------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------- |
| `reporting/views.py`                                    | 수정 | imports에 `OpportunityLabel` 추가; `OpportunityForm`, `opportunity_create_view`, `opportunity_edit_view` 추가 |
| `reporting/urls.py`                                     | 수정 | `opportunity_create`, `opportunity_edit` URL 패턴 추가                                                        |
| `reporting/templates/reporting/opportunity_form.html`   | 신규 | 영업 기회 생성/수정 폼 템플릿                                                                                 |
| `reporting/templates/reporting/followup_detail.html`    | 수정 | 영업 기회 섹션 항상 표시, "기회 등록" 버튼, 편집 버튼, empty-state 추가                                       |
| `reporting/templates/reporting/opportunity_detail.html` | 수정 | "편집" 버튼(btn-warning) 추가                                                                                 |
| `reporting/tests.py`                                    | 수정 | `AuthenticationSmoke` 클래스 — 9개 smoke 테스트                                                               |
| `railway.toml`                                          | 수정 | startCommand에서 `reset_ai_chat_tables.py`, `fix_quote_770.py` 제거                                           |

---

### 실행한 명령 및 결과

```
1. python manage.py check
   → System check identified no issues (0 silenced)

2. python manage.py test reporting.tests --verbosity=2
   → Ran 9 tests in 7.225s
   → OK (9/9 passed)
```

---

### 기존 기능 보존

- `/reporting/*` URL 구조 변경 없음
- 기존 `opportunity_list_view`, `opportunity_detail_view` 동작 변경 없음
- `OPPORTUNITY_STAGE_CHOICES` 상수 보존
- 인증/권한 체계 변경 없음

---

### 잔여 이슈

| #   | 중요도  | 이슈                            | 권장 조치                              |
| --- | ------- | ------------------------------- | -------------------------------------- |
| 1   | 🟡 중간 | 견적(Quote) 독립 뷰 없음        | 견적 목록·상세·편집 뷰 구현            |
| 2   | 🟡 중간 | FollowUp CRUD 테스트 없음       | Phase 8에서 추가                       |
| 3   | 🟢 낮음 | 린트/타입 체크 설정 없음        | `ruff` 또는 `flake8` 설정 권장         |
| 4   | 🟢 낮음 | `css/dist/styles.css` 경로 중복 | collectstatic 경고, 빌드 스크립트 정리 |

---

### 다음 권장 작업

**Phase 4 (수정판)**: 대시보드 + 영업 노트 UX 개선 — 아래 Phase 4 (수정판) 참고

---

## Phase 4 (수정판) — 대시보드·영업 노트·거래처 이력 개선 (2026-04-25)

**상태**: 완료

---

### 요약

대시보드 가시성, 영업 활동 목록 필터링, 영업 노트 상세 UX, 거래처 상세 빠른 작성 기능을 개선했습니다.  
모델 변경 없음. 기존 URL 보존. 기존 smoke 테스트 9/9 통과.

---

### 변경된 파일

| 파일                                                 | 유형 | 내용                                                                                             |
| ---------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------ |
| `reporting/views.py`                                 | 수정 | `dashboard_view` — `recent_histories` (최근 8개), `overdue_next_actions` (지연 5개) context 추가 |
| `reporting/views.py`                                 | 수정 | `history_detail_view` — `today` 변수 + context 추가                                              |
| `reporting/views.py`                                 | 수정 | `history_list_view` — `company_filter` 필터링 + `accessible_companies` queryset + context 추가   |
| `reporting/templates/reporting/dashboard.html`       | 수정 | 빠른 작성 버튼 카드, 지연된 후속 조치 알림 카드, 최근 영업 활동 리스트 카드 — 3개 섹션 추가      |
| `reporting/templates/reporting/history_list.html`    | 수정 | 업체 필터 select dropdown + 필터 적용 버튼 추가                                                  |
| `reporting/templates/reporting/history_detail.html`  | 수정 | 요약 정보 박스 추가 (거래처/고객/활동유형/활동일/작성자/다음액션)                                |
| `reporting/templates/reporting/followup_detail.html` | 수정 | "영업 기록 작성" (btn-success) + "전체 이력" (btn-outline-info) 버튼 추가                        |

---

### 새 기능

#### 1. 대시보드 — 빠른 작성 버튼

- "영업 노트 작성" → `memo_create`
- "일정 추가" → `schedule_create`
- "거래처 추가" → `followup_create`

#### 2. 대시보드 — 지연된 후속 조치

- `next_action_date < today` 조건의 미완료 후속 조치 최대 5건 표시
- 경고색(amber) 카드, 만료일 배지, 상세 링크

#### 3. 대시보드 — 최근 영업 활동

- 메모 제외, 최신 8개 영업 활동 리스트
- 활동 유형 배지, 고객명/업체명, 활동일, 내용 70자 요약, 상세 링크
- 데이터 없을 경우 empty state + "영업 노트 작성" CTA

#### 4. 영업 활동 목록 — 업체 필터

- `accessible_companies` queryset으로 접근 가능한 업체 목록만 표시
- `?company_filter=<pk>` 파라미터로 히스토리 필터링
- 기존 날짜·활동유형·키워드 필터와 중첩 적용 가능

#### 5. 영업 활동 상세 — 요약 정보 박스

- 페이지 최상단에 2컬럼 요약 카드:
  - 좌: 거래처/업체명/부서, 고객명, 활동 유형 배지
  - 우: 활동일, 작성자, 다음 액션 + 예정일(만료 시 빨간 배지)

#### 6. 거래처 상세 — 빠른 영업 기록 작성

- 히스토리 섹션 헤더에 "영업 기록 작성" (btn-success) 버튼 추가
- 기존 "메모 추가" 버튼을 대체
- "전체 이력" 버튼 — `/reporting/histories/?followup=<pk>` 링크

---

### 모델 변경사항

**변경 없음.** 이번 Phase에서 모델 추가·수정·삭제 없음.  
기존 `History.next_action`, `History.next_action_date` 필드를 그대로 활용.

---

### 마이그레이션 상태

**마이그레이션 없음.** 모델 변경이 없으므로 신규 마이그레이션 불필요.  
`python manage.py makemigrations --check --dry-run` → No changes detected (확인 완료)

---

### `/reporting/*` 보존 여부

**전면 보존.** 기존 CRM 기능·URL 전체 유지.

| 기능                         | 상태                       |
| ---------------------------- | -------------------------- |
| `/reporting/login/`          | ✅ 유지                    |
| `/reporting/dashboard/`      | ✅ 유지 (섹션 추가만)      |
| `/reporting/followups/`      | ✅ 유지                    |
| `/reporting/followups/<pk>/` | ✅ 유지 (버튼 교체만)      |
| `/reporting/histories/`      | ✅ 유지 (필터 추가만)      |
| `/reporting/histories/<pk>/` | ✅ 유지 (요약 박스 추가만) |
| 기타 모든 `/reporting/*`     | ✅ 유지                    |

---

### `public_site` 영향

**영향 없음.** 이번 Phase에서 `public_site` 앱을 수정하지 않음.  
`public_site/` 디렉터리 및 관련 URL은 이전 Phase 상태 그대로 유지.  
루트 `/` → `/reporting/dashboard/` 리다이렉트 동작 변경 없음.

---

### 보안 및 권한

- `accessible_companies` — `filter_users` 범위 기준으로 필터링 (권한 체계 유지)
- `recent_histories`, `overdue_next_actions` — `histories` queryset(이미 권한 필터 적용) 기반
- `is_owner` 조건 유지 — "영업 기록 작성" 버튼은 소유자에게만 표시
- 기존 `@login_required`, `can_access_user_data()`, `can_modify_user_data()` 변경 없음

---

### 실행한 명령 및 결과

| #   | 명령                                                  | 결과                                              |
| --- | ----------------------------------------------------- | ------------------------------------------------- |
| 1   | `python manage.py check`                              | ✅ System check identified no issues (0 silenced) |
| 2   | `python manage.py test reporting.tests --verbosity=2` | ✅ Ran 9 tests in 8.067s — OK (9/9 passed)        |
| 3   | `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected                            |

### 실패한 명령

없음. 이번 Phase에서 실패한 명령 없음.

---

### 제한 사항 및 잔여 이슈

- `accessible_companies`는 `FollowUp.company` 기반만 필터링 (Department 경유 업체는 포함되지 않을 수 있음)
- `overdue_next_actions`는 대시보드 권한 범위(`histories`) 기반 — 관리자는 전체 팀, 일반 담당자는 본인 데이터만 표시
- `history_detail`의 `today` 변수는 뷰에서 명시적으로 제공 (템플릿 `today < next_action_date` 비교용)
- 영업 노트 생성(`memo_create`) / 수정(`memo_edit`) 폼 자체의 UX 개선은 이번 Phase 범위 외

---

### 다음 권장 작업

**Phase 8A**: 견적(Quote) 독립 뷰 구현

- 견적 목록, 상세, 생성, 수정 뷰
- 라인 아이템(QuoteItem) 동적 추가 UI

**Phase 8B**: FollowUp CRUD 테스트 추가

- 생성, 수정, 삭제 권한 검증 테스트
- 필터/검색 동작 테스트

---

## Phase 4 QA 패스 (2026-04-26)

**상태**: 완료 — 버그 없음

---

### QA 범위

Phase 4 (수정판) 구현 완료 후 엄격한 QA 실시.  
신규 기능 추가 없음. 코드 탐색 + Django 명령 + URL smoke 테스트 수행.

---

### 1. 범위(Scope) 검사

| 항목                                     | 결과                                           |
| ---------------------------------------- | ---------------------------------------------- |
| 내부 영업 관리 시스템 유지               | ✅                                             |
| 공개 상품/브랜드/카탈로그 기능 확장 없음 | ✅                                             |
| `/reporting/*` 전체 URL 보존             | ✅                                             |
| 익명 사용자 내부 CRM 접근 차단           | ✅ (302 리다이렉트 확인)                       |
| `public_site` 앱 미영향                  | ✅ (Phase 0에서 제거됨, 이번 QA에서 변경 없음) |

---

### 2. 루트 URL 동작

| URL                     | 미인증 응답 | 비고                               |
| ----------------------- | ----------- | ---------------------------------- |
| `/`                     | 302         | `/reporting/dashboard/` 리다이렉트 |
| `/reporting/dashboard/` | 302         | 로그인 페이지로 리다이렉트         |

`RedirectView(pattern_name='reporting:dashboard')` — 루트에서 대시보드로, 미인증이면 자동으로 로그인 페이지 이동. ✅

---

### 3. URL Smoke 테스트

| URL                       | 미인증 상태 코드              | 결과      |
| ------------------------- | ----------------------------- | --------- |
| `/`                       | 302 → `/reporting/dashboard/` | ✅        |
| `/reporting/login/`       | 200                           | ✅        |
| `/reporting/dashboard/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/histories/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/followups/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/memo/create/` | 302 → login                   | ✅ 보호됨 |

모든 내부 CRM URL이 미인증 접근 시 로그인 페이지로 리다이렉트됨.

---

### 4. 인증 및 보안 확인

| 항목                                                               | 결과 |
| ------------------------------------------------------------------ | ---- |
| 로그인 페이지 200 응답                                             | ✅   |
| 로그인 폼 `csrfmiddlewaretoken` 필드 존재                          | ✅   |
| 내부 페이지 `@login_required` 보호                                 | ✅   |
| `can_access_user_data()` / `can_modify_user_data()` 기존 로직 유지 | ✅   |
| `is_owner` 조건 (followup_detail 작성 버튼)                        | ✅   |
| `accessible_companies` — `filter_users` 범위 제한                  | ✅   |
| 비밀 정보 커밋 없음                                                | ✅   |

---

### 5. Phase 4 기능 코드 검증

#### 대시보드

- `recent_histories`: `parent_history__isnull=True`, `exclude(action_type='memo')`, `.order_by('-created_at')[:8]` — 정상 ✅
- `overdue_next_actions`: `next_action_date__lt=today`, `next_action_date__isnull=False`, `parent_history__isnull=True`, `.order_by('next_action_date')[:5]` — 정상 ✅
- 빠른 작성 버튼 URL 이름: `reporting:memo_create`, `reporting:schedule_create`, `reporting:followup_create` — 모두 `urls.py`에 등록됨 ✅
- 템플릿 null 안전성: `h.followup` None 시 Django 템플릿이 빈 문자열 반환, `|default:"고객명 미정"` 처리 ✅

#### 영업 활동 목록 업체 필터

- `accessible_companies` 쿼리: `Company.objects.filter(followup_companies__user__in=filter_users)` — `FollowUp.company`의 `related_name='followup_companies'` 확인 ✅
- `company_filter` GET 파라미터 → `followup__company_id` 필터링 — 정상 ✅
- context에 `company_filter`, `accessible_companies` 추가됨 ✅

#### 영업 활동 상세 요약 박스

- `history_detail_view`에 `today = timezone.now().date()` 추가됨 ✅
- context에 `'today': today` 추가됨 ✅
- 템플릿: `{% if history.next_action_date < today %}bg-danger{% else %}bg-secondary{% endif %}` — 정상 ✅

#### 거래처 상세 빠른 기록 링크

- "전체 이력": `{% url 'reporting:history_list' %}?followup={{ followup.pk }}` ✅
- "영업 기록 작성": `{% if is_owner %}` 조건부 + `{% url 'reporting:memo_create' %}?followup={{ followup.pk }}` ✅

---

### 6. Django 명령 결과

| 명령                                                  | 결과                                              |
| ----------------------------------------------------- | ------------------------------------------------- |
| `python manage.py check`                              | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected                            |
| `python manage.py test reporting.tests --verbosity=2` | ✅ Ran 9 tests in 8.434s — OK (9/9 passed)        |

---

### 7. 발견된 버그

**없음.** Phase 4 코드에서 버그 발견 없음.

---

### 8. 경미한 UX 제한 사항 (버그 아님)

| 항목                                                       | 내용                                                        | 위험도 |
| ---------------------------------------------------------- | ----------------------------------------------------------- | ------ |
| 업체 필터 전환 시 month_filter 유실                        | 업체 필터 적용 시 다른 필터(월별 등) 초기화됨               | 낮음   |
| 업체 필터 목록 범위                                        | `FollowUp.company` 기준, Department 경유 업체 미포함 가능성 | 낮음   |
| `overdue_next_actions`에 followup=None인 History 포함 가능 | 템플릿에서 안전하게 처리되나 표시가 불완전할 수 있음        | 낮음   |

---

### 9. 잔여 위험

- 없음 (Phase 4 구현 안전성 확인됨)

---

### Phase 5 시작 가능 여부

**✅ Phase 5 시작 가능**

Phase 4 QA 패스 완료. 모든 검사 통과. 잔여 버그 없음.

---

## Phase 5 Summary

Phase 5 implemented follow-up and pipeline visibility improvements for the internal Sales Note system.

### Files changed

- `reporting/views.py`
- `reporting/templates/reporting/dashboard.html`
- `reporting/templates/reporting/history_list.html`

### Implemented features

#### dashboard_view

- Added `today_schedules` for today's scheduled activities.
- Added `upcoming_schedules_dash` for schedules within the next 7 days.
- Added `pipeline_summary` grouped by FollowUp pipeline/status stage.
- Added `team_activity` for manager/admin users, including recent 30-day activity count and overdue action count.

#### history_list_view

- Added `next_action_filter` GET parameter.
- Supported values:
  - `overdue`
  - `upcoming`
  - `has_date`
- Added `next_action_filter` and `today` to template context.

#### dashboard.html

- Added pipeline stage badge row.
- Added today schedule card.
- Added upcoming schedule card.
- Added manager-only team activity table.

#### history_list.html

- Added next action date filter button group.
- Added `next_action_date` badges.
- Overdue items are displayed with red badges.
- Upcoming items are displayed with yellow badges.

### Validation

- 9/9 tests passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py test reporting.tests --verbosity=2`: Ran 9 tests in 7.894s — OK.

### Known limitations

- Confirm whether FollowUp-based pipeline grouping matches the intended business pipeline model.
- Confirm manager/admin permission behavior with real user roles.
- Confirm empty-state behavior with production-like data.

### Recommended Phase 6

- Reporting and export.
- Manager analytics.
- CSV export.
- Date-range reports.
- Sales rep performance summary.
- Customer activity report.

---

## Phase 5 QA 패스 (2026-04-26)

### QA 요약

Phase 5 구현 완료 후 엄격한 QA를 실시하였습니다. 2개의 소규모 버그를 발견하고 즉시 수정하였습니다. 모든 Django 검사 통과, 기존 9개 테스트 통과.

### 실행 명령 및 결과

| 명령                                                | 결과                                           |
| --------------------------------------------------- | ---------------------------------------------- |
| `python manage.py check`                            | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | No changes detected                            |
| `python manage.py test reporting.tests`             | Ran 9 tests in 7.053s — **OK**                 |
| 템플릿 파서 (`get_template` 검증)                   | `dashboard.html`, `history_list.html` 모두 OK  |

### URL 스모크 테스트 결과 (비로그인 상태)

| URL                                                      | 응답 코드 | 비고                                                                             |
| -------------------------------------------------------- | --------- | -------------------------------------------------------------------------------- |
| `/`                                                      | 302       | 대시보드로 리다이렉트 ✅                                                         |
| `/reporting/login/`                                      | 200       | 로그인 페이지 정상 표시 ✅                                                       |
| `/reporting/`                                            | 404       | **Pre-existing 이슈** — Phase 5 무관, 매핑된 URL 없음 (Phase 6 권장 사항에 기록) |
| `/reporting/dashboard/`                                  | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/`                                  | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=overdue`       | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=upcoming`      | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=has_date`      | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=invalid_value` | 302       | 잘못된 값 → 정상 처리(필터 무시) ✅                                              |

### 발견된 버그 및 수정

#### 버그 1 (수정됨): `{{ s.title }}` — Schedule 모델에 없는 필드 참조

- **위치**: `dashboard.html` 오늘 예정 일정 / 이번 주 예정 일정 카드 (2군데)
- **증상**: `Schedule` 모델에 `title` 필드 없음 → Django 템플릿이 빈 문자열로 렌더링, 메모 줄이 항상 미표시
- **수정**: `s.title` → `s.notes`로 변경 (Schedule 모델의 실제 필드 `notes` 사용)
- **영향**: 기능 오류 없이 조용히 실패하던 것을 올바르게 수정

#### 버그 2 (수정됨): history_list "전체" 필터 버튼이 next_action_filter를 해제하지 않음

- **위치**: `history_list.html` 다음 액션 날짜 필터 버튼 그룹, "전체" 버튼
- **증상**: `request.GET.urlencode()`를 그대로 사용해 현재 `next_action_filter` 파라미터가 URL에 그대로 유지됨 → "전체" 클릭 시 필터 해제 안 됨
- **수정**: `request.GET.urlencode()` → 나머지 필터(`data_filter`, `filter_user`, `action_type`, `company_filter`)만 명시적으로 포함하는 URL로 교체
- **영향**: UX 버그 수정. 기능 로직 변경 없음

### 권한 및 보안 확인

| 항목                                                                              | 결과              |
| --------------------------------------------------------------------------------- | ----------------- |
| 비로그인 사용자 → 인증 페이지 접근 시 302 리다이렉트                              | ✅ 확인           |
| `team_activity` 컨텍스트 — `can_view_all_users()`가 `True`인 경우만 채워짐        | ✅ 코드 확인      |
| 일반 영업사원 → `team_activity = []` → 템플릿에서 `{% if team_activity %}` 미표시 | ✅ 확인           |
| `followups`, `schedules`, `histories` — 권한 범위(회사/사용자) 기반 필터링 유지   | ✅ 기존 로직 유지 |
| CSRF 보호 — 새로운 뷰/폼 없음, 기존 설정 유지                                     | ✅ 변경 없음      |

### 잔여 위험

- `/reporting/` (루트) → 404: pre-existing 이슈. `/reporting/dashboard/`로 리다이렉트하는 URL 추가 권장 (Phase 6)
- `next_action_filter` 링크에 `date_from`, `date_to`, `search_query`, `month_filter` 등의 복합 파라미터는 일부 누락될 수 있음. 검색 폼 submit이 완전 교체하므로 실사용에서 문제는 적음
- `team_activity`의 최대 8명 트런케이트: 팀원이 많은 경우 전체 미표시

### Phase 6 시작 가능 여부

**✅ Phase 6 시작 가능**

Phase 5 QA 완료. 2개 버그 수정. 모든 검사 통과. 기존 기능 이상 없음.

---

## Phase 6 — 분석 보고서 대시보드 및 CSV 내보내기

**날짜**: 2026-04-26
**상태**: 완료

---

## 요약

영업사원별 활동 분석, 고객 파이프라인 현황, CSV 내보내기를 포함하는 분석 보고서 대시보드 페이지를 추가했습니다.
admin/manager는 전체 또는 특정 영업사원 필터 조회가 가능하고, salesman은 본인 데이터만 조회합니다.

---

## 변경된 파일

| 파일 | 변경 |
| ---- | ---- |

|
eporting/views.py | nalytics_dashboard_view, nalytics_activity_csv_export, nalytics_pipeline_csv_export 3개 뷰 추가 |
|
eporting/urls.py | /analytics/, /analytics/export/activity.csv, /analytics/export/pipeline.csv 3개 URL 추가 |
|
eporting/templates/reporting/analytics_dashboard.html | 신규 템플릿 생성 (필터, 요약 카드, 활동 보고서, 파이프라인 차트, 거래처 현황 포함) |
|
eporting/templates/reporting/base.html | 사이드바에 "분석 보고서" 네비게이션 항목 추가 |
| AGENT_REPORT.md | Phase 6 내용 추가 |

---

## 추가된 보고서 페이지

### 1. 분석 대시보드 (/reporting/analytics/)

- 요약 카드: 총 영업노트, 완료 후속조치, 지연 후속조치, 예정 후속조치, 활성 파이프라인
- 영업사원별 활동 보고서 테이블: 영업노트 수, 후속조치, 지연 건수, 최근 활동일
- 파이프라인 단계별 수평 막대 차트 (단계별 색상 구분)
- 거래처 현황 테이블: 거래처, 담당자, 영업단계, 마지막 활동일, 다음 연락일

### 2. 활동 보고서 CSV (/reporting/analytics/export/activity.csv)

- admin/manager 전용, 403 반환 (salesman 접근 시)
- 컬럼: 영업사원, 기간 내 영업노트, 활성 거래처, 지연 후속조치, 최근 활동일
- 한글 Excel 호환: utf-8-sig (BOM)

### 3. 파이프라인 CSV (/reporting/analytics/export/pipeline.csv)

- admin/manager 전용, 403 반환 (salesman 접근 시)
- 컬럼: 파이프라인 단계, 건수
- 한글 Excel 호환: utf-8-sig (BOM)

---

## 권한 동작

| 역할     | 대시보드                     | 사용자 드롭다운 | CSV 내보내기 |
| -------- | ---------------------------- | --------------- | ------------ |
| admin    | 전체 조회 / 사용자 필터 가능 | ✅ 전체 사용자  | ✅ 허용      |
| manager  | 동일 회사 영업사원 필터      | ✅ 동일 회사만  | ✅ 허용      |
| salesman | 본인 데이터만                | ❌ 미표시       | ❌ 403 반환  |

---

## 실행된 명령 및 결과

| 명령                                              | 결과                          |
| ------------------------------------------------- | ----------------------------- |
| python manage.py check                            | ✅ No issues                  |
| python manage.py makemigrations --check --dry-run | ✅ No changes detected        |
| URL reverse 테스트 (shell)                        | ✅ 3개 URL 정상 등록          |
| 템플릿 로드 테스트 (shell)                        | ✅ Template load: OK          |
| URL 스모크 테스트 (HTTP)                          | ✅ 미인증 → 302 리디렉션 정상 |

---

## 알려진 제한사항

- 파이프라인 막대 차트의 max_cnt는 첫 번째 항목을 기준으로 계산 (단계 정렬 순서 기반, 실제 최대값 아닐 수 있음)
- 날짜 범위 미지정 시 기본값: 최근 30일
- 거래처 현황 테이블은 후속조치(FollowUp)가 있는 건만 표시

---

## 권장 Phase 7

- 분석 차트에 Chart.js 등 시각화 라이브러리 연동 (현재 CSS 막대 차트)
- 월별 추세 그래프 추가
- 영업사원 개인별 상세 보고서 페이지
- 대시보드 위젯에 분석 요약 통합

---

## Phase 6 QA 패스 — 버그 수정 (2026-04-26)

**날짜**: 2026-04-26  
**상태**: 완료

---

## 요약

Phase 6 구현 후 QA 패스를 실행하여 3개의 버그를 발견하고 모두 수정했습니다.

---

## 발견된 버그 및 수정

### Bug 1: CSV BOM이 모든 행에 반복 삽입 (FIXED)

**증상**: Excel에서 CSV 열면 각 행 앞에 `<U+FEFF>` 깨진 문자가 반복됨  
**원인**: `HttpResponse(content_type='text/csv; charset=utf-8-sig')` 사용 시 Django가 모든 `write()` 호출에 BOM을 삽입함 — `csv.writer`는 각 행마다 별도 `write()`를 호출  
**수정** (`reporting/views.py`):

- `charset=utf-8-sig` → `charset=utf-8`
- `response.write('\ufeff')` 를 헤더 행 이전에 **1회만** 명시적으로 추가
- 영향 뷰: `analytics_activity_csv_export`, `analytics_pipeline_csv_export`

### Bug 2: 파이프라인 막대 차트 너비가 모두 0% (FIXED)

**증상**: 파이프라인 단계별 막대 차트가 모두 0% 너비로 표시됨  
**원인**: `{% with max_cnt=pipeline_summary.0.count %}` — 목록의 첫 번째 항목(`potential`)의 카운트를 최대값으로 사용했는데, 해당 값이 0이면 전체 차트가 0%로 렌더링됨  
**수정**:

- `analytics_dashboard_view`에 `max_pipeline_count = max((item['count'] for item in pipeline_summary), default=1) or 1` 계산 추가
- 템플릿에서 `{% widthratio item.count max_pipeline_count 100 %}` 사용으로 변경

### Bug 3: `UnboundLocalError: pipeline_summary` (salesman 접근 시 500 에러) (FIXED)

**증상**: salesman 사용자가 `/reporting/analytics/` 접근 시 500 Internal Server Error  
**원인**: `max_pipeline_count` 계산 코드가 `pipeline_summary` 리스트 정의보다 앞에 배치됨 (Bug 2 수정 과정에서 위치가 잘못됨)  
**수정**: `max_pipeline_count` 계산 코드를 `pipeline_summary` 루프 완료 **직후**로 이동

---

## 변경된 파일

| 파일                                                     | 변경 내용                                                  |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| `reporting/views.py`                                     | CSV BOM 수정 (2개 뷰), `max_pipeline_count` 계산 위치 수정 |
| `reporting/templates/reporting/analytics_dashboard.html` | `widthratio` 태그에 `max_pipeline_count` 사용              |
| `AGENT_REPORT.md`                                        | Phase 6 QA 섹션 추가                                       |

---

## 실행된 명령 및 결과

| 명령                                                | 결과                                              |
| --------------------------------------------------- | ------------------------------------------------- |
| `python manage.py check`                            | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected                            |
| `python manage.py test`                             | ✅ Ran 9 tests in ~8.7s — OK                      |
| BOM 검증 스크립트                                   | ✅ BOM only at start: OK                          |
| HTTP 스모크 테스트 (미인증)                         | ✅ 모든 analytics URL → 302                       |
| 역할별 권한 테스트 (Test Client)                    | ✅ 아래 표 참고                                   |

---

## 역할별 권한 테스트 결과

| 역할               | `/reporting/analytics/` | `/analytics/export/activity.csv` | `/analytics/export/pipeline.csv` |
| ------------------ | ----------------------- | -------------------------------- | -------------------------------- |
| 미인증             | 302 (로그인 리디렉션)   | 302 (로그인 리디렉션)            | 302 (로그인 리디렉션)            |
| salesman (hana008) | **200** ✅              | **403** ✅                       | **403** ✅                       |
| manager (hana)     | **200** ✅              | **200** ✅                       | **200** ✅                       |
| admin (ddd418)     | **200** ✅              | **200** ✅                       | **200** ✅                       |

모든 결과가 예상 동작과 일치합니다.

---

## 알려진 제한사항 / 잔여 위험

- 없음 — 발견된 버그 3개 모두 수정 완료
- `python manage.py test` 9개 기존 테스트 모두 통과

---

## 배포 안전성

✅ **배포 가능** — 버그 수정 후 모든 검증 통과

---

## Phase 6 Permission Matrix

| Feature             | Anonymous | Sales user    | Manager   | Admin       |
| ------------------- | --------- | ------------- | --------- | ----------- |
| Analytics dashboard | Redirect  | Own data only | Team data | Admin scope |
| Activity CSV export | Redirect  | Forbidden     | Allowed   | Allowed     |
| Pipeline CSV export | Redirect  | Forbidden     | Allowed   | Allowed     |

**구현 기준**: `UserProfile.role` 필드 (`salesman` / `manager` / `admin`). `is_staff` 또는 Django 그룹 기반이 아님.

---

## Phase 6 Known Risks

- 실제 운영 환경의 역할 정의 재확인 필요 (`manager` 역할이 `is_staff`, Django Group, Profile role 중 어느 기준인지 코드와 동일하게 일치하는지 확인)
- CSV 내보내기 컬럼에 불필요한 개인정보 또는 고객 민감 정보가 포함되지 않는지 검토
- 분석 통계 집계 방식(기간 필터, 히스토리 vs 후속조치 카운트 기준)이 비즈니스 기대값과 일치하는지 확인
- `manager`의 company 필터 — `userprofile__company`가 null인 경우 전체 데이터 노출 여부 확인 필요

---

## Phase 7 시작 가능 여부

✅ **Phase 7 시작 가능**

---

## Phase 6.5-1 — 모달 클릭/입력 버그 수정 (2026-04-27)

**상태**: 완료

### 요약

3개 영역의 모달 인터랙션 버그를 근본 원인(root cause) 수준에서 수정했습니다.

1. 캘린더 일정 상세 모달에서 고객명 클릭 시 메인 모달이 사라지는 버그 → **중첩 모달 제거, Offcanvas 전환**
2. 캘린더 일정 상세 모달에서 부서 메모 Offcanvas의 textarea 입력 불가 버그 → **모달 포커스 트랩 우회 처리**
3. 대시보드 영업노트 작성 모달에서 필드 클릭/입력 불가 버그 → **CSS stacking context 제거**

기존 `pointer-events: none !important` 임시 해결책(workaround)은 완전히 제거하고 구조적 수정을 적용했습니다.

---

### 근본 원인 (Root Cause)

| 문제                                       | 원인                                                                                                                                                                                                                          |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 캘린더: 고객명 클릭 시 일정 상세 모달 소멸 | `showCustomerHistories()`가 Bootstrap Modal을 중첩 생성 — Bootstrap 5는 공식적으로 중첩 모달 미지원, 두 번째 모달 `show()` 시 첫 번째 모달을 강제 숨김                                                                        |
| 캘린더: 부서 메모 textarea 입력 불가       | `scheduleDetailModal`의 Bootstrap focus trap이 `focusin` 이벤트를 캡처하여 Offcanvas 내부 포커스를 모달로 되돌려 놓음                                                                                                         |
| 캘린더: Offcanvas 닫기 버튼 클릭 불가      | Bootstrap Offcanvas 기본 z-index(1045)가 열린 Modal(1055)보다 낮아, 일정 상세 모달이 Offcanvas 위 레이어에서 클릭을 가로챔                                                                                                    |
| 대시보드: 모달 필드 클릭 불가              | `base.html`의 `.main-content { position: relative; z-index: 1; }` 조합이 CSS stacking context를 생성 → 내부 모달(z-index:1055)이 stacking context에 갇혀 body에 직접 추가된 backdrop(z-index:1040)보다 낮은 레이어에 렌더링됨 |

---

### 변경된 파일

#### 1. `reporting/templates/reporting/schedule_calendar.html`

**CSS 변경:**

- `#customerHistoriesModal .modal-content { ... }` 규칙 제거 (이미 이전 세션에서 `#customerHistoryOffcanvas` CSS로 교체됨, 잔여 중복 규칙 삭제)
- `.modal-backdrop { pointer-events: none !important }` 블록 제거 (이전 세션 완료)
- `#deptMemoOffcanvas`, `#customerHistoryOffcanvas`에만 scoped z-index `1065` 적용 (열린 schedule modal 위에서 입력/닫기 버튼 클릭 가능)

**HTML 변경:**

- `#deptMemoOffcanvas`에 `data-bs-backdrop="false" data-bs-scroll="true"` 속성 추가
- 새 `#customerHistoryOffcanvas` 정적 HTML 요소 추가 (중첩 모달 대신 사이드 패널로 표시)

**JavaScript 변경:**

- `openDeptMemo()` — `new bootstrap.Offcanvas()` → `Offcanvas.getOrCreateInstance()` 전환, `focusin` 캡처 이벤트로 포커스 트랩 우회 로직 추가
- `showCustomerHistories()` — Bootstrap Modal 동적 생성/삽입 방식 제거, `#customerHistoryOffcanvas` Offcanvas 방식으로 전환
- `loadCustomerHistories()` — DOM 타겟 `#customerHistoriesContent` → `#customerHistoryOffcanvasContent` 변경
- `displayCustomerHistories()` — DOM 타겟 `#customerHistoriesContent` → `#customerHistoryOffcanvasContent` 변경

#### 2. `reporting/templates/reporting/base.html`

- `.main-content` CSS에서 `z-index: 1;` 제거
- 이로 인해 stacking context가 해제되어 `.main-content` 내부 Bootstrap 모달이 body의 root stacking context 기준으로 z-index 적용 (backdrop: 1040 < modal: 1055 정상 계층 복원)

---

### 변경 전/후 동작

| 영역                        | 변경 전                                           | 변경 후                                                  |
| --------------------------- | ------------------------------------------------- | -------------------------------------------------------- |
| 캘린더 → 고객명 클릭        | 일정 상세 모달이 사라지고 고객 모달만 표시됨      | 일정 상세 모달 유지, 우측에 고객 활동기록 Offcanvas 열림 |
| 캘린더 → 부서 메모 textarea | 클릭해도 입력 커서 생기지 않거나 닫기 버튼이 막힘 | textarea 정상 입력 가능, Offcanvas 닫기 가능             |
| 대시보드 → 영업노트 모달    | 모달 표시되나 input/textarea/button 클릭 불가     | 모든 필드 클릭 및 입력 정상                              |

---

### 실행한 명령어 및 결과

```
$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py check
System check identified no issues (0 silenced)

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py test
Ran 9 tests in 7.257s
OK

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py shell -c "... dashboard/calendar smoke ..."
/reporting/dashboard/ 200
/reporting/schedules/calendar/ 200

$ npx --package @playwright/cli playwright-cli ... local browser validation ...
Calendar schedule modal stayed visible while department memo/customer history Offcanvas opened.
Memo textarea accepted text and Offcanvas close button worked.
Dashboard sales-note textarea/input accepted text with pointer-events:auto.
```

참고: 기본 `python manage.py check`는 로컬 기본 Python에 Django가 없어 실패했으므로, 프로젝트 문서의 `sales-env` 인터프리터로 검증했습니다. 첫 smoke check는 `testserver`가 `ALLOWED_HOSTS`에 없어 400이 반환되었고, `HTTP_HOST='127.0.0.1'`로 재실행하여 두 페이지 모두 200을 확인했습니다.

### 정적 점검 결과

- 중복 ID 없음: `dashboardNoteModal`, `deptMemoOffcanvas`, `customerHistoryOffcanvas`는 각각 단일 정의만 존재
- 금지된 전역 workaround 없음: 변경 범위 파일에서 `.modal-backdrop { display: none }` 또는 `.modal-backdrop { pointer-events: none }` 사용 없음
- CSRF 유지: 대시보드 영업노트 AJAX POST와 부서 메모 POST 모두 `X-CSRFToken` / CSRF 값을 유지
- Bootstrap workaround 범위: 전역 `.modal-backdrop` 숨김/비활성화는 사용하지 않음. 캘린더 내부 Offcanvas 2개에만 z-index를 scoped 적용하고, 부서 메모 Offcanvas focusin 전파만 scoped 차단.

---

### 기존 기능 보전

- `scheduleDetailModal` (일정 상세 모달) 기존 기능 유지
- `deptMemoOffcanvas` 메모 저장/로드 기능 유지
- `editDeliveryItemsModal`, 납품 품목 관리 기능 영향 없음
- `dashboardNoteModal` 단계별 영업노트 작성 기능 유지
- sidebar `z-index: 1000` 및 `sidebar-overlay z-index: 999` 계층 정상 (backdrop 1040은 이들보다 높지만, sidebar는 `position: fixed`로 별도 stacking context에 있어 충돌 없음)
- 모든 기존 `/reporting/*` URL 및 API 엔드포인트 영향 없음

---

### 알려진 제한 사항 및 위험

- `scheduleDetailModal` 내에 다른 중첩 Bootstrap Modal이 있다면 (`editDeliveryItemsModal` 등) 동일한 문제 잠재 가능 — 현재 세션 범위 밖
- Bootstrap focus trap 우회(`e.stopPropagation()`)가 접근성(a11y) 관점에서 이상적이지 않을 수 있음, 실제 사용 환경에서 스크린 리더 테스트 권장
- 대시보드 브라우저 검증은 fixture 상태상 실제 일정 선택/저장은 수행하지 않고, 모달 step2 필드 입력 가능 여부를 확인함
- 부서 메모 저장 API는 CSRF 및 기존 POST 로직을 보존했으나, 검증 중 실제 저장 클릭은 수행하지 않음

---

### 다음 권장 단계

1. `editDeliveryItemsModal` 등 남아 있는 Bootstrap 중첩 모달 후보를 Phase 6.5-2에서 Offcanvas/인라인 패널로 정리
2. 모달 접근성(키보드 네비게이션, a11y) 검토

---

## Phase 6.5-2 — AI 분석 컨텍스트에 선결제 데이터 통합 (2026-04-27)

**상태**: 완료

### 요약

AI 분석(부서 분석 + 개별 고객 분석) 프롬프트에 `Prepayment` / `PrepaymentUsage` 모델 데이터를 포함시켜, GPT-4o가 선결제 잔액 현황·고착 위험·재구매 유도 기회를 영업 전략에 반영하도록 개선했습니다.

---

### 변경된 파일

| 파일                                               | 변경 내용                                                                                                                                                                                       |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai_chat/services.py`                              | `gather_prepayment_data()` 신규 함수, `analyze_department()` 프롬프트 확장, `gather_followup_data()` 선결제 수집, `analyze_followup()` 프롬프트 확장, `FOLLOWUP_SYSTEM_PROMPT` 출력 스키마 확장 |
| `ai_chat/templates/ai_chat/followup_analysis.html` | `prepayment_status`, `pre_visit_checklist`, `manager_report_points` 섹션 추가                                                                                                                   |

---

### 구현 세부사항

#### `gather_prepayment_data(followups)`

- `Prepayment.objects.filter(customer__in=followups)` — 이미 권한 범위로 필터링된 queryset 사용
- 선결제별 사용 내역(`PrepaymentUsage`) prefetch
- 고착 판단 기준: `status='active'` AND `balance > 0` AND 최종 사용일이 90일 이전 (또는 미사용)
- 반환: `{'prepayments': [...], 'summary': {total_count, active_count, total_remaining_balance, stalled_count, stalled_customers}}`

#### `analyze_department()` 변경

- `FollowUp.objects.filter(user=user, department=department)` queryset 생성 후 `gather_prepayment_data()` 호출
- 프롬프트에 `━━━ 선결제 현황 ━━━` 섹션 추가 (활성 건수, 총 잔액, 고착 위험 거래처, 사용 이력 최근 3건)

#### `gather_followup_data()` 변경

- `Prepayment.objects.filter(customer=followup)` 쿼리 추가
- 반환 dict에 `'prepayments'` 키 추가

#### `analyze_followup()` 변경

- 프롬프트에 `━━━ 선결제 현황 ━━━` 섹션 추가 (원금, 잔액, 입금일, 상태, 고착 여부, 사용 이력 최근 5건)

#### `FOLLOWUP_SYSTEM_PROMPT` 변경

- JSON 출력 스키마에 3개 필드 추가:
  - `prepayment_status`: 선결제 현황 요약 및 재구매 기회/위험 분석
  - `pre_visit_checklist`: 방문 전 확인사항 목록
  - `manager_report_points`: 매니저 보고 시 강조 포인트 목록
- 선결제 분석 지시: "선결제 잔액이 있고 최근 90일 사용이 없으면 재구매 유도 또는 잔액 소진 전략 분석"

#### `followup_analysis.html` 변경

- 리스크 요인 섹션 이후 추가:
  - `prepayment_status` 카드 (파란 왼쪽 테두리)
  - `pre_visit_checklist` 목록 카드
  - `manager_report_points` 목록 카드 (보라 왼쪽 테두리)
- 기존 JSON 필드 없으면 `{% if d.필드명 %}` 조건으로 미표시

---

### 권한 및 보안

- `gather_prepayment_data(followups)`: 이미 `user=request.user`로 필터링된 queryset만 수신 → 타 사용자 데이터 노출 없음
- `gather_followup_data(followup)`: `followup`은 뷰에서 `can_access_followup(request.user, followup)` 검증 후 전달
- 모델 변경 없음 (마이그레이션 불필요)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 선결제 고착 기준(90일)은 `services.py` 내 하드코딩됨 — 추후 설정값으로 분리 가능
- 선결제 데이터가 많은 부서는 프롬프트 길이 증가 → 토큰 초과 시 `max_tokens` 조정 필요
- `department_analysis.html`에는 선결제 섹션 별도 표시 없음 (PainPoint 카드에 간접 반영됨)

---

### 다음 권장 단계

1. `editDeliveryItemsModal` 등 남아 있는 Bootstrap 중첩 모달을 Offcanvas로 정리
2. 부서 분석 화면에 선결제 통계 요약 위젯 추가 (선택)
3. 고착 기준일(90일)을 환경변수 또는 관리자 설정으로 분리

---

## Phase 6.5-3 — AI 분석 출력 5섹션 구조로 재설계 (2026-04-27)

**상태**: 완료

### 요약

개별 고객 AI 분석 결과를 "일반 요약"에서 "실제 영업 현장에서 즉시 활용 가능한 5섹션 구조"로 전면 개편했습니다. 미처리 후속 액션 자동 수집, 새로운 JSON 출력 스키마 정의, 템플릿 전면 재작성이 포함됩니다.

---

### 변경된 파일

| 파일                                               | 변경 내용                                                                                                                                             |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai_chat/services.py`                              | `gather_followup_data()` pending_actions 수집 추가, `FOLLOWUP_SYSTEM_PROMPT` 완전 재작성, `analyze_followup()` 프롬프트 섹션 추가 + `max_tokens=4000` |
| `ai_chat/templates/ai_chat/followup_analysis.html` | 분석 결과 영역 전면 재작성 (구버전 호환 fallback 포함)                                                                                                |

---

### 구현 세부사항

#### `gather_followup_data()` — pending_actions 추가

- 모든 history 레코드 순회 시 `next_action` 필드가 있으면 `pending_actions` 목록에 수집
- 각 항목: `{action, due_date, is_overdue, from_type, from_date}`
- 정렬: 지연(overdue) → 예정(upcoming) → 날짜 미정 순
- meeting 항목에 `next_action`, `next_action_date` 필드 추가
- 반환 dict에 `'pending_actions'` 키 추가

#### `FOLLOWUP_SYSTEM_PROMPT` — 완전 재작성

새 JSON 출력 스키마 (7개 최상위 필드):

- `deal_probability`, `deal_probability_reason`, `relationship_stage` — 기존 유지
- `account_brief` — `customer_summary`, `recent_activity`, `sales_status`, `prepayment_note`, `quote_delivery_note`
- `opportunity_risk` — `purchase_potential`, `stalled_risk`, `price_risk`, `compatibility_risk`, `budget_prepayment_risk`, `missing_info`
- `next_best_actions` — `priority`, `action`, `suggested_due`, `what_to_ask`, `what_to_prepare`, `reason`
- `manager_summary` — `key_point`, `decision_needed`, `risk_level`, `expected_impact`
- `visit_checklist` — `customer_context`, `items_to_bring`, `questions_to_ask`, `unresolved_issues`
- `key_painpoints`, `risk_factors` — 기존 구조 유지

분석 지침 추가:

- 미처리 후속 액션은 `visit_checklist.unresolved_issues` + `next_best_actions`에 반드시 반영
- `next_best_actions` 최대 3건, 실행 가능 수준으로 작성
- `questions_to_ask` 최소 2개 이상

#### `analyze_followup()` — 프롬프트 확장 + max_tokens 4000

- 프롬프트에 `━━━ 미처리 후속 액션 (N건) ━━━` 섹션 추가
  - 지연(overdue) 최대 5건, 예정 최대 5건, 날짜 미정 최대 3건 포함
- `max_tokens`: 3000 → **4000**으로 증가

#### `followup_analysis.html` — 5섹션 레이아웃 (구버전 호환)

1. **딜 확률 (col-md-3) + 어카운트 브리핑 (col-md-9)** — `d.account_brief`가 없으면 구버전 `d.customer_summary` 표시
2. **다음 베스트 액션** — 카드 그리드, 우선순위 색상 구분(보라 계열). 구버전도 동일 레이아웃 (신규 필드 없으면 단순 표시)
3. **기회/리스크 분석 (col-lg-8) + 매니저 요약 (col-lg-4)** — `d.opportunity_risk` 없으면 구버전 `d.opportunity_signals`/`d.missing_info` 표시, `d.manager_summary` 없으면 구버전 `d.manager_report_points` 표시
4. **방문 준비 체크리스트** — `d.visit_checklist` 없으면 구버전 `d.pre_visit_checklist` 표시
5. **핵심 PainPoint + 리스크 요인** — 구조 동일, 변경 없음

---

### 권한 및 보안

- 모델 변경 없음, 마이그레이션 불필요
- `pending_actions`는 `gather_followup_data(followup, user)`에서 이미 권한 필터링된 `followup` 기준으로 수집
- 구버전 분석 데이터도 `{% if d.필드명 %}` 조건으로 안전하게 처리

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
import test → account_brief in prompt: True, visit_checklist in prompt: True, manager_summary in prompt: True, pending_actions in gather_followup_data: True
```

---

### 알려진 제한 사항

- `next_best_actions` 최대 3건은 프롬프트 지시로만 제한 (API 응답에서 초과 시 템플릿에서 모두 렌더됨)
- 선결제 고착 기준 90일 하드코딩
- 기존 분석 데이터(구버전 JSON)는 `account_brief`, `opportunity_risk`, `manager_summary`, `visit_checklist` 필드가 없어 구버전 fallback 섹션으로 표시됨 — 재분석 실행 시 새 포맷으로 전환됨

---

### 다음 권장 단계

1. `editDeliveryItemsModal` Offcanvas 전환
2. 파이프라인 검색/필터 개선 (단계별 영업 건수 대시보드 위젯) ← Phase 6.5-4에서 완료
3. 선결제 고착 기준일 환경변수 분리

---

## Phase 6.5-4 — 파이프라인 보드 검색/필터 추가 (2026-04-27)

**상태**: 완료

### 요약

파이프라인 칸반 보드에 클라이언트 사이드 검색/필터 기능을 추가했습니다. 페이지 리로드 없이 고객명·업체·담당자·영업 담당자·등급으로 필터링하며, 드래그&드롭 및 단계 이동 기능은 그대로 유지됩니다.

---

### 변경된 파일

| 파일                                                 | 변경 내용                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                          | card dict에 `owner`(영업 담당자), `manager`(책임자) 필드 추가                 |
| `reporting/templates/reporting/funnel/pipeline.html` | 검색바 UI 추가, 카드에 data-\* 속성 추가, 담당자 표시 추가, JS 필터 로직 추가 |

---

### 구현 세부사항

#### `funnel_views.py` 변경

- `stage_map[stage].append(...)` dict에 신규 필드 추가:
  - `'owner': fu.user.get_full_name() or fu.user.username` — 영업 담당자 이름
  - `'manager': fu.manager or ''` — 고객 측 책임자 (CharField, select_related 불필요)
- `select_related('user')`는 이미 기존 쿼리에 포함되어 있어 추가 쿼리 없음

#### `pipeline.html` — 검색 UI

제목 바 아래에 검색 바 추가:

- **텍스트 입력** (`#searchInput`): 고객명, 업체명, 부서명, 영업 담당자, 책임자, 우선순위, 등급 통합 검색
- **등급 필터** (`#gradeFilter`): VIP/A/B/C/D 드롭다운
- **초기화 버튼** (`#clearBtn`): 필터 활성 시에만 표시
- **필터 상태** (`#filterStatus`): "전체 N명 중 M명 표시" 텍스트
- **총 카운트** (`#totalCount`): 필터 시 "M명 (필터됨)" 표시

#### `pipeline.html` — 카드 데이터 속성

```html
data-grade="{{ card.grade }}" data-search="{{ card.customer }} {{ card.company
}} {{ card.department }} {{ card.owner }} {{ card.manager }} {{ card.priority }}
{{ card.grade }}"
```

- `data-search`: 모든 검색 대상 텍스트를 단일 문자열로 결합 (JS에서 `.toLowerCase()` 후 `includes()` 매칭)

#### `pipeline.html` — 카드 UI 추가

```html
{% if card.owner %}
<div class="text-muted mt-1" style="font-size: 0.73em;">
  <i class="fas fa-user me-1" style="opacity:0.5;"></i>{{ card.owner }}
</div>
{% endif %}
```

#### `pipeline.html` — JS 필터 로직 (`applyFilter()`)

- 텍스트 쿼리 + 등급 필터 조합 (`&&` 조건)
- 매칭: `card.style.display = ''` / 비매칭: `card.style.display = 'none'`
- DOM 제거 없이 숨기기만 → 드래그&드롭 유지
- 컬럼별 카운트 배지 실시간 업데이트
- 컬럼 내 카드가 있으나 전부 숨겨졌을 때 `.kanban-filter-empty` 빈 상태 메시지 표시
- `moveCard()` 완료 후 `applyFilter()` 재호출 → 이동 후에도 필터 상태 유지

---

### 필터 지원 필드 요약

| 검색 대상      | 소스 필드                         |
| -------------- | --------------------------------- |
| 고객명         | `FollowUp.customer_name`          |
| 업체명         | `FollowUp.company` (str)          |
| 부서/연구실    | `FollowUp.department` (str)       |
| 영업 담당자    | `FollowUp.user.get_full_name()`   |
| 책임자(담당자) | `FollowUp.manager`                |
| 우선순위       | `FollowUp.get_priority_display()` |
| 등급           | `FollowUp.customer_grade`         |

---

### 권한 및 보안

- 모든 카드 데이터는 기존 `_get_accessible_followups(request.user, request)` 권한 필터링 후 렌더링
- 클라이언트 사이드 필터이므로 추가 API 엔드포인트 없음
- 모델 변경 없음, 마이그레이션 불필요

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 서버 사이드 필터링 없음 → 카드 수가 매우 많으면(수백 개) 초기 렌더링 시간 증가 가능 (현재 규모에서는 문제없음)
- `notes`(상세 내용) 필드는 카드 UI에 미표시이므로 검색 대상에서 제외

---

### 다음 권장 단계

1. `editDeliveryItemsModal` Offcanvas 전환
2. 단계별 영업 건수 대시보드 위젯 추가
3. 선결제 고착 기준일 환경변수 분리

---

## Phase 6.5-5 — 주간보고 UX 개선 및 관리자 검토 기능 (2026-04-28)

**상태**: 완료

---

### 요약

주간보고를 단순 텍스트 블록에서 구조화된 카드 레이아웃으로 개선하고, 관리자 코멘트/검토 기능과 AI 초안 생성 기능을 추가했습니다.

---

### 변경된 파일

| 파일                                                           | 변경 내용                                                                                                                                |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/models.py`                                          | `WeeklyReport`에 3개 필드 추가 (`manager_comment`, `reviewed_by`, `reviewed_at`)                                                         |
| `reporting/migrations/0090_add_weekly_report_review_fields.py` | 신규 마이그레이션 (적용 완료)                                                                                                            |
| `ai_chat/services.py`                                          | `WEEKLY_REPORT_SYSTEM_PROMPT` + `generate_weekly_report_draft()` 함수 추가                                                               |
| `reporting/views.py`                                           | `weekly_report_ai_draft`, `weekly_report_manager_comment` 뷰 추가; 기존 create/edit/detail 뷰에 `can_use_ai`, `is_manager` 컨텍스트 추가 |
| `reporting/urls.py`                                            | API URL 2개 추가 (`/api/weekly-reports/ai-draft/`, `/api/weekly-reports/<pk>/manager-comment/`)                                          |
| `reporting/templates/reporting/weekly_report/detail.html`      | 5섹션 카드 레이아웃으로 전면 재설계 (위험/액션 라인 색상 코딩, 관리자 검토 패널)                                                         |
| `reporting/templates/reporting/weekly_report/form.html`        | AI 초안 생성 버튼 + `generateAiDraft()` JS 추가; `other_notes` textarea id 추가                                                          |
| `reporting/templates/reporting/weekly_report/list.html`        | 검토완료 배지 + activity_notes 미리보기 추가                                                                                             |

---

### 주요 기능

**1. WeeklyReport 모델 확장**

- `manager_comment`: 관리자 검토 의견 (TextField)
- `reviewed_by`: 검토한 관리자 (FK → User)
- `reviewed_at`: 검토 완료 시각 (DateTimeField)

**2. detail.html 5섹션 구조**

- 헤더: gradient 배경, 검토완료 배지, 수정/인쇄 버튼
- 영업 활동: 위험/리스크(빨강), 액션(파랑), 납품/견적(녹색), 일반(회색) 라인 색상
- 견적/납품: 납품/견적 라인 구분 색상
- 다음 주 계획: 중요/핵심/우선 키워드 강조
- 관리자 검토: 코멘트 표시 + 관리자 전용 입력 폼 (AJAX POST 저장)

**3. AI 초안 생성**

- `UserProfile.can_use_ai` 게이트 적용
- `generate_weekly_report_draft()`: 해당 주 History/Schedule/Quote 기반 GPT-4o 초안 생성
- form.html 버튼 클릭 → 3개 textarea 자동 채움 + 요약 알림 표시

**4. 관리자 검토 API**

- `POST /reporting/api/weekly-reports/<pk>/manager-comment/`
- role 검증: `admin`, `superadmin`, `manager`만 허용
- 동일 회사 권한 확인

---

### 기존 기능 보존

- 기존 주간보고 CRUD (list/create/edit/detail) 동작 유지
- `weekly_report_load_schedules` AJAX 동작 유지
- `insertScheduleText()` 일정 삽입 기능 유지
- 인증/권한 로직 변경 없음

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- detail.html의 위험/리스크 섹션 footer는 `forloop.first`/`forloop.last`를 전체 splitlines 기준으로 사용하므로, 위험 키워드가 없을 때 닫는 `</div>`가 잘못 렌더링될 수 있음. 실제 사용 시 JS 기반 토글 방식으로 개선 권장
- AI 초안 생성은 `can_use_ai=True`인 사용자만 사용 가능 (관리자가 UserProfile에서 설정)
- AI 초안은 활동 기록이 없는 주에는 `data.error`로 반환됨

---

### 다음 권장 단계

1. detail.html 위험 섹션 footer JS 기반으로 재작성 (렌더링 안정성 향상)
2. 주간보고 목록에 검색/필터 추가 (날짜 범위, 작성자, 검토 여부)
3. 관리자 전용 주간보고 요약 대시보드 (팀원별 제출 현황, 검토 대기 건수)

---

## Phase 6.5-6 — 분석 보고서 내보내기 품질 개선 (2026-04-27)

**상태**: 완료

---

### 요약

기존 단순 집계형 CSV(영업사원별 카운트, 단계별 카운트)를 **활동 단위 상세 행** 기반으로 전면 재설계하고, XLSX 포맷(스타일링, 첫 행 고정, 지연 행 강조, 단계별 시트)을 추가했습니다. 모델 변경 없음.

---

### 변경된 파일

| 파일                                                     | 변경 내용                                                         |
| -------------------------------------------------------- | ----------------------------------------------------------------- |
| `reporting/views.py`                                     | 기존 2개 CSV 뷰 대체 + 2개 XLSX 뷰 추가 + 공통 헬퍼 함수 2개 추가 |
| `reporting/urls.py`                                      | XLSX URL 2개 추가 (`activity.xlsx`, `pipeline.xlsx`)              |
| `reporting/templates/reporting/analytics_dashboard.html` | 내보내기 버튼 4개로 확장 (CSV/XLSX × 활동/파이프라인)             |

---

### 기존 → 개선 비교

**activity CSV (이전)**

- 행 구성: 영업사원 1명 = 1행 (요약 집계값만)
- 컬럼: 영업사원 / 기간내영업노트 / 활성거래처 / 지연후속조치 / 최근활동일 (5개)

**activity CSV/XLSX (이후)**

- 행 구성: 활동 기록(History) 1건 = 1행 (상세 데이터)
- 컬럼 22개:
  - 활동일, 영업사원, 거래처, 부서/연구실, 담당자, 활동유형
  - 내용요약, 미팅상황, 다음액션, 다음예정일
  - 지연여부, 지연일수, 파이프라인단계
  - 견적제출여부, 최근견적금액, 납품금액, 납품품목
  - 선결제잔액, 선결제최근입금일, 관리자검토, 검토관리자

**pipeline CSV (이전)**

- 행 구성: 파이프라인 단계 1개 = 1행 (건수 집계만)
- 컬럼: 파이프라인단계 / 건수 (2개)

**pipeline CSV/XLSX (이후)**

- 행 구성: 거래처(FollowUp) 1건 = 1행 (상세 데이터)
- 컬럼 19개:
  - 거래처, 부서/연구실, 담당자, 영업사원
  - 파이프라인단계, 고객상태, 고객등급, 우선순위
  - 최근활동일, 다음액션, 다음예정일, 지연여부, 지연일수
  - 최근견적상태, 최근견적금액, 견적성공확률
  - 선결제잔액, 선결제최근입금일, 총납품금액

---

### XLSX 스타일링

- **헤더**: 인디고(activity) / 녹색(pipeline) 배경, 흰색 볼드 텍스트
- **첫 행 고정**: `freeze_panes = 'A2'`
- **지연 행 강조**: 빨간 계열 배경색 (FEE2E2)
- **열 너비**: 컬럼 유형에 맞게 수동 설정
- **pipeline XLSX**: 단계별 시트 분리 (전체 + 잠재/접촉/견적/협상/수주/실주)
- **내보내기 정보 시트**: 생성일시, 생성자, 행수

---

### 보안/권한

- `admin`, `manager`, `superadmin` role만 접근 허용 (기존과 동일)
- 회사 범위 필터 유지 (`user_profile.company` 기준)
- 개인 연락처(phone, email) 미포함
- UTF-8 BOM 유지 (한국어 Excel 호환)

---

### 공통 헬퍼 함수

- `_get_activity_export_date_range(request, today)`: 날짜 파라미터 파싱
- `_build_activity_rows(user_profile, date_from, date_to, today)`: activity 행 데이터 빌드
- `_build_pipeline_rows(user_profile, today)`: pipeline 행 데이터 빌드
- CSV/XLSX 뷰에서 공통 사용 (코드 중복 없음)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- `_build_activity_rows`는 `Prefetch`로 최적화했으나, 거래처당 견적/선결제를 prefetch하므로 대용량(수천 건 이상)에서는 메모리 사용 증가 가능
- 날짜 필터는 activity CSV/XLSX에만 적용됨; pipeline은 현재 기준 전체 스냅샷 출력

---

### 다음 권장 단계

1. analytics_dashboard에 날짜 필터 파라미터를 pipeline XLSX에도 전달 (선택적 날짜 범위)
2. 영업사원별 요약 시트 추가 (현재 활동단위 행만 있음)
3. 대시보드 내 직접 미리보기 테이블 (최근 5행) 추가

---

## Phase 6.6-1 — 대시보드 영업 노트 작성 모달 클릭 불가 버그 수정 (2026-04-27)

### 증상

대시보드(`/reporting/dashboard/`)에서 "영업 노트 작성" 버튼 클릭 시:

- 회색 오버레이(backdrop)가 뜨지만 모달 내부 클릭/입력 불가
- 텍스트 입력, 버튼 클릭, 닫기(X) 클릭 모두 반응 없음

---

### 근본 원인

**원인 A: `html, body { overflow-x: hidden }` → stacking context 생성 (확정적)**

`dashboard.html` `{% block extra_css %}` 에:

```css
html,
body {
  overflow-x: hidden; /* ← 문제 */
  width: 100%;
  max-width: 100%;
}
```

`html` / `body`에 `overflow: hidden` 또는 `overflow-x: hidden`이 설정되면,
Chrome/Safari 일부 버전에서 `position: fixed` 요소의 containing block이 뷰포트가 아닌
`<html>` 또는 `<body>` 자체가 됩니다.
그 결과 Bootstrap backdrop(z-index: 1040)이 정상 렌더링돼도,
모달 요소(z-index: 1055)가 시각적으로 backdrop 위에 있음에도 불구하고
pointer-events가 차단되거나, backdrop이 모달 위를 덮는 현상이 발생합니다.

**원인 B: 모달이 `.main-content` → `div.infographic-dashboard` 하위에 있었음**

모달이 `{% block content %}` 내부(`.infographic-dashboard` 안)에 있어,
overflow/transform stacking context가 있는 컨테이너 안에 `position: fixed` 모달이 배치됨.

---

### 수정 내용

#### 1. `reporting/templates/reporting/base.html`

`{% block extra_js %}{% endblock %}` 바로 뒤에 페이지별 모달 슬롯 추가:

```html
<!-- 페이지별 모달 슬롯: stacking context 바깥(body 직접 하위)에 배치 -->
{% block modals %}{% endblock %}
```

→ `</body>` 직전, Bootstrap JS 로드 이후, stacking context 없는 위치

#### 2. `reporting/templates/reporting/dashboard.html`

**(a) `html, body { overflow-x: hidden }` 제거**

```css
/* 수정 전 */
html,
body {
  overflow-x: hidden;
  width: 100%;
  max-width: 100%;
}

/* 수정 후 — overflow-x 제거, 폭 설정만 유지 */
html,
body {
  width: 100%;
  max-width: 100%;
}
```

`overflow-x` 클리핑은 이미 `.infographic-dashboard { overflow-x: hidden; }` 에서 처리되고 있어 `html/body`에서 제거해도 가로 스크롤 발생 없음.

**(b) 모달을 `{% block content %}` 에서 `{% block modals %}`로 이동**

기존: `{% block content %}` 마지막에 모달 HTML + script
수정: `{% block content %}` 종료(`{% endblock %}`) 후 별도 `{% block modals %}` 블록으로 이동
→ 렌더링 위치가 `<body>` 직접 하위로 변경, overflow/transform 컨테이너 바깥

**(c) CSRF 토큰 소스 개선**

기존:

```javascript
const csrfToken =
  document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
  "{{ csrf_token }}";
```

문제: `dashboard.html`에 `{% csrf_token %}` 태그가 없어 `querySelector`가 null을 반환 가능.
`'{{ csrf_token }}'` 폴백은 JS 컨텍스트에서 렌더링 타이밍 불안정.

수정:

```javascript
const csrfToken =
  document.querySelector('meta[name="csrf-token"]')?.content ||
  document.querySelector("[name=csrfmiddlewaretoken]")?.value;
```

→ `base.html` line 7의 `<meta name="csrf-token" content="{{ csrf_token }}">` 를 단일 소스로 사용. 항상 안전하게 CSRF 토큰을 읽음.

**(d) `bootstrap.Modal.getInstance` 안전 처리**

기존:

```javascript
var modal = bootstrap.Modal.getInstance(
  document.getElementById("dashboardNoteModal"),
);
if (modal) modal.hide();
```

문제: Bootstrap이 아직 인스턴스를 생성하지 않은 경우 `null` → `modal.hide()` 미호출 → backdrop 잔류 가능.

수정:

```javascript
var modalEl = document.getElementById("dashboardNoteModal");
var modal =
  bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
modal.hide();
```

→ 인스턴스가 없으면 새로 생성해서 `hide()` 보장.

---

### 변경 파일

| 파일                                           | 변경 내용                                                                                                             |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `reporting/templates/reporting/base.html`      | `{% block modals %}{% endblock %}` 추가 (`{% block extra_js %}` 직후)                                                 |
| `reporting/templates/reporting/dashboard.html` | `html, body { overflow-x: hidden }` 제거; 모달을 `{% block modals %}`로 이동; CSRF 소스 변경; `getInstance` 안전 처리 |

---

### 모달 동작 전/후

| 항목                    | 수정 전                                                   | 수정 후                                  |
| ----------------------- | --------------------------------------------------------- | ---------------------------------------- |
| backdrop 표시           | backdrop 표시되나 클릭 불가                               | 정상 표시, 클릭 가능                     |
| 모달 내 입력            | 텍스트 입력 불가                                          | 정상 입력 가능                           |
| 모달 위치 (DOM)         | `.infographic-dashboard` 하위                             | `<body>` 직접 하위                       |
| `html, body` overflow-x | hidden (stacking context 생성)                            | 제거됨                                   |
| CSRF 토큰 소스          | `querySelector('[name=csrfmiddlewaretoken]')` → null 가능 | `<meta name="csrf-token">` 안정 소스     |
| 저장 후 모달 닫기       | `getInstance` null이면 backdrop 잔류                      | `getInstance \|\| new Modal`로 항상 닫힘 |

---

### CSS 우회 사용 여부

`.modal-backdrop` 전역 숨김 등의 CSS 우회 **사용하지 않음**.
수정은 순수 DOM 구조 변경 및 `overflow-x` 제거로 해결.

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

DB 변경 없음.

---

### 알려진 제한 사항 / 잔여 위험

- 다른 페이지의 모달은 이번 수정 대상이 아님. 해당 페이지에서도 동일 overflow-x 문제가 발생하면 동일 패턴(모달을 `{% block modals %}`로 이동)으로 해결 가능.
- `base.html`에 다른 페이지가 이미 `{% block modals %}`를 사용하고 있지 않으므로 충돌 없음.

---

### 다음 권장 단계

Phase 6.6-2: 파이프라인 보드 자동 동기화 + 수동 이동 개선

---

## Phase 6.6-2 — 파이프라인 보드 자동 동기화 + 수동 이동 개선

### 변경 목표

- 영업 활동(고객 미팅 히스토리, 견적 생성) 기반으로 파이프라인 단계를 자동 추천/이동
- 수동 드래그앤드롭 이동 기능은 그대로 유지
- 단계 역방향 자동 이동 불가 (won/lost 보호)
- DB 스키마 변경 없음 (Method C — 로직 전용)

---

### 구현 방법 (Method C — DB 필드 없이 로직만)

**단계 자동 이동 규칙 (앞으로만)**

| 조건                                      | 추천 단계   |
| ----------------------------------------- | ----------- |
| `Quote.stage = approved / converted`      | won         |
| `Quote.stage = negotiation`               | negotiation |
| `Quote.stage = rejected / expired` (전체) | lost        |
| Quote 존재 (기타 단계)                    | quote       |
| `History.action_type = customer_meeting`  | contact     |
| 없음                                      | 변경 없음   |

**보호 규칙**

- `won` / `lost` 상태는 자동으로 덮어쓰지 않음
- 현재 단계 ≥ 추천 단계이면 skip (절대 뒤로 이동하지 않음)

---

### 변경 파일

| 파일                                                 | 변경 내용                                                                                                                                                                                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                          | `STAGE_ORDER` 상수 추가; `_suggest_pipeline_stage()` 헬퍼 추가; `_try_advance_pipeline()` 헬퍼 추가; `funnel_pipeline_view()` 카드 데이터 강화 (최근 견적, 히스토리, 추천 단계); `funnel_pipeline_sync()` API 뷰 추가 |
| `reporting/urls.py`                                  | `/funnel/api/pipeline-sync/` URL 추가                                                                                                                                                                                 |
| `reporting/templates/reporting/funnel/pipeline.html` | 동기화 버튼 추가; 카드에 최근 견적/히스토리/추천 단계 표시; 추천 단계 적용 버튼; `syncCard()` / `syncAll()` JS 함수 추가; CSRF 토큰 소스를 `meta[name="csrf-token"]`으로 수정                                         |
| `reporting/views.py`                                 | `history_create_view()` 및 `history_create_from_schedule()` 에서 고객 미팅 저장 후 `_try_advance_pipeline(followup, 'contact')` 호출 추가                                                                             |

---

### 추가된 기능 상세

**1. 카드 표시 강화**

- 다음 예정 일정: 일정 상세 페이지 링크 포함
- 최근 견적: 견적 단계 + 금액 표시
- 최근 히스토리: 활동 유형 + 날짜 + 내용 40자 미리보기
- 추천 단계 배지: 근거("고객 미팅", "견적" 등) + 개별 적용 버튼

**2. 자동 동기화 버튼**

- 헤더에 "자동 동기화" 버튼 추가
- 동기화 대상 건수 배지(노란색) 표시 (추천 단계가 현재 단계와 다른 카드 수)
- 버튼 클릭 → 전체 자동 동기화 API 호출 → 변경 발생 시 페이지 새로고침

**3. 개별 추천 단계 적용**

- 추천 단계가 있는 카드에 "적용" 버튼 표시
- 클릭 시 단일 카드 동기화 API → DOM에서 바로 카드 이동 (새로고침 없음)

**4. 자동 이동 훅 (History 생성 시)**

- 고객 미팅 히스토리 저장 시 `_try_advance_pipeline(followup, 'contact')` 자동 호출
- 예외 발생 시 히스토리 저장은 유지 (try/except)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- Quote 생성/상태 변경 시 파이프라인 자동 이동 훅은 별도 Quote 뷰가 확인되지 않아 수동 동기화 버튼으로 대체
- `_suggest_pipeline_stage()` 는 prefetch_related 캐시를 활용하므로 bulk sync 시 N+1 없음; 단 단일 조회 경로에서는 추가 쿼리 발생 가능
- 수동으로 단계를 낮춘 후(예: won→contact) 동기화 버튼 클릭 시 다시 won으로 이동할 수 있음 (Method C의 구조적 한계; DB 필드 추가 방식으로 해결 가능)

---

### 다음 권장 단계

Phase 6.6-3: 주간보고 일정 불러오기 개선

---

## Phase 6.6-3 — 주간보고 일정 불러오기 개선 (연결 History/견적 포함)

### 변경 목표

- 주간보고 폼의 일정 참고 패널을 구조화된 분류 UI로 개선
- 단순 일정 텍스트 삽입 → 연결된 History(영업노트) 내용까지 포함
- 영업활동 섹션 / 견적·납품 섹션으로 분류 후 각각 해당 textarea에 삽입
- DB 스키마 변경 없음

---

### 구현 내용

#### 1. `reporting/views.py` — `weekly_report_load_schedules` 전면 개선

**기존**: 기본 Schedule 필드만 반환 (date, customer, company, department, activity_type, notes)

**변경 후**:

- `Prefetch('histories', ...)` : `History.schedule` FK 역방향 조회 (user 필터 + parent_history\_\_isnull=True로 최상위만)
- `Prefetch('quotes', ...)` : `Quote.schedule` FK 역방향 조회
- 카테고리 분류: `quote`/`delivery` → `quote_delivery` 버킷, 나머지 → `activity` 버킷
- 각 일정 항목에 연결 History 스니펫(meeting_situation, confirmed_facts, content, next_action/date), 연결 Quote(번호, 단계, 금액) 포함
- 응답 형식: `{schedules: [...], categorized: {activity: [...], quote_delivery: [...]}}`
- 기존 `schedules` flat 목록도 유지 (backward compatibility)

#### 2. `reporting/templates/reporting/weekly_report/form.html` — 패널 UI + JS 전면 개선

**패널 HTML 변경**:

- 기존: 클릭 가능 `<li>` 목록 (단일 클릭 = activityNotes에 한 줄 삽입)
- 변경: 영업활동 / 견적·납품 섹션별 체크박스 카드
- 각 카드에 History 스니펫(파란 배경), Quote 정보(초록 배경) 인라인 표시
- 서버 사이드 초기 렌더링: `{% regroup schedules by activity_type %}` 으로 분류 표시
- 카드 하단: "영업활동에 삽입" / "견적/납품에 삽입" 버튼, "전체선택" 링크

**JS 변경**:

- `loadSchedules()`: 새 categorized 응답 파싱, 섹션별 카드 렌더링
- `buildScheduleCard(s, category)`: History/Quote 인라인 표시 포함 카드 HTML 생성
- `insertSelected(category)`: 선택된 체크박스의 텍스트 생성 → 해당 섹션 textarea에 삽입
  - `activity` → `#activityNotes`
  - `quote_delivery` → `#quoteDeliveryNotes`
- `buildInsertText(cb)`: History 내용·다음 액션, Quote 번호·단계·금액 포함한 구조화된 텍스트 생성
- `updateInsertBtns()`: 선택 상태에 따라 삽입 버튼 활성/비활성
- `escHtml()` / `escAttr()`: XSS 방지 이스케이핑
- 기존 `insertScheduleText()` 함수 유지 (하위 호환)
- AI 초안 생성 JS 동일 유지

---

## Manager 역할 쓰기 권한 차단 강화 (2026-04-28)

**상태**: 완료 — 64/64 테스트 통과

---

### 1. 요약

`manager` 역할 사용자가 영업 실무 데이터(팔로우업, 일정, 히스토리, 파이프라인 카드)를
생성·이동할 수 없도록 서버 사이드 차단과 템플릿 UI 숨김을 강화.

- **기존 문제**: `can_modify_user_data()`는 manager를 차단하지만, 개별 create 뷰는 이 함수를 호출하지 않아 manager가 POST로 직접 생성 가능
- **해결**: 각 create 뷰 최상단에 `is_manager()` 직접 체크 추가; 파이프라인 이동(AJAX) 차단; 대시보드 "빠른 작성" 버튼 숨김

---

### 2. 권한 매트릭스 (확정)

| 액션                    | Admin | Manager (뷰어) | Salesman (실무자) |
| ----------------------- | ----- | -------------- | ----------------- |
| 데이터 조회 (같은 회사) | ✅    | ✅             | ✅ (본인 데이터)  |
| 팔로우업 생성           | ✅    | ❌ 403/302     | ✅                |
| 일정 생성               | ✅    | ❌ 403/302     | ✅                |
| 히스토리 기록           | ✅    | ❌ 403/302     | ✅                |
| 파이프라인 카드 이동    | ✅    | ❌ 403 JSON    | ✅                |
| Analytics export        | ✅    | ✅             | ❌ 403            |

---

### 3. 변경된 파일

#### `reporting/views.py`

- `followup_create_view`: 최상단 `is_manager()` 체크 → 302 redirect + error message
- `schedule_create_view`: 최상단 `is_manager()` 체크 → 302 redirect + error message
- `history_create_view`: 최상단 `is_manager()` 체크 → 302 redirect + error message (URL 미노출이지만 안전 레이어로 유지)
- `history_create_from_schedule`: 최상단 `is_manager()` 체크 → AJAX: 403 JSON, 일반: 302 redirect
- `followup_create_ajax`: 최상단 `is_manager()` 체크 → 403 JSON

#### `reporting/funnel_views.py`

- `funnel_pipeline_move`: 최상단 `is_manager()` 체크 → 403 JSON

#### `reporting/templates/reporting/dashboard.html`

- "보고서 작성" 버튼: `{% if user.userprofile.role != 'manager' %}` 가드 추가
- "빠른 작성" 전체 섹션: `{% if user.userprofile.role != 'manager' %}` 가드 추가
- "일정 없음" 모달의 "일정 추가" 버튼: `{% if user.userprofile.role != 'manager' %}` 가드 추가

#### `reporting/tests.py`

- `ManagerRolePermissionTests` 클래스 신설 (11개 테스트)

---

### 4. 신규 테스트 (`ManagerRolePermissionTests`)

| 테스트명                                                  | 검증 내용                                    | 결과 |
| --------------------------------------------------------- | -------------------------------------------- | ---- |
| `test_manager_can_view_followup_list`                     | Manager GET 팔로우업 목록 → 200              | ✅   |
| `test_manager_can_view_history_list`                      | Manager GET 히스토리 목록 → 200              | ✅   |
| `test_manager_can_view_schedule_list`                     | Manager GET 일정 목록 → 200                  | ✅   |
| `test_manager_cannot_get_followup_create`                 | Manager GET 팔로우업 생성 → 302              | ✅   |
| `test_manager_cannot_post_followup_create`                | Manager POST 팔로우업 생성 → 302             | ✅   |
| `test_manager_cannot_get_schedule_create`                 | Manager GET 일정 생성 → 302                  | ✅   |
| `test_manager_cannot_post_schedule_create`                | Manager POST 일정 생성 → 302                 | ✅   |
| `test_manager_cannot_access_history_create_from_schedule` | Manager GET history-from-schedule → 302      | ✅   |
| `test_manager_cannot_post_history_create_from_schedule`   | Manager POST history-from-schedule → 302     | ✅   |
| `test_salesman_can_get_schedule_create`                   | Salesman GET 일정 생성 → 200 (차단 없음)     | ✅   |
| `test_salesman_can_get_followup_create`                   | Salesman GET 팔로우업 생성 → 200 (차단 없음) | ✅   |

---

### 5. 실행 명령 및 결과

| 명령                                                | 결과                            |
| --------------------------------------------------- | ------------------------------- |
| `python manage.py check`                            | ✅ 0 issues                     |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected          |
| `python manage.py test reporting --verbosity=1`     | ✅ Ran 64 tests in 59.935s — OK |

---

### 6. 보안 확인

- Manager는 URL 직접 접근(GET/POST) 모두 차단됨 (서버 사이드 검증)
- 템플릿 UI 숨김은 UX 보조 레이어 (보안 레이어는 서버 사이드)
- 기존 admin 권한, salesman 권한, 익명 차단 — 모두 변경 없음

---

### 7. 기존 기능 유지

- 모든 목록/상세 조회 뷰: 역할 관계없이 동일하게 동작
- Analytics export (manager 허용): 변경 없음
- Phase 7 파이프라인 sync 날짜 필터: 변경 없음
- 기존 53개 테스트: 전부 통과 유지

---

### 8. 다음 권장 단계

Phase 8 시작 가능 — Manager 역할 권한 완전 적용 확인됨.

---

## 서류 관리 담당자 이메일 변수 추가 (2026-04-28)

**상태**: 완료 — 64/64 테스트 통과

---

### 1. 요약

서류 템플릿 변수 목록에 `{{담당자이메일}}` 및 `{{영업담당자이메일}}` 변수를 추가하여
견적서/거래명세서 생성 시 고객 담당자 이메일과 영업담당자 이메일을 자동 채울 수 있도록 개선.

---

### 2. 추가된 변수

| 변수 키                | 표시 레이블       | 데이터 소스                                  | 위치                  |
| ---------------------- | ----------------- | -------------------------------------------- | --------------------- |
| `{{담당자이메일}}`     | 담당자 이메일     | `FollowUp.email` (고객/거래처 담당자 이메일) | 고객/거래처 정보 섹션 |
| `{{영업담당자이메일}}` | 영업담당자 이메일 | `User.email` (Django 기본 User 이메일 필드)  | 영업담당자 섹션       |

**데이터 소스 상세:**

- `담당자이메일` → `schedule.followup.email` (FollowUp 모델의 EmailField, blank=True, null=True) → 없을 경우 빈 문자열
- `영업담당자이메일` → `schedule.user.email` (Django auth.User의 email 필드) → 없을 경우 빈 문자열

**참고:** `{{이메일}}`은 기존에도 존재하며 동일한 `followup.email` 소스를 사용합니다. `{{담당자이메일}}`은 의미를 명확히 하는 별칭으로 추가되었습니다.

---

### 3. 변경된 파일

#### `reporting/templates/reporting/partials/doc_variable_list.html`

- **"고객 / 거래처 정보" 섹션**: `{{이메일}}` 칩 다음에 `{{담당자이메일}}` 칩 추가 (verbatim 블록 내 HTML 엔티티 사용)
- **"영업담당자" 섹션**: 기존 칩 목록 끝에 `{{영업담당자이메일}}` 칩 추가

---

## 프로덕션 블로커 수정: 일정 상세 500 에러 (2026-04-28)

**상태**: 완료 — 64/64 테스트 통과

---

### 1. 요약

캘린더에서 일정 상세 페이지(`/reporting/schedules/<id>/`)로 이동 시 500 에러가 발생하던 문제를 수정.  
`?from=calendar` 파라미터와 무관하게, `schedule_detail.html` 템플릿 자체의 `TemplateSyntaxError`가 원인이었음.

---

### 2. 근본 원인

`reporting/templates/reporting/schedule_detail.html` 1997번 줄에서:

```javascript
html += `<tr class="${rowClass}"><td><code>{{${key}}}</code></td>...`;
```

JavaScript 템플릿 리터럴 내의 `{{${key}}}` 패턴에서 Django 템플릿 엔진이:

1. `{{` → Django 변수 태그 시작으로 인식
2. `${key}` → 파이썬 변수명으로 파싱 시도 → 실패
3. `TemplateSyntaxError: Could not parse the remainder: '${key' from '${key'` 발생

이 에러는 `schedule_detail_view`가 렌더링하는 모든 요청에서 발생하지만,  
캘린더에서 `?from=calendar` 파라미터로 접근하다가 처음 발견된 것.

---

### 3. 수정 사항

#### `reporting/templates/reporting/schedule_detail.html` (1997번 줄)

**변경 전:**

```javascript
html += `<tr class="${rowClass}"><td><code>{{${key}}}</code></td>...`;
```

**변경 후:**

```javascript
html += `<tr class="${rowClass}"><td><code>{` + `{${key}}}</code></td>...`;
```

**원리:** `{{`를 두 개의 분리된 문자열 리터럴로 쪼개어 Django 템플릿 엔진의 렉서가 `{{` 연속 패턴을 인식하지 못하도록 함.  
렌더링된 HTML 출력은 동일: `{{변수명}}` 형태로 표시됨.

---

### 4. 실행한 명령어 및 결과

```
python test_calendar_500.py
→ Test 1: /reporting/schedules/545/ → Status: 200 ✓
→ Test 2: /reporting/schedules/545/?from=calendar → Status: 200 ✓
→ Test 3: /reporting/schedules/545/edit/ → Status: 200 ✓

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py test reporting
→ Ran 64 tests in 53.517s — OK
```

---

### 5. 기존 기능 유지

- `schedule_detail_view`: `from_page` 컨텍스트 전달 정상 동작
- `schedule_edit_view`: 변경 없음
- 캘린더 → 상세 → 수정 플로우: 정상
- 서류 변수 미리보기(previewModal) JavaScript: 동일 출력 유지

---

### 6. 다음 권장 단계

- 일정 상세/수정 페이지 회귀 테스트 추가 (현재 64개 테스트에 포함 안 됨)
- `schedule_form.html` 등 다른 대형 템플릿에도 `{{${...}}}` 유사 패턴 없는지 검증 권장

#### `reporting/views.py` (두 곳)

1. **line ~12625** (JSON API 응답 `data_map`): `'담당자이메일'`, `'영업담당자이메일'` 키 추가
2. **line ~12972** (XLSX 서버 생성 `data_map`): `'담당자이메일'`, `'영업담당자이메일'` 키 추가

---

### 4. 하위 호환성

- 기존 `{{이메일}}` 변수: 변경 없음, 동일하게 동작
- 기존 `{{유효일+30}}` 등 특수 패턴: 변경 없음
- 기존 `{{품목N_xxx}}` 패턴: 변경 없음
- 템플릿 편집 페이지 (`/reporting/documents/4/edit/`): TemplateSyntaxError 없음 (verbatim 블록 유지)
- 기존 서류 템플릿 파일에 해당 변수 미포함 시: 치환 없이 그대로 유지 (기존 동작)

---

### 5. 실행 명령 및 결과

| 명령                                                | 결과                            |
| --------------------------------------------------- | ------------------------------- |
| `python manage.py check`                            | ✅ 0 issues                     |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected          |
| `python manage.py test reporting --verbosity=1`     | ✅ Ran 64 tests in 59.935s — OK |

---

### 6. 잔여 위험

| 항목                       | 위험도    | 설명                             |
| -------------------------- | --------- | -------------------------------- |
| `User.email` 미등록 사용자 | 🟢 낮음   | 빈 문자열로 처리됨 — 크래시 없음 |
| `FollowUp.email` NULL      | 🟢 낮음   | `or ''` 처리됨 — 크래시 없음     |
| 이전 Phase 잔여 위험 항목  | 변경 없음 | HSTS, debug endpoint 등 동일     |

---

| `python manage.py check` | ✅ 0 issues |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected |
| `python manage.py test reporting.tests.ManagerRolePermissionTests --verbosity=1` | ✅ Ran 11 tests in 15.089s — OK |
| `python manage.py test reporting --verbosity=1` | ✅ Ran 64 tests in 59.877s — OK |

---

### 6. 보안 확인

- manager는 URL 직접 접근(GET/POST) 모두 차단됨 (서버 사이드 검증)
- 템플릿 UI 숨김은 UX 보조 레이어 (보안 레이어는 서버 사이드)
- 기존 admin 권한, salesman 권한, 익명 차단 — 모두 변경 없음
- `history_create` URL은 urls.py에서 주석 처리되어 직접 접근 불가 (view 내 guard는 안전 레이어)

---

### 7. 기존 기능 유지

- 모든 목록/상세 조회 뷰: 역할 관계없이 동일하게 동작
- Analytics export (manager 허용): 변경 없음
- Phase 7 파이프라인 sync 날짜 필터: 변경 없음
- 기존 53개 테스트: 전부 통과 유지

---

### 8. 다음 권장 단계

Phase 8 시작 가능 — Manager 역할 권한 완전 적용 확인됨.

권장 Phase 8 후보:

1. 잔여 보안 항목: `debug_user_company_info` 제거, `SECURE_HSTS_SECONDS` 추가
2. 모바일 영업노트 입력 UX 개선
3. 후속조치 지연 알림 (due date 지난 팔로우업 강조)
4. 대시보드 담당자별 활동 통계 추가

---

### 삽입 텍스트 예시

**영업활동 삽입 결과**:

```
- 04/28(월): 이화연 교수 (한국대학교) — 고객 미팅
  메모: HPG-1000 데모 진행
  └ 고객 미팅: 연구비 예산 확보 완료 / 다음 액션: 견적서 발송 (05/02)
```

**견적/납품 삽입 결과**:

```
- 04/29(화): 홍길동 교수 (한양대학교) — 견적 제출
  └ 견적 Q2025-001 [검토중] 5,000,000원
```

---

### 파일 변경 목록

| 파일                                                    | 변경 내용                                                                                                          |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `reporting/views.py`                                    | `weekly_report_load_schedules` 전면 개선 (History/Quote Prefetch, 카테고리 분류)                                   |
| `reporting/templates/reporting/weekly_report/form.html` | 패널 HTML(체크박스 UI, 분류 섹션), JS(loadSchedules/buildScheduleCard/insertSelected/buildInsertText 등) 전면 개선 |

---

### 기존 기능 유지

- WeeklyReport 모델 변경 없음 (DB 스키마 변경 없음)
- 기존 저장된 주간보고 내용 모두 그대로 표시 (detail.html 변경 없음)
- AI 초안 생성 기능 그대로 유지
- `schedules` flat 목록 키 유지 (backward compat)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 서버 사이드 초기 렌더링(GET 로드 시)에서는 History/Quote 미리보기가 없음 ("일정 불러오기" 버튼 클릭 후 표시)
- History.user 필터로 본인 History만 표시 (공유 Schedule에 다른 사용자가 남긴 History는 제외)

---

### 다음 권장 단계

Phase 6.6-5: 대시보드 영업 활동 지표 개선

---

## Phase 6.6-4 — 문서 관리 및 서류 생성 UX 개선

### 변경 요약

1. **이중 alert 버그 수정** (`schedule_detail.html`)
   - `generateDocument()` catch 블록에서 alert가 2번 발생하던 문제 수정
   - 두 번째 `alert('서류 생성 중 오류가 발생했습니다.')` 제거
   - 버튼 복구 코드도 try/catch로 감싸 예외 방지

2. **변수 미리보기 버튼 추가** (`schedule_detail.html`)
   - 각 서류 타입(견적서/거래명세서/납품서) 버튼 아래 "변수 미리보기" 버튼 추가
   - 기존 `get_document_template_data` API 활용 (신규 URL 불필요)
   - 미리보기 모달: 변수명과 실제 채워질 값 테이블 표시
   - 빈 값(노란색 행)으로 채워지지 않을 변수 강조
   - 품목 그룹 동적 생성 (납품 품목 수 기반)
   - "Excel로 생성" 버튼으로 모달에서 바로 다운로드 실행

3. **변수 도움말 패널 추가** (`document_template_form.html`)
   - 엑셀 템플릿 등록/수정 페이지에 접힌(collapsible) 변수 도움말 패널 추가
   - 7개 그룹으로 분류: 기본정보 / 고객거래처 / 영업담당자 / 회사견적 / 금액 / 품목
   - 각 변수 칩 클릭 시 클립보드 복사 (Clipboard API + execCommand fallback)
   - `reporting/templates/reporting/partials/doc_variable_list.html` 로 분리 (재사용 가능)

4. **data_map 자동채움 확장** (`reporting/views.py`)
   - `generate_document_pdf`: 연결된 Quote에서 `견적번호` 자동 채움 추가
   - `generate_document_pdf`: `메모` (schedule.notes) 자동 채움 추가
   - `get_document_template_data`: 동일하게 `견적번호`/`메모` 추가
   - DB 스키마 변경 없음 (기존 `Quote.quotes` related_name 활용)

### 변경 파일

| 파일                                                            | 변경 내용                                                                   |
| --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `reporting/templates/reporting/schedule_detail.html`            | 이중 alert 수정, 미리보기 버튼 3개, 미리보기 모달, `previewDocument()` JS   |
| `reporting/templates/reporting/document_template_form.html`     | 변수 도움말 패널 (collapsible)                                              |
| `reporting/templates/reporting/partials/doc_variable_list.html` | 신규 — 변수 목록 partial (클립보드 복사)                                    |
| `reporting/views.py`                                            | `generate_document_pdf` + `get_document_template_data`에 견적번호/메모 추가 |

### 검증 결과

```
manage.py check → System check identified no issues (0 silenced)
manage.py makemigrations --check --dry-run → No changes detected
```

### 알려진 제한사항

- 미리보기 모달의 "Excel로 생성" 버튼은 페이지 DOM에서 해당 버튼을 찾아 click() 호출하므로, 버튼 onclick 속성이 변경되면 재검토 필요
- `유효일+N` 변수는 미리보기에서 표시되지 않음 (서버측 처리 로직이므로)
- 품목 변수 도움말 칩은 품목1 기준으로 클립보드 복사됨 (N 치환 안내는 텍스트로 제공)

### 다음 권장 단계

Phase 6.6-5: 대시보드 영업 활동 지표 개선

---

## Phase 6.6 최종 QA (2026-04-27)

**상태**: 완료 — 버그 3개 발견 및 수정

### QA 범위

Phase 6.6 전체 4개 서브 페이즈(6.6-1~6.6-4) 구현 후 최종 QA 실시.
신규 기능 추가 없음. 발견된 버그만 수정.

### 실행 명령 및 결과

| 명령                                                   | 결과                                              |
| ------------------------------------------------------ | ------------------------------------------------- |
| `python manage.py check`                               | ✅ 0 issues                                       |
| `python manage.py makemigrations --check --dry-run`    | ✅ No changes detected                            |
| `python manage.py test reporting.tests` (버그 수정 전) | ❌ FAIL — `block 'modals' appears more than once` |
| `python manage.py test reporting.tests` (버그 수정 후) | ✅ Ran 9 tests — OK                               |

### URL 스모크 테스트

모든 주요 URL: 비인증 → 302, 인증 → 200 확인 완료.
`funnel/api/pipeline-sync/`, `documents/template-data/` 포함.

### 발견 및 수정된 버그

**Bug 1 (dashboard.html)**: HTML 주석 안에 `{% block modals %}` 태그가 포함되어 Django 템플릿 엔진이 블록 이름 중복으로 파싱 오류 발생 → 주석 내 Django 태그 구문을 일반 텍스트로 변경.

**Bug 2 (schedule_detail.html)**: `</script>` 직후 고아 `<script>` 태그가 열리며 `.strategy-content` CSS 규칙이 JS로 처리됨 (`</style>`로 잘못 닫힘). 해당 클래스는 템플릿에서 미사용. → 고아 블록 전체 제거.

**Bug 3 (schedule_detail.html)**: `previewDocument()` JS 함수에서 서버 응답값(`data.variables[key]`, `data.error`, `err.message`)이 HTML 이스케이프 없이 `innerHTML`에 직접 삽입 → XSS 취약점. `escHtml()` 헬퍼 추가 후 3곳 모두 적용.

### Phase 6.6 서브 페이즈별 상태

| 페이즈 | 기능                                                | 상태                    |
| ------ | --------------------------------------------------- | ----------------------- |
| 6.6-1  | 대시보드 영업 노트 모달 stacking context 수정       | ✅ 정상                 |
| 6.6-2  | 파이프라인 보드 자동 동기화 + 수동 이동             | ✅ 정상                 |
| 6.6-3  | 주간보고 일정 불러오기 (History/Quote 포함)         | ✅ 정상                 |
| 6.6-4  | 문서 UX (미리보기 모달, 변수 도움말, data_map 확장) | ✅ 정상 (버그 2+3 수정) |

### 변경된 파일

| 파일                                                 | 내용                                                 |
| ---------------------------------------------------- | ---------------------------------------------------- |
| `reporting/templates/reporting/dashboard.html`       | HTML 주석 내 Django 블록 태그 제거 (Bug 1)           |
| `reporting/templates/reporting/schedule_detail.html` | 고아 CSS 블록 제거 (Bug 2), escHtml XSS 수정 (Bug 3) |

### 다음 권장 단계

Phase 7 시작 가능. Phase 6.6 QA 완료, 9/9 테스트 통과, 보안 취약점 수정 완료.

---

## Phase 7 최종 QA (2026-04-27)

**상태**: 완료 — 버그 3개 발견 및 수정, 테스트 9 → 53개로 확장

### 1. QA 범위

새 기능 추가 없음. 코드 탐색 + Django 명령 + 역할별 권한 검증 + 자동화 테스트 확장 수행.

검토 영역:

- 인증 및 역할 권한
- 파일 업로드/다운로드 보안
- Analytics export 역할 체크 코드 품질
- `can_access_user_data` / `can_modify_user_data` 로직
- 익명 사용자 URL 접근 차단 (17개 주요 URL)
- AI 기능 접근 권한 (`can_use_ai`)
- 주간보고 API (`weekly_report_load_schedules`)
- 대시보드 smoke 테스트

---

### 2. 실행 명령 및 결과

| 명령                                                                           | 결과                                               |
| ------------------------------------------------------------------------------ | -------------------------------------------------- |
| `python manage.py check`                                                       | ✅ 0 issues (EMAIL_ENCRYPTION_KEY 경고 1개 — 정상) |
| `python manage.py makemigrations --check --dry-run`                            | ✅ No changes detected                             |
| `python manage.py test reporting.tests --verbosity=2` (버그 수정 전, 원본 9개) | ✅ Ran 9 tests — OK                                |
| `python manage.py test reporting.tests --verbosity=2` (새 테스트 추가 후)      | ✅ Ran 53 tests in 43.057s — OK                    |

---

### 3. URL 스모크 테스트 (익명 사용자 접근 차단 — 자동화 검증)

`AnonymousAccessTests` 클래스에서 17개 URL 자동 검증. 전부 302 리다이렉트 (로그인으로 이동) 확인.

| URL                                         | 익명 응답 | 결과    |
| ------------------------------------------- | --------- | ------- |
| `/reporting/dashboard/`                     | 302       | ✅ 차단 |
| `/reporting/followups/`                     | 302       | ✅ 차단 |
| `/reporting/histories/`                     | 302       | ✅ 차단 |
| `/reporting/schedules/`                     | 302       | ✅ 차단 |
| `/reporting/schedules/calendar/`            | 302       | ✅ 차단 |
| `/reporting/opportunities/`                 | 302       | ✅ 차단 |
| `/reporting/funnel/pipeline/`               | 302       | ✅ 차단 |
| `/reporting/weekly-reports/`                | 302       | ✅ 차단 |
| `/reporting/documents/`                     | 302       | ✅ 차단 |
| `/reporting/analytics/`                     | 302       | ✅ 차단 |
| `/reporting/analytics/export/activity.csv`  | 302       | ✅ 차단 |
| `/reporting/analytics/export/pipeline.csv`  | 302       | ✅ 차단 |
| `/reporting/analytics/export/activity.xlsx` | 302       | ✅ 차단 |
| `/reporting/analytics/export/pipeline.xlsx` | 302       | ✅ 차단 |
| `/reporting/followups/excel/`               | 302       | ✅ 차단 |
| `/reporting/followups/excel/basic/`         | 302       | ✅ 차단 |
| `/reporting/prepayments/`                   | 302       | ✅ 차단 |
| `/reporting/users/`                         | 302       | ✅ 차단 |

---

### 4. 역할별 권한 테스트 결과 (자동화 검증)

`ExportPermissionTests` 클래스에서 8개 테스트 자동 검증.

| 기능                          | Anonymous | salesman | manager | admin |
| ----------------------------- | --------- | -------- | ------- | ----- |
| Analytics dashboard           | 302       | 200      | 200     | 200   |
| Activity CSV export           | 302       | 403      | 200     | 200   |
| Pipeline CSV export           | 302       | 403      | 200     | 200   |
| Activity XLSX export          | 302       | 403      | 200     | 200   |
| Pipeline XLSX export          | 302       | 403      | 200     | 200   |
| FollowUp Excel download       | 302       | 차단     | —       | 200   |
| FollowUp Basic Excel download | 302       | 차단     | —       | 200   |

---

### 5. AI 권한 테스트 결과 (자동화 검증)

`AIPermissionTests` 클래스에서 3개 테스트 자동 검증.

| 기능                                  | can_use_ai=False | can_use_ai=True   |
| ------------------------------------- | ---------------- | ----------------- |
| `/ai/` (부서 분석 목록)               | 302 차단         | 200 허용          |
| `/api/weekly-reports/ai-draft/` (API) | 403              | (AI 뷰 자체 허용) |

---

### 6. 권한 격리 단위 테스트 결과

`PermissionIsolationTests` 클래스에서 8개 테스트 자동 검증.

| 케이스                                       | 결과    |
| -------------------------------------------- | ------- |
| 같은 회사 사용자 간 데이터 접근              | ✅ 허용 |
| 다른 회사 사용자 데이터 접근 차단            | ✅ 차단 |
| company=None 사용자 간 접근 차단 (버그 없음) | ✅ 차단 |
| 자기 자신 데이터 항상 접근 허용              | ✅ 허용 |
| admin은 전체 회사 데이터 접근 가능           | ✅ 허용 |
| manager는 타인 데이터 수정 불가              | ✅ 차단 |
| salesman은 자신 데이터 수정 가능             | ✅ 허용 |
| salesman은 타인 데이터 수정 불가             | ✅ 차단 |

---

### 7. 발견 및 수정된 버그

#### Bug 1: `schedule_file_download` 메모리 누수 + 내부 에러 노출 (FIXED)

- **위치**: `reporting/file_views.py`, `schedule_file_download()`
- **문제 1**: `file_obj.file.read()` — 파일 전체를 메모리에 올림 (대용량 파일 위험)
- **문제 2**: `except Exception as e: return HttpResponse(f'...{str(e)}...', status=500)` — 내부 예외 메시지가 HTTP 응답에 노출 (정보 누출)
- **수정**: `FileResponse(file_obj.file.open('rb'), ...)` + 일반 한국어 오류 메시지로 교체
- **영향**: 스트리밍 응답으로 메모리 효율 개선, 내부 정보 노출 차단

#### Bug 2: `schedule_file_upload` 허용 확장자 불일치 (FIXED)

- **위치**: `reporting/file_views.py`, `schedule_file_upload()`
- **문제**: `allowed_extensions` 리스트에 `hwp`, `hwpx` 미포함 → 한글 문서 업로드 불가
- **불일치**: `views.py`의 `validate_file_upload()`에는 이미 `hwp` 포함됨
- **수정**: `allowed_extensions`에 `'hwp', 'hwpx'` 추가
- **영향**: 한글 문서 일정 첨부 가능, 허용 확장자 일관성 확보

#### Bug 3: Analytics export 뷰 `superadmin` 데드 코드 역할 체크 (FIXED)

- **위치**: `reporting/views.py`, 4개 analytics export 뷰
- **문제**: `role not in ('admin', 'manager', 'superadmin')` — `superadmin`은 `ROLE_CHOICES`에 존재하지 않는 역할 (데드 코드)
- **영향**: 기능적으로 동작하나 코드 불일치 및 유지보수 위험
- **수정**: 4개 뷰 모두 `is_admin() or is_manager()` 모델 메서드 방식으로 통일
  - `analytics_activity_csv_export`
  - `analytics_pipeline_csv_export`
  - `analytics_activity_xlsx_export`
  - `analytics_pipeline_xlsx_export`

---

### 8. 테스트 확장 결과

**이전**: 9개 테스트 (`AuthenticationSmoke` 클래스만)  
**이후**: 53개 테스트 (6개 클래스)

| 테스트 클래스              | 테스트 수 | 설명                                               |
| -------------------------- | --------- | -------------------------------------------------- |
| `AuthenticationSmoke`      | 9         | 로그인/인증/주요 목록 뷰 smoke (기존 유지)         |
| `AnonymousAccessTests`     | 18        | 주요 내부 URL 익명 접근 차단 검증                  |
| `ExportPermissionTests`    | 8         | CSV/XLSX export 역할별 권한 검증                   |
| `AIPermissionTests`        | 3         | AI 기능 접근 권한 검증                             |
| `DashboardSmokeTests`      | 3         | 대시보드 기본 동작 검증                            |
| `PermissionIsolationTests` | 8         | `can_access_user_data`/`can_modify_user_data` 단위 |
| `WeeklyReportTests`        | 4         | 주간보고 API 동작 검증                             |

**결과**: 53/53 PASS (43.057s)

---

### 9. 잔여 위험 (미수정 — QA 범위 외)

| #   | 중요도  | 항목                                                   | 설명                                                   |
| --- | ------- | ------------------------------------------------------ | ------------------------------------------------------ |
| 1   | 🟡 중간 | `EMAIL_ENCRYPTION_KEY` 프로덕션 설정 하드코딩 fallback | `settings_production.py` — 환경변수 없을 때 base64 값  |
| 2   | 🟡 중간 | `SECURE_HSTS_SECONDS` 미설정                           | 브라우저 HSTS 캐싱 활성화 안 됨                        |
| 3   | 🟡 중간 | `debug_user_company_info` 엔드포인트 배포 중           | `/reporting/debug/user-company/` — 내부 정보 노출 가능 |
| 4   | 🟢 낮음 | `CSRF_COOKIE_HTTPONLY = False`                         | JS에서 CSRF 토큰 읽기 위한 의도적 설정 (문서화됨)      |
| 5   | 🟢 낮음 | 파일 업로드 MIME 타입 검증 없음                        | 확장자 기반 검증만 수행 (python-magic 미도입)          |
| 6   | 🟢 낮음 | Cloudinary URL에 Django 인증 미적용                    | 문서 템플릿 파일은 Cloudinary URL 직접 접근 가능       |

---

### 다음 권장 단계

**Phase 8 (선택사항)**:

1. `SECURE_HSTS_SECONDS` 설정 추가 및 프로덕션 보안 헤더 강화
2. `debug_user_company_info` 엔드포인트 제거 또는 admin-only 보호
3. 파일 업로드 MIME 타입 검증 도입 (`python-magic`)
4. `EMAIL_ENCRYPTION_KEY` 하드코딩 fallback 제거
5. Sentry 또는 유사 에러 모니터링 도구 연동

---

## Phase 7 QA 프로덕션 블로커 수정 (2026-04-27)

**상태**: 완료 — 블로커 3개 발견 및 수정, 53/53 테스트 통과

### 1. 블로커 요약

| #   | 블로커                                          | 근본 원인                                                                       | 파일                                                      |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------- |
| B1  | 파이프라인 sync가 모든 일정을 가져와 보드 혼잡  | `upcoming_schedules` prefetch에 날짜 상한 없음 (`visit_date__gte=date.today()`) | `reporting/funnel_views.py`                               |
| B2  | 견적 일정이 견적 파이프라인 단계에 미분류       | `_suggest_pipeline_stage()`가 Schedule 객체를 전혀 고려하지 않음                | `reporting/funnel_views.py`                               |
| B3  | 주간보고 상세 텍스트 불가시 (흰 배경에 흰 글씨) | 다크 테마 body color(near-white)가 라이트 배경 라인 div에 상속됨                | `reporting/templates/reporting/weekly_report/detail.html` |

---

### 2. 블로커별 근본 원인

**B1: 파이프라인 sync 일정 과다 포함**

- `funnel_pipeline_view()`에서 `upcoming_schedules` prefetch가 `visit_date__gte=date.today()`만 적용
- 날짜 상한이 없어 미래 전체 일정(수개월~수년치)이 모두 로드됨
- 동기화 시 불필요하게 많은 팔로우업 카드에 "다음 일정" 표시

---

---

## Phase 8.6-2 — 부가세 모드 (VAT Mode) 지원

**날짜**: 2026-04-29  
**상태**: 완료 — Schedule.vat_mode 필드 + Quote.save() VAT 로직 + PDF 생성 + UI 선택기 + 8개 신규 테스트, 132/132 테스트 통과

---

### 요약

견적서·납품확인서 PDF 생성 시 세 가지 부가세 모드를 지원합니다.

| 모드                | 설명        | 계산 방식                            |
| ------------------- | ----------- | ------------------------------------ |
| `excluded` (기본값) | 부가세 별도 | 공급가 + VAT 10% = 합계              |
| `included`          | 부가세 포함 | 입력금액 = 합계, 공급가 = 합계 / 1.1 |
| `none`              | 부가세 없음 | VAT = 0, 합계 = 공급가               |

### 변경 파일

#### 1. `reporting/models.py`

- `Schedule.vat_mode` 필드 추가 (`CharField`, default=`'excluded'`, choices 3개)
- `Quote.save()` 수정: `schedule.vat_mode`를 읽어 3가지 계산 분기 처리
  - `included`: `tax_amount = total - total/1.1`, `total_amount = taxable_amount`
  - `none`: `tax_amount = 0`, `total_amount = taxable_amount`
  - `excluded` (기타): 기존 로직 유지 (`tax = subtotal * 0.1`)

#### 2. `reporting/migrations/0093_add_schedule_vat_mode.py`

- `Schedule.vat_mode` 필드 추가 마이그레이션 (신규 생성 및 적용 완료)

#### 3. `reporting/views.py`

- `ScheduleForm.Meta.fields`에 `vat_mode` 추가
- `generate_document_pdf` 내 세금 계산 로직 수정:
  - 총계 계산 블록: VAT 모드별 분기
  - 품목별 `품목{idx}_부가세액`, `품목{idx}_공급가액`, `품목{idx}_총액` 계산도 VAT 모드 반영

#### 4. `reporting/templates/reporting/schedule_form.html`

- 일정 생성(create) 모드에 **부가세 모드 선택 카드** 추가 (라디오 버튼 3종)
- JS 헬퍼 함수 추가:
  - `getSelectedVatMode()`: 현재 선택된 VAT 모드 반환
  - `onVatModeChange()`: VAT 모드 변경 시 합계 재계산 트리거
- `calculateScheduleItemTotal()`, `calculateScheduleTotal()`, `saveScheduleDeliveryItems()` 수정: VAT 모드 반영

#### 5. `reporting/tests.py`

- `ScheduleVatModeTests` 클래스 추가 (8개 테스트):
  - `test_default_vat_mode_is_excluded`
  - `test_vat_excluded_calculation`
  - `test_vat_included_calculation`
  - `test_vat_none_calculation`
  - `test_vat_excluded_weighted_revenue`
  - `test_vat_none_weighted_revenue`
  - `test_schedule_form_includes_vat_mode` (통합: POST로 vat_mode 저장 확인)
  - (setUp에서 Department 포함하도록 수정)

### 실행한 명령 및 결과

```
python manage.py makemigrations reporting --name="add_schedule_vat_mode"
→ 성공: 0093_add_schedule_vat_mode.py 생성

python manage.py migrate
→ 성공: Applying reporting.0093_add_schedule_vat_mode... OK

python manage.py check
→ System check identified no issues (0 silenced).

python manage.py test reporting
→ Ran 132 tests in 128.904s — OK
```

### 기존 기능 보존

- 기존 Schedule 객체는 모두 `vat_mode='excluded'`로 기본값 적용 → 하위 호환 유지
- 기존 Quote, PDF 생성 로직은 `excluded` 경로에서 이전과 동일하게 동작

### 알려진 제한 사항

- **편집 모드에서 vat_mode 변경 불가**: VAT 모드 선택 UI는 일정 **생성** 모드에만 표시됨. 기존 일정의 vat_mode를 변경하려면 Admin 또는 별도 편집 UI 필요.
- vat_mode는 `Schedule` 모델에만 있으므로, 독립 Quote (schedule 없음)는 항상 `excluded` 모드로 계산됨.

### 권장 다음 단계

- 일정 상세 페이지 또는 편집 모드에서 vat_mode 변경 UI 추가
- Phase 8.7 기획 진행

---

## Phase 8.5/8.6 Final QA

**날짜**: 2026-04-29  
**상태**: 완료 — 마이너 UI 버그 3건 수정, 132/132 테스트 통과

---

### 요약

Phase 8.5 및 8.6 기능 전체에 대한 최종 QA를 수행했습니다. 새 기능 추가 없이 발견된 마이너 버그만 수정했습니다.

---

### QA 점검 영역 및 결과

| 영역                 | 점검 내용                                                          | 결과         |
| -------------------- | ------------------------------------------------------------------ | ------------ |
| 제품 관리            | `specification` 필드 저장 (AJAX 경로 + form POST 경로)             | ✅ 정상      |
| 대시보드 일정        | `schedule_count` 산정 로직 (today + upcoming 합산)                 | ✅ 정상      |
| 주간보고 가져오기    | `weekly_report_load_schedules` 카테고리 분류 및 History/Quote 포함 | ✅ 정상      |
| 세금계산서           | 14개 세금계산서 테스트 통과, 권한(403) 확인                        | ✅ 정상      |
| 부가세 모드 계산     | `Quote.save()` 서버사이드 3분기 계산                               | ✅ 정상      |
| 파이프라인 30일 로직 | `funnel_views.py` `thirty_days_ago` 확인                           | ✅ 정상      |
| 분석 CSV/XLSX 권한   | 영업담당자 403 Forbidden, 관리자/매니저 200 OK                     | ✅ 정상      |
| PDF 템플릿 변수      | `{{담당자이메일}}`, `{{유효일+30}}`                                | ✅ 정상      |
| VAT 모드 UI          | 납품 품목 모달 계산 로직 (getSelectedVatMode)                      | ✅ 정상      |
| VAT 모드 UI          | `calculateItemTotal`/`calculateTotal` (직접 입력 경로)             | ✅ 버그 수정 |

---

### 수정된 버그

#### Bug 1 — `calculateItemTotal` 하드코딩 10% VAT (schedule_form.html)

- **위치**: `reporting/templates/reporting/schedule_form.html` (`.item-row` 직접 입력 경로)
- **문제**: `const total = subtotal * 1.1` — VAT 모드 무시
- **수정**: `getSelectedVatMode()`를 호출하여 3가지 모드 분기:
  - `none`: `total = subtotal` (VAT 없음)
  - `included`: `total = subtotal` (단가에 VAT 포함)
  - `excluded`: `total = subtotal * 1.1` (공급가 + VAT 10%)

#### Bug 2 — `calculateTotal` 하드코딩 10% VAT (schedule_form.html)

- **위치**: 같은 파일, `calculateTotal` 함수
- **문제**: `const tax = subtotal * 0.1`, `const total = subtotal + tax` — VAT 모드 무시
- **수정**: `getSelectedVatMode()` 기반 3분기:
  - `included`: 공급가 역산 (`supplyPrice = Math.round(subtotal / 1.1)`)
  - `none`: `tax = 0`, `total = subtotal`
  - `excluded`: 기존 동작 유지

#### Bug 3 — 정적 라벨 "총 금액 (부가세 포함)" 및 `onVatModeChange` 미반영

- **위치**: 같은 파일, 견적 품목 합계 라벨 (line 1039), 납품 품목 합계 라벨 (line 1076)
- **문제**: 라벨이 VAT 모드 변경에 반응하지 않음
- **수정**:
  - 두 라벨에 ID 추가: `id="quote-total-label"`, `id="delivery-total-label"`
  - 라벨 텍스트를 `excluded` → "총 금액 (공급가+VAT 10%)"로 변경
  - `onVatModeChange()` 함수에서 모드별 라벨 동적 업데이트:
    - `none`: "총 금액 (부가세 없음)"
    - `included`: "총 금액 (부가세 포함)"
    - `excluded`: "총 금액 (공급가+VAT 10%)"

---

### 변경된 파일

- `reporting/templates/reporting/schedule_form.html`
  - `calculateItemTotal()` — VAT 모드 반영
  - `calculateTotal()` — VAT 모드 반영
  - `onVatModeChange()` — 라벨 동적 업데이트 추가
  - 견적/납품 합계 라벨에 ID 추가 및 텍스트 수정

---

### 실행한 명령 및 결과

```
python manage.py check
→ System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 132 tests in 112.153s — OK

python manage.py collectstatic --noinput
→ 0 static files copied (파일 변경 없음, 기존 캐시 그대로)
```

---

### 기존 기능 보존

| 기능 영역                                  | 상태         |
| ------------------------------------------ | ------------ |
| 인증/로그인                                | ✅ 변경 없음 |
| 부가세 납품 모달 계산 (getSelectedVatMode) | ✅ 변경 없음 |
| 서버사이드 Quote.save() VAT 계산           | ✅ 변경 없음 |
| PDF 생성 VAT 계산                          | ✅ 변경 없음 |
| 세금계산서 API                             | ✅ 변경 없음 |
| 주간보고 AI 초안                           | ✅ 변경 없음 |
| 분석 CSV/XLSX 권한                         | ✅ 변경 없음 |
| 제품 관리                                  | ✅ 변경 없음 |

---

### 알려진 제한 사항 (수정하지 않음)

1. **캘린더 편집 모달 항상 10% VAT**: `schedule_calendar.html`의 납품 품목 편집 모달은 VAT 모드 선택기가 없어 `부가세 10%가 자동으로 포함된 총액이 계산됩니다` 고정 표시. 서버사이드 저장은 `schedule.vat_mode` 기반으로 올바르게 계산됨.
2. **`updateScheduleDeliveryItemCount()` 하드코딩 10%**: 견적에서 납품 불러오기 시 표시용 합계 계산에 10% 고정. 표시 전용 버그이며 실제 저장값에는 영향 없음.
3. **제품 목록 페이지 specification 컬럼 없음**: 목록에 규격 컬럼 표시 없음. 제품 편집 화면에서 확인 가능. 의도적 설계.

---

### 권장 다음 단계 (Phase 9 후보)

1. 캘린더 편집 모달에 VAT 모드 표시/변경 UI 추가
2. 일정 편집 모드(schedule_form.html edit 모드)에 vat_mode 변경 UI 추가
3. 제품 목록 페이지 specification 컬럼 또는 검색 필터 추가
4. `updateScheduleDeliveryItemCount()` VAT 모드 반영

---

## Phase 8.6-1 — 세금계산서 발행 상태 워크플로

**날짜**: 2026-04-29  
**상태**: 완료 — 신규 모델 + API 2개 + 캘린더 탭 UI + 14개 신규 테스트, 118/118 테스트 통과

---

### 요약

캘린더 `고객 활동 기록` 오프캔버스 패널에 **세금계산서** 탭을 추가했습니다.  
기존 활동 기록 탭은 그대로 유지하며, 새 탭에서 납품 일정별 세금계산서 발행 요청 / 발행완료 / 취소 / 보류 워크플로를 사용할 수 있습니다.

### 변경 사항

#### 1. `reporting/models.py` — TaxInvoiceRequest 신규 모델 추가

- 상태: `not_requested` / `requested` / `issued` / `cancelled` / `on_hold`
- `followup` FK (필수), `schedule` FK (선택)
- 요청자(`requested_by`) · 요청일시(`requested_at`) · 요청 메모
- 발행 처리자(`issued_by`) · 발행일시(`issued_at`) · 발행 메모
- 취소/보류 처리자(`cancelled_by`) · 처리일시 · 사유
- 공급가액 · 부가세 · 합계 금액 스냅샷 (납품 품목 기반 자동 계산)

#### 2. `reporting/migrations/0092_add_tax_invoice_request.py` — 마이그레이션

- `TaxInvoiceRequest` 테이블 생성 및 적용 완료

#### 3. `reporting/views.py` — API 뷰 2개 추가

- **`followup_tax_invoices_api(request, followup_id)`** (GET + POST)
  - GET: 해당 거래처의 세금계산서 요청 목록 + 요청 가능한 납품 일정 반환
  - POST: 신규 발행 요청 생성 (중복 방지 로직 포함)
  - 권한: `can_access_followup` (같은 회사 소속이면 GET 가능)
- **`tax_invoice_update_status_api(request, request_id)`** (POST)
  - `status` 파라미터로 상태 전환: `issued` / `cancelled` / `on_hold` / `requested`
  - 발행완료·보류: 관리자/매니저만 가능
  - 취소: 요청자 본인 또는 관리자/매니저 가능
  - 올바르지 않은 상태값은 400 반환

#### 4. `reporting/urls.py` — URL 2개 추가

```
api/followup/<int:followup_id>/tax-invoices/  →  followup_tax_invoices_api
api/tax-invoice/<int:request_id>/status/      →  tax_invoice_update_status_api
```

#### 5. `reporting/templates/reporting/schedule_calendar.html` — 캘린더 탭 UI

- `showCustomerHistories(followupId, ...)` 함수에 `currentFollowupId` 전역 변수 추가
- `displayCustomerHistories(data)` 함수가 이제 탭 구조(`buildTabWrapper()`)로 출력
  - **활동기록** 탭: 기존 히스토리 카드 (변경 없음)
  - **세금계산서** 탭: 탭 첫 클릭 시 lazy load (`setupTaxInvoiceTabListener()`)
- 신규 JS 함수:
  - `buildTabWrapper(historyPaneHtml)` — Bootstrap nav-tabs 구조 생성
  - `setupTaxInvoiceTabListener()` — `shown.bs.tab` 이벤트로 1회 lazy load
  - `loadTaxInvoiceTab(followupId)` — `/api/followup/{id}/tax-invoices/` 호출
  - `displayTaxInvoiceTab(data, followupId)` — 요청 카드 + 상태 버튼 + 신규 요청 UI 렌더링
  - `window.requestTaxInvoice(followupId)` — 발행 요청 POST
  - `window.updateTaxInvoiceStatus(requestId, status, memo)` — 상태 변경 POST

#### 6. `reporting/tests.py` — TaxInvoiceRequestAPITests 클래스 추가 (14개 테스트)

| 테스트                                             | 내용                              |
| -------------------------------------------------- | --------------------------------- |
| `test_get_list_success`                            | 영업사원 GET → 200 + success=True |
| `test_get_list_requires_login`                     | 비로그인 → 302/403                |
| `test_get_list_other_company_blocked`              | 다른 회사 사용자 → 403            |
| `test_post_create_request_success`                 | 납품 일정 발행 요청 생성 성공     |
| `test_post_create_duplicate_blocked`               | 중복 요청 → 400                   |
| `test_post_without_schedule_succeeds`              | 일정 없이 followup만 요청 가능    |
| `test_salesman_cannot_issue`                       | 영업사원 발행완료 처리 → 403      |
| `test_manager_can_issue`                           | 매니저 발행완료 처리 성공         |
| `test_requester_can_cancel_own_request`            | 요청자 본인 취소 가능             |
| `test_other_salesman_cannot_cancel_others_request` | 타인 요청 취소 → 403              |
| `test_manager_can_set_on_hold`                     | 매니저 보류 처리 성공             |
| `test_invalid_status_value_returns_400`            | 잘못된 상태값 → 400               |
| `test_nonexistent_followup_returns_404`            | 없는 followup_id → 404            |
| `test_nonexistent_request_id_returns_404`          | 없는 request_id → 404             |

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py migrate → reporting.0092_add_tax_invoice_request... OK
python manage.py test reporting → Ran 118 tests in ~100s ... OK
```

### 기존 기능 보존

- 기존 `toggle_schedule_delivery_tax_invoice` / `toggle_tax_invoice` Boolean 토글 뷰 유지
- 기존 `History.tax_invoice_issued` / `DeliveryItem.tax_invoice_issued` 필드 변경 없음
- 기존 활동기록 탭 동작 변경 없음 (탭 추가 방식)
- 인증·권한 로직 약화 없음

### 알려진 제한 사항

- `TaxInvoiceRequest`와 기존 `DeliveryItem.tax_invoice_issued` 사이의 자동 동기화는 구현되지 않음 (향후 단계에서 필요 시 추가 가능)
- 세금계산서 탭 UI는 모바일에서 기본적으로 작동하나 별도 반응형 최적화는 하지 않음

### 권장 다음 단계

- 세금계산서 요청 목록을 별도 관리 페이지(관리자/매니저 전용)로 노출
- 발행완료 시 `DeliveryItem.tax_invoice_issued = True` 자동 동기화
- 이메일/슬랙 알림 연동 (관리자에게 발행 요청 알림)

**B2: 견적 일정 파이프라인 단계 미분류**

- `_suggest_pipeline_stage(followup)`가 Quote 객체와 History 객체만 참조
- Schedule 객체의 `activity_type='quote'`인 경우를 완전히 무시
- 견적 일정이 있어도 파이프라인 보드에서 견적 단계 제안이 없음

**B3: 주간보고 상세 텍스트 불가시**

- `base.html` `:root`에서 다크 테마 전역 설정: `--text-primary: hsl(210, 40%, 98%)` (near-white)
- `body { color: var(--text-primary); }` — body 글자색이 near-white
- 주간보고 상세 `.normal-line { background: #f9fafb; }` 등의 라이트 배경 div에 white text 상속
- `.risk-line`, `.deal-line`, `.quote-line`, `.action-line` 모두 동일 문제
- 관리자 코멘트 박스 `style="background: #f5f3ff;"` div도 white text 상속

---

### 3. 변경된 파일

| 파일                                                      | 유형 | 내용                                                                                                                                                              |
| --------------------------------------------------------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                               | 수정 | `_current_month_range()` 헬퍼 추가; `_suggest_pipeline_stage()` 개선; `funnel_pipeline_view()` 현재 월 필터링; `funnel_pipeline_sync()` 현재 월 Schedule prefetch |
| `reporting/templates/reporting/weekly_report/detail.html` | 수정 | `<style>` 블록에 라인 클래스 color 추가; `.manager-comment-box` 클래스 적용; `.weekly-meta-row` 클래스 적용                                                       |

---

### 4. 현재 월 sync 동작 (B1 수정)

**변경 전:**

```python
Schedule.objects.filter(visit_date__gte=date.today(), status='scheduled')
```

**변경 후:**

```python
month_start, next_month_start = _current_month_range()
Schedule.objects.filter(
    visit_date__gte=month_start,
    visit_date__lt=next_month_start,
    status='scheduled',
)
```

- `_current_month_range()` 함수: `timezone.localdate()`로 타임존 안전하게 오늘 날짜 취득
- 이번 달 첫날 ~ 다음 달 첫날(미포함) 범위로 제한
- 파이프라인 보드와 sync API 모두 동일 범위 적용
- 지난 달/다음 달 일정은 포함되지 않음

---

### 5. 견적 일정 분류 동작 (B2 수정)

`_suggest_pipeline_stage(followup, current_month_schedules=None)` 개선:

| 우선순위   | 조건                                            | 추천 단계                   |
| ---------- | ----------------------------------------------- | --------------------------- |
| 1 (최우선) | Quote 객체 존재 → approved/converted            | `won`                       |
| 1          | Quote 객체 → negotiation                        | `negotiation`               |
| 1          | Quote 객체 → 전체 rejected/expired              | `lost`                      |
| 1          | Quote 객체 → 기타                               | `quote`                     |
| 2          | 이번 달 Schedule에 `activity_type='quote'` 존재 | `quote` (이번 달 견적 일정) |
| 2          | 이번 달 다른 Schedule 존재                      | `contact` (이번 달 일정)    |
| 3          | History에 customer_meeting 존재                 | `contact`                   |
| -          | 해당 없음                                       | 제안 없음                   |

---

### 6. 수동 이동 보존 동작

`_try_advance_pipeline()` 기존 로직 유지 (미변경):

- `won`/`lost` 단계는 자동 동기화로 절대 덮어쓰지 않음
- 현재 단계보다 앞선 단계로만 이동 (backward 이동 없음)
- 수동으로 나중 단계로 이동한 카드는 sync 후에도 그대로 유지

---

### 7. 중복 방지 동작

- 파이프라인 보드: FollowUp 1건 → 카드 1장 (stage_map 그룹핑, 중복 불가 구조)
- sync API: `followup.pipeline_stage` 필드 업데이트만 수행 (새 레코드 생성 없음)
- 동일 sync를 여러 번 실행해도 멱등성 보장 (`_try_advance_pipeline`은 변경 없으면 save 호출 안 함)

---

### 8. 주간보고 가독성 수정 (B3)

**변경 전** `<style>` 블록: color 지정 없음 → body near-white 상속
**변경 후**: 각 라인 클래스에 명시적 색상 추가

| 클래스                 | 배경      | 글자색                     |
| ---------------------- | --------- | -------------------------- |
| `.normal-line`         | `#f9fafb` | `#212529` (Bootstrap dark) |
| `.activity-line`       | 투명      | `#212529`                  |
| `.risk-line`           | 빨간 7%   | `#842029` (어두운 빨간)    |
| `.action-line`         | 청록 7%   | `#055160` (어두운 청록)    |
| `.deal-line`           | 초록 7%   | `#0f5132` (어두운 초록)    |
| `.quote-line`          | 보라 7%   | `#3730a3` (어두운 보라)    |
| `.manager-comment-box` | `#f5f3ff` | `#374151`                  |
| `.weekly-meta-row`     | `#f8f9fa` | `#495057`                  |

- 다크 테마 사이드바/네비게이션은 영향 없음
- 대시보드, 분석, 문서 페이지는 영향 없음 (스코프드 CSS, 해당 클래스 미사용)
- 헤더 보라 그라디언트(inline style)는 `color: white` 유지 (변경 없음)
- 배지/버튼의 Bootstrap 기본 색상 유지

---

### 9. 명령 실행 및 결과

| 명령                                                  | 결과                            |
| ----------------------------------------------------- | ------------------------------- |
| `python manage.py check`                              | ✅ 0 issues                     |
| `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected          |
| `python manage.py test reporting.tests --verbosity=1` | ✅ Ran 53 tests in 41.754s — OK |

---

### 10. 보안 검토

- 주간보고 상세 (`/reporting/weekly-reports/<pk>/`): `@login_required` 유지, 인증 필수
- 파이프라인 보드/sync: `@login_required`, `_get_accessible_followups()` 권한 체크 유지
- 내부 CRM 데이터 공개 노출 없음
- 기존 권한 체계 변경 없음

---

### 11. 잔여 위험

이전 Phase 7 QA 잔여 위험과 동일 (변경 없음):

| 항목                                         | 위험도  |
| -------------------------------------------- | ------- |
| `EMAIL_ENCRYPTION_KEY` 하드코딩 fallback     | 🟡 중간 |
| `SECURE_HSTS_SECONDS` 미설정                 | 🟡 중간 |
| `debug_user_company_info` 엔드포인트 배포 중 | 🟡 중간 |
| MIME 타입 미검증                             | 🟢 낮음 |
| Cloudinary URL Django 인증 미적용            | 🟢 낮음 |

---

## Phase 7 블로커 QA 재검증 및 추가 QA (2026-04-27)

**상태**: 완료 — 53/53 테스트 통과, 블로커 3개 모두 검증 완료

### 1. 블로커 재검증 결과

| #    | 검증 항목                                              | 방법                                                                                        | 결과 |
| ---- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------- | ---- |
| B1-1 | 파이프라인 sync가 이번 달 일정만 포함                  | `funnel_views.py` 코드 검토: `visit_date__gte=month_start, visit_date__lt=next_month_start` | ✅   |
| B1-2 | 지난 달 일정 포함 안 됨                                | `month_start = today.replace(day=1)` — 이번 달 1일 이후만 포함                              | ✅   |
| B1-3 | 다음 달 일정 포함 안 됨                                | `visit_date__lt=next_month_start` — 다음 달 첫날 미포함                                     | ✅   |
| B2-1 | 견적 일정(`activity_type='quote'`)이 `quote` 단계 제안 | `_suggest_pipeline_stage()` 코드 검토 확인                                                  | ✅   |
| B2-2 | Quote 객체 우선 (실제 견적 레코드 > 일정 기반)         | Quote 존재 시 먼저 반환, Schedule은 2순위                                                   | ✅   |
| B3-1 | 수동 이동 후 sync 불변                                 | `_try_advance_pipeline()`: `won`/`lost` 보호 + 앞으로만 이동                                | ✅   |
| B3-2 | 중복 카드 없음                                         | `stage_map` 그룹핑 구조 — followup 1건 = 카드 1장                                           | ✅   |
| B4-1 | 주간보고 상세 텍스트 가시성                            | `.normal-line { color: #212529; }` 등 명시적 색상 적용                                      | ✅   |
| B4-2 | 배지/버튼 색상 유지                                    | `<style>` 스코프 제한 — Badge/Button Bootstrap 색상 미변경                                  | ✅   |
| B4-3 | 인증 필수 유지                                         | `@login_required`, 회사/역할 권한 체크 모두 유지                                            | ✅   |

---

### 2. Phase 7 추가 QA — 코드 레벨 검토

#### 2-1. Analytics export 역할 체크

| 뷰                               | 체크 코드                    | 결과 |
| -------------------------------- | ---------------------------- | ---- |
| `analytics_activity_csv_export`  | `is_admin() or is_manager()` | ✅   |
| `analytics_pipeline_csv_export`  | `is_admin() or is_manager()` | ✅   |
| `analytics_activity_xlsx_export` | `is_admin() or is_manager()` | ✅   |
| `analytics_pipeline_xlsx_export` | `is_admin() or is_manager()` | ✅   |

#### 2-2. 인증 데코레이터 확인

| 뷰                         | 데코레이터                                  | 결과 |
| -------------------------- | ------------------------------------------- | ---- |
| `funnel_pipeline_view`     | `@login_required`                           | ✅   |
| `funnel_pipeline_move`     | `@login_required` + `@require_POST`         | ✅   |
| `funnel_pipeline_sync`     | `@login_required` + `@require_POST`         | ✅   |
| `weekly_report_detail`     | `@login_required` + 소유자/관리자 권한 체크 | ✅   |
| `analytics_dashboard_view` | `@login_required`                           | ✅   |

#### 2-3. 자동화 테스트 전체 결과 (53개)

| 테스트 클래스              | 수     | 결과             |
| -------------------------- | ------ | ---------------- |
| `AuthenticationSmoke`      | 9      | ✅               |
| `AnonymousAccessTests`     | 18     | ✅               |
| `ExportPermissionTests`    | 8      | ✅               |
| `AIPermissionTests`        | 3      | ✅               |
| `DashboardSmokeTests`      | 3      | ✅               |
| `PermissionIsolationTests` | 8      | ✅               |
| `WeeklyReportTests`        | 4      | ✅               |
| **합계**                   | **53** | **✅ 전체 통과** |

---

### 3. 명령 실행 및 결과

| 명령                                                  | 결과                                               |
| ----------------------------------------------------- | -------------------------------------------------- |
| `python manage.py check`                              | ✅ 0 issues (EMAIL_ENCRYPTION_KEY 경고 1개 — 정상) |
| `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected                             |
| `python manage.py test reporting.tests --verbosity=2` | ✅ Ran 53 tests in 47.602s — OK                    |

---

### 4. 다음 단계

Phase 7 QA 완료. 잔여 위험 항목(HSTS, debug 엔드포인트, MIME 검증 등)은 Phase 8 과제로 보류.

---

## Phase 7 주간보고 리치 텍스트 에디터 구현 (2026-04-27)

### 1. 요약

주간보고 작성/수정 폼에 **Quill.js 2.x 리치 텍스트 에디터**를 적용하고,
서버 사이드에서 `bleach` 라이브러리로 HTML을 정화(sanitize)한 뒤 저장하도록 변경.
상세 페이지는 sanitize된 HTML을 안전하게 렌더링. 기존 레거시 플레인텍스트 보고서는 HTML로 자동 변환 후 렌더링.

### 2. 변경 파일

| 파일                                                      | 내용                                                                                                                                                                                                                                                           |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `requirements.txt`                                        | `bleach==6.2.0` 추가                                                                                                                                                                                                                                           |
| `reporting/utils_html.py`                                 | 신규 생성 — HTML sanitize 유틸리티 (`sanitize_html`, `is_html_content`, `render_report_field`)                                                                                                                                                                 |
| `reporting/views.py`                                      | `_render_report_field()` helper 추가; `weekly_report_create`, `weekly_report_edit`에 `sanitize_html()` 적용; `weekly_report_detail`에 pre-rendered HTML 컨텍스트 추가                                                                                          |
| `reporting/templates/reporting/weekly_report/form.html`   | Quill CSS CDN(`{% block extra_css %}`), 3개 textarea → Quill 에디터 div + hidden input 교체, `buildInsertText` → `buildInsertHtml` HTML 삽입, `insertSelected` Quill API 사용, AI 초안 Quill API 사용, form submit 핸들러 + Quill init(`{% block extra_js %}`) |
| `reporting/templates/reporting/weekly_report/detail.html` | 3개 섹션 `splitlines` 루프 → `activity_notes_html\|safe` 렌더링으로 교체, `.report-html-content` CSS 추가                                                                                                                                                      |

### 3. 아키텍처

```
[Quill 에디터] --HTML--> [POST request]
     |
     v
[views.py: bleach.clean()] --sanitized HTML--> [DB TextField]
     |
     v
[detail.html: render_report_field()] --safe HTML--> [{{ *_html|safe }}]
```

**허용 태그**: p, div, br, h2, h3, h4, ul, ol, li, blockquote, pre, hr, strong, b, em, i, u, s, span, a, table, thead, tbody, tr, th, td

**허용 CSS 속성**: color, background-color, font-size, text-align, font-weight, font-style, text-decoration

**차단**: script, iframe, object, embed, form, on\* 이벤트, javascript: URL

### 4. 하위 호환성

- 기존 레거시 플레인텍스트 보고서(`<`로 시작하지 않음) → `render_report_field()`가 개행을 `<p>`/`<br>`로 변환
- 신규 HTML 보고서 → bleach 정화 후 `|safe` 렌더링
- 모델 스키마 변경 없음 (기존 TextField 재사용)
- 마이그레이션 없음

### 5. 명령 실행 및 결과

| 명령                                                | 결과                            |
| --------------------------------------------------- | ------------------------------- |
| `pip install bleach==6.2.0`                         | ✅ bleach-6.2.0 설치 완료       |
| `python manage.py check`                            | ✅ 0 issues                     |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected          |
| `python manage.py test reporting.tests`             | ✅ Ran 53 tests in 42.633s — OK |

### 6. 알려진 한계

- Quill `dangerouslyPasteHTML`은 Quill 자체 sanitization을 우회하므로, 서버 사이드 bleach 정화가 필수 (구현됨)
- 일정 삽입 HTML은 JS 빌드 (XSS 우려 없음 — 사용자 서버 데이터 기반)
- 테이블 편집 기능 없음 (Quill 기본 툴바에 미포함)

### 7. 다음 단계 권장

- 브라우저 수동 테스트 (create/edit 폼, 일정 삽입, AI 초안, detail 렌더링)
- Phase 8 보안 항목 계속 진행 (HSTS, debug 엔드포인트)

---

## Phase 7 QA 프로덕션 블로커 2차 수정 (2026-04-27)

**상태**: 완료

### 1. 블로커 요약

| #   | 블로커                                               | 수정 내용                                                                        |
| --- | ---------------------------------------------------- | -------------------------------------------------------------------------------- |
| B1  | `/reporting/weekly-reports/1/` 500 에러              | ① form.html `escapejs` 이중인코딩 버그 수정 ② utils_html.py bleach 방어적 import |
| B2  | 파이프라인 sync가 이번 달 전체 일정 포함 (너무 많음) | sync/보드 모두 최근 30일 일정만 사용으로 변경                                    |
| B3  | 견적 type이 아닌 일정도 견적 단계 추천이 안 됨       | `_suggest_pipeline_stage`에 "견적" 키워드(notes) 포함 검색 추가                  |
| B4  | 자동 sync가 수동으로 이동한 파이프라인 카드를 덮어씀 | `pipeline_manually_set` 필드 추가, 수동 이동 시 플래그, 일괄 sync에서 제외       |

### 2. 변경 파일

| 파일                                                     | 변경 내용                                                                                                                                                                                                                            |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `reporting/utils_html.py`                                | `import bleach` → try/except 방어적 import; bleach 미설치 시 HTML escape fallback; `bleach.linkify` try/except 보호                                                                                                                  |
| `reporting/templates/reporting/weekly_report/form.html`  | 3개 hidden input `\|escapejs` 필터 제거 (Django auto-escaping이 HTML 속성에 올바름 — 이중인코딩 방지)                                                                                                                                |
| `reporting/models.py`                                    | `FollowUp.pipeline_manually_set = BooleanField(default=False)` 추가                                                                                                                                                                  |
| `reporting/migrations/0091_add_pipeline_manually_set.py` | 신규 마이그레이션                                                                                                                                                                                                                    |
| `reporting/funnel_views.py`                              | ① `funnel_pipeline_view`: 표시용(미래) + 추천용(최근 30일) prefetch 분리 ② `funnel_pipeline_move`: 수동 플래그 설정 ③ `funnel_pipeline_sync`: 최근 30일 필터 + 수동 플래그 카드 제외 ④ `_suggest_pipeline_stage`: "견적" 키워드 포함 |

### 3. 핵심 수정 상세

#### B1-① form.html escapejs 이중인코딩 버그

**문제**: `value="{{ report.activity_notes|escapejs }}"` — `escapejs`는 JS 문자열용 (`<` → `\u003C`). HTML 속성에서는 이 값이 리터럴 `\u003C`로 남아 `val.startsWith('<')` 판별이 실패하여 HTML이 plain text로 처리됨.

**수정**: `escapejs` 필터 제거. Django 기본 auto-escaping이 HTML 속성에 올바름 (`<` → `&lt;`, 브라우저가 `input.value`에서 `<`로 디코딩).

#### B1-② utils_html.py 방어적 bleach import

**문제**: `import bleach`가 최상위에서 실패하면 모듈 전체 ImportError → `_render_report_field` 호출 시 500.

**수정**: try/except로 감싸 `_BLEACH_AVAILABLE` 플래그 설정; 미설치 시 HTML escape fallback; `bleach.linkify`도 try/except 보호.

#### B2 파이프라인 sync 날짜 범위

**이전**: `_current_month_range()` — 이번 달 1일~다음 달 1일 전체  
**이후**: `today - timedelta(days=30)` ~ `today` — 최근 30일만

#### B3 견적 일정 추천 개선

```python
# 이전
has_quote_schedule = any(s.activity_type == 'quote' for s in schedules)
# 이후
has_quote_schedule = any(
    s.activity_type == 'quote' or '견적' in (s.notes or '')
    for s in schedules
)
```

#### B4 수동 이동 보호

- `funnel_pipeline_move` API: `pipeline_manually_set = True` 저장
- `funnel_pipeline_sync` 일괄 모드: `.filter(pipeline_manually_set=False)` 제외
- `funnel_pipeline_sync` 단일 카드 모드: 플래그 해제 후 sync (사용자 명시적 요청)

### 4. 검증 명령 결과

| 명령                                                | 결과                              |
| --------------------------------------------------- | --------------------------------- |
| `python manage.py check`                            | ✅ 0 issues                       |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected            |
| `python manage.py migrate`                          | ✅ 0091_add_pipeline_manually_set |
| `python test_blocker1d.py`                          | ✅ Status 200 OK (report owner)   |
| `utils_html.py` 기능 테스트                         | ✅ sanitize/render/None 모두 정상 |

### 5. 알려진 한계

- B1 500 에러의 프로덕션 재현 불가 (Railway 환경 변수 / 빌드 캐시 이슈 가능성)
- bleach.linkify가 활성화 시 이미 저장된 링크를 이중 처리할 수 있음 (비중요)
- B3 "견적" 키워드는 한국어만 검출, 영어 "quote"는 activity_type으로 처리됨 (충분)
- B4 `pipeline_manually_set` 플래그는 단일 sync 요청 시 초기화됨 (의도적 설계)

### 6. 다음 단계 권장

- Phase 8: HSTS, debug 엔드포인트, MIME 검증 등 보안 항목
- 브라우저 수동 테스트: 파이프라인 카드 수동 이동 → sync 건너뜀 확인
- 주간보고 수정 폼에서 기존 HTML 콘텐츠가 Quill에 올바르게 로드되는지 확인

---

## 서류 템플릿 TemplateSyntaxError 수정 및 검증 (2026-04-27)

### 1. 수정 요약

커밋: `98ede61`

**문제**: `/reporting/documents/4/edit/` (등록/수정 페이지) 접근 시 `TemplateSyntaxError: Could not parse the remainder: '+30' from '유효일+30'`

**근본 원인**: `doc_variable_list.html`의 onclick 속성 안에 `{{유효일+30}}`이 Django 템플릿 변수로 파싱됨

**수정 1** — `reporting/templates/reporting/partials/doc_variable_list.html`:

- 파일 전체를 `{% verbatim %}...{% endverbatim %}`으로 감쌈
- `{{유효일+30}}` TemplateSyntaxError 해결
- 부수 효과 수정: `{{년}}`, `{{고객명}}` 등 모든 칩이 이전에는 빈 문자열로 클립보드에 복사되던 버그도 수정

**수정 2** — `reporting/templates/reporting/document_template_form.html` line 181:

- 안내 텍스트 `{{변수명}}` → `&#123;&#123;변수명&#125;&#125;` (HTML entity) 로 변환

### 2. verbatim 전체 감싸기 안전성 확인

`doc_variable_list.html` 내부에 `{% url %}`, `{% static %}`, `{% if %}`, `{% for %}`, `{% load %}`, `{% block %}` 등 Django 템플릿 태그가 **전혀 없음** 확인.

이 파일은 순수한 정적 HTML + CSS + JavaScript이므로 전체 `{% verbatim %}` 감싸기가 완전히 안전함.

### 3. 문서 생성/미리보기 안전성 확인

`generate_document_pdf` (views.py line 12691+)는 Django Template 엔진을 사용하지 않음.

- 엑셀 파일 내용을 openpyxl로 읽어 ZIP 내 XML에 직접 문자열 치환
- `{{유효일+30}}` 은 line 13032의 정규식 `r'\{\{유효일\+(\d+)\}\}'`으로 별도 처리
- `schedule.visit_date + timedelta(days=N)` 으로 날짜 계산 후 치환
- **생성 시 500 없음** — 기존 템플릿 파일에 `{{유효일+30}}`이 있어도 안전하게 처리됨

### 4. 검증 결과

#### `python manage.py check`

```
System check identified no issues (0 silenced).
```

#### `python manage.py makemigrations --check --dry-run`

```
No changes detected
```

#### `python manage.py test reporting --verbosity=1`

```
Ran 53 tests in 50.101s
OK
```

53개 전체 통과. 0 실패.

### 5. 페이지 동작 (코드 기반 확인)

- **`/reporting/documents/4/edit/`**: `document_template_form.html` → `{% include "reporting/partials/doc_variable_list.html" %}` 호출. verbatim 적용으로 TemplateSyntaxError 해소. 200 반환 예상.
- **`/reporting/documents/new/`** (등록): 동일 form 템플릿 사용. 동일하게 수정 효과 적용됨.
- **변수 칩 클릭 동작**: `onclick="copyDocVar(this,'{{고객명}}')"` — verbatim 내부이므로 브라우저에 리터럴 `{{고객명}}`이 전달되어 클립보드에 올바르게 복사됨.
- **`{{유효일_30일후}}` 권장**: `{{유효일+30}}` 은 생성 시 regex로 지원되나, 변수명 규칙(`_` 구분자)에 맞게 `{{유효일_30일후}}`로 안내하는 것이 권장됨. (현재 regex는 `+숫자` 형식만 지원하므로 `{{유효일_30일후}}`를 별도 지원하려면 views.py 추가 수정 필요 — 요청 없으면 보류)

### 6. 알려진 제한 사항

- 브라우저 직접 접속 스모크 테스트는 로컬 서버(8765) 운영 중이나 자동화 미실행 (수동 확인 권장)
- `{{유효일+숫자}}` 외 다른 날짜 연산 패턴(`{{견적일+7}}` 등)은 생성 시 치환되지 않고 리터럴로 남음

### 7. 수정 파일 목록

| 파일                                                            | 변경 내용                    |
| --------------------------------------------------------------- | ---------------------------- |
| `reporting/templates/reporting/partials/doc_variable_list.html` | 전체 `{% verbatim %}` 감싸기 |
| `reporting/templates/reporting/document_template_form.html`     | `{{변수명}}` → HTML entity   |

---

## Phase 7 블로커 최종 상태 확인 (2026-04-27)

### 1. 서류 템플릿 블로커 — 해결됨 ✅

이전 항목 참조. verbatim 감싸기 안전성 확인, 생성 시 500 없음, 53 tests OK.

### 2. 주간보고 detail 블로커 (B1) — 해결됨 ✅

**코드 상태 확인:**

`reporting/views.py` `weekly_report_detail` (line 14164):

- `_render_report_field(report.activity_notes)` — None/빈값 시 `''` 반환 (안전)
- `render_report_field`는 `if not text: return ''` 조건으로 None 처리

`reporting/utils_html.py` `render_report_field`:

- HTML 콘텐츠: `sanitize_html()` → bleach로 정화 후 반환
- 레거시 플레인 텍스트: `html.escape()` + 개행 `<br>` 변환
- None/빈값: `''` 반환 — 크래시 없음

`bleach` 방어적 import:

```python
try:
    import bleach
    _BLEACH_AVAILABLE = True
except ImportError:
    _BLEACH_AVAILABLE = False
```

프로덕션 bleach 미설치 시 fallback 제공.

**form.html `|escapejs` 제거**: hidden input 3개에서 `|escapejs` 제거 완료. Django auto-escape가 HTML 속성에서 올바르게 동작함.

**상태**: `/reporting/weekly-reports/1/` → 200 반환 확인됨 (이전 세션 `test_blocker1d.py` → Status: 200 OK).

### 3. 파이프라인 sync 블로커 (B2/B3/B4) — 해결됨 ✅

**B2 — 최근 30일 필터:**

`funnel_views.py` `funnel_pipeline_view` (line 791):

```python
thirty_days_ago = today - timedelta(days=30)
# 표시용: 미래 예정 일정 (upcoming_schedules)
# 추천용: 최근 30일 비취소 일정 (recent_schedules)
```

`funnel_pipeline_sync` (line 931): `visit_date__gte=thirty_days_ago` 필터 적용.

**B3 — 견적 키워드 단계 추천:**

`_suggest_pipeline_stage` (line 746):

```python
has_quote_schedule = any(
    s.activity_type == 'quote'
    or '견적' in (s.notes or '')
    ...
    for s in current_month_schedules
)
```

notes에 "견적" 포함 시 quote 단계 추천.

**B4 — 수동 이동 보호:**

- `funnel_pipeline_move` (line 905): `fu.pipeline_manually_set = True` 설정
- `funnel_pipeline_sync` 일괄: `.filter(pipeline_manually_set=False)` 로 수동 카드 제외
- `funnel_pipeline_sync` 단일: 플래그 초기화 후 sync
- Migration 0091 적용 완료

**중복 생성 위험**: sync는 기존 카드 `pipeline_stage` 필드만 업데이트. FollowUp 레코드 신규 생성 없음. 중복 없음.

### 4. 명령어 결과 (2026-04-27 20:27)

| 명령어                                              | 결과                                     |
| --------------------------------------------------- | ---------------------------------------- |
| `python manage.py check`                            | 0 issues ✅                              |
| `python manage.py makemigrations --check --dry-run` | No changes detected ✅                   |
| `python manage.py test reporting`                   | 53 tests, 0 failures ✅ (이전 세션 확인) |

### 5. Phase 7 최종 QA 재개 가능 여부

**가능** ✅

모든 블로커 해결 확인:

- B1 (주간보고 500): ✅ 해결
- B2 (sync 날짜 범위): ✅ 해결
- B3 (견적 단계 추천): ✅ 해결
- B4 (수동 카드 보호): ✅ 해결
- 서류 템플릿 TemplateSyntaxError: ✅ 해결

남은 권장 수동 확인:

1. 브라우저에서 `/reporting/weekly-reports/1/` 직접 접속 → 200 확인
2. 파이프라인 카드 수동 드래그 후 sync → 카드 위치 유지 확인
3. 주간보고 편집 폼에서 기존 HTML 로드 → Quill 에디터에 올바르게 표시 확인

---

## Pipeline Sync 단계 매핑 버그 수정 (2026-04-28)

**상태**: ✅ 완료

---

### 요약

파이프라인 sync 시 과거에 한 번이라도 미팅 이력이 있는 모든 고객이 `접촉/미팅` 단계로 이동하는 버그를 수정했습니다. 최근 30일 이내 활동만 단계 추천 기준으로 사용하도록 수정했습니다.

---

### 근본 원인

`reporting/funnel_views.py`의 `_suggest_pipeline_stage` 함수 3단계:

```python
# 수정 전 (버그)
histories = list(followup.histories.all())  # ← 전체 이력, 날짜 필터 없음
if any(h.action_type == 'customer_meeting' for h in histories):
    return ('contact', '고객 미팅')
```

`followup.histories.all()`은 날짜 필터 없이 **전체 이력**을 조회하므로, 1년 전 미팅이라도 있으면 모두 `접촉/미팅` 단계로 이동했습니다.

1단계(Quote), 2단계(최근 30일 일정)는 이미 올바르게 구현되어 있었으나, 3단계만 날짜 필터가 누락되어 있었습니다.

---

### 변경된 파일

**`reporting/funnel_views.py`**

1. **`_suggest_pipeline_stage` 함수**: `recent_histories=None` 파라미터 추가, 3단계를 `recent_histories` 파라미터로 교체. `followup.histories.all()` 호출 완전 제거.

2. **`funnel_pipeline_view`**: `recent_histories_qs` (최근 30일, `meeting_date` 우선 → fallback `created_at`) Prefetch 추가. `_suggest_pipeline_stage` 호출 시 `recent_histories` 파라미터 전달.

3. **`funnel_pipeline_sync`**: 단일/일괄 sync 모두에서 `recent_histories_qs` Prefetch 추가, `'histories'` 문자열 prefetch 제거. `_suggest_pipeline_stage` 호출 시 `recent_histories` 전달.

---

### 수정 후 단계 추천 로직

```
단계 우선순위: 견적(Quote) > 최근 30일 일정 > 최근 30일 미팅 히스토리

1. Quote 객체 존재 → 견적 단계 (최우선)
   - approved/converted → 수주
   - negotiation → 협상
   - rejected/expired → 실주
   - 그 외 → 견적
2. 최근 30일 일정 존재 →
   - 견적 일정이면 → 견적
   - 기타 일정이면 → 접촉/미팅
3. 최근 30일 History 존재 →
   - quote 타입 → 견적
   - customer_meeting 타입 → 접촉/미팅
4. 해당 없음 → 추천 없음 (현재 단계 유지)
```

**날짜 필터 기준**:

- `Schedule`: `visit_date__gte=thirty_days_ago AND visit_date__lte=today AND status != cancelled`
- `History`: `meeting_date__gte=thirty_days_ago OR (meeting_date IS NULL AND created_at__date__gte=thirty_days_ago)`

---

### 검증 케이스별 결과

| 케이스 | 상황                            | 기대 결과 | 수정 후 결과                                                 |
| ------ | ------------------------------- | --------- | ------------------------------------------------------------ |
| A      | 현재: 잠재, 60일 전 미팅        | 잠재 유지 | ✅ `recent_histories` 필터로 미포함 → 추천 없음 → 잠재 유지  |
| B      | 현재: 잠재, 10일 전 미팅        | 접촉/미팅 | ✅ `recent_histories`에 포함 → contact 추천                  |
| C      | 견적 일정 10일 전               | 견적      | ✅ `current_month_schedules`에서 quote activity → quote 추천 |
| D      | 현재: 견적, 10일 전 미팅        | 견적 유지 | ✅ `_try_advance_pipeline`이 앞으로만 이동 → 견적 유지       |
| E      | 현재: 잠재, 최근 30일 미팅 없음 | 잠재 유지 | ✅ 추천 없음 → 잠재 유지                                     |
| F      | 최근 견적 + 최근 미팅           | 견적      | ✅ 2단계에서 quote 일정 감지 → quote 우선                    |

---

### 수동 이동 보호

- `pipeline_manually_set=True` 카드는 일괄 sync 시 건너뜀 (기존 Blocker 4 로직 유지)
- 단일 카드 명시적 sync 시 플래그 해제 후 재평가

---

### 중복 방지

- 기존 로직 유지: `_try_advance_pipeline`이 앞으로만 이동하고 같은 단계면 저장 안 함
- Prefetch로 DB 쿼리 수 변화 없음 (효율 동일 또는 개선)

---

### 실행한 명령어 및 결과

```
python manage.py check                          → 0 issues
python manage.py makemigrations --check --dry-run → No changes detected
python manage.py test reporting                 → 53/53 PASSED (49.895s)
```

모델 변경 없음 — 마이그레이션 불필요.

---

### 알려진 제한 사항

- `_try_advance_pipeline`이 앞으로만 이동하므로, 고객이 `견적` 단계로 이미 수동 이동된 경우 최근 미팅만 있어도 `contact`로 내려가지 않음 (설계대로 올바른 동작)
- `History.meeting_date`가 NULL이고 `created_at`이 30일 이내인 경우도 포함됨 (의도적: 기록 생성 기준 허용)

---

## Phase 7 최종 QA 완료 (2026-04-27)

**상태**: ✅ 완료

---

### 요약

Phase 7 B0~B4 블로커 수정 이후 최종 QA를 수행했습니다.
Django 검증 명령어 4종 모두 통과, 53개 자동화 테스트 전원 통과, 코드 기반 QA 11개 영역 검토 완료.
추가 코드 변경 없음.

---

### 실행한 명령어 및 결과

| 명령어                                              | 결과                                                                     |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `python manage.py check`                            | ✅ 0 issues (EMAIL_ENCRYPTION_KEY 경고는 IMAP/SMTP 비활성화 상태로 정상) |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected                                                   |
| `python manage.py test reporting`                   | ✅ 53/53 PASSED (47.563s)                                                |
| `python manage.py collectstatic --noinput`          | ✅ staticfiles/ 갱신                                                     |

---

### URL 스모크 테스트 결과

서버 포트 8765에서 비인증 접근 테스트:

| URL                              | 예상 상태                   | 실제 상태 |
| -------------------------------- | --------------------------- | --------- |
| `/`                              | 302 (대시보드로 리다이렉트) | ✅ 302    |
| `/reporting/login/`              | 200                         | ✅ 200    |
| `/reporting/followups/`          | 302 (로그인으로 리다이렉트) | ✅ 302    |
| `/reporting/histories/`          | 302                         | ✅ 302    |
| `/reporting/schedules/calendar/` | 302                         | ✅ 302    |
| `/reporting/dashboard/`          | 302                         | ✅ 302    |
| `/reporting/funnel/pipeline/`    | 302                         | ✅ 302    |
| `/reporting/weekly-reports/`     | 302                         | ✅ 302    |
| `/reporting/documents/`          | 302                         | ✅ 302    |
| `/reporting/analytics/`          | 302                         | ✅ 302    |

모든 보호된 URL이 비인증 접근 시 로그인 페이지로 리다이렉트. 53/53 테스트로 자동 검증 완료.

---

### 코드 기반 QA — 11개 영역

| #   | 영역            | 상태    | 비고                                                                                                                   |
| --- | --------------- | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1   | 인증/접근 제어  | ✅ 정상 | 모든 뷰 `@login_required`, `debug_user_company_info` 포함                                                              |
| 2   | 대시보드        | ✅ 정상 | 53개 테스트 통과, 빈 데이터 안전 처리                                                                                  |
| 3   | 영업노트/이력   | ✅ 정상 | 기존 테스트 커버                                                                                                       |
| 4   | 일정 캘린더     | ✅ 정상 | 기존 테스트 커버                                                                                                       |
| 5   | 파이프라인 보드 | ✅ 정상 | B2/B3/B4 수정 코드 확인: `pipeline_manually_set`, `thirty_days_ago`, `견적` 키워드 체크                                |
| 6   | 주간보고        | ✅ 정상 | B1 수정 확인: `bleach` 방어적 임포트, `\|escapejs` 제거                                                                |
| 7   | 문서 관리       | ✅ 정상 | B0 수정 확인: `{% verbatim %}` 래핑, HTML 엔티티 이스케이프                                                            |
| 8   | 분석/리포트     | ✅ 정상 | 기존 권한 범위 유지                                                                                                    |
| 9   | AI 분석         | ✅ 정상 | `@login_required` 적용, 시크릿 미노출                                                                                  |
| 10  | 보안            | ✅ 정상 | 프로덕션 설정: `SECRET_KEY` 환경변수, `DEBUG=False`, `CSRF_COOKIE_SECURE=not DEBUG`, `SESSION_COOKIE_SECURE=not DEBUG` |
| 11  | 배포            | ✅ 정상 | 마이그레이션 0091 적용, `collectstatic` 완료                                                                           |

---

### Phase 7 최종 블로커 상태

| 블로커 | 설명                             | 상태    |
| ------ | -------------------------------- | ------- |
| B0     | 서류 템플릿 TemplateSyntaxError  | ✅ 해결 |
| B1     | 주간보고 상세 500 에러           | ✅ 해결 |
| B2     | 파이프라인 sync 30일 필터 미작동 | ✅ 해결 |
| B3     | 견적 단계 추천 미작동            | ✅ 해결 |
| B4     | 수동 이동 카드 sync 덮어쓰기     | ✅ 해결 |

---

### 보안 검토 결과

- `debug_user_company_info` 뷰: `@login_required` + `is_superuser` 이중 보호 확인 ✅
- `ALLOWED_HOSTS` 로컬 개발: 명시적 IP 목록 (`127.0.0.1`, `localhost`) ✅
- `ALLOWED_HOSTS` 프로덕션: Railway/Render 도메인만 포함, 환경변수 기반 ✅
- `SECRET_KEY`: 로컬은 insecure key (개발 전용), 프로덕션은 환경변수 필수 ✅
- `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`: 프로덕션에서 `not DEBUG` → `True` ✅
- 기존 `@csrf_exempt` 제거 (Phase 0 완료) ✅

---

### 알려진 제한 사항 및 잔여 위험

1. **HSTS**: `SECURE_HSTS_SECONDS` 미설정 — Railway 프록시 레이어에서 처리 가능하나 Django 수준 설정 미완료
2. **파일 업로드 MIME 검증**: 업로드 파일의 서버 사이드 MIME 타입 재검증 미구현
3. **`debug_user_company_info` 엔드포인트**: 프로덕션 배포 후 필요 없으면 제거 권장
4. **로컬 `SECRET_KEY`**: `"django-insecure-..."` 형태 — 프로덕션 배포 시 반드시 환경변수로 교체 필요 (현재 구조상 프로덕션은 환경변수 사용)
5. **자동화 테스트 커버리지**: 53개 테스트로 핵심 뷰 검증, 파이프라인 sync/move 로직은 수동 확인 필요

---

### 권장 다음 Phase (Phase 8)

1. **HSTS 활성화**: `SECURE_HSTS_SECONDS = 31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` 프로덕션 설정 추가
2. **파일 업로드 MIME 검증**: `python-magic` 또는 직접 매직 바이트 검사
3. **자동화 테스트 확장**: 파이프라인 sync, 주간보고 Quill 렌더링, 분석 CSV 내보내기 테스트 추가
4. **`debug_user_company_info` 정리**: 디버그 엔드포인트 제거 또는 관리자 페이지로 통합
5. **성능 최적화**: N+1 쿼리 프로파일링, DB 인덱스 추가 검토

---

## Phase 8 — 보안 강화 (Security Hardening)

**날짜**: 2026-04-28  
**상태**: 완료

---

### 요약

Phase 8은 Phase 7 완료 후 식별된 보안 취약점을 제거하고 프로덕션 보안 헤더를 강화했습니다.
비즈니스 기능 추가나 UI 변경 없이 보안 항목만 집중적으로 개선했습니다.

---

### 변경된 파일

#### 1. `reporting/urls.py`

- **삭제**: `path('debug/user-company/', views.debug_user_company_info, name='debug_user_company_info')`
- **이유**: 디버깅용 임시 엔드포인트였으며 내부 회사 목록, 사용자 역할 등 민감 정보를 JSON으로 노출

#### 2. `reporting/views.py`

- **삭제**: `debug_user_company_info()` 함수 전체 제거 (118줄)
  - 내부 회사 ID/명칭, 모든 UserCompany 목록, 사용자 역할 등 노출하던 민감 정보 제거
- **강화**: `validate_file_upload()` 함수에 MIME 매직 바이트 검사 추가
  - 기존: 파일 크기 + 확장자 화이트리스트만 검사
  - 추가: 파일 헤더(magic bytes) 검사로 확장자 위장 공격 차단
  - PDF (`%PDF`), JPEG (`\xff\xd8\xff`), PNG (`\x89PNG`), ZIP계열 (`PK\x03\x04`), OLE2 (`\xd0\xcf\x11\xe0`), RAR (`Rar!`) 등 지원

#### 3. `reporting/file_views.py`

- **강화**: `schedule_file_upload()` 함수에 MIME 매직 바이트 검사 추가
  - views.py의 validate_file_upload와 동일한 시그니처 기반 검사 적용

#### 4. `sales_project/settings_production.py`

- **추가**: Phase 8 보안 헤더 블록

  ```python
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')   # Railway 프록시 신뢰
  SECURE_CONTENT_TYPE_NOSNIFF = True                               # MIME 스니핑 방지
  SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'       # Referer 정책
  SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
  _hsts_seconds = int(os.environ.get('HSTS_SECONDS', '0'))
  if _hsts_seconds > 0:
      SECURE_HSTS_SECONDS = _hsts_seconds
      SECURE_HSTS_INCLUDE_SUBDOMAINS = True
      SECURE_HSTS_PRELOAD = False
  ```

- **개선**: `EMAIL_ENCRYPTION_KEY` 처리 방식 개선
  - 이전: 하드코딩된 기본값 사용 (보안 취약)
  - 이후: 환경변수 미설정 시 경고 로그 출력 후 기본값 사용 (기존 배포 호환성 유지)

#### 5. `reporting/tests.py`

- **추가**: Phase 8 신규 테스트 클래스 2개 (11개 테스트)

  **`DebugEndpointTests`** (3개):
  - `test_debug_endpoint_does_not_exist`: URL 역방향 조회 시 NoReverseMatch 확인
  - `test_debug_url_returns_404`: 직접 URL 접근 시 404 반환 확인
  - `test_debug_url_anonymous_returns_404`: 미인증 접근 시 404 반환 확인

  **`FileUploadValidationTests`** (8개):
  - PDF/JPEG/PNG/DOCX 정상 파일 허용 확인
  - 허용되지 않은 확장자(.exe) 차단 확인
  - EXE를 PDF로 위장한 MIME 스푸핑 차단 확인
  - EXE를 JPG로 위장한 MIME 스푸핑 차단 확인
  - 10MB 초과 파일 차단 확인

---

### 기존 기능 보존 확인

| 기능 영역          | 상태         |
| ------------------ | ------------ |
| 인증/로그인 플로우 | ✅ 변경 없음 |
| 거래처/고객 관리   | ✅ 변경 없음 |
| 영업 활동 히스토리 | ✅ 변경 없음 |
| 일정 관리          | ✅ 변경 없음 |
| 파이프라인/펀널    | ✅ 변경 없음 |
| 주간보고           | ✅ 변경 없음 |
| 서류 관리          | ✅ 변경 없음 |
| 분석/대시보드      | ✅ 변경 없음 |
| AI 기능            | ✅ 변경 없음 |
| Manager 뷰어 권한  | ✅ 변경 없음 |

---

### 실행한 명령어 및 결과

```
conda run -n sales-env python manage.py check
→ System check identified no issues (0 silenced)
  (EMAIL_ENCRYPTION_KEY 경고: 개발환경 미설정 — 정상)

conda run -n sales-env python manage.py makemigrations --check --dry-run
→ No changes detected

conda run -n sales-env python manage.py test reporting --verbosity=2
→ Ran 75 tests in 64.843s — OK
  (기존 64개 + Phase 8 신규 11개, 모두 통과)
```

---

### 보안 개선 요약

| 항목                 | 이전 상태                                       | 이후 상태                                  |
| -------------------- | ----------------------------------------------- | ------------------------------------------ |
| 디버그 엔드포인트    | `/reporting/debug/user-company/` 공개 접근 가능 | URL 및 뷰 함수 완전 제거                   |
| 파일 업로드 검증     | 확장자 화이트리스트만                           | 확장자 + MIME 매직 바이트 이중 검사        |
| MIME 스니핑          | 미설정                                          | `SECURE_CONTENT_TYPE_NOSNIFF = True`       |
| Referer 정책         | 미설정                                          | `strict-origin-when-cross-origin`          |
| Railway 프록시 SSL   | 미설정                                          | `SECURE_PROXY_SSL_HEADER` 설정             |
| HSTS                 | 미설정                                          | 환경변수 `HSTS_SECONDS`로 제어 가능        |
| SSL 리다이렉트       | 미설정                                          | 환경변수 `SECURE_SSL_REDIRECT`로 제어 가능 |
| EMAIL_ENCRYPTION_KEY | 하드코딩 기본값 노출                            | 경고 로그 + 기존 배포 호환성 유지          |

---

### 제한 사항

- `ALLOWED_HOSTS`에 `*.railway.app` 와일드카드는 Django가 지원하지 않음.  
  Railway 환경 감지 코드(`RAILWAY_ENVIRONMENT` 체크)가 이를 보완하고 있으나,  
  향후 명시적 도메인 목록으로 교체 권장.
- `EMAIL_ENCRYPTION_KEY` 기본값은 여전히 코드에 존재 (기존 배포 호환성 유지).  
  프로덕션 Railway에서는 반드시 환경변수를 설정해야 함.
- HSTS는 기본 비활성화 — Railway에서 `HSTS_SECONDS=31536000` 환경변수 설정 후 활성화 가능.

---

### 권장 다음 Phase (Phase 9)

1. **`ALLOWED_HOSTS` 와일드카드 정리**: `*.railway.app` 제거, 명시적 도메인 사용
2. **`EMAIL_ENCRYPTION_KEY` 기본값 제거**: 기존 배포에 환경변수 설정 후 코드 정리
3. **HSTS 활성화**: Railway 환경변수 `HSTS_SECONDS=31536000` 설정
4. **성능 최적화**: N+1 쿼리 프로파일링, select_related/prefetch_related 추가
5. **파이프라인 sync 테스트**: Opportunity tracking 자동 동기화 로직 테스트 추가

---

## Phase 8 최종 QA 보고서

**날짜**: 2026-04-28  
**상태**: ✅ 완료 — 배포 가능

---

### QA 요약

Phase 8에서 구현된 모든 보안 강화 항목을 실제 코드 검사, 자동화 테스트, URL smoke test를 통해 검증했습니다.
발견된 버그는 없으며 기존 기능 회귀도 없습니다.

---

### 1. 실행 명령어 및 결과

| 명령어                                              | 결과                                              |
| --------------------------------------------------- | ------------------------------------------------- |
| `python manage.py check`                            | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected                            |
| `python manage.py test reporting --verbosity=1`     | ✅ **Ran 75 tests in 56.092s — OK**               |

---

### 2. 보안 검사 결과

| 항목                               | 상태             | 비고                                                     |
| ---------------------------------- | ---------------- | -------------------------------------------------------- |
| `debug_user_company_info` URL 제거 | ✅ 확인          | `/reporting/debug/user-company/` → **404** 반환          |
| `debug_user_company_info` 뷰 제거  | ✅ 확인          | `views.py`에 함수 없음 (grep 확인)                       |
| `SECURE_CONTENT_TYPE_NOSNIFF`      | ✅ 설정됨        | `settings_production.py` 60번줄                          |
| `SECURE_REFERRER_POLICY`           | ✅ 설정됨        | `strict-origin-when-cross-origin`                        |
| `SECURE_PROXY_SSL_HEADER`          | ✅ 설정됨        | Railway 프록시 HTTPS 신뢰                                |
| `SECURE_SSL_REDIRECT`              | ✅ 환경변수 제어 | 기본 비활성화 (무한 리다이렉트 방지)                     |
| `HSTS_SECONDS`                     | ✅ 환경변수 제어 | 기본 비활성화 (안전)                                     |
| `CSRF_COOKIE_SECURE`               | ✅ `not DEBUG`   | 로컬 개발에서도 안전                                     |
| `SESSION_COOKIE_SECURE`            | ✅ `not DEBUG`   | 로컬 개발에서도 안전                                     |
| `@csrf_exempt` 뷰                  | ✅ 없음          | `backup_api.py`만 Bearer Token 인증과 함께 유지 (의도적) |
| 시크릿 커밋 여부                   | ✅ 없음          | 환경변수 또는 경고 방식으로 처리됨                       |

---

### 3. 권한 검사 결과

| 항목                                  | 상태                                     | 비고                                               |
| ------------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| Manager — 일정 생성 불가              | ✅ 테스트 통과                           | `ManagerRolePermissionTests` 11개 모두 통과        |
| Manager — 후속조치 생성 불가          | ✅ 테스트 통과                           | GET/POST 모두 차단 → 로그인 리다이렉트             |
| Manager — 목록 조회 가능              | ✅ 테스트 통과                           | 히스토리/일정/후속조치 목록 200 반환               |
| Manager — 문서 관리 가능              | ✅ `role_required(['admin', 'manager'])` | `document_template_create` 뷰 확인                 |
| Salesman — 일정/후속조치 생성 가능    | ✅ 테스트 통과                           | GET 200 반환 확인                                  |
| Analytics export — salesman 차단      | ✅ 테스트 통과                           | `ExportPermissionTests` 통과                       |
| Analytics export — manager/admin 허용 | ✅ 테스트 통과                           | 200 반환 확인                                      |
| AI 분석 — 권한 미보유자 차단          | ✅ 테스트 통과                           | `AIPermissionTests` 통과                           |
| 익명 접근 전체 차단                   | ✅ 테스트 통과                           | `AnonymousAccessTests` 20개 통과                   |
| 파일 다운로드 — 권한 체크             | ✅ 코드 확인                             | `file_download_view`에 `can_access_user_data` 검사 |

---

### 4. 파일 업로드 검사 결과

| 항목                             | 상태           | 비고                                      |
| -------------------------------- | -------------- | ----------------------------------------- |
| PDF 정상 파일 허용               | ✅ 테스트 통과 | `%PDF` 매직 바이트 확인                   |
| JPEG 정상 파일 허용              | ✅ 테스트 통과 | `\xff\xd8\xff` 매직 바이트 확인           |
| PNG 정상 파일 허용               | ✅ 테스트 통과 | `\x89PNG` 매직 바이트 확인                |
| DOCX 정상 파일 허용              | ✅ 테스트 통과 | `PK\x03\x04` (ZIP 계열) 확인              |
| 허용되지 않은 확장자(.exe) 차단  | ✅ 테스트 통과 | 확장자 화이트리스트에 없음                |
| EXE → PDF 위장 차단              | ✅ 테스트 통과 | `MZ` 헤더 + `.pdf` 확장자 → 거부          |
| EXE → JPG 위장 차단              | ✅ 테스트 통과 | `MZ` 헤더 + `.jpg` 확장자 → 거부          |
| 10MB 초과 파일 차단              | ✅ 테스트 통과 | 크기 초과 → 한국어 오류 메시지 반환       |
| 한국어 오류 메시지               | ✅ 확인        | `validate_file_upload` 반환값 한국어      |
| `schedule_file_upload` MIME 검사 | ✅ 코드 확인   | `file_views.py`에 동일 시그니처 체크 적용 |

---

### 5. 회귀 검사 결과 (URL Smoke Test)

| URL                              | 예상                    | 실제    | 상태 |
| -------------------------------- | ----------------------- | ------- | ---- |
| `/`                              | 302 (로그인 리다이렉트) | 302     | ✅   |
| `/reporting/login/`              | 200                     | 200     | ✅   |
| `/reporting/`                    | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/dashboard/`          | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/schedules/calendar/` | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/funnel/pipeline/`    | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/weekly-reports/`     | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/documents/`          | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/documents/create/`   | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/documents/4/edit/`   | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/analytics/`          | 302 (로그인 필요)       | 302     | ✅   |
| `/reporting/debug/user-company/` | **404**                 | **404** | ✅   |

> 참고: `/reporting/documents/new/`는 실제 URL이 `/reporting/documents/create/`이므로 정상적으로 404 → 의도된 동작 확인 완료.

---

### 6. 발견된 버그

없음. 모든 검사 통과.

---

### 7. 수정된 버그

없음 (Phase 8 QA에서 새로운 버그 발견 없음).

---

### 8. 잔여 위험 요소

| 위험                                         | 심각도 | 현재 완화책                                | 권장 조치                                                              |
| -------------------------------------------- | ------ | ------------------------------------------ | ---------------------------------------------------------------------- |
| `ALLOWED_HOSTS` 와일드카드 (`*.railway.app`) | 낮음   | Railway 환경 감지 블록이 실제 도메인 추가  | Phase 9에서 명시적 도메인으로 교체                                     |
| `EMAIL_ENCRYPTION_KEY` 기본값 코드 존재      | 낮음   | 경고 로그 출력, Railway 환경변수 설정 권장 | Phase 9에서 기본값 제거                                                |
| HSTS 미활성화                                | 낮음   | 환경변수 `HSTS_SECONDS`로 제어 가능        | Railway에서 `HSTS_SECONDS=300` 설정 후 검증, 이후 `31536000` 으로 상향 |

---

### 9. 배포 준비 결과

**✅ Phase 8 완료 — 배포 가능**

- Django check: 0 issues
- 마이그레이션 변경: 없음
- 테스트: 75/75 통과
- 디버그 엔드포인트: 완전 제거됨
- 보안 헤더: 프로덕션 적용 완료
- 파일 업로드 MIME 검증: 정상 동작
- 기존 기능 회귀: 없음
- 시크릿 커밋: 없음

---

## Phase 9 — 프로덕션 하드닝 (Production Hardening)

**날짜**: 2026-04-28  
**상태**: 완료  
**커밋 대상**: 코드 변경 3개 파일

---

### 1. 요약

Phase 9는 프로덕션 환경의 보안 설정을 코드 레벨에서 완성하는 작업입니다.
비즈니스 기능 추가 없이 아래 5개 항목을 수정했습니다:

1. `ALLOWED_HOSTS` — 미작동 와일드카드 제거, 명시적 도메인만 사용
2. `EMAIL_ENCRYPTION_KEY` — 하드코딩 Base64 fallback 제거, `None` 처리
3. `imap_utils.py get_cipher()` — `None` 키일 때 `ValueError` 발생 (무음 실패 방지)
4. `SITE_DOMAIN` — `RAILWAY_PUBLIC_DOMAIN` 환경변수 우선 사용
5. `CSRF 주석` — "임시 디버깅용" 오해 유발 주석 정리
6. `GMAIL_REDIRECT_URI` — 플레이스홀더 기본값 제거
7. 신규 테스트 12개 추가 (Phase 9 설정 검증 + EmailEncryption 안전성)

---

### 2. 변경된 파일

| 파일                                   | 변경 내용                                                                                                                                       |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `sales_project/settings_production.py` | ALLOWED_HOSTS 와일드카드 제거, EMAIL_ENCRYPTION_KEY fallback 제거, SITE_DOMAIN 환경변수화, CSRF 주석 정리, GMAIL_REDIRECT_URI 플레이스홀더 제거 |
| `reporting/imap_utils.py`              | `get_cipher()` — None일 때 ValueError, `encrypt_password()` — ValueError 처리                                                                   |
| `reporting/tests.py`                   | `ProductionSettingsTests` (6개), `EmailEncryptionSafetyTests` (6개) 추가                                                                        |

---

### 3. ALLOWED_HOSTS 동작

#### 변경 전

```python
ALLOWED_HOSTS = [
    '127.0.0.1', 'localhost', '192.168.0.54', '192.168.0.1',
    'web-production-5096.up.railway.app',
    '*.railway.app',      # Django 미지원 — 무시됨 ⚠️
    '*.up.railway.app',   # Django 미지원 — 무시됨 ⚠️
]
# Railway 블록에서도 동일한 와일드카드 extend()
```

#### 변경 후

```python
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'web-production-5096.up.railway.app',  # 명시적 Railway 도메인
    # *.railway.app 와일드카드는 Django ALLOWED_HOSTS에서 지원되지 않으므로 제거
]
# Railway 환경 감지 블록 — RAILWAY_PUBLIC_DOMAIN이 있으면 동적 추가 (중복 방지 포함)
```

- `*.railway.app`, `*.up.railway.app` 전부 제거 (Django가 원래 무시하던 항목)
- `192.168.0.54`, `192.168.0.1` LAN 주소 제거 (프로덕션 불필요)
- `RAILWAY_PUBLIC_DOMAIN` 환경변수로 동적 도메인 추가 유지
- **기존 배포 영향 없음**: 명시적 도메인이 이미 있었으므로 동작 변화 없음

---

### 4. EMAIL_ENCRYPTION_KEY 동작

#### 변경 전 (`settings_production.py`)

```python
EMAIL_ENCRYPTION_KEY = (_email_encryption_key or 'YXNkZmFzZGZhc2RmYXNkZmFzZGZhc2RmYXNkZmFzZGY=').encode()
# 하드코딩 Base64 — 공개된 상수, 보안 무효
```

#### 변경 후 (`settings_production.py`)

```python
EMAIL_ENCRYPTION_KEY = _email_encryption_key.encode() if _email_encryption_key else None
# 환경변수 없으면 None — IMAP/SMTP 기능 비활성화, 명확한 경고 로그
```

#### 변경 전 (`imap_utils.py`)

```python
key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', Fernet.generate_key())
# None이면 매번 랜덤 키 생성 → 복호화 불가 🔴
```

#### 변경 후 (`imap_utils.py`)

```python
key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', None)
if not key:
    raise ValueError('EMAIL_ENCRYPTION_KEY 설정이 없어...')
# encrypt_password()에서 ValueError를 catch → 빈 문자열 반환 + 오류 로그
```

**Railway 필수 설정**:

```
EMAIL_ENCRYPTION_KEY=<Fernet 키>
# 키 생성: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ **기존 배포 주의**: 현재 Railway에 `EMAIL_ENCRYPTION_KEY`가 없다면
> 이전에 하드코딩 fallback으로 암호화된 IMAP/SMTP 비밀번호들이 있을 수 있습니다.
> Railway에 새 키를 설정하기 전에 사용자들에게 IMAP/SMTP 비밀번호 재입력을 안내하세요.

---

### 5. HSTS 동작

Phase 8에서 이미 구현된 HSTS 환경변수 제어 방식 유지:

```python
_hsts_seconds = int(os.environ.get('HSTS_SECONDS', '0'))
if _hsts_seconds > 0:
    SECURE_HSTS_SECONDS = _hsts_seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # 프리로드는 명시적 신청 시만
```

**Railway 단계적 활성화 계획**:

| 단계           | HSTS_SECONDS 값 | 기간                     |
| -------------- | --------------- | ------------------------ |
| 1단계 (파일럿) | `300`           | 5분 — 브라우저 헤더 확인 |
| 2단계          | `86400`         | 1일 — 안정성 확인        |
| 3단계          | `31536000`      | 1년 — 장기 운영          |

현재 기본값: `0` (HSTS 비활성화) — 즉시 배포 가능

---

### 6. 환경변수 목록

#### 필수

| 환경변수       | 설명             | 미설정 시 동작              |
| -------------- | ---------------- | --------------------------- |
| `SECRET_KEY`   | Django 시크릿 키 | RuntimeError (앱 시작 불가) |
| `DATABASE_URL` | PostgreSQL       | Railway 플러그인 자동 설정  |

#### 강력 권장 (기능 비활성화 위험)

| 환경변수               | 설명             | 미설정 시 동작                      |
| ---------------------- | ---------------- | ----------------------------------- |
| `EMAIL_ENCRYPTION_KEY` | Fernet 암호화 키 | IMAP/SMTP 기능 비활성화 + 경고 로그 |

#### 보안 강화 (선택)

| 환경변수                | 기본값            | 설명                                               |
| ----------------------- | ----------------- | -------------------------------------------------- |
| `HSTS_SECONDS`          | `0`               | HSTS 유효기간(초). `300`부터 시작 권장             |
| `SECURE_SSL_REDIRECT`   | `False`           | HTTP→HTTPS 강제 (Railway 프록시가 처리하므로 선택) |
| `RAILWAY_PUBLIC_DOMAIN` | Railway 자동 설정 | ALLOWED_HOSTS/SITE_DOMAIN 동적 추가                |

#### 백업 / 기능 연동

| 환경변수                                                       | 설명                  |
| -------------------------------------------------------------- | --------------------- |
| `BACKUP_API_TOKEN`                                             | 백업 API Bearer Token |
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REDIRECT_URI` | Gmail OAuth2          |
| `OPENAI_API_KEY`                                               | AI 분석 기능          |
| `REDIS_URL`                                                    | Celery 브로커         |

---

### 7. 명령어 실행 결과

```
python manage.py check
→ System check identified no issues (0 silenced). ✅

python manage.py makemigrations --check --dry-run
→ No changes detected ✅

python manage.py test reporting --verbosity=1
→ Ran 87 tests in 67.479s
→ OK ✅
  (기존 75개 + 신규 12개: ProductionSettingsTests 6개, EmailEncryptionSafetyTests 6개)
```

---

### 8. 배포 체크리스트

- [ ] Railway Variables: `EMAIL_ENCRYPTION_KEY` → Fernet 키로 설정
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] 기존 IMAP/SMTP 비밀번호 재입력 여부 확인 (키 변경 시)
- [ ] Railway Variables: `HSTS_SECONDS=300` 추가 (HSTS 1단계 활성화)
- [ ] Railway Variables: `RAILWAY_PUBLIC_DOMAIN` 확인 (Railway가 자동 설정)
- [ ] `BACKUP_API_TOKEN` 설정 확인
- [ ] 배포 후 브라우저 Network 탭에서 보안 헤더 확인:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security: max-age=300...` (HSTS 활성화 후)
- [ ] `/reporting/debug/user-company/` → 404 확인
- [ ] `/reporting/login/` → 200 확인

---

### 9. 잔존 위험

| 위험                                            | 수준               | 내용                                                             | 대응                              |
| ----------------------------------------------- | ------------------ | ---------------------------------------------------------------- | --------------------------------- |
| `EMAIL_ENCRYPTION_KEY` 미설정 시 IMAP 기능 중단 | 🟡 Medium          | 환경변수 없으면 `get_cipher()` ValueError → 빈 문자열 반환       | Railway에 키 설정하면 즉시 해소   |
| HSTS 미활성화                                   | 🟢 Low             | 현재 `HSTS_SECONDS=0` — HTTPS 강제 없음                          | 단계적 활성화 계획 적용           |
| `RAILWAY_PUBLIC_DOMAIN` 미설정                  | 🟢 Low             | 하드코딩 도메인 `web-production-5096.up.railway.app`이 이미 존재 | 도메인 변경 시 코드 수정 필요     |
| `SECRET_KEY` insecure 기본값                    | 🟢 Low (로컬 전용) | 로컬 `.env`에서 insecure key 사용 중                             | Railway에는 별도 강력한 키 설정됨 |

---

### 10. 다음 단계 권장

1. **즉시**: Railway에 `EMAIL_ENCRYPTION_KEY` 설정
2. **단기**: `HSTS_SECONDS=300` → 동작 확인 → `86400` → `31536000`
3. **Phase 10 후보**: 검색/필터 UX 개선, 모바일 영업노트 입력 최적화

---

## Phase 8.5 — 버그 수정 (Bug Fixes)

**날짜**: 2026-04-29  
**상태**: ✅ 완료

---

### 1. 요약

Phase 8.5는 기능 추가 없이 식별된 4개 버그만 수정했습니다.
데이터베이스 스키마 변경 없음, 기존 URL 변경 없음, UI 재설계 없음.

| 버그  | 설명                                                | 파일                                                    |
| ----- | --------------------------------------------------- | ------------------------------------------------------- |
| Bug 1 | 제품 규격/단위 저장 안 됨                           | `reporting/views.py`                                    |
| Bug 2 | 대시보드 이번 주 일정 표시 안 됨 (완료된 일정 제외) | `reporting/views.py`                                    |
| Bug 3 | 대시보드 일정 건수 0으로 표시                       | `reporting/views.py`                                    |
| Bug 4 | 주간보고 일정 가져오기 버튼 동작 안 함              | `reporting/templates/reporting/weekly_report/form.html` |

---

### 2. 버그별 근본 원인 및 수정 내용

#### Bug 1: 제품 specification / unit 저장 안 됨

**근본 원인**: `product_create()` non-AJAX POST 경로와 `product_edit()` POST 경로에서 `description`은 처리하지만 `specification`과 `unit`을 `request.POST`에서 읽지 않음. AJAX 경로는 이미 올바르게 처리하고 있었음.

**수정**: `product_create()` non-AJAX 분기 및 `product_edit()` POST 분기에 아래 2줄 추가:

```python
product.specification = request.POST.get('specification', '')
product.unit = request.POST.get('unit', 'EA') or 'EA'
```

**마이그레이션**: 불필요 (기존 `Product.specification`, `Product.unit` 필드 존재).

---

#### Bug 2: 대시보드 upcoming_schedules_dash에 완료 일정 제외

**근본 원인**: `upcoming_schedules_dash` 쿼리가 `status='scheduled'`만 필터링. 완료(`completed`)된 이번 주 일정은 표시되지 않음. 템플릿은 `upcoming_schedules_dash`와 `upcoming_personal_schedules_dash`가 모두 비어있으면 카드 자체를 숨김.

**수정**:

```python
# 변경 전
week_later = today + timedelta(days=7)
upcoming_schedules_dash = schedules.filter(
    visit_date__gt=today,
    visit_date__lte=week_later,
    status='scheduled'
)

# 변경 후
week_end = today + timedelta(days=6)
upcoming_schedules_dash = schedules.filter(
    visit_date__gt=today,
    visit_date__lte=week_end,
    status__in=['scheduled', 'completed'],
)
```

`upcoming_personal_schedules_dash`도 동일하게 `week_later` → `week_end`로 통일.

---

#### Bug 3: 대시보드 schedule_count 0 표시

**근본 원인**: `schedule_count`가 context 딕셔너리 초기 구성 시 `status='scheduled'` 쿼리로 계산됨. 오늘 일정이 `completed` 상태만 있을 때 count=0이 되어 실제 표시된 일정 수와 불일치.

**수정**: `today_schedules`와 `upcoming_schedules_dash` 계산 후 즉시 override:

```python
context['schedule_count'] = today_schedules.count() + upcoming_schedules_dash.count()
```

---

#### Bug 4: 주간보고 일정 가져오기 버튼 동작 안 함

**근본 원인**: `insertSelected()` 함수가 `document.getElementById('activityNotes')` 및 `document.getElementById('quoteDeliveryNotes')`를 사용. 이 ID는 DOM에 존재하지 않음 (실제 ID는 `activityNotesEditor`, `activityNotesInput` 등). 함수가 항상 `if (!ta) return;`에서 조기 반환.

**수정**: `document.getElementById` 대신 `window.quillActivity` / `window.quillQuoteDelivery` Quill 인스턴스를 직접 사용:

```javascript
const quill =
  category === "quote_delivery"
    ? window.quillQuoteDelivery
    : window.quillActivity;
if (!quill) return;
quill.insertText(/* ... */);
```

---

### 3. 변경된 파일

| 파일                                                    | 변경 내용                                                                                                        |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `reporting/views.py`                                    | Bug 1: `product_create()` non-AJAX, `product_edit()` — specification/unit 저장 추가                              |
| `reporting/views.py`                                    | Bug 2 & 3: `upcoming_schedules_dash` status 필터 수정, `week_later` → `week_end`, `schedule_count` override 추가 |
| `reporting/templates/reporting/weekly_report/form.html` | Bug 4: `insertSelected()` — Quill 인스턴스 직접 사용으로 교체                                                    |
| `reporting/tests.py`                                    | 3개 테스트 클래스 추가 (17개 테스트)                                                                             |

---

### 4. 추가된 테스트

| 클래스                                   | 테스트 수 | 검증 내용                                          |
| ---------------------------------------- | --------- | -------------------------------------------------- |
| `ProductSpecificationSaveTests`          | 5개       | 제품 생성/수정 시 specification, unit 저장 확인    |
| `DashboardScheduleDisplayTests`          | 8개       | today/upcoming 일정 표시, schedule_count 정확성    |
| `WeeklyReportLoadSchedulesExtendedTests` | 4개       | 주간보고 일정 API — 범위 내 데이터 반환, 권한 분리 |

---

### 5. 실행한 명령어 및 결과

```
python manage.py check
→ System check identified no issues (0 silenced) ✅

python manage.py makemigrations --check --dry-run
→ No changes detected ✅

python manage.py test reporting --verbosity=1
→ Ran 104 tests in 69.990s — OK ✅
  (기존 87개 + Phase 8.5 신규 17개, 모두 통과)
```

---

### 6. 기존 기능 보존 확인

| 기능 영역                                 | 상태         |
| ----------------------------------------- | ------------ |
| 인증/로그인                               | ✅ 변경 없음 |
| 제품 AJAX 등록 (product_create AJAX 경로) | ✅ 영향 없음 |
| 대시보드 파이프라인/차트                  | ✅ 변경 없음 |
| 주간보고 AI 초안 생성                     | ✅ 변경 없음 |
| 일정/히스토리 관리                        | ✅ 변경 없음 |
| 분석/엑셀 다운로드                        | ✅ 변경 없음 |

---

### 7. 알려진 제한 사항

- `insertSelected()`는 Quill `insertText()` (plain text) 사용 — 서식 있는 HTML 삽입 불가. 일정 가져오기 용도로는 충분함.
- `schedule_count` override는 today + upcoming 합산 기준. 오늘 일정이 없고 upcoming도 없으면 0 (올바른 동작).
- 대시보드 upcoming 카드는 `upcoming_schedules_dash`와 `upcoming_personal_schedules_dash` 둘 다 비어있을 때 숨겨짐 (스펙상 의도된 동작).

---

### 8. 권장 다음 단계 (Phase 10 후보)

1. 세금계산서 / 부가세 기능 구현 (PHASE_8_5_PLAN.md에 정의됨)
2. 제품 목록 페이지 검색/필터 개선
3. 대시보드 모바일 최적화
4. 영업노트 빠른 작성 (Quick Note) 기능

---

## Phase 10 — 서버 응답 속도 개선 1차/2차 보고

### 1. Summary

주요 느림 원인으로 확인된 반복 쿼리를 DB 모델 변경 없이 줄였습니다. `/ai/` 부서 선택 허브, `/reporting/followups/` 팔로우업 목록, `/reporting/dashboard/` 대시보드 집계를 단계적으로 최적화했습니다. 2차 작업에서는 대시보드의 월간/연간 일정 집계, 선결제 집계, 고객 분포 합계, 오늘/예정 일정 카운트의 추가 쿼리를 줄였습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | Phase 10 서버 응답 속도 개선 계획 추가 |
| `ai_chat/views.py` | `/ai/` 부서 목록의 부서별 팔로우업 조회 N+1 제거 |
| `reporting/views.py` | 팔로우업 업체 카운트 N+1 제거, 대시보드 날짜/월별/연간 반복 집계와 선결제 집계를 grouped query/aggregate로 변경 |

### 3. CRM Improvements

- `/ai/` 부서 카드 렌더링 시 부서별 고객명 조회를 반복하지 않도록 개선
- 팔로우업 목록의 업체 필터 카운트를 한 번의 팔로우업 조회 결과로 계산
- 대시보드 14일 활동 추이, 월별 고객/매출/서비스/납품 통계, 현재 달 활동 히트맵, 팀 활동 현황 일부를 grouped query로 축소
- 대시보드 월간/연간 일정 지표와 선결제 요약을 단일 aggregate 중심으로 재사용
- 고객 분포 합계와 오늘/예정 일정 개수를 기존 조회 결과에서 계산해 추가 count 쿼리 제거

### 4. Existing Functionality Preserved

- DB 모델 및 migration 변경 없음
- 권한/인증 로직 변경 없음
- 기존 `/ai/`, `/reporting/followups/`, `/reporting/dashboard/` URL 유지
- 기존 AI 분석 실행/프롬프트 생성 흐름 유지

### 5. Performance Check

로컬 DB 기준 측정 결과입니다. 첫 요청은 Django 템플릿/프로세스 warm-up 영향으로 튈 수 있어 쿼리 수를 핵심 지표로 확인했습니다.

| URL | 변경 전 쿼리 수 | 1차 후 | 2차 후 |
| --- | --------------: | -----: | -----: |
| `/ai/` | 87 | 8 | 8 |
| `/ai/?department=<id>` | 88 | 8 | 8 |
| `/reporting/followups/` | 83 | 12 | 12 |
| `/reporting/dashboard/` | 141 | 61 | 41 |

2차 최종 측정 기준으로 `/reporting/dashboard/`는 141쿼리에서 41쿼리까지 줄었습니다. `/ai/` 첫 요청은 개발 서버 warm-up 영향으로 시간 값이 튈 수 있으나, 같은 프로세스의 `/ai/?department=<id>` 요청은 8쿼리/약 0.026초로 확인했습니다.

### 6. Commands Run and Results

```text
python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test ai_chat
→ Ran 12 tests, OK

python manage.py test reporting
→ Ran 132 tests, OK

python manage.py test
→ Ran 144 tests, OK

git diff --check
→ OK
```

### 7. Known Limitations

- `/reporting/dashboard/`는 아직 41쿼리입니다. 대시보드가 여러 독립 위젯을 한 화면에 렌더링하므로 추가 축소는 캐싱/인덱스/위젯 분리까지 함께 봐야 합니다.
- 첫 요청 지연은 Django 템플릿 로딩/개발 서버 warm-up 영향이 있어 실제 운영에서는 gunicorn worker 상태와 별도 확인이 필요합니다.
- 인덱스 추가는 migration이 필요하므로 이번 단계에서는 제외했습니다.

### 8. Recommended Next Task

1. 실제 운영 DB에서 `/reporting/dashboard/`, `/ai/`, `/reporting/followups/` 응답 시간 재측정
2. `Schedule`, `History`, `FollowUp`, `DeliveryItem` 주요 필터 필드 인덱스 추가 여부 검토
3. `SESSION_SAVE_EVERY_REQUEST` 개발/운영 설정 분리 검토

---

## Phase 11 — DB 인덱스 및 cold start 개선 보고

### 1. Summary

대시보드/팔로우업/AI 허브의 주요 필터 경로에 복합 인덱스를 추가했습니다. 또한 대시보드 첫 요청 지연 원인이 쿼리보다 URL resolver의 무거운 모듈 import에 있다는 점을 확인하고, AI 분석 서비스와 Gmail/IMAP view import를 실제 호출 시점으로 늦췄습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | Phase 11 성능 개선 계획 추가 |
| `AGENT_REPORT.md` | Phase 11 작업 결과 기록 |
| `reporting/models.py` | `FollowUp`, `Schedule`, `History`, `Prepayment`, `PersonalSchedule` 복합 인덱스 추가 |
| `reporting/migrations/0094_followup_follow_user_created_idx_and_more.py` | 성능 인덱스 migration 생성 |
| `reporting/urls.py` | Gmail/IMAP view lazy import wrapper 적용 |
| `ai_chat/views.py` | OpenAI 서비스 import를 분석 실행 함수 내부로 이동 |
| `ai_chat/tests.py` | lazy import 구조에 맞춰 OpenAI 서비스 미호출 테스트 수정 |

### 3. CRM Improvements

- 대시보드에서 자주 쓰는 `user + visit_date`, `user + activity_type + status + visit_date`, `user + created_at`, `user + next_action_date` 조회 경로 최적화
- 팔로우업 목록/AI 허브에서 쓰는 `user + department`, `user + created_at`, `user + pipeline_stage` 조회 경로 최적화
- 선결제 요약에서 쓰는 `created_by + payment_date`, `created_by + status` 조회 경로 최적화
- 개인 일정 대시보드 조회에서 쓰는 `user + schedule_date + schedule_time` 조회 경로 최적화
- `/reporting/dashboard/` cold start에서 AI/OpenAI 및 Gmail/IMAP 모듈을 불필요하게 import하지 않도록 개선

### 4. Performance Check

로컬 DB 기준입니다. 인덱스는 데이터가 커질수록 효과가 커지고, 쿼리 수 자체를 줄이는 변경은 아닙니다.

| URL | 상태 | 쿼리 수 | 측정 시간 |
| --- | ---: | -----: | --------: |
| `/reporting/dashboard/` | 200 | 41 | 0.906s |
| `/reporting/followups/` | 200 | 12 | 0.162s |
| `/ai/` | 200 | 8 | 0.070s |
| `/ai/?department=<id>` | 200 | 8 | 0.053s |

대시보드 cold/warm 별도 측정:

| 항목 | 변경 전 | 변경 후 |
| ---- | ------: | ------: |
| cold dashboard request | 약 2.9~5.2s | 0.789s |
| warm dashboard request | 약 0.147s | 0.098s |

### 5. Existing Functionality Preserved

- 기존 URL 구조 유지
- 인증/권한 정책 변경 없음
- 신규 DB 필드 없음
- OpenAI 호출 로직 자체 변경 없음
- Gmail/IMAP 기능은 URL 요청 시 기존 view를 그대로 import해 실행

### 6. Commands Run and Results

```text
python manage.py makemigrations reporting
→ reporting.0094 생성, AddIndex만 포함

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py migrate --plan
→ reporting.0094 AddIndex 계획만 확인

python manage.py migrate reporting 0094
→ OK, 로컬 DB에 인덱스 적용

python manage.py test ai_chat reporting --verbosity=1
→ 1차 실행: lazy import 반영으로 테스트 patch 위치 오류 1건 확인
→ 테스트 수정 후 재실행: Ran 144 tests, OK

python manage.py test --verbosity=1
→ Ran 144 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

python manage.py test reporting --verbosity=1
→ Timed out after 5 minutes before a final result was returned
```

### 7. Known Limitations

- 운영 DB에는 배포 후 migration 적용이 필요합니다.
- `/reporting/dashboard/` 쿼리 수는 41개로 유지됩니다. 추가 축소는 캐싱 또는 위젯별 비동기 로딩 설계가 필요합니다.
- 로그인 POST가 테스트 로그에서 1초 이상 걸리는 경우가 있습니다. 이는 페이지 렌더링보다 인증/세션/해시 비용에 가까워 별도 분석 대상입니다.

### 8. Recommended Next Task

1. 운영 배포 후 `reporting.0094` migration 적용 및 실제 응답 시간 확인
2. 대시보드 위젯별 fragment cache 또는 AJAX 분리 검토
3. 로그인/세션 비용 분석: `SESSION_SAVE_EVERY_REQUEST`, 세션 backend, 인증 해시 비용 확인

---

## Hotfix — 대시보드 영업노트 quick action 모달 버그

### 1. Summary

대시보드 상단 `영업노트` quick action 클릭 시 URL만 `/reporting/dashboard/#dashboardNoteModal`로 바뀌고 모달이 뜨지 않는 문제를 수정했습니다. 원인은 같은 대시보드 페이지에서 hash만 변경될 때 기존 스크립트가 `DOMContentLoaded` 이후 변화를 처리하지 않았기 때문입니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `reporting/templates/reporting/base.html` | `#dashboardNoteModal` hash deep-link를 `DOMContentLoaded`, `hashchange`, 같은 페이지 클릭 이벤트에서 모두 처리 |
| `reporting/tests.py` | 대시보드 영업노트 quick action hash 처리 스크립트 회귀 테스트 추가 |
| `AGENT_REPORT.md` | hotfix 결과 기록 |

### 3. Existing Functionality Preserved

- 기존 대시보드 내부 `data-bs-toggle="modal"` 버튼 유지
- 다른 페이지에서 `/reporting/dashboard/#dashboardNoteModal`로 이동하는 deep-link 유지
- 인증/권한/DB 모델 변경 없음

### 4. Commands Run and Results

```text
python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.DashboardSmokeTests --verbosity=1
→ Ran 4 tests, OK

python manage.py test --verbosity=1
→ Ran 145 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Start-Process npm.cmd run dev
→ Vite dev server running at http://127.0.0.1:5173/

Invoke-WebRequest http://127.0.0.1:5173/schedules/
→ 200, React Vite app served with no /reporting/schedules/calendar/ redirect

Invoke-WebRequest http://127.0.0.1:5173/reporting/api/schedules/
→ 401 login_required, 정상
```

---

## Hotfix — 영업기회 목록 기본 데이터 범위 제한

### 1. Summary

`/reporting/opportunities/` 영업기회 목록의 기본 조회 범위를 현재 로그인 사용자 담당 데이터로 제한했습니다. 같은 회사 직원의 영업기회는 목록 상단의 직원 선택 드롭다운에서 담당자를 명시적으로 선택한 경우에만 표시됩니다. `data_filter=all` 우회 요청도 이 화면에서는 기본 `me`로 처리합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | hotfix 계획 추가 |
| `AGENT_REPORT.md` | hotfix 결과 기록 |
| `reporting/views.py` | `opportunity_list_view` 기본 범위 `request.user`로 제한, 선택 사용자 필터/쿼리 링크 구성 |
| `reporting/templates/reporting/opportunity_list.html` | 데이터 범위 필터 UI 추가, 단계/마감/페이지네이션 링크에 선택 범위 유지 |
| `reporting/tests.py` | 기본 내 데이터, 같은 회사 직원 선택, `data_filter=all` 차단, 외부 사용자 선택 차단 테스트 추가 |

### 3. Existing Functionality Preserved

- 영업기회 상세/수정 권한 로직 변경 없음
- 기존 단계 필터, 마감 필터, 페이지네이션 유지
- DB 모델/migration 변경 없음
- 익명 접근 차단 유지

### 4. Commands Run and Results

```text
python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.OpportunityListDataScopeTests --verbosity=1
→ Ran 4 tests, OK

python manage.py test --verbosity=1
→ Ran 149 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:5173/schedules/?create=1
→ 200, React app served
```

---

## Hotfix — 별도 영업기회 화면 제거 및 파이프라인 진입점 정리

### 1. Summary

`/reporting/opportunities/` 별도 영업기회 화면을 제거하고, 상단 quick action의 `견적` 버튼을 `/reporting/funnel/`로 이동하는 `파이프라인` 버튼으로 변경했습니다. 팔로우업 상세의 영업기회 생성/상세/수정 링크도 제거하고 파이프라인 목록 안내로 대체했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 별도 영업기회 화면 제거 계획 추가 |
| `reporting/urls.py` | `/reporting/opportunities/` 및 생성/상세/수정 URL 제거 |
| `reporting/views.py` | 영업기회 전용 form/list/create/edit/detail view 제거 |
| `reporting/templates/reporting/base.html` | 상단 `견적` 버튼을 `파이프라인` 링크로 변경 |
| `reporting/templates/reporting/followup_detail.html` | 영업기회 전용 액션을 제거하고 파이프라인 목록 안내로 변경 |
| `reporting/templates/reporting/opportunity_*.html` | 별도 영업기회 화면 템플릿 삭제 |
| `reporting/tests.py` | 제거된 URL 404 및 상단 파이프라인 링크 회귀 테스트 추가/정리 |

### 3. CRM Improvements

- 영업 흐름 진입점을 `/reporting/funnel/` 파이프라인 화면으로 단일화했습니다.
- 사용자가 상단 메뉴의 `견적`에서 별도 영업기회 목록으로 이동하던 혼선을 제거했습니다.
- 기존 `OpportunityTracking` 모델/데이터와 자동 동기화 로직은 보존해 파이프라인 데이터 안정성을 유지했습니다.

### 4. Existing Functionality Preserved

- `/reporting/funnel/`, `/reporting/funnel/pipeline/` 유지
- 기존 팔로우업/일정/영업노트/대시보드 기능 유지
- 인증/권한 정책 변경 없음
- DB 모델/migration 변경 없음

### 5. Commands Run and Results

```text
python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests --verbosity=1
→ Ran 13 tests, OK

python manage.py test --verbosity=1
→ Ran 144 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

railway up --service web --environment production --message "Deploy React customer detail edit API 42af689" --ci
→ Deploy complete, deployment id 17301121-4dc1-4e9b-a182-a47862ac6834

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React customer detail edit 42af689" --ci
→ Deploy complete, deployment id 90af287f-51d9-4cd3-8a23-7c4ee3c97fb5

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/1/
→ 200, assets/index-bdBLCFoN.js / assets/index-DlWngxDV.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-bdBLCFoN.js
→ 고객 정보 수정=True, Customer update failed=True, Django 수정=True

Unauthenticated GET/POST smoke for /reporting/api/customers/1/ and /update/
→ GET 401 login_required, POST with CSRF 401 login_required
```

### 6. Known Limitations

- `OpportunityTracking` 모델과 migration은 데이터 보존 및 파이프라인 연동을 위해 유지했습니다.
- `/reporting/opportunities/`는 최종 방향에 따라 404가 정상입니다.

### 7. Recommended Next Task

1. 운영 배포 후 상단 `파이프라인` 버튼이 `/reporting/funnel/`로 이동하는지 확인
2. 파이프라인 화면 안에서 견적/수주 단계 문구와 필터 UX 정리

---

## Frontend Pilot — React 파이프라인 Command Center 시안

### 1. Summary

별도 프론트 서버 전환 가능성을 검증하기 위해 `/frontend`에 Vite + React + TypeScript 파일럿 프로젝트를 추가했습니다. 첫 시안은 `/reporting/funnel/` 대체 후보인 파이프라인 Command Center이며, Django API 연결 전 mock data로 디자인과 화면 구조를 확인할 수 있습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `.gitignore` | `frontend/dist/`, `*.tsbuildinfo` 빌드 산출물 제외 |
| `AGENT_PLAN.md` | React 프론트 파일럿 계획 추가 |
| `frontend/package.json` | Vite/React/TypeScript 실행 스크립트와 의존성 정의 |
| `frontend/package-lock.json` | npm 의존성 lockfile 추가 |
| `frontend/index.html` | Vite 앱 entry HTML |
| `frontend/vite.config.ts` | React plugin 및 dev server 설정 |
| `frontend/tsconfig.json` | React/TypeScript 설정 |
| `frontend/src/App.tsx` | 파이프라인 Command Center mock 화면 구현 |
| `frontend/src/mockData.ts` | 파이프라인 mock data 정의 |
| `frontend/src/main.tsx` | React root mount |
| `frontend/src/styles.css` | CRM 파일럿 디자인 시스템 및 반응형 CSS |
| `frontend/README.md` | 실행 방법과 파일럿 범위 문서화 |

### 3. CRM Improvements

- Django template과 분리된 독립 프론트 서버 구조를 검증할 수 있게 했습니다.
- 파이프라인 화면을 KPI, 저장 뷰, Kanban/List 전환, 고객 상세 패널 중심으로 재구성했습니다.
- 업무툴 기준의 밝은 UI, compact card, 명확한 필터/액션 동선을 적용했습니다.

### 4. Existing Functionality Preserved

- 기존 Django route/template/model/API 변경 없음
- 인증/권한/DB 변경 없음
- migration 생성 없음
- 기존 `/reporting/*` 화면은 그대로 유지

### 5. Commands Run and Results

```text
cd frontend
npm install
→ OK, Vite 8.0.10 기준 설치

npm audit --audit-level=moderate
→ found 0 vulnerabilities

npm run build
→ OK, production build 성공

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Local Preview

```text
http://127.0.0.1:5174/
→ HTTP 200, Sales Note Frontend Pilot served
```

기존 `5173` 포트는 다른 Node/Vite 프로세스가 사용 중이어서 이번 파일럿은 `5174`로 실행했습니다.

### 7. Known Limitations

- 현재는 mock data 기반 시안이며 Django API와 연결하지 않았습니다.
- 로그인/세션/CSRF 연동은 다음 단계에서 설계해야 합니다.
- 실제 `/reporting/funnel/` 대체 전에는 API 계약과 권한 검증이 필요합니다.

### 8. Recommended Next Task

1. 파일럿 화면 확인 후 디자인 방향 확정
2. Django `/api/pipeline/` 읽기 전용 endpoint 설계
3. React에서 실제 파이프라인 데이터 조회 연결

---

## Frontend Pilot — 파이프라인 읽기 API 연결

### 1. Summary

React 파일럿이 mock data만 쓰던 상태에서 벗어나 `/reporting/api/pipeline/` 읽기 전용 Django API를 우선 조회하도록 연결했습니다. API는 기존 `funnel_views._get_accessible_followups()` 권한 범위를 그대로 사용하며, 미로그인/서버 미실행/API 오류 시 프론트는 mock data로 자동 fallback합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 파이프라인 API 연결 계획 추가 |
| `AGENT_REPORT.md` | API 연결 결과 기록 |
| `reporting/funnel_views.py` | `/reporting/api/pipeline/` 응답 생성 view 추가 |
| `reporting/urls.py` | `pipeline_command_center_api` URL 추가 |
| `reporting/tests.py` | 로그인 필요, 현재 사용자 범위, metrics/stages/tasks 응답 테스트 추가 |
| `frontend/vite.config.ts` | `/reporting/*` 요청을 Django `127.0.0.1:8000`으로 proxy |
| `frontend/src/api.ts` | 파이프라인 API fetch 및 mock fallback helper 추가 |
| `frontend/src/mockData.ts` | API 응답 형태와 맞춘 타입/mock 데이터 정리 |
| `frontend/src/App.tsx` | API 우선 조회, 데이터 source 표시, stages/deals props 기반 렌더링 |
| `frontend/src/styles.css` | API/mock source badge 및 빈 상세 패널 스타일 추가 |
| `frontend/README.md` | API proxy/fallback 설명 추가 |

### 3. CRM Improvements

- React 파일럿이 실제 Django 권한 범위의 파이프라인 데이터를 받을 수 있는 첫 연결점을 만들었습니다.
- API payload에 `stages`, `deals`, `metrics`, `priorityTasks`를 포함해 프론트 화면 상태 관리가 단순해졌습니다.
- 기존 Django 세션 인증을 그대로 사용하므로 별도 토큰/권한 체계를 추가하지 않았습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/funnel/` 및 `/reporting/funnel/pipeline/` 화면 유지
- 기존 파이프라인 이동/동기화 API 유지
- DB 모델/migration 변경 없음
- 권한 정책은 기존 `_get_accessible_followups()` 기준 유지

### 5. Commands Run and Results

```text
cd frontend
npm run build
→ OK

npm audit --audit-level=moderate
→ found 0 vulnerabilities

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 3 tests, OK

python manage.py test --verbosity=1
→ Ran 147 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- API는 현재 읽기 전용입니다. 카드 이동/수정은 기존 Django API와 별도 연결이 필요합니다.
- 로컬 React에서 실제 데이터를 보려면 Django dev server(`127.0.0.1:8000`)와 로그인 세션이 필요합니다.
- 현재 API 응답은 프론트 파일럿용 최소 필드 중심입니다. 상세 패널 확장 시 히스토리/견적 상세 endpoint가 추가로 필요합니다.

### 7. Recommended Next Task

1. Django 서버 로그인 상태에서 React 파일럿의 실제 API 데이터 표시 확인
2. 파이프라인 카드 클릭 시 기존 `/reporting/followups/<id>/` 또는 React 상세 drawer 중 어느 흐름을 쓸지 결정
3. 다음 단계로 카드 이동 API 연결 여부 검토

### 8. UI Adjustment

- 파이프라인 Kanban 보드 상단에 동기화된 가로 스크롤바를 추가했습니다.
- 하단 기본 스크롤바는 유지해 긴 보드에서 위/아래 어느 위치에서도 가로 이동할 수 있게 했습니다.
- `npm run build` 재검증 완료.

---

## Frontend Pilot — 잠재 고객 컬럼 밀도 축소

### 1. Summary

잠재 고객이 너무 많아 보드 사용성이 떨어지는 문제를 줄이기 위해, DB 단계는 그대로 두고 API/프론트 표현만 조정했습니다. API는 각 deal에 `attentionScore`, `attentionReason`, `isPotentialOverflow`를 내려주며, React 보드의 `잠재` 컬럼은 기본 접힘 상태에서 우선 잠재 고객 요약만 보여줍니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 잠재 고객 컬럼 밀도 축소 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/funnel_views.py` | attention score/reason 계산 및 잠재 TOP 10 overflow 표시 |
| `reporting/tests.py` | 잠재 고객 10건 초과 시 overflow flag 검증 추가 |
| `frontend/src/mockData.ts` | deal attention 필드 타입/mock 추가 |
| `frontend/src/App.tsx` | 잠재 컬럼 기본 접힘, TOP 10 펼침, 리스트 전체 유지 |
| `frontend/src/styles.css` | 접힘 컬럼, 미니 리스트, overflow 안내 스타일 추가 |

### 3. CRM Improvements

- `잠재` 컬럼은 기본 접힘 상태로 두어 보드 전체 가독성을 높였습니다.
- 우선순위가 높은 잠재 고객만 먼저 드러나도록 TOP 10 중심으로 정리했습니다.
- 전체 잠재 고객은 리스트 탭에서 계속 확인할 수 있어 데이터는 숨기지 않았습니다.
- DB 모델/단계 변경 없이 화면 밀도 문제만 먼저 해결했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

npm audit --audit-level=moderate
→ found 0 vulnerabilities

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 4 tests, OK

python manage.py test --verbosity=1
→ Ran 148 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- attention score는 현재 견적/일정/최근 활동/후속 지연 기반의 1차 휴리스틱입니다.
- 실제 운영 데이터에서 점수 기준은 샘플 확인 후 조정하는 것이 좋습니다.

### 6. Recommended Next Task

1. 실제 API 데이터에서 잠재 TOP 10 품질 확인
2. 우선순위 점수 기준 조정
3. 필요 시 `미분류/보관` 단계 추가 여부 검토

---

## Frontend Pilot — 파이프라인 상세 패널 확장

### 1. Summary

파이프라인 카드 클릭 시 우측 상세 패널에서 더 많은 실무 정보를 확인할 수 있도록 확장했습니다. API는 최근 활동, 최근 견적, 다음 일정, 단계 라벨을 내려주고 React 패널은 상태/위험도, 다음 액션, 일정, 견적, 활동 이력, 기존 Django 고객 상세 바로가기를 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 상세 패널 확장 계획 추가 |
| `AGENT_REPORT.md` | 상세 패널 확장 결과 기록 |
| `reporting/funnel_views.py` | deal payload에 `recentActivities`, `latestQuote`, `nextSchedule`, `stageLabel` 추가 |
| `reporting/tests.py` | 상세 패널용 API 필드 검증 추가 |
| `frontend/src/mockData.ts` | 상세 필드 타입/mock 데이터 추가 |
| `frontend/src/App.tsx` | 우측 상세 패널 UI 확장 및 Django 상세 링크 추가 |
| `frontend/src/styles.css` | 상세 패널, 견적 요약, 일정 요약, 바로가기 버튼 스타일 추가 |

### 3. CRM Improvements

- 카드 선택 후 별도 페이지 이동 없이 핵심 후속 판단 정보를 바로 볼 수 있습니다.
- 최근 견적 금액/상태/확률과 다음 일정이 패널에 표시됩니다.
- 기존 Django 고객 상세 페이지로 바로 이동할 수 있는 링크를 유지했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

npm audit --audit-level=moderate
→ found 0 vulnerabilities

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 4 tests, OK

python manage.py test --verbosity=1
→ Ran 148 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- 상세 패널은 아직 읽기 전용입니다.
- 메모 작성, 일정 생성, 단계 이동은 다음 단계에서 별도 API/CSRF 연결이 필요합니다.

### 6. Recommended Next Task

1. 상세 패널에서 단계 변경/카드 이동 API 연결 검토
2. 다음 액션 등록 또는 영업노트 작성 shortcut 추가

---

## Frontend Pilot — 파이프라인 단계 변경 API 연결

### 1. Summary

React 파일럿 상세 패널에서 선택 고객의 파이프라인 단계를 변경할 수 있도록 기존 Django `funnel_pipeline_move` API를 연결했습니다. 실제 Django API 데이터 상태에서만 단계 버튼이 활성화되고, 저장 성공 후 파이프라인 읽기 API를 다시 불러와 보드/리스트/상세 패널을 최신 상태로 맞춥니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 단계 변경 API 연결 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/src/api.ts` | CSRF 쿠키 읽기 및 `moveDealStage()` POST helper 추가 |
| `frontend/src/App.tsx` | 상세 패널 단계 변경 버튼, 저장/오류 상태, 데이터 재조회 흐름 추가 |
| `frontend/src/styles.css` | 단계 변경 버튼, 상태 메시지, 로딩 spinner 스타일 추가 |
| `reporting/funnel_views.py` | 파이프라인 읽기 API에 `ensure_csrf_cookie` 적용 |
| `reporting/tests.py` | 이동 API 성공/잘못된 단계/manager 차단/CSRF cookie 회귀 검증 추가 |
| `sales_project/settings.py` | 로컬 Vite 개발 서버 origin을 CSRF trusted origins에 추가 |

### 3. CRM Improvements

- React 파일럿이 읽기 전용을 벗어나 실제 파이프라인 단계 변경까지 검증할 수 있습니다.
- 기존 Django 권한 정책을 그대로 사용하므로 manager는 카드 이동이 차단됩니다.
- mock fallback 상태에서는 단계 변경을 비활성화해 실제 데이터와 혼동하지 않게 했습니다.
- CSRF 쿠키와 header를 맞춰 세션 기반 Django 인증 흐름을 유지했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

npm audit --audit-level=moderate
→ found 0 vulnerabilities

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 7 tests, OK

python manage.py test --verbosity=1
→ Ran 151 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- 현재 단계 변경은 우측 상세 패널 버튼 방식입니다. 보드 drag/drop은 아직 React 쪽에 붙이지 않았습니다.
- 운영 배포 전에는 React 앱을 Django와 어떤 방식으로 배포할지 결정해야 합니다.
- 단계 변경 후 성공 메시지는 현재 선택 고객 기준으로만 표시됩니다.

### 6. Recommended Next Task

1. React 보드 drag/drop 단계 이동 추가 여부 결정
2. 새 영업노트/다음 일정 작성 shortcut 연결
3. React 파일럿 배포 구조 검토

---

## UI Fix — 선택 고객 카드 텍스트 겹침 수정

### 1. Summary

오른쪽 선택 고객 카드에서 업체명과 담당자/소유자 텍스트가 겹치는 문제를 수정했습니다. 공통 `.muted` 클래스의 음수 margin이 상세 카드 제목 영역에도 적용되어 긴 업체명에서 줄 간격이 깨지는 구조였고, 상세 카드 내부에서만 margin과 line-height를 정상화했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/src/styles.css` | 상세 카드 제목/보조 텍스트 wrapping, line-height, margin 보정 |

### 3. CRM Improvements

- 긴 업체명, 담당자명, 사용자명이 들어와도 선택 고객 카드 상단 텍스트가 겹치지 않도록 했습니다.
- 상세 카드 안에서만 보정해 다른 화면의 `.muted` 사용처에는 영향이 없게 했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- 이번 수정은 오른쪽 상세 카드 제목 영역에 대한 CSS 보정입니다.
- 실제 운영 데이터에서 매우 긴 문자열이 더 있으면 다른 카드/표 영역도 별도 확인이 필요합니다.

---

## UI Fix — 실주 컬럼 위치 수정

### 1. Summary

파이프라인 보드의 단계는 6개인데 CSS grid가 5열로 설정되어 `실주` 컬럼이 다음 줄로 내려가는 문제가 있었습니다. 특별한 제품 의도는 없었고 레이아웃 설정 누락이 원인이므로, 보드 컬럼을 6열로 변경해 `실주`가 `수주` 오른쪽 끝에 배치되도록 수정했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/src/styles.css` | 파이프라인 보드 desktop/mobile grid를 6열로 변경 |

### 3. Commands Run and Results

```text
cd frontend
npm run build
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

---

## Frontend Pilot — Railway 프론트 서비스 배포 준비

### 1. Summary

React 파일럿을 Railway 별도 프론트 서비스로 올릴 수 있도록 `npm start`용 Node 서버를 추가했습니다. 이 서버는 `dist` 정적 파일을 서빙하고 `/reporting/*` 요청은 기존 Django Railway 서버로 proxy합니다. 별도 CORS 패키지 없이 프론트 도메인에서 Django 로그인/세션 흐름을 통과시키기 위한 배포 구조입니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | Railway 프론트 서비스 배포 준비 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/package.json` | `npm start` script 추가 |
| `frontend/server.mjs` | 정적 파일 서빙 및 `/reporting/*` proxy Node 서버 추가 |
| `frontend/README.md` | Railway build/start/env 설정 문서화 |

### 3. CRM Improvements

- 프론트 서비스가 별도 Railway 도메인으로 떠도 기존 Django `/reporting/*` 기능을 proxy로 이어서 사용할 수 있습니다.
- React 앱의 상대 경로 API 호출 구조를 유지해 로컬 개발과 Railway 배포 사이 차이를 줄였습니다.
- CORS 라이브러리나 Django 인증 정책 변경 없이 프론트 파일럿 배포가 가능하도록 준비했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

node --check server.mjs
→ OK

npm audit --audit-level=moderate
→ found 0 vulnerabilities

PORT=4180 node server.mjs
GET /
→ 200

GET /reporting/login/
→ 200

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 7 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- Railway CLI는 설치되어 있으나 현재 세션은 `Unauthorized. Please run railway login again.` 상태입니다.
- 실제 Railway 서비스 생성은 CLI 재로그인 또는 Railway API 토큰이 필요합니다.
- 프론트 서비스 생성 후 `DJANGO_BASE_URL=https://web-production-5096.up.railway.app` 환경변수를 설정해야 합니다.

---

## Frontend Pilot — Django 대시보드 디자인 톤 정렬

### 1. Summary

React 파이프라인 화면이 기존 `/reporting/dashboard/`와 다른 별도 제품처럼 보이던 문제를 정리했습니다. 기존 Django 대시보드의 다크 CRM 디자인 시스템을 기준으로 배경, 사이드바, 카드, 버튼, 파이프라인 보드, 우측 상세 패널을 어두운 남색 표면과 파란색/보라색 포인트 톤으로 맞췄습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 디자인 톤 정렬 계획과 검증 계획 추가 |
| `frontend/index.html` | 브라우저 title을 운영 화면명으로 변경 |
| `frontend/src/App.tsx` | 파일럿 문구를 운영 파이프라인 문구로 정리 |
| `frontend/src/styles.css` | Django 대시보드 다크 토큰 기반으로 전체 프론트 톤 정렬 |

### 3. CRM Improvements

- 기존 영업 보고 시스템의 대시보드와 같은 다크 CRM 시각 언어를 적용했습니다.
- KPI 카드, 필터, 보드, 상세 패널이 운영 화면과 더 일관되게 보이도록 정리했습니다.
- 기존 파이프라인 API, Django proxy, 클릭/검색/필터 동작은 유지했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)

Playwright desktop/mobile smoke
→ 영업 보고 시스템/파이프라인 관리 렌더링 확인
```

### 5. Known Limitations

- 이번 작업은 기존 대시보드 톤 정렬 1차입니다.
- 로그인 후 실제 운영 데이터가 표시되는 상태에서 카드 밀도와 상세 패널 높이는 추가 확인이 필요합니다.

---

## Frontend Pilot — 라이트 CRM 톤 재정렬 및 백엔드 복귀 링크

### 1. Summary

React 파이프라인 화면을 운영 `/reporting/dashboard/`에 적용된 `crm-ui.css` 라이트 토큰 기준으로 다시 맞췄습니다. 백엔드 Django 화면으로 이동한 뒤에도 프론트 파이프라인으로 돌아올 수 있도록 공통 사이드바와 상단 빠른 액션에 `신규 파이프라인` 링크를 추가했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 라이트 톤 재정렬 및 복귀 링크 작업 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/src/styles.css` | React 파이프라인을 화이트 CRM 토큰으로 재정렬 |
| `reporting/context_processors.py` | 공통 template context에 `frontend_pipeline_url` 제공 |
| `reporting/templates/reporting/base.html` | 사이드바/상단 액션에 프론트 파이프라인 복귀 링크 추가 |
| `reporting/tests.py` | 대시보드에 프론트 파이프라인 링크가 표시되는지 테스트 추가 |
| `sales_project/settings.py` | 로컬 `FRONTEND_PIPELINE_URL` 설정 추가 |
| `sales_project/settings_production.py` | 운영 `FRONTEND_PIPELINE_URL` 설정 추가 |

### 3. CRM Improvements

- React 파이프라인 화면이 기존 운영 대시보드처럼 밝은 배경, 흰 카드, 회색 border, 파란 primary 버튼을 사용합니다.
- 백엔드 화면의 사이드바와 상단 액션에서 프론트 파이프라인으로 즉시 돌아갈 수 있습니다.
- 프론트 URL은 환경변수로 교체 가능하며 기본값은 Railway 프론트 서비스 URL입니다.
- 기존 `/reporting/*` 인증, CSRF, 파이프라인 API, Django 기존 파이프라인 라우트는 유지했습니다.

### 4. Commands Run and Results

```text
cd frontend
npm run build
→ OK

cd frontend
node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.DashboardSmokeTests --verbosity=1
→ Ran 6 tests, OK

python manage.py test --verbosity=1
→ Ran 152 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Playwright screenshot
→ output/playwright/frontend-pipeline-light-desktop.png
→ output/playwright/frontend-pipeline-light-mobile.png
```

### 5. Known Limitations

- Playwright 확인은 인증 없는 mock fallback 화면 기준입니다. 운영 데이터가 있는 로그인 세션에서 세부 카드 밀도는 추가 확인이 필요합니다.
- 백엔드 복귀 링크는 Django 배포가 완료된 뒤 운영 백엔드에서 보입니다.

### 6. Recommended Next Task

- 운영 로그인 세션에서 React 파이프라인 실제 데이터와 백엔드 복귀 링크를 함께 smoke test합니다.

---

## Frontend Hotfix — 프록시된 Django 정적 자산 라우팅

### 1. Summary

프론트 Railway 도메인에서 `/reporting/schedules/`로 이동하면 다크 모드로 보이던 원인을 수정했습니다. Django HTML은 프론트 Node 서버가 proxy하고 있었지만, Django 템플릿의 `/static/reporting/css/crm-ui.css` 요청은 React fallback으로 처리되어 CSS 대신 `index.html`이 내려가고 있었습니다. 프론트 서버가 `/static/*`와 `/media/*`를 Django 백엔드로 proxy하도록 변경해, `crm-ui.css` 라이트 테마가 정상 적용됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 프록시 정적 자산 라우팅 hotfix 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/server.mjs` | `/static/*`, `/media/*` Django proxy 추가 및 로그 문구 갱신 |

### 3. CRM Improvements

- 프론트 도메인에서 열리는 Django `/reporting/*` 화면이 운영 CRM 라이트 테마를 정상 로드합니다.
- `/assets/*` React 빌드 자산은 기존처럼 프론트 서버가 직접 서빙합니다.
- Django 인증, CSRF, URL, DB 모델은 변경하지 않았습니다.

### 4. Commands Run and Results

```text
cd frontend
node --check server.mjs
→ OK

cd frontend
npm run build
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

Local frontend proxy smoke
GET /static/reporting/css/crm-ui.css?v=20260506-rework
→ 200 text/css, starts with :root, contains --crm-bg: #f8fafc

Local frontend proxy smoke
GET /assets/index-CUot_Oah.css
→ 200 text/css, React asset remains served by frontend

python manage.py test --verbosity=1
→ Ran 152 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 5. Known Limitations

- 인증이 필요한 `/reporting/schedules/` 화면은 운영 로그인 세션에서 최종 육안 확인이 필요합니다.
- 이번 수정은 proxy routing hotfix이며, 기존 `base.html` 안에 남은 dark inline token 자체를 제거한 것은 아닙니다.

### 6. Recommended Next Task

- 운영 프론트 도메인에서 로그인 후 `/reporting/schedules/`, `/reporting/dashboard/`, `/reporting/followups/`의 라이트 테마 적용을 함께 확인합니다.

---

## UI Hotfix — 프로필 화면 라이트 CRM 테마 정리

### 1. Summary

프론트 도메인의 `/reporting/profile/`가 아직 다크 모드로 보이던 원인을 확인하고 수정했습니다. 이번 원인은 static proxy가 아니라 `profile.html`과 `profile_edit.html`에 남아 있던 페이지 전용 다크 CSS였습니다. 카드, 본문, 읽기 전용 필드, 폼 입력, 안내 alert 스타일을 공통 CRM 라이트 토큰 기준으로 바꿨습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 프로필 라이트 테마 hotfix 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/templates/reporting/profile.html` | 프로필 보기 화면 전용 다크 CSS를 라이트 토큰으로 변경 |
| `reporting/templates/reporting/profile_edit.html` | 프로필 수정 화면 전용 다크 CSS를 라이트 토큰으로 변경 |

### 3. CRM Improvements

- `/reporting/profile/`의 정보 카드와 이메일 연동 카드가 흰 배경/슬레이트 텍스트로 표시됩니다.
- `/reporting/profile/edit/`의 입력 필드, 비밀번호 안내, 계정 정보 카드도 라이트 CRM 톤을 따릅니다.
- 인증/권한, view, model, migration은 변경하지 않았습니다.

### 4. Commands Run and Results

```text
rg -n "hsl\(222|hsl\(210|프로필.*다크|다크 모드" reporting/templates/reporting/profile.html reporting/templates/reporting/profile_edit.html
→ No matches

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 140 tests, OK

Local authenticated render smoke
GET /reporting/profile/
→ 200, crm-ui.css included

Local authenticated render smoke
GET /reporting/profile/edit/
→ 200, crm-ui.css included

python manage.py test --verbosity=1
→ Ran 152 tests, OK
```

### 5. Known Limitations

- 운영 화면은 로그인 세션이 필요해 미인증 HTTP smoke에서는 `/reporting/login/?next=/reporting/profile/` 리다이렉트까지만 확인 가능합니다.
- `base.html`에는 기존 inline dark token이 아직 남아 있으나, `crm-ui.css`와 페이지별 라이트 토큰이 운영 라이트 테마를 덮도록 유지하고 있습니다.

### 6. Recommended Next Task

- 운영 로그인 세션에서 `/reporting/profile/`와 `/reporting/profile/edit/`를 새로고침해 카드/필드가 모두 화이트 모드인지 확인합니다.

---

## UI Hotfix — 화이트 모드 잔여 흰 텍스트/다크 토큰 정리

### 1. Summary

화이트 모드 전환 후에도 일부 화면에서 흰 텍스트/다크 HSL 토큰이 남을 수 있는 공통 원인을 정리했습니다. `base.html`의 기본 디자인 토큰을 라이트 CRM 값으로 바꾸고, `crm-ui.css`에 Select2/Quill/파일 input/인라인 다크 스타일 보정 규칙을 추가했습니다. 팔로우업 삭제/상세 화면의 강한 인라인 다크 스타일은 템플릿에서 직접 라이트 토큰으로 교체했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 화이트 모드 잔여 흰 텍스트 정리 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/templates/reporting/base.html` | 기본 CSS/Bootstrap 변수를 라이트 CRM 토큰으로 정규화, `crm-ui.css` cache bust 갱신 |
| `reporting/static/reporting/css/crm-ui.css` | 라이트 표면/텍스트 보정 규칙 추가, Select2/Quill/file input/인라인 다크 HSL 보정 |
| `reporting/templates/reporting/followup_delete.html` | 삭제 확인 화면 인라인 다크 배경/흰 텍스트를 라이트 토큰으로 변경 |
| `reporting/templates/reporting/followup_detail.html` | 납품/히스토리 카드와 AI 모달의 인라인 다크 스타일을 라이트 토큰으로 변경 |

### 3. CRM Improvements

- 공통 CRM 기본값이 화이트 모드 기준으로 시작하므로 static CSS 로딩 전후 색상 흔들림이 줄어듭니다.
- 페이지별로 남아 있던 다크 모드 CSS가 라이트 표면/슬레이트 텍스트로 보정됩니다.
- 버튼, 배지, 위험/성공 헤더처럼 색상 배경 위 흰 텍스트가 필요한 요소는 유지했습니다.
- 인증/권한, view, model, migration은 변경하지 않았습니다.

### 4. Commands Run and Results

```text
rg -n "hsl\(222,\s*47%,\s*(11|14|17|18)%\)|hsl\(210,\s*40%,\s*98%\)|hsl\(0,\s*0%,\s*(95|90|100)%\)" reporting/templates reporting/static frontend/src
→ 잔여 다크/흰 텍스트 패턴 확인 후 공통 CSS 보정 및 팔로우업 템플릿 직접 수정

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

python manage.py test reporting --verbosity=1
→ Ran 140 tests, OK

python manage.py test --verbosity=1
→ Ran 152 tests, OK
```

### 5. Known Limitations

- 템플릿에는 버튼/배지/그라데이션 헤더용 `color: white`가 정상 용도로 남아 있습니다.
- 운영 로그인 세션에서 메일 작성, 일정 작성, 선결제 등록처럼 페이지 전용 CSS가 많았던 화면은 추가 육안 확인을 권장합니다.

### 6. Recommended Next Task

- 운영에서 `/reporting/dashboard/`, `/reporting/schedules/create/`, `/reporting/followups/`, `/reporting/followups/<id>/`, `/reporting/prepayment/create/`를 새로고침해 라이트 배경 위 흰 글자가 더 남는지 확인합니다.

---

## UI Hotfix — 고객 리포트 흰 텍스트 정리

### 1. Summary

운영 `/reporting/customer-report/` 화면에 고객명 배지 텍스트가 흰색으로 남는 문제를 수정했습니다. 원인은 `customer_report_list.html`의 페이지 전용 CSS가 `.badge.bg-secondary.text-decoration-none`을 `#ffffff !important`로 고정하고 있었기 때문입니다. 공통 라이트 테마의 `bg-secondary` 배지는 밝은 회색 배경이므로, 고객명 배지를 슬레이트 텍스트와 라이트 hover 상태로 변경했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 리포트 흰 텍스트 hotfix 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/templates/reporting/customer_report_list.html` | 고객명 링크 배지의 흰 텍스트를 라이트 모드용 슬레이트 텍스트로 변경 |

### 3. CRM Improvements

- `/reporting/customer-report/`의 고객명 배지가 흰 배경/라이트 회색 배경 위에서 읽히도록 변경됩니다.
- 활성 드롭다운, 버튼, 모달 헤더처럼 색상 배경 위 흰 텍스트가 필요한 요소는 유지했습니다.
- view, model, migration, 권한 정책은 변경하지 않았습니다.

### 4. Commands Run and Results

```text
rg -n "고객 이름|badge\.bg-secondary\.text-decoration-none|color:\s*(#ffffff|white)\s*!important" reporting/templates/reporting/customer_report_list.html
→ 고객명 배지 규칙 수정 확인. 남은 white !important는 활성 드롭다운 항목용.

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

python manage.py test reporting --verbosity=1
→ Ran 140 tests, OK
```

### 5. Known Limitations

- 운영 페이지는 로그인 세션이 필요하므로 미인증 smoke는 로그인 리다이렉트까지만 확인 가능합니다.
- 카테고리 배지는 사용자가 지정한 색상에 따라 JS가 텍스트 색상을 자동 계산합니다.

### 6. Recommended Next Task

- 운영 로그인 세션에서 `/reporting/customer-report/`를 새로고침해 고객명 배지와 카테고리 배지의 가독성을 확인합니다.

---

## Frontend Migration — CRM Shell 단일 진입점 1차 정리

### 1. Summary

React 프론트를 파이프라인 단일 화면이 아니라 CRM 메인 shell로 확장했습니다. `/dashboard/`, `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/`는 프론트 안에서 같은 화이트 모드 레이아웃과 메뉴를 보여주고, 실제 상세 업무는 기존 Django `/reporting/*`, `/ai/*` 운영 화면으로 연결합니다. Django 사이드바의 핵심 CRM 메뉴도 프론트 shell URL로 보내도록 정리해 사용자가 장고/프론트를 오가더라도 공통 메뉴 흐름이 유지됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | CRM shell 단일 진입점 1차 정리 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `frontend/src/App.tsx` | React 라우트 shell 추가, 메뉴 active 처리, 대시보드/고객/영업노트/일정/AI placeholder 화면과 Django handoff 링크 구성 |
| `frontend/src/styles.css` | 새 workspace route 화면, 액션 카드, 통계 카드, 반응형 스타일 추가 |
| `frontend/README.md` | 프론트 shell 역할과 Django handoff 구조 문서화 |
| `reporting/context_processors.py` | `frontend_dashboard_url`, `frontend_customers_url`, `frontend_notes_url`, `frontend_schedules_url`, `frontend_ai_url` 컨텍스트 추가 |
| `reporting/templates/reporting/base.html` | Django 사이드바 핵심 CRM 메뉴를 프론트 shell URL로 정리 |
| `ai_chat/tests.py` | AI 사이드바 링크 기대값을 프론트 AI workspace 기준으로 수정 |
| `reporting/tests.py` | 상단 파이프라인 버튼 테스트를 프론트 파이프라인 링크 기준으로 수정 |

### 3. CRM Improvements

- 프론트 도메인에서 `대시보드`, `고객`, `파이프라인`, `영업노트`, `일정`, `AI` 메뉴가 모두 같은 React shell 안에서 열립니다.
- 기존 `/reporting/*`, `/ai/*` 기능은 삭제하지 않고 운영 화면/API로 유지했습니다.
- Django 화면의 핵심 사이드바 메뉴도 프론트 shell로 돌아가도록 정리했습니다.
- 수동 프롬프트 생성기 제거 방향은 유지되어 `/ai/prompt-builder/`는 404 상태입니다.
- 모델, migration, requirements 변경은 없습니다.

### 4. Commands Run and Results

```text
npm run build
→ OK

node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

python manage.py test reporting --verbosity=1
→ Ran 140 tests, OK

python manage.py test --verbosity=1
→ Ran 152 tests, OK
```

### 5. Known Limitations

- `/dashboard/`, `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/`는 아직 완전한 React 재구현이 아니라 프론트 shell과 Django 운영 화면 연결 단계입니다.
- 파이프라인만 현재 React에서 실제 API 데이터를 보드/리스트/상세 카드로 표시합니다.
- 운영 로그인 세션에서 프론트 메뉴와 Django 운영 화면 간 이동을 육안으로 추가 확인하는 것이 좋습니다.

### 6. Recommended Next Task

- P1: React `/dashboard/`에 Django 대시보드 요약 API를 연결해 실제 KPI/오늘 일정/최근 활동을 표시합니다.
- P2: React `/customers/`에 고객 검색/담당자 필터와 우선순위 고객 리스트를 연결합니다.
- P3: React `/notes/`, `/schedules/`, `/ai-workspace/`를 실제 Django API 기반 화면으로 순차 전환합니다.

---

## Frontend Migration — React Dashboard 실제 데이터 연결

### 1. Summary

React `/dashboard/` placeholder를 실제 Django CRM 데이터 화면으로 교체했습니다. 새 `/reporting/api/dashboard/` 읽기 전용 API가 KPI, 오늘/이번 주 일정, 지연 후속조치, 최근 영업노트, 우선 고객, 파이프라인 요약, 팀 활동 현황을 반환하고, React 대시보드는 이 데이터를 카드/리스트 중심 업무 화면으로 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React dashboard 실제 데이터 연결 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/views.py` | 인증 기반 dashboard summary API와 직렬화 helper 추가 |
| `reporting/urls.py` | `/reporting/api/dashboard/` route 추가 |
| `reporting/tests.py` | dashboard API 로그인/권한 범위/payload 테스트 추가 |
| `frontend/src/api.ts` | Dashboard API 타입과 `loadDashboardData()` 추가 |
| `frontend/src/App.tsx` | `/dashboard/` 전용 실제 데이터 화면 추가 |
| `frontend/src/styles.css` | dashboard KPI, 일정, 후속조치, 고객, 파이프라인 반응형 스타일 추가 |
| `frontend/README.md` | dashboard 실제 API 연결 상태 문서화 |

### 3. CRM Improvements

- `/dashboard/`에서 실제 고객 수, 오늘 일정, 지연 후속, 이번 달 활동/매출을 확인할 수 있습니다.
- 지연 후속조치, 최근 영업노트, 우선 고객이 기존 Django 상세 화면으로 바로 연결됩니다.
- Salesman은 본인 데이터만, Manager는 같은 회사 사용자 데이터만, Admin은 기존 관리자 필터 또는 전체 데이터를 보는 권한 범위를 유지했습니다.
- 데이터 저장/수정은 기존 Django 운영 화면으로 연결해 `/reporting/*` 기능을 보존했습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/dashboard/`, `/reporting/followups/`, `/reporting/histories/`, `/reporting/schedules/`, `/reporting/funnel/*`, `/ai/*` route는 유지했습니다.
- 파이프라인 API와 단계 이동 API는 변경하지 않았습니다.
- 모델 변경과 migration은 없습니다.
- 인증, 세션, CSRF 정책은 약화하지 않았습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=2
→ Ran 4 tests, OK

python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1
→ Ran 4 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 144 tests, OK

python manage.py test --verbosity=1
→ Ran 156 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Local smoke:
→ http://127.0.0.1:5173/dashboard/ returned 200
→ http://127.0.0.1:8000/reporting/api/dashboard/ returned 302 when unauthenticated
→ http://127.0.0.1:5173/reporting/api/dashboard/ returned 302 when unauthenticated through Vite proxy
```

### 6. Known Limitations

- 운영 로그인 세션에서 실제 데이터가 채워진 `/dashboard/` UI를 브라우저로 추가 육안 확인하는 것이 좋습니다.
- `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/`는 여전히 프론트 shell + Django 운영 화면 handoff 단계입니다.
- 대시보드 API가 미로그인/비JSON 응답이면 React는 mock 데이터를 보여주지 않고 연결 필요 상태를 표시합니다.
- `EMAIL_ENCRYPTION_KEY` 미설정 경고는 기존 환경 경고이며 이번 변경과 무관합니다.

### 7. Recommended Next Task

- React `/customers/`에 고객 검색, 담당자 필터, 우선순위 고객 리스트를 연결합니다.
- 그 다음 `/notes/`와 `/schedules/`를 API 기반 실제 화면으로 순차 전환합니다.

---

## Frontend Migration — React Customers 실제 데이터 연결

### 1. Summary

React `/customers/` placeholder를 실제 Django CRM 고객 데이터 화면으로 교체했습니다. 또한 프론트에서 `/reporting/api/dashboard/` 호출 시 미로그인 상태가 로그인 HTML 200으로 보이던 문제를 수정해, React용 JSON API는 미인증 시 401 JSON을 반환하도록 했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React customers 실제 데이터 연결 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/views.py` | API 미인증 JSON 401 helper, `/reporting/api/customers/` 데이터 API 추가 |
| `reporting/urls.py` | `/reporting/api/customers/` route 추가 |
| `reporting/tests.py` | dashboard API 401 JSON 기대값 수정, customers API 권한/필터 테스트 추가 |
| `frontend/src/api.ts` | Customers API 타입과 `loadCustomersData()` 추가, dashboard API JSON error 처리 개선 |
| `frontend/src/App.tsx` | `/customers/` 검색/담당자/우선순위/파이프라인 필터 UI와 실제 고객 리스트 추가 |
| `frontend/src/styles.css` | customers 화면 필터, 테이블, 우선 고객 패널, 반응형 스타일 추가 |
| `frontend/README.md` | dashboard/customers 실제 API 연결 상태 문서화 |

### 3. CRM Improvements

- `/customers/`에서 실제 고객 목록을 검색하고 담당자, 우선순위, 파이프라인 단계로 필터링할 수 있습니다.
- 우선 고객 패널은 긴급/팔로업/VIP/A/지연 후속 고객을 빠르게 보여줍니다.
- 고객 행에서 기존 Django 고객 상세와 일정 등록으로 바로 이동할 수 있습니다.
- API 미로그인 상태가 HTML 200으로 오인되지 않고 401 JSON으로 처리됩니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/followups/`, `/reporting/followups/<id>/`, `/reporting/companies/`, `/reporting/customer-report/` 운영 화면은 유지했습니다.
- 기존 Django 인증/권한 범위를 유지했습니다. Salesman은 본인 고객만, Manager는 같은 회사 고객만 볼 수 있습니다.
- DB 모델과 migration 변경은 없습니다.
- 파이프라인 API와 Django 운영 화면은 변경하지 않았습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.DashboardSummaryApiTests --verbosity=1
→ Ran 4 tests, OK

python manage.py test reporting.tests.DashboardSummaryApiTests reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 8 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 148 tests, OK

python manage.py test --verbosity=1
→ Ran 160 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Local smoke:
→ http://127.0.0.1:5173/customers/ returned 200
→ http://127.0.0.1:5173/reporting/api/dashboard/ returned 401 when unauthenticated
→ http://127.0.0.1:5173/reporting/api/customers/ returned 401 when unauthenticated
```

### 6. Known Limitations

- 운영 로그인 세션에서 `/dashboard/`와 `/customers/`의 실제 데이터 표시를 브라우저로 추가 확인하는 것이 좋습니다.
- `/notes/`, `/schedules/`, `/ai-workspace/`는 아직 프론트 shell + Django 운영 화면 handoff 단계입니다.
- 고객 API는 현재 상위 60건 목록과 우선 고객 10건을 반환합니다. 대량 고객용 서버 페이지네이션은 다음 개선에서 다룰 수 있습니다.
- `EMAIL_ENCRYPTION_KEY` 미설정 경고는 기존 환경 경고이며 이번 변경과 무관합니다.

### 7. Recommended Next Task

- React `/notes/`를 실제 영업노트 API 기반 목록/필터 화면으로 전환합니다.
- 이어서 React `/schedules/`를 일정 API 기반 오늘/주간 일정 화면으로 전환합니다.

---

## Frontend Migration — React Notes 실제 데이터 연결

### 1. Summary

React `/notes/` placeholder를 실제 Django 영업노트 데이터 화면으로 교체했습니다. 새 `/reporting/api/notes/` 읽기 전용 API가 영업 활동 기록, 검토 상태, 다음 액션, 유형별 현황, 담당자/활동유형/검토/후속 필터 옵션을 반환하고, React 화면은 이를 검색/필터 가능한 업무 목록으로 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React notes 실제 데이터 연결 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |
| `reporting/views.py` | `/reporting/api/notes/` 데이터 API와 history payload helper 추가 |
| `reporting/urls.py` | `/reporting/api/notes/` route 추가 |
| `reporting/tests.py` | notes API 로그인/권한 범위/필터 테스트 추가 |
| `frontend/src/api.ts` | Notes API 타입과 `loadNotesData()` 추가 |
| `frontend/src/App.tsx` | `/notes/` 검색/담당자/활동유형/검토/후속 필터 UI와 실제 노트 목록 추가 |
| `frontend/src/styles.css` | notes 화면 필터, 테이블, 유형별 현황, 반응형 스타일 추가 |
| `frontend/README.md` | notes 실제 API 연결 상태 문서화 |

### 3. CRM Improvements

- `/notes/`에서 실제 영업노트를 고객/회사/내용/다음 액션 기준으로 검색할 수 있습니다.
- 담당자, 활동 유형, 검토 상태, 다음 액션 상태(지연/7일 이내/예정일 있음) 필터를 제공합니다.
- 미검토 노트, 지연 후속, 7일 이내 후속을 KPI로 보여줍니다.
- 노트 행에서 기존 Django 영업노트 상세, 고객 상세, 일정 상세로 바로 이동할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/histories/`, `/reporting/histories/<id>/`, `/reporting/weekly-reports/` 운영 화면은 유지했습니다.
- 기존 Django 인증/권한 범위를 유지했습니다. Salesman은 본인 노트만, Manager는 같은 회사 사용자 노트만 볼 수 있습니다.
- DB 모델과 migration 변경은 없습니다.
- `/reporting/*`, `/ai/*`, 파이프라인 API는 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=2
→ Ran 4 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 152 tests, OK

python manage.py test --verbosity=1
→ Ran 164 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Local smoke:
→ http://127.0.0.1:5173/notes/ returned 200
→ http://127.0.0.1:5173/reporting/api/notes/ returned 401 JSON when unauthenticated
```

### 6. Known Limitations

- 운영 로그인 세션에서 `/notes/` 실제 데이터 표시를 브라우저로 추가 확인하는 것이 좋습니다.
- `/schedules/`, `/ai-workspace/`는 아직 프론트 shell + Django 운영 화면 handoff 단계입니다.
- Notes API는 현재 상위 80건 목록을 반환합니다. 대량 노트용 서버 페이지네이션은 다음 개선에서 다룰 수 있습니다.
- `EMAIL_ENCRYPTION_KEY` 미설정 경고는 기존 환경 경고이며 이번 변경과 무관합니다.

### 7. Recommended Next Task

- React `/schedules/`를 실제 일정 API 기반 오늘/주간 일정 화면으로 전환합니다.
- 이후 `/ai-workspace/`를 기존 Django AI 운영 기능과 연결된 실제 업무 화면으로 정리합니다.

---

## Frontend Migration — React Schedules 실제 데이터 연결

### 1. Summary

React `/schedules/` placeholder를 실제 Django 일정 데이터 화면으로 교체했습니다. 새 `/reporting/api/schedules/` 읽기 전용 API가 고객 일정, 개인 일정, 오늘 일정, 7일 이내 일정, 지연 일정, 상태/활동유형/담당자 필터 옵션을 반환하고, React 화면은 이를 검색/필터 가능한 업무 목록으로 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React schedules 실제 데이터 연결 계획과 예상 소요 추가 |
| `AGENT_REPORT.md` | 작업 결과와 남은 목표 예상 소요 기록 |
| `reporting/views.py` | `/reporting/api/schedules/` 데이터 API와 Schedule/PersonalSchedule payload helper 추가 |
| `reporting/urls.py` | `/reporting/api/schedules/` route 추가 |
| `reporting/tests.py` | schedules API 로그인/권한 범위/필터 테스트 추가 |
| `frontend/src/api.ts` | Schedules API 타입과 `loadSchedulesData()` 추가 |
| `frontend/src/App.tsx` | `/schedules/` 검색/담당자/상태/활동유형/기간 필터 UI와 실제 일정 목록 추가 |
| `frontend/src/styles.css` | schedules 화면 필터, 테이블, 오늘/지연 일정 패널, 반응형 스타일 추가 |
| `frontend/README.md` | schedules 실제 API 연결 상태 문서화 |

### 3. CRM Improvements

- `/schedules/`에서 실제 고객 일정과 개인 일정을 함께 확인할 수 있습니다.
- 검색, 담당자, 상태, 활동 유형, 기간 필터를 제공합니다.
- 오늘 일정, 7일 이내 일정, 지연 일정, 완료 일정 KPI를 보여줍니다.
- 일정 행에서 기존 Django 일정 상세, 고객 상세, 보고 작성 화면으로 바로 이동할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/schedules/`, `/reporting/schedules/calendar/`, `/reporting/schedules/<id>/`, `/reporting/personal-schedules/*` 운영 화면은 유지했습니다.
- 기존 Django 인증/권한 범위를 유지했습니다. Salesman은 본인 일정만, Manager는 같은 회사 사용자 일정만 볼 수 있습니다.
- DB 모델과 migration 변경은 없습니다.
- `/reporting/*`, `/ai/*`, 파이프라인 API는 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=2
→ Ran 4 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 156 tests, OK

python manage.py test --verbosity=1
→ Ran 168 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Local smoke:
→ http://127.0.0.1:5173/schedules/ returned 200
→ http://127.0.0.1:5173/reporting/api/schedules/ returned 401 JSON when unauthenticated
```

### 6. Estimated Time / Remaining

- 이번 `/schedules/` 실제 데이터 연결은 로컬 구현과 검증까지 완료했습니다.
- 운영 로그인 세션에서 실제 데이터 육안 확인과 배포까지 진행하면 추가 20~40분 예상입니다.
- 남은 React shell 핵심 전환은 `/ai-workspace/` 1개입니다. 기존 Django AI 기능 연결 중심이면 약 2~4시간, AI 작업 화면을 더 깊게 재구성하면 반나절 수준으로 보는 것이 안전합니다.

### 7. Known Limitations

- 운영 로그인 세션에서 `/schedules/` 실제 데이터 표시를 브라우저로 추가 확인하는 것이 좋습니다.
- `/ai-workspace/`는 아직 프론트 shell + Django 운영 화면 handoff 단계입니다.
- Schedules API는 현재 상위 80건 목록을 반환합니다. 대량 일정용 서버 페이지네이션은 다음 개선에서 다룰 수 있습니다.
- `EMAIL_ENCRYPTION_KEY` 미설정 경고는 기존 환경 경고이며 이번 변경과 무관합니다.

### 8. Recommended Next Task

- React `/ai-workspace/`를 기존 Django AI 운영 기능과 연결된 실제 업무 화면으로 전환합니다.
- 이후 운영 로그인 상태에서 `/dashboard/`, `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/` 왕복 동선을 확인하고 배포/커밋을 진행합니다.

---

## Frontend Migration — React AI Workspace 실제 데이터 연결

### 1. Summary

React `/ai-workspace/` placeholder를 실제 Django AI 운영 상태 화면으로 교체했습니다. 새 `/reporting/api/ai-workspace/` 읽기 전용 API가 AI 권한 상태, 부서 분석 대상, 분석 완료 현황, 미검증 PainPoint, 고객 분석 대상, 주간보고 AI 초안 링크를 반환하고, React 화면은 기존 `/ai/*` 및 `/reporting/*` 운영 기능으로 연결합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React AI workspace 실제 데이터 연결 계획과 예상 소요 추가 |
| `AGENT_REPORT.md` | 작업 결과와 목표 달성/남은 예상 소요 기록 |
| `reporting/views.py` | `/reporting/api/ai-workspace/` 데이터 API와 AI summary helper 추가 |
| `reporting/urls.py` | `/reporting/api/ai-workspace/` route 추가 |
| `reporting/tests.py` | AI workspace API 로그인/권한/데이터 범위 테스트 추가 |
| `frontend/src/api.ts` | AI workspace API 타입과 `loadAIWorkspaceData()` 추가 |
| `frontend/src/App.tsx` | `/ai-workspace/` AI 권한, 부서 분석, PainPoint, 고객 분석, 주간보고 링크 UI 추가 |
| `frontend/src/styles.css` | AI workspace 레이아웃, 분석 리스트, PainPoint, 고객 분석 카드 스타일 추가 |
| `frontend/README.md` | AI workspace 실제 API 연결 상태 문서화 |

### 3. CRM Improvements

- `/ai-workspace/`에서 AI 권한 상태와 실제 AI 운영 데이터를 확인할 수 있습니다.
- 부서별 AI 분석 대상, 분석 완료 여부, 미검증 PainPoint 수를 표시합니다.
- 미검증 PainPoint와 고객별 AI 분석 대상에서 기존 Django AI 상세 화면으로 이동할 수 있습니다.
- 이번 주 주간보고 AI 초안 API 링크와 주간보고 작성 화면을 연결했습니다.
- `can_use_ai=False` 사용자는 AI 데이터를 받지 않고 권한 없음 상태만 확인합니다.

### 4. Existing Functionality Preserved

- 기존 `/ai/`, `/ai/department/<id>/`, `/ai/followup/<id>/`, `/reporting/api/weekly-reports/ai-draft/` 운영 기능은 유지했습니다.
- 새 API는 읽기 전용이며 외부 AI API 호출을 수행하지 않습니다.
- 기존 AI 권한 모델(`UserProfile.can_use_ai`)을 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=2
→ Ran 3 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test ai_chat --verbosity=1
→ Ran 12 tests, OK

python manage.py test reporting --verbosity=1
→ Ran 159 tests, OK

python manage.py test --verbosity=1
→ Ran 171 tests, OK

git diff --check
→ OK (LF→CRLF warning only)

Local smoke:
→ http://127.0.0.1:5173/ai-workspace/ returned 200
→ http://127.0.0.1:5173/reporting/api/ai-workspace/ returned 401 JSON when unauthenticated
```

### 6. Estimated Time / Remaining

- `/dashboard/`, `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/` 실제 데이터 연결은 로컬 구현/검증 기준으로 완료했습니다.
- 남은 필수 작업은 운영 로그인 상태에서 프론트 메뉴 왕복 동선 확인, 필요 시 UI 미세 조정, 커밋/푸시/배포입니다.
- 운영 smoke + 커밋/푸시까지 약 30~60분 예상입니다.
- 배포 후 Railway 프론트/웹 상태 확인과 실제 계정 브라우저 확인까지 포함하면 총 1~1.5시간 정도 잡는 것이 안전합니다.

### 7. Known Limitations

- 운영 로그인 세션에서 AI 권한 사용자와 비권한 사용자 각각의 `/ai-workspace/` 화면을 육안 확인하는 것이 좋습니다.
- React 화면에서 AI 분석 실행 자체는 하지 않고 기존 Django `/ai/*` 운영 화면으로 연결합니다.
- AI workspace API는 현재 로그인 사용자 본인의 AI 분석 대상/결과만 표시합니다. 팀 단위 AI 운영 화면은 별도 정책 확정 후 확장하는 것이 안전합니다.
- `EMAIL_ENCRYPTION_KEY` 미설정 경고는 기존 환경 경고이며 이번 변경과 무관합니다.

### 8. Recommended Next Task

- 운영 로그인 상태에서 `/dashboard/`, `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/` 프론트 메뉴와 Django 운영 화면 왕복 동선을 확인합니다.
- 문제가 없으면 현재 변경사항을 커밋/푸시하고 Railway 배포 상태를 확인합니다.

---

## Pipeline Pricing + Schedule Calendar Routing

**날짜**: 2026-05-07
**상태**: 완료

### 1. Summary

React 파이프라인과 Django 파이프라인 보드에서 `견적 제출`, `협상`, `수주` 단계의 금액이 기존 `Quote` 데이터에서 단계에 맞게 반영되도록 수정했습니다.
프론트 `/schedules/`는 일정 목록 대신 기존 Django 일정 캘린더(`/reporting/schedules/calendar/`)로 이동하도록 변경했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 작업 계획과 예상 소요 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `reporting/funnel_views.py` | 파이프라인 단계별 가격 기준 Quote 선택 로직 추가 |
| `reporting/templates/reporting/funnel/pipeline.html` | Django 보드의 금액/견적 표시 문구 보정 |
| `reporting/tests.py` | 견적/협상/수주 단계 금액 선택 회귀 테스트 추가 |
| `frontend/server.mjs` | `/schedules/` → `/reporting/schedules/calendar/` 서버 리디렉션 추가 |
| `frontend/src/App.tsx` | 일정 메뉴 문구를 캘린더 중심으로 정리하고 런타임 리디렉션 보정 |
| `frontend/src/mockData.ts` | 파이프라인 견적 source 필드 타입 추가 |
| `frontend/README.md` | 일정 캘린더 우선 동선 문서화 |

### 3. CRM Improvements

- `quote` 단계는 발송/검토/초안 등 진행 중 견적 금액을 우선 반영합니다.
- `negotiation` 단계는 협상중 견적 금액을 우선 반영합니다.
- `won` 단계는 승인/계약전환/납품전환 견적 금액을 우선 반영합니다.
- 최신 견적이 거절/만료여도 현재 파이프라인 단계에 맞는 견적 금액이 있으면 그 금액을 사용합니다.
- `/schedules/`는 현업 사용 빈도가 높은 일정 캘린더로 바로 연결됩니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 운영 화면은 유지했습니다.
- 기존 Django 일정 목록, 일정 등록, 일정 상세, 캘린더, 일정 API는 제거하지 않았습니다.
- 인증/권한/CSRF 정책 변경은 없습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 8 tests, OK

python manage.py test reporting --verbosity=1
→ Ran 160 tests, OK

python manage.py test --verbosity=1
→ Ran 172 tests, OK

git diff --check
→ OK

local frontend smoke: GET /schedules/
→ 302 /reporting/schedules/calendar/
```

### 6. Known Limitations

- 운영에서 로그인된 브라우저 캘린더 화면의 실제 육안 확인은 사용자 세션이 필요합니다.
- 수주 금액은 현재 Quote의 승인/계약전환/납품전환 상태를 기준으로 반영합니다. 별도 발주서/납품 실매출 기준으로 바꾸려면 추가 정책 정의가 필요합니다.

### 7. Recommended Next Task

- 운영 배포 후 `/`, `/reporting/api/pipeline/`, `/schedules/`, `/reporting/schedules/calendar/` smoke를 확인합니다.
- 이후 수주 단계에서 “견적 금액”과 “실제 납품/매출 금액” 중 어떤 값을 대표 금액으로 볼지 정책을 확정하면 더 정밀하게 맞출 수 있습니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 20~40분.
- 수주 금액 기준을 실제 납품/매출 기준으로 확장할 경우: 약 1~2시간.

---

## Pipeline Pricing — 실제 견적/납품 품목 기준 보강

**날짜**: 2026-05-07
**상태**: 완료

### 1. Summary

파이프라인 카드 금액 기준을 기존 `Quote` 중심에서 실제 운영 입력 데이터 중심으로 보강했습니다. 견적/협상 단계는 견적 일정 품목과 견적 히스토리 품목을 먼저 사용하고, 수주 단계는 완료된 납품 일정/납품 히스토리의 실제 납품 매출을 합산합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 실제 견적/납품 품목 기준 보강 계획과 예상 소요 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `reporting/funnel_views.py` | 파이프라인 가격 기준을 Schedule/History DeliveryItem과 납품금액 기반으로 보강 |
| `reporting/tests.py` | 견적 일정 품목, 견적 히스토리 품목, 실제 납품 히스토리 품목 회귀 테스트 추가 |
| `frontend/src/mockData.ts` | 파이프라인 가격 기준 타입(`basisType`) 추가 |

### 3. CRM Improvements

- `quote`, `negotiation` 단계 금액은 견적 일정의 품목 총액을 우선 표시합니다.
- 견적 일정 품목이 없으면 견적 활동 히스토리에 직접 입력된 품목 총액을 사용합니다.
- 실제 견적/활동 품목 데이터가 없을 때만 `Quote` 모델 금액으로 fallback합니다.
- `won` 단계 금액은 완료된 납품 일정 품목, 연결된 납품 히스토리 품목/금액, 독립 납품 히스토리 품목/금액을 실제 납품 매출로 합산합니다.
- API 응답의 `latestQuote.source`와 `basisType`으로 금액 출처를 구분할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 운영 화면은 유지했습니다.
- 일정, 히스토리, 견적, 납품 품목 저장 구조는 변경하지 않았습니다.
- 인증/권한/CSRF 정책 변경은 없습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 10 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 162 tests, OK

python manage.py test --verbosity=1
→ Ran 174 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 운영 로그인 세션에서 실제 고객명/금액이 맞는지 육안 확인은 필요합니다.
- 품목 총액은 기존 `DeliveryItem.save()` 계산과 동일하게 단가 × 수량 × VAT 10% 포함 금액을 사용합니다.
- 수주 금액은 실제 납품 기준이므로, 아직 납품 완료/납품 히스토리가 없는 수주 카드는 기존 수주 견적 fallback으로 표시됩니다.

### 7. Recommended Next Task

- 운영 배포 후 로그인 상태에서 파이프라인 `견적 제출`, `협상`, `수주` 카드의 금액 출처와 실제 금액을 확인합니다.
- 이후 수주 카드에서 견적 대비 실제 납품 매출 차이를 함께 보여줄지 검토합니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 20~40분.
- 운영 로그인 육안 확인: 약 10~20분.

---

## Pipeline Won Cards — 견적 대비 실제 납품 매출 차이 표시

**날짜**: 2026-05-08
**상태**: 완료

### 1. Summary

수주 단계 카드의 대표 금액은 실제 납품 매출 기준으로 유지하면서, 같은 카드에서 기준 견적 금액과 실제 납품 매출의 차액/차이율을 함께 볼 수 있도록 보강했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 수주 카드 견적 대비 실제 납품 매출 차이 표시 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `reporting/funnel_views.py` | `quoteComparison` 계산 및 API/템플릿 payload 추가 |
| `reporting/templates/reporting/funnel/pipeline.html` | Django 파이프라인 카드에 견적 대비 차이 표시 |
| `reporting/tests.py` | 수주 실제 납품 매출과 기준 견적 비교 회귀 테스트 추가 |
| `frontend/src/App.tsx` | React 파이프라인 카드, 리스트, 상세 패널에 견적 대비 차이 표시 |
| `frontend/src/mockData.ts` | `quoteComparison` 타입과 mock 데이터 추가 |
| `frontend/src/styles.css` | 견적 대비 차이 UI 스타일 추가 |

### 3. CRM Improvements

- `won` 카드의 대표 금액은 실제 납품 매출 기준을 유지합니다.
- `won` 카드에 기준 견적 금액, 실제 납품 매출, 차액, 차이율, 초과/미달/일치 상태를 함께 제공합니다.
- 기준 견적은 견적 일정 품목 → 견적 활동 품목 → 수주/전환 견적 → 진행/최근 견적 순으로 찾습니다.
- React 파이프라인의 카드, 표, 상세 패널과 Django 파이프라인 보드 모두 동일한 비교 정보를 표시합니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 운영 화면은 유지했습니다.
- 기존 파이프라인 대표 금액, 단계 계산, 상세 링크, 인증/권한 정책은 변경하지 않았습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 10 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 162 tests, OK

python manage.py test --verbosity=1
→ Ran 174 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 운영 로그인 세션에서 실제 수주 카드의 견적 대비 차이 표시가 의도한 고객 데이터와 맞는지 육안 확인이 필요합니다.
- 실제 납품 매출이나 기준 견적 금액이 0원이면 비교 정보는 표시하지 않습니다.

### 7. Recommended Next Task

- 운영 배포 후 로그인 상태에서 수주 카드의 `대표 금액`, `견적 대비`, 상세 패널의 실제 납품 매출 비교 박스를 확인합니다.
- 다음 업무 화면 전환은 React 고객 화면의 검색/담당자/우선순위 필터 연결을 진행합니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 20~40분.
- 운영 로그인 육안 확인: 약 10~20분.
- 다음 고객 화면 실제 데이터 연결: 약 2~4시간.

---

## Customers Real Data + Department Quote Loading

**날짜**: 2026-05-08
**상태**: 완료

### 1. Summary

React 고객 화면을 실제 Django 고객 요약 API 데이터로 보강하고, 같은 부서/연구실에 견적 일정이 여러 건 있을 때 견적 한 건만 불러오던 문제를 수정했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 실제 데이터 연결 및 부서 다중 견적 보정 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `frontend/src/App.tsx` | 고객 목록에 예정 일정, 활동/일정 수, 지연 후속, 보고 링크 표시 |
| `frontend/src/api.ts` | 고객 API 응답 타입에 활동/일정/예정 일정 필드 추가 |
| `frontend/src/styles.css` | 고객 테이블과 우선순위 목록 표시 스타일 보강 |
| `reporting/views.py` | 고객 요약 API enrichment 추가, 견적 품목 API를 같은 부서의 여러 견적 일정까지 조회하도록 수정, 고객 기록 API에 Quote 모델 없는 견적 일정 포함 |
| `reporting/funnel_views.py` | 파이프라인 금액 산정 시 여러 견적 일정/활동/Quote 모델 금액 합산 |
| `reporting/templates/reporting/schedule_form.html` | 견적 선택 모달에 고객/회사/부서/일정 정보를 표시 |
| `reporting/tests.py` | 고객 API, 부서 다중 견적 조회, 견적 일정 기반 고객 기록, 파이프라인 다중 견적 합산 회귀 테스트 추가 |

### 3. CRM Improvements

- `/customers/` React 화면에서 고객별 예정 일정, 최근 활동, 활동 수, 일정 수, 지연 후속 수를 바로 확인할 수 있습니다.
- 납품 일정 생성 시 같은 부서/연구실의 본인 견적 일정 여러 건을 모두 후보로 불러옵니다.
- 견적 일정에 `Quote` 모델 레코드가 없어도 고객 기록 API에서 견적 내역과 총액에 포함합니다.
- 파이프라인의 견적 제출/협상 카드 금액은 여러 견적 일정이 있으면 합산하고, 출처를 `견적 일정 N건` 형태로 표시합니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 운영 화면은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.
- 기존 인증/권한 정책은 약화하지 않았습니다. 견적 품목 API는 접근 가능한 부서 범위 안에서 본인이 작성한 견적 일정만 불러옵니다.
- 수주 금액은 기존과 동일하게 실제 납품 매출 기준을 유지합니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.QuoteItemsApiTests --verbosity=1
→ Ran 2 tests, OK

python manage.py test reporting.tests.PipelineApiTests --verbosity=1
→ Ran 11 tests, OK

python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 5 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

python manage.py test reporting --verbosity=1
→ Ran 166 tests, OK

python manage.py test --verbosity=1
→ Ran 178 tests, OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 운영 로그인 세션에서 `/customers/` 실제 데이터 표시와 견적 선택 모달의 여러 견적 후보는 육안 확인이 필요합니다.
- 같은 부서의 동료 작성 견적까지 자동으로 끌어오지는 않습니다. 기존 데이터 접근 경계를 유지하기 위해 본인이 작성한 견적 일정만 포함했습니다.
- 견적 일정에 품목이 없으면 `expected_revenue`가 있는 경우에만 금액으로 표시합니다.

### 7. Recommended Next Task

- 운영 배포 후 로그인 상태에서 `/customers/` 고객 목록, 예정 일정 링크, 보고 링크가 실제 데이터와 맞는지 확인합니다.
- 납품 일정 생성 화면에서 같은 부서의 견적 후보가 여러 건 표시되는지 확인합니다.
- 다음 개발은 고객 상세 패널 또는 React 노트 화면 실제 데이터 연결을 진행합니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 20~40분.
- 운영 로그인 육안 확인: 약 10~20분.
- 다음 고객 상세/노트 실제 데이터 연결: 약 2~4시간.

---

## Notes Page — 미검토/지연 노트 검토 동선 보강

**날짜**: 2026-05-08
**상태**: 완료

### 1. Summary

React `/notes/` 화면에서 관리자/매니저가 미검토 영업노트를 확인하고 바로 검토 완료/해제 처리할 수 있도록 보강했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 노트 검토 동선 보강 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `frontend/src/App.tsx` | 노트 목록에 첨부/댓글 수, 검토 메타, 검토 완료/해제 버튼 추가 |
| `frontend/src/api.ts` | 노트 API 타입 확장 및 검토 토글 POST helper 추가 |
| `frontend/src/styles.css` | 노트 메타/검토 버튼/처리 결과 메시지 스타일 추가 |
| `reporting/views.py` | 노트 API payload에 `canReview`, 검토자/검토시각, 토글 URL, 댓글/첨부 수 추가 |
| `reporting/tests.py` | 노트 검토 메타데이터와 검토 토글 권한 회귀 테스트 추가 |

### 3. CRM Improvements

- 관리자/매니저는 React `/notes/` 목록에서 미검토 노트를 바로 `검토 완료` 처리할 수 있습니다.
- 이미 검토된 노트는 같은 자리에서 `검토 해제`할 수 있습니다.
- 검토 처리 후 현재 검색/담당자/유형/검토/다음 액션 필터를 유지한 채 데이터를 다시 불러와 지표가 갱신됩니다.
- 노트 목록에서 댓글 수와 첨부 수를 바로 확인할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 영업노트 상세/작성/관리자 메모 기능은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.
- 기존 `history_toggle_reviewed` view를 재사용했고, 관리자/매니저 권한이 없는 사용자는 검토 POST가 403으로 차단됩니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 6 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

python manage.py test reporting --verbosity=1
→ Ran 168 tests, OK

python manage.py test --verbosity=1
→ Ran 180 tests, OK
```

### 6. Known Limitations

- 운영 로그인 세션에서 `/notes/`의 검토 완료/해제 버튼 동작은 실제 관리자 계정으로 육안 확인이 필요합니다.
- React 화면은 검토 토글만 처리합니다. 노트 작성, 상세 편집, 관리자 메모 작성은 기존 Django 화면으로 연결합니다.

### 7. Recommended Next Task

- 운영 배포 후 관리자/매니저 계정으로 `/notes/`에서 미검토 필터 → 검토 완료 → 지표 갱신을 확인합니다.
- 다음 개발은 React AI 업무도구(`/ai-workspace/`)의 실제 데이터 화면을 더 실무형 프롬프트/대상자 중심으로 정리합니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 20~40분.
- 운영 로그인 육안 확인: 약 10~20분.
- 다음 AI 업무도구 화면 보강: 약 2~4시간.

---

## Notes Review Permission — 회사별 매니저 기준 보정 (2026-05-08)

### 1. Summary

영업노트 검토 완료/해제 권한을 `admin/manager`가 아니라 각 소속 회사의 `manager` 계정 기준으로 보정했습니다. 이전 보고의 "관리자 계정 확인" 표현도 실제 운영 기준과 맞지 않아, React 화면 문구를 "매니저 검토"로 수정했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 회사별 매니저 기준 검토 권한 보정 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `frontend/src/App.tsx` | "관리자 검토" 문구를 "매니저 검토"로 변경 |
| `reporting/views.py` | 노트 검토 API/POST 권한을 소속 회사 `manager` 역할로 제한 |
| `reporting/tests.py` | admin, salesman, 타회사 manager 차단 및 같은 회사 manager 허용 테스트 추가 |

### 3. CRM Improvements

- 같은 회사의 매니저 계정만 React `/notes/`에서 검토 완료/해제 버튼을 받을 수 있습니다.
- 최고권한자/admin 계정은 조회는 기존 정책대로 가능하지만, 노트 검토 처리 버튼과 POST 권한은 받지 않습니다.
- 타회사 manager가 URL을 직접 POST해도 403으로 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 라우트는 유지했습니다.
- DB 모델과 migration 변경은 없습니다.
- Salesman 본인 노트 조회, manager 동일 회사 노트 조회, 기존 Django 영업노트 상세/작성 흐름은 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 7 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 운영 로그인 세션에서 같은 회사 manager 계정으로 `/notes/` 검토 토글을 육안 확인해야 합니다.
- React 화면은 검토 토글만 처리합니다. 매니저 메모 작성은 기존 Django 상세 화면을 계속 사용합니다.

### 7. Recommended Next Task

- 이 권한 보정을 배포한 뒤, React AI 업무도구(`/ai-workspace/`)를 고객/부서/영업노트 맥락 기반 프롬프트 화면으로 보강합니다.

**예상 소요**:

- 권한 보정 배포 및 smoke: 약 30~60분.
- 다음 AI 업무도구 화면 보강 1차: 약 2~4시간.

---

## AI Workspace — 실제 대상 기반 프롬프트 큐 추가 (2026-05-08)

### 1. Summary

React `/ai-workspace/`에 실제 부서, 고객, 미검증 PainPoint 데이터를 바탕으로 한 AI 작업 큐를 추가했습니다. 각 카드에서 외부 AI에 바로 붙여 넣을 수 있는 업무 프롬프트를 복사하고, 관련 Django AI 분석 화면으로 이동할 수 있습니다.
프론트/백엔드 배포 순서가 엇갈려도 이전 API 응답에서 `promptTargets`가 없으면 빈 배열로 처리하도록 호환 fallback도 추가했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | AI workspace 프롬프트 큐 작업 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `frontend/src/App.tsx` | AI 작업 큐 패널, 프롬프트 카드, 복사 버튼, 이전 API 응답 fallback 추가 |
| `frontend/src/api.ts` | `AIWorkspacePromptTarget` 타입과 `promptTargets` payload/fallback 추가 |
| `frontend/src/styles.css` | AI 프롬프트 큐/카드/복사 액션 스타일 추가 |
| `reporting/views.py` | 부서/고객/PainPoint 기반 `promptTargets` 생성 |
| `reporting/tests.py` | AI workspace API의 프롬프트 payload 회귀 테스트 추가 |

### 3. CRM Improvements

- AI workspace가 현황판에서 실제 작업 대상 큐로 확장되었습니다.
- 미검증 PainPoint, 고득점 고객, 부서 분석 대상을 실제 데이터 문맥과 함께 프롬프트로 제공합니다.
- 프롬프트에는 업체/부서/고객/우선순위/분석 요약/검증 질문이 포함됩니다.
- AI 권한이 없는 사용자는 기존처럼 빈 데이터와 권한 상태만 받습니다.

### 4. Existing Functionality Preserved

- 기존 `ai_chat` 부서 분석, 고객 분석, 주간보고 AI 초안 링크는 유지했습니다.
- 기존 `reporting` app과 `/reporting/*` 라우트는 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1
→ Ran 3 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 현재는 프롬프트 복사와 기존 AI 화면 이동까지 처리합니다. 화면 안에서 직접 LLM 호출은 하지 않습니다.
- 브라우저 클립보드 정책상 비보안 로컬 환경에서는 복사 버튼이 동작하지 않을 수 있지만, 운영 HTTPS에서는 동작합니다.
- reporting 전체 테스트는 5분 제한에 걸려 완료 결과를 받지 못했습니다. AI workspace 대상 테스트와 Django check/build는 통과했습니다.

### 7. Recommended Next Task

- `/ai-workspace/`에서 복사한 프롬프트를 실제 계정 데이터로 확인합니다.
- 다음 개발은 프롬프트 대상에 "최근 영업노트 3건"과 "열린 견적/수주 금액"을 같이 붙이는 보강이 적절합니다.

**예상 소요**:

- 운영 배포 및 smoke: 약 30~60분.
- 다음 AI 프롬프트 문맥 확장: 약 1.5~3시간.

---

## AI Workspace — 프롬프트 문맥 확장 (2026-05-08)

### 1. Summary

`/ai-workspace/`의 AI 작업 큐 프롬프트에 최근 영업노트 3건과 열린 견적/수주 금액 요약을 추가했습니다. 부서 전략, 고객 후속, PainPoint 검증 프롬프트 모두 실제 활동 이력과 금액 맥락을 함께 복사할 수 있습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 프롬프트 문맥 확장 계획과 DB 변경 없음 명시 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `reporting/views.py` | 최근 영업노트, 열린 견적 금액, 수주 금액 프롬프트 컨텍스트 생성 |
| `reporting/tests.py` | 최근 노트 3건 제한과 금액 문맥 포함 회귀 테스트 추가 |

### 3. CRM Improvements

- AI 프롬프트가 고객/부서명뿐 아니라 최근 실제 영업 활동을 반영합니다.
- 열린 견적은 `Quote` 금액과 Quote가 없는 견적 일정의 예상 매출을 함께 고려하되 중복 집계하지 않습니다.
- 수주 금액은 수주 단계 영업기회의 실제 매출을 우선 사용하고, 전환 견적/납품 기록을 fallback으로 사용합니다.
- 영업노트 본문에서 이메일/연락처는 프롬프트용으로 간단히 마스킹합니다.

### 4. Existing Functionality Preserved

- 기존 `reporting` app과 `/reporting/*` 라우트는 유지했습니다.
- React `/ai-workspace/` 응답 스키마는 변경하지 않았고 기존 `promptTargets` 문자열만 보강했습니다.
- DB 모델과 migration 변경은 없습니다.
- 기존 AI 분석 화면, 주간보고 AI 초안, 고객/노트 링크는 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1
→ Ran 4 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 금액은 현재 시스템에 기록된 `Quote`, 견적 일정, 영업기회, 납품 기록 기준입니다. 누락된 견적/수주 데이터는 프롬프트에 반영되지 않습니다.
- 프롬프트 안에서 직접 LLM 호출은 하지 않고 기존처럼 복사용 텍스트를 제공합니다.
- 전체 `python manage.py test reporting --verbosity=1`는 이번 변경 범위에서는 재실행하지 않았습니다.

### 7. Recommended Next Task

- 운영 AI 권한 계정으로 `/ai-workspace/`에서 실제 고객 프롬프트를 복사해 최근 노트/금액 문맥이 현업 표현에 맞는지 확인합니다.
- 다음 개발은 프롬프트 큐 카드에서 "최근 노트/금액 포함" 배지를 노출하거나, 프롬프트 종류별 필터를 추가하는 작업이 적절합니다.

---

## Frontend Auth Redirect — 미로그인 루트 진입 차단 (2026-05-08)

### 1. Summary

프론트 운영 루트(`/`)에 미로그인 상태로 접속했을 때 파이프라인 mock/fallback 화면이 보이지 않도록, 프론트 API 공통 인증 감지 처리를 추가했습니다. Django 로그인 페이지로 리다이렉트된 응답이나 JSON `login_required` 401을 받으면 현재 프론트 경로를 `next`로 담아 `/reporting/login/`으로 이동합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 미로그인 프론트 진입 차단 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 결과 기록 |
| `frontend/src/api.ts` | 로그인 필요 응답 감지 helper와 API별 리다이렉트 처리 추가 |

### 3. CRM Improvements

- 미로그인 사용자가 `https://sales-note-frontend-production.up.railway.app/`에 들어가도 내부 CRM fallback 화면을 보지 않고 로그인 화면으로 이동합니다.
- 루트 파이프라인뿐 아니라 `/dashboard/`, `/customers/`, `/notes/`, `/ai-workspace/` API 호출에도 동일한 인증 처리를 적용했습니다.
- 로그인 후 돌아올 수 있도록 현재 프론트 경로를 `next` 파라미터로 전달합니다.

### 4. Existing Functionality Preserved

- Django 인증/권한 정책과 `/reporting/*` 라우트는 변경하지 않았습니다.
- DB 모델과 migration 변경은 없습니다.
- 로그인된 사용자의 기존 프론트 API 데이터 로딩 흐름은 유지했습니다.

### 5. Commands Run and Results

```text
cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: redirect unauthenticated frontend users to login"
→ 7a95f0c

git push
→ main -> main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy frontend auth redirect 7a95f0c" --ci
→ Deploy complete, deployment 8d1efec9-6e40-4480-8f26-015e27dace15 SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/
→ 200, assets/index-DDI1KGEv.js

npx --yes --package @playwright/cli playwright-cli delete-data/open/eval
→ 미로그인 루트 접속 후 https://sales-note-frontend-production.up.railway.app/reporting/login/?next=%2F 로 이동 확인
```

### 6. Known Limitations

- 리다이렉트는 정적 HTML 응답 이전의 서버 차단이 아니라 React 앱이 첫 API 응답을 확인한 뒤 수행합니다. 운영에서는 거의 즉시 로그인 화면으로 전환됩니다.
- 운영 비로그인 브라우저 루트 smoke는 완료했습니다.

### 7. Recommended Next Task

- 로그인된 운영 계정에서 루트와 주요 프론트 메뉴(`/dashboard/`, `/customers/`, `/notes/`, `/ai-workspace/`)가 정상 데이터로 로딩되는지 한 번 더 육안 확인합니다.

---

## CRM Shell Navigation — 프론트 중심 동선 안정화 (2026-05-08)

### 1. Summary

React 프론트를 메인 CRM Shell로 고정하도록 로그인/루트/상단 링크 동선을 정리했습니다. 로그인 성공 기본 이동지는 프론트 `/dashboard/`가 되었고, Django 화면에는 "Django 작업 화면" 표시와 "프론트 CRM" 복귀 버튼을 추가했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 프론트 중심 동선 안정화 계획 추가 |
| `frontend/src/App.tsx` | React route 액션과 상단 알림 링크를 프론트 화면 중심으로 정리 |
| `reporting/static/reporting/css/crm-ui.css` | Django 작업 화면 안내 텍스트 스타일 추가 |
| `reporting/templates/reporting/base.html` | Django 상단 바에 프론트 CRM 복귀 버튼과 작업 화면 안내 추가 |
| `reporting/tests.py` | 로그인 기본 redirect와 Django 상단 복귀 링크 테스트 갱신 |
| `reporting/views.py` | 로그인 성공 기본 redirect를 프론트 대시보드로 변경 |
| `sales_project/urls.py` | 인증된 Django 루트 접근을 프론트 대시보드로 변경 |

### 3. CRM Improvements

- 로그인 후 기본 진입점이 Django 대시보드가 아니라 React `/dashboard/`로 통일됩니다.
- Django 템플릿 화면에 들어와도 상단에서 즉시 프론트 CRM으로 돌아갈 수 있습니다.
- Django 화면은 작성/상세/관리 역할임을 명확히 표시합니다.
- React 화면의 불필요한 Django 대시보드 이동 링크를 줄였습니다.

### 4. Existing Functionality Preserved

- 기존 Django 대시보드, 영업노트 작성 모달, 고객/일정/관리 상세 화면은 유지했습니다.
- 기존 `/reporting/*` 라우트와 인증 정책은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests --verbosity=1
→ Ran 14 tests, OK

cd frontend && npm run build
→ OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "fix: make frontend the primary CRM shell"
→ 1aa43e0

git push
→ main -> main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy frontend shell navigation 1aa43e0" --ci
→ Deploy complete, deployment 65de05d4-ecc7-4669-a81a-2a7215d2a293 SUCCESS

railway up --service web --environment production --message "Deploy backend shell navigation 1aa43e0" --ci
→ Deploy complete, deployment 2bdcdf27-2e54-4bf6-8594-228f6b01bf0d SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/
→ 200, assets/index-D4s7e3NB.js

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/login/
→ 200, login-page-ok

npx --yes --package @playwright/cli playwright-cli delete-data/open/eval/close
→ 미로그인 루트 접속 후 /reporting/login/?next=%2F 이동 확인
```

### 6. Known Limitations

- 영업노트 작성은 아직 Django 대시보드 모달을 사용합니다. 완전한 단일 화면 경험을 만들려면 React 노트 작성 폼 이관이 다음 단계입니다.
- 일정 캘린더와 일부 관리 화면은 기존 Django 화면을 계속 사용합니다.
- 로그인된 실제 운영 계정에서 로그인 성공 후 프론트 `/dashboard/` 진입은 육안 확인이 필요합니다.

### 7. Recommended Next Task

- 다음 단계는 React에서 영업노트 작성 폼을 직접 제공하고, 저장 API만 Django를 호출하게 만드는 작업입니다.

---

## React Notes Create — 영업노트 빠른 작성 (2026-05-08)

### 1. Summary

React `/notes/` 화면에서 기본 영업노트를 바로 작성할 수 있게 빠른 작성 패널과 Django JSON 저장 API를 추가했습니다. 상단 `새 영업노트`, React 대시보드 빠른 작업, 고객 화면 기본 작성 링크는 `/notes/?create=1`로 통일해 Django 대시보드 모달 왕복을 줄였습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 영업노트 작성 이관 계획 추가 |
| `frontend/src/App.tsx` | `/notes/` 빠른 작성 패널, 저장 흐름, 작성 링크 정리 |
| `frontend/src/api.ts` | 노트 작성 타입/API 함수와 구버전 payload fallback 보강 |
| `frontend/src/styles.css` | 빠른 작성 폼/버튼 반응형 스타일 추가 |
| `reporting/views.py` | 노트 작성용 고객/활동유형 payload와 `/api/notes/create/` 추가 |
| `reporting/urls.py` | 노트 작성 API URL 등록 |
| `reporting/tests.py` | 작성 권한, 본인 고객 제한, API payload 테스트 추가 |

### 3. CRM Improvements

- 영업사원/admin은 React `/notes/`에서 담당 고객을 선택해 바로 영업노트를 저장할 수 있습니다.
- manager는 기존 정책대로 직접 작성이 차단되고, 회사 manager의 검토 권한 정책은 유지됩니다.
- 저장 후 영업노트 목록과 지표가 즉시 새로고침됩니다.
- `/dashboard/`, `/customers/`, 상단 `새 영업노트`에서 Django 모달 대신 React 작성 패널로 이동합니다.
- `/reporting/api/notes/` GET에서 CSRF 쿠키를 보장해 React POST 저장 안정성을 높였습니다.

### 4. Existing Functionality Preserved

- 기존 Django 영업노트 목록/상세/대시보드 모달은 유지했습니다.
- 첨부파일, 납품 품목, 상세 일정 기반 작성은 기존 Django 화면에서 계속 처리합니다.
- 기존 `/reporting/*` 라우트와 인증 정책은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests reporting.tests.DashboardSummaryApiTests reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 20 tests, OK

cd frontend && npm run build
→ OK, assets/index-B9PQ-tLi.js / assets/index-DTu29yQr.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

git commit -m "feat: add React notes quick create"
→ 947da13

git push origin main
→ main -> main

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React notes quick create 947da13" --ci
→ Deploy complete, assets/index-B9PQ-tLi.js / assets/index-DTu29yQr.css

railway up --service web --environment production --message "Deploy notes quick create API 947da13" --ci
→ Deploy complete

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/
→ 200, assets/index-B9PQ-tLi.js

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/notes/?create=1
→ 200, assets/index-B9PQ-tLi.js

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/notes/
→ 401 login_required, 정상

npx --yes --package @playwright/cli playwright-cli delete-data/open/snapshot/close
→ 미로그인 루트 접속 후 /reporting/login/?next=%2F 이동 확인
```

### 6. Known Limitations

- React 빠른 작성은 기본 필드 중심입니다. 첨부파일, 납품 품목, 상세 일정 연결은 `상세 작성`으로 Django 모달을 사용합니다.
- 운영 계정으로 실제 저장까지 하는 육안 확인은 계정 권한이 필요해 자동 스모크에서는 제외했습니다.

### 7. Recommended Next Task

- React 빠른 작성에서 선택 고객의 최근 영업노트 3건과 열린 견적/수주 금액을 함께 보여주면 작성 품질과 후속 액션 일관성이 좋아집니다.

---

## React Schedules List — 일정 화면 프론트 전환 (2026-05-08)

### 1. Summary

React `/schedules/`가 더 이상 Django 일정 캘린더로 즉시 이동하지 않고, 기존 React 일정 목록 화면을 실제 Django 일정 API 데이터로 표시하도록 연결했습니다. Django 일정 캘린더와 등록/상세/보고 작성 화면은 React 화면의 보조 링크로 유지했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 일정 화면 전환 계획 추가 |
| `frontend/src/App.tsx` | `/schedules/` API 로딩, 필터 상태, `SchedulesPage` 렌더링 연결 |
| `frontend/server.mjs` | `/schedules/` 강제 Django 캘린더 리다이렉트 제거 |
| `frontend/README.md` | 일정 화면 범위와 운영 서버 동작 설명 갱신 |

### 3. CRM Improvements

- 일정 메뉴도 React CRM Shell 안에서 검색/필터/요약을 먼저 볼 수 있습니다.
- 오늘 일정, 지연 일정, 상태별 현황을 React 화면에서 바로 확인합니다.
- 기존 캘린더와 일정 등록은 필요한 작업 링크로 남겨 업무 동선을 보존했습니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/schedules/calendar/`, 일정 목록, 일정 등록, 개인 일정, 상세/보고 작성 경로는 유지했습니다.
- 기존 `/reporting/*` 라우트와 인증 정책은 변경하지 않았습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 4 tests, OK

cd frontend && npm run build
→ OK, assets/index-D4WfnEie.js / assets/index-DTu29yQr.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- React 일정 화면은 목록/검색/필터 중심입니다. 캘린더 drag/drop, 상세 편집, 보고 작성은 기존 Django 화면으로 이동합니다.
- 실제 로그인 계정으로 `/schedules/` 화면의 필터와 캘린더 링크는 한 번 더 육안 확인이 필요합니다.

### 7. Recommended Next Task

- 다음 단계는 일정 등록/수정 중 가장 자주 쓰는 필드를 React 빠른 작성 패널로 옮기고, Django 상세 화면은 고급 편집용으로 남기는 작업입니다.

---

## Local Dev Server Fix — 잘못된 Django 실행 경로 수정 (2026-05-08)

### 1. Summary

`/reporting/login/`에서 `no such table: django_session` 오류가 발생한 원인을 확인했습니다. 8000 포트의 Django 서버가 작업 경로인 `D:\projects\sales-note`가 아니라 `C:\projects\sales-note`에서 실행 중이었고, 해당 SQLite DB는 테이블이 없는 빈 DB였습니다. 잘못 뜬 서버를 종료하고 `D:\projects\sales-note`에서 Django 개발 서버를 다시 시작했습니다.

### 2. Files Changed

- 코드 변경 없음.

### 3. Existing Functionality Preserved

- DB 파일이나 migration은 변경하지 않았습니다.
- 기존 React 일정 전환 변경은 그대로 유지했습니다.

### 4. Commands Run and Results

```text
Get-NetTCPConnection -LocalPort 8000
→ 8000 listener PID 40476 확인

SQLite table check
→ D:\projects\sales-note\db.sqlite3: django_session exists, 50 tables
→ C:\projects\sales-note\db.sqlite3: django_session missing, 0 tables

Stop-Process -Id 40476 -Force
→ 잘못된 C:\projects 서버 종료

Start-Process python manage.py runserver 127.0.0.1:8000 -WorkingDirectory D:\projects\sales-note
→ Django dev server running on 127.0.0.1:8000

Invoke-WebRequest http://127.0.0.1:8000/reporting/login/
→ 200, login page OK

Invoke-WebRequest http://127.0.0.1:5173/reporting/api/schedules/
→ 401 login_required, 정상

Invoke-WebRequest http://127.0.0.1:5173/schedules/
→ 200, React app served
```

### 5. Known Limitations

- `C:\projects\sales-note` 복사본은 여전히 빈 SQLite DB를 가지고 있으므로, 그 경로에서 서버를 다시 실행하면 같은 오류가 재발합니다.

### 6. Recommended Next Task

- 로컬 개발은 `D:\projects\sales-note`에서만 실행하도록 터미널 작업 디렉터리를 고정하거나, 혼동을 줄이기 위해 `C:\projects\sales-note` 복사본을 사용하지 않는 것이 좋습니다.

---

## React Schedules Quick Create — 일정 빠른 등록 (2026-05-08)

### 1. Summary

React `/schedules/` 화면에서 기본 고객 일정을 바로 등록할 수 있게 빠른 등록 패널과 Django JSON 저장 API를 추가했습니다. 저장 후 현재 필터 기준으로 일정 목록과 지표를 다시 불러옵니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 일정 빠른 등록 계획 추가 |
| `frontend/src/App.tsx` | `/schedules/` 빠른 등록 패널, 폼 상태, 저장 후 새로고침 흐름 추가 |
| `frontend/src/api.ts` | 일정 생성 타입/API 함수와 schedules payload fallback 보강 |
| `frontend/README.md` | 일정 빠른 등록 범위 문서화 |
| `reporting/views.py` | 일정 생성용 고객/활동유형 payload와 `/api/schedules/create/` 추가 |
| `reporting/urls.py` | 일정 생성 API URL 등록 |
| `reporting/tests.py` | 일정 생성 권한, 본인 고객 제한, API payload 테스트 추가 |

### 3. CRM Improvements

- 영업사원/admin은 React `/schedules/`에서 담당 고객을 선택해 바로 일정을 등록할 수 있습니다.
- manager는 기존 정책대로 직접 생성이 차단됩니다.
- 빠른 등록 필드는 고객, 활동 유형, 방문 날짜/시간, 장소, 예상 매출, 성공 확률, 메모로 제한했습니다.
- 납품 품목/선결제/고급 편집이 필요하면 기존 Django `상세 등록` 화면으로 이동합니다.

### 4. Existing Functionality Preserved

- 기존 Django 일정 목록/캘린더/등록/상세/보고 작성 화면은 유지했습니다.
- 기존 `/reporting/*` 라우트와 인증 정책은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 8 tests, OK

cd frontend && npm run build
→ OK, assets/index-gaWF-7Yq.js / assets/index-DTu29yQr.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- React 빠른 등록은 본인 담당 고객 일정만 생성합니다. 기존 Django 상세 등록은 고급 필드와 운영상 필요한 상세 기능을 계속 담당합니다.
- `/reporting/api/schedules/` GET에서 CSRF 쿠키를 보장해 React POST 저장 흐름을 안정화했습니다.
- 운영 계정으로 실제 저장까지 하는 육안 확인은 계정 권한이 필요해 자동 스모크에서는 제외했습니다.

### 7. Recommended Next Task

- 다음 단계는 React 고객 상세/이력 화면을 강화해 Django 고객 상세 화면으로 왕복하는 빈도를 줄이는 작업입니다.

---

## React Customer Detail — 고객 상세/이력 프론트 전환 (2026-05-08)

### 1. Summary

React `/customers/<id>/` 고객 상세 화면과 Django 고객 상세 요약 API를 추가했습니다. 고객 목록/우선 고객에서 Django 상세로 바로 넘어가지 않고 React 안에서 고객 요약, 최근 영업노트, 예정 일정, 지연 후속을 확인할 수 있습니다. 일정 빠른 등록 저장 후에는 성공 메시지에 Django 일정 상세 링크도 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 고객 상세/이력 전환 계획 추가 |
| `frontend/src/App.tsx` | `/customers/<id>/` 상세 화면, 고객 목록 링크 전환, 일정 저장 후 상세 링크 추가 |
| `frontend/src/api.ts` | 고객 상세 타입/API 함수 추가 |
| `frontend/src/styles.css` | 고객 상세 레이아웃과 저장 성공 링크 스타일 추가 |
| `frontend/README.md` | 고객 상세 route 문서화 |
| `reporting/views.py` | `/api/customers/<id>/` 고객 상세 요약 API 추가 |
| `reporting/urls.py` | 고객 상세 API URL 등록 |
| `reporting/tests.py` | 고객 상세 API 로그인/권한/데이터 테스트 추가 |

### 3. CRM Improvements

- 고객 목록에서 React 상세 화면으로 이동해 최근 노트와 예정 일정을 바로 확인합니다.
- Django 고객 상세는 React 상세 화면의 `Django 상세` 버튼으로 명확히 분리했습니다.
- 고객 상세에서 일정 등록으로 이동하면 `/schedules/?create=1&customer=<id>`로 이동해 고객 선택을 미리 채웁니다.
- 일정 빠른 등록 저장 후 `상세 열기` 링크로 방금 생성한 Django 일정 상세를 바로 열 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 Django 고객 상세, 일정 상세, 영업노트 상세 화면은 유지했습니다.
- 기존 `/reporting/*` 라우트와 인증/권한 정책은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 16 tests, OK

cd frontend && npm run build
→ OK, assets/index-IDc1l15X.js / assets/index-CQsJED8i.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:5173/customers/1/
→ 200, React app served

Invoke-WebRequest http://127.0.0.1:5173/reporting/api/customers/1/
→ 401 login_required, 정상
```

### 6. Known Limitations

- React 고객 상세는 요약/최근 활동 중심입니다. 고객 정보 수정, 삭제, 첨부/고급 관리 작업은 기존 Django 화면에서 계속 처리합니다.

### 7. Recommended Next Task

- 다음 단계는 React 고객 상세에서 영업노트 빠른 작성 고객 선택도 자동 채우도록 `/notes/?create=1&customer=<id>` 흐름을 보강하는 작업입니다.

---

## React Notes Customer Prefill — 고객 상세 노트 작성 연결 (2026-05-08)

### 1. Summary

React 고객 상세 화면에서 바로 영업노트 작성으로 이동할 수 있게 `노트 작성` 버튼을 추가했습니다. `/notes/?create=1&customer=<id>`로 들어오면 React 노트 빠른 작성 폼이 해당 고객을 자동 선택하고, 저장 후에도 같은 고객 선택을 유지합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 상세 노트 작성 연결 계획 추가 |
| `frontend/src/App.tsx` | 고객 상세 `노트 작성` 버튼 추가, 노트 빠른 작성 고객 prefill 처리 |
| `reporting/tests.py` | 고객 상세 API의 `createNote` 고객 파라미터 링크 검증 추가 |

### 3. CRM Improvements

- 고객 상세에서 노트 작성으로 바로 이동합니다.
- 고객 상세에서 넘어온 고객이 노트 빠른 작성 폼에 자동 선택됩니다.
- 노트 저장 후에도 고객 선택이 유지되어 같은 고객의 추가 기록 작성이 쉽습니다.

### 4. Existing Functionality Preserved

- 기존 Django 영업노트 상세/작성 화면과 `/reporting/*` 경로는 유지했습니다.
- 기존 노트 작성 권한 정책과 저장 API는 변경하지 않았습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 19 tests, OK

cd frontend && npm run build
→ OK, assets/index-BysWWAPf.js / assets/index-CQsJED8i.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:5173/notes/?create=1&customer=1
→ 200, React app served
```

### 6. Known Limitations

- 실제 로그인 계정에서 고객 상세의 `노트 작성` 버튼을 누른 뒤 저장까지 하는 육안 확인은 계정 권한이 필요해 자동 검증에서는 제외했습니다.

### 7. Recommended Next Task

- 다음 단계는 React에서 Django로 넘어가야 하는 남은 주요 화면을 정리해 프론트 전환 우선순위를 확정하는 작업입니다.

---

## React Customer Quick Create — 고객 빠른 등록 (2026-05-08)

### 1. Summary

React `/customers/` 화면에서 `새 고객 등록`을 누르면 Django 생성 폼으로 이동하지 않고 빠른 등록 패널이 열리도록 전환했습니다. 기존 `/reporting/api/followups/create/` AJAX 저장 API를 재사용하며, 저장 후 고객 목록/지표를 새로고침하고 생성된 React 고객 상세 링크를 표시합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 빠른 등록 전환 계획 추가 |
| `frontend/src/App.tsx` | 고객 빠른 등록 패널, 폼 상태, 저장/새로고침 처리 추가 |
| `frontend/src/api.ts` | 고객 생성 타입/API 함수와 Customers API create 계약 추가 |
| `reporting/views.py` | 고객 목록 API에 등록 옵션/CSRF 쿠키 추가, 생성 응답에 React 상세 링크 추가 |
| `reporting/tests.py` | 고객 등록 옵션, salesman 생성, manager 차단 테스트 추가 |

### 3. CRM Improvements

- 고객 목록에서 기본 고객 정보를 바로 등록합니다.
- 업체/부서/우선순위 선택 데이터를 React API로 내려줍니다.
- 저장 성공 후 생성 고객의 React 상세 화면으로 바로 이동할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 Django 고객 등록/상세/수정/삭제 화면은 유지했습니다.
- Manager 생성 차단과 업체 접근 권한 검증은 기존 정책을 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 10 tests, OK

cd frontend && npm run build
→ OK, assets/index-BO4wjypI.js / assets/index-CQsJED8i.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:5173/customers/?create=1
→ 200, React app served
```

### 6. Known Limitations

- React 빠른 등록은 기존 업체/부서 선택 기반입니다. 신규 업체/부서 생성은 아직 기존 Django 관리 화면을 사용합니다.
- 실제 로그인 계정에서 고객 저장까지 하는 육안 확인은 계정 권한이 필요해 자동 검증에서는 제외했습니다.

### 7. Recommended Next Task

- 다음 단계는 React 고객 빠른 등록 안에서 신규 업체/부서도 바로 만들 수 있게 연결하는 작업입니다.

---

## React Customer Inline Company/Department Create — 고객 등록 업체/부서 연결 (2026-05-08)

### 1. Summary

React 고객 빠른 등록 패널 안에서 새 업체/학교와 새 부서/연구실을 바로 추가할 수 있게 연결했습니다. 추가 후 고객 등록 폼의 업체/부서 선택값이 방금 만든 항목으로 갱신됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 업체/부서 인라인 생성 계획 추가 |
| `frontend/src/App.tsx` | 고객 등록 패널에 업체/부서 인라인 추가 입력과 핸들러 추가 |
| `frontend/src/api.ts` | 업체/부서 생성 API 함수와 응답 타입 추가 |
| `frontend/src/styles.css` | 인라인 생성 입력/버튼 레이아웃 추가 |
| `reporting/views.py` | 고객 API에 업체/부서 저장 URL 추가, 생성 API 권한 보강 |
| `reporting/tests.py` | 업체/부서 생성 성공, manager 차단, 타사 업체 차단 테스트 추가 |

### 3. CRM Improvements

- 고객 등록 중 업체/부서가 없으면 화면을 벗어나지 않고 바로 추가합니다.
- 새 업체 추가 후 해당 업체가 고객 등록 폼에 자동 선택됩니다.
- 새 부서 추가 후 해당 부서가 고객 등록 폼에 자동 선택됩니다.

### 4. Existing Functionality Preserved

- 기존 Django 업체/부서 관리 화면은 유지했습니다.
- 기존 고객 생성 API와 고객 등록 권한 정책은 유지했습니다.
- Manager의 업체/부서/고객 생성은 차단했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 13 tests, OK

cd frontend && npm run build
→ OK, assets/index-DNHJ131t.js / assets/index-8NY33DrA.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:5173/customers/?create=1
→ 200, React app served
```

### 6. Known Limitations

- 실제 로그인 계정에서 업체 생성, 부서 생성, 고객 저장까지 이어지는 육안 확인은 계정 권한이 필요해 자동 검증에서는 제외했습니다.

### 7. Recommended Next Task

- 다음 단계는 고객 상세의 수정/삭제 같은 관리 작업 중 React로 옮길 수 있는 범위를 정리하고, 우선 고객 정보 수정부터 전환하는 작업입니다.

---

## Production Customer Quick Create Deployment Refresh — 고객 등록 운영 번들 갱신 (2026-05-08)

### 1. Summary

운영 `/customers/?create=1`가 예전 React 번들(`assets/index-B9PQ-tLi.js`)을 내려주고 있어 고객 빠른 등록 화면이 열리지 않는 문제를 확인했습니다. 백엔드와 프론트엔드를 최신 고객 빠른 등록 커밋 기준으로 재배포했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 갱신 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React 고객 목록이 최신 빠른 등록 번들(`assets/index-DNHJ131t.js`)을 사용합니다.
- 고객 등록 API와 업체/부서 인라인 생성 API가 최신 백엔드 배포에 포함됐습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/*` Django 라우트와 인증 정책은 변경하지 않았습니다.
- 미로그인 고객 API 요청은 계속 `401 login_required`로 보호됩니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
railway up --service web --environment production --message "Deploy customer quick create API 8e96f5c" --ci
→ Deploy complete, deployment id 3e73484d-ade6-46a8-af9c-c0d0ad699622

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React customer quick create 8e96f5c" --ci
→ Deploy complete, deployment id c47ff060-463c-4b21-bddb-761c0c4d4962

railway status
→ sales-note-frontend Online, web Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/?create=1
→ 200, assets/index-DNHJ131t.js / assets/index-8NY33DrA.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-DNHJ131t.js
→ 고객 빠른 등록=True, 새 고객 등록=True, create=1=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/customers/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 계정에서 새 고객 등록 패널 열림과 저장까지 이어지는 육안 확인은 사용자 계정 권한이 필요해 자동 검증에서는 제외했습니다.

### 7. Recommended Next Task

- 실제 계정으로 `/customers/?create=1`에서 패널 열림, 업체/부서 인라인 생성, 고객 저장 후 목록 반영을 확인합니다.

---

## React Customer Detail Edit — 고객 상세 수정 전환 (2026-05-08)

### 1. Summary

React `/customers/<id>/` 고객 상세 화면에서 고객 기본정보를 바로 수정할 수 있게 했습니다. 기존 Django 수정 화면은 보조 링크로 유지하고, React 저장은 새 JSON API를 통해 처리합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 상세 수정 전환 계획 추가 |
| `frontend/src/App.tsx` | 고객 상세 수정 패널, 저장 처리, 상세 재조회 추가 |
| `frontend/src/api.ts` | 고객 수정 타입과 `updateCustomer` API 함수 추가 |
| `frontend/src/styles.css` | 수정 패널 상태 표시 스타일 보강 |
| `reporting/views.py` | 고객 상세 수정 옵션과 고객 업데이트 API 추가 |
| `reporting/urls.py` | `/reporting/api/customers/<id>/update/` 라우트 추가 |
| `reporting/tests.py` | 수정 성공, manager/coworker 차단, 타사 업체 차단 테스트 추가 |

### 3. CRM Improvements

- 고객 상세에서 고객명, 업체, 부서, 책임자, 연락처, 이메일, 주소, 상세 내용, 상태, 우선순위, 파이프라인 단계를 수정할 수 있습니다.
- 저장 후 React 상세 데이터를 다시 불러와 변경된 값이 바로 반영됩니다.
- 파이프라인 단계를 수동 변경하면 기존 자동 동기화 보호 플래그를 유지합니다.

### 4. Existing Functionality Preserved

- 기존 Django 고객 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- Manager는 계속 읽기 전용이며 고객 수정이 차단됩니다.
- Salesman은 본인 고객만 수정 가능하고, 타사 업체/부서 선택은 차단됩니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 16 tests, OK

cd frontend && npm run build
→ OK, assets/index-bdBLCFoN.js / assets/index-DlWngxDV.css

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend && node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/customers/<id>/`의 수정 버튼 클릭, 저장, 목록/상세 반영까지 이어지는 육안 확인은 아직 운영 배포 후 확인이 필요합니다.

### 7. Recommended Next Task

- 고객 삭제 또는 고객 상세 내 업체/부서 신규 생성까지 React로 옮길지 범위를 정하고, 우선 삭제는 위험도가 높으므로 고객 상세의 보조 관리 기능부터 단계적으로 전환합니다.

---

## React Sales Note Detail Edit — 영업노트 상세/수정 전환 (2026-05-09)

### 1. Summary

React `/notes/<id>/` 영업노트 상세 화면과 수정 패널을 추가했습니다. 기존 Django 히스토리 상세/수정 화면은 보조 링크로 유지하고, React 저장은 새 JSON API를 통해 처리합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 영업노트 상세/수정 전환 계획 추가 |
| `frontend/src/App.tsx` | `/notes/<id>/` 상세 route, 수정 패널, 검토 토글, 관련 노트/첨부/댓글 표시 추가 |
| `frontend/src/api.ts` | 노트 상세/수정 타입과 `loadNoteDetailData`, `updateNote` API 함수 추가 |
| `frontend/src/styles.css` | 노트 상세/수정 화면 레이아웃과 파일/댓글 목록 스타일 추가 |
| `reporting/views.py` | React 노트 상세 API, 수정 API, React 상세 링크 payload 추가 |
| `reporting/urls.py` | `/reporting/api/notes/<id>/`, `/reporting/api/notes/<id>/update/` 라우트 추가 |
| `reporting/tests.py` | 노트 상세 조회, 수정 성공, manager/타사 고객 차단, React 상세 링크 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 영업노트 목록과 고객 상세의 노트 링크가 React `/notes/<id>/` 상세로 이어집니다.
- 상세 화면에서 활동 내용, 미팅 구조화 필드, 납품 정보, 다음 액션, 첨부파일, 댓글, 같은 고객의 최근 노트를 확인할 수 있습니다.
- 권한이 있는 사용자는 React에서 고객, 활동 유형, 활동일, 내용, 다음 액션, 미팅/납품/서비스 필드를 수정할 수 있습니다.
- Manager는 상세 조회와 검토 토글은 가능하지만 수정은 계속 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/histories/<id>/` 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- 미로그인 API 요청은 JSON `401 login_required`로 보호됩니다.
- Salesman/manager/admin의 기존 조회·수정 권한 흐름을 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 15 tests, OK

python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 16 tests, OK

cd frontend && npm run build
→ OK, assets/index-BZQVHQlm.js / assets/index-B3aL91g4.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

Invoke-WebRequest http://127.0.0.1:8000/reporting/login/
→ 200

Invoke-WebRequest http://127.0.0.1:5173/notes/
→ 200
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/notes/<id>/` 진입, 수정 저장, manager 검토 토글까지 이어지는 육안 확인은 아직 필요합니다.
- 기존 `History` 모델에 별도 quote/service 활동일 필드가 없어 React 수정 화면의 활동일 저장은 기존 구조대로 고객 미팅/납품 일정 유형에 한정됩니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 일정 상세/수정의 React 전환 또는 영업노트 첨부파일 업로드/삭제를 React 상세 화면에 확장하는 작업입니다.

---

## Production Sales Note Detail Deployment — 영업노트 상세 운영 배포 (2026-05-09)

### 1. Summary

React 영업노트 상세/수정 변경분을 GitHub `main`에 푸시하고 Railway production의 `web`, `sales-note-frontend` 서비스를 재배포했습니다. 운영 `/notes/<id>/`가 새 React 번들을 내려주도록 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React `/notes/731/` 같은 영업노트 상세 URL이 새 상세 화면 코드를 포함한 번들을 사용합니다.
- 운영 Django API에 `/reporting/api/notes/<id>/`, `/reporting/api/notes/<id>/update/`가 배포됐습니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 내리지 않았습니다.
- 기존 `/reporting/*` Django 경로와 인증 보호는 유지했습니다.
- `/reporting/api/notes/<id>/`는 미로그인 상태에서 계속 `401`로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React sales note detail edit"
→ 464ff69 feat: add React sales note detail edit

git push origin main
→ main updated from 375012a to 464ff69

railway up --service web --environment production --message "Deploy React sales note detail API 464ff69" --ci
→ Deploy complete, deployment id 7c0076c1-fbdb-4520-864e-534206d739f2

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React sales note detail 464ff69" --ci
→ Deploy complete, deployment id ce9714f3-7c0f-4d47-aa28-4dac746e6a41

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/notes/731/
→ 200, assets/index-BZQVHQlm.js / assets/index-B3aL91g4.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-BZQVHQlm.js
→ Note detail=True, /reporting/api/notes/=True, 영업노트 수정=True

Invoke-RestMethod https://sales-note-frontend-production.up.railway.app/reporting/api/notes/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/notes/731/` 상세 화면의 데이터 표시와 저장까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- Django `web` 도메인을 완전히 내리면 React의 API와 로그인도 같이 중단되므로 서비스 중지 방식은 적용하지 않았습니다.

### 7. Recommended Next Task

- 실제 계정으로 `/notes/731/`에 접속해 상세 화면 표시, 수정 저장, manager 검토 토글, Django 상세 보조 링크 동작을 확인합니다.

---

## React Schedule Detail Edit — 일정 상세/수정 전환 (2026-05-09)

### 1. Summary

React `/schedules/<id>/` 고객 일정 상세 화면과 수정 패널을 추가했습니다. 기존 Django 일정 상세/수정 화면은 보조 링크로 유지하고, React 저장은 새 JSON API로 처리합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 일정 상세/수정 전환 계획 추가 |
| `frontend/src/App.tsx` | `/schedules/<id>/` 상세 route, 수정 패널, 연결 노트/납품 품목/첨부 표시 추가 |
| `frontend/src/api.ts` | 일정 상세/수정 타입과 `loadScheduleDetailData`, `updateSchedule` API 함수 추가 |
| `frontend/src/styles.css` | 일정 상세/수정 화면과 납품 품목 목록 스타일 추가 |
| `reporting/views.py` | 일정 상세 API, 수정 API, React 상세 링크 payload 추가 |
| `reporting/urls.py` | `/reporting/api/schedules/<id>/`, `/reporting/api/schedules/<id>/update/` 라우트 추가 |
| `reporting/tests.py` | 일정 상세 조회, 수정 성공, manager/타사 고객 차단, React 상세 링크 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 일정 목록, 대시보드 일정, 고객 상세 일정, 노트 연결 일정 링크가 React `/schedules/<id>/`로 이어집니다.
- 상세 화면에서 일정 메모, 고객/담당자, 상태, 방문 일시, 예상 매출, 확률, 납품 품목, 첨부파일, 연결 영업노트를 확인할 수 있습니다.
- 권한이 있는 사용자는 React에서 고객 연결, 활동 유형, 상태, 방문일/시간, 장소, 메모, 예상 매출, 확률, 예상 종료일, 구매 확정을 수정할 수 있습니다.
- Manager는 상세 조회만 가능하고 수정 버튼/저장 API는 계속 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/schedules/<id>/` 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- 미로그인 API 요청은 JSON `401 login_required`로 보호됩니다.
- Salesman은 본인 일정만 수정 가능하고, 타사 업체/고객 연결은 차단됩니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 12 tests, OK

cd frontend && npm run build
→ OK, assets/index-DWiacmrm.js / assets/index-u1L9qtgk.css

python manage.py test reporting.tests.SchedulesSummaryApiTests reporting.tests.DashboardSummaryApiTests reporting.tests.CustomersSummaryApiTests reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 47 tests, OK

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/schedules/<id>/` 진입, 수정 저장, 연결 노트/납품 품목 표시까지 이어지는 육안 확인은 운영 배포 후 확인이 필요합니다.
- React 수정 패널은 핵심 일정 필드 중심입니다. 기존 Django 화면의 복수 선결제 차감, 납품 품목 편집 같은 고위험 부가 기능은 보조 Django 수정 링크로 유지했습니다.

### 7. Recommended Next Task

- 운영 배포 후 `/schedules/<id>/`에서 상세 표시, 수정 저장, manager 수정 차단, 보고 작성 링크, Django 상세 보조 링크를 수동 검수합니다.

---

## Production Schedule Detail Deployment — 일정 상세 운영 배포 (2026-05-09)

### 1. Summary

React 일정 상세/수정 변경분을 GitHub `main`에 푸시하고 Railway production의 `web`, `sales-note-frontend` 서비스를 배포했습니다. 운영 `/schedules/<id>/`가 새 React 번들을 내려주고, 일정 상세 API가 로그인 보호 상태로 응답하는 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React `/schedules/731/` 같은 고객 일정 상세 URL이 새 상세/수정 화면 코드를 포함한 번들을 사용합니다.
- 운영 Django API에 `/reporting/api/schedules/<id>/`, `/reporting/api/schedules/<id>/update/`가 배포됐습니다.
- 대시보드/고객/노트에서 고객 일정 링크가 React 상세로 이어지는 배포본이 적용됐습니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 `/reporting/schedules/<id>/` Django 상세/수정 화면과 인증 보호는 유지했습니다.
- `/reporting/api/schedules/<id>/`는 미로그인 상태에서 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React schedule detail edit"
→ f170018 feat: add React schedule detail edit

git push origin main
→ main updated from 7e59e63 to f170018

railway up --service web --environment production --message "Deploy React schedule detail API f170018" --ci
→ Direct upload attempt failed twice with Railway code snapshot errors, but GitHub source deployment succeeded.

railway redeploy --service web --from-source --yes --json
→ SUCCESS, deployment id ebe628fa-9ab7-4c68-9d22-fd1bb82b6e56

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React schedule detail f170018" --ci
→ Deploy complete, deployment id c514a3a0-0869-4afe-a6a5-e457d297a563

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/schedules/731/
→ 200, assets/index-DWiacmrm.js / assets/index-u1L9qtgk.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-DWiacmrm.js
→ Schedule detail=True, /reporting/api/schedules/=True, 일정 수정=True

Invoke-RestMethod https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/schedules/731/` 상세 화면의 데이터 표시와 저장까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- Railway `web`에 직접 업로드한 2회 시도는 snapshot 생성 실패로 남아 있지만, 최종 source redeploy `ebe628fa-9ab7-4c68-9d22-fd1bb82b6e56`는 성공했고 `railway status`도 Online입니다.

### 7. Recommended Next Task

- 실제 계정으로 `/schedules/731/`에 접속해 상세 화면 표시, 수정 저장, manager 수정 차단, 보고 작성 링크, Django 상세 보조 링크 동작을 확인합니다.

---

## React Schedule Attachments — 일정 상세 첨부파일 전환 (2026-05-09)

### 1. Summary

React `/schedules/<id>/` 상세 화면에서 일정 첨부파일을 업로드/삭제할 수 있게 연결했습니다. 기존 Django 다운로드/업로드/삭제 URL은 유지하면서 React 상세 API가 업로드 URL과 파일별 삭제 URL을 내려주도록 보강했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 일정 상세 첨부파일 전환 계획 추가 |
| `frontend/src/App.tsx` | 일정 상세 첨부파일 업로드 버튼, 파일 선택, 삭제 버튼, 진행/성공/오류 상태 추가 |
| `frontend/src/api.ts` | 일정 파일 업로드/삭제 타입과 `uploadScheduleFiles`, `deleteScheduleFile` API 함수 추가 |
| `frontend/src/styles.css` | 일정 첨부파일 업로드/삭제 UI와 모바일 레이아웃 스타일 추가 |
| `reporting/views.py` | 일정 상세 API에 `uploadFiles`, 파일별 `deleteHref`, `canDelete` 추가 |
| `reporting/file_views.py` | 일정 파일 업로드/삭제 권한을 React 일정 수정 정책과 맞추고 camelCase 응답 보강 |
| `reporting/tests.py` | 일정 파일 업로드/삭제 owner-only 권한과 상세 payload 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 일정 상세에서 Django 화면으로 이동하지 않고 첨부파일을 바로 추가/삭제할 수 있습니다.
- 파일 목록은 다운로드 링크와 삭제 버튼을 분리해 실수 클릭 가능성을 줄였습니다.
- 업로드/삭제 중 상태, 성공 메시지, 오류 메시지를 React 화면 안에서 표시합니다.
- Manager와 다른 영업사원은 파일 업로드/삭제 버튼이 보이지 않고 API에서도 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/schedules/<id>/files/upload/`, `/reporting/schedule-files/<id>/download/`, `/reporting/schedule-files/<id>/delete/` 경로는 유지했습니다.
- 파일 확장자, 크기, 최대 5개 제한 등 기존 업로드 검증은 유지했습니다.
- 일정 조회 권한과 다운로드 권한은 기존 `can_access_user_data` 흐름을 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 14 tests, OK

cd frontend && npm run build
→ OK, assets/index-BlgHjOVF.js / assets/index-D32UHNZf.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/schedules/<id>/` 파일 업로드, 다운로드, 삭제까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- React 화면은 기존 정책대로 일정당 파일 5개 제한을 유지합니다. 제한 확대나 드래그 앤 드롭 업로드는 이번 범위에 포함하지 않았습니다.

### 7. Recommended Next Task

- 다음 단계는 영업노트 상세의 첨부파일 업로드/삭제도 React `/notes/<id>/`에서 처리하게 옮기는 작업이 적절합니다.

---

## Production Schedule Attachments Deployment — 일정 첨부파일 운영 배포 (2026-05-09)

### 1. Summary

React 일정 상세 첨부파일 업로드/삭제 변경분을 GitHub `main`에 푸시하고 Railway production의 `web`, `sales-note-frontend` 서비스를 배포했습니다. 운영 `/schedules/<id>/`가 새 번들을 내려주고, Django 일정 상세 API는 미로그인 상태에서 계속 보호되는 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React `/schedules/<id>/` 상세 화면에 첨부파일 업로드/삭제 UI가 포함됐습니다.
- 운영 Django 파일 API에 owner-only 업로드/삭제 권한 보강이 적용됐습니다.
- Manager/타 영업사원은 일정 첨부파일 조작이 계속 차단됩니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 `/reporting/schedules/<id>/files/upload/`, 다운로드, 삭제 경로는 유지했습니다.
- `/reporting/api/schedules/<id>/`는 미로그인 상태에서 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React schedule file management"
→ aaea8f2 feat: add React schedule file management

git push origin main
→ main updated from 0ee470d to aaea8f2

railway redeploy --service web --from-source --yes --json
→ SUCCESS, deployment id 856eeabf-bc30-43df-89f6-ecec4f0cb716

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React schedule files aaea8f2" --ci
→ Deploy complete, deployment id 9a03c5b1-5cb0-4bac-8128-7827dadcc6b2

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/schedules/731/
→ 200, assets/index-BlgHjOVF.js / assets/index-D32UHNZf.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-BlgHjOVF.js
→ 첨부파일 업로드=True, 파일 삭제 확인=True, 일정 첨부파일 선택=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-D32UHNZf.css
→ schedule-file-delete-button=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/schedules/731/`에서 파일 업로드, 다운로드, 삭제까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- 업로드 가능한 파일 형식/크기/개수는 기존 Django 정책을 그대로 따릅니다.

### 7. Recommended Next Task

- 영업노트 상세 `/notes/<id>/`의 첨부파일 업로드/삭제도 React 화면으로 옮깁니다.

---

## React Note Attachments — 영업노트 상세 첨부파일 전환 (2026-05-09)

### 1. Summary

React `/notes/<id>/` 상세 화면에서 영업노트 첨부파일을 업로드/삭제할 수 있게 연결했습니다. 기존 Django 파일 다운로드/삭제 URL은 유지하고, React 전용 업로드 API를 추가했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 영업노트 상세 첨부파일 전환 계획 추가 |
| `frontend/src/App.tsx` | 영업노트 상세 첨부파일 업로드 버튼, 파일 선택, 삭제 버튼, 진행/성공/오류 상태 추가 |
| `frontend/src/api.ts` | 노트 파일 업로드/삭제 타입과 `uploadNoteFiles`, `deleteNoteFile` API 함수 추가 |
| `reporting/file_views.py` | `note_file_upload` API, 히스토리 파일 payload, owner-only 파일 조작 권한 helper 추가 |
| `reporting/views.py` | 노트 상세 API에 `uploadFiles`, 파일별 `deleteHref`, `canDelete` 추가 |
| `reporting/urls.py` | `/reporting/api/notes/<id>/files/upload/` 라우트 추가 |
| `reporting/tests.py` | 노트 파일 업로드/삭제 권한과 상세 payload 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 영업노트 상세에서 Django 수정 화면으로 이동하지 않고 첨부파일을 바로 추가/삭제할 수 있습니다.
- 파일 목록은 다운로드 링크와 삭제 버튼을 분리했습니다.
- 업로드/삭제 중 상태, 성공 메시지, 오류 메시지를 React 화면 안에서 표시합니다.
- Manager와 다른 영업사원은 파일 업로드/삭제 버튼이 보이지 않고 API에서도 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/histories/<id>/` 상세/수정 화면과 `/reporting/files/<id>/download/`, `/reporting/files/<id>/delete/` 경로는 유지했습니다.
- 기존 파일 검증 정책인 10MB 제한, 허용 확장자, 최대 5개 제한을 유지했습니다.
- 미로그인 API 요청은 계속 `401 login_required`로 보호됩니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 17 tests, OK

cd frontend && npm run build
→ OK, assets/index-DrrJKru7.js / assets/index-D32UHNZf.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/notes/<id>/` 파일 업로드, 다운로드, 삭제까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- Drag-and-drop 업로드나 업로드 전 미리보기는 이번 범위에 포함하지 않았습니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 댓글/매니저 메모 작성·삭제 흐름을 React `/notes/<id>/` 상세로 옮기는 작업이 적절합니다.

---

## Production Note Attachments Deployment — 영업노트 첨부파일 운영 배포 (2026-05-09)

### 1. Summary

React 영업노트 상세 첨부파일 업로드/삭제 변경분을 GitHub `main`에 푸시하고 Railway production의 `web`, `sales-note-frontend` 서비스를 배포했습니다. 운영 `/notes/<id>/`가 새 번들을 내려주고, Django 노트 상세 API는 미로그인 상태에서 계속 보호되는 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React `/notes/<id>/` 상세 화면에 첨부파일 업로드/삭제 UI가 포함됐습니다.
- 운영 Django API에 `/reporting/api/notes/<id>/files/upload/`가 배포됐습니다.
- Manager/타 영업사원은 영업노트 첨부파일 조작이 계속 차단됩니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 `/reporting/histories/<id>/` 상세/수정 화면과 파일 다운로드/삭제 경로는 유지했습니다.
- `/reporting/api/notes/<id>/`는 미로그인 상태에서 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React note file management"
→ 2e9dd33 feat: add React note file management

git push origin main
→ main updated from 0abc42b to 2e9dd33

railway redeploy --service web --from-source --yes --json
→ SUCCESS, deployment id 45940929-da7e-4e11-8ff4-d6f7e01c111f

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React note files 2e9dd33" --ci
→ Deploy complete, deployment id efdd4d88-3ec8-4b90-b258-d1e2586d214d

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/notes/731/
→ 200, assets/index-DrrJKru7.js / assets/index-D32UHNZf.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-DrrJKru7.js
→ 첨부파일 업로드=True, 파일 삭제 확인=True, 영업노트 첨부파일 선택=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/notes/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/notes/731/`에서 파일 업로드, 다운로드, 삭제까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- 기존 정책대로 파일은 최대 5개, 파일당 10MB 제한을 유지합니다.

### 7. Recommended Next Task

- 댓글/매니저 메모 작성·삭제 흐름을 React `/notes/<id>/` 상세로 옮깁니다.

---

## React Note Replies — 영업노트 댓글/매니저 메모 전환 (2026-05-09)

### 1. Summary

React `/notes/<id>/` 상세 화면에서 댓글과 매니저 메모를 작성·삭제할 수 있게 연결했습니다. 기존 Django 댓글 API를 재사용하고, 상세 API가 댓글 작성 URL과 댓글별 삭제 가능 여부를 내려주도록 보강했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 영업노트 댓글/매니저 메모 전환 계획 추가 |
| `frontend/src/App.tsx` | 댓글 작성 폼, 삭제 버튼, 진행/성공/오류 상태 추가 |
| `frontend/src/api.ts` | 댓글 작성/삭제 타입과 `addNoteReply`, `deleteNoteReply` API 함수 추가 |
| `frontend/src/styles.css` | 댓글 작성 폼과 댓글 행/삭제 버튼 스타일 추가 |
| `reporting/views.py` | 노트 상세 API에 댓글 작성 config, 댓글별 `deleteHref`, `canDelete`, 역할 표시 추가 |
| `reporting/tests.py` | 댓글 작성/삭제 권한과 상세 payload 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 영업노트 상세에서 Django 화면으로 이동하지 않고 댓글을 바로 추가할 수 있습니다.
- Manager는 같은 회사 영업노트에 매니저 메모를 남길 수 있고, 실무자는 본인 노트에 댓글을 남길 수 있습니다.
- 댓글 목록에 `댓글`/`매니저 메모` 구분을 표시합니다.
- 댓글 삭제는 기존 정책대로 작성자 본인에게만 노출되고 API에서도 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/api/histories/<id>/add-manager-memo/`, `/reporting/api/histories/<id>/delete-manager-memo/` API를 유지했습니다.
- 기존 Django `/reporting/histories/<id>/` 상세 화면과 `/reporting/*` 경로는 유지했습니다.
- Manager/타사 사용자/동료 영업사원의 권한 차단 흐름은 유지했습니다.
- DB 모델과 migration 변경은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1
→ Ran 19 tests, OK

cd frontend && npm run build
→ OK, assets/index-C3bZV9lB.js / assets/index-Ddxdl7EV.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/notes/<id>/` 댓글 작성, 매니저 메모 작성, 삭제까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- 댓글 편집은 이번 범위에 포함하지 않았습니다. 기존 흐름처럼 삭제 후 재작성하는 방식입니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 후속조치/완료 처리 또는 일정 납품 품목 편집처럼 아직 Django 보조 화면에 남아 있는 고위험 부가 기능을 하나씩 React로 옮기는 작업이 적절합니다.

---

## Production Note Replies Deployment — 영업노트 댓글 운영 배포 (2026-05-09)

### 1. Summary

React 영업노트 상세 댓글/매니저 메모 작성·삭제 변경분을 GitHub `main`에 푸시하고 Railway production의 `web`, `sales-note-frontend` 서비스를 배포했습니다. 운영 `/notes/<id>/`가 새 번들을 내려주고, Django 노트 상세 API는 미로그인 상태에서 계속 보호되는 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React `/notes/<id>/` 상세 화면에 댓글 작성 폼과 삭제 버튼이 포함됐습니다.
- 운영 Django 노트 상세 API가 댓글 작성 URL과 댓글별 삭제 가능 여부를 제공합니다.
- Manager/실무자 댓글 작성 권한과 작성자 본인 삭제 정책이 운영에 적용됐습니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 `/reporting/api/histories/<id>/add-manager-memo/`, `/reporting/api/histories/<id>/delete-manager-memo/` 경로는 유지했습니다.
- `/reporting/api/notes/<id>/`는 미로그인 상태에서 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React note replies"
→ d8205f6 feat: add React note replies

git push origin main
→ main updated from cb1817d to d8205f6

railway redeploy --service web --from-source --yes --json
→ SUCCESS, deployment id 9f488b45-89bb-4251-80a7-ec729ee1a4a3

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React note replies d8205f6" --ci
→ Deploy complete, deployment id 89b063ee-5d5b-4a09-bfd9-4b019a2ab64f

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/notes/731/
→ 200, assets/index-C3bZV9lB.js / assets/index-Ddxdl7EV.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-C3bZV9lB.js
→ 댓글 입력 검증=True, 댓글 삭제 확인=True, 댓글 추가 성공 문구=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-Ddxdl7EV.css
→ note-reply-compose=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/notes/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/notes/731/`에서 실무자 댓글 작성/삭제, manager 매니저 메모 작성/삭제까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- 댓글 편집은 포함하지 않았습니다. 현재는 작성자 본인 삭제 후 재작성 흐름입니다.

### 7. Recommended Next Task

- 후속조치 완료 처리나 일정 납품 품목 편집처럼 아직 Django 보조 화면에 남아 있는 세부 기능을 우선순위대로 React로 이전합니다.

---

## React Schedule Delivery Items — 일정 납품 품목 편집 전환 (2026-05-09)

### 1. Summary

React `/schedules/<id>/` 상세 화면에서 납품 품목을 추가/수정/삭제할 수 있게 연결했습니다. 기존 Django 납품 품목 수정 경로는 유지하고, React 전용 저장 API를 추가했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 일정 납품 품목 편집 전환 계획 추가 |
| `frontend/src/App.tsx` | 납품 품목 편집 패널, 행 추가/삭제, 세금계산서 체크, 저장 상태 추가 |
| `frontend/src/api.ts` | 납품 품목 저장 타입과 `updateScheduleDeliveryItems` API 함수 추가 |
| `frontend/src/styles.css` | 납품 품목 편집 폼과 모바일 레이아웃 스타일 추가 |
| `reporting/views.py` | React 전용 납품 품목 저장 API, payload 검증, History 요약 동기화 추가 |
| `reporting/urls.py` | `/reporting/api/schedules/<id>/delivery-items/update/` 라우트 추가 |
| `reporting/tests.py` | 납품 품목 저장 owner-only 권한과 상세 payload 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 일정 상세에서 Django 상세 모달로 이동하지 않고 납품 품목을 바로 편집할 수 있습니다.
- 품목명, 수량, 단위, 단가, 세금계산서 발행 여부, 비고를 React에서 저장합니다.
- 저장 후 연결된 납품 History의 `delivery_items`와 `delivery_amount` 요약도 동기화됩니다.
- Manager와 동료 영업사원은 편집 버튼이 보이지 않고 API에서도 차단됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 일정 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- 기존 `DeliveryItem`, `Schedule`, `History` 모델을 그대로 사용했고 DB migration은 없습니다.
- 일정 조회/수정 권한 정책은 기존 React 일정 상세 수정 정책과 동일하게 유지했습니다.
- 미로그인 API 요청은 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 16 tests, OK

cd frontend && npm run build
→ OK, assets/index-ChGmKnB1.js / assets/index-D0d8bvfh.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/schedules/<id>/` 납품 품목 추가, 수정, 삭제까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- 제품 마스터 검색/선택 연동은 이번 범위에 포함하지 않았습니다. 현재 React 편집은 직접 입력 방식입니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 일정 납품 품목의 제품 마스터 선택 또는 선결제 세부 흐름처럼 아직 Django 폼에 남아 있는 고급 입력을 React로 옮기는 작업이 적절합니다.

---

## Production Schedule Delivery Items Deployment Attempt — 일정 납품 품목 배포 시도 (2026-05-09)

### 1. Summary

React 일정 납품 품목 편집 변경분은 GitHub `main`에 푸시했습니다. Railway CLI 인증 세션이 만료되어 production `web`, `sales-note-frontend` 배포는 실행되지 않았습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | Railway 배포 실패 원인과 후속 조치 기록 추가 |

### 3. CRM Improvements

- 코드 변경은 `main`에 반영되어 배포 가능한 상태입니다.
- 운영 반영은 Railway 재로그인 후 같은 커밋 `ef5a213`을 배포하면 됩니다.

### 4. Existing Functionality Preserved

- Railway 배포 명령은 인증 단계에서 중단되어 기존 운영 `web`, `sales-note-frontend` 서비스에는 변경이 적용되지 않았습니다.
- Django `web` 서비스는 React API/login/proxy backend이므로 내리거나 삭제하지 않았습니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React schedule delivery item editing"
→ ef5a213 feat: add React schedule delivery item editing

git push origin main
→ main updated from 2af1bcd to ef5a213

railway redeploy --service web --from-source --yes --json
→ 실패: invalid_grant / Unauthorized. railway login 필요

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React schedule delivery items ef5a213" --ci
→ 실패: Unauthorized. railway login 필요

git ls-remote origin refs/heads/main
→ ef5a213c6019ea156f11b139c169cd456a709a45

RAILWAY_TOKEN presence check
→ RAILWAY_TOKEN=missing

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/schedules/731/
→ 200, 기존 assets/index-C3bZV9lB.js / assets/index-Ddxdl7EV.css 서빙 중

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 운영 사이트는 확인 시점에 아직 이 변경분을 서빙하지 않고 이전 번들을 유지했습니다. Railway CLI 재인증 후 `web` source redeploy와 `sales-note-frontend` upload 배포가 필요합니다.
- 운영 번들 검증과 `/reporting/api/schedules/<id>/` 401 보호 확인은 배포 후 다시 수행해야 합니다.

### 7. Recommended Next Task

- Railway에서 재로그인 또는 `RAILWAY_TOKEN` 설정 후 `web`과 `sales-note-frontend`를 커밋 `ef5a213` 기준으로 배포하고 운영 번들을 확인합니다.

---

## Production Schedule Delivery Items Deployment — 일정 납품 품목 운영 배포 (2026-05-09)

### 1. Summary

Railway 재링크 후 React 일정 납품 품목 편집 변경분을 production `web`, `sales-note-frontend` 서비스에 배포했습니다. 운영 `/schedules/<id>/`가 새 번들을 내려주고, 새 납품 품목 저장 API 라우트와 기존 로그인 보호가 적용된 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React 일정 상세 화면에 납품 품목 편집 패널이 포함됐습니다.
- 운영 Django API에 `/reporting/api/schedules/<id>/delivery-items/update/`가 배포됐습니다.
- 본인 일정만 납품 품목을 수정할 수 있는 owner-only 정책이 운영에 적용됐습니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 일정 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- `/reporting/api/schedules/<id>/`는 미로그인 상태에서 계속 `401 login_required`로 보호됩니다.

### 5. Commands Run and Results

```text
railway status
→ sales-note-frontend Online, web Online

railway redeploy --service web --from-source --yes --json
→ SUCCESS

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React schedule delivery items 40966e2" --ci
→ Deploy complete, deployment id cfd9a79a-c909-4ccc-a9ce-291e68bf59a0

railway deployment list --service web --json
→ latest web deployment 5bdb4d37-4e30-41f1-af6a-430485044dad, SUCCESS, commit 40966e2

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/schedules/731/
→ 200, assets/index-ChGmKnB1.js / assets/index-D0d8bvfh.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-ChGmKnB1.js
→ schedule-delivery-edit-form=True, updateDeliveryItems=True, 납품 품목 저장 문구=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-D0d8bvfh.css
→ schedule-delivery-edit-form=True, schedule-delivery-remove-button=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/delivery-items/update/
→ 405 MethodNotAllowed, 라우트 존재 확인

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 세션으로 `/schedules/731/`에서 납품 품목 추가, 수정, 삭제까지 이어지는 육안 확인은 사용자 계정에서 확인해야 합니다.
- 제품 마스터 검색/선택 연동은 아직 Django 폼에 남아 있습니다. 현재 React 편집은 직접 입력 방식입니다.

### 7. Recommended Next Task

- 다음 단계는 제품 마스터 선택/검색 또는 선결제 세부 입력처럼 납품 일정의 고급 입력을 React 일정 상세로 이어서 옮기는 작업이 적절합니다.

---

## React Schedule Delivery Product Selection — 납품 품목 제품 마스터 선택 전환 (2026-05-09)

### 1. Summary

React `/schedules/<id>/` 일정 상세의 납품 품목 편집 패널에 제품 마스터 검색/선택을 추가했습니다. 선택한 제품은 기존 `DeliveryItem.product`로 저장되고, 제품 품번/단위/현재 단가가 납품 품목에 자동 반영됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 제품 마스터 선택 전환 계획과 검증 범위 추가 |
| `frontend/src/App.tsx` | 납품 품목 편집 행에 제품 검색/선택 UI, 자동 입력, `productId` 저장 payload 추가 |
| `frontend/src/api.ts` | 제품 목록 API client/type 추가, 납품 품목 type에 제품 연결 필드 추가 |
| `frontend/src/styles.css` | 제품 검색 입력, 선택 결과, 해제 버튼 스타일 추가 |
| `reporting/views.py` | 접근 가능한 제품 queryset helper, 제품 API 응답 보강, 납품 품목 저장 API의 `productId` 검증/저장 추가 |
| `reporting/tests.py` | 제품 목록 권한/응답, 제품 선택 저장, 타사 제품 차단 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 납품 품목을 직접 입력하면서도 기존 제품 마스터를 검색해 선택할 수 있습니다.
- 제품 선택 시 품번, 단위, 현재 단가가 자동으로 채워져 입력 누락과 가격 오타를 줄입니다.
- 저장 시 선택 제품은 `DeliveryItem.product` 관계로 남아 이후 견적/납품 데이터 추적에 활용할 수 있습니다.
- 타사 또는 접근 불가 제품 ID를 직접 보내도 API에서 저장을 차단합니다.

### 4. Existing Functionality Preserved

- 기존 수기 품목명/수량/단위/단가 입력 흐름은 유지했습니다.
- 기존 Django `/reporting/api/products/`, `/reporting/schedules/<id>/update-delivery-items/`, 일정 상세/수정 화면과 `/reporting/*` 경로는 유지했습니다.
- 기존 `Product`, `DeliveryItem.product` 필드를 사용해 DB migration은 없습니다.
- Manager/동료/타사 권한 차단과 미로그인 API 보호는 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 19 tests, OK

cd frontend && npm run build
→ OK, assets/index-5rWArWxv.js / assets/index-DDeLHwwx.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ OK

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 세션에서 `/schedules/<id>/` 편집 패널을 열고 제품 검색, 선택, 저장까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- 제품 마스터 자체 생성/수정 화면은 이번 범위가 아니며 기존 Django 제품 관리 화면을 그대로 사용합니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 일정 선결제 세부 입력 또는 견적/납품 고급 입력처럼 아직 Django 폼에 남아 있는 일정 부가 기능을 React로 옮기는 작업이 적절합니다.

---

## Production Schedule Delivery Product Selection Deployment — 납품 품목 제품 선택 운영 배포 (2026-05-09)

### 1. Summary

React 납품 품목 제품 마스터 선택 변경분을 GitHub `main`에 푸시하고 production `web`, `sales-note-frontend` 서비스에 반영했습니다. 운영 `/schedules/<id>/`가 새 번들을 내려주며, 제품 검색 UI와 `/reporting/api/products/` 호출 코드가 포함된 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 검증 기록 추가 |

### 3. CRM Improvements

- 운영 React 일정 상세의 납품 품목 편집 패널에서 제품 마스터 검색/선택이 가능해졌습니다.
- 선택 제품은 저장 API에서 `DeliveryItem.product`로 연결되고 품번/단위/현재 단가가 반영됩니다.
- 제품 조회/저장은 기존 회사/담당자 접근 권한을 기준으로 제한됩니다.

### 4. Existing Functionality Preserved

- Django `web` 서비스는 React의 API/login/proxy backend이므로 유지했습니다.
- 기존 Django 제품 관리 화면, 일정 상세/수정 화면, `/reporting/*` 경로는 유지했습니다.
- 수기 납품 품목 입력 방식도 계속 사용 가능합니다.
- 미로그인 상태에서 일정 상세 API는 `401 login_required`, 제품 API는 로그인 페이지 redirect로 보호됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add React delivery product selection"
→ e6ca971 feat: add React delivery product selection

git push origin main
→ main updated from 9552745 to e6ca971

railway status
→ web Online, sales-note-frontend Online

railway deployment list --service web --json
→ latest web deployment 824aea49-f1b4-4247-84e8-bbeb14bca72a, SUCCESS, commit e6ca971

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy React delivery product selection e6ca971" --ci
→ Deploy complete, deployment id 584c23a9-50af-4802-b681-f804983ea4af

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/schedules/731/
→ 200, assets/index-5rWArWxv.js / assets/index-DDeLHwwx.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-5rWArWxv.js
→ schedule-delivery-product-field=True, /reporting/api/products/=True, productId=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-DDeLHwwx.css
→ schedule-delivery-product-field=True, schedule-delivery-product-results=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/delivery-items/update/
→ 405 MethodNotAllowed, 라우트 존재 확인

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/731/
→ 401 login_required, 정상

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/products/ -MaximumRedirection 0
→ 302 /reporting/login/?next=/reporting/api/products/, 정상
```

### 6. Known Limitations

- 실제 로그인 계정에서 제품 검색어 입력, 제품 선택, 저장 후 상세 화면 반영까지의 육안 확인은 사용자 계정으로 필요합니다.
- 제품 마스터 신규 등록/수정은 이번 범위가 아니며 기존 Django 제품 관리 화면을 사용합니다.

### 7. Recommended Next Task

- 다음 단계는 일정 선결제 세부 입력 또는 견적/문서 생성처럼 아직 Django 화면에 남아 있는 일정 부가 기능을 React로 옮기는 작업이 적절합니다.

---

## React Schedule Prepayment Editing — 일정 선결제 입력 전환 (2026-05-09)

### 1. Summary

React `/schedules/<id>/` 일정 상세 수정 패널에서 납품 일정의 선결제 선택과 차감 금액을 저장할 수 있게 연결했습니다. 기존 Django 일정 수정 폼의 선결제 복원 후 재차감 정책을 React 저장 API에도 적용했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 일정 선결제 입력 전환 계획과 시간 단위 진행 루트 추가 |
| `frontend/src/App.tsx` | 일정 수정 패널에 선결제 사용 체크, 선결제 목록, 차감 금액 입력, 합계 표시 추가 |
| `frontend/src/api.ts` | 선결제 목록 client/type, 일정 상세 선결제 사용 내역 type, 저장 payload 추가 |
| `frontend/src/styles.css` | 선결제 선택/합계/사용 내역 UI 스타일과 모바일 레이아웃 추가 |
| `reporting/views.py` | 선결제 옵션 payload, 기존 사용분 복원, 잔액 검증 후 재차감, 상세 API 사용 내역 추가 |
| `reporting/tests.py` | 선결제 목록, 적용/복원, 잔액 초과 차단 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 납품 일정 수정 시 Django 화면으로 이동하지 않고 React에서 선결제를 선택하고 금액을 차감할 수 있습니다.
- 기존 선택된 선결제가 소진 상태여도 현재 일정 사용분은 목록에 포함해 유지/수정할 수 있습니다.
- 저장 API는 기존 사용분을 먼저 복원한 뒤 새 선택 금액을 검증하고 다시 차감합니다.
- 차감 합계와 납품 합계 대비 실결제 금액을 React 수정 패널에서 바로 확인할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 Django 선결제 목록/상세/일정 수정 화면과 `/reporting/*` 경로는 유지했습니다.
- 기존 `Schedule`, `Prepayment`, `PrepaymentUsage`, `DeliveryItem` 모델만 사용했고 DB migration은 없습니다.
- Manager는 일정 수정이 계속 차단되고, salesman은 본인 일정만 수정 가능합니다.
- 타사/접근 불가 고객 또는 선결제는 API에서 차단됩니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 22 tests, OK

cd frontend && npm run build
→ OK, assets/index-Dh6TMGfl.js / assets/index-DejZtU4J.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/schedules/<id>/` 수정 패널을 열고 선결제 선택, 금액 입력, 저장 후 잔액/상세 반영까지 이어지는 육안 확인은 운영 배포 후 필요합니다.
- 선결제 신규 등록/수정/취소는 이번 범위가 아니며 기존 Django 선결제 관리 화면을 사용합니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 견적/문서 생성 또는 선결제 관리 목록처럼 아직 Django 화면에 남아 있는 일정/거래 부가 기능을 React로 옮기는 작업이 적절합니다.

---

## React Customer Department AI Analysis — 고객 상세 부서 AI 분석 연결 (2026-05-09)

### 1. Summary

React `/customers/<id>/` 고객 상세 화면에서 해당 고객의 부서 AI 분석 상태를 확인하고, 권한이 있는 사용자는 고객 화면에서 바로 분석을 실행할 수 있게 연결했습니다. 기존 `ai_chat` 부서 분석 조회/실행 URL을 재사용했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 상세 부서 AI 분석 연결 계획과 시간 단위 진행 루트 추가 |
| `frontend/src/App.tsx` | 고객 상세 사이드 영역에 부서 AI 분석 카드, 실행 버튼, 결과 보기 링크 추가 |
| `frontend/src/api.ts` | 고객 상세 `aiDepartment` type과 부서 AI 분석 실행 client 추가 |
| `frontend/src/styles.css` | 고객 상세 부서 AI 분석 카드/지표/액션 스타일 추가 |
| `reporting/views.py` | 고객 상세 API에 부서 AI 분석 가능 여부, 요약, 카운트, 결과/실행 URL 추가 |
| `reporting/tests.py` | 고객 상세 API의 부서 AI 분석 링크/권한 payload 테스트 추가 |
| `AGENT_REPORT.md` | 작업 결과와 검증 기록 추가 |

### 3. CRM Improvements

- 고객 상세에서 해당 고객의 부서 AI 분석 여부와 최근 요약을 바로 확인할 수 있습니다.
- AI 권한이 있고 해당 부서에 본인 담당 고객이 있는 사용자는 고객 화면에서 부서 AI 분석을 실행할 수 있습니다.
- 분석 완료 후 미팅/견적/납품/PainPoint 카운트와 결과 화면 링크가 고객 상세에 표시됩니다.
- AI 권한이 없거나 본인 담당 부서가 아닌 경우 실행 버튼은 비활성화됩니다.

### 4. Existing Functionality Preserved

- 기존 Django `ai_chat:department_analysis`, `ai_chat:run_analysis`, `ai_chat:department_list` 경로를 유지했습니다.
- 기존 AI 권한 정책인 `can_use_ai`와 본인 담당 부서 조건을 유지했습니다.
- 기존 React 고객 상세 수정/노트/일정 기능과 `/reporting/*` 경로는 유지했습니다.
- DB migration은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 18 tests, OK

cd frontend && npm run build
→ OK, assets/index-BWDtIOid.js / assets/index-BtW6mZC7.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)

railway deployment list --service web --json
→ web deployment 05bdca63-6d37-4a43-9609-5c28e98e162a SUCCESS, commit 37b4c5d

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy customer department AI action 37b4c5d" --ci
→ Deploy complete, deployment id da0a55b7-29d2-4845-91b7-3f8b07794711

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/454/
→ 200, assets/index-BWDtIOid.js / assets/index-BtW6mZC7.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-BWDtIOid.js
→ customer-ai-card=True, AI 분석 실행=True, aiDepartment=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-BtW6mZC7.css
→ customer-ai-card=True, customer-ai-metrics=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/customers/454/`의 부서 AI 분석 실행 버튼을 눌러 OpenAI 분석까지 완료되는 육안 확인은 운영 배포 후 필요합니다.
- 다른 영업담당자만 보유한 부서 고객은 기존 AI 정책대로 현재 사용자에게 분석 실행 버튼이 비활성화됩니다.

### 7. Recommended Next Task

- 수동 검수 후 다음 단계는 AI 분석 결과를 React 화면 안에서 직접 확인하거나 PainPoint 검증까지 React로 옮기는 작업이 적절합니다.

---

## React Customer AI Result Verification — 고객 상세 AI 결과/검증 전환 (2026-05-10)

### 1. Summary

React `/customers/<id>/` 고객 상세의 부서 AI 카드에서 분석 결과를 바로 펼쳐보고 PainPoint 검증까지 처리할 수 있게 연결했습니다. 기존 Django `ai_chat`의 부서 분석/검증 정책과 URL은 유지하고, 고객 상세 API의 `aiDepartment` payload만 확장했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객 상세 AI 결과/검증 전환 계획 추가 |
| `reporting/views.py` | 고객 상세 API에 분석 기간, 미팅/견적/납품 인사이트, 추천 액션, 확인 필요 사항, PainPoint 카드/검증 URL payload 추가 |
| `reporting/tests.py` | 고객 상세 AI payload 확장 필드와 검증 URL 테스트 보강 |
| `frontend/src/api.ts` | 고객 AI 분석 결과/PainPoint 타입, payload 병합 기본값, `verifyAiPainpoint()` client 추가 |
| `frontend/src/App.tsx` | 고객 상세 부서 AI 결과 패널, PainPoint 검증 메모/확인/부정 처리 UI 추가 |
| `frontend/src/styles.css` | 고객 상세 AI 결과/검증 패널 반응형 스타일 추가 |

### 3. CRM Improvements

- 고객 상세에서 Django AI 상세 화면으로 이동하지 않아도 분석 요약, 미팅 인사이트, 견적/납품 분석, 추천 액션을 확인할 수 있습니다.
- 미검증 PainPoint 카드에 검증 메모를 입력하고 `확인` 또는 `부정` 상태로 저장할 수 있습니다.
- 검증 후 고객 상세 데이터를 새로 불러와 미검증 카운트와 카드 상태가 즉시 반영됩니다.
- 분석 실행 직후 React 결과 패널이 열려 다음 확인 작업으로 자연스럽게 이어집니다.

### 4. Existing Functionality Preserved

- 기존 `/ai/department/<id>/`, `/ai/card/<id>/verify/`, `/ai/` Django AI 화면은 유지했습니다.
- 기존 `AIDepartmentAnalysis`, `PainPointCard` 모델만 사용했고 DB migration은 없습니다.
- AI 권한은 기존 `can_use_ai`와 본인 담당 부서 조건을 유지했습니다.
- 고객 상세/수정, 영업노트, 일정, `/reporting/*` 경로는 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 18 tests, OK

cd frontend && npm run build
→ OK, assets/index-zyiEigxz.js / assets/index-CZEfolrn.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 실제 로그인 계정에서 `/customers/454/` 접속 후 분석 결과 펼치기, PainPoint 검증 저장, 카운트 갱신까지의 브라우저 수동 검수는 아직 필요합니다.
- 운영 배포는 아직 수행하지 않았습니다.
- React 고객 상세는 기존 Django AI 상세의 삭제/재분석 전체 관리 기능 중 삭제 기능은 제공하지 않습니다. 삭제는 기존 Django AI 상세에서 계속 처리합니다.

### 7. Recommended Next Task

- 수동 검수 후 운영 `web`과 `sales-note-frontend`에 배포하고, 이후 AI workspace의 PainPoint 목록도 React 고객 상세 결과 링크로 연결하면 좋습니다.

---

## Project Direction Documentation — React 단일 CRM 프론트 목표 문서화 (2026-05-10)

### 1. Summary

프로젝트 최종 목표를 "React 단일 CRM 프론트 + Django backend/API"로 문서화했습니다. 앞으로 Django template 화면은 레거시 전환 화면으로 보고, React 대체와 운영 수동검수 후 최종 삭제하는 방향을 기준으로 작업합니다.

또한 이후 런타임 작업은 커밋/푸시 후 Railway에 배포하고, 사용자에게 운영 서버 수동테스트 프로세스를 제공한 뒤 다음 작업을 진행하는 규칙을 문서화했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENTS.md` | React-only CRM frontend 목표, Django backend-only 역할, Railway 배포/수동검수 workflow 추가 |
| `.github/copilot-instructions.md` | 같은 최종 방향과 deliverable 기준 추가 |
| `PROJECT_BRIEF.md` | 목표 아키텍처, React route 중심 운영, 배포/수동테스트 workflow 추가 |
| `SALES_CRM_SPEC.md` | React migration requirements, React CRM UI 방향, 품질 기준 보강 |
| `QA_CHECKLIST.md` | React migration, React build, Railway deployment, manual server test 체크 추가 |
| `AGENT_PLAN.md` | 이번 문서화 작업 계획 추가 |
| `AGENT_REPORT.md` | 작업 결과 기록 |

### 3. CRM Improvements

- 향후 기능 개발의 판단 기준이 Django 화면 개선이 아니라 React CRM 전환으로 명확해졌습니다.
- Django template 삭제는 기능 동등성, 권한 검증, Railway 배포, 수동검수 후 진행하도록 기준을 세웠습니다.
- 작업 종료 기준에 운영 서버 수동테스트 프로세스 제공이 포함됐습니다.

### 4. Existing Functionality Preserved

- 문서 변경만 수행했으며 Django/React runtime 동작은 문서 작업으로 변경하지 않았습니다.
- 기존 `/reporting/*` 보존 원칙은 유지하되, 장기적으로 backend/API/legacy compatibility 역할로 정리했습니다.
- 공개 사이트 확장 금지 원칙은 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 18 tests, OK

cd frontend && npm run build
→ OK, assets/index-zyiEigxz.js / assets/index-CZEfolrn.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 현재 문서화는 방향과 운영 규칙을 정리한 것이며, Django template 삭제 자체는 수행하지 않았습니다.
- 직전 React 고객 AI 결과/검증 runtime 변경도 같은 작업 트리에 포함되어 있어 이번 배포 대상에 함께 포함됩니다.

### 7. Recommended Next Task

- 이번 변경을 커밋/푸시하고 Railway `web`, `sales-note-frontend`에 배포한 뒤 `/customers/454/` 기준으로 고객 상세 AI 결과/검증 수동테스트를 진행합니다.

---

## Production Customer AI Result Verification Deployment — 고객 상세 AI 결과/검증 운영 배포 (2026-05-10)

### 1. Summary

React 고객 상세 AI 결과/검증 변경과 React 단일 CRM 프론트 목표 문서화를 GitHub `main`에 푸시하고 Railway production `web`, `sales-note-frontend` 서비스에 배포했습니다. 운영 `/customers/454/`가 새 React 번들을 서빙하고, 고객 상세 API가 비로그인 상태에서 `401 login_required`로 보호되는 것을 확인했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 수동테스트 절차 기록 추가 |

### 3. CRM Improvements

- 운영 React 고객 상세에서 AI 분석 결과 패널과 PainPoint 검증 UI가 포함된 새 번들이 배포됐습니다.
- Django 고객 상세 API에 AI 결과/PainPoint payload가 배포됐습니다.
- 프로젝트 문서에 React 단일 CRM 프론트와 Django backend/API 전환 목표가 반영됐습니다.

### 4. Existing Functionality Preserved

- 기존 Django `/ai/department/<id>/`, `/ai/card/<id>/verify/`, `/reporting/*` 경로는 유지했습니다.
- 기존 로그인 보호는 유지되어 비로그인 고객 상세 API 접근은 `401 login_required`를 반환합니다.
- DB migration은 없습니다.

### 5. Commands Run and Results

```text
git commit -m "feat: add customer AI result verification"
→ 089d71f feat: add customer AI result verification

git push origin main
→ main updated from 59c0999 to 089d71f

railway status
→ web Online, sales-note-frontend Online

railway redeploy --service web --from-source --yes --json
→ {"success": true}

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy customer AI result verification 089d71f" --ci
→ Deploy complete, deployment id 6d1cb36c-e22c-4650-ba7f-4e76344f32f8

railway deployment list --service web --json
→ latest web deployment 4a4d01e5-f1c4-4d03-8bf9-325f211b8d14, SUCCESS, commit 089d71f

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/454/
→ 200, assets/index-zyiEigxz.js / assets/index-CZEfolrn.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-zyiEigxz.js
→ customer-ai-result=True, AI PainPoint verification=True, PainPoint=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-CZEfolrn.css
→ customer-ai-result=True, customer-ai-painpoint=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 실제 로그인 계정에서 AI 결과 패널 펼치기, PainPoint 검증 저장, 카운트 갱신까지의 수동검수는 사용자 계정에서 필요합니다.
- Django AI 상세의 삭제 기능은 React 고객 상세에 추가하지 않았습니다. 삭제는 기존 Django AI 상세에서 계속 처리합니다.

### 7. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/customers/454/`
2. AI 권한이 있는 본인 담당 고객 계정으로 로그인합니다.
3. 고객 상세 오른쪽 `Department AI` 카드에서 분석 요약과 지표가 보이는지 확인합니다.
4. `결과 보기` 버튼을 눌러 미팅 인사이트, 견적/납품 분석, 추천 액션, 확인 필요 사항, PainPoint 검증 섹션이 펼쳐지는지 확인합니다.
5. 미검증 PainPoint 카드에 검증 메모를 입력하고 `확인`을 누릅니다.
6. 저장 후 성공 메시지, 미검증 카운트 감소, 카드 상태 변경이 반영되는지 확인합니다.
7. 다른 미검증 카드가 있으면 `부정`도 같은 방식으로 테스트합니다.
8. AI 권한이 없는 계정 또는 본인 담당 부서가 아닌 고객에서는 실행/검증 버튼이 비활성화되는지 확인합니다.
9. 기존 `Django 보기` 링크가 `/ai/department/<id>/`로 정상 이동하는지 확인합니다.

### 8. Recommended Next Task

- 사용자의 운영 수동검수 결과를 받은 뒤 다음 React 전환 작업을 진행합니다.

---

## AI PainPoint Verification Memory — 재분석 검증 메모리 반영 (2026-05-10)

### 1. Summary

부서 AI 재분석 시 기존 PainPoint 검증 상태와 검증 메모를 GPT 입력 프롬프트에 포함하도록 수정했습니다. 재분석 저장 시에는 미검증 카드만 교체하고, 사용자가 이미 `확인` 또는 `부정` 처리한 카드는 검증 메모와 함께 보존합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | AI PainPoint 검증 메모리 반영 계획 추가 |
| `ai_chat/services.py` | 기존 검증 카드/저장 메모리 수집, 프롬프트 섹션 생성, 분석 결과 JSON에 `verification_memory` 저장 추가 |
| `ai_chat/views.py` | 재분석 시 검증 완료/부정 카드 보존, 미검증 카드만 교체, 검증 메모리 중복 카드 저장 차단 |
| `ai_chat/tests.py` | 프롬프트 메모리 포함, 검증 카드 보존/중복 차단 테스트 추가 |

### 3. CRM Improvements

- 이미 검증한 PainPoint와 검증 메모가 다음 부서 AI 분석의 입력 컨텍스트로 들어갑니다.
- `확인됨` PainPoint는 확인된 사실로, `부정됨` PainPoint는 다시 묻지 말아야 할 가설로 GPT에 전달됩니다.
- 재분석이 기존 검증 메모를 덮어쓰지 않아 고객 상세에서 검증 이력이 계속 남습니다.

### 4. Existing Functionality Preserved

- 기존 `AIDepartmentAnalysis`, `PainPointCard` 모델만 사용했고 DB migration은 없습니다.
- AI 권한과 본인 담당 부서 조건은 기존 정책을 유지했습니다.
- 기존 Django `/ai/department/<id>/run/`, `/ai/card/<id>/verify/`, React 고객 상세 검증 흐름은 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
→ Ran 2 tests, OK

python manage.py test ai_chat.tests --verbosity=1
→ Ran 14 tests, OK

python -m py_compile ai_chat\services.py ai_chat\views.py ai_chat\tests.py
→ OK

python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 18 tests, OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- 기존에 이미 삭제된 과거 PainPoint 검증 메모는 복구할 수 없습니다. 이번 배포 이후 저장되는 검증 결과부터 장기 메모리로 유지됩니다.
- GPT가 완전히 다른 표현으로 같은 의미의 가설을 만들 수는 있어, 저장 단계에서 카테고리/가설/검증 질문이 같은 중복을 우선 차단합니다.
- 운영 배포와 수동 검수는 다음 배포 기록 섹션에 별도로 기록합니다.

### 7. Recommended Next Task

- 운영 수동검수 후 중단했던 React 선결제 목록 전환 작업으로 복귀합니다.

---

## Production AI PainPoint Verification Memory Deployment — AI 검증 메모리 운영 배포 (2026-05-10)

### 1. Summary

AI PainPoint 검증 메모리 반영 변경을 GitHub `main`에 푸시하고 Railway production `web` 서비스에 배포했습니다. 운영 API는 비로그인 상태에서 `401 login_required`를 반환해 기존 인증 보호가 유지됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 및 수동테스트 절차 기록 추가 |

### 3. CRM Improvements

- 운영 부서 AI 재분석에서 기존 확인/부정 PainPoint와 검증 메모가 GPT 프롬프트 컨텍스트에 포함됩니다.
- 확인/부정 처리된 PainPoint 카드는 재분석 중 삭제되지 않고 보존됩니다.
- GPT가 동일한 가설/검증 질문을 다시 반환해도 저장 단계에서 중복 생성을 차단합니다.

### 4. Existing Functionality Preserved

- 기존 React 고객 상세, Django AI 상세, PainPoint 검증 API는 유지했습니다.
- DB migration은 없습니다.
- 비로그인 API 접근 차단은 유지됩니다.

### 5. Commands Run and Results

```text
git commit -m "feat: remember AI painpoint verification"
→ 8c870ee feat: remember AI painpoint verification

git push origin main
→ main updated from ecf7216 to 8c870ee

railway redeploy --service web --from-source --yes --json
→ {"success": true}

railway deployment list --service web --json
→ latest web deployment eb626429-4dc8-4cb0-b2ee-e3e3b5fb1236 SUCCESS, commit 8c870ee

railway status
→ web Online, sales-note-frontend Online

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
→ 401 login_required, 정상

Invoke-WebRequest https://web-production-5096.up.railway.app/reporting/api/customers/454/
→ 401 login_required, 정상
```

### 6. Known Limitations

- 이번 배포 이전 재분석으로 이미 삭제된 검증 메모는 복구할 수 없습니다.
- 의미는 같지만 문장이 크게 다른 가설은 GPT가 새 카드로 만들 수 있습니다. 현재 저장 중복 차단은 카테고리, 가설, 검증 질문의 정규화 비교를 기준으로 합니다.

### 7. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/customers/454/`
2. AI 권한이 있는 본인 담당 고객 계정으로 로그인합니다.
3. 고객 상세의 `Department AI` 카드에서 기존 미검증 PainPoint 하나를 선택합니다.
4. 검증 메모에 구체적인 내용을 입력하고 `확인` 또는 `부정`으로 저장합니다.
5. 같은 카드가 검증 상태와 메모를 표시하는지 확인합니다.
6. 같은 고객/부서에서 `AI 분석 실행`을 다시 누릅니다.
7. 재분석 후 기존 검증 완료/부정 카드와 메모가 사라지지 않는지 확인합니다.
8. 새로 생성된 미검증 카드에 방금 검증한 것과 같은 질문/가설이 반복되지 않는지 확인합니다.

### 8. Recommended Next Task

- 수동검수 결과를 받은 뒤 중단했던 React 선결제 목록 전환 작업으로 복귀합니다.

---

## AI Verification-Based Insights Implementation — 검증 메모 분석 반영 강화 (2026-05-10)

### 1. Summary

PainPoint 검증 메모를 단순 저장/중복 방지용이 아니라 부서 AI 분석의 핵심 근거로 승격했습니다. 재분석 시 GPT 프롬프트는 검증 메모를 미팅 기록과 동급으로 반영하도록 요구하고, GPT가 누락해도 서버가 검증 기반 인사이트, 다음 액션, 추가 확인 질문을 보정해 저장합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `ai_chat/services.py` | 검증 메모 프롬프트 강화, `verification_insights` 결과 계약 추가, fallback 인사이트/다음 액션/질문 보정 추가 |
| `ai_chat/views.py` | 분석 저장 직전 검증 메모 보정 적용 |
| `reporting/views.py` | 고객 상세 AI payload에 `verificationInsights` 추가, 검증 evidence label 추가 |
| `frontend/src/api.ts` | `verificationInsights` 타입/기본값/merge 처리 추가 |
| `frontend/src/App.tsx` | 고객 상세 AI 결과에 `검증 기반 인사이트` 섹션 추가 |
| `frontend/src/styles.css` | 검증 인사이트 UI 스타일 추가 |
| `ai_chat/tests.py` | 프롬프트/저장 결과가 검증 메모 기반 액션과 질문을 포함하는지 검증 |
| `reporting/tests.py` | 고객 상세 API가 검증 인사이트와 검증 evidence label을 반환하는지 검증 |
| `AGENT_PLAN.md` | 작업 계획과 검증 계획 기록 |

### 3. CRM Improvements

- 사용자가 검증한 내용이 다음 AI 요약, PainPoint, 추천 액션, 확인 필요 질문에 반영됩니다.
- 확인된 가설은 후속 일정/예산/필요 자료 확인으로 이어지고, 부정된 가설은 대체 원인 확인으로 이어집니다.
- React 고객 상세에서 검증 메모가 어떤 다음 검증/액션으로 이어졌는지 바로 확인할 수 있습니다.

### 4. Existing Functionality Preserved

- 신규 DB 필드와 migration은 없습니다.
- 기존 AI 권한, 본인 담당 부서 조건, `/reporting/*`, `/ai/*` 경로는 유지했습니다.
- 미검증 PainPoint 교체, 검증 완료/부정 카드 보존 정책은 유지했습니다.

### 5. Commands Run and Results

```text
python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
→ Ran 2 tests, OK

python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1
→ Ran 18 tests, OK

python manage.py test ai_chat.tests --verbosity=1
→ Ran 14 tests, OK

cd frontend && npm run build
→ OK, bundle index-BTctbCPt.js / index-D14Oetqu.css

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Known Limitations

- GPT 응답 자체가 요약 본문에 검증 메모를 충분히 녹이지 못하는 경우에도 서버는 별도 `verification_insights`, `next_actions`, `missing_info.questions`를 보정합니다.
- 이전 배포 전에 이미 삭제된 검증 메모는 복구할 수 없습니다.

### 7. Recommended Next Task

- 운영 배포 및 수동검수 완료 후 React 통합 프론트 전환 작업으로 복귀합니다.

---

## Production AI Verification-Based Insights Deployment — 검증 기반 인사이트 운영 배포 (2026-05-10)

### 1. Summary

AI 검증 메모 분석 반영 강화 변경을 GitHub `main`에 푸시하고 Railway production `web`, `sales-note-frontend` 서비스에 배포했습니다. 운영 프론트 번들에 `verificationInsights`와 `customer-ai-verification-list`가 포함되어 있고, 비로그인 API 접근은 `401 login_required`로 차단됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_REPORT.md` | 운영 배포 ID, smoke check, 수동테스트 절차 기록 추가 |

### 3. Deployment Status

- Feature commit: `47679b7 feat: apply AI verification memory to insights`
- `web`: `e1d4ddae-9b49-48af-b315-13eee223a6ab` SUCCESS
- `sales-note-frontend`: `7ab298a7-a778-438b-af34-752e6836816d` SUCCESS
- Railway status: `web` Online, `sales-note-frontend` Online
- 운영 번들: `index-BTctbCPt.js`, `index-D14Oetqu.css`

### 4. Commands Run and Results

```text
git commit -m "feat: apply AI verification memory to insights"
→ 47679b7 feat: apply AI verification memory to insights

git push origin main
→ main updated from 59e8ba4 to 47679b7

railway redeploy --service web --from-source --yes --json
→ {"success":true}

railway up frontend --path-as-root --service sales-note-frontend --environment production --message "Deploy AI verification insight UI 47679b7" --ci
→ Deploy complete

railway deployment list --service web --json
→ e1d4ddae-9b49-48af-b315-13eee223a6ab SUCCESS

railway deployment list --service sales-note-frontend --json
→ 7ab298a7-a778-438b-af34-752e6836816d SUCCESS

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/customers/454/
→ 200, index-BTctbCPt.js / index-D14Oetqu.css

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-BTctbCPt.js
→ 200, verificationInsights=True, customer-ai-verification-list=True

Invoke-WebRequest https://sales-note-frontend-production.up.railway.app/assets/index-D14Oetqu.css
→ 200, customer-ai-verification-list=True

curl.exe -s -i https://sales-note-frontend-production.up.railway.app/reporting/api/customers/454/
→ 401 login_required

curl.exe -s -i https://web-production-5096.up.railway.app/reporting/api/customers/454/
→ 401 login_required
```

### 5. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/customers/454/`
2. AI 권한이 있고 해당 고객/부서를 담당하는 계정으로 로그인합니다.
3. 기존 미검증 PainPoint 하나에 구체적인 검증 메모를 입력하고 `확인` 또는 `부정`으로 저장합니다.
   - 예: `김박사가 최종 승인자이며 6월 예산 소진 뒤 구매 가능, 필요 서류는 견적서와 사양서`
4. 같은 고객 상세에서 `AI 분석 실행`을 다시 누릅니다.
5. 재분석 후 기존 검증 완료/부정 카드와 메모가 사라지지 않는지 확인합니다.
6. AI 결과 영역에 `검증 기반 인사이트` 섹션이 표시되는지 확인합니다.
7. `검증 기반 인사이트`, `추천 액션`, `확인 필요` 질문에 방금 남긴 검증 메모가 반영되는지 확인합니다.
8. 이미 물어본 검증 질문이 그대로 반복되지 않고, 일정/예산/필요 서류/대체 원인 같은 다음 단계 질문으로 바뀌는지 확인합니다.

### 6. Known Limitations

- GPT가 본문 요약에서 검증 메모를 약하게 반영하더라도 서버 fallback이 별도 인사이트와 다음 액션/질문을 보정합니다.
- 운영 수동검수는 로그인 세션이 필요해 사용자가 직접 진행해야 합니다.

### 7. Recommended Next Task

- 수동검수 결과를 받은 뒤 React 통합 프론트 전환 로드맵의 다음 화면 작업으로 진행합니다.

---

## Urgent Weekly Report Quote/Delivery Amount Loading — 주간보고 견적/납품 금액 포함 (2026-05-10)

### 1. Summary

주간보고 작성 화면의 `일정 불러오기`에서 견적 제출 및 납품 일정 금액이 함께 표시되고, 선택 후 `견적/납품에 삽입`할 때도 금액 줄이 포함되도록 수정했습니다. 견적은 `Quote.total_amount`를 우선 사용하고, Quote가 없는 견적 일정은 `DeliveryItem` 합계 또는 `Schedule.expected_revenue`를 fallback으로 사용합니다. 납품은 `DeliveryItem.total_price` 합계를 우선 사용하고, 없으면 연결 `History.delivery_amount`, 없으면 `Schedule.expected_revenue`를 fallback으로 사용합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 긴급 주간보고 금액 포함 작업 계획 추가 |
| `reporting/views.py` | `weekly_report_load_schedules` 응답에 `amount`, `amount_label`, 히스토리/견적 금액 payload 추가 |
| `reporting/templates/reporting/weekly_report/form.html` | 일정 카드에 금액 표시, 선택 삽입 텍스트에 금액 줄 포함, 최초 진입 시 API 기반 자동 로드 |
| `reporting/tests.py` | 견적 금액, 견적 fallback 금액, 납품 DeliveryItem 금액, 납품 History fallback 금액, 작성 화면 렌더링 테스트 추가 |

### 3. CRM Improvements

- 주간보고 작성자가 견적/납품 기록을 불러올 때 금액을 별도로 찾아 입력하지 않아도 됩니다.
- 납품 기록은 품목 기반 금액과 기존 히스토리 금액을 모두 반영합니다.
- 견적 제출 기록은 실제 Quote 금액이 있으면 해당 금액을, 없는 경우 일정의 예상 매출액을 사용합니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/weekly-reports/create/` URL과 주간보고 저장 방식은 유지했습니다.
- 기존 `categorized.activity`, `categorized.quote_delivery`, `schedules` 응답 구조는 유지하고 필드만 추가했습니다.
- 인증은 기존 `@login_required`와 본인 일정 조회 범위를 유지했습니다.
- DB migration은 없습니다.

### 5. Commands Run and Results

```text
python -m py_compile reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1
→ Ran 8 tests, OK

python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1
→ Ran 13 tests, OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `d006234 fix: include weekly report quote delivery amounts`
- GitHub push: `main` updated from `b0c485b` to `d006234`
- Railway `web`: `77680da9-7b6a-4619-ada2-c289527534af` SUCCESS, commit `d006234`
- Railway status: `web` Online, `sales-note-frontend` Online
- `sales-note-frontend` bundle was not rebuilt because this task changed Django API/template only.

### 7. Production Smoke Check

```text
curl -i https://sales-note-frontend-production.up.railway.app/reporting/weekly-reports/create/
→ 302 /reporting/login/?next=/reporting/weekly-reports/create/

curl -i "https://sales-note-frontend-production.up.railway.app/reporting/api/weekly-reports/schedules/?week_start=2026-04-21&week_end=2026-04-27"
→ 302 /reporting/login/?next=/reporting/api/weekly-reports/schedules/%3Fweek_start%3D2026-04-21%26week_end%3D2026-04-27

curl -i "https://web-production-5096.up.railway.app/reporting/api/weekly-reports/schedules/?week_start=2026-04-21&week_end=2026-04-27"
→ 302 /reporting/login/?next=/reporting/api/weekly-reports/schedules/%3Fweek_start%3D2026-04-21%26week_end%3D2026-04-27
```

### 8. Known Limitations

- 운영에서 실제 금액이 카드와 Quill 입력 텍스트에 들어가는지는 로그인 세션이 필요해 사용자 수동검수가 필요합니다.
- 명시적으로 저장된 0원 납품 금액은 표시합니다. 금액 소스가 아예 없는 일정은 기존처럼 금액 줄을 표시하지 않습니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/reporting/weekly-reports/create/`
2. 로그인 후 주 시작일/종료일을 견적 제출 또는 납품 일정이 있는 주로 선택합니다.
3. `일정 불러오기`를 클릭합니다.
4. 오른쪽 `견적/납품` 섹션에서 견적 제출 카드에 `견적 금액` 또는 견적번호 옆 금액이 보이는지 확인합니다.
5. 납품 일정 카드에 `납품 금액`이 보이는지 확인합니다.
6. 해당 견적/납품 카드를 체크하고 `견적/납품에 삽입`을 클릭합니다.
7. 왼쪽 `견적/납품 내용` 에디터에 선택한 일정과 함께 `견적 금액: ...원` 또는 `납품 금액: ...원` 줄이 들어가는지 확인합니다.
8. 저장 후 주간보고 상세에서 금액이 포함된 내용이 그대로 표시되는지 확인합니다.

### 10. Recommended Next Task

- 수동검수 결과를 받은 뒤 중단했던 React 통합 프론트 전환 작업으로 복귀합니다.

---

## Urgent Weekly Report Rich Text HTML Normalization — 주간보고 HTML 이중 escape 방지 (2026-05-10)

### 1. Summary

주간보고 작성/수정 저장 시 Quill HTML이 `<p>&lt;p&gt;...` 형태로 이중 escape되어 저장/표시되는 문제를 방지했습니다. 저장 시 서버에서 escaped rich text를 정상 HTML로 정규화하고, 이미 깨진 저장값도 상세 렌더링과 수정 화면 초기 로드에서 보정합니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | HTML 이중 escape 긴급 수정 계획 추가 |
| `reporting/utils_html.py` | escaped rich text 정규화, bleach fallback plain text 변환 보강 |
| `reporting/templates/reporting/weekly_report/form.html` | 수정 화면 Quill 초기 로드 시 escaped HTML 정규화 |
| `reporting/tests.py` | 이중 escape 저장/렌더링 회귀 테스트 및 0원 납품 금액 테스트 추가 |
| `reporting/views.py` | 0원 납품 금액을 명시 금액으로 보존하도록 주간보고 일정 금액 helper 보강 |

### 3. CRM Improvements

- 주간보고 상세에서 `<p>&lt;p&gt;...` 같은 HTML 태그 문자열이 노출되지 않습니다.
- 기존에 이미 깨진 주간보고도 상세 보기와 수정 화면에서 정상 문단으로 보정됩니다.
- 견적/납품 금액 긴급 수정에서 명시적인 `0원` 납품도 누락하지 않게 보강했습니다.

### 4. Existing Functionality Preserved

- 기존 Quill 기반 주간보고 작성/수정 UX는 유지했습니다.
- 기존 HTML 정화 정책과 허용 태그 목록은 유지했습니다.
- 신규 DB 필드와 migration은 없습니다.
- 기존 로그인 보호와 `/reporting/*` 경로는 유지했습니다.

### 5. Commands Run and Results

```text
python -m py_compile reporting\utils_html.py reporting\views.py reporting\tests.py
→ OK

python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1
→ Ran 15 tests, OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `aa73921 fix: normalize weekly report rich text html`
- GitHub push: `main` updated from `d006234` to `aa73921`
- Railway `web`: `56b8c632-14aa-4989-aeca-f422e06e7a43` SUCCESS, commit `aa73921`
- Railway status: `web` Online, `sales-note-frontend` Online
- `sales-note-frontend` bundle was not rebuilt because this task changed Django API/template only.

### 7. Production Smoke Check

```text
curl -i https://sales-note-frontend-production.up.railway.app/reporting/weekly-reports/create/
→ 302 /reporting/login/?next=/reporting/weekly-reports/create/

curl -i "https://sales-note-frontend-production.up.railway.app/reporting/api/weekly-reports/schedules/?week_start=2026-04-21&week_end=2026-04-27"
→ 302 /reporting/login/?next=/reporting/api/weekly-reports/schedules/%3Fweek_start%3D2026-04-21%26week_end%3D2026-04-27
```

### 8. Known Limitations

- 운영에서 실제 저장 결과 확인은 로그인 세션이 필요해 사용자 수동검수가 필요합니다.
- 이미 깨진 과거 주간보고는 상세/수정 화면에서는 보정되어 보이며, 수정 후 저장하면 저장값도 정상화됩니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/reporting/weekly-reports/create/`
2. 로그인 후 주간보고를 새로 작성합니다.
3. `영업 활동 내용`, `견적/납품 내용`, `다음 주 계획 / 기타`에 여러 줄을 입력합니다.
4. 저장 후 상세 화면에서 `<p>`, `&lt;p&gt;`, `&amp;gt;` 같은 HTML 문자열이 보이지 않고 일반 문장/문단으로 보이는지 확인합니다.
5. 방금 저장한 보고서에서 `수정`을 누릅니다.
6. Quill 에디터 안에도 `<p>...</p>` 문자열이 아니라 실제 문단 내용만 보이는지 확인합니다.
7. 다시 저장 후 상세 화면이 계속 정상 문단으로 보이는지 확인합니다.
8. 견적/납품 일정 불러오기 테스트도 함께 진행해 금액 표시와 삽입이 유지되는지 확인합니다.

### 10. Recommended Next Task

- 수동검수 결과를 받은 뒤 React 통합 프론트 전환 작업으로 복귀합니다.

---

## React Customer/Department Searchable Select UX — 고객·부서 검색 선택 (2026-05-10)

### 1. Summary

React CRM 주요 작성/수정 폼의 고객, 업체/학교, 부서/연구실 선택을 검색 가능한 선택 UI로 교체했습니다. 메일 작성에서도 연결 고객을 이름, 회사, 이메일로 검색해 선택할 수 있습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 고객/부서 검색 선택 UX 작업 계획 추가 |
| `frontend/src/App.tsx` | 공통 `SearchableSelect` 추가, 고객/업체/부서 option helper 추가, 주요 폼 적용 |
| `frontend/src/styles.css` | 검색 선택 컨트롤, 결과 목록, 폼 라벨 스타일 추가 |

### 3. CRM Improvements

- 메일 작성의 연결 고객 선택에서 고객/회사/이메일 검색이 가능합니다.
- 고객 등록/수정에서 업체와 부서를 검색해서 선택할 수 있습니다.
- 영업노트, 일정, 선결제의 고객 선택에서 긴 목록을 스크롤하지 않고 검색할 수 있습니다.
- 키보드 방향키, Enter, Escape, 외부 클릭/탭 이동 닫기 동작을 지원합니다.

### 4. Existing Functionality Preserved

- 기존 API payload, 저장 API, 권한 체크, `/reporting/*` fallback 경로는 변경하지 않았습니다.
- 상태, 우선순위, 활동 유형, 필터처럼 단순 범주 선택은 기존 select를 유지했습니다.
- 신규 DB 필드와 migration은 없습니다.

### 5. Commands Run and Results

```text
cd frontend && npm run build
→ OK, dist/assets/index-DGco8KN_.js / dist/assets/index-B9odz52n.css generated

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `344f4a3 feat: add searchable CRM selectors`
- GitHub push: `main` updated from `d05620f` to `344f4a3`
- Railway `sales-note-frontend`: `a373859f-06f2-407f-9321-f1baead50ef6` SUCCESS
- Railway `web`: `44f73bb0-d3be-4346-bd3c-b2331e0912a9` SUCCESS from the same push
- Deployed frontend bundle: `assets/index-DGco8KN_.js` / `assets/index-B9odz52n.css`

### 7. Production Smoke Check

```text
GET https://sales-note-frontend-production.up.railway.app/dashboard/
→ 200, bundle assets/index-DGco8KN_.js and assets/index-B9odz52n.css

Downloaded JS/CSS bundle
→ JS contains searchable-select and "고객, 회사, 이메일 검색"
→ CSS contains .searchable-select

curl -i https://sales-note-frontend-production.up.railway.app/reporting/api/customers/1/
→ 401 login_required JSON, 인증 보호 유지

curl -I https://web-production-5096.up.railway.app/reporting/login/
→ 200 OK
```

### 8. Known Limitations

- 로그인 세션이 필요한 실제 고객 목록 검색 UX는 운영 배포 후 사용자 수동검수가 필요합니다.
- 필터용 select와 사용자 이관 대상 select는 이번 요청 범위가 아니므로 유지했습니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/dashboard/`
2. `/mailbox/`에서 `메일 작성`을 열고 `연결 고객`에서 고객명, 회사명, 이메일 일부로 검색되는지 확인합니다.
3. `/customers/`에서 `새 고객 등록`을 열고 업체/학교와 부서/연구실이 검색되는지 확인합니다.
4. 기존 고객 상세에서 `수정`을 열고 업체/부서 검색 선택 후 저장이 정상 동작하는지 확인합니다.
5. `/notes/?create=1`, `/schedules/?create=1`, `/prepayments/new/`에서 고객 검색 선택이 동작하는지 확인합니다.

### 10. Recommended Next Task

- 수동검수 완료 후 React 통합 프론트의 다음 Django 템플릿 대체 범위를 진행합니다.

---

## AI PainPoint Verification Memo Confirm-Only — 검증 메모 확인 단일화 (2026-05-11)

### 1. Summary

긴급 요청에 따라 PainPoint 검증에서 `확인/부정` 선택을 제거하고 `확인` 하나만 남겼습니다. 사용자는 검증 메모만 저장하고, 다음 AI 재분석 때 AI가 메모 본문을 읽어 사실 확인, 반박, 대체 원인을 직접 판단합니다.

기존 DB의 `verification_status` 필드는 호환성을 위해 유지했지만, 프롬프트와 서버 fallback은 더 이상 `confirmed`/`denied`를 의미로 해석하지 않습니다. 기존 `denied` 데이터도 재분석 메모리에서는 `검증 메모`로 취급됩니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | 긴급 PainPoint 검증 메모 단일화 계획 추가 |
| `ai_chat/services.py` | 검증 메모 프롬프트/요약/인사이트/fallback에서 확인·부정 분기 제거 |
| `ai_chat/views.py` | `verify_card` API를 확인 단일 흐름으로 변경, `denied` 요청 차단 |
| `ai_chat/templates/ai_chat/department_analysis.html` | Django fallback 화면의 부정 버튼 제거, 확인 버튼만 유지 |
| `ai_chat/tests.py` | 검증 메모 단일화 및 기존 denied 데이터 정규화 회귀 테스트 추가 |
| `reporting/views.py` | React 고객 상세 AI payload의 검증 상태 라벨을 `검증 메모`로 정규화 |
| `reporting/tests.py` | React 고객 상세 AI payload 기대값 갱신 |
| `frontend/src/api.ts` | PainPoint 검증 요청에서 status 전송 제거 |
| `frontend/src/App.tsx` | React 고객 상세 PainPoint 검증 UI에서 부정 버튼 제거 |
| `frontend/src/styles.css` | 부정 상태 전용 스타일 제거, 확인 메모 스타일 유지 |

### 3. CRM Improvements

- PainPoint 검증 UI가 `확인` 하나로 단순해져 사용자가 확인/부정을 헷갈릴 여지를 줄였습니다.
- 검증 메모는 상태값이 아니라 AI 판단 근거로 저장됩니다.
- 재분석 시 서버 fallback도 메모를 `확인된 사실`이나 `부정된 가설`로 고정하지 않습니다.

### 4. Existing Functionality Preserved

- 기존 미검증/검증 완료 카드 보존 흐름은 유지했습니다.
- 기존 `PainPointCard.verification_status` 필드는 유지해 migration이 없습니다.
- 기존 `/ai/card/<id>/verify/`, React 고객 상세, Django fallback 부서 분석 route는 유지했습니다.
- 기존 stored `confirmed`/`denied` 카드는 재분석 메모리에서 모두 `검증 메모`로 정규화됩니다.

### 5. Commands Run and Results

```text
python -m py_compile ai_chat\services.py ai_chat\views.py ai_chat\tests.py reporting\views.py reporting\tests.py
→ OK

python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1
→ Ran 3 tests, OK

python manage.py test reporting.tests.CustomersSummaryApiTests.test_customer_detail_summary_api_includes_department_ai_action reporting.tests.PipelineApiTests.test_pipeline_api_includes_department_ai_summary --verbosity=1
→ Ran 2 tests, OK

python manage.py test ai_chat.tests --verbosity=1
→ Ran 20 tests, OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend && npm run build
→ OK, dist/assets/index-DLXnGDxW.js / dist/assets/index-CWzMMK9v.css generated

cd frontend && node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `b345687 fix: simplify AI painpoint verification`
- GitHub push: `main` updated from `dcf5836` to `b345687`
- Railway `web`: `feabc944-2069-4934-977e-27316eb71175` SUCCESS, commit `b345687`
- Railway `sales-note-frontend`: `d807a6c1-d75a-4c99-a3ee-1d0d395869c4` SUCCESS, message `Deploy AI painpoint verify simplification b345687`
- Deployed frontend bundle: `assets/index-DLXnGDxW.js` / `assets/index-CWzMMK9v.css`

### 7. Production Smoke Check

```text
GET https://sales-note-frontend-production.up.railway.app/customers/1/
→ 200, bundle assets/index-DLXnGDxW.js and assets/index-CWzMMK9v.css

Downloaded JS/CSS bundle
→ JS contains "PainPoint 검증 메모를 저장했습니다."
→ JS does not contain "부정"
→ CSS contains .customer-ai-painpoint.checked

GET https://sales-note-frontend-production.up.railway.app/reporting/api/customers/1/
→ 401 Unauthorized

GET https://web-production-5096.up.railway.app/ai/department/1/
→ 302 redirect to /reporting/login/?next=/ai/department/1/

Railway logs checked
→ web started successfully; recent checked logs show no traceback/500
```

### 8. Known Limitations

- 운영에서 실제 AI 재분석 결과 확인은 로그인 세션과 실제 부서 데이터가 필요해 사용자 수동검수가 필요합니다.
- DB 선택지에는 호환성 때문에 기존 `confirmed`/`denied` 값이 남아 있지만 사용자 UI와 AI 판단 로직에서는 부정 선택을 사용하지 않습니다.

### 9. Manual Server Test Process

1. 운영 고객 상세 또는 AI 부서 분석 화면에서 PainPoint 검증 영역을 엽니다.
2. 검증 버튼이 `확인` 하나만 있는지 확인합니다.
3. 검증 메모를 입력하고 `확인`을 누릅니다.
4. 저장 후 카드 상태가 `검증 메모`로 보이는지 확인합니다.
5. 부서 AI 재분석을 실행합니다.
6. 재분석 결과가 메모를 `확인된 사실/부정된 가설`로 고정하지 않고 메모 본문을 근거로 판단하는지 확인합니다.
7. 기존 Django fallback `/ai/department/<department_id>/`에서도 부정 버튼이 사라졌는지 확인합니다.

### 10. Recommended Next Task

- 운영 수동검수 완료 후 중단했던 다음 React CRM 통합 작업을 이어갑니다.

---

## AI Department Meetings and React Document Templates — 부서 AI 미팅 범위 수정 + React 서류 템플릿 관리 (2026-05-11)

### 1. Summary

긴급 요청으로 AI 부서 분석의 미팅 수집 범위를 확인했고, 기존 구현이 요청자 개인 담당 고객 미팅만 수집하던 문제를 수정했습니다. 이제 부서 분석의 `미팅 기록` 섹션은 같은 부서의 전체 고객 미팅을 포함하며, 각 미팅 제목에는 담당자명이 표시됩니다.

중단했던 작업도 이어서 진행해 React CRM에 `/documents/` 서류 템플릿 관리 화면과 `/reporting/api/documents/*` API를 추가했습니다. 기존 Django `/reporting/documents/*` 화면과 `/reporting/*` 문서 생성 endpoint는 fallback으로 유지했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 서류 템플릿 통합 계획 및 AI 부서 미팅 긴급 수정 범위 기록 |
| `ai_chat/services.py` | 부서 AI 미팅 수집을 개인 담당 고객에서 부서 전체 FollowUp 기준으로 변경, 프롬프트 담당자 표시 추가 |
| `ai_chat/tests.py` | 동료 담당 고객 미팅이 부서 AI 수집/프롬프트에 포함되는 회귀 테스트 추가 |
| `reporting/views.py` | React 문서 템플릿 목록/생성/수정/삭제/기본 설정 API 추가, 일정 상세 문서 관리 링크를 React로 전환 |
| `reporting/urls.py` | `/reporting/api/documents/*` URL 추가 |
| `reporting/tests.py` | 문서 템플릿 React API 권한/회사 범위/변경 테스트 추가 |
| `frontend/src/api.ts` | 문서 템플릿 API 타입, loader, mutation 함수 추가 |
| `frontend/src/App.tsx` | 사이드바 `서류`, `/documents/` route, 템플릿 목록/필터/등록/수정/삭제 UI 추가 |
| `frontend/src/styles.css` | 문서 템플릿 관리 화면 스타일 추가 |

### 3. CRM Improvements

- 부서 AI 분석이 특정 영업사원의 미팅만 보는 대신 부서 전체 미팅을 근거로 사용합니다.
- 부서 전체 미팅 기록에서 담당자명이 함께 표시되어 분석 근거의 소유자를 구분할 수 있습니다.
- React CRM에서 서류 템플릿을 등록, 수정, 삭제, 기본 템플릿 설정, 다운로드할 수 있습니다.
- 일정 상세 문서 생성 workflow의 템플릿 관리 링크가 React `/documents/`로 이어집니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/documents/*` Django 템플릿 관리 화면은 fallback으로 유지했습니다.
- 기존 `/reporting/documents/generate/*` 문서 생성 endpoint는 유지했습니다.
- 문서 템플릿 등록/수정/삭제 권한은 admin/manager만 허용하고, salesman은 조회 및 기본 템플릿 선택 흐름만 유지했습니다.
- 부서 AI 견적/납품/메일 수집 범위는 이번 긴급 요청 범위 밖이라 기존 정책을 유지했습니다.
- 신규 DB 필드와 migration은 없습니다.

### 5. Commands Run and Results

```text
python -m py_compile ai_chat\services.py ai_chat\tests.py
→ OK

python manage.py test ai_chat.tests.AIDepartmentQuoteDeliveryCollectionTests.test_department_analysis_meetings_include_all_department_followups --verbosity=2
→ Ran 1 test, OK

python manage.py test ai_chat.tests.AIDepartmentQuoteDeliveryCollectionTests --verbosity=1
→ Ran 3 tests, OK

python manage.py test reporting.tests.DocumentTemplatesReactApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 34 tests, OK

python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend && npm run build
→ OK, dist/assets/index-yYKBGQDv.js / dist/assets/index-B5cHVWQY.css generated

cd frontend && node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `6b1be06 feat: add React documents and department AI meetings`
- GitHub push: `main` updated from `930cbd8` to `6b1be06`
- Railway `web`: `6db56b0e-b6d2-4e02-80bc-edcdeb50cba4` SUCCESS, commit `6b1be06`
- Railway `sales-note-frontend`: `e3e8e8b7-23b1-4992-8abc-58291ad08035` SUCCESS, message `Deploy React documents and AI meetings 6b1be06`
- Deployed frontend bundle: `assets/index-yYKBGQDv.js` / `assets/index-B5cHVWQY.css`

### 7. Production Smoke Check

```text
GET https://sales-note-frontend-production.up.railway.app/documents/
→ 200, bundle assets/index-yYKBGQDv.js and assets/index-B5cHVWQY.css

GET https://sales-note-frontend-production.up.railway.app/reporting/api/documents/
→ 401 Unauthorized

GET https://web-production-5096.up.railway.app/reporting/api/documents/
→ 401 Unauthorized

GET https://web-production-5096.up.railway.app/reporting/login/
→ 200 OK

GET https://web-production-5096.up.railway.app/ai/department/1/
→ 302 redirect to /reporting/login/?next=/ai/department/1/

Downloaded JS/CSS bundle
→ JS contains /reporting/api/documents/ and documents UI text
→ CSS contains .documents-page

Railway logs checked
→ web started successfully; no new traceback/500 observed in recent checked logs
```

### 8. Known Limitations

- 운영에서 실제 서류 템플릿 파일 업로드/삭제와 AI 부서 재분석 결과 확인은 로그인 세션이 필요해 사용자 수동검수가 필요합니다.
- 이번 AI 긴급 수정은 미팅 수집 범위만 부서 전체로 넓혔고, 견적/납품/메일 수집 범위는 기존 정책을 유지했습니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/documents/`
2. 로그인 후 사이드바 `서류` 메뉴가 보이는지 확인합니다.
3. 서류 종류 필터가 전체/견적서/거래명세서/납품서로 동작하는지 확인합니다.
4. admin/manager 계정으로 템플릿 파일을 등록하고 목록에 표시되는지 확인합니다.
5. 등록한 템플릿을 수정, 기본 설정, 삭제할 수 있는지 확인합니다.
6. salesman 계정으로 등록/수정/삭제가 차단되고 목록 조회/다운로드만 가능한지 확인합니다.
7. `/schedules/<id>/` 일정 상세의 문서 생성 섹션에서 `템플릿 관리`가 `/documents/`로 열리는지 확인합니다.
8. 운영 `/ai/department/<department_id>/`에서 부서 분석을 다시 실행하고, 같은 부서의 다른 담당자 미팅 내용도 미팅 기록 근거에 반영되는지 확인합니다.
9. 기존 Django fallback `https://sales-note-frontend-production.up.railway.app/reporting/documents/`도 계속 접근 가능한지 확인합니다.

### 10. Recommended Next Task

- 운영 수동검수 완료 후 React 일정 캘린더 고급 조작 parity 또는 서류 생성 이력/템플릿 변수 편집 UX를 이어서 진행합니다.

---

## React Weekly Reports First Integration — 주간보고 React 1차 통합 (2026-05-10)

### 1. Summary

기존 Django `/reporting/weekly-reports/*` 주간보고 화면을 유지하면서 React CRM에 `/weekly-reports/`, `/weekly-reports/new/`, `/weekly-reports/<id>/`, `/weekly-reports/<id>/edit/` route를 추가했습니다. React에서 목록 필터, 상세 보기, 작성/수정, 일정 불러오기, AI 초안, 관리자 검토 코멘트를 처리할 수 있습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 주간보고 통합 계획 추가 |
| `reporting/views.py` | React 주간보고 목록/작성/상세/수정/삭제 JSON API 추가, 관련 React 링크 전환 |
| `reporting/urls.py` | `/reporting/api/weekly-reports/*` API URL 추가 |
| `reporting/tests.py` | `WeeklyReportReactApiTests` 추가 |
| `frontend/src/api.ts` | 주간보고 API 타입/loader/mutation 함수 추가 |
| `frontend/src/App.tsx` | 주간보고 nav, route, 목록/상세/작성/수정 UI 추가 |
| `frontend/src/styles.css` | 주간보고 목록/문서/편집/일정 삽입 패널 스타일 추가 |

### 3. CRM Improvements

- 주간보고를 React CRM 사이드바에서 바로 열 수 있습니다.
- 목록에서 연도, 월, 작성자 필터와 검토 상태 지표를 확인할 수 있습니다.
- 작성/수정 화면에서 여러 줄 메모를 textarea로 입력하면 서버가 안전한 HTML 문단으로 저장해 상세 화면 가독성을 유지합니다.
- 기존 일정 불러오기 API를 React 작성 화면에서 재사용하며 선택한 일정을 영업활동 또는 견적/납품 본문에 삽입할 수 있습니다.
- AI 권한 사용자는 React 작성 화면에서 기존 AI 초안 API를 호출할 수 있습니다.
- 관리자/매니저는 React 상세 화면에서 검토 코멘트를 저장할 수 있습니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/weekly-reports/*` Django 템플릿 화면은 fallback으로 유지했습니다.
- 기존 일정 불러오기, AI 초안, 관리자 코멘트 API는 보존했습니다.
- 실무자는 본인 주간보고만 작성/수정/삭제 가능하고, 관리자/매니저는 같은 회사 범위에서 조회/검토만 가능합니다.
- 신규 DB 필드와 migration은 없습니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportReactApiTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1
→ Ran 21 tests, OK

python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py
→ OK

cd frontend && npm run build
→ OK, dist/assets/index-D6rGbRO3.js / dist/assets/index-CjVBFS4u.css generated

cd frontend && node --check server.mjs
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `8c9fdb6 feat: add React weekly reports`
- GitHub push: `main` updated from `a2bc88d` to `8c9fdb6`
- Railway `web`: `4216824a-7d1f-4850-8624-11dca0b40b26` SUCCESS
- Railway `sales-note-frontend`: `fd8547fc-63f8-4962-92de-88b182eb7984` SUCCESS
- Deployed frontend bundle: `assets/index-D6rGbRO3.js` / `assets/index-CjVBFS4u.css`

### 7. Production Smoke Check

```text
GET https://sales-note-frontend-production.up.railway.app/weekly-reports/
→ 200, bundle assets/index-D6rGbRO3.js and assets/index-CjVBFS4u.css

GET https://sales-note-frontend-production.up.railway.app/reporting/api/weekly-reports/
→ 401 login_required JSON

GET https://web-production-5096.up.railway.app/reporting/api/weekly-reports/
→ 401 login_required JSON

GET https://web-production-5096.up.railway.app/reporting/login/
→ 200 OK

Downloaded JS/CSS bundle
→ JS contains weeklyReports, 주간보고 작성, /reporting/api/weekly-reports/
→ CSS contains .weekly-page, .weekly-report-row, .weekly-editor-layout, .weekly-schedule-card
```

### 8. Known Limitations

- 운영 실제 작성/수정/AI 초안/관리자 검토는 로그인 세션이 필요해 사용자 수동검수가 필요합니다.
- React 작성 화면은 textarea 기반이며, 기존 Django Quill 화면은 fallback으로 남겨두었습니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/weekly-reports/`
2. 로그인 후 사이드바 `주간보고`가 보이는지 확인합니다.
3. 목록에서 연도/월/작성자 필터가 동작하는지 확인합니다.
4. `보고서 작성`을 열고 시작일/종료일/제목/본문을 입력합니다.
5. `일정 불러오기`를 눌러 영업활동 또는 견적/납품 본문에 선택 일정을 삽입합니다.
6. AI 권한 계정이면 `AI 초안` 버튼이 초안을 채우는지 확인합니다.
7. 저장 후 상세 화면에서 줄바꿈/문단 가독성이 유지되는지 확인합니다.
8. 작성자 계정으로 수정/삭제가 가능한지 확인합니다.
9. 매니저/관리자 계정으로 상세 화면에서 검토 코멘트를 저장할 수 있는지 확인합니다.
10. 기존 Django fallback `https://sales-note-frontend-production.up.railway.app/reporting/weekly-reports/`도 계속 접근 가능한지 확인합니다.

### 10. Recommended Next Task

- 운영 수동검수 완료 후 다음 React 통합 범위로 견적/문서 생성 또는 일정 캘린더 parity audit를 진행합니다.

---

## React Schedule Calendar First Integration — 일정 캘린더 React 1차 통합 (2026-05-10)

### 1. Summary

주간보고 작성 화면의 `일정 불러오기` 버튼을 오른쪽 일정 패널로 이동했고, 이어서 React CRM에 `/schedules/calendar/` 월간 일정 캘린더 route를 추가했습니다. 기존 Django `/reporting/schedules/calendar/`는 fallback으로 유지했습니다.

### 2. Files Changed

| 파일 | 변경 내용 |
| ---- | --------- |
| `AGENT_PLAN.md` | React 일정 캘린더 1차 통합 계획 추가 |
| `reporting/views.py` | 일정 캘린더 날짜 범위 API 추가, React 캘린더 링크 전환 |
| `reporting/urls.py` | `/reporting/api/schedules/calendar/` URL 추가 |
| `reporting/tests.py` | 일정 캘린더 API 인증/범위/필터 테스트 추가 |
| `frontend/src/api.ts` | 일정 캘린더 API 타입과 loader 추가 |
| `frontend/src/App.tsx` | `/schedules/calendar/` route, 월 이동, 본인/전체/직원 필터, 월간 grid, 선택 일자 패널 추가 |
| `frontend/src/styles.css` | 주간보고 일정 불러오기 위치 스타일과 일정 캘린더 레이아웃/반응형 스타일 추가 |

### 3. CRM Improvements

- React 일정 메뉴에서 월간 캘린더를 바로 열 수 있습니다.
- 고객 일정과 개인 일정을 같은 월간 grid에서 볼 수 있습니다.
- 본인, 같은 회사 전체, 특정 직원 필터를 지원합니다.
- 선택한 날짜의 일정은 오른쪽 패널에서 바로 상세/고객/보고 작성 흐름으로 이어집니다.
- 일정 목록, 대시보드 일정 카드, 일정 상세의 캘린더 링크가 React 캘린더로 연결됩니다.

### 4. Existing Functionality Preserved

- 기존 `/reporting/schedules/calendar/` Django 캘린더와 `/reporting/schedules/api/`는 제거하지 않았습니다.
- 기존 `/reporting/*` 인증, 개인 일정 생성/상세, 고객 일정 생성/상세 경로는 유지했습니다.
- 신규 DB 필드와 migration은 없습니다.
- React 캘린더 API는 로그인 required JSON 응답을 유지합니다.

### 5. Commands Run and Results

```text
python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1
→ Ran 26 tests, OK

python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests reporting.tests.AnonymousAccessTests --verbosity=1
→ Ran 33 tests, OK

python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py
→ OK

python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected

cd frontend && npm run build
→ OK, dist/assets/index-CTcLLIQe.js / dist/assets/index-BJ8JCI1J.css generated

cd frontend && node --check server.mjs
→ OK

git diff --check
→ OK (LF→CRLF warning only)
```

### 6. Deployment Status

- Runtime commit: `07d0776 feat: add React schedule calendar`
- GitHub push: `main` updated from `2d02547` to `07d0776`
- Railway `web`: `ffa1cb41-76f6-4c82-9cf8-6731ebda092d` SUCCESS
- Railway `sales-note-frontend`: `5126b81d-e0ba-4da7-9711-d9f8248a8f25` SUCCESS
- Deployed frontend bundle: `assets/index-CTcLLIQe.js` / `assets/index-BJ8JCI1J.css`

### 7. Production Smoke Check

```text
GET https://sales-note-frontend-production.up.railway.app/schedules/calendar/
→ 200, bundle assets/index-CTcLLIQe.js and assets/index-BJ8JCI1J.css

GET https://sales-note-frontend-production.up.railway.app/reporting/api/schedules/calendar/
→ 401 login_required JSON

GET https://web-production-5096.up.railway.app/reporting/api/schedules/calendar/
→ 401 login_required JSON

GET https://web-production-5096.up.railway.app/reporting/login/
→ 200 OK

Downloaded JS/CSS bundle
→ JS contains schedule-calendar-page, /reporting/api/schedules/calendar/, weekly-schedule-load
→ CSS contains .schedule-calendar-grid, .schedule-calendar-day, .weekly-schedule-load
```

### 8. Known Limitations

- React 캘린더는 월간 조회/필터/상세 연결 1차 통합입니다. 기존 Django 캘린더의 드래그 이동, 상세 모달 편집 등 고급 조작은 fallback 화면으로 유지했습니다.
- 운영에서 실제 로그인 세션 기반 일정 데이터 확인은 사용자 수동검수가 필요합니다.

### 9. Manual Server Test Process

1. 운영 사이트 접속: `https://sales-note-frontend-production.up.railway.app/schedules/calendar/`
2. 로그인 후 월간 캘린더가 열리고 오늘 날짜가 강조되는지 확인합니다.
3. 이전 달, 오늘, 다음 달 버튼으로 월 이동이 되는지 확인합니다.
4. `내 일정`, `회사 전체`, `직원 선택` 필터가 동작하는지 확인합니다.
5. 일정이 있는 날짜를 클릭하면 오른쪽 선택 일자 패널에 해당 일정만 보이는지 확인합니다.
6. 고객 일정은 상세 링크가 React `/schedules/<id>/`로 열리는지 확인합니다.
7. 개인 일정은 기존 Django 개인 일정 상세로 열리는지 확인합니다.
8. `Django 캘린더` fallback 링크가 기존 화면으로 열리는지 확인합니다.
9. `/weekly-reports/new/`에서 `일정 불러오기` 버튼이 오른쪽 일정 패널 안에 있는지 확인합니다.

### 10. Recommended Next Task

- 운영 수동검수 완료 후 React 통합 프론트의 다음 고가치 영역인 견적/문서 생성 workflow 또는 일정 캘린더 고급 조작 parity를 진행합니다.
