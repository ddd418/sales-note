"""
영업 보고 시스템 시그널
- 납품 완료 시 OpportunityTracking 자동 업데이트
- Schedule 삭제 시 연결된 OpportunityTracking도 삭제
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from datetime import date
from .models import History, OpportunityTracking, Schedule


@receiver(post_save, sender=History)
def update_opportunity_on_delivery(sender, instance, created, **kwargs):
    """
    납품 완료 히스토리 생성 시 관련 OpportunityTracking을 'won' 단계로 업데이트
    """
    # 납품 일정 히스토리만 처리
    if instance.action_type != 'delivery_schedule':
        return
    
    # 팔로우업이 없으면 처리 안함
    if not instance.followup:
        return
    
    # 해당 팔로우업과 연결된 OpportunityTracking 찾기
    opportunities = OpportunityTracking.objects.filter(
        followup=instance.followup
    ).exclude(current_stage='won').exclude(current_stage='lost')
    
    for opportunity in opportunities:
        # 현재 단계를 'won'으로 변경
        old_stage = opportunity.current_stage
        opportunity.current_stage = 'won'
        
        # stage_history에 새로운 단계 추가
        if opportunity.stage_history is None:
            opportunity.stage_history = []
        
        # 이전 단계 종료 처리
        if opportunity.stage_history:
            for stage_entry in opportunity.stage_history:
                if stage_entry.get('stage') == old_stage and not stage_entry.get('exited'):
                    stage_entry['exited'] = date.today().isoformat()
        
        # 새로운 'won' 단계 추가
        opportunity.stage_history.append({
            'stage': 'won',
            'entered': date.today().isoformat(),
            'exited': None
        })
        
        # 실제 매출액 업데이트 (납품 금액이 있으면)
        if instance.delivery_amount:
            opportunity.actual_revenue = instance.delivery_amount
        
        # 실제 계약일 업데이트
        if instance.delivery_date:
            opportunity.actual_close_date = instance.delivery_date
        elif instance.created_at:
            opportunity.actual_close_date = instance.created_at.date()
        
        opportunity.save()


@receiver(pre_save, sender=Schedule)
def update_opportunity_on_schedule_change(sender, instance, **kwargs):
    """
    일정의 상태나 금액이 변경될 때 OpportunityTracking 업데이트
    서비스 일정은 제외 (영업 기회와 무관)
    """
    # 서비스 일정은 영업 기회와 무관하므로 처리 안함
    if instance.activity_type == 'service':
        return
    
    # 새로 생성되는 경우는 처리 안함 (create_view에서 처리)
    if not instance.pk:
        return
    
    # 기존 일정 가져오기
    try:
        old_schedule = Schedule.objects.get(pk=instance.pk)
    except Schedule.DoesNotExist:
        return
    
    # OpportunityTracking이 연결되어 있으면 업데이트
    if instance.opportunity:
        opportunity = instance.opportunity
        
        # 예상 매출액 변경 시
        if instance.expected_revenue != old_schedule.expected_revenue:
            if instance.expected_revenue:
                opportunity.expected_revenue = instance.expected_revenue
                # 가중치 매출액도 업데이트
                probability = instance.probability or opportunity.probability or 50
                opportunity.weighted_revenue = instance.expected_revenue * probability / 100
        
        # 확률 변경 시
        if instance.probability != old_schedule.probability:
            if instance.probability is not None:
                opportunity.probability = instance.probability
                # 가중치 매출액 재계산
                if opportunity.expected_revenue:
                    opportunity.weighted_revenue = opportunity.expected_revenue * instance.probability / 100
        
        # 예상 계약일 변경 시
        if instance.expected_close_date != old_schedule.expected_close_date:
            if instance.expected_close_date:
                opportunity.expected_close_date = instance.expected_close_date
        
        # 일정 상태가 완료로 변경되고 납품 일정인 경우
        if (instance.status == 'completed' and 
            old_schedule.status != 'completed' and 
            instance.activity_type == 'delivery'):
            
            # OpportunityTracking을 'won'으로 변경
            old_stage = opportunity.current_stage
            opportunity.current_stage = 'won'
            opportunity.stage_entry_date = date.today()
            
            # stage_history 업데이트
            if opportunity.stage_history is None:
                opportunity.stage_history = []
            
            # 이전 단계 종료
            for stage_entry in opportunity.stage_history:
                if stage_entry.get('stage') == old_stage and not stage_entry.get('exited'):
                    stage_entry['exited'] = date.today().isoformat()
            
            # won 단계 추가
            opportunity.stage_history.append({
                'stage': 'won',
                'entered': date.today().isoformat(),
                'exited': None,
                'note': f'납품 완료로 자동 전환 (일정 ID: {instance.id})'
            })
        
        # 일정 상태가 예정 → 완료로 변경되고 고객 미팅인 경우
        elif (instance.status == 'completed' and 
              old_schedule.status == 'scheduled' and 
              instance.activity_type == 'customer_meeting' and
              opportunity.current_stage == 'lead'):
            
            # lead → contact 단계로 변경 (미팅 완료)
            old_stage = opportunity.current_stage
            opportunity.current_stage = 'contact'
            opportunity.stage_entry_date = date.today()
            
            # stage_history 업데이트
            if opportunity.stage_history is None:
                opportunity.stage_history = []
            
            # 이전 단계 종료
            for stage_entry in opportunity.stage_history:
                if stage_entry.get('stage') == old_stage and not stage_entry.get('exited'):
                    stage_entry['exited'] = date.today().isoformat()
            
            # contact 단계 추가
            opportunity.stage_history.append({
                'stage': 'contact',
                'entered': date.today().isoformat(),
                'exited': None,
                'note': f'고객 미팅 완료로 자동 전환 (일정 ID: {instance.id})'
            })
        
        opportunity.save()


@receiver(post_delete, sender=Schedule)
def delete_opportunity_when_schedule_deleted(sender, instance, **kwargs):
    """
    Schedule 삭제 시 연결된 OpportunityTracking도 함께 삭제
    단, 다른 Schedule이 같은 OpportunityTracking을 참조하고 있으면 삭제 안함
    """
    # 서비스 일정은 OpportunityTracking과 무관
    if instance.activity_type == 'service':
        return
    
    # OpportunityTracking이 연결되어 있지 않으면 종료
    if not instance.opportunity:
        return
    
    opportunity = instance.opportunity
    
    # 같은 OpportunityTracking을 참조하는 다른 Schedule이 있는지 확인
    other_schedules = Schedule.objects.filter(
        opportunity=opportunity
    ).exclude(pk=instance.pk).exists()
    
    # 다른 Schedule이 없으면 OpportunityTracking도 삭제
    if not other_schedules:
        opportunity.delete()
