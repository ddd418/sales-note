import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class CompanyFilterMiddleware(MiddlewareMixin):
    """
    회사별 데이터 필터링 미들웨어
    로그인한 사용자의 회사에 따라 데이터를 자동으로 필터링합니다.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """요청 처리 시 사용자의 회사 정보를 request에 추가"""
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            try:
                # Admin 사용자는 모든 데이터에 접근 가능하도록 특별 처리
                if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin':
                    request.user_company = None  # Admin은 회사 제한 없음
                    request.user_company_name = 'Admin (전체 접근)'
                    request.is_hanagwahak = True  # Admin은 모든 기능 사용 가능
                    request.is_admin = True
                    logger.info(f"Admin 사용자 {request.user.username}: 전체 접근 권한 부여")
                    
                # UserProfile을 통해 사용자의 회사 정보 가져오기
                elif hasattr(request.user, 'userprofile') and request.user.userprofile.company:
                    request.user_company = request.user.userprofile.company  # UserCompany 객체
                    request.user_company_name = request.user.userprofile.company.name  # 회사명
                    request.is_admin = False
                    
                    # 하나과학인지 확인 (다양한 형태 허용)
                    company_name_clean = request.user_company_name.strip().replace(' ', '').lower()
                    hanagwahak_variations = ['하나과학', 'hanagwahak', 'hana', '하나']
                    request.is_hanagwahak = any(variation.lower() in company_name_clean for variation in hanagwahak_variations)
                    
                    # 디버깅을 위한 로깅
                    logger.info(f"사용자 {request.user.username}의 회사: '{request.user_company_name}' (clean: '{company_name_clean}') -> is_hanagwahak: {request.is_hanagwahak}")
                else:
                    request.user_company = None
                    request.user_company_name = None
                    request.is_hanagwahak = False
                    request.is_admin = False
                    logger.info(f"사용자 {request.user.username}의 회사 정보 없음")
                    
            except Exception as e:
                logger.error(f"Error getting user company info: {e}")
                request.user_company = None
                request.user_company_name = None
                request.is_hanagwahak = False
                request.is_admin = False
        else:
            request.user_company = None
            request.user_company_name = None
            request.is_hanagwahak = False
            request.is_admin = False
        
        return None

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    성능 모니터링 미들웨어
    각 요청의 처리 시간을 로깅하고, 느린 요청을 추적합니다.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """요청 시작 시간 기록"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """요청 완료 시간 계산 및 로깅"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # 느린 요청 임계값 (1초)
            slow_request_threshold = 1.0
            
            if duration > slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} "
                    f"took {duration:.2f}s (User: {getattr(request.user, 'username', 'Anonymous')})"
                )
            else:
                logger.info(
                    f"Request: {request.method} {request.path} "
                    f"took {duration:.3f}s (User: {getattr(request.user, 'username', 'Anonymous')})"
                )
            
            # 응답 헤더에 처리 시간 추가 (개발 환경에서 유용)
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    def process_exception(self, request, exception):
        """예외 발생 시 로깅"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.error(
                f"Exception in request: {request.method} {request.path} "
                f"after {duration:.3f}s - {exception} "
                f"(User: {getattr(request.user, 'username', 'Anonymous')})"
            )
        return None
