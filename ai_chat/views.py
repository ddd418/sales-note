"""
AI PainPoint 생성기 - Views
채팅방 관리, 메시지 전송, PainPoint 검증
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import IntegrityError

from reporting.models import FollowUp, History
from .models import AIChatRoom, AIChatMessage, PainPointCard
from .services import analyze_meeting, chat_with_ai

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
# 채팅방 목록
# ================================================

@login_required
@ai_permission_required
def room_list(request):
    """내 AI 채팅방 목록"""
    rooms = AIChatRoom.objects.filter(
        user=request.user
    ).select_related('followup', 'followup__company', 'followup__department')

    # 각 방의 최근 메시지, 미검증 카드 수
    room_data = []
    for room in rooms:
        last_msg = room.messages.order_by('-created_at').first()
        unverified_count = room.painpoint_cards.filter(verification_status='unverified').count()
        room_data.append({
            'room': room,
            'last_message': last_msg,
            'unverified_count': unverified_count,
        })

    # 새 채팅방 생성을 위한 팔로우업 목록 (이미 방이 있는 것 제외)
    existing_followup_ids = AIChatRoom.objects.filter(
        user=request.user
    ).values_list('followup_id', flat=True)
    
    available_followups = FollowUp.objects.filter(
        user=request.user
    ).exclude(
        id__in=existing_followup_ids
    ).select_related('company', 'department').order_by('company__name', 'customer_name')

    return render(request, 'ai_chat/room_list.html', {
        'room_data': room_data,
        'available_followups': available_followups,
    })


# ================================================
# 채팅방 상세 (대화 UI)
# ================================================

@login_required
@ai_permission_required
def room_detail(request, room_id):
    """채팅방 대화 뷰"""
    room = get_object_or_404(AIChatRoom, id=room_id, user=request.user)
    messages_qs = room.messages.order_by('created_at')
    cards = room.painpoint_cards.order_by('-confidence_score')

    # History(미팅록) 목록 - 분석 가능한 것들
    histories = History.objects.filter(
        followup=room.followup,
        action_type='customer_meeting'
    ).order_by('-created_at')[:20]

    return render(request, 'ai_chat/room_detail.html', {
        'room': room,
        'messages': messages_qs,
        'cards': cards,
        'histories': histories,
    })


# ================================================
# 메시지 전송 (자유 채팅)
# ================================================

@login_required
@ai_permission_required
@require_POST
def send_message(request, room_id):
    """채팅 메시지 전송 → AI 응답"""
    room = get_object_or_404(AIChatRoom, id=room_id, user=request.user)
    user_text = request.POST.get('message', '').strip()

    if not user_text:
        return JsonResponse({'error': '메시지를 입력하세요.'}, status=400)

    # 사용자 메시지 저장
    user_msg = AIChatMessage.objects.create(
        room=room,
        role='user',
        content=user_text,
    )

    try:
        ai_text, structured, token_usage = chat_with_ai(room, user_text)

        # AI 응답 저장
        ai_msg = AIChatMessage.objects.create(
            room=room,
            role='assistant',
            content=ai_text,
            structured_data=structured,
            token_usage=token_usage,
        )

        # 구조화 데이터에서 PainPoint 카드 추출
        cards_created = []
        if structured and 'painpoint_cards' in structured:
            cards_created = _save_painpoint_cards(structured['painpoint_cards'], ai_msg, room)

        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])

        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.strftime('%H:%M'),
            },
            'ai_message': {
                'id': ai_msg.id,
                'content': ai_text,
                'structured_data': structured,
                'token_usage': token_usage,
                'created_at': ai_msg.created_at.strftime('%H:%M'),
            },
            'cards_created': len(cards_created),
        })

    except Exception as e:
        logger.error(f"AI 응답 생성 실패: {str(e)}")
        return JsonResponse({'error': f'AI 응답 생성 실패: {str(e)}'}, status=500)


# ================================================
# 미팅록(History)에서 분석 시작
# ================================================

@login_required
@ai_permission_required
@require_POST
def analyze_history(request, history_id):
    """특정 미팅록을 AI로 분석"""
    history = get_object_or_404(
        History, id=history_id, action_type='customer_meeting'
    )

    if not history.followup:
        return JsonResponse({'error': '팔로우업이 연결되지 않은 히스토리입니다.'}, status=400)

    # 채팅방 가져오기 (없으면 생성)
    room, created = AIChatRoom.objects.get_or_create(
        user=request.user,
        followup=history.followup,
        defaults={
            'title': f"{history.followup.customer_name} - AI 분석"
        }
    )

    # 미팅록 데이터 조립
    meeting_data = {
        'situation': history.meeting_situation or '',
        'researcher_quote': history.meeting_researcher_quote or '',
        'confirmed_facts': history.meeting_confirmed_facts or '',
        'obstacles': history.meeting_obstacles or '',
        'next_action': history.meeting_next_action or '',
        'free_text': history.content or '',
        'channel': '방문',
        'visit_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else history.created_at.strftime('%Y-%m-%d'),
    }

    # 사용자 메시지 기록
    summary_text = f"미팅록 분석 요청 (일자: {meeting_data['visit_date']})"
    user_msg = AIChatMessage.objects.create(
        room=room,
        role='user',
        content=summary_text,
        source_history=history,
    )

    try:
        ai_text, structured, token_usage = analyze_meeting(room, meeting_data, history.followup)

        # AI 응답 저장
        ai_msg = AIChatMessage.objects.create(
            room=room,
            role='assistant',
            content=ai_text,
            structured_data=structured,
            source_history=history,
            token_usage=token_usage,
        )

        # PainPoint 카드 추출/저장
        cards_created = []
        if structured and 'painpoint_cards' in structured:
            cards_created = _save_painpoint_cards(structured['painpoint_cards'], ai_msg, room)

        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])

        return JsonResponse({
            'success': True,
            'room_id': room.id,
            'redirect_url': f'/ai/room/{room.id}/',
            'cards_created': len(cards_created),
        })

    except Exception as e:
        logger.error(f"미팅록 분석 실패: {str(e)}")
        return JsonResponse({'error': f'AI 분석 실패: {str(e)}'}, status=500)


# ================================================
# PainPoint 카드 검증
# ================================================

@login_required
@ai_permission_required
@require_POST
def verify_card(request, card_id):
    """PainPoint 카드 검증 상태 업데이트"""
    card = get_object_or_404(PainPointCard, id=card_id, room__user=request.user)

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
# FollowUp에서 채팅방 시작/이동
# ================================================

@login_required
@ai_permission_required
def start_chat(request, followup_id):
    """FollowUp에서 AI 채팅 시작 (방이 없으면 생성, 있으면 이동)"""
    followup = get_object_or_404(FollowUp, id=followup_id)

    room, created = AIChatRoom.objects.get_or_create(
        user=request.user,
        followup=followup,
        defaults={
            'title': f"{followup.customer_name} - AI 분석"
        }
    )

    return redirect('ai_chat:room_detail', room_id=room.id)


# ================================================
# 채팅방 삭제
# ================================================

@login_required
@ai_permission_required
@require_POST
def room_delete(request, room_id):
    """AI 채팅방 삭제 (본인 소유만)"""
    room = get_object_or_404(AIChatRoom, id=room_id, user=request.user)
    room.delete()
    return JsonResponse({'success': True})


# ================================================
# 유틸: PainPoint 카드 저장
# ================================================

def _save_painpoint_cards(cards_data, ai_message, room):
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
                message=ai_message,
                room=room,
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
