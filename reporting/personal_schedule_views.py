"""
개인 일정 (PersonalSchedule) 관련 뷰
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms
from django.views.decorators.http import require_http_methods
from .models import PersonalSchedule, History, UserProfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
