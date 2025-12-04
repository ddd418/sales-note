import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')
django.setup()

from reporting.models import Schedule, DeliveryItem, History, FollowUp
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

# dkswogus95 사용자 조회
user = User.objects.get(username='dkswogus95')
print(f'사용자: {user.username} ({user.get_full_name()})')
print()

print('=== 대시보드 방식 (현재) ===')
# DeliveryItem 기반 (2025년)
schedule_amount = DeliveryItem.objects.filter(
    schedule__user=user,
    schedule__visit_date__year=2025,
    schedule__activity_type='delivery'
).exclude(schedule__status='cancelled').aggregate(total=Sum('total_price'))['total'] or Decimal('0')
print(f'DeliveryItem 총액: {schedule_amount:,}원')

# History에서 schedule 미연결만 (2025년)
history_amount = History.objects.filter(
    user=user,
    action_type='delivery_schedule',
    schedule__isnull=True,
    created_at__year=2025
).aggregate(total=Sum('delivery_amount'))['total'] or Decimal('0')
print(f'History (schedule 미연결): {history_amount:,}원')
print(f'대시보드 합계: {schedule_amount + history_amount:,}원')

print()
print('=== 고객 리포트 방식 (새로 수정한 로직) ===')
# 모든 고객의 납품 금액 합산 (고객 리포트와 동일한 로직)
total_report_amount = Decimal('0')

# dkswogus95의 고객들
followups = FollowUp.objects.filter(user=user)
for followup in followups:
    delivery_histories = History.objects.filter(followup=followup, user=user, action_type='delivery_schedule')
    schedule_deliveries = Schedule.objects.filter(followup=followup, user=user, activity_type='delivery')
    
    # Schedule ID별 DeliveryItem 금액 맵 생성
    schedule_item_amounts = {}
    for schedule in schedule_deliveries:
        items = list(schedule.delivery_items_set.all())
        schedule_item_amounts[schedule.id] = sum(item.total_price or Decimal('0') for item in items)
    
    # History 처리된 Schedule ID 추적
    processed_schedule_ids = set()
    
    customer_amount = Decimal('0')
    for h in delivery_histories:
        if h.schedule_id is None:
            customer_amount += h.delivery_amount or Decimal('0')
        else:
            processed_schedule_ids.add(h.schedule_id)
            schedule_item_amount = schedule_item_amounts.get(h.schedule_id, Decimal('0'))
            if schedule_item_amount > 0:
                customer_amount += schedule_item_amount
            else:
                customer_amount += h.delivery_amount or Decimal('0')
    
    for schedule in schedule_deliveries:
        if schedule.id not in processed_schedule_ids:
            customer_amount += schedule_item_amounts.get(schedule.id, Decimal('0'))
    
    if customer_amount > 0:
        total_report_amount += customer_amount

print(f'고객 리포트 합계: {total_report_amount:,}원')

print()
print('=== 차이 분석 ===')
print(f'대시보드: {schedule_amount + history_amount:,}원')
print(f'고객리포트: {total_report_amount:,}원')
print(f'차이: {(schedule_amount + history_amount) - total_report_amount:,}원')

print()
print('=== Schedule에 연결됐지만 DeliveryItem 없는 History 확인 ===')
histories_with_schedule = History.objects.filter(
    user=user,
    action_type='delivery_schedule',
    schedule__isnull=False
)
for h in histories_with_schedule:
    schedule = h.schedule
    items = schedule.delivery_items_set.all() if schedule else []
    item_total = sum(i.total_price or Decimal('0') for i in items)
    if item_total == 0 and h.delivery_amount and h.delivery_amount > 0:
        print(f'  History ID:{h.id} (Schedule ID:{h.schedule_id}) - History금액:{h.delivery_amount:,}원, DeliveryItem:0원')
