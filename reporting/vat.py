"""부가세 계산의 단일 출처.

일정(Schedule.vat_mode)마다 입력한 금액을 어떻게 읽을지가 다르다.

- ``excluded`` (부가세 별도, 기본): 입력 금액 = 공급가. 매출 총액 = 공급가 × 1.1
- ``included`` (부가세 포함): 입력 금액 = 부가세까지 들어간 총액. 매출 총액 = 입력 금액
- ``none``     (부가세 없음): 입력 금액 = 총액, 세액 0

예전에는 이 규칙이 납품 품목 저장·대시보드 매출·외상·파이프라인·서류 생성 등 35곳 넘게
`* Decimal('1.1')` 로 흩어져 있었고, 일정의 부가세 모드는 서류 생성 한 곳만 반영했다.
그래서 "부가세 포함" 건은 서류와 매출 숫자가 10% 어긋났다. 이제 모든 곳이 이 모듈을 쓴다.

'별도'는 예전 계산식(× 1.1, 반올림 없음)을 그대로 유지해 기존 숫자가 1원도 바뀌지 않는다.
"""

from decimal import ROUND_HALF_UP, Decimal

VAT_EXCLUDED = 'excluded'
VAT_INCLUDED = 'included'
VAT_NONE = 'none'
VAT_MODES = (VAT_EXCLUDED, VAT_INCLUDED, VAT_NONE)

VAT_RATE = Decimal('0.1')
_GROSS_MULTIPLIER = Decimal('1.1')
_WON = Decimal('1')


def _dec(value):
    if value is None or value == '':
        return Decimal('0')
    return value if isinstance(value, Decimal) else Decimal(str(value))


def normalize_vat_mode(value):
    mode = str(value or '').strip()
    return mode if mode in VAT_MODES else VAT_EXCLUDED


def schedule_vat_mode(schedule):
    return normalize_vat_mode(getattr(schedule, 'vat_mode', None)) if schedule is not None else VAT_EXCLUDED


def gross_amount(entered, vat_mode):
    """입력 금액 → 부가세까지 포함한 총액(= CRM 매출 기준 금액)."""
    amount = _dec(entered)
    if normalize_vat_mode(vat_mode) == VAT_EXCLUDED:
        return amount * _GROSS_MULTIPLIER
    return amount


def supply_from_gross(gross, vat_mode):
    """총액(부가세 포함) → 공급가액. 부가세 없음이면 총액이 곧 공급가."""
    amount = _dec(gross)
    if normalize_vat_mode(vat_mode) == VAT_NONE:
        return amount
    return amount / _GROSS_MULTIPLIER


def split_amount(entered, vat_mode):
    """입력 금액 → (공급가액, 세액, 총액). 서류·견적서 표시용으로 원 단위 반올림."""
    amount = _dec(entered)
    mode = normalize_vat_mode(vat_mode)
    if mode == VAT_INCLUDED:
        supply = (amount / _GROSS_MULTIPLIER).quantize(_WON, rounding=ROUND_HALF_UP)
        return supply, amount - supply, amount
    if mode == VAT_NONE:
        return amount, Decimal('0'), amount
    tax = (amount * VAT_RATE).quantize(_WON, rounding=ROUND_HALF_UP)
    return amount, tax, amount + tax


def item_vat_mode(item):
    """납품/견적 품목이 따르는 부가세 모드 — 연결된 일정(직접 또는 활동 기록을 통해) 기준."""
    schedule = None
    cache = getattr(getattr(item, '_state', None), 'fields_cache', {}) or {}
    if getattr(item, 'schedule_id', None):
        schedule = cache.get('schedule') or getattr(item, 'schedule', None)
    elif getattr(item, 'history_id', None):
        history = cache.get('history') or getattr(item, 'history', None)
        if history is not None and getattr(history, 'schedule_id', None):
            schedule = history.schedule
    return schedule_vat_mode(schedule)


def item_gross_total(item, *, unit_price=None, quantity=None, vat_mode=None):
    """품목 1줄의 매출 총액. 단가는 할인 반영 단가(effective) 우선."""
    if unit_price is None:
        unit_price = item.get_effective_unit_price() if hasattr(item, 'get_effective_unit_price') else None
        if unit_price is None:
            unit_price = getattr(item, 'unit_price', None)
    qty = item.quantity if quantity is None else quantity
    mode = item_vat_mode(item) if vat_mode is None else vat_mode
    return gross_amount(_dec(unit_price) * _dec(qty), mode)


def parse_vat_mode(payload, current=None):
    """API 입력의 vatMode 를 검증한다. 값이 없으면 현재 값(없으면 기본 '별도')을 유지."""
    raw = payload.get('vatMode', payload.get('vat_mode')) if hasattr(payload, 'get') else None
    if raw is None or raw == '':
        return normalize_vat_mode(current)
    mode = str(raw).strip()
    if mode not in VAT_MODES:
        raise ValueError('부가세 방식은 별도·포함·없음 중에서 선택하세요.')
    return mode


def recalculate_schedule_amounts(schedule):
    """일정의 부가세 모드가 바뀌었을 때 그 일정에 딸린 금액을 다시 계산한다.

    납품/견적 품목의 총액(total_price)과 견적 합계는 저장 시점에 부가세 모드를 반영해
    계산되므로, 모드를 바꾸면 다시 저장해야 매출·서류 숫자가 새 규칙을 따른다.
    """
    from reporting.models import DeliveryItem, Quote

    items = DeliveryItem.objects.filter(schedule=schedule) | DeliveryItem.objects.filter(history__schedule=schedule)
    count = 0
    for item in items.distinct():
        item.save()
        count += 1
    for quote in Quote.objects.filter(schedule=schedule):
        quote.save()
    return count
