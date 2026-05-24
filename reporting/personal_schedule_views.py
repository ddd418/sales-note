"""
개인 일정 (PersonalSchedule) 관련 뷰
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .models import PersonalSchedule, History, UserProfile
from .readonly_api import api_login_required_or_readonly_response
from datetime import date, time
import json
import logging

logger = logging.getLogger(__name__)


def _api_login_required_response(request):
    return api_login_required_or_readonly_response(request)


def _user_display_name(user):
    return user.get_full_name() or user.username


def _date_or_none(value):
    return value.isoformat() if value else None


def _parse_iso_date_or_none(value):
    value = str(value or '').strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_time_or_none(value):
    value = str(value or '').strip()
    if not value:
        return None
    parts = value.split(':')
    if len(parts) < 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        return time(hour=hour, minute=minute)
    except (TypeError, ValueError):
        return None


def _personal_schedule_can_view(request_user, personal_schedule, user_profile=None):
    if personal_schedule.user_id == request_user.id:
        return True
    user_profile = user_profile or get_object_or_404(UserProfile, user=request_user)
    if user_profile.is_admin():
        return True
    return bool(
        user_profile.can_view_all_users()
        and user_profile.company_id
        and personal_schedule.company_id == user_profile.company_id
    )


def _personal_schedule_can_edit(request_user, personal_schedule):
    return personal_schedule.user_id == request_user.id


def _personal_schedule_react_href(personal_schedule):
    query = f'personal={personal_schedule.id}'
    date_value = _date_or_none(personal_schedule.schedule_date)
    if date_value:
        query = f'{query}&month={date_value[:7]}'
    return f'/schedules/calendar/?{query}'


def _personal_schedule_payload(personal_schedule, request_user=None):
    can_edit = bool(request_user and _personal_schedule_can_edit(request_user, personal_schedule))
    return {
        'id': personal_schedule.id,
        'type': 'personal',
        'followupId': None,
        'customer': personal_schedule.title,
        'title': personal_schedule.title,
        'company': personal_schedule.company.name if personal_schedule.company else '',
        'department': '',
        'owner': _user_display_name(personal_schedule.user),
        'ownerId': personal_schedule.user_id,
        'date': _date_or_none(personal_schedule.schedule_date),
        'time': personal_schedule.schedule_time.strftime('%H:%M') if personal_schedule.schedule_time else '',
        'activityType': 'personal',
        'activityLabel': '개인 일정',
        'status': 'personal',
        'statusLabel': '개인 일정',
        'location': '',
        'notes': (personal_schedule.content or '').strip()[:180],
        'notesFull': personal_schedule.content or '',
        'priority': '',
        'priorityLabel': '',
        'expectedRevenue': 0,
        'probability': 0,
        'expectedCloseDate': None,
        'purchaseConfirmed': False,
        'overdue': False,
        'historyCount': getattr(personal_schedule, 'history_count', 0),
        'reports': [],
        'href': _personal_schedule_react_href(personal_schedule),
        'djangoHref': reverse('reporting:personal_schedule_detail', args=[personal_schedule.id]),
        'djangoEditHref': reverse('reporting:personal_schedule_edit', args=[personal_schedule.id]) if can_edit else '',
        'statusUpdateHref': '',
        'deleteHref': reverse('reporting:personal_schedules_delete_api', args=[personal_schedule.id]) if can_edit else '',
        'canEdit': can_edit,
        'statusOptions': [],
        'customerHref': '',
        'djangoCustomerHref': '',
        'createHistoryHref': '',
    }


def _personal_schedule_detail_response(request, personal_schedule, message=''):
    can_edit = _personal_schedule_can_edit(request.user, personal_schedule)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'message': message,
        'scheduleId': personal_schedule.id,
        'href': _personal_schedule_react_href(personal_schedule),
        'schedule': _personal_schedule_payload(personal_schedule, request.user),
        'links': {
            'calendar': '/schedules/calendar/',
            'djangoCalendar': reverse('reporting:schedule_calendar'),
            'djangoDetail': reverse('reporting:personal_schedule_detail', args=[personal_schedule.id]),
            'djangoEdit': reverse('reporting:personal_schedule_edit', args=[personal_schedule.id]) if can_edit else '',
            'deleteSchedule': reverse('reporting:personal_schedules_delete_api', args=[personal_schedule.id]) if can_edit else '',
        },
        'edit': {
            'canEdit': can_edit,
            'message': '' if can_edit else '본인 개인 일정만 수정할 수 있습니다.',
            'submitUrl': reverse('reporting:personal_schedules_update_api', args=[personal_schedule.id]) if can_edit else '',
            'djangoUrl': reverse('reporting:personal_schedule_edit', args=[personal_schedule.id]) if can_edit else '',
        },
    })


def _ensure_personal_schedule_history(personal_schedule):
    updated = History.objects.filter(
        personal_schedule=personal_schedule,
        parent_history__isnull=True,
    ).update(
        user_id=personal_schedule.user_id,
        company_id=personal_schedule.company_id,
        action_type='memo',
        content=f"개인 일정: {personal_schedule.title}",
        created_by_id=personal_schedule.user_id,
    )
    if updated:
        return
    History.objects.create(
        user=personal_schedule.user,
        company=personal_schedule.company,
        personal_schedule=personal_schedule,
        action_type='memo',
        content=f"개인 일정: {personal_schedule.title}",
        created_by=personal_schedule.user,
    )


def _parse_personal_schedule_payload(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    title = str(payload.get('title') or '').strip()[:200]
    content = str(payload.get('content') or '').strip()
    schedule_date = _parse_iso_date_or_none(payload.get('scheduleDate') or payload.get('schedule_date'))
    schedule_time = _parse_time_or_none(payload.get('scheduleTime') or payload.get('schedule_time'))

    if not title:
        return None, JsonResponse({'success': False, 'error': '일정 제목을 입력하세요.'}, status=400)
    if not schedule_date:
        return None, JsonResponse({'success': False, 'error': '일정 날짜를 선택하세요.'}, status=400)
    if not schedule_time:
        return None, JsonResponse({'success': False, 'error': '일정 시간을 선택하세요.'}, status=400)

    return {
        'title': title,
        'content': content,
        'schedule_date': schedule_date,
        'schedule_time': schedule_time,
    }, None


class PersonalScheduleForm(forms.ModelForm):
    """개인 일정 폼"""
    
    class Meta:
        model = PersonalSchedule
        fields = ['title', 'content', 'schedule_date', 'schedule_time']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '일정 제목을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '일정 내용을 입력하세요 (선택사항)'
            }),
            'schedule_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'schedule_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }
        labels = {
            'title': '일정 제목',
            'content': '일정 내용',
            'schedule_date': '날짜',
            'schedule_time': '시간',
        }


@login_required
def personal_schedule_create_view(request):
    """개인 일정 생성"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = PersonalScheduleForm(request.POST)
        if form.is_valid():
            personal_schedule = form.save(commit=False)
            personal_schedule.user = request.user
            personal_schedule.company = user_profile.company
            personal_schedule.save()
            
            # 개인 일정 생성 시 History 레코드 생성
            History.objects.create(
                user=request.user,
                company=user_profile.company,
                personal_schedule=personal_schedule,
                action_type='memo',  # 개인 일정은 memo 타입으로
                content=f"개인 일정: {personal_schedule.title}",
                created_by=request.user
            )
            
            messages.success(request, '개인 일정이 생성되었습니다.')
            return redirect('reporting:schedule_calendar')
    else:
        # GET 파라미터에서 날짜/시간 받기 (캘린더에서 더블클릭한 경우)
        initial = {}
        if request.GET.get('date'):
            initial['schedule_date'] = request.GET.get('date')
        if request.GET.get('time'):
            initial['schedule_time'] = request.GET.get('time')
        
        form = PersonalScheduleForm(initial=initial)
    
    return render(request, 'reporting/personal_schedule_form.html', {
        'form': form,
        'title': '새 일정 추가'
    })


@never_cache
@require_http_methods(["POST"])
def personal_schedules_create_api(request):
    """React 캘린더용 개인 일정 생성 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.is_manager():
        return JsonResponse({
            'success': False,
            'error': 'Manager는 일정을 직접 생성할 수 없습니다.',
        }, status=403)

    parsed, error_response = _parse_personal_schedule_payload(request)
    if error_response:
        return error_response

    personal_schedule = PersonalSchedule.objects.create(
        user=request.user,
        company=user_profile.company,
        **parsed,
    )
    _ensure_personal_schedule_history(personal_schedule)

    response = _personal_schedule_detail_response(request, personal_schedule, '개인 일정을 등록했습니다.')
    response.status_code = 201
    return response


@never_cache
@require_http_methods(["GET"])
def personal_schedules_detail_api(request, pk):
    """React 캘린더용 개인 일정 상세 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    personal_schedule = get_object_or_404(
        PersonalSchedule.objects.select_related('user', 'company'),
        pk=pk,
    )
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if not _personal_schedule_can_view(request.user, personal_schedule, user_profile):
        return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)

    return _personal_schedule_detail_response(request, personal_schedule)


@never_cache
@require_http_methods(["POST"])
def personal_schedules_update_api(request, pk):
    """React 캘린더용 개인 일정 수정 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    personal_schedule = get_object_or_404(
        PersonalSchedule.objects.select_related('user', 'company'),
        pk=pk,
    )
    if not _personal_schedule_can_edit(request.user, personal_schedule):
        return JsonResponse({'success': False, 'error': '본인 개인 일정만 수정할 수 있습니다.'}, status=403)

    parsed, error_response = _parse_personal_schedule_payload(request)
    if error_response:
        return error_response

    personal_schedule.title = parsed['title']
    personal_schedule.content = parsed['content']
    personal_schedule.schedule_date = parsed['schedule_date']
    personal_schedule.schedule_time = parsed['schedule_time']
    personal_schedule.save(update_fields=['title', 'content', 'schedule_date', 'schedule_time', 'updated_at'])
    _ensure_personal_schedule_history(personal_schedule)

    return _personal_schedule_detail_response(request, personal_schedule, '개인 일정을 수정했습니다.')


@never_cache
@require_http_methods(["POST"])
def personal_schedules_delete_api(request, pk):
    """React 캘린더용 개인 일정 삭제 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    personal_schedule = get_object_or_404(
        PersonalSchedule.objects.select_related('user'),
        pk=pk,
    )
    if not _personal_schedule_can_edit(request.user, personal_schedule):
        return JsonResponse({'success': False, 'error': '본인 개인 일정만 삭제할 수 있습니다.'}, status=403)

    personal_schedule.delete()
    return JsonResponse({'success': True, 'message': '개인 일정을 삭제했습니다.'})


@login_required
def personal_schedule_edit_view(request, pk):
    """개인 일정 수정"""
    personal_schedule = get_object_or_404(PersonalSchedule, pk=pk)
    
    # 권한 확인: 본인 또는 매니저만 수정 가능
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if personal_schedule.user != request.user and not user_profile.can_view_all_users():
        messages.error(request, '이 일정을 수정할 권한이 없습니다.')
        return redirect('reporting:schedule_calendar')
    
    if request.method == 'POST':
        form = PersonalScheduleForm(request.POST, instance=personal_schedule)
        if form.is_valid():
            form.save()
            messages.success(request, '개인 일정이 수정되었습니다.')
            return redirect('reporting:personal_schedule_detail', pk=pk)
    else:
        form = PersonalScheduleForm(instance=personal_schedule)
    
    return render(request, 'reporting/personal_schedule_form.html', {
        'form': form,
        'personal_schedule': personal_schedule,
        'title': '일정 수정'
    })


@login_required
def personal_schedule_detail_view(request, pk):
    """개인 일정 상세 + 댓글"""
    personal_schedule = get_object_or_404(PersonalSchedule, pk=pk)
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    # 권한 확인
    if personal_schedule.user != request.user and not user_profile.can_view_all_users():
        messages.error(request, '이 일정을 볼 권한이 없습니다.')
        return redirect('reporting:schedule_calendar')
    
    # 개인 일정의 메인 History 찾기
    main_history = History.objects.filter(
        personal_schedule=personal_schedule,
        parent_history__isnull=True
    ).first()
    
    # 댓글(답글 메모) 조회 - 메인 History의 답글들
    comments = []
    if main_history:
        comments = main_history.reply_memos.select_related('user', 'created_by').order_by('created_at')
    
    return render(request, 'reporting/personal_schedule_detail.html', {
        'personal_schedule': personal_schedule,
        'comments': comments,
        'user_profile': user_profile
    })


@login_required
@require_http_methods(["POST"])
def personal_schedule_add_comment(request, pk):
    """개인 일정에 댓글 추가"""
    personal_schedule = get_object_or_404(PersonalSchedule, pk=pk)
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'status': 'error', 'message': '내용을 입력하세요.'}, status=400)
    
    # 개인 일정의 메인 History 찾기 (parent_history가 None인 것)
    main_history = History.objects.filter(
        personal_schedule=personal_schedule,
        parent_history__isnull=True
    ).first()
    
    if not main_history:
        # 메인 History가 없으면 생성 (기존 개인 일정의 경우)
        main_history = History.objects.create(
            user=personal_schedule.user,
            company=personal_schedule.company,
            personal_schedule=personal_schedule,
            action_type='memo',
            content=f"개인 일정: {personal_schedule.title}",
            created_by=personal_schedule.user
        )
    
    # 댓글을 답글(reply_memo)로 생성
    comment = History.objects.create(
        user=request.user,
        company=user_profile.company,
        personal_schedule=personal_schedule,
        parent_history=main_history,  # 메인 History에 연결
        action_type='memo',
        content=content,
        created_by=request.user
    )
    
    return JsonResponse({
        'status': 'success',
        'message': '댓글이 등록되었습니다.',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'user_name': comment.user.username,
        }
    })


@login_required
@require_http_methods(["POST"])
def personal_schedule_delete_view(request, pk):
    """개인 일정 삭제"""
    personal_schedule = get_object_or_404(PersonalSchedule, pk=pk)
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    # 권한 확인
    if personal_schedule.user != request.user and not user_profile.can_view_all_users():
        return JsonResponse({'status': 'error', 'message': '삭제 권한이 없습니다.'}, status=403)
    
    personal_schedule.delete()
    messages.success(request, '개인 일정이 삭제되었습니다.')
    
    return JsonResponse({'status': 'success', 'message': '일정이 삭제되었습니다.'})


@login_required
@require_http_methods(["POST"])
def personal_schedule_edit_comment(request, comment_id):
    """개인 일정 댓글 수정"""
    comment = get_object_or_404(History, pk=comment_id, action_type='memo')
    
    # 권한 확인: 댓글 작성자만 수정 가능
    if comment.created_by != request.user:
        return JsonResponse({'status': 'error', 'message': '수정 권한이 없습니다.'}, status=403)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'status': 'error', 'message': '내용을 입력하세요.'}, status=400)
    
    comment.content = content
    comment.save()
    
    return JsonResponse({
        'status': 'success',
        'message': '댓글이 수정되었습니다.',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_http_methods(["POST"])
def personal_schedule_delete_comment(request, comment_id):
    """개인 일정 댓글 삭제"""
    comment = get_object_or_404(History, pk=comment_id, action_type='memo')
    
    # 권한 확인: 댓글 작성자만 삭제 가능
    if comment.created_by != request.user:
        return JsonResponse({'status': 'error', 'message': '삭제 권한이 없습니다.'}, status=403)
    
    comment.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': '댓글이 삭제되었습니다.'
    })
