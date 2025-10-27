"""
펀넬 더미 데이터 정리 스크립트
FunnelStage 7개는 유지하고, 더미 OpportunityTracking, Product, Quote, QuoteItem만 삭제
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, FunnelStage, Product, Quote, QuoteItem

def clean_funnel_dummy_data():
    print("=" * 60)
    print("펀넬 더미 데이터 정리 시작")
    print("=" * 60)
    
    # 현재 데이터 개수 확인
    print("\n[삭제 전 데이터 개수]")
    print(f"OpportunityTracking: {OpportunityTracking.objects.count()}개")
    print(f"FunnelStage: {FunnelStage.objects.count()}개 (유지)")
    print(f"Product: {Product.objects.count()}개")
    print(f"Quote: {Quote.objects.count()}개")
    print(f"QuoteItem: {QuoteItem.objects.count()}개")
    
    # FunnelStage는 유지하고 나머지만 삭제
    print("\n[데이터 삭제 중...]")
    
    # OpportunityTracking 삭제 (Schedule과 연결된 것도 모두 삭제)
    opp_count = OpportunityTracking.objects.count()
    OpportunityTracking.objects.all().delete()
    print(f"✓ OpportunityTracking {opp_count}개 삭제 완료")
    
    # QuoteItem 먼저 삭제 (외래키 관계)
    quote_item_count = QuoteItem.objects.count()
    QuoteItem.objects.all().delete()
    print(f"✓ QuoteItem {quote_item_count}개 삭제 완료")
    
    # Quote 삭제
    quote_count = Quote.objects.count()
    Quote.objects.all().delete()
    print(f"✓ Quote {quote_count}개 삭제 완료")
    
    # Product 삭제
    product_count = Product.objects.count()
    Product.objects.all().delete()
    print(f"✓ Product {product_count}개 삭제 완료")
    
    # 삭제 후 데이터 개수 확인
    print("\n[삭제 후 데이터 개수]")
    print(f"OpportunityTracking: {OpportunityTracking.objects.count()}개")
    print(f"FunnelStage: {FunnelStage.objects.count()}개 (유지됨)")
    print(f"Product: {Product.objects.count()}개")
    print(f"Quote: {Quote.objects.count()}개")
    print(f"QuoteItem: {QuoteItem.objects.count()}개")
    
    print("\n" + "=" * 60)
    print("펀넬 더미 데이터 정리 완료!")
    print("이제 실제 Schedule 데이터로 OpportunityTracking을 생성할 수 있습니다.")
    print("=" * 60)

if __name__ == '__main__':
    clean_funnel_dummy_data()
