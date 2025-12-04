import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.contrib.auth.models import User
from reporting.models import OpportunityTracking

user = User.objects.get(username='dkswogus95')
print(f'=== 사용자: {user.username} ===')
print()

print('=== 수주 현황 기준 ===')
closing_opps = OpportunityTracking.objects.filter(followup__user=user, current_stage='closing')
quote_lost_opps = OpportunityTracking.objects.filter(followup__user=user, current_stage='quote_lost')
print(f'수주(closing): {closing_opps.count()}건')
print(f'납품취소(quote_lost): {quote_lost_opps.count()}건')

print()
print('=== 단계별 현황 기준 ===')
for stage in ['lead', 'contact', 'quote', 'closing']:
    count = OpportunityTracking.objects.filter(followup__user=user, current_stage=stage).count()
    print(f'{stage}: {count}건')
