"""
기존 DeliveryItem 데이터를 Product 모델로 마이그레이션하는 스크립트

사용법:
1. 서버에서 마이그레이션 먼저 실행: python manage.py migrate
2. 이 스크립트 실행: python migrate_delivery_items_to_products.py
"""

import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import DeliveryItem, Product
from decimal import Decimal
from collections import defaultdict

def migrate_delivery_items_to_products():
    """기존 DeliveryItem을 분석하여 Product 생성 및 연결"""
    
    print("=" * 80)
    print("DeliveryItem → Product 마이그레이션 시작")
    print("=" * 80)
    
    # 1. product가 None인 모든 DeliveryItem 조회
    items_without_product = DeliveryItem.objects.filter(product__isnull=True)
    total_count = items_without_product.count()
    
    print(f"\n📦 Product와 연결되지 않은 DeliveryItem: {total_count}개")
    
    if total_count == 0:
        print("✅ 모든 DeliveryItem이 이미 Product와 연결되어 있습니다.")
        return
    
    # 2. item_name별로 그룹화하여 제품 정보 수집
    product_data = defaultdict(lambda: {
        'prices': [],
        'items': [],
        'total_quantity': 0
    })
    
    for item in items_without_product:
        item_name = item.item_name.strip()
        if not item_name:
            continue
            
        product_data[item_name]['items'].append(item)
        product_data[item_name]['total_quantity'] += item.quantity or 0
        
        if item.unit_price:
            product_data[item_name]['prices'].append(float(item.unit_price))
    
    print(f"\n📊 발견된 고유 제품명: {len(product_data)}개\n")
    
    # 3. 각 제품명에 대해 Product 생성 또는 조회
    created_products = 0
    updated_items = 0
    
    for product_code, data in sorted(product_data.items()):
        items = data['items']
        prices = data['prices']
        total_qty = data['total_quantity']
        
        # 평균 가격 계산 (부가세 제외된 가격)
        avg_price = int(sum(prices) / len(prices)) if prices else 0
        
        print(f"처리 중: {product_code}")
        print(f"  - 품목 수: {len(items)}개")
        print(f"  - 총 수량: {total_qty}개")
        print(f"  - 평균 단가: {avg_price:,}원")
        
        # Product 생성 또는 조회
        product, created = Product.objects.get_or_create(
            product_code=product_code,
            defaults={
                'description': f'{product_code}',  # 기본 설명은 품번과 동일
                'standard_price': Decimal(str(avg_price)),
                'is_active': True,
            }
        )
        
        if created:
            created_products += 1
            print(f"  ✅ 새 제품 생성: {product.product_code}")
        else:
            print(f"  ℹ️  기존 제품 사용: {product.product_code}")
        
        # DeliveryItem과 Product 연결
        for item in items:
            item.product = product
            item.save()
            updated_items += 1
        
        print()
    
    print("=" * 80)
    print("마이그레이션 완료!")
    print("=" * 80)
    print(f"✅ 생성된 제품: {created_products}개")
    print(f"✅ 업데이트된 품목: {updated_items}개")
    print()
    
    # 4. 검증
    remaining = DeliveryItem.objects.filter(product__isnull=True).count()
    print(f"🔍 검증: Product 없는 DeliveryItem 남은 개수: {remaining}개")
    
    if remaining == 0:
        print("🎉 모든 DeliveryItem이 성공적으로 Product와 연결되었습니다!")
    else:
        print(f"⚠️  주의: {remaining}개의 DeliveryItem이 여전히 Product와 연결되지 않았습니다.")
        print("    (item_name이 비어있는 항목일 수 있습니다)")

if __name__ == '__main__':
    try:
        migrate_delivery_items_to_products()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
