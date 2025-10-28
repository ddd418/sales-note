import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking

print("OpportunityTracking 데이터 삭제 중...\n")

count = OpportunityTracking.objects.count()
OpportunityTracking.objects.all().delete()

print(f"총 {count}개의 OpportunityTracking 데이터가 삭제되었습니다.")
