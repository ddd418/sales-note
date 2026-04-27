"""
HTML 정화(Sanitization) 유틸리티
-----------------------------------
주간보고 리치 텍스트 에디터에서 저장된 HTML을 서버 사이드에서 정화합니다.

허용 태그: 문서 구조 및 인라인 서식에 필요한 안전한 태그만 허용.
허용 속성: style(제한), href(a 태그), class(span/div 계열)
허용 style 속성: color, background-color, font-size, text-align, font-weight, font-style, text-decoration

차단:
  - <script>, <iframe>, <object>, <embed>, <form>, <input> 등
  - on* 이벤트 핸들러
  - javascript: URL
  - 임의의 style 속성 (허용 목록 외)
"""

import re
import bleach
from bleach.css_sanitizer import CSSSanitizer
from django.utils.safestring import mark_safe


# ── 허용 태그 ────────────────────────────────────────────────────────────────
ALLOWED_TAGS = [
    # 블록 레벨
    'p', 'div', 'br',
    'h2', 'h3', 'h4',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'hr',
    # 인라인
    'strong', 'b', 'em', 'i', 'u', 's',
    'span', 'a',
    # 테이블 (기존 견적/납품 데이터 호환)
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
]

# ── 허용 속성 ────────────────────────────────────────────────────────────────
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'span': ['class', 'style'],
    'div': ['class', 'style'],
    'p': ['class', 'style'],
    'h2': ['class', 'style'],
    'h3': ['class', 'style'],
    'h4': ['class', 'style'],
    'li': ['class', 'style'],
    'td': ['colspan', 'rowspan', 'style'],
    'th': ['colspan', 'rowspan', 'style'],
    'table': ['class', 'style'],
    'blockquote': ['class', 'style'],
    '*': [],  # 나머지 태그는 추가 속성 없음
}

# ── 허용 CSS 속성 ────────────────────────────────────────────────────────────
ALLOWED_CSS_PROPERTIES = [
    'color',
    'background-color',
    'font-size',
    'text-align',
    'font-weight',
    'font-style',
    'text-decoration',
]

_css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)


def _safe_link_callback(attrs, new=False):
    """a 태그 href에서 javascript: URL 차단, target 설정."""
    href = attrs.get((None, 'href'), '')
    if href.lower().lstrip().startswith('javascript:'):
        return None  # 이 링크 전체 제거
    # 외부 링크에 noopener 추가
    if href.startswith('http'):
        attrs[(None, 'target')] = '_blank'
        attrs[(None, 'rel')] = 'noopener noreferrer'
    return attrs


def sanitize_html(html: str) -> str:
    """
    사용자 입력 HTML을 정화하여 안전한 HTML 문자열을 반환합니다.

    Quill 에디터 출력 또는 사용자 작성 HTML에 적용하세요.
    반환값은 Django 템플릿에서 |safe 필터와 함께 사용할 수 있습니다.
    """
    if not html:
        return ''
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=_css_sanitizer,
        strip=True,          # 허용되지 않은 태그 내용은 유지, 태그만 제거
        strip_comments=True,
    )
    # bleach.linkify 미사용 (불필요한 자동 링크 변환 방지)
    # <a> 태그 href 추가 정화
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[_safe_link_callback],
        parse_email=False,
        skip_tags=['code', 'pre'],
    )
    return cleaned


def is_html_content(text: str) -> bool:
    """
    텍스트가 HTML인지 휴리스틱으로 판별합니다.
    기존 plain-text 보고서와 새 HTML 보고서 구분에 사용.
    """
    if not text:
        return False
    stripped = text.strip()
    return bool(re.match(r'^\s*<[a-zA-Z]', stripped))


def render_report_field(text: str) -> str:
    """
    주간보고 필드 렌더링 헬퍼.

    - HTML 콘텐츠: sanitize 후 반환
    - 플레인 텍스트(기존 레거시): 개행을 <br>로 변환해 반환
    반환값은 템플릿에서 |safe 사용.
    """
    if not text:
        return ''
    if is_html_content(text):
        return sanitize_html(text)
    # 레거시 플레인 텍스트: 개행 보존, HTML 이스케이프
    import html as html_module
    escaped = html_module.escape(text)
    return '<p>' + escaped.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
