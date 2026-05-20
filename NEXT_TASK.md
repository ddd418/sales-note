# NEXT_TASK.md

## 다음 시작 작업

**작업명**: `/assets/` 직접 장비 등록 UX 운영 수동검수

**상태**: 구현, 로컬 검증, GitHub push, Railway `web`/`sales-note-frontend` 배포, 운영 smoke 완료. 사용자 운영 로그인 세션 수동검수 대기.

## 배포 요약

- 런타임 기능 커밋: `d0dd3c6 feat: add asset directory direct create`
- 프론트 Railway GitHub 배포 보정:
  - `b0c82f8 fix: pin frontend railway node runtime`
  - `df84b41 fix: configure frontend railway start command`
- Railway 최종 검증 배포:
  - `web`: `50d7f9ce-dad6-4327-92ac-6d9d84221ef5`, SUCCESS
  - `sales-note-frontend`: `b1457f47-b9e8-4c53-a848-4d4d1f77eb8f`, SUCCESS
- 운영 smoke:
  - `https://sales-note-frontend-production.up.railway.app/assets/` 200
  - 최신 JS bundle 200, `장비 등록`/`assetCreateUrl` marker 확인
  - anonymous `/reporting/api/customer-assets/` 401 `login_required`
  - `/reporting/login/` 200

## 사용자 운영 수동검수 절차

1. `https://sales-note-frontend-production.up.railway.app/assets/` 접속 후 로그인합니다.
2. `/assets/` 상단의 `장비 등록` 버튼이 보이는지 확인합니다.
3. 고객/FollowUp을 검색 선택하고 장비명, 모델, 시리얼, 설치 위치를 입력해 저장합니다.
4. 저장 후 URL에 `asset=<id>`가 붙고 새 장비 행과 오른쪽 상세 드로어가 자동 선택되는지 확인합니다.
5. 새 장비에서 장비 정보 수정, A/S 케이스 등록/수정, 교정 기록 등록/수정 화면이 기존처럼 동작하는지 확인합니다.
6. manager 계정에서는 `장비 등록` 버튼이 보이지 않고 수정 액션이 차단되는지 확인합니다.

## 주의사항

- Django template 삭제는 아직 하지 않습니다.
- `/reporting/*` API/session/auth 흐름은 유지합니다.
- `public_site`는 이번 React CRM 전환 범위가 아닙니다.
- 직접 등록 고객 목록은 현재 최근/접근 가능 고객 160건입니다. 고객 수가 많아지면 remote autocomplete 보강을 다음 후보로 잡습니다.
- 수동검수 확인 전에는 다음 구현 작업을 시작하지 않습니다.

## 권장 다음 작업

사용자 운영 수동검수 통과 후 `/assets/` 고객 선택을 remote autocomplete로 확장하거나, 장비 등록 이후 A/S 접수까지 이어지는 빠른 작업 흐름을 보강합니다.
