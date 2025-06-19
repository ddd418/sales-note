from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 로그인 요구 데코레이터
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator  # 페이지네이션 추가
from .models import FollowUp, Schedule, History, UserProfile # UserProfile 모델 추가
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from functools import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.conf import settings

# 권한 체크 데코레이터
def role_required(allowed_roles):
    """특정 역할을 가진 사용자만 접근할 수 있도록 하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('reporting:login')
            
            try:
                user_profile = request.user.userprofile
                if user_profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, '이 페이지에 접근할 권한이 없습니다.')
                    return redirect('reporting:dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, '사용자 프로필이 설정되지 않았습니다. 관리자에게 문의하세요.')
                return redirect('reporting:dashboard')
        return wrapper
    return decorator

def get_user_profile(user):
    """사용자 프로필을 가져오는 헬퍼 함수"""
    try:
        return user.userprofile
    except UserProfile.DoesNotExist:
        # 프로필이 없는 경우 기본 salesman 권한으로 생성
        return UserProfile.objects.create(user=user, role='salesman')

def can_access_user_data(request_user, target_user):
    """현재 사용자가 대상 사용자의 데이터에 접근할 수 있는지 확인"""
    user_profile = get_user_profile(request_user)
    
    # Admin은 모든 데이터 접근 가능
    if user_profile.is_admin():
        return True
    
    # Manager는 Salesman 데이터만 접근 가능
    if user_profile.is_manager():
        target_profile = get_user_profile(target_user)
        return target_profile.is_salesman()
    
    # Salesman은 자신의 데이터만 접근 가능
    return request_user == target_user

def get_accessible_users(request_user):
    """현재 사용자가 접근할 수 있는 사용자 목록을 반환"""
    user_profile = get_user_profile(request_user)
    
    if user_profile.is_admin():
        # Admin은 모든 사용자에 접근 가능
        return User.objects.all()
    elif user_profile.is_manager():
        # Manager는 salesman들에만 접근 가능
        salesman_profiles = UserProfile.objects.filter(role='salesman')
        return User.objects.filter(userprofile__in=salesman_profiles)
    else:
        # Salesman은 자기 자신만 접근 가능
        return User.objects.filter(id=request_user.id)

# 팔로우업 폼 클래스
class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ['customer_name', 'company', 'department', 'manager', 'phone_number', 'email', 'address', 'notes', 'priority']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '고객명을 입력하세요 (선택사항)'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '업체/학교명을 입력하세요'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '부서/연구실명을 입력하세요 (선택사항)'}),
            'manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '책임자명을 입력하세요 (선택사항)'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '010-0000-0000 (선택사항)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@company.com (선택사항)'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '상세주소를 입력하세요 (선택사항)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '상세 내용을 입력하세요 (선택사항)'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'customer_name': '고객명',
            'company': '업체/학교명',
            'department': '부서/연구실명',
            'manager': '책임자',
            'phone_number': '핸드폰 번호',
            'email': '메일 주소',
            'address': '상세주소',
            'notes': '상세 내용',
            'priority': '우선순위',
        }

# 일정 폼 클래스
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['followup', 'visit_date', 'visit_time', 'location', 'status', 'notes']
        widgets = {
            'followup': forms.Select(attrs={'class': 'form-control'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'visit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '방문 장소를 입력하세요 (선택사항)'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '메모를 입력하세요 (선택사항)'}),
        }
        labels = {
            'followup': '관련 팔로우업',
            'visit_date': '방문 날짜',
            'visit_time': '방문 시간',
            'location': '장소',
            'status': '상태',
            'notes': '메모',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # 현재 사용자의 팔로우업만 선택할 수 있도록 필터링
            if user.is_staff or user.is_superuser:
                self.fields['followup'].queryset = FollowUp.objects.all()
            else:
                self.fields['followup'].queryset = FollowUp.objects.filter(user=user)

# 히스토리 폼 클래스
class HistoryForm(forms.ModelForm):
    class Meta:
        model = History
        fields = ['followup', 'schedule', 'action_type', 'content', 'delivery_amount', 'delivery_items', 'delivery_date', 'meeting_date']
        widgets = {
            'followup': forms.Select(attrs={'class': 'form-control'}),
            'schedule': forms.Select(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '활동 내용을 입력하세요'}),
            'delivery_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '납품 금액을 입력하세요 (원)', 'min': '0'}),
            'delivery_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '납품 품목을 입력하세요 (예: 제품A 10개, 제품B 5개)'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'meeting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        }
        labels = {
            'followup': '관련 고객 정보',
            'schedule': '관련 일정',
            'action_type': '활동 유형',
            'content': '활동 내용',
            'delivery_amount': '납품 금액 (원)',
            'delivery_items': '납품 품목',
            'delivery_date': '납품 날짜',
            'meeting_date': '미팅 날짜',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # 현재 사용자의 팔로우업만 선택할 수 있도록 필터링
            if user.is_staff or user.is_superuser:
                self.fields['followup'].queryset = FollowUp.objects.all()
            else:
                self.fields['followup'].queryset = FollowUp.objects.filter(user=user)
            
            # 일정 필드를 빈 상태로 초기화 (JavaScript에서 동적으로 로드)
            self.fields['schedule'].queryset = Schedule.objects.none()
            
            # 선택된 팔로우업이 있으면 해당 팔로우업의 일정만 표시
            if 'followup' in self.data:
                try:
                    followup_id = int(self.data.get('followup'))
                    self.fields['schedule'].queryset = Schedule.objects.filter(followup_id=followup_id, user=user)
                except (ValueError, TypeError):
                    pass  # 잘못된 입력인 경우 무시
            elif self.instance.pk:
                # 수정 시에는 해당 인스턴스의 팔로우업에 연결된 일정들을 표시
                self.fields['schedule'].queryset = self.instance.followup.schedules.all()
        
        # 일정은 선택사항으로 설정
        self.fields['schedule'].required = False
        self.fields['schedule'].empty_label = "관련 일정 없음"
        
        # 납품 금액은 선택사항으로 설정
        self.fields['delivery_amount'].required = False

@login_required # 이 뷰는 로그인이 필요함을 명시
def followup_list_view(request):
    """팔로우업 목록 보기 (권한 기반 필터링 적용)"""
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 모든 또는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related('user').prefetch_related('schedules', 'histories')
    else:
        # Salesman은 자신의 데이터만 조회
        followups = FollowUp.objects.filter(user=request.user).select_related('user').prefetch_related('schedules', 'histories')
    
    # 고객명/업체명 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 우선순위 필터링
    priority_filter = request.GET.get('priority')
    if priority_filter:
        followups = followups.filter(priority=priority_filter)
    
    # 담당자 필터링
    user_filter = request.GET.get('user')
    if user_filter:
        followups = followups.filter(user_id=user_filter)
      # 정렬 (최신순)
    followups = followups.order_by('-created_at')
    
    # 우선순위별 카운트 (효율적인 쿼리)
    from django.db.models import Count, Q as DbQ
    stats = followups.aggregate(
        total_count=Count('id'),
        high_priority_count=Count('id', filter=DbQ(priority='high')),
        medium_priority_count=Count('id', filter=DbQ(priority='medium')),
        low_priority_count=Count('id', filter=DbQ(priority='low'))
    )
      # 담당자 목록 (필터용)
    if request.user.is_staff or request.user.is_superuser:
        from django.contrib.auth.models import User
        users = User.objects.filter(followup__isnull=False).distinct()
    else:
        users = [request.user]
    
    # 선택된 사용자 정보
    selected_user = None
    if user_filter:
        try:
            from django.contrib.auth.models import User
            selected_user = User.objects.get(id=user_filter)
        except (User.DoesNotExist, ValueError):
            pass
    
    # 페이지네이션 처리
    paginator = Paginator(followups, 10) # 페이지당 10개 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'followups': page_obj,
        'page_title': '팔로우업 목록', # 템플릿에 전달할 페이지 제목
        'search_query': search_query,
        'priority_filter': priority_filter,
        'user_filter': user_filter,        'selected_user': selected_user,
        'total_count': stats['total_count'],
        'high_priority_count': stats['high_priority_count'],
        'medium_priority_count': stats['medium_priority_count'],
        'low_priority_count': stats['low_priority_count'],
        'users': users,
    }
    return render(request, 'reporting/followup_list.html', context)

# 여기에 앞으로 팔로우업 상세, 생성, 수정, 삭제 등의 뷰 함수를 추가할 예정입니다.

@login_required
def followup_detail_view(request, pk):
    """팔로우업 상세 보기 (Manager 권한 포함)"""
    followup = get_object_or_404(FollowUp, pk=pk)
    
    # 권한 체크 (Manager도 Salesman 데이터 접근 가능)
    if not can_access_user_data(request.user, followup.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:followup_list')
    
    # 관련 히스토리 조회 (최신순)
    related_histories = History.objects.filter(followup=followup).order_by('-created_at')[:10]
    
    context = {
        'followup': followup,
        'related_histories': related_histories,
        'page_title': f'팔로우업 상세 - {followup.customer_name}'
    }
    return render(request, 'reporting/followup_detail.html', context)

@login_required
def followup_create_view(request):
    """팔로우업 생성"""
    if request.method == 'POST':
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.user = request.user  # 현재 로그인한 사용자를 연결
            followup.save()
            
            messages.success(request, '고객 정보가 성공적으로 생성되었습니다.')
            return redirect('reporting:followup_detail', pk=followup.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = FollowUpForm()
    
    context = {
        'form': form,
        'page_title': '새 고객 정보 생성'
    }
    return render(request, 'reporting/followup_form.html', context)

@login_required
def followup_edit_view(request, pk):
    """팔로우업 수정"""
    followup = get_object_or_404(FollowUp, pk=pk)
    
    # 권한 체크: 자신의 팔로우업이거나 관리자인 경우만 수정 가능
    if not (request.user.is_staff or request.user.is_superuser or followup.user == request.user):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:followup_list')
    
    if request.method == 'POST':
        form = FollowUpForm(request.POST, instance=followup)
        if form.is_valid():
            updated_followup = form.save()
            
            messages.success(request, '고객 정보가 성공적으로 수정되었습니다.')
            return redirect('reporting:followup_detail', pk=followup.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = FollowUpForm(instance=followup)
    
    context = {
        'form': form,
        'followup': followup,
        'page_title': f'고객 정보 수정 - {followup.customer_name}'
    }
    return render(request, 'reporting/followup_form.html', context)

@login_required
def followup_delete_view(request, pk):
    """팔로우업 삭제"""
    followup = get_object_or_404(FollowUp, pk=pk)
    
    # 권한 체크: 자신의 팔로우업이거나 관리자인 경우만 삭제 가능
    if not (request.user.is_staff or request.user.is_superuser or followup.user == request.user):
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('reporting:followup_list')
    
    if request.method == 'POST':
        customer_name = followup.customer_name or "고객명 미정"
        company_name = followup.company or "업체명 미정"
        followup.delete()
        messages.success(request, f'{customer_name} ({company_name}) 팔로우업이 삭제되었습니다.')
        return redirect('reporting:followup_list')
    
    context = {
        'followup': followup,
        'page_title': f'팔로우업 삭제 - {followup.customer_name or "고객명 미정"}'
    }
    return render(request, 'reporting/followup_delete.html', context)

@login_required
@never_cache
def dashboard_view(request):
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import datetime, timedelta
    import calendar
    
    # 사용자 프로필 가져오기
    user_profile = get_user_profile(request.user)
    
    # URL 파라미터로 특정 사용자 필터링
    user_filter = request.GET.get('user')
    selected_user = None
    
    if user_filter and user_profile.can_view_all_users():
        try:
            from django.contrib.auth.models import User
            selected_user = User.objects.get(id=user_filter)
            target_user = selected_user
        except (User.DoesNotExist, ValueError):
            target_user = request.user
    else:
        target_user = request.user
    
    # Manager인 경우 특정 사용자가 지정되지 않았다면 Manager 대시보드로 리디렉션
    if user_profile.is_manager() and not selected_user:
        return redirect('reporting:manager_dashboard')
    
    # 현재 연도 가져오기
    current_year = timezone.now().year
    
    # 권한에 따른 데이터 필터링
    if user_profile.is_admin() and not selected_user:
        # Admin은 모든 데이터 접근 가능
        followup_count = FollowUp.objects.count()
        schedule_count = Schedule.objects.filter(status='scheduled').count()
        history_count = History.objects.filter(created_at__year=current_year).count()
        histories = History.objects.all()
        histories_current_year = History.objects.filter(created_at__year=current_year)
        schedules = Schedule.objects.all()
        followups = FollowUp.objects.all()
    else:
        # 특정 사용자 또는 본인의 데이터만 접근
        followup_count = FollowUp.objects.filter(user=target_user).count()
        schedule_count = Schedule.objects.filter(user=target_user, status='scheduled').count()
        history_count = History.objects.filter(user=target_user, created_at__year=current_year).count()
        histories = History.objects.filter(user=target_user)
        histories_current_year = History.objects.filter(user=target_user, created_at__year=current_year)
        schedules = Schedule.objects.filter(user=target_user)
        followups = FollowUp.objects.filter(user=target_user)

    # 납품 금액 통계 (현재 연도만)
    delivery_stats = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False
    ).aggregate(
        total_amount=Sum('delivery_amount'),
        delivery_count=Count('id')
    )
    
    total_delivery_amount = delivery_stats['total_amount'] or 0
    delivery_count = delivery_stats['delivery_count'] or 0
      # 활동 유형별 통계 (현재 연도만)
    activity_stats = histories_current_year.values('action_type').annotate(
        count=Count('id')
    ).order_by('action_type')
      # 최근 활동 (현재 연도, 최근 5개)
    recent_activities = histories_current_year.order_by('-created_at')[:5]
    
    # 월별 고객 추가 현황 (최근 6개월)
    now = timezone.now()
    monthly_customers = []
    for i in range(6):
        month_start = (now.replace(day=1) - timedelta(days=32*i)).replace(day=1)
        month_end = (month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1]))
        
        count = followups.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        monthly_customers.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': f"{month_start.year}년 {month_start.month}월",
            'count': count
        })
    
    monthly_customers.reverse()  # 시간순 정렬
    
    # 일정 완료율 통계
    schedule_stats = schedules.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        scheduled=Count('id', filter=Q(status='scheduled'))
    )
    
    completion_rate = 0
    if schedule_stats['total'] > 0:
        completion_rate = round((schedule_stats['completed'] / schedule_stats['total']) * 100, 1)
      # 활동 히스토리 추이 (최근 30일, 현재 연도만)
    thirty_days_ago = now - timedelta(days=30)
    daily_activities = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        activity_count = histories_current_year.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).count()
        
        daily_activities.append({
            'date': day.strftime('%m/%d'),
            'count': activity_count
        })
    
    # 오늘 일정
    today = now.date()
    today_schedules = schedules.filter(
        visit_date=today,
        status='scheduled'
    ).order_by('visit_time')[:5]
    
    # 최근 고객 (최근 7일)
    week_ago = now - timedelta(days=7)
    recent_customers = followups.filter(
        created_at__gte=week_ago
    ).order_by('-created_at')[:5]

    # 새로운 성과 지표 계산
    from django.db.models import Avg
    current_month = now.month
    current_year = now.year
    
    # 이번 달 납품액
    monthly_revenue = histories.filter(
        action_type='delivery_schedule',
        created_at__month=current_month,
        created_at__year=current_year,
        delivery_amount__isnull=False
    ).aggregate(total=Sum('delivery_amount'))['total'] or 0
    
    # 이번 달 미팅 수
    monthly_meetings = histories.filter(
        action_type='customer_meeting',
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
      # 납품 전환율 (현재 연도 기준 미팅 대비 납품 비율)
    total_meetings = histories_current_year.filter(action_type='customer_meeting').count()
    total_deliveries = histories_current_year.filter(action_type='delivery_schedule').count()
    conversion_rate = (total_deliveries / total_meetings * 100) if total_meetings > 0 else 0
    
    # 평균 거래 규모 (현재 연도 기준)
    avg_deal_size = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False
    ).aggregate(avg=Avg('delivery_amount'))['avg'] or 0
    
    # 월별 납품 금액 데이터 (최근 6개월)
    monthly_revenue_data = []
    monthly_revenue_labels = []
    
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=30*i)
        month_revenue = histories.filter(
            action_type='delivery_schedule',
            created_at__month=target_date.month,
            created_at__year=target_date.year,
            delivery_amount__isnull=False
        ).aggregate(total=Sum('delivery_amount'))['total'] or 0
        
        monthly_revenue_data.append(float(month_revenue))
        monthly_revenue_labels.append(f"{target_date.year}년 {target_date.month}월")
      # 고객별 납품 현황 (현재 연도 기준, 상위 5개)
    customer_revenue_data = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False,
        followup__isnull=False
    ).values('followup__customer_name', 'followup__company').annotate(
        total_revenue=Sum('delivery_amount')
    ).order_by('-total_revenue')[:5]
    
    customer_labels = [f"{item['followup__customer_name'] or '미정'} ({item['followup__company'] or '미정'})" for item in customer_revenue_data]
    customer_amounts = [float(item['total_revenue']) for item in customer_revenue_data]

    context = {        'page_title': '대시보드',
        'current_year': current_year,  # 현재 연도 정보 추가
        'selected_user': selected_user,  # 선택된 사용자 정보
        'target_user': target_user,  # 실제 대상 사용자
        'followup_count': followup_count,
        'schedule_count': schedule_count,
        'history_count': history_count,
        'total_delivery_amount': total_delivery_amount,
        'delivery_count': delivery_count,
        'activity_stats': activity_stats,
        'recent_activities': recent_activities,
        'monthly_customers': monthly_customers,
        'schedule_stats': schedule_stats,
        'completion_rate': completion_rate,
        'daily_activities': daily_activities,
        'today_schedules': today_schedules,        'recent_customers': recent_customers,
        'monthly_revenue': monthly_revenue,
        'monthly_meetings': monthly_meetings,
        'conversion_rate': conversion_rate,
        'avg_deal_size': avg_deal_size,
        'monthly_revenue_data': monthly_revenue_data,
        'monthly_revenue_labels': monthly_revenue_labels,        'customer_revenue_labels': customer_labels,
        'customer_revenue_data': customer_amounts,
    }
    return render(request, 'reporting/dashboard.html', context)

# ============ 일정(Schedule) 관련 뷰들 ============

@login_required
def schedule_list_view(request):
    """일정 목록 보기 (권한 기반 필터링 적용)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        schedules = Schedule.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        schedules = Schedule.objects.filter(user=request.user)
    
    # 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        schedules = schedules.filter(
            Q(followup__customer_name__icontains=search_query) |
            Q(followup__company__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 상태별 필터링
    status_filter = request.GET.get('status')
    if status_filter:
        schedules = schedules.filter(status=status_filter)
    
    # 담당자 필터링
    user_filter = request.GET.get('user')
    if user_filter:
        schedules = schedules.filter(user_id=user_filter)
    
    # 날짜 범위 필터링
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            schedules = schedules.filter(visit_date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            schedules = schedules.filter(visit_date__lte=to_date)
        except ValueError:
            pass
    
    # 정렬 (방문 날짜순)
    schedules = schedules.order_by('visit_date', 'visit_time')
    
    # 상태별 카운트
    base_queryset = schedules
    total_count = base_queryset.count()
    scheduled_count = base_queryset.filter(status='scheduled').count()
    completed_count = base_queryset.filter(status='completed').count()
    cancelled_count = base_queryset.filter(status='cancelled').count()    # 담당자 목록 (필터용)
    if request.user.is_staff or request.user.is_superuser:
        from django.contrib.auth.models import User
        users = User.objects.filter(schedule__isnull=False).distinct()
    else:
        users = [request.user]
    
    # 선택된 사용자 정보
    selected_user = None
    if user_filter:
        try:
            from django.contrib.auth.models import User
            selected_user = User.objects.get(id=user_filter)
        except (User.DoesNotExist, ValueError):
            pass
    
    # 페이지네이션 처리
    paginator = Paginator(schedules, 10) # 페이지당 10개 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'schedules': page_obj,
        'page_title': '일정 목록',
        'status_filter': status_filter,
        'total_count': total_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'search_query': search_query,
        'user_filter': user_filter,
        'selected_user': selected_user,
        'date_from': date_from,
        'date_to': date_to,
        'users': users,
    }
    return render(request, 'reporting/schedule_list.html', context)

@login_required
def schedule_detail_view(request, pk):
    """일정 상세 보기 (Manager 권한 포함)"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크 (Manager도 Salesman 데이터 접근 가능)
    if not can_access_user_data(request.user, schedule.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:schedule_list')
    
    # 관련 히스토리 조회 (최신순)
    related_histories = History.objects.filter(schedule=schedule).order_by('-created_at')[:10]
    
    context = {
        'schedule': schedule,
        'related_histories': related_histories,
        'page_title': f'일정 상세 - {schedule.followup.customer_name}'
    }
    return render(request, 'reporting/schedule_detail.html', context)

@login_required
def schedule_create_view(request):
    """일정 생성 (캘린더에서 선택된 날짜 지원)"""
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()
            
            messages.success(request, '일정이 성공적으로 생성되었습니다.')
            return redirect('reporting:schedule_detail', pk=schedule.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        # URL 파라미터에서 날짜 가져오기
        selected_date = request.GET.get('date')
        initial_data = {}
        
        if selected_date:
            try:
                # 날짜 형식 검증 (YYYY-MM-DD)
                from datetime import datetime
                parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                initial_data['visit_date'] = parsed_date
                messages.info(request, f'{parsed_date.strftime("%Y년 %m월 %d일")}에 일정을 생성합니다.')
            except ValueError:
                messages.warning(request, '잘못된 날짜 형식입니다.')
        
        form = ScheduleForm(user=request.user, initial=initial_data)
    
    context = {
        'form': form,
        'page_title': '새 일정 생성',
        'selected_date': request.GET.get('date')  # 템플릿에서 사용할 수 있도록
    }
    return render(request, 'reporting/schedule_form.html', context)

@login_required
def schedule_edit_view(request, pk):
    """일정 수정"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크
    if not (request.user.is_staff or request.user.is_superuser or schedule.user == request.user):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:schedule_list')
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            updated_schedule = form.save()
            
            messages.success(request, '일정이 성공적으로 수정되었습니다.')
            return redirect('reporting:schedule_detail', pk=schedule.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = ScheduleForm(instance=schedule, user=request.user)
    
    context = {
        'form': form,
        'schedule': schedule,
        'page_title': f'일정 수정 - {schedule.followup.customer_name}'
    }
    return render(request, 'reporting/schedule_form.html', context)

@login_required
def schedule_delete_view(request, pk):
    """일정 삭제"""
    import traceback
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"일정 삭제 요청 - 사용자: {request.user.username}, 일정 ID: {pk}")
        logger.info(f"요청 메서드: {request.method}")
        logger.info(f"AJAX 요청 여부: {request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'}")
        
        schedule = get_object_or_404(Schedule, pk=pk)
        logger.info(f"일정 정보 - 고객: {schedule.followup.customer_name}, 날짜: {schedule.visit_date}")
          # 권한 체크: 자신의 일정이거나 관리 권한이 있는 경우만 허용
        if not can_access_user_data(request.user, schedule.user):
            logger.warning(f"권한 없음 - 요청자: {request.user.username}, 일정 소유자: {schedule.user.username}")
            # AJAX 요청 감지 - X-Requested-With 헤더 확인
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다.'}, status=403)
            messages.error(request, '삭제 권한이 없습니다.')
            return redirect('reporting:schedule_list')
        
        if request.method == 'POST':
            customer_name = schedule.followup.customer_name or "고객명 미정"
            schedule_date = schedule.visit_date.strftime("%Y년 %m월 %d일")
            
            # 관련 히스토리 확인
            related_histories = schedule.histories.all()
            history_count = related_histories.count()
            
            logger.info(f"일정 삭제 실행 - {customer_name} ({schedule_date})")
            logger.info(f"연결된 히스토리 개수: {history_count}")
            
            # 관련 히스토리들의 정보를 로깅
            for history in related_histories:
                logger.info(f"삭제될 히스토리: {history.get_action_type_display()} - {history.created_at}")
            
            # 일정과 관련 히스토리 삭제
            if history_count > 0:
                related_histories.delete()
                logger.info(f"관련 히스토리 {history_count}개 삭제 완료")
            
            schedule.delete()
            logger.info(f"일정 삭제 완료 - ID: {pk}")
            
            # AJAX 요청 감지 - X-Requested-With 헤더 확인
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax:
                logger.info("AJAX 응답 반환")
                success_message = f'{customer_name} ({schedule_date}) 일정이 삭제되었습니다.'
                if history_count > 0:
                    success_message += f' (관련 활동 기록 {history_count}개도 함께 삭제되었습니다.)'
                
                return JsonResponse({
                    'success': True, 
                    'message': success_message
                })
            
            # 일반 폼 요청인 경우 리다이렉트
            success_message = f'{customer_name} ({schedule_date}) 일정이 삭제되었습니다.'
            if history_count > 0:
                success_message += f' (관련 활동 기록 {history_count}개도 함께 삭제되었습니다.)'
            
            messages.success(request, success_message)
            return redirect('reporting:schedule_list')
        
        # GET 요청인 경우
        context = {
            'schedule': schedule,
            'page_title': f'일정 삭제 - {schedule.followup.customer_name or "고객명 미정"}'
        }
        return render(request, 'reporting/schedule_delete.html', context)
        
    except Exception as e:
        # 예외 발생 시 상세 로깅
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        logger.error(f"일정 삭제 중 예외 발생:")
        logger.error(f"오류 메시지: {error_msg}")
        logger.error(f"스택 트레이스:\n{error_traceback}")
        
        # AJAX 요청인 경우 JSON 에러 응답
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': f'일정 삭제 중 오류가 발생했습니다: {error_msg}',
                'detail': error_traceback if settings.DEBUG else None  # DEBUG 모드에서만 상세 정보 포함
            }, status=500)
        
        # 일반 요청인 경우 에러 메시지와 함께 리다이렉트
        messages.error(request, f'일정 삭제 중 오류가 발생했습니다: {error_msg}')
        return redirect('reporting:schedule_list')

@login_required
def schedule_calendar_view(request):
    """일정 캘린더 뷰 (권한 기반 필터링 적용)"""
    user_profile = get_user_profile(request.user)
    
    # URL 파라미터로 특정 사용자 필터링
    user_filter = request.GET.get('user')
    selected_user = None
    
    if user_filter and user_profile.can_view_all_users():
        try:
            from django.contrib.auth.models import User
            selected_user = User.objects.get(id=user_filter)
        except (User.DoesNotExist, ValueError):
            pass
    
    context = {
        'page_title': '일정 캘린더',
        'selected_user': selected_user,
        'user_filter': user_filter,
    }
    return render(request, 'reporting/schedule_calendar.html', context)

@login_required
def schedule_api_view(request):
    """일정 데이터 API (JSON 응답) - 권한 기반 필터링 적용"""
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        schedules = Schedule.objects.filter(user__in=accessible_users)
        
        # URL 파라미터로 특정 사용자 필터링
        user_filter = request.GET.get('user')
        if user_filter:
            try:
                user_filter_int = int(user_filter)
                schedules = schedules.filter(user_id=user_filter_int)
            except (ValueError, TypeError):
                pass
    else:
        # Salesman은 자신의 데이터만 조회
        schedules = Schedule.objects.filter(user=request.user)
    
    schedule_data = []
    for schedule in schedules:
        schedule_data.append({
            'id': schedule.id,
            'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
            'time': schedule.visit_time.strftime('%H:%M'),
            'customer': schedule.followup.customer_name or '고객명 미정',
            'company': schedule.followup.company or '업체명 미정',
            'location': schedule.location or '',
            'status': schedule.status,
            'status_display': schedule.get_status_display(),
            'notes': schedule.notes or '',
            'user_name': schedule.user.username,
        })
    
    return JsonResponse(schedule_data, safe=False)

# ============ 히스토리(History) 관련 뷰들 ============

@login_required
def history_list_view(request):
    """히스토리 목록 보기 (권한 기반 필터링 적용)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        histories = History.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        histories = History.objects.filter(user=request.user)
    
    # 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        histories = histories.filter(
            Q(content__icontains=search_query) |
            Q(followup__customer_name__icontains=search_query) |
            Q(followup__company__icontains=search_query)
        )
    
    # 활동 유형 필터링
    action_type_filter = request.GET.get('action_type')
    if action_type_filter:
        histories = histories.filter(action_type=action_type_filter)
    
    # 담당자 필터링
    user_filter = request.GET.get('user')
    if user_filter:
        histories = histories.filter(user_id=user_filter)
    
    # 날짜 범위 필터링
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            histories = histories.filter(created_at__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            histories = histories.filter(created_at__date__lte=to_date)
        except ValueError:
            pass
    
    # 정렬 (최신순)
    histories = histories.order_by('-created_at')
    
    # 활동 유형별 카운트
    base_queryset = histories
    total_count = base_queryset.count()
    meeting_count = base_queryset.filter(action_type='customer_meeting').count()
    delivery_count = base_queryset.filter(action_type='delivery_schedule').count()
      # 담당자 목록 (필터용)
    if request.user.is_staff or request.user.is_superuser:
        from django.contrib.auth.models import User
        users = User.objects.filter(history__isnull=False).distinct()
    else:
        users = [request.user]
    
    # 선택된 사용자 정보
    selected_user = None
    if user_filter:
        try:
            from django.contrib.auth.models import User
            selected_user = User.objects.get(id=user_filter)
        except (User.DoesNotExist, ValueError):
            pass
    
    # 페이지네이션 처리
    paginator = Paginator(histories, 10) # 페이지당 10개 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'histories': page_obj,
        'page_title': '활동 히스토리',
        'action_type_filter': action_type_filter,
        'total_count': total_count,
        'meeting_count': meeting_count,
        'delivery_count': delivery_count,
        'search_query': search_query,
        'user_filter': user_filter,
        'selected_user': selected_user,
        'date_from': date_from,
        'date_to': date_to,
        'users': users,
    }
    return render(request, 'reporting/history_list.html', context)

@login_required
def history_detail_view(request, pk):
    """히스토리 상세 보기 (Manager 권한 포함)"""
    history = get_object_or_404(History, pk=pk)
    
    # 권한 체크 (Manager도 Salesman 데이터 접근 가능)
    if not can_access_user_data(request.user, history.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:history_list')
    
    context = {
        'history': history,
        'page_title': f'활동 상세 - {history.followup.customer_name}'
    }
    return render(request, 'reporting/history_detail.html', context)

@login_required
def history_create_view(request):
    """히스토리 생성"""
    if request.method == 'POST':
        form = HistoryForm(request.POST, user=request.user)
        if form.is_valid():
            history = form.save(commit=False)
            history.user = request.user
            history.save()
            messages.success(request, '활동 히스토리가 성공적으로 기록되었습니다.')
            return redirect('reporting:history_detail', pk=history.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = HistoryForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': '새 활동 기록'
    }
    return render(request, 'reporting/history_form.html', context)

@login_required
def history_edit_view(request, pk):
    """히스토리 수정"""
    history = get_object_or_404(History, pk=pk)
    
    # 권한 체크
    if not (request.user.is_staff or request.user.is_superuser or history.user == request.user):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:history_list')
    
    if request.method == 'POST':
        form = HistoryForm(request.POST, instance=history, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '활동 히스토리가 성공적으로 수정되었습니다.')
            return redirect('reporting:history_detail', pk=history.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = HistoryForm(instance=history, user=request.user)
    
    context = {
        'form': form,
        'history': history,
        'page_title': f'활동 수정 - {history.followup.customer_name}'
    }
    return render(request, 'reporting/history_form.html', context)

@login_required
def history_delete_view(request, pk):
    """히스토리 삭제"""
    history = get_object_or_404(History, pk=pk)
    
    # 권한 체크
    if not (request.user.is_staff or request.user.is_superuser or history.user == request.user):
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('reporting:history_list')
    
    if request.method == 'POST':
        customer_name = history.followup.customer_name or "고객명 미정"
        action_display = history.get_action_type_display()
        history.delete()
        messages.success(request, f'{customer_name} ({action_display}) 활동 기록이 삭제되었습니다.')
        return redirect('reporting:history_list')
    
    context = {
        'history': history,
        'page_title': f'활동 삭제 - {history.followup.customer_name or "고객명 미정"}'
    }
    return render(request, 'reporting/history_delete.html', context)

@login_required
def history_by_followup_view(request, followup_pk):
    """특정 팔로우업의 히스토리 목록"""
    followup = get_object_or_404(FollowUp, pk=followup_pk)
    
    # 권한 체크
    if not (request.user.is_staff or request.user.is_superuser or followup.user == request.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:followup_list')
    
    histories = History.objects.filter(followup=followup)
    
    context = {
        'histories': histories,
        'followup': followup,
        'page_title': f'{followup.customer_name} 활동 히스토리'
    }
    return render(request, 'reporting/history_list.html', context)

# ============ API 엔드포인트들 ============

@login_required
def api_followup_schedules(request, followup_pk):
    """특정 팔로우업의 일정 목록을 JSON으로 반환 (AJAX용)"""
    try:
        followup = get_object_or_404(FollowUp, pk=followup_pk)
          # 권한 체크
        if not (request.user.is_staff or request.user.is_superuser or followup.user == request.user):
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        schedules = Schedule.objects.filter(followup=followup, user=request.user)
        schedule_list = []
        
        for schedule in schedules:
            schedule_list.append({
                'id': schedule.id,
                'text': f"{schedule.visit_date} {schedule.visit_time} - {schedule.location or '장소 미정'}",
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d')  # 납품 날짜 자동 설정용
            })
        
        return JsonResponse({'schedules': schedule_list})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============ 인증 관련 뷰들 ============

class CustomLoginView(LoginView):
    """커스텀 로그인 뷰 (성공 메시지 추가)"""
    template_name = 'reporting/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        messages.success(self.request, f'안녕하세요, {form.get_user().username}님! 성공적으로 로그인되었습니다.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """커스텀 로그아웃 뷰 (성공 메시지 추가)"""
    next_page = reverse_lazy('reporting:login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            username = request.user.username
            response = super().dispatch(request, *args, **kwargs)
            messages.info(request, f'{username}님, 성공적으로 로그아웃되었습니다.')
            return response
        return super().dispatch(request, *args, **kwargs)

# ============ 사용자 관리 뷰들 ============

# 사용자 생성 폼
class UserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '한글 이름 (예: 홍길동)'}),
        label='사용자 이름'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='비밀번호'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='비밀번호 확인'
    )
    role = forms.ChoiceField(
        choices=[('manager', 'Manager (뷰어)'), ('salesman', 'SalesMan (실무자)')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='권한'
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '성 (선택사항)'}),
        label='성'
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름 (선택사항)'}),
        label='이름'
    )
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return password2

# 사용자 편집 폼 클래스
class UserEditForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '한글 이름 (예: 홍길동)'}),
        label='사용자 이름'
    )
    role = forms.ChoiceField(
        choices=[('admin', 'Admin (최고권한자)'), ('manager', 'Manager (뷰어)'), ('salesman', 'SalesMan (실무자)')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='권한'
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '성 (선택사항)'}),
        label='성'
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름 (선택사항)'}),
        label='이름'
    )
    change_password = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='비밀번호 변경'
    )
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='새 비밀번호'
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='새 비밀번호 확인'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        change_password = cleaned_data.get('change_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if change_password:
            if not password1:
                raise forms.ValidationError("비밀번호 변경을 선택했으면 새 비밀번호를 입력해야 합니다.")
            if password1 != password2:
                raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        
        return cleaned_data

@role_required(['admin'])
def user_list(request):
    """사용자 목록 (Admin 전용)"""
    users = User.objects.select_related('userprofile').all()
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # 역할별 필터
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(userprofile__role=role_filter)
    
    # 페이지네이션
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': UserProfile.ROLE_CHOICES,
        'page_title': '사용자 관리'
    }
    return render(request, 'reporting/user_list.html', context)

@role_required(['admin'])
def user_create(request):
    """사용자 생성 (Admin 전용)"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # 사용자 생성
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            # 사용자 프로필 생성
            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                created_by=request.user
            )
            
            messages.success(request, f'사용자 "{user.username}"이(가) 성공적으로 생성되었습니다.')
            return redirect('reporting:user_list')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'page_title': '사용자 생성'
    }
    return render(request, 'reporting/user_create.html', context)

@role_required(['admin'])
def user_edit(request, user_id):
    """사용자 편집 (Admin 전용)"""
    user = get_object_or_404(User, id=user_id)
    user_profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            # 사용자 정보 수정
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            
            # 비밀번호 변경
            if form.cleaned_data['change_password'] and form.cleaned_data['password1']:
                user.set_password(form.cleaned_data['password1'])
            
            user.save()
            
            # 권한 수정
            user_profile.role = form.cleaned_data['role']
            user_profile.save()
            
            messages.success(request, f'사용자 "{user.username}"의 정보가 성공적으로 수정되었습니다.')
            return redirect('reporting:user_list')
    else:
        # 기존 데이터로 폼 초기화
        form = UserEditForm(initial={
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user_profile.role,
        })
    
    context = {
        'form': form,
        'edit_user': user,
        'user_profile': user_profile,
        'page_title': f'사용자 편집 - {user.username}'
    }
    return render(request, 'reporting/user_edit.html', context)

@role_required(['admin'])
def user_delete(request, user_id):
    """사용자 삭제 (Admin 전용)"""
    import traceback
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"사용자 삭제 요청 - 요청자: {request.user.username}, 대상 사용자 ID: {user_id}")
        
        # 삭제할 사용자 가져오기
        user_to_delete = get_object_or_404(User, id=user_id)
        
        # 자기 자신은 삭제할 수 없음
        if user_to_delete.id == request.user.id:
            logger.warning(f"자신의 계정 삭제 시도 - {request.user.username}")
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'error': '자신의 계정은 삭제할 수 없습니다.'
                }, status=400)
            messages.error(request, '자신의 계정은 삭제할 수 없습니다.')
            return redirect('reporting:user_list')
        
        if request.method == 'POST':
            username = user_to_delete.username
            user_profile = getattr(user_to_delete, 'userprofile', None)
            role_display = user_profile.get_role_display() if user_profile else '알 수 없음'
            
            logger.info(f"사용자 삭제 실행 - {username} ({role_display})")
            
            # 관련 데이터 개수 확인
            followups_count = FollowUp.objects.filter(user=user_to_delete).count()
            schedules_count = Schedule.objects.filter(user=user_to_delete).count()
            histories_count = History.objects.filter(user=user_to_delete).count()
            
            logger.info(f"삭제될 데이터 - 고객정보: {followups_count}개, 일정: {schedules_count}개, 히스토리: {histories_count}개")
            
            # 사용자와 관련된 모든 데이터가 CASCADE로 삭제됨
            # (models.py에서 ForeignKey의 on_delete=models.CASCADE 설정에 의해)
            user_to_delete.delete()
            
            logger.info(f"사용자 삭제 완료 - {username}")
            
            # AJAX 요청인 경우 JSON 응답
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                success_message = f'사용자 "{username}"이(가) 성공적으로 삭제되었습니다.'
                if followups_count > 0 or schedules_count > 0 or histories_count > 0:
                    success_message += f' (관련 데이터 {followups_count + schedules_count + histories_count}개도 함께 삭제되었습니다.)'
                
                return JsonResponse({
                    'success': True,
                    'message': success_message
                })
            
            # 일반 요청인 경우 리다이렉트
            success_message = f'사용자 "{username}"이(가) 성공적으로 삭제되었습니다.'
            if followups_count > 0 or schedules_count > 0 or histories_count > 0:
                success_message += f' (관련 데이터 {followups_count + schedules_count + histories_count}개도 함께 삭제되었습니다.)'
            
            messages.success(request, success_message)
            return redirect('reporting:user_list')
        
        # GET 요청인 경우 (확인 페이지)
        context = {
            'user_to_delete': user_to_delete,
            'page_title': f'사용자 삭제 - {user_to_delete.username}'
        }
        return render(request, 'reporting/user_delete.html', context)
        
    except Exception as e:
        # 예외 발생 시 상세 로깅
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        logger.error(f"사용자 삭제 중 예외 발생:")
        logger.error(f"오류 메시지: {error_msg}")
        logger.error(f"스택 트레이스:\n{error_traceback}")
        
        # AJAX 요청인 경우 JSON 에러 응답
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': f'사용자 삭제 중 오류가 발생했습니다: {error_msg}',
                'detail': error_traceback if settings.DEBUG else None
            }, status=500)
        
        # 일반 요청인 경우 에러 메시지와 함께 리다이렉트
        messages.error(request, f'사용자 삭제 중 오류가 발생했습니다: {error_msg}')
        return redirect('reporting:user_list')

@role_required(['manager'])
@never_cache
def manager_dashboard(request):
    """Manager 전용 대시보드 - 모든 Salesman의 현황을 볼 수 있음"""
    # 선택된 salesman (기본값: 첫 번째 salesman)
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 접근 가능한 Salesman 목록
    accessible_users = get_accessible_users(request.user)
    salesman_users = accessible_users.filter(userprofile__role='salesman')
    
    if not salesman_users.exists():
        context = {
            'no_salesmen': True,
            'page_title': 'Manager 대시보드'
        }
        return render(request, 'reporting/manager_dashboard.html', context)
      # 선택된 사용자 결정
    if view_all:
        selected_user = salesman_users.first()  # 전체보기인 경우에도 기본값 설정
    elif selected_user_id:
        try:
            selected_user = salesman_users.get(id=selected_user_id)
        except User.DoesNotExist:
            selected_user = salesman_users.first()
    else:
        selected_user = salesman_users.first()
      # 선택된 사용자의 데이터 가져오기 (dashboard 뷰와 동일한 로직)
    from datetime import datetime
    current_year = datetime.now().year
    
    # 기본 쿼리셋 (선택된 사용자로 필터링 또는 전체보기)
    if view_all:
        # 전체보기인 경우 모든 Salesman의 데이터
        followups = FollowUp.objects.filter(user__in=salesman_users)
        schedules = Schedule.objects.filter(user__in=salesman_users)
        histories = History.objects.filter(user__in=salesman_users, created_at__year=current_year)
    else:
        # 특정 사용자의 데이터
        followups = FollowUp.objects.filter(user=selected_user)
        schedules = Schedule.objects.filter(user=selected_user)
        histories = History.objects.filter(user=selected_user, created_at__year=current_year)
    
    # 통계 계산
    total_followups = followups.count()
    active_followups = followups.filter(status='active').count()
    
    # 일정 통계
    total_schedules = schedules.count()
    completed_schedules = schedules.filter(status='completed').count()
    pending_schedules = schedules.filter(status='scheduled').count()
    
    # 히스토리 통계 (현재 연도)
    total_histories = histories.count()
    delivery_histories = histories.filter(action_type='delivery_schedule')
    total_delivery_amount = delivery_histories.aggregate(
        total=Sum('delivery_amount')    )['total'] or 0
    
    # 월별 데이터 (납품 날짜 기준)
    monthly_data = []
    monthly_delivery = []
    for month in range(1, 13):
        # 고객 미팅은 meeting_date 기준으로 집계 (meeting_date가 없으면 created_at 기준)
        month_meetings = histories.filter(
            Q(meeting_date__month=month) | 
            (Q(meeting_date__isnull=True) & Q(created_at__month=month, action_type='customer_meeting'))
        ).filter(action_type='customer_meeting')
        
        # 납품 일정은 delivery_date 기준으로 집계 (delivery_date가 없으면 created_at 기준)
        month_deliveries = delivery_histories.filter(
            Q(delivery_date__month=month) | 
            (Q(delivery_date__isnull=True) & Q(created_at__month=month))
        )
        
        monthly_data.append({
            'month': f'{month}월',
            'meetings': month_meetings.count(),
            'deliveries': month_deliveries.count(),
            'amount': month_deliveries.aggregate(total=Sum('delivery_amount'))['total'] or 0
        })
        
        monthly_delivery.append(month_deliveries.aggregate(total=Sum('delivery_amount'))['total'] or 0)
    
    # 고객별 납품 현황 (현재 연도)
    customer_delivery = {}
    for history in delivery_histories:
        customer = history.followup.customer_name or history.followup.company or "고객명 미정"
        if customer in customer_delivery:
            customer_delivery[customer] += history.delivery_amount or 0
        else:
            customer_delivery[customer] = history.delivery_amount or 0
      # 상위 10개 고객
    top_customers = sorted(customer_delivery.items(), key=lambda x: x[1], reverse=True)[:10]
    
    context = {
        'selected_user': selected_user,
        'salesman_users': salesman_users,
        'view_all': view_all,
        'current_year': current_year,
        'total_followups': total_followups,
        'active_followups': active_followups,
        'total_schedules': total_schedules,
        'completed_schedules': completed_schedules,
        'pending_schedules': pending_schedules,
        'total_histories': total_histories,
        'total_delivery_amount': total_delivery_amount,
        'monthly_data': monthly_data,
        'monthly_delivery': monthly_delivery,
        'top_customers': top_customers,
        'page_title': f'Manager 대시보드 - {"전체보기" if view_all else selected_user.username}'
    }
    return render(request, 'reporting/manager_dashboard.html', context)

@role_required(['manager'])
def salesman_detail(request, user_id):
    """특정 Salesman의 상세 정보 조회 (Manager 전용)"""
    # 접근 권한 확인
    accessible_users = get_accessible_users(request.user)
    selected_user = get_object_or_404(accessible_users, id=user_id)
    
    # 해당 사용자의 데이터만 필터링
    followups = FollowUp.objects.filter(user=selected_user)
    schedules = Schedule.objects.filter(user=selected_user)
    histories = History.objects.filter(user=selected_user)
    
    # 검색 및 필터링
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    if status_filter:
        followups = followups.filter(status=status_filter)
    
    # 페이지네이션
    paginator = Paginator(followups, 10)
    page_number = request.GET.get('page')
    followups = paginator.get_page(page_number)
    
    context = {
        'selected_user': selected_user,
        'followups': followups,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_schedules': schedules.count(),
        'total_histories': histories.count(),
        'page_title': f'{selected_user.username} 상세 정보'
    }
    return render(request, 'reporting/salesman_detail.html', context)

@role_required(['admin'])
@require_POST
def user_toggle_active(request, user_id):
    """사용자 활성화/비활성화 토글 (Admin 전용)"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # 자기 자신은 비활성화할 수 없음
        if user == request.user:
            return JsonResponse({'error': '자기 자신의 계정은 비활성화할 수 없습니다.'}, status=400)
        
        # 상태 토글
        user.is_active = not user.is_active
        user.save()
        
        status_text = "활성화" if user.is_active else "비활성화"
        messages.success(request, f'사용자 "{user.username}"이(가) {status_text}되었습니다.')
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'사용자가 {status_text}되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
@never_cache
def toggle_tax_invoice(request, history_id):
    """세금계산서 발행 여부 토글 (AJAX)"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 권한 체크: 자신의 히스토리이거나 접근 권한이 있는 경우
        try:
            if not can_access_user_data(request.user, history.user):
                return JsonResponse({
                    'success': False, 
                    'error': '접근 권한이 없습니다.'
                }, status=403)
        except Exception as e:
            # 권한 체크 실패 시 자신의 히스토리인지만 확인
            if request.user != history.user:
                return JsonResponse({
                    'success': False, 
                    'error': '접근 권한이 없습니다.'
                }, status=403)
        
        # 납품 일정 히스토리인지 확인
        if history.action_type != 'delivery_schedule':
            return JsonResponse({
                'success': False,
                'error': '납품 일정 히스토리만 세금계산서 토글이 가능합니다.'
            }, status=400)
        
        # 토글 실행
        history.tax_invoice_issued = not history.tax_invoice_issued
        history.save()
        
        return JsonResponse({
            'success': True,
            'tax_invoice_issued': history.tax_invoice_issued,
            'message': f'세금계산서 발행 여부가 {"발행완료" if history.tax_invoice_issued else "미발행"}로 변경되었습니다.'
        })
        
    except Exception as e:
        import traceback
        print(f"Error in toggle_tax_invoice: {traceback.format_exc()}")  # 로깅용
        return JsonResponse({
            'success': False,
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)

@login_required
def history_create_from_schedule(request, schedule_id):
    """일정에서 히스토리 생성"""
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크: 자신의 일정이거나 관리 권한이 있는 경우만 허용
        try:
            if not can_access_user_data(request.user, schedule.user):
                messages.error(request, '이 일정에 대한 히스토리를 생성할 권한이 없습니다.')
                return redirect('reporting:schedule_list')
        except Exception as e:
            # 권한 체크 실패 시 자신의 일정인지만 확인
            if request.user != schedule.user:
                messages.error(request, '이 일정에 대한 히스토리를 생성할 권한이 없습니다.')
                return redirect('reporting:schedule_list')
        
        if request.method == 'POST':
            form = HistoryForm(request.POST, user=request.user)
            if form.is_valid():
                history = form.save(commit=False)
                history.user = request.user
                history.followup = schedule.followup  # 일정의 팔로우업으로 강제 설정
                history.schedule = schedule  # 일정 연결
                  # 납품 일정인 경우 delivery_date가 설정되지 않았다면 일정 날짜로 설정
                if history.action_type == 'delivery_schedule' and not history.delivery_date:
                    history.delivery_date = schedule.visit_date
                
                # 고객 미팅인 경우 meeting_date가 설정되지 않았다면 일정 날짜로 설정
                if history.action_type == 'customer_meeting' and not history.meeting_date:
                    history.meeting_date = schedule.visit_date
                    
                history.save()
                messages.success(request, f'"{schedule.followup.customer_name}" 일정에 대한 활동 히스토리가 성공적으로 기록되었습니다.')
                return redirect('reporting:history_detail', pk=history.pk)
            else:
                messages.error(request, '입력 정보를 확인해주세요.')
                # POST 실패 시에도 일정 정보를 유지하기 위해 폼 필드를 다시 설정
                form.fields['followup'].queryset = FollowUp.objects.filter(id=schedule.followup.id)
                form.fields['schedule'].queryset = Schedule.objects.filter(id=schedule.id)
                form.fields['followup'].initial = schedule.followup
                form.fields['schedule'].initial = schedule
                # 필드를 읽기 전용으로 설정
                form.fields['followup'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
                form.fields['schedule'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
        else:
            # GET 요청 시 폼 초기화
            initial_data = {
                'followup': schedule.followup.id,
                'schedule': schedule.id,
                'action_type': 'customer_meeting',  # 기본값으로 고객 미팅 설정 (올바른 값)
                'delivery_date': schedule.visit_date,  # 납품 날짜를 일정 날짜로 설정
                'meeting_date': schedule.visit_date,  # 미팅 날짜를 일정 날짜로 설정
            }
            form = HistoryForm(user=request.user, initial=initial_data)
            
            # 팔로우업과 일정 필드를 해당 일정으로 고정
            form.fields['followup'].queryset = FollowUp.objects.filter(id=schedule.followup.id)
            form.fields['schedule'].queryset = Schedule.objects.filter(id=schedule.id)
            
            # 필드를 읽기 전용으로 설정 (disabled 대신 시각적으로 비활성화)
            form.fields['followup'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            form.fields['schedule'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
        
        context = {
            'form': form,
            'schedule': schedule,
            'page_title': f'활동 기록 추가 - {schedule.followup.customer_name} (일정: {schedule.visit_date})'
        }
        return render(request, 'reporting/history_form.html', context)
        
    except Exception as e:
        # 전체적인 오류 처리
        import traceback
        error_msg = f"오류 발생: {str(e)}"
        print(f"Error in history_create_from_schedule: {traceback.format_exc()}")  # 로그용
        messages.error(request, error_msg)
        return redirect('reporting:schedule_list')
        initial_data = {
            'followup': schedule.followup.id,
            'schedule': schedule.id,
            'action_type': 'customer_meeting',  # 기본값으로 고객 미팅 설정 (올바른 값)
            'delivery_date': schedule.visit_date,  # 납품 날짜를 일정 날짜로 설정
            'meeting_date': schedule.visit_date,  # 미팅 날짜를 일정 날짜로 설정
        }
        form = HistoryForm(user=request.user, initial=initial_data)
        
        # 팔로우업과 일정 필드를 해당 일정으로 고정
        form.fields['followup'].queryset = FollowUp.objects.filter(id=schedule.followup.id)
        form.fields['schedule'].queryset = Schedule.objects.filter(id=schedule.id)
        
        # 필드를 읽기 전용으로 설정 (disabled 대신 시각적으로 비활성화)
        form.fields['followup'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
        form.fields['schedule'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
    
    context = {
        'form': form,
        'schedule': schedule,
        'page_title': f'활동 기록 추가 - {schedule.followup.customer_name} (일정: {schedule.visit_date})'
    }
    return render(request, 'reporting/history_form.html', context)

@login_required
@require_POST
def schedule_move_api(request, pk):
    """일정을 다른 날짜로 이동하는 API"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크: 자신의 일정이거나 관리 권한이 있는 경우만 허용
    if not can_access_user_data(request.user, schedule.user):
        return JsonResponse({'success': False, 'error': '이 일정을 이동할 권한이 없습니다.'}, status=403)
    
    try:
        # POST 데이터에서 새로운 날짜 정보 가져오기
        import json
        data = json.loads(request.body)
        new_date = data.get('new_date')  # 'YYYY-MM-DD' 형식
        
        if not new_date:
            return JsonResponse({'success': False, 'error': '새로운 날짜가 제공되지 않았습니다.'}, status=400)
        
        # 날짜 형식 검증 및 변환
        from datetime import datetime
        try:
            new_visit_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': '잘못된 날짜 형식입니다.'}, status=400)
        
        # 일정 날짜 업데이트
        old_date = schedule.visit_date
        schedule.visit_date = new_visit_date
        schedule.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'일정이 {old_date.strftime("%Y년 %m월 %d일")}에서 {new_visit_date.strftime("%Y년 %m월 %d일")}로 이동되었습니다.',
            'old_date': old_date.strftime('%Y-%m-%d'),
            'new_date': new_visit_date.strftime('%Y-%m-%d')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 데이터입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'일정 이동 중 오류가 발생했습니다: {str(e)}'}, status=500)
