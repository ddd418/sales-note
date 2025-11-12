"""
펀넬 관리 시스템 - 분석 유틸리티
"""
from django.db.models import Sum, Count, Avg, Q, F
from datetime import date, timedelta
from decimal import Decimal
from .models import OpportunityTracking, Quote, FunnelStage, FollowUp


class FunnelAnalytics:
    """펀넬 분석 클래스"""
    
    @staticmethod
    def get_pipeline_summary(user=None):
        """파이프라인 전체 요약"""
        qs = OpportunityTracking.objects.exclude(
            current_stage__in=['won', 'lost']
        )
        
        if user:
            qs = qs.filter(followup__user=user)
        
        summary = qs.aggregate(
            total_opportunities=Count('id'),
            total_expected=Sum('expected_revenue'),
            total_weighted=Sum('weighted_revenue'),
            avg_probability=Avg('probability')
        )
        
        # Null 값 처리
        summary['total_expected'] = summary['total_expected'] or 0
        summary['total_weighted'] = summary['total_weighted'] or 0
        summary['avg_probability'] = summary['avg_probability'] or 0
        
        return summary
    
    @staticmethod
    def get_stage_breakdown(user=None):
        """단계별 분석"""
        stages = FunnelStage.objects.all().order_by('stage_order')
        breakdown = []
        
        for stage in stages:
            opps = OpportunityTracking.objects.filter(
                current_stage=stage.name
            )
            
            if user:
                opps = opps.filter(followup__user=user)
            
            # won/lost는 별도 처리 (제외하지 않음)
            stage_data = {
                'stage': stage.display_name,
                'stage_code': stage.name,
                'count': opps.count(),
                'total_value': opps.aggregate(Sum('expected_revenue'))['expected_revenue__sum'] or 0,
                'weighted_value': opps.aggregate(Sum('weighted_revenue'))['weighted_revenue__sum'] or 0,
                'avg_probability': opps.aggregate(Avg('probability'))['probability__avg'] or 0,
                'color': stage.color,
                'icon': stage.icon,
                'stage_order': stage.stage_order,
            }
            
            breakdown.append(stage_data)
        
        return breakdown
    
    @staticmethod
    def get_monthly_forecast(months=3, user=None):
        """월별 매출 예측"""
        today = date.today()
        forecasts = []
        
        for i in range(months):
            # 해당 월의 첫날과 마지막날 계산
            if i == 0:
                month_start = today.replace(day=1)
            else:
                # 다음 월
                month_start = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
            
            # 다음 달의 첫날을 구하고 하루를 뺌
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            
            opps = OpportunityTracking.objects.filter(
                expected_close_date__range=[month_start, month_end]
            ).exclude(current_stage='lost')
            
            if user:
                opps = opps.filter(followup__user=user)
            
            forecasts.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%Y년 %m월'),
                'expected': opps.aggregate(Sum('expected_revenue'))['expected_revenue__sum'] or 0,
                'weighted': opps.aggregate(Sum('weighted_revenue'))['weighted_revenue__sum'] or 0,
                'count': opps.count(),
            })
        
        return forecasts
    
    @staticmethod
    def get_conversion_rates(user=None):
        """단계별 전환율 (SQLite 호환)"""
        stages = ['lead', 'contact', 'quote', 'negotiation', 'closing', 'won']
        rates = []
        
        for i in range(len(stages) - 1):
            current = stages[i]
            next_stage = stages[i + 1]
            
            # 전체 기회 목록 가져오기 (Python에서 필터링)
            all_opps = OpportunityTracking.objects.all()
            if user:
                all_opps = all_opps.filter(followup__user=user)
            
            # Python에서 stage_history 검사
            total = 0
            converted = 0
            
            for opp in all_opps:
                if not opp.stage_history:
                    continue
                
                # 현재 단계를 거쳤는지 확인
                has_current = any(h.get('stage') == current for h in opp.stage_history)
                if has_current:
                    total += 1
                    
                    # 다음 단계도 거쳤는지 확인
                    has_next = any(h.get('stage') == next_stage for h in opp.stage_history)
                    if has_next:
                        converted += 1
            
            rate = (converted / total * 100) if total > 0 else 0
            
            # 단계 표시명 가져오기
            try:
                from_stage_obj = FunnelStage.objects.get(name=current)
                to_stage_obj = FunnelStage.objects.get(name=next_stage)
                from_display = from_stage_obj.display_name
                to_display = to_stage_obj.display_name
            except FunnelStage.DoesNotExist:
                from_display = current
                to_display = next_stage
            
            rates.append({
                'from_stage': from_display,
                'to_stage': to_display,
                'total': total,
                'converted': converted,
                'rate': round(rate, 1)
            })
        
        return rates
    
    @staticmethod
    def get_bottleneck_analysis(user=None):
        """병목 단계 분석"""
        stages = FunnelStage.objects.exclude(
            name__in=['won', 'lost']
        ).order_by('stage_order')
        
        bottlenecks = []
        
        for stage in stages:
            opps = OpportunityTracking.objects.filter(
                current_stage=stage.name
            )
            
            if user:
                opps = opps.filter(followup__user=user)
            
            # 평균 체류 시간 계산
            total_duration = 0
            duration_count = 0
            
            for opp in opps:
                if opp.stage_history:
                    for history in opp.stage_history:
                        if history.get('stage') == stage.name:
                            entry_date = date.fromisoformat(history['entered'])
                            if history.get('exited'):
                                exit_date = date.fromisoformat(history['exited'])
                            else:
                                # 아직 해당 단계에 있음
                                exit_date = date.today()
                            
                            duration = (exit_date - entry_date).days
                            total_duration += duration
                            duration_count += 1
            
            actual_avg = (total_duration / duration_count) if duration_count > 0 else 0
            
            # 병목 여부 판단
            is_bottleneck = (
                actual_avg > stage.avg_duration_days * 1.5 or
                opps.count() > 10  # 10개 이상 정체
            )
            
            severity = 'low'
            if is_bottleneck:
                if actual_avg > stage.avg_duration_days * 2:
                    severity = 'high'
                else:
                    severity = 'medium'
            
            # 체류시간 차이 계산
            duration_diff = round(actual_avg - stage.avg_duration_days, 1)
            
            bottlenecks.append({
                'stage': stage.display_name,
                'stage_code': stage.name,
                'count': opps.count(),
                'expected_duration': stage.avg_duration_days,
                'actual_duration': round(actual_avg, 1),
                'duration_diff': duration_diff,  # 차이 추가
                'is_bottleneck': is_bottleneck,
                'severity': severity,
                'color': stage.color
            })
        
        return sorted(bottlenecks, key=lambda x: x['count'], reverse=True)
    
    @staticmethod
    def get_top_opportunities(limit=10, user=None):
        """예측 매출 상위 영업 기회 (진행 중인 것만, won/lost 제외)"""
        qs = OpportunityTracking.objects.exclude(
            current_stage__in=['won', 'lost']
        ).select_related('followup', 'followup__company', 'followup__user')
        
        if user:
            qs = qs.filter(followup__user=user)
        
        top_opps = qs.order_by('-weighted_revenue')[:limit]
        
        result = []
        for opp in top_opps:
            try:
                stage_obj = FunnelStage.objects.get(name=opp.current_stage)
                stage_display = stage_obj.display_name
                stage_color = stage_obj.color
            except FunnelStage.DoesNotExist:
                stage_display = opp.current_stage
                stage_color = '#667eea'
            
            result.append({
                'id': opp.id,
                'customer_name': opp.followup.customer_name or '고객명 미정',
                'company_name': opp.followup.company.name if opp.followup.company else '업체명 미정',
                'expected_revenue': opp.expected_revenue,
                'weighted_revenue': opp.weighted_revenue,
                'backlog_amount': opp.backlog_amount,
                'probability': opp.probability,
                'current_stage': stage_display,
                'stage_color': stage_color,
                'expected_close_date': opp.expected_close_date,
                'user': opp.followup.user.username,
            })
        
        return result
    
    @staticmethod
    def get_won_lost_summary(user=None):
        """수주/실주 요약"""
        won_qs = OpportunityTracking.objects.filter(current_stage='won')
        lost_qs = OpportunityTracking.objects.filter(current_stage='lost')
        
        if user:
            won_qs = won_qs.filter(followup__user=user)
            lost_qs = lost_qs.filter(followup__user=user)
        
        won_summary = won_qs.aggregate(
            count=Count('id'),
            total_revenue=Sum('actual_revenue')
        )
        
        lost_summary = lost_qs.aggregate(
            count=Count('id')
        )
        
        total = won_summary['count'] + lost_summary['count']
        win_rate = (won_summary['count'] / total * 100) if total > 0 else 0
        
        return {
            'won_count': won_summary['count'],
            'won_revenue': won_summary['total_revenue'] or 0,
            'lost_count': lost_summary['count'],
            'win_rate': round(win_rate, 1)
        }
    
    @staticmethod
    def get_average_lead_time(user=None):
        """평균 리드 타임 분석 (견적~납품 소요일)"""
        from .models import Schedule
        
        # 견적 일정과 납품 일정을 가진 팔로우업들
        lead_times = []
        
        followups_with_schedules = FollowUp.objects.prefetch_related('schedules').all()
        if user:
            followups_with_schedules = followups_with_schedules.filter(user=user)
        
        for followup in followups_with_schedules:
            # 해당 팔로우업의 견적 일정들
            quote_schedules = followup.schedules.filter(activity_type='quote').order_by('visit_date')
            # 해당 팔로우업의 납품 일정들
            delivery_schedules = followup.schedules.filter(activity_type='delivery').order_by('visit_date')
            
            if quote_schedules.exists() and delivery_schedules.exists():
                # 첫 견적 날짜
                first_quote_date = quote_schedules.first().visit_date
                # 첫 납품 날짜
                first_delivery_date = delivery_schedules.first().visit_date
                
                # 리드 타임 계산 (일 수)
                lead_time_days = (first_delivery_date - first_quote_date).days
                
                # 음수가 아닌 경우만 (견적이 납품보다 먼저인 경우)
                if lead_time_days >= 0:
                    lead_times.append({
                        'followup': followup,
                        'customer_name': followup.customer_name,
                        'company_name': followup.company.name if followup.company else '업체명 미정',
                        'quote_date': first_quote_date,
                        'delivery_date': first_delivery_date,
                        'lead_time_days': lead_time_days,
                    })
        
        # 평균 계산
        if lead_times:
            avg_lead_time = sum(lt['lead_time_days'] for lt in lead_times) / len(lead_times)
            max_lead_time = max(lt['lead_time_days'] for lt in lead_times)
            min_lead_time = min(lt['lead_time_days'] for lt in lead_times)
        else:
            avg_lead_time = 0
            max_lead_time = 0
            min_lead_time = 0
        
        return {
            'average_days': round(avg_lead_time, 1),
            'max_days': max_lead_time,
            'min_days': min_lead_time,
            'total_cases': len(lead_times),
            'details': sorted(lead_times, key=lambda x: x['lead_time_days'], reverse=True)[:10]  # 상위 10개
        }
    
    @staticmethod
    def get_product_sales_distribution(user=None):
        """제품군별 매출 비중"""
        from .models import DeliveryItem, Product
        
        # 납품 완료된 품목들의 제품별 집계 (status='completed'인 Schedule)
        delivery_items = DeliveryItem.objects.select_related('product', 'schedule').filter(
            product__isnull=False,  # 제품이 연결된 품목만
            schedule__status='completed'  # 완료된 일정만
        )
        
        if user:
            delivery_items = delivery_items.filter(schedule__user=user)
        
        # 제품별로 그룹화하여 매출 집계
        product_sales = {}
        total_revenue = Decimal('0')
        
        for item in delivery_items:
            product_name = item.product.product_code if item.product else item.item_name
            product_desc = item.product.description if item.product else ''
            item_total = item.total_price or Decimal('0')
            
            if product_name not in product_sales:
                product_sales[product_name] = {
                    'product_name': product_name,
                    'product_description': product_desc,
                    'total_revenue': Decimal('0'),
                    'quantity': 0,
                    'order_count': 0,
                }
            
            product_sales[product_name]['total_revenue'] += item_total
            product_sales[product_name]['quantity'] += item.quantity or 0
            product_sales[product_name]['order_count'] += 1
            total_revenue += item_total
        
        # 비중 계산 및 정렬
        product_list = []
        for product_name, data in product_sales.items():
            percentage = (float(data['total_revenue']) / float(total_revenue) * 100) if total_revenue > 0 else 0
            product_list.append({
                'product_name': data['product_name'],
                'product_description': data['product_description'],
                'total_revenue': data['total_revenue'],
                'quantity': data['quantity'],
                'order_count': data['order_count'],
                'percentage': round(percentage, 1),
            })
        
        # 매출액 기준 내림차순 정렬
        product_list = sorted(product_list, key=lambda x: x['total_revenue'], reverse=True)
        
        return {
            'total_revenue': total_revenue,
            'product_count': len(product_list),
            'products': product_list,
            'top_5': product_list[:5] if len(product_list) >= 5 else product_list,
        }
