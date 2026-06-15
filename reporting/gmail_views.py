"""
Gmail 연동 관련 뷰
- OAuth2 인증 (연결, 콜백, 연결 해제)
- 메일 발송 (일정/메일함에서)
- 메일함 조회 (받은편지함, 보낸편지함, 스레드 상세)
- 수신 메일 동기화
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import (
    UserProfile, EmailLog, ScheduledEmail, ScheduledEmailAttachment,
    BusinessCard, Schedule, FollowUp, DocumentGenerationLog,
)
from .gmail_utils import GmailService, get_authorization_url, exchange_code_for_token
from .readonly_api import api_login_required_or_readonly_response
from .react_redirects import frontend_url


# ============================================
# 헬퍼 함수
# ============================================

def _normalize_email_body_text(value):
    """Normalize textarea line endings before MIME and HTML conversion."""
    return (value or '').replace('\r\n', '\n').replace('\r', '\n')


def _redirect_profile_react():
    return redirect(frontend_url('profile/'))


def _reply_target_email(email_log):
    """Return the external address that should receive a reply for an EmailLog."""
    if not email_log:
        return ''
    if email_log.email_type == 'sent':
        return (email_log.recipient_email or '').strip()
    return (email_log.sender_email or '').strip()


def _plain_email_body_to_html(value):
    from html import escape

    normalized = _normalize_email_body_text(value)
    escaped = escape(normalized, quote=False)
    html_body = escaped.replace('\n', '<br>\n')
    return f'<div style="font-family: Arial, sans-serif; line-height: 1.45; margin: 0;">{html_body}</div>'


def _sanitize_outgoing_email_html(value):
    """Allow CRM email formatting while stripping scripts and unsafe attributes."""
    raw_html = (value or '').strip()
    if not raw_html:
        return ''

    import html
    import re
    import bleach

    allowed_style_properties = {
        'background-color',
        'border',
        'border-collapse',
        'color',
        'font-family',
        'font-size',
        'font-style',
        'font-weight',
        'height',
        'line-height',
        'margin',
        'margin-bottom',
        'margin-left',
        'margin-right',
        'margin-top',
        'max-width',
        'padding',
        'padding-bottom',
        'padding-left',
        'padding-right',
        'padding-top',
        'text-align',
        'text-decoration',
        'vertical-align',
        'width',
    }

    def sanitize_inline_style(style_value):
        declarations = []
        for chunk in html.unescape(style_value or '').split(';'):
            if ':' not in chunk:
                continue
            prop, css_value = chunk.split(':', 1)
            prop = prop.strip().lower()
            css_value = ' '.join(css_value.strip().split())
            if prop not in allowed_style_properties or not css_value:
                continue
            lowered = css_value.lower()
            if any(unsafe in lowered for unsafe in ['expression', 'javascript:', 'url(', '<', '>']):
                continue
            declarations.append(f'{prop}: {css_value}')
        return '; '.join(declarations)

    raw_html = re.sub(r'(?is)<(script|style)\b[^>]*>.*?</\1>', '', raw_html)

    def stash_style(match):
        safe_style = sanitize_inline_style(match.group(2))
        if not safe_style:
            return ''
        return f' data-safe-style="{html.escape(safe_style, quote=True)}"'

    raw_html = re.sub(r'\sstyle=(["\'])(.*?)\1', stash_style, raw_html, flags=re.IGNORECASE | re.DOTALL)

    allowed_tags = [
        'a', 'b', 'blockquote', 'br', 'code', 'div', 'em', 'font', 'h1', 'h2', 'h3',
        'h4', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 's', 'span', 'strike',
        'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'u', 'ul',
    ]
    allowed_attributes = {
        '*': ['data-safe-style', 'title'],
        'a': ['href', 'rel', 'target', 'title'],
        'font': ['color', 'face', 'size'],
        'img': ['alt', 'height', 'src', 'title', 'width', 'data-safe-style'],
        'td': ['colspan', 'rowspan', 'data-safe-style'],
        'th': ['colspan', 'rowspan', 'data-safe-style'],
    }
    cleaned = bleach.clean(
        raw_html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https', 'mailto', 'tel'],
        strip=True,
    )
    cleaned = re.sub(
        r'\sdata-safe-style="([^"]*)"',
        lambda match: f' style="{match.group(1)}"',
        cleaned,
    )
    return cleaned.strip()


def _uploaded_email_attachments(request):
    attachments = []
    for uploaded_file in request.FILES.getlist('attachments'):
        attachments.append({
            'filename': uploaded_file.name,
            'content': uploaded_file.read(),
            'mimetype': uploaded_file.content_type or 'application/octet-stream',
            'size': uploaded_file.size,
            'source': 'uploaded',
        })
    return attachments


AUTO_MAIL_DOCUMENT_TYPES = {
    'quote': ['quotation'],
    'delivery': ['transaction_statement'],
}

DOCUMENT_TYPE_LABELS = {
    'quotation': '견적서',
    'transaction_statement': '거래명세서',
    'delivery_note': '납품서',
}


def _auto_document_types_for_schedule(schedule):
    if not schedule:
        return []
    return AUTO_MAIL_DOCUMENT_TYPES.get(schedule.activity_type, [])


def _document_logs_for_schedule(schedule, document_type):
    return DocumentGenerationLog.objects.filter(
        schedule=schedule,
        document_type=document_type,
        output_format='pdf',
        file__isnull=False,
    ).exclude(file='').select_related('user').order_by('created_at', 'id')


def _quote_document_logs_for_schedule(schedule):
    return _document_logs_for_schedule(schedule, 'quotation')


def _quote_group_keys_for_schedule(schedule):
    groups = []
    seen = set()
    for item in schedule.delivery_items_set.all().order_by('id'):
        group = (getattr(item, 'quote_group', '') or '').strip()[:100]
        if group in seen:
            continue
        seen.add(group)
        groups.append(group)
    return groups or ['']


def _decode_response_filename(response, fallback='quotation.pdf'):
    from urllib.parse import unquote
    import re

    encoded = response.get('X-Filename', '') if hasattr(response, 'get') else ''
    if encoded:
        try:
            return unquote(encoded)
        except Exception:
            return encoded

    disposition = response.get('Content-Disposition', '') if hasattr(response, 'get') else ''
    encoded_match = re.search(r"filename\*=UTF-8''([^;]+)", disposition, flags=re.I)
    if encoded_match:
        try:
            return unquote(encoded_match.group(1).strip())
        except Exception:
            return encoded_match.group(1).strip()
    quoted_match = re.search(r'filename="?([^";]+)"?', disposition, flags=re.I)
    return quoted_match.group(1).strip() if quoted_match else fallback


def _document_type_label(document_type):
    return DOCUMENT_TYPE_LABELS.get(document_type, '서류')


def _document_attachment_source(document_type):
    if document_type == 'quotation':
        return 'quote_document'
    if document_type == 'transaction_statement':
        return 'transaction_statement_document'
    return 'document'


def _auto_attachment_log_key(log):
    return f'log:{log.id}'


def _auto_attachment_generate_key(document_type, quote_group=''):
    return f'generate:{document_type}:{quote_group or ""}'


def _json_error_from_document_response(response, document_type='quotation'):
    try:
        payload = json.loads(response.content.decode('utf-8') or '{}')
    except Exception:
        payload = {}
    return payload.get('error') or payload.get('message') or f'{_document_type_label(document_type)} PDF 생성에 실패했습니다.'


def _attachment_from_document_log(log):
    document_type = log.document_type or 'quotation'
    filename = log.filename or (log.file.name.rsplit('/', 1)[-1] if log.file else f'{document_type}.pdf')
    with log.file.open('rb') as file_handle:
        content = file_handle.read()
    return {
        'filename': filename,
        'content': content,
        'mimetype': 'application/pdf',
        'size': log.file_size or len(content),
        'source': _document_attachment_source(document_type),
        'documentLogId': log.id,
        'documentType': document_type,
        'documentTypeLabel': _document_type_label(document_type),
        'autoAttachmentKey': _auto_attachment_log_key(log),
    }


def _auto_document_generation_targets(schedule, document_type):
    if document_type == 'quotation':
        return [
            {
                'documentType': document_type,
                'quoteGroup': quote_group,
                'key': _auto_attachment_generate_key(document_type, quote_group),
            }
            for quote_group in _quote_group_keys_for_schedule(schedule)
        ]
    return [{
        'documentType': document_type,
        'quoteGroup': '',
        'key': _auto_attachment_generate_key(document_type),
    }]


def _auto_document_pdf_attachments(request, schedule, document_type, excluded_keys=None):
    excluded_keys = set(excluded_keys or [])
    if not schedule or document_type not in _auto_document_types_for_schedule(schedule):
        return []

    logs = list(_document_logs_for_schedule(schedule, document_type))
    if logs:
        return [
            _attachment_from_document_log(log)
            for log in logs
            if _auto_attachment_log_key(log) not in excluded_keys
        ]

    generated_fallbacks = []
    targets = [
        target
        for target in _auto_document_generation_targets(schedule, document_type)
        if target['key'] not in excluded_keys
    ]
    if targets:
        from .views import generate_document_pdf

        for target in targets:
            quote_group = target.get('quoteGroup') or ''
            if document_type == 'quotation':
                response = generate_document_pdf(request, document_type, schedule.id, 'pdf', quote_group=quote_group)
            else:
                response = generate_document_pdf(request, document_type, schedule.id, 'pdf')
            content_type = (response.get('Content-Type', '') if hasattr(response, 'get') else '').split(';')[0].strip()
            if content_type == 'application/json':
                raise Exception(_json_error_from_document_response(response, document_type))
            if getattr(response, 'status_code', 500) >= 400:
                raise Exception(_json_error_from_document_response(response, document_type))
            if content_type != 'application/pdf':
                raise Exception(f'{_document_type_label(document_type)} PDF를 생성하지 못했습니다. PDF 변환 설정을 확인해주세요.')
            generated_fallbacks.append({
                'filename': _decode_response_filename(response, fallback=f'{document_type}.pdf'),
                'content': bytes(response.content),
                'mimetype': 'application/pdf',
                'size': len(response.content),
                'source': _document_attachment_source(document_type),
                'documentLogId': None,
                'documentType': document_type,
                'documentTypeLabel': _document_type_label(document_type),
                'autoAttachmentKey': target['key'],
                'quoteGroup': quote_group,
            })

    return generated_fallbacks


def _auto_schedule_document_attachments(request, schedule, excluded_keys=None):
    attachments = []
    for document_type in _auto_document_types_for_schedule(schedule):
        attachments.extend(_auto_document_pdf_attachments(
            request,
            schedule,
            document_type,
            excluded_keys=excluded_keys,
        ))
    return attachments


def _auto_quote_pdf_attachments(request, schedule):
    return _auto_document_pdf_attachments(request, schedule, 'quotation')


def _attachment_info(attachment):
    info = {
        'filename': attachment['filename'],
        'size': attachment['size'],
        'mimetype': attachment['mimetype'],
    }
    if attachment.get('source'):
        info['source'] = attachment.get('source')
    if attachment.get('source') in {'quote_document', 'transaction_statement_document', 'document'}:
        document_type = attachment.get('documentType') or 'quotation'
        info['label'] = f'자동 첨부 {_document_type_label(document_type)}'
        info['documentType'] = document_type
        info['documentTypeLabel'] = _document_type_label(document_type)
        if attachment.get('documentLogId'):
            info['documentLogId'] = attachment['documentLogId']
        if attachment.get('autoAttachmentKey'):
            info['autoAttachmentKey'] = attachment['autoAttachmentKey']
    return info


def _mailbox_scheduled_at_value(request):
    return request.POST.get('scheduled_at') or request.POST.get('scheduledAt') or ''


def _parse_mailbox_scheduled_at(value):
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime

    raw_value = str(value or '').strip()
    if not raw_value:
        return None, ''
    scheduled_at = parse_datetime(raw_value)
    if scheduled_at is None:
        return None, '예약 발송 일시 형식이 올바르지 않습니다.'
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())
    if scheduled_at <= timezone.now() + timedelta(minutes=1):
        return None, '예약 발송 일시는 현재보다 1분 이후로 선택하세요.'
    return scheduled_at, ''


def _scheduled_email_attachment_payloads(scheduled_email):
    rows = []
    for attachment in scheduled_email.attachments.all():
        metadata = attachment.metadata if isinstance(attachment.metadata, dict) else {}
        rows.append({
            'filename': attachment.filename,
            'size': attachment.size,
            'mimetype': attachment.mimetype,
            'source': metadata.get('source') or '',
            'downloadHref': '',
        })
    return rows


def _save_scheduled_email_attachments(scheduled_email, attachment_entries):
    from django.core.files.base import ContentFile

    for attachment in attachment_entries:
        filename = str(attachment.get('filename') or 'attachment').strip()[:255] or 'attachment'
        content = attachment.get('content') or b''
        row = ScheduledEmailAttachment(
            scheduled_email=scheduled_email,
            filename=filename,
            mimetype=attachment.get('mimetype') or 'application/octet-stream',
            size=int(attachment.get('size') or len(content) or 0),
            metadata=_attachment_info(attachment),
        )
        row.file.save(filename, ContentFile(content), save=False)
        row.save()


def _scheduled_attachment_entries(scheduled_email):
    rows = []
    for attachment in scheduled_email.attachments.all():
        content = b''
        if attachment.file:
            with attachment.file.open('rb') as file_handle:
                content = file_handle.read()
        rows.append({
            'id': attachment.id,
            'filename': attachment.filename,
            'content': content,
            'mimetype': attachment.mimetype or 'application/octet-stream',
            'size': attachment.size or len(content),
            'metadata': attachment.metadata if isinstance(attachment.metadata, dict) else {},
        })
    return rows


def _email_log_attachment_info_from_scheduled(entries):
    rows = []
    for entry in entries:
        info = dict(entry.get('metadata') or {})
        info.setdefault('filename', entry.get('filename') or 'attachment')
        info.setdefault('size', entry.get('size') or 0)
        info.setdefault('mimetype', entry.get('mimetype') or 'application/octet-stream')
        if entry.get('id'):
            info['scheduledAttachmentId'] = entry['id']
        rows.append(info)
    return rows


def _post_json_list(request, *names):
    values = []
    for name in names:
        for raw_value in request.POST.getlist(name):
            if raw_value in (None, ''):
                continue
            if isinstance(raw_value, str) and raw_value.strip().startswith('['):
                try:
                    decoded = json.loads(raw_value)
                except Exception:
                    decoded = []
                if isinstance(decoded, list):
                    values.extend(decoded)
                    continue
            values.append(raw_value)
    return values


def _excluded_auto_attachment_keys(request, schedule=None):
    excluded = {
        str(value).strip()
        for value in _post_json_list(
            request,
            'excluded_auto_attachment_keys',
            'excludedAutoAttachmentKeys',
        )
        if str(value).strip()
    }
    include_mode = request.POST.get('auto_attachment_include_mode') == '1'
    if include_mode and schedule:
        included = {
            str(value).strip()
            for value in _post_json_list(
                request,
                'included_auto_attachment_keys',
                'includedAutoAttachmentKeys',
            )
            if str(value).strip()
        }
        all_keys = {
            candidate['key']
            for candidate in _auto_document_candidates_for_schedule(schedule)
            if candidate.get('key')
        }
        excluded.update(all_keys - included)
    return excluded


def _auto_document_candidate_from_log(log):
    return {
        'key': _auto_attachment_log_key(log),
        'filename': log.filename or (log.file.name.rsplit('/', 1)[-1] if log.file else f'{log.document_type}.pdf'),
        'size': log.file_size or 0,
        'documentLogId': log.id,
        'documentType': log.document_type,
        'documentTypeLabel': _document_type_label(log.document_type),
        'quoteGroup': log.quote_group or '',
        'quoteGroupLabel': log.quote_group or '',
        'willGenerate': False,
        'description': '등록된 PDF가 자동 첨부됩니다.',
    }


def _auto_document_candidate_from_target(target):
    document_type = target['documentType']
    quote_group = target.get('quoteGroup') or ''
    document_label = _document_type_label(document_type)
    display_label = f'{quote_group} {document_label}' if quote_group else document_label
    return {
        'key': target['key'],
        'filename': f'{display_label} PDF 자동 생성',
        'size': 0,
        'documentLogId': None,
        'documentType': document_type,
        'documentTypeLabel': document_label,
        'quoteGroup': quote_group,
        'quoteGroupLabel': quote_group,
        'willGenerate': True,
        'description': '등록된 PDF가 없어 발송 시 새 PDF를 생성합니다.',
    }


def _auto_document_candidates_for_schedule(schedule):
    candidates = []
    for document_type in _auto_document_types_for_schedule(schedule):
        logs = list(_document_logs_for_schedule(schedule, document_type))
        if logs:
            candidates.extend(_auto_document_candidate_from_log(log) for log in logs)
        else:
            candidates.extend(
                _auto_document_candidate_from_target(target)
                for target in _auto_document_generation_targets(schedule, document_type)
            )
    return candidates


def _auto_document_attach_label(candidates):
    if not candidates:
        return ''
    labels = []
    for candidate in candidates:
        label = candidate.get('documentTypeLabel') or '서류'
        if label not in labels:
            labels.append(label)
    count = len(candidates)
    generated_count = sum(1 for candidate in candidates if candidate.get('willGenerate'))
    label_text = '/'.join(labels)
    if generated_count == count:
        return f'등록된 {label_text} PDF가 없으면 메일 발송 시 새 PDF {count}개를 생성해 자동 첨부합니다.'
    if generated_count:
        return f'메일 발송 시 {label_text} PDF {count}개가 자동 첨부되며, 일부는 새로 생성됩니다.'
    return f'메일 발송 시 {label_text} PDF {count}개가 자동 첨부됩니다.'


def _email_address_list(value):
    from email.utils import getaddresses

    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = [str(item or '') for item in value]
    else:
        raw_values = [str(value or '')]

    addresses = []
    seen = set()
    for _name, address in getaddresses(raw_values):
        normalized = (address or '').strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        addresses.append(normalized)
    return addresses


def _email_address_text(addresses):
    cleaned = []
    seen = set()
    for address in addresses or []:
        normalized = str(address or '').strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)
    return ', '.join(cleaned)


def _internal_cc_requested(request):
    value = request.POST.get('include_internal_cc') or request.POST.get('includeInternalCc') or ''
    return str(value).lower() in {'1', 'true', 'yes', 'y', 'on'}


def _display_name_for_internal_user(user):
    return user.get_full_name() or user.username or user.email


def _internal_cc_contacts_for_user(user, exclude_emails=None):
    from django.contrib.auth import get_user_model

    try:
        company_id = user.userprofile.company_id
    except UserProfile.DoesNotExist:
        company_id = None
    if not company_id:
        return []

    excluded = {email.lower() for email in _email_address_list(exclude_emails or [])}
    excluded.update(_email_address_list([user.email]))
    excluded = {email.lower() for email in excluded if email}

    User = get_user_model()
    contacts = []
    seen = set()
    users = User.objects.filter(
        is_active=True,
        userprofile__company_id=company_id,
    ).exclude(id=user.id).select_related('userprofile').order_by('username')
    for teammate in users:
        profile = getattr(teammate, 'userprofile', None)
        candidates = [
            teammate.email,
            getattr(profile, 'gmail_email', ''),
            getattr(profile, 'imap_email', ''),
        ]
        added_for_user = False
        for candidate in candidates:
            for address in _email_address_list(candidate):
                key = address.lower()
                if key in excluded or key in seen:
                    continue
                seen.add(key)
                contacts.append({
                    'id': teammate.id,
                    'name': _display_name_for_internal_user(teammate),
                    'email': address,
                    'label': f"{_display_name_for_internal_user(teammate)} <{address}>",
                })
                added_for_user = True
                break
            if added_for_user:
                break
    return contacts


def _internal_cc_emails_for_user(user, exclude_emails=None):
    return [
        contact['email']
        for contact in _internal_cc_contacts_for_user(user, exclude_emails=exclude_emails)
    ]


def _requested_internal_cc_emails(request, exclude_emails=None):
    raw_value = (
        request.POST.get('internal_cc_emails')
        or request.POST.get('internalCcEmails')
        or request.POST.get('selected_internal_cc_emails')
        or request.POST.get('selectedInternalCcEmails')
        or ''
    )
    if not raw_value:
        if _internal_cc_requested(request):
            return _internal_cc_emails_for_user(request.user, exclude_emails=exclude_emails)
        return []

    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        parsed = raw_value

    if isinstance(parsed, list):
        requested = _email_address_list(parsed)
    else:
        requested = _email_address_list(str(parsed))

    allowed = {
        contact['email'].lower(): contact['email']
        for contact in _internal_cc_contacts_for_user(request.user)
    }
    excluded = {email.lower() for email in _email_address_list(exclude_emails or [])}
    selected = []
    seen = set()
    for address in requested:
        key = address.lower()
        if key not in allowed or key in excluded or key in seen:
            continue
        selected.append(allowed[key])
        seen.add(key)
    return selected


def _strip_html_style_blocks(value):
    import re

    text = str(value or '')
    text = re.sub(r'(?is)<\s*style\b[^>]*>.*?<\s*/\s*style\s*>', ' ', text)
    text = re.sub(r'(?is)<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', ' ', text)
    return text


def _strip_css_text_artifacts(value):
    import re

    text = str(value or '')
    selector_pattern = r'(?:p|div|span|body|td|table|tr|a|li|ul|ol)'
    css_prop_pattern = r'(?:margin|padding|font|color|line-height|mso-|text-|background|border|white-space)'
    text = re.sub(
        rf'(?im)^\s*{selector_pattern}\s*\{{[^{{}}\n]*{css_prop_pattern}[^{{}}\n]*\}}\s*$',
        '',
        text,
    )
    text = re.sub(
        rf'(?i)\b{selector_pattern}\s*\{{[^{{}}]*(?:margin|padding|font|mso-)[^{{}}]*\}}\s*',
        '',
        text,
    )
    return text


def _looks_like_email_html(value):
    import html
    import re

    text = str(value or '')
    if not text.strip():
        return False
    candidates = [text]
    unescaped = html.unescape(text)
    if unescaped != text:
        candidates.append(unescaped)
    html_pattern = re.compile(
        r'(?is)<\s*(?:!doctype|html|head|body|style|script|meta|div|p|br|span|table|tbody|tr|td|blockquote)\b'
    )
    return any(html_pattern.search(candidate) for candidate in candidates)


def _email_html_to_display_text(value, limit=12000, strip_quotes=True):
    import html
    import re
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = html.unescape(str(value or ''))
    raw = _strip_html_style_blocks(raw)
    if strip_quotes:
        raw = _strip_quoted_html_for_display(raw)
    text = re.sub(r'(?i)<\s*br\s*/?\s*>', '\n', raw)
    text = re.sub(r'(?i)<\s*/\s*(p|div|li|tr|h[1-6]|blockquote|section|article|table|head|body|html)\s*>', '\n', text)
    text = re.sub(r'(?i)<\s*li(?:\s[^>]*)?>', '- ', text)
    text = strip_tags(text)
    text = html.unescape(text).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [' '.join(line.split()) for line in text.split('\n')]
    normalized = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append('')
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False
    return Truncator(_strip_quoted_text_for_display('\n'.join(normalized).strip())).chars(limit)


def _clean_outgoing_body_text(value):
    text = _normalize_email_body_text(value)
    if _looks_like_email_html(text):
        return _email_html_to_display_text(text, strip_quotes=False)
    return text


def _html_matches_escaped_plain_body(body_html, body_text):
    import html

    html_value = str(body_html or '')
    if not html_value:
        return False
    if not any(token in html_value.lower() for token in ('&lt;html', '&lt;body', '&lt;div', '&lt;p', '&lt;style')):
        return False
    text_value = str(body_text or '')
    return _looks_like_email_html(html.unescape(html_value)) or _looks_like_email_html(text_value)


def _sanitize_received_attachments(attachments, message_id=''):
    rows = []
    for attachment in attachments or []:
        if not isinstance(attachment, dict):
            continue
        filename = str(attachment.get('filename') or '').strip()
        if not filename:
            continue
        try:
            size = int(attachment.get('size') or 0)
        except (TypeError, ValueError):
            size = 0
        row = {
            'filename': filename,
            'size': size,
            'mimetype': attachment.get('mimetype') or attachment.get('mimeType') or 'application/octet-stream',
            'source': attachment.get('source') or ('gmail' if attachment.get('gmailAttachmentId') else ''),
        }
        if attachment.get('gmailAttachmentId'):
            row['gmailAttachmentId'] = attachment['gmailAttachmentId']
            row['gmailMessageId'] = attachment.get('gmailMessageId') or message_id
        if attachment.get('contentBase64'):
            row['contentBase64'] = attachment['contentBase64']
        if attachment.get('documentLogId'):
            row['documentLogId'] = attachment['documentLogId']
        rows.append(row)
    return rows


def _sync_emails_by_days(user, days=1):
    """
    지정한 일수만큼 메일 동기화
    
    Args:
        user: User 객체
        days: 동기화할 일수 (기본 1일)
    
    Returns:
        동기화된 메일 개수
    """
    import os
    from django.utils import timezone
    
    profile = user.userprofile
    
    if not profile.gmail_token:
        return 0
    
    gmail_service = GmailService(profile)
    
    followups = list(
        FollowUp.objects
        .filter(user=user)
        .exclude(email='')
        .select_related('company', 'department')
    )
    followup_by_email = {
        followup.email.strip().lower(): followup
        for followup in followups
        if followup.email
    }
    target_emails = set(followup_by_email)
    
    if not target_emails:
        return 0
    
    # 마지막 동기화 시점 이후의 메일만 가져오기
    if profile.gmail_last_sync_at:
        # 마지막 동기화 이후 메일만
        query = f'after:{int(profile.gmail_last_sync_at.timestamp())}'
        max_results = 80
    else:
        # 첫 동기화 또는 지정된 일수
        query = f'newer_than:{days}d'
        max_results = 120 if days > 7 else 80
    try:
        env_limit = int(os.environ.get('GMAIL_SYNC_MAX_RESULTS', max_results))
        max_results = max(10, min(env_limit, 200))
    except (TypeError, ValueError):
        pass
    
    result = gmail_service.get_messages(query=query, max_results=max_results)
    messages_list = result.get('messages', [])
    message_ids = [
        str(msg.get('id') or '').strip()
        for msg in messages_list
        if msg.get('id')
    ]
    if not message_ids:
        profile.gmail_last_sync_at = timezone.now()
        profile.save(update_fields=['gmail_last_sync_at'])
        return 0

    existing_ids = set(
        EmailLog.objects
        .filter(gmail_message_id__in=message_ids)
        .exclude(gmail_message_id='')
        .values_list('gmail_message_id', flat=True)
    )

    metadata_rows = []
    for message_id in message_ids:
        if message_id in existing_ids:
            continue
        metadata = gmail_service.get_message_metadata(
            message_id,
            metadata_headers=['From', 'To', 'Cc', 'Bcc', 'Date', 'Subject'],
        )
        if metadata:
            metadata_rows.append(metadata)

    thread_ids = {
        row.get('thread_id')
        for row in metadata_rows
        if row.get('thread_id')
    }
    from django.db.models import Q

    thread_contexts = {
        email.gmail_thread_id: email
        for email in EmailLog.objects.filter(
            Q(sender=user) | Q(user=user) | Q(followup__user=user) | Q(schedule__user=user),
            gmail_thread_id__in=thread_ids,
        ).select_related('schedule', 'followup')
        if email.gmail_thread_id
    }
    
    synced_count = 0
    own_email = (profile.gmail_email or '').strip().lower()

    for metadata in metadata_rows:
        from_addresses = {
            address.lower()
            for address in _email_address_list(metadata.get('from'))
        }
        recipient_addresses = {
            address.lower()
            for address in _email_address_list([
                metadata.get('to'),
                metadata.get('cc'),
                metadata.get('bcc'),
            ])
        }
        is_sent = bool(own_email and own_email in from_addresses)
        candidate_addresses = recipient_addresses if is_sent else from_addresses
        matched_followup = next(
            (
                followup_by_email[address]
                for address in candidate_addresses
                if address in followup_by_email
            ),
            None,
        )
        existing_thread_email = thread_contexts.get(metadata.get('thread_id') or '')
        matched_schedule = existing_thread_email.schedule if existing_thread_email else None
        if existing_thread_email and not matched_followup:
            matched_followup = existing_thread_email.followup

        if not matched_followup and not matched_schedule:
            continue

        msg_detail = gmail_service.get_message_detail(metadata['id'])
        if not msg_detail:
            continue

        from_header = msg_detail.get('from') or metadata.get('from') or ''
        to_header = msg_detail.get('to') or metadata.get('to') or ''
        from_email = (_email_address_list(from_header) or [from_header.lower()])[0].lower()
        to_email = (_email_address_list(to_header) or [to_header.lower()])[0].lower()
        if not from_email or not to_email:
            continue

        body_html = msg_detail.get('body_html', '')
        body_text = msg_detail.get('body_text', '')
        body_content = body_html or body_text or msg_detail.get('snippet', '') or metadata.get('snippet', '')

        from email.utils import parsedate_to_datetime
        email_date = None
        if msg_detail.get('date') or metadata.get('date'):
            try:
                email_date = parsedate_to_datetime(msg_detail.get('date') or metadata.get('date'))
            except Exception:
                pass

        EmailLog.objects.create(
            email_type='sent' if is_sent else 'received',
            sender=user if is_sent else None,
            sender_email=from_email,
            recipient_email=to_email,
            subject=msg_detail.get('subject') or metadata.get('subject') or '(제목 없음)',
            body=body_content,
            body_html=body_html,
            gmail_message_id=msg_detail.get('id') or metadata['id'],
            gmail_thread_id=msg_detail.get('thread_id') or metadata.get('thread_id') or '',
            followup=matched_followup,
            schedule=matched_schedule,
            attachments_info=_sanitize_received_attachments(
                msg_detail.get('attachments') or [],
                msg_detail.get('id') or metadata['id'],
            ),
            is_read=True if is_sent else False,
            status='sent' if is_sent else 'received',
            sent_at=email_date if is_sent else None,
            received_at=email_date if not is_sent else None
        )
        synced_count += 1
    
    profile.gmail_last_sync_at = timezone.now()
    profile.save(update_fields=['gmail_last_sync_at'])
    
    return synced_count


def _sync_imap_emails_by_days(user, days=1):
    """현재 React 메일함 API에서 쓰는 IMAP 동기화 경로."""
    from django.utils import timezone
    from .imap_utils import IMAPEmailService

    profile = user.userprofile
    if not profile.imap_connected_at:
        return 0

    followups = list(
        FollowUp.objects
        .filter(user=user)
        .exclude(email='')
        .select_related('company', 'department')
    )
    followup_by_email = {
        followup.email.strip().lower(): followup
        for followup in followups
        if followup.email
    }
    target_emails = set(followup_by_email)
    if not target_emails:
        profile.imap_last_sync_at = timezone.now()
        profile.save(update_fields=['imap_last_sync_at'])
        return 0

    imap_service = IMAPEmailService(profile)
    if not imap_service.connect():
        raise Exception('이메일 서버 연결에 실패했습니다.')

    try:
        emails = imap_service.fetch_emails(
            folder='INBOX',
            days=max(1, min(int(days or 1), 7)),
            target_emails=list(target_emails),
        )
    finally:
        imap_service.disconnect()

    message_ids = [
        str(email.get('message_id') or '').strip()
        for email in emails
        if email.get('message_id')
    ]
    existing_ids = set(
        EmailLog.objects
        .filter(user=user, provider='imap', message_id__in=message_ids)
        .exclude(message_id='')
        .values_list('message_id', flat=True)
    )

    synced_count = 0
    for email_data in emails:
        message_id = str(email_data.get('message_id') or '').strip()
        if not message_id or message_id in existing_ids:
            continue

        from_email = (email_data.get('from_email') or '').strip().lower()
        to_email = (email_data.get('to_email') or '').strip().lower()
        cc_emails = [
            str(address or '').strip().lower()
            for address in email_data.get('cc_emails') or []
            if str(address or '').strip()
        ]
        candidate_addresses = {from_email, to_email, *cc_emails}
        matched_followup = next(
            (
                followup_by_email[address]
                for address in candidate_addresses
                if address in followup_by_email
            ),
            None,
        )
        if not matched_followup:
            continue

        received_at = email_data.get('date') or timezone.now()
        if timezone.is_naive(received_at):
            received_at = timezone.make_aware(received_at, timezone.get_current_timezone())

        EmailLog.objects.create(
            user=user,
            provider='imap',
            message_id=message_id,
            thread_id=email_data.get('thread_id') or message_id,
            email_type='received',
            is_sent=False,
            from_email=from_email,
            from_name=email_data.get('from_name') or '',
            to_email=to_email,
            sender_email=from_email,
            recipient_email=to_email,
            cc_emails=_email_address_text(cc_emails),
            subject=(email_data.get('subject') or '(제목 없음)')[:500],
            body=email_data.get('body') or '',
            attachments_info=email_data.get('attachments') or [],
            followup=matched_followup,
            status='received',
            received_at=received_at,
            is_read=False,
        )
        existing_ids.add(message_id)
        synced_count += 1

    profile.imap_last_sync_at = timezone.now()
    profile.save(update_fields=['imap_last_sync_at'])
    return synced_count


# ============================================
# Gmail OAuth2 인증
# ============================================

@login_required
def gmail_connect(request):
    """Gmail 계정 연결 시작"""
    # 환경 변수 체크
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET or not settings.GMAIL_REDIRECT_URI:
        messages.error(request, 'Gmail API 설정이 올바르지 않습니다. 관리자에게 문의하세요.')
        return _redirect_profile_react()
    
    try:
        redirect_uri = settings.GMAIL_REDIRECT_URI
        auth_url, state = get_authorization_url(redirect_uri)
        # state를 세션에 저장 (보안을 위해)
        request.session['gmail_oauth_state'] = state
        return redirect(auth_url)
    except Exception as e:
        messages.error(request, f'Gmail 연결 시작 중 오류: {str(e)}')
        return _redirect_profile_react()


@login_required
def gmail_callback(request):
    """Gmail OAuth2 콜백"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Gmail 연결 실패: {error}')
        return _redirect_profile_react()
    
    if not code:
        messages.error(request, 'Gmail 인증 코드가 없습니다.')
        return _redirect_profile_react()
    
    try:
        # 인증 코드를 토큰으로 교환
        redirect_uri = settings.GMAIL_REDIRECT_URI
        creds, gmail_email = exchange_code_for_token(code, redirect_uri)
        
        # UserProfile에 토큰 저장
        profile = request.user.userprofile
        profile.gmail_token = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        profile.gmail_email = gmail_email
        profile.save()
        
        # 첫 연동 시 메시지만 표시 (동기화는 사용자가 수동으로 또는 나중에)
        messages.success(request, f'Gmail 계정({gmail_email})이 연결되었습니다. 메일함에서 "메일 동기화" 버튼을 눌러 이메일을 가져올 수 있습니다.')
        
        return _redirect_profile_react()
        
    except Exception as e:
        messages.error(request, f'Gmail 연결 중 오류 발생: {str(e)}')
        return _redirect_profile_react()


@login_required
def gmail_disconnect(request):
    """Gmail 계정 연결 해제"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            profile.gmail_token = None
            profile.gmail_email = ''
            profile.gmail_connected_at = None
            profile.gmail_last_sync_at = None
            profile.save()
            
            messages.success(request, 'Gmail 계정 연결이 해제되었습니다.')
        except Exception as e:
            messages.error(request, f'연결 해제 중 오류 발생: {str(e)}')
    
    return _redirect_profile_react()


# ============================================
# 이메일 발송
# ============================================

@login_required
def send_email_from_schedule(request, schedule_id):
    """일정에서 이메일 발송"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # 권한 확인: 자신의 일정 또는 매니저
    if schedule.user != request.user and request.user.userprofile.role != 'manager':
        messages.error(request, '권한이 없습니다.')
        return redirect('reporting:schedule_detail', pk=schedule_id)
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return _redirect_profile_react()
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    auto_attachments = _auto_document_candidates_for_schedule(schedule)
    context = {
        'schedule': schedule,
        'followup': schedule.followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
        'quote_document_count': _quote_document_logs_for_schedule(schedule).count() if schedule.activity_type == 'quote' else 0,
        'auto_attachments': auto_attachments,
        'auto_attach_label': _auto_document_attach_label(auto_attachments),
    }
    
    if request.method == 'POST':
        result = _handle_email_send(request, schedule=schedule, auto_attach_schedule_documents=True)
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            # 디버그: 오류 정보 로깅
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Email send validation failed: {result}")
            context.update(result)
            return render(request, 'reporting/gmail/compose_from_schedule.html', context)
        # 성공 시 (리다이렉트 반환)
        return result
    
    # GET: 이메일 작성 폼
    return render(request, 'reporting/gmail/compose_from_schedule.html', context)


@login_required
def send_email_from_mailbox(request, followup_id=None):
    """메일함에서 이메일 발송 (팔로우업 연결)"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"send_email_from_mailbox called: method={request.method}, user={request.user}, followup_id={followup_id}")
    
    followup = None
    if followup_id:
        followup = get_object_or_404(FollowUp, id=followup_id)
        
        # 권한 확인: 자신의 팔로우업 또는 매니저
        if followup.user != request.user and request.user.userprofile.role != 'manager':
            messages.error(request, '권한이 없습니다.')
            return redirect('reporting:mailbox_inbox')
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return _redirect_profile_react()
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'followup': followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    
    if request.method == 'POST':
        logger.info(f"POST request received, calling _handle_email_send")
        
        # 팔로우업 검색으로 선택한 경우 처리
        if not followup:
            selected_followup_id = request.POST.get('selected_followup_id')
            if selected_followup_id:
                try:
                    # 같은 회사 내 팔로우업이면 허용
                    followup = FollowUp.objects.get(
                        id=selected_followup_id,
                        user__userprofile__company=request.user.userprofile.company
                    )
                    logger.info(f"Followup selected from search: {followup.id}")
                except FollowUp.DoesNotExist:
                    pass
        
        result = _handle_email_send(request, followup=followup)
        logger.info(f"_handle_email_send result type: {type(result)}, is_dict: {isinstance(result, dict)}")
        
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            logger.warning(f"Email validation failed, re-rendering template with errors: {result}")
            context.update(result)
            return render(request, 'reporting/gmail/compose_from_mailbox.html', context)
        # 성공 시 (리다이렉트 반환)
        logger.info(f"Email sent successfully, redirecting")
        return result
    
    # GET: 이메일 작성 폼
    return render(request, 'reporting/gmail/compose_from_mailbox.html', context)


@login_required
def reply_email(request, email_log_id):
    """이메일 답장"""
    email_log = get_object_or_404(EmailLog, id=email_log_id)
    
    # 권한 확인: 발신 메일은 발신자만, 수신 메일은 누구나 답장 가능
    if email_log.email_type == 'sent':
        # 발신 메일: 본인이 보낸 메일만 답장 가능
        if email_log.sender != request.user and request.user.userprofile.role != 'manager':
            messages.error(request, '권한이 없습니다.')
            return redirect('reporting:mailbox_inbox')
    # 수신 메일은 권한 체크 없이 누구나 답장 가능
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return _redirect_profile_react()
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'original_email': email_log,
        'reply_target_email': _reply_target_email(email_log),
        'original_email_display_body': _email_body_text(email_log),
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    
    if request.method == 'POST':
        result = _handle_email_send(request, reply_to=email_log)
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            context.update(result)
            return render(request, 'reporting/gmail/reply_email.html', context)
        # 성공 시 (리다이렉트 반환)
        return result
    
    # GET: 답장 폼
    return render(request, 'reporting/gmail/reply_email.html', context)


def _handle_email_send(
    request,
    schedule=None,
    followup=None,
    reply_to=None,
    auto_attach_quote_documents=False,
    auto_attach_schedule_documents=False,
):
    """이메일 발송 공통 처리"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"_handle_email_send called: user={request.user}, schedule={schedule}, followup={followup}")
        
        # POST 데이터 추출
        to_email = request.POST.get('to_email', '')
        cc_emails = request.POST.get('cc_emails', '')
        bcc_emails = request.POST.get('bcc_emails', '')
        subject = request.POST.get('subject', '')
        if reply_to:
            reply_target = _reply_target_email(reply_to)
            if reply_target and (not to_email or to_email == (reply_to.sender_email or '').strip()):
                to_email = reply_target
        body_text = _clean_outgoing_body_text(request.POST.get('body_text', ''))
        body_html = _sanitize_outgoing_email_html(request.POST.get('body_html', ''))
        if body_text and _html_matches_escaped_plain_body(body_html, request.POST.get('body_text', '')):
            body_html = _plain_email_body_to_html(body_text)
        if not body_text and body_html:
            from django.utils.html import strip_tags
            body_text = _normalize_email_body_text(strip_tags(body_html))
        business_card_id = request.POST.get('business_card_id', '')
        
        logger.info(f"Form data: to_email={to_email}, subject={subject}, body_text_len={len(body_text)}, body_html_len={len(body_html)}")
        
        # 유효성 검사 - 검증 실패 시 딕셔너리 반환 (템플릿 재렌더링용)
        if not to_email or not subject:
            logger.warning(f"Validation failed: missing to_email or subject")
            messages.error(request, '받는 사람과 제목은 필수입니다.')
            return {
                'error': True,
                'form_data': {
                    'to_email': to_email,
                    'cc_emails': cc_emails,
                    'bcc_emails': bcc_emails,
                    'subject': subject,
                    'body_text': body_text,
                    'body_html': body_html,
                    'business_card_id': business_card_id,
                }
            }
        
        if not body_text and not body_html:
            logger.warning(f"Validation failed: missing body")
            messages.error(request, '본문을 입력해주세요.')
            return {
                'error': True,
                'form_data': {
                    'to_email': to_email,
                    'cc_emails': cc_emails,
                    'bcc_emails': bcc_emails,
                    'subject': subject,
                    'body_text': body_text,
                    'body_html': body_html,
                    'business_card_id': business_card_id,
                }
            }
        
        # 명함 서명 추가
        signature_html = ''
        business_card = None
        if business_card_id:
            business_card = BusinessCard.objects.get(id=business_card_id, user=request.user)
            signature_html = business_card.generate_signature(request=request)
        
        # 본문과 서명 사이 구분선
        separator = '<div style="margin: 20px 0; padding-top: 20px; border-top: 1px solid #ddd;"></div>' if signature_html else ''
        
        # HTML 본문에 서명 추가
        if body_html and body_html.strip():
            full_body_html = body_html + separator + signature_html
        else:
            # HTML이 비어있으면 body_text를 사용
            if body_text and body_text.strip():
                full_body_html = _plain_email_body_to_html(body_text) + separator + signature_html
            else:
                full_body_html = signature_html
        
        if reply_to:
            if not followup:
                followup = reply_to.followup
            if not schedule:
                schedule = reply_to.schedule

        cc_list = _email_address_list(cc_emails)
        bcc_list = _email_address_list(bcc_emails)
        internal_cc_list = _requested_internal_cc_emails(
            request,
            exclude_emails=[to_email, *cc_list, *bcc_list],
        )
        if internal_cc_list:
            cc_list = [*cc_list, *internal_cc_list]
        cc_emails = _email_address_text(cc_list)
        bcc_emails = _email_address_text(bcc_list)

        attachment_entries = _uploaded_email_attachments(request)
        excluded_auto_keys = _excluded_auto_attachment_keys(request, schedule=schedule)
        if auto_attach_schedule_documents and schedule:
            attachment_entries.extend(_auto_schedule_document_attachments(
                request,
                schedule,
                excluded_keys=excluded_auto_keys,
            ))
        elif auto_attach_quote_documents and schedule and schedule.activity_type == 'quote':
            attachment_entries.extend(_auto_quote_pdf_attachments(request, schedule))
        attachments_info = [_attachment_info(attachment) for attachment in attachment_entries]

        profile = request.user.userprofile
        requested_scheduled_at = _mailbox_scheduled_at_value(request)
        scheduled_at, scheduled_error = _parse_mailbox_scheduled_at(requested_scheduled_at)
        if scheduled_error:
            messages.error(request, scheduled_error)
            return {
                'error': True,
                'exception': scheduled_error,
                'form_data': {
                    'to_email': to_email,
                    'cc_emails': cc_emails,
                    'bcc_emails': bcc_emails,
                    'subject': subject,
                    'body_text': body_text,
                    'body_html': body_html,
                    'business_card_id': business_card_id,
                }
            }
        queue_immediate_send = (
            not scheduled_at
            and str(request.POST.get('queue_send') or request.POST.get('queueSend') or '').lower()
            in {'1', 'true', 'yes', 'on'}
        )
        if queue_immediate_send:
            from django.utils import timezone
            scheduled_at = timezone.now()

        if scheduled_at:
            with transaction.atomic():
                scheduled_email = ScheduledEmail.objects.create(
                    user=request.user,
                    provider=profile.email_provider or ('gmail' if profile.gmail_token else 'smtp'),
                    sender_email=profile.gmail_email or profile.imap_email,
                    to_email=to_email,
                    cc_emails=cc_emails,
                    bcc_emails=bcc_emails,
                    subject=subject,
                    body=body_text,
                    body_html=full_body_html,
                    followup=followup,
                    schedule=schedule,
                    reply_to=reply_to,
                    business_card=business_card,
                    scheduled_at=scheduled_at,
                    metadata={
                        'autoAttachmentCount': len(attachments_info),
                        'queuedImmediate': queue_immediate_send,
                    },
                )
                _save_scheduled_email_attachments(scheduled_email, attachment_entries)

            from django.utils import timezone
            if queue_immediate_send:
                messages.success(request, '이메일 발송 요청을 접수했습니다. 잠시 후 발송됩니다.')
            else:
                scheduled_label = timezone.localtime(scheduled_at).strftime('%Y-%m-%d %H:%M')
                messages.success(request, f'이메일이 {scheduled_label} 발송으로 예약되었습니다.')
            return redirect('/mailbox/?box=scheduled')

        # Gmail 또는 IMAP/SMTP로 이메일 발송
        
        if profile.gmail_token:
            # Gmail OAuth 사용
            gmail_service = GmailService(profile)
            
            # 첨부파일 처리
            attachments = [
                {
                    'filename': attachment['filename'],
                    'content': attachment['content'],
                    'mimetype': attachment['mimetype'],
                }
                for attachment in attachment_entries
            ]
            
            # 답장 정보
            in_reply_to = None
            thread_id = None
            if reply_to:
                in_reply_to = reply_to.gmail_message_id
                thread_id = reply_to.gmail_thread_id
            
            # 이메일 발송
            message_info = gmail_service.send_email(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=full_body_html,
                cc=cc_list,
                bcc=bcc_list,
                attachments=attachments,
                in_reply_to=in_reply_to,
                thread_id=thread_id
            )
            
            if not message_info:
                raise Exception("이메일 발송에 실패했습니다.")
            
            message_id = message_info['message_id']
            thread_id_result = message_info['thread_id']
            
        elif profile.imap_connected_at:
            # IMAP/SMTP 사용
            from .imap_utils import SMTPEmailService
            import uuid
            
            smtp_service = SMTPEmailService(profile)
            
            # 첨부파일 처리 (SMTP는 다른 형식)
            attachments = [
                {
                    'filename': attachment['filename'],
                    'content': attachment['content'],
                    'content_type': attachment['mimetype'],
                }
                for attachment in attachment_entries
            ]
            
            # SMTP로 이메일 발송
            success = smtp_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body_text,
                html_body=full_body_html,
                cc_emails=cc_list,
                bcc_emails=bcc_list,
                attachments=attachments
            )
            
            if not success:
                raise Exception("이메일 발송에 실패했습니다.")
            
            # IMAP의 경우 message_id와 thread_id를 생성
            message_id = f"<{uuid.uuid4()}@{profile.imap_email.split('@')[1]}>"
            thread_id_result = message_id  # IMAP는 thread 개념이 없으므로 message_id 사용
            
        else:
            raise Exception("이메일 계정이 연결되지 않았습니다.")
        
        # EmailLog 생성
        from django.utils import timezone
        
        # 일정 자동 생성 옵션 확인
        create_schedule_option = request.POST.get('create_schedule') == '1'
        created_schedule = None
        
        with transaction.atomic():
            # 일정 자동 생성 (팔로우업이 있고, 기존 일정이 없고, 옵션이 선택된 경우)
            if followup and not schedule and create_schedule_option:
                from datetime import datetime, time
                today = timezone.now().date()
                current_time = timezone.now().time()
                
                # 새 일정 생성
                created_schedule = Schedule.objects.create(
                    user=request.user,
                    company=request.user.userprofile.company,
                    followup=followup,
                    visit_date=today,
                    visit_time=current_time.replace(second=0, microsecond=0),
                    location='이메일',
                    status='completed',  # 이메일 발송은 완료 상태로
                    activity_type='customer_meeting',
                    notes=f'이메일 발송: {subject}'
                )
                schedule = created_schedule
                logger.info(f"Schedule auto-created: id={created_schedule.id} for followup={followup.id}")
            
            email_log = EmailLog.objects.create(
                email_type='sent',
                sender=request.user,
                sender_email=profile.gmail_email or profile.imap_email,
                recipient_email=to_email,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body=body_html if body_html else body_text,
                body_html=full_body_html,
                gmail_message_id=message_id,
                gmail_thread_id=thread_id_result,
                followup=followup,
                schedule=schedule,
                business_card=business_card,
                in_reply_to=reply_to,
                status='sent',
                sent_at=timezone.now(),
                attachments_info=attachments_info,  # 첨부파일 정보 저장
                user=request.user,  # IMAP용
                provider=profile.email_provider or 'gmail'  # IMAP용
            )
        
        if created_schedule:
            messages.success(request, f'이메일이 발송되었고, 일정이 자동 생성되었습니다.')
        else:
            messages.success(request, '이메일이 발송되었습니다.')
        
        # 리다이렉트 경로 결정
        if schedule:
            return redirect('reporting:schedule_detail', pk=schedule.id)
        elif followup:
            return redirect('reporting:mailbox_thread', thread_id=email_log.gmail_thread_id)
        else:
            return redirect('reporting:mailbox_sent')
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Exception in _handle_email_send: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 토큰 만료 에러 체크
        error_message = str(e)
        if 'invalid_grant' in error_message or 'Token has been expired or revoked' in error_message:
            messages.error(request, '⚠️ Gmail 인증이 만료되었습니다. 우측 상단 "Gmail 연동" 버튼을 눌러 재인증해주세요.')
        elif 'SMTP' in error_message and ('Authentication' in error_message or '535' in error_message):
            messages.error(request, '⚠️ IMAP/SMTP 인증 실패. 앱 비밀번호를 확인하거나 "IMAP 연결" 버튼으로 재설정해주세요.')
        else:
            messages.error(request, f'이메일 발송 실패: {error_message}')
        
        # POST 데이터 다시 가져오기
        return {
            'error': True,
            'exception': str(e),
            'form_data': {
                'to_email': request.POST.get('to_email', ''),
                'cc_emails': request.POST.get('cc_emails', ''),
                'bcc_emails': request.POST.get('bcc_emails', ''),
                'subject': request.POST.get('subject', ''),
                'body_text': request.POST.get('body_text', ''),
                'body_html': request.POST.get('body_html', ''),
                'business_card_id': request.POST.get('business_card_id', ''),
            }
        }


def send_scheduled_email(scheduled_email):
    """예약 메일 1건을 실제 발송하고 EmailLog로 전환한다."""
    import logging
    import uuid
    from django.utils import timezone

    logger = logging.getLogger(__name__)
    if scheduled_email.status not in {'pending', 'sending'}:
        return False

    profile = scheduled_email.user.userprofile
    attachment_entries = _scheduled_attachment_entries(scheduled_email)
    cc_list = _email_address_list(scheduled_email.cc_emails)
    bcc_list = _email_address_list(scheduled_email.bcc_emails)
    now = timezone.now()

    try:
        if profile.gmail_token:
            gmail_service = GmailService(profile)
            message_info = gmail_service.send_email(
                to_email=scheduled_email.to_email,
                subject=scheduled_email.subject,
                body_text=scheduled_email.body,
                body_html=scheduled_email.body_html,
                cc=cc_list,
                bcc=bcc_list,
                attachments=[
                    {
                        'filename': attachment['filename'],
                        'content': attachment['content'],
                        'mimetype': attachment['mimetype'],
                    }
                    for attachment in attachment_entries
                ],
                in_reply_to=scheduled_email.reply_to.gmail_message_id if scheduled_email.reply_to else None,
                thread_id=scheduled_email.reply_to.gmail_thread_id if scheduled_email.reply_to else None,
            )
            if not message_info:
                raise Exception("이메일 발송에 실패했습니다.")
            message_id = message_info['message_id']
            thread_id_result = message_info['thread_id']
            provider = 'gmail'
            sender_email = profile.gmail_email
        elif profile.imap_connected_at:
            from .imap_utils import SMTPEmailService

            smtp_service = SMTPEmailService(profile)
            success = smtp_service.send_email(
                to_email=scheduled_email.to_email,
                subject=scheduled_email.subject,
                body=scheduled_email.body,
                html_body=scheduled_email.body_html,
                cc_emails=cc_list,
                bcc_emails=bcc_list,
                attachments=[
                    {
                        'filename': attachment['filename'],
                        'content': attachment['content'],
                        'content_type': attachment['mimetype'],
                    }
                    for attachment in attachment_entries
                ],
            )
            if not success:
                raise Exception("이메일 발송에 실패했습니다.")
            domain = (profile.imap_email or 'scheduled.local').split('@')[-1]
            message_id = f"<{uuid.uuid4()}@{domain}>"
            thread_id_result = message_id
            provider = 'smtp'
            sender_email = profile.imap_email
        else:
            raise Exception("이메일 계정이 연결되지 않았습니다.")

        with transaction.atomic():
            email_log = EmailLog.objects.create(
                email_type='sent',
                sender=scheduled_email.user,
                sender_email=sender_email or scheduled_email.sender_email,
                recipient_email=scheduled_email.to_email,
                cc_emails=scheduled_email.cc_emails,
                bcc_emails=scheduled_email.bcc_emails,
                subject=scheduled_email.subject,
                body=scheduled_email.body,
                body_html=scheduled_email.body_html,
                gmail_message_id=message_id,
                gmail_thread_id=thread_id_result,
                followup=scheduled_email.followup,
                schedule=scheduled_email.schedule,
                business_card=scheduled_email.business_card,
                in_reply_to=scheduled_email.reply_to,
                status='sent',
                sent_at=now,
                attachments_info=_email_log_attachment_info_from_scheduled(attachment_entries),
                user=scheduled_email.user,
                provider=profile.email_provider or provider,
            )
            scheduled_email.status = 'sent'
            scheduled_email.sent_at = now
            scheduled_email.sent_email = email_log
            scheduled_email.error_message = ''
            scheduled_email.save(update_fields=['status', 'sent_at', 'sent_email', 'error_message', 'updated_at'])
        return True
    except Exception as exc:
        logger.error('예약 메일 발송 실패: scheduled_email=%s error=%s', scheduled_email.id, exc)
        scheduled_email.status = 'failed'
        scheduled_email.error_message = str(exc)
        scheduled_email.save(update_fields=['status', 'error_message', 'updated_at'])
        return False


def process_due_scheduled_emails(limit=50):
    """발송 시각이 지난 예약 메일을 처리한다."""
    from django.utils import timezone

    processed = 0
    sent = 0
    failed = 0
    due_ids = list(
        ScheduledEmail.objects.filter(
            status='pending',
            scheduled_at__lte=timezone.now(),
        ).order_by('scheduled_at', 'id').values_list('id', flat=True)[:limit]
    )
    for scheduled_email_id in due_ids:
        with transaction.atomic():
            scheduled_email = (
                ScheduledEmail.objects
                .select_for_update()
                .select_related('user', 'followup', 'schedule', 'reply_to', 'business_card')
                .filter(id=scheduled_email_id, status='pending')
                .first()
            )
            if not scheduled_email:
                continue
            scheduled_email.status = 'sending'
            scheduled_email.attempt_count += 1
            scheduled_email.last_attempt_at = timezone.now()
            scheduled_email.save(update_fields=['status', 'attempt_count', 'last_attempt_at', 'updated_at'])

        processed += 1
        if send_scheduled_email(scheduled_email):
            sent += 1
        else:
            failed += 1

    return {'processed': processed, 'sent': sent, 'failed': failed}


# ============================================
# 메일함 조회
# ============================================

def _mailbox_email_q(user):
    from django.db.models import Q

    return Q(sender=user) | Q(user=user) | Q(followup__user=user) | Q(schedule__user=user)


def _scheduled_email_q(user):
    from django.db.models import Q

    return Q(user=user) | Q(followup__user=user) | Q(schedule__user=user)


def _email_thread_identifier(email):
    return email.gmail_thread_id or email.thread_id or email.gmail_message_id or email.message_id or str(email.id)


def _email_contact_for_box(email, mailbox_type):
    if mailbox_type == 'sent':
        return email.recipient_name or email.to_name or email.recipient_email or email.to_email
    return email.from_name or email.sender_email or email.from_email or email.sender_email


def _email_datetime(email):
    return email.received_at or email.sent_at or email.created_at


def _email_text_preview(email, limit=160):
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = email.body_html or email.body or ''
    if email.body_html or _looks_like_email_html(raw):
        text = _email_html_to_display_text(raw, limit=limit)
    else:
        raw = _strip_html_style_blocks(raw)
        text = strip_tags(raw).replace('\xa0', ' ')
        text = _strip_css_text_artifacts(text)
    text = ' '.join(text.split())
    return Truncator(text).chars(limit)


def _email_body_text(email, limit=12000):
    import html
    from django.utils.text import Truncator

    raw = email.body_html or email.body or ''
    if email.body_html or _looks_like_email_html(raw):
        return _email_html_to_display_text(raw, limit=limit)

    text = raw
    text = html.unescape(text).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [' '.join(line.split()) for line in text.split('\n')]
    normalized = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append('')
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False

    return Truncator(_strip_quoted_text_for_display('\n'.join(normalized).strip())).chars(limit)


def _strip_quoted_html_for_display(raw_html):
    """React 메일 상세 표시에서는 Gmail/Outlook 인용 체인을 숨긴다."""
    import re

    quote_patterns = [
        r'(?is)<div[^>]+class=["\'][^"\']*gmail_quote[^"\']*["\'][^>]*>.*$',
        r'(?is)<div[^>]+id=["\']mail-editor-reference-message-container["\'][^>]*>.*$',
        r'(?is)<div[^>]+class=["\'][^"\']*ms-outlook-mobile-reference-message[^"\']*["\'][^>]*>.*$',
        r'(?is)<blockquote\b[^>]*>.*$',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, raw_html)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return raw_html
    return raw_html[:min(cut_positions)]


def _strip_quoted_text_for_display(text):
    import re

    quote_patterns = [
        r'\n\s*\d{4}년\s+\d{1,2}월\s+\d{1,2}일.{0,500}?(님이 작성:|wrote:)',
        r'\n\s*On .{1,500}? wrote:',
        r'\n\s*-{2,}\s*Original Message\s*-{2,}',
        r'\n\s*-----Original Message-----',
        r'\n\s*보낸 사람\s*:',
        r'\n\s*From\s*:',
        r'\n\s*Sent\s*:',
        r'\n\s*받는 사람\s*:',
        r'\n\s*To\s*:',
        r'\n\s*Get Outlook for',
        r'\n\s*받기 Mac용 Outlook',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return text
    return text[:min(cut_positions)].rstrip()


def _ensure_gmail_attachment_metadata(email, user):
    if email.attachments_info:
        return
    if not email.gmail_message_id:
        return
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return
    if not profile.gmail_token:
        return

    try:
        msg_detail = GmailService(profile).get_message_detail(email.gmail_message_id)
    except Exception:
        return
    attachments_info = _sanitize_received_attachments(
        (msg_detail or {}).get('attachments') or [],
        (msg_detail or {}).get('id') or email.gmail_message_id,
    )
    if attachments_info:
        email.attachments_info = attachments_info
        email.save(update_fields=['attachments_info', 'updated_at'])


def _email_attachment_payloads(email):
    rows = []
    for index, attachment in enumerate(email.attachments_info or []):
        if not isinstance(attachment, dict):
            continue
        filename = str(attachment.get('filename') or '').strip()
        if not filename:
            continue
        try:
            size = int(attachment.get('size') or 0)
        except (TypeError, ValueError):
            size = 0
        can_download = any([
            attachment.get('gmailAttachmentId'),
            attachment.get('contentBase64'),
            attachment.get('documentLogId'),
            attachment.get('scheduledAttachmentId'),
        ])
        rows.append({
            'filename': filename,
            'size': size,
            'mimetype': attachment.get('mimetype') or 'application/octet-stream',
            'source': attachment.get('source') or '',
            'downloadHref': reverse('reporting:mailbox_api_attachment_download', args=[email.id, index]) if can_download else '',
        })
    return rows


def _serialize_email_item(email, mailbox_type='inbox'):
    thread_id = _email_thread_identifier(email)
    followup = email.followup
    schedule = email.schedule
    happened_at = _email_datetime(email)
    return {
        'id': email.id,
        'type': email.email_type,
        'typeLabel': '보낸 메일' if email.email_type == 'sent' else '받은 메일',
        'subject': email.subject,
        'contact': _email_contact_for_box(email, mailbox_type),
        'senderEmail': email.sender_email or email.from_email,
        'recipientEmail': email.recipient_email or email.to_email,
        'ccEmails': email.cc_emails,
        'preview': _email_text_preview(email),
        'bodyText': _email_body_text(email),
        'sentAt': email.sent_at.isoformat() if email.sent_at else None,
        'receivedAt': email.received_at.isoformat() if email.received_at else None,
        'happenedAt': happened_at.isoformat() if happened_at else None,
        'isRead': email.is_read,
        'isStarred': email.is_starred,
        'isArchived': email.is_archived,
        'isTrashed': email.is_trashed,
        'status': email.status,
        'statusLabel': email.get_status_display(),
        'scheduledAt': None,
        'isScheduled': False,
        'threadId': thread_id,
        'threadHref': f'/mailbox/thread/{thread_id}/',
        'djangoThreadHref': reverse('reporting:mailbox_thread', args=[thread_id]),
        'replyHref': reverse('reporting:mailbox_api_reply', args=[email.id]),
        'toggleStarHref': reverse('reporting:mailbox_api_toggle_star', args=[email.id]),
        'archiveHref': reverse('reporting:mailbox_api_archive', args=[email.id]),
        'trashHref': reverse('reporting:mailbox_api_move_to_trash', args=[email.id]),
        'restoreHref': reverse('reporting:mailbox_api_restore', args=[email.id]),
        'deleteHref': reverse('reporting:mailbox_api_delete', args=[email.id]),
        'cancelHref': '',
        'followup': {
            'id': followup.id if followup else None,
            'customer': followup.customer_name if followup else '',
            'company': followup.company.name if followup and followup.company else '',
            'department': followup.department.name if followup and followup.department else '',
            'href': f'/customers/{followup.id}/' if followup else '',
            'djangoHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
        },
        'schedule': {
            'id': schedule.id if schedule else None,
            'href': f'/schedules/{schedule.id}/' if schedule else '',
            'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        },
        'attachments': _email_attachment_payloads(email),
    }


def _serialize_scheduled_email_item(scheduled_email):
    followup = scheduled_email.followup
    schedule = scheduled_email.schedule
    scheduled_at = scheduled_email.scheduled_at
    preview = _email_html_to_display_text(scheduled_email.body_html, limit=160) if scheduled_email.body_html else ' '.join((scheduled_email.body or '').split())[:160]
    return {
        'id': scheduled_email.id,
        'type': 'sent',
        'typeLabel': '예약 메일',
        'subject': scheduled_email.subject,
        'contact': scheduled_email.to_email,
        'senderEmail': scheduled_email.sender_email,
        'recipientEmail': scheduled_email.to_email,
        'ccEmails': scheduled_email.cc_emails,
        'preview': preview,
        'bodyText': scheduled_email.body,
        'sentAt': None,
        'receivedAt': None,
        'happenedAt': scheduled_at.isoformat() if scheduled_at else None,
        'isRead': True,
        'isStarred': False,
        'isArchived': False,
        'isTrashed': False,
        'status': scheduled_email.status,
        'statusLabel': scheduled_email.get_status_display(),
        'scheduledAt': scheduled_at.isoformat() if scheduled_at else None,
        'isScheduled': scheduled_email.status == 'pending',
        'threadId': f'scheduled-{scheduled_email.id}',
        'threadHref': f'/mailbox/scheduled/{scheduled_email.id}/',
        'djangoThreadHref': '',
        'replyHref': '',
        'toggleStarHref': '',
        'archiveHref': '',
        'trashHref': '',
        'restoreHref': '',
        'deleteHref': '',
        'sendNowHref': reverse('reporting:mailbox_api_send_scheduled_now', args=[scheduled_email.id]),
        'cancelHref': reverse('reporting:mailbox_api_cancel_scheduled', args=[scheduled_email.id]),
        'followup': {
            'id': followup.id if followup else None,
            'customer': followup.customer_name if followup else '',
            'company': followup.company.name if followup and followup.company else '',
            'department': followup.department.name if followup and followup.department else '',
            'href': f'/customers/{followup.id}/' if followup else '',
            'djangoHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
        },
        'schedule': {
            'id': schedule.id if schedule else None,
            'href': f'/schedules/{schedule.id}/' if schedule else '',
            'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        },
        'attachments': _scheduled_email_attachment_payloads(scheduled_email),
    }


def _mailbox_connection_payload(profile):
    provider = profile.email_provider or ('gmail' if profile.gmail_token else 'imap')
    address = profile.gmail_email or profile.imap_email or ''
    connected = bool(profile.gmail_token or profile.imap_connected_at)
    return {
        'connected': connected,
        'provider': provider,
        'address': address,
        'gmailConnected': bool(profile.gmail_token),
        'imapConnected': bool(profile.imap_connected_at),
        'lastSyncAt': (
            profile.gmail_last_sync_at.isoformat() if profile.gmail_last_sync_at
            else profile.imap_last_sync_at.isoformat() if profile.imap_last_sync_at
            else None
        ),
        'connectHref': reverse('reporting:gmail_connect'),
        'imapConnectHref': reverse('reporting:imap_connect'),
        'profileHref': reverse('reporting:profile'),
    }


def _mailbox_counts(user):
    base = EmailLog.objects.filter(_mailbox_email_q(user))
    scheduled = ScheduledEmail.objects.filter(_scheduled_email_q(user), status='pending')
    return {
        'inbox': base.filter(email_type='received', is_trashed=False, is_archived=False).count(),
        'sent': base.filter(email_type='sent', is_trashed=False).count(),
        'scheduled': scheduled.count(),
        'starred': base.filter(is_starred=True, is_trashed=False).count(),
        'archived': base.filter(is_archived=True, is_trashed=False).count(),
        'trash': base.filter(is_trashed=True).count(),
        'unread': base.filter(email_type='received', is_read=False, is_trashed=False).count(),
    }


def _mailbox_queryset(user, mailbox_type):
    from django.db.models.functions import Coalesce

    base = EmailLog.objects.filter(_mailbox_email_q(user)).select_related(
        'sender', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card'
    )
    if mailbox_type == 'sent':
        return base.filter(email_type='sent', is_trashed=False).order_by('-sent_at', '-created_at')
    if mailbox_type == 'starred':
        return base.filter(is_starred=True, is_trashed=False).order_by(Coalesce('received_at', 'sent_at', 'created_at').desc())
    if mailbox_type == 'archived':
        return base.filter(is_archived=True, is_trashed=False).order_by(Coalesce('received_at', 'sent_at', 'created_at').desc())
    if mailbox_type == 'trash':
        return base.filter(is_trashed=True).order_by('-trashed_at', '-created_at')
    return base.filter(email_type='received', is_trashed=False, is_archived=False).order_by(
        Coalesce('received_at', 'created_at').desc()
    )


def _mail_schedule_for_user(user, schedule_id):
    if not schedule_id:
        return None, None
    try:
        schedule = Schedule.objects.select_related('user', 'followup', 'followup__user').get(id=schedule_id)
    except (Schedule.DoesNotExist, ValueError):
        return None, JsonResponse({'success': False, 'error': '선택한 일정을 찾을 수 없습니다.'}, status=404)

    from .views import can_access_user_data
    if not can_access_user_data(user, schedule.user):
        return None, JsonResponse({'success': False, 'error': '일정 메일 발송 권한이 없습니다.'}, status=403)
    return schedule, None


def _mailbox_create_payload(user, schedule=None):
    followups = FollowUp.objects.filter(user=user).select_related('company', 'department').order_by('company__name', 'customer_name')
    business_cards = BusinessCard.objects.filter(user=user, is_active=True).order_by('-is_default', '-created_at')
    auto_attachments = _auto_document_candidates_for_schedule(schedule) if schedule else []
    return {
        'canSend': True,
        'message': '',
        'submitUrl': reverse('reporting:mailbox_api_send'),
        'djangoUrl': reverse('reporting:send_email_from_mailbox'),
        'autoAttachments': auto_attachments,
        'autoAttachLabel': _auto_document_attach_label(auto_attachments),
        'schedule': {
            'id': schedule.id,
            'activityType': schedule.activity_type,
        } if schedule else None,
        'internalCcEmails': _internal_cc_emails_for_user(user),
        'internalCcContacts': _internal_cc_contacts_for_user(user),
        'customers': [
            {
                'id': followup.id,
                'customer': followup.customer_name or '',
                'company': followup.company.name if followup.company else '',
                'department': followup.department.name if followup.department else '',
                'email': followup.email or '',
            }
            for followup in followups
        ],
        'businessCards': [
            {
                'id': card.id,
                'name': card.name,
                'fullName': card.full_name,
                'email': card.email,
                'isDefault': card.is_default,
            }
            for card in business_cards
        ],
    }


def _followup_allowed_for_mail(user, followup):
    profile = user.userprofile
    if profile.is_admin():
        return True
    if followup.user_id == user.id:
        return True
    if profile.company and followup.user_id:
        try:
            return followup.user.userprofile.company_id == profile.company_id
        except UserProfile.DoesNotExist:
            return False
    return False


def _json_method_error():
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'}, status=405)


def mailbox_api_list(request):
    """React 메일함 목록 API"""
    from django.db.models import Q

    auth_response = api_login_required_or_readonly_response(request)
    if auth_response:
        return auth_response
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'}, status=405)

    mailbox_type = request.GET.get('box') or 'inbox'
    if mailbox_type not in {'inbox', 'sent', 'scheduled', 'starred', 'archived', 'trash'}:
        mailbox_type = 'inbox'

    query = (request.GET.get('q') or '').strip()
    if mailbox_type == 'scheduled':
        emails = ScheduledEmail.objects.filter(
            _scheduled_email_q(request.user),
            status='pending',
        ).select_related('user', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card').prefetch_related(
            'attachments'
        ).order_by('scheduled_at', 'created_at')
        if query:
            emails = emails.filter(
                Q(subject__icontains=query) |
                Q(body__icontains=query) |
                Q(body_html__icontains=query) |
                Q(to_email__icontains=query) |
                Q(cc_emails__icontains=query) |
                Q(followup__customer_name__icontains=query) |
                Q(followup__company__name__icontains=query) |
                Q(followup__department__name__icontains=query)
            )
    else:
        emails = _mailbox_queryset(request.user, mailbox_type)
        if query:
            emails = emails.filter(
                Q(subject__icontains=query) |
                Q(body__icontains=query) |
                Q(body_html__icontains=query) |
                Q(sender_email__icontains=query) |
                Q(recipient_email__icontains=query) |
                Q(followup__customer_name__icontains=query) |
                Q(followup__company__name__icontains=query) |
                Q(followup__department__name__icontains=query)
            )

    paginator = Paginator(emails, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    profile = request.user.userprofile
    schedule = None
    schedule_id = request.GET.get('schedule_id') or request.GET.get('scheduleId')
    if schedule_id:
        schedule, schedule_error = _mail_schedule_for_user(request.user, schedule_id)
        if schedule_error:
            return schedule_error

    return JsonResponse({
        'success': True,
        'source': 'django',
        'mailboxType': mailbox_type,
        'filters': {
            'q': query,
            'page': page_obj.number,
        },
        'connection': _mailbox_connection_payload(profile),
        'counts': _mailbox_counts(request.user),
        'pagination': {
            'page': page_obj.number,
            'totalPages': paginator.num_pages,
            'totalCount': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
            'nextPage': page_obj.next_page_number() if page_obj.has_next() else None,
            'previousPage': page_obj.previous_page_number() if page_obj.has_previous() else None,
        },
        'links': {
            'inbox': '/mailbox/?box=inbox',
            'sent': '/mailbox/?box=sent',
            'scheduled': '/mailbox/?box=scheduled',
            'starred': '/mailbox/?box=starred',
            'archived': '/mailbox/?box=archived',
            'trash': '/mailbox/?box=trash',
            'sync': reverse('reporting:mailbox_api_sync'),
            'djangoInbox': reverse('reporting:mailbox_inbox'),
            'djangoSent': reverse('reporting:mailbox_sent'),
        },
        'create': _mailbox_create_payload(request.user, schedule=schedule),
        'emails': [
            _serialize_scheduled_email_item(email) if mailbox_type == 'scheduled' else _serialize_email_item(email, mailbox_type)
            for email in page_obj
        ],
    })


@login_required
def mailbox_api_thread(request, thread_id):
    """React 메일 스레드 상세 API"""
    from django.db.models import Q

    emails = EmailLog.objects.filter(
        _mailbox_email_q(request.user),
        Q(gmail_thread_id=thread_id) | Q(thread_id=thread_id) | Q(message_id=thread_id) | Q(gmail_message_id=thread_id)
    ).select_related('sender', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card').order_by(
        'sent_at', 'received_at', 'created_at'
    )

    if not emails.exists():
        return JsonResponse({'success': False, 'error': '메일 스레드를 찾을 수 없습니다.'}, status=404)

    unread = emails.filter(email_type='received', is_read=False)
    if unread.exists():
        unread.update(is_read=True)

    first_email = emails.first()
    last_received_email = emails.filter(email_type='received').order_by('-sent_at', '-received_at', '-created_at').first()
    last_email = emails.order_by('-sent_at', '-received_at', '-created_at').first()
    reply_target_email = last_received_email or last_email
    profile = request.user.userprofile
    email_rows = list(emails)
    for email in email_rows:
        _ensure_gmail_attachment_metadata(email, request.user)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'thread': {
            'id': thread_id,
            'subject': first_email.subject if first_email else '',
            'followup': _serialize_email_item(first_email)['followup'] if first_email else None,
            'messageCount': emails.count(),
            'lastReceivedEmailId': last_received_email.id if last_received_email else None,
        },
        'connection': _mailbox_connection_payload(profile),
        'links': {
            'mailbox': '/mailbox/',
            'djangoThread': reverse('reporting:mailbox_thread', args=[thread_id]),
            'reply': reverse('reporting:mailbox_api_reply', args=[reply_target_email.id]) if reply_target_email else '',
        },
        'create': _mailbox_create_payload(request.user),
        'emails': [_serialize_email_item(email) for email in email_rows],
    })


@login_required
def mailbox_api_scheduled_detail(request, scheduled_email_id):
    """React 예약메일 상세 API"""
    scheduled_email = ScheduledEmail.objects.filter(
        _scheduled_email_q(request.user),
        id=scheduled_email_id,
        status='pending',
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card'
    ).prefetch_related('attachments').first()
    if not scheduled_email:
        return JsonResponse({'success': False, 'error': '예약 메일을 찾을 수 없습니다.'}, status=404)

    profile = request.user.userprofile
    item = _serialize_scheduled_email_item(scheduled_email)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'thread': {
            'id': f'scheduled-{scheduled_email.id}',
            'subject': scheduled_email.subject,
            'followup': item['followup'],
            'messageCount': 1,
            'lastReceivedEmailId': None,
            'isScheduled': True,
        },
        'connection': _mailbox_connection_payload(profile),
        'links': {
            'mailbox': '/mailbox/?box=scheduled',
            'djangoThread': '',
            'reply': '',
        },
        'create': _mailbox_create_payload(request.user),
        'emails': [item],
    })


@login_required
def mailbox_api_send(request):
    """React 메일 작성 API"""
    if request.method != 'POST':
        return _json_method_error()

    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 먼저 연결해주세요.'}, status=400)

    followup = None
    schedule = None
    schedule_id = request.POST.get('schedule_id') or request.POST.get('scheduleId')
    if schedule_id:
        schedule, schedule_error = _mail_schedule_for_user(request.user, schedule_id)
        if schedule_error:
            return schedule_error
        followup = schedule.followup

    selected_followup_id = request.POST.get('selected_followup_id') or request.POST.get('followup_id')
    if selected_followup_id and not followup:
        try:
            followup = FollowUp.objects.select_related('user', 'user__userprofile').get(id=selected_followup_id)
        except (FollowUp.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': '선택한 고객을 찾을 수 없습니다.'}, status=404)
        if not _followup_allowed_for_mail(request.user, followup):
            return JsonResponse({'success': False, 'error': '고객 메일 발송 권한이 없습니다.'}, status=403)
    elif selected_followup_id and followup and str(followup.id) != str(selected_followup_id):
        return JsonResponse({'success': False, 'error': '일정과 고객 정보가 일치하지 않습니다.'}, status=400)

    result = _handle_email_send(
        request,
        schedule=schedule,
        followup=followup,
        auto_attach_schedule_documents=bool(schedule),
    )
    if isinstance(result, dict):
        return JsonResponse({
            'success': False,
            'error': result.get('exception') or '메일 발송 입력값을 확인해주세요.',
            'form': result.get('form_data', {}),
        }, status=400)

    location = result.get('Location', '/mailbox/?box=sent') if hasattr(result, 'get') else '/mailbox/?box=sent'
    scheduled_requested = bool(_mailbox_scheduled_at_value(request))
    queued_requested = (
        not scheduled_requested
        and str(request.POST.get('queue_send') or request.POST.get('queueSend') or '').lower()
        in {'1', 'true', 'yes', 'on'}
    )
    return JsonResponse({
        'success': True,
        'scheduled': scheduled_requested,
        'queued': queued_requested,
        'message': (
            '이메일을 예약했습니다.'
            if scheduled_requested
            else '이메일 발송 요청을 접수했습니다. 잠시 후 발송됩니다.'
            if queued_requested
            else '이메일이 발송되었습니다.'
        ),
        'href': location.replace('/reporting/mailbox/thread/', '/mailbox/thread/') if location else '/mailbox/?box=sent',
        'djangoHref': location,
    })


@login_required
def mailbox_api_reply(request, email_id):
    """React 메일 답장 API"""
    if request.method != 'POST':
        return _json_method_error()

    email = EmailLog.objects.filter(_mailbox_email_q(request.user), id=email_id).select_related('followup', 'schedule').first()
    if not email:
        return JsonResponse({'success': False, 'error': '답장할 메일을 찾을 수 없습니다.'}, status=404)

    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 먼저 연결해주세요.'}, status=400)

    result = _handle_email_send(request, reply_to=email)
    if isinstance(result, dict):
        return JsonResponse({
            'success': False,
            'error': result.get('exception') or '메일 답장 입력값을 확인해주세요.',
            'form': result.get('form_data', {}),
        }, status=400)

    thread_id = _email_thread_identifier(email)
    scheduled_requested = bool(_mailbox_scheduled_at_value(request))
    queued_requested = (
        not scheduled_requested
        and str(request.POST.get('queue_send') or request.POST.get('queueSend') or '').lower()
        in {'1', 'true', 'yes', 'on'}
    )
    return JsonResponse({
        'success': True,
        'scheduled': scheduled_requested,
        'queued': queued_requested,
        'message': (
            '답장을 예약했습니다.'
            if scheduled_requested
            else '답장 발송 요청을 접수했습니다. 잠시 후 발송됩니다.'
            if queued_requested
            else '답장을 발송했습니다.'
        ),
        'href': '/mailbox/?box=scheduled' if scheduled_requested or queued_requested else f'/mailbox/thread/{thread_id}/',
        'djangoHref': '/mailbox/?box=scheduled' if scheduled_requested or queued_requested else reverse('reporting:mailbox_thread', args=[thread_id]),
    })


@login_required
def mailbox_api_cancel_scheduled(request, scheduled_email_id):
    """예약 메일 취소 API"""
    if request.method != 'POST':
        return _json_method_error()

    scheduled_email = ScheduledEmail.objects.filter(
        _scheduled_email_q(request.user),
        id=scheduled_email_id,
        status='pending',
    ).first()
    if not scheduled_email:
        return JsonResponse({'success': False, 'error': '취소할 예약 메일을 찾을 수 없습니다.'}, status=404)

    scheduled_email.status = 'cancelled'
    scheduled_email.error_message = ''
    scheduled_email.save(update_fields=['status', 'error_message', 'updated_at'])
    return JsonResponse({
        'success': True,
        'message': '예약 메일을 취소했습니다.',
        'href': '/mailbox/?box=scheduled',
    })


@login_required
def mailbox_api_send_scheduled_now(request, scheduled_email_id):
    """예약 메일을 사용자가 즉시 발송한다."""
    if request.method != 'POST':
        return _json_method_error()

    with transaction.atomic():
        scheduled_email = (
            ScheduledEmail.objects
            .select_for_update()
            .select_related('user', 'followup', 'schedule', 'reply_to', 'business_card')
            .prefetch_related('attachments')
            .filter(
                _scheduled_email_q(request.user),
                id=scheduled_email_id,
                status='pending',
            )
            .first()
        )
        if not scheduled_email:
            return JsonResponse({'success': False, 'error': '발송할 예약 메일을 찾을 수 없습니다.'}, status=404)
        scheduled_email.status = 'sending'
        scheduled_email.attempt_count += 1
        from django.utils import timezone
        scheduled_email.last_attempt_at = timezone.now()
        scheduled_email.save(update_fields=['status', 'attempt_count', 'last_attempt_at', 'updated_at'])

    if not send_scheduled_email(scheduled_email):
        scheduled_email.refresh_from_db()
        return JsonResponse({
            'success': False,
            'error': scheduled_email.error_message or '예약 메일 즉시 발송에 실패했습니다.',
            'href': f'/mailbox/scheduled/{scheduled_email.id}/',
        }, status=400)

    scheduled_email.refresh_from_db()
    sent_email = scheduled_email.sent_email
    href = f'/mailbox/thread/{_email_thread_identifier(sent_email)}/' if sent_email else '/mailbox/?box=sent'
    return JsonResponse({
        'success': True,
        'message': '예약 메일을 바로 발송했습니다.',
        'href': href,
        'djangoHref': reverse('reporting:mailbox_thread', args=[_email_thread_identifier(sent_email)]) if sent_email else reverse('reporting:mailbox_sent'),
    })


@login_required
def mailbox_api_sync(request):
    """React 메일 동기화 API"""
    if request.method != 'POST':
        return _json_method_error()
    return sync_received_emails(request)


@login_required
def mailbox_api_toggle_star(request, email_id):
    return toggle_star_email(request, email_id)


@login_required
def mailbox_api_archive(request, email_id):
    return archive_email(request, email_id)


@login_required
def mailbox_api_move_to_trash(request, email_id):
    return move_to_trash_email(request, email_id)


@login_required
def mailbox_api_restore(request, email_id):
    return restore_email(request, email_id)


@login_required
def mailbox_api_delete(request, email_id):
    return delete_email(request, email_id)


@login_required
def mailbox_api_attachment_download(request, email_id, attachment_index):
    import base64
    from urllib.parse import quote

    email = EmailLog.objects.filter(
        _mailbox_email_q(request.user),
        id=email_id,
    ).select_related('user').first()
    if not email:
        return JsonResponse({'success': False, 'error': '메일을 찾을 수 없습니다.'}, status=404)

    attachments = email.attachments_info or []
    try:
        attachment = attachments[int(attachment_index)]
    except (IndexError, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': '첨부파일을 찾을 수 없습니다.'}, status=404)
    if not isinstance(attachment, dict):
        return JsonResponse({'success': False, 'error': '첨부파일 정보를 읽을 수 없습니다.'}, status=404)

    filename = str(attachment.get('filename') or 'attachment').strip() or 'attachment'
    mimetype = attachment.get('mimetype') or 'application/octet-stream'
    content = None

    if attachment.get('contentBase64'):
        try:
            content = base64.b64decode(attachment['contentBase64'])
        except Exception:
            content = None

    if content is None and attachment.get('documentLogId'):
        log = DocumentGenerationLog.objects.filter(id=attachment.get('documentLogId')).first()
        if log and log.file:
            with log.file.open('rb') as file_handle:
                content = file_handle.read()
            filename = log.filename or filename

    if content is None and attachment.get('scheduledAttachmentId'):
        scheduled_attachment = ScheduledEmailAttachment.objects.filter(id=attachment.get('scheduledAttachmentId')).first()
        scheduled_email = getattr(email, 'scheduled_source', None)
        if (
            scheduled_attachment
            and scheduled_email
            and scheduled_attachment.scheduled_email_id == scheduled_email.id
            and scheduled_attachment.file
        ):
            with scheduled_attachment.file.open('rb') as file_handle:
                content = file_handle.read()
            filename = scheduled_attachment.filename or filename

    if content is None and attachment.get('gmailAttachmentId'):
        profile = request.user.userprofile
        if not profile.gmail_token:
            return JsonResponse({'success': False, 'error': 'Gmail 연결이 필요합니다.'}, status=400)
        message_id = attachment.get('gmailMessageId') or email.gmail_message_id
        content = GmailService(profile).get_attachment(message_id, attachment.get('gmailAttachmentId'))

    if content is None:
        return JsonResponse({'success': False, 'error': '첨부파일을 다운로드할 수 없습니다.'}, status=404)

    response = HttpResponse(content, content_type=mimetype)
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return response


@login_required
def mailbox_inbox(request):
    """받은편지함 (본인 담당 팔로우업 연결 메일만)"""
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return _redirect_profile_react()
    
    # DB에서 수신 메일 조회 (본인 담당 팔로우업만, 휴지통 제외)
    # 최신순 정렬: received_at이 null이면 created_at 사용
    from django.db.models.functions import Coalesce
    emails = EmailLog.objects.filter(
        email_type='received',
        followup__isnull=False,  # 팔로우업 연결된 메일만
        followup__user=request.user,  # 본인 담당 팔로우업만
        is_trashed=False,  # 휴지통 제외
        is_archived=False  # 보관함 제외
    ).select_related('followup', 'sender', 'business_card').order_by(
        Coalesce('received_at', 'created_at').desc()
    )
    
    # 페이지네이션 (20개씩)
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 중요편지 개수
    starred_count = EmailLog.objects.filter(
        followup__user=request.user,
        is_starred=True,
        is_trashed=False
    ).count()
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'inbox',
        'total_count': paginator.count,
        'starred_count': starred_count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_sent(request):
    """보낸편지함"""
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return _redirect_profile_react()
    
    emails = EmailLog.objects.filter(
        email_type='sent',
        sender=request.user,
        is_trashed=False
    ).select_related('followup', 'schedule', 'business_card').order_by('-sent_at')
    
    # 페이지네이션 (20개씩)
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'sent',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_starred(request):
    """중요편지함"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return _redirect_profile_react()
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_starred=True,
        is_trashed=False
    ).select_related('followup', 'schedule', 'business_card').order_by(
        Coalesce('received_at', 'sent_at').desc()
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'starred',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_archived(request):
    """보관함"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_archived=True,
        is_trashed=False
    ).select_related('followup', 'schedule', 'business_card').order_by(
        Coalesce('received_at', 'sent_at').desc()
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'archived',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_trash(request):
    """휴지통"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_trashed=True
    ).select_related('followup', 'schedule', 'business_card').order_by(
        '-trashed_at'
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'trash',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def toggle_star_email(request, email_id):
    """이메일 중요 표시 토글"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_starred = not email.is_starred
        email.save(update_fields=['is_starred'])
        
        return JsonResponse({
            'success': True,
            'is_starred': email.is_starred,
            'message': '중요 표시됨' if email.is_starred else '중요 표시 해제됨'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def archive_email(request, email_id):
    """이메일 보관"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_archived = not email.is_archived
        email.save(update_fields=['is_archived'])
        
        return JsonResponse({
            'success': True,
            'is_archived': email.is_archived,
            'message': '보관함으로 이동됨' if email.is_archived else '보관 해제됨'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def move_to_trash_email(request, email_id):
    """이메일 휴지통으로 이동"""
    from django.db.models import Q
    from django.utils import timezone
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_trashed = True
        email.trashed_at = timezone.now()
        email.save(update_fields=['is_trashed', 'trashed_at'])
        
        return JsonResponse({
            'success': True,
            'message': '휴지통으로 이동되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def restore_email(request, email_id):
    """이메일 복원 (휴지통에서)"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id,
            is_trashed=True
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_trashed = False
        email.trashed_at = None
        email.save(update_fields=['is_trashed', 'trashed_at'])
        
        return JsonResponse({
            'success': True,
            'message': '이메일이 복원되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mailbox_thread(request, thread_id):
    """이메일 스레드 상세 (대화 전체)"""
    import logging
    logger = logging.getLogger(__name__)
    
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return _redirect_profile_react()
    
    # Gmail에서 최신 스레드 데이터 가져와서 DB 동기화
    if profile.gmail_token:
        try:
            gmail_service = GmailService(profile)
            thread_data = gmail_service.get_thread(thread_id)
            
            if thread_data and thread_data.get('messages'):
                logger.info(f"스레드 {thread_id}: Gmail에서 {len(thread_data['messages'])}개 메시지 조회")
                
                # DB에 저장된 메시지 ID 목록
                existing_message_ids = set(
                    EmailLog.objects.filter(gmail_thread_id=thread_id)
                    .values_list('gmail_message_id', flat=True)
                )
                
                # 새로운 메시지만 DB에 저장
                new_count = 0
                for msg_detail in thread_data['messages']:
                    msg_id = msg_detail['id']
                    
                    if msg_id not in existing_message_ids:
                        # 새 메시지 저장
                        try:
                            from .imap_utils import save_email_to_db
                            
                            # 이메일 타입 결정 (From 주소로 판단)
                            from_email = msg_detail.get('from', '').lower()
                            user_email = request.user.email.lower() if request.user.email else ''
                            email_type = 'sent' if user_email in from_email else 'received'
                            
                            save_email_to_db(
                                user=request.user,
                                message_id=msg_id,
                                thread_id=thread_id,
                                sender_email=msg_detail.get('from', ''),
                                recipient_email=msg_detail.get('to', ''),
                                cc_emails=msg_detail.get('cc', ''),
                                bcc_emails=msg_detail.get('bcc', ''),
                                subject=msg_detail.get('subject', ''),
                                body=msg_detail.get('body_text') or msg_detail.get('body') or msg_detail.get('snippet', ''),
                                body_html=msg_detail.get('body_html', ''),
                                sent_at=msg_detail.get('date'),
                                email_type=email_type,
                                labels=msg_detail.get('labels', []),
                                attachments_info=_sanitize_received_attachments(
                                    msg_detail.get('attachments') or [],
                                    msg_id,
                                ),
                            )
                            new_count += 1
                            logger.info(f"새 메시지 저장: {msg_id}")
                        except Exception as e:
                            logger.error(f"메시지 저장 실패 ({msg_id}): {e}")
                            continue
                    else:
                        existing_email = EmailLog.objects.filter(gmail_message_id=msg_id).first()
                        if existing_email and not existing_email.attachments_info:
                            attachments_info = _sanitize_received_attachments(
                                msg_detail.get('attachments') or [],
                                msg_id,
                            )
                            if attachments_info:
                                existing_email.attachments_info = attachments_info
                                existing_email.save(update_fields=['attachments_info', 'updated_at'])
                
                if new_count > 0:
                    logger.info(f"스레드 {thread_id}: {new_count}개 새 메시지 동기화 완료")
        except Exception as e:
            logger.error(f"스레드 동기화 오류: {e}")
            # 동기화 실패해도 계속 진행
    
    # DB에서 스레드의 모든 메일 조회
    emails = EmailLog.objects.filter(
        gmail_thread_id=thread_id
    ).select_related('sender', 'followup', 'schedule', 'business_card').order_by('sent_at')
    
    if not emails.exists():
        messages.error(request, '해당 스레드를 찾을 수 없습니다.')
        return redirect('reporting:mailbox_inbox')
    
    # 읽음 표시 (수신 메일만)
    unread_emails = emails.filter(email_type='received', is_read=False)
    if unread_emails.exists():
        unread_emails.update(is_read=True)
        
        # Gmail에도 읽음 표시
        gmail_service = GmailService(profile)
        for email in unread_emails:
            try:
                gmail_service.mark_as_read(email.gmail_message_id)
            except:
                pass  # 실패해도 계속 진행
    
    email_rows = list(emails)
    for email in email_rows:
        email.display_body_text = _email_body_text(email)

    # 답장 대상: 가장 최근 수신 메일
    last_received_email = emails.filter(email_type='received').order_by('-sent_at', '-received_at').first()
    
    context = {
        'thread_id': thread_id,
        'first_email': email_rows[0],
        'emails': email_rows,
        'followup': email_rows[0].followup,
        'last_received_email': last_received_email,
    }
    return render(request, 'reporting/gmail/thread_detail.html', context)


@login_required
@login_required
@login_required
def sync_received_emails(request):
    """
    수동 메일 동기화
    - 마지막 동기화 시점 이후의 메일만 가져옴
    - 첫 동기화인 경우 최근 1일치
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 연결해주세요.'})
    
    try:
        # 마지막 동기화 시점 이후의 메일만 동기화
        if profile.gmail_token:
            synced_count = _sync_emails_by_days(request.user, days=1)
        else:
            synced_count = _sync_imap_emails_by_days(request.user, days=1)
        
        if synced_count > 0:
            message = f'{synced_count}개의 새 메일을 동기화했습니다.'
        else:
            message = '새로운 메일이 없습니다.'
        
        return JsonResponse({
            'success': True,
            'synced': synced_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_email(request, email_id):
    """이메일 삭제"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"delete_email called: email_id={email_id}, user={request.user.username}, method={request.method}")
    
    if request.method == 'POST':
        try:
            email = get_object_or_404(EmailLog, id=email_id)
            logger.info(f"Email found: id={email.id}, type={email.email_type}, sender={email.sender}, sender_email={email.sender_email}")
            
            # 권한 확인: 관리자, 본인이 보낸 메일, 또는 본인 팔로우업 관련 메일만 삭제 가능
            can_delete = False
            
            # 관리자는 모든 메일 삭제 가능
            if request.user.is_staff or request.user.is_superuser:
                can_delete = True
                logger.info("Delete allowed: user is staff/superuser")
            # 보낸 메일: sender가 본인이거나 sender_email이 본인 이메일
            elif email.email_type == 'sent':
                if email.sender == request.user:
                    can_delete = True
                    logger.info("Delete allowed: sender matches user")
                elif email.sender_email and request.user.email and email.sender_email == request.user.email:
                    can_delete = True
                    logger.info("Delete allowed: sender_email matches user email")
                else:
                    logger.info(f"Delete denied: sent mail - sender={email.sender}, user={request.user}, sender_email={email.sender_email}, user_email={request.user.email}")
            # 받은 메일: followup 담당자가 본인
            elif email.email_type == 'received':
                if email.followup and email.followup.user == request.user:
                    can_delete = True
                    logger.info("Delete allowed: followup user matches")
                elif not email.followup:
                    # followup이 없는 받은 메일은 삭제 가능
                    can_delete = True
                    logger.info("Delete allowed: no followup")
                else:
                    logger.info(f"Delete denied: received mail - followup.user={email.followup.user if email.followup else None}, user={request.user}")
            
            if not can_delete:
                logger.warning(f"Delete permission denied for email {email_id}")
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다.'})
            
            email.delete()
            logger.info(f"Email {email_id} deleted successfully")
            return JsonResponse({'success': True, 'message': '메일이 삭제되었습니다.'})
            
        except Exception as e:
            logger.exception(f"Error deleting email {email_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})


# ============================================
# 명함 관리
# ============================================

def _business_card_bool(value):
    return str(value or '').lower() in {'1', 'true', 'yes', 'on'}


def _gmail_api_login_required_response(request):
    return api_login_required_or_readonly_response(request)


def _business_card_payload(card, request=None, include_signature=True):
    logo_url = ''
    if card.logo:
        logo_url = card.logo.url
        if request:
            logo_url = request.build_absolute_uri(logo_url)
    return {
        'id': card.id,
        'name': card.name or '',
        'fullName': card.full_name or '',
        'title': card.title or '',
        'companyName': card.company_name or '',
        'department': card.department or '',
        'phone': card.phone or '',
        'mobile': card.mobile or '',
        'email': card.email or '',
        'address': card.address or '',
        'website': card.website or '',
        'fax': card.fax or '',
        'logoUrl': card.logo_url or '',
        'logoFileUrl': logo_url,
        'logoLinkUrl': card.logo_link_url or '',
        'signatureHtml': card.signature_html or '',
        'signaturePreviewHtml': card.generate_signature(request=request) if include_signature else '',
        'isDefault': bool(card.is_default),
        'isActive': bool(card.is_active),
        'createdAt': card.created_at.isoformat() if card.created_at else None,
        'updatedAt': card.updated_at.isoformat() if card.updated_at else None,
        'links': {
            'update': reverse('reporting:business_card_api_update', args=[card.id]),
            'delete': reverse('reporting:business_card_api_delete', args=[card.id]),
            'setDefault': reverse('reporting:business_card_api_set_default', args=[card.id]),
            'legacyEdit': reverse('reporting:business_card_edit', args=[card.id]),
        },
    }


def _business_cards_api_payload(request, message=''):
    cards = BusinessCard.objects.filter(
        user=request.user,
        is_active=True,
    ).order_by('-is_default', '-created_at')
    payload = {
        'success': True,
        'source': 'django',
        'cards': [_business_card_payload(card, request=request) for card in cards],
        'links': {
            'create': reverse('reporting:business_card_api_create'),
            'legacy': reverse('reporting:business_card_list'),
            'mailbox': '/mailbox/',
            'profile': '/profile/',
        },
    }
    if message:
        payload['message'] = message
    return payload


def _assign_business_card_fields(card, request):
    data = request.POST
    card.name = (data.get('name') or '').strip()
    card.full_name = (data.get('fullName') or data.get('full_name') or '').strip()
    card.title = (data.get('title') or '').strip()
    card.company_name = (data.get('companyName') or data.get('company_name') or '').strip()
    card.department = (data.get('department') or '').strip()
    card.phone = (data.get('phone') or '').strip()
    card.mobile = (data.get('mobile') or '').strip()
    card.email = (data.get('email') or '').strip()
    card.address = (data.get('address') or '').strip()
    card.website = (data.get('website') or '').strip()
    card.fax = (data.get('fax') or '').strip()
    card.logo_url = (data.get('logoUrl') or data.get('logo_url') or '').strip()
    card.logo_link_url = (data.get('logoLinkUrl') or data.get('logo_link_url') or '').strip()
    card.signature_html = data.get('signatureHtml') or data.get('signature_html') or ''
    card.is_default = _business_card_bool(data.get('isDefault') or data.get('is_default'))
    if request.FILES.get('logo'):
        card.logo = request.FILES['logo']


def _validate_business_card(card):
    errors = {}
    if not card.name:
        errors['name'] = '명함 이름을 입력하세요.'
    if not card.full_name:
        errors['fullName'] = '이름을 입력하세요.'
    if not card.email:
        errors['email'] = '이메일을 입력하세요.'
    else:
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(card.email)
        except ValidationError:
            errors['email'] = '올바른 이메일 주소를 입력하세요.'
    return errors


def business_card_api_list(request):
    """React 명함 관리 목록 API."""
    auth_response = _gmail_api_login_required_response(request)
    if auth_response:
        return auth_response
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'}, status=405)
    return JsonResponse(_business_cards_api_payload(request))


def business_card_api_create(request):
    """React 명함 생성 API."""
    auth_response = _gmail_api_login_required_response(request)
    if auth_response:
        return auth_response
    if request.method != 'POST':
        return _json_method_error()

    card = BusinessCard(user=request.user)
    _assign_business_card_fields(card, request)
    errors = _validate_business_card(card)
    if errors:
        return JsonResponse({'success': False, 'error': '입력값을 확인하세요.', 'errors': errors}, status=400)
    card.save()
    return JsonResponse(_business_cards_api_payload(request, '명함을 생성했습니다.'))


def business_card_api_update(request, card_id):
    """React 명함 수정 API."""
    auth_response = _gmail_api_login_required_response(request)
    if auth_response:
        return auth_response
    if request.method != 'POST':
        return _json_method_error()

    card = get_object_or_404(BusinessCard, id=card_id, user=request.user, is_active=True)
    _assign_business_card_fields(card, request)
    errors = _validate_business_card(card)
    if errors:
        return JsonResponse({'success': False, 'error': '입력값을 확인하세요.', 'errors': errors}, status=400)
    card.save()
    return JsonResponse(_business_cards_api_payload(request, '명함을 저장했습니다.'))


def business_card_api_delete(request, card_id):
    """React 명함 soft delete API."""
    auth_response = _gmail_api_login_required_response(request)
    if auth_response:
        return auth_response
    if request.method != 'POST':
        return _json_method_error()

    card = get_object_or_404(BusinessCard, id=card_id, user=request.user, is_active=True)
    card.is_active = False
    card.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse(_business_cards_api_payload(request, '명함을 삭제했습니다.'))


def business_card_api_set_default(request, card_id):
    """React 기본 명함 설정 API."""
    auth_response = _gmail_api_login_required_response(request)
    if auth_response:
        return auth_response
    if request.method != 'POST':
        return _json_method_error()

    card = get_object_or_404(BusinessCard, id=card_id, user=request.user, is_active=True)
    BusinessCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
    card.is_default = True
    card.save()
    return JsonResponse(_business_cards_api_payload(request, f'{card.name} 명함을 기본으로 설정했습니다.'))


@login_required
def business_card_list(request):
    """명함 목록"""
    cards = BusinessCard.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    # 각 카드의 서명을 미리 생성 (절대 URL 포함)
    for card in cards:
        card.signature_preview = card.generate_signature(request=request)
    
    context = {
        'cards': cards
    }
    return render(request, 'reporting/gmail/business_card_list.html', context)


@login_required
def business_card_create(request):
    """명함 생성"""
    if request.method == 'POST':
        try:
            card = BusinessCard.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                full_name=request.POST.get('full_name'),
                title=request.POST.get('title'),
                company_name=request.POST.get('company_name'),
                phone=request.POST.get('phone', ''),
                mobile=request.POST.get('mobile', ''),
                email=request.POST.get('email'),
                address=request.POST.get('address', ''),
                website=request.POST.get('website', ''),
                logo_url=request.POST.get('logo_url', ''),
                logo_link_url=request.POST.get('logo_link_url', ''),
                is_default=request.POST.get('is_default') == 'on'
            )
            
            # 로고 이미지 파일 업로드
            if 'logo' in request.FILES:
                card.logo = request.FILES['logo']
                card.save()
            
            messages.success(request, '명함이 생성되었습니다.')
            return redirect('reporting:business_card_list')
        except Exception as e:
            messages.error(request, f'명함 생성 실패: {str(e)}')
    
    return render(request, 'reporting/gmail/business_card_form.html', {'card': None})


@login_required
def business_card_edit(request, card_id):
    """명함 수정"""
    card = get_object_or_404(BusinessCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        try:
            card.name = request.POST.get('name')
            card.full_name = request.POST.get('full_name')
            card.title = request.POST.get('title')
            card.company_name = request.POST.get('company_name')
            card.phone = request.POST.get('phone', '')
            card.mobile = request.POST.get('mobile', '')
            card.email = request.POST.get('email')
            card.address = request.POST.get('address', '')
            card.website = request.POST.get('website', '')
            card.logo_url = request.POST.get('logo_url', '')
            card.logo_link_url = request.POST.get('logo_link_url', '')
            card.is_default = request.POST.get('is_default') == 'on'
            
            # 로고 이미지 파일 업로드
            if 'logo' in request.FILES:
                card.logo = request.FILES['logo']
            
            card.save()
            
            messages.success(request, '명함이 수정되었습니다.')
            return redirect('reporting:business_card_list')
        except Exception as e:
            messages.error(request, f'명함 수정 실패: {str(e)}')
    
    return render(request, 'reporting/gmail/business_card_form.html', {'card': card})


@login_required
def business_card_delete(request, card_id):
    """명함 삭제 (비활성화)"""
    if request.method == 'POST':
        card = get_object_or_404(BusinessCard, id=card_id, user=request.user)
        card.is_active = False
        card.save()
        
        messages.success(request, '명함이 삭제되었습니다.')
    
    return redirect('reporting:business_card_list')


@login_required
def business_card_set_default(request, card_id):
    """기본 명함 설정"""
    if request.method == 'POST':
        card = get_object_or_404(BusinessCard, id=card_id, user=request.user, is_active=True)
        
        # 기존 기본 명함 해제
        BusinessCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # 새 기본 명함 설정
        card.is_default = True
        card.save()
        
        messages.success(request, f'{card.name} 명함이 기본 명함으로 설정되었습니다.')
    
    return redirect('reporting:business_card_list')


# ============================================
# 이미지 업로드 (Quill 에디터용)
# ============================================

@login_required
def upload_editor_image(request):
    """Quill 에디터에서 이미지 업로드"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            import os
            from django.core.files.storage import default_storage
            from django.conf import settings
            
            uploaded_file = request.FILES['image']
            
            # 파일 크기 제한 (2MB)
            max_size = 2 * 1024 * 1024  # 2MB
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'success': False,
                    'error': '이미지 크기는 2MB 이하여야 합니다.'
                }, status=400)
            
            # 이미지 파일 타입 검증
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if uploaded_file.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'error': '지원하지 않는 이미지 형식입니다. (JPG, PNG, GIF, WebP만 가능)'
                }, status=400)
            
            # 파일명 생성 (중복 방지)
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = os.path.splitext(uploaded_file.name)[1]
            filename = f'email_images/{timestamp}_{uuid.uuid4().hex[:8]}{ext}'
            
            # 파일 저장
            file_path = default_storage.save(filename, uploaded_file)
            
            # 절대 URL 생성
            file_url = default_storage.url(file_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            return JsonResponse({
                'success': True,
                'url': absolute_url
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Image upload failed: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)
