"""
Context processors for the reporting app.
"""

def manager_filter_context(request):
    """
    매니저가 모든 페이지에서 실무자 필터를 사용할 수 있도록 컨텍스트 제공
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            
            # 매니저인 경우에만 실무자 목록 제공
            if user_profile.role == 'manager' and user_profile.company:
                from django.contrib.auth.models import User
                from reporting.models import UserProfile
                
                # 같은 회사의 실무자(salesman) 목록
                accessible_salesmen = User.objects.filter(
                    userprofile__company=user_profile.company,
                    userprofile__role='salesman'
                ).select_related('userprofile').order_by('username')
                
                context['accessible_salesmen'] = accessible_salesmen
        except:
            pass
    
    return context
