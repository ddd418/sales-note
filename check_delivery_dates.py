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

# followup_id=156 (한은영) 데이터 분석
followup = FollowUp.objects.get(id=156)
print(f'고객: {followup.customer_name} (ID: {followup.id})')
print()

print('=== History 납품 기록 ===')
delivery_histories = History.objects.filter(followup=followup, action_type='delivery_schedule')
for h in delivery_histories:
    print(f'  History ID:{h.id} - schedule_id:{h.schedule_id} - {h.delivery_amount or 0:,}원')
history_total = delivery_histories.aggregate(total=Sum('delivery_amount'))['total'] or Decimal('0')
print(f'History 총액: {history_total:,}원')

print()
print('=== Schedule 납품 일정 ===')
schedule_deliveries = Schedule.objects.filter(followup=followup, activity_type='delivery')
schedule_total = Decimal('0')
for s in schedule_deliveries:
    items = s.delivery_items_set.all()
    item_total = sum(i.total_price or Decimal('0') for i in items)
    schedule_total += item_total
    # 연결된 History가 있는지 확인
    related_history = delivery_histories.filter(schedule=s).first()
    history_link = f'(History ID:{related_history.id})' if related_history else '(History 없음)'
    print(f'  Schedule ID:{s.id} {s.visit_date} - {item_total:,}원 {history_link}')
print(f'Schedule DeliveryItem 총액: {schedule_total:,}원')

print()
print('=== 고객 목록 페이지 방식 (중복 제거) ===')
# Schedule에 연결되지 않은 History만 합산
history_only_amount = Decimal('0')
for h in delivery_histories:
    if h.schedule_id is None:
        history_only_amount += h.delivery_amount or Decimal('0')
        print(f'  History만: ID:{h.id} - {h.delivery_amount or 0:,}원')
print(f'History만 총액: {history_only_amount:,}원')
print(f'Schedule DeliveryItem 총액: {schedule_total:,}원')
print(f'합계 (목록 방식): {history_only_amount + schedule_total:,}원')

print()
print('=== 고객 상세 페이지 방식 ===')
detail_total = Decimal('0')
processed_schedules = set()

# History 기반 처리
for h in delivery_histories:
    if h.schedule_id:
        # Schedule에 연결된 경우 - DeliveryItem 금액 사용
        schedule = Schedule.objects.filter(id=h.schedule_id).first()
        if schedule:
            items = schedule.delivery_items_set.all()
            if items.exists():
                item_total = sum(i.total_price or Decimal('0') for i in items)
                detail_total += item_total
                processed_schedules.add(h.schedule_id)
                print(f'  History→Schedule: Schedule ID:{schedule.id} - {item_total:,}원')
            else:
                # DeliveryItem 없으면 History 금액 사용
                detail_total += h.delivery_amount or Decimal('0')
                print(f'  History (items 없음): ID:{h.id} - {h.delivery_amount or 0:,}원')
    else:
        # Schedule에 연결 안된 경우 - History 금액 사용
        detail_total += h.delivery_amount or Decimal('0')
        print(f'  History만: ID:{h.id} - {h.delivery_amount or 0:,}원')

# History에 연결 안된 Schedule 처리
for s in schedule_deliveries:
    if s.id not in processed_schedules:
        items = s.delivery_items_set.all()
        item_total = sum(i.total_price or Decimal('0') for i in items)
        detail_total += item_total
        print(f'  Schedule만: ID:{s.id} - {item_total:,}원')

print(f'합계 (상세 방식): {detail_total:,}원')
