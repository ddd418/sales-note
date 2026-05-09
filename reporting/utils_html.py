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

import html as _html_module
import re

try:
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    _BLEACH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BLEACH_AVAILABLE = False

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

_css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES) if _BLEACH_AVAILABLE else None

_RICH_TEXT_TAG_RE = re.compile(
    r'</?\s*(p|div|br|h2|h3|h4|ul|ol|li|blockquote|pre|hr|strong|b|em|i|u|s|span|a|table|thead|tbody|tr|th|td)\b',
    re.IGNORECASE,
)
_ESCAPED_RICH_TEXT_TAG_RE = re.compile(
    r'&lt;/?\s*(p|div|br|h2|h3|h4|ul|ol|li|blockquote|pre|hr|strong|b|em|i|u|s|span|a|table|thead|tbody|tr|th|td)\b',
    re.IGNORECASE,
)
_OUTER_PARAGRAPH_RE = re.compile(r'^\s*<p(?:\s[^>]*)?>(?P<body>.*)</p>\s*$', re.IGNORECASE | re.DOTALL)


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


def normalize_report_html_input(text: str) -> str:
    """
    Quill HTML이 한 번 문자열로 escape되어 들어온 값을 정상 HTML로 복구합니다.

    대표 증상:
    - <p>&lt;p&gt;내용&lt;/p&gt;</p>
    - &lt;p&gt;내용&lt;/p&gt;

    사용자가 실제로 작성한 일반 텍스트는 건드리지 않고, rich-text 태그가
    entity 형태로 들어온 경우만 제한적으로 unescape합니다.
    """
    if not text:
        return ''

    normalized = str(text).strip()

    outer = _OUTER_PARAGRAPH_RE.match(normalized)
    if outer and _ESCAPED_RICH_TEXT_TAG_RE.search(outer.group('body')):
        normalized = outer.group('body').strip()

    for _ in range(3):
        if not _ESCAPED_RICH_TEXT_TAG_RE.search(normalized):
            break
        unescaped = _html_module.unescape(normalized).strip()
        if unescaped == normalized:
            break
        if _RICH_TEXT_TAG_RE.search(unescaped):
            normalized = unescaped
        else:
            break

    return normalized


def _html_to_plain_paragraphs(value: str) -> str:
    """bleach가 없는 환경에서 HTML 태그 문자열 노출을 피하기 위한 fallback."""
    if not value:
        return ''

    text = normalize_report_html_input(value)
    text = re.sub(r'<\s*br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</\s*(p|div|li|h2|h3|h4|blockquote)\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*(p|div|li|h2|h3|h4|blockquote)(?:\s[^>]*)?>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = _html_module.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    paragraphs = []
    current = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            paragraphs.append('<br>'.join(_html_module.escape(part) for part in current))
            current = []
    if current:
        paragraphs.append('<br>'.join(_html_module.escape(part) for part in current))
    if not paragraphs:
        return ''
    return ''.join(f'<p>{paragraph}</p>' for paragraph in paragraphs)


def sanitize_html(html: str) -> str:
    """
    사용자 입력 HTML을 정화하여 안전한 HTML 문자열을 반환합니다.

    Quill 에디터 출력 또는 사용자 작성 HTML에 적용하세요.
    반환값은 Django 템플릿에서 |safe 필터와 함께 사용할 수 있습니다.
    bleach 미설치 시: 모든 HTML 태그를 이스케이프하여 안전하게 반환.
    """
    if not html:
        return ''

    html = normalize_report_html_input(html)

    if not _BLEACH_AVAILABLE:
        return _html_to_plain_paragraphs(html)

    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=_css_sanitizer,
        strip=True,          # 허용되지 않은 태그 내용은 유지, 태그만 제거
        strip_comments=True,
    )
    # <a> 태그 href 추가 정화 (linkify 사용 가능 시에만)
    try:
        cleaned = bleach.linkify(
            cleaned,
            callbacks=[_safe_link_callback],
            parse_email=False,
            skip_tags=['code', 'pre'],
        )
    except (AttributeError, Exception):
        pass  # linkify 미지원 환경에서는 생략
    return cleaned


def is_html_content(text: str) -> bool:
    """
    텍스트가 HTML인지 휴리스틱으로 판별합니다.
    기존 plain-text 보고서와 새 HTML 보고서 구분에 사용.
    """
    if not text:
        return False
    stripped = normalize_report_html_input(text)
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
    text = normalize_report_html_input(text)
    if is_html_content(text):
        return sanitize_html(text)
    # 레거시 플레인 텍스트: 개행 보존, HTML 이스케이프
    import html as html_module
    escaped = html_module.escape(text)
    return '<p>' + escaped.replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>'
