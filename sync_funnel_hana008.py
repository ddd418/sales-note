"""
hana008 실무자의 펀넬 데이터 정리 스크립트

일정 유형별 펀넬 단계 매핑:
- 미팅 예정 (customer_meeting + scheduled) = lead (리드)
- 미팅 완료 (customer_meeting + completed) = contact (컨택)
- 견적 예정/완료 (quote) = quote (견적)
- 납품 예정 (delivery + scheduled) = closing (클로징)
- 납품 완료 (delivery + completed) = won (수주) → 영업기회에서 제외

실행 방법:
python manage.py shell < sync_funnel_hana008.py
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from reporting.models import Schedule, OpportunityTracking, FollowUp, FunnelStage

def sync_funnel_for_user(username):
    """특정 사용자의 펀넬 데이터 동기화"""
    
    try:
        user = User.objects.get(username=username)
        print(f"\n{'='*60}")
        print(f"사용자: {user.username} ({user.get_full_name() or user.email})")
        print(f"{'='*60}")
    except User.DoesNotExist:
        print(f"❌ 사용자 '{username}'을(를) 찾을 수 없습니다.")
        return
    
    # 해당 사용자의 모든 FollowUp 조회
    followups = FollowUp.objects.filter(user=user)
    print(f"\n📋 총 팔로우업 수: {followups.count()}")
    
    # 통계
    stats = {
        'lead': 0,
        'contact': 0,
        'quote': 0,
        'closing': 0,
        'won': 0,
        'no_schedule': 0,
        'updated': 0,
        'created': 0,
        'deleted': 0,
    }
    
    with transaction.atomic():
        for followup in followups:
            # 해당 FollowUp의 모든 일정 조회
            schedules = Schedule.objects.filter(followup=followup)
            
            if not schedules.exists():
                stats['no_schedule'] += 1
                # 일정 없으면 영업기회도 삭제
                deleted_count = OpportunityTracking.objects.filter(followup=followup).delete()[0]
                if deleted_count:
                    stats['deleted'] += deleted_count
                continue
            
            # 가장 진행도가 높은 단계 결정 (우선순위: 납품 > 견적 > 미팅)
            best_stage = determine_best_stage(schedules)
            
            new_stage = best_stage
            
            # 납품 완료 = 수주 → 영업기회에서 제외
            if new_stage == 'won':
                stats['won'] += 1
                # 기존 영업기회 삭제
                deleted_count = OpportunityTracking.objects.filter(followup=followup).delete()[0]
                if deleted_count:
                    stats['deleted'] += deleted_count
                    print(f"  🏆 {followup.customer_name or followup.company.name}: 수주 완료 → 영업기회 제외")
                continue
            
            # 중복 영업기회 정리 (1개만 남기고 삭제)
            existing_opps = OpportunityTracking.objects.filter(followup=followup)
            if existing_opps.count() > 1:
                # 첫번째 것만 남기고 나머지 삭제
                first_opp = existing_opps.first()
                deleted_count = existing_opps.exclude(id=first_opp.id).delete()[0]
                print(f"  ⚠️ {followup.customer_name or followup.company.name}: 중복 영업기회 {deleted_count}개 삭제")
                stats['deleted'] += deleted_count
            
            # 기존 영업기회가 있는지 확인
            opp = existing_opps.first()
            
            # 리드/컨택은 기존 영업기회가 있을 때만 업데이트 (새로 생성 안함)
            if opp is None and new_stage in ['lead', 'contact']:
                stats['no_schedule'] += 1  # 영업기회 없음으로 카운트
                continue
            
            # 영업기회 생성 또는 업데이트
            if opp:
                created = False
            else:
                # 견적/클로징 단계만 새로 생성
                # expected_revenue는 견적 일정에서 가져옴
                quote_schedule = schedules.filter(activity_type='quote').first()
                expected_revenue = quote_schedule.expected_revenue if quote_schedule and quote_schedule.expected_revenue else 0
                opp = OpportunityTracking.objects.create(
                    followup=followup,
                    current_stage=new_stage,
                    expected_revenue=expected_revenue,
                    probability=get_default_probability(new_stage),
                )
                created = True
            
            if created:
                stats['created'] += 1
                stats[new_stage] += 1
                print(f"  ✨ {followup.customer_name or followup.company.name}: 새 영업기회 생성 → {get_stage_display(new_stage)}")
            else:
                # 기존 단계와 다르면 업데이트
                if opp.current_stage != new_stage:
                    old_stage = opp.current_stage
                    opp.current_stage = new_stage
                    opp.probability = get_default_probability(new_stage)
                    opp.save()
                    stats['updated'] += 1
                    stats[new_stage] += 1
                    print(f"  🔄 {followup.customer_name or followup.company.name}: {get_stage_display(old_stage)} → {get_stage_display(new_stage)}")
                else:
                    stats[new_stage] += 1
    
    # 결과 출력
    print(f"\n{'='*60}")
    print("📊 동기화 결과")
    print(f"{'='*60}")
    print(f"  🆕 새로 생성: {stats['created']}건")
    print(f"  🔄 단계 변경: {stats['updated']}건")
    print(f"  🗑️  삭제 (수주완료): {stats['deleted']}건")
    print(f"  ⚠️  일정 없음: {stats['no_schedule']}건")
    print(f"\n📈 현재 펀넬 분포:")
    print(f"  🎯 리드 (Lead): {stats['lead']}건")
    print(f"  📞 컨택 (Contact): {stats['contact']}건")
    print(f"  📋 견적 (Quote): {stats['quote']}건")
    print(f"  🤝 클로징 (Closing): {stats['closing']}건")
    print(f"  🏆 수주 완료 (Won): {stats['won']}건")


def determine_best_stage(schedules):
    """
    일정들 중 가장 진행도가 높은 단계 결정
    우선순위: 납품완료(won) > 납품예정(closing) > 견적(quote) > 미팅완료(contact) > 미팅예정(lead)
    """
    # 우선순위 (높을수록 우선)
    stage_priority = {
        'won': 5,
        'closing': 4,
        'quote': 3,
        'contact': 2,
        'lead': 1,
    }
    
    best_stage = 'lead'
    best_priority = 0
    
    for schedule in schedules:
        stage = determine_stage(schedule.activity_type, schedule.status)
        priority = stage_priority.get(stage, 0)
        
        if priority > best_priority:
            best_priority = priority
            best_stage = stage
    
    return best_stage


def determine_stage(activity_type, status):
    """일정 유형과 상태에 따라 펀넬 단계 결정"""
    
    if activity_type == 'customer_meeting':
        if status == 'completed':
            return 'contact'  # 미팅 완료 = 컨택
        else:
            return 'lead'  # 미팅 예정 = 리드
    
    elif activity_type == 'quote':
        return 'quote'  # 견적 = 견적
    
    elif activity_type == 'delivery':
        if status == 'completed':
            return 'won'  # 납품 완료 = 수주
        else:
            return 'closing'  # 납품 예정 = 클로징
    
    elif activity_type == 'service':
        return 'won'  # 서비스 = 기존 고객이므로 수주 처리
    
    return 'lead'  # 기본값


def get_default_probability(stage):
    """단계별 기본 확률"""
    probabilities = {
        'lead': 10,
        'contact': 25,
        'quote': 40,
        'negotiation': 60,
        'closing': 80,
        'won': 100,
        'lost': 0,
    }
    return probabilities.get(stage, 10)


def get_stage_display(stage):
    """단계 표시명"""
    displays = {
        'lead': '🎯 리드',
        'contact': '📞 컨택',
        'quote': '📋 견적',
        'negotiation': '💬 협상',
        'closing': '🤝 클로징',
        'won': '🏆 수주',
        'lost': '❌ 실주',
    }
    return displays.get(stage, stage)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔧 펀넬 데이터 동기화 스크립트")
    print("="*60)
    
    # hana008 사용자 펀넬 동기화
    sync_funnel_for_user('hana008')
    
    print("\n✅ 완료!")
