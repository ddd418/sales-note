from django import template

register = template.Library()

@register.filter
def currency_format(value):
    """숫자를 원화 형식(천단위 쉼표)으로 포맷팅"""
    if value is None:
        return "0"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "0"

@register.filter
def priority_badge_class(priority):
    """우선순위에 따른 배지 CSS 클래스 반환"""
    if priority == 'high':
        return 'danger'
    elif priority == 'medium':
        return 'warning'
    else:
        return 'secondary'

@register.filter
def status_badge_class(status):
    """상태에 따른 배지 CSS 클래스 반환"""
    if status == 'active':
        return 'success'
    elif status == 'completed':
        return 'primary'
    else:
        return 'secondary'

@register.filter
def sum_total_price(delivery_items):
    """납품 품목들의 총 금액 계산"""
    if not delivery_items:
        return 0
    
    total = 0
    for item in delivery_items:
        if hasattr(item, 'total_price') and item.total_price:
            total += item.total_price
        elif hasattr(item, 'unit_price') and item.unit_price and hasattr(item, 'quantity'):
            total += (item.unit_price * item.quantity)
    
    return total
