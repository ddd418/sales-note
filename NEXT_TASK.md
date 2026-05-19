# NEXT_TASK.md

## 다음 시작 작업

**작업명**: 장비/글로벌 기능 및 AI 액션 통합 재개

**상태**: 구현 중단분이 stash에 보관되어 있음.

```text
stash@{0}: wip-asset-ai-action-integration-before-memory-hotfix
```

## 왜 이 작업인가

- 사용자가 AI hotfix 때문에 잠깐 멈추라고 요청하기 전 진행 중이던 작업입니다.
- 목표는 장비를 포함한 글로벌 기능을 확장하기 전에, 장비/서비스/교정 데이터가 AI 워크스페이스와 React CRM 흐름에서 제대로 활용되도록 정리하는 것입니다.
- 이후 글로벌 기능 추가, Django 메뉴 선별/React 이관, 장비 관련 고객 흐름 확장을 이어갈 수 있습니다.

## 다음 세션 시작 순서

1. 사용자에게 이번 AI 메일/기억 hotfix 운영 수동검수 결과를 먼저 확인합니다.
2. 검수 완료 또는 진행 지시가 있으면 stash 내용을 먼저 확인합니다.

```powershell
git stash show --stat stash@{0}
git stash show -p stash@{0}
```

3. 최신 `main` 기준으로 stash를 적용합니다.

```powershell
git stash apply stash@{0}
```

4. 충돌이 있으면 `reporting/views.py`, `reporting/tests.py`를 특히 주의해서 병합합니다. 이번 세션에서 AI 메일/기억 필터 로직이 추가됐기 때문입니다.
5. 변경 범위가 여전히 아래 파일 중심인지 확인합니다.

```text
AGENT_PLAN.md
frontend/src/App.tsx
frontend/src/api.ts
reporting/tests.py
reporting/views.py
```

## 구현 방향

- 장비/서비스/교정 데이터는 Django 모델과 API를 기준으로 사용합니다.
- React는 고객/AI/글로벌 화면에서 필요한 데이터만 호출하도록 유지합니다.
- AI 액션 큐는 이미 해결된 메일/검수 기억/최근 연락 필터와 충돌하지 않아야 합니다.
- 고객 상세 화면에 별도 Department AI 사이드 패널을 다시 넣지 않습니다. 고객 상세 AI는 제거하기로 한 사용자 결정이 우선입니다.

## 검증 기준

- `python -m py_compile reporting\views.py reporting\tests.py`
- 관련 AI Workspace focused tests
- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- frontend 변경이 있으면 `cd frontend; npx tsc --noEmit --pretty false`
- 런타임 영향이 있으면 commit/push/Railway 배포/smoke까지 진행합니다.

## 주의사항

- stash 적용 전에 새 작업을 시작하지 않습니다.
- 사용자 수동검수 대기 상태라면 먼저 확인을 받고 진행합니다.
- unrelated stash는 건드리지 않습니다.
- `public_site`는 이번 작업 범위가 아닙니다.
