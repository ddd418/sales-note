"""
TODOLIST 뷰
- 실무자: 내 할 일, 받은 일, 맡긴 일
- 매니저: 업무 하달, 진행 현황, 워크로드
"""
import json

from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from .models import Todo, TodoAttachment, TodoLog, TodoCategory


# ============================================
# 메인 목록
# ============================================

@login_required
def todo_list(request):
    """TODOLIST 메인 페이지 (탭 구조)"""
    user = request.user
    
    # 탭별 카운트
    my_count = Todo.objects.filter(
        created_by=user, 
        assigned_to__isnull=True,
        status='ongoing'  # 진행중만 카운트 (보류, 완료 제외)
    ).count()
    
    received_count = Todo.objects.filter(
        assigned_to=user,
        status__in=['pending', 'ongoing']  # 승인대기 + 진행중만 카운트 (보류, 완료 제외)
    ).exclude(
        created_by=user,
        requested_by__isnull=True
    ).count()
    
    requested_count = Todo.objects.filter(
        requested_by=user,
        status__in=['pending', 'ongoing']  # 승인대기 + 진행중만 카운트 (보류, 완료 제외)
    ).exclude(assigned_to=user).count()
    
    context = {
        'my_count': my_count,
        'received_count': received_count,
        'requested_count': requested_count,
        'active_tab': request.GET.get('tab', 'my'),
        'categories': TodoCategory.objects.filter(created_by=user),
    }
    return render(request, 'todos/todo_list.html', context)


@login_required
def todo_my_list(request):
    """내 할 일 목록 (직접 생성한 TODO)"""
    user = request.user
    status_filter = request.GET.get('status', 'active')
    
    queryset = Todo.objects.filter(
        created_by=user,
        assigned_to__isnull=True  # 남에게 할당하지 않은 것
    ).select_related('related_client')
    
    if status_filter == 'active':
        queryset = queryset.filter(status='ongoing')
    elif status_filter == 'on_hold':
        queryset = queryset.filter(status='on_hold')
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    elif status_filter == 'all':
        pass  # 전체
    
    queryset = queryset.order_by('-created_at')
    
    # 페이징
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    todos = paginator.get_page(page)
    
    context = {
        'todos': todos,
        'status_filter': status_filter,
        'tab': 'my',
    }
    
    # HTMX 요청이면 partial 반환
    if request.headers.get('HX-Request'):
        return render(request, 'todos/partials/todo_table.html', context)
    return render(request, 'todos/todo_my_list.html', context)


@login_required
def todo_received_list(request):
    """받은 일 목록 (동료 요청 + 매니저 하달)"""
    user = request.user
    status_filter = request.GET.get('status', 'active')
    
    # 받은 일: 내가 담당자이면서, 다른 사람이 요청한 것만
    # (자기가 만든 할일은 '내 할일'에 표시)
    queryset = Todo.objects.filter(
        assigned_to=user
    ).exclude(
        created_by=user,  # 자기가 만든 건 제외
        requested_by__isnull=True  # 위임받은 게 아닌 경우만 제외
    ).select_related('created_by', 'requested_by', 'related_client')
    
    if status_filter == 'active':
        queryset = queryset.filter(status='ongoing')  # 진행중만
    elif status_filter == 'pending':
        queryset = queryset.filter(status='pending')  # 승인대기만
    elif status_filter == 'rejected':
        queryset = queryset.filter(status='rejected')  # 반려만
    elif status_filter == 'on_hold':
        queryset = queryset.filter(status='on_hold')
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    elif status_filter == 'all':
        pass  # 전체
    
    queryset = queryset.order_by('-created_at')
    
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    todos = paginator.get_page(page)
    
    context = {
        'todos': todos,
        'status_filter': status_filter,
        'tab': 'received',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'todos/partials/todo_table.html', context)
    return render(request, 'todos/todo_received_list.html', context)


@login_required
def todo_requested_list(request):
    """맡긴 일 목록 (내가 다른 사람에게 요청한 것)"""
    user = request.user
    status_filter = request.GET.get('status', 'active')
    
    queryset = Todo.objects.filter(
        requested_by=user
    ).exclude(
        assigned_to=user  # 자기 자신에게 요청한 건 제외
    ).select_related('assigned_to', 'related_client')
    
    if status_filter == 'active':
        queryset = queryset.filter(status='ongoing')  # 진행중만
    elif status_filter == 'pending':
        queryset = queryset.filter(status='pending')  # 승인대기만
    elif status_filter == 'rejected':
        queryset = queryset.filter(status='rejected')  # 반려만
    elif status_filter == 'on_hold':
        queryset = queryset.filter(status='on_hold')
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    elif status_filter == 'all':
        pass  # 전체
    
    queryset = queryset.order_by('-created_at')
    
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    todos = paginator.get_page(page)
    
    context = {
        'todos': todos,
        'status_filter': status_filter,
        'tab': 'requested',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'todos/partials/todo_table.html', context)
    return render(request, 'todos/todo_requested_list.html', context)


# ============================================
# CRUD
# ============================================

@login_required
def todo_create(request):
    """TODO 생성"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date') or None
        expected_duration = request.POST.get('expected_duration') or None
        related_client_id = request.POST.get('related_client') or None
        category_id = request.POST.get('category') or None
        
        if not title:
            messages.error(request, '제목을 입력해주세요.')
            return redirect('todos:create')
        
        todo = Todo.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            expected_duration=expected_duration,
            related_client_id=related_client_id,
            category_id=category_id,
            created_by=request.user,
            source_type=Todo.SourceType.SELF,
            status=Todo.Status.ONGOING,
        )
        
        # 로그 기록
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.CREATED,
            message="TODO 생성",
            new_status='ongoing'
        )
        
        # 첨부파일 처리
        files = request.FILES.getlist('attachments')
        for f in files:
            TodoAttachment.objects.create(
                todo=todo,
                file=f,
                filename=f.name,
                uploaded_by=request.user
            )
        
        messages.success(request, f'"{title}" TODO가 생성되었습니다.')
        
        # HTMX 요청이면
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={'HX-Trigger': 'todoCreated'})
        
        return redirect('todos:list')
    
    # GET: 폼 표시
    context = {
        'duration_choices': Todo.Duration.choices,
        'categories': TodoCategory.objects.filter(created_by=request.user),
    }
    return render(request, 'todos/todo_form.html', context)


@login_required
def todo_detail(request, pk):
    """TODO 상세"""
    todo = get_object_or_404(
        Todo.objects.select_related(
            'created_by', 'assigned_to', 'requested_by', 'related_client'
        ).prefetch_related('attachments', 'logs__actor'),
        pk=pk
    )
    
    # 권한 체크: 생성자, 담당자, 요청자만 볼 수 있음
    user = request.user
    if not (todo.created_by == user or todo.assigned_to == user or todo.requested_by == user):
        # 매니저인 경우 허용
        if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
            messages.error(request, '접근 권한이 없습니다.')
            return redirect('todos:list')
    
    context = {
        'todo': todo,
        'logs': todo.logs.all()[:20],
        'attachments': todo.attachments.all(),
    }
    return render(request, 'todos/todo_detail.html', context)


@login_required
def todo_edit(request, pk):
    """TODO 수정"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 매니저 하달 업무는 실무자가 수정 불가 (매니저만 수정 가능)
    if todo.source_type == Todo.SourceType.MANAGER_ASSIGN:
        if todo.requested_by != request.user:
            messages.error(request, '매니저 하달 업무는 매니저만 수정할 수 있습니다.')
            return redirect('todos:detail', pk=pk)
    
    # 권한 체크: 내가 만든 일이고 위임하지 않은 경우만 수정 가능
    # 위임받은 TODO는 수정 불가
    if todo.created_by != request.user or todo.assigned_to is not None:
        messages.error(request, '수정 권한이 없습니다. 위임받은 업무는 수정할 수 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    if request.method == 'POST':
        old_title = todo.title
        
        todo.title = request.POST.get('title', '').strip() or todo.title
        todo.description = request.POST.get('description', '').strip()
        todo.due_date = request.POST.get('due_date') or None
        todo.expected_duration = request.POST.get('expected_duration') or None
        
        category_id = request.POST.get('category') or None
        todo.category_id = category_id
        
        related_client_id = request.POST.get('related_client')
        if related_client_id:
            todo.related_client_id = related_client_id
        else:
            todo.related_client = None
        
        todo.save()
        
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.UPDATED,
            message=f"수정됨 (이전 제목: {old_title})" if old_title != todo.title else "내용 수정됨"
        )
        
        messages.success(request, 'TODO가 수정되었습니다.')
        return redirect('todos:detail', pk=pk)
    
    # GET
    context = {
        'todo': todo,
        'duration_choices': Todo.Duration.choices,
        'categories': TodoCategory.objects.filter(created_by=request.user),
        'edit_mode': True,
    }
    return render(request, 'todos/todo_form.html', context)


@login_required
@require_POST
def todo_delete(request, pk):
    """TODO 삭제"""
    todo = get_object_or_404(Todo, pk=pk)
    title = todo.title
    
    # 매니저 하달 업무는 실무자가 삭제 불가 (매니저만 삭제 가능)
    if todo.source_type == Todo.SourceType.MANAGER_ASSIGN:
        if todo.requested_by != request.user:
            messages.error(request, '매니저 하달 업무는 매니저만 삭제할 수 있습니다.')
            if request.headers.get('HX-Request'):
                return HttpResponse(status=403)
            return redirect('todos:detail', pk=pk)
    
    # Case 1: 내가 위임받은 할일 → 위임 해제, 요청자의 '내 할일'로 전환
    if todo.assigned_to == request.user and todo.requested_by and todo.requested_by != request.user:
        # 위임 해제 - 요청자의 '내 할일'로 전환
        todo.assigned_to = None
        todo.requested_by = None  # 요청자 정보도 제거
        todo.status = 'ongoing'  # 원래 상태로
        # created_by는 원래 요청자이므로 그대로 두면 요청자의 '내 할일'이 됨
        todo.save()
        
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.ASSIGNED,
            message=f"{request.user.get_full_name() or request.user.username}님이 받은 일에서 삭제함 (요청자의 내 할일로 전환)"
        )
        
        messages.success(request, f'"{title}"이(가) 받은 일에서 삭제되었습니다.')
        
        if request.headers.get('HX-Request'):
            # 빈 응답으로 해당 행 삭제
            return HttpResponse('')
        return redirect('todos:received_list')
    
    # Case 2: 내가 맡긴 할일 → DB에서 완전 삭제
    if todo.requested_by == request.user and todo.assigned_to and todo.assigned_to != request.user:
        todo.delete()
        
        messages.success(request, f'"{title}"이(가) 맡긴 일에서 삭제되었습니다.')
        
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        return redirect('todos:requested_list')
    
    # Case 3: 내가 만든 내 할일 → 완전 삭제
    if todo.created_by != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    todo.delete()
    
    messages.success(request, f'"{title}" TODO가 삭제되었습니다.')
    
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    
    return redirect('todos:list')


# ============================================
# 상태 변경
# ============================================

@login_required
@require_POST
def todo_complete(request, pk):
    """TODO 완료 처리"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한: 담당자만 (요청자는 불가)
    # 담당자가 있으면 담당자만 완료 가능
    if todo.assigned_to:
        if todo.assigned_to != request.user:
            messages.error(request, '담당자만 완료 처리할 수 있습니다.')
            return redirect('todos:detail', pk=pk)
    # 담당자가 없으면 생성자가 완료 가능
    elif todo.created_by != request.user:
        messages.error(request, '완료 처리 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    todo.complete(request.user)
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204, headers={'HX-Trigger': 'todoUpdated'})
    
    messages.success(request, f'"{todo.title}" TODO가 완료 처리되었습니다.')
    return redirect('todos:detail', pk=pk)


@login_required
@require_POST
def todo_change_status(request, pk):
    """TODO 상태 변경"""
    todo = get_object_or_404(Todo, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Todo.Status.choices):
        return JsonResponse({'error': '잘못된 상태입니다.'}, status=400)
    
    # 승인 대기 상태일 때는 상태 변경 불가 (승인/반려로만 처리)
    if todo.status == Todo.Status.PENDING:
        return JsonResponse({'error': '승인 대기 중인 업무입니다. 먼저 승인/반려를 결정해주세요.'}, status=403)
    
    # 반려된 상태일 때는 상태 변경 불가
    if todo.status == Todo.Status.REJECTED:
        return JsonResponse({'error': '반려된 업무는 상태를 변경할 수 없습니다.'}, status=403)
    
    # 권한 체크: 담당자가 있으면 담당자만, 없으면 생성자만
    # 요청자(requested_by)는 상태 변경 불가 (맡긴 일은 담당자가 처리)
    user = request.user
    
    if todo.assigned_to:
        # 담당자가 있는 경우: 담당자만 상태 변경 가능
        can_change = (todo.assigned_to == user)
    else:
        # 담당자가 없는 경우: 생성자만 상태 변경 가능
        can_change = (todo.created_by == user)
    
    # 매니저는 항상 변경 가능
    if hasattr(user, 'userprofile') and user.userprofile.role == 'manager':
        can_change = True
    
    if not can_change:
        if todo.requested_by == user:
            return JsonResponse({'error': '맡긴 일은 담당자만 상태를 변경할 수 있습니다.'}, status=403)
        return JsonResponse({'error': '상태 변경 권한이 없습니다.'}, status=403)
    
    prev_status = todo.status
    todo.status = new_status
    
    if new_status == 'done':
        todo.completed_at = timezone.now()
    
    todo.save()
    
    TodoLog.objects.create(
        todo=todo,
        actor=user,
        action_type=TodoLog.ActionType.STATUS_CHANGED,
        message=f"상태 변경: {dict(Todo.Status.choices).get(prev_status)} → {dict(Todo.Status.choices).get(new_status)}",
        prev_status=prev_status,
        new_status=new_status
    )
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204, headers={'HX-Trigger': 'todoUpdated'})
    
    messages.success(request, f'상태가 "{dict(Todo.Status.choices).get(new_status)}"로 변경되었습니다.')
    return redirect('todos:detail', pk=pk)


@login_required
@require_POST
def todo_cancel_request(request, pk):
    """요청 취소 - 동료에게 맡긴 일을 다시 내 할일로 되돌림"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한 체크: 요청자만 취소 가능
    if todo.requested_by != request.user:
        messages.error(request, '요청 취소 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 승인 대기 상태일 때만 취소 가능
    if todo.status != Todo.Status.PENDING:
        messages.error(request, '승인 대기 상태일 때만 요청을 취소할 수 있습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 이전 담당자 기록
    prev_assignee = todo.assigned_to
    prev_assignee_name = prev_assignee.get_full_name() or prev_assignee.username if prev_assignee else None
    
    # 다시 내 할일로 변경
    todo.assigned_to = None
    todo.requested_by = None
    todo.source_type = Todo.SourceType.SELF
    todo.status = Todo.Status.ONGOING
    todo.save()
    
    # 로그 기록
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.STATUS_CHANGED,
        message=f"요청 취소: {prev_assignee_name}에게 맡겼던 일을 회수함",
        prev_status='pending',
        new_status='ongoing'
    )
    
    messages.success(request, f'요청이 취소되었습니다. 다시 내 할 일로 돌아왔습니다.')
    return redirect('todos:detail', pk=pk)


@login_required
@require_POST
def todo_approve_request(request, pk):
    """업무 요청 승인 - 받은 일을 수락"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한 체크: 담당자만 승인 가능
    if todo.assigned_to != request.user:
        messages.error(request, '승인 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 승인 대기 상태일 때만 승인 가능
    if todo.status != Todo.Status.PENDING:
        messages.error(request, '승인 대기 상태가 아닙니다.')
        return redirect('todos:detail', pk=pk)
    
    # 승인 처리: 상태를 진행중으로 변경
    todo.status = Todo.Status.ONGOING
    todo.save()
    
    # 로그 기록
    requester_name = todo.requested_by.get_full_name() or todo.requested_by.username if todo.requested_by else '알 수 없음'
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.APPROVED,
        message=f"{requester_name}님의 업무 요청을 승인함",
        prev_status='pending',
        new_status='ongoing'
    )
    
    messages.success(request, f'업무 요청을 승인했습니다. 이제 내 할 일입니다.')
    return redirect('todos:detail', pk=pk)


@login_required
@require_POST
def todo_reject_request(request, pk):
    """업무 요청 반려 - 받은일에는 반려로 남고, 요청자의 내 할일에는 진행중으로 복제"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한 체크: 담당자만 반려 가능
    if todo.assigned_to != request.user:
        messages.error(request, '반려 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 승인 대기 상태일 때만 반려 가능
    if todo.status != Todo.Status.PENDING:
        messages.error(request, '승인 대기 상태가 아닙니다.')
        return redirect('todos:detail', pk=pk)
    
    reject_reason = request.POST.get('reject_reason', '').strip()
    
    # 요청자 정보 저장
    requester = todo.requested_by
    requester_name = requester.get_full_name() or requester.username if requester else '알 수 없음'
    rejector_name = request.user.get_full_name() or request.user.username
    
    # 1. 요청자의 '내 할일'에 새 TODO 생성 (진행중)
    new_todo = Todo.objects.create(
        title=todo.title,
        description=todo.description,
        created_by=requester,  # 요청자가 생성자
        assigned_to=None,  # 위임 없음
        requested_by=None,  # 요청 없음
        status=Todo.Status.ONGOING,  # 진행중
        due_date=todo.due_date,
        expected_duration=todo.expected_duration,
        related_client=todo.related_client,
        source_type=todo.source_type,
    )
    
    # 새 TODO에 반려 사유 로그 추가
    TodoLog.objects.create(
        todo=new_todo,
        actor=request.user,
        action_type=TodoLog.ActionType.REJECTED,
        message=f"[반려로 인해 생성됨] {rejector_name}님이 반려" + (f"\n사유: {reject_reason}" if reject_reason else ""),
    )
    
    # 2. 기존 TODO는 반려 상태로 변경 (받은 일 - 반려 필터에 표시)
    todo.status = Todo.Status.REJECTED
    
    # 반려 사유를 설명에 추가
    if reject_reason:
        todo.description = f"[반려됨] {rejector_name}님이 반려\n사유: {reject_reason}\n\n" + (todo.description or '')
    else:
        todo.description = f"[반려됨] {rejector_name}님이 반려\n\n" + (todo.description or '')
    
    todo.save()
    
    # 로그 기록
    log_message = f"{rejector_name}이(가) 업무 요청을 반려함"
    if reject_reason:
        log_message += f"\n반려 사유: {reject_reason}"
    
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.REJECTED,
        message=log_message,
        prev_status='pending',
        new_status='rejected'
    )
    
    messages.success(request, f'업무 요청을 반려했습니다. {requester_name}님의 내 할일로 전환되었습니다.')
    return redirect('todos:list')


# ============================================
# 동료 요청
# ============================================

@login_required
def todo_request_to_peer(request):
    """동료에게 업무 요청"""
    from django.contrib.auth.models import User
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date') or None
        
        if not title or not assigned_to_id:
            messages.error(request, '제목과 담당자를 입력해주세요.')
            return redirect('todos:request_to_peer')
        
        assigned_to = get_object_or_404(User, pk=assigned_to_id)
        
        todo = Todo.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            created_by=request.user,
            assigned_to=assigned_to,
            requested_by=request.user,
            source_type=Todo.SourceType.PEER_REQUEST,
            status=Todo.Status.PENDING,  # 승인 대기
        )
        
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.DELEGATED,
            message=f"{assigned_to.get_full_name() or assigned_to.username}에게 업무 요청",
            new_status='pending'
        )
        
        messages.success(request, f'{assigned_to.get_full_name() or assigned_to.username}에게 업무를 요청했습니다.')
        return redirect('todos:list')
    
    # GET: 동료 목록
    peers = User.objects.filter(
        is_active=True
    ).exclude(pk=request.user.pk).order_by('first_name', 'username')
    
    context = {
        'peers': peers,
        'is_request': True,
    }
    return render(request, 'todos/todo_request_form.html', context)


@login_required
@require_POST
def todo_delegate(request, pk):
    """기존 TODO를 동료에게 위임/요청"""
    from django.contrib.auth.models import User
    from reporting.models import UserProfile
    
    todo = get_object_or_404(Todo, pk=pk)
    
    # 위임받은 TODO는 재위임 불가
    if todo.requested_by and todo.requested_by != request.user:
        messages.error(request, '위임받은 업무는 다시 위임할 수 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 권한 체크: 생성자만 위임 가능 (담당자가 없는 경우)
    if todo.created_by != request.user or todo.assigned_to is not None:
        messages.error(request, '이 TODO를 위임할 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    assigned_to_id = request.POST.get('assigned_to')
    delegate_message = request.POST.get('delegate_message', '').strip()
    
    if not assigned_to_id:
        messages.error(request, '담당자를 선택해주세요.')
        return redirect('todos:detail', pk=pk)
    
    assigned_to = get_object_or_404(User, pk=assigned_to_id)
    
    # 자기 자신에게 위임 불가
    if assigned_to == request.user:
        messages.error(request, '자기 자신에게는 위임할 수 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    # 이전 담당자 기록
    prev_assignee = todo.assigned_to
    prev_assignee_name = prev_assignee.get_full_name() or prev_assignee.username if prev_assignee else None
    
    # 위임 처리
    todo.assigned_to = assigned_to
    todo.requested_by = request.user  # 위임 요청자 기록
    todo.source_type = Todo.SourceType.PEER_REQUEST  # 출처를 동료 요청으로 변경
    todo.status = Todo.Status.PENDING  # 승인 대기 상태로 변경
    
    # 설명에 위임 메시지 추가
    if delegate_message:
        todo.description = f"[위임 메시지] {delegate_message}\n\n" + (todo.description or '')
    
    todo.save()
    
    # 로그 기록
    log_message = f"{request.user.get_full_name() or request.user.username}이(가) {assigned_to.get_full_name() or assigned_to.username}에게 위임"
    if prev_assignee_name:
        log_message += f" (이전 담당: {prev_assignee_name})"
    if delegate_message:
        log_message += f"\n메시지: {delegate_message}"
    
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.DELEGATED,
        message=log_message,
        prev_status=todo.status,
        new_status='pending'
    )
    
    messages.success(request, f'{assigned_to.get_full_name() or assigned_to.username}에게 업무를 위임했습니다.')
    return redirect('todos:detail', pk=pk)


@login_required
def api_get_colleagues(request):
    """같은 회사 동료 목록 조회 API (실무자만, 매니저 제외)"""
    from django.contrib.auth.models import User
    from reporting.models import UserProfile
    
    user = request.user
    
    try:
        # 현재 사용자의 회사 정보
        user_profile = UserProfile.objects.get(user=user)
        user_company = user_profile.company
        
        if user_company:
            # 같은 회사 동료 중 실무자(salesman)만 조회 (매니저, 관리자 제외)
            colleagues = User.objects.filter(
                is_active=True,
                userprofile__company=user_company,
                userprofile__role='salesman'  # 실무자만
            ).exclude(pk=user.pk).select_related('userprofile').order_by('first_name', 'username')
        else:
            # 회사 정보가 없으면 모든 실무자
            colleagues = User.objects.filter(
                is_active=True,
                userprofile__role='salesman'  # 실무자만
            ).exclude(pk=user.pk).order_by('first_name', 'username')
    except UserProfile.DoesNotExist:
        # 프로필이 없으면 모든 실무자
        colleagues = User.objects.filter(
            is_active=True,
            userprofile__role='salesman'  # 실무자만
        ).exclude(pk=user.pk).order_by('first_name', 'username')
    
    results = []
    for colleague in colleagues:
        role = ''
        try:
            role = colleague.userprofile.get_role_display()
        except:
            pass
        
        results.append({
            'id': colleague.pk,
            'username': colleague.username,
            'full_name': colleague.get_full_name() or colleague.username,
            'role': role,
        })
    
    return JsonResponse({'colleagues': results})


# ============================================
# 매니저 기능
# ============================================

@login_required
def manager_dashboard(request):
    """매니저 대시보드 - 업무 하달 현황"""
    from django.contrib.auth.models import User
    
    user = request.user
    
    # 매니저 권한 체크
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:list')
    
    # 매니저의 회사 확인
    manager_company = user.userprofile.company
    if not manager_company:
        messages.error(request, '소속 회사 정보가 없습니다.')
        return redirect('reporting:dashboard')
    
    # 내가 하달한 업무
    assigned_todos = Todo.objects.filter(
        requested_by=user,
        source_type=Todo.SourceType.MANAGER_ASSIGN
    ).select_related('assigned_to', 'related_client', 'related_client__company').prefetch_related('attachments')
    
    # 필터 적용
    status_filter = request.GET.get('status', 'all')
    assignee_filter = request.GET.get('assignee', '')
    
    filtered_todos = assigned_todos
    if status_filter and status_filter != 'all':
        filtered_todos = filtered_todos.filter(status=status_filter)
    if assignee_filter:
        filtered_todos = filtered_todos.filter(assigned_to_id=assignee_filter)
    
    # 상태별 집계
    status_counts = assigned_todos.values('status').annotate(count=Count('id'))
    total_count = assigned_todos.count()
    
    # 담당자별 요약 (같은 회사 실무자만)
    team_members = User.objects.filter(
        is_active=True,
        userprofile__role='salesman',
        userprofile__company=manager_company  # 같은 회사만
    ).exclude(pk=user.pk).order_by('first_name', 'username')
    
    assignee_summary = []
    for member in team_members:
        member_todos = assigned_todos.filter(assigned_to=member)
        total = member_todos.count()
        if total > 0:
            done = member_todos.filter(status='done').count()
            ongoing = member_todos.filter(status='ongoing').count()
            on_hold = member_todos.filter(status='on_hold').count()
            assignee_summary.append({
                'name': member.get_full_name() or member.username,
                'total': total,
                'done': done,
                'ongoing': ongoing,
                'on_hold': on_hold,
                'done_percent': (done / total * 100) if total > 0 else 0,
                'ongoing_percent': (ongoing / total * 100) if total > 0 else 0,
                'on_hold_percent': (on_hold / total * 100) if total > 0 else 0,
            })
    
    context = {
        'assigned_todos': filtered_todos.order_by('-created_at')[:100],
        'status_counts': {s['status']: s['count'] for s in status_counts},
        'total_count': total_count,
        'assignee_summary': assignee_summary,
        'team_members': team_members,
        'status_filter': status_filter,
        'assignee_filter': assignee_filter,
    }
    return render(request, 'todos/manager_dashboard.html', context)


@login_required
@require_POST
def manager_assign(request):
    """매니저 업무 하달 (복수 담당자, 첨부파일 지원)"""
    from django.contrib.auth.models import User
    from reporting.models import FollowUp
    
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:manager_dashboard')
    
    # 매니저의 회사 확인
    manager_company = user.userprofile.company
    if not manager_company:
        messages.error(request, '소속 회사 정보가 없습니다.')
        return redirect('todos:manager_dashboard')
    
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    assigned_to_ids = request.POST.getlist('assigned_to')  # 복수 선택
    due_date = request.POST.get('due_date') or None
    task_type = request.POST.get('task_type', 'general')
    related_client_id = request.POST.get('related_client') or None
    files = request.FILES.getlist('files')
    
    if not title or not assigned_to_ids:
        messages.error(request, '업무 내용과 담당자를 선택해주세요.')
        return redirect('todos:manager_dashboard')
    
    # 고객형인 경우 고객 확인 (같은 회사의 고객만)
    related_client = None
    if task_type == 'customer' and related_client_id:
        try:
            related_client = FollowUp.objects.get(
                pk=related_client_id,
                user__userprofile__company=manager_company  # 같은 회사 소속 실무자의 고객만
            )
        except FollowUp.DoesNotExist:
            pass
    
    # 각 담당자에게 업무 하달 (같은 회사 실무자만)
    created_count = 0
    for assigned_to_id in assigned_to_ids:
        try:
            assigned_to = User.objects.get(
                pk=assigned_to_id, 
                is_active=True,
                userprofile__company=manager_company  # 같은 회사만
            )
        except User.DoesNotExist:
            continue
        
        todo = Todo.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            created_by=user,
            assigned_to=assigned_to,
            requested_by=user,
            related_client=related_client,
            source_type=Todo.SourceType.MANAGER_ASSIGN,
            status=Todo.Status.ONGOING,  # 매니저 하달은 바로 진행중
        )
        
        # 첨부파일 저장
        for f in files:
            TodoAttachment.objects.create(
                todo=todo,
                file=f,
                filename=f.name,
                uploaded_by=user,
            )
        
        TodoLog.objects.create(
            todo=todo,
            actor=user,
            action_type=TodoLog.ActionType.ASSIGNED,
            message=f"매니저 업무 하달: {assigned_to.get_full_name() or assigned_to.username}",
            new_status='ongoing'
        )
        created_count += 1
    
    if created_count > 0:
        messages.success(request, f'{created_count}명에게 업무를 하달했습니다.')
    else:
        messages.error(request, '업무 하달에 실패했습니다.')
    
    return redirect('todos:manager_dashboard')


@login_required
def manager_task_detail(request, pk):
    """매니저 - 하달 업무 상세 보기"""
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:manager_dashboard')
    
    todo = get_object_or_404(
        Todo.objects.select_related('assigned_to', 'related_client', 'related_client__company').prefetch_related('attachments', 'logs'),
        pk=pk, 
        requested_by=user,
        source_type=Todo.SourceType.MANAGER_ASSIGN
    )
    
    # 첨부파일 분류 (매니저가 올린 것 vs 실무자가 올린 것)
    manager_attachments = todo.attachments.filter(uploaded_by=user)
    completion_attachments = todo.attachments.exclude(uploaded_by=user)
    
    context = {
        'todo': todo,
        'manager_attachments': manager_attachments,
        'completion_attachments': completion_attachments,
    }
    return render(request, 'todos/manager_task_detail.html', context)


@login_required
@require_POST
def manager_update_status(request, pk):
    """매니저 - 하달 업무 상태 변경"""
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        return JsonResponse({'error': '권한 없음'}, status=403)
    
    todo = get_object_or_404(
        Todo, pk=pk, requested_by=user, source_type=Todo.SourceType.MANAGER_ASSIGN
    )
    
    new_status = request.POST.get('status')
    if new_status not in ['ongoing', 'on_hold', 'done']:
        messages.error(request, '잘못된 상태입니다.')
        return redirect('todos:manager_task_detail', pk=pk)
    
    prev_status = todo.status
    todo.status = new_status
    if new_status == 'done':
        todo.completed_at = timezone.now()
    todo.save()
    
    TodoLog.objects.create(
        todo=todo,
        actor=user,
        action_type=TodoLog.ActionType.STATUS_CHANGED,
        message=f"매니저가 상태 변경",
        prev_status=prev_status,
        new_status=new_status
    )
    
    messages.success(request, '상태가 변경되었습니다.')
    return redirect('todos:manager_task_detail', pk=pk)


@login_required
@require_POST
def manager_cancel_task(request, pk):
    """매니저 - 하달 업무 취소 (삭제)"""
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'error': '권한 없음'}, status=403)
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:manager_dashboard')
    
    todo = get_object_or_404(
        Todo, pk=pk, requested_by=user, source_type=Todo.SourceType.MANAGER_ASSIGN
    )
    
    # 삭제 전 로그
    todo_title = todo.title
    assigned_to_name = todo.assigned_to.get_full_name() or todo.assigned_to.username if todo.assigned_to else ''
    
    todo.delete()
    
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'success': True})
    
    messages.success(request, f'업무 "{todo_title}"가 취소되었습니다.')
    return redirect('todos:manager_dashboard')


@login_required
@require_POST
def upload_completion_file(request, pk):
    """실무자 - 매니저 하달 업무에 증빙자료 업로드"""
    user = request.user
    
    todo = get_object_or_404(
        Todo, pk=pk, assigned_to=user, source_type=Todo.SourceType.MANAGER_ASSIGN
    )
    
    files = request.FILES.getlist('files')
    if not files:
        messages.error(request, '파일을 선택해주세요.')
        return redirect('todos:detail', pk=pk)
    
    for f in files:
        TodoAttachment.objects.create(
            todo=todo,
            file=f,
            filename=f.name,
            uploaded_by=user,
        )
    
    TodoLog.objects.create(
        todo=todo,
        actor=user,
        action_type=TodoLog.ActionType.COMMENTED,
        message=f"증빙자료 {len(files)}개 업로드",
    )
    
    messages.success(request, f'{len(files)}개의 증빙자료가 업로드되었습니다.')
    return redirect('todos:detail', pk=pk)


@login_required
def manager_workload(request):
    """팀원별 워크로드 현황"""
    from django.contrib.auth.models import User
    
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:list')
    
    # 팀원별 진행중인 업무 수
    workload = User.objects.filter(
        is_active=True
    ).annotate(
        ongoing_count=Count('assigned_todos', filter=Q(assigned_todos__status='ongoing')),
        pending_count=Count('assigned_todos', filter=Q(assigned_todos__status='pending')),
        total_active=Count('assigned_todos', filter=Q(assigned_todos__status__in=['ongoing', 'pending', 'on_hold']))
    ).order_by('-total_active')
    
    context = {
        'workload': workload,
    }
    return render(request, 'todos/manager_workload.html', context)


# ============================================
# API (HTMX용)
# ============================================

@login_required
@require_POST
def api_quick_add(request):
    """빠른 TODO 추가 (HTMX)"""
    title = request.POST.get('title', '').strip()
    
    if not title:
        return HttpResponse('<div class="text-danger">제목을 입력해주세요.</div>', status=400)
    
    todo = Todo.objects.create(
        title=title,
        created_by=request.user,
        source_type=Todo.SourceType.SELF,
        status=Todo.Status.ONGOING,
    )
    
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.CREATED,
        message="빠른 추가로 생성",
        new_status='ongoing'
    )
    
    # 새로 생성된 TODO 행 반환
    return render(request, 'todos/partials/todo_row.html', {'todo': todo})


@login_required
@require_POST
def api_toggle_status(request, pk):
    """TODO 상태 토글 (ongoing ↔ done)"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한 체크
    if todo.assigned_to:
        if todo.assigned_to != request.user:
            return HttpResponse(status=403)
    elif todo.created_by != request.user:
        return HttpResponse(status=403)
    
    prev_status = todo.status
    
    if todo.status == 'done':
        todo.status = Todo.Status.ONGOING
        todo.completed_at = None
    else:
        todo.status = Todo.Status.DONE
        todo.completed_at = timezone.now()
    
    todo.save()
    
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.STATUS_CHANGED,
        message=f"상태 토글: {prev_status} → {todo.status}",
        prev_status=prev_status,
        new_status=todo.status
    )
    
    # tab 파라미터 가져오기
    tab = request.POST.get('tab', 'my')
    
    response = render(request, 'todos/partials/todo_row.html', {'todo': todo, 'tab': tab})
    
    # HX-Trigger 헤더로 카운트 업데이트 정보 전달
    import json
    trigger_data = json.dumps({
        'todoStatusChanged': {
            'tab': tab,
            'prevStatus': prev_status,
            'newStatus': todo.status
        }
    })
    response['HX-Trigger'] = trigger_data
    
    return response


@login_required
def api_search_clients(request):
    """고객 검색 API (모달용)"""
    from reporting.models import FollowUp
    
    query = request.GET.get('q', '').strip()
    user = request.user
    
    if not query:
        return JsonResponse({'results': []})
    
    # 기본 검색 조건
    search_filter = Q(customer_name__icontains=query) | Q(company__name__icontains=query)
    
    # 매니저는 회사 내 모든 고객, 실무자는 본인 고객만
    if hasattr(user, 'userprofile') and user.userprofile.role == 'manager' and user.userprofile.company:
        # 매니저: 같은 회사 소속 실무자들의 모든 고객
        clients = FollowUp.objects.filter(
            search_filter,
            user__userprofile__company=user.userprofile.company
        ).select_related('company', 'user').order_by('customer_name')[:20]
    else:
        # 실무자: 본인 담당 고객만
        clients = FollowUp.objects.filter(
            search_filter,
            user=user
        ).select_related('company').order_by('customer_name')[:20]
    
    results = [
        {
            'id': client.id,
            'customer_name': client.customer_name or '(이름 없음)',
            'company_name': client.company.name if client.company else '',
        }
        for client in clients
    ]
    
    return JsonResponse({'results': results})


# ============================================
# 카테고리 관리
# ============================================

@login_required
def category_list(request):
    """카테고리 목록 (JSON API)"""
    categories = TodoCategory.objects.filter(created_by=request.user).values('id', 'name', 'color')
    return JsonResponse({'categories': list(categories)})


@login_required
@require_http_methods(["POST"])
def category_create(request):
    """카테고리 생성"""
    name = request.POST.get('name', '').strip()
    color = request.POST.get('color', '#6c757d').strip()
    
    if not name:
        return JsonResponse({'success': False, 'error': '카테고리 이름을 입력해주세요.'}, status=400)
    
    if len(name) > 50:
        return JsonResponse({'success': False, 'error': '카테고리 이름은 50자 이하여야 합니다.'}, status=400)

    # color 유효성 검증 (HEX 형식)
    import re
    if not re.match(r'^#[0-9a-fA-F]{6}$', color):
        color = '#6c757d'

    category, created = TodoCategory.objects.get_or_create(
        name=name,
        created_by=request.user,
        defaults={'color': color}
    )
    
    if not created:
        return JsonResponse({'success': False, 'error': '동일한 이름의 카테고리가 이미 존재합니다.'}, status=400)
    
    return JsonResponse({'success': True, 'id': category.id, 'name': category.name, 'color': category.color})


@login_required
@require_http_methods(["POST"])
def category_delete(request, pk):
    """카테고리 삭제"""
    category = get_object_or_404(TodoCategory, pk=pk, created_by=request.user)
    name = category.name
    # 연결된 todo의 category를 NULL로 해제 후 삭제
    category.todos.update(category=None)
    category.delete()
    return JsonResponse({'success': True, 'message': f'"{name}" 카테고리가 삭제되었습니다.'})


# ============================================
# React CRM API
# ============================================

TASK_ACTIVE_STATUSES = [Todo.Status.PENDING, Todo.Status.ONGOING, Todo.Status.ON_HOLD]


def _tasks_api_login_required_response(request):
    if request.user.is_authenticated:
        return None
    return JsonResponse({
        'success': False,
        'error': 'login_required',
        'message': '로그인이 필요합니다.',
        'loginUrl': reverse('reporting:login'),
    }, status=401)


def _tasks_user_profile(user):
    from reporting.models import UserProfile

    try:
        return user.userprofile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user, role='salesman')


def _tasks_user_name(user):
    if not user:
        return ''
    return user.get_full_name() or user.username


def _tasks_user_payload(user):
    if not user:
        return None
    profile = getattr(user, 'userprofile', None)
    company = profile.company if profile else None
    return {
        'id': user.id,
        'name': _tasks_user_name(user),
        'username': user.username,
        'role': profile.role if profile else '',
        'roleLabel': profile.get_role_display() if profile else '',
        'company': company.name if company else '',
    }


def _tasks_is_manager(user):
    profile = _tasks_user_profile(user)
    return profile.role == 'manager'


def _tasks_team_members(user):
    from django.contrib.auth.models import User

    profile = _tasks_user_profile(user)
    if profile.company:
        return User.objects.filter(
            is_active=True,
            userprofile__company=profile.company,
            userprofile__role='salesman',
        ).select_related('userprofile', 'userprofile__company').order_by('first_name', 'username')
    return User.objects.filter(
        is_active=True,
        userprofile__role='salesman',
    ).select_related('userprofile', 'userprofile__company').order_by('first_name', 'username')


def _tasks_assignee_options(user):
    return [
        _tasks_user_payload(member)
        for member in _tasks_team_members(user).exclude(pk=user.pk)
    ]


def _tasks_parse_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}'), None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}, '잘못된 요청 형식입니다.'
    return request.POST, None


def _tasks_payload_list(payload, key):
    if hasattr(payload, 'getlist'):
        return payload.getlist(key)
    value = payload.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _tasks_parse_date(value):
    import datetime

    value = str(value or '').strip()
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _tasks_parse_duration(value):
    value = str(value or '').strip()
    if not value:
        return None
    try:
        duration = int(value)
    except (TypeError, ValueError):
        return None
    valid = {choice[0] for choice in Todo.Duration.choices}
    return duration if duration in valid else None


def _tasks_customer_queryset(user):
    from reporting.models import FollowUp

    profile = _tasks_user_profile(user)
    queryset = FollowUp.objects.select_related('company', 'department', 'user', 'user__userprofile')
    if profile.role == 'manager' and profile.company:
        return queryset.filter(user__userprofile__company=profile.company)
    return queryset.filter(user=user)


def _tasks_customer_payload(customer):
    if not customer:
        return None
    return {
        'id': customer.id,
        'customer': customer.customer_name or '',
        'company': customer.company.name if customer.company else '',
        'department': customer.department.name if customer.department else '',
        'owner': _tasks_user_name(customer.user),
        'href': f'/customers/{customer.id}/',
        'djangoHref': reverse('reporting:followup_detail', args=[customer.id]),
    }


def _tasks_customer_for_user(user, customer_id):
    if not customer_id:
        return None
    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        return None
    return _tasks_customer_queryset(user).filter(id=customer_id).first()


def _tasks_apply_status_filter(queryset, status_filter):
    status_filter = str(status_filter or 'active').strip()
    today = timezone.localdate()
    if status_filter == 'active':
        return queryset.filter(status__in=TASK_ACTIVE_STATUSES)
    if status_filter == 'overdue':
        return queryset.filter(due_date__lt=today).exclude(status__in=[Todo.Status.DONE, Todo.Status.REJECTED])
    if status_filter == 'all':
        return queryset
    if status_filter in dict(Todo.Status.choices):
        return queryset.filter(status=status_filter)
    return queryset.filter(status__in=TASK_ACTIVE_STATUSES)


def _tasks_relation_querysets(user):
    base = Todo.objects.select_related(
        'created_by', 'created_by__userprofile', 'assigned_to', 'assigned_to__userprofile',
        'requested_by', 'requested_by__userprofile', 'related_client', 'related_client__company',
        'related_client__department', 'category',
    )
    my_tasks = base.filter(created_by=user, assigned_to__isnull=True)
    received_tasks = base.filter(assigned_to=user).exclude(created_by=user, requested_by__isnull=True)
    requested_tasks = base.filter(requested_by=user).exclude(assigned_to=user)
    return my_tasks, received_tasks, requested_tasks


def _tasks_metric_count(queryset, status_filter='active'):
    return _tasks_apply_status_filter(queryset, status_filter).count()


def _tasks_can_set_status(todo, user):
    if todo.status in [Todo.Status.PENDING, Todo.Status.REJECTED]:
        return False
    if todo.assigned_to_id:
        return todo.assigned_to_id == user.id
    return todo.created_by_id == user.id


def _tasks_can_manager_set_status(todo, user):
    return bool(
        _tasks_is_manager(user)
        and todo.requested_by_id == user.id
        and todo.source_type == Todo.SourceType.MANAGER_ASSIGN
    )


def _tasks_can_view(todo, user):
    if todo.created_by_id == user.id or todo.assigned_to_id == user.id or todo.requested_by_id == user.id:
        return True
    profile = _tasks_user_profile(user)
    if profile.role != 'manager' or not profile.company:
        return False
    participant_ids = [todo.created_by_id, todo.assigned_to_id, todo.requested_by_id]
    return User.objects.filter(
        id__in=[value for value in participant_ids if value],
        userprofile__company=profile.company,
    ).exists()


def _tasks_can_update(todo, user):
    if todo.source_type == Todo.SourceType.MANAGER_ASSIGN:
        return todo.requested_by_id == user.id
    return todo.created_by_id == user.id and todo.assigned_to_id is None


def _tasks_can_delete(todo, user):
    if todo.source_type == Todo.SourceType.MANAGER_ASSIGN:
        return todo.requested_by_id == user.id
    if todo.assigned_to_id == user.id and todo.requested_by_id and todo.requested_by_id != user.id:
        return True
    if todo.requested_by_id == user.id and todo.assigned_to_id and todo.assigned_to_id != user.id:
        return True
    return todo.created_by_id == user.id


def _tasks_can_upload_attachment(todo, user):
    return _tasks_can_update(todo, user) or (
        todo.source_type == Todo.SourceType.MANAGER_ASSIGN
        and todo.assigned_to_id == user.id
    )


def _tasks_attachment_payload(attachment):
    return {
        'id': attachment.id,
        'filename': attachment.filename,
        'fileSize': attachment.file_size,
        'uploadedAt': attachment.uploaded_at.isoformat() if attachment.uploaded_at else None,
        'uploadedBy': _tasks_user_payload(attachment.uploaded_by),
        'downloadHref': attachment.file.url if attachment.file else '',
    }


def _tasks_log_payload(log):
    action_labels = dict(TodoLog.ActionType.choices)
    return {
        'id': log.id,
        'actionType': log.action_type,
        'actionLabel': action_labels.get(log.action_type, log.action_type),
        'actor': _tasks_user_payload(log.actor),
        'message': log.message or '',
        'prevStatus': log.prev_status or '',
        'newStatus': log.new_status or '',
        'createdAt': log.created_at.isoformat() if log.created_at else None,
    }


def _tasks_payload(todo, user):
    status_labels = dict(Todo.Status.choices)
    source_labels = dict(Todo.SourceType.choices)
    duration_labels = dict(Todo.Duration.choices)
    can_status = _tasks_can_set_status(todo, user) or _tasks_can_manager_set_status(todo, user)
    can_complete = can_status and todo.status not in [Todo.Status.DONE, Todo.Status.PENDING, Todo.Status.REJECTED]
    can_update = _tasks_can_update(todo, user)
    can_delete = _tasks_can_delete(todo, user)
    can_upload = _tasks_can_upload_attachment(todo, user)
    return {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description or '',
        'status': todo.status,
        'statusLabel': status_labels.get(todo.status, todo.status),
        'sourceType': todo.source_type,
        'sourceLabel': source_labels.get(todo.source_type, todo.source_type),
        'dueDate': todo.due_date.isoformat() if todo.due_date else None,
        'completedAt': todo.completed_at.isoformat() if todo.completed_at else None,
        'createdAt': todo.created_at.isoformat() if todo.created_at else None,
        'updatedAt': todo.updated_at.isoformat() if todo.updated_at else None,
        'isOverdue': todo.is_overdue,
        'expectedDuration': todo.expected_duration,
        'expectedDurationLabel': duration_labels.get(todo.expected_duration, '') if todo.expected_duration else '',
        'category': {
            'id': todo.category_id,
            'name': todo.category.name if todo.category else '',
            'color': todo.category.color if todo.category else '',
        } if todo.category_id else None,
        'createdBy': _tasks_user_payload(todo.created_by),
        'assignedTo': _tasks_user_payload(todo.assigned_to),
        'requestedBy': _tasks_user_payload(todo.requested_by),
        'relatedClient': _tasks_customer_payload(todo.related_client),
        'canApprove': todo.status == Todo.Status.PENDING and todo.assigned_to_id == user.id,
        'canReject': todo.status == Todo.Status.PENDING and todo.assigned_to_id == user.id,
        'canChangeStatus': can_status,
        'canComplete': can_complete,
        'canSetOngoing': can_status and todo.status != Todo.Status.ONGOING,
        'canSetOnHold': can_status and todo.status != Todo.Status.ON_HOLD,
        'canUpdate': can_update,
        'canDelete': can_delete,
        'canUploadAttachment': can_upload,
        'attachmentCount': getattr(todo, 'attachment_count', None) if hasattr(todo, 'attachment_count') else todo.attachments.count(),
        'logCount': getattr(todo, 'log_count', None) if hasattr(todo, 'log_count') else todo.logs.count(),
        'detailHref': f'/tasks/{todo.id}/',
        'statusHref': reverse('reporting:tasks_status_api', args=[todo.id]),
        'updateHref': reverse('reporting:tasks_update_api', args=[todo.id]),
        'deleteHref': reverse('reporting:tasks_delete_api', args=[todo.id]),
        'uploadHref': reverse('reporting:tasks_attachment_upload_api', args=[todo.id]),
        'djangoHref': reverse('todos:detail', args=[todo.id]),
    }


def _tasks_detail_payload(todo, user):
    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'task': _tasks_payload(todo, user),
        'attachments': [_tasks_attachment_payload(attachment) for attachment in todo.attachments.all()],
        'logs': [_tasks_log_payload(log) for log in todo.logs.all()[:30]],
        'options': _tasks_options_payload(user),
        'links': {
            'list': '/tasks/',
            'manager': '/tasks/manager/',
            'djangoDetail': reverse('todos:detail', args=[todo.id]),
        },
    }


def _tasks_options_payload(user):
    return {
        'statuses': [{'value': value, 'label': label} for value, label in Todo.Status.choices],
        'statusFilters': [
            {'value': 'active', 'label': '진행/대기'},
            {'value': 'overdue', 'label': '지연'},
            {'value': 'pending', 'label': '승인 대기'},
            {'value': 'ongoing', 'label': '진행중'},
            {'value': 'on_hold', 'label': '보류'},
            {'value': 'done', 'label': '완료'},
            {'value': 'rejected', 'label': '반려'},
            {'value': 'all', 'label': '전체'},
        ],
        'durations': [{'value': value, 'label': label} for value, label in Todo.Duration.choices],
        'assignees': _tasks_assignee_options(user),
    }


@require_http_methods(["GET"])
def tasks_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    status_filter = request.GET.get('status', 'active')
    my_tasks, received_tasks, requested_tasks = _tasks_relation_querysets(request.user)
    my_filtered = _tasks_apply_status_filter(my_tasks, status_filter).order_by('due_date', '-created_at')
    received_filtered = _tasks_apply_status_filter(received_tasks, status_filter).order_by('due_date', '-created_at')
    requested_filtered = _tasks_apply_status_filter(requested_tasks, status_filter).order_by('due_date', '-created_at')
    visible_ids = list(my_tasks.values_list('id', flat=True)) + list(received_tasks.values_list('id', flat=True)) + list(requested_tasks.values_list('id', flat=True))
    visible = Todo.objects.filter(id__in=set(visible_ids))
    overdue_count = visible.filter(due_date__lt=timezone.localdate()).exclude(status__in=[Todo.Status.DONE, Todo.Status.REJECTED]).count()
    profile = _tasks_user_profile(request.user)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'currentUser': _tasks_user_payload(request.user),
        'scope': {
            'label': _tasks_user_name(request.user),
            'canManage': profile.role == 'manager',
        },
        'filters': {
            'status': status_filter,
        },
        'metrics': {
            'myActive': _tasks_metric_count(my_tasks),
            'receivedActive': _tasks_metric_count(received_tasks),
            'requestedActive': _tasks_metric_count(requested_tasks),
            'overdue': overdue_count,
            'done': visible.filter(status=Todo.Status.DONE).count(),
        },
        'options': _tasks_options_payload(request.user),
        'links': {
            'createApi': reverse('reporting:tasks_create_api'),
            'requestApi': reverse('reporting:tasks_request_api'),
            'assigneesApi': reverse('reporting:tasks_assignees_api'),
            'customersApi': reverse('reporting:tasks_customers_api'),
            'managerApi': reverse('reporting:tasks_manager_api'),
            'djangoList': reverse('todos:list'),
            'djangoCreate': reverse('todos:create'),
        },
        'tasks': {
            'my': [_tasks_payload(todo, request.user) for todo in list(my_filtered[:80])],
            'received': [_tasks_payload(todo, request.user) for todo in list(received_filtered[:80])],
            'requested': [_tasks_payload(todo, request.user) for todo in list(requested_filtered[:80])],
        },
    })


@require_http_methods(["GET"])
def tasks_detail_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    todo = get_object_or_404(
        Todo.objects.select_related(
            'created_by', 'created_by__userprofile', 'assigned_to', 'assigned_to__userprofile',
            'requested_by', 'requested_by__userprofile', 'related_client', 'related_client__company',
            'related_client__department', 'category',
        ).prefetch_related('attachments__uploaded_by', 'attachments__uploaded_by__userprofile', 'logs__actor', 'logs__actor__userprofile'),
        pk=pk,
    )
    if not _tasks_can_view(todo, request.user):
        return JsonResponse({'success': False, 'error': '업무 조회 권한이 없습니다.'}, status=403)
    return JsonResponse(_tasks_detail_payload(todo, request.user))


@require_http_methods(["POST"])
def tasks_update_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    todo = get_object_or_404(
        Todo.objects.select_related('created_by', 'assigned_to', 'requested_by', 'related_client'),
        pk=pk,
    )
    if not _tasks_can_update(todo, request.user):
        return JsonResponse({'success': False, 'error': '업무 수정 권한이 없습니다.'}, status=403)

    title = str(payload.get('title') or '').strip()
    if not title:
        return JsonResponse({'success': False, 'error': '제목을 입력하세요.'}, status=400)

    old_title = todo.title
    todo.title = title[:200]
    todo.description = str(payload.get('description') or '').strip()
    todo.due_date = _tasks_parse_date(payload.get('dueDate') or payload.get('due_date'))
    todo.expected_duration = _tasks_parse_duration(payload.get('expectedDuration') or payload.get('expected_duration'))
    todo.related_client = _tasks_customer_for_user(request.user, payload.get('relatedClientId') or payload.get('related_client'))
    todo.save()

    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.UPDATED,
        message=f"React CRM에서 수정됨 (이전 제목: {old_title})" if old_title != todo.title else 'React CRM에서 내용 수정됨',
    )
    todo = Todo.objects.select_related(
        'created_by', 'created_by__userprofile', 'assigned_to', 'assigned_to__userprofile',
        'requested_by', 'requested_by__userprofile', 'related_client', 'related_client__company',
        'related_client__department', 'category',
    ).prefetch_related('attachments__uploaded_by', 'attachments__uploaded_by__userprofile', 'logs__actor', 'logs__actor__userprofile').get(pk=todo.pk)
    return JsonResponse({
        **_tasks_detail_payload(todo, request.user),
        'message': '업무를 수정했습니다.',
    })


@require_http_methods(["POST"])
def tasks_delete_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    todo = get_object_or_404(Todo.objects.select_related('created_by', 'assigned_to', 'requested_by'), pk=pk)
    if not _tasks_can_delete(todo, request.user):
        return JsonResponse({'success': False, 'error': '업무 삭제 권한이 없습니다.'}, status=403)

    if todo.source_type == Todo.SourceType.MANAGER_ASSIGN and todo.requested_by_id == request.user.id:
        todo.delete()
        return JsonResponse({'success': True, 'source': 'django', 'message': '업무를 취소했습니다.', 'href': '/tasks/manager/'})

    if todo.assigned_to_id == request.user.id and todo.requested_by_id and todo.requested_by_id != request.user.id:
        todo.assigned_to = None
        todo.requested_by = None
        todo.status = Todo.Status.ONGOING
        todo.save()
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.ASSIGNED,
            message=f'{_tasks_user_name(request.user)}님이 받은 일에서 삭제함',
        )
        return JsonResponse({'success': True, 'source': 'django', 'message': '받은 일에서 삭제했습니다.', 'href': '/tasks/'})

    todo.delete()
    return JsonResponse({'success': True, 'source': 'django', 'message': '업무를 삭제했습니다.', 'href': '/tasks/'})


@require_http_methods(["POST"])
def tasks_attachment_upload_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    todo = get_object_or_404(
        Todo.objects.select_related('created_by', 'assigned_to', 'requested_by'),
        pk=pk,
    )
    if not _tasks_can_upload_attachment(todo, request.user):
        return JsonResponse({'success': False, 'error': '첨부 업로드 권한이 없습니다.'}, status=403)

    files = request.FILES.getlist('files') or request.FILES.getlist('attachments')
    if not files:
        return JsonResponse({'success': False, 'error': '업로드할 파일을 선택하세요.'}, status=400)

    attachments = []
    for uploaded_file in files:
        attachments.append(TodoAttachment.objects.create(
            todo=todo,
            file=uploaded_file,
            filename=uploaded_file.name,
            uploaded_by=request.user,
        ))
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.COMMENTED,
        message=f'React CRM에서 첨부파일 {len(attachments)}개 업로드',
    )
    todo = Todo.objects.select_related(
        'created_by', 'created_by__userprofile', 'assigned_to', 'assigned_to__userprofile',
        'requested_by', 'requested_by__userprofile', 'related_client', 'related_client__company',
        'related_client__department', 'category',
    ).prefetch_related('attachments__uploaded_by', 'attachments__uploaded_by__userprofile', 'logs__actor', 'logs__actor__userprofile').get(pk=todo.pk)
    return JsonResponse({
        **_tasks_detail_payload(todo, request.user),
        'message': f'첨부파일 {len(attachments)}개를 업로드했습니다.',
    })


@require_http_methods(["POST"])
def tasks_create_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    title = str(payload.get('title') or '').strip()
    if not title:
        return JsonResponse({'success': False, 'error': '제목을 입력하세요.'}, status=400)

    todo = Todo.objects.create(
        title=title[:200],
        description=str(payload.get('description') or '').strip(),
        due_date=_tasks_parse_date(payload.get('dueDate') or payload.get('due_date')),
        expected_duration=_tasks_parse_duration(payload.get('expectedDuration') or payload.get('expected_duration')),
        related_client=_tasks_customer_for_user(request.user, payload.get('relatedClientId') or payload.get('related_client')),
        created_by=request.user,
        source_type=Todo.SourceType.SELF,
        status=Todo.Status.ONGOING,
    )
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.CREATED,
        message='React CRM에서 TODO 생성',
        new_status=Todo.Status.ONGOING,
    )
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '업무를 생성했습니다.',
        'task': _tasks_payload(todo, request.user),
    }, status=201)


@require_http_methods(["POST"])
def tasks_request_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    title = str(payload.get('title') or '').strip()
    try:
        assigned_to_id = int(payload.get('assignedToId') or payload.get('assigned_to') or 0)
    except (TypeError, ValueError):
        assigned_to_id = 0
    if not title or not assigned_to_id:
        return JsonResponse({'success': False, 'error': '제목과 담당자를 입력하세요.'}, status=400)
    assigned_to = _tasks_team_members(request.user).exclude(pk=request.user.pk).filter(pk=assigned_to_id).first()
    if not assigned_to:
        return JsonResponse({'success': False, 'error': '같은 회사 실무자만 담당자로 선택할 수 있습니다.'}, status=403)

    todo = Todo.objects.create(
        title=title[:200],
        description=str(payload.get('description') or '').strip(),
        due_date=_tasks_parse_date(payload.get('dueDate') or payload.get('due_date')),
        expected_duration=_tasks_parse_duration(payload.get('expectedDuration') or payload.get('expected_duration')),
        related_client=_tasks_customer_for_user(request.user, payload.get('relatedClientId') or payload.get('related_client')),
        created_by=request.user,
        assigned_to=assigned_to,
        requested_by=request.user,
        source_type=Todo.SourceType.PEER_REQUEST,
        status=Todo.Status.PENDING,
    )
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.DELEGATED,
        message=f'{_tasks_user_name(assigned_to)}에게 업무 요청',
        new_status=Todo.Status.PENDING,
    )
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '업무를 요청했습니다.',
        'task': _tasks_payload(todo, request.user),
    }, status=201)


def _tasks_reject(todo, user, reason=''):
    requester = todo.requested_by
    rejector_name = _tasks_user_name(user)
    if requester:
        new_todo = Todo.objects.create(
            title=todo.title,
            description=todo.description,
            created_by=requester,
            assigned_to=None,
            requested_by=None,
            status=Todo.Status.ONGOING,
            due_date=todo.due_date,
            expected_duration=todo.expected_duration,
            related_client=todo.related_client,
            source_type=todo.source_type,
        )
        TodoLog.objects.create(
            todo=new_todo,
            actor=user,
            action_type=TodoLog.ActionType.REJECTED,
            message=f'[반려로 인해 생성됨] {rejector_name}님이 반려' + (f'\n사유: {reason}' if reason else ''),
        )
    todo.status = Todo.Status.REJECTED
    todo.description = f"[반려됨] {rejector_name}님이 반려" + (f"\n사유: {reason}" if reason else "") + "\n\n" + (todo.description or '')
    todo.save()
    TodoLog.objects.create(
        todo=todo,
        actor=user,
        action_type=TodoLog.ActionType.REJECTED,
        message='React CRM에서 업무 요청 반려' + (f'\n반려 사유: {reason}' if reason else ''),
        prev_status=Todo.Status.PENDING,
        new_status=Todo.Status.REJECTED,
    )


@require_http_methods(["POST"])
def tasks_status_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response

    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    todo = get_object_or_404(Todo.objects.select_related('created_by', 'assigned_to', 'requested_by'), pk=pk)
    action = str(payload.get('action') or '').strip()
    new_status = str(payload.get('status') or '').strip()

    if action == 'approve':
        if todo.assigned_to_id != request.user.id or todo.status != Todo.Status.PENDING:
            return JsonResponse({'success': False, 'error': '승인 권한이 없습니다.'}, status=403)
        prev_status = todo.status
        todo.status = Todo.Status.ONGOING
        todo.save()
        TodoLog.objects.create(todo=todo, actor=request.user, action_type=TodoLog.ActionType.APPROVED, message='React CRM에서 승인', prev_status=prev_status, new_status=todo.status)
    elif action == 'reject':
        if todo.assigned_to_id != request.user.id or todo.status != Todo.Status.PENDING:
            return JsonResponse({'success': False, 'error': '반려 권한이 없습니다.'}, status=403)
        _tasks_reject(todo, request.user, str(payload.get('reason') or '').strip())
    else:
        if new_status not in [Todo.Status.ONGOING, Todo.Status.ON_HOLD, Todo.Status.DONE]:
            return JsonResponse({'success': False, 'error': '잘못된 상태입니다.'}, status=400)
        if not (_tasks_can_set_status(todo, request.user) or _tasks_can_manager_set_status(todo, request.user)):
            return JsonResponse({'success': False, 'error': '상태 변경 권한이 없습니다.'}, status=403)
        prev_status = todo.status
        todo.status = new_status
        todo.completed_at = timezone.now() if new_status == Todo.Status.DONE else None
        todo.save()
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.STATUS_CHANGED,
            message='React CRM에서 상태 변경',
            prev_status=prev_status,
            new_status=new_status,
        )

    todo.refresh_from_db()
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '업무 상태를 변경했습니다.',
        'task': _tasks_payload(todo, request.user),
    })


@require_http_methods(["GET"])
def tasks_assignees_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response
    return JsonResponse({
        'success': True,
        'source': 'django',
        'assignees': _tasks_assignee_options(request.user),
    })


@require_http_methods(["GET"])
def tasks_customers_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response
    query = str(request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'success': True, 'source': 'django', 'customers': []})
    search_filter = Q(customer_name__icontains=query) | Q(company__name__icontains=query) | Q(department__name__icontains=query)
    customers = _tasks_customer_queryset(request.user).filter(search_filter).order_by('customer_name')[:20]
    return JsonResponse({
        'success': True,
        'source': 'django',
        'customers': [_tasks_customer_payload(customer) for customer in customers],
    })


@require_http_methods(["GET"])
def tasks_manager_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response
    profile = _tasks_user_profile(request.user)
    if profile.role != 'manager':
        return JsonResponse({'success': False, 'error': '매니저 권한이 필요합니다.'}, status=403)

    status_filter = request.GET.get('status', 'active')
    assignee = str(request.GET.get('assignee') or '').strip()
    base = Todo.objects.filter(
        requested_by=request.user,
        source_type=Todo.SourceType.MANAGER_ASSIGN,
    ).select_related(
        'created_by', 'assigned_to', 'assigned_to__userprofile', 'requested_by', 'related_client',
        'related_client__company', 'related_client__department',
    )
    filtered = _tasks_apply_status_filter(base, status_filter)
    if assignee.isdigit():
        filtered = filtered.filter(assigned_to_id=int(assignee))

    team_members = list(_tasks_team_members(request.user))
    summaries = []
    for member in team_members:
        member_tasks = base.filter(assigned_to=member)
        total = member_tasks.count()
        summaries.append({
            'user': _tasks_user_payload(member),
            'total': total,
            'active': member_tasks.filter(status__in=TASK_ACTIVE_STATUSES).count(),
            'done': member_tasks.filter(status=Todo.Status.DONE).count(),
            'overdue': member_tasks.filter(due_date__lt=timezone.localdate()).exclude(status__in=[Todo.Status.DONE, Todo.Status.REJECTED]).count(),
        })

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': f'{profile.company.name} 팀' if profile.company else _tasks_user_name(request.user),
            'canManage': True,
        },
        'filters': {
            'status': status_filter,
            'assignee': assignee if assignee.isdigit() else '',
        },
        'metrics': {
            'total': base.count(),
            'active': base.filter(status__in=TASK_ACTIVE_STATUSES).count(),
            'done': base.filter(status=Todo.Status.DONE).count(),
            'overdue': base.filter(due_date__lt=timezone.localdate()).exclude(status__in=[Todo.Status.DONE, Todo.Status.REJECTED]).count(),
        },
        'options': {
            **_tasks_options_payload(request.user),
            'teamMembers': [_tasks_user_payload(member) for member in team_members],
        },
        'links': {
            'assignApi': reverse('reporting:tasks_manager_assign_api'),
            'customersApi': reverse('reporting:tasks_customers_api'),
            'djangoManager': reverse('todos:manager_dashboard'),
        },
        'teamSummary': summaries,
        'tasks': [_tasks_payload(todo, request.user) for todo in list(filtered.order_by('due_date', '-created_at')[:120])],
    })


@require_http_methods(["POST"])
def tasks_manager_assign_api(request):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response
    profile = _tasks_user_profile(request.user)
    if profile.role != 'manager':
        return JsonResponse({'success': False, 'error': '매니저 권한이 필요합니다.'}, status=403)
    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    title = str(payload.get('title') or '').strip()
    assignee_ids = []
    for value in _tasks_payload_list(payload, 'assignedToIds') or _tasks_payload_list(payload, 'assigned_to'):
        try:
            assignee_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    if not title or not assignee_ids:
        return JsonResponse({'success': False, 'error': '업무 내용과 담당자를 선택하세요.'}, status=400)
    assignees = list(_tasks_team_members(request.user).filter(id__in=set(assignee_ids)))
    if not assignees:
        return JsonResponse({'success': False, 'error': '같은 회사 실무자를 담당자로 선택하세요.'}, status=403)

    related_client = _tasks_customer_for_user(request.user, payload.get('relatedClientId') or payload.get('related_client'))
    created = []
    for assignee in assignees:
        todo = Todo.objects.create(
            title=title[:200],
            description=str(payload.get('description') or '').strip(),
            due_date=_tasks_parse_date(payload.get('dueDate') or payload.get('due_date')),
            expected_duration=_tasks_parse_duration(payload.get('expectedDuration') or payload.get('expected_duration')),
            related_client=related_client,
            created_by=request.user,
            assigned_to=assignee,
            requested_by=request.user,
            source_type=Todo.SourceType.MANAGER_ASSIGN,
            status=Todo.Status.ONGOING,
        )
        TodoLog.objects.create(
            todo=todo,
            actor=request.user,
            action_type=TodoLog.ActionType.ASSIGNED,
            message=f'React CRM에서 매니저 업무 하달: {_tasks_user_name(assignee)}',
            new_status=Todo.Status.ONGOING,
        )
        created.append(todo)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'{len(created)}명에게 업무를 하달했습니다.',
        'tasks': [_tasks_payload(todo, request.user) for todo in created],
    }, status=201)


@require_http_methods(["POST"])
def tasks_manager_status_api(request, pk):
    auth_response = _tasks_api_login_required_response(request)
    if auth_response:
        return auth_response
    if not _tasks_is_manager(request.user):
        return JsonResponse({'success': False, 'error': '매니저 권한이 필요합니다.'}, status=403)
    payload, error = _tasks_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    todo = get_object_or_404(Todo, pk=pk, requested_by=request.user, source_type=Todo.SourceType.MANAGER_ASSIGN)
    new_status = str(payload.get('status') or '').strip()
    if new_status not in [Todo.Status.ONGOING, Todo.Status.ON_HOLD, Todo.Status.DONE]:
        return JsonResponse({'success': False, 'error': '잘못된 상태입니다.'}, status=400)
    prev_status = todo.status
    todo.status = new_status
    todo.completed_at = timezone.now() if new_status == Todo.Status.DONE else None
    todo.save()
    TodoLog.objects.create(
        todo=todo,
        actor=request.user,
        action_type=TodoLog.ActionType.STATUS_CHANGED,
        message='React CRM 매니저 화면에서 상태 변경',
        prev_status=prev_status,
        new_status=new_status,
    )
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '업무 상태를 변경했습니다.',
        'task': _tasks_payload(todo, request.user),
    })
