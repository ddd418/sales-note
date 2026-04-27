"""
펀넬 관리 뷰 - 부서/연구실별 매출 비교 및 목표 관리
"""
import json
import logging
from decimal import Decimal
from datetime import date

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum, Count, Q, Prefetch
from django.utils import timezone

from .models import (
    Department, Company, FollowUp, Schedule, History, 
    DeliveryItem, FunnelTarget, Quote
)

logger = logging.getLogger(__name__)


def _get_user_profile(user):
    """사용자 프로필 헬퍼"""
    from .views import get_user_profile
    return get_user_profile(user)


def _get_accessible_followups(user, request):
    """권한에 따른 접근 가능한 FollowUp 쿼리셋 반환"""
    user_profile = _get_user_profile(user)
    
    if user_profile.is_admin():
        if hasattr(request, 'admin_filter_user') and request.admin_filter_user:
            return FollowUp.objects.filter(user=request.admin_filter_user)
        elif hasattr(request, 'admin_filter_company') and request.admin_filter_company:
            from .views import get_accessible_users
            accessible_users = get_accessible_users(user, request)
            return FollowUp.objects.filter(user__in=accessible_users)
        return FollowUp.objects.all()
    elif user_profile.role == 'manager':
        from .views import get_accessible_users
        accessible_users = get_accessible_users(user, request)
        return FollowUp.objects.filter(user__in=accessible_users)
    else:
        return FollowUp.objects.filter(user=user)


def _calculate_department_revenue(department_id, year, followup_ids):
    """
    부서의 연간 매출 계산 (대시보드와 동일한 로직)
    - Schedule 기반 DeliveryItem 합산 우선
    - DeliveryItem 없으면 History.delivery_amount 사용
    - Schedule 없는 독립 History 금액 추가
    """
    total = Decimal('0')
    
    # 해당 부서의 FollowUp에 연결된 납품 Schedule (완료된 것만)
    delivery_schedules = Schedule.objects.filter(
        followup_id__in=followup_ids,
        visit_date__year=year,
        activity_type='delivery',
        status='completed',
    ).prefetch_related('delivery_items_set')
    
    # 해당 부서의 납품 History
    delivery_histories = History.objects.filter(
        followup_id__in=followup_ids,
        action_type='delivery_schedule',
        created_at__year=year,
    )
    
    processed_schedule_ids = set()
    
    # 1단계: Schedule의 DeliveryItem 우선
    for schedule in delivery_schedules:
        items = list(schedule.delivery_items_set.all())
        schedule_amount = sum(item.total_price or Decimal('0') for item in items)
        
        if schedule_amount > 0:
            total += schedule_amount
        else:
            related_history = delivery_histories.filter(
                schedule_id=schedule.id
            ).order_by('-created_at').first()
            if related_history:
                total += related_history.delivery_amount or Decimal('0')
        
        processed_schedule_ids.add(schedule.id)
    
    # 2단계: Schedule 없는 독립 History
    standalone_histories = delivery_histories.filter(schedule_id__isnull=True)
    for h in standalone_histories:
        total += h.delivery_amount or Decimal('0')
    
    return total


def _calculate_department_stats(department_id, year, followup_ids):
    """부서의 연간 활동 통계 (미팅, 견적, 납품 횟수)"""
    schedules = Schedule.objects.filter(
        followup_id__in=followup_ids,
        visit_date__year=year,
    )
    
    meeting_count = schedules.filter(activity_type='customer_meeting').count()
    quote_count = schedules.filter(activity_type='quote').count()
    delivery_count = schedules.filter(activity_type='delivery', status='completed').count()
    
    return {
        'meeting_count': meeting_count,
        'quote_count': quote_count,
        'delivery_count': delivery_count,
    }


def _calculate_monthly_revenue(followup_ids, year):
    """월별 매출 계산 (차트용)"""
    monthly_data = []
    
    for month in range(1, 13):
        # DeliveryItem 기준
        delivery_schedules = Schedule.objects.filter(
            followup_id__in=followup_ids,
            visit_date__year=year,
            visit_date__month=month,
            activity_type='delivery',
            status='completed',
        )
        
        item_total = DeliveryItem.objects.filter(
            schedule__in=delivery_schedules
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        # DeliveryItem 없는 Schedule의 History 금액
        schedules_without_items = []
        for s in delivery_schedules:
            if not s.delivery_items_set.exists():
                schedules_without_items.append(s.id)
        
        history_total = History.objects.filter(
            schedule_id__in=schedules_without_items,
            action_type='delivery_schedule',
        ).aggregate(total=Sum('delivery_amount'))['total'] or Decimal('0')
        
        # 독립 History
        standalone_total = History.objects.filter(
            followup_id__in=followup_ids,
            action_type='delivery_schedule',
            created_at__year=year,
            created_at__month=month,
            schedule_id__isnull=True,
        ).aggregate(total=Sum('delivery_amount'))['total'] or Decimal('0')
        
        monthly_data.append(float(item_total + history_total + standalone_total))
    
    return monthly_data


@login_required
def funnel_list_view(request):
    """펀넬 메인 리스트 - 부서별 매출 비교 테이블"""
    user_profile = _get_user_profile(request.user)
    current_year = timezone.now().year
    last_year = current_year - 1
    
    # 접근 가능한 FollowUp
    accessible_followups = _get_accessible_followups(request.user, request)
    
    # 매출이 있는 부서 찾기 (작년 또는 올해)
    # 1) 납품 Schedule이 있는 FollowUp의 department_id
    followup_with_delivery = accessible_followups.filter(
        Q(schedules__activity_type='delivery', schedules__status='completed',
          schedules__visit_date__year__in=[last_year, current_year]) |
        Q(histories__action_type='delivery_schedule',
          histories__created_at__year__in=[last_year, current_year])
    ).values_list('department_id', flat=True).distinct()
    
    # 2) 수동 추가된 FunnelTarget의 department_id
    manual_targets = FunnelTarget.objects.filter(
        user=request.user,
        year=current_year,
        is_auto_added=False,
    ).values_list('department_id', flat=True)
    
    # 합치기
    all_dept_ids = set(followup_with_delivery) | set(manual_targets)
    all_dept_ids.discard(None)  # None 제거
    
    departments = Department.objects.filter(
        id__in=all_dept_ids
    ).select_related('company').order_by('company__name', 'name')
    
    # 부서별 데이터 조합
    funnel_data = []
    total_last_revenue = Decimal('0')
    total_target_revenue = Decimal('0')
    total_current_revenue = Decimal('0')
    
    for dept in departments:
        # 해당 부서의 FollowUp IDs
        dept_followup_ids = list(
            accessible_followups.filter(department=dept).values_list('id', flat=True)
        )
        
        # 작년/올해 매출 (FollowUp이 없으면 0)
        if dept_followup_ids:
            last_revenue = _calculate_department_revenue(dept.id, last_year, dept_followup_ids)
            current_revenue = _calculate_department_revenue(dept.id, current_year, dept_followup_ids)
            current_stats = _calculate_department_stats(dept.id, current_year, dept_followup_ids)
        else:
            last_revenue = Decimal('0')
            current_revenue = Decimal('0')
            current_stats = {'meeting_count': 0, 'quote_count': 0, 'delivery_count': 0}
        
        # 목표 매출 (FunnelTarget)
        target = FunnelTarget.objects.filter(
            user=request.user, department=dept, year=current_year
        ).first()
        target_revenue = target.target_revenue if target else Decimal('0')
        target_note = target.note if target else ''
        target_id = target.id if target else None
        
        # 달성률
        achievement_rate = 0
        if target_revenue > 0:
            achievement_rate = round(float(current_revenue) / float(target_revenue) * 100, 1)
        
        # 증감률 (작년 대비)
        growth_rate = 0
        if last_revenue > 0:
            growth_rate = round((float(current_revenue) - float(last_revenue)) / float(last_revenue) * 100, 1)
        
        # 신호등 상태
        if achievement_rate >= 80:
            status_color = 'success'   # 초록
        elif achievement_rate >= 50:
            status_color = 'warning'   # 노랑
        else:
            status_color = 'danger'    # 빨강
        
        funnel_data.append({
            'department': dept,
            'company_name': dept.company.name,
            'department_name': dept.name,
            'department_id': dept.id,
            'last_revenue': last_revenue,
            'target_revenue': target_revenue,
            'current_revenue': current_revenue,
            'achievement_rate': achievement_rate,
            'growth_rate': growth_rate,
            'status_color': status_color,
            'target_id': target_id,
            'target_note': target_note,
            'meeting_count': current_stats['meeting_count'],
            'quote_count': current_stats['quote_count'],
            'delivery_count': current_stats['delivery_count'],
            'is_manual': target is not None and not target.is_auto_added,
            'can_delete': (target is not None and not target.is_auto_added 
                          and last_revenue == 0 and current_revenue == 0),
        })
        
        total_last_revenue += last_revenue
        total_target_revenue += target_revenue
        total_current_revenue += current_revenue
    
    # 정렬 옵션
    sort_by = request.GET.get('sort', 'current_revenue')
    sort_dir = request.GET.get('dir', 'desc')
    
    sort_key_map = {
        'company': lambda x: x['company_name'],
        'department': lambda x: x['department_name'],
        'last_revenue': lambda x: x['last_revenue'],
        'target_revenue': lambda x: x['target_revenue'],
        'current_revenue': lambda x: x['current_revenue'],
        'achievement_rate': lambda x: x['achievement_rate'],
        'growth_rate': lambda x: x['growth_rate'],
    }
    
    if sort_by in sort_key_map:
        funnel_data.sort(
            key=sort_key_map[sort_by],
            reverse=(sort_dir == 'desc')
        )
    
    # 전체 달성률/증감률
    total_achievement = 0
    if total_target_revenue > 0:
        total_achievement = round(float(total_current_revenue) / float(total_target_revenue) * 100, 1)
    
    total_growth = 0
    if total_last_revenue > 0:
        total_growth = round((float(total_current_revenue) - float(total_last_revenue)) / float(total_last_revenue) * 100, 1)
    
    context = {
        'funnel_data': funnel_data,
        'current_year': current_year,
        'last_year': last_year,
        'total_last_revenue': total_last_revenue,
        'total_target_revenue': total_target_revenue,
        'total_current_revenue': total_current_revenue,
        'total_achievement': total_achievement,
        'total_growth': total_growth,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        'total_count': len(funnel_data),
    }
    
    return render(request, 'reporting/funnel/funnel_list.html', context)


@login_required
def funnel_detail_view(request, department_id):
    """펀넬 상세 - 부서별 작년/올해 비교 상세 페이지"""
    department = get_object_or_404(Department.objects.select_related('company'), id=department_id)
    user_profile = _get_user_profile(request.user)
    current_year = timezone.now().year
    last_year = current_year - 1
    
    accessible_followups = _get_accessible_followups(request.user, request)
    dept_followup_ids = list(
        accessible_followups.filter(department=department).values_list('id', flat=True)
    )
    
    # === 매출 데이터 ===
    last_revenue = _calculate_department_revenue(department.id, last_year, dept_followup_ids)
    current_revenue = _calculate_department_revenue(department.id, current_year, dept_followup_ids)
    
    # 목표
    target = FunnelTarget.objects.filter(
        user=request.user, department=department, year=current_year
    ).first()
    target_revenue = target.target_revenue if target else Decimal('0')
    
    achievement_rate = 0
    if target_revenue > 0:
        achievement_rate = round(float(current_revenue) / float(target_revenue) * 100, 1)
    
    growth_rate = 0
    if last_revenue > 0:
        growth_rate = round((float(current_revenue) - float(last_revenue)) / float(last_revenue) * 100, 1)
    
    remaining_revenue = max(target_revenue - current_revenue, Decimal('0'))
    target_achieved = current_revenue >= target_revenue and target_revenue > 0
    
    # === 활동 통계 비교 ===
    last_stats = _calculate_department_stats(department.id, last_year, dept_followup_ids)
    current_stats = _calculate_department_stats(department.id, current_year, dept_followup_ids)
    
    # === 월별 매출 추이 (차트용) ===
    last_monthly = _calculate_monthly_revenue(dept_followup_ids, last_year)
    current_monthly = _calculate_monthly_revenue(dept_followup_ids, current_year)
    
    # === 미팅 히스토리 (타임라인) ===
    last_meetings = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=last_year,
        activity_type='customer_meeting',
    ).select_related('followup').order_by('-visit_date')[:20]
    
    current_meetings = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=current_year,
        activity_type='customer_meeting',
    ).select_related('followup').order_by('-visit_date')[:20]
    
    # === 견적 리스트 ===
    last_quotes = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=last_year,
        activity_type='quote',
    ).select_related('followup').order_by('-visit_date')
    
    current_quotes = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=current_year,
        activity_type='quote',
    ).select_related('followup').order_by('-visit_date')
    
    # === 납품 리스트 ===
    last_deliveries = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=last_year,
        activity_type='delivery',
        status='completed',
    ).select_related('followup').prefetch_related('delivery_items_set').order_by('-visit_date')
    
    current_deliveries = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__year=current_year,
        activity_type='delivery',
        status='completed',
    ).select_related('followup').prefetch_related('delivery_items_set').order_by('-visit_date')
    
    # === 제품별 매출 분석 ===
    last_product_sales = DeliveryItem.objects.filter(
        schedule__followup_id__in=dept_followup_ids,
        schedule__visit_date__year=last_year,
        schedule__activity_type='delivery',
        schedule__status='completed',
    ).values('item_name').annotate(
        total=Sum('total_price'),
        qty=Sum('quantity'),
    ).order_by('-total')[:10]
    
    current_product_sales = DeliveryItem.objects.filter(
        schedule__followup_id__in=dept_followup_ids,
        schedule__visit_date__year=current_year,
        schedule__activity_type='delivery',
        schedule__status='completed',
    ).values('item_name').annotate(
        total=Sum('total_price'),
        qty=Sum('quantity'),
    ).order_by('-total')[:10]
    
    # === 다음 예정 일정 ===
    today = timezone.now().date()
    upcoming_schedules = Schedule.objects.filter(
        followup_id__in=dept_followup_ids,
        visit_date__gte=today,
        status='scheduled',
    ).select_related('followup').order_by('visit_date', 'visit_time')[:5]
    
    # === 고객(FollowUp) 목록 ===
    dept_followups = accessible_followups.filter(
        department=department
    ).select_related('company', 'department')
    
    context = {
        'department': department,
        'current_year': current_year,
        'last_year': last_year,
        'last_revenue': last_revenue,
        'current_revenue': current_revenue,
        'target_revenue': target_revenue,
        'target': target,
        'achievement_rate': achievement_rate,
        'growth_rate': growth_rate,
        'remaining_revenue': remaining_revenue,
        'target_achieved': target_achieved,
        'last_stats': last_stats,
        'current_stats': current_stats,
        'last_monthly': json.dumps(last_monthly),
        'current_monthly': json.dumps(current_monthly),
        'last_meetings': last_meetings,
        'current_meetings': current_meetings,
        'last_quotes': last_quotes,
        'current_quotes': current_quotes,
        'last_deliveries': last_deliveries,
        'current_deliveries': current_deliveries,
        'last_product_sales': last_product_sales,
        'current_product_sales': current_product_sales,
        'upcoming_schedules': upcoming_schedules,
        'dept_followups': dept_followups,
    }
    
    return render(request, 'reporting/funnel/funnel_detail.html', context)


@login_required
@require_POST
def funnel_save_target(request):
    """펀넬 목표 매출 저장 API"""
    try:
        data = json.loads(request.body)
        department_id = data.get('department_id')
        target_revenue = data.get('target_revenue', 0)
        note = data.get('note', '')
        year = data.get('year', timezone.now().year)
        
        department = get_object_or_404(Department, id=department_id)
        
        target, created = FunnelTarget.objects.update_or_create(
            user=request.user,
            department=department,
            year=year,
            defaults={
                'target_revenue': Decimal(str(target_revenue)),
                'note': note,
            }
        )
        
        return JsonResponse({
            'success': True,
            'target_id': target.id,
            'target_revenue': float(target.target_revenue),
            'message': '목표가 저장되었습니다.' if not created else '목표가 생성되었습니다.',
        })
    except Exception as e:
        logger.error(f"펀넬 목표 저장 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def funnel_auto_target(request):
    """작년 매출 기준 자동 목표 설정 API"""
    try:
        data = json.loads(request.body)
        department_id = data.get('department_id')
        percentage = float(data.get('percentage', 100))
        year = data.get('year', timezone.now().year)
        
        department = get_object_or_404(Department, id=department_id)
        
        # 작년 매출 조회
        accessible_followups = _get_accessible_followups(request.user, request)
        dept_followup_ids = list(
            accessible_followups.filter(department=department).values_list('id', flat=True)
        )
        last_revenue = _calculate_department_revenue(department.id, year - 1, dept_followup_ids)
        
        # 퍼센트 적용
        target_revenue = Decimal(str(float(last_revenue) * percentage / 100))
        
        target, created = FunnelTarget.objects.update_or_create(
            user=request.user,
            department=department,
            year=year,
            defaults={
                'target_revenue': target_revenue,
            }
        )
        
        return JsonResponse({
            'success': True,
            'target_id': target.id,
            'target_revenue': float(target.target_revenue),
            'last_revenue': float(last_revenue),
            'percentage': percentage,
        })
    except Exception as e:
        logger.error(f"자동 목표 설정 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def funnel_add_department(request):
    """수동으로 부서를 펀넬에 추가하는 API"""
    try:
        data = json.loads(request.body)
        department_id = data.get('department_id')
        year = data.get('year', timezone.now().year)
        
        department = get_object_or_404(Department, id=department_id)
        
        # 이미 존재하는지 확인
        target, created = FunnelTarget.objects.get_or_create(
            user=request.user,
            department=department,
            year=year,
            defaults={
                'target_revenue': Decimal('0'),
                'is_auto_added': False,
            }
        )
        
        if not created:
            return JsonResponse({
                'success': False,
                'error': '이미 펀넬에 추가된 부서입니다.',
            })
        
        # 해당 부서의 매출 데이터 계산
        accessible_followups = _get_accessible_followups(request.user, request)
        dept_followup_ids = list(
            accessible_followups.filter(department=department).values_list('id', flat=True)
        )
        
        last_revenue = _calculate_department_revenue(department.id, year - 1, dept_followup_ids)
        current_revenue = _calculate_department_revenue(department.id, year, dept_followup_ids)
        
        return JsonResponse({
            'success': True,
            'department_id': department.id,
            'department_name': department.name,
            'company_name': department.company.name,
            'last_revenue': float(last_revenue),
            'current_revenue': float(current_revenue),
            'message': f'{department.company.name} - {department.name}이(가) 추가되었습니다.',
        })
    except Exception as e:
        logger.error(f"부서 추가 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def funnel_remove_department(request):
    """펀넬에서 수동 추가된 부서 제거 API"""
    try:
        data = json.loads(request.body)
        department_id = data.get('department_id')
        year = data.get('year', timezone.now().year)
        
        deleted_count, _ = FunnelTarget.objects.filter(
            user=request.user,
            department_id=department_id,
            year=year,
            is_auto_added=False,
        ).delete()
        
        if deleted_count == 0:
            return JsonResponse({
                'success': False,
                'error': '자동 추가된 부서는 제거할 수 없습니다.',
            })
        
        return JsonResponse({
            'success': True,
            'message': '펀넬에서 제거되었습니다.',
        })
    except Exception as e:
        logger.error(f"부서 제거 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def funnel_search_departments(request):
    """부서 검색 API (펀넬 추가용)"""
    query = request.GET.get('q', '').strip()
    year = int(request.GET.get('year', timezone.now().year))
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # 부서 검색
    departments = Department.objects.filter(
        Q(name__icontains=query) | Q(company__name__icontains=query)
    ).select_related('company').order_by('company__name', 'name')[:20]
    
    # 이미 펀넬에 있는 부서 ID 목록
    existing_dept_ids = set(
        FunnelTarget.objects.filter(
            user=request.user, year=year
        ).values_list('department_id', flat=True)
    )
    
    results = []
    for dept in departments:
        results.append({
            'id': dept.id,
            'name': dept.name,
            'company_name': dept.company.name,
            'already_added': dept.id in existing_dept_ids,
        })
    
    return JsonResponse({'results': results})


@login_required
@require_POST
def funnel_bulk_auto_target(request):
    """전체 부서 일괄 자동 목표 설정 API"""
    try:
        data = json.loads(request.body)
        percentage = float(data.get('percentage', 100))
        year = data.get('year', timezone.now().year)
        
        accessible_followups = _get_accessible_followups(request.user, request)
        
        # 올해 FunnelTarget이 있는 부서들
        targets = FunnelTarget.objects.filter(
            user=request.user, year=year
        ).select_related('department')
        
        updated_count = 0
        for target in targets:
            dept_followup_ids = list(
                accessible_followups.filter(department=target.department).values_list('id', flat=True)
            )
            last_revenue = _calculate_department_revenue(target.department_id, year - 1, dept_followup_ids)
            
            if last_revenue > 0:
                target.target_revenue = Decimal(str(float(last_revenue) * percentage / 100))
                target.save(update_fields=['target_revenue', 'updated_at'])
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'{updated_count}개 부서의 목표가 설정되었습니다.',
        })
    except Exception as e:
        logger.error(f"일괄 목표 설정 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================
# 칸반 파이프라인 보드
# ============================================================


def _current_month_range():
    """이번 달 첫날과 다음 달 첫날을 반환 (DateField 비교용, 타임존 안전)"""
    today = timezone.localdate()
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month_start = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month_start = today.replace(month=today.month + 1, day=1)
    return month_start, next_month_start


# 파이프라인 단계 순서 (앞으로만 자동 이동 시 비교용)
STAGE_ORDER = ['potential', 'contact', 'quote', 'negotiation', 'won', 'lost']

PIPELINE_STAGES = [
    ('potential',    '잠재',      '#6c757d', 'fas fa-seedling'),
    ('contact',      '접촉/미팅', '#0d6efd', 'fas fa-handshake'),
    ('quote',        '견적 제출', '#f59e0b', 'fas fa-file-invoice'),
    ('negotiation',  '협상',      '#8b5cf6', 'fas fa-comments-dollar'),
    ('won',          '수주',      '#198754', 'fas fa-trophy'),
    ('lost',         '실주',      '#dc3545', 'fas fa-times-circle'),
]

GRADE_COLORS = {'VIP': '#ffd700', 'A': '#28a745', 'B': '#17a2b8', 'C': '#6c757d', 'D': '#dc3545'}


def _suggest_pipeline_stage(followup, current_month_schedules=None, recent_histories=None):
    """
    Quote / Schedule / History 데이터를 기반으로 추천 파이프라인 단계와 근거를 반환.
    - prefetch_related('quotes') 후 호출 시 DB 추가 쿼리 없음.
    - current_month_schedules: 최근 30일 Schedule 리스트 (미리 날짜 필터링된 것).
    - recent_histories: 최근 30일 History 리스트 (미리 날짜 필터링된 것).
      None 이면 History 기반 단계 추천을 건너뜀 (날짜 필터 없는 전체 조회 방지).
    Returns (stage_key, source_label) or (None, None) if no better suggestion.

    단계 우선순위: 견적(Quote) > 최근 30일 일정 > 최근 30일 미팅 히스토리
    """
    # 1. Quote 기반 (최우선 — 실제 견적 객체)
    quotes = list(followup.quotes.all())
    if quotes:
        stages_set = {q.stage for q in quotes}
        if stages_set & {'approved', 'converted'}:
            return ('won', '견적 수주')
        if 'negotiation' in stages_set:
            return ('negotiation', '견적 협상')
        # 전체가 거절/만료면 실주 추천
        if stages_set <= {'rejected', 'expired'}:
            return ('lost', '견적 거절')
        return ('quote', '견적')

    # 2. 최근 30일 일정 기반 (current_month_schedules는 이미 날짜 필터된 목록)
    #    ※ 견적 일정이 있으면 quote 우선 — 미팅 일정보다 항상 앞섬
    if current_month_schedules:
        has_quote_schedule = any(
            s.activity_type == 'quote'
            or '견적' in (s.notes or '')
            or '견적' in (s.title if hasattr(s, 'title') else '')
            for s in current_month_schedules
        )
        if has_quote_schedule:
            return ('quote', '최근 견적 일정')
        # 최근 30일 내 다른 일정(미팅/접촉 등)이 있으면 contact 단계 추천
        return ('contact', '최근 30일 일정')

    # 3. 최근 30일 History 기반 (recent_histories는 이미 날짜 필터된 목록)
    #    ※ 날짜 필터 없는 followup.histories.all() 호출 절대 금지
    #    ※ None 이면 안전하게 건너뜀 (전체 이력 조회 방지)
    if recent_histories is not None:
        # 견적 히스토리가 있으면 quote 우선
        if any(h.action_type == 'quote' for h in recent_histories):
            return ('quote', '최근 견적 활동')
        # 최근 30일 내 고객 미팅 히스토리가 있으면 contact
        if any(h.action_type == 'customer_meeting' for h in recent_histories):
            return ('contact', '최근 고객 미팅')

    return (None, None)


def _try_advance_pipeline(followup, target_stage):
    """
    파이프라인 단계를 앞으로만 자동 이동 (Method C — DB 필드 추가 없음).
    - won / lost 단계는 자동으로 덮어쓰지 않음.
    - 현재 단계가 이미 같거나 더 앞선 경우 skip.
    Returns True if stage was actually changed.
    """
    current = followup.pipeline_stage or 'potential'
    if current in ('won', 'lost'):
        return False
    if target_stage not in STAGE_ORDER:
        return False
    current_idx = STAGE_ORDER.index(current) if current in STAGE_ORDER else 0
    target_idx = STAGE_ORDER.index(target_stage)
    if target_idx > current_idx:
        followup.pipeline_stage = target_stage
        followup.save(update_fields=['pipeline_stage'])
        return True
    return False


@login_required
def funnel_pipeline_view(request):
    """칸반 파이프라인 보드 뷰"""
    from datetime import timedelta
    today = timezone.localdate()
    thirty_days_ago = today - timedelta(days=30)

    followups = _get_accessible_followups(request.user, request)
    # 단계 추천용: 최근 30일 히스토리 (날짜 필터 — meeting_date 우선, fallback created_at)
    recent_histories_qs = History.objects.filter(
        parent_history__isnull=True,
    ).filter(
        Q(meeting_date__gte=thirty_days_ago) |
        Q(meeting_date__isnull=True, created_at__date__gte=thirty_days_ago)
    ).order_by('-created_at')

    followups = followups.select_related(
        'company', 'department', 'user'
    ).prefetch_related(
        # 표시용: 미래 예정 일정 (카드에 "다음 방문" 표시)
        Prefetch('schedules', queryset=Schedule.objects.filter(
            visit_date__gte=today,
            status='scheduled',
        ).order_by('visit_date'), to_attr='upcoming_schedules'),
        # 단계 추천용: 최근 30일 일정 (cancelled 제외)
        Prefetch('schedules', queryset=Schedule.objects.filter(
            visit_date__gte=thirty_days_ago,
            visit_date__lte=today,
        ).exclude(status='cancelled').order_by('visit_date'), to_attr='recent_schedules'),
        # 표시용: 전체 히스토리 (카드에 최근 활동 표시)
        Prefetch('histories', queryset=History.objects.filter(
            parent_history__isnull=True
        ).order_by('-created_at'), to_attr='all_histories'),
        # 단계 추천용: 최근 30일 히스토리 (날짜 필터)
        Prefetch('histories', queryset=recent_histories_qs,
                 to_attr='recent_histories_for_stage'),
        Prefetch('quotes', queryset=Quote.objects.order_by('-created_at'), to_attr='all_quotes'),
    )

    stage_labels = {s[0]: s[1] for s in PIPELINE_STAGES}

    # 단계별 그룹핑
    stage_map = {s[0]: [] for s in PIPELINE_STAGES}
    for fu in followups:
        stage = fu.pipeline_stage if fu.pipeline_stage in stage_map else 'potential'
        next_schedule = fu.upcoming_schedules[0] if fu.upcoming_schedules else None
        last_history = fu.all_histories[0] if fu.all_histories else None
        latest_quote = fu.all_quotes[0] if fu.all_quotes else None

        # 최근 30일 일정·히스토리를 단계 추천에 사용 (날짜 필터 필수)
        recent_schedules = getattr(fu, 'recent_schedules', [])
        recent_histories = getattr(fu, 'recent_histories_for_stage', [])
        suggested_stage, suggested_source = _suggest_pipeline_stage(
            fu, current_month_schedules=recent_schedules, recent_histories=recent_histories
        )
        has_suggestion = bool(suggested_stage and suggested_stage != fu.pipeline_stage)

        stage_map[stage].append({
            'id': fu.id,
            'customer': fu.customer_name or '이름 미입력',
            'company': str(fu.company) if fu.company else '',
            'department': str(fu.department) if fu.department else '',
            'manager': fu.manager or '',
            'owner': fu.user.get_full_name() or fu.user.username,
            'grade': fu.customer_grade,
            'grade_color': GRADE_COLORS.get(fu.customer_grade, '#6c757d'),
            'priority': fu.get_priority_display(),
            'pipeline_stage': fu.pipeline_stage,
            # 다음 예정 일정
            'next_date': next_schedule.visit_date.strftime('%m/%d') if next_schedule else None,
            'next_type': next_schedule.get_activity_type_display() if next_schedule else None,
            'next_schedule_id': next_schedule.pk if next_schedule else None,
            # 최근 히스토리
            'last_history_type': last_history.get_action_type_display() if last_history else None,
            'last_history_date': last_history.created_at.strftime('%m/%d') if last_history else None,
            'last_history_snippet': (last_history.content or '')[:40] if last_history else None,
            # 최근 견적
            'latest_quote_stage': latest_quote.get_stage_display() if latest_quote else None,
            'latest_quote_amount': f'{int(latest_quote.total_amount):,}원' if latest_quote else None,
            # 추천 단계 (자동 동기화 대상)
            'suggested_stage': suggested_stage,
            'suggested_stage_label': stage_labels.get(suggested_stage, '') if suggested_stage else '',
            'suggested_source': suggested_source or '',
            'has_suggestion': has_suggestion,
        })

    stages_context = [
        {
            'key': s[0],
            'label': s[1],
            'color': s[2],
            'icon': s[3],
            'cards': stage_map[s[0]],
            'count': len(stage_map[s[0]]),
        }
        for s in PIPELINE_STAGES
    ]

    sync_count = sum(
        1 for stage_data in stages_context
        for card in stage_data['cards']
        if card.get('has_suggestion')
    )

    return render(request, 'reporting/funnel/pipeline.html', {
        'stages': stages_context,
        'stages_json': json.dumps(stages_context, ensure_ascii=False),
        'total': sum(len(v) for v in stage_map.values()),
        'sync_count': sync_count,
    })


@login_required
@require_POST
def funnel_pipeline_move(request):
    """카드 단계 이동 API"""
    try:
        # Manager는 파이프라인 카드 이동 불가 (뷰어 권한)
        _move_profile = _get_user_profile(request.user)
        if _move_profile.is_manager():
            return JsonResponse({'success': False, 'error': '권한이 없습니다. Manager는 파이프라인 카드를 이동할 수 없습니다.'}, status=403)

        data = json.loads(request.body)
        followup_id = data.get('followup_id')
        new_stage = data.get('stage')

        valid_stages = [s[0] for s in PIPELINE_STAGES]
        if new_stage not in valid_stages:
            return JsonResponse({'success': False, 'error': '유효하지 않은 단계'}, status=400)

        # 권한 확인: 접근 가능한 followup인지
        accessible = _get_accessible_followups(request.user, request)
        fu = accessible.filter(pk=followup_id).first()
        if not fu:
            return JsonResponse({'success': False, 'error': '권한 없음'}, status=403)

        fu.pipeline_stage = new_stage
        fu.pipeline_manually_set = True  # 수동 이동 플래그: 자동 sync 보호
        fu.save(update_fields=['pipeline_stage', 'pipeline_manually_set'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def funnel_pipeline_sync(request):
    """
    파이프라인 단계 자동 동기화 API (앞으로만 이동).
    - followup_id 지정 시 단일 카드 동기화 (수동 설정 플래그 무시, 완료 후 플래그 해제)
    - followup_id 없으면 접근 가능한 전체 카드 일괄 동기화
      · pipeline_manually_set=True 카드는 건너뜀 (Blocker 4)
      · 최근 30일 일정만 기준으로 사용 (Blocker 2)
    """
    try:
        data = json.loads(request.body)
        followup_id = data.get('followup_id')

        accessible = _get_accessible_followups(request.user, request)

        # 최근 30일 기준 날짜 계산
        from datetime import timedelta
        today = timezone.localdate()
        thirty_days_ago = today - timedelta(days=30)

        # 최근 30일 일정 쿼리 (cancelled 제외)
        recent_schedules_qs = Schedule.objects.filter(
            visit_date__gte=thirty_days_ago,
            visit_date__lte=today,
        ).exclude(status='cancelled')

        # 최근 30일 히스토리 쿼리 (meeting_date 우선, fallback created_at)
        recent_histories_qs = History.objects.filter(
            parent_history__isnull=True,
        ).filter(
            Q(meeting_date__gte=thirty_days_ago) |
            Q(meeting_date__isnull=True, created_at__date__gte=thirty_days_ago)
        )

        if followup_id:
            # 단일 카드 동기화: 수동 플래그 무시, 완료 후 플래그 해제
            fu = (
                accessible
                .prefetch_related(
                    'quotes',
                    Prefetch('schedules', queryset=recent_schedules_qs,
                             to_attr='current_month_schedules'),
                    Prefetch('histories', queryset=recent_histories_qs,
                             to_attr='recent_histories'),
                )
                .filter(pk=followup_id)
                .first()
            )
            if not fu:
                return JsonResponse({'success': False, 'error': '권한 없음'}, status=403)
            # 수동 플래그 해제 (사용자가 명시적으로 단일 sync 요청)
            if fu.pipeline_manually_set:
                fu.pipeline_manually_set = False
                fu.save(update_fields=['pipeline_manually_set'])
            current_schedules = getattr(fu, 'current_month_schedules', [])
            recent_hist = getattr(fu, 'recent_histories', [])
            suggested_stage, suggested_source = _suggest_pipeline_stage(
                fu, current_month_schedules=current_schedules, recent_histories=recent_hist
            )
            if suggested_stage and suggested_stage != fu.pipeline_stage:
                changed = _try_advance_pipeline(fu, suggested_stage)
                stage_label = dict(FollowUp.PIPELINE_STAGE_CHOICES).get(fu.pipeline_stage, fu.pipeline_stage)
                return JsonResponse({
                    'success': True,
                    'changed': changed,
                    'new_stage': fu.pipeline_stage,
                    'message': f'"{stage_label}"로 단계가 변경되었습니다.' if changed else '이미 적절한 단계입니다.',
                })
            return JsonResponse({'success': True, 'changed': False, 'message': '이미 적절한 단계입니다.'})

        else:
            # 전체 일괄 동기화: 수동 설정된 카드는 건너뜀 (Blocker 4)
            followups = (
                accessible
                .filter(pipeline_manually_set=False)  # Blocker 4: 수동 이동 카드 제외
                .prefetch_related(
                    'quotes',
                    Prefetch('schedules', queryset=recent_schedules_qs,
                             to_attr='current_month_schedules'),
                    Prefetch('histories', queryset=recent_histories_qs,
                             to_attr='recent_histories'),
                )
                .all()
            )
            changed_count = 0
            for fu in followups:
                current_schedules = getattr(fu, 'current_month_schedules', [])
                recent_hist = getattr(fu, 'recent_histories', [])
                suggested_stage, _ = _suggest_pipeline_stage(
                    fu, current_month_schedules=current_schedules, recent_histories=recent_hist
                )
                if suggested_stage and _try_advance_pipeline(fu, suggested_stage):
                    changed_count += 1
            return JsonResponse({
                'success': True,
                'changed_count': changed_count,
                'message': f'{changed_count}개 항목의 단계가 업데이트되었습니다.' if changed_count else '모든 항목이 이미 적절한 단계입니다.',
            })

    except Exception as e:
        logger.error(f"파이프라인 동기화 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

