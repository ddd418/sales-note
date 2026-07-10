# Sales Note MCP 서버 (읽기+쓰기 원격 커넥터)

Cowork / claude.ai 커스텀 커넥터로 쓰는 Streamable HTTP MCP 서버.
`claude.ai → 이 서버(/mcp) → Django reporting API`.

## 도구
- `salesnote_read(path, query)` — CRM 읽기(GET). 읽기 토큰 사용.
- `salesnote_search(q)` — 통합 검색.
- `salesnote_write(path, payload, confirm, form)` — CRM 쓰기(POST). 쓰기 토큰 사용.
  삭제·메일발송·금액취소 등 되돌릴 수 없는 작업은 `confirm=True` 필요(서버가 428로 강제).

## 환경변수 (Railway 서비스에 설정)
- `MCP_CONNECTOR_TOKEN` — 커넥터 접근 토큰. claude.ai 커넥터 헤더 `Authorization: Bearer <이 값>` 에 입력.
- `SALES_NOTE_READONLY_TOKEN` — Django 읽기 bearer.
- `SALES_NOTE_WRITE_TOKEN` — Django 쓰기 bearer.
- `SALESNOTE_API_BASE` — (선택) 기본 `https://web-production-8a820.up.railway.app/reporting/api`.

## claude.ai 등록
Settings → Connectors → Add custom connector → URL `https://<이 서비스 도메인>/mcp`
→ Advanced/Request headers 에 `Authorization` = `Bearer <MCP_CONNECTOR_TOKEN>` (Required) → Add.
Cowork 는 동일 계정 커넥터를 자동 사용.

## 로컬 실행
```
pip install -r requirements.txt
MCP_CONNECTOR_TOKEN=... SALES_NOTE_READONLY_TOKEN=... SALES_NOTE_WRITE_TOKEN=... python server.py
```
