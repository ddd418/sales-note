"""
Reporting 앱 전용 템플릿 태그
"""
from django import template
from django.contrib.auth import get_user_model
from reporting.models import UserCompany

register = template.Library()
User = get_user_model()


@register.simple_tag
def get_all_companies():
    """
    모든 회사 목록을 반환 (관리자 필터용)
    """
    return UserCompany.objects.all().order_by('name')


@register.simple_tag
def get_users_by_company(company_id):
    """
    특정 회사에 속한 사용자 목록을 반환 (관리자 필터용)
    
    Args:
        company_id: 회사 ID
        
    Returns:
        QuerySet: 해당 회사의 사용자 목록
    """
    return User.objects.filter(
        userprofile__company_id=company_id
    ).select_related('userprofile').order_by('username')
