from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 로그인 요구 데코레이터
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator  # 페이지네이션 추가
from .models import FollowUp, Schedule, History, UserProfile, Company, Department, HistoryFile # HistoryFile 모델 추가
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from functools import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import mimetypes

# 납품 품목 처리 함수
def save_delivery_items(request, instance_obj):
    """납품 품목 데이터를 저장하는 함수 (스케줄 또는 히스토리)"""
    from .models import DeliveryItem
    
    # 인스턴스 타입 확인
    from .models import Schedule, History
    is_schedule = isinstance(instance_obj, Schedule)
    is_history = isinstance(instance_obj, History)
    
    if not (is_schedule or is_history):
        return
    
    # 기존 품목들 삭제 (수정 시)
    if is_schedule:
        instance_obj.delivery_items_set.all().delete()
    else:  # is_history
        instance_obj.delivery_items_set.all().delete()
    
    # 새로운 형태의 POST 데이터 처리 (delivery_items[0][name] 형태)
    delivery_items_data = {}
    for key, value in request.POST.items():
        if key.startswith('delivery_items[') and '][' in key:
            # delivery_items[0][name] -> index=0, field=name
            try:
                start = key.find('[') + 1
                end = key.find(']')
                index = int(key[start:end])
                
                field_start = key.rfind('[') + 1
                field_end = key.rfind(']')
                field = key[field_start:field_end]
                
                if index not in delivery_items_data:
                    delivery_items_data[index] = {}
                delivery_items_data[index][field] = value
            except (ValueError, IndexError):
                continue
    
    # 납품 품목 저장
    for index, item_data in delivery_items_data.items():
        item_name = item_data.get('name', '').strip()
        quantity = item_data.get('quantity', '').strip()
        unit_price = item_data.get('unit_price', '').strip()
        
        if item_name and quantity:
            try:
                delivery_item = DeliveryItem(
                    item_name=item_name,
                    quantity=int(quantity),
                    unit='개',  # 기본값
                )
                
                # 스케줄 또는 히스토리 연결
                if is_schedule:
                    delivery_item.schedule = instance_obj
                else:
                    delivery_item.history = instance_obj
                
                if unit_price:
                    delivery_item.unit_price = float(unit_price)
                
                delivery_item.save()
            except (ValueError, TypeError):
                continue  # 잘못된 데이터는 무시

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

# 파일 업로드 관련 헬퍼 함수들
def validate_file_upload(file):
    """업로드된 파일의 유효성을 검사"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
        '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar'
    ]
    
    # 파일 크기 검사
    if file.size > MAX_FILE_SIZE:
        return False, f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 업로드 가능합니다."
    
    # 파일 확장자 검사
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"지원하지 않는 파일 형식입니다. 허용된 확장자: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, "유효한 파일입니다."

def handle_file_uploads(files, history, user):
    """여러 파일 업로드를 처리"""
    MAX_FILES = 5
    uploaded_files = []
    errors = []
    
    if len(files) > MAX_FILES:
        return [], [f"최대 {MAX_FILES}개의 파일만 업로드할 수 있습니다."]
    
    for file in files:
        is_valid, message = validate_file_upload(file)
        if not is_valid:
            errors.append(f"{file.name}: {message}")
            continue
            
        try:
            history_file = HistoryFile.objects.create(
                history=history,
                file=file,
                original_filename=file.name,
                file_size=file.size,
                uploaded_by=user
            )
            uploaded_files.append(history_file)
        except Exception as e:
            errors.append(f"{file.name}: 업로드 중 오류가 발생했습니다.")
    
    return uploaded_files, errors

def can_modify_user_data(request_user, target_user):
    """현재 사용자가 대상 사용자의 데이터를 수정/추가/삭제할 수 있는지 확인"""
    user_profile = get_user_profile(request_user)
    
    # Admin은 모든 데이터 수정 가능
    if user_profile.is_admin():
        return True
    
    # Manager는 읽기만 가능하고 수정 불가
    if user_profile.is_manager():
        return False
    
    # Salesman은 자신의 데이터만 수정 가능
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
    # 자동완성을 위한 hidden 필드들
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': '업체/학교를 선택해주세요.'}
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': '부서/연구실명은 필수 입력사항입니다.'}
    )
    
    class Meta:
        model = FollowUp
        fields = ['customer_name', 'company', 'department', 'manager', 'phone_number', 'email', 'address', 'notes', 'priority']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '고객명을 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            'manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '책임자명을 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '010-0000-0000 (선택사항)', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@company.com (선택사항)', 'autocomplete': 'off'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '상세주소를 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '상세 내용을 입력하세요 (선택사항)', 'autocomplete': 'off'}),
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
        
    def clean_company(self):
        company = self.cleaned_data.get('company')
        if not company:
            raise forms.ValidationError('업체/학교를 선택해주세요.')
        return company

    def clean_department(self):
        department = self.cleaned_data.get('department')
        if not department:
            raise forms.ValidationError('부서/연구실명은 필수 입력사항입니다.')
        return department

# 일정 폼 클래스
class ScheduleForm(forms.ModelForm):
    followup = forms.ModelChoiceField(
        queryset=FollowUp.objects.none(),  # 초기에는 비어있음
        widget=forms.Select(attrs={
            'class': 'form-control followup-autocomplete',
            'data-placeholder': '팔로우업을 검색하세요...',
            'data-url': '',  # JavaScript에서 설정됨
        }),
        label='관련 팔로우업',
        help_text='고객명, 업체명 또는 부서명으로 검색할 수 있습니다.'
    )
    
    class Meta:
        model = Schedule
        fields = ['followup', 'visit_date', 'visit_time', 'activity_type', 'location', 'status', 'notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'visit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '방문 장소를 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '메모를 입력하세요 (선택사항)', 'autocomplete': 'off'}),
        }
        labels = {
            'visit_date': '방문 날짜',
            'visit_time': '방문 시간',
            'activity_type': '일정 유형',
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
                base_queryset = FollowUp.objects.all()
            else:
                base_queryset = FollowUp.objects.filter(user=user)
                
            # 기존 인스턴스가 있는 경우 해당 팔로우업도 포함
            if self.instance.pk and self.instance.followup:
                # Q 객체를 사용하여 기존 팔로우업과 사용자 팔로우업을 OR 조건으로 결합
                from django.db.models import Q
                if user.is_staff or user.is_superuser:
                    queryset_filter = Q()  # 모든 팔로우업
                else:
                    queryset_filter = Q(user=user) | Q(pk=self.instance.followup.pk)
                self.fields['followup'].queryset = FollowUp.objects.filter(queryset_filter).select_related('company', 'department').distinct()
            else:
                self.fields['followup'].queryset = base_queryset.select_related('company', 'department')
                
            # 자동완성 URL 설정
            from django.urls import reverse
            self.fields['followup'].widget.attrs['data-url'] = reverse('reporting:followup_autocomplete')

# 히스토리 폼 클래스
class HistoryForm(forms.ModelForm):
    # 파일 업로드 필드 (JavaScript로 여러 파일 처리)
    files = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar'
        }),
        label='첨부파일',
        help_text='최대 10MB, 최대 5개 파일까지 업로드 가능'
    )
    
    class Meta:
        model = History
        fields = ['followup', 'schedule', 'action_type', 'service_status', 'content', 'delivery_amount', 'delivery_items', 'delivery_date', 'meeting_date']
        widgets = {
            'followup': forms.Select(attrs={'class': 'form-control'}),
            'schedule': forms.Select(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-control'}),
            'service_status': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '활동 내용을 입력하세요', 'autocomplete': 'off'}),
            'delivery_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '납품 금액을 입력하세요 (원)', 'min': '0', 'autocomplete': 'off'}),
            'delivery_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '납품 품목을 입력하세요 (예: 제품A 10개, 제품B 5개)', 'autocomplete': 'off'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'meeting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        }
        labels = {
            'followup': '관련 고객 정보',
            'schedule': '관련 일정',
            'action_type': '활동 유형',
            'service_status': '서비스 상태',
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
                if self.instance.followup:
                    self.fields['schedule'].queryset = self.instance.followup.schedules.all()
                else:
                    # 팔로우업이 없는 경우 (일반 메모 등) 빈 쿼리셋 유지
                    self.fields['schedule'].queryset = Schedule.objects.none()
                
            # 선택된 일정이 있으면 해당 일정의 activity_type에 맞게 action_type 매핑
            if 'schedule' in self.data and self.data.get('schedule'):
                try:
                    schedule_id = int(self.data.get('schedule'))
                    selected_schedule = Schedule.objects.get(id=schedule_id)
                    # 일정의 activity_type을 히스토리의 action_type으로 매핑
                    activity_mapping = {
                        'customer_meeting': 'customer_meeting',
                        'delivery': 'delivery_schedule',
                        'service': 'service',
                    }
                    # Schedule 모델의 activity_type을 확인하여 매핑
                    if hasattr(selected_schedule, 'activity_type'):
                        mapped_action = activity_mapping.get(selected_schedule.activity_type, 'customer_meeting')
                        self.fields['action_type'].initial = mapped_action
                except (ValueError, TypeError, Schedule.DoesNotExist):
                    pass
        
        # 일정은 선택사항으로 설정
        self.fields['schedule'].required = False
        self.fields['schedule'].empty_label = "관련 일정 없음"
        
        # 활동 유형에서 메모 제외 (메모는 별도 폼에서만 생성 가능)
        self.fields['action_type'].choices = [
            choice for choice in self.fields['action_type'].choices 
            if choice[0] != 'memo'
        ]
        
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
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related('user', 'company', 'department').prefetch_related('schedules', 'histories')
    else:
        # Salesman은 자신의 데이터만 조회
        followups = FollowUp.objects.filter(user=request.user).select_related('user', 'company', 'department').prefetch_related('schedules', 'histories')
    
    # 고객명/업체명 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 담당자 필터링 - 권한 체크 추가
    user_filter = request.GET.get('user')
    if user_filter:
        # 접근 권한이 있는 사용자인지 확인
        accessible_users = get_accessible_users(request.user)
        try:
            filter_user = accessible_users.get(id=user_filter)
            followups = followups.filter(user=filter_user)
        except User.DoesNotExist:
            # 접근 권한이 없는 사용자인 경우 필터링하지 않음
            pass
    
    # 업체별 카운트 (업체 필터 적용 전 기준)
    from django.db.models import Count, Q as DbQ
    stats = followups.aggregate(
        total_count=Count('id'),
        active_count=Count('id', filter=DbQ(status='active')),
        completed_count=Count('id', filter=DbQ(status='completed')),
        paused_count=Count('id', filter=DbQ(status='paused'))
    )
    
    # 업체 필터링 (카운트 계산 후에 적용)
    company_filter = request.GET.get('company')
    if company_filter:
        followups = followups.filter(
            Q(company_id=company_filter) | Q(department__company_id=company_filter)
        )
      
    # 정렬 (최신순)
    followups = followups.order_by('-created_at')
    
    # 담당자 목록 (필터용) - 권한 기반으로 수정
    user_profile = get_user_profile(request.user)
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자 목록
        accessible_users = get_accessible_users(request.user)
        users = accessible_users.filter(followup__isnull=False).distinct()
    else:
        # Salesman은 자기 자신만
        users = [request.user]
    
    # 업체 목록 (필터용) - 각 업체별 팔로우업 개수 계산
    accessible_users = get_accessible_users(request.user)
    companies = Company.objects.filter(
        Q(followup_companies__user__in=accessible_users) |
        Q(departments__followup_departments__user__in=accessible_users)
    ).distinct().order_by('name')
    
    # 각 업체별 팔로우업 개수 계산
    for company in companies:
        company.followup_count = FollowUp.objects.filter(
            Q(company=company) | Q(department__company=company),
            user__in=accessible_users
        ).count()
    
    # 선택된 사용자 정보 - 권한 체크 추가
    selected_user = None
    if user_filter:
        try:
            from django.contrib.auth.models import User
            candidate_user = User.objects.get(id=user_filter)
            # 접근 권한이 있는 사용자인지 확인
            accessible_users = get_accessible_users(request.user)
            if candidate_user in accessible_users:
                selected_user = candidate_user
        except (User.DoesNotExist, ValueError):
            pass
    
    # 선택된 업체 정보
    selected_company = None
    if company_filter:
        try:
            selected_company = Company.objects.get(id=company_filter)
        except (Company.DoesNotExist, ValueError):
            pass
            if candidate_user in accessible_users:
                selected_user = candidate_user
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
        'company_filter': company_filter,
        'user_filter': user_filter,
        'selected_user': selected_user,
        'selected_company': selected_company,
        'total_count': stats['total_count'],
        'active_count': stats['active_count'],
        'completed_count': stats['completed_count'],
        'paused_count': stats['paused_count'],
        'users': users,
        'companies': companies,
        'user_profile': user_profile,  # 사용자 프로필 추가
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
    
    # 관련 히스토리 조회 (일정이 있는 경우 일정 날짜 기준, 없는 경우 작성일 기준으로 최신순)
    from django.db.models import Case, When, F
    related_histories = History.objects.filter(followup=followup).annotate(
        sort_date=Case(
            When(schedule__isnull=False, then=F('schedule__visit_date')),
            default=F('created_at__date')
        )
    ).order_by('-sort_date', '-created_at')[:10]
    
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
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, followup.user):
        messages.error(request, '수정 권한이 없습니다. Manager는 읽기 전용입니다.')
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
    
    # 권한 체크: 삭제 권한이 있는 경우만 삭제 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, followup.user):
        messages.error(request, '삭제 권한이 없습니다. Manager는 읽기 전용입니다.')
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
    
    # 현재 연도와 월 가져오기
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # 권한에 따른 데이터 필터링
    if user_profile.is_admin() and not selected_user:
        # Admin은 모든 데이터 접근 가능
        followup_count = FollowUp.objects.count()
        schedule_count = Schedule.objects.filter(status='scheduled').count()
        # 영업 기록 (미팅, 납품만 카운팅 - 서비스 제외)
        sales_record_count = History.objects.filter(
            created_at__year=current_year, 
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
        histories = History.objects.all()
        histories_current_year = History.objects.filter(created_at__year=current_year)
        schedules = Schedule.objects.all()
        followups = FollowUp.objects.all()
    else:
        # 특정 사용자 또는 본인의 데이터만 접근
        followup_count = FollowUp.objects.filter(user=target_user).count()
        schedule_count = Schedule.objects.filter(user=target_user, status='scheduled').count()
        # 영업 기록 (미팅, 납품만 카운팅 - 서비스 제외)
        sales_record_count = History.objects.filter(
            user=target_user, 
            created_at__year=current_year, 
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
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
      # 활동 유형별 통계 (현재 연도만, 메모 제외)
    activity_stats = histories_current_year.exclude(action_type='memo').values('action_type').annotate(
        count=Count('id')
    ).order_by('action_type')
    
    # 서비스 통계 추가 (완료된 서비스만 카운팅)
    service_count = histories_current_year.filter(action_type='service', service_status='completed').count()
    
    # 이번 달 서비스 수 (완료된 것만)
    this_month_service_count = histories.filter(
        action_type='service',
        service_status='completed',
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
      # 최근 활동 (현재 연도, 최근 5개, 메모 제외)
    recent_activities = histories_current_year.exclude(action_type='memo').order_by('-created_at')[:5]
    
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
      # 영업 기록 추이 (최근 14일, 미팅/납품만 - 서비스 제외)
    fourteen_days_ago = now - timedelta(days=14)
    daily_activities = []
    for i in range(14):
        day = fourteen_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # 영업 활동만 카운팅 (미팅, 납품 - 서비스 제외)
        activity_count = histories_current_year.filter(
            created_at__gte=day_start,
            created_at__lt=day_end,
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
        
        daily_activities.append({
            'date': day.strftime('%m/%d'),
            'full_date': day.strftime('%Y-%m-%d'),
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
    
    # 이번 달 서비스 수 (완료된 것만)
    monthly_services = histories.filter(
        action_type='service',
        service_status='completed',
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
      # 납품 전환율 (현재 연도 기준 미팅 대비 납품 비율, 메모 제외)
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

    # 월별 서비스 데이터 (최근 6개월, 완료된 서비스만)
    monthly_service_data = []
    monthly_service_labels = []
    for i in range(5, -1, -1):
        target_date = now - timedelta(days=30*i)
        service_count_monthly = histories.filter(
            action_type='service',
            service_status='completed',
            created_at__month=target_date.month,
            created_at__year=target_date.year
        ).count()
        
        monthly_service_data.append(service_count_monthly)
        monthly_service_labels.append(f"{target_date.year}년 {target_date.month}월")

    context = {        'page_title': '대시보드',
        'current_year': current_year,  # 현재 연도 정보 추가
        'selected_user': selected_user,  # 선택된 사용자 정보
        'target_user': target_user,  # 실제 대상 사용자
        'followup_count': followup_count,
        'schedule_count': schedule_count,
        'sales_record_count': sales_record_count,
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
        'monthly_services': monthly_services,
        'service_count': service_count,
        'this_month_service_count': this_month_service_count,
        'conversion_rate': conversion_rate,
        'avg_deal_size': avg_deal_size,
        'monthly_revenue_data': monthly_revenue_data,
        'monthly_revenue_labels': monthly_revenue_labels,        'customer_revenue_labels': customer_labels,
        'customer_revenue_data': customer_amounts,
        'monthly_service_data': monthly_service_data,
        'monthly_service_labels': monthly_service_labels,
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
            Q(followup__company__name__icontains=search_query) |
            Q(followup__department__name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
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
    
    # 필터 값 가져오기
    status_filter = request.GET.get('status')
    activity_type_filter = request.GET.get('activity_type')
    
    # 기본 쿼리셋 (검색, 담당자, 날짜 필터가 적용된 상태)
    base_queryset = schedules
    
    # 상태별 카운트 계산 (활동 유형 필터만 적용된 상태에서)
    if activity_type_filter:
        status_count_queryset = base_queryset.filter(activity_type=activity_type_filter)
    else:
        status_count_queryset = base_queryset
    
    total_count = status_count_queryset.count()
    scheduled_count = status_count_queryset.filter(status='scheduled').count()
    completed_count = status_count_queryset.filter(status='completed').count()
    cancelled_count = status_count_queryset.filter(status='cancelled').count()
    
    # 활동 유형별 카운트 계산 (상태 필터만 적용된 상태에서)
    if status_filter:
        activity_count_queryset = base_queryset.filter(status=status_filter)
    else:
        activity_count_queryset = base_queryset
    
    activity_total_count = activity_count_queryset.count()  # 활동 유형 필터용 전체 카운트
    meeting_count = activity_count_queryset.filter(activity_type='customer_meeting').count()
    delivery_count = activity_count_queryset.filter(activity_type='delivery').count()
    service_count = activity_count_queryset.filter(activity_type='service').count()
    
    # 두 필터 모두 적용
    if status_filter:
        schedules = schedules.filter(status=status_filter)
    
    if activity_type_filter:
        schedules = schedules.filter(activity_type=activity_type_filter)
    
    # 정렬 (예정됨 우선, 그 다음 최신 날짜순)
    # Django의 Case를 사용해서 상태별 우선순위 설정
    from django.db.models import Case, When, IntegerField
    schedules = schedules.annotate(
        status_priority=Case(
            When(status='scheduled', then=1),    # 예정됨: 최우선
            When(status='completed', then=2),    # 완료됨: 두번째
            When(status='cancelled', then=3),    # 취소됨: 마지막
            default=4,
            output_field=IntegerField()
        )
    ).order_by('status_priority', '-visit_date', '-visit_time')  # 상태 우선순위 → 최신 날짜순 → 최신 시간순    # 담당자 목록 (필터용)
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
    
    # 페이지네이션 제거 - 항상 모든 데이터 로드
    page_obj = schedules
    
    context = {
        'schedules': page_obj,
        'page_title': '일정 목록',
        'status_filter': status_filter,
        'activity_type_filter': activity_type_filter,
        'total_count': total_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'activity_total_count': activity_total_count,
        'meeting_count': meeting_count,
        'delivery_count': delivery_count,
        'service_count': service_count,
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
    
    # 이전 페이지 정보 (캘린더에서 온 경우)
    from_page = request.GET.get('from', 'list')  # 기본값은 'list'
    
    context = {
        'schedule': schedule,
        'related_histories': related_histories,
        'delivery_items': schedule.delivery_items_set.all(),
        'from_page': from_page,
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
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, schedule.user):
        messages.error(request, '수정 권한이 없습니다. Manager는 읽기 전용입니다.')
        return redirect('reporting:schedule_list')
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            updated_schedule = form.save()
            
            # 납품 품목 처리 (활동 유형이 납품인 경우)
            if updated_schedule.activity_type == 'delivery':
                save_delivery_items(request, updated_schedule)
            
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
          # 권한 체크: 삭제 권한이 있는 경우만 허용 (Manager는 읽기 전용)
        if not can_modify_user_data(request.user, schedule.user):
            logger.warning(f"권한 없음 - 요청자: {request.user.username}, 일정 소유자: {schedule.user.username}")
            # AJAX 요청 감지 - X-Requested-With 헤더 확인
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
            messages.error(request, '삭제 권한이 없습니다. Manager는 읽기 전용입니다.')
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
            
            # 이전 페이지 정보 확인 (캘린더에서 온 경우)
            from_page = request.GET.get('from', 'list')
            user_filter = request.GET.get('user', '')  # user 파라미터로 수정
            
            # 캘린더에서 온 경우 캘린더로 돌아가기
            if from_page == 'calendar':
                if user_filter:
                    return redirect(f"{reverse('reporting:schedule_calendar')}?user={user_filter}")
                else:
                    return redirect('reporting:schedule_calendar')
            else:
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
def schedule_update_delivery_items(request, pk):
    """일정의 납품 품목 업데이트"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능
    if not can_modify_user_data(request.user, schedule.user):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:schedule_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # 납품 품목 저장
            save_delivery_items(request, schedule)
            messages.success(request, '납품 품목이 성공적으로 업데이트되었습니다.')
        except Exception as e:
            messages.error(request, f'납품 품목 업데이트 중 오류가 발생했습니다: {str(e)}')
        
        return redirect('reporting:schedule_detail', pk=pk)
    
    # GET 요청은 허용하지 않음
    return redirect('reporting:schedule_detail', pk=pk)

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
    try:
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
                'followup_id': schedule.followup.id,  # 팔로우업 ID 추가
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'time': schedule.visit_time.strftime('%H:%M'),
                'customer': schedule.followup.customer_name or '고객명 미정',
                'company': str(schedule.followup.company) if schedule.followup.company else '업체명 미정',
                'department': str(schedule.followup.department) if schedule.followup.department else '부서명 미정',
                'manager': schedule.followup.manager or '',
                'address': schedule.followup.address or '',
                'location': schedule.location or '',
                'status': schedule.status,
                'status_display': schedule.get_status_display(),
                'activity_type': schedule.activity_type,
                'activity_type_display': schedule.get_activity_type_display(),
                'notes': schedule.notes or '',
                'user_name': schedule.user.username,
            })
        
        return JsonResponse(schedule_data, safe=False)
    
    except Exception as e:
        # 에러 디버깅을 위한 JSON 응답
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'message': 'schedule_api_view에서 오류가 발생했습니다.'
        }, status=500)# ============ 히스토리(History) 관련 뷰들 ============

@login_required
def history_list_view(request):
    """히스토리 목록 보기 (권한 기반 필터링 적용)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        histories = History.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        histories = History.objects.filter(user=request.user)
    
    # 관련 객체들을 미리 로드하여 성능 최적화
    histories = histories.select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'schedule'
    )
    
    # 검색 기능 (책임자 검색 추가)
    search_query = request.GET.get('search')
    if search_query:
        histories = histories.filter(
            Q(content__icontains=search_query) |
            Q(followup__customer_name__icontains=search_query) |
            Q(followup__company__name__icontains=search_query) |
            Q(followup__manager__icontains=search_query)
        )
    
    # 담당자 필터링 (매니저/어드민만 사용 가능)
    user_filter = request.GET.get('user')
    user_profile = get_user_profile(request.user)
    if user_filter and user_profile.can_view_all_users():
        histories = histories.filter(user_id=user_filter)
    
    # 팔로우업 필터링 (특정 팔로우업의 모든 히스토리 보기)
    followup_filter = request.GET.get('followup')
    if followup_filter:
        histories = histories.filter(followup_id=followup_filter)
    
    # 날짜 범위 필터링 제거
    # date_from = request.GET.get('date_from')
    # date_to = request.GET.get('date_to')
    
    # if date_from:
    #     try:
    #         from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    #         histories = histories.filter(created_at__date__gte=from_date)
    #     except ValueError:
    #         pass
    
    # if date_to:
    #     try:
    #         to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    #         histories = histories.filter(created_at__date__lte=to_date)
    #     except ValueError:
    #         pass
    
    # 활동 유형별 카운트 계산
    base_queryset_for_counts = histories
    total_count = base_queryset_for_counts.count()
    meeting_count = base_queryset_for_counts.filter(action_type='customer_meeting').count()
    delivery_count = base_queryset_for_counts.filter(action_type='delivery_schedule').count()
    service_count = base_queryset_for_counts.filter(action_type='service', service_status='completed').count()
    memo_count = base_queryset_for_counts.filter(action_type='memo').count()
    
    # 활동 유형 필터링
    action_type_filter = request.GET.get('action_type')
    if action_type_filter:
        histories = histories.filter(action_type=action_type_filter)
    
    # 월별 필터링 추가
    months_filter = request.GET.get('months')
    month_filter = None
    if months_filter:
        try:
            selected_months = [int(month.strip()) for month in months_filter.split(',') if month.strip().isdigit()]
            if selected_months:
                month_filter = months_filter  # 템플릿에서 사용할 원본 문자열
                # 월별 필터링 적용 순서:
                # 1. 관련 일정이 있는 경우 → 일정의 visit_date 월로 필터링
                # 2. 관련 일정이 없는 경우 → 히스토리 생성일자(created_at) 월로 필터링
                from django.db.models import Q, Case, When, IntegerField
                from django.db.models.functions import Extract
                histories = histories.annotate(
                    filter_month=Case(
                        When(schedule__isnull=False, then=Extract('schedule__visit_date', 'month')),
                        default=Extract('created_at', 'month'),
                        output_field=IntegerField()
                    )
                ).filter(filter_month__in=selected_months)
        except (ValueError, TypeError):
            pass
    
    # 정렬 (일정이 있는 경우 일정 날짜 기준, 없는 경우 작성일 기준으로 최신순)
    from django.db.models import Case, When, F
    histories = histories.annotate(
        sort_date=Case(
            When(schedule__isnull=False, then=F('schedule__visit_date')),
            default=F('created_at__date')
        )
    ).order_by('-sort_date', '-created_at')
    # 담당자 목록 (매니저/어드민용 필터)
    users = []
    selected_user = None
    user_profile = get_user_profile(request.user)
    
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자 목록
        accessible_users = get_accessible_users(request.user)
        users = accessible_users.filter(history__isnull=False).distinct()
        
        # 선택된 사용자 정보 - 권한 체크 추가
        if user_filter:
            try:
                from django.contrib.auth.models import User
                candidate_user = User.objects.get(id=user_filter)
                # 접근 권한이 있는 사용자인지 확인
                if candidate_user in accessible_users:
                    selected_user = candidate_user
            except (User.DoesNotExist, ValueError):
                pass
    
    # 선택된 팔로우업 정보
    selected_followup = None
    if followup_filter:
        try:
            candidate_followup = FollowUp.objects.get(id=followup_filter)
            # 접근 권한이 있는지 확인
            if can_access_user_data(request.user, candidate_followup.user):
                selected_followup = candidate_followup
        except (FollowUp.DoesNotExist, ValueError):
            pass
    
    # 페이지 제목 동적 설정
    if selected_followup:
        page_title = f'{selected_followup.customer_name or "고객명 미정"} 활동 히스토리'
    else:
        page_title = '활동 히스토리'
    
    # 페이지네이션 제거 - 항상 모든 데이터 로드
    page_obj = histories
    
    context = {
        'histories': page_obj,
        'page_title': page_title,
        'action_type_filter': action_type_filter,
        'month_filter': month_filter,
        'total_count': total_count,
        'meeting_count': meeting_count,
        'delivery_count': delivery_count,
        'service_count': service_count,
        'memo_count': memo_count,
        'search_query': search_query,
        'user_filter': user_filter,
        'selected_user': selected_user,
        'followup_filter': followup_filter,
        'selected_followup': selected_followup,
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
    
    # 매니저 메모 추가 처리
    user_profile = get_user_profile(request.user)
    if request.method == 'POST' and user_profile.is_manager():
        manager_memo = request.POST.get('manager_memo', '').strip()
        if manager_memo:
            # 매니저 메모를 새로운 히스토리로 생성
            memo_history = History.objects.create(
                followup=history.followup,
                user=history.user,  # 원래 실무자를 유지
                action_type='memo',
                content=f"[매니저 메모 - {request.user.username}] {manager_memo}",
                created_by=request.user,  # 실제 작성자는 매니저
                schedule=history.schedule if history.schedule else None
            )
            messages.success(request, '매니저 메모가 추가되었습니다.')
            return redirect('reporting:history_detail', pk=pk)
    
    # 사용자 필터 정보 추가 (Manager가 특정 사용자의 활동을 보고 있는 경우)
    user_filter = request.GET.get('user_filter', '')
    if not user_filter and request.user != history.user:
        # Manager가 다른 사용자의 활동을 보고 있다면 해당 사용자 필터 설정
        user_profile = get_user_profile(request.user)
        if user_profile.can_view_all_users():
            user_filter = history.user.id
    
    # 동일한 팔로우업의 최근 히스토리들 가져오기 (메모 포함)
    related_histories = History.objects.filter(
        followup=history.followup
    ).select_related('user', 'created_by', 'schedule').order_by('-created_at')[:10]
    
    context = {
        'history': history,
        'related_histories': related_histories,
        'user_filter': user_filter,
        'can_add_memo': user_profile.is_manager(),
        'page_title': f'활동 상세 - {history.followup.customer_name if history.followup else "일반 메모"}'
    }
    return render(request, 'reporting/history_detail.html', context)

@login_required
def history_create_view(request):
    """히스토리 생성"""
    if request.method == 'POST':
        form = HistoryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            history = form.save(commit=False)
            history.user = request.user
            history.save()
            
            # 납품 품목 저장
            save_delivery_items(request, history)
            
            # 파일 업로드 처리
            uploaded_files = request.FILES.getlist('files')
            if uploaded_files:
                uploaded_file_objects, file_errors = handle_file_uploads(uploaded_files, history, request.user)
                
                if uploaded_file_objects:
                    file_count = len(uploaded_file_objects)
                    messages.success(request, f'활동 히스토리가 성공적으로 기록되었습니다. ({file_count}개 파일 업로드됨)')
                else:
                    messages.success(request, '활동 히스토리가 성공적으로 기록되었습니다.')
                
                # 파일 업로드 오류가 있는 경우 경고 메시지 표시
                for error in file_errors:
                    messages.warning(request, f'파일 업로드 오류: {error}')
            else:
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
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, history.user):
        messages.error(request, '수정 권한이 없습니다. Manager는 읽기 전용입니다.')
        return redirect('reporting:history_list')
    
    if request.method == 'POST':
        form = HistoryForm(request.POST, request.FILES, instance=history, user=request.user)
        if form.is_valid():
            form.save()
            
            # 납품 품목 저장
            save_delivery_items(request, history)
            
            # 새로운 파일 업로드 처리
            uploaded_files = request.FILES.getlist('files')
            if uploaded_files:
                uploaded_file_objects, file_errors = handle_file_uploads(uploaded_files, history, request.user)
                
                if uploaded_file_objects:
                    file_count = len(uploaded_file_objects)
                    messages.success(request, f'활동 히스토리가 성공적으로 수정되었습니다. ({file_count}개 파일 추가 업로드됨)')
                else:
                    messages.success(request, '활동 히스토리가 성공적으로 수정되었습니다.')
                
                # 파일 업로드 오류가 있는 경우 경고 메시지 표시
                for error in file_errors:
                    messages.warning(request, f'파일 업로드 오류: {error}')
            else:
                messages.success(request, '활동 히스토리가 성공적으로 수정되었습니다.')
            
            return redirect('reporting:history_detail', pk=history.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = HistoryForm(instance=history, user=request.user)
    
    context = {
        'form': form,
        'history': history,
        'existing_delivery_items': history.delivery_items_set.all(),
        'page_title': f'활동 수정 - {history.followup.customer_name if history.followup else "일반 메모"}'
    }
    return render(request, 'reporting/history_form.html', context)

@login_required
def history_delete_view(request, pk):
    """히스토리 삭제"""
    history = get_object_or_404(History, pk=pk)
    
    # 권한 체크: 삭제 권한이 있는 경우만 삭제 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, history.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': '삭제 권한이 없습니다. Manager는 읽기 전용입니다.'
            })
        messages.error(request, '삭제 권한이 없습니다. Manager는 읽기 전용입니다.')
        return redirect('reporting:history_list')
    
    if request.method == 'POST':
        customer_name = history.followup.customer_name or "고객명 미정" if history.followup else "일반 메모"
        action_display = history.get_action_type_display()
        
        try:
            history.delete()
            success_message = f'{customer_name} ({action_display}) 활동 기록이 삭제되었습니다.'
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_message
                })
            
            # 일반 요청인 경우 기존 방식
            messages.success(request, success_message)
            return redirect('reporting:history_list')
            
        except Exception as e:
            error_message = f'활동 기록 삭제 중 오류가 발생했습니다: {str(e)}'
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            
            # 일반 요청인 경우 기존 방식
            messages.error(request, error_message)
            return redirect('reporting:history_list')
    
    context = {
        'history': history,
        'page_title': f'활동 삭제 - {history.followup.customer_name or "고객명 미정" if history.followup else "일반 메모"}'
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

@login_required
def schedule_histories_api(request, schedule_id):
    """특정 일정의 관련 활동 기록을 JSON으로 반환"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        # 해당 일정에 직접 연결된 활동 기록만 조회 (최신순)
        histories = History.objects.filter(schedule=schedule).order_by('-created_at')
        
        histories_data = []
        for history in histories:
            # 활동 타입에 따른 추가 정보 포함
            history_data = {
                'id': history.id,
                'action_type': history.action_type,
                'action_type_display': history.get_action_type_display(),
                'content': history.content or '',
                'created_at': history.created_at.strftime('%Y-%m-%d %H:%M'),
                'user': history.user.username,
                'created_by': history.created_by.username if history.created_by else history.user.username,
            }
            
            # 첨부파일 정보 추가
            files_data = []
            for file_obj in history.files.all():
                files_data.append({
                    'id': file_obj.id,
                    'filename': file_obj.original_filename,
                    'size': file_obj.get_file_size_display(),
                    'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                    'uploaded_by': file_obj.uploaded_by.username,
                })
            history_data['files'] = files_data
            
            # 납품 일정인 경우 추가 정보
            if history.action_type == 'delivery_schedule':
                history_data.update({
                    'delivery_amount': history.delivery_amount,
                    'delivery_items': history.delivery_items or '',
                    'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
                    'tax_invoice_issued': history.tax_invoice_issued,
                })
            
            # 고객 미팅인 경우 추가 정보
            elif history.action_type == 'customer_meeting':
                history_data.update({
                    'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
                })
            
            # 서비스인 경우 추가 정보
            elif history.action_type == 'service':
                history_data.update({
                    'service_status': history.service_status or '',
                    'service_status_display': history.get_service_status_display() if history.service_status else '',
                })
            
            histories_data.append(history_data)
        
        return JsonResponse({
            'success': True,
            'histories': histories_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def followup_histories_api(request, followup_id):
    """특정 팔로우업의 모든 활동 기록을 JSON으로 반환"""
    try:
        followup = get_object_or_404(FollowUp, id=followup_id)
        
        # 권한 체크 - followup.user가 None인 경우를 처리
        if followup.user:
            if not can_access_user_data(request.user, followup.user):
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        else:
            # followup.user가 None인 경우, 현재 사용자가 관리자이거나 매니저인 경우만 접근 허용
            user_profile = get_user_profile(request.user)
            if not (user_profile.is_admin() or user_profile.is_manager()):
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        # 해당 팔로우업의 모든 활동 기록 조회 (최신순)
        histories = History.objects.filter(followup=followup).order_by('-created_at')
        
        histories_data = []
        for history in histories:
            try:
                # 활동 타입에 따른 추가 정보 포함
                history_data = {
                    'id': history.id,
                    'action_type': history.action_type,
                    'action_type_display': history.get_action_type_display(),
                    'content': history.content or '',
                    'created_at': history.created_at.strftime('%Y-%m-%d %H:%M'),
                    'user': history.user.username if history.user else '사용자 미정',
                    'created_by': history.created_by.username if history.created_by else (history.user.username if history.user else '사용자 미정'),
                }
                
                # 납품 일정인 경우 추가 정보
                if history.action_type == 'delivery_schedule':
                    history_data.update({
                        'delivery_amount': history.delivery_amount,
                        'delivery_items': history.delivery_items or '',
                        'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
                        'tax_invoice_issued': history.tax_invoice_issued,
                    })
                
                # 고객 미팅인 경우 추가 정보
                elif history.action_type == 'customer_meeting':
                    history_data.update({
                        'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
                    })
                
                histories_data.append(history_data)
                
            except Exception as history_error:
                # 개별 히스토리 처리 중 에러가 발생해도 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"History {history.id} processing error: {str(history_error)}")
                continue
        
        return JsonResponse({
            'success': True,
            'customer_name': followup.customer_name or '고객명 미정',
            'company': followup.company.name if followup.company else '업체명 미정',
            'histories': histories_data,
            'total_count': len(histories_data)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"followup_histories_api error for followup_id={followup_id}: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'서버 에러: {str(e)}'}, status=500)

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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '한글 이름 (예: 홍길동)', 'autocomplete': 'off'}),
        label='사용자 이름'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label='비밀번호'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label='비밀번호 확인'
    )
    role = forms.ChoiceField(
        choices=[('manager', 'Manager (뷰어)'), ('salesman', 'SalesMan (실무자)')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='권한'
    )
    can_download_excel = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='엑셀 다운로드 권한',
        help_text='체크 시 팔로우업 엑셀 다운로드가 가능합니다'
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '성 (선택사항)', 'autocomplete': 'off'}),
        label='성'
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름 (선택사항)', 'autocomplete': 'off'}),
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '한글 이름 (예: 홍길동)', 'autocomplete': 'off'}),
        label='사용자 이름'
    )
    role = forms.ChoiceField(
        choices=[('admin', 'Admin (최고권한자)'), ('manager', 'Manager (뷰어)'), ('salesman', 'SalesMan (실무자)')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='권한'
    )
    can_download_excel = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='엑셀 다운로드 권한',
        help_text='체크 시 팔로우업 엑셀 다운로드가 가능합니다 (관리자는 항상 가능)'
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '성 (선택사항)', 'autocomplete': 'off'}),
        label='성'
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름 (선택사항)', 'autocomplete': 'off'}),
        label='이름'
    )
    change_password = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='비밀번호 변경'
    )
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label='새 비밀번호'
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
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
                can_download_excel=form.cleaned_data['can_download_excel'],
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
            user_profile.can_download_excel = form.cleaned_data['can_download_excel']
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
            'can_download_excel': user_profile.can_download_excel,
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
    
    # 히스토리 통계 (현재 연도, 메모 제외)
    total_histories = histories.exclude(action_type='memo').count()
    delivery_histories = histories.filter(action_type='delivery_schedule')
    service_histories = histories.filter(action_type='service', service_status='completed')
    total_delivery_amount = delivery_histories.aggregate(
        total=Sum('delivery_amount')
    )['total'] or 0
    
    # 월별 데이터 (날짜 기준)
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
        
        # 서비스는 완료된 것만 집계
        month_services = histories.filter(
            action_type='service',
            service_status='completed',
            created_at__month=month
        )
        
        monthly_data.append({
            'month': f'{month}월',
            'meetings': month_meetings.count(),
            'deliveries': month_deliveries.count(),
            'services': month_services.count(),
            'amount': month_deliveries.aggregate(total=Sum('delivery_amount'))['total'] or 0
        })
        
        monthly_delivery.append(month_deliveries.aggregate(total=Sum('delivery_amount'))['total'] or 0)
    
    # 고객별 납품 현황 (현재 연도)
    customer_delivery = {}
    for history in delivery_histories:
        customer = history.followup.customer_name or history.followup.company or "고객명 미정" if history.followup else "일반 메모"
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
        'total_services': service_histories.count(),
        'monthly_data': monthly_data,
        'monthly_delivery': monthly_delivery,
        'top_customers': top_customers,
        'page_title': f'Manager 대시보드 - {"전체보기" if view_all else selected_user.username}'
    }
    return render(request, 'reporting/manager_dashboard.html', context)

@role_required(['manager', 'admin'])
def salesman_detail(request, user_id):
    """특정 Salesman의 상세 정보 조회 (Manager, Admin 전용)"""
    try:
        # 먼저 user_id가 유효한 정수인지 확인
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            messages.error(request, '잘못된 사용자 ID입니다.')
            return redirect('reporting:manager_dashboard')
        
        # 접근 권한 확인
        accessible_users = get_accessible_users(request.user)
        
        # 해당 사용자가 존재하고 접근 가능한지 확인
        try:
            selected_user = accessible_users.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, '해당 사용자를 찾을 수 없거나 접근 권한이 없습니다.')
            return redirect('reporting:manager_dashboard')
        
        # 사용자 프로필 확인
        try:
            user_profile = selected_user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(request, '사용자 프로필이 설정되지 않았습니다.')
            return redirect('reporting:manager_dashboard')
        
        # 해당 사용자의 데이터만 필터링 (select_related로 성능 최적화)
        followups = FollowUp.objects.filter(user=selected_user).select_related('user')
        schedules = Schedule.objects.filter(user=selected_user).select_related('user', 'followup')
        histories = History.objects.filter(user=selected_user).select_related('user', 'followup', 'schedule')
        
        # 검색 및 필터링
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        
        if search_query:
            followups = followups.filter(
                Q(customer_name__icontains=search_query) |
                Q(company__icontains=search_query)
            )
        
        if status_filter and status_filter in ['initial', 'in_progress', 'visited', 'closed']:
            followups = followups.filter(status=status_filter)
        
        # 정렬 추가
        followups = followups.order_by('-updated_at')
        
        # 페이지네이션 전에 총 개수 계산 (안전하게)
        try:
            total_followups = followups.count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"팔로우업 개수 계산 중 오류: {str(e)}")
            total_followups = 0
        
        # 페이지네이션 처리 (단순화)
        try:
            from django.core.paginator import Paginator
            paginator = Paginator(followups, 10)
            page_number = request.GET.get('page', 1)
            try:
                page_number = int(page_number)
            except (ValueError, TypeError):
                page_number = 1
            followups = paginator.get_page(page_number)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"페이지네이션 처리 중 오류: {str(e)}")
            # 페이지네이션 실패 시 원본 쿼리셋 유지하되 첫 10개만
            followups = followups[:10]
        
        # 집계 값들을 안전하게 계산
        try:
            total_schedules = schedules.count()
            total_histories = histories.count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"집계 계산 중 오류: {str(e)}")
            total_schedules = 0
            total_histories = 0
        
        context = {
            'selected_user': selected_user,
            'followups': followups,
            'search_query': search_query,
            'status_filter': status_filter,
            'total_followups': total_followups,
            'total_schedules': total_schedules,
            'total_histories': total_histories,
            'page_title': f'{selected_user.username} 상세 정보'
        }
        return render(request, 'reporting/salesman_detail.html', context)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"salesman_detail 오류 - user_id: {user_id}, user: {request.user}, error: {str(e)}")
        messages.error(request, f'사용자 상세 정보를 불러오는 중 오류가 발생했습니다. 관리자에게 문의하세요.')
        return redirect('reporting:manager_dashboard')

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
        
        # 권한 체크: 수정 권한이 있는 경우만 토글 가능 (Manager는 읽기 전용)
        try:
            if not can_modify_user_data(request.user, history.user):
                return JsonResponse({
                    'success': False, 
                    'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'
                }, status=403)
        except Exception as e:
            # 권한 체크 실패 시 자신의 히스토리인지만 확인
            if request.user != history.user:
                return JsonResponse({
                    'success': False, 
                    'error': '수정 권한이 없습니다.'
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
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': '이 일정에 대한 히스토리를 생성할 권한이 없습니다.'})
                messages.error(request, '이 일정에 대한 히스토리를 생성할 권한이 없습니다.')
                return redirect('reporting:schedule_list')
        except Exception as e:
            # 권한 체크 실패 시 자신의 일정인지만 확인
            if request.user != schedule.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': '이 일정에 대한 히스토리를 생성할 권한이 없습니다.'})
                messages.error(request, '이 일정에 대한 히스토리를 생성할 권한이 없습니다.')
                return redirect('reporting:schedule_list')
        
        if request.method == 'POST':
            # AJAX 요청인지 확인
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            # 디버깅용 로그
            print(f"POST data: {request.POST}")
            print(f"Is AJAX: {is_ajax}")
            
            # 인라인 폼에서 온 데이터를 위해 followup과 schedule을 자동 설정
            post_data = request.POST.copy()
            post_data['followup'] = schedule.followup.id
            post_data['schedule'] = schedule.id
            
            form = HistoryForm(post_data, user=request.user)
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
                
                # 파일 업로드 처리
                uploaded_files = request.FILES.getlist('files')
                for uploaded_file in uploaded_files:
                    if uploaded_file:  # 빈 파일 체크
                        # 파일 크기 제한 (10MB)
                        max_size = 10 * 1024 * 1024  # 10MB
                        if uploaded_file.size > max_size:
                            continue  # 큰 파일은 건너뛰기
                        
                        # 파일 확장자 검증
                        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.hwp']
                        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                        if file_extension not in allowed_extensions:
                            continue  # 허용되지 않은 확장자는 건너뛰기
                        
                        # HistoryFile 생성
                        HistoryFile.objects.create(
                            history=history,
                            file=uploaded_file,
                            original_filename=uploaded_file.name,
                            file_size=uploaded_file.size,
                            uploaded_by=request.user
                        )
                
                if is_ajax:
                    # AJAX 요청인 경우 JSON 응답
                    return JsonResponse({
                        'success': True,
                        'message': f'"{schedule.followup.customer_name}" 일정에 대한 활동 히스토리가 성공적으로 기록되었습니다.',
                        'history_id': history.id
                    })
                else:
                    # 일반 폼 제출인 경우 일정 상세 페이지로 리다이렉트
                    messages.success(request, f'"{schedule.followup.customer_name}" 일정에 대한 활동 히스토리가 성공적으로 기록되었습니다.')
                    return redirect('reporting:schedule_detail', pk=schedule.pk)
            else:
                # 폼 검증 실패
                print(f"Form errors: {form.errors}")
                if is_ajax:
                    # AJAX 요청인 경우 오류 응답
                    errors = []
                    for field, field_errors in form.errors.items():
                        for error in field_errors:
                            field_label = form.fields.get(field, {}).get('label', field) if hasattr(form.fields, 'get') else field
                            errors.append(f"{field_label}: {error}")
                    return JsonResponse({
                        'success': False,
                        'error': '입력 정보를 확인해주세요: ' + ', '.join(errors),
                        'form_errors': form.errors
                    })
                else:
                    # 일반 폼 제출인 경우 기존 동작
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
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        
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
    
    # 권한 체크: 수정 권한이 있는 경우만 이동 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, schedule.user):
        return JsonResponse({'success': False, 'error': '이 일정을 이동할 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
    
    try:
        # POST 데이터에서 새로운 날짜 정보 가져오기 (FormData 형식)
        new_date = request.POST.get('new_date')  # 'YYYY-MM-DD' 형식
        
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
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'일정 이동 중 오류가 발생했습니다: {str(e)}'}, status=500)

@login_required
@require_POST
def schedule_status_update_api(request, schedule_id):
    """일정 상태 업데이트 API"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 상태 변경 가능 (Manager는 읽기 전용)
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status not in ['scheduled', 'completed', 'cancelled']:
            return JsonResponse({'error': '잘못된 상태값입니다.'}, status=400)
        
        old_status = schedule.status
        schedule.status = new_status
        schedule.save()
        
        status_display = {
            'scheduled': '예정됨',
            'completed': '완료됨', 
            'cancelled': '취소됨'
        }
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'status_display': status_display[new_status],
            'message': f'일정 상태가 "{status_display[new_status]}"로 변경되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def schedule_add_memo_api(request, schedule_id):
    """일정에 매니저 메모 추가 API"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        user_profile = get_user_profile(request.user)
        
        # 권한 체크: 매니저만 메모 추가 가능하고, 해당 실무자의 일정에만 접근 가능
        if not user_profile.is_manager():
            return JsonResponse({'error': '매니저만 메모를 추가할 수 있습니다.'}, status=403)
        
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'error': '이 일정에 접근할 권한이 없습니다.'}, status=403)
        
        memo_content = request.POST.get('memo', '').strip()
        if not memo_content:
            return JsonResponse({'error': '메모 내용을 입력해주세요.'}, status=400)
        
        # 매니저 메모를 히스토리로 생성
        memo_history = History.objects.create(
            followup=schedule.followup,
            user=request.user,  # 매니저가 작성자
            action_type='memo',
            content=memo_content,  # 매니저 메모 표시 제거
            created_by=request.user,  # 실제 작성자는 매니저
            schedule=schedule
        )
        
        return JsonResponse({
            'success': True,
            'message': '매니저 메모가 추가되었습니다.',
            'memo': {
                'id': memo_history.id,
                'content': memo_history.content,
                'created_at': memo_history.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': request.user.username
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'메모 추가 중 오류가 발생했습니다: {str(e)}'}, status=500)

# 자동완성 API 뷰들
@login_required
def company_autocomplete(request):
    """업체/학교명 자동완성 API"""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    companies = Company.objects.filter(
        name__icontains=query
    ).order_by('name')[:10]
    
    results = []
    for company in companies:
        results.append({
            'id': company.id,
            'text': company.name
        })
    
    return JsonResponse({'results': results})

@login_required
def department_autocomplete(request):
    """부서/연구실명 자동완성 API"""
    query = request.GET.get('q', '').strip()
    company_id = request.GET.get('company_id')
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    departments = Department.objects.filter(name__icontains=query)
    
    # 회사가 선택된 경우 해당 회사의 부서만 필터링
    if company_id:
        departments = departments.filter(company_id=company_id)
    
    departments = departments.select_related('company').order_by('company__name', 'name')[:10]
    
    results = []
    for dept in departments:
        results.append({
            'id': dept.id,
            'text': f"{dept.company.name} - {dept.name}",
            'company_id': dept.company.id,
            'company_name': dept.company.name,
            'department_name': dept.name
        })
    
    return JsonResponse({'results': results})

@login_required
def followup_autocomplete(request):
    """팔로우업 자동완성 API (일정 생성용)"""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # 현재 사용자의 권한에 따른 팔로우업 필터링
    user_profile = get_user_profile(request.user)
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users)
    else:
        followups = FollowUp.objects.filter(user=request.user)
    
    # 검색어로 필터링 (고객명, 업체명, 부서명, 책임자명으로 검색)
    followups = followups.filter(
        Q(customer_name__icontains=query) |
        Q(company__name__icontains=query) |
        Q(department__name__icontains=query) |
        Q(manager__icontains=query)
    ).select_related('company', 'department', 'user').order_by('company__name', 'customer_name')[:15]
    
    results = []
    for followup in followups:
        # 표시 텍스트 구성
        company_name = str(followup.company) if followup.company else '업체명 미정'
        department_name = str(followup.department) if followup.department else '부서명 미정'
        customer_name = followup.customer_name or '고객명 미정'
        
        display_text = f"{company_name} - {department_name} | {customer_name}"
        
        # 관리자/매니저인 경우 담당자 정보도 표시
        if user_profile.can_view_all_users() and followup.user != request.user:
            display_text += f" ({followup.user.username})"
        
        results.append({
            'id': followup.id,
            'text': display_text,
            'customer_name': customer_name,
            'company_name': company_name,
            'department_name': department_name,
            'user_name': followup.user.username
        })
    
    return JsonResponse({'results': results})

@login_required
def schedule_activity_type(request):
    """일정의 activity_type을 반환하는 API"""
    schedule_id = request.GET.get('schedule_id')
    if schedule_id:
        try:
            schedule = Schedule.objects.get(id=schedule_id, user=request.user)
            # 일정의 activity_type을 히스토리의 action_type으로 매핑
            activity_mapping = {
                'customer_meeting': 'customer_meeting',
                'delivery': 'delivery_schedule',
                'service': 'service',
            }
            mapped_action = activity_mapping.get(schedule.activity_type, 'customer_meeting')
            return JsonResponse({
                'success': True,
                'activity_type': schedule.activity_type,
                'mapped_action_type': mapped_action
            })
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'error': '일정을 찾을 수 없습니다.'})
    
    return JsonResponse({'success': False, 'error': '일정 ID가 필요합니다.'})

@login_required
@csrf_exempt
@require_POST
def company_create_api(request):
    """새 업체/학교 생성 API"""
    name = request.POST.get('name', '').strip()
    
    if not name:
        return JsonResponse({'error': '업체/학교명을 입력해주세요.'}, status=400)
    
    # 중복 체크
    if Company.objects.filter(name=name).exists():
        return JsonResponse({'error': '이미 존재하는 업체/학교명입니다.'}, status=400)
    
    try:
        company = Company.objects.create(name=name, created_by=request.user)
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name
            },
            'message': f'"{name}" 업체/학교가 추가되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'error': f'업체/학교 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_POST
def department_create_api(request):
    """새 부서/연구실 생성 API"""
    name = request.POST.get('name', '').strip()
    company_id = request.POST.get('company_id')
    
    if not name:
        return JsonResponse({'error': '부서/연구실명을 입력해주세요.'}, status=400)
    
    if not company_id:
        return JsonResponse({'error': '업체/학교를 먼저 선택해주세요.'}, status=400)
    
    try:
        company = Company.objects.get(id=company_id)
        
        # 중복 체크
        if Department.objects.filter(company=company, name=name).exists():
            return JsonResponse({'error': f'{company.name}에 이미 존재하는 부서/연구실명입니다.'}, status=400)
        
        department = Department.objects.create(company=company, name=name, created_by=request.user)
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'company_id': company.id,
                'company_name': company.name
            },
            'message': f'"{company.name} - {name}" 부서/연구실이 추가되었습니다.'
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': '존재하지 않는 업체/학교입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'부서/연구실 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)


# ============ 업체/부서 관리 뷰들 ============

@role_required(['admin', 'salesman'])
def company_list_view(request):
    """업체/학교 목록 (Admin, Salesman 전용)"""
    companies = Company.objects.annotate(
        department_count=Count('departments', distinct=True),
        followup_count=Count('followup_companies', distinct=True)
    ).order_by('name')
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(name__icontains=search_query)
    
    # 페이지네이션
    paginator = Paginator(companies, 10)
    page_number = request.GET.get('page')
    companies = paginator.get_page(page_number)
    
    context = {
        'companies': companies,
        'search_query': search_query,
        'page_title': '업체/학교 관리'
    }
    return render(request, 'reporting/company_list.html', context)

@role_required(['admin', 'salesman'])
def company_create_view(request):
    """업체/학교 생성 (Admin, Salesman 전용)"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '업체/학교명을 입력해주세요.')
        elif Company.objects.filter(name=name).exists():
            messages.error(request, '이미 존재하는 업체/학교명입니다.')
        else:
            Company.objects.create(name=name, created_by=request.user)
            messages.success(request, f'"{name}" 업체/학교가 추가되었습니다.')
            return redirect('reporting:company_list')
    
    context = {
        'page_title': '새 업체/학교 추가'
    }
    return render(request, 'reporting/company_form.html', context)

@role_required(['admin', 'salesman'])
def company_edit_view(request, pk):
    """업체/학교 수정 (Admin, 생성자 전용)"""
    company = get_object_or_404(Company, pk=pk)
    
    # 권한 체크: 관리자이거나 생성자만 수정 가능
    user_profile = get_user_profile(request.user)
    if not (user_profile.role == 'admin' or company.created_by == request.user):
        messages.error(request, '이 업체/학교를 수정할 권한이 없습니다. (생성자 또는 관리자만 가능)')
        return redirect('reporting:company_list')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '업체/학교명을 입력해주세요.')
        elif Company.objects.filter(name=name).exclude(pk=company.pk).exists():
            messages.error(request, '이미 존재하는 업체/학교명입니다.')
        else:
            company.name = name
            company.save()
            messages.success(request, f'"{name}" 업체/학교 정보가 수정되었습니다.')
            return redirect('reporting:company_list')
    
    context = {
        'company': company,
        'page_title': f'업체/학교 수정 - {company.name}'
    }
    return render(request, 'reporting/company_form.html', context)

@role_required(['admin', 'salesman'])
def company_delete_view(request, pk):
    """업체/학교 삭제 (Admin, 생성자 전용)"""
    company = get_object_or_404(Company, pk=pk)
    
    # 권한 체크: 관리자이거나 생성자만 삭제 가능
    user_profile = get_user_profile(request.user)
    if not (user_profile.role == 'admin' or company.created_by == request.user):
        messages.error(request, '이 업체/학교를 삭제할 권한이 없습니다. (생성자 또는 관리자만 가능)')
        return redirect('reporting:company_list')
    
    # 관련 데이터 개수 확인
    department_count = company.departments.count()
    followup_count = company.followup_companies.count()
    
    if request.method == 'POST':
        company_name = company.name
        
        if followup_count > 0:
            messages.error(request, f'이 업체/학교를 사용하는 고객 정보가 {followup_count}개 있어 삭제할 수 없습니다.')
            return redirect('reporting:company_list')
        
        company.delete()
        messages.success(request, f'"{company_name}" 업체/학교가 삭제되었습니다.')
        return redirect('reporting:company_list')
    
    context = {
        'company': company,
        'department_count': department_count,
        'followup_count': followup_count,
        'page_title': f'업체/학교 삭제 - {company.name}'
    }
    return render(request, 'reporting/company_delete.html', context)

@role_required(['admin', 'salesman'])
def company_detail_view(request, pk):
    """업체/학교 상세 (부서 목록 포함) (Admin, Salesman 전용)"""
    company = get_object_or_404(Company, pk=pk)
    
    # 해당 업체의 부서 목록
    departments = company.departments.annotate(
        followup_count=Count('followup_departments')
    ).order_by('name')
    
    # 검색 기능 (부서명)
    dept_search = request.GET.get('dept_search', '')
    if dept_search:
        departments = departments.filter(name__icontains=dept_search)
    
    context = {
        'company': company,
        'departments': departments,
        'dept_search': dept_search,
        'page_title': f'{company.name} - 부서/연구실 관리'
    }
    return render(request, 'reporting/company_detail.html', context)

@role_required(['admin', 'salesman'])
def department_create_view(request, company_pk):
    """부서/연구실 생성 (Admin, Salesman 전용)"""
    company = get_object_or_404(Company, pk=company_pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '부서/연구실명을 입력해주세요.')
        elif Department.objects.filter(company=company, name=name).exists():
            messages.error(request, f'{company.name}에 이미 존재하는 부서/연구실명입니다.')
        else:
            Department.objects.create(company=company, name=name, created_by=request.user)
            messages.success(request, f'"{company.name} - {name}" 부서/연구실이 추가되었습니다.')
            return redirect('reporting:company_detail', pk=company.pk)
    
    context = {
        'company': company,
        'page_title': f'{company.name} - 새 부서/연구실 추가'
    }
    return render(request, 'reporting/department_form.html', context)

@role_required(['admin', 'salesman'])
def department_edit_view(request, pk):
    """부서/연구실 수정 (Admin, 생성자 전용)"""
    department = get_object_or_404(Department, pk=pk)
    
    # 권한 체크: 관리자이거나 생성자만 수정 가능
    user_profile = get_user_profile(request.user)
    if not (user_profile.role == 'admin' or department.created_by == request.user):
        messages.error(request, '이 부서/연구실을 수정할 권한이 없습니다. (생성자 또는 관리자만 가능)')
        return redirect('reporting:company_detail', pk=department.company.pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '부서/연구실명을 입력해주세요.')
        elif Department.objects.filter(company=department.company, name=name).exclude(pk=department.pk).exists():
            messages.error(request, f'{department.company.name}에 이미 존재하는 부서/연구실명입니다.')
        else:
            department.name = name
            department.save()
            messages.success(request, f'"{department.company.name} - {name}" 부서/연구실 정보가 수정되었습니다.')
            return redirect('reporting:company_detail', pk=department.company.pk)
    
    context = {
        'department': department,
        'page_title': f'{department.company.name} - 부서/연구실 수정'
    }
    return render(request, 'reporting/department_form.html', context)

@role_required(['admin', 'salesman'])
def department_delete_view(request, pk):
    """부서/연구실 삭제 (Admin, 생성자 전용)"""
    department = get_object_or_404(Department, pk=pk)
    
    # 권한 체크: 관리자이거나 생성자만 삭제 가능
    user_profile = get_user_profile(request.user)
    if not (user_profile.role == 'admin' or department.created_by == request.user):
        messages.error(request, '이 부서/연구실을 삭제할 권한이 없습니다. (생성자 또는 관리자만 가능)')
        return redirect('reporting:company_detail', pk=department.company.pk)
    
    # 관련 데이터 개수 확인
    followup_count = department.followup_departments.count()
    
    if request.method == 'POST':
        department_name = department.name
        company_name = department.company.name
        company_pk = department.company.pk
        
        if followup_count > 0:
            messages.error(request, f'이 부서/연구실을 사용하는 고객 정보가 {followup_count}개 있어 삭제할 수 없습니다.')
            return redirect('reporting:company_detail', pk=company_pk)
        
        department.delete()
        messages.success(request, f'"{company_name} - {department_name}" 부서/연구실이 삭제되었습니다.')
        return redirect('reporting:company_detail', pk=company_pk)
    
    context = {
        'department': department,
        'followup_count': followup_count,
        'page_title': f'{department.company.name} - 부서/연구실 삭제'
    }
    return render(request, 'reporting/department_delete.html', context)

# ============ 매니저용 읽기 전용 업체/부서 뷰들 ============

@role_required(['manager'])
def manager_company_list_view(request):
    """매니저용 업체/학교 목록 (읽기 전용)"""
    companies = Company.objects.annotate(
        department_count=Count('departments', distinct=True),
        followup_count=Count('followup_companies', distinct=True)
    ).order_by('name')
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(name__icontains=search_query)
    
    # 각 업체별 담당자 정보 추가
    companies_with_salesmen = []
    for company in companies:
        # 해당 업체를 담당하는 실무자들 조회
        followups_in_company = FollowUp.objects.filter(
            Q(company=company) | Q(department__company=company)
        ).select_related('user').distinct()
        
        # 담당자 목록 (중복 제거)
        salesmen = list(set(followup.user for followup in followups_in_company))
        
        # 회사 객체에 담당자 정보 추가
        company.salesmen = salesmen
        companies_with_salesmen.append(company)
    
    # 페이지네이션
    paginator = Paginator(companies_with_salesmen, 10)
    page_number = request.GET.get('page')
    companies = paginator.get_page(page_number)
    
    context = {
        'companies': companies,
        'search_query': search_query,
        'page_title': '업체/학교 목록 (조회)',
        'is_readonly': True
    }
    return render(request, 'reporting/company_list.html', context)

@role_required(['manager'])
def manager_company_detail_view(request, pk):
    """매니저용 업체/학교 상세 (읽기 전용)"""
    company = get_object_or_404(Company, pk=pk)
    
    # 해당 업체의 부서 목록
    departments = company.departments.annotate(
        followup_count=Count('followup_departments')
    ).order_by('name')
    
    # 검색 기능 (부서명)
    dept_search = request.GET.get('dept_search', '')
    if dept_search:
        departments = departments.filter(name__icontains=dept_search)
    
    # 해당 업체를 관리하는 실무자들 조회
    followups_in_company = FollowUp.objects.filter(
        Q(company=company) | Q(department__company=company)
    ).select_related('user', 'user__userprofile')
    
    # 실무자별 담당 고객 수 집계
    salesmen_stats = {}
    for followup in followups_in_company:
        user = followup.user
        if user not in salesmen_stats:
            salesmen_stats[user] = {
                'user': user,
                'followup_count': 0,
                'recent_activity': None
            }
        salesmen_stats[user]['followup_count'] += 1
        
        # 가장 최근 활동 히스토리 찾기 (메모 제외)
        recent_history = History.objects.filter(
            followup=followup
        ).exclude(action_type='memo').order_by('-created_at').first()
        
        if recent_history and (
            not salesmen_stats[user]['recent_activity'] or
            recent_history.created_at > salesmen_stats[user]['recent_activity'].created_at
        ):
            salesmen_stats[user]['recent_activity'] = recent_history
    
    # 실무자 목록 (담당 고객 수 순으로 정렬)
    salesmen_list = sorted(
        salesmen_stats.values(), 
        key=lambda x: x['followup_count'], 
        reverse=True
    )
    
    # 페이지네이션 (부서)
    paginator = Paginator(departments, 10)
    page_number = request.GET.get('page')
    departments = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'departments': departments,
        'dept_search': dept_search,
        'salesmen_list': salesmen_list,
        'page_title': f'{company.name} - 상세 정보 (조회)',
        'is_readonly': True
    }
    return render(request, 'reporting/company_detail.html', context)

# ============ 추가 API 엔드포인트들 ============

@login_required
def api_company_detail(request, pk):
    """개별 회사 정보 조회 API"""
    try:
        company = get_object_or_404(Company, pk=pk)
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required  
def api_department_detail(request, pk):
    """개별 부서 정보 조회 API"""
    try:
        department = get_object_or_404(Department, pk=pk)
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'company_id': department.company.id,
                'company_name': department.company.name
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def history_detail_api(request, history_id):
    """히스토리 상세 정보를 JSON으로 반환하는 API"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 접근 권한 확인
        user_profile = get_user_profile(request.user)
        if user_profile.role == 'salesman' and history.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '이 기록에 접근할 권한이 없습니다.'
            })
        
        # 히스토리 데이터 직렬화
        history_data = {
            'id': history.id,
            'content': history.content or '',
            'action_type': history.action_type,
            'action_type_display': history.get_action_type_display(),
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': history.user.get_full_name() or history.user.username,
            'created_by': history.created_by.username if history.created_by else '',
            'followup_id': history.followup.id if history.followup else None,
            'schedule_id': history.schedule.id if history.schedule else None,
            
            # 납품 일정 관련 필드
            'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
            'delivery_amount': history.delivery_amount,
            'delivery_items': history.delivery_items or '',
            'tax_invoice_issued': history.tax_invoice_issued,
            
            # 고객 미팅 관련 필드
            'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
            
            # 서비스 관련 필드
            'service_status': history.service_status or '',
            'service_status_display': history.get_service_status_display() if history.service_status else '',
            
            # 첨부파일 정보
            'files': []
        }
        
        # 첨부파일 정보 추가
        for file in history.files.all():
            # 파일 크기를 읽기 쉬운 형태로 변환
            file_size = file.file_size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            else:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            
            history_data['files'].append({
                'id': file.id,
                'filename': file.original_filename,
                'size': size_str,
                'uploaded_at': file.uploaded_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'히스토리 정보를 불러올 수 없습니다: {str(e)}'
        })

@login_required
@require_POST
def history_update_api(request, history_id):
    """히스토리 업데이트 API"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 접근 권한 확인
        user_profile = get_user_profile(request.user)
        if user_profile.role == 'salesman' and history.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '이 기록을 수정할 권한이 없습니다.'
            })
        
        # 폼 데이터 처리
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({
                'success': False,
                'error': '활동 내용을 입력해주세요.'
            })
        
        # 기본 필드 업데이트
        history.content = content
        
        # 활동 유형별 추가 필드 처리
        if history.action_type == 'delivery_schedule':
            delivery_date = request.POST.get('delivery_date')
            if delivery_date:
                try:
                    from datetime import datetime
                    history.delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
                except ValueError:
                    history.delivery_date = None
            else:
                history.delivery_date = None
            
            delivery_amount = request.POST.get('delivery_amount')
            if delivery_amount:
                try:
                    history.delivery_amount = int(delivery_amount)
                except (ValueError, TypeError):
                    history.delivery_amount = None
            else:
                history.delivery_amount = None
            
            history.delivery_items = request.POST.get('delivery_items', '').strip()
            history.tax_invoice_issued = request.POST.get('tax_invoice_issued') == 'on'
            
        elif history.action_type == 'customer_meeting':
            meeting_date = request.POST.get('meeting_date')
            if meeting_date:
                try:
                    from datetime import datetime
                    history.meeting_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
                except ValueError:
                    history.meeting_date = None
            else:
                history.meeting_date = None
                
        elif history.action_type == 'service':
            history.service_status = request.POST.get('service_status', '')
        
        # 변경사항 저장
        history.save()
        
        # 기존 파일 삭제 처리
        delete_file_ids = request.POST.getlist('delete_files')
        if delete_file_ids:
            try:
                # 삭제할 파일들 조회 및 삭제
                files_to_delete = HistoryFile.objects.filter(
                    id__in=delete_file_ids,
                    history=history
                )
                for file_obj in files_to_delete:
                    # 실제 파일 삭제
                    if file_obj.file and os.path.exists(file_obj.file.path):
                        os.remove(file_obj.file.path)
                    # DB에서 삭제
                    file_obj.delete()
                    
            except Exception as delete_error:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 삭제 중 오류가 발생했습니다: {str(delete_error)}'
                })
        
        # 새로운 파일 첨부 처리
        uploaded_files = request.FILES.getlist('files')
        if uploaded_files:
            try:
                # 현재 파일 개수 확인 (삭제 후)
                current_file_count = history.files.count()
                total_files_after_upload = current_file_count + len(uploaded_files)
                
                # 파일 개수 제한 (최대 5개)
                if total_files_after_upload > 5:
                    return JsonResponse({
                        'success': False,
                        'error': f'파일은 최대 5개까지만 첨부할 수 있습니다. (현재 {current_file_count}개, 추가 {len(uploaded_files)}개)'
                    })
                
                # 각 파일 유효성 검사 및 저장
                for file in uploaded_files:
                    # 파일 크기 검사 (10MB)
                    if file.size > 10 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'error': f'파일 {file.name}이 10MB를 초과합니다.'
                        })
                    
                    # 파일 확장자 검사
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar']
                    file_extension = os.path.splitext(file.name)[1].lower()
                    if file_extension not in allowed_extensions:
                        return JsonResponse({
                            'success': False,
                            'error': f'파일 {file.name}은 지원되지 않는 형식입니다.'
                        })
                    
                    # 파일 저장
                    history_file = HistoryFile.objects.create(
                        history=history,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        uploaded_by=request.user
                    )
                    
            except Exception as file_error:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 중 오류가 발생했습니다: {str(file_error)}'
                })
        
        return JsonResponse({
            'success': True,
            'message': '활동 기록이 성공적으로 수정되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'활동 기록 수정 중 오류가 발생했습니다: {str(e)}'
        })

# ============ 메모 관련 뷰들 ============

@login_required
def memo_create_view(request):
    """메모 생성 (팔로우업 연결 선택사항)"""
    followup_id = request.GET.get('followup')
    followup = None
    
    if followup_id:
        try:
            followup = get_object_or_404(FollowUp, pk=followup_id)
            # 권한 체크 (팔로우업이 있는 경우만)
            if not can_modify_user_data(request.user, followup.user):
                messages.error(request, '메모 작성 권한이 없습니다.')
                return redirect('reporting:followup_detail', pk=followup.pk)
        except FollowUp.DoesNotExist:
            followup = None
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, '메모 내용을 입력해주세요.')
        else:
            # 메모 히스토리 생성
            history = History.objects.create(
                user=request.user,
                followup=followup,  # followup이 None일 수도 있음
                action_type='memo',
                content=content,
                schedule=None  # 메모는 일정과 연결되지 않음
            )
            
            messages.success(request, '메모가 성공적으로 추가되었습니다.')
            
            # 팔로우업이 있으면 팔로우업 상세로, 없으면 히스토리 목록으로
            if followup:
                return redirect('reporting:followup_detail', pk=followup.pk)
            else:
                return redirect('reporting:history_list')
    
    context = {
        'followup': followup,
        'page_title': f'메모 추가{" - " + followup.customer_name if followup else ""}',
    }
    return render(request, 'reporting/memo_form.html', context)


# ============ 인라인 메모 편집 API ============

@login_required
@require_POST
@csrf_exempt
def history_update_memo(request, pk):
    """AJAX 요청으로 메모 내용 업데이트"""
    import json
    
    try:
        history = get_object_or_404(History, pk=pk, action_type='memo')
        
        # 권한 체크
        if not can_modify_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '메모 수정 권한이 없습니다.'
            })
        
        # 요청 데이터 파싱
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({
                'success': False,
                'error': '메모 내용을 입력해주세요.'
            })
        
        # 메모 내용 업데이트
        history.content = new_content
        history.save()
        
        return JsonResponse({
            'success': True,
            'message': '메모가 성공적으로 수정되었습니다.'
        })
        
    except History.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '메모를 찾을 수 없습니다.'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '잘못된 요청 형식입니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'메모 수정 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
def followup_excel_download(request):
    """팔로우업 전체 정보 엑셀 다운로드 (권한 체크)"""
    user_profile = get_user_profile(request.user)
    
    # 엑셀 다운로드 권한 체크
    if not user_profile.can_excel_download():
        messages.error(request, '엑셀 다운로드 권한이 없습니다. 관리자에게 문의해주세요.')
        return redirect('reporting:followup_list')
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    import io
    from datetime import datetime
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링 (기존 로직과 동일)
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related(
            'user', 'company', 'department'
        ).prefetch_related('schedules', 'histories')
    else:
        followups = FollowUp.objects.filter(user=request.user).select_related(
            'user', 'company', 'department'
        ).prefetch_related('schedules', 'histories')
    
    # 검색 필터 적용
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 담당자 필터 적용
    user_filter = request.GET.get('user')
    if user_filter:
        accessible_users = get_accessible_users(request.user)
        try:
            filter_user = accessible_users.get(id=user_filter)
            followups = followups.filter(user=filter_user)
        except User.DoesNotExist:
            pass
    
    # 엑셀 파일 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "팔로우업 전체 정보"
    
    # 스타일 정의
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5F8F", end_color="2F5F8F", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    wrap_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    
    # 최대 히스토리 개수 계산
    max_histories = 0
    for followup in followups:
        history_count = followup.histories.count()
        max_histories = max(max_histories, history_count)
    
    # 헤더 생성
    headers = [
        '고객명', '업체/학교명', '부서/연구실명', '책임자', '핸드폰 번호', 
        '메일 주소', '상세 주소', '상세 내용'
    ]
    
    # 히스토리 컬럼 추가
    for i in range(1, max_histories + 1):
        headers.append(f'관련 활동 히스토리 {i}')
    
    # 헤더 스타일 적용
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_alignment
    
        # 데이터 입력
    for row_num, followup in enumerate(followups, 2):
        # 책임자 정보 가져오기 (FollowUp 모델의 manager 필드)
        manager_name = followup.manager or ''
        
        # 기본 정보
        data = [
            followup.customer_name or '',
            followup.company.name if followup.company else '',
            followup.department.name if followup.department else '',
            manager_name,  # FollowUp의 책임자 필드에서 가져오기
            followup.phone_number or '',
            followup.email or '',
            followup.address or '',
            followup.notes or ''
        ]
        
        # 히스토리 정보 추가
        histories = list(followup.histories.all().order_by('-created_at'))
        for i in range(max_histories):
            if i < len(histories):
                history = histories[i]
                history_text = f"[{history.created_at.strftime('%Y-%m-%d')}] {history.get_action_type_display()}: {history.content or ''}"
                data.append(history_text)
            else:
                data.append('')
        
        # 데이터 셀에 값 입력 및 스타일 적용
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = border
            cell.alignment = wrap_alignment
    
    # 컬럼 너비 자동 조정 (개선된 버전)
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                cell_value = str(cell.value) if cell.value is not None else ''
                # 한글과 영문의 너비 차이를 고려
                korean_chars = len([c for c in cell_value if ord(c) > 127])
                english_chars = len(cell_value) - korean_chars
                adjusted_length = korean_chars * 2 + english_chars
                
                if adjusted_length > max_length:
                    max_length = adjusted_length
            except:
                pass
        
        # 최소 8, 최대 60 문자로 제한하고, 여유분 추가
        adjusted_width = min(max(max_length + 3, 8), 60)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # 응답 생성
    today = datetime.now().strftime('%Y%m%d')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"전체정보_{today}.xlsx"
    
    # 한글 파일명을 올바르게 인코딩
    from urllib.parse import quote
    encoded_filename = quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    
    # 엑셀 파일을 메모리에서 저장
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    response.write(excel_file.getvalue())
    
    return response


@login_required
def followup_basic_excel_download(request):
    """팔로우업 기본 정보 엑셀 다운로드 (권한 체크)"""
    user_profile = get_user_profile(request.user)
    
    # 엑셀 다운로드 권한 체크
    if not user_profile.can_excel_download():
        messages.error(request, '엑셀 다운로드 권한이 없습니다. 관리자에게 문의해주세요.')
        return redirect('reporting:followup_list')
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    import io
    from datetime import datetime
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링 (기존 로직과 동일)
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related(
            'user', 'company', 'department'
        )
    else:
        followups = FollowUp.objects.filter(user=request.user).select_related(
            'user', 'company', 'department'
        )
    
    # 검색 필터 적용
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 담당자 필터 적용
    user_filter = request.GET.get('user')
    if user_filter:
        accessible_users = get_accessible_users(request.user)
        try:
            filter_user = accessible_users.get(id=user_filter)
            followups = followups.filter(user=filter_user)
        except User.DoesNotExist:
            pass
    
    # 엑셀 파일 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "팔로우업 기본 정보"
    
    # 스타일 정의
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5F8F", end_color="2F5F8F", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    
    # 헤더 생성
    headers = ['고객명', '업체/학교명', '부서/연구실명', '책임자', '핸드폰 번호', '메일 주소']
    
    # 헤더 스타일 적용
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_alignment
    
    # 데이터 입력
    for row_num, followup in enumerate(followups, 2):
        # 책임자 정보 가져오기 (FollowUp 모델의 manager 필드)
        manager_name = followup.manager or ''
        
        data = [
            followup.customer_name or '',
            followup.company.name if followup.company else '',
            followup.department.name if followup.department else '',
            manager_name,  # FollowUp의 책임자 필드에서 가져오기
            followup.phone_number or '',
            followup.email or ''
        ]
        
        # 데이터 셀에 값 입력 및 스타일 적용
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = border
            cell.alignment = left_alignment
    
    # 컬럼 너비 자동 조정 (개선된 버전)
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                cell_value = str(cell.value) if cell.value is not None else ''
                # 한글과 영문의 너비 차이를 고려
                korean_chars = len([c for c in cell_value if ord(c) > 127])
                english_chars = len(cell_value) - korean_chars
                adjusted_length = korean_chars * 2 + english_chars
                
                if adjusted_length > max_length:
                    max_length = adjusted_length
            except:
                pass
        
        # 최소 8, 최대 50 문자로 제한하고, 여유분 추가
        adjusted_width = min(max(max_length + 3, 8), 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # 응답 생성
    today = datetime.now().strftime('%Y%m%d')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"기본정보_{today}.xlsx"
    
    # 한글 파일명을 올바르게 인코딩
    from urllib.parse import quote
    encoded_filename = quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    
    # 엑셀 파일을 메모리에서 저장
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    response.write(excel_file.getvalue())
    
    return response

# 파일 관리 뷰들을 별도 모듈에서 import
from .file_views import (
    file_download_view, file_delete_view, history_files_api,
    schedule_file_upload, schedule_file_download, schedule_file_delete, schedule_files_api
) 

# ============ 고객 리포트 관련 뷰들 ============

@login_required
def customer_report_view(request):
    """고객별 활동 요약 리포트 목록"""
    from django.db.models import Count, Sum, Max, Q
    from decimal import Decimal
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        followups = FollowUp.objects.filter(user=request.user)
    
    # 각 고객별 활동 통계 집계
    followups_with_stats = followups.annotate(
        # 미팅 횟수
        total_meetings=Count('histories', filter=Q(histories__action_type='customer_meeting')),
        # 납품 횟수
        total_deliveries=Count('histories', filter=Q(histories__action_type='delivery_schedule')),
        # 총 납품 금액
        total_amount=Sum('histories__delivery_amount'),
        # 최근 접촉일
        last_contact=Max('histories__created_at'),
        # 미결제건 (세금계산서 미발행)
        unpaid_count=Count('histories', filter=Q(
            histories__action_type='delivery_schedule',
            histories__tax_invoice_issued=False
        ))
    ).select_related('user', 'company', 'department').order_by('-last_contact')
    
    # 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups_with_stats = followups_with_stats.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(manager__icontains=search_query)
        )
    
    # 담당자 필터링 (매니저/어드민만)
    user_filter = request.GET.get('user')
    users = []
    selected_user = None
    
    if user_profile.can_view_all_users():
        accessible_users_list = get_accessible_users(request.user)
        users = accessible_users_list.filter(followup__isnull=False).distinct()
        
        if user_filter:
            try:
                from django.contrib.auth.models import User
                candidate_user = User.objects.get(id=user_filter)
                if candidate_user in accessible_users_list:
                    selected_user = candidate_user
                    followups_with_stats = followups_with_stats.filter(user=candidate_user)
            except (User.DoesNotExist, ValueError):
                pass
    
    # 전체 통계
    total_customers = followups_with_stats.count()
    total_amount_sum = followups_with_stats.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    total_meetings_sum = followups_with_stats.aggregate(
        total=Sum('total_meetings')
    )['total'] or 0
    total_deliveries_sum = followups_with_stats.aggregate(
        total=Sum('total_deliveries')
    )['total'] or 0
    total_unpaid_sum = followups_with_stats.aggregate(
        total=Sum('unpaid_count')
    )['total'] or 0
    
    context = {
        'followups': followups_with_stats,
        'total_customers': total_customers,
        'total_amount_sum': total_amount_sum,
        'total_meetings_sum': total_meetings_sum,
        'total_deliveries_sum': total_deliveries_sum,
        'total_unpaid_sum': total_unpaid_sum,
        'search_query': search_query,
        'user_filter': user_filter,
        'selected_user': selected_user,
        'users': users,
        'page_title': '고객 리포트',
    }
    
    return render(request, 'reporting/customer_report_list.html', context)

@login_required
def customer_detail_report_view(request, followup_id):
    """특정 고객의 상세 활동 리포트"""
    from django.db.models import Count, Sum, Q
    from datetime import datetime, timedelta
    import json
    
    # 권한 확인 및 팔로우업 조회
    try:
        followup = FollowUp.objects.select_related('user', 'company', 'department').get(id=followup_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, followup.user):
            messages.error(request, '접근 권한이 없습니다.')
            return redirect('reporting:customer_report')
            
    except FollowUp.DoesNotExist:
        messages.error(request, '해당 고객 정보를 찾을 수 없습니다.')
        return redirect('reporting:customer_report')
    
    # 해당 고객의 모든 히스토리
    histories = History.objects.filter(followup=followup).select_related(
        'user', 'schedule'
    ).order_by('-created_at')
    
    # 기본 통계
    total_meetings = histories.filter(action_type='customer_meeting').count()
    total_deliveries = histories.filter(action_type='delivery_schedule').count()
    total_amount = histories.filter(action_type='delivery_schedule').aggregate(
        total=Sum('delivery_amount')
    )['total'] or 0
    
    # 세금계산서 현황
    tax_invoices_issued = histories.filter(
        action_type='delivery_schedule',
        tax_invoice_issued=True
    ).count()
    tax_invoices_pending = histories.filter(
        action_type='delivery_schedule',
        tax_invoice_issued=False
    ).count()
    
    # 월별 활동 통계 (최근 12개월)
    from django.db.models.functions import TruncMonth
    monthly_stats = histories.filter(
        created_at__gte=datetime.now() - timedelta(days=365)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        meetings=Count('id', filter=Q(action_type='customer_meeting')),
        deliveries=Count('id', filter=Q(action_type='delivery_schedule')),
        amount=Sum('delivery_amount')
    ).order_by('month')
    
    # Chart.js용 데이터 준비
    chart_labels = []
    chart_meetings = []
    chart_deliveries = []
    chart_amounts = []
    
    for stat in monthly_stats:
        chart_labels.append(stat['month'].strftime('%Y-%m'))
        chart_meetings.append(stat['meetings'])
        chart_deliveries.append(stat['deliveries'])
        chart_amounts.append(float(stat['amount'] or 0))
    
    # 납품 내역 상세
    delivery_histories = histories.filter(
        action_type='delivery_schedule'
    ).order_by('-delivery_date', '-created_at')
    
    # 미팅 기록
    meeting_histories = histories.filter(
        action_type='customer_meeting'
    ).order_by('-meeting_date', '-created_at')
    
    context = {
        'followup': followup,
        'histories': histories,
        'total_meetings': total_meetings,
        'total_deliveries': total_deliveries,
        'total_amount': total_amount,
        'tax_invoices_issued': tax_invoices_issued,
        'tax_invoices_pending': tax_invoices_pending,
        'delivery_histories': delivery_histories,
        'meeting_histories': meeting_histories,
        'chart_data': {
            'labels': json.dumps(chart_labels),
            'meetings': json.dumps(chart_meetings),
            'deliveries': json.dumps(chart_deliveries),
            'amounts': json.dumps(chart_amounts),
        },
        'page_title': f'{followup.customer_name or "고객명 미정"} 상세 리포트',
    }
    
    return render(request, 'reporting/customer_detail_report.html', context)
