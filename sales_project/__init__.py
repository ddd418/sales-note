"""
Django 프로젝트 초기화
Celery 앱을 자동으로 로드하여 Django 시작 시 사용 가능하도록 함
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
