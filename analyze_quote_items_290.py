#!/usr/bin/env python
"""
FollowUp 290 (최승현) 견적 품목 누락 원인 분석 스크립트

문제: 견적이 나갔는데 납품하려 할 때 견적 품목이 없다고 표시됨
원인 분석: Schedule, DeliveryItem, History 관계 확인
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import FollowUp, Schedule, DeliveryItem, History

def analyze_followup_290():
    """FollowUp 290의 견적 품목 상태 분석"""
    
    print("="*80)
    print("  FollowUp 290 (최승현) 견적 품목 누락 원인 분석")
    print("="*80)
    
    try:
        # 1. FollowUp 조회
        followup = FollowUp.objects.get(id=290)
        print(f"\n[1] FollowUp 정보")
        print(f"  - ID: {followup.id}")
        print(f"  - 고객명: {followup.customer_name}")
        print(f"  - 업체: {followup.company.name if followup.company else '없음'}")
        print(f"  - 담당자: {followup.user.username}")
        
        # 2. 전체 Schedule 조회
        print(f"\n[2] Schedule 조회")
        all_schedules = Schedule.objects.filter(followup=followup).order_by('visit_date')
        print(f"  - 전체 일정: {all_schedules.count()}개\n")
        
        for schedule in all_schedules:
            print(f"  Schedule ID: {schedule.id}")
            print(f"    - 타입: {schedule.activity_type} ({schedule.get_activity_type_display()})")
            print(f"    - 날짜: {schedule.visit_date} {schedule.visit_time}")
            print(f"    - 상태: {schedule.status} ({schedule.get_status_display()})")
            print(f"    - 메모: {schedule.notes or '없음'}")
            
            # 각 Schedule의 DeliveryItem 확인
            items = DeliveryItem.objects.filter(schedule=schedule)
            print(f"    - DeliveryItem 개수: {items.count()}개")
            
            if items.exists():
                print(f"    - DeliveryItem 상세:")
                for item in items:
                    print(f"      * {item.item_name}: {item.quantity}개 x {item.unit_price:,}원 = {item.total_price:,}원")
            print()
        
        # 3. 견적(quote) 일정 상세 분석
        print(f"\n[3] 견적(quote) 일정 상세 분석")
        quote_schedules = all_schedules.filter(activity_type='quote')
        print(f"  - 견적 일정 개수: {quote_schedules.count()}개\n")
        
        if not quote_schedules.exists():
            print(f"  ❌ 견적 일정이 없습니다!")
            print(f"     → 견적이 나갔다면 activity_type이 'quote'가 아닐 수 있습니다.")
        else:
            for quote in quote_schedules:
                print(f"  견적 Schedule ID: {quote.id}")
                print(f"    - 날짜: {quote.visit_date} {quote.visit_time}")
                print(f"    - 상태: {quote.status}")
                
                # 견적 품목 확인
                quote_items = DeliveryItem.objects.filter(schedule=quote)
                print(f"    - 견적 품목(DeliveryItem): {quote_items.count()}개")
                
                if quote_items.exists():
                    total = sum(item.total_price or 0 for item in quote_items)
                    print(f"    - 총 견적 금액: {total:,}원")
                    print(f"    - 품목 상세:")
                    for item in quote_items:
                        print(f"      * ID {item.id}: {item.item_name}")
                        print(f"        수량: {item.quantity}, 단가: {item.unit_price:,}원")
                        print(f"        합계: {item.total_price:,}원")
                else:
                    print(f"    ❌ 견적 품목이 없습니다!")
                print()
        
        # 4. History 확인 (견적 관련 활동 기록)
        print(f"\n[4] History 확인 (견적 관련 활동)")
        histories = History.objects.filter(
            followup=followup
        ).order_by('-created_at')
        
        print(f"  - 전체 History: {histories.count()}개\n")
        
        quote_histories = histories.filter(action_type='quote')
        print(f"  - 견적(quote) History: {quote_histories.count()}개")
        
        if quote_histories.exists():
            for history in quote_histories:
                print(f"\n  History ID: {history.id}")
                print(f"    - 타입: {history.action_type} ({history.get_action_type_display()})")
                print(f"    - 생성일: {history.created_at}")
                print(f"    - 내용: {history.content or '없음'}")
                print(f"    - 관련 Schedule: {history.schedule.id if history.schedule else '없음'}")
                
                if history.schedule:
                    schedule_items = DeliveryItem.objects.filter(schedule=history.schedule)
                    print(f"    - Schedule의 DeliveryItem: {schedule_items.count()}개")
        
        # 5. 납품(delivery) 일정 확인
        print(f"\n[5] 납품(delivery) 일정 확인")
        delivery_schedules = all_schedules.filter(activity_type='delivery')
        print(f"  - 납품 일정 개수: {delivery_schedules.count()}개\n")
        
        if delivery_schedules.exists():
            for delivery in delivery_schedules:
                print(f"  납품 Schedule ID: {delivery.id}")
                print(f"    - 날짜: {delivery.visit_date} {delivery.visit_time}")
                print(f"    - 상태: {delivery.status}")
                
                delivery_items = DeliveryItem.objects.filter(schedule=delivery)
                print(f"    - 납품 품목: {delivery_items.count()}개")
                
                if delivery_items.exists():
                    for item in delivery_items:
                        print(f"      * {item.item_name}: {item.quantity}개")
                print()
        
        # 6. 문제 진단
        print(f"\n[6] 문제 진단")
        
        has_quote_schedule = quote_schedules.exists()
        has_quote_items = False
        
        if has_quote_schedule:
            for quote in quote_schedules:
                if DeliveryItem.objects.filter(schedule=quote).exists():
                    has_quote_items = True
                    break
        
        if not has_quote_schedule:
            print(f"  ❌ 견적 일정(activity_type='quote')이 없습니다!")
            print(f"     → 가능한 원인:")
            print(f"        1. 견적 일정을 다른 타입(customer_meeting 등)으로 생성")
            print(f"        2. 이전 버그로 인해 견적 타입이 변경됨")
            print(f"        3. 견적 일정이 삭제됨")
            
            # customer_meeting 타입 확인
            meeting_schedules = all_schedules.filter(activity_type='customer_meeting')
            if meeting_schedules.exists():
                print(f"\n     💡 customer_meeting 타입 일정이 {meeting_schedules.count()}개 있습니다:")
                for meeting in meeting_schedules:
                    items = DeliveryItem.objects.filter(schedule=meeting)
                    if items.exists():
                        print(f"        - Schedule ID {meeting.id}: DeliveryItem {items.count()}개 있음!")
                        print(f"          → 이 일정이 실제로는 견적일 수 있습니다.")
        
        elif not has_quote_items:
            print(f"  ❌ 견적 일정은 있지만 DeliveryItem이 없습니다!")
            print(f"     → 가능한 원인:")
            print(f"        1. 견적 품목을 등록하지 않음")
            print(f"        2. DeliveryItem이 삭제됨 (Schedule 삭제 후 재생성 등)")
            print(f"        3. 다른 Schedule에 품목이 연결되어 있음")
        else:
            print(f"  ✅ 견적 일정과 품목이 정상적으로 존재합니다.")
        
        # 7. 해결 방법 제시
        print(f"\n[7] 해결 방법")
        
        if not has_quote_schedule:
            print(f"  → customer_meeting 타입 일정을 quote로 변경")
            print(f"  → 또는 견적 일정을 새로 생성하고 품목 등록")
        elif not has_quote_items:
            print(f"  → 견적 일정에 DeliveryItem 추가")
            print(f"  → 견적 품목 등록 화면에서 품목 입력")
        
        print(f"\n{'='*80}")
        print("  분석 완료")
        print("="*80)
        
    except FollowUp.DoesNotExist:
        print(f"\n❌ FollowUp ID 290을 찾을 수 없습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    analyze_followup_290()
