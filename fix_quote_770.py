"""
견적 일정 770번을 완료 처리하는 일회성 스크립트
납품으로 전환되었으나 자동 완료 기능 추가 전이라 수동 처리 필요
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule

try:
    s = Schedule.objects.get(id=770, activity_type='quote')
    old_status = s.status
    s.status = 'completed'
    s.save()
    print(f'[OK] Schedule 770: {old_status} -> completed')
except Schedule.DoesNotExist:
    print('[SKIP] Schedule 770 not found or not a quote')
