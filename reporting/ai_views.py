"""
AI 기능 관련 뷰
- 이메일 자동 생성
- 이메일 변환
- 고객 요약
- 고객 등급 업데이트
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from reporting.ai_utils import (
    generate_email,
    transform_email,
    generate_customer_summary,
    update_customer_grade_with_ai,
    analyze_email_sentiment,
    recommend_products,
    summarize_meeting_notes,
    analyze_email_thread,
    check_ai_permission
)
from reporting.models import FollowUp, Schedule

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def ai_generate_email(request):
    """
    AI로 이메일 자동 생성
    POST 파라미터:
    - purpose: 'compose' 또는 'reply'
    - tone: 'formal', 'casual', 'simple'
    - schedule_id: 일정 ID (선택)
    - customer_name: 고객명
    - company_name: 회사명
    - product: 제품/서비스
    - notes: 추가 메모
    - original_subject: 원본 제목 (답장시)
    - original_body: 원본 내용 (답장시)
    """
    try:
        # AI 권한 체크
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다. 관리자에게 문의하세요.'
            }, status=403)
        
        data = json.loads(request.body)
        purpose = data.get('purpose', 'compose')
        tone = data.get('tone', 'formal')
        
        context = {
            'customer_name': data.get('customer_name', ''),
            'company_name': data.get('company_name', ''),
            'product': data.get('product', ''),
            'schedule_content': data.get('schedule_content', ''),
            'notes': data.get('notes', ''),
        }
        
        if purpose == 'reply':
            context['original_subject'] = data.get('original_subject', '')
            context['original_body'] = data.get('original_body', '')
            context['reply_points'] = data.get('reply_points', '')
        
        result = generate_email(purpose, context, tone, request.user)
        
        return JsonResponse({
            'success': True,
            'subject': result.get('subject', ''),
            'body': result.get('body', '')
        })
    
    except PermissionError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    
    except Exception as e:
        logger.error(f"Error generating email with AI: {e}")
        return JsonResponse({
            'success': False,
            'error': f'이메일 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_transform_email(request):
    """
    AI로 이메일 톤 변환
    POST 파라미터:
    - content: 원본 이메일 내용
    - tone: 'formal', 'casual', 'simple'
    - instructions: 추가 지시사항 (선택)
    """
    try:
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        data = json.loads(request.body)
        content = data.get('content', '')
        tone = data.get('tone', 'formal')
        instructions = data.get('instructions', '')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': '변환할 내용을 입력해주세요.'
            }, status=400)
        
        result = transform_email(content, tone, instructions, request.user)
        
        return JsonResponse({
            'success': True,
            'body': result
        })
    
    except Exception as e:
        logger.error(f"Error transforming email: {e}")
        return JsonResponse({
            'success': False,
            'error': f'이메일 변환 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_generate_customer_summary(request, followup_id):
    """
    AI로 고객 요약 리포트 생성
    """
    try:
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        from django.db.models import Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        from reporting.models import OpportunityTracking, EmailLog
        
        followup = FollowUp.objects.get(id=followup_id)
        
        # 최근 6개월 데이터
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # 스케줄 통계
        schedules = Schedule.objects.filter(
            followup=followup,
            visit_date__gte=six_months_ago
        )
        meeting_count = schedules.filter(activity_type='customer_meeting').count()
        quote_count = schedules.filter(activity_type='quote').count()
        
        # 구매 내역 (납품 일정)
        delivery_schedules = schedules.filter(activity_type='delivery')
        purchase_count = delivery_schedules.count()
        
        # 납품 금액 합계
        total_purchase = delivery_schedules.aggregate(
            total=Sum('expected_revenue')
        )['total'] or 0
        
        # 이메일 교환
        email_count = EmailLog.objects.filter(
            Q(schedule__followup=followup) | Q(followup=followup),
            created_at__gte=six_months_ago
        ).count()
        
        # 마지막 연락일
        last_contact = '정보 없음'
        last_schedule = schedules.order_by('-visit_date').first()
        if last_schedule:
            last_contact = last_schedule.visit_date.strftime('%Y-%m-%d')
        
        # 미팅 노트 수집 (최근 5개) - 히스토리에서
        from reporting.models import History
        histories = History.objects.filter(
            followup=followup,
            created_at__gte=six_months_ago
        )
        meeting_notes = []
        recent_meetings = histories.filter(
            action_type='customer_meeting'
        ).order_by('-created_at')[:5]
        for h in recent_meetings:
            if h.content:
                meeting_notes.append(f"[{h.created_at.strftime('%Y-%m-%d')}] {h.content[:200]}")
        
        # 견적 내역
        quotes = []
        quote_schedules = schedules.filter(activity_type='quote').order_by('-visit_date')[:5]
        for sch in quote_schedules:
            quotes.append({
                'date': sch.visit_date.strftime('%Y-%m-%d'),
                'content': sch.notes or '견적 요청'
            })
        
        # 고객 등급
        customer_grade = '미분류'
        if hasattr(followup, 'customer_grade') and followup.customer_grade:
            customer_grade = followup.get_customer_grade_display()
        
        # 선결제 정보 (있는 경우만)
        from reporting.models import Prepayment
        prepayments = Prepayment.objects.filter(
            customer=followup,
            status='active'
        ).order_by('-payment_date')
        
        prepayment_info = None
        if prepayments.exists():
            total_balance = sum(p.balance for p in prepayments)
            prepayment_info = {
                'total_balance': total_balance,
                'count': prepayments.count(),
                'details': [{
                    'date': p.payment_date.strftime('%Y-%m-%d'),
                    'amount': p.amount,
                    'balance': p.balance,
                    'memo': p.memo
                } for p in prepayments[:3]]  # 최근 3건만
            }
        
        customer_data = {
            'name': followup.customer_name or '고객명 미정',
            'company': followup.company or '업체명 미정',
            'industry': '과학/실험실',
            'meeting_count': meeting_count,
            'quote_count': quote_count,
            'purchase_count': purchase_count,
            'total_purchase': total_purchase,
            'last_contact': last_contact,
            'quotes': quotes,
            'meeting_notes': meeting_notes,
            'email_count': email_count,
            'customer_grade': customer_grade,
            'prepayment': prepayment_info,  # 선결제 정보 추가
        }
        
        summary = generate_customer_summary(customer_data, request.user)
        
        return JsonResponse({
            'success': True,
            'summary': summary
        })
    
    except FollowUp.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '고객을 찾을 수 없습니다.'
        }, status=404)
    
    except Exception as e:
        import traceback
        logger.error(f"Error generating customer summary: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'요약 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_update_customer_grade(request, followup_id):
    """
    AI로 고객 등급 자동 업데이트
    """
    try:
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        from django.db.models import Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        from reporting.models import History, OpportunityTracking, EmailLog
        
        followup = FollowUp.objects.get(id=followup_id)
        
        # 최근 6개월 데이터
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # 스케줄 통계
        schedules = Schedule.objects.filter(
            followup=followup,
            visit_date__gte=six_months_ago
        )
        meeting_count = schedules.filter(activity_type='customer_meeting').count()
        quote_count = schedules.filter(activity_type='quote').count()
        
        # 히스토리 통계
        histories = History.objects.filter(
            followup=followup,
            created_at__gte=six_months_ago
        )
        
        # 구매 내역 (납품 일정)
        purchase_histories = histories.filter(action_type='delivery_schedule')
        purchase_count = purchase_histories.count()
        total_purchase = purchase_histories.aggregate(
            total=Sum('delivery_amount')
        )['total'] or 0
        
        # 이메일 교환
        email_count = EmailLog.objects.filter(
            Q(schedule__followup=followup) | Q(followup=followup),
            created_at__gte=six_months_ago
        ).count()
        
        # 마지막 연락일
        last_contact = '정보 없음'
        last_schedule = schedules.order_by('-visit_date').first()
        if last_schedule:
            last_contact = last_schedule.visit_date.strftime('%Y-%m-%d')
        
        # 미팅 노트
        meeting_summary = ''
        recent_meeting = histories.filter(action_type='customer_meeting').order_by('-created_at').first()
        if recent_meeting and recent_meeting.content:
            meeting_summary = recent_meeting.content[:200]
        
        # 진행 중인 기회
        opportunities = []
        active_opps = OpportunityTracking.objects.filter(
            followup=followup,
            current_stage__in=['lead', 'contact', 'quote', 'closing']
        )[:5]
        for opp in active_opps:
            opportunities.append({
                'stage': opp.get_current_stage_display(),
                'content': opp.title or '영업 기회'
            })
        
        customer_data = {
            'name': followup.customer_name or '고객명 미정',
            'company': followup.company or '업체명 미정',
            'meeting_count': meeting_count,
            'email_count': email_count,
            'quote_count': quote_count,
            'purchase_count': purchase_count,
            'total_purchase': total_purchase,
            'last_contact': last_contact,
            'avg_response_time': '알 수 없음',
            'email_sentiment': '중립',
            'meeting_summary': meeting_summary,
            'opportunities': opportunities,
        }
        
        result = update_customer_grade_with_ai(customer_data, request.user)
        
        # 고객 등급 업데이트 (실제 적용은 사용자 확인 후)
        return JsonResponse({
            'success': True,
            'grade': result.get('grade'),
            'score': result.get('score'),
            'reasoning': result.get('reasoning'),
            'factors': result.get('factors'),
            'recommendations': result.get('recommendations', [])
        })
    
    except FollowUp.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '고객을 찾을 수 없습니다.'
        }, status=404)
    
    except Exception as e:
        import traceback
        logger.error(f"Error updating customer grade: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'등급 업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)
