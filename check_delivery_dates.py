import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')
django.setup()

from reporting.models import Schedule, DeliveryItem, History
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

# dkswogus95 사용자 조회
user = User.objects.get(username='dkswogus95')
print(f'사용자: {user.username} ({user.get_full_name()})')
print()

# History의 납품 기록 확인
print('=== History 납품 기록 (delivery_schedule) ===')
delivery_histories = History.objects.filter(user=user, action_type='delivery_schedule')
history_total = Decimal('0')
for h in delivery_histories[:20]:
    amount = h.delivery_amount or Decimal('0')
    history_total += amount
    print(f'  ID:{h.id} {h.created_at.date()} - {h.followup.customer_name} - {amount:,}원 (schedule_id:{h.schedule_id})')

print(f'History 납품 총 건수: {delivery_histories.count()}')
history_sum = delivery_histories.aggregate(total=Sum('delivery_amount'))
print(f"History 납품 총액: {history_sum['total']:,}원" if history_sum['total'] else 'History 납품 총액: 0원')

print()
print('=== DeliveryItem 기반 매출 (대시보드 방식) ===')
total_2025 = DeliveryItem.objects.filter(
    schedule__user=user,
    schedule__visit_date__year=2025,
    schedule__activity_type='delivery'
).exclude(schedule__status='cancelled').aggregate(total=Sum('total_price'))
print(f"2025년 DeliveryItem 총 매출: {total_2025['total']:,}원" if total_2025['total'] else '2025년 DeliveryItem 총 매출: 0원')

print()
print('=== 고객 리포트 방식 (History + DeliveryItem) ===')
# History에서 schedule 연결 안된 것
history_without_schedule = History.objects.filter(
    user=user, 
    action_type='delivery_schedule',
    schedule__isnull=True
).aggregate(total=Sum('delivery_amount'))
print(f"History (schedule 미연결): {history_without_schedule['total']:,}원" if history_without_schedule['total'] else 'History (schedule 미연결): 0원')

# DeliveryItem 총액
print(f"DeliveryItem 총액: {total_2025['total']:,}원" if total_2025['total'] else 'DeliveryItem 총액: 0원')

# 합계
h_amt = history_without_schedule['total'] or Decimal('0')
d_amt = total_2025['total'] or Decimal('0')
print(f"합계: {h_amt + d_amt:,}원")
