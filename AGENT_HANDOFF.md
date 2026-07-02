# Sales Note 인수인계서

작성일: 2026-07-03  
저장소: `D:\projects\sales-note`  
현재 운영 프론트: https://sales-note-frontend-production.up.railway.app/  
현재 운영 백엔드: https://web-production-8a820.up.railway.app/

## 1. 프로젝트 성격

이 저장소는 공개 홈페이지가 아니라 내부 영업 CRM / 영업보고 시스템이다.

- Django `reporting` 앱이 핵심 백엔드다.
- React `frontend/`가 사용자-facing CRM 화면을 맡는 방향이다.
- `/reporting/*`는 로그인, API, legacy fallback, backend route 유지를 위해 아직 보존해야 한다.
- Django 템플릿은 장기적으로 제거 대상이지만, React 기능 대체와 운영 수동 확인 전에는 삭제하면 안 된다.
- 내부 영업 데이터, 고객 데이터, 메일/문서/선결제 정보가 있으므로 인증과 권한을 절대 약화하면 안 된다.

## 2. 반드시 먼저 읽을 문서

작업 전 아래 순서로 확인한다.

1. `.github/copilot-instructions.md`
2. `PROJECT_BRIEF.md`
3. `SALES_CRM_SPEC.md`
4. `QA_CHECKLIST.md`
5. `README.md`
6. `AGENT_PLAN.md`
7. `AGENT_REPORT.md`
8. 관련 Django settings / urls / models / views / API / React page

## 3. 현재 Git 상태

- 현재 기준 최근 원격 반영 커밋:
  - `02c18f0` `Record dashboard revenue deployment`
  - `a653ac5` `Include prepayments in dashboard revenue`
  - `3b21476` `Record reports quote sort deployment`
  - `9c03f60` `Add reports quote item sorting`
- 작업 트리에 기존 미추적 폴더 `output/`가 있다. 이번 작업들과 무관하므로 임의로 삭제하거나 커밋하지 않는다.
- 브랜치는 보통 `main`에서 작업해 왔다.

## 4. 최근 완료 작업

### 4.1 대시보드 매출에 선결제 포함

사용자 요청: `대시보드에 나오는 매출은 선결제도 포함되어야함`

완료 내용:

- React `/dashboard/` 매출 카드의 `yearRevenue`, `quarterRevenue`, `monthlyRevenue`에 선결제 입금액을 포함했다.
- Django `/reporting/api/dashboard/`에서 기존 납품 품목 합계에 `Prepayment.amount`를 더한다.
- 선결제 기간 기준은 `Prepayment.payment_date`다.
- 취소 선결제(`status='cancelled'`)는 제외한다.
- 권한 범위는 기존 대시보드 `scope_users`를 그대로 따른다.
- 프론트 문구는 `납품·선결제 기준`으로 변경했다.

주의:

- 현재 대시보드 매출 정의는 `납품 품목 합계 + 취소되지 않은 선결제 입금액`이다.
- 같은 선결제가 나중에 납품 차감으로도 잡히면 입금 흐름과 납품 흐름이 모두 매출 카드에 반영될 수 있다. 이는 사용자가 요청한 기준대로 반영한 것이다.
- 납품분/선결제분 breakdown은 아직 화면에 없다.

운영 배포:

- Backend Railway deployment: `e20a18c3-2ed2-4bcd-ab70-28e3b409d49e` SUCCESS
- Frontend Railway deployment: `284fc0e6-c0a5-4221-a593-7f3edcedf9ba` SUCCESS
- Smoke: OK

수동 확인 대기:

- `/dashboard/`에서 당해년도/분기/월 매출 카드가 선결제를 포함하는지 사용자가 직접 확인해야 한다.

### 4.2 Reports 견적품목 있음 정렬

사용자 요청: `/reports/`에서 `견적품목 있음`도 sorting 가능하게.

완료 내용:

- React `/reports/` 필터 영역에 `정렬` 드롭다운 추가.
- `최근 활동순`, `견적품목 있음` 옵션 제공.
- Django reports API가 `sort=quote_items`를 받으면 실제 견적 품목이 있는 계정을 우선 정렬한다.
- 공통 계정 원장에 `quoteItemCount`를 추가했다.
- 엑셀 다운로드 링크에도 정렬 query가 유지된다.

운영 배포:

- Backend Railway deployment: `a11d4f02-45a1-4570-be7a-57264e8d83f3` SUCCESS
- Frontend Railway deployment: `d307d7d1-cc44-41b2-8361-dc31f545bcba` SUCCESS
- Smoke: OK

수동 확인 대기:

- `/reports/`에서 정렬을 `견적품목 있음`으로 바꾸고 실제 견적 품목 있는 계정이 상단으로 올라오는지 확인해야 한다.

### 4.3 파이프라인 동일 연구실 담당자 분리 표시 수정

관련 운영 사례:

- `/schedules/927/` 김혜란 교수 견적
- `/schedules/936/` 김종환 연구원 납품
- 둘 다 `department_id=410`, 강원대학교 / 식물세포및유전공학연구실 계정으로 확인됨.

완료 내용:

- React `/pipeline/` API가 개별 `FollowUp`이 아니라 가능한 한 `Department` 계정 기준으로 카드를 묶도록 변경했다.
- 같은 계정에 수주/납품이 있으면 견적 단계보다 수주가 우선된다.
- 파이프라인 수동 이동은 같은 계정 내 접근 가능한 담당자들에게 함께 적용된다.

운영 배포:

- Backend Railway deployment: `cc2458b4-4a85-4fa6-9a4a-31030eff26f4` SUCCESS
- Frontend는 당시 watch 파일 변경 없음으로 SKIPPED.

수동 확인 대기:

- `/pipeline/`에서 같은 연구실 담당자가 분리 카드로 보이지 않는지 확인해야 한다.

### 4.4 Schedule 947 선결제 차감 저장 오류 수정

사용자 요청:

- `/schedules/947/`에서 납품 입력 후 선결제 차감 시 저장이 안 됨.

완료 내용:

- PostgreSQL `FOR UPDATE cannot be applied to the nullable side of an outer join` 문제 수정.
- 선결제 row lock query에 `select_for_update(of=('self',))` 적용.
- 모델 변경 없음.

운영 배포 완료, smoke OK.

## 5. 중요한 업무 규칙

### 5.1 계정 기준

- 가능한 한 고객/거래처 기록은 개별 담당자 `FollowUp`보다 `Department` 즉 업체/부서/연구실 계정 기준으로 봐야 한다.
- 같은 연구실 안의 담당자가 바뀌어도 납품, 견적, 선결제, 장비, 서비스 기록은 같은 계정 이력으로 보는 게 현재 방향이다.

### 5.2 일정과 파이프라인 동기화

사용자 요구:

- 일정에서 변경된 내용은 파이프라인에 반영되어야 한다.
- 파이프라인에서 수동으로 변경한 내용은 일정으로 역동기화될 필요 없다.

현재 방향:

- schedule status/activity changes -> pipeline 반영.
- pipeline manual stage move -> pipeline card/stage만 조정.
- 이미 `won`인 계정은 quote cancel 등으로 함부로 lost로 덮지 않도록 주의한다.

### 5.3 선결제 판단

- 선결제 차감 납품은 메모 텍스트 추정이 아니라 구조화 필드로만 확정한다.
- 우선 기준:
  - `Schedule.delivery_payment_type`
  - `Schedule.delivery_payment_status`
  - `Schedule.use_prepayment`
  - `Schedule.prepayment`
  - `Schedule.prepayment_amount`
  - `PrepaymentUsage`
- AI / Reports / Receivables / Account ledger 모두 이 기준을 흔들면 안 된다.

### 5.4 Django 프론트 제거

사용자가 Django 프론트를 없애고 싶어했지만, 현재 결론은 바로 삭제하면 위험하다.

- Django는 backend/API/login/legacy fallback 역할을 계속 가진다.
- React feature parity가 확인된 화면만 Django template 제거 후보가 된다.
- 삭제 전에는 URL 참조 검색, 권한 체크, POST 동작 대체, 운영 수동 확인이 필요하다.

## 6. 주요 파일 지도

### Backend

- `reporting/models.py`
  - `FollowUp`, `Department`, `Schedule`, `DeliveryItem`, `Quote`, `QuoteItem`, `Prepayment`, `PrepaymentUsage`
- `reporting/views.py`
  - React dashboard API: `dashboard_summary_api`
  - schedule detail/update 관련 API 다수
- `reporting/funnel_views.py`
  - pipeline API / 계정 단위 파이프라인 집계
- `reporting/account_ledger.py`
  - 계정별 납품/견적/선결제 공통 원장
- `reporting/api/reports.py`
  - React reports API
- `reporting/api/prepayments.py`
  - React prepayments API
- `reporting/api/receivables.py`
  - 외상/세금계산서 관련 API
- `reporting/tests.py`
  - 현재 대부분의 회귀 테스트가 여기에 모여 있다.

### Frontend

- `frontend/src/App.tsx`
  - 큰 통합 React 앱. 아직 많은 화면 로직이 들어 있다.
- `frontend/src/DashboardApp.tsx`
  - dashboard standalone/lazy entry 성격.
- `frontend/src/api/dashboard.ts`
  - dashboard API client/type.
- `frontend/src/api/reports.ts`
  - reports API client/type.
- `frontend/src/pages/reports/ReportsPage.tsx`
  - reports 화면.
- `frontend/src/components/shared/`
  - CRM shell, metric card, formatter, feedback states.

## 7. 자주 쓰는 검증 명령

```powershell
py -3.13 -m py_compile reporting\views.py reporting\tests.py
py -3.13 manage.py check
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py test reporting.tests.DashboardSummaryApiTests --keepdb --verbosity=1
py -3.13 manage.py test reporting.tests.ReactReportsProfileBusinessCardApiTests --keepdb --verbosity=1
py -3.13 manage.py test reporting.tests.PipelineApiTests --keepdb --verbosity=1
cd frontend
npm run build
node --check server.mjs
```

운영 smoke:

```powershell
py -3.13 scripts\post_deploy_smoke.py --backend-url https://web-production-8a820.up.railway.app --frontend-url https://sales-note-frontend-production.up.railway.app
```

## 8. 배포 절차

런타임 변경이면 보통 다음 순서를 따른다.

1. `AGENT_PLAN.md` 업데이트.
2. 코드 변경.
3. focused test 실행.
4. `manage.py check`, migration dry-run, frontend build 실행.
5. `AGENT_REPORT.md` 업데이트.
6. 변경 파일만 명시적으로 `git add`.
7. commit.
8. `git push origin main`.
9. Railway deployment 확인:
   - `railway deployment list --service web --environment production --limit 5 --json`
   - `railway deployment list --service sales-note-frontend --environment production --limit 5 --json`
10. 배포 완료까지 polling.
11. `scripts\post_deploy_smoke.py` 실행.
12. `AGENT_PLAN.md`, `AGENT_REPORT.md`에 deployment ID와 smoke 결과 기록.
13. docs-only 기록 커밋/푸시.
14. 사용자에게 운영 수동 테스트 절차를 안내하고, 확인 전 다음 구현 작업은 시작하지 않는다.

문서만 바꾸는 경우 Railway 배포는 보통 SKIPPED이며 runtime 배포는 필요 없다.

## 9. 운영 수동 확인 대기 항목

아래는 최근 배포 후 사용자가 직접 확인해야 하는 항목이다.

1. `/dashboard/`
   - 당해년도/분기/월 매출이 선결제 입금액을 포함하는지.
   - 취소된 선결제가 빠지는지.
   - 카드 설명이 `납품·선결제 기준`인지.
2. `/reports/`
   - 정렬 `견적품목 있음` 선택 시 견적 품목 있는 계정이 먼저 올라오는지.
   - 검색/날짜/업체/부서 필터와 함께 사용해도 정렬이 유지되는지.
3. `/pipeline/`
   - 같은 연구실 담당자 변경 건이 계정 하나로 보이는지.
   - 일정에서 완료/취소한 상태가 파이프라인에 반영되는지.
4. `/schedules/947/`
   - 납품 품목 저장 + 선결제 차감 저장이 정상 동작하는지.

## 10. 다음 작업 후보

사용자 확인 후 우선순위가 높은 후보:

- 대시보드 매출 카드에 납품분/선결제분 breakdown 표시.
- Reports에서 `견적품목 있음`을 정렬이 아니라 필터로도 제공할지 검토.
- Django template 제거 가능 화면 inventory 작성.
- 일정 상태 변경 -> 파이프라인 동기화 회귀 테스트 확대.
- 담당자 변경/계정 병합 관련 운영 데이터 정리 도구 또는 관리자 화면 개선.

## 11. 주의할 것

- `output/` 폴더는 기존 미추적 산출물이다. 건드리지 않는다.
- secrets, Railway env, 이메일 비밀번호, API key는 절대 커밋하지 않는다.
- 내부 데이터를 외부 공개 route로 노출하지 않는다.
- `git reset --hard`, `git checkout --` 같은 되돌리기 명령은 사용자 요청 없이는 쓰지 않는다.
- 프론트 문구를 바꿀 때는 `frontend/src/App.tsx`와 `frontend/src/DashboardApp.tsx`에 중복 구현이 있는지 확인한다.
- 대시보드나 리포트 금액 산식 변경은 반드시 테스트에 실제 `Prepayment`, `DeliveryItem` 데이터를 같이 넣어 검증한다.
