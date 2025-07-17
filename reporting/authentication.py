from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Company, UserProfile


class CompanyAuthenticationBackend(BaseBackend):
    """
    회사코드 + 사번 + 비밀번호로 로그인하는 커스텀 인증 백엔드
    """
    
    def authenticate(self, request, company_code=None, employee_id=None, password=None, **kwargs):
        """
        회사코드와 사번을 조합하여 사용자 인증
        """
        if not all([company_code, employee_id, password]):
            return None
        
        try:
            # 회사 조회
            company = Company.objects.get(company_code=company_code, is_active=True)
            
            # 해당 회사의 사용자 프로필 조회
            user_profile = UserProfile.objects.get(
                company=company,
                employee_id=employee_id
            )
            
            # 비밀번호 확인
            user = user_profile.user
            if user.check_password(password) and user.is_active:
                return user
                
        except (Company.DoesNotExist, UserProfile.DoesNotExist):
            return None
        
        return None
    
    def get_user(self, user_id):
        """
        사용자 ID로 사용자 객체 반환
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CompanyBasedPermissionMixin:
    """
    회사별 데이터 접근을 제한하는 Mixin
    """
    
    def get_company_queryset(self, queryset):
        """
        현재 사용자의 회사 데이터만 필터링
        """
        if not hasattr(self.request.user, 'userprofile'):
            return queryset.none()
        
        user_company = self.request.user.userprofile.company
        return queryset.filter(company=user_company)
    
    def get_queryset(self):
        """
        기본 queryset을 회사별로 필터링
        """
        queryset = super().get_queryset()
        return self.get_company_queryset(queryset)
    
    def form_valid(self, form):
        """
        폼 저장 시 자동으로 회사 정보 추가
        """
        if hasattr(form.instance, 'company'):
            form.instance.company = self.request.user.userprofile.company
        if hasattr(form.instance, 'user') and not form.instance.user:
            form.instance.user = self.request.user
        return super().form_valid(form)
