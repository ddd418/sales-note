from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 로그인 요구 데코레이터
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator  # 페이지네이션 추가
from .models import FollowUp, Schedule, History, UserProfile, Company, Department, HistoryFile, DeliveryItem, UserCompany # UserCompany 추가
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from functools import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .decorators import hanagwahak_only, get_allowed_action_types, get_allowed_activity_types, filter_service_for_non_hanagwahak
import os
import mimetypes
import logging
import json

# 로거 설정
logger = logging.getLogger(__name__)

def save_delivery_items(request, instance_obj):
    """납품 품목 데이터를 저장하는 함수 (스케줄 또는 히스토리)"""
    from .models import DeliveryItem
    
    # 인스턴스 타입 확인
    from .models import Schedule, History
    is_schedule = isinstance(instance_obj, Schedule)
    is_history = isinstance(instance_obj, History)
    
    if not (is_schedule or is_history):
        logger.error(f"save_delivery_items: 지원되지 않는 객체 타입: {type(instance_obj)}")
        return
    
    logger.info(f"save_delivery_items: {'Schedule' if is_schedule else 'History'} {instance_obj.pk}에 대한 납품 품목 저장 시작")
    
    # 기존 품목들 삭제 (수정 시)
    if is_schedule:
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
        logger.info(f"기존 Schedule 납품 품목 {existing_count}개 삭제")
    else:  # is_history
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
        logger.info(f"기존 History 납품 품목 {existing_count}개 삭제")
    
    # POST 데이터 로깅
    logger.info(f"전체 POST 데이터: {dict(request.POST)}")
    
    # delivery_items 관련 POST 데이터만 필터링
    delivery_post_data = {k: v for k, v in request.POST.items() if 'delivery_items' in k}
    logger.info(f"납품 품목 관련 POST 데이터: {delivery_post_data}")
    
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
                
                logger.info(f"파싱됨: {key} -> index={index}, field={field}, value={value}")
            except (ValueError, IndexError) as e:
                logger.error(f"POST 데이터 파싱 실패: {key} = {value}, 오류: {e}")
                continue
    
    # 납품 품목 저장
    created_count = 0
    logger.info(f"파싱된 납품 품목 데이터: {delivery_items_data}")
    
    for index, item_data in delivery_items_data.items():
        item_name = item_data.get('name', '').strip()
        quantity = item_data.get('quantity', '').strip()
        unit_price = item_data.get('unit_price', '').strip()
        
        logger.info(f"품목 {index}: name={item_name}, quantity={quantity}, unit_price={unit_price}")
        
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
                    from decimal import Decimal
                    delivery_item.unit_price = Decimal(str(unit_price))
                
                delivery_item.save()
                created_count += 1
                logger.info(f"납품 품목 저장 성공: {delivery_item.item_name} (ID: {delivery_item.pk})")
            except (ValueError, TypeError) as e:
                logger.error(f"납품 품목 저장 실패: {e}")
                continue  # 잘못된 데이터는 무시
        else:
            logger.warning(f"필수 데이터 누락: name={item_name}, quantity={quantity}")
    
    logger.info(f"총 {created_count}개 납품 품목 저장 완료")
    return created_count

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
        # Manager는 같은 회사의 salesman들에만 접근 가능
        if hasattr(request_user, 'userprofile') and request_user.userprofile.company:
            user_company = request_user.userprofile.company
            # 같은 회사 소속의 salesman만 필터링
            salesman_profiles = UserProfile.objects.filter(
                role='salesman',
                company=user_company
            )
            return User.objects.filter(userprofile__in=salesman_profiles)
        else:
            # 회사 정보가 없는 매니저는 아무도 볼 수 없음
            return User.objects.none()
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
        request = kwargs.pop('request', None)
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
            
        # 하나과학이 아닌 경우 activity_type에서 서비스 제거
        if request and not getattr(request, 'is_hanagwahak', False):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[SCHFORM] request.is_hanagwahak = False, 서비스 옵션 제거")
            logger.info(f"[SCHFORM] 사용자: {getattr(request, 'user', 'Unknown')}")
            logger.info(f"[SCHFORM] 회사명: {getattr(request, 'user_company_name', 'Unknown')}")
            self.fields['activity_type'].choices = [
                choice for choice in self.fields['activity_type'].choices 
                if choice[0] != 'service'
            ]
        else:
            import logging
            logger = logging.getLogger(__name__)
            is_hanagwahak = getattr(request, 'is_hanagwahak', False) if request else False
            logger.info(f"[SCHFORM] request.is_hanagwahak = {is_hanagwahak}, 서비스 옵션 유지")
            if request:
                logger.info(f"[SCHFORM] 사용자: {getattr(request, 'user', 'Unknown')}")
                logger.info(f"[SCHFORM] 회사명: {getattr(request, 'user_company_name', 'Unknown')}")

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
        request = kwargs.pop('request', None)
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
        # 하나과학이 아닌 경우 서비스도 제외
        excluded_types = ['memo']
        if request and not getattr(request, 'is_hanagwahak', False):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[HISTORYFORM] request.is_hanagwahak = False, 서비스 옵션 제거")
            logger.info(f"[HISTORYFORM] 사용자: {getattr(request, 'user', 'Unknown')}")
            logger.info(f"[HISTORYFORM] 회사명: {getattr(request, 'user_company_name', 'Unknown')}")
            excluded_types.append('service')
        else:
            import logging
            logger = logging.getLogger(__name__)
            is_hanagwahak = getattr(request, 'is_hanagwahak', False) if request else False
            logger.info(f"[HISTORYFORM] request.is_hanagwahak = {is_hanagwahak}, 서비스 옵션 유지")
            if request:
                logger.info(f"[HISTORYFORM] 사용자: {getattr(request, 'user', 'Unknown')}")
                logger.info(f"[HISTORYFORM] 회사명: {getattr(request, 'user_company_name', 'Unknown')}")
            
        self.fields['action_type'].choices = [
            choice for choice in self.fields['action_type'].choices 
            if choice[0] not in excluded_types
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
    
    # 고객명/업체명/책임자명 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(manager__icontains=search_query) |
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
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 사용자 프로필 가져오기
    user_profile = get_user_profile(request.user)
    
    # 디버깅 로그 추가
    logger.info(f"[DASHBOARD] 사용자: {request.user.username}")
    logger.info(f"[DASHBOARD] 사용자 역할: {user_profile.role}")
    logger.info(f"[DASHBOARD] request.is_admin: {getattr(request, 'is_admin', 'Not Set')}")
    logger.info(f"[DASHBOARD] request.is_hanagwahak: {getattr(request, 'is_hanagwahak', 'Not Set')}")
    logger.info(f"[DASHBOARD] request.user_company_name: {getattr(request, 'user_company_name', 'Not Set')}")
    
    # URL 파라미터로 특정 사용자 필터링
    user_filter = request.GET.get('user')
    selected_user = None
    
    if user_filter and user_profile.can_view_all_users():
        try:
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

    # 납품 금액 통계 (현재 연도만) - History와 Schedule의 DeliveryItem 모두 포함
    # 1. History에서 납품 금액
    history_delivery_stats = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False
    ).aggregate(
        total_amount=Sum('delivery_amount'),
        delivery_count=Count('id')
    )
    
    # 2. Schedule에 연결된 DeliveryItem에서 납품 금액
    schedule_delivery_stats = DeliveryItem.objects.filter(
        schedule__user=target_user if not (user_profile.is_admin() and not selected_user) else None,
        schedule__created_at__year=current_year,
        schedule__activity_type='delivery'
    ).aggregate(
        total_amount=Sum('total_price'),
        delivery_count=Count('schedule', distinct=True)
    )
    
    # Admin이고 특정 사용자가 선택되지 않은 경우 모든 사용자의 데이터
    if user_profile.is_admin() and not selected_user:
        schedule_delivery_stats = DeliveryItem.objects.filter(
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).aggregate(
            total_amount=Sum('total_price'),
            delivery_count=Count('schedule', distinct=True)
        )
    
    # 총합 계산
    history_amount = history_delivery_stats['total_amount'] or 0
    schedule_amount = schedule_delivery_stats['total_amount'] or 0
    total_delivery_amount = history_amount + schedule_amount
    
    # 중복 제거된 납품 횟수 계산
    # History에서 delivery_schedule인 것들 중 일정과 연결된 것들
    history_with_schedule = histories_current_year.filter(
        action_type='delivery_schedule',
        schedule__isnull=False
    ).values_list('schedule_id', flat=True).distinct()
    
    # History에서 delivery_schedule인 것들 중 일정과 연결되지 않은 것들
    history_without_schedule = histories_current_year.filter(
        action_type='delivery_schedule',
        schedule__isnull=True
    ).count()
    
    # Schedule에 DeliveryItem이 있는 일정들
    schedules_with_delivery = DeliveryItem.objects.filter(
        schedule__user=target_user if not (user_profile.is_admin() and not selected_user) else None,
        schedule__created_at__year=current_year,
        schedule__activity_type='delivery'
    ).values_list('schedule_id', flat=True).distinct()
    
    # Admin이고 특정 사용자가 선택되지 않은 경우 모든 사용자의 데이터
    if user_profile.is_admin() and not selected_user:
        schedules_with_delivery = DeliveryItem.objects.filter(
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).values_list('schedule_id', flat=True).distinct()
    
    # 고유한 일정 ID들의 합집합 + 일정이 없는 History 납품
    unique_schedule_ids = set(history_with_schedule) | set(schedules_with_delivery)
    delivery_count = len(unique_schedule_ids) + history_without_schedule
    # 활동 유형별 통계 (현재 연도만, 메모 제외)
    if getattr(request, 'is_admin', False) or getattr(request, 'is_hanagwahak', False):
        logger.info(f"[DASHBOARD] 서비스 접근 권한 있음 - is_admin: {getattr(request, 'is_admin', False)}, is_hanagwahak: {getattr(request, 'is_hanagwahak', False)}")
        activity_stats = histories_current_year.exclude(action_type='memo').values('action_type').annotate(
            count=Count('id')
        ).order_by('action_type')
        
        # 활동 유형별 상세 로그
        for stat in activity_stats:
            logger.info(f"[DASHBOARD] 활동 유형: {stat['action_type']}, 개수: {stat['count']}")
    else:
        logger.info(f"[DASHBOARD] 서비스 접근 권한 없음 - 서비스 제외")
        # Admin이 아니고 하나과학이 아닌 경우 서비스 항목도 제외
        activity_stats = histories_current_year.exclude(action_type__in=['memo', 'service']).values('action_type').annotate(
            count=Count('id')
        ).order_by('action_type')
        
        # 활동 유형별 상세 로그
        for stat in activity_stats:
            logger.info(f"[DASHBOARD] 활동 유형: {stat['action_type']}, 개수: {stat['count']}")
    
    # 서비스 통계 추가 (완료된 서비스만 카운팅) - Admin이나 하나과학만
    if getattr(request, 'is_admin', False) or getattr(request, 'is_hanagwahak', False):
        service_count = histories_current_year.filter(action_type='service', service_status='completed').count()
        logger.info(f"[DASHBOARD] 올해 완료된 서비스 개수: {service_count}")
        
        # 이번 달 서비스 수 (완료된 것만)
        this_month_service_count = histories.filter(
            action_type='service',
            service_status='completed',
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        logger.info(f"[DASHBOARD] 이번 달 완료된 서비스 개수: {this_month_service_count}")
        
        # 전체 서비스 히스토리 개수도 확인
        total_service_count = histories_current_year.filter(action_type='service').count()
        logger.info(f"[DASHBOARD] 올해 전체 서비스 히스토리 개수: {total_service_count}")
        
        # 서비스 상태별 개수
        service_status_stats = histories_current_year.filter(action_type='service').values('service_status').annotate(
            count=Count('id')
        )
        for status_stat in service_status_stats:
            logger.info(f"[DASHBOARD] 서비스 상태 '{status_stat['service_status']}': {status_stat['count']}개")
            
    else:
        service_count = 0
        this_month_service_count = 0
        logger.info(f"[DASHBOARD] 서비스 접근 권한 없음 - service_count = 0")
      # 최근 활동 (현재 연도, 최근 5개, 메모 제외)
    recent_activities_queryset = histories_current_year.exclude(action_type='memo')
    if not getattr(request, 'is_admin', False) and not getattr(request, 'is_hanagwahak', False):
        # Admin이 아니고 하나과학이 아닌 경우 서비스도 제외
        recent_activities_queryset = recent_activities_queryset.exclude(action_type='service')
        logger.info(f"[DASHBOARD] 최근 활동에서 서비스 제외됨")
    else:
        logger.info(f"[DASHBOARD] 최근 활동에 서비스 포함됨")
        
    recent_activities = recent_activities_queryset.order_by('-created_at')[:5]
    
    # 최근 활동 상세 로깅
    for activity in recent_activities:
        logger.info(f"[DASHBOARD] 최근 활동: {activity.action_type} - {activity.get_action_type_display()}")
    
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

    # 월별 서비스 데이터 (최근 6개월, 완료된 서비스만) - Admin이나 하나과학만
    if getattr(request, 'is_admin', False) or getattr(request, 'is_hanagwahak', False):
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
    else:
        monthly_service_data = []
        monthly_service_labels = []

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
        'today_schedules': today_schedules,        
        'recent_customers': recent_customers,
        'monthly_revenue': monthly_revenue,
        'monthly_meetings': monthly_meetings,
        'monthly_services': monthly_services,
        'service_count': service_count,
        'this_month_service_count': this_month_service_count,
        'conversion_rate': conversion_rate,
        'avg_deal_size': avg_deal_size,
        # 템플릿에서 직접 사용할 수 있도록 추가
        'is_hanagwahak': getattr(request, 'is_hanagwahak', False),
        'is_admin': getattr(request, 'is_admin', False),
        'user_company_name': getattr(request, 'user_company_name', None),
        'monthly_revenue_data': monthly_revenue_data,
        'monthly_revenue_labels': monthly_revenue_labels,        'customer_revenue_labels': customer_labels,
        'customer_revenue_data': customer_amounts,
        'monthly_service_data': monthly_service_data,
        'monthly_service_labels': monthly_service_labels,
    }
    
    # 최종 컨텍스트 로깅
    logger.info(f"[DASHBOARD] 최종 컨텍스트 전달:")
    logger.info(f"[DASHBOARD] - is_hanagwahak (context): {context['is_hanagwahak']}")
    logger.info(f"[DASHBOARD] - is_admin (context): {context['is_admin']}")
    logger.info(f"[DASHBOARD] - user_company_name (context): {context['user_company_name']}")
    logger.info(f"[DASHBOARD] - service_count: {context['service_count']}")
    logger.info(f"[DASHBOARD] - this_month_service_count: {context['this_month_service_count']}")
    
    # monthly_services 타입 확인 후 로깅
    monthly_services = context.get('monthly_services')
    if hasattr(monthly_services, '__len__'):
        logger.info(f"[DASHBOARD] - monthly_services 데이터 개수: {len(monthly_services)}")
    else:
        logger.info(f"[DASHBOARD] - monthly_services 데이터: {monthly_services} (타입: {type(monthly_services)})")
        
    logger.info(f"[DASHBOARD] - monthly_service_data: {context['monthly_service_data']}")
    logger.info(f"[DASHBOARD] - monthly_service_labels: {context['monthly_service_labels']}")
    logger.info(f"[DASHBOARD] - activity_stats 개수: {len(list(context['activity_stats']))}")
    
    # activity_stats에 서비스가 포함되어 있는지 확인
    activity_types = [stat['action_type'] for stat in context['activity_stats']]
    logger.info(f"[DASHBOARD] - 활동 유형 목록: {activity_types}")
    if 'service' in activity_types:
        service_stat = next(stat for stat in context['activity_stats'] if stat['action_type'] == 'service')
        logger.info(f"[DASHBOARD] - 서비스 통계: {service_stat}")
    else:
        logger.info(f"[DASHBOARD] - 활동 통계에 서비스 없음")
    
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
        users = User.objects.filter(schedule__isnull=False).distinct()
    else:
        users = [request.user]
    
    # 선택된 사용자 정보
    selected_user = None
    if user_filter:
        try:
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
    related_histories_all = History.objects.filter(schedule=schedule).order_by('-created_at')
    related_histories = related_histories_all[:10]  # 표시용 최신 10개
    
    # 납품 품목 조회 (DeliveryItem 모델)
    delivery_items = DeliveryItem.objects.filter(schedule=schedule)
    
    # 디버깅: 납품 품목 정보 출력
    print(f"Schedule ID: {schedule.id}")
    print(f"DeliveryItem count: {delivery_items.count()}")
    for item in delivery_items:
        print(f"  - {item.item_name}: {item.quantity} x {item.unit_price}")
    
    # 관련 히스토리에서 납품 품목 텍스트 찾기 (대체 방법)
    delivery_text = None
    delivery_histories = related_histories_all.filter(action_type='delivery_schedule', delivery_items__isnull=False)
    if delivery_histories.exists():
        raw_delivery_text = delivery_histories.first().delivery_items
        # \n을 실제 줄바꿈으로 변환
        if raw_delivery_text:
            delivery_text = raw_delivery_text.replace('\\n', '\n')
            print(f"Raw delivery text: {repr(raw_delivery_text)}")
            print(f"Processed delivery text: {repr(delivery_text)}")
        print(f"Found delivery text from history: {delivery_text}")
    
    # 이전 페이지 정보 (캘린더에서 온 경우)
    from_page = request.GET.get('from', 'list')  # 기본값은 'list'
    
    context = {
        'schedule': schedule,
        'related_histories': related_histories,
        'delivery_items': delivery_items,
        'delivery_text': delivery_text,  # 히스토리에서 가져온 납품 품목 텍스트
        'from_page': from_page,
        'page_title': f'일정 상세 - {schedule.followup.customer_name}'
    }
    return render(request, 'reporting/schedule_detail.html', context)

@login_required
def schedule_create_view(request):
    """일정 생성 (캘린더에서 선택된 날짜 지원)"""
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user, request=request)
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
        
        form = ScheduleForm(user=request.user, request=request, initial=initial_data)
    
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
        form = ScheduleForm(request.POST, instance=schedule, user=request.user, request=request)
        if form.is_valid():
            updated_schedule = form.save()
            
            # 납품 품목 데이터가 있으면 저장
            has_delivery_items = any(key.startswith('delivery_items[') for key in request.POST.keys())
            if has_delivery_items:
                save_delivery_items(request, updated_schedule)
            
            messages.success(request, '일정이 성공적으로 수정되었습니다.')
            return redirect('reporting:schedule_detail', pk=schedule.pk)
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        form = ScheduleForm(instance=schedule, user=request.user, request=request)
    
    # DeliveryItem 모델에서 납품 품목 데이터 가져오기 (우선순위 1)
    delivery_text = None
    delivery_amount = 0
    
    # 1차: DeliveryItem 모델에서 최신 데이터 확인
    delivery_items = schedule.delivery_items_set.all().order_by('id')
    print(f"Found {delivery_items.count()} delivery items for schedule {schedule.pk}")
    
    if delivery_items.exists():
        delivery_text_parts = []
        total_amount = 0
        
        for item in delivery_items:
            print(f"  - {item.item_name}: {item.quantity} x {item.unit_price}")
            # VAT 포함 총액 계산 (DeliveryItem의 save()에서 자동 계산됨)
            item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
            total_amount += item_total
            
            # 텍스트 형태로 변환
            text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
            delivery_text_parts.append(text_part)
        
        delivery_text = '\n'.join(delivery_text_parts)
        delivery_amount = int(total_amount)
        
        print(f"DeliveryItem text: {delivery_text}")
        print(f"DeliveryItem amount: {delivery_amount}")
    
    # 2차: DeliveryItem이 없으면 History에서 fallback
    if not delivery_text:
        related_histories = History.objects.filter(schedule=schedule, action_type='delivery_schedule').order_by('-created_at')
        print(f"No DeliveryItems found, checking {related_histories.count()} histories")
        
        if related_histories.exists():
            latest_delivery = related_histories.first()
            if latest_delivery.delivery_items:
                raw_text = latest_delivery.delivery_items
                print(f"Raw delivery text: '{raw_text}'")
                delivery_text = raw_text.replace('\\n', '\n')
                print(f"Processed delivery text: '{delivery_text}'")
                print(f"Found delivery text from history: {delivery_text}")
            if latest_delivery.delivery_amount:
                delivery_amount = latest_delivery.delivery_amount
    
    context = {
        'form': form,
        'schedule': schedule,
        'delivery_text': delivery_text,
        'delivery_amount': delivery_amount,
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
    logger.info(f"=== Schedule 납품 품목 업데이트 시작 (ID: {pk}) ===")
    logger.info(f"요청 메소드: {request.method}")
    logger.info(f"사용자: {request.user.username}")
    logger.info(f"Content-Type: {request.content_type}")
    
    schedule = get_object_or_404(Schedule, pk=pk)
    logger.info(f"Schedule 정보: {schedule} (ID: {schedule.pk})")
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능
    if not can_modify_user_data(request.user, schedule.user):
        logger.warning(f"권한 없음: {request.user.username}이 {schedule.user.username}의 스케줄을 수정하려고 시도")
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:schedule_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            logger.info(f"Schedule {pk}의 납품 품목 업데이트 시작")
            
            # 납품 품목 저장
            created_count = save_delivery_items(request, schedule)
            logger.info(f"Schedule {pk}에 {created_count}개 납품 품목 저장됨")
            
            # 관련된 History들의 delivery_items 텍스트도 업데이트
            related_histories = schedule.histories.filter(action_type='delivery_schedule')
            logger.info(f"연관된 History 개수: {related_histories.count()}")
            
            if related_histories.exists():
                # 새로 저장된 DeliveryItem들을 텍스트로 변환
                delivery_items = schedule.delivery_items_set.all()
                logger.info(f"Schedule에 저장된 DeliveryItem 개수: {delivery_items.count()}")
                
                if delivery_items.exists():
                    delivery_lines = []
                    for item in delivery_items:
                        if item.unit_price:
                            # 부가세 포함 총액 계산 (단가 * 수량 * 1.1)
                            total_amount = int(float(item.unit_price) * item.quantity * 1.1)
                            delivery_lines.append(f"{item.item_name}: {item.quantity}개 ({total_amount:,}원)")
                        else:
                            delivery_lines.append(f"{item.item_name}: {item.quantity}개")
                    delivery_text = '\n'.join(delivery_lines)
                    logger.info(f"생성된 delivery_text: {delivery_text}")
                    
                    # 관련 History들의 delivery_items 필드 업데이트
                    for history in related_histories:
                        history.delivery_items = delivery_text
                        history.save(update_fields=['delivery_items'])
                        logger.info(f"History {history.pk}의 delivery_items 업데이트 완료")
            
            messages.success(request, '납품 품목이 성공적으로 업데이트되었습니다.')
        except Exception as e:
            logger.error(f'납품 품목 업데이트 중 오류: {str(e)}', exc_info=True)
            messages.error(request, f'납품 품목 업데이트 중 오류가 발생했습니다: {str(e)}')
        
        return redirect('reporting:schedule_detail', pk=pk)
    
    # GET 요청은 허용하지 않음
    logger.warning(f"GET 요청으로 schedule_update_delivery_items 호출됨 (Schedule ID: {pk})")
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
            schedule_item = {
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
                'priority': schedule.followup.priority,  # 고객 우선순위 추가
            }
            
            # 납품 일정인 경우 납품 품목 정보 추가
            if schedule.activity_type == 'delivery':
                delivery_items_text = ''
                delivery_amount = 0
                
                # Schedule에 연결된 History에서 납품 품목 찾기
                delivery_history = schedule.histories.filter(action_type='delivery_schedule').first()
                if delivery_history and delivery_history.delivery_items:
                    delivery_items_text = delivery_history.delivery_items.strip()
                    delivery_amount = delivery_history.delivery_amount or 0
                else:
                    # History가 없으면 DeliveryItem 모델에서 데이터 가져오기
                    delivery_items = schedule.delivery_items_set.all().order_by('id')
                    if delivery_items.exists():
                        delivery_text_parts = []
                        total_amount = 0
                        
                        for item in delivery_items:
                            item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                            total_amount += item_total
                            text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                            delivery_text_parts.append(text_part)
                        
                        delivery_items_text = '\n'.join(delivery_text_parts)
                        delivery_amount = int(total_amount)
                
                schedule_item.update({
                    'delivery_items': delivery_items_text,
                    'delivery_amount': delivery_amount,
                })
            
            schedule_data.append(schedule_item)
        
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
    
    # 권한에 따른 데이터 필터링 (매니저 메모 제외)
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        histories = History.objects.filter(user__in=accessible_users, parent_history__isnull=True)  # 매니저 메모 제외
    else:
        # Salesman은 자신의 데이터만 조회
        histories = History.objects.filter(user=request.user, parent_history__isnull=True)  # 매니저 메모 제외
    
    # 관련 객체들을 미리 로드하여 성능 최적화 (답글 메모도 포함)
    histories = histories.select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'schedule'
    ).prefetch_related('reply_memos__created_by')  # 답글 메모들을 미리 로드
    
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
            # 매니저 메모를 부모 히스토리에 연결된 자식 히스토리로 생성
            memo_history = History.objects.create(
                followup=history.followup,
                user=history.user,  # 원래 실무자를 유지
                parent_history=history,  # 부모 히스토리 설정
                action_type='memo',
                content=manager_memo,  # 매니저 메모 표시 제거 (parent_history로 구분)
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
        form = HistoryForm(request.POST, request.FILES, user=request.user, request=request)
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
        form = HistoryForm(user=request.user, request=request)
    
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
        form = HistoryForm(request.POST, request.FILES, instance=history, user=request.user, request=request)
        if form.is_valid():
            form.save()
            
            # 납품 품목 저장
            save_delivery_items(request, history)
            
            # History에 연결된 Schedule이 있다면 Schedule의 DeliveryItem도 동기화
            if history.schedule:
                # Schedule의 기존 DeliveryItem들 삭제
                history.schedule.delivery_items_set.all().delete()
                
                # History의 새로운 DeliveryItem들을 Schedule에도 복사
                history_delivery_items = history.delivery_items_set.all()
                for history_item in history_delivery_items:
                    DeliveryItem.objects.create(
                        schedule=history.schedule,
                        item_name=history_item.item_name,
                        quantity=history_item.quantity,
                        unit=history_item.unit,
                        unit_price=history_item.unit_price
                    )
            
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
        form = HistoryForm(instance=history, user=request.user, request=request)
    
    # 관련 스케줄의 납품 품목 정보 가져오기
    schedule_delivery_items = []
    delivery_text = ""
    delivery_amount = 0
    
    if history.schedule:
        # 스케줄에 연결된 납품 품목들 가져오기
        schedule_delivery_items = history.schedule.delivery_items_set.all()
        
        # 납품 품목들을 텍스트 형태로 변환하고 총액 계산
        if schedule_delivery_items:
            delivery_lines = []
            total_delivery_amount = 0
            for item in schedule_delivery_items:
                if item.unit_price:
                    # 부가세 포함 총액 계산 (단가 * 수량 * 1.1)
                    from decimal import Decimal
                    item_total_amount = int(float(item.unit_price) * item.quantity * 1.1)
                    total_delivery_amount += item_total_amount
                    delivery_lines.append(f"{item.item_name}: {item.quantity}개 ({item_total_amount:,}원)")
                else:
                    delivery_lines.append(f"{item.item_name}: {item.quantity}개")
            delivery_text = '\n'.join(delivery_lines)
            delivery_amount = total_delivery_amount
    
    context = {
        'form': form,
        'history': history,
        'existing_delivery_items': history.delivery_items_set.all(),
        'schedule_delivery_items': schedule_delivery_items,
        'delivery_text': delivery_text,
        'delivery_amount': delivery_amount,
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
                # DeliveryItem 모델에서 최신 납품 품목 데이터 가져오기
                delivery_items_text = ''
                delivery_amount = history.delivery_amount or 0
                
                # 1차: History에 연결된 DeliveryItem 확인
                delivery_items = history.delivery_items_set.all().order_by('id')
                if delivery_items.exists():
                    delivery_text_parts = []
                    total_amount = 0
                    
                    for item in delivery_items:
                        item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                        total_amount += item_total
                        text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                        delivery_text_parts.append(text_part)
                    
                    delivery_items_text = '\n'.join(delivery_text_parts)
                    delivery_amount = int(total_amount)
                
                # 2차: History의 schedule에 연결된 DeliveryItem 확인 (fallback)
                elif history.schedule:
                    schedule_delivery_items = history.schedule.delivery_items_set.all().order_by('id')
                    if schedule_delivery_items.exists():
                        delivery_text_parts = []
                        total_amount = 0
                        
                        for item in schedule_delivery_items:
                            item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                            total_amount += item_total
                            text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                            delivery_text_parts.append(text_part)
                        
                        delivery_items_text = '\n'.join(delivery_text_parts)
                        delivery_amount = int(total_amount)
                
                # 3차: 기존 텍스트 필드 사용 (최종 fallback)
                if not delivery_items_text and history.delivery_items:
                    delivery_items_text = history.delivery_items
                
                history_data.update({
                    'delivery_amount': delivery_amount,
                    'delivery_items': delivery_items_text,
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
    company = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '회사명을 입력하세요 (예: 하나과학)'}),
        label='소속 회사',
        help_text='사용자가 속할 회사명을 직접 입력하세요'
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
    company = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '회사명을 입력하세요 (예: 하나과학)'}),
        label='소속 회사',
        help_text='사용자가 속할 회사명을 직접 입력하세요'
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
    users = User.objects.select_related('userprofile').all().order_by('username')
    
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
    
    # 페이지네이션 (정렬된 쿼리셋 사용으로 경고 해결)
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
            
            # 회사 정보 가져오기 또는 생성
            company_name = form.cleaned_data['company']
            user_company, created = UserCompany.objects.get_or_create(name=company_name)
            
            # 사용자 프로필 생성
            UserProfile.objects.create(
                user=user,
                company=user_company,  # UserCompany 객체 사용
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
            # 회사 정보 가져오기 또는 생성
            company_name = form.cleaned_data['company']
            user_company, created = UserCompany.objects.get_or_create(name=company_name)
            
            # 사용자 정보 수정
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            
            # 비밀번호 변경
            if form.cleaned_data['change_password'] and form.cleaned_data['password1']:
                user.set_password(form.cleaned_data['password1'])
            
            user.save()
            
            # 권한 및 회사 수정
            user_profile.company = user_company  # 회사 정보 업데이트
            user_profile.role = form.cleaned_data['role']
            user_profile.can_download_excel = form.cleaned_data['can_download_excel']
            user_profile.save()
            
            messages.success(request, f'사용자 "{user.username}"의 정보가 성공적으로 수정되었습니다.')
            return redirect('reporting:user_list')
    else:
        # 기존 데이터로 폼 초기화
        form = UserEditForm(initial={
            'username': user.username,
            'company': user_profile.company.name if user_profile.company else '',
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
    """Manager 전용 대시보드 - 같은 회사 Salesman의 현황을 볼 수 있음"""
    # 선택된 salesman (기본값: 첫 번째 salesman)
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 접근 가능한 Salesman 목록 (get_accessible_users에서 이미 회사별 필터링됨)
    accessible_users = get_accessible_users(request.user)
    salesman_users = accessible_users.filter(userprofile__role='salesman')
    
    # 추가 보안 체크: 매니저의 회사 정보가 있는지 확인
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.company:
        context = {
            'error_message': '회사 정보가 없어 접근할 수 없습니다.',
            'page_title': 'Manager 대시보드'
        }
        return render(request, 'reporting/manager_dashboard.html', context)
    
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
    
    # 보안 로깅: 매니저가 어떤 데이터에 접근하는지 기록
    user_company_name = request.user.userprofile.company.name if request.user.userprofile.company else "미정"
    accessible_company_names = [user.userprofile.company.name if user.userprofile.company else "미정" 
                               for user in salesman_users]
    logger.info(f"매니저 {request.user.username} ({user_company_name})가 접근하는 영업사원들: {accessible_company_names}")
    
    # 기본 쿼리셋 (선택된 사용자로 필터링 또는 전체보기)
    # 추가 보안: salesman_users가 이미 회사별로 필터링되었지만 다시 한 번 체크
    if view_all:
        # 전체보기인 경우 같은 회사 Salesman의 데이터만
        followups = FollowUp.objects.filter(user__in=salesman_users)
        schedules = Schedule.objects.filter(user__in=salesman_users)
        histories = History.objects.filter(user__in=salesman_users, created_at__year=current_year)
        
        # 추가 보안 체크: 실제로 가져온 데이터가 매니저와 같은 회사인지 확인
        manager_company = request.user.userprofile.company
        followup_companies = set(followups.values_list('user__userprofile__company', flat=True))
        if followup_companies and manager_company.id not in followup_companies:
            logger.warning(f"보안 경고: 매니저 {request.user.username}가 다른 회사 데이터에 접근 시도")
            
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
    
    # 납품 금액 계산 - History와 Schedule의 DeliveryItem 모두 포함
    # 1. History에서 납품 금액
    history_delivery_amount = delivery_histories.aggregate(
        total=Sum('delivery_amount')
    )['total'] or 0
    
    # 2. Schedule에 연결된 DeliveryItem에서 납품 금액
    if view_all:
        # 전체보기인 경우 모든 Salesman의 Schedule DeliveryItem
        schedule_delivery_amount = DeliveryItem.objects.filter(
            schedule__user__in=salesman_users,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    else:
        # 특정 사용자의 Schedule DeliveryItem
        schedule_delivery_amount = DeliveryItem.objects.filter(
            schedule__user=selected_user,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # 총 납품 금액
    total_delivery_amount = history_delivery_amount + schedule_delivery_amount
    
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
        
        # 월별 납품 금액 계산 (History + Schedule DeliveryItem)
        history_month_amount = month_deliveries.aggregate(total=Sum('delivery_amount'))['total'] or 0
        
        # Schedule에서 해당 월의 DeliveryItem 금액
        if view_all:
            schedule_month_amount = DeliveryItem.objects.filter(
                schedule__user__in=salesman_users,
                schedule__created_at__month=month,
                schedule__created_at__year=current_year,
                schedule__activity_type='delivery'
            ).aggregate(total=Sum('total_price'))['total'] or 0
        else:
            schedule_month_amount = DeliveryItem.objects.filter(
                schedule__user=selected_user,
                schedule__created_at__month=month,
                schedule__created_at__year=current_year,
                schedule__activity_type='delivery'
            ).aggregate(total=Sum('total_price'))['total'] or 0
        
        total_month_amount = history_month_amount + schedule_month_amount
        
        monthly_data.append({
            'month': f'{month}월',
            'meetings': month_meetings.count(),
            'deliveries': month_deliveries.count(),
            'services': month_services.count(),
            'amount': total_month_amount
        })
        
        monthly_delivery.append(total_month_amount)
    
    # 고객별 납품 현황 (현재 연도) - History와 Schedule DeliveryItem 모두 포함
    customer_delivery = {}
    
    # 1. History에서 고객별 납품 금액
    for history in delivery_histories:
        customer = history.followup.customer_name or history.followup.company or "고객명 미정" if history.followup else "일반 메모"
        if customer in customer_delivery:
            customer_delivery[customer] += history.delivery_amount or 0
        else:
            customer_delivery[customer] = history.delivery_amount or 0
    
    # 2. Schedule DeliveryItem에서 고객별 납품 금액
    if view_all:
        schedule_deliveries = DeliveryItem.objects.filter(
            schedule__user__in=salesman_users,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).select_related('schedule__followup')
    else:
        schedule_deliveries = DeliveryItem.objects.filter(
            schedule__user=selected_user,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).select_related('schedule__followup')
    
    for delivery_item in schedule_deliveries:
        if delivery_item.schedule and delivery_item.schedule.followup:
            customer = (delivery_item.schedule.followup.customer_name or 
                       delivery_item.schedule.followup.company or "고객명 미정")
            if customer in customer_delivery:
                customer_delivery[customer] += delivery_item.total_price or 0
            else:
                customer_delivery[customer] = delivery_item.total_price or 0
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
    """일정에서 히스토리 생성 또는 기존 히스토리로 이동"""
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
        
        # 스케줄의 activity_type에 따른 action_type 매핑
        action_type_mapping = {
            'customer_meeting': 'customer_meeting',
            'delivery': 'delivery_schedule', 
            'service': 'service_visit',
        }
        expected_action_type = action_type_mapping.get(schedule.activity_type, 'customer_meeting')
        
        # AJAX 요청으로 기존 히스토리 확인하는 경우
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
            existing_history = History.objects.filter(
                schedule=schedule,
                action_type=expected_action_type
            ).first()
            
            if existing_history:
                return JsonResponse({
                    'success': True,
                    'has_existing': True,
                    'message': f'이미 "{schedule.followup.customer_name}" 일정에 대한 활동 기록이 존재합니다.',
                    'history_id': existing_history.pk,
                    'history_url': f'/reporting/histories/{existing_history.pk}/',
                    'customer_name': schedule.followup.customer_name,
                    'visit_date': schedule.visit_date.strftime('%Y년 %m월 %d일')
                })
            else:
                return JsonResponse({
                    'success': True,
                    'has_existing': False,
                    'message': '새로운 활동 기록을 생성할 수 있습니다.',
                    'create_url': f'/reporting/histories/create-from-schedule/{schedule.pk}/',
                    'customer_name': schedule.followup.customer_name,
                    'visit_date': schedule.visit_date.strftime('%Y년 %m월 %d일')
                })
        
        # 기존 히스토리가 있는지 확인 (일반 GET 요청일 때만)
        if request.method == 'GET':
            existing_history = History.objects.filter(
                schedule=schedule,
                action_type=expected_action_type
            ).first()
            
            if existing_history:
                messages.info(request, f'이미 "{schedule.followup.customer_name}" 일정에 대한 활동 기록이 존재합니다. 기존 기록으로 이동합니다.')
                return redirect('reporting:history_detail', pk=existing_history.pk)
        
        
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
            
            form = HistoryForm(post_data, user=request.user, request=request)
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
            # 스케줄의 활동 유형에 따라 히스토리 action_type 설정
            action_type_mapping = {
                'customer_meeting': 'customer_meeting',
                'delivery': 'delivery_schedule', 
                'service': 'service_visit',
            }
            initial_action_type = action_type_mapping.get(schedule.activity_type, 'customer_meeting')
            
            initial_data = {
                'followup': schedule.followup.id,
                'schedule': schedule.id,
                'action_type': initial_action_type,  # 스케줄의 activity_type에 맞춰 설정
                'delivery_date': schedule.visit_date,  # 납품 날짜를 일정 날짜로 설정
                'meeting_date': schedule.visit_date,  # 미팅 날짜를 일정 날짜로 설정
            }
            form = HistoryForm(user=request.user, request=request, initial=initial_data)
            
            # 팔로우업과 일정 필드를 해당 일정으로 고정
            form.fields['followup'].queryset = FollowUp.objects.filter(id=schedule.followup.id)
            form.fields['schedule'].queryset = Schedule.objects.filter(id=schedule.id)
            
            # 필드를 읽기 전용으로 설정 (disabled 대신 시각적으로 비활성화)
            form.fields['followup'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
            form.fields['schedule'].widget.attrs.update({'readonly': True, 'style': 'pointer-events: none; background-color: #e9ecef;'})
        
        # 스케줄의 납품 품목 정보 가져오기
        delivery_text = None
        delivery_amount = 0
        
        if schedule.activity_type == 'delivery':
            # 1차: DeliveryItem 모델에서 최신 데이터 확인
            delivery_items = schedule.delivery_items_set.all().order_by('id')
            
            if delivery_items.exists():
                delivery_text_parts = []
                total_amount = 0
                
                for item in delivery_items:
                    # VAT 포함 총액 계산
                    item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                    total_amount += item_total
                    
                    # 텍스트 형태로 변환
                    text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                    delivery_text_parts.append(text_part)
                
                delivery_text = '\n'.join(delivery_text_parts)
                delivery_amount = int(total_amount)
            
            # 2차: DeliveryItem이 없으면 History에서 fallback
            if not delivery_text:
                related_histories = History.objects.filter(schedule=schedule, action_type='delivery_schedule').order_by('-created_at')
                
                if related_histories.exists():
                    latest_delivery = related_histories.first()
                    if latest_delivery.delivery_items:
                        delivery_text = latest_delivery.delivery_items.replace('\\n', '\n')
                    if latest_delivery.delivery_amount:
                        delivery_amount = latest_delivery.delivery_amount
        
        context = {
            'form': form,
            'schedule': schedule,
            'delivery_text': delivery_text,
            'delivery_amount': delivery_amount,
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
        form = HistoryForm(user=request.user, request=request, initial=initial_data)
        
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
            user=schedule.user,  # 일정의 원래 담당자를 유지
            action_type='memo',
            content=f"[매니저 메모 - {request.user.username}] {memo_content}",  # 매니저 메모 표시 추가
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
    import logging
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '').strip()
    logger.info(f"[COMPANY_AUTOCOMPLETE] 사용자: {request.user.username}, 검색어: '{query}'")
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Admin 사용자는 모든 업체 검색 가능
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        companies = Company.objects.filter(name__icontains=query).order_by('name')[:10]
        logger.info(f"[COMPANY_AUTOCOMPLETE] Admin 사용자 - 전체 업체에서 검색: {companies.count()}개 결과")
    else:
        # ======= 임시 수정: 모든 사용자가 모든 업체를 검색할 수 있도록 변경 =======
        # 원래: 사용자의 회사별로 데이터 필터링
        # 수정: 모든 업체를 검색할 수 있도록 변경 (company_list_view와 동일)
        companies = Company.objects.filter(name__icontains=query).order_by('name')[:10]
        logger.info(f"[COMPANY_AUTOCOMPLETE] 일반 사용자 - 전체 업체에서 검색: {companies.count()}개 결과 (임시 수정)")
        
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        logger.info(f"[COMPANY_AUTOCOMPLETE] user_company (middleware): {user_company}")
        logger.info(f"[COMPANY_AUTOCOMPLETE] user_profile.company: {user_profile.company if user_profile else None}")
        
        # ======= 원래 로직 (주석 처리됨) =======
        # if user_company:
        #     # 미들웨어에서 설정한 user_company 사용
        #     same_company_users = User.objects.filter(userprofile__company=user_company)
        #     logger.info(f"[COMPANY_AUTOCOMPLETE] 같은 회사 사용자 수: {same_company_users.count()}")
        #     
        #     companies = Company.objects.filter(
        #         name__icontains=query,
        #         created_by__in=same_company_users
        #     ).order_by('name')[:10]
        #     logger.info(f"[COMPANY_AUTOCOMPLETE] 검색 결과: {companies.count()}개")
        #     
        # elif user_profile and user_profile.company:
        #     # 백업: UserProfile에서 직접 가져오기
        #     same_company_users = User.objects.filter(userprofile__company=user_profile.company)
        #     logger.info(f"[COMPANY_AUTOCOMPLETE] 백업 방식 - 같은 회사 사용자 수: {same_company_users.count()}")
        #     
        #     companies = Company.objects.filter(
        #         name__icontains=query,
        #         created_by__in=same_company_users
        #     ).order_by('name')[:10]
        #     logger.info(f"[COMPANY_AUTOCOMPLETE] 백업 방식 검색 결과: {companies.count()}개")
        # else:
        #     companies = Company.objects.none()
        #     logger.warning(f"[COMPANY_AUTOCOMPLETE] 회사 정보 없음 - 빈 결과 반환")
    
    results = []
    for company in companies:
        results.append({
            'id': company.id,
            'text': company.name
        })
        logger.info(f"[COMPANY_AUTOCOMPLETE] 결과 업체: {company.name} (생성자: {company.created_by.username if company.created_by else 'Unknown'})")
    
    logger.info(f"[COMPANY_AUTOCOMPLETE] 최종 반환 결과: {len(results)}개")
    return JsonResponse({'results': results})

@login_required
def department_autocomplete(request):
    """부서/연구실명 자동완성 API"""
    import logging
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '').strip()
    company_id = request.GET.get('company') or request.GET.get('company_id')  # 둘 다 지원
    
    logger.info(f"[DEPT_AUTOCOMPLETE] 사용자: {request.user.username}, 검색어: '{query}', 회사 ID: {company_id}")
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Admin 사용자는 모든 부서 검색 가능
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        departments = Department.objects.filter(name__icontains=query)
        logger.info(f"[DEPT_AUTOCOMPLETE] Admin 사용자 - 전체 부서에서 검색")
    else:
        # ======= 임시 수정: 모든 사용자가 모든 부서를 검색할 수 있도록 변경 =======
        # 원래: 같은 회사 사용자들이 생성한 업체의 부서만 검색
        # 수정: 모든 업체의 부서를 검색할 수 있도록 변경
        departments = Department.objects.filter(name__icontains=query)
        logger.info(f"[DEPT_AUTOCOMPLETE] 일반 사용자 - 전체 부서에서 검색 (임시 수정)")
        
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        logger.info(f"[DEPT_AUTOCOMPLETE] user_company: {user_company}, user_profile.company: {user_profile.company if user_profile else None}")
        
        # ======= 원래 로직 (주석 처리됨) =======
        # if user_company:
        #     same_company_users = User.objects.filter(userprofile__company=user_company)
        #     # 같은 회사 사용자들이 생성한 업체의 부서만 필터링
        #     departments = Department.objects.filter(
        #         name__icontains=query,
        #         company__created_by__in=same_company_users
        #     )
        #     logger.info(f"[DEPT_AUTOCOMPLETE] 같은 회사 사용자들의 업체 부서에서 검색")
        # elif user_profile and user_profile.company:
        #     same_company_users = User.objects.filter(userprofile__company=user_profile.company)
        #     departments = Department.objects.filter(
        #         name__icontains=query,
        #         company__created_by__in=same_company_users
        #     )
        #     logger.info(f"[DEPT_AUTOCOMPLETE] 백업 방식 - 같은 회사 사용자들의 업체 부서에서 검색")
        # else:
        #     departments = Department.objects.none()
        #     logger.warning(f"[DEPT_AUTOCOMPLETE] 회사 정보 없음 - 빈 결과 반환")
    
    # 회사가 선택된 경우 해당 회사의 부서만 필터링
    if company_id:
        departments = departments.filter(company_id=company_id)
        logger.info(f"[DEPT_AUTOCOMPLETE] 특정 회사 {company_id}의 부서로 제한")
    
    departments = departments.select_related('company').order_by('company__name', 'name')[:10]
    logger.info(f"[DEPT_AUTOCOMPLETE] 검색 결과: {departments.count()}개")
    
    results = []
    for dept in departments:
        results.append({
            'id': dept.id,
            'text': f"{dept.company.name} - {dept.name}",
            'company_id': dept.company.id,
            'company_name': dept.company.name,
            'department_name': dept.name
        })
        logger.info(f"[DEPT_AUTOCOMPLETE] 결과 부서: {dept.company.name} - {dept.name}")
    
    return JsonResponse({'results': results})

@login_required
def followup_autocomplete(request):
    """팔로우업 자동완성 API (일정 생성용)"""
    import logging
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # 현재 사용자의 권한에 따른 팔로우업 필터링
    user_profile = get_user_profile(request.user)
    user_company = getattr(request, 'user_company', None)
    is_admin = getattr(request, 'is_admin', False)
    
    logger.info(f"[FOLLOWUP_AUTOCOMPLETE] 사용자: {request.user.username}, 검색어: '{query}', "
                f"사용자_회사: {user_company.name if user_company else 'None'}, "
                f"admin권한: {is_admin}, 전체조회가능: {user_profile.can_view_all_users()}")
    
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user)
        followups = FollowUp.objects.filter(user__in=accessible_users)
        logger.info(f"[FOLLOWUP_AUTOCOMPLETE] 관리자/매니저 - 접근가능 사용자 수: {accessible_users.count()}")
    else:
        followups = FollowUp.objects.filter(user=request.user)
        logger.info(f"[FOLLOWUP_AUTOCOMPLETE] 일반 사용자 - 본인 팔로우업만 조회")
    
    # 검색어로 필터링 (고객명, 업체명, 부서명, 책임자명으로 검색)
    followups = followups.filter(
        Q(customer_name__icontains=query) |
        Q(company__name__icontains=query) |
        Q(department__name__icontains=query) |
        Q(manager__icontains=query)
    ).select_related('company', 'department', 'user').order_by('company__name', 'customer_name')[:15]
    
    logger.info(f"[FOLLOWUP_AUTOCOMPLETE] 검색 결과: {followups.count()}개")
    
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
    
    logger.info(f"[FOLLOWUP_AUTOCOMPLETE] 최종 결과: {len(results)}개")
    
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        name = request.POST.get('name', '').strip()
        logger.info(f"업체 생성 요청: user={request.user.username}, name='{name}'")
        
        if not name:
            logger.warning(f"업체 생성 실패: 빈 이름 (user={request.user.username})")
            return JsonResponse({'error': '업체/학교명을 입력해주세요.'}, status=400)
        
        # 중복 체크 - 같은 회사 내에서만
        user_profile_obj = getattr(request.user, 'userprofile', None)
        if user_profile_obj and user_profile_obj.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
            if Company.objects.filter(name=name, created_by__in=same_company_users).exists():
                logger.warning(f"업체 생성 실패: 중복 이름 '{name}' (user={request.user.username})")
                return JsonResponse({'error': '이미 존재하는 업체/학교명입니다.'}, status=400)
        
        company = Company.objects.create(name=name, created_by=request.user)
        logger.info(f"업체 생성 성공: id={company.id}, name='{company.name}' (user={request.user.username})")
        
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name
            },
            'message': f'"{name}" 업체/학교가 추가되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"업체 생성 오류: {str(e)} (user={request.user.username})", exc_info=True)
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Admin 사용자는 모든 업체를 볼 수 있음
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        # Admin은 모든 업체 조회 가능
        companies = Company.objects.all().annotate(
            department_count=Count('departments', distinct=True),
            followup_count=Count('followup_companies', distinct=True)
        ).order_by('name')
        
        logger.info(f"[COMPANY_LIST] Admin 사용자 {request.user.username}: 전체 {companies.count()}개 업체 조회")
    else:
        # ======= 임시 수정: 모든 사용자가 모든 업체를 볼 수 있도록 변경 =======
        # 원래: 사용자의 회사별로 데이터 필터링 - 같은 회사 사용자가 만든 업체만 조회
        # 수정: 모든 업체를 조회할 수 있도록 변경 (단, salesman 권한은 유지)
        companies = Company.objects.all().annotate(
            department_count=Count('departments', distinct=True),
            followup_count=Count('followup_companies', distinct=True)
        ).order_by('name')
        
        user_company = getattr(request.user, 'userprofile', None)
        logger.info(f"[COMPANY_LIST] 일반 사용자 {request.user.username}: 전체 {companies.count()}개 업체 조회 (임시 수정 - 모든 업체 접근 허용)")
        if user_company and user_company.company:
            logger.info(f"[COMPANY_LIST] 사용자 회사: {user_company.company.name}")
        
        # ======= 원래 로직 (주석 처리됨) =======
        # user_company = getattr(request.user, 'userprofile', None)
        # if user_company and user_company.company:
        #     # 같은 회사 소속 사용자들이 생성한 업체만 조회
        #     same_company_users = User.objects.filter(userprofile__company=user_company.company)
        #     companies = Company.objects.filter(created_by__in=same_company_users).annotate(
        #         department_count=Count('departments', distinct=True),
        #         followup_count=Count('followup_companies', distinct=True)
        #     ).order_by('name')
        #     
        #     logger.info(f"[COMPANY_LIST] 일반 사용자 {request.user.username}: {companies.count()}개 업체 조회 (회사: {user_company.company.name})")
        #     logger.info(f"[COMPANY_LIST] 같은 회사 사용자 수: {same_company_users.count()}명")
        #     logger.info(f"[COMPANY_LIST] 같은 회사 사용자 목록: {list(same_company_users.values_list('username', flat=True))}")
        # else:
        #     # 회사 정보가 없는 경우 빈 쿼리셋
        #     companies = Company.objects.none()
        #     
        #     logger.warning(f"[COMPANY_LIST] 사용자 {request.user.username}: 회사 정보 없음, 빈 목록 반환")
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        companies_before_search = companies.count()
        companies = companies.filter(name__icontains=search_query)
        companies_after_search = companies.count()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[COMPANY_LIST] 검색어: '{search_query}' - 검색 전: {companies_before_search}개, 검색 후: {companies_after_search}개")
        
        # 디버깅을 위해 검색된 업체들의 정보를 로그에 출력
        if companies_after_search > 0:
            company_names = list(companies.values_list('name', flat=True)[:10])  # 최대 10개만
            logger.info(f"[COMPANY_LIST] 검색 결과 업체명: {company_names}")
        
        # "고려대"로 검색하는 경우 특별 디버깅
        if '고려대' in search_query:
            # 전체 Company에서 고려대 관련 업체 찾기
            all_korea_companies = Company.objects.filter(name__icontains='고려대')
            logger.info(f"[COMPANY_LIST] 전체 DB에서 '고려대' 포함 업체: {all_korea_companies.count()}개")
            
            if all_korea_companies.exists():
                for company in all_korea_companies[:5]:  # 최대 5개만 로그
                    created_by_company = 'Unknown'
                    if company.created_by and hasattr(company.created_by, 'userprofile') and company.created_by.userprofile.company:
                        created_by_company = company.created_by.userprofile.company.name
                    logger.info(f"[COMPANY_LIST] 고려대 업체: '{company.name}' (생성자: {company.created_by.username if company.created_by else 'Unknown'}, 생성자 회사: {created_by_company})")
    
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
        else:
            # Admin은 전체 업체를 기준으로, 일반 사용자는 같은 회사 사용자들이 만든 업체를 기준으로 중복 확인
            is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
            
            if is_admin:
                # Admin은 전체 업체 중 중복 확인
                existing_company = Company.objects.filter(name=name).exists()
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[COMPANY_CREATE] Admin 사용자 {request.user.username}: '{name}' 전체 중복 확인 결과 = {existing_company}")
            else:
                # 같은 회사 사용자들이 만든 업체 중에서 중복 확인
                user_company = getattr(request.user, 'userprofile', None)
                if user_company and user_company.company:
                    same_company_users = User.objects.filter(userprofile__company=user_company.company)
                    existing_company = Company.objects.filter(name=name, created_by__in=same_company_users).exists()
                else:
                    existing_company = Company.objects.filter(name=name, created_by=request.user).exists()
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[COMPANY_CREATE] 일반 사용자 {request.user.username}: '{name}' 회사 내 중복 확인 결과 = {existing_company}")
                
            if existing_company:
                messages.error(request, '이미 존재하는 업체/학교명입니다.')
            else:
                Company.objects.create(name=name, created_by=request.user)
                messages.success(request, f'"{name}" 업체/학교가 추가되었습니다.')
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[COMPANY_CREATE] 사용자 {request.user.username}: '{name}' 업체 생성 완료")
                
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
    is_admin = getattr(request, 'is_admin', False) or user_profile.role == 'admin'
    
    import logging
    logger = logging.getLogger(__name__)
    
    if not (is_admin or company.created_by == request.user):
        # Admin이 아닌 경우 같은 회사 사용자가 생성한 업체인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        if user_company and user_company.company:
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if not Company.objects.filter(pk=pk, created_by__in=same_company_users).exists():
                logger.warning(f"[COMPANY_EDIT] 사용자 {request.user.username}: 업체 {pk} 수정 권한 없음 (다른 회사)")
                messages.error(request, '이 업체/학교를 수정할 권한이 없습니다.')
                return redirect('reporting:company_list')
        else:
            logger.warning(f"[COMPANY_EDIT] 사용자 {request.user.username}: 업체 {pk} 수정 권한 없음 (생성자 아님)")
            messages.error(request, '이 업체/학교를 수정할 권한이 없습니다. (생성자 또는 관리자만 가능)')
            return redirect('reporting:company_list')
    
    logger.info(f"[COMPANY_EDIT] 사용자 {request.user.username}: 업체 {pk} 수정 권한 확인됨")
    
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
            
            logger.info(f"[COMPANY_EDIT] 사용자 {request.user.username}: 업체 {pk} '{name}' 수정 완료")
            
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
    is_admin = getattr(request, 'is_admin', False) or user_profile.role == 'admin'
    
    if not (is_admin or company.created_by == request.user):
        # Admin이 아닌 경우 같은 회사 사용자가 생성한 업체인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        if user_company and user_company.company:
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if not Company.objects.filter(pk=pk, created_by__in=same_company_users).exists():
                messages.error(request, '이 업체/학교를 삭제할 권한이 없습니다.')
                return redirect('reporting:company_list')
        else:
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
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[COMPANY_DELETE] 사용자 {request.user.username}: 업체 '{company_name}' 삭제 완료")
        
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
    
    import logging
    logger = logging.getLogger(__name__)
    
    # ======= 임시 수정: 모든 사용자가 모든 업체 상세보기 가능 =======
    # 권한 체크를 제거하고 모든 salesman이 상세보기 가능하도록 변경
    # 단, 수정/삭제 권한은 템플릿이나 별도 함수에서 제어
    
    is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
    user_company = getattr(request.user, 'userprofile', None)
    
    # 수정/삭제 권한 확인을 위한 변수 (템플릿에서 사용)
    can_edit_company = False
    if is_admin:
        can_edit_company = True
        logger.info(f"[COMPANY_DETAIL] Admin 사용자 {request.user.username}: 업체 {pk} 접근 및 수정 권한 있음")
    elif user_company and user_company.company:
        # 같은 회사 사용자가 생성한 업체인지 확인 (수정 권한용)
        same_company_users = User.objects.filter(userprofile__company=user_company.company)
        can_edit_company = Company.objects.filter(pk=pk, created_by__in=same_company_users).exists()
        
        if can_edit_company:
            logger.info(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 업체 {pk} 접근 및 수정 권한 있음 (같은 회사)")
        else:
            logger.info(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 업체 {pk} 접근 가능, 수정 권한 없음 (다른 회사)")
    
    logger.info(f"[COMPANY_DETAIL] 업체 '{company.name}' 상세보기 접근 (생성자: {company.created_by.username if company.created_by else 'Unknown'})")
    
    # ======= 원래 권한 체크 로직 (주석 처리됨) =======
    # # Admin이 아닌 경우 권한 확인
    # if not (getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
    #     # 자신의 회사 소속 사용자들이 생성한 업체인지 확인
    #     user_company = getattr(request.user, 'userprofile', None)
    #     if user_company and user_company.company:
    #         same_company_users = User.objects.filter(userprofile__company=user_company.company)
    #         if not Company.objects.filter(pk=pk, created_by__in=same_company_users).exists():
    #             import logging
    #             logger = logging.getLogger(__name__)
    #             logger.warning(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 업체 {pk} 접근 권한 없음")
    #             messages.error(request, '해당 업체/학교에 접근할 권한이 없습니다.')
    #             return redirect('reporting:company_list')
    #     else:
    #         messages.error(request, '회사 정보가 없어 접근할 수 없습니다.')
    #         return redirect('reporting:company_list')
    # else:
    #     import logging
    #     logger = logging.getLogger(__name__)
    #     logger.info(f"[COMPANY_DETAIL] Admin 사용자 {request.user.username}: 업체 {pk} 접근")
    
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
        'can_edit_company': can_edit_company,  # 수정/삭제 권한 정보
        'page_title': f'{company.name} - 부서/연구실 관리'
    }
    return render(request, 'reporting/company_detail.html', context)

@role_required(['admin', 'salesman'])
def department_create_view(request, company_pk):
    """부서/연구실 생성 (Admin, Salesman 전용)"""
    company = get_object_or_404(Company, pk=company_pk)
    
    import logging
    logger = logging.getLogger(__name__)
    
    # ======= 임시 수정: 모든 salesman이 모든 업체에 부서 추가 가능 =======
    # 권한 체크를 완화하여 모든 사용자가 부서 추가 가능하도록 변경
    # (company_detail_view와 동일한 접근 방식)
    
    is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
    user_company = getattr(request.user, 'userprofile', None)
    
    if is_admin:
        logger.info(f"[DEPT_CREATE] Admin 사용자 {request.user.username}: 업체 {company_pk} '{company.name}'에 부서 추가 권한 있음")
    else:
        logger.info(f"[DEPT_CREATE] 일반 사용자 {request.user.username}: 업체 {company_pk} '{company.name}'에 부서 추가 (모든 업체 허용)")
        if user_company and user_company.company:
            logger.info(f"[DEPT_CREATE] 사용자 회사: {user_company.company.name}")
    
    # ======= 원래 권한 체크 로직 (주석 처리됨) =======
    # # Admin이 아닌 경우 권한 확인
    # if not is_admin:
    #     # 자신의 회사 소속 사용자들이 생성한 업체인지 확인
    #     if user_company and user_company.company:
    #         same_company_users = User.objects.filter(userprofile__company=user_company.company)
    #         if not Company.objects.filter(pk=company_pk, created_by__in=same_company_users).exists():
    #             logger.warning(f"[DEPT_CREATE] 사용자 {request.user.username}: 업체 {company_pk} 부서 추가 권한 없음")
    #             messages.error(request, '해당 업체/학교에 부서를 추가할 권한이 없습니다.')
    #             return redirect('reporting:company_detail', pk=company_pk)
    #     else:
    #         messages.error(request, '회사 정보가 없어 부서를 추가할 수 없습니다.')
    #         return redirect('reporting:company_detail', pk=company_pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, '부서/연구실명을 입력해주세요.')
        elif Department.objects.filter(company=company, name=name).exists():
            messages.error(request, f'{company.name}에 이미 존재하는 부서/연구실명입니다.')
        else:
            Department.objects.create(company=company, name=name, created_by=request.user)
            messages.success(request, f'"{company.name} - {name}" 부서/연구실이 추가되었습니다.')
            
            logger.info(f"[DEPT_CREATE] 사용자 {request.user.username}: 업체 '{company.name}'에 부서 '{name}' 추가 완료")
            
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
    
    # 권한 체크: 관리자이거나 같은 회사 사용자만 수정 가능
    user_profile = get_user_profile(request.user)
    is_admin = getattr(request, 'is_admin', False) or user_profile.role == 'admin'
    
    import logging
    logger = logging.getLogger(__name__)
    
    if not is_admin:
        # Admin이 아닌 경우 같은 회사 사용자인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        has_edit_permission = False
        
        if user_company and user_company.company:
            # 같은 회사 사용자들이 생성한 업체의 부서인지 확인
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if Company.objects.filter(pk=department.company.pk, created_by__in=same_company_users).exists():
                has_edit_permission = True
                logger.info(f"[DEPT_EDIT] 사용자 {request.user.username}: 부서 {pk} 수정 권한 있음 (같은 회사)")
            else:
                logger.warning(f"[DEPT_EDIT] 사용자 {request.user.username}: 부서 {pk} 수정 권한 없음 (다른 회사)")
        
        if not has_edit_permission:
            messages.error(request, '이 부서/연구실을 수정할 권한이 없습니다.')
            return redirect('reporting:company_detail', pk=department.company.pk)
    else:
        logger.info(f"[DEPT_EDIT] Admin 사용자 {request.user.username}: 부서 {pk} 수정 권한 있음")
    
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
    
    # 권한 체크: 관리자이거나 같은 회사 사용자만 삭제 가능
    user_profile = get_user_profile(request.user)
    is_admin = getattr(request, 'is_admin', False) or user_profile.role == 'admin'
    
    import logging
    logger = logging.getLogger(__name__)
    
    if not is_admin:
        # Admin이 아닌 경우 같은 회사 사용자인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        has_delete_permission = False
        
        if user_company and user_company.company:
            # 같은 회사 사용자들이 생성한 업체의 부서인지 확인
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if Company.objects.filter(pk=department.company.pk, created_by__in=same_company_users).exists():
                has_delete_permission = True
                logger.info(f"[DEPT_DELETE] 사용자 {request.user.username}: 부서 {pk} 삭제 권한 있음 (같은 회사)")
            else:
                logger.warning(f"[DEPT_DELETE] 사용자 {request.user.username}: 부서 {pk} 삭제 권한 없음 (다른 회사)")
        
        if not has_delete_permission:
            messages.error(request, '이 부서/연구실을 삭제할 권한이 없습니다.')
            return redirect('reporting:company_detail', pk=department.company.pk)
    else:
        logger.info(f"[DEPT_DELETE] Admin 사용자 {request.user.username}: 부서 {pk} 삭제 권한 있음")
    
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
        
        logger.info(f"[DEPT_DELETE] 사용자 {request.user.username}: 부서 '{company_name} - {department_name}' 삭제 완료")
        
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
    
    # 현재 사용자 회사와 같은 회사의 사용자들이 생성한 업체만 조회
    user_profile_obj = getattr(request.user, 'userprofile', None)
    if user_profile_obj and user_profile_obj.company:
        # 같은 회사 소속 사용자들이 생성한 업체만 조회
        same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
        companies = Company.objects.filter(created_by__in=same_company_users).annotate(
            department_count=Count('departments', distinct=True),
            followup_count=Count('followup_companies', distinct=True)
        ).order_by('name')
    else:
        # 회사 정보가 없는 경우 빈 쿼리셋
        companies = Company.objects.none()
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(name__icontains=search_query)
    
    # 각 업체별 담당자 정보 추가 (같은 회사 사용자들만)
    companies_with_salesmen = []
    if user_profile_obj and user_profile_obj.company:
        same_company_users_list = User.objects.filter(userprofile__company=user_profile_obj.company)
    else:
        same_company_users_list = []
        
    for company in companies:
        # 기본 담당자: 업체를 생성한 사람
        salesmen = []
        if company.created_by:
            salesmen.append(company.created_by)
        
        # 추가 담당자: 해당 업체의 FollowUp을 담당하는 실무자들 (같은 회사 사용자들만)
        followups_in_company = FollowUp.objects.filter(
            Q(company=company) | Q(department__company=company),
            user__in=same_company_users_list
        ).select_related('user').distinct()
        
        # FollowUp 담당자들을 추가 (중복 제거)
        for followup in followups_in_company:
            if followup.user not in salesmen:
                salesmen.append(followup.user)
        
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
    
    # 현재 사용자 회사와 같은 회사에서 생성된 업체인지 확인
    user_profile_obj = getattr(request.user, 'userprofile', None)
    if user_profile_obj and user_profile_obj.company:
        same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
        company = get_object_or_404(Company, pk=pk, created_by__in=same_company_users)
    else:
        # 회사 정보가 없는 경우 접근 거부
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:manager_company_list')
    
    # 해당 업체의 부서 목록
    departments = company.departments.annotate(
        followup_count=Count('followup_departments')
    ).order_by('name')
    
    # 검색 기능 (부서명)
    dept_search = request.GET.get('dept_search', '')
    if dept_search:
        departments = departments.filter(name__icontains=dept_search)
    
    # 해당 업체를 관리하는 실무자들 조회 (같은 회사 사용자들만)
    followups_in_company = FollowUp.objects.filter(
        Q(company=company) | Q(department__company=company),
        user__in=same_company_users
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
    from decimal import Decimal
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
            Q(manager__icontains=search_query) |
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
        '메일 주소', '상세 주소', '고객 등급', '납품 품목', '총 납품 금액', '상세 내용'
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
        
        # 고객 등급 (우선순위)
        priority_display = followup.get_priority_display() or '보통'
        
        # 납품 관련 정보 집계
        delivery_histories = followup.histories.filter(action_type='delivery_schedule')
        
        # 납품 품목별 수량 집계용 딕셔너리
        item_quantities = {}
        total_delivery_amount = 0
        
        for history in delivery_histories:
            # 납품 금액 집계
            if history.delivery_amount:
                total_delivery_amount += history.delivery_amount
            
            # 납품 품목 집계
            if history.delivery_items:
                # 줄바꿈 문자 처리
                processed_items = history.delivery_items.replace('\\n', '\n').replace('\\r\\n', '\n').replace('\\r', '\n').strip()
                
                # 각 라인 처리하여 품목명과 수량 추출
                lines = [line.strip() for line in processed_items.split('\n') if line.strip()]
                for line in lines:
                    # "품목명: 수량개 (금액원)" 패턴 파싱
                    if ':' in line and '개' in line:
                        try:
                            # 품목명 추출
                            item_name = line.split(':')[0].strip()
                            
                            # 수량 추출 (: 이후 첫 번째 숫자)
                            after_colon = line.split(':', 1)[1]
                            import re
                            quantity_match = re.search(r'(\d+(?:\.\d+)?)개', after_colon)
                            
                            if quantity_match:
                                quantity = float(quantity_match.group(1))
                                
                                # 품목별 수량 누적
                                if item_name in item_quantities:
                                    item_quantities[item_name] += quantity
                                else:
                                    item_quantities[item_name] = quantity
                            else:
                                # 수량을 찾지 못한 경우 1개로 처리
                                if item_name in item_quantities:
                                    item_quantities[item_name] += 1
                                else:
                                    item_quantities[item_name] = 1
                        except:
                            # 파싱 실패 시 품목명만 추출하고 1개로 처리
                            item_name = line.split(':')[0].strip()
                            if item_name in item_quantities:
                                item_quantities[item_name] += 1
                            else:
                                item_quantities[item_name] = 1
                    else:
                        # 단순 품목명인 경우 1개로 처리
                        if line in item_quantities:
                            item_quantities[line] += 1
                        else:
                            item_quantities[line] = 1
        
        # Schedule 기반 DeliveryItem도 포함
        schedule_deliveries = followup.schedules.filter(
            activity_type='delivery',
            delivery_items_set__isnull=False
        )
        
        for schedule in schedule_deliveries:
            for item in schedule.delivery_items_set.all():
                # Schedule 기반 품목의 금액도 포함 (Decimal 타입으로 변환)
                if item.total_price:
                    total_delivery_amount += Decimal(str(item.total_price))
                
                # Schedule 기반 품목 집계
                item_name = item.item_name
                quantity = float(item.quantity)
                
                # 품목별 수량 누적 (History와 Schedule 통합)
                if item_name in item_quantities:
                    item_quantities[item_name] += quantity
                else:
                    item_quantities[item_name] = quantity
        
        # 품목 텍스트 생성 (품목명과 총 수량 표시)
        if item_quantities:
            items_list = []
            for item_name, total_qty in sorted(item_quantities.items()):
                # 소수점이 있으면 그대로, 정수면 정수로 표시
                if total_qty == int(total_qty):
                    qty_str = str(int(total_qty))
                else:
                    qty_str = str(total_qty)
                items_list.append(f"{item_name}: {qty_str}개")
            
            # 최대 10개까지 표시
            if len(items_list) <= 10:
                items_text = ', '.join(items_list)
            else:
                items_text = ', '.join(items_list[:10]) + f' 등 총 {len(items_list)}개 품목'
        else:
            items_text = '납품 기록 없음'
        
        # 기본 정보
        data = [
            followup.customer_name or '',
            followup.company.name if followup.company else '',
            followup.department.name if followup.department else '',
            manager_name,  # FollowUp의 책임자 필드에서 가져오기
            followup.phone_number or '',
            followup.email or '',
            followup.address or '',
            priority_display,  # 고객 등급
            items_text,  # 납품 품목
            f"{total_delivery_amount:,}원" if total_delivery_amount > 0 else '납품 기록 없음',  # 총 납품 금액
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
    # 각 컬럼별 최적 너비 설정
    column_widths = {
        1: 15,   # 고객명
        2: 20,   # 업체/학교명
        3: 20,   # 부서/연구실명
        4: 12,   # 책임자
        5: 15,   # 핸드폰 번호
        6: 25,   # 메일 주소
        7: 30,   # 상세 주소
        8: 10,   # 고객 등급
        9: 40,   # 납품 품목 (넓게)
        10: 15,  # 총 납품 금액
        11: 30,  # 상세 내용
    }
    
    for column in ws.columns:
        column_letter = get_column_letter(column[0].column)
        col_num = column[0].column
        
        # 미리 정의된 너비가 있으면 사용
        if col_num in column_widths:
            ws.column_dimensions[column_letter].width = column_widths[col_num]
        else:
            # 히스토리 컬럼들에 대한 자동 조정
            max_length = 0
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
            
            # 히스토리 컬럼은 최소 20, 최대 50으로 제한
            adjusted_width = min(max(max_length + 3, 20), 50)
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
            Q(manager__icontains=search_query) |
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
    """고객별 활동 요약 리포트 목록 - Schedule DeliveryItem도 포함"""
    from django.db.models import Count, Sum, Max, Q
    from django.contrib.auth.models import User
    from decimal import Decimal
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        
        # Admin이 아니고 하나과학이 아닌 경우 같은 회사의 사용자만 필터링
        if not getattr(request, 'is_admin', False) and not getattr(request, 'is_hanagwahak', False):
            user_profile_obj = getattr(request.user, 'userprofile', None)
            if user_profile_obj and user_profile_obj.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
                accessible_users = accessible_users.filter(id__in=same_company_users.values_list('id', flat=True))
        
        followups = FollowUp.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        followups = FollowUp.objects.filter(user=request.user)
    
    # 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
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
        
        # 하나과학이 아닌 경우 같은 회사의 사용자만 필터링
        if not getattr(request, 'is_hanagwahak', False):
            user_profile_obj = getattr(request.user, 'userprofile', None)
            if user_profile_obj and user_profile_obj.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
                accessible_users_list = accessible_users_list.filter(id__in=same_company_users.values_list('id', flat=True))
        
        users = accessible_users_list.filter(followup__isnull=False).distinct()
        
        if user_filter:
            try:
                candidate_user = User.objects.get(id=user_filter)
                if candidate_user in accessible_users_list:
                    selected_user = candidate_user
                    followups = followups.filter(user=candidate_user)
            except (User.DoesNotExist, ValueError):
                pass
    
    # 각 고객별 통계 수동 계산
    followups_with_stats = []
    total_amount_sum = Decimal('0')
    total_meetings_sum = 0
    total_deliveries_sum = 0
    total_unpaid_sum = 0
    
    for followup in followups.select_related('user', 'company', 'department'):
        # History 기반 통계
        histories = History.objects.filter(followup=followup)
        meetings = histories.filter(action_type='customer_meeting').count()
        delivery_histories = histories.filter(action_type='delivery_schedule')
        deliveries = delivery_histories.count()
        history_amount = delivery_histories.aggregate(total=Sum('delivery_amount'))['total'] or Decimal('0')
        unpaid = delivery_histories.filter(tax_invoice_issued=False).count()
        
        # Schedule DeliveryItem 기반 통계
        schedule_deliveries = Schedule.objects.filter(
            followup=followup,
            activity_type='delivery',
            delivery_items_set__isnull=False
        ).distinct()
        schedule_delivery_count = schedule_deliveries.count()
        schedule_amount = DeliveryItem.objects.filter(
            schedule__followup=followup,
            schedule__activity_type='delivery'
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        # 중복 제거된 납품 횟수 계산
        # History에 기록된 일정 ID들
        history_schedule_ids = set(
            delivery_histories.filter(schedule__isnull=False).values_list('schedule_id', flat=True)
        )
        # Schedule에 DeliveryItem이 있는 일정 ID들  
        schedule_ids = set(schedule_deliveries.values_list('id', flat=True))
        
        # History만 있는 납품 + Schedule만 있는 납품 + 둘 다 있는 경우는 1개로 카운팅
        history_only_deliveries = delivery_histories.filter(schedule__isnull=True).count()
        unique_deliveries_count = len(history_schedule_ids | schedule_ids) + history_only_deliveries
        
        # 통합 통계
        total_meetings_count = meetings
        total_deliveries_count = unique_deliveries_count
        total_amount = history_amount + schedule_amount
        last_contact = histories.aggregate(last=Max('created_at'))['last']
        
        # 객체에 통계 추가
        followup.total_meetings = total_meetings_count
        followup.total_deliveries = total_deliveries_count
        followup.total_amount = total_amount
        followup.unpaid_count = unpaid  # Schedule에서는 세금계산서 정보가 없으므로 History만
        followup.last_contact = last_contact
        
        followups_with_stats.append(followup)
        
        # 전체 통계 누적
        total_amount_sum += total_amount
        total_meetings_sum += total_meetings_count
        total_deliveries_sum += total_deliveries_count
        total_unpaid_sum += unpaid
    
    # 최근 접촉일 기준으로 정렬
    from django.utils import timezone
    followups_with_stats.sort(key=lambda x: x.last_contact or timezone.now().replace(year=1900), reverse=True)
    
    context = {
        'followups': followups_with_stats,
        'total_customers': len(followups_with_stats),
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
    
    print(f"=== 고객 상세 보고서 요청 (ID: {followup_id}) ===")
    logger.info(f"=== 고객 상세 보고서 요청 (ID: {followup_id}) ===")
    
    # 권한 확인 및 팔로우업 조회
    try:
        followup = FollowUp.objects.select_related('user', 'company', 'department').get(id=followup_id)
        
        # Admin 사용자는 모든 데이터에 접근 가능
        if getattr(request, 'is_admin', False):
            logger.info(f"Admin 사용자 {request.user.username}가 고객 {followup_id}에 접근")
        else:
            # 권한 체크
            if not can_access_user_data(request.user, followup.user):
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('reporting:customer_report')
            
            # 하나과학이 아닌 경우 같은 회사 체크
            if not getattr(request, 'is_hanagwahak', False):
                user_profile_obj = getattr(request.user, 'userprofile', None)
                followup_user_profile = getattr(followup.user, 'userprofile', None)
                if (user_profile_obj and user_profile_obj.company and 
                    followup_user_profile and followup_user_profile.company and
                    user_profile_obj.company != followup_user_profile.company):
                    messages.error(request, '접근 권한이 없습니다.')
                    return redirect('reporting:customer_report')
            
    except FollowUp.DoesNotExist:
        messages.error(request, '해당 고객 정보를 찾을 수 없습니다.')
        return redirect('reporting:customer_report')
    
    # 해당 고객의 모든 히스토리
    histories = History.objects.filter(followup=followup).select_related(
        'user', 'schedule'
    ).order_by('-created_at')
    
    # Admin이 아니고 하나과학이 아닌 경우 서비스 히스토리 제외
    if not getattr(request, 'is_admin', False) and not getattr(request, 'is_hanagwahak', False):
        histories = histories.exclude(action_type='service')
    
    # 기본 통계 - History와 Schedule의 DeliveryItem 모두 포함 (중복 제거)
    total_meetings = histories.filter(action_type='customer_meeting').count()
    
    # 납품 히스토리
    delivery_histories = histories.filter(action_type='delivery_schedule')
    
    # 전체 데이터 조회 로그 추가
    print(f"=== 전체 납품 데이터 조회 시작 (고객 ID: {followup_id}) ===")
    print(f"전체 History 개수: {histories.count()}")
    print(f"납품 History 개수: {delivery_histories.count()}")
    
    logger.info(f"=== 전체 납품 데이터 조회 시작 (고객 ID: {followup_id}) ===")
    logger.info(f"전체 History 개수: {histories.count()}")
    logger.info(f"납품 History 개수: {delivery_histories.count()}")
    
    # 각 delivery_history 상세 정보
    for history in delivery_histories:
        print(f"History {history.id}: action_type={history.action_type}, delivery_amount={history.delivery_amount}, schedule_id={history.schedule_id if history.schedule else None}")
        logger.info(f"History {history.id}: action_type={history.action_type}, delivery_amount={history.delivery_amount}, schedule_id={history.schedule_id if history.schedule else None}")
    
    # 납품 금액 계산
    history_amount = delivery_histories.aggregate(total=Sum('delivery_amount'))['total'] or 0
    
    # Schedule에서 해당 고객의 DeliveryItem 금액
    schedule_amount = DeliveryItem.objects.filter(
        schedule__followup=followup,
        schedule__activity_type='delivery'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    total_amount = history_amount + schedule_amount
    
    # 전체 Schedule 조회 (참고용)
    all_schedules = Schedule.objects.filter(followup=followup)
    delivery_schedules = all_schedules.filter(activity_type='delivery')
    
    print(f"전체 Schedule 개수: {all_schedules.count()}")
    print(f"납품 타입 Schedule 개수: {delivery_schedules.count()}")
    logger.info(f"전체 Schedule 개수: {all_schedules.count()}")
    logger.info(f"납품 타입 Schedule 개수: {delivery_schedules.count()}")
    
    # 납품 타입 Schedule 각각 확인
    for schedule in delivery_schedules:
        items_count = schedule.delivery_items_set.count()
        print(f"납품 Schedule {schedule.id}: visit_date={schedule.visit_date}, items_count={items_count}")
        logger.info(f"납품 Schedule {schedule.id}: visit_date={schedule.visit_date}, items_count={items_count}")
    
    # Schedule DeliveryItem이 있는 일정들 (중복 제거)
    schedule_deliveries_ids = Schedule.objects.filter(
        followup=followup,
        activity_type='delivery',
        delivery_items_set__isnull=False
    ).values_list('id', flat=True).distinct()
    
    print(f"🔍 schedule_deliveries_ids: {list(schedule_deliveries_ids)}")
    logger.info(f"🔍 schedule_deliveries_ids: {list(schedule_deliveries_ids)}")
    
    schedule_deliveries = Schedule.objects.filter(id__in=schedule_deliveries_ids)
    
    print(f"🔍 schedule_deliveries count: {schedule_deliveries.count()}")
    print(f"🔍 schedule_deliveries list: {list(schedule_deliveries.values_list('id', flat=True))}")
    logger.info(f"🔍 schedule_deliveries count: {schedule_deliveries.count()}")
    logger.info(f"🔍 schedule_deliveries list: {list(schedule_deliveries.values_list('id', flat=True))}")
    
    # Schedule 33 특별 확인
    schedule_33 = Schedule.objects.filter(id=33).first()
    if schedule_33:
        items_count = schedule_33.delivery_items_set.count()
        print(f"🔍 Schedule 33 특별 확인: followup={schedule_33.followup_id}, activity_type={schedule_33.activity_type}, items_count={items_count}")
        print(f"🔍 Schedule 33이 schedule_deliveries에 포함되는가: {schedule_33 in schedule_deliveries}")
        logger.info(f"🔍 Schedule 33 특별 확인: followup={schedule_33.followup_id}, activity_type={schedule_33.activity_type}, items_count={items_count}")
        logger.info(f"🔍 Schedule 33이 schedule_deliveries에 포함되는가: {schedule_33 in schedule_deliveries}")
    
    # Schedule 데이터 상세 로그
    print(f"Schedule 납품 개수: {schedule_deliveries.count()}")
    logger.info(f"Schedule 납품 개수: {schedule_deliveries.count()}")
    
    # 각 schedule 상세 정보
    for schedule in schedule_deliveries:
        items_count = schedule.delivery_items_set.count()
        items_total = schedule.delivery_items_set.aggregate(total=Sum('total_price'))['total'] or 0
        print(f"Schedule {schedule.id}: activity_type={schedule.activity_type}, items={items_count}, total_amount={items_total}")
        logger.info(f"Schedule {schedule.id}: activity_type={schedule.activity_type}, items={items_count}, total_amount={items_total}")
        
        # 각 DeliveryItem 상세
        for item in schedule.delivery_items_set.all():
            print(f"  - DeliveryItem {item.id}: name={item.item_name}, quantity={item.quantity}, unit_price={item.unit_price}, total_price={item.total_price}")
            logger.info(f"  - DeliveryItem {item.id}: name={item.item_name}, quantity={item.quantity}, unit_price={item.unit_price}, total_price={item.total_price}")
    
    # 중복 제거된 납품 횟수 계산
    # History에 기록된 일정 ID들
    history_schedule_ids = set(
        delivery_histories.filter(schedule__isnull=False).values_list('schedule_id', flat=True)
    )
    # Schedule에 DeliveryItem이 있는 일정 ID들  
    schedule_ids = set(schedule_deliveries.values_list('id', flat=True))
    
    # History만 있는 납품 + Schedule만 있는 납품 + 둘 다 있는 경우는 1개로 카운팅
    history_only_deliveries = delivery_histories.filter(schedule__isnull=True).count()
    total_deliveries = len(history_schedule_ids | schedule_ids) + history_only_deliveries
    
    # 세금계산서 현황 - 중복 제거하여 계산
    # History에서 일정과 연결된 세금계산서 상태
    history_with_schedule_issued = delivery_histories.filter(
        schedule__isnull=False,
        tax_invoice_issued=True
    ).values_list('schedule_id', flat=True).distinct()
    
    history_with_schedule_pending = delivery_histories.filter(
        schedule__isnull=False,
        tax_invoice_issued=False
    ).values_list('schedule_id', flat=True).distinct()
    
    # History에서 일정과 연결되지 않은 세금계산서 상태
    history_without_schedule_issued = delivery_histories.filter(
        schedule__isnull=True,
        tax_invoice_issued=True
    ).count()
    
    history_without_schedule_pending = delivery_histories.filter(
        schedule__isnull=True,
        tax_invoice_issued=False
    ).count()
    
    # Schedule DeliveryItem에서 세금계산서 상태 (모든 품목이 발행되었는지 확인)
    schedule_with_items = Schedule.objects.filter(
        followup=followup,
        activity_type='delivery',
        delivery_items_set__isnull=False
    ).distinct()
    
    schedule_tax_issued_ids = set()
    schedule_tax_pending_ids = set()
    
    for schedule in schedule_with_items:
        items = schedule.delivery_items_set.all()
        if items.exists():
            all_issued = all(item.tax_invoice_issued for item in items)
            if all_issued:
                schedule_tax_issued_ids.add(schedule.id)
            else:
                schedule_tax_pending_ids.add(schedule.id)
    
    # 중복 제거하여 최종 세금계산서 현황 계산
    # 1. History와 Schedule 모두에 있는 경우: History 우선
    combined_issued_ids = set(history_with_schedule_issued) | schedule_tax_issued_ids
    combined_pending_ids = set(history_with_schedule_pending) | schedule_tax_pending_ids
    
    # 발행된 것이 우선 (같은 일정에 대해 History는 발행, Schedule은 미발행인 경우 발행으로 처리)
    final_issued_ids = combined_issued_ids
    final_pending_ids = combined_pending_ids - combined_issued_ids
    
    tax_invoices_issued = len(final_issued_ids) + history_without_schedule_issued
    tax_invoices_pending = len(final_pending_ids) + history_without_schedule_pending
    
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
    
    # Schedule에서 DeliveryItem이 있는 납품 일정들 (이미 위에서 중복 제거됨)
    # schedule_deliveries는 이미 정의되어 있음 - 중복 방지를 위해 재사용
    schedule_deliveries = schedule_deliveries.select_related('user').prefetch_related('delivery_items_set').order_by('-visit_date', '-created_at')
    
    # Schedule 납품 일정에 총액 정보 추가
    for schedule in schedule_deliveries:
        total_amount = 0
        tax_invoice_issued_count = 0
        total_items_count = 0
        
        for item in schedule.delivery_items_set.all():
            if item.total_price:
                item_total = float(item.total_price)
            elif item.unit_price:
                item_total = float(item.unit_price) * item.quantity * 1.1
            else:
                item_total = 0
            total_amount += item_total
            total_items_count += 1
            if item.tax_invoice_issued:
                tax_invoice_issued_count += 1
        
        schedule.calculated_total_amount = total_amount
        schedule.tax_invoice_issued_count = tax_invoice_issued_count
        schedule.total_items_count = total_items_count
    
    # 통합 납품 내역 생성 (중복 제거)
    integrated_deliveries = []
    processed_schedule_ids = set()  # 이미 처리된 Schedule ID를 추적
    
    print(f"=== 통합 납품 내역 생성 시작 (고객 ID: {followup_id}) ===")
    print(f"납품 히스토리 개수: {delivery_histories.count()}")
    print(f"스케줄 납품 개수: {schedule_deliveries.count()}")
    
    logger.info(f"=== 통합 납품 내역 생성 시작 (고객 ID: {followup_id}) ===")
    logger.info(f"납품 히스토리 개수: {delivery_histories.count()}")
    logger.info(f"스케줄 납품 개수: {schedule_deliveries.count()}")
    
    # History-Schedule 연결 관계 분석
    print("=== History-Schedule 연결 관계 분석 ===")
    logger.info("=== History-Schedule 연결 관계 분석 ===")
    
    history_with_schedule = delivery_histories.filter(schedule__isnull=False)
    history_without_schedule = delivery_histories.filter(schedule__isnull=True)
    
    print(f"Schedule과 연결된 History: {history_with_schedule.count()}개")
    print(f"Schedule과 연결되지 않은 History: {history_without_schedule.count()}개")
    logger.info(f"Schedule과 연결된 History: {history_with_schedule.count()}개")
    logger.info(f"Schedule과 연결되지 않은 History: {history_without_schedule.count()}개")
    
    # 모든 납품 타입 Schedule 확인 (DeliveryItem 유무 관계없이)
    all_delivery_schedules = Schedule.objects.filter(followup=followup, activity_type='delivery')
    schedules_with_history = set(delivery_histories.filter(schedule__isnull=False).values_list('schedule_id', flat=True))
    schedules_with_items = set(schedule_deliveries.values_list('id', flat=True))
    
    print(f"전체 납품 Schedule: {all_delivery_schedules.count()}개")
    print(f"History와 연결된 Schedule ID들: {schedules_with_history}")
    print(f"DeliveryItem이 있는 Schedule ID들: {schedules_with_items}")
    logger.info(f"전체 납품 Schedule: {all_delivery_schedules.count()}개")
    logger.info(f"History와 연결된 Schedule ID들: {schedules_with_history}")
    logger.info(f"DeliveryItem이 있는 Schedule ID들: {schedules_with_items}")
    
    # History와도 연결되지 않고 DeliveryItem도 없는 Schedule 찾기
    orphaned_schedules = all_delivery_schedules.exclude(
        Q(id__in=schedules_with_history) | Q(id__in=schedules_with_items)
    )
    print(f"고립된 Schedule (History 없고 DeliveryItem 없음): {orphaned_schedules.count()}개")
    logger.info(f"고립된 Schedule (History 없고 DeliveryItem 없음): {orphaned_schedules.count()}개")
    for schedule in orphaned_schedules:
        print(f"  - 고립된 Schedule {schedule.id}: date={schedule.visit_date}, notes={schedule.notes}")
        logger.info(f"  - 고립된 Schedule {schedule.id}: date={schedule.visit_date}, notes={schedule.notes}")

    # 1. History 기반 납품 내역
    for history in delivery_histories:
        print(f"History {history.id}: schedule_id={history.schedule_id}, amount={history.delivery_amount}")
        logger.info(f"History {history.id}: schedule_id={history.schedule_id}, amount={history.delivery_amount}")
        
        delivery_data = {
            'type': 'history',
            'id': history.id,
            'date': history.delivery_date or history.created_at.date(),
            'schedule_id': history.schedule_id if history.schedule else None,
            'items_display': history.delivery_items or None,
            'amount': history.delivery_amount,
            'tax_invoice_issued': history.tax_invoice_issued,  # History 기준으로 세금계산서 상태 표시
            'content': history.content,
            'user': history.user.username,
            'has_schedule_items': False,
        }
        
        # 연결된 일정이 있고, 그 일정에 DeliveryItem이 있는지 확인
        if history.schedule:
            print(f"🔍 History {history.id} -> Schedule {history.schedule.id} 연결 발견")
            if history.schedule.id == 33:
                print(f"🚨 중요: History {history.id}이 Schedule 33과 연결되어 있음!")
                logger.info(f"🚨 중요: History {history.id}이 Schedule 33과 연결되어 있음!")
            
            schedule_items = history.schedule.delivery_items_set.all()
            logger.info(f"History {history.id}의 연결된 Schedule {history.schedule.id}에 {schedule_items.count()}개 품목 존재")
            if schedule_items.exists():
                delivery_data['has_schedule_items'] = True
                # Schedule의 품목 정보를 추가로 표시
                delivery_data['schedule_items'] = schedule_items
                # Schedule 품목의 총액 계산
                schedule_total = 0
                for item in schedule_items:
                    if item.unit_price:
                        item_total = float(item.unit_price) * item.quantity * 1.1
                        schedule_total += item_total
                delivery_data['schedule_amount'] = schedule_total
                # 처리된 Schedule ID 기록
                processed_schedule_ids.add(history.schedule.id)
                print(f"🔍 processed_schedule_ids에 {history.schedule.id} 추가됨")
                logger.info(f"Schedule {history.schedule.id} 처리됨 (총액: {schedule_total})")
        
        integrated_deliveries.append(delivery_data)
    
    print(f"처리된 Schedule IDs: {processed_schedule_ids}")
    logger.info(f"처리된 Schedule IDs: {processed_schedule_ids}")
    
    # 2. History에 없는 Schedule 기반 납품 내역만 추가
    print(f"=== Schedule 기반 납품 처리 시작 ===")
    print(f"처리할 schedule_deliveries: {list(schedule_deliveries.values_list('id', flat=True))}")
    logger.info(f"=== Schedule 기반 납품 처리 시작 ===")
    logger.info(f"처리할 schedule_deliveries: {list(schedule_deliveries.values_list('id', flat=True))}")
    
    for schedule in schedule_deliveries:
        print(f"Schedule {schedule.id} 확인: processed={schedule.id in processed_schedule_ids}")
        logger.info(f"Schedule {schedule.id} 확인: processed={schedule.id in processed_schedule_ids}")
        # 이미 History에서 처리된 일정은 제외
        if schedule.id not in processed_schedule_ids:
            # Schedule 전용인 경우, Schedule 품목들의 세금계산서 상태를 기준으로 함
            schedule_tax_issued = schedule.tax_invoice_issued_count > 0 and schedule.tax_invoice_issued_count == schedule.total_items_count
            
            print(f"Schedule {schedule.id} 전용 납품 추가 준비 - visit_date={schedule.visit_date}, calculated_total={schedule.calculated_total_amount}")
            logger.info(f"Schedule {schedule.id} 전용 납품 추가 (총액: {schedule.calculated_total_amount})")
            
            delivery_data = {
                'type': 'schedule_only',
                'id': schedule.id,
                'date': schedule.visit_date,
                'schedule_id': schedule.id,
                'items_display': None,
                'amount': 0,  # Schedule 전용은 amount를 0으로 설정
                'tax_invoice_issued': schedule_tax_issued,  # Schedule 품목 기준 세금계산서 상태
                'content': schedule.notes or '일정 기반 납품',
                'user': schedule.user.username,
                'has_schedule_items': True,
                'schedule_items': schedule.delivery_items_set.all(),
                'schedule_amount': schedule.calculated_total_amount,
                'schedule_tax_status': {
                    'issued_count': schedule.tax_invoice_issued_count,
                    'total_count': schedule.total_items_count,
                }
            }
            print(f"Schedule {schedule.id} delivery_data 생성 완료 - date={delivery_data['date']}, amount={delivery_data['amount']}, schedule_amount={delivery_data['schedule_amount']}")
            integrated_deliveries.append(delivery_data)
            print(f"integrated_deliveries에 추가 완료 - 현재 총 {len(integrated_deliveries)}개")
            # 처리 완료된 Schedule ID 추가
            processed_schedule_ids.add(schedule.id)
            print(f"processed_schedule_ids에 {schedule.id} 추가 완료")
        else:
            print(f"Schedule {schedule.id} 건너뛰기 - 이미 processed_schedule_ids에 존재")
            logger.info(f"Schedule {schedule.id} 이미 History에서 처리됨 - 건너뛰기")
    
    print(f"=== 최종 통합 납품 내역: {len(integrated_deliveries)}개 ===")
    logger.info(f"=== 최종 통합 납품 내역: {len(integrated_deliveries)}개 ===")
    for i, delivery in enumerate(integrated_deliveries):
        print(f"  {i+1}. {delivery['type']} ID={delivery['id']}, amount={delivery.get('amount', 0)}, schedule_amount={delivery.get('schedule_amount', 0)}")
        print(f"     date={delivery['date']}, content='{delivery.get('content', '')}', user='{delivery.get('user', '')}'")
        logger.info(f"  {i+1}. {delivery['type']} ID={delivery['id']}, amount={delivery.get('amount', 0)}, schedule_amount={delivery.get('schedule_amount', 0)}")
        logger.info(f"     date={delivery['date']}, content='{delivery.get('content', '')}', user='{delivery.get('user', '')}'")
    
    # 날짜순 정렬
    integrated_deliveries.sort(key=lambda x: x['date'], reverse=True)
    
    print(f"=== 정렬 후 통합 납품 내역: {len(integrated_deliveries)}개 ===")
    for i, delivery in enumerate(integrated_deliveries):
        print(f"  {i+1}. {delivery['type']} ID={delivery['id']}, date={delivery['date']}")
        logger.info(f"  {i+1}. {delivery['type']} ID={delivery['id']}, date={delivery['date']}")
    
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
        'schedule_deliveries': schedule_deliveries,
        'integrated_deliveries': integrated_deliveries,  # 통합 납품 내역
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


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def toggle_schedule_delivery_tax_invoice(request, schedule_id):
    """Schedule의 DeliveryItem 세금계산서 발행여부 일괄 토글 API"""
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 가능
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '세금계산서 상태를 변경할 권한이 없습니다.'
            }, status=403)
        
        # Schedule에 연결된 DeliveryItem들 조회
        delivery_items = schedule.delivery_items_set.all()
        
        if not delivery_items.exists():
            return JsonResponse({
                'success': False,
                'error': '해당 일정에 납품 품목이 없습니다.'
            })
        
        # 현재 상태 확인 (하나라도 미발행이면 모두 발행으로, 모두 발행이면 모두 미발행으로)
        any_not_issued = delivery_items.filter(tax_invoice_issued=False).exists()
        new_status = any_not_issued  # 미발행이 있으면 True(발행)로, 없으면 False(미발행)로
        
        # 일괄 업데이트
        updated_count = delivery_items.update(tax_invoice_issued=new_status)
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'updated_count': updated_count,
            'status_text': '발행됨' if new_status else '미발행'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'세금계산서 상태 변경 중 오류가 발생했습니다: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_manager_memo_api(request, history_id):
    """댓글 메모 삭제 API - 매니저는 모든 댓글, 실무자는 자신의 댓글만 삭제 가능"""
    try:
        user_profile = get_user_profile(request.user)
        
        # 히스토리 조회
        history = get_object_or_404(History, pk=history_id)
        
        # 메모 타입이고 부모 히스토리가 있는 댓글인지 확인
        if history.action_type != 'memo' or not history.parent_history:
            return JsonResponse({
                'success': False,
                'error': '댓글 메모만 삭제할 수 있습니다.'
            }, status=400)
        
        # 권한 확인 - 모든 사용자는 본인이 작성한 댓글만 삭제 가능
        can_delete = False
        
        # 매니저가 작성한 댓글인지 확인 (created_by가 있는 경우)
        if history.created_by:
            # 매니저 댓글은 작성한 매니저만 삭제 가능
            if history.created_by == request.user:
                can_delete = True
        else:
            # 일반 실무자 댓글은 작성한 실무자만 삭제 가능
            if history.user == request.user:
                can_delete = True
        
        if not can_delete:
            return JsonResponse({
                'success': False,
                'error': '이 댓글을 삭제할 권한이 없습니다.'
            }, status=403)
        
        # 삭제 실행
        history.delete()
        
        return JsonResponse({
            'success': True,
            'message': '댓글이 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Manager memo deletion error: {e}")
        return JsonResponse({
            'success': False,
            'error': '메모 삭제 중 오류가 발생했습니다.'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def add_manager_memo_to_history_api(request, history_id):
    """히스토리에 댓글 메모 추가 API - 매니저와 해당 실무자가 추가 가능"""
    try:
        user_profile = get_user_profile(request.user)
        
        # 부모 히스토리 조회
        parent_history = get_object_or_404(History, pk=history_id)
        
        # 권한 확인 - 매니저이거나 해당 히스토리의 담당자인 경우 허용
        if not (user_profile.is_manager() or request.user == parent_history.user):
            return JsonResponse({
                'success': False,
                'error': '이 히스토리에 댓글을 추가할 권한이 없습니다.'
            }, status=403)
        
        # 매니저가 다른 사용자 데이터에 접근하는 경우 권한 체크
        if user_profile.is_manager() and request.user != parent_history.user:
            if not can_access_user_data(request.user, parent_history.user):
                return JsonResponse({
                    'success': False,
                    'error': '이 히스토리에 접근할 권한이 없습니다.'
                }, status=403)
        
        # 메모 내용 가져오기
        memo_content = request.POST.get('memo', '').strip()
        if not memo_content:
            return JsonResponse({
                'success': False,
                'error': '메모 내용을 입력해주세요.'
            }, status=400)
        
        # 댓글 메모를 부모 히스토리에 연결된 자식 히스토리로 생성
        # 매니저의 경우: created_by에 매니저 정보 저장, user는 원래 실무자 유지
        # 실무자의 경우: created_by는 None, user는 본인
        memo_history = History.objects.create(
            followup=parent_history.followup,
            user=parent_history.user,  # 원래 실무자를 유지
            parent_history=parent_history,  # 부모 히스토리 설정
            action_type='memo',
            content=memo_content,
            created_by=request.user if user_profile.is_manager() else None,  # 매니저인 경우만 created_by 설정
            schedule=parent_history.schedule if parent_history.schedule else None
        )
        
        # 메시지도 역할에 따라 구분
        message = '댓글이 성공적으로 추가되었습니다.'
        if user_profile.is_manager():
            message = '매니저 메모가 성공적으로 추가되었습니다.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'memo': {
                'id': memo_history.id,
                'content': memo_history.content,
                'created_at': memo_history.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': request.user.username
            }
        })
        
    except Exception as e:
        logger.error(f"Add manager memo to history error: {e}")
        return JsonResponse({
            'success': False,
            'error': '메모 추가 중 오류가 발생했습니다.'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def customer_priority_update(request, followup_id):
    """고객 우선순위 업데이트 API"""
    try:
        followup = get_object_or_404(FollowUp, pk=followup_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 가능
        if not can_modify_user_data(request.user, followup.user):
            return JsonResponse({
                'success': False,
                'error': '고객 정보를 수정할 권한이 없습니다.'
            }, status=403)
        
        new_priority = request.POST.get('priority')
        
        # 유효한 우선순위인지 확인
        valid_priorities = ['one_month', 'three_months', 'long_term']
        if new_priority not in valid_priorities:
            return JsonResponse({
                'success': False,
                'error': '유효하지 않은 우선순위입니다.'
            }, status=400)
        
        # 우선순위 업데이트
        followup.priority = new_priority
        followup.save()
        
        # 응답에 포함할 우선순위 표시명
        priority_display = {
            'one_month': '한달',
            'three_months': '세달', 
            'long_term': '장기'
        }.get(new_priority, '장기')
        
        return JsonResponse({
            'success': True,
            'message': f'고객 우선순위가 {priority_display}로 변경되었습니다.',
            'priority': new_priority,
            'priority_display': priority_display
        })
        
    except Exception as e:
        logger.error(f"Customer priority update error: {e}")
        return JsonResponse({
            'success': False,
            'error': '우선순위 업데이트 중 오류가 발생했습니다.'
        }, status=500)


@login_required
def schedule_delivery_items_api(request, schedule_id):
    """Schedule의 DeliveryItem 정보를 가져오는 API"""
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크: 해당 일정을 볼 수 있는 권한이 있는지 확인
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # 연결된 History가 있는지 확인 (History 기준 세금계산서 상태 적용을 위해)
        related_history = None
        try:
            related_history = History.objects.filter(schedule=schedule).first()  # 이 Schedule에 연결된 첫 번째 History
            # 디버깅 로그
            print(f"DEBUG Schedule API - Schedule ID: {schedule.id}")
            print(f"DEBUG Schedule API - Related History: {related_history.id if related_history else 'None'}")
            if related_history:
                print(f"DEBUG Schedule API - History tax_invoice_issued: {related_history.tax_invoice_issued}")
        except:
            pass
        
        # DeliveryItem 정보 가져오기
        delivery_items = schedule.delivery_items_set.all().order_by('id')
        
        items_data = []
        for item in delivery_items:
            item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
            
            # History가 있으면 History 기준, 없으면 Schedule DeliveryItem 기준
            tax_invoice_status = related_history.tax_invoice_issued if related_history else item.tax_invoice_issued
            
            # 디버깅 로그
            print(f"DEBUG Schedule API - DeliveryItem ID: {item.id}")
            print(f"DEBUG Schedule API - Original tax_invoice_issued: {item.tax_invoice_issued}")
            print(f"DEBUG Schedule API - Applied tax_invoice_status: {tax_invoice_status}")
            
            items_data.append({
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item_total),
                'tax_invoice_issued': tax_invoice_status,
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'schedule_id': schedule.id,
            'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
            'has_related_history': related_history is not None,  # History 연결 여부
            'history_tax_status': related_history.tax_invoice_issued if related_history else None,  # History 세금계산서 상태
        })
        
    except Exception as e:
        logger.error(f"Schedule delivery items API error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'DeliveryItem 정보를 가져오는 중 오류가 발생했습니다.'
        }, status=500)


@login_required
def history_delivery_items_api(request, history_id):
    """History의 DeliveryItem 정보를 가져오는 API"""
    import re
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        history = get_object_or_404(History, pk=history_id)
        
        logger.info(f"[HISTORY_DELIVERY_API] History {history_id} 품목 조회 시작")
        logger.info(f"[HISTORY_DELIVERY_API] History의 연결된 Schedule: {history.schedule.id if history.schedule else 'None'}")
        
        # 권한 체크: 해당 활동기록을 볼 수 있는 권한이 있는지 확인
        if not can_access_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # DeliveryItem 정보 가져오기
        delivery_items = history.delivery_items_set.all().order_by('id')
        
        items_data = []
        has_history_items = False
        has_schedule_items = False
        
        # 1. History DeliveryItem 모델이 있는 경우
        if delivery_items.exists():
            has_history_items = True
            logger.info(f"[HISTORY_DELIVERY_API] History에 {delivery_items.count()}개 DeliveryItem 발견")
            for item in delivery_items:
                item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                items_data.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item_total),
                    'tax_invoice_issued': item.tax_invoice_issued,
                    'source': 'history'  # 출처 표시
                })
        else:
            logger.info(f"[HISTORY_DELIVERY_API] History에 DeliveryItem 없음")
        
        # 2. History DeliveryItem이 없지만 기존 텍스트 데이터가 있는 경우 (fallback)
        if not has_history_items and history.delivery_items and history.delivery_items.strip():
            has_history_items = True
            logger.info(f"[HISTORY_DELIVERY_API] History 텍스트 데이터에서 품목 파싱: '{history.delivery_items[:100]}...'")
            # 기존 텍스트 데이터 파싱
            delivery_text = history.delivery_items.strip()
            
            # 줄바꿈으로 분리하여 각 라인 처리
            lines = delivery_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # "품목명: 수량개 (금액원)" 패턴 파싱
                match = re.match(r'^(.+?):\s*(\d+(?:\.\d+)?)개\s*\((.+?)원\)$', line)
                if match:
                    item_name = match.group(1).strip()
                    quantity = float(match.group(2))
                    amount_str = match.group(3).replace(',', '').replace(' ', '')
                    
                    try:
                        total_amount = float(amount_str)
                        # 부가세 포함 금액에서 단가 역산 (부가세 포함 / 수량)
                        unit_price = total_amount / quantity if quantity > 0 else 0
                    except ValueError:
                        total_amount = 0
                        unit_price = 0
                    
                    items_data.append({
                        'id': f'text_{len(items_data)}',  # 임시 ID
                        'item_name': item_name,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': total_amount,
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준
                        'source': 'history_text'  # 출처 표시
                    })
                else:
                    # 패턴에 맞지 않는 경우, 전체를 품목명으로 처리
                    items_data.append({
                        'id': f'text_{len(items_data)}',  # 임시 ID
                        'item_name': line,
                        'quantity': 1,
                        'unit_price': 0,
                        'total_price': 0,
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준
                        'source': 'history_text'  # 출처 표시
                    })
        
        # 3. 연결된 Schedule의 DeliveryItem도 항상 확인 (History 기준 세금계산서 상태 적용)
        # History에 DeliveryItem이나 텍스트가 없어도 Schedule DeliveryItem은 항상 확인
        if history.schedule:
            schedule_items = history.schedule.delivery_items_set.all().order_by('id')
            logger.info(f"[HISTORY_DELIVERY_API] Schedule {history.schedule.id}에 {schedule_items.count()}개 DeliveryItem 발견")
            
            if schedule_items.exists():
                has_schedule_items = True
                for item in schedule_items:
                    item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                    logger.info(f"[HISTORY_DELIVERY_API] Schedule DeliveryItem: {item.item_name} - {item.quantity}개 x {item.unit_price}원")
                    
                    items_data.append({
                        'id': f'schedule_{item.id}',
                        'item_name': item.item_name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item_total),
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준으로 강제 설정
                        'source': 'schedule'  # 출처 표시
                    })
        else:
            logger.info(f"[HISTORY_DELIVERY_API] History에 연결된 Schedule 없음")
        
        logger.info(f"[HISTORY_DELIVERY_API] 최종 품목 데이터: {len(items_data)}개")
        logger.info(f"[HISTORY_DELIVERY_API] has_history_items: {has_history_items}, has_schedule_items: {has_schedule_items}")
        
        # 디버깅: 최종 응답 데이터 로그
        logger.info(f"[HISTORY_DELIVERY_API] 최종 API 응답 - History {history.id}:")
        logger.info(f"[HISTORY_DELIVERY_API] items_data: {items_data}")
        logger.info(f"[HISTORY_DELIVERY_API] tax_invoice_status: {history.tax_invoice_issued}")
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'history_id': history.id,
            'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
            'is_legacy_data': not has_history_items and bool(history.delivery_items),  # 레거시 데이터 여부
            'has_history_items': has_history_items,
            'has_schedule_items': has_schedule_items,
            'tax_invoice_status': history.tax_invoice_issued,  # History 기준 세금계산서 상태
        })
        
    except Exception as e:
        logger.error(f"[HISTORY_DELIVERY_API] API 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'DeliveryItem 정보를 가져오는 중 오류가 발생했습니다.'
        }, status=500)

@login_required
@require_POST
def followup_create_ajax(request):
    """AJAX로 팔로우업을 생성하는 뷰"""
    try:
        # 필수 필드 검증
        customer_name = request.POST.get('customer_name', '').strip()
        company_id = request.POST.get('company', '').strip()
        department_id = request.POST.get('department', '').strip()
        priority = request.POST.get('priority', '').strip()
        
        if not customer_name:
            return JsonResponse({
                'success': False,
                'error': '고객명을 입력해주세요.'
            })
        
        if not company_id:
            return JsonResponse({
                'success': False,
                'error': '업체/학교를 선택해주세요.'
            })
            
        if not department_id:
            return JsonResponse({
                'success': False,
                'error': '부서/연구실을 선택해주세요.'
            })
        
        if not priority:
            return JsonResponse({
                'success': False,
                'error': '우선순위를 선택해주세요.'
            })
        
        # Company와 Department 객체 가져오기
        try:
            company = Company.objects.get(id=company_id)
            department = Department.objects.get(id=department_id, company=company)
        except (Company.DoesNotExist, Department.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '선택한 업체 또는 부서가 존재하지 않습니다.'
            })
        
        # ======= 임시 수정: 모든 사용자가 모든 업체에 팔로우업 생성 가능 =======
        # 권한 체크를 제거하여 모든 업체에 팔로우업 생성 허용
        
        import logging
        logger = logging.getLogger(__name__)
        
        user_profile_obj = getattr(request.user, 'userprofile', None)
        is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
        
        if is_admin:
            logger.info(f"[FOLLOWUP_CREATE_AJAX] Admin 사용자 {request.user.username}: 업체 {company.name}에 팔로우업 생성 권한 있음")
        else:
            logger.info(f"[FOLLOWUP_CREATE_AJAX] 일반 사용자 {request.user.username}: 업체 {company.name}에 팔로우업 생성 (모든 업체 허용)")
            if user_profile_obj and user_profile_obj.company:
                logger.info(f"[FOLLOWUP_CREATE_AJAX] 사용자 회사: {user_profile_obj.company.name}")
        
        # ======= 원래 권한 체크 로직 (주석 처리됨) =======
        # # 권한 체크: 같은 회사에서 생성된 업체인지 확인
        # user_profile_obj = getattr(request.user, 'userprofile', None)
        # if user_profile_obj and user_profile_obj.company:
        #     same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
        #     if company.created_by not in same_company_users:
        #         return JsonResponse({
        #             'success': False,
        #             'error': '접근 권한이 없는 업체입니다.'
        #         })
        
        # 중복 체크 (같은 고객명, 회사, 부서)
        existing_followup = FollowUp.objects.filter(
            customer_name=customer_name,
            company=company,
            department=department,
            user=request.user
        ).first()
        
        if existing_followup:
            return JsonResponse({
                'success': False,
                'error': '이미 동일한 팔로우업이 존재합니다.'
            })
        
        # 팔로우업 생성
        followup = FollowUp.objects.create(
            user=request.user,
            customer_name=customer_name,
            company=company,
            department=department,
            manager=request.POST.get('manager', '').strip(),
            phone_number=request.POST.get('phone_number', '').strip(),
            email=request.POST.get('email', '').strip(),
            priority=priority,  # 요청에서 받은 우선순위 사용
            address=request.POST.get('address', '').strip(),     # 상세주소 추가
            notes=request.POST.get('notes', '').strip(),
            status='active'
        )
        
        logger.info(f"[FOLLOWUP_CREATE_AJAX] 팔로우업 생성 완료 - ID: {followup.id}, 고객: {customer_name}, 업체: {company.name}, 부서: {department.name}")
        
        # 사용자 회사 정보 설정
        if user_profile_obj and user_profile_obj.company:
            followup.user_company = user_profile_obj.company
            followup.save(update_fields=['user_company'])
        
        # 성공 응답
        followup_text = f"{followup.customer_name} ({followup.company.name} - {followup.department.name})"
        
        return JsonResponse({
            'success': True,
            'followup_id': followup.id,
            'followup_text': followup_text,
            'message': '팔로우업이 성공적으로 생성되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"AJAX 팔로우업 생성 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다. 다시 시도해주세요.'
        }, status=500)

@login_required
def department_list_ajax(request, company_id):
    """특정 업체의 부서 목록을 AJAX로 반환"""
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # 권한 체크: 같은 회사에서 생성된 업체인지 확인
        user_profile_obj = getattr(request.user, 'userprofile', None)
        if user_profile_obj and user_profile_obj.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
            if company.created_by not in same_company_users:
                return JsonResponse({
                    'error': '접근 권한이 없는 업체입니다.'
                }, status=403)
        
        departments = Department.objects.filter(company=company).values('id', 'name')
        departments_list = [{'id': dept['id'], 'name': dept['name']} for dept in departments]
        
        return JsonResponse(departments_list, safe=False)
        
    except Exception as e:
        logger.error(f"부서 목록 AJAX 조회 오류: {str(e)}")
        return JsonResponse({
            'error': '부서 목록을 가져오는 중 오류가 발생했습니다.'
        }, status=500)

@login_required
@role_required(['admin', 'salesman'])
@require_POST
@csrf_exempt
def update_tax_invoice_status(request):
    """세금계산서 상태 업데이트 API"""
    try:
        data = json.loads(request.body)
        delivery_type = data.get('type')
        delivery_id = data.get('id')
        tax_invoice_issued = data.get('tax_invoice_issued')
        
        if delivery_type == 'history':
            # History 레코드의 세금계산서 상태 업데이트
            try:
                history = History.objects.get(id=delivery_id)
                
                # 권한 체크
                if not can_access_user_data(request.user, history.user):
                    return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    history_user_profile = getattr(history.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        history_user_profile and history_user_profile.company and
                        user_profile_obj.company != history_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                history.tax_invoice_issued = tax_invoice_issued
                history.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '세금계산서 상태가 업데이트되었습니다.'
                })
                
            except History.DoesNotExist:
                return JsonResponse({'error': '해당 납품 기록을 찾을 수 없습니다.'}, status=404)
                
        elif delivery_type == 'delivery_item':
            # DeliveryItem의 세금계산서 상태 업데이트
            try:
                delivery_item = DeliveryItem.objects.get(id=delivery_id)
                
                # 권한 체크
                if not can_access_user_data(request.user, delivery_item.schedule.user):
                    return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    item_user_profile = getattr(delivery_item.schedule.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        item_user_profile and item_user_profile.company and
                        user_profile_obj.company != item_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                delivery_item.tax_invoice_issued = tax_invoice_issued
                delivery_item.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '세금계산서 상태가 업데이트되었습니다.'
                })
                
            except DeliveryItem.DoesNotExist:
                return JsonResponse({'error': '해당 납품 품목을 찾을 수 없습니다.'}, status=404)
        
        else:
            return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"세금계산서 상태 업데이트 오류: {str(e)}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)

@login_required
@role_required(['admin', 'salesman'])
def schedule_delivery_items_api(request, schedule_id):
    """Schedule의 DeliveryItem 정보를 반환하는 API"""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        # 하나과학이 아닌 경우 같은 회사 체크
        if not getattr(request, 'is_hanagwahak', False):
            user_profile_obj = getattr(request.user, 'userprofile', None)
            schedule_user_profile = getattr(schedule.user, 'userprofile', None)
            if (user_profile_obj and user_profile_obj.company and 
                schedule_user_profile and schedule_user_profile.company and
                user_profile_obj.company != schedule_user_profile.company):
                return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        # DeliveryItem 정보 가져오기
        items = []
        for item in schedule.delivery_items_set.all():
            items.append({
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'tax_invoice_issued': item.tax_invoice_issued
            })
        
        return JsonResponse({
            'success': True,
            'items': items,
            'schedule_id': schedule.id,
            'visit_date': schedule.visit_date.strftime('%Y-%m-%d')
        })
        
    except Schedule.DoesNotExist:
        return JsonResponse({'error': '해당 일정을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"Schedule 납품 품목 API 오류: {str(e)}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)

@login_required
def debug_user_company_info(request):
    """사용자 회사 정보 디버깅용 임시 뷰"""
    if not request.user.is_superuser:
        return JsonResponse({'error': '관리자만 접근 가능합니다.'}, status=403)
    
    import logging
    logger = logging.getLogger(__name__)
    
    debug_info = {}
    
    try:
        # 현재 사용자 정보
        debug_info['username'] = request.user.username
        debug_info['has_userprofile'] = hasattr(request.user, 'userprofile')
        
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            debug_info['userprofile_id'] = profile.id
            debug_info['userprofile_role'] = profile.role
            debug_info['has_company'] = profile.company is not None
            
            if profile.company:
                debug_info['company_id'] = profile.company.id
                debug_info['company_name'] = profile.company.name
                debug_info['company_name_repr'] = repr(profile.company.name)
                debug_info['company_name_clean'] = profile.company.name.strip().replace(' ', '').lower()
                
                # 하나과학 인식 로직 테스트 (더 상세하게)
                company_name = profile.company.name
                company_name_clean = company_name.strip().replace(' ', '').lower()
                hanagwahak_variations = ['하나과학', 'hanagwahak', 'hana', '하나']
                
                # 각 패턴별 매칭 결과
                pattern_results = {}
                for variation in hanagwahak_variations:
                    pattern_results[variation] = {
                        'pattern_lower': variation.lower(),
                        'in_company_name': variation.lower() in company_name_clean,
                        'bytes_pattern': variation.encode('utf-8'),
                        'bytes_company': company_name_clean.encode('utf-8')
                    }
                
                is_hanagwahak = any(variation.lower() in company_name_clean for variation in hanagwahak_variations)
                debug_info['pattern_results'] = pattern_results
                debug_info['is_hanagwahak_calculated'] = is_hanagwahak
                
                # 인코딩 정보도 추가
                debug_info['company_name_utf8'] = company_name.encode('utf-8').hex()
                debug_info['company_name_bytes'] = [hex(ord(c)) for c in company_name]
                
        # request 객체의 정보
        debug_info['request_user_company'] = str(getattr(request, 'user_company', 'Not set'))
        debug_info['request_user_company_name'] = getattr(request, 'user_company_name', 'Not set')
        debug_info['request_is_hanagwahak'] = getattr(request, 'is_hanagwahak', 'Not set')
        debug_info['request_is_admin'] = getattr(request, 'is_admin', 'Not set')
        
        # 모든 회사 목록
        from .models import UserCompany, Company
        user_companies = UserCompany.objects.all()
        client_companies = Company.objects.all()
        
        debug_info['user_companies_count'] = user_companies.count()
        debug_info['client_companies_count'] = client_companies.count()
        
        debug_info['all_user_companies'] = []
        for c in user_companies:
            company_info = {
                'id': c.id,
                'name': c.name,
                'name_repr': repr(c.name),
                'clean_name': c.name.strip().replace(' ', '').lower(),
                'utf8_hex': c.name.encode('utf-8').hex()
            }
            
            # 각 회사별로 하나과학 패턴 매칭 테스트
            clean_name = c.name.strip().replace(' ', '').lower()
            hanagwahak_variations = [
                '하나과학', 'hanagwahak', 'hana', '하나',
                'hanagwahac', 'hana gwahak', '하나 과학',
                'hanascience', 'hana science'
            ]
            company_info['is_hanagwahak'] = any(variation.lower() in clean_name for variation in hanagwahak_variations)
            company_info['pattern_matches'] = {
                variation: variation.lower() in clean_name for variation in hanagwahak_variations
            }
            
            debug_info['all_user_companies'].append(company_info)
        
        debug_info['all_client_companies'] = []
        for c in client_companies:
            company_info = {
                'id': c.id,
                'name': c.name,
                'created_by': c.created_by.username if c.created_by else 'Unknown',
                'department_count': c.departments.count(),
                'followup_count': c.followup_companies.count()
            }
            debug_info['all_client_companies'].append(company_info)
        
        # 특별히 "고려대학교" 검색
        korea_companies = client_companies.filter(name__icontains='고려대')
        debug_info['korea_university_companies'] = []
        for c in korea_companies:
            company_info = {
                'id': c.id,
                'name': c.name,
                'created_by': c.created_by.username if c.created_by else 'Unknown',
                'created_by_company': c.created_by.userprofile.company.name if c.created_by and hasattr(c.created_by, 'userprofile') and c.created_by.userprofile.company else 'Unknown'
            }
            debug_info['korea_university_companies'].append(company_info)
        
        # 로그에도 기록
        logger.info(f"[DEBUG] 디버그 정보 요청 - 사용자: {request.user.username}")
        logger.info(f"[DEBUG] request.is_hanagwahak: {getattr(request, 'is_hanagwahak', 'Not set')}")
        logger.info(f"[DEBUG] 계산된 is_hanagwahak: {debug_info.get('is_hanagwahak_calculated', 'N/A')}")
        logger.info(f"[DEBUG] 사용자 회사(UserCompany) 수: {debug_info.get('user_companies_count', 0)}")
        logger.info(f"[DEBUG] 고객 업체(Company) 수: {debug_info.get('client_companies_count', 0)}")
        logger.info(f"[DEBUG] 고려대학교 관련 업체 수: {len(debug_info.get('korea_university_companies', []))}")
        
        return JsonResponse(debug_info, ensure_ascii=False, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"[DEBUG] 디버그 뷰 에러: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
