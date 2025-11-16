"""
최적화된 인증 백엔드
UserProfile을 select_related로 미리 로드하여 N+1 쿼리 방지
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class OptimizedAuthBackend(ModelBackend):
    """
    UserProfile을 select_related로 미리 로드하는 최적화된 인증 백엔드
    로그인 시 매번 발생하는 N+1 쿼리를 방지합니다.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """인증 시 UserProfile을 함께 로드"""
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        try:
            # select_related로 UserProfile과 Company를 함께 조회
            user = User.objects.select_related(
                'userprofile',
                'userprofile__company'
            ).get(**{User.USERNAME_FIELD: username})
        except User.DoesNotExist:
            # 타이밍 공격 방지를 위해 비밀번호 해싱 수행
            User().set_password(password)
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
    
    def get_user(self, user_id):
        """세션에서 사용자를 가져올 때도 UserProfile을 함께 로드"""
        try:
            user = User.objects.select_related(
                'userprofile',
                'userprofile__company'
            ).get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None
