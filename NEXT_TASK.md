# NEXT_TASK.md

## 다음 시작 작업

**작업명**: `/assets/` 직접 장비 등록 UX 운영 배포 및 로그인 세션 수동검수

**상태**: `/assets/` 직접 `장비 등록` CTA/고객 선택/장비 생성/새 장비 드로어 자동 선택은 로컬 구현 및 로컬 Playwright smoke 완료. Railway가 현재 접속 불가라서 커밋/푸시/배포/운영 smoke는 보류 상태입니다.

## 왜 이 작업인가

- 사용자는 당분간 Railway 대신 로컬에서 작업하자고 지시했습니다.
- 이전 `/assets/` 운영형 V2의 가장 큰 UX gap은 신규 장비를 고객 상세에서만 만들 수 있다는 점이었습니다.
- 이번 로컬 배치에서 `/assets/` 직접 등록 흐름을 추가했으므로, Railway 복구 후 운영 배포와 로그인 세션 검수가 필요합니다.

## 다음 세션 시작 순서

1. Railway 접근 가능 여부를 먼저 확인합니다.
2. Railway가 아직 불안정하면 로컬에서만 이어서 검수합니다.
3. 로컬 확인 시 `python manage.py runserver 127.0.0.1:8000`과 `cd frontend; npm run dev -- --host 127.0.0.1 --port 5173`을 실행합니다.
4. 로그인 후 `http://127.0.0.1:5173/assets/`에서 `장비 등록`을 누릅니다.
5. 고객 선택, 장비 생성, URL `asset=<id>` 반영, 새 장비 드로어 자동 선택을 확인합니다.
6. manager 계정에서 `장비 등록` CTA가 숨겨지는지 확인합니다.
7. Railway가 복구되면 변경 사항을 커밋/푸시하고 `web`/`sales-note-frontend` 배포 및 운영 smoke를 수행합니다.

## 이번 로컬 배치 구현 내용

- `/reporting/api/customer-assets/`에 `canManage`, 읽기 전용 message, 직접 등록용 `create.customers` 추가
- 직접 등록은 기존 `/reporting/api/customers/<followup_id>/assets/create/` 저장 API 재사용
- `/assets/` 상단 `장비 등록` CTA 추가
- 고객/FollowUp 검색 선택 후 장비 기본 정보를 저장하는 인라인 패널 추가
- 저장 후 필터 초기화 및 새 장비 선택
- focused Django API tests 추가

## 검증 완료

- `python -m py_compile reporting\views.py reporting\urls.py reporting\tests.py`
- `python manage.py test` focused customer asset API 4건
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- `cd frontend; node --check server.mjs`
- `git diff --check`
- Local Playwright smoke for `/assets/` direct create

## 주의사항

- Django template 파일 삭제는 아직 하지 않습니다.
- `/reporting/*` API/session/auth 흐름은 유지합니다.
- `public_site`는 이번 React CRM 전환 범위가 아닙니다.
- Railway 복구 전에는 운영 배포 상태를 완료로 쓰지 않습니다.
- 직접 등록 고객 목록은 현재 최근/접근 가능 고객 160건입니다. 고객 수가 많아지면 remote autocomplete 보강을 다음 후보로 잡습니다.

## 권장 다음 작업

Railway 복구 즉시 이번 로컬 변경을 커밋/푸시/배포하고 운영 로그인 세션에서 `/assets/` 직접 등록, 기존 장비 수정, 서비스 접수/수정, 교정 기록/수정, 파일 다운로드, manager 읽기 전용 상태를 수동 검수합니다.
