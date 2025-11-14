from reporting.models import Schedule, DeliveryItem
from django.db.models import Sum

s = Schedule.objects.get(id=491)
items = DeliveryItem.objects.filter(schedule=s)

print('=== 납품 품목 ===')
print('품목 수:', items.count())
total = items.aggregate(Sum('total_price'))['total_price__sum'] or 0
print('총 금액:', f'{total:,}원')

for item in items:
    print(f'  - {item.product_name}: {item.quantity}개 x {item.unit_price:,}원 = {item.total_price:,}원')
