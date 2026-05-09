"""
AI 부서 분석 - Views
부서 목록, 분석 실행, 결과 조회, PainPoint 검증
"""
import logging
import re
from collections import defaultdict
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from reporting.models import FollowUp, Department
from .models import AIDepartmentAnalysis, PainPointCard, AIFollowUpAnalysis
from .department_prompt import (
    build_prompt_from_department_analysis,
    summarize_department_analysis,
    suggest_goals_from_department_analysis,
)

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
    """AI 부서분석 기반 프롬프트 생성 허브"""
    # 사용자의 팔로우업에서 부서 목록과 검색용 고객명을 한 번에 추출한다.
    followup_rows = list(FollowUp.objects.filter(
        user=request.user,
        department__isnull=False
    ).values('department_id', 'customer_name').order_by('department_id', 'customer_name'))

    customer_names_by_department = defaultdict(list)
    followup_counts_by_department = defaultdict(int)
    for row in followup_rows:
        department_id = row['department_id']
        followup_counts_by_department[department_id] += 1
        if row['customer_name']:
            customer_names_by_department[department_id].append(row['customer_name'])

    department_ids = list(followup_counts_by_department.keys())
    departments = list(Department.objects.filter(
        id__in=department_ids
    ).select_related('company').order_by('company__name', 'name'))
    department_map = {department.id: department for department in departments}

    # 기존 분석 정보
    analyses = AIDepartmentAnalysis.objects.filter(
        user=request.user,
        department_id__in=department_ids
    )
    analysis_map = {a.department_id: a for a in analyses}

    selected_department = None
    selected_analysis = None
    analysis_summary = None
    goal_cards = []
    generated_prompt = ''
    selected_goal = ''
    custom_goal = ''
    prompt_error = ''

    selected_department_id = request.POST.get('department_id') or request.GET.get('department')
    allowed_department_ids = set(department_map.keys())

    if selected_department_id:
        try:
            selected_department_id = int(selected_department_id)
        except (TypeError, ValueError):
            selected_department_id = None

    if selected_department_id and selected_department_id in allowed_department_ids:
        selected_department = department_map.get(selected_department_id)
        selected_analysis = analysis_map.get(selected_department_id)
    elif selected_department_id:
        from django.contrib import messages
        messages.error(request, '해당 부서에 접근 권한이 없습니다.')

    if selected_analysis:
        analysis_summary = summarize_department_analysis(selected_analysis)
        goal_cards = suggest_goals_from_department_analysis(selected_analysis)

    if request.method == 'POST':
        selected_goal = (request.POST.get('selected_goal') or '').strip()
        custom_goal = (request.POST.get('custom_goal') or '').strip()

        if not selected_department:
            prompt_error = '프롬프트를 생성할 부서를 선택하세요.'
        elif not selected_analysis:
            prompt_error = '먼저 부서 분석을 실행해야 프롬프트를 생성할 수 있습니다.'
        elif not selected_goal and not custom_goal:
            prompt_error = '목표 카드를 선택하거나 직접 목표를 한 문장으로 입력하세요.'
        else:
            try:
                generated_prompt = build_prompt_from_department_analysis(
                    selected_analysis,
                    selected_goal=selected_goal,
                    custom_goal=custom_goal,
                )
            except ValueError as exc:
                prompt_error = str(exc)

    dept_data = []
    for dept in departments:
        analysis = analysis_map.get(dept.id)
        customer_names = customer_names_by_department.get(dept.id, [])
        dept_data.append({
            'department': dept,
            'analysis': analysis,
            'followup_count': followup_counts_by_department.get(dept.id, 0),
            'has_analysis': analysis is not None,
            'customer_names': customer_names,
            'is_selected': selected_department is not None and dept.id == selected_department.id,
        })

    return render(request, 'ai_chat/department_list.html', {
        'dept_data': dept_data,
        'selected_department': selected_department,
        'selected_analysis': selected_analysis,
        'analysis_summary': analysis_summary,
        'goal_cards': goal_cards,
        'generated_prompt': generated_prompt,
        'selected_goal': selected_goal,
        'custom_goal': custom_goal,
        'prompt_error': prompt_error,
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
    from .services import analyze_department, collect_painpoint_verification_memory, gather_meeting_data

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

        verification_memory = analysis_result.get('verification_memory')
        if not isinstance(verification_memory, list):
            verification_memory = collect_painpoint_verification_memory(analysis)
        analysis_result['verification_memory'] = verification_memory

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

        # 검증 완료/부정 카드는 메모리로 보존하고, 미검증 카드만 새 분석 결과로 교체한다.
        preserved_cards = analysis.painpoint_cards.exclude(verification_status='unverified').count()
        analysis.painpoint_cards.filter(verification_status='unverified').delete()
        created_cards = []
        if 'painpoint_cards' in analysis_result:
            created_cards = _save_painpoint_cards(
                analysis_result['painpoint_cards'],
                analysis,
                verification_memory=verification_memory,
            )

        return JsonResponse({
            'success': True,
            'redirect_url': f'/ai/department/{department.id}/',
            'cards_created': len(created_cards),
            'cards_preserved': preserved_cards,
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

def _normalize_painpoint_memory_text(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip().lower()


def _painpoint_memory_key(category, hypothesis, verification_question):
    return '|'.join([
        _normalize_painpoint_memory_text(category),
        _normalize_painpoint_memory_text(hypothesis)[:180],
        _normalize_painpoint_memory_text(verification_question)[:140],
    ])


def _painpoint_card_matches_memory(card_data, verification_memory):
    """이미 검증/부정된 가설과 같은 카드를 재생성하지 않도록 거른다."""
    if not verification_memory:
        return False

    category = card_data.get('category', '')
    hypothesis = card_data.get('hypothesis', '')
    question = card_data.get('verification_question', '')
    candidate_key = _painpoint_memory_key(category, hypothesis, question)
    candidate_hypothesis = _normalize_painpoint_memory_text(hypothesis)
    candidate_question = _normalize_painpoint_memory_text(question)

    for item in verification_memory:
        if not isinstance(item, dict):
            continue
        memory_status = item.get('verification_status') or item.get('verificationStatus') or ''
        if memory_status not in ('confirmed', 'denied'):
            continue

        memory_category = item.get('category', '')
        memory_hypothesis = item.get('hypothesis', '')
        memory_question = item.get('verification_question') or item.get('verificationQuestion') or ''
        memory_key = _painpoint_memory_key(memory_category, memory_hypothesis, memory_question)
        if candidate_key == memory_key:
            return True

        normalized_memory_hypothesis = _normalize_painpoint_memory_text(memory_hypothesis)
        normalized_memory_question = _normalize_painpoint_memory_text(memory_question)
        same_category = _normalize_painpoint_memory_text(category) == _normalize_painpoint_memory_text(memory_category)
        same_hypothesis = (
            candidate_hypothesis
            and normalized_memory_hypothesis
            and (
                candidate_hypothesis in normalized_memory_hypothesis
                or normalized_memory_hypothesis in candidate_hypothesis
            )
        )
        same_question = (
            candidate_question
            and normalized_memory_question
            and (
                candidate_question in normalized_memory_question
                or normalized_memory_question in candidate_question
            )
        )
        if same_category and (same_hypothesis or same_question):
            return True

    return False


def _save_painpoint_cards(cards_data, analysis, verification_memory=None):
    """JSON에서 PainPoint 카드 파싱 후 DB 저장"""
    valid_categories = dict(PainPointCard.CATEGORY_CHOICES).keys()
    valid_confidences = dict(PainPointCard.CONFIDENCE_CHOICES).keys()
    valid_attributions = dict(PainPointCard.ATTRIBUTION_CHOICES).keys()

    created_cards = []
    for card_data in cards_data:
        try:
            if _painpoint_card_matches_memory(card_data, verification_memory or []):
                logger.info("검증 메모리와 중복되는 PainPoint 카드 저장 생략: %s", card_data.get('hypothesis', '')[:80])
                continue

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



# ================================================
# 개별 고객(FollowUp) AI 분석
# ================================================

@login_required
@ai_permission_required
def followup_analysis_view(request, followup_id):
    """개별 고객 AI 분석 결과 뷰"""
    from reporting.views import can_access_followup
    followup = get_object_or_404(FollowUp, id=followup_id)

    if not can_access_followup(request.user, followup):
        from django.contrib import messages
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:followup_list')

    analysis = AIFollowUpAnalysis.objects.filter(
        followup=followup, user=request.user
    ).first()

    return render(request, 'ai_chat/followup_analysis.html', {
        'followup': followup,
        'analysis': analysis,
    })


@login_required
@ai_permission_required
@require_POST
def run_followup_analysis(request, followup_id):
    """개별 고객 AI 분석 실행 (AJAX POST)"""
    from reporting.views import can_access_followup
    from .services import analyze_followup

    followup = get_object_or_404(FollowUp, id=followup_id)

    if not can_access_followup(request.user, followup):
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)

    try:
        analysis, created = AIFollowUpAnalysis.objects.get_or_create(
            followup=followup,
            user=request.user,
        )

        analysis_result, meeting_count, token_usage = analyze_followup(
            analysis, followup, request.user
        )

        if not analysis_result:
            return JsonResponse({'error': 'AI 분석 결과를 파싱하지 못했습니다.'}, status=500)

        analysis.analysis_data = analysis_result
        analysis.meeting_count = meeting_count
        analysis.token_usage = token_usage
        analysis.save()

        return JsonResponse({
            'success': True,
            'redirect_url': '/ai/followup/{}/'.format(followup_id),
        })

    except Exception as e:
        logger.error('FollowUp AI 분석 실패: {}'.format(str(e)))
        return JsonResponse({'error': 'AI 분석 실패: {}'.format(str(e))}, status=500)


@login_required
@ai_permission_required
@require_POST
def delete_followup_analysis(request, followup_id):
    """개별 고객 분석 삭제"""
    analysis = get_object_or_404(
        AIFollowUpAnalysis,
        followup_id=followup_id,
        user=request.user,
    )
    analysis.delete()
    return JsonResponse({'success': True})
