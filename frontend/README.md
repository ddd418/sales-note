# Sales Note Frontend Pilot

React/Vite 기반 프론트 분리 파일럿입니다.

현재 목적은 Django API 연결 전후의 디자인과 화면 구조를 빠르게 검증하는 것입니다. `/reporting/api/pipeline/`이 응답하면 실제 데이터를 사용하고, Django 서버 미실행/미로그인/응답 오류 시 `src/mockData.ts`의 mock data로 fallback합니다.

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

- 파이프라인 Command Center 시안
- 좌측 CRM 내비게이션
- KPI strip
- Kanban/List 전환
- 고객 상세 패널
- 모바일 대응 기본 레이아웃
- Django pipeline API 우선 조회
- mock data fallback

## 비범위

- 인증/세션 연동
- 실제 저장/수정
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

`npm start`는 `dist` 정적 파일을 서빙하고 `/reporting/*` 요청을 기존 Django 서버로 proxy합니다.

환경변수:

```text
DJANGO_BASE_URL=https://web-production-5096.up.railway.app
```
