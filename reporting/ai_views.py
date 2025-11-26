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
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
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
    natural_language_search,
    check_ai_permission,
    suggest_follow_ups
)
from reporting.models import FollowUp, Schedule, History, Prepayment

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
        schedule_id = data.get('schedule_id')
        
        context = {
            'customer_name': data.get('customer_name', ''),
            'company_name': data.get('company_name', ''),
            'product': data.get('product', ''),
            'schedule_content': data.get('schedule_content', ''),
            'notes': data.get('notes', ''),
            'schedule_id': schedule_id,
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
        logger.info(f"[AI 인사이트] 시작 - 고객 ID: {followup_id}, 사용자: {request.user.username}")
        
        if not check_ai_permission(request.user):
            logger.warning(f"[AI 인사이트] 권한 없음 - 사용자: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        from django.db.models import Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        from reporting.models import OpportunityTracking, EmailLog
        
        logger.info(f"[AI 인사이트] 고객 데이터 조회 중...")
        followup = FollowUp.objects.get(id=followup_id)
        logger.info(f"[AI 인사이트] 고객명: {followup.customer_name}")
        
        # 최근 6개월 데이터
        six_months_ago = timezone.now() - timedelta(days=180)
        
        logger.info(f"[AI 인사이트] 스케줄 데이터 수집 중...")
        # 스케줄 통계
        schedules = Schedule.objects.filter(
            followup=followup,
            visit_date__gte=six_months_ago
        )
        meeting_count = schedules.filter(activity_type='customer_meeting').count()
        quote_count = schedules.filter(activity_type='quote').count()
        logger.info(f"[AI 인사이트] 미팅: {meeting_count}건, 견적: {quote_count}건")
        
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
        
        logger.info(f"[AI 인사이트] AI 요약 생성 시작...")
        summary = generate_customer_summary(customer_data, request.user)
        logger.info(f"[AI 인사이트] AI 요약 생성 완료 (길이: {len(summary)} 자)")
        
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
        logger.info(f"[AI 등급평가] 시작 - 고객 ID: {followup_id}, 사용자: {request.user.username}")
        
        if not check_ai_permission(request.user):
            logger.warning(f"[AI 등급평가] 권한 없음 - 사용자: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        from django.db.models import Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        from reporting.models import (
            History, OpportunityTracking, EmailLog, 
            DeliveryItem, Prepayment
        )
        
        logger.info(f"[AI 등급평가] 고객 데이터 조회 중...")
        followup = FollowUp.objects.get(id=followup_id)
        logger.info(f"[AI 등급평가] 고객명: {followup.customer_name}")
        
        # 최근 6개월 데이터
        six_months_ago = timezone.now() - timedelta(days=180)
        
        logger.info(f"[AI 등급평가] 활동 데이터 수집 중...")
        # 미팅 횟수 (최근 6개월)
        meeting_count = Schedule.objects.filter(
            followup=followup,
            activity_type='meeting',
            created_at__gte=six_months_ago
        ).count()
        logger.info(f"[AI 등급평가] 미팅 횟수: {meeting_count}건")
        
        # 이메일 교환 (최근 6개월)
        email_count = EmailLog.objects.filter(
            followup=followup,
            sent_at__gte=six_months_ago
        ).count()
        
        # 견적 횟수 (최근 6개월)
        quote_count = Schedule.objects.filter(
            followup=followup,
            activity_type='quote',
            created_at__gte=six_months_ago
        ).count()
        
        # 구매 횟수 및 금액 (전체 + 최근 6개월)
        # 납품 일정(delivery)만 카운트 (견적 일정 제외)
        all_deliveries = DeliveryItem.objects.filter(
            schedule__followup=followup,
            schedule__activity_type='delivery'
        )
        
        recent_deliveries = all_deliveries.filter(
            schedule__created_at__gte=six_months_ago
        )
        
        purchase_count = all_deliveries.values('schedule').distinct().count()
        recent_purchase_count = recent_deliveries.values('schedule').distinct().count()
        
        total_purchase = all_deliveries.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        recent_total_purchase = recent_deliveries.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        # 선결제 정보 (전체)
        prepayments = Prepayment.objects.filter(
            customer=followup
        )
        prepayment_count = prepayments.count()
        total_prepayment = prepayments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # 마지막 연락일 (최근 일정 기준)
        last_schedule = Schedule.objects.filter(followup=followup).order_by('-visit_date').first()
        last_contact = last_schedule.visit_date.strftime('%Y-%m-%d') if last_schedule else '없음'
        
        # 미팅 요약 (최근 3개)
        recent_meetings = Schedule.objects.filter(
            followup=followup,
            activity_type='meeting',
            notes__isnull=False
        ).order_by('-visit_date')[:3]
        
        meeting_summary = []
        for meeting in recent_meetings:
            if meeting.notes:
                meeting_summary.append(f"[{meeting.visit_date.strftime('%Y-%m-%d')}] {meeting.notes[:100]}")
        
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
            'recent_purchase_count': recent_purchase_count,
            'total_purchase': float(total_purchase),
            'recent_total_purchase': float(recent_total_purchase),
            'prepayment_count': prepayment_count,
            'total_prepayment': float(total_prepayment),
            'last_contact': last_contact,
            'avg_response_time': '알 수 없음',
            'email_sentiment': '중립',
            'meeting_summary': meeting_summary,
            'opportunities': opportunities,
        }
        
        logger.info(f"[AI 등급평가] AI 분석 시작...")
        result = update_customer_grade_with_ai(customer_data, request.user)
        logger.info(f"[AI 등급평가] AI 분석 완료 - 등급: {result.get('grade')}, 점수: {result.get('score')}")
        
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


@login_required
@require_http_methods(["POST"])
def ai_summarize_meeting_notes(request):
    """
    AI로 미팅 노트 요약
    """
    try:
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        data = json.loads(request.body)
        notes = data.get('notes', '').strip()
        
        if not notes:
            return JsonResponse({
                'success': False,
                'error': '요약할 노트 내용이 없습니다.'
            }, status=400)
        
        # 너무 짧은 노트는 요약 불필요
        if len(notes) < 100:
            return JsonResponse({
                'success': False,
                'error': '노트가 너무 짧아 요약이 필요하지 않습니다.'
            }, status=400)
        
        result = summarize_meeting_notes(notes, request.user)
        
        # 요약 결과를 Markdown 형식으로 포맷팅
        summary_text = f"""## 요약
{result.get('summary', '')}

## 주요 포인트
{chr(10).join('- ' + point for point in result.get('key_points', []))}

## 액션 아이템
{chr(10).join('- ' + item for item in result.get('action_items', []))}
"""
        
        # 키워드가 있으면 추가
        keywords = result.get('keywords', {})
        if any(keywords.values()):
            summary_text += "\n## 주요 키워드\n"
            if keywords.get('budget'):
                summary_text += f"- 💰 예산: {keywords['budget']}\n"
            if keywords.get('deadline'):
                summary_text += f"- 📅 납기: {keywords['deadline']}\n"
            if keywords.get('decision_maker'):
                summary_text += f"- 👤 결정권자: {keywords['decision_maker']}\n"
            if keywords.get('pain_points'):
                summary_text += f"- ⚠️ 고객 문제점: {keywords['pain_points']}\n"
            if keywords.get('competitors'):
                summary_text += f"- 🏢 경쟁사: {keywords['competitors']}\n"
        
        return JsonResponse({
            'success': True,
            'summary': summary_text.strip(),
            'original_length': len(notes),
            'summary_length': len(summary_text)
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error summarizing meeting notes: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'노트 요약 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_suggest_follow_ups(request):
    """
    AI로 팔로우업 우선순위 제안
    """
    try:
        logger.info(f"[AI 팔로우업] 시작 - 사용자: {request.user.username}")
        
        if not check_ai_permission(request.user):
            logger.warning(f"[AI 팔로우업] 권한 없음 - 사용자: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        from django.db.models import Sum, Q, Max, Count
        from django.utils import timezone
        from datetime import timedelta
        from reporting.models import History, Prepayment, OpportunityTracking
        
        logger.info(f"[AI 팔로우업] 고객 데이터 수집 중...")
        # 사용자의 모든 고객 가져오기 (최근 6개월 이내 활동이 있는 고객만)
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # ✅ 일정이 1개라도 있는 고객만 필터링 (속도 & 토큰 절약)
        # Schedule 테이블에서 일정이 있는 followup_id만 추출
        followups_with_schedules = FollowUp.objects.filter(
            user=request.user
        ).annotate(
            schedule_count=Count('schedules'),
            recent_schedule_count=Count('schedules', filter=Q(schedules__visit_date__gte=six_months_ago))
        ).filter(
            schedule_count__gt=0  # 일정이 1개라도 있는 고객만
        ).select_related('company')
        
        logger.info(f"[AI 팔로우업] 일정 있는 고객 수: {followups_with_schedules.count()}명")
        
        customer_list = []
        
        for followup in followups_with_schedules[:50]:  # 최대 50명만 분석
            # 스케줄 통계 (최근 6개월)
            schedules = Schedule.objects.filter(
                followup=followup,
                visit_date__gte=six_months_ago
            )
            
            # 히스토리에서 사용자가 작성한 메모만 가져오기 (최근 6개월)
            histories = History.objects.filter(
                followup=followup,
                created_at__gte=six_months_ago
            ).exclude(content__isnull=True).exclude(content='')
            
            # 활동 횟수 확인 (스케줄 + 히스토리 최소 1개 이상)
            total_activities = schedules.count() + histories.count()
            if total_activities == 0:
                continue  # 활동 없는 고객 제외
            
            # 미팅 횟수 (스케줄에서만)
            meeting_count = schedules.filter(activity_type='customer_meeting').count()
            
            # 견적 횟수 (스케줄에서만)
            quote_count = schedules.filter(activity_type='quote').count()
            
            # 구매 통계 (스케줄에서만)
            delivery_schedules = schedules.filter(activity_type='delivery')
            purchase_count = delivery_schedules.count()
            total_purchase = delivery_schedules.aggregate(total=Sum('expected_revenue'))['total'] or 0
            
            # 마지막 연락일 (스케줄과 히스토리 모두 확인)
            last_schedule = schedules.order_by('-visit_date').first()
            last_history = histories.order_by('-created_at').first()
            
            if last_schedule and last_history:
                last_contact_date = max(last_schedule.visit_date, last_history.created_at.date())
            elif last_schedule:
                last_contact_date = last_schedule.visit_date
            elif last_history:
                last_contact_date = last_history.created_at.date()
            else:
                last_contact_date = None
                
            last_contact = last_contact_date.strftime('%Y-%m-%d') if last_contact_date else '연락 기록 없음'
            
            # 히스토리 메모 수집 (최근 5개만)
            history_notes = [h.content for h in histories.order_by('-created_at')[:5] if h.content]
            
            # 고객 구분 판단
            customer_type = '미정'
            if followup.company and followup.company.name:
                company_name = followup.company.name
                customer_name = followup.customer_name or ''
                manager_name = followup.manager or ''
                
                # 대학/연구소 판단
                if any(keyword in company_name for keyword in ['대학', '연구소', '연구원', 'University', 'Research']):
                    # 이름과 책임자명이 같으면 교수, 다르면 연구원
                    if customer_name and manager_name and customer_name == manager_name:
                        customer_type = '교수'
                    else:
                        customer_type = '연구원'
                else:
                    # 일반 업체: 이름과 책임자명이 같으면 대표, 다르면 실무자
                    if customer_name and manager_name and customer_name == manager_name:
                        customer_type = '대표'
                    else:
                        customer_type = '실무자'
            
            # 진행 중인 기회
            opportunities = OpportunityTracking.objects.filter(
                followup=followup,
                current_stage__in=['lead', 'contact', 'quote', 'closing']
            )
            
            # 선결제 잔액
            prepayments = Prepayment.objects.filter(
                customer=followup,
                status='active'
            )
            prepayment_balance = sum(p.balance for p in prepayments)
            
            customer_list.append({
                'id': followup.id,
                'name': followup.customer_name,
                'company': str(followup.company),
                'customer_type': customer_type,  # 고객 구분 추가
                'last_contact': last_contact,
                'meeting_count': meeting_count,
                'quote_count': quote_count,
                'purchase_count': purchase_count,
                'total_purchase': float(total_purchase),
                'grade': followup.customer_grade if followup.customer_grade else 'D',
                'opportunities': [{'stage': o.get_current_stage_display()} for o in opportunities],
                'prepayment_balance': float(prepayment_balance),
                'total_activities': total_activities,
                'history_notes': history_notes  # 히스토리 메모 추가
            })
        
        if not customer_list:
            return JsonResponse({
                'success': False,
                'error': '일정이 있는 고객이 없습니다. 먼저 고객과의 일정을 등록해주세요.'
            }, status=400)
        
        # AI에게 일정이 있는 고객만 전달하여 분석 (토큰 절약)
        suggestions = suggest_follow_ups(customer_list, request.user)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions,
            'total_analyzed': len(customer_list)
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error suggesting follow-ups: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'우선순위 제안 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_analyze_email_thread(request):
    """
    AI로 이메일 스레드 분석
    """
    try:
        if not check_ai_permission(request.user):
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다.'
            }, status=403)
        
        data = json.loads(request.body)
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return JsonResponse({
                'success': False,
                'error': '스레드 ID가 필요합니다.'
            }, status=400)
        
        from reporting.models import EmailLog
        
        # 스레드의 모든 이메일 가져오기
        emails = EmailLog.objects.filter(
            gmail_thread_id=thread_id
        ).order_by('sent_at')
        
        if not emails.exists():
            return JsonResponse({
                'success': False,
                'error': '이메일 스레드를 찾을 수 없습니다.'
            }, status=404)
        
        # 이메일 데이터 변환
        email_list = []
        for email in emails:
            email_list.append({
                'date': email.sent_at.strftime('%Y-%m-%d %H:%M') if email.sent_at else '',
                'from': email.sender_email,
                'subject': email.subject or '',
                'body': email.body or email.body_html or ''
            })
        
        result = analyze_email_thread(email_list, request.user)
        
        return JsonResponse({
            'success': True,
            'analysis': result,
            'email_count': len(email_list)
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error analyzing email thread: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'이메일 스레드 분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
def ai_recommend_products(request, followup_id):
    """
    고객의 구매 이력, 견적 이력, 미팅 노트를 종합 분석하여 상품 추천
    구매 이력이 없어도 견적/미팅 히스토리 기반으로 추천 가능
    """
    from reporting.ai_utils import recommend_products, check_ai_permission
    
    logger.info(f"[AI 상품추천] 시작 - 고객 ID: {followup_id}, 사용자: {request.user.username}")
    
    if not check_ai_permission(request.user):
        logger.warning(f"[AI 상품추천] 권한 없음 - 사용자: {request.user.username}")
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        from reporting.models import FollowUp, DeliveryItem, Schedule, QuoteItem
        
        logger.info(f"[AI 상품추천] 고객 데이터 조회 중...")
        # 고객 정보 가져오기
        followup = get_object_or_404(FollowUp, id=followup_id)
        logger.info(f"[AI 상품추천] 고객명: {followup.customer_name}")
        
        # 구매 이력 가져오기 (최근 2년)
        from datetime import timedelta
        two_years_ago = timezone.now() - timedelta(days=730)
        six_months_ago = timezone.now() - timedelta(days=180)
        
        delivery_items = DeliveryItem.objects.filter(
            schedule__followup=followup,
            schedule__activity_type='delivery',
            schedule__created_at__gte=two_years_ago
        ).select_related('product', 'schedule').order_by('-schedule__visit_date')
        
        purchase_history = []
        for item in delivery_items[:20]:  # 최근 20개까지
            purchase_history.append({
                'product_name': item.product.product_code if item.product else '제품 정보 없음',
                'quantity': float(item.quantity) if item.quantity else 0,
                'unit': item.unit or '',
                'date': item.schedule.visit_date.strftime('%Y-%m-%d') if item.schedule.visit_date else '',
                'specification': item.product.specification if item.product else ''
            })
        
        # 견적 이력 가져오기 (최근 6개월)
        quote_items = QuoteItem.objects.filter(
            quote__followup=followup,
            quote__created_at__gte=six_months_ago
        ).select_related('product', 'quote').order_by('-quote__quote_date')
        
        quote_history = []
        for item in quote_items[:15]:  # 최근 15개까지
            quote_history.append({
                'product_name': item.product.product_code if item.product else '제품 정보 없음',
                'quantity': float(item.quantity) if item.quantity else 0,
                'unit_price': float(item.unit_price) if item.unit_price else 0,
                'date': item.quote.quote_date.strftime('%Y-%m-%d') if item.quote.quote_date else '',
                'specification': item.product.specification if item.product else ''
            })
        
        # 최근 미팅 노트 가져오기 (최근 10개)
        meeting_schedules = Schedule.objects.filter(
            followup=followup,
            activity_type='customer_meeting'
        ).order_by('-visit_date')[:10]
        
        meeting_notes = ""
        for schedule in meeting_schedules:
            if schedule.notes:
                meeting_notes += f"[{schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '날짜 미상'}] {schedule.notes}\n\n"
        
        # 관심 키워드 추출 (미팅 노트와 견적/구매 제품에서)
        interest_keywords = []
        all_text = meeting_notes
        
        # 제품명에서 키워드 추출
        for item in purchase_history + quote_history:
            if item.get('product_name'):
                all_text += " " + item['product_name']
        
        # 일반적인 과학 장비 키워드 확인
        common_keywords = [
            'HPLC', 'GC', 'LC-MS', 'UV', '분광광도계',
            '컬럼', '시약', '필터', '소모품',
            '분석', '실험', '연구', '장비', '테스트',
            '정제', '추출', '분리', '측정'
        ]
        for keyword in common_keywords:
            if keyword.lower() in all_text.lower():
                interest_keywords.append(keyword)
        
        # 중복 제거
        interest_keywords = list(set(interest_keywords))
        
        # 실제 DB 제품 목록 가져오기 (활성 제품만, 사용자 회사 제품만)
        from reporting.models import Product
        
        # 사용자의 회사에 속한 제품만 가져오기
        user_company = request.user.userprofile.company if hasattr(request.user, 'userprofile') else None
        
        if user_company:
            # 같은 회사의 사용자가 생성한 제품만
            available_products = Product.objects.filter(
                is_active=True,
                created_by__userprofile__company=user_company
            ).values(
                'product_code', 'specification', 'unit', 'standard_price', 'description'
            )[:100]  # 최대 100개
        else:
            # 회사 정보가 없으면 사용자가 생성한 제품만
            available_products = Product.objects.filter(
                is_active=True,
                created_by=request.user
            ).values(
                'product_code', 'specification', 'unit', 'standard_price', 'description'
            )[:100]  # 최대 100개
        
        product_catalog = []
        for prod in available_products:
            product_catalog.append({
                'product_code': prod['product_code'],
                'specification': prod['specification'] or '',
                'unit': prod['unit'] or 'EA',
                'price': float(prod['standard_price']) if prod['standard_price'] else 0,
                'description': prod['description'] or ''
            })
        
        # 고객 데이터 준비
        customer_data = {
            'name': followup.customer_name,
            'company': followup.company or '',
            'industry': followup.department or '',
            'purchase_history': purchase_history,
            'quote_history': quote_history,
            'meeting_notes': meeting_notes[:2500],  # 토큰 절약
            'interest_keywords': interest_keywords,
            'available_products': product_catalog  # 실제 제품 카탈로그 추가
        }
        
        logger.info(f"[AI 상품추천] AI 분석 시작 - 구매: {len(purchase_history)}건, 견적: {len(quote_history)}건")
        # AI 추천 실행
        result = recommend_products(customer_data, request.user)
        logger.info(f"[AI 상품추천] AI 분석 완료 - 추천: {len(result.get('recommendations', []))}개")
        
        return JsonResponse({
            'success': True,
            'recommendations': result.get('recommendations', []),
            'analysis_summary': result.get('analysis_summary', ''),
            'customer_name': followup.customer_name,
            'purchase_count': len(purchase_history),
            'quote_count': len(quote_history),
            'meeting_count': len(meeting_schedules),
            'data_sources': {
                'has_purchases': len(purchase_history) > 0,
                'has_quotes': len(quote_history) > 0,
                'has_meetings': bool(meeting_notes.strip())
            }
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error recommending products: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'상품 추천 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ai_get_product_detail(request, product_code):
    """
    제품 상세 정보 조회 (AI 추천에서 사용)
    """
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        from reporting.models import Product
        from urllib.parse import unquote
        
        # URL 디코딩
        product_code = unquote(product_code)
        
        # 사용자의 회사에 속한 제품만 조회
        user_company = request.user.userprofile.company if hasattr(request.user, 'userprofile') else None
        
        if user_company:
            product = Product.objects.filter(
                product_code=product_code,
                created_by__userprofile__company=user_company,
                is_active=True
            ).first()
        else:
            product = Product.objects.filter(
                product_code=product_code,
                created_by=request.user,
                is_active=True
            ).first()
        
        if not product:
            return JsonResponse({
                'success': False,
                'error': '제품을 찾을 수 없습니다.',
                'is_catalog_product': False
            })
        
        # 제품 정보 반환
        return JsonResponse({
            'success': True,
            'is_catalog_product': True,
            'product': {
                'product_code': product.product_code,
                'specification': product.specification or '',
                'description': product.description or '',
                'unit': product.unit or 'EA',
                'standard_price': float(product.standard_price) if product.standard_price else 0,
                'current_price': float(product.get_current_price()),
                'is_promo': product.is_promo,
                'promo_price': float(product.promo_price) if product.promo_price else None,
                'total_quoted': product.total_quoted,
                'total_sold': product.total_sold,
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting product detail: {e}")
        return JsonResponse({
            'success': False,
            'error': f'제품 정보 조회 중 오류가 발생했습니다: {str(e)}',
            'is_catalog_product': False
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_natural_language_search(request):
    """
    자연어 검색 쿼리를 SQL 필터 조건으로 변환
    """
    from reporting.ai_utils import natural_language_search, check_ai_permission
    
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        from reporting.models import FollowUp, Schedule, OpportunityTracking
        from django.db.models import Q
        from datetime import datetime, timedelta
        
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        search_type = data.get('search_type', 'all')  # customers, schedules, opportunities, all
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': '검색어를 입력해주세요.'
            }, status=400)
        
        # AI로 자연어 쿼리 변환
        result = natural_language_search(query, search_type, request.user)
        
        # 변환된 필터를 실제 쿼리로 실행
        search_results = {
            'interpretation': result.get('interpretation', ''),
            'customers': [],
            'schedules': [],
            'opportunities': []
        }
        
        filters = result.get('filters', {})
        
        # 고객 검색
        if search_type in ['customers', 'all'] and filters:
            try:
                # 권한 필터링 추가
                from reporting.views import get_accessible_users
                accessible_users = get_accessible_users(request.user)
                
                # 필터 분리: 고객 직접, 스케줄, 납품상품, 견적상품
                customer_filters = {}
                schedule_filters = {}
                delivery_filters = {}
                quote_filters = {}
                
                for key, value in filters.items():
                    if 'deliveryitems__' in key:
                        # deliveryitems__ 접두사 제거하고 납품상품 필터로
                        clean_key = key.replace('deliveryitems__', '')
                        delivery_filters[clean_key] = value
                    elif 'quoteitems__' in key:
                        # quoteitems__ 접두사 제거하고 견적상품 필터로
                        clean_key = key.replace('quoteitems__', '')
                        quote_filters[clean_key] = value
                    elif 'schedules__' in key:
                        # schedules__ 접두사 제거하고 스케줄 필터로
                        clean_key = key.replace('schedules__', '')
                        schedule_filters[clean_key] = value
                    else:
                        # 고객 직접 필터
                        customer_filters[key] = value
                
                # 납품 상품 필터가 있으면 해당 상품을 구매한 고객만 조회
                customer_ids_from_delivery = None
                if delivery_filters:
                    from reporting.models import DeliveryItem
                    customer_ids_from_delivery = DeliveryItem.objects.filter(
                        **delivery_filters
                    ).values_list('schedule__followup_id', flat=True).distinct()
                    logger.info(f"[자연어검색] 납품상품 필터: {delivery_filters} → 고객 {len(customer_ids_from_delivery)}명")
                
                # 견적 상품 필터가 있으면 해당 상품을 견적받은 고객만 조회
                customer_ids_from_quote = None
                if quote_filters:
                    from reporting.models import QuoteItem
                    customer_ids_from_quote = QuoteItem.objects.filter(
                        **quote_filters
                    ).values_list('quote__followup_id', flat=True).distinct()
                    logger.info(f"[자연어검색] 견적상품 필터: {quote_filters} → 고객 {len(customer_ids_from_quote)}명")
                
                # 스케줄 필터가 있으면 해당 일정이 있는 고객만 조회
                customer_ids_from_schedule = None
                if schedule_filters:
                    customer_ids_from_schedule = Schedule.objects.filter(
                        user__in=accessible_users,  # 권한 필터 추가
                        **schedule_filters
                    ).values_list('followup_id', flat=True).distinct()
                    logger.info(f"[자연어검색] 일정 필터: {schedule_filters} → 고객 {len(customer_ids_from_schedule)}명")
                
                # 고객 ID 리스트 결합 (교집합)
                final_customer_ids = None
                
                if customer_ids_from_delivery is not None:
                    final_customer_ids = set(customer_ids_from_delivery)
                
                if customer_ids_from_quote is not None:
                    if final_customer_ids is None:
                        final_customer_ids = set(customer_ids_from_quote)
                    else:
                        final_customer_ids &= set(customer_ids_from_quote)
                
                if customer_ids_from_schedule is not None:
                    if final_customer_ids is None:
                        final_customer_ids = set(customer_ids_from_schedule)
                    else:
                        final_customer_ids &= set(customer_ids_from_schedule)
                
                # 최종 고객 쿼리
                if final_customer_ids is not None:
                    if customer_filters:
                        customers = FollowUp.objects.filter(
                            user__in=accessible_users,
                            id__in=final_customer_ids,
                            **customer_filters
                        ).distinct()[:20]
                    else:
                        customers = FollowUp.objects.filter(
                            user__in=accessible_users,
                            id__in=final_customer_ids
                        ).distinct()[:20]
                elif customer_filters:
                    customers = FollowUp.objects.filter(
                        user__in=accessible_users,
                        **customer_filters
                    ).distinct()[:20]
                else:
                    customers = FollowUp.objects.filter(
                        user__in=accessible_users
                    ).distinct()[:20]
                
                logger.info(f"[자연어검색] 최종 고객 수: {customers.count()}명")
                
                for customer in customers:
                    # 마지막 연락일 계산
                    last_schedule = Schedule.objects.filter(followup=customer).order_by('-visit_date').first()
                    last_contact = last_schedule.visit_date.strftime('%Y-%m-%d') if last_schedule else ''
                    
                    # 구매 상품 정보 (상품 검색인 경우)
                    purchased_products = []
                    if delivery_filters:
                        from reporting.models import DeliveryItem
                        delivery_items = DeliveryItem.objects.filter(
                            schedule__followup=customer,
                            **delivery_filters
                        ).select_related('product')[:5]
                        
                        for item in delivery_items:
                            product_info = item.product.product_code if item.product else item.item_name
                            purchased_products.append(product_info)
                    
                    search_results['customers'].append({
                        'id': customer.id,
                        'name': customer.customer_name,
                        'company': str(customer.company) if customer.company else '',
                        'grade': customer.customer_grade or '',
                        'last_contact': last_contact,
                        'purchased_products': purchased_products if delivery_filters else None
                    })
            except Exception as e:
                logger.error(f"Customer search error: {e}")
        
        # 일정 검색
        if search_type in ['schedules', 'all'] and filters:
            try:
                # 권한 필터링 추가
                from reporting.views import get_accessible_users
                accessible_users = get_accessible_users(request.user)
                
                # schedules__ 접두사 제거 (일정 검색에서는 불필요)
                schedule_filters = {}
                followup_filters = {}
                
                for key, value in filters.items():
                    if key.startswith('schedules__'):
                        # schedules__ 접두사 제거
                        clean_key = key.replace('schedules__', '')
                        schedule_filters[clean_key] = value
                    elif key.startswith('followup__'):
                        # 고객 관련 필터
                        followup_filters[key] = value
                    else:
                        # 일정 직접 필터
                        schedule_filters[key] = value
                
                # 필터 적용 (권한 필터 추가)
                if followup_filters and schedule_filters:
                    schedules = Schedule.objects.filter(
                        user__in=accessible_users,  # 권한 필터 추가
                        **schedule_filters, 
                        **followup_filters
                    ).select_related('followup')[:20]
                elif schedule_filters:
                    schedules = Schedule.objects.filter(
                        user__in=accessible_users,  # 권한 필터 추가
                        **schedule_filters
                    ).select_related('followup')[:20]
                elif followup_filters:
                    schedules = Schedule.objects.filter(
                        user__in=accessible_users,  # 권한 필터 추가
                        **followup_filters
                    ).select_related('followup')[:20]
                else:
                    schedules = Schedule.objects.filter(
                        user__in=accessible_users  # 권한 필터 추가
                    ).select_related('followup')[:20]
                
                for schedule in schedules:
                    type_labels = {
                        'customer_meeting': '미팅',
                        'quote': '견적',
                        'delivery': '납품',
                        'call': '전화',
                        'email': '이메일'
                    }
                    search_results['schedules'].append({
                        'id': schedule.id,
                        'type': type_labels.get(schedule.activity_type, schedule.activity_type),
                        'customer': schedule.followup.customer_name if schedule.followup else '',
                        'start_date': schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '',
                        'content': schedule.notes[:100] if schedule.notes else ''
                    })
            except Exception as e:
                logger.error(f"Schedule search error: {e}")
        
        # 영업기회 검색
        if search_type in ['opportunities', 'all'] and filters:
            try:
                # 권한 필터링 추가
                from reporting.views import get_accessible_users
                accessible_users = get_accessible_users(request.user)
                
                opp_filters = {k: v for k, v in filters.items() if not k.startswith('followup__')}
                opportunities = OpportunityTracking.objects.filter(
                    followup__user__in=accessible_users,  # 권한 필터 추가
                    **opp_filters
                ).select_related('followup')[:20]
                
                for opp in opportunities:
                    search_results['opportunities'].append({
                        'id': opp.id,
                        'title': opp.title,
                        'customer': opp.followup.customer_name if opp.followup else '',
                        'stage': opp.get_current_stage_display(),
                        'value': float(opp.expected_revenue) if opp.expected_revenue else 0,
                        'created': opp.created_at.strftime('%Y-%m-%d') if opp.created_at else ''
                    })
            except Exception as e:
                logger.error(f"Opportunity search error: {e}")
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': search_results,
            'total_count': len(search_results['customers']) + len(search_results['schedules']) + len(search_results['opportunities'])
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error in natural language search: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'자연어 검색 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_refresh_all_grades(request):
    """
    전체 고객 등급을 AI로 일괄 업데이트 (백그라운드 작업)
    """
    from django.db.models import Count
    from django.core.cache import cache
    import threading
    import time
    import uuid
    
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        limit = data.get('limit')
        background = data.get('background', True)
        
        # 마지막 AI 등급 갱신 시간 조회 (가장 최근에 갱신된 고객 기준)
        from django.utils import timezone
        from django.db.models import Count
        
        last_refresh_time = FollowUp.objects.filter(
            ai_grade_updated_at__isnull=False
        ).order_by('-ai_grade_updated_at').values_list('ai_grade_updated_at', flat=True).first()
        
        # 갱신 대상: 마지막 갱신 이후 활동이 있는 고객만
        if last_refresh_time:
            # 마지막 갱신 이후 스케줄이나 선결제가 생성/수정된 고객 ID 수집
            
            # 스케줄이 생성된 고객
            schedule_updated_ids = Schedule.objects.filter(
                Q(created_at__gte=last_refresh_time) | Q(updated_at__gte=last_refresh_time)
            ).values_list('followup_id', flat=True).distinct()
            
            # 선결제가 생성된 고객 (updated_at 필드 없음)
            prepayment_updated_ids = Prepayment.objects.filter(
                created_at__gte=last_refresh_time
            ).values_list('customer_id', flat=True).distinct()
            
            # 히스토리가 생성된 고객
            history_updated_ids = History.objects.filter(
                created_at__gte=last_refresh_time
            ).values_list('followup_id', flat=True).distinct()
            
            # 합치기
            updated_followup_ids = set(schedule_updated_ids) | set(prepayment_updated_ids) | set(history_updated_ids)
            
            if not updated_followup_ids:
                # 변경된 고객이 없으면 한 번도 갱신 안 된 고객만 대상
                queryset = FollowUp.objects.filter(
                    ai_grade_updated_at__isnull=True
                ).distinct()
                refresh_info = f"마지막 갱신: {last_refresh_time.strftime('%Y-%m-%d %H:%M')}, 변경 없음 (미갱신 고객만)"
            else:
                # 해당 고객들만 (한 번도 갱신 안 된 고객 제외)
                queryset = FollowUp.objects.filter(
                    id__in=updated_followup_ids
                ).distinct()
                refresh_info = f"마지막 갱신: {last_refresh_time.strftime('%Y-%m-%d %H:%M')}, 변경된 고객 {len(updated_followup_ids)}명"
            
            refresh_info = f"마지막 갱신: {last_refresh_time.strftime('%Y-%m-%d %H:%M')}, 변경된 고객만 선별"
        else:
            # 첫 갱신: 활동 이력이 있는 모든 고객
            queryset = FollowUp.objects.annotate(
                schedule_count=Count('schedules', distinct=True),
                email_count=Count('emails', distinct=True),
                history_count=Count('histories', distinct=True),
                prepayment_count=Count('prepayments', distinct=True)
            ).filter(
                Q(schedule_count__gte=1) | 
                Q(email_count__gte=1) | 
                Q(history_count__gte=1) |
                Q(prepayment_count__gte=1)
            )
            refresh_info = "전체 고객 첫 갱신"
        
        if limit:
            queryset = queryset[:limit]
        
        total_count = queryset.count()
        
        if total_count == 0:
            return JsonResponse({
                'success': False,
                'error': '업데이트할 고객이 없습니다. (마지막 갱신 이후 활동 없음)',
                'last_refresh': last_refresh_time.strftime('%Y-%m-%d %H:%M') if last_refresh_time else None
            }, status=400)
        
        # 예상 소요 시간 계산
        estimated_minutes = (total_count * 2.5) / 60  # 고객당 약 2.5초
        if estimated_minutes < 1:
            estimated_time = f"{int(total_count * 2.5)}초"
        else:
            estimated_time = f"{int(estimated_minutes)}분"
        
        if background:
            # 작업 ID 생성
            task_id = str(uuid.uuid4())
            
            # 초기 상태 저장
            cache.set(f'grade_update_{task_id}', {
                'status': 'running',
                'total': total_count,
                'processed': 0,
                'success': 0,
                'failed': 0,
                'grade_changes': 0
            }, timeout=3600)  # 1시간
            
            # 백그라운드 스레드로 실행
            # 스레드 밖에서 user_id 추출 (request는 thread-local이므로)
            user_id = request.user.id
            
            def update_grades_background():
                from django.contrib.auth import get_user_model
                from django.db.models import Sum, Q
                from django.utils import timezone
                from datetime import timedelta
                from decimal import Decimal
                from reporting.models import (
                    History, OpportunityTracking, EmailLog, 
                    DeliveryItem, Prepayment
                )
                
                # 스레드 내에서 User 객체 가져오기
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    logger.error(f"User {user_id} not found in background thread")
                    cache.set(f'grade_update_{task_id}', {
                        'status': 'failed',
                        'error': 'User not found'
                    }, timeout=3600)
                    return
                
                start_time = time.time()
                success_count = 0
                failed_count = 0
                grade_changes = []
                six_months_ago = timezone.now() - timedelta(days=180)
                
                try:
                    # 각 고객 처리
                    for idx, followup in enumerate(queryset, 1):
                        try:
                            # 기존 등급 저장
                            old_grade = followup.ai_grade_score
                            old_grade_letter = followup.customer_grade
                            
                            # AI로 등급 업데이트 (내부 로직 직접 실행)
                            # 미팅 횟수 (최근 6개월)
                            meeting_count = Schedule.objects.filter(
                                followup=followup,
                                activity_type='meeting',
                                created_at__gte=six_months_ago
                            ).count()
                            
                            # 이메일 교환 (최근 6개월)
                            email_count = EmailLog.objects.filter(
                                followup=followup,
                                created_at__gte=six_months_ago
                            ).count()
                            
                            # 견적 횟수 (최근 6개월)
                            quote_count = Schedule.objects.filter(
                                followup=followup,
                                activity_type='quote',
                                created_at__gte=six_months_ago
                            ).count()
                            
                            # 구매 횟수 및 금액 (전체 + 최근 6개월)
                            # 납품 일정(delivery)만 카운트 (견적 일정 제외)
                            all_deliveries = DeliveryItem.objects.filter(
                                schedule__followup=followup,
                                schedule__activity_type='delivery'
                            )
                            
                            recent_deliveries = all_deliveries.filter(
                                schedule__created_at__gte=six_months_ago
                            )
                            
                            purchase_count = all_deliveries.values('schedule').distinct().count()
                            recent_purchase_count = recent_deliveries.values('schedule').distinct().count()
                            
                            total_purchase = all_deliveries.aggregate(
                                total=Sum('total_price')
                            )['total'] or Decimal('0')
                            
                            recent_total_purchase = recent_deliveries.aggregate(
                                total=Sum('total_price')
                            )['total'] or Decimal('0')
                            
                            # 선결제 정보 (전체)
                            prepayments = Prepayment.objects.filter(
                                customer=followup
                            )
                            prepayment_count = prepayments.count()
                            total_prepayment = prepayments.aggregate(
                                total=Sum('amount')
                            )['total'] or Decimal('0')
                            
                            # 마지막 연락일 (최근 일정 기준)
                            last_schedule = Schedule.objects.filter(followup=followup).order_by('-visit_date').first()
                            last_contact = last_schedule.visit_date.strftime('%Y-%m-%d') if last_schedule else '없음'
                            
                            # 미팅 요약 (최근 3개)
                            recent_meetings = Schedule.objects.filter(
                                followup=followup,
                                activity_type='meeting',
                                notes__isnull=False
                            ).order_by('-visit_date')[:3]
                            
                            meeting_summary = []
                            for meeting in recent_meetings:
                                if meeting.notes:
                                    meeting_summary.append(f"[{meeting.visit_date.strftime('%Y-%m-%d')}] {meeting.notes[:100]}")
                            
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
                                'current_grade': old_grade_letter,  # 현재 등급 전달
                                'current_score': old_grade,  # 현재 점수 전달
                                'meeting_count': meeting_count,
                                'email_count': email_count,
                                'quote_count': quote_count,
                                'purchase_count': purchase_count,
                                'recent_purchase_count': recent_purchase_count,
                                'total_purchase': float(total_purchase),
                                'recent_total_purchase': float(recent_total_purchase),
                                'prepayment_count': prepayment_count,
                                'total_prepayment': float(total_prepayment),
                                'last_contact': last_contact,
                                'avg_response_time': '알 수 없음',
                                'email_sentiment': '중립',
                                'meeting_summary': meeting_summary,
                                'opportunities': opportunities,
                            }
                            
                            result = update_customer_grade_with_ai(customer_data, user)
                            
                            if result.get('grade') and result.get('score') is not None:
                                # DB 업데이트 (갱신 시간 포함)
                                followup.customer_grade = result.get('grade')
                                followup.ai_grade_score = result.get('score')
                                followup.ai_grade_updated_at = timezone.now()  # 갱신 시간 기록
                                followup.save(update_fields=['customer_grade', 'ai_grade_score', 'ai_grade_updated_at'])
                                
                                success_count += 1
                                
                                # 등급 변경 확인
                                followup.refresh_from_db()
                                new_grade = followup.ai_grade_score
                                new_grade_letter = followup.customer_grade
                                
                                if old_grade != new_grade:
                                    grade_changes.append({
                                        'customer_name': followup.customer_name or '고객명 없음',
                                        'company': str(followup.company) if followup.company else '업체명 없음',
                                        'old_grade': old_grade_letter or 'N/A',
                                        'new_grade': new_grade_letter or 'N/A',
                                        'old_score': int(old_grade) if old_grade else 0,
                                        'new_score': int(new_grade) if new_grade else 0
                                    })
                            else:
                                failed_count += 1
                            
                            # 진행 상황 업데이트
                            cache.set(f'grade_update_{task_id}', {
                                'status': 'running',
                                'total': total_count,
                                'processed': idx,
                                'success': success_count,
                                'failed': failed_count,
                                'grade_changes': len(grade_changes),
                                'changes': grade_changes[:50]  # 최대 50개만 저장
                            }, timeout=3600)
                            
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"Failed to update grade for customer {followup.id}: {e}")
                    
                    # 결과 추출
                    elapsed_time = time.time() - start_time
                    
                    # 완료 상태 저장
                    cache.set(f'grade_update_{task_id}', {
                        'status': 'completed',
                        'total': total_count,
                        'processed': total_count,
                        'success': success_count,
                        'failed': failed_count,
                        'grade_changes': len(grade_changes),
                        'changes': grade_changes,
                        'elapsed_time': f"{int(elapsed_time)}초"
                    }, timeout=3600)
                    
                    logger.info(f"Background grade update completed: {success_count} success, {failed_count} failed, {len(grade_changes)} changes in {elapsed_time:.1f}s")
                    
                except Exception as e:
                    logger.error(f"Background grade update failed: {e}")
                    cache.set(f'grade_update_{task_id}', {
                        'status': 'failed',
                        'error': str(e)
                    }, timeout=3600)
            
            thread = threading.Thread(target=update_grades_background, daemon=True)
            thread.start()
            
            return JsonResponse({
                'success': True,
                'message': f'{total_count}명의 고객 등급 업데이트가 백그라운드에서 시작되었습니다.',
                'total_count': total_count,
                'estimated_time': estimated_time,
                'task_id': task_id,
                'refresh_info': refresh_info,
                'last_refresh': last_refresh_time.strftime('%Y-%m-%d %H:%M') if last_refresh_time else '첫 갱신'
            })
        else:
            # 동기 실행 (테스트용)
            return JsonResponse({
                'success': False,
                'error': '동기 실행은 지원하지 않습니다. Management command를 사용하세요.'
            }, status=400)
    
    except Exception as e:
        import traceback
        logger.error(f"Error in refresh all grades: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'등급 업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ai_check_grade_update_status(request, task_id):
    """
    등급 업데이트 작업 상태 확인
    """
    from django.core.cache import cache
    
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        status_data = cache.get(f'grade_update_{task_id}')
        
        if not status_data:
            return JsonResponse({
                'success': False,
                'error': '작업 정보를 찾을 수 없습니다.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'status': status_data
        })
    
    except Exception as e:
        logger.error(f"Error checking grade update status: {e}")
        return JsonResponse({
            'success': False,
            'error': f'상태 확인 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
def ai_meeting_advisor(request):
    """
    AI 미팅 준비 페이지
    """
    from django.shortcuts import render
    from django.http import HttpResponseForbidden
    
    # UserProfile 확인
    if not hasattr(request.user, 'userprofile'):
        return HttpResponseForbidden("사용자 프로필이 없습니다.")
    
    user_profile = request.user.userprofile
    
    # 실무자(salesman)만 접근 가능
    if user_profile.role != 'salesman':
        return HttpResponseForbidden("실무자만 접근 가능합니다.")
    
    # AI 권한 확인
    if not check_ai_permission(request.user):
        return HttpResponseForbidden("AI 기능 사용 권한이 없습니다.")
    
    return render(request, 'reporting/ai_meeting_advisor.html')


@login_required
@require_http_methods(["GET"])
def ai_upcoming_schedules(request):
    """
    다가오는 일정 목록 (오늘 포함 미래 일정)
    """
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        from datetime import date
        
        # 실무자는 본인 일정만 조회 (미팅 준비는 개인용 기능)
        # 오늘 이후 일정 (최대 30일)
        today = date.today()
        end_date = today + timedelta(days=30)
        
        schedules = Schedule.objects.filter(
            user=request.user,  # 본인 일정만
            visit_date__gte=today,
            visit_date__lte=end_date,
            status__in=['scheduled', 'in_progress']
        ).select_related('followup', 'followup__company').order_by('visit_date', 'visit_time')[:50]
        
        schedule_list = []
        for schedule in schedules:
            schedule_list.append({
                'id': schedule.id,
                'customer_name': schedule.followup.customer_name or '고객명 미정',
                'company': str(schedule.followup.company) if schedule.followup.company else '회사명 미정',
                'activity_type': schedule.activity_type,
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'visit_time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else None,
            })
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_list
        })
    
    except Exception as e:
        logger.error(f"Error getting upcoming schedules: {e}")
        return JsonResponse({
            'success': False,
            'error': f'일정 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ai_schedule_detail(request, schedule_id):
    """
    일정 상세 정보
    """
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 확인 - 본인 일정만 조회 가능
        if schedule.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '본인의 일정만 조회할 수 있습니다.'
            }, status=403)
        
        return JsonResponse({
            'success': True,
            'schedule': {
                'id': schedule.id,
                'customer_name': schedule.followup.customer_name or '고객명 미정',
                'company': str(schedule.followup.company) if schedule.followup.company else '회사명 미정',
                'activity_type': schedule.activity_type,
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'visit_time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else None,
                'location': schedule.location,
                'notes': schedule.notes,
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting schedule detail: {e}")
        return JsonResponse({
            'success': False,
            'error': f'일정 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_meeting_advice(request):
    """
    AI 미팅 조언 생성
    """
    if not check_ai_permission(request.user):
        return JsonResponse({
            'success': False,
            'error': 'AI 기능 사용 권한이 없습니다.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        user_question = data.get('question', '')
        
        if not schedule_id:
            return JsonResponse({
                'success': False,
                'error': '일정 ID가 필요합니다.'
            }, status=400)
        
        if not user_question:
            return JsonResponse({
                'success': False,
                'error': '질문을 입력해주세요.'
            }, status=400)
        
        # 일정 조회
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 확인 - 본인 일정만 조회 가능
        if schedule.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '본인의 일정만 조회할 수 있습니다.'
            }, status=403)
        
        # 고객 정보 수집
        followup = schedule.followup
        
        # 모든 히스토리 메모 수집
        from datetime import timedelta
        from django.db.models import Sum
        
        histories = History.objects.filter(
            followup=followup
        ).exclude(content__isnull=True).exclude(content='').order_by('-created_at')[:20]
        
        history_notes = [
            f"[{h.created_at.strftime('%Y-%m-%d')}] {h.content}"
            for h in histories
        ]
        
        # 구매 이력 (스케줄 기반)
        past_deliveries = Schedule.objects.filter(
            followup=followup,
            activity_type='delivery',
            status='completed'
        ).order_by('-visit_date')[:10]
        
        delivery_history = []
        for d in past_deliveries:
            items = d.delivery_items_set.all()
            total = sum(item.total_price for item in items if item.total_price)
            delivery_history.append({
                'date': d.visit_date.strftime('%Y-%m-%d'),
                'amount': float(total),
                'items_count': items.count()
            })
        
        # 견적 이력
        past_quotes = Schedule.objects.filter(
            followup=followup,
            activity_type='quote'
        ).order_by('-visit_date')[:10]
        
        quote_history = []
        for q in past_quotes:
            items = q.delivery_items_set.all()
            total = sum(item.total_price for item in items)
            quote_history.append({
                'date': q.visit_date.strftime('%Y-%m-%d'),
                'amount': float(total),
                'items_count': items.count()
            })
        
        # 과거 미팅 메모
        past_meetings = Schedule.objects.filter(
            followup=followup,
            activity_type='customer_meeting',
            notes__isnull=False
        ).exclude(notes='').order_by('-visit_date')[:5]
        
        meeting_notes = [
            f"[{m.visit_date.strftime('%Y-%m-%d')}] {m.notes}"
            for m in past_meetings
        ]
        
        # 이메일 주고받은 내역 수집
        from reporting.models import EmailLog
        
        email_history = []
        emails = EmailLog.objects.filter(
            followup=followup
        ).order_by('-created_at')[:20]
        
        for email in emails:
            email_type = '발신' if email.email_type == 'sent' else '수신'
            email_date = email.created_at.strftime('%Y-%m-%d %H:%M')
            email_subject = email.subject or '(제목 없음)'
            email_body = email.body[:200] if email.body else ''  # 본문 일부만
            
            email_history.append(
                f"[{email_date}] {email_type} - {email_subject}\n내용: {email_body}"
            )
        
        # 고객 구분 판단
        customer_type = '미정'
        if followup.company and followup.company.name:
            company_name = followup.company.name
            customer_name = followup.customer_name or ''
            manager_name = followup.manager or ''
            
            if any(keyword in company_name for keyword in ['대학', '연구소', '연구원', 'University', 'Research']):
                if customer_name and manager_name and customer_name == manager_name:
                    customer_type = '교수'
                else:
                    customer_type = '연구원'
            else:
                if customer_name and manager_name and customer_name == manager_name:
                    customer_type = '대표'
                else:
                    customer_type = '실무자'
        
        # AI에게 전달할 컨텍스트 구성
        context = {
            'schedule': {
                'type': schedule.get_activity_type_display(),
                'date': schedule.visit_date.strftime('%Y-%m-%d'),
                'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '미정',
                'location': schedule.location or '미정',
                'notes': schedule.notes or '없음'
            },
            'customer': {
                'name': followup.customer_name or '고객명 미정',
                'company': str(followup.company) if followup.company else '회사명 미정',
                'department': str(followup.department) if followup.department else '부서 미정',
                'type': customer_type,
                'manager': followup.manager or '미정',
                'grade': followup.customer_grade or 'C',
            },
            'history_notes': history_notes,
            'delivery_history': delivery_history,
            'quote_history': quote_history,
            'meeting_notes': meeting_notes,
            'email_history': email_history,
            'user_question': user_question
        }
        
        # AI 조언 생성
        from reporting.ai_utils import generate_meeting_advice
        advice = generate_meeting_advice(context, request.user)
        
        return JsonResponse({
            'success': True,
            'advice': advice
        })
    
    except Exception as e:
        import traceback
        logger.error(f"Error generating meeting advice: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'AI 조언 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_generate_meeting_strategy(request):
    """
    일정 기반 AI 미팅 전략 추천 (신규 버전)
    
    POST 파라미터:
    - schedule_id: 일정 ID (필수)
    
    Returns:
        - success: True/False
        - strategy: AI가 생성한 미팅 전략 (Markdown)
        - error: 에러 메시지 (실패 시)
    """
    try:
        logger.info(f"[AI 미팅전략] 시작 - 사용자: {request.user.username}")
        
        # AI 권한 체크
        if not check_ai_permission(request.user):
            logger.warning(f"[AI 미팅전략] 권한 없음 - 사용자: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'AI 기능 사용 권한이 없습니다. 관리자에게 문의하세요.'
            }, status=403)
        
        # 파라미터 받기
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        
        logger.info(f"[AI 미팅전략] 일정 ID: {schedule_id}")
        
        if not schedule_id:
            return JsonResponse({
                'success': False,
                'error': '일정 ID가 필요합니다.'
            }, status=400)
        
        # 일정 조회 및 권한 확인
        from reporting.models import Schedule
        from reporting.views import can_access_user_data
        
        logger.info(f"[AI 미팅전략] 일정 조회 중...")
        try:
            schedule = Schedule.objects.select_related('followup', 'user').get(id=schedule_id)
            logger.info(f"[AI 미팅전략] 일정 조회 완료 - 고객: {schedule.followup.customer_name}, 활동: {schedule.get_activity_type_display()}")
        except Schedule.DoesNotExist:
            logger.error(f"[AI 미팅전략] 일정을 찾을 수 없음 - ID: {schedule_id}")
            return JsonResponse({
                'success': False,
                'error': f'일정 ID {schedule_id}를 찾을 수 없습니다.'
            }, status=404)
        
        # 접근 권한 확인
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '해당 일정에 대한 접근 권한이 없습니다.'
            }, status=403)
        
        # AI 미팅 전략 생성
        from reporting.ai_utils import generate_meeting_strategy
        
        logger.info(f"[AI 미팅전략] AI 전략 생성 시작...")
        strategy = generate_meeting_strategy(schedule_id, request.user)
        logger.info(f"[AI 미팅전략] AI 전략 생성 완료 (길이: {len(strategy)} 자)")
        
        return JsonResponse({
            'success': True,
            'strategy': strategy,
            'schedule_info': {
                'customer_name': schedule.followup.customer_name,
                'activity_type': schedule.get_activity_type_display(),
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'visit_time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '미정'
            }
        })
    
    except PermissionError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except Exception as e:
        import traceback
        logger.error(f"Error generating meeting strategy: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'AI 미팅 전략 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_analyze_funnel(request):
    """
    펀넬 대시보드 AI 분석
    """
    try:
        # AI 권한 확인
        check_ai_permission(request.user)
        
        # 필터 파라미터 가져오기
        data = json.loads(request.body) if request.body else {}
        user_filter = data.get('user')
        grade_filter = data.get('grade')
        priority_filter = data.get('priority')
        level_filter = data.get('level')
        
        logger.info(f"[펀넬 AI] 분석 시작 - 필터: user={user_filter}, grade={grade_filter}, priority={priority_filter}, level={level_filter}")
        
        # FunnelAnalytics로 펀넬 데이터 수집
        from reporting.funnel_analytics import FunnelAnalytics
        from reporting.views import get_accessible_users
        
        analytics = FunnelAnalytics()
        
        # 접근 가능한 사용자 결정
        if request.user.is_superuser:
            accessible_users = None  # 모든 사용자
        else:
            accessible_users = get_accessible_users(request.user, request)
        
        # 펀넬 데이터 수집
        pipeline_summary = analytics.get_pipeline_summary(
            user=user_filter,
            accessible_users=accessible_users
        )
        
        stage_breakdown = analytics.get_stage_breakdown(
            user=user_filter,
            accessible_users=accessible_users
        )
        
        top_opportunities = analytics.get_top_opportunities(
            user=user_filter,
            grade_filter=grade_filter,
            priority_filter=priority_filter,
            level_filter=level_filter,
            accessible_users=accessible_users,
            limit=20  # 상위 20개 기회
        )
        
        won_lost_summary = analytics.get_won_lost_summary(
            user=user_filter,
            accessible_users=accessible_users
        )
        
        # 펀넬 데이터 구조화
        funnel_data = {
            'pipeline_summary': pipeline_summary,
            'stage_breakdown': stage_breakdown,
            'top_opportunities': top_opportunities,
            'won_lost_summary': won_lost_summary
        }
        
        logger.info(f"[펀넬 AI] 데이터 수집 완료 - 기회 {pipeline_summary.get('total_opportunities', 0)}건")
        
        # AI 분석 실행
        from reporting.ai_utils import analyze_funnel_performance
        
        logger.info(f"[펀넬 AI] AI 분석 시작...")
        analysis = analyze_funnel_performance(funnel_data, request.user)
        logger.info(f"[펀넬 AI] AI 분석 완료 (길이: {len(analysis)} 자)")
        
        return JsonResponse({
            'success': True,
            'analysis': analysis,
            'summary': {
                'total_opportunities': pipeline_summary.get('total_opportunities', 0),
                'total_expected_revenue': pipeline_summary.get('total_expected_revenue', 0),
                'total_weighted_revenue': pipeline_summary.get('total_weighted_revenue', 0),
                'conversion_rate': pipeline_summary.get('conversion_rate', 0),
                'win_rate': pipeline_summary.get('win_rate', 0)
            }
        })
    
    except PermissionError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=403)
    
    except Exception as e:
        import traceback
        logger.error(f"Error analyzing funnel: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'펀넬 분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)
