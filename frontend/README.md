# Sales Note Frontend Pilot

React/Vite 기반 프론트 분리 파일럿입니다.

현재 목적은 React를 CRM의 메인 Shell로 세우고 핵심 메뉴를 단계적으로 프론트로 이관하는 것입니다. `/dashboard/`는 `/reporting/api/dashboard/`, `/customers/`는 `/reporting/api/customers/`, `/notes/`는 `/reporting/api/notes/`, `/schedules/`는 `/reporting/api/schedules/`, `/ai-workspace/`는 `/reporting/api/ai-workspace/`의 실제 Django CRM 데이터를 사용합니다. 기존 Django 일정 캘린더(`/reporting/schedules/calendar/`)는 React 일정 화면의 보조 링크로 유지합니다. 파이프라인은 `/reporting/api/pipeline/`이 응답하면 실제 데이터를 사용하고, 파이프라인 API가 응답하지 않을 때만 `src/mockData.ts`의 mock data로 fallback합니다.

## 실행

```bash
cd frontend
npm install
npm run dev
```

로컬 URL:

```text
http://127.0.0.1:5173/
```

## 범위

- 프론트 CRM Shell 및 좌측 핵심 내비게이션
- `/dashboard/` 실제 데이터 대시보드
- `/customers/` 실제 고객 검색/필터 화면
- `/notes/` 실제 영업노트 검색/필터 화면
- `/schedules/` 실제 일정 검색/필터 화면
- `/ai-workspace/` 실제 AI 업무 상태 화면
- `/pipeline/` route shell
- 대시보드 KPI, 오늘 일정, 지연 후속조치, 최근 영업노트, 우선 고객
- Kanban/List 전환
- 고객 상세 패널
- 모바일 대응 기본 레이아웃
- Django dashboard API 우선 조회
- Django customers API 우선 조회
- Django notes API 우선 조회
- Django schedules API 우선 조회
- Django AI workspace API 우선 조회
- Django pipeline API 우선 조회
- pipeline mock data fallback
- Django 운영 화면 handoff 링크

## 비범위

- 인증/세션 연동
- 영업노트/일정/AI 전체 기능의 React 재구현
- 기존 Django template 제거

## API Proxy

개발 서버는 `/reporting/*` 요청을 `http://127.0.0.1:8000`으로 proxy합니다.

```bash
python manage.py runserver 127.0.0.1:8000
cd frontend
npm run dev
```

## Railway 배포

Railway 프론트 서비스는 `frontend` 디렉터리를 root로 두고 아래 명령을 사용합니다.

```bash
npm ci
npm run build
npm start
```

`npm start`는 `dist` 정적 파일을 서빙하고 `/reporting/*` 요청을 기존 Django 서버로 proxy합니다. `/schedules/`는 React 정적 앱으로 처리하며, Django 일정 캘린더는 `/reporting/schedules/calendar/`로 접근합니다.

환경변수:

```text
DJANGO_BASE_URL=https://web-production-5096.up.railway.app
```
