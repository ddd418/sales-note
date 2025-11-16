import time
import logging
import os
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
        """요청 처리 시 사용자의 회사 정보를 request에 추가 (세션 캐싱 적용)"""
        
        # 사용자 인증 확인
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            # 세션 캐시 체크 (DB 조회 최소화)
            cache_key = f'user_profile_{request.user.id}'
            if cache_key in request.session:
                cached_data = request.session[cache_key]
                request.user_company = cached_data.get('company_id')
                request.user_company_name = cached_data.get('company_name')
                request.is_admin = cached_data.get('is_admin', False)
                request.is_hanagwahak = cached_data.get('is_hanagwahak', False)
                return None
            
            try:
                # select_related로 한 번에 조회 (N+1 방지)
                if hasattr(request.user, 'userprofile'):
                    profile = request.user.userprofile
                    # Admin 사용자는 모든 데이터에 접근 가능
                    if profile.role == 'admin':
                        request.user_company = None
                        request.user_company_name = 'Admin (전체 접근)'
                        request.is_hanagwahak = True
                        request.is_admin = True
                        
                        # 세션 캐시 저장
                        request.session[cache_key] = {
                            'company_id': None,
                            'company_name': 'Admin (전체 접근)',
                            'is_admin': True,
                            'is_hanagwahak': True
                        }
                    
                    # 일반 사용자 - 회사 정보 조회
                    elif profile.company:
                        company = profile.company
                        request.user_company = company
                        request.user_company_name = company.name
                        request.is_admin = False
                        
                        # 하나과학 체크 간소화 (성능 개선)
                        company_name_lower = company.name.lower().replace(' ', '')
                        request.is_hanagwahak = (
                            '하나과학' in company_name_lower or 
                            'hanagwahak' in company_name_lower or
                            (os.environ.get('HANAGWAHAK_COMPANY_IDS', '').find(str(company.id)) != -1)
                        )
                        
                        # 세션 캐시 저장
                        request.session[cache_key] = {
                            'company_id': company.id,
                            'company_name': company.name,
                            'is_admin': False,
                            'is_hanagwahak': request.is_hanagwahak
                        }
                    else:
                        # 회사 정보 없음
                        request.user_company = None
                        request.user_company_name = None
                        request.is_hanagwahak = False
                        request.is_admin = False
                        
                        request.session[cache_key] = {
                            'company_id': None,
                            'company_name': None,
                            'is_admin': False,
                            'is_hanagwahak': False
                        }
                        
                else:
                    # UserProfile 없음
                    request.user_company = None
                    request.user_company_name = None
                    request.is_hanagwahak = False
                    request.is_admin = False
                    
            except Exception as e:
                logger.error(f"[MIDDLEWARE] 사용자 프로필 조회 오류: {e}")
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
