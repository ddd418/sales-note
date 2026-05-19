# NEXT_TASK.md

## 다음 시작 작업

**작업명**: React CRM 전환 2차 배치 준비

**상태**: 1차 핵심 CRM redirect cutover 구현/로컬 검증 완료. 커밋/푸시/Railway 배포와 운영 수동검수 후 다음 작업으로 넘어갑니다.

## 왜 이 작업인가

- 사용자는 Django 템플릿 프론트를 빠르게 닫고 React CRM을 안정화하길 원합니다.
- 1차 범위는 dashboard, customers/followups, notes/histories, schedules, pipeline입니다.
- 다음 단계는 남은 React 이관 화면의 legacy GET 진입을 닫는 것입니다.

## 다음 세션 시작 순서

1. 먼저 1차 배포 운영 수동검수 결과를 확인합니다.
2. 문제가 있으면 1차 redirect mapping 또는 React 링크 정규화를 먼저 수정합니다.
3. 검수 완료 후 2차 배치 범위를 확정합니다.

## 2차 후보 범위

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

- focused redirect/auth tests
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend; node --check server.mjs`
- `cd frontend; npx tsc --noEmit --pretty false`
- `cd frontend; npm run build`
- runtime 변경 시 commit/push/Railway 배포/smoke

## 주의사항

- 사용자의 운영 수동검수 확인 전에는 다음 구현 배치를 시작하지 않습니다.
- Django template 파일 삭제는 별도 cleanup 단계에서만 진행합니다.
- `public_site`는 이번 React CRM 전환 범위가 아닙니다.
