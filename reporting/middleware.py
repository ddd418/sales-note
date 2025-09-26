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
        """요청 처리 시 사용자의 회사 정보를 request에 추가"""
        
        # 사용자 인증 확인
            
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            try:
                # Admin 사용자는 모든 데이터에 접근 가능하도록 특별 처리
                if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin':
                    request.user_company = None  # Admin은 회사 제한 없음
                    request.user_company_name = 'Admin (전체 접근)'
                    request.is_hanagwahak = True  # Admin은 모든 기능 사용 가능
                    request.is_admin = True
                    
                # UserProfile을 통해 사용자의 회사 정보 가져오기
                elif hasattr(request.user, 'userprofile') and request.user.userprofile.company:
                    try:
                        request.user_company = request.user.userprofile.company  # UserCompany 객체
                        request.user_company_name = request.user.userprofile.company.name  # 회사명
                        request.is_admin = False
                        
                        # 하나과학인지 확인 (더욱 강화된 매칭)
                        company_name_clean = request.user_company_name.strip().replace(' ', '').lower()
                        
                        # 더 많은 variation 패턴 추가
                        hanagwahak_variations = [
                            '하나과학', 'hanagwahak', 'hana', '하나',
                            'hanagwahac', 'hana gwahak', '하나 과학',
                            'hanascience', 'hana science'
                        ]
                        
                        # 기본 매칭
                        request.is_hanagwahak = any(variation.lower() in company_name_clean for variation in hanagwahak_variations)
                        
                        # 만약 기본 매칭이 실패하면 더 정교한 매칭 시도
                        if not request.is_hanagwahak:
                            try:
                                # 유니코드 정규화
                                import unicodedata
                                normalized_name = unicodedata.normalize('NFKC', company_name_clean)
                                request.is_hanagwahak = any(variation.lower() in normalized_name for variation in hanagwahak_variations)
                                
                                # 여전히 실패하면 부분 매칭 시도
                                if not request.is_hanagwahak:
                                    # '하나'와 '과학'이 모두 포함되어 있는지 확인
                                    has_hana = any(hana in company_name_clean for hana in ['하나', 'hana'])
                                    has_science = any(science in company_name_clean for science in ['과학', 'gwahak', 'science'])
                                    request.is_hanagwahak = has_hana and has_science
                            except Exception as unicode_error:
                                logger.error(f"[MIDDLEWARE] 유니코드 처리 에러: {unicode_error}")
                                # 기본적으로 False로 설정하되, 예외적으로 하나과학 문자열이 포함되어 있으면 True
                                request.is_hanagwahak = '하나과학' in request.user_company_name or 'hanagwahak' in request.user_company_name.lower()
                        
                        # Railway 서버에서의 임시 해결책: 환경변수나 특정 조건으로 강제 인식
                        if not request.is_hanagwahak:
                            # RAILWAY_ENVIRONMENT가 설정되어 있고, 회사 ID가 특정 값이면 하나과학으로 인식
                            railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
                            if railway_env:
                                # Railway 환경에서는 회사명에 '하나' 또는 'hana'가 포함되면 하나과학으로 처리
                                if any(keyword in request.user_company_name.lower() for keyword in ['하나', 'hana']):
                                    request.is_hanagwahak = True
                            
                            # 또는 특정 회사 ID들을 하나과학으로 처리 (관리자가 수동으로 설정할 수 있는 방법)
                            hanagwahak_company_ids = os.environ.get('HANAGWAHAK_COMPANY_IDS', '').split(',')
                            if str(request.user_company.id) in hanagwahak_company_ids:
                                request.is_hanagwahak = True
                        
                    except Exception as company_error:
                        logger.error(f"[MIDDLEWARE] 회사 정보 처리 에러: {company_error}")
                        request.user_company = request.user.userprofile.company
                        request.user_company_name = str(request.user.userprofile.company.name) if request.user.userprofile.company else None
                        request.is_hanagwahak = False
                        request.is_admin = False
                        
                else:
                    request.user_company = None
                    request.user_company_name = None
                    request.is_hanagwahak = False
                    request.is_admin = False
                    
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
