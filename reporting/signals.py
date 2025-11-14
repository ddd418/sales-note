"""
영업 보고 시스템 시그널
- 납품 완료 시 OpportunityTracking 자동 업데이트
- Schedule 삭제 시 연결된 OpportunityTracking도 삭제
- DeliveryItem 생성/삭제 시 Product 판매횟수 자동 업데이트
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from datetime import date
from .models import History, OpportunityTracking, Schedule, DeliveryItem


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
            
            # 납품 품목의 제품 판매횟수 증가
            for delivery_item in instance.delivery_items_set.all():
                if delivery_item.product:
                    delivery_item.product.total_sold += delivery_item.quantity
                    delivery_item.product.save(update_fields=['total_sold'])
            
            # 납품 품목 총액 계산하여 actual_revenue 업데이트
            total_delivery_amount = 0
            for item in instance.delivery_items_set.all():
                if item.total_price:
                    total_delivery_amount += item.total_price
                elif item.unit_price and item.quantity:
                    from decimal import Decimal
                    total_delivery_amount += item.unit_price * item.quantity * Decimal('1.1')
            
            if total_delivery_amount > 0:
                opportunity.actual_revenue = total_delivery_amount
            
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
        
        # 일정 상태가 완료 → 예정으로 변경되고 납품 일정인 경우 (판매횟수 감소)
        elif (instance.status != 'completed' and 
              old_schedule.status == 'completed' and 
              instance.activity_type == 'delivery'):
            
            # 납품 품목의 제품 판매횟수 감소
            for delivery_item in instance.delivery_items_set.all():
                if delivery_item.product:
                    delivery_item.product.total_sold = max(0, delivery_item.product.total_sold - delivery_item.quantity)
                    delivery_item.product.save(update_fields=['total_sold'])
            
            # actual_revenue 초기화 (완료 취소)
            opportunity.actual_revenue = None
        
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
    단, 다른 Schedule이 같은 OpportunityTracking을 참조하고 있으면 삭제 안하고 금액만 재계산
    """
    # 서비스 일정은 OpportunityTracking과 무관
    if instance.activity_type == 'service':
        return
    
    # OpportunityTracking이 연결되어 있지 않으면 종료
    try:
        opportunity = instance.opportunity
        if not opportunity:
            return
    except OpportunityTracking.DoesNotExist:
        # opportunity가 이미 삭제된 경우 무시
        return
    
    # 같은 OpportunityTracking을 참조하는 다른 Schedule이 있는지 확인
    other_schedules = Schedule.objects.filter(
        opportunity=opportunity
    ).exclude(pk=instance.pk).exists()
    
    if not other_schedules:
        # 다른 Schedule이 없으면 OpportunityTracking도 삭제
        try:
            opportunity.delete()
        except OpportunityTracking.DoesNotExist:
            # 이미 삭제된 경우 무시
            pass
    else:
        # 다른 Schedule이 남아있으면 수주 금액과 실제 매출 재계산
        try:
            opportunity.update_revenue_amounts()
        except Exception:
            # 재계산 실패 시 무시
            pass


@receiver(post_save, sender=DeliveryItem)
def update_product_sales_count_on_create(sender, instance, created, **kwargs):
    """
    DeliveryItem 생성 시:
    1. 연결된 Product의 판매횟수 증가 (납품 완료 시에만)
    2. Schedule의 OpportunityTracking 수주 금액 업데이트
    """
    if created and instance.product and instance.schedule:
        # 1. 제품 판매횟수 증가 (납품 완료 시에만)
        if instance.schedule.status == 'completed':
            instance.product.total_sold += instance.quantity
            instance.product.save(update_fields=['total_sold'])
    
    # 2. OpportunityTracking 수주 금액 업데이트 (Schedule 또는 History 통해)
    target_schedule = None
    
    if created and instance.schedule:
        target_schedule = instance.schedule
    elif created and instance.history and instance.history.schedule:
        target_schedule = instance.history.schedule
    
    if target_schedule:
        # Schedule에 연결된 OpportunityTracking 찾기
        if hasattr(target_schedule, 'opportunity') and target_schedule.opportunity:
            opportunity = target_schedule.opportunity
            
            # 해당 Schedule의 모든 DeliveryItem 총액 계산 (Schedule + History)
            total_delivery_amount = 0
            from decimal import Decimal
            
            # Schedule의 DeliveryItem
            for item in target_schedule.delivery_items_set.all():
                if item.total_price:
                    total_delivery_amount += item.total_price
                elif item.unit_price and item.quantity:
                    total_delivery_amount += item.unit_price * item.quantity * Decimal('1.1')
            
            # History의 DeliveryItem
            for history in target_schedule.histories.all():
                for item in history.delivery_items_set.all():
                    if item.total_price:
                        total_delivery_amount += item.total_price
                    elif item.unit_price and item.quantity:
                        total_delivery_amount += item.unit_price * item.quantity * Decimal('1.1')
            
            # OpportunityTracking의 actual_revenue 업데이트
            if total_delivery_amount > 0:
                opportunity.actual_revenue = total_delivery_amount
                
                # won 단계가 아니면 won으로 변경
                if opportunity.current_stage != 'won':
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
                        'note': f'납품 완료 (Schedule ID: {target_schedule.id})'
                    })
                
                opportunity.save()


@receiver(post_delete, sender=DeliveryItem)
def update_product_sales_count_on_delete(sender, instance, **kwargs):
    """
    DeliveryItem 삭제 시:
    1. 연결된 Product의 판매횟수 감소 (납품 완료 시에만)
    2. Schedule의 OpportunityTracking 수주 금액 재계산 (Schedule + History 포함)
    """
    # 1. 제품 판매횟수 감소 (납품 완료 시에만)
    if instance.product_id and instance.schedule_id:
        try:
            from .models import Product
            schedule = Schedule.objects.get(id=instance.schedule_id)
            
            # 납품 완료 상태일 때만 판매횟수 감소
            if schedule.status == 'completed':
                product = Product.objects.get(id=instance.product_id)
                # 판매횟수가 음수가 되지 않도록 보호
                product.total_sold = max(0, product.total_sold - instance.quantity)
                product.save(update_fields=['total_sold'])
        except Exception:
            # Product 또는 Schedule이 이미 삭제된 경우 무시
            pass
    
    # 2. OpportunityTracking 수주 금액 재계산
    target_schedule_id = instance.schedule_id
    
    # History를 통한 삭제인 경우
    if not target_schedule_id and instance.history_id:
        try:
            from .models import History
            history = History.objects.get(id=instance.history_id)
            target_schedule_id = history.schedule_id
        except Exception:
            pass
    
    if target_schedule_id:
        try:
            schedule = Schedule.objects.get(id=target_schedule_id)
            
            # Schedule에 연결된 OpportunityTracking 찾기
            if hasattr(schedule, 'opportunity') and schedule.opportunity:
                opportunity = schedule.opportunity
                
                # OpportunityTracking의 backlog_amount와 actual_revenue 재계산
                opportunity.update_revenue_amounts()
        except Schedule.DoesNotExist:
            # Schedule이 이미 삭제된 경우 무시 (CASCADE 삭제 중)
            pass
        except Exception:
            # 기타 예외 무시
            pass
