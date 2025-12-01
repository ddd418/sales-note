"""
Celery 설정
- 비동기 작업 처리
- 주기적 작업 스케줄링 (Beat)
"""
import os
from celery import Celery
from celery.schedules import crontab

# Django settings 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')

app = Celery('sales_project')

# Django settings에서 celery 설정 읽기
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django app에서 tasks 자동 검색
app.autodiscover_tasks()

# 주기적 작업 스케줄
app.conf.beat_schedule = {
    # 매일 새벽 3시에 오래된 파일 정리
    'cleanup-old-files-daily': {
        'task': 'reporting.tasks.cleanup_old_files_task',
        'schedule': crontab(hour=3, minute=0),
    },
    # 매일 새벽 4시에 Gmail 토큰 자동 갱신
    'refresh-gmail-tokens-daily': {
        'task': 'reporting.tasks.refresh_gmail_tokens',
        'schedule': crontab(hour=4, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
