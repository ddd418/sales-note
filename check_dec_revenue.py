import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
import django
django.setup()
from reporting.models import Schedule, DeliveryItem
from django.db.models import Sum
from decimal import Decimal

user_id = 3  # dkswogus95

print('=== 2025년 12월 납품 일정 ===')
# 12월 납품 일정
dec_schedules = Schedule.objects.filter(
    user_id=user_id,
    activity_type='delivery',
    visit_date__year=2025,
    visit_date__month=12
)
print(f'전체 12월 납품 일정 수: {dec_schedules.count()}')

# 상태별
for status in ['scheduled', 'completed', 'cancelled']:
    cnt = dec_schedules.filter(status=status).count()
    print(f'  {status}: {cnt}개')

# 대시보드 로직 (scheduled + completed만)
dashboard_schedules = dec_schedules.filter(status__in=['scheduled', 'completed'])
print(f'대시보드 포함 일정 (scheduled + completed): {dashboard_schedules.count()}')

# DeliveryItem 총액
for s in dashboard_schedules:
    items_total = DeliveryItem.objects.filter(schedule=s).aggregate(total=Sum('total_price'))['total'] or 0
    customer = s.followup.customer_name if s.followup else "없음"
    print(f'  Schedule {s.id} ({customer}): {items_total:,.0f}원')

dashboard_total = DeliveryItem.objects.filter(
    schedule__in=dashboard_schedules,
    schedule__use_prepayment=False
).aggregate(total=Sum('total_price'))['total'] or 0
print(f'대시보드 납품 매출 (선결제 미사용): {dashboard_total:,.0f}원')

# 선결제 포함 전체
dashboard_all = DeliveryItem.objects.filter(
    schedule__in=dashboard_schedules
).aggregate(total=Sum('total_price'))['total'] or 0
print(f'대시보드 납품 매출 (전체): {dashboard_all:,.0f}원')

# 선결제 사용 금액
from reporting.models import PrepaymentUsage
prepay = PrepaymentUsage.objects.filter(
    prepayment__created_by_id=user_id,
    used_at__year=2025,
    used_at__month=12
).aggregate(total=Sum('amount'))['total'] or 0
print(f'선결제 사용 금액: {prepay:,.0f}원')
print(f'총 이번달 매출 (대시보드): {dashboard_all + prepay:,.0f}원')
