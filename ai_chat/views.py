"""
AI 부서 분석 - Views
부서 목록, 분석 실행, 결과 조회, PainPoint 검증
"""
import json
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from reporting.models import FollowUp, Department
from .models import AIDepartmentAnalysis, PainPointCard
from .services import analyze_department, gather_meeting_data, gather_quote_delivery_data

logger = logging.getLogger(__name__)


def ai_permission_required(view_func):
    """can_use_ai 권한 체크 데코레이터"""
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or not profile.can_use_ai:
            from django.contrib import messages
            messages.error(request, 'AI 기능 사용 권한이 없습니다. 관리자에게 문의하세요.')
            return redirect('reporting:dashboard')
        return view_func(request, *args, **kwargs)
    _wrapped.__name__ = view_func.__name__
    return _wrapped


# ================================================
# 부서 목록 (분석 대상 선택)
# ================================================

@login_required
@ai_permission_required
def department_list(request):
    """내 팔로우업이 있는 부서 목록"""
    # 사용자의 팔로우업에서 부서 목록 추출
    department_ids = FollowUp.objects.filter(
        user=request.user,
        department__isnull=False
    ).values_list('department_id', flat=True).distinct()

    departments = Department.objects.filter(
        id__in=department_ids
    ).select_related('company').order_by('company__name', 'name')

    # 기존 분석 정보
    analyses = AIDepartmentAnalysis.objects.filter(
        user=request.user,
        department__in=departments
    )
    analysis_map = {a.department_id: a for a in analyses}

    dept_data = []
    for dept in departments:
        analysis = analysis_map.get(dept.id)
        followup_count = FollowUp.objects.filter(
            user=request.user, department=dept
        ).count()
        dept_data.append({
            'department': dept,
            'analysis': analysis,
            'followup_count': followup_count,
            'has_analysis': analysis is not None,
        })

    return render(request, 'ai_chat/department_list.html', {
        'dept_data': dept_data,
    })


# ================================================
# 부서 분석 결과 조회
# ================================================

@login_required
@ai_permission_required
def department_analysis(request, department_id):
    """부서 분석 결과 상세 뷰"""
    department = get_object_or_404(Department, id=department_id)

    # 사용자에게 해당 부서 팔로우업이 있는지 확인
    has_followups = FollowUp.objects.filter(
        user=request.user, department=department
    ).exists()
    if not has_followups:
        from django.contrib import messages
        messages.error(request, '해당 부서에 접근 권한이 없습니다.')
        return redirect('ai_chat:department_list')

    analysis = AIDepartmentAnalysis.objects.filter(
        user=request.user, department=department
    ).first()

    cards = []
    if analysis:
        cards = analysis.painpoint_cards.order_by('-confidence_score')

    return render(request, 'ai_chat/department_analysis.html', {
        'department': department,
        'analysis': analysis,
        'cards': cards,
    })


# ================================================
# 분석 실행 (POST)
# ================================================

@login_required
@ai_permission_required
@require_POST
def run_analysis(request, department_id):
    """부서 AI 분석 실행 (새로 생성 또는 재분석)"""
    department = get_object_or_404(Department, id=department_id)

    # 권한 확인
    has_followups = FollowUp.objects.filter(
        user=request.user, department=department
    ).exists()
    if not has_followups:
        return JsonResponse({'error': '해당 부서에 접근 권한이 없습니다.'}, status=403)

    try:
        # 기존 분석 가져오기 또는 새로 생성
        analysis, created = AIDepartmentAnalysis.objects.get_or_create(
            user=request.user,
            department=department,
        )

        # AI 분석 실행
        analysis_result, qd_data, token_usage = analyze_department(
            analysis, department, request.user
        )

        if not analysis_result:
            return JsonResponse({'error': 'AI 분석 결과를 파싱하지 못했습니다.'}, status=500)

        # 분석 기간 계산
        period_end = timezone.now().date()
        period_start = period_end - timedelta(days=180)

        # 분석 결과 저장
        analysis.analysis_data = analysis_result
        analysis.quote_delivery_data = qd_data['summary']
        analysis.meeting_count = len(gather_meeting_data(department, request.user))
        analysis.quote_count = qd_data['summary']['total_quotes']
        analysis.delivery_count = qd_data['summary']['total_deliveries']
        analysis.analysis_period_start = period_start
        analysis.analysis_period_end = period_end
        analysis.token_usage = token_usage
        analysis.save()

        # 기존 PainPoint 카드 삭제 후 새로 생성
        analysis.painpoint_cards.all().delete()
        if 'painpoint_cards' in analysis_result:
            _save_painpoint_cards(analysis_result['painpoint_cards'], analysis)

        return JsonResponse({
            'success': True,
            'redirect_url': f'/ai/department/{department.id}/',
            'cards_created': len(analysis_result.get('painpoint_cards', [])),
        })

    except Exception as e:
        logger.error(f"부서 분석 실패: {str(e)}")
        return JsonResponse({'error': f'AI 분석 실패: {str(e)}'}, status=500)


# ================================================
# PainPoint 카드 검증
# ================================================

@login_required
@ai_permission_required
@require_POST
def verify_card(request, card_id):
    """PainPoint 카드 검증 상태 업데이트"""
    card = get_object_or_404(PainPointCard, id=card_id, analysis__user=request.user)

    status = request.POST.get('status', '')
    note = request.POST.get('note', '')

    if status not in ('confirmed', 'denied'):
        return JsonResponse({'error': '유효한 상태를 선택하세요. (confirmed/denied)'}, status=400)

    card.verification_status = status
    card.verification_note = note
    card.verified_at = timezone.now()
    card.save(update_fields=['verification_status', 'verification_note', 'verified_at'])

    return JsonResponse({
        'success': True,
        'card_id': card.id,
        'status': card.get_verification_status_display(),
    })


# ================================================
# 분석 삭제
# ================================================

@login_required
@ai_permission_required
@require_POST
def delete_analysis(request, department_id):
    """부서 분석 삭제"""
    analysis = get_object_or_404(
        AIDepartmentAnalysis,
        department_id=department_id,
        user=request.user
    )
    analysis.delete()
    return JsonResponse({'success': True})


# ================================================
# FollowUp에서 부서 분석으로 이동
# ================================================

@login_required
@ai_permission_required
def start_analysis(request, followup_id):
    """FollowUp에서 해당 부서의 AI 분석 페이지로 이동"""
    followup = get_object_or_404(FollowUp, id=followup_id)

    if not followup.department:
        from django.contrib import messages
        messages.warning(request, '부서가 지정되지 않은 팔로우업입니다.')
        return redirect('ai_chat:department_list')

    return redirect('ai_chat:department_analysis', department_id=followup.department.id)


# ================================================
# 유틸: PainPoint 카드 저장
# ================================================

def _save_painpoint_cards(cards_data, analysis):
    """JSON에서 PainPoint 카드 파싱 후 DB 저장"""
    valid_categories = dict(PainPointCard.CATEGORY_CHOICES).keys()
    valid_confidences = dict(PainPointCard.CONFIDENCE_CHOICES).keys()
    valid_attributions = dict(PainPointCard.ATTRIBUTION_CHOICES).keys()

    created_cards = []
    for card_data in cards_data:
        try:
            category = card_data.get('category', '')
            if category not in valid_categories:
                logger.warning(f"잘못된 카테고리: {category}")
                continue

            confidence = card_data.get('confidence', 'low')
            if confidence not in valid_confidences:
                confidence = 'low'

            attribution = card_data.get('attribution', 'individual')
            if attribution not in valid_attributions:
                attribution = 'individual'

            card = PainPointCard.objects.create(
                analysis=analysis,
                category=category,
                hypothesis=card_data.get('hypothesis', ''),
                confidence=confidence,
                confidence_score=int(card_data.get('confidence_score', 50)),
                evidence=card_data.get('evidence', []),
                attribution=attribution,
                verification_question=card_data.get('verification_question', ''),
                action_if_yes=card_data.get('action_if_yes', ''),
                action_if_no=card_data.get('action_if_no', ''),
                caution=card_data.get('caution', ''),
            )
            created_cards.append(card)
        except Exception as e:
            logger.error(f"PainPoint 카드 저장 실패: {str(e)}, data={card_data}")
            continue

    return created_cards
