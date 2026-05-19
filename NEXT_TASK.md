# NEXT_TASK.md

## 다음 시작 작업

**작업명**: Customer Asset Directory V2 운영 수동검수 및 `/assets/` 직접 장비 등록 UX 보강

**상태**: `/assets/` 운영형 V2 구현, 커밋/푸시, Railway `web`/`sales-note-frontend` 배포, 익명 smoke 완료. 사용자 로그인 세션 수동검수 대기입니다.

## 왜 이 작업인가

- 사용자는 Django 템플릿 프론트를 빠르게 닫고 React CRM을 안정화하길 원합니다.
- 글로벌 CRM 벤치마크 기준으로 고객 장비/A/S/교정 운영성이 우선순위로 확인되었습니다.
- 이번 배치에서 React `/assets/`가 검색 전용에서 장비 운영 콘솔로 확장되었으므로, 실제 로그인 계정에서 저장/업로드/다운로드를 확인해야 합니다.
- 사용자가 확인한 UX gap: 신규 장비 추가가 아직 고객 상세의 `장비 등록`에서만 가능하고 `/assets/`에는 직접 등록 CTA/고객 선택 폼이 없습니다. 다음 작업자는 이 보강을 우선 검토합니다.

## 다음 세션 시작 순서

1. 먼저 사용자 운영 수동검수 결과를 확인합니다.
2. `https://sales-note-frontend-production.up.railway.app/assets/`에서 장비 목록/작업 큐/상세 드로어가 보이는지 확인합니다.
3. 장비 수정, 서비스 접수/수정, 교정 기록/수정, 파일 업로드/다운로드를 실제 데이터 1건으로 확인합니다.
4. 매니저 계정에서 조회만 가능하고 수정 UI가 숨겨지는지 확인합니다.
5. `/assets/`에서 직접 `장비 등록` 버튼을 제공하고 고객/담당자를 검색 선택해 생성하는 API/UI를 추가할지 우선 결정합니다.
6. 통과하면 다음 React 안정화 배치를 확정합니다.

## 우선 보강 후보

- `/assets/` 상단에 `장비 등록` CTA 추가
- 고객/FollowUp 검색 또는 선택 API 재사용
- 선택한 고객의 company/department/primary_followup 기준으로 `CustomerAsset` 생성
- 기존 고객 상세 `customer_asset_save_api` 권한 규칙과 동일하게 manager는 차단
- 생성 후 `asset=<id>`로 새 장비 드로어 자동 선택

## 다음 React 안정화 후보 범위

- products
- prepayments
- weekly reports
- documents
- mailbox / business cards
- profile
- 개인 일정 보조 화면

## 구현 방향

- Django 템플릿 삭제는 아직 하지 않습니다.
- 각 legacy `GET/HEAD` 화면에 React replacement가 있으면 redirect로 닫습니다.
- `/reporting/api/*`, 파일 다운로드, export, OAuth, send/sync/upload/delete 같은 민감 action은 redirect 대상에서 제외합니다.
- React 내부에서 `Django` CTA로 보이는 핵심 업무 링크는 React route 또는 실제 필요한 backend action 링크로 정리합니다.

## 검증 기준

- 사용자 로그인 세션에서 `/assets/` 수동검수 통과
- focused asset API tests
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; node --check server.mjs`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- runtime 변경 시 commit/push/Railway 배포/smoke

## 주의사항

- 사용자의 운영 수동검수 확인 전에는 다음 구현 배치를 시작하지 않습니다.
- Django template 파일 삭제는 별도 cleanup 단계에서만 진행합니다.
- `web-production-2cc17.up.railway.app` public domain 제거는 프론트 proxy가 private backend URL로 안정화된 뒤 진행합니다.
- `public_site`는 이번 React CRM 전환 범위가 아닙니다.
