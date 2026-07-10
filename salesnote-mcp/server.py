"""Sales Note 읽기+쓰기 통합 원격 MCP 서버 (Cowork / claude.ai 커스텀 커넥터용).

구조:
    claude.ai(Cowork) --[Authorization: Bearer <MCP_CONNECTOR_TOKEN>]--> 이 서버(/mcp)
        --[읽기: SALES_NOTE_READONLY_TOKEN]--> Django GET API
        --[쓰기: SALES_NOTE_WRITE_TOKEN]-----> Django POST API

인증:
- 들어오는 요청은 MCP_CONNECTOR_TOKEN(사용자가 커넥터 헤더에 넣는 값)으로 검증한다.
- Django 읽기/쓰기 토큰은 이 서버 환경변수에만 있고 모델(Claude)엔 절대 노출되지 않는다.

안전:
- 되돌릴 수 없거나 외부로 나가는 작업(삭제·메일발송·금액취소 등)은 Django 가 428 로 막고,
  salesnote_write(confirm=True) 로만 실행된다(사람 확인 후).

환경변수:
    MCP_CONNECTOR_TOKEN       (필수) 커넥터 접근 토큰. claude.ai 커넥터 헤더에 입력.
    SALES_NOTE_READONLY_TOKEN (필수) Django 읽기 bearer.
    SALES_NOTE_WRITE_TOKEN    (필수) Django 쓰기 bearer.
    SALESNOTE_API_BASE        (선택) 기본 https://web-production-8a820.up.railway.app/reporting/api
    PORT                      (Railway 주입)
"""
import os
import secrets

import httpx
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

API_BASE = os.environ.get(
    "SALESNOTE_API_BASE",
    "https://web-production-8a820.up.railway.app/reporting/api",
).rstrip("/")
READONLY_TOKEN = os.environ.get("SALES_NOTE_READONLY_TOKEN", "").strip()
WRITE_TOKEN = os.environ.get("SALES_NOTE_WRITE_TOKEN", "").strip()
CONNECTOR_TOKEN = os.environ.get("MCP_CONNECTOR_TOKEN", "").strip()

CONFIRM_HEADER = "X-Salesnote-Write-Confirm"

mcp = FastMCP(name="Sales Note")


def _check_auth():
    """들어오는 요청의 Authorization 헤더를 MCP_CONNECTOR_TOKEN 과 대조한다."""
    if not CONNECTOR_TOKEN:
        raise ValueError("서버 설정 오류: MCP_CONNECTOR_TOKEN 미설정")
    headers = get_http_headers(include=["authorization"])
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1].strip()
    if not (token and secrets.compare_digest(token, CONNECTOR_TOKEN)):
        raise ValueError("인증 실패: 커넥터 토큰이 없거나 올바르지 않습니다.")


def _fmt(r: httpx.Response) -> str:
    return f"HTTP {r.status_code}\n{r.text}"


@mcp.tool
def salesnote_read(path: str, query: dict | None = None) -> str:
    """Sales Note CRM 읽기(GET).

    path 예시(끝에 / 유지):
      dashboard/ · dashboard/search/ · customers/ · customers/<id>/ ·
      schedules/ · schedules/<id>/ · schedules/calendar/ · notes/ · notes/<id>/ ·
      pipeline/ · followups/ · prepayments/ · reports/ · products/ · ai-workspace/
    query: 필터 dict (예: {"q":"김교수","page":1}).
    """
    _check_auth()
    r = httpx.get(
        f"{API_BASE}/{path.lstrip('/')}",
        params=query or {},
        headers={"Authorization": f"Bearer {READONLY_TOKEN}"},
        timeout=30,
    )
    return _fmt(r)


@mcp.tool
def salesnote_search(q: str) -> str:
    """고객/부서/일정/노트/납품 통합 검색. (dashboard/search/ 래퍼)"""
    _check_auth()
    r = httpx.get(
        f"{API_BASE}/dashboard/search/",
        params={"q": q},
        headers={"Authorization": f"Bearer {READONLY_TOKEN}"},
        timeout=30,
    )
    return _fmt(r)


@mcp.tool
def salesnote_write(
    path: str,
    payload: dict,
    confirm: bool = False,
    form: bool = False,
) -> str:
    """Sales Note CRM 쓰기(POST).

    path 예시:
      notes/create/ · notes/<id>/update/ · schedules/create/ ·
      schedules/<id>/move/ · schedules/<id>/update/ · customers/<id>/update/
    payload: 필드 dict.
    confirm: 되돌릴 수 없거나 외부로 나가는 작업(삭제·메일발송·금액취소·파괴적 대량변경)은
      True 여야 실행됨. 없으면 서버가 428(confirmation_required) 로 거부한다.
      → 반드시 사용자에게 먼저 확인받고 confirm=True 로 재호출할 것.
    form: True 면 form-encoded 로 전송(일부 레거시 엔드포인트, 예: schedules/<id>/move/ 는
      new_date 를 form 으로 받음). 기본은 JSON. JSON 으로 "필드 없음" 오류가 나면 form=True 로 재시도.
    """
    _check_auth()
    url = f"{API_BASE}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {WRITE_TOKEN}"}
    if confirm:
        headers[CONFIRM_HEADER] = "yes"
    if form:
        r = httpx.post(url, data=payload, headers=headers, timeout=30)
    else:
        headers["Content-Type"] = "application/json"
        r = httpx.post(url, json=payload, headers=headers, timeout=30)
    return _fmt(r)


# Streamable HTTP ASGI 앱. host_origin_protection 은 끄고(실제 인증은 커넥터 토큰),
# stateless 로 두어 프록시 뒤에서 안정 동작.
app = mcp.http_app(
    path="/mcp",
    stateless_http=True,
    host_origin_protection=False,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
