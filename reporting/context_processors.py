"""
Context processors for the reporting app.
"""
import logging

logger = logging.getLogger(__name__)

def manager_filter_context(request):
    """
    매니저가 모든 페이지에서 실무자 필터를 사용할 수 있도록 컨텍스트 제공
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            
            logger.info(f"User: {request.user.username}, Role: {user_profile.role}, Company: {user_profile.company}")
            
            # 매니저인 경우에만 실무자 목록 제공
            if user_profile.role == 'manager':
                from django.contrib.auth.models import User
                from reporting.models import UserProfile
                
                # URL 파라미터로 사용자 선택 시 세션에 저장
                user_filter = request.GET.get('user')
                if user_filter:
                    request.session['manager_selected_user'] = user_filter
                
                # 같은 회사의 실무자(salesman) 목록
                if user_profile.company:
                    accessible_salesmen = User.objects.filter(
                        userprofile__company=user_profile.company,
                        userprofile__role='salesman'
                    ).select_related('userprofile').order_by('username')
                    
                    logger.info(f"Accessible salesmen count: {accessible_salesmen.count()}")
                    for salesman in accessible_salesmen:
                        logger.info(f"  - {salesman.username}")
                else:
                    # 회사가 없는 경우 빈 쿼리셋
                    accessible_salesmen = User.objects.none()
                    logger.warning(f"Manager {request.user.username} has no company!")
                
                context['accessible_salesmen'] = accessible_salesmen
                
                # 세션에 저장된 선택 사용자가 있으면 컨텍스트에 추가
                if 'manager_selected_user' in request.session:
                    context['manager_selected_user_id'] = request.session['manager_selected_user']
        except Exception as e:
            logger.error(f"Error in manager_filter_context: {e}")
            pass
    
    return context
