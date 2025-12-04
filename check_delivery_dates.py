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

print('=== Schedule ID:415 상세 ===')
s415 = Schedule.objects.filter(id=415).first()
if s415:
    print(f'Schedule ID: 415')
    print(f'  날짜: {s415.visit_date}')
    print(f'  고객: {s415.followup.customer_name if s415.followup else "없음"} (followup_id: {s415.followup_id})')
    print(f'  담당자: {s415.user.username}')
    items = s415.delivery_items_set.all()
    print(f'  DeliveryItem 합계: {sum(i.total_price or 0 for i in items):,}원')
    for item in items:
        print(f'    - {item.item_name}: {item.total_price:,}원')
    
    # 연결된 History
    h386 = History.objects.filter(id=386).first()
    if h386:
        print(f'  연결된 History ID:386')
        followup_name = h386.followup.customer_name if h386.followup else "없음"
        print(f'    followup: {followup_name} (followup_id: {h386.followup_id})')
        print(f'    delivery_amount: {h386.delivery_amount or 0:,}원')

print()
print('=== History ID:453 상세 ===')
h453 = History.objects.filter(id=453).first()
if h453:
    print(f'History ID: 453')
    followup_name = h453.followup.customer_name if h453.followup else "없음"
    print(f'  followup: {followup_name} (followup_id: {h453.followup_id})')
    print(f'  담당자: {h453.user.username}')
    print(f'  schedule_id: {h453.schedule_id}')
    print(f'  delivery_amount: {h453.delivery_amount or 0:,}원')
    print(f'  created_at: {h453.created_at}')
    print(f'  content: {h453.content[:100] if h453.content else "없음"}...')
