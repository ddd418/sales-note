"""
제품 재연결 스크립트

1단계: 기존 제품 모두 삭제 (DeliveryItem의 product는 NULL로 변경)
2단계: 새 제품 등록 (수동 또는 일괄 등록)
3단계: 이 스크립트 실행 - item_name과 유사한 product_code로 자동 재연결

주의:
- 기존 납품/견적의 가격(unit_price, total_price)은 절대 변경하지 않습니다
- item_name으로만 매칭하여 product 필드만 연결합니다
"""

import os
import django
from difflib import SequenceMatcher

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Product, DeliveryItem

def similarity(a, b):
    """두 문자열의 유사도 계산 (0.0 ~ 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def reconnect_products(similarity_threshold=0.8):
    """
    DeliveryItem의 product가 NULL인 항목들을 
    item_name과 유사한 product_code를 가진 Product와 재연결
    
    Args:
        similarity_threshold: 유사도 임계값 (0.0 ~ 1.0, 기본값 0.8)
    """
    
    # product가 NULL인 DeliveryItem 조회
    unlinked_items = DeliveryItem.objects.filter(product__isnull=True)
    total_unlinked = unlinked_items.count()
    
    # 활성 제품 목록
    products = Product.objects.filter(is_active=True)
    total_products = products.count()
    
    print(f"연결되지 않은 납품 품목: {total_unlinked}개")
    print(f"활성 제품: {total_products}개")
    print(f"유사도 임계값: {similarity_threshold}")
    print()
    
    if total_unlinked == 0:
        print("재연결할 항목이 없습니다.")
        return
    
    if total_products == 0:
        print("활성 제품이 없습니다. 먼저 제품을 등록해주세요.")
        return
    
    # 제품 코드 캐시 (성능 향상)
    product_dict = {p.product_code: p for p in products}
    
    matched_count = 0
    unmatched_items = []
    matches = []
    
    print("매칭 중...")
    for item in unlinked_items:
        best_match = None
        best_score = 0
        
        for product_code, product in product_dict.items():
            score = similarity(item.item_name, product_code)
            
            if score > best_score:
                best_score = score
                best_match = product
        
        if best_score >= similarity_threshold:
            matches.append({
                'item': item,
                'product': best_match,
                'score': best_score,
                'item_name': item.item_name,
                'product_code': best_match.product_code,
                'unit_price': item.unit_price  # 기존 가격 (변경하지 않음)
            })
            matched_count += 1
        else:
            unmatched_items.append({
                'item_name': item.item_name,
                'best_match': best_match.product_code if best_match else 'N/A',
                'best_score': best_score
            })
    
    # 매칭 결과 미리보기
    print(f"\n✓ 매칭된 항목: {matched_count}개")
    print(f"✗ 매칭 실패: {len(unmatched_items)}개")
    print()
    
    if matched_count > 0:
        print("매칭 미리보기 (상위 10개):")
        print("-" * 80)
        for i, match in enumerate(matches[:10], 1):
            print(f"{i}. {match['item_name']:30} → {match['product_code']:30} (유사도: {match['score']:.2%})")
            print(f"   기존 가격: {match['unit_price']:,}원 (유지됨)")
        print("-" * 80)
        print()
    
    if len(unmatched_items) > 0:
        print(f"매칭 실패 항목 (상위 10개):")
        print("-" * 80)
        for i, item in enumerate(unmatched_items[:10], 1):
            print(f"{i}. {item['item_name']:30} (최고 유사도: {item['best_score']:.2%} - {item['best_match']})")
        print("-" * 80)
        print()
    
    if matched_count == 0:
        print("매칭된 항목이 없습니다. 유사도 임계값을 낮춰보세요.")
        return
    
    # 확인
    confirm = input(f"\n{matched_count}개 항목을 재연결하시겠습니까? (yes/no): ")
    
    if confirm.lower() == 'yes':
        print("\n재연결 중...")
        
        for match in matches:
            item = match['item']
            # product 필드만 업데이트, 가격은 절대 변경하지 않음
            item.product = match['product']
            item.save(update_fields=['product'])  # product 필드만 업데이트
        
        print(f"\n✓ {matched_count}개 항목이 재연결되었습니다.")
        
        # 최종 확인
        remaining = DeliveryItem.objects.filter(product__isnull=True).count()
        linked = DeliveryItem.objects.filter(product__isnull=False).count()
        
        print(f"✓ 연결된 항목: {linked}개")
        print(f"✓ 미연결 항목: {remaining}개")
        print()
        print("참고:")
        print("- 기존 납품/견적의 가격은 변경되지 않았습니다.")
        print("- product 필드만 재연결되었습니다.")
    else:
        print("취소되었습니다.")

def delete_all_products():
    """모든 제품 삭제 (1단계) - 특정 제품 제외 가능"""
    
    # 제외할 제품 코드 리스트
    exclude_products = ['Countess 3']
    
    # 삭제할 제품 필터링
    products_to_delete = Product.objects.exclude(product_code__in=exclude_products)
    product_count = products_to_delete.count()
    
    total_count = Product.objects.count()
    linked_items = DeliveryItem.objects.filter(product__isnull=False).count()
    
    print(f"전체 제품: {total_count}개")
    print(f"삭제할 제품: {product_count}개")
    print(f"제외할 제품: {exclude_products}")
    print(f"제품과 연결된 납품 품목: {linked_items}개")
    print()
    print("제품 삭제 시:")
    print("- DeliveryItem의 product 필드만 NULL로 변경됩니다.")
    print("- item_name, unit_price, total_price는 그대로 유지됩니다.")
    print()
    
    confirm = input(f"정말로 {product_count}개의 제품을 삭제하시겠습니까? (yes/no): ")
    
    if confirm.lower() == 'yes':
        deleted_count, _ = products_to_delete.delete()
        
        print(f"\n✓ {deleted_count}개의 제품이 삭제되었습니다.")
        print(f"✓ 제외된 제품: {', '.join(exclude_products)}")
        print()
        print("다음 단계:")
        print("1. 새 제품 일괄 등록")
        print("2. python reconnect_products.py 실행하여 재연결")
    else:
        print("취소되었습니다.")

if __name__ == '__main__':
    import sys
    
    print("=" * 80)
    print("제품 관리 스크립트")
    print("=" * 80)
    print()
    print("1. 기존 제품 모두 삭제 (DeliveryItem은 유지)")
    print("2. 제품 재연결 (item_name ↔ product_code 유사도 매칭)")
    print()
    
    choice = input("선택 (1 또는 2): ")
    
    if choice == '1':
        delete_all_products()
    elif choice == '2':
        # 유사도 임계값 설정 (선택)
        threshold_input = input("유사도 임계값 (0.0~1.0, 기본값 0.8, Enter=기본값): ")
        
        if threshold_input.strip():
            try:
                threshold = float(threshold_input)
                if 0 <= threshold <= 1:
                    reconnect_products(threshold)
                else:
                    print("유사도는 0.0~1.0 사이여야 합니다.")
            except ValueError:
                print("올바른 숫자를 입력해주세요.")
        else:
            reconnect_products()  # 기본값 0.8
    else:
        print("올바른 선택지가 아닙니다.")
