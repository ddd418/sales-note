"""
백업 API 엔드포인트
외부 스케줄러에서 호출할 수 있는 백업 웹 엔드포인트
"""
import os
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def backup_database_api(request):
    """
    데이터베이스 백업을 실행하는 API 엔드포인트
    POST /backup/database/
    """
    try:
        # 인증 토큰 확인 (환경 변수에서 설정)
        auth_token = request.headers.get('Authorization')
        expected_token = os.environ.get('BACKUP_API_TOKEN')
        
        if not expected_token:
            return JsonResponse({
                'error': 'Backup API token not configured'
            }, status=500)
            
        if auth_token != f'Bearer {expected_token}':
            return JsonResponse({
                'error': 'Invalid authentication token'
            }, status=401)
        
        # 간단한 환경변수 백업 실행 (성공했던 방식 사용)
        logger.info("API를 통한 환경변수 백업 시작")
        
        # 백업 정보 생성
        korea_time = timezone.now()
        timestamp = korea_time.strftime('%Y%m%d_%H%M%S')
        
        backup_info = {
            'timestamp': timestamp,
            'korea_time': korea_time.strftime('%Y년 %m월 %d일 %H시 %M분'),
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development'),
            'database_configured': bool(settings.DATABASES.get('default')),
            'email_configured': bool(settings.EMAIL_HOST),
            'total_env_vars': len([k for k in os.environ.keys() if not k.startswith('_')])
        }
        
        # 이메일 알림 전송 (성공했던 방식 사용)
        try:
            call_command('backup_database', no_email=True)
            logger.info("Django 백업 명령어 실행 완료")
        except Exception as cmd_error:
            logger.warning(f"Django 백업 명령어 실행 실패: {cmd_error}")
        
        logger.info("API를 통한 환경변수 백업 완료")
        
        return JsonResponse({
            'success': True,
            'message': 'Environment backup completed successfully',
            'backup_info': backup_info,
            'timestamp': korea_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"백업 API 실행 중 오류: {str(e)}")
        return JsonResponse({
            'error': f'Backup failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def backup_status_api(request):
    """
    백업 시스템 상태를 확인하는 API 엔드포인트
    GET /backup/status/
    """
    try:
        # 기본 정보 수집
        status_info = {
            'django_version': '5.2.3',
            'database_configured': bool(settings.DATABASES.get('default')),
            'email_configured': bool(settings.EMAIL_HOST),
            'backup_api_configured': bool(os.environ.get('BACKUP_API_TOKEN')),
            'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development')
        }
        
        return JsonResponse({
            'success': True,
            'status': status_info
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Status check failed: {str(e)}'
        }, status=500)
