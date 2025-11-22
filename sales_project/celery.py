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

# 주기적 작업 스케줄 (현재 비활성화)
# app.conf.beat_schedule = {
#     'sync-gmail-every-10-minutes': {
#         'task': 'reporting.tasks.auto_sync_gmail',
#         'schedule': crontab(minute='*/10'),  # 10분마다 실행
#     },
# }

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
