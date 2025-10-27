"""
펀넬 관리 시스템 초기 설정 스크립트
- FunnelStage 기본 데이터 생성
- 기존 FollowUp에 OpportunityTracking 자동 생성
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import FunnelStage, OpportunityTracking, FollowUp
from datetime import date

def create_funnel_stages():
    """펀넬 단계 기본 데이터 생성"""
    stages = [
        {
            'name': 'lead',
            'display_name': '리드',
            'stage_order': 1,
            'default_probability': 10,
            'avg_duration_days': 7,
            'color': '#94a3b8',
            'icon': 'fa-user-plus',
            'description': '잠재 고객 등록 단계',
            'success_criteria': '첫 미팅 일정 잡기'
        },
        {
            'name': 'contact',
            'display_name': '컨택',
            'stage_order': 2,
            'default_probability': 30,
            'avg_duration_days': 7,
            'color': '#60a5fa',
            'icon': 'fa-handshake',
            'description': '첫 접촉 및 미팅 단계',
            'success_criteria': '고객 니즈 파악 및 견적 요청'
        },
        {
            'name': 'quote',
            'display_name': '견적',
            'stage_order': 3,
            'default_probability': 50,
            'avg_duration_days': 10,
            'color': '#667eea',
            'icon': 'fa-file-invoice-dollar',
            'description': '견적서 발송 단계',
            'success_criteria': '고객 견적 검토 완료'
        },
        {
            'name': 'negotiation',
            'display_name': '협상',
            'stage_order': 4,
            'default_probability': 70,
            'avg_duration_days': 14,
            'color': '#f59e0b',
            'icon': 'fa-comments-dollar',
            'description': '가격 및 조건 협상 단계',
            'success_criteria': '최종 조건 합의'
        },
        {
            'name': 'closing',
            'display_name': '클로징',
            'stage_order': 5,
            'default_probability': 90,
            'avg_duration_days': 7,
            'color': '#10b981',
            'icon': 'fa-check-circle',
            'description': '계약 직전 최종 확정 단계',
            'success_criteria': '계약 체결 및 납품'
        },
        {
            'name': 'won',
            'display_name': '수주',
            'stage_order': 6,
            'default_probability': 100,
            'avg_duration_days': 0,
            'color': '#059669',
            'icon': 'fa-trophy',
            'description': '계약 성공 및 납품 완료',
            'success_criteria': '완료'
        },
        {
            'name': 'lost',
            'display_name': '실주',
            'stage_order': 7,
            'default_probability': 0,
            'avg_duration_days': 0,
            'color': '#ef4444',
            'icon': 'fa-times-circle',
            'description': '계약 실패',
            'success_criteria': '없음'
        },
    ]
    
    print("=" * 60)
    print("FunnelStage 기본 데이터 생성 중...")
    print("=" * 60)
    
    created_count = 0
    for stage_data in stages:
        stage, created = FunnelStage.objects.get_or_create(
            name=stage_data['name'],
            defaults=stage_data
        )
        if created:
            print(f"✅ {stage.display_name} 단계 생성 완료")
            created_count += 1
        else:
            print(f"ℹ️  {stage.display_name} 단계 이미 존재")
    
    print(f"\n총 {created_count}개 단계 생성 완료!\n")
    return created_count


def auto_classify_opportunities():
    """기존 FollowUp 데이터 자동 분류"""
    print("=" * 60)
    print("기존 고객 데이터 자동 분류 중...")
    print("=" * 60)
    
    followups = FollowUp.objects.all()
    total = followups.count()
    
    if total == 0:
        print("ℹ️  분류할 고객 데이터가 없습니다.\n")
        return 0
    
    created_count = 0
    updated_count = 0
    
    for idx, followup in enumerate(followups, 1):
        # 이미 OpportunityTracking이 있는지 확인
        opportunity, created = OpportunityTracking.objects.get_or_create(
            followup=followup
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
        
        # 단계 자동 분류
        stage = 'lead'  # 기본값
        
        # 납품 기록이 있으면 'won'
        if followup.histories.filter(action_type='delivery_schedule').exists():
            stage = 'won'
            delivery = followup.histories.filter(action_type='delivery_schedule').first()
            opportunity.won_date = delivery.created_at.date()
            if delivery.delivery_amount:
                opportunity.actual_revenue = delivery.delivery_amount
        
        # 견적이 있으면 'quote' 이상
        elif followup.quotes.exists():
            latest_quote = followup.quotes.order_by('-created_at').first()
            if latest_quote.stage == 'negotiation':
                stage = 'negotiation'
            elif latest_quote.stage in ['approved', 'sent', 'review']:
                stage = 'quote'
            elif latest_quote.stage in ['rejected', 'expired']:
                stage = 'lost'
                opportunity.lost_date = latest_quote.updated_at.date()
                opportunity.lost_reason = f"견적 {latest_quote.get_stage_display()}"
            
            # 견적 금액 반영
            opportunity.expected_revenue = latest_quote.total_amount
            opportunity.probability = latest_quote.probability
        
        # 일정이 3개 이상이면 'negotiation'
        elif followup.schedules.count() >= 3:
            stage = 'negotiation'
            opportunity.total_meetings = followup.schedules.filter(
                activity_type='customer_meeting'
            ).count()
        
        # 일정이 1개 이상이면 'contact'
        elif followup.schedules.exists():
            stage = 'contact'
            opportunity.total_meetings = followup.schedules.filter(
                activity_type='customer_meeting'
            ).count()
        
        # 단계 업데이트
        opportunity.current_stage = stage
        
        # 단계별 기본 확률 설정
        try:
            stage_obj = FunnelStage.objects.get(name=stage)
            if not opportunity.probability or opportunity.probability == 50:
                opportunity.probability = stage_obj.default_probability
        except FunnelStage.DoesNotExist:
            pass
        
        # 단계 이력 초기화
        if not opportunity.stage_history:
            opportunity.stage_history = [{
                'stage': stage,
                'entered': date.today().isoformat(),
                'exited': None
            }]
        
        opportunity.save()
        
        # 진행상황 출력
        stage_display = FunnelStage.objects.get(name=stage).display_name
        print(f"[{idx}/{total}] {followup.customer_name or '고객'} → {stage_display} 단계")
    
    print(f"\n✅ 총 {created_count}개 영업 기회 생성, {updated_count}개 업데이트 완료!\n")
    return created_count


def create_sample_products():
    """샘플 제품 데이터 생성"""
    from reporting.models import Product
    
    print("=" * 60)
    print("샘플 제품 데이터 생성 중...")
    print("=" * 60)
    
    products = [
        {
            'product_code': 'EQP-001',
            'name': '분석장비 A형',
            'category': 'equipment',
            'standard_price': 10000000,
            'description': '고성능 분석 장비'
        },
        {
            'product_code': 'EQP-002',
            'name': '분석장비 B형',
            'category': 'equipment',
            'standard_price': 15000000,
            'description': '프리미엄 분석 장비'
        },
        {
            'product_code': 'SW-001',
            'name': '데이터 분석 소프트웨어',
            'category': 'software',
            'standard_price': 5000000,
            'description': 'AI 기반 데이터 분석 솔루션'
        },
        {
            'product_code': 'SVC-001',
            'name': '유지보수 서비스 (1년)',
            'category': 'service',
            'standard_price': 2000000,
            'description': '연간 유지보수 서비스'
        },
        {
            'product_code': 'CSM-001',
            'name': '소모품 세트',
            'category': 'consumable',
            'standard_price': 500000,
            'description': '정기 교체 소모품'
        },
    ]
    
    created_count = 0
    for product_data in products:
        product, created = Product.objects.get_or_create(
            product_code=product_data['product_code'],
            defaults=product_data
        )
        if created:
            print(f"✅ {product.name} ({product.product_code}) 생성 완료")
            created_count += 1
        else:
            print(f"ℹ️  {product.name} 이미 존재")
    
    print(f"\n총 {created_count}개 제품 생성 완료!\n")
    return created_count


def display_summary():
    """현황 요약 출력"""
    print("=" * 60)
    print("📊 펀넬 관리 시스템 현황")
    print("=" * 60)
    
    # 단계별 통계
    print("\n[단계별 영업 기회 현황]")
    stages = FunnelStage.objects.all().order_by('stage_order')
    for stage in stages:
        count = OpportunityTracking.objects.filter(current_stage=stage.name).count()
        total_revenue = OpportunityTracking.objects.filter(
            current_stage=stage.name
        ).aggregate(
            models.Sum('expected_revenue')
        )['expected_revenue__sum'] or 0
        
        print(f"  {stage.display_name:10} : {count:3}건  (예상매출: ₩{total_revenue:,})")
    
    # 전체 통계
    total_opps = OpportunityTracking.objects.count()
    total_expected = OpportunityTracking.objects.aggregate(
        models.Sum('expected_revenue')
    )['expected_revenue__sum'] or 0
    total_weighted = OpportunityTracking.objects.aggregate(
        models.Sum('weighted_revenue')
    )['weighted_revenue__sum'] or 0
    
    print(f"\n[전체 현황]")
    print(f"  총 영업 기회: {total_opps}건")
    print(f"  예상 매출: ₩{total_expected:,}")
    print(f"  가중 매출: ₩{total_weighted:,}")
    
    # 제품 통계
    from reporting.models import Product
    product_count = Product.objects.count()
    print(f"\n[제품]")
    print(f"  등록된 제품: {product_count}개")
    
    print("\n" + "=" * 60)
    print("✅ 펀넬 관리 시스템 설정 완료!")
    print("=" * 60)


if __name__ == '__main__':
    from django.db import models
    
    print("\n" + "🚀 " * 20)
    print("펀넬 관리 시스템 초기 설정 시작")
    print("🚀 " * 20 + "\n")
    
    try:
        # 1. FunnelStage 생성
        create_funnel_stages()
        
        # 2. 샘플 제품 생성
        create_sample_products()
        
        # 3. 기존 고객 자동 분류
        auto_classify_opportunities()
        
        # 4. 현황 요약
        display_summary()
        
        print("\n🎉 모든 설정이 완료되었습니다!")
        print("\n다음 단계:")
        print("  1. Admin에서 제품 추가/수정")
        print("  2. 일정 생성 시 견적 추가")
        print("  3. /reporting/funnel/ 에서 펀넬 대시보드 확인")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
