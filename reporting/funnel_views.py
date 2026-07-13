"""
펀넬 관리 뷰 - 부서/연구실별 매출 비교 및 목표 관리
"""
import json
import logging
from decimal import Decimal
from datetime import date

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum, Count, Q, Prefetch
from django.utils import timezone

from .models import (
    Department, Company, FollowUp, Schedule, History, 
    DeliveryItem, FunnelTarget, Quote
)
from .readonly_api import readonly_bearer_or_login_required

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
    pricing_histories_qs = History.objects.filter(
        parent_history__isnull=True,
        action_type__in=['quote', 'delivery_schedule'],
    ).prefetch_related(
        Prefetch('delivery_items_set', queryset=DeliveryItem.objects.select_related('product')),
    ).order_by('-created_at')
    pricing_schedules_qs = Schedule.objects.filter(
        activity_type__in=['quote', 'delivery'],
    ).prefetch_related(
        Prefetch('delivery_items_set', queryset=DeliveryItem.objects.select_related('product')),
        Prefetch('histories', queryset=pricing_histories_qs, to_attr='pricing_histories'),
    ).order_by('-visit_date', '-created_at')

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
        # 가격 기준: 실제 견적/납품 일정 품목
        Prefetch('schedules', queryset=pricing_schedules_qs, to_attr='pricing_schedules'),
        # 표시용: 전체 히스토리 (카드에 최근 활동 표시)
        Prefetch('histories', queryset=History.objects.filter(
            parent_history__isnull=True
        ).order_by('-created_at'), to_attr='all_histories'),
        Prefetch('histories', queryset=pricing_histories_qs, to_attr='pricing_histories'),
        # 단계 추천용: 최근 30일 히스토리 (날짜 필터)
        Prefetch('histories', queryset=recent_histories_qs,
                 to_attr='recent_histories_for_stage'),
        Prefetch('quotes', queryset=Quote.objects.order_by('-created_at'), to_attr='all_quotes'),
    )

    stage_labels = {s[0]: s[1] for s in PIPELINE_STAGES}

    # 단계별 그룹핑
    stage_map = {s[0]: [] for s in PIPELINE_STAGES}
    stage_amounts = {s[0]: 0 for s in PIPELINE_STAGES}
    stage_overdue_counts = {s[0]: 0 for s in PIPELINE_STAGES}
    for fu in followups:
        stage = fu.pipeline_stage if fu.pipeline_stage in stage_map else 'potential'
        next_schedule = fu.upcoming_schedules[0] if fu.upcoming_schedules else None
        last_history = fu.all_histories[0] if fu.all_histories else None
        pricing = _select_pipeline_pricing(fu, stage)
        pricing_amount = pricing['amount']
        quote_reference = _select_quote_reference_pricing(fu, stage)
        quote_comparison = _build_quote_comparison(stage, pricing, quote_reference)
        has_overdue_action = any(
            h.next_action_date and h.next_action_date < today
            for h in getattr(fu, 'all_histories', [])
        )
        if pricing_amount > 0:
            stage_amounts[stage] += pricing_amount
        if has_overdue_action:
            stage_overdue_counts[stage] += 1

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
            # 가격 기준 데이터
            'latest_quote_stage': pricing['stage'] if pricing['source'] else None,
            'latest_quote_amount': f'{int(pricing_amount):,}원' if pricing_amount > 0 else None,
            'latest_quote_source': pricing['source'],
            'quote_comparison': _quote_comparison_template_payload(quote_comparison),
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
            'amount': int(stage_amounts.get(s[0], 0) or 0),
            'overdue_count': stage_overdue_counts.get(s[0], 0),
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


STAGE_CAPTIONS = {
    'potential': '관심 확인',
    'contact': '요구사항 파악',
    'quote': '금액/범위 협의',
    'negotiation': '의사결정 추적',
    'won': '납품 전환',
    'lost': '실주 원인 정리',
}

STAGE_PROBABILITY = {
    'potential': 18,
    'contact': 42,
    'quote': 60,
    'negotiation': 78,
    'won': 100,
    'lost': 0,
}

PIPELINE_QUOTE_PRIORITY = {
    'quote': ('sent', 'review', 'draft', 'negotiation', 'approved', 'converted'),
    'negotiation': ('negotiation', 'review', 'sent', 'approved', 'converted', 'draft'),
}

PIPELINE_ACTIVE_QUOTE_STAGES = {'draft', 'sent', 'review', 'negotiation', 'approved', 'converted'}
PIPELINE_WON_QUOTE_STAGES = {'approved', 'converted'}
PIPELINE_NULL_PROBABILITY_STAGES = {'potential', 'contact'}
PIPELINE_ACCOUNT_STAGE_PRIORITY = ('won', 'negotiation', 'quote', 'contact', 'lost', 'potential')


def _pipeline_default_probability(stage):
    if stage in PIPELINE_NULL_PROBABILITY_STAGES:
        return None
    return STAGE_PROBABILITY.get(stage, 30)


def _pipeline_account_key(followup):
    if followup.department_id:
        return ('department', followup.department_id)
    return ('followup', followup.id)


def _pipeline_account_stage(followups):
    # 끝난(비활성) 연락처가 계정 단계를 지배하지 않도록 활성 연락처만으로 단계를 정한다.
    # (예: 과거 수주 연락처가 비활성이면, 지금 진행 중인 견적 활동이 계정 단계에 드러나야 함)
    # 활성 연락처가 하나도 없으면 전체를 사용해 카드가 사라지거나 단계가 비지 않게 한다.
    active_followups = [f for f in followups if getattr(f, 'is_active', True)]
    considered = active_followups or list(followups)
    stage_values = {
        followup.pipeline_stage if followup.pipeline_stage in STAGE_PROBABILITY else 'potential'
        for followup in considered
    }
    for stage in PIPELINE_ACCOUNT_STAGE_PRIORITY:
        if stage in stage_values:
            return stage
    return 'potential'


def _pipeline_local_created_date(value):
    if not value:
        return None
    return timezone.localtime(value).date()


def _pipeline_followup_latest_date(followup):
    dates = []
    for schedule in getattr(followup, 'pricing_schedules', []):
        if schedule.visit_date:
            dates.append(schedule.visit_date)
    for schedule in getattr(followup, 'upcoming_schedules', []):
        if schedule.visit_date:
            dates.append(schedule.visit_date)
    for schedule in getattr(followup, 'recent_schedules', []):
        if schedule.visit_date:
            dates.append(schedule.visit_date)
    for history in getattr(followup, 'all_histories', []):
        history_date = _history_pricing_date(history)
        if history_date:
            dates.append(history_date)
    for quote in getattr(followup, 'all_quotes', []):
        quote_date = quote.quote_date or _pipeline_local_created_date(quote.created_at)
        if quote_date:
            dates.append(quote_date)
    return max(dates) if dates else date.min


def _pipeline_primary_followup(followups, account_stage):
    return max(
        followups,
        key=lambda followup: (
            followup.pipeline_stage == account_stage,
            _pipeline_followup_latest_date(followup),
            followup.id or 0,
        ),
    )


def _pipeline_unique_objects(items):
    result = []
    seen = set()
    for item in items:
        identity = (item.__class__, item.pk)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
    return result


def _pipeline_collect_attr(followups, attr):
    return _pipeline_unique_objects(
        item
        for followup in followups
        for item in getattr(followup, attr, [])
    )


def _pipeline_schedule_desc_key(schedule):
    created_at = schedule.created_at.isoformat() if schedule.created_at else ''
    return (schedule.visit_date or date.min, created_at, schedule.id or 0)


def _pipeline_schedule_asc_key(schedule):
    visit_time = schedule.visit_time.isoformat() if schedule.visit_time else ''
    return (schedule.visit_date or date.max, visit_time, schedule.id or 0)


def _pipeline_created_desc_key(obj):
    created_at = obj.created_at.isoformat() if obj.created_at else ''
    return (created_at, obj.id or 0)


def _pipeline_account_followup(followups, account_stage):
    followups = list(followups)
    primary = _pipeline_primary_followup(followups, account_stage)
    ordered_followups = [primary] + [followup for followup in followups if followup.id != primary.id]

    primary.account_followups = ordered_followups
    primary.pricing_schedules = sorted(
        _pipeline_collect_attr(followups, 'pricing_schedules'),
        key=_pipeline_schedule_desc_key,
        reverse=True,
    )
    primary.upcoming_schedules = sorted(
        _pipeline_collect_attr(followups, 'upcoming_schedules'),
        key=_pipeline_schedule_asc_key,
    )
    primary.recent_schedules = sorted(
        _pipeline_collect_attr(followups, 'recent_schedules'),
        key=_pipeline_schedule_desc_key,
        reverse=True,
    )
    primary.all_histories = sorted(
        _pipeline_collect_attr(followups, 'all_histories'),
        key=_pipeline_created_desc_key,
        reverse=True,
    )
    primary.pricing_histories = sorted(
        _pipeline_collect_attr(followups, 'pricing_histories'),
        key=_pipeline_created_desc_key,
        reverse=True,
    )
    primary.recent_histories_for_stage = sorted(
        _pipeline_collect_attr(followups, 'recent_histories_for_stage'),
        key=_pipeline_created_desc_key,
        reverse=True,
    )
    primary.all_quotes = sorted(
        _pipeline_collect_attr(followups, 'all_quotes'),
        key=_pipeline_created_desc_key,
        reverse=True,
    )
    return primary


def _pipeline_account_groups(followups):
    groups = {}
    for followup in followups:
        groups.setdefault(_pipeline_account_key(followup), []).append(followup)
    return groups.values()


def _pipeline_contact_label(followup):
    names = []
    seen = set()
    for contact in getattr(followup, 'account_followups', [followup]):
        name = (contact.customer_name or contact.manager or '').strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    if not names:
        return '담당자 미정'
    if len(names) == 1:
        return names[0]
    return f'{names[0]} 외 {len(names) - 1}명'


def _pipeline_account_metadata(followup):
    account_followups = getattr(followup, 'account_followups', [followup])
    if followup.department_id:
        account_key = f'department:{followup.department_id}'
    else:
        account_key = f'followup:{followup.id}'
    return {
        'accountKey': account_key,
        'accountType': 'department' if followup.department_id else 'followup',
        'accountId': followup.department_id or followup.id,
        'primaryContactId': followup.id,
        'contactIds': [contact.id for contact in account_followups],
        'contactCount': len(account_followups),
    }


def _quote_amount(quote):
    return quote.total_amount or Decimal('0')


def _delivery_item_total(items):
    total = Decimal('0')
    for item in items:
        if item.total_price is not None:
            total += item.total_price
        elif item.unit_price is not None and item.quantity:
            total += item.unit_price * item.quantity * Decimal('1.1')
    return total


def _schedule_item_total(schedule):
    return _delivery_item_total(list(schedule.delivery_items_set.all()))


def _history_item_total(history):
    return _delivery_item_total(list(history.delivery_items_set.all()))


def _history_pricing_amount(history):
    item_total = _history_item_total(history)
    if item_total > 0:
        return item_total
    return history.delivery_amount or Decimal('0')


def _history_pricing_date(history):
    if history.delivery_date:
        return history.delivery_date
    if history.meeting_date:
        return history.meeting_date
    if history.created_at:
        return timezone.localtime(history.created_at).date()
    return None


def _latest_dated_entries(entries):
    dated_entries = [entry for entry in entries if entry.get('date')]
    if not dated_entries:
        return []
    latest_date = max(entry['date'] for entry in dated_entries)
    return [entry for entry in dated_entries if entry['date'] == latest_date]


def _sum_entry_amounts(entries):
    return sum((entry['amount'] for entry in entries), Decimal('0'))


def _latest_schedule_history_amount(schedule, action_type=None):
    histories = getattr(schedule, 'pricing_histories', None)
    if histories is None:
        histories = schedule.histories.filter(
            parent_history__isnull=True,
        )
        if action_type:
            histories = histories.filter(action_type=action_type)
        histories = histories.prefetch_related('delivery_items_set').order_by('-created_at')
    for history in histories:
        if action_type and history.action_type != action_type:
            continue
        amount = _history_pricing_amount(history)
        if amount > 0:
            return amount
    return Decimal('0')


def _schedule_quote_amount(schedule):
    item_total = _schedule_item_total(schedule)
    if item_total > 0:
        return item_total
    history_amount = _latest_schedule_history_amount(schedule, 'quote')
    if history_amount > 0:
        return history_amount
    return schedule.expected_revenue or Decimal('0')


def _delivery_schedule_amount(schedule):
    item_total = _schedule_item_total(schedule)
    if item_total > 0:
        return item_total
    history_amount = _latest_schedule_history_amount(schedule, 'delivery_schedule')
    if history_amount > 0:
        return history_amount
    return schedule.expected_revenue or Decimal('0')


def _select_latest_quote_schedule(followup):
    schedules = list(getattr(followup, 'pricing_schedules', []))
    quote_schedules = [schedule for schedule in schedules if schedule.activity_type == 'quote']
    with_amount = [schedule for schedule in quote_schedules if _schedule_quote_amount(schedule) > 0]
    return with_amount[0] if with_amount else (quote_schedules[0] if quote_schedules else None)


def _select_latest_quote_history(followup):
    histories = list(getattr(followup, 'pricing_histories', []))
    quote_histories = [history for history in histories if history.action_type == 'quote']
    with_amount = [history for history in quote_histories if _history_pricing_amount(history) > 0]
    return with_amount[0] if with_amount else (quote_histories[0] if quote_histories else None)


def _quote_model_pricing(followup, stage):
    prefetched_quotes = getattr(followup, 'all_quotes', None)
    quotes = (
        list(prefetched_quotes)
        if prefetched_quotes is not None
        else list(followup.quotes.all().order_by('-created_at'))
    )
    if not quotes:
        return None

    def matching(predicate):
        return [quote for quote in quotes if predicate(quote)]

    def build(quote_matches, source):
        if not quote_matches:
            return None
        priced_entries = [
            {
                'quote': quote,
                'amount': _quote_amount(quote),
                'date': quote.quote_date,
            }
            for quote in quote_matches
            if _quote_amount(quote) > 0
        ]
        selected_entries = _latest_dated_entries(priced_entries)
        selected_quotes = [entry['quote'] for entry in selected_entries]
        if not selected_quotes:
            selected_quotes = quote_matches[:1]
            selected_entries = [
                {
                    'quote': quote,
                    'amount': _quote_amount(quote),
                    'date': quote.quote_date,
                }
                for quote in selected_quotes
            ]
        primary_quote = selected_quotes[0]
        amount = _sum_entry_amounts(selected_entries)
        if amount > 0:
            probability = round(
                sum(
                    _quote_amount(quote) * Decimal(str(quote.probability or 0))
                    for quote in selected_quotes
                ) / amount
            )
        else:
            probability = int(primary_quote.probability or 0)
        count = len(selected_quotes)
        return {
            'object': primary_quote,
            'kind': 'quote',
            'amount': amount,
            'source': f'{source} {count}건' if count > 1 else source,
            'number': (
                f'{primary_quote.quote_number} 외 {count - 1}건'
                if count > 1 else primary_quote.quote_number
            ),
            'stage': primary_quote.get_stage_display() if count == 1 else f'{primary_quote.get_stage_display()} 외 {count - 1}건',
            'probability': int(probability or 0),
            'valid_until': primary_quote.valid_until,
            'basis_date': selected_entries[0]['date'] if selected_entries else primary_quote.quote_date,
            'quote_date': selected_entries[0]['date'] if selected_entries else primary_quote.quote_date,
            'count': count,
            'items': [
                item
                for quote in selected_quotes
                for item in _pipeline_quote_model_items(quote, source)
            ],
        }

    if stage == 'won':
        pricing = build(
            matching(
                lambda item: item.converted_to_delivery or item.stage in PIPELINE_WON_QUOTE_STAGES
            ),
            '수주 견적',
        )
        if pricing:
            return pricing

    for quote_stage in PIPELINE_QUOTE_PRIORITY.get(stage, ()):
        source_label = '협상 견적' if stage == 'negotiation' else '제출 견적'
        pricing = build(matching(lambda item, expected=quote_stage: item.stage == expected), source_label)
        if pricing:
            return pricing

    pricing = build(matching(lambda item: item.stage in PIPELINE_ACTIVE_QUOTE_STAGES), '진행 견적')
    if pricing:
        return pricing

    return build(matching(lambda item: True), '최근 견적')


def _select_quote_reference_pricing(followup, stage):
    schedules = list(getattr(followup, 'pricing_schedules', []))
    quote_schedules = [schedule for schedule in schedules if schedule.activity_type == 'quote']
    priced_schedule_entries = []
    for schedule in quote_schedules:
        amount = _schedule_quote_amount(schedule)
        if amount > 0:
            priced_schedule_entries.append({
                'schedule': schedule,
                'amount': amount,
                'date': schedule.visit_date,
            })
    selected_schedule_entries = _latest_dated_entries(priced_schedule_entries)
    if selected_schedule_entries:
        total_amount = _sum_entry_amounts(selected_schedule_entries)
        primary_schedule = selected_schedule_entries[0]['schedule']
        count = len(selected_schedule_entries)
        probability = round(
            sum(
                entry['amount'] * Decimal(str(entry['schedule'].probability or STAGE_PROBABILITY.get(stage, 30)))
                for entry in selected_schedule_entries
            ) / total_amount
        ) if total_amount > 0 else STAGE_PROBABILITY.get(stage, 30)
        return {
            'object': primary_schedule,
            'kind': 'schedule',
            'amount': total_amount,
            'source': f'견적 일정 {count}건' if count > 1 else '견적 일정',
            'number': f'일정 #{primary_schedule.id} 외 {count - 1}건' if count > 1 else f'일정 #{primary_schedule.id}',
            'stage': primary_schedule.get_activity_type_display() if count == 1 else f'{primary_schedule.get_activity_type_display()} 외 {count - 1}건',
            'probability': int(probability or 0),
            'valid_until': primary_schedule.expected_close_date,
            'basis_date': selected_schedule_entries[0]['date'],
            'quote_date': selected_schedule_entries[0]['date'],
            'count': count,
            'items': [
                item
                for entry in selected_schedule_entries
                for item in _pipeline_schedule_quote_items(entry['schedule'], '견적 일정')
            ],
        }

    histories = list(getattr(followup, 'pricing_histories', []))
    quote_histories = [history for history in histories if history.action_type == 'quote']
    priced_history_entries = []
    for history in quote_histories:
        amount = _history_pricing_amount(history)
        if amount > 0:
            priced_history_entries.append({
                'history': history,
                'amount': amount,
                'date': _history_pricing_date(history),
            })
    selected_history_entries = _latest_dated_entries(priced_history_entries)
    if selected_history_entries:
        total_amount = _sum_entry_amounts(selected_history_entries)
        primary_history = selected_history_entries[0]['history']
        count = len(selected_history_entries)
        return {
            'object': primary_history,
            'kind': 'history',
            'amount': total_amount,
            'source': f'견적 활동 {count}건' if count > 1 else '견적 활동',
            'number': f'활동 #{primary_history.id} 외 {count - 1}건' if count > 1 else f'활동 #{primary_history.id}',
            'stage': primary_history.get_action_type_display() if count == 1 else f'{primary_history.get_action_type_display()} 외 {count - 1}건',
            'probability': STAGE_PROBABILITY.get(stage, 30),
            'valid_until': None,
            'basis_date': selected_history_entries[0]['date'],
            'quote_date': selected_history_entries[0]['date'],
            'count': count,
            'items': [
                item
                for entry in selected_history_entries
                for item in _pipeline_history_quote_items(entry['history'], '견적 활동')
            ],
        }

    # 금액이 없는 견적 일정/활동은 가격 기준으로 쓰지 않고 Quote 모델로 fallback한다.
    quote_schedule = quote_schedules[0] if quote_schedules else None
    if quote_schedule:
        amount = _schedule_quote_amount(quote_schedule)
        if amount > 0:
            return {
                'object': quote_schedule,
                'kind': 'schedule',
                'amount': amount,
                'source': '견적 일정',
                'number': f'일정 #{quote_schedule.id}',
                'stage': quote_schedule.get_activity_type_display(),
                'probability': quote_schedule.probability or STAGE_PROBABILITY.get(stage, 30),
                'valid_until': quote_schedule.expected_close_date,
                'basis_date': quote_schedule.visit_date,
                'quote_date': quote_schedule.visit_date,
                'items': _pipeline_schedule_quote_items(quote_schedule, '견적 일정'),
            }

    quote_history = quote_histories[0] if quote_histories else None
    if quote_history:
        amount = _history_pricing_amount(quote_history)
        if amount > 0:
            return {
                'object': quote_history,
                'kind': 'history',
                'amount': amount,
                'source': '견적 활동',
                'number': f'활동 #{quote_history.id}',
                'stage': quote_history.get_action_type_display(),
                'probability': STAGE_PROBABILITY.get(stage, 30),
                'valid_until': None,
                'basis_date': _history_pricing_date(quote_history),
                'quote_date': _history_pricing_date(quote_history),
                'items': _pipeline_history_quote_items(quote_history, '견적 활동'),
            }

    return _quote_model_pricing(followup, stage)


def _build_quote_comparison(stage, pricing, quote_reference):
    if stage != 'won' or pricing.get('kind') != 'delivery' or not quote_reference:
        return None

    actual_amount = pricing['amount'] or Decimal('0')
    quoted_amount = quote_reference['amount'] or Decimal('0')
    if actual_amount <= 0 or quoted_amount <= 0:
        return None

    delta_amount = actual_amount - quoted_amount
    delta_rate = round(float(delta_amount * Decimal('100') / quoted_amount), 1)
    if delta_amount > 0:
        status = 'over'
        status_label = '실매출 초과'
    elif delta_amount < 0:
        status = 'under'
        status_label = '실매출 미달'
    else:
        status = 'match'
        status_label = '견적 일치'

    return {
        'quoted_amount': quoted_amount,
        'actual_amount': actual_amount,
        'delta_amount': delta_amount,
        'delta_rate': delta_rate,
        'status': status,
        'status_label': status_label,
        'source': quote_reference['source'],
        'number': quote_reference['number'],
        'items': quote_reference.get('items', []),
    }


def _format_signed_money(value):
    amount = int(value or Decimal('0'))
    if amount > 0:
        return f'+{amount:,}원'
    if amount < 0:
        return f'-{abs(amount):,}원'
    return '0원'


def _quote_comparison_template_payload(comparison):
    if not comparison:
        return None
    return {
        'quoted_amount': f"{int(comparison['quoted_amount']):,}원",
        'actual_amount': f"{int(comparison['actual_amount']):,}원",
        'delta_amount': _format_signed_money(comparison['delta_amount']),
        'delta_rate': comparison['delta_rate'],
        'status': comparison['status'],
        'status_label': comparison['status_label'],
        'source': comparison['source'],
        'number': comparison['number'],
    }


def _quote_comparison_api_payload(comparison):
    if not comparison:
        return None
    return {
        'quotedAmount': _money_int(comparison['quoted_amount']),
        'actualAmount': _money_int(comparison['actual_amount']),
        'deltaAmount': _money_int(comparison['delta_amount']),
        'deltaRate': comparison['delta_rate'],
        'status': comparison['status'],
        'statusLabel': comparison['status_label'],
        'source': comparison['source'],
        'number': comparison['number'],
        'items': comparison.get('items', []),
    }


def _actual_delivery_revenue(followup):
    schedules = list(getattr(followup, 'pricing_schedules', []))
    completed_delivery_schedules = [
        schedule
        for schedule in schedules
        if schedule.activity_type == 'delivery' and schedule.status == 'completed'
    ]
    processed_schedule_ids = set()
    delivery_entries = []

    for schedule in completed_delivery_schedules:
        amount = _delivery_schedule_amount(schedule)
        if amount > 0:
            delivery_entries.append({
                'object': schedule,
                'amount': amount,
                'date': schedule.visit_date,
                'number': f'납품 #{schedule.id}',
            })
            processed_schedule_ids.add(schedule.id)

    histories = list(getattr(followup, 'pricing_histories', getattr(followup, 'all_histories', [])))
    for history in histories:
        if history.action_type != 'delivery_schedule':
            continue
        if history.schedule_id and history.schedule_id in processed_schedule_ids:
            continue
        amount = _history_pricing_amount(history)
        if amount > 0:
            delivery_entries.append({
                'object': history,
                'amount': amount,
                'date': _history_pricing_date(history),
                'number': f'활동 #{history.id}',
            })

    selected_entries = _latest_dated_entries(delivery_entries)
    if not selected_entries:
        return Decimal('0'), None, None, 0

    return (
        _sum_entry_amounts(selected_entries),
        selected_entries[0]['object'],
        selected_entries[0]['date'],
        len(selected_entries),
    )


def _select_pipeline_pricing(followup, stage):
    """
    Return the object and amount that should drive the pipeline card value.

    운영 데이터는 Quote 모델뿐 아니라 견적/납품 Schedule의 DeliveryItem과
    납품 History 금액에도 저장된다. 파이프라인 단계별로 실제 업무 소스를 우선한다.
    """
    if stage == 'won':
        amount, delivery_object, basis_date, count = _actual_delivery_revenue(followup)
        if amount > 0:
            if isinstance(delivery_object, Schedule):
                number = f'납품 #{delivery_object.id}'
            elif isinstance(delivery_object, History):
                number = f'활동 #{delivery_object.id}'
            else:
                number = '납품 히스토리'
            if count > 1:
                number = f'{number} 외 {count - 1}건'
            return {
                'object': delivery_object,
                'kind': 'delivery',
                'amount': amount,
                'source': f'실제 납품 매출 {count}건' if count > 1 else '실제 납품 매출',
                'number': number,
                'stage': '완료됨',
                'probability': 100,
                'valid_until': None,
                'basis_date': basis_date,
                'quote_date': None,
                'items': [],
            }

    if stage in ('quote', 'negotiation', 'lost'):
        quote_reference = _select_quote_reference_pricing(followup, stage)
        if quote_reference:
            return quote_reference

    quote_pricing = _quote_model_pricing(followup, stage)
    if quote_pricing:
        return quote_pricing

    return {
        'object': None,
        'kind': '',
        'amount': Decimal('0'),
        'source': '',
        'number': '',
        'stage': '',
        'probability': _pipeline_default_probability(stage),
        'valid_until': None,
        'basis_date': None,
        'quote_date': None,
        'items': [],
    }


def _date_label(target_date, today):
    if not target_date:
        return '일정 없음'
    delta = (target_date - today).days
    if delta == 0:
        return '오늘'
    if delta == 1:
        return '내일'
    if delta == -1:
        return '어제'
    if delta > 1:
        return f'{delta}일 후'
    return f'{abs(delta)}일 지연'


def _money_int(value):
    return int(value or Decimal('0'))


def _pipeline_quote_group_label(value):
    return str(value or '').strip()[:100] or '기본 견적서'


def _pipeline_delivery_item_payload(item, source_label=''):
    effective_unit_price = item.get_effective_unit_price()
    return {
        'id': f'delivery-item-{item.id}',
        'sourceType': 'delivery_item',
        'source': source_label,
        'itemName': item.item_name,
        'productCode': item.product.product_code if item.product_id and item.product else '',
        'quantity': item.quantity,
        'unit': item.unit or '',
        'unitPrice': _money_int(effective_unit_price) if effective_unit_price is not None else None,
        'totalPrice': _money_int(item.total_price),
        'quoteGroup': item.quote_group or '',
        'quoteGroupLabel': _pipeline_quote_group_label(item.quote_group),
        'notes': item.notes or '',
    }


def _pipeline_quote_item_payload(item, source_label=''):
    product = item.product
    return {
        'id': f'quote-item-{item.id}',
        'sourceType': 'quote_item',
        'source': source_label,
        'itemName': product.product_code if product else '품목명 미정',
        'productCode': product.product_code if product else '',
        'quantity': item.quantity,
        'unit': product.unit if product else '',
        'unitPrice': _money_int(item.unit_price),
        'totalPrice': _money_int(item.subtotal),
        'quoteGroup': '',
        'quoteGroupLabel': '기본 견적서',
        'notes': item.description or '',
    }


def _pipeline_schedule_quote_items(schedule, source_label='견적 일정'):
    return [
        _pipeline_delivery_item_payload(item, source_label)
        for item in schedule.delivery_items_set.all()
    ]


def _pipeline_history_quote_items(history, source_label='견적 활동'):
    return [
        _pipeline_delivery_item_payload(item, source_label)
        for item in history.delivery_items_set.all()
    ]


def _pipeline_quote_model_items(quote, source_label='견적서'):
    return [
        _pipeline_quote_item_payload(item, source_label)
        for item in quote.items.all()
    ]


def _attention_score(stage, latest_quote, next_schedule, last_history, has_overdue_action, today):
    score = 0
    reasons = []
    if latest_quote:
        score += 40
        reasons.append('견적 이력')
    if next_schedule:
        days = (next_schedule.visit_date - today).days
        score += 30 if days <= 7 else 15
        reasons.append('예정 일정')
    if last_history:
        score += 15
        reasons.append('최근 활동')
    if has_overdue_action:
        score += 35
        reasons.append('후속 지연')
    if stage in ('quote', 'negotiation'):
        score += 20
        reasons.append('진행 단계')
    return score, ' · '.join(reasons[:3]) if reasons else '추가 활동 필요'


def _pipeline_ai_department_payload(request, followup, user_profile):
    """파이프라인 우측 패널용 부서 AI compact payload."""
    department = followup.department
    can_use_ai = bool(getattr(user_profile, 'can_use_ai', False))
    if not department:
        return {
            'departmentId': None,
            'departmentName': '',
            'companyName': followup.company.name if followup.company else '',
            'canUseAi': can_use_ai,
            'canAnalyze': False,
            'hasAnalysis': False,
            'message': '부서가 지정되지 않았습니다.',
            'summary': '',
            'updatedAt': None,
            'meetingCount': 0,
            'quoteCount': 0,
            'deliveryCount': 0,
            'painpointCount': 0,
            'unverifiedPainpointCount': 0,
            'href': '',
            'hubHref': reverse('ai_chat:department_list') if can_use_ai else '',
            'runHref': '',
        }

    has_own_department_followup = FollowUp.objects.filter(
        user=request.user,
        department=department,
    ).exists()
    can_analyze = can_use_ai and has_own_department_followup
    analysis = None
    painpoint_count = 0
    unverified_painpoint_count = 0

    if can_analyze:
        from ai_chat.models import AIDepartmentAnalysis, PainPointCard
        from .views import (
            _ai_workspace_analysis_summary,
            _customers_ai_result_payload,
            _customers_empty_ai_result_payload,
            _datetime_or_none,
        )

        analysis = AIDepartmentAnalysis.objects.filter(
            user=request.user,
            department=department,
        ).first()
        if analysis:
            painpoint_count = PainPointCard.objects.filter(analysis=analysis).count()
            unverified_painpoint_count = PainPointCard.objects.filter(
                analysis=analysis,
                verification_status='unverified',
            ).count()
            summary = _ai_workspace_analysis_summary(analysis)
            updated_at = _datetime_or_none(analysis.updated_at)
        else:
            summary = ''
            updated_at = None
    else:
        summary = ''
        updated_at = None
        from .views import _customers_empty_ai_result_payload

    if not can_use_ai:
        message = 'AI 기능 사용 권한이 없습니다.'
    elif not has_own_department_followup:
        message = '본인 담당 고객이 있는 부서만 AI 분석할 수 있습니다.'
    elif analysis:
        message = ''
    else:
        message = '아직 부서 AI 분석이 없습니다.'

    result_payload = (
        _customers_ai_result_payload(analysis, can_analyze)
        if analysis and can_analyze
        else _customers_empty_ai_result_payload()
    )

    return {
        'departmentId': department.id,
        'departmentName': department.name,
        'companyName': department.company.name if department.company else (followup.company.name if followup.company else ''),
        'canUseAi': can_use_ai,
        'canAnalyze': can_analyze,
        'hasAnalysis': analysis is not None,
        'message': message,
        'summary': summary,
        'updatedAt': updated_at,
        'meetingCount': analysis.meeting_count if analysis else 0,
        'quoteCount': analysis.quote_count if analysis else 0,
        'deliveryCount': analysis.delivery_count if analysis else 0,
        'painpointCount': painpoint_count,
        'unverifiedPainpointCount': unverified_painpoint_count,
        'href': reverse('ai_chat:department_analysis', args=[department.id]) if can_analyze else '',
        'hubHref': f"{reverse('ai_chat:department_list')}?department={department.id}" if can_use_ai else '',
        'runHref': reverse('ai_chat:run_analysis', args=[department.id]) if can_analyze else '',
        **result_payload,
    }


@readonly_bearer_or_login_required
@require_GET
@ensure_csrf_cookie
def pipeline_command_center_api(request):
    """React 파일럿용 읽기 전용 파이프라인 데이터 API."""
    from datetime import timedelta

    today = timezone.localdate()
    thirty_days_ago = today - timedelta(days=30)

    recent_histories_qs = History.objects.filter(
        parent_history__isnull=True,
    ).filter(
        Q(meeting_date__gte=thirty_days_ago) |
        Q(meeting_date__isnull=True, created_at__date__gte=thirty_days_ago)
    ).order_by('-created_at')
    pricing_histories_qs = History.objects.filter(
        parent_history__isnull=True,
        action_type__in=['quote', 'delivery_schedule'],
    ).prefetch_related('delivery_items_set').order_by('-created_at')
    pricing_schedules_qs = Schedule.objects.filter(
        activity_type__in=['quote', 'delivery'],
    ).prefetch_related(
        'delivery_items_set',
        Prefetch('histories', queryset=pricing_histories_qs, to_attr='pricing_histories'),
    ).order_by('-visit_date', '-created_at')

    followups = (
        _get_accessible_followups(request.user, request)
        .filter(pipeline_hidden=False)
        .select_related('company', 'department', 'user')
        .prefetch_related(
            Prefetch('schedules', queryset=Schedule.objects.filter(
                visit_date__gte=today,
                status='scheduled',
            ).order_by('visit_date', 'visit_time'), to_attr='upcoming_schedules'),
            Prefetch('schedules', queryset=Schedule.objects.filter(
                visit_date__gte=thirty_days_ago,
                visit_date__lte=today,
            ).exclude(status='cancelled').order_by('-visit_date'), to_attr='recent_schedules'),
            Prefetch('schedules', queryset=pricing_schedules_qs, to_attr='pricing_schedules'),
            Prefetch('histories', queryset=History.objects.filter(
                parent_history__isnull=True,
            ).order_by('-created_at'), to_attr='all_histories'),
            Prefetch('histories', queryset=pricing_histories_qs, to_attr='pricing_histories'),
            Prefetch('histories', queryset=recent_histories_qs,
                     to_attr='recent_histories_for_stage'),
            Prefetch('quotes', queryset=Quote.objects.prefetch_related('items__product').order_by('-created_at'),
                     to_attr='all_quotes'),
        )
        .order_by('pipeline_stage', 'company__name', 'customer_name')
    )

    stage_map = {stage_key: [] for stage_key, *_ in PIPELINE_STAGES}
    stage_amounts = {stage_key: Decimal('0') for stage_key, *_ in PIPELINE_STAGES}
    stage_overdue_counts = {stage_key: 0 for stage_key, *_ in PIPELINE_STAGES}
    deals = []
    user_profile = _get_user_profile(request.user)

    for account_followups in _pipeline_account_groups(followups):
        stage = _pipeline_account_stage(account_followups)
        fu = _pipeline_account_followup(account_followups, stage)
        next_schedule = fu.upcoming_schedules[0] if fu.upcoming_schedules else None
        last_history = fu.all_histories[0] if fu.all_histories else None
        pricing = _select_pipeline_pricing(fu, stage)
        pricing_amount = pricing['amount']
        quote_reference = _select_quote_reference_pricing(fu, stage)
        quote_comparison = _build_quote_comparison(stage, pricing, quote_reference)
        probability = pricing['probability']
        if probability is None:
            probability = _pipeline_default_probability(stage)
        next_action_date = last_history.next_action_date if last_history else None
        has_overdue_action = bool(next_action_date and next_action_date < today)
        due_date = next_action_date or (next_schedule.visit_date if next_schedule else None)
        risk = 'high' if has_overdue_action else ('medium' if stage in ('quote', 'negotiation') else 'low')
        next_action = (
            (last_history.next_action or '').strip()
            if last_history and last_history.next_action else
            (f"{next_schedule.get_activity_type_display()} 예정" if next_schedule else '다음 액션 등록 필요')
        )
        last_activity = (
            f"{last_history.get_action_type_display()} · {last_history.created_at.strftime('%m/%d')}"
            if last_history else '최근 활동 없음'
        )
        recent_activities = [
            {
                'type': history.get_action_type_display(),
                'date': history.created_at.strftime('%m/%d'),
                'summary': (history.next_action or history.content or '').strip()[:80],
            }
            for history in getattr(fu, 'all_histories', [])[:3]
        ]
        latest_quote_payload = None
        if pricing['source'] or pricing_amount > 0:
            valid_until = pricing['valid_until']
            basis_date = pricing.get('basis_date')
            quote_date = pricing.get('quote_date')
            latest_quote_payload = {
                'number': pricing['number'],
                'stage': pricing['stage'],
                'amount': _money_int(pricing_amount),
                'probability': int(probability or 0),
                'validUntil': valid_until.isoformat() if valid_until else None,
                'source': pricing['source'],
                'basisType': pricing['kind'],
                'basisDate': basis_date.isoformat() if basis_date else None,
                'quoteDate': quote_date.isoformat() if quote_date else None,
                'items': pricing.get('items', []),
            }
        next_schedule_payload = None
        if next_schedule:
            next_schedule_payload = {
                'id': next_schedule.id,
                'type': next_schedule.get_activity_type_display(),
                'date': next_schedule.visit_date.isoformat(),
                'time': next_schedule.visit_time.strftime('%H:%M') if next_schedule.visit_time else '',
                'location': next_schedule.location or '',
            }
        tags = []
        if pricing['source']:
            tags.append(pricing['source'])
        if has_overdue_action:
            tags.append('후속 지연')
        if fu.customer_grade:
            tags.append(f'{fu.customer_grade} 등급')
        attention_score, attention_reason = _attention_score(
            stage, pricing_amount > 0, next_schedule, last_history, has_overdue_action, today
        )

        deal = {
            'id': fu.id,
            **_pipeline_account_metadata(fu),
            'company': str(fu.company) if fu.company else fu.customer_name or '고객명 미정',
            'contact': _pipeline_contact_label(fu),
            'department': str(fu.department) if fu.department else '',
            'owner': fu.user.get_full_name() or fu.user.username,
            'stage': stage,
            'stageLabel': dict(FollowUp.PIPELINE_STAGE_CHOICES).get(stage, stage),
            'value': _money_int(pricing_amount),
            'probability': int(probability) if probability is not None else None,
            'nextAction': next_action[:80],
            'due': _date_label(due_date, today),
            'risk': risk,
            'tags': tags[:3],
            'lastActivity': last_activity,
            'attentionScore': attention_score,
            'attentionReason': attention_reason,
            'isPotentialOverflow': False,
            'recentActivities': recent_activities,
            'latestQuote': latest_quote_payload,
            'quoteComparison': _quote_comparison_api_payload(quote_comparison),
            'nextSchedule': next_schedule_payload,
            'detailUrl': f'/reporting/followups/{fu.id}/',
            'aiDepartment': _pipeline_ai_department_payload(request, fu, user_profile),
        }
        stage_map[stage].append(deal)
        stage_amounts[stage] += pricing_amount or Decimal('0')
        if has_overdue_action:
            stage_overdue_counts[stage] += 1
        deals.append(deal)

    for potential_index, deal in enumerate(
        sorted(stage_map.get('potential', []), key=lambda item: item['attentionScore'], reverse=True)
    ):
        deal['isPotentialOverflow'] = potential_index >= 10

    for stage_key in stage_map:
        stage_map[stage_key].sort(
            key=lambda item: (item['isPotentialOverflow'], -item['attentionScore'], item['company'])
        )
    deals.sort(key=lambda item: (item['stage'] != 'potential', item['isPotentialOverflow'], -item['attentionScore'], item['company']))

    stages_payload = [
        {
            'id': stage_key,
            'label': label,
            'caption': STAGE_CAPTIONS.get(stage_key, ''),
            'color': color,
            'count': len(stage_map[stage_key]),
            'totalValue': _money_int(stage_amounts[stage_key]),
            'overdueCount': stage_overdue_counts[stage_key],
        }
        for stage_key, label, color, _icon in PIPELINE_STAGES
    ]
    total_value = sum(deal['value'] for deal in deals)
    weighted_value = sum(deal['value'] * ((deal['probability'] or 0) / 100) for deal in deals)
    overdue_count = sum(1 for deal in deals if deal['risk'] == 'high')
    contact_count = sum(1 for deal in deals if deal['stage'] == 'contact')

    # 숨긴 카드(복원 패널용) — 계정(부서) 단위로 대표 하나씩.
    hidden_seen = set()
    hidden_deals = []
    hidden_followups = (
        _get_accessible_followups(request.user, request)
        .filter(pipeline_hidden=True)
        .select_related('company', 'department', 'user')
        .order_by('company__name', 'customer_name')
    )
    for hf in hidden_followups:
        key = f'dept:{hf.department_id}' if hf.department_id else f'fu:{hf.id}'
        if key in hidden_seen:
            continue
        hidden_seen.add(key)
        hidden_deals.append({
            'id': hf.id,
            'company': (hf.company.name if hf.company else '') or (hf.customer_name or ''),
            'department': hf.department.name if hf.department else '',
            'contact': hf.customer_name or '',
            'owner': (hf.user.get_full_name() or hf.user.username) if hf.user else '',
        })

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'stages': stages_payload,
        'deals': deals,
        'hiddenDeals': hidden_deals,
        'metrics': {
            'totalPipelineValue': int(total_value),
            'weightedPipelineValue': int(weighted_value),
            'activeCount': len(deals),
            'overdueCount': overdue_count,
            'contactCount': contact_count,
        },
        'priorityTasks': [
            {'title': '견적 후속 지연 고객', 'count': overdue_count, 'tone': 'danger'},
            {'title': '오늘 연락 필요', 'count': sum(1 for deal in deals if deal['due'] == '오늘'), 'tone': 'warning'},
            {'title': '협상/견적 단계', 'count': sum(1 for deal in deals if deal['stage'] in ('quote', 'negotiation')), 'tone': 'info'},
        ],
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

        if fu.department_id:
            targets = accessible.filter(department_id=fu.department_id)
        else:
            targets = accessible.filter(pk=fu.pk)

        updated_count = targets.update(
            pipeline_stage=new_stage,
            pipeline_manually_set=True,
            updated_at=timezone.now(),
        )
        return JsonResponse({'success': True, 'updatedCount': updated_count})
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


@login_required
@require_POST
def funnel_pipeline_hide(request):
    """카드를 파이프라인 보드에서 숨김(데이터 보존, 복원 가능). 부서 그룹 전체 적용."""
    return _funnel_pipeline_set_hidden(request, True)


@login_required
@require_POST
def funnel_pipeline_unhide(request):
    """숨긴 카드를 파이프라인 보드에 복원. 부서 그룹 전체 적용."""
    return _funnel_pipeline_set_hidden(request, False)


def _funnel_pipeline_set_hidden(request, hidden):
    try:
        profile = _get_user_profile(request.user)
        if profile.is_manager():
            return JsonResponse(
                {'success': False, 'error': '권한이 없습니다. Manager는 파이프라인 카드를 변경할 수 없습니다.'},
                status=403,
            )
        data = json.loads(request.body)
        followup_id = data.get('followup_id')

        accessible = _get_accessible_followups(request.user, request)
        fu = accessible.filter(pk=followup_id).first()
        if not fu:
            return JsonResponse({'success': False, 'error': '권한 없음'}, status=403)

        if fu.department_id:
            targets = accessible.filter(department_id=fu.department_id)
        else:
            targets = accessible.filter(pk=fu.pk)

        updated_count = targets.update(pipeline_hidden=hidden, updated_at=timezone.now())
        return JsonResponse({'success': True, 'updatedCount': updated_count, 'hidden': hidden})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

