@login_required
def customer_detail_report_view(request, followup_id):
    """특정 고객의 상세 활동 리포트 - 단순화된 버전"""
    from django.db.models import Count, Sum, Q
    from datetime import datetime, timedelta
    import json
    
    # 권한 확인 및 팔로우업 조회
    try:
        followup = FollowUp.objects.select_related('user', 'company', 'department').get(id=followup_id)
        
        # Admin 사용자는 모든 데이터에 접근 가능
        if getattr(request, 'is_admin', False):
            pass  # Admin은 권한 체크 없이 진행
        else:
            # 권한 체크
            if not can_access_user_data(request.user, followup.user):
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('reporting:customer_report')
            
            # 하나과학이 아닌 경우 같은 회사 체크
            if not getattr(request, 'is_hanagwahak', False):
                user_profile_obj = getattr(request.user, 'userprofile', None)
                followup_user_profile = getattr(followup.user, 'userprofile', None)
                if (user_profile_obj and user_profile_obj.company and 
                    followup_user_profile and followup_user_profile.company and
                    user_profile_obj.company != followup_user_profile.company):
                    messages.error(request, '접근 권한이 없습니다.')
                    return redirect('reporting:customer_report')
            
    except FollowUp.DoesNotExist:
        messages.error(request, '해당 고객 정보를 찾을 수 없습니다.')
        return redirect('reporting:customer_report')
    
    # 기본 History 데이터 조회
    histories = History.objects.filter(followup=followup).order_by('-created_at')
    
    # 기본 통계 계산
    delivery_histories = histories.filter(action_type='delivery_schedule')
    meeting_histories = histories.filter(action_type='customer_meeting')
    
    total_amount = 0
    for history in delivery_histories:
        if history.delivery_amount:
            total_amount += float(history.delivery_amount)
    
    # Schedule 기반 납품 일정
    schedule_deliveries = Schedule.objects.filter(
        followup=followup,
        activity_type='delivery'
    ).order_by('-visit_date')
    
    context = {
        'followup': followup,
        'total_amount': total_amount,
        'total_meetings': meeting_histories.count(),
        'total_deliveries': delivery_histories.count(),
        'tax_invoices_issued': delivery_histories.filter(tax_invoice_issued=True).count(),
        'tax_invoices_pending': delivery_histories.filter(tax_invoice_issued=False).count(),
        'chart_labels': json.dumps([]),
        'chart_meetings': json.dumps([]),
        'chart_deliveries': json.dumps([]),
        'chart_amounts': json.dumps([]),
        'delivery_histories': delivery_histories,
        'schedule_deliveries': schedule_deliveries,
        'integrated_deliveries': list(delivery_histories) + list(schedule_deliveries),
        'meeting_histories': meeting_histories,
        'page_title': f'{followup.company.name} - {followup.contact_person if followup.contact_person else "담당자 미정"}'
    }
    
    return render(request, 'reporting/customer_detail_report.html', context)