"""
TODOLIST 뷰
- 실무자: 내 할 일, 받은 일, 맡긴 일
- 매니저: 업무 하달, 진행 현황, 워크로드
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_http_methods

from .models import Todo, TodoAttachment, TodoLog


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
        status__in=['ongoing', 'on_hold']
    ).count()
    
    received_count = Todo.objects.filter(
        assigned_to=user,
        status__in=['pending', 'ongoing', 'on_hold']
    ).count()
    
    requested_count = Todo.objects.filter(
        requested_by=user,
        status__in=['pending', 'ongoing', 'on_hold']
    ).exclude(assigned_to=user).count()
    
    context = {
        'my_count': my_count,
        'received_count': received_count,
        'requested_count': requested_count,
        'active_tab': request.GET.get('tab', 'my'),
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
        queryset = queryset.filter(status__in=['ongoing', 'on_hold'])
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
    
    queryset = Todo.objects.filter(
        assigned_to=user
    ).select_related('created_by', 'requested_by', 'related_client')
    
    if status_filter == 'active':
        queryset = queryset.filter(status__in=['pending', 'ongoing', 'on_hold'])
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    
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
        queryset = queryset.filter(status__in=['pending', 'ongoing', 'on_hold'])
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    
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
        
        if not title:
            messages.error(request, '제목을 입력해주세요.')
            return redirect('todos:create')
        
        todo = Todo.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            expected_duration=expected_duration,
            related_client_id=related_client_id,
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
    
    # 권한 체크
    if todo.created_by != request.user and todo.assigned_to != request.user:
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    if request.method == 'POST':
        old_title = todo.title
        
        todo.title = request.POST.get('title', '').strip() or todo.title
        todo.description = request.POST.get('description', '').strip()
        todo.due_date = request.POST.get('due_date') or None
        todo.expected_duration = request.POST.get('expected_duration') or None
        
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
        'edit_mode': True,
    }
    return render(request, 'todos/todo_form.html', context)


@login_required
@require_POST
def todo_delete(request, pk):
    """TODO 삭제"""
    todo = get_object_or_404(Todo, pk=pk)
    
    if todo.created_by != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('todos:detail', pk=pk)
    
    title = todo.title
    todo.delete()
    
    messages.success(request, f'"{title}" TODO가 삭제되었습니다.')
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204, headers={'HX-Trigger': 'todoDeleted'})
    
    return redirect('todos:list')


# ============================================
# 상태 변경
# ============================================

@login_required
@require_POST
def todo_complete(request, pk):
    """TODO 완료 처리"""
    todo = get_object_or_404(Todo, pk=pk)
    
    # 권한: 담당자 또는 생성자
    if todo.assigned_to:
        if todo.assigned_to != request.user:
            return JsonResponse({'error': '완료 처리 권한이 없습니다.'}, status=403)
    elif todo.created_by != request.user:
        return JsonResponse({'error': '완료 처리 권한이 없습니다.'}, status=403)
    
    todo.complete(request.user)
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204, headers={'HX-Trigger': 'todoUpdated'})
    
    return JsonResponse({'success': True, 'message': 'TODO가 완료되었습니다.'})


@login_required
@require_POST
def todo_change_status(request, pk):
    """TODO 상태 변경"""
    todo = get_object_or_404(Todo, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Todo.Status.choices):
        return JsonResponse({'error': '잘못된 상태입니다.'}, status=400)
    
    # 권한 체크
    user = request.user
    can_change = (
        todo.created_by == user or 
        todo.assigned_to == user or
        (hasattr(user, 'userprofile') and user.userprofile.role == 'manager')
    )
    
    if not can_change:
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
    
    return JsonResponse({'success': True})


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


# ============================================
# 매니저 기능
# ============================================

@login_required
def manager_dashboard(request):
    """매니저 대시보드 - 업무 하달 현황"""
    user = request.user
    
    # 매니저 권한 체크
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:list')
    
    # 내가 하달한 업무 현황
    assigned_todos = Todo.objects.filter(
        requested_by=user,
        source_type=Todo.SourceType.MANAGER_ASSIGN
    ).select_related('assigned_to', 'related_client')
    
    # 상태별 집계
    status_counts = assigned_todos.values('status').annotate(count=Count('id'))
    
    # 담당자별 집계
    assignee_counts = assigned_todos.filter(
        status__in=['pending', 'ongoing', 'on_hold']
    ).values('assigned_to__username', 'assigned_to__first_name').annotate(count=Count('id'))
    
    context = {
        'assigned_todos': assigned_todos.order_by('-created_at')[:50],
        'status_counts': {s['status']: s['count'] for s in status_counts},
        'assignee_counts': assignee_counts,
    }
    return render(request, 'todos/manager_dashboard.html', context)


@login_required
def manager_assign(request):
    """매니저 업무 하달"""
    from django.contrib.auth.models import User
    
    user = request.user
    
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'manager':
        messages.error(request, '매니저 권한이 필요합니다.')
        return redirect('todos:list')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date') or None
        
        if not title or not assigned_to_id:
            messages.error(request, '제목과 담당자를 입력해주세요.')
            return redirect('todos:manager_assign')
        
        assigned_to = get_object_or_404(User, pk=assigned_to_id)
        
        todo = Todo.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            created_by=user,
            assigned_to=assigned_to,
            requested_by=user,
            source_type=Todo.SourceType.MANAGER_ASSIGN,
            status=Todo.Status.ONGOING,  # 매니저 하달은 바로 진행중
        )
        
        TodoLog.objects.create(
            todo=todo,
            actor=user,
            action_type=TodoLog.ActionType.ASSIGNED,
            message=f"매니저 업무 하달: {assigned_to.get_full_name() or assigned_to.username}",
            new_status='ongoing'
        )
        
        messages.success(request, f'{assigned_to.get_full_name() or assigned_to.username}에게 업무를 하달했습니다.')
        return redirect('todos:manager_dashboard')
    
    # GET: 팀원 목록
    team_members = User.objects.filter(
        is_active=True
    ).exclude(pk=user.pk).order_by('first_name', 'username')
    
    context = {
        'team_members': team_members,
        'is_manager_assign': True,
    }
    return render(request, 'todos/todo_request_form.html', context)


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
    
    return render(request, 'todos/partials/todo_row.html', {'todo': todo})


@login_required
def api_search_clients(request):
    """고객 검색 API (모달용)"""
    from reporting.models import FollowUp
    
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # 고객명 또는 회사명으로 검색 (user가 담당자)
    clients = FollowUp.objects.filter(
        Q(customer_name__icontains=query) | Q(company__name__icontains=query),
        user=request.user
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
