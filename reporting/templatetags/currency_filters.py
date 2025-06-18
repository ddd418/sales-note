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
