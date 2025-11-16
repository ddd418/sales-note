"""
견적 스케줄 상태 수정 스크립트

납품과 연결되지 않은 견적 스케줄 중 '완료'로 되어있는 것을 '예정'으로 변경합니다.
견적은 납품으로 전환되어야 하며, 단독으로 완료될 수 없습니다.
"""
import os
import sys
import django

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.db import transaction
from reporting.models import Schedule, History
from datetime import datetime


def fix_quote_schedules():
    """납품과 연결되지 않은 완료된 견적 스케줄을 예정으로 변경"""
    
    print("=" * 80)
    print("견적 스케줄 상태 수정 시작")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 문제가 있는 견적 스케줄 조회
    print("[1단계] 수정 대상 견적 스케줄 조회...")
    
    problematic_quotes = Schedule.objects.filter(
        activity_type='quote',
        status='completed'
    ).select_related('followup', 'user', 'opportunity')
    
    total_count = problematic_quotes.count()
    print(f"   → 완료 상태의 견적 스케줄: {total_count}개")
    
    if total_count == 0:
        print("\n✅ 수정이 필요한 견적 스케줄이 없습니다.")
        return
    
    # 2. 각 견적이 납품으로 전환되었는지 확인
    print("\n[2단계] 납품 전환 여부 확인...")
    
    needs_fix = []
    already_converted = []
    
    for quote_schedule in problematic_quotes:
        # 같은 팔로우업의 납품 스케줄이 있는지 확인
        has_delivery = Schedule.objects.filter(
            followup=quote_schedule.followup,
            activity_type='delivery',
            visit_date__gte=quote_schedule.visit_date  # 견적 이후의 납품
        ).exists()
        
        # 같은 팔로우업의 납품 히스토리가 있는지 확인
        has_delivery_history = History.objects.filter(
            followup=quote_schedule.followup,
            action_type='delivery_schedule',
            created_at__gte=quote_schedule.created_at
        ).exists()
        
        if has_delivery or has_delivery_history:
            already_converted.append(quote_schedule)
        else:
            needs_fix.append(quote_schedule)
    
    print(f"   → 납품으로 전환된 견적: {len(already_converted)}개 (수정 불필요)")
    print(f"   → 납품 없이 완료된 견적: {len(needs_fix)}개 (수정 필요)")
    
    if len(needs_fix) == 0:
        print("\n✅ 모든 완료된 견적이 납품과 연결되어 있습니다.")
        return
    
    # 3. 상세 정보 출력
    print("\n[3단계] 수정 대상 상세 정보")
    print("-" * 80)
    print(f"{'ID':<6} {'고객명':<20} {'회사명':<20} {'일정일':<12} {'담당자':<10}")
    print("-" * 80)
    
    for schedule in needs_fix[:10]:  # 처음 10개만 출력
        customer = schedule.followup.customer_name or '미정'
        company = schedule.followup.company.name if schedule.followup.company else '미정'
        visit_date = schedule.visit_date.strftime('%Y-%m-%d')
        user = schedule.user.username
        
        print(f"{schedule.id:<6} {customer:<20} {company:<20} {visit_date:<12} {user:<10}")
    
    if len(needs_fix) > 10:
        print(f"... 외 {len(needs_fix) - 10}개 더")
    print("-" * 80)
    
    # 4. 사용자 확인
    print(f"\n⚠️  총 {len(needs_fix)}개의 견적 스케줄을 '완료' → '예정'으로 변경합니다.")
    
    # 환경 변수로 자동 실행 여부 확인 (Railway 배포 시)
    auto_confirm = os.environ.get('AUTO_CONFIRM_FIX', 'false').lower() == 'true'
    
    if not auto_confirm:
        response = input("계속하시겠습니까? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n❌ 작업이 취소되었습니다.")
            return
    else:
        print("   (자동 확인 모드: AUTO_CONFIRM_FIX=true)")
    
    # 5. 상태 변경 실행
    print("\n[4단계] 상태 변경 실행...")
    
    fixed_count = 0
    error_count = 0
    
    with transaction.atomic():
        for schedule in needs_fix:
            try:
                old_status = schedule.status
                schedule.status = 'scheduled'
                schedule.save()
                
                fixed_count += 1
                
                # 진행 상황 출력 (10개마다)
                if fixed_count % 10 == 0:
                    print(f"   → 진행: {fixed_count}/{len(needs_fix)}")
                
            except Exception as e:
                error_count += 1
                print(f"   ❌ 오류 (ID: {schedule.id}): {str(e)}")
    
    # 6. 결과 출력
    print("\n" + "=" * 80)
    print("작업 완료!")
    print("=" * 80)
    print(f"✅ 성공: {fixed_count}개")
    if error_count > 0:
        print(f"❌ 실패: {error_count}개")
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 7. 검증
    print("\n[검증] 수정 후 상태 확인...")
    remaining = Schedule.objects.filter(
        activity_type='quote',
        status='completed'
    ).count()
    print(f"   → 남은 완료 상태 견적: {remaining}개")
    
    if remaining == 0:
        print("\n🎉 모든 견적 스케줄이 올바르게 수정되었습니다!")
    elif remaining < total_count:
        print(f"\n✅ {total_count - remaining}개 수정 완료, {remaining}개는 납품과 연결된 견적입니다.")


if __name__ == '__main__':
    try:
        fix_quote_schedules()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
