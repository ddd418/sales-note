from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 로그인 요구 데코레이터
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator  # 페이지네이션 추가
from .models import FollowUp, Schedule, History, UserProfile, Company, Department, HistoryFile, DeliveryItem, UserCompany, OpportunityTracking, FunnelStage, Prepayment, PrepaymentUsage
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from functools import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
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
    
    # 기존 품목들 삭제 (수정 시)
    if is_schedule:
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
    else:  # is_history
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
    
    # delivery_items 관련 POST 데이터만 필터링
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
            except (ValueError, IndexError) as e:
                logger.error(f"POST 데이터 파싱 실패: {key} = {value}, 오류: {e}")
                continue
    
    # 납품 품목 저장
    created_count = 0
    
    for index, item_data in delivery_items_data.items():
        item_name = item_data.get('name', '').strip()
        quantity = item_data.get('quantity', '').strip()
        unit_price = item_data.get('unit_price', '').strip()
        product_id = item_data.get('product_id', '').strip()
        
        if item_name and quantity:
            try:
                delivery_item = DeliveryItem(
                    item_name=item_name,
                    quantity=int(quantity),
                    unit='개',  # 기본값
                )
                
                # 제품 연결
                if product_id:
                    try:
                        from .models import Product
                        delivery_item.product = Product.objects.get(id=int(product_id))
                    except (Product.DoesNotExist, ValueError):
                        logger.warning(f"제품 ID {product_id}를 찾을 수 없습니다.")
                
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
            except (ValueError, TypeError) as e:
                logger.error(f"납품 품목 저장 실패: {e}")
                continue  # 잘못된 데이터는 무시
        else:
            logger.warning(f"필수 데이터 누락: name={item_name}, quantity={quantity}")
    
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
    
    # Manager는 모든 Salesman과 다른 Manager의 데이터 접근 가능 (읽기 권한)
    if user_profile.is_manager():
        target_profile = get_user_profile(target_user)
        # Manager는 Salesman과 다른 Manager의 데이터 모두 볼 수 있음
        return target_profile.is_salesman() or target_profile.is_manager()
    
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
        # Manager는 같은 회사의 salesman과 manager들에게 접근 가능
        if hasattr(request_user, 'userprofile') and request_user.userprofile.company:
            user_company = request_user.userprofile.company
            # 같은 회사 소속의 salesman과 manager 모두 필터링
            accessible_profiles = UserProfile.objects.filter(
                role__in=['salesman', 'manager'],
                company=user_company
            )
            return User.objects.filter(userprofile__in=accessible_profiles)
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
    
    opportunity = forms.ModelChoiceField(
        queryset=OpportunityTracking.objects.none(),
        required=False,
        widget=forms.HiddenInput(),  # Select 대신 HiddenInput 사용
        label='연결할 영업 기회',
        help_text='납품/미팅 일정인 경우 기존 영업 기회를 선택하세요. 견적은 자동으로 새 영업 기회가 생성됩니다.'
    )
    
    # 선결제 관련 필드
    prepayment = forms.ModelChoiceField(
        queryset=Prepayment.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_prepayment',
        }),
        label='사용할 선결제',
        help_text='고객의 선결제 잔액에서 차감할 선결제를 선택하세요.'
    )
    
    # status 필드를 명시적으로 선언 (required=False)
    status = forms.ChoiceField(
        choices=Schedule.STATUS_CHOICES,
        required=False,
        initial='scheduled',
        widget=forms.HiddenInput(attrs={'value': 'scheduled'}),
        label='상태'
    )
    
    class Meta:
        model = Schedule
        fields = ['followup', 'opportunity', 'visit_date', 'visit_time', 'activity_type', 'location', 'status', 'notes', 
                  'expected_revenue', 'probability', 'expected_close_date', 'purchase_confirmed',
                  'use_prepayment', 'prepayment', 'prepayment_amount']
        widgets = {
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'visit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '방문 장소를 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            # status는 위에서 명시적으로 선언했으므로 여기서 제거
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '메모를 입력하세요 (선택사항)', 'autocomplete': 'off'}),
            'expected_revenue': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '예상 매출액 (원)', 'min': '0'}),
            'probability': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '성공 확률 (%)', 'min': '0', 'max': '100'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'use_prepayment': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_use_prepayment'}),
            'prepayment_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '차감할 금액 (원)', 'min': '0', 'id': 'id_prepayment_amount'}),
        }
        labels = {
            'visit_date': '방문 날짜',
            'visit_time': '방문 시간',
            'activity_type': '일정 유형',
            'location': '장소',
            'status': '상태',
            'notes': '메모',
            'expected_revenue': '예상 매출액 (원)',
            'probability': '성공 확률 (%)',
            'expected_close_date': '예상 계약일',
            'purchase_confirmed': '구매 확정',
            'use_prepayment': '선결제 사용',
            'prepayment_amount': '선결제 차감 금액 (원)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # 새 일정 생성 시 기본값 설정
        if not self.instance.pk:
            self.initial['status'] = 'scheduled'
            self.fields['status'].initial = 'scheduled'
        
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
        
        # OpportunityTracking 필드 설정
        if self.instance.pk and self.instance.followup:
            # 수정 시: 해당 고객의 진행 중인 영업 기회 목록
            self.fields['opportunity'].queryset = self.instance.followup.opportunities.exclude(current_stage='lost').order_by('-created_at')
            # 수정 시: 해당 고객의 사용 가능한 선결제 목록
            self.fields['prepayment'].queryset = Prepayment.objects.filter(
                customer=self.instance.followup,
                status='active',
                balance__gt=0
            ).order_by('-payment_date')
            # 선결제 옵션 라벨 설정
            self.fields['prepayment'].label_from_instance = lambda obj: f"{obj.payment_date.strftime('%Y-%m-%d')} - {obj.payer_name or '미지정'} (잔액: {obj.balance:,}원)"
        elif 'followup' in self.data:
            # 생성 시 followup이 선택된 경우
            try:
                followup_id = int(self.data.get('followup'))
                followup = FollowUp.objects.get(pk=followup_id)
                self.fields['opportunity'].queryset = followup.opportunities.exclude(current_stage='lost').order_by('-created_at')
                # 생성 시: 선택된 고객의 사용 가능한 선결제 목록
                self.fields['prepayment'].queryset = Prepayment.objects.filter(
                    customer=followup,
                    status='active',
                    balance__gt=0
                ).order_by('-payment_date')
                # 선결제 옵션 라벨 설정
                self.fields['prepayment'].label_from_instance = lambda obj: f"{obj.payment_date.strftime('%Y-%m-%d')} - {obj.payer_name or '미지정'} (잔액: {obj.balance:,}원)"
            except (ValueError, TypeError, FollowUp.DoesNotExist):
                pass
            
        # 하나과학이 아닌 경우 activity_type에서 서비스 제거
        if request and not getattr(request, 'is_hanagwahak', False):
            self.fields['activity_type'].choices = [
                choice for choice in self.fields['activity_type'].choices 
                if choice[0] != 'service'
            ]

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
            excluded_types.append('service')
            
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
    
    # 매니저용 실무자 필터 (세션 기반)
    view_all = request.GET.get('view_all') == 'true'
    
    # 전체 팀원 선택 시 세션 초기화
    if view_all and user_profile.can_view_all_users():
        if 'selected_user_id' in request.session:
            del request.session['selected_user_id']
        user_filter = None
    else:
        user_filter = request.GET.get('user')
        if not user_filter:
            user_filter = request.session.get('selected_user_id')
        
        if user_filter and user_profile.can_view_all_users():
            request.session['selected_user_id'] = str(user_filter)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 모든 또는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        
        # 매니저가 특정 실무자를 선택한 경우
        if user_filter and not view_all:
            try:
                selected_user = accessible_users.get(id=user_filter)
                followups = FollowUp.objects.filter(user=selected_user).select_related('user', 'company', 'department').prefetch_related('schedules', 'histories')
            except (User.DoesNotExist, ValueError):
                followups = FollowUp.objects.filter(user__in=accessible_users).select_related('user', 'company', 'department').prefetch_related('schedules', 'histories')
        else:
            # 전체보기 또는 선택 안 함
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
    
    # 우선순위 필터링
    priority_filter = request.GET.get('priority')
    if priority_filter:
        followups = followups.filter(priority=priority_filter)
    
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
    
    # 우선순위 선택지 (필터용)
    priority_choices = FollowUp.PRIORITY_CHOICES
    
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
    
    # 선택된 우선순위 정보
    selected_priority = None
    selected_priority_display = None
    if priority_filter:
        # 유효한 우선순위 값인지 확인
        valid_priorities = [choice[0] for choice in FollowUp.PRIORITY_CHOICES]
        if priority_filter in valid_priorities:
            selected_priority = priority_filter
            # 우선순위 표시명 찾기
            for choice in FollowUp.PRIORITY_CHOICES:
                if choice[0] == priority_filter:
                    selected_priority_display = choice[1]
                    break
    
    # 선택된 업체 정보
    selected_company = None
    if company_filter:
        try:
            selected_company = Company.objects.get(id=company_filter)
        except (Company.DoesNotExist, ValueError):
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
        'priority_filter': priority_filter,
        'selected_priority': selected_priority,
        'selected_priority_display': selected_priority_display,
        'selected_company': selected_company,
        'total_count': stats['total_count'],
        'active_count': stats['active_count'],
        'completed_count': stats['completed_count'],
        'paused_count': stats['paused_count'],
        'priority_choices': priority_choices,
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
    
    # 같은 업체-부서의 모든 팔로우업 찾기
    same_department_followups = FollowUp.objects.filter(
        company=followup.company,
        department=followup.department
    ).values_list('id', flat=True)
    
    # 같은 부서의 모든 히스토리 조회 (일정이 있는 경우 일정 날짜 기준, 없는 경우 작성일 기준으로 최신순)
    from django.db.models import Case, When, F
    related_histories = History.objects.filter(
        followup_id__in=same_department_followups
    ).select_related('followup', 'schedule').annotate(
        sort_date=Case(
            When(schedule__isnull=False, then=F('schedule__visit_date')),
            default=F('created_at__date')
        )
    ).order_by('-sort_date', '-created_at')[:20]
    
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
    from reporting.models import DeliveryItem, PrepaymentUsage
    import calendar
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 사용자 프로필 가져오기
    user_profile = get_user_profile(request.user)
    
    # URL 파라미터로 특정 사용자 필터링
    user_filter = request.GET.get('user')
    view_all = request.GET.get('view_all') == 'true'
    selected_user = None
    
    if user_profile.can_view_all_users():
        # 전체 팀원 선택 시 세션 초기화
        if view_all:
            if 'selected_user_id' in request.session:
                del request.session['selected_user_id']
            target_user = None  # 전체 팀원 데이터 표시
        else:
            # user_filter가 없으면 세션에서 가져오기
            if not user_filter:
                user_filter = request.session.get('selected_user_id')
            
            if user_filter:
                try:
                    selected_user = User.objects.get(id=user_filter)
                    target_user = selected_user
                    # 세션에 저장
                    request.session['selected_user_id'] = str(user_filter)
                except (User.DoesNotExist, ValueError):
                    logger.warning(f"[DASHBOARD FILTER] 사용자 찾기 실패: {user_filter}")
                    target_user = None  # 전체 팀원 데이터 표시
                    # 잘못된 세션 값 제거
                    if 'selected_user_id' in request.session:
                        del request.session['selected_user_id']
            else:
                target_user = None  # 전체 팀원 데이터 표시
    else:
        target_user = request.user
    
    # 매니저용 팀원 목록
    salesman_users = []
    if user_profile.can_view_all_users():
        salesman_users = get_accessible_users(request.user)
    
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
    elif user_profile.can_view_all_users() and target_user is None:
        # Manager가 전체 팀원을 선택한 경우 - 접근 가능한 모든 사용자의 데이터
        accessible_users = get_accessible_users(request.user)
        followup_count = FollowUp.objects.filter(user__in=accessible_users).count()
        schedule_count = Schedule.objects.filter(user__in=accessible_users, status='scheduled').count()
        sales_record_count = History.objects.filter(
            user__in=accessible_users,
            created_at__year=current_year, 
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
        histories = History.objects.filter(user__in=accessible_users)
        histories_current_year = History.objects.filter(user__in=accessible_users, created_at__year=current_year)
        schedules = Schedule.objects.filter(user__in=accessible_users)
        followups = FollowUp.objects.filter(user__in=accessible_users)
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

    # 올해 매출 통계 (Schedule의 DeliveryItem 기준, 취소된 일정 제외)
    if user_profile.is_admin() and not selected_user:
        # Admin은 모든 사용자 데이터
        schedule_delivery_stats = DeliveryItem.objects.filter(
            schedule__visit_date__year=current_year,
            schedule__activity_type='delivery'
        ).exclude(
            schedule__status='cancelled'
        ).aggregate(
            total_amount=Sum('total_price'),
            delivery_count=Count('schedule', distinct=True)
        )
    else:
        # 특정 사용자 데이터만
        schedule_delivery_stats = DeliveryItem.objects.filter(
            schedule__user=target_user,
            schedule__visit_date__year=current_year,
            schedule__activity_type='delivery'
        ).exclude(
            schedule__status='cancelled'
        ).aggregate(
            total_amount=Sum('total_price'),
            delivery_count=Count('schedule', distinct=True)
        )
    
    total_delivery_amount = schedule_delivery_stats['total_amount'] or 0
    delivery_count = schedule_delivery_stats['delivery_count'] or 0
    
    # 활동 유형별 통계 (Schedule 기준, 현재 연도)
    schedules_current_year_filter = schedules.filter(visit_date__year=current_year)
    
    if getattr(request, 'is_admin', False) or getattr(request, 'is_hanagwahak', False):
        activity_stats = schedules_current_year_filter.values('activity_type').annotate(
            count=Count('id')
        ).order_by('activity_type')
    else:
        # Admin이 아니고 하나과학이 아닌 경우 서비스 항목 제외
        activity_stats = schedules_current_year_filter.exclude(activity_type='service').values('activity_type').annotate(
            count=Count('id')
        ).order_by('activity_type')
    
    # 서비스 통계 추가 (완료된 서비스만 카운팅) - Admin이나 하나과학만
    if getattr(request, 'is_admin', False) or getattr(request, 'is_hanagwahak', False):
        service_count = schedules_current_year_filter.filter(activity_type='service', status='completed').count()
        
        # 이번 달 서비스 수 (완료된 것만)
        this_month_service_count = schedules.filter(
            activity_type='service',
            status='completed',
            visit_date__month=current_month,
            visit_date__year=current_year
        ).count()
    else:
        service_count = 0
        this_month_service_count = 0
    
    # 최근 활동 (현재 연도, 최근 5개, 메모 제외)
    recent_activities_queryset = histories_current_year.exclude(action_type='memo')
    if not getattr(request, 'is_admin', False) and not getattr(request, 'is_hanagwahak', False):
        # Admin이 아니고 하나과학이 아닌 경우 서비스도 제외
        recent_activities_queryset = recent_activities_queryset.exclude(action_type='service')
        
    recent_activities = recent_activities_queryset.order_by('-created_at')[:5]
    
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

    # 평균 리드 타임 & 제품별 매출 분석 추가
    from reporting.funnel_analytics import FunnelAnalytics
    analytics = FunnelAnalytics()
    
    # 평균 리드 타임 분석
    lead_time_analysis = analytics.get_average_lead_time(user=target_user)
    
    # 제품군별 매출 비중
    product_sales_distribution = analytics.get_product_sales_distribution(user=target_user)

    # 새로운 성과 지표 계산
    from django.db.models import Avg
    current_month = now.month
    current_year = now.year
    
    # ========================================
    # 이번 달 활동 현황 (일정 기준)
    # ========================================
    # 이번 달 시작/끝 날짜
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_month == 12:
        month_end = now.replace(year=current_year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        month_end = now.replace(month=current_month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 이번 달 마지막 날 계산 (URL 표시용)
    from calendar import monthrange
    last_day = monthrange(current_year, current_month)[1]
    month_last_date = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    # 이번 달 미팅 일정 수 (일정 기준)
    monthly_meetings = schedules.filter(
        activity_type='customer_meeting',
        visit_date__gte=month_start.date(),
        visit_date__lt=month_end.date()
    ).count()
    
    # 처리해야 할 견적 (예정 상태의 견적만)
    # 견적은 납품 생성 시 자동으로 완료 처리되므로, 예정 상태인 것만 처리 대상
    quote_count = schedules.filter(
        activity_type='quote',
        status='scheduled'
    ).count()
    
    # 이번 달 견적 횟수 (이번 달의 모든 견적 일정)
    monthly_quote_count = schedules.filter(
        activity_type='quote',
        visit_date__gte=month_start.date(),
        visit_date__lt=month_end.date()
    ).count()
    
    # 이번 달 납품 일정 수 (취소된 일정 제외)
    monthly_delivery_count = schedules.filter(
        activity_type='delivery',
        status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        visit_date__gte=month_start.date(),
        visit_date__lt=month_end.date()
    ).count()
    
    # 이번 달 매출 (납품 일정의 DeliveryItem 총액 합산, 취소된 일정 제외)
    monthly_delivery_schedules = schedules.filter(
        activity_type='delivery',
        status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        visit_date__gte=month_start.date(),
        visit_date__lt=month_end.date()
    )
    monthly_revenue = DeliveryItem.objects.filter(
        schedule__in=monthly_delivery_schedules
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Prepayment 모델 명시적 import
    from .models import Prepayment
    
    # 이번 달 선결제 건수 (새로 등록된 선결제) - 등록자 본인만
    monthly_prepayment_count = Prepayment.objects.filter(
        created_by=target_user,
        created_at__gte=month_start,
        created_at__lt=month_end
    ).count()
    
    # 이번 달 서비스 수 (완료된 것만)
    monthly_services = histories.filter(
        action_type='service',
        service_status='completed',
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
      # 전환율 계산 (현재 연도 기준)
    # Schedule 테이블 기반으로 계산 (현재 활성 데이터)
    schedules_current_year = schedules.filter(visit_date__year=current_year)
    
    total_meetings = schedules_current_year.filter(activity_type='customer_meeting').count()
    total_quotes = schedules_current_year.filter(activity_type='quote').count()
    total_deliveries = schedules_current_year.filter(activity_type='delivery', status__in=['scheduled', 'completed']).count()  # 취소된 일정 제외
    
    # 견적 → 납품 전환율: 견적을 낸 것 중 납품까지 완료된 비율
    # 같은 opportunity를 가진 견적과 납품을 매칭
    quote_schedules = schedules_current_year.filter(activity_type='quote')
    quotes_with_delivery = 0
    
    for quote in quote_schedules:
        if quote.opportunity:
            # 같은 opportunity에 납품 일정이 있는지 확인
            has_delivery = schedules.filter(
                opportunity=quote.opportunity,
                activity_type='delivery'
            ).exists()
            if has_delivery:
                quotes_with_delivery += 1
    
    # 미팅 → 납품 전환율 (일정 기준: 일정 중 미팅 건수 대비 납품 완료 건수)
    schedule_meetings = schedules_current_year.filter(activity_type='customer_meeting').count()
    schedule_deliveries_completed = schedules_current_year.filter(activity_type='delivery', status='completed').count()
    meeting_to_delivery_rate = (schedule_deliveries_completed / schedule_meetings * 100) if schedule_meetings > 0 else 0
    
    # 견적 → 납품 전환율 (견적을 낸 것 중 납품으로 전환된 비율)
    quote_to_delivery_rate = (quotes_with_delivery / total_quotes * 100) if total_quotes > 0 else 0
    
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

    # ============================================
    # 📊 새로운 7개 차트를 위한 데이터 준비 - Schedule 기준
    # ============================================
    
    # 1️⃣ 매출 및 납품 추이 (월별 납품 금액 + 건수) - Schedule 기준
    monthly_delivery_stats = {
        'labels': [],
        'amounts': [],
        'counts': []
    }
    
    for i in range(11, -1, -1):  # 최근 12개월
        target_date = now - timedelta(days=30*i)
        month_start = target_date.replace(day=1)
        if target_date.month == 12:
            month_end = target_date.replace(year=target_date.year+1, month=1, day=1)
        else:
            month_end = target_date.replace(month=target_date.month+1, day=1)
        
        month_schedules = schedules.filter(
            visit_date__gte=month_start.date(),
            visit_date__lt=month_end.date(),
            activity_type='delivery'
        )
        
        month_data = DeliveryItem.objects.filter(
            schedule__in=month_schedules
        ).aggregate(
            total=Sum('total_price'),
            count=Count('id')
        )
        
        monthly_delivery_stats['labels'].append(f"{target_date.month}월")
        monthly_delivery_stats['amounts'].append(float(month_data['total'] or 0))
        monthly_delivery_stats['counts'].append(month_data['count'] or 0)
    
    # 2️⃣ 영업 퍼널 (미팅 → 견적 제출 → 발주 예정 → 납품 완료)
    # 기준: 모두 일정(Schedule) 기반으로 집계
    schedules_current_year = schedules.filter(visit_date__year=current_year)
    
    meeting_count = schedules_current_year.filter(activity_type='customer_meeting').count()
    quote_count_funnel = schedules_current_year.filter(activity_type='quote').count()
    scheduled_delivery_count = schedules_current_year.filter(activity_type='delivery', status='scheduled').count()
    completed_delivery_count = schedules_current_year.filter(activity_type='delivery', status='completed').count()
    
    sales_funnel = {
        'stages': ['미팅', '견적 제출', '발주 예정', '납품 완료'],
        'values': [
            meeting_count,
            quote_count_funnel,
            scheduled_delivery_count,
            completed_delivery_count
        ]
    }
    
    # 3️⃣ 고객사별 매출 비중 (Top 5 + 기타) - Schedule + History 기준
    # Schedule 기반 매출
    schedule_top_customers = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # History 기반 매출
    histories_current_year_with_company = histories_current_year.filter(
        followup__isnull=False,
        followup__company__isnull=False
    )
    
    history_top_customers = DeliveryItem.objects.filter(
        history__in=histories_current_year_with_company
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # 고객사별 매출 합산
    from collections import defaultdict
    company_revenue = defaultdict(float)
    
    for item in schedule_top_customers:
        company_name = item['schedule__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    for item in history_top_customers:
        company_name = item['history__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    # 상위 5개 추출
    sorted_companies = sorted(company_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
    
    customer_distribution = {
        'labels': [],
        'data': []
    }
    
    total_top5_revenue = 0
    for company_name, revenue in sorted_companies:
        customer_distribution['labels'].append(company_name)
        customer_distribution['data'].append(revenue)
        total_top5_revenue += revenue
    
    # 기타 금액 계산 - Schedule + History 합산
    schedule_total = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    history_total = DeliveryItem.objects.filter(
        history__in=histories_current_year
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    total_all_revenue = float(schedule_total) + float(history_total)
    other_revenue = total_all_revenue - total_top5_revenue
    if other_revenue > 0:
        customer_distribution['labels'].append('기타')
        customer_distribution['data'].append(other_revenue)
    
    # 6️⃣ 고객 유형별 통계 (대학/기업/관공서) - Schedule + History 기준
    customer_type_stats = {
        'labels': ['대학', '기업', '관공서'],
        'revenue': [0, 0, 0],
        'count': [0, 0, 0]
    }
    
    # TODO: Company 모델에 customer_type 필드 추가 후 활성화
    # 현재는 company name으로 간단히 분류 (예: 대학교 포함 여부 등)
    
    # Schedule 기반 통계
    schedule_company_stats = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # 간단한 키워드 기반 분류 (연구소 제외)
    for item in schedule_company_stats:
        company_name = item['schedule__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            # 연구소 포함 모든 기타 기업
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt
    
    # History 기반 통계
    history_company_stats = DeliveryItem.objects.filter(
        history__in=histories_current_year,
        history__followup__isnull=False,
        history__followup__company__isnull=False
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    for item in history_company_stats:
        company_name = item['history__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            # 연구소 포함 모든 기타 기업
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt

    
    # 7️⃣ 활동 히트맵 (현재 달) - 현재 사용자의 일정만
    daily_activity_heatmap = []
    
    # 현재 달의 첫날과 마지막 날 계산
    current_month_start = now.replace(day=1).date()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    current_month_end = (next_month - timedelta(days=1)).date()
    
    # 현재 달의 각 날짜별 활동 카운트 (현재 사용자만)
    current_date = current_month_start
    while current_date <= current_month_end:
        day_activity_count = schedules.filter(
            visit_date=current_date
        ).count()
        
        daily_activity_heatmap.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day_of_week': current_date.weekday(),  # 0=월, 6=일
            'intensity': day_activity_count
        })
        
        current_date += timedelta(days=1)

    context = {        'page_title': '대시보드',
        'current_year': current_year,  # 현재 연도 정보 추가
        'selected_user': selected_user,  # 선택된 사용자 정보
        'target_user': target_user,  # 실제 대상 사용자
        'salesman_users': salesman_users,  # 매니저용 실무자 목록
        'view_all': False,  # 현재 전체보기 기능은 미사용
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
        'meeting_to_delivery_rate': meeting_to_delivery_rate,
        'quote_to_delivery_rate': quote_to_delivery_rate,
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
        # 새로운 차트 데이터
        'monthly_delivery_stats': json.dumps(monthly_delivery_stats, cls=DjangoJSONEncoder),
        'sales_funnel': json.dumps(sales_funnel, cls=DjangoJSONEncoder),
        'customer_distribution': json.dumps(customer_distribution, cls=DjangoJSONEncoder),
        'customer_type_stats': json.dumps(customer_type_stats, cls=DjangoJSONEncoder),
        'daily_activity_heatmap': json.dumps(daily_activity_heatmap, cls=DjangoJSONEncoder),
    }
    
    # 선결제 통계 추가
    from reporting.models import Prepayment
    from decimal import Decimal
    
    # 선결제 조회 - 등록자 본인만 (Manager도 자신이 등록한 것만)
    prepayments = Prepayment.objects.filter(created_by=target_user)
    
    # 선결제 통계 계산
    prepayment_total = prepayments.aggregate(
        total_amount=Sum('amount'),
        total_balance=Sum('balance')
    )
    
    prepayment_stats = {
        'total_amount': prepayment_total['total_amount'] or Decimal('0'),
        'total_balance': prepayment_total['total_balance'] or Decimal('0'),
        'total_used': (prepayment_total['total_amount'] or Decimal('0')) - (prepayment_total['total_balance'] or Decimal('0')),
        'active_count': prepayments.filter(status='active', balance__gt=0).count(),
        'depleted_count': prepayments.filter(status='depleted').count(),
        'total_count': prepayments.count(),
        'monthly_count': monthly_prepayment_count,  # 이번 달 선결제 등록 건수
    }
    
    context['prepayment_stats'] = prepayment_stats
    context['quote_count'] = quote_count  # 처리해야 할 견적 수 (납품 전환 안 된 것)
    context['monthly_quote_count'] = monthly_quote_count  # 이번 달 견적 횟수
    context['monthly_delivery_count'] = monthly_delivery_count  # 이번 달 납품 횟수
    context['current_month'] = current_month  # 현재 월
    context['month_start'] = month_start.date()  # 이번 달 시작일
    context['month_end'] = month_last_date.date()  # 이번 달 마지막 날 (URL 표시용)
    
    # 평균 리드 타임 & 제품별 매출 분석 추가
    context['lead_time_analysis'] = lead_time_analysis
    context['product_sales_distribution'] = product_sales_distribution
    
    # 제품 차트 데이터 (상위 10개까지 표시)
    top_products = product_sales_distribution['products'][:10] if len(product_sales_distribution['products']) > 10 else product_sales_distribution['products']
    product_chart_data = {
        'labels': [p['product_name'] for p in top_products],
        'data': [float(p['total_revenue']) for p in top_products],
        'percentages': [p['percentage'] for p in top_products],
    }
    context['product_chart_data'] = json.dumps(product_chart_data, cls=DjangoJSONEncoder)
    
    return render(request, 'reporting/dashboard.html', context)

# ============ 일정(Schedule) 관련 뷰들 ============

@login_required
def schedule_list_view(request):
    """일정 목록 보기 (권한 기반 필터링 적용)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    user_profile = get_user_profile(request.user)
    
    # 매니저용 실무자 필터 (세션 기반)
    view_all = request.GET.get('view_all') == 'true'
    
    # 전체 팀원 선택 시 세션 초기화
    if view_all and user_profile.can_view_all_users():
        if 'selected_user_id' in request.session:
            del request.session['selected_user_id']
        user_filter = None
    else:
        user_filter = request.GET.get('user')
        if not user_filter:
            user_filter = request.session.get('selected_user_id')
        
        if user_filter and user_profile.can_view_all_users():
            request.session['selected_user_id'] = str(user_filter)
    
    # 권한에 따른 데이터 필터링
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        
        # 매니저가 특정 실무자를 선택한 경우
        if user_filter and not view_all:
            try:
                selected_user = accessible_users.get(id=user_filter)
                schedules = Schedule.objects.filter(user=selected_user)
            except (User.DoesNotExist, ValueError):
                schedules = Schedule.objects.filter(user__in=accessible_users)
        else:
            # 전체보기 또는 선택 안 함
            schedules = Schedule.objects.filter(user__in=accessible_users)
    else:
        # Salesman은 자신의 데이터만 조회
        schedules = Schedule.objects.filter(user=request.user)
    
    # 검색 기능
    search_query = request.GET.get('search')
    product_search = request.GET.get('product_search')  # 제품 검색 추가
    
    if search_query:
        schedules = schedules.filter(
            Q(followup__customer_name__icontains=search_query) |
            Q(followup__company__name__icontains=search_query) |
            Q(followup__department__name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # 제품 검색 (별도 필드로 분리)
    if product_search:
        schedules = schedules.filter(
            Q(delivery_items_set__product__product_code__icontains=product_search) |
            Q(delivery_items_set__product__description__icontains=product_search)
        ).distinct()
    
    # 담당자 필터링
    user_filter = request.GET.get('user')
    if user_filter:
        schedules = schedules.filter(user_id=user_filter)
    
    # 날짜 범위 필터링
    date_from = request.GET.get('date_from') or request.GET.get('start_date')
    date_to = request.GET.get('date_to') or request.GET.get('end_date')
    
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
    product_filter = request.GET.get('product')  # 제품 필터 추가
    
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
    quote_count = activity_count_queryset.filter(activity_type='quote').count()  # 견적 카운트 추가
    delivery_count = activity_count_queryset.filter(activity_type='delivery').count()
    service_count = activity_count_queryset.filter(activity_type='service').count()
    
    # 두 필터 모두 적용
    if status_filter:
        schedules = schedules.filter(status=status_filter)
    
    if activity_type_filter:
        schedules = schedules.filter(activity_type=activity_type_filter)
    
    # 제품 필터 적용
    if product_filter:
        schedules = schedules.filter(
            delivery_items_set__product__product_code__icontains=product_filter
        ).distinct()
    
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
    
    # 페이지네이션 추가
    from django.core.paginator import Paginator
    paginator = Paginator(schedules, 30)  # 페이지당 30개
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'schedules': page_obj,
        'page_obj': page_obj,
        'page_title': '일정 목록',
        'status_filter': status_filter,
        'activity_type_filter': activity_type_filter,
        'total_count': total_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'activity_total_count': activity_total_count,
        'meeting_count': meeting_count,
        'quote_count': quote_count,  # 견적 카운트 추가
        'delivery_count': delivery_count,
        'service_count': service_count,
        'search_query': search_query,
        'product_search': product_search,  # 제품 검색 추가
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
    
    # 관련 히스토리에서 납품 품목 텍스트 찾기 (대체 방법)
    delivery_text = None
    delivery_amount = 0
    delivery_histories = related_histories_all.filter(
        action_type='delivery_schedule'
    ).exclude(
        delivery_items__isnull=True
    ).exclude(
        delivery_items=''
    )
    
    if delivery_histories.exists():
        latest_delivery = delivery_histories.first()
        raw_delivery_text = latest_delivery.delivery_items
        # \n을 실제 줄바꿈으로 변환
        if raw_delivery_text:
            delivery_text = raw_delivery_text.replace('\\n', '\n')
            delivery_text = raw_delivery_text.replace('\\n', '\n').replace('\\r\\n', '\n')
        
        # 납품 금액도 가져오기
        if latest_delivery.delivery_amount:
            delivery_amount = latest_delivery.delivery_amount
    
    # 이전 페이지 정보 (캘린더에서 온 경우)
    from_page = request.GET.get('from', 'list')  # 기본값은 'list'
    
    context = {
        'schedule': schedule,
        'related_histories': related_histories,
        'delivery_items': delivery_items,
        'delivery_text': delivery_text,  # 히스토리에서 가져온 납품 품목 텍스트
        'delivery_amount': delivery_amount,  # 납품 금액
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
            
            # 복수 선결제 처리 로직
            selected_prepayments_json = request.POST.get('selected_prepayments')
            prepayment_amounts_json = request.POST.get('prepayment_amounts')
            
            if selected_prepayments_json and prepayment_amounts_json:
                import json
                from reporting.models import Prepayment, PrepaymentUsage
                from decimal import Decimal
                
                try:
                    selected_prepayments = json.loads(selected_prepayments_json)
                    prepayment_amounts = json.loads(prepayment_amounts_json)
                    
                    total_prepayment_used = Decimal('0')
                    
                    # 각 선결제에 대해 차감 처리
                    for prepayment_id in selected_prepayments:
                        prepayment_id = str(prepayment_id)
                        if prepayment_id not in prepayment_amounts:
                            continue
                        
                        amount = Decimal(str(prepayment_amounts[prepayment_id]))
                        if amount <= 0:
                            continue
                        
                        try:
                            prepayment = Prepayment.objects.get(id=int(prepayment_id))
                            
                            # 선결제 잔액 확인
                            if prepayment.balance >= amount:
                                # 선결제 잔액 차감
                                prepayment.balance -= amount
                                
                                # 잔액이 0이 되면 상태를 'depleted'로 변경
                                if prepayment.balance <= 0:
                                    prepayment.status = 'depleted'
                                
                                prepayment.save()
                                
                                # PrepaymentUsage 생성
                                PrepaymentUsage.objects.create(
                                    prepayment=prepayment,
                                    schedule=schedule,
                                    product_name=f"{schedule.get_activity_type_display()}",
                                    quantity=1,
                                    amount=amount,
                                    remaining_balance=prepayment.balance,
                                    memo=f"{schedule.get_activity_type_display()} - {schedule.followup.customer_name}"
                                )
                                
                                total_prepayment_used += amount
                                messages.success(request, f'선결제 {prepayment.payer_name or "미지정"} - {amount:,}원이 차감되었습니다. (남은 잔액: {prepayment.balance:,}원)')
                            else:
                                messages.warning(request, f'선결제 {prepayment.payer_name or "미지정"}의 잔액({prepayment.balance:,}원)이 부족합니다.')
                        
                        except Prepayment.DoesNotExist:
                            messages.error(request, f'선결제 ID {prepayment_id}를 찾을 수 없습니다.')
                    
                    if total_prepayment_used > 0:
                        # Schedule의 use_prepayment 플래그 설정
                        schedule.use_prepayment = True
                        # 첫 번째 선결제를 대표로 저장 (기존 필드 호환성)
                        if selected_prepayments:
                            first_prepayment = Prepayment.objects.filter(id=int(selected_prepayments[0])).first()
                            if first_prepayment:
                                schedule.prepayment = first_prepayment
                        schedule.prepayment_amount = total_prepayment_used
                        schedule.save()
                        
                        messages.info(request, f'총 선결제 사용 금액: {total_prepayment_used:,}원')
                
                except json.JSONDecodeError:
                    messages.error(request, '선결제 데이터 형식이 올바르지 않습니다.')
                except Exception as e:
                    messages.error(request, f'선결제 처리 중 오류 발생: {str(e)}')
            
            # 품목 데이터 처리 (견적 또는 납품)
            if schedule.activity_type in ['quote', 'delivery']:
                # 품목 데이터가 있으면 저장
                has_delivery_items = any(key.startswith('delivery_items[') for key in request.POST.keys())
                if has_delivery_items:
                    created_count = save_delivery_items(request, schedule)
                    if created_count > 0:
                        messages.success(request, f'{created_count}개의 품목이 저장되었습니다.')
                
                # 납품 품목 저장 후 펀넬 예상 수주액 업데이트
                if schedule.activity_type == 'delivery' and has_delivery_items and schedule.opportunity:
                    from decimal import Decimal
                    delivery_items = schedule.delivery_items_set.all()
                    if delivery_items.exists():
                        delivery_total = sum(Decimal(str(item.total_price or 0)) for item in delivery_items)
                        if delivery_total > 0:
                            # 펀넬의 예상 수주액 업데이트
                            opportunity = schedule.opportunity
                            if not opportunity.expected_revenue or opportunity.expected_revenue == 0:
                                opportunity.expected_revenue = delivery_total
                                opportunity.save()
                                opportunity.update_revenue_amounts()
                                logger.info(f"[DELIVERY_FUNNEL] 펀넬 ID {opportunity.id}의 예상 수주액을 납품 품목 총액 {delivery_total:,}원으로 업데이트")
                            
                            # 일정의 예상 수주액도 업데이트
                            if not schedule.expected_revenue or schedule.expected_revenue == 0:
                                schedule.expected_revenue = delivery_total
                                schedule.save()
                                logger.info(f"[DELIVERY_FUNNEL] 일정 ID {schedule.id}의 예상 수주액을 납품 품목 총액 {delivery_total:,}원으로 업데이트")
                
                # 선결제 사용 시 PrepaymentUsage에 품목 정보 업데이트
                if schedule.use_prepayment:
                    from reporting.models import PrepaymentUsage, DeliveryItem
                    usages = PrepaymentUsage.objects.filter(schedule=schedule)
                    delivery_items = DeliveryItem.objects.filter(schedule=schedule).order_by('id')
                    
                    if usages.exists() and delivery_items.exists():
                        # 첫 번째 품목 정보를 첫 번째 usage에 저장
                        first_item = delivery_items.first()
                        for usage in usages:
                            usage.product_name = first_item.item_name
                            usage.quantity = first_item.quantity
                            usage.save()
                            break  # 첫 번째 usage만 업데이트
            
            # 납품 일정 생성 시 연결된 견적을 자동 완료 처리
            if schedule.activity_type == 'delivery' and schedule.opportunity:
                # 같은 opportunity를 가진 예정 상태의 견적을 모두 완료 처리
                related_quotes = Schedule.objects.filter(
                    opportunity=schedule.opportunity,
                    activity_type='quote',
                    status='scheduled'
                )
                completed_quotes = related_quotes.update(status='completed')
                if completed_quotes > 0:
                    logger.info(f"[QUOTE_AUTO_COMPLETE] 납품 생성으로 인해 {completed_quotes}개의 견적이 자동 완료 처리됨")
                    messages.info(request, f'{completed_quotes}개의 관련 견적이 자동으로 완료 처리되었습니다.')
            
            # 펀넬 관련: 서비스는 제외, 고객 미팅/납품/견적만 영업 기회 생성
            # 폼에서 선택된 opportunity가 있는지 확인
            selected_opportunity = schedule.opportunity  # 폼에서 선택한 opportunity
            should_create_or_update_opportunity = False
            
            # 기존 Opportunity 찾기 (같은 고객의 진행 중인 영업 기회)
            existing_opportunities = schedule.followup.opportunities.exclude(current_stage='lost').order_by('-created_at')
            has_existing_opportunity = existing_opportunities.exists()
            
            # Opportunity 생성/업데이트 조건 판단
            if schedule.activity_type != 'service':
                # 사용자가 특정 opportunity를 선택한 경우 (기존 OpportunityTracking 업데이트)
                if selected_opportunity:
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = True
                # 견적 일정이고 기존 opportunity가 없으면 새로 생성
                elif schedule.activity_type == 'quote' and not has_existing_opportunity:
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = False
                # 납품 일정이고 기존 opportunity가 있으면 업데이트
                elif schedule.activity_type == 'delivery' and has_existing_opportunity:
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = True
                # 납품 일정이고 기존 opportunity가 없으면 새로 생성
                elif schedule.activity_type == 'delivery' and not has_existing_opportunity:
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = False
                elif has_existing_opportunity:
                    # 기존 Opportunity가 있으면 항상 업데이트 (예상 매출액 없어도 가능)
                    should_create_or_update_opportunity = True
                elif schedule.expected_revenue and schedule.expected_revenue > 0:
                    # 기존 Opportunity가 없으면 예상 매출액이 있을 때만 생성
                    should_create_or_update_opportunity = True
            
            if should_create_or_update_opportunity:
                
                # 이미 OpportunityTracking이 있는지 확인 (견적은 제외)
                # 이미 OpportunityTracking이 있는지 확인 (견적은 제외)
                if has_existing_opportunity:
                    # 사용자가 선택한 opportunity 우선, 없으면 가장 최근 것
                    if selected_opportunity:
                        opportunity = selected_opportunity
                    else:
                        opportunity = existing_opportunities.first()
                    
                    # 구매 확정 시 클로징 단계로 전환
                    if schedule.purchase_confirmed and opportunity.current_stage != 'closing':
                        opportunity.update_stage('closing')
                    
                    # 취소된 일정인 경우 실주 단계로 전환
                    elif schedule.status == 'cancelled' and opportunity.current_stage != 'lost':
                        opportunity.update_stage('lost')
                    
                    # 납품 예정인 경우 closing 단계로 전환 (won/lost 에서도 전환)
                    elif schedule.activity_type == 'delivery' and schedule.status == 'scheduled' and opportunity.current_stage != 'closing':
                        opportunity.update_stage('closing')
                    
                    # 납품 완료인 경우 won 단계로 전환
                    elif schedule.activity_type == 'delivery' and schedule.status == 'completed' and opportunity.current_stage != 'won':
                        opportunity.update_stage('won')
                    
                    # 견적 후 미팅 일정인 경우 협상 단계로 전환
                    elif schedule.activity_type == 'customer_meeting' and opportunity.current_stage == 'quote':
                        opportunity.update_stage('negotiation')
                    
                    # 견적 일정인 경우 quote 단계로 전환 필요
                    elif schedule.activity_type == 'quote' and opportunity.current_stage != 'quote':
                        opportunity.update_stage('quote')
                    
                    # 기존 것이 있으면 업데이트 (값이 있을 때만)
                    # 값이 없으면 기존 opportunity 값 유지
                    if schedule.expected_revenue:
                        opportunity.expected_revenue = schedule.expected_revenue
                    elif not opportunity.expected_revenue and schedule.activity_type == 'delivery':
                        # 납품 일정이고 예상 수주액이 없으면 납품 품목에서 계산
                        from decimal import Decimal
                        delivery_total = Decimal('0')
                        
                        # 저장된 납품 품목들에서 총액 계산
                        delivery_items = schedule.delivery_items_set.all()
                        if delivery_items.exists():
                            delivery_total = sum(Decimal(str(item.total_price or 0)) for item in delivery_items)
                        
                        if delivery_total > 0:
                            opportunity.expected_revenue = delivery_total
                            schedule.expected_revenue = delivery_total
                        elif not opportunity.expected_revenue:
                            # opportunity에도 값이 없으면 schedule에 opportunity 값 복사
                            schedule.expected_revenue = opportunity.expected_revenue
                    elif not opportunity.expected_revenue:
                        # opportunity에도 값이 없으면 schedule에 opportunity 값 복사
                        schedule.expected_revenue = opportunity.expected_revenue
                    
                    if schedule.probability is not None:
                        opportunity.probability = schedule.probability
                    elif opportunity.probability:
                        # schedule에 값이 없으면 opportunity 값 복사
                        schedule.probability = opportunity.probability
                    
                    if schedule.expected_close_date:
                        opportunity.expected_close_date = schedule.expected_close_date
                    elif opportunity.expected_close_date:
                        # schedule에 값이 없으면 opportunity 값 복사
                        schedule.expected_close_date = opportunity.expected_close_date
                    
                    opportunity.save()
                    
                    # 수주 금액 업데이트
                    opportunity.update_revenue_amounts()
                    
                    # 기존 Opportunity를 Schedule과 연결
                    schedule.opportunity = opportunity
                    schedule.save()
                    
                else:
                    # 없으면 새로 생성
                    # 초기 단계 결정:
                    # 1. 예정됨(scheduled) + 납품: closing (클로징) - 납품 예정
                    # 2. 완료됨(completed) + 고객 미팅: contact (컨택) - 미팅 완료
                    # 3. 완료됨(completed) + 납품: won (수주) - 납품 완료
                    if schedule.status == 'scheduled':
                        # 예정 단계
                        if schedule.activity_type == 'quote':
                            initial_stage = 'quote'  # 견적 제출 예정
                        elif schedule.activity_type == 'delivery':
                            initial_stage = 'closing'  # 납품 예정 = 클로징
                        else:
                            initial_stage = 'lead'
                    elif schedule.status == 'completed':
                        # 완료 단계
                        if schedule.activity_type == 'customer_meeting':
                            initial_stage = 'contact'  # 미팅 완료
                        elif schedule.activity_type == 'quote':
                            initial_stage = 'quote'  # 견적 제출 완료
                        elif schedule.activity_type == 'delivery':
                            initial_stage = 'won'  # 납품 완료 = 수주
                        else:
                            initial_stage = 'lead'  # 기본값
                    else:
                        # 취소됨 등 기타 상태
                        initial_stage = 'lead'  # 기본값
                    
                    # 영업 기회 제목 생성 (일정 유형 기반)
                    activity_type_names = {
                        'customer_meeting': '고객 미팅',
                        'quote': '견적',
                        'delivery': '납품',
                        'service': '서비스'
                    }
                    opportunity_title = f"{activity_type_names.get(schedule.activity_type, '영업 기회')} - {schedule.visit_date.strftime('%m/%d')}"
                    
                    # OpportunityTracking 생성
                    from datetime import date
                    from decimal import Decimal
                    opportunity = OpportunityTracking.objects.create(
                        followup=schedule.followup,
                        title=opportunity_title,
                        current_stage=initial_stage,
                        expected_revenue=schedule.expected_revenue or Decimal('0'),
                        probability=schedule.probability or 50,  # 기본값 50%
                        expected_close_date=schedule.expected_close_date or schedule.visit_date,
                        stage_history=[{
                            'stage': initial_stage,
                            'entered': date.today().isoformat(),
                            'exited': None,
                            'note': f'일정 생성으로 자동 생성 (일정 ID: {schedule.id})'
                        }]
                    )
                    
                    # Schedule과 연결
                    schedule.opportunity = opportunity
                    schedule.save()
                    
                    # 수주 금액 업데이트
                    opportunity.update_revenue_amounts()
                
                messages.success(request, f'일정이 성공적으로 생성되었습니다. 영업 기회도 함께 생성되었습니다.')
            else:
                messages.success(request, '일정이 성공적으로 생성되었습니다.')
            
            # 일정 캘린더로 리다이렉트 (모달이 자동으로 열리도록 schedule_id 전달)
            return redirect(f"{reverse('reporting:schedule_calendar')}?schedule_id={schedule.pk}")
        else:
            messages.error(request, '입력 정보를 확인해주세요.')
    else:
        # URL 파라미터에서 날짜 가져오기
        selected_date = request.GET.get('date')
        followup_id = request.GET.get('followup')
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
        
        # 팔로우업 ID가 있으면 기존 펀넬 정보 가져오기
        if followup_id:
            try:
                followup = FollowUp.objects.get(pk=followup_id)
                # 해당 팔로우업에 진행 중인 OpportunityTracking이 있는지 확인
                latest_opportunity = followup.opportunities.exclude(current_stage='lost').order_by('-created_at').first()
                if latest_opportunity:
                    initial_data['expected_revenue'] = latest_opportunity.expected_revenue
                    initial_data['probability'] = latest_opportunity.probability
                    initial_data['expected_close_date'] = latest_opportunity.expected_close_date
                    initial_data['followup'] = followup
                    messages.info(request, f'기존 펀넬 정보를 불러왔습니다. (예상 매출: {latest_opportunity.expected_revenue:,}원)')
            except FollowUp.DoesNotExist:
                pass
        
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
    from reporting.models import OpportunityTracking, FunnelStage
    
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, schedule.user):
        messages.error(request, '수정 권한이 없습니다. Manager는 읽기 전용입니다.')
        return redirect('reporting:schedule_list')
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule, user=request.user, request=request)
        if form.is_valid():
            updated_schedule = form.save()
            
            # 복수 선결제 처리 로직 (수정 시에도 적용)
            selected_prepayments_json = request.POST.get('selected_prepayments')
            prepayment_amounts_json = request.POST.get('prepayment_amounts')
            
            if selected_prepayments_json and prepayment_amounts_json:
                import json
                from reporting.models import Prepayment, PrepaymentUsage
                from decimal import Decimal
                
                try:
                    # 기존 선결제 사용 내역 복구 (수정 전 상태로 롤백)
                    existing_usages = PrepaymentUsage.objects.filter(schedule=updated_schedule)
                    for usage in existing_usages:
                        # 선결제 잔액 복구
                        prepayment = usage.prepayment
                        prepayment.balance += usage.amount
                        if prepayment.status == 'depleted' and prepayment.balance > 0:
                            prepayment.status = 'active'
                        prepayment.save()
                    
                    # 기존 사용 내역 삭제
                    existing_usages.delete()
                    
                    # 새로운 선결제 적용
                    selected_prepayments = json.loads(selected_prepayments_json)
                    prepayment_amounts = json.loads(prepayment_amounts_json)
                    
                    total_prepayment_used = Decimal('0')
                    
                    for prepayment_id in selected_prepayments:
                        prepayment_id = str(prepayment_id)
                        if prepayment_id not in prepayment_amounts:
                            continue
                        
                        amount = Decimal(str(prepayment_amounts[prepayment_id]))
                        if amount <= 0:
                            continue
                        
                        try:
                            prepayment = Prepayment.objects.get(id=int(prepayment_id))
                            
                            if prepayment.balance >= amount:
                                prepayment.balance -= amount
                                
                                if prepayment.balance <= 0:
                                    prepayment.status = 'depleted'
                                
                                prepayment.save()
                                
                                PrepaymentUsage.objects.create(
                                    prepayment=prepayment,
                                    schedule=updated_schedule,
                                    product_name=f"{updated_schedule.get_activity_type_display()}",
                                    quantity=1,
                                    amount=amount,
                                    remaining_balance=prepayment.balance,
                                    memo=f"{updated_schedule.get_activity_type_display()} - {updated_schedule.followup.customer_name}"
                                )
                                
                                total_prepayment_used += amount
                                messages.success(request, f'선결제 {prepayment.payer_name or "미지정"} - {amount:,}원이 차감되었습니다.')
                            else:
                                messages.warning(request, f'선결제 {prepayment.payer_name or "미지정"}의 잔액({prepayment.balance:,}원)이 부족합니다.')
                        
                        except Prepayment.DoesNotExist:
                            messages.error(request, f'선결제 ID {prepayment_id}를 찾을 수 없습니다.')
                    
                    if total_prepayment_used > 0:
                        updated_schedule.use_prepayment = True
                        if selected_prepayments:
                            first_prepayment = Prepayment.objects.filter(id=int(selected_prepayments[0])).first()
                            if first_prepayment:
                                updated_schedule.prepayment = first_prepayment
                        updated_schedule.prepayment_amount = total_prepayment_used
                        updated_schedule.save()
                        
                        messages.info(request, f'총 선결제 사용 금액: {total_prepayment_used:,}원')
                
                except json.JSONDecodeError:
                    messages.error(request, '선결제 데이터 형식이 올바르지 않습니다.')
                except Exception as e:
                    messages.error(request, f'선결제 처리 중 오류 발생: {str(e)}')
            
            # 펀넬 관련: 서비스는 제외, 고객 미팅/납품/견적만 영업 기회 생성/업데이트
            # 기존 OpportunityTracking이 있으면 해당 정보를 활용
            should_create_or_update_opportunity = False
            
            # 기존 Opportunity가 있는지 먼저 확인
            existing_opportunity = None
            has_existing_opportunity = False
            # 우선 원본 schedule에 직접 연결된 opportunity가 있는지 확인 (updated_schedule이 아닌 schedule 사용)
            if getattr(schedule, 'opportunity', None):
                existing_opportunity = schedule.opportunity
                has_existing_opportunity = True
            else:
                # FollowUp에 연결된 OpportunityTracking 중 진행 중인 항목 조회 (lost 제외)
                existing_opportunity = OpportunityTracking.objects.filter(
                    followup=updated_schedule.followup
                ).exclude(current_stage='lost').order_by('-created_at').first()
                has_existing_opportunity = existing_opportunity is not None
            
            # Opportunity 생성/업데이트 조건 판단
            if updated_schedule.activity_type != 'service':
                # 견적 일정은 항상 새로운 영업 기회 생성
                if updated_schedule.activity_type == 'quote':
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = False  # 강제로 새로 생성
                # 납품 완료이면서 기존 opportunity가 없는 경우만 새로 생성
                elif updated_schedule.activity_type == 'delivery' and updated_schedule.status == 'completed' and not has_existing_opportunity:
                    should_create_or_update_opportunity = True
                    has_existing_opportunity = False  # 강제로 새로 생성
                elif has_existing_opportunity:
                    # 기존 Opportunity가 있으면 항상 업데이트 (예상 매출액 없어도 가능)
                    should_create_or_update_opportunity = True
                    should_create_or_update_opportunity = True
                elif updated_schedule.expected_revenue and updated_schedule.expected_revenue > 0:
                    # 기존 Opportunity가 없으면 예상 매출액이 있을 때만 생성
                    should_create_or_update_opportunity = True
                elif updated_schedule.activity_type == 'delivery':
                    # 납품 예정 일정은 펀넬 생성 (납품 품목에서 금액 계산 가능)
                    should_create_or_update_opportunity = True
            
            if should_create_or_update_opportunity:
                # 기존 Opportunity가 있으면 그것을 사용하고, 없으면 새로 생성
                if has_existing_opportunity and existing_opportunity:
                    opportunity = existing_opportunity
                    
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"[SCHEDULE_UPDATE_DEBUG] 일정 ID: {updated_schedule.id}, activity_type: {updated_schedule.activity_type}, status: {updated_schedule.status}")
                    logger.info(f"[SCHEDULE_UPDATE_DEBUG] 현재 opportunity ID: {opportunity.id}, current_stage: {opportunity.current_stage}")
                    
                    # 구매 확정 시 클로징 단계로 전환
                    if updated_schedule.purchase_confirmed and opportunity.current_stage != 'closing':
                        logger.info(f"[STAGE_UPDATE] 구매 확정 → closing")
                        opportunity.update_stage('closing')
                    
                    # 취소된 일정인 경우 실주 단계로 전환
                    elif updated_schedule.status == 'cancelled' and opportunity.current_stage != 'lost':
                        logger.info(f"[STAGE_UPDATE] 취소됨 → lost")
                        opportunity.update_stage('lost')
                    
                    # 납품 예정인 경우 closing 단계로 전환 (won/lost 에서도 전환)
                    elif updated_schedule.activity_type == 'delivery' and updated_schedule.status == 'scheduled' and opportunity.current_stage != 'closing':
                        logger.info(f"[STAGE_UPDATE] 납품 예정 (현재: {opportunity.current_stage}) → closing")
                        opportunity.update_stage('closing')
                    
                    # 납품 완료인 경우 won 단계로 전환
                    elif updated_schedule.activity_type == 'delivery' and updated_schedule.status == 'completed' and opportunity.current_stage != 'won':
                        logger.info(f"[STAGE_UPDATE] 납품 완료 (현재: {opportunity.current_stage}) → won")
                        opportunity.update_stage('won')
                    
                    # 견적 후 미팅 일정인 경우 협상 단계로 전환
                    elif updated_schedule.activity_type == 'customer_meeting' and opportunity.current_stage == 'quote':
                        logger.info(f"[STAGE_UPDATE] 견적 후 미팅 → negotiation")
                        opportunity.update_stage('negotiation')
                    
                    # 견적 일정인 경우 quote 단계로 전환 필요
                    elif updated_schedule.activity_type == 'quote' and opportunity.current_stage != 'quote':
                        logger.info(f"[STAGE_UPDATE] 견적 일정 → quote")
                        opportunity.update_stage('quote')
                    else:
                        logger.info(f"[STAGE_UPDATE] 단계 전환 조건 미충족 - 단계 유지: {opportunity.current_stage}")
                    
                    logger.info(f"[SCHEDULE_UPDATE_DEBUG] 업데이트 후 opportunity.current_stage: {opportunity.current_stage}")
                    
                    # 기존 것이 있으면 업데이트 (값이 있을 때만)
                    # 값이 없으면 기존 opportunity 값 유지
                    if updated_schedule.expected_revenue:
                        opportunity.expected_revenue = updated_schedule.expected_revenue
                    elif not opportunity.expected_revenue:
                        # opportunity에도 값이 없으면 schedule에 opportunity 값 복사
                        updated_schedule.expected_revenue = opportunity.expected_revenue
                    
                    if updated_schedule.probability is not None:
                        opportunity.probability = updated_schedule.probability
                    elif opportunity.probability:
                        # schedule에 값이 없으면 opportunity 값 복사
                        updated_schedule.probability = opportunity.probability
                    
                    if updated_schedule.expected_close_date:
                        opportunity.expected_close_date = updated_schedule.expected_close_date
                    elif opportunity.expected_close_date:
                        # schedule에 값이 없으면 opportunity 값 복사
                        updated_schedule.expected_close_date = opportunity.expected_close_date
                    
                    # 일정 날짜가 변경되었으면 stage_entry_date도 업데이트
                    if updated_schedule.visit_date != schedule.visit_date:
                        opportunity.stage_entry_date = updated_schedule.visit_date
                        
                        # stage_history의 가장 최근 항목도 업데이트
                        if opportunity.stage_history:
                            for history in reversed(opportunity.stage_history):
                                if not history.get('exited'):
                                    history['entered'] = updated_schedule.visit_date.isoformat()
                                    break
                    
                    opportunity.save()
                    
                    # 수주/실주 금액 업데이트
                    opportunity.update_revenue_amounts()
                    
                    # Schedule과 연결
                    updated_schedule.opportunity = opportunity
                    updated_schedule.save()
                else:
                    # 없으면 새로 생성
                    if updated_schedule.status == 'scheduled':
                        if updated_schedule.activity_type == 'quote':
                            initial_stage = 'quote'
                        elif updated_schedule.activity_type == 'delivery':
                            initial_stage = 'closing'  # 납품 예정 = 클로징
                        else:
                            initial_stage = 'lead'
                    elif updated_schedule.status == 'completed':
                        if updated_schedule.activity_type == 'customer_meeting':
                            initial_stage = 'contact'
                        elif updated_schedule.activity_type == 'quote':
                            initial_stage = 'quote'
                        elif updated_schedule.activity_type == 'delivery':
                            initial_stage = 'won'  # 납품 완료 = 수주
                        else:
                            initial_stage = 'lead'
                    else:
                        initial_stage = 'lead'
                    
                    # OpportunityTracking 생성
                    from datetime import date
                    from decimal import Decimal
                    opportunity = OpportunityTracking.objects.create(
                        followup=updated_schedule.followup,
                        current_stage=initial_stage,
                        expected_revenue=updated_schedule.expected_revenue or Decimal('0'),
                        probability=updated_schedule.probability or 50,
                        expected_close_date=updated_schedule.expected_close_date or updated_schedule.visit_date,
                        stage_history=[{
                            'stage': initial_stage,
                            'entered': date.today().isoformat(),
                            'exited': None,
                            'note': f'일정 수정으로 자동 생성 (일정 ID: {updated_schedule.id})'
                        }]
                    )
                    
                    # Schedule과 연결
                    updated_schedule.opportunity = opportunity
                    updated_schedule.save()
                    
                    # 수주/실주 금액 업데이트
                    opportunity.update_revenue_amounts()
            
            # 납품 품목 데이터가 있으면 저장
            has_delivery_items = any(key.startswith('delivery_items[') for key in request.POST.keys())
            if has_delivery_items:
                created_count = save_delivery_items(request, updated_schedule)
                if created_count > 0:
                    messages.success(request, f'{created_count}개의 품목이 저장되었습니다.')
            
            # 선결제 사용 시 PrepaymentUsage에 품목 정보 업데이트
            if updated_schedule.use_prepayment:
                from reporting.models import PrepaymentUsage, DeliveryItem
                usages = PrepaymentUsage.objects.filter(schedule=updated_schedule)
                delivery_items = DeliveryItem.objects.filter(schedule=updated_schedule).order_by('id')
                
                if usages.exists() and delivery_items.exists():
                    # 첫 번째 품목 정보를 모든 usage에 저장
                    first_item = delivery_items.first()
                    for usage in usages:
                        usage.product_name = first_item.item_name
                        usage.quantity = first_item.quantity
                        usage.save()

            
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
    
    if delivery_items.exists():
        delivery_text_parts = []
        total_amount = 0
        
        for item in delivery_items:
            # VAT 포함 총액 계산 (DeliveryItem의 save()에서 자동 계산됨)
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
                raw_text = latest_delivery.delivery_items
                delivery_text = raw_text.replace('\\n', '\n')
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
            
            # OpportunityTracking 저장 (삭제 전 저장)
            opportunity = schedule.opportunity  # followup.opportunity → schedule.opportunity
            
            # 선결제 사용 내역 롤백 (선결제 잔액 복구)
            prepayment_usages = PrepaymentUsage.objects.filter(schedule=schedule)
            if prepayment_usages.exists():
                for usage in prepayment_usages:
                    # 선결제 잔액 복구
                    prepayment = usage.prepayment
                    old_balance = prepayment.balance
                    prepayment.balance += usage.amount
                    
                    # 잔액이 0원에서 복구되면 상태를 'active'로 변경
                    if old_balance == 0 and prepayment.balance > 0:
                        prepayment.status = 'active'
                    
                    prepayment.save()
                
                # 사용 내역 삭제
                prepayment_usages.delete()
            
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
            
            # OpportunityTracking 처리
            if opportunity:
                try:
                    # DB를 새로고침하여 삭제된 일정이 제외된 상태로 가져오기
                    opportunity.refresh_from_db()
                    
                    # 삭제된 일정 외에 다른 일정이 남아있는지 확인
                    remaining_schedules = opportunity.schedules.all().order_by('-visit_date', '-id')
                    remaining_count = remaining_schedules.count()
                    
                    if remaining_count == 0:
                        # 남은 일정이 없으면 OpportunityTracking도 삭제
                        opportunity_id = opportunity.id
                        opportunity.delete()
                    else:
                        # 남은 일정이 있으면 가장 최근 일정을 기준으로 펀넬 단계 재조정
                        latest_schedule = remaining_schedules.first()
                        
                        # 가장 최근 일정의 유형에 따라 단계 결정
                        new_stage = None
                        if latest_schedule.activity_type == 'delivery':
                            new_stage = 'won'
                        elif latest_schedule.activity_type == 'quote':
                            new_stage = 'quote'
                        elif latest_schedule.activity_type == 'customer_meeting':
                            # 견적 후 미팅인지 확인
                            has_quote = remaining_schedules.filter(activity_type='quote').exists()
                            new_stage = 'negotiation' if has_quote else 'contact'
                        else:
                            new_stage = 'lead'
                        
                        # 단계가 변경되어야 하는 경우
                        if new_stage and new_stage != opportunity.current_stage:
                            opportunity.update_stage(new_stage)
                        
                        # 수주 금액 업데이트
                        old_backlog = opportunity.backlog_amount
                        opportunity.update_revenue_amounts()
                        opportunity.backlog_amount = old_backlog - schedule_revenue
                        opportunity.save()
                except Exception as e:
                    logger.error(f"OpportunityTracking 처리 중 오류: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # AJAX 요청 감지 - X-Requested-With 헤더 확인
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax:
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
def schedule_update_funnel(request, pk):
    """일정의 펀넬 정보 업데이트 (AJAX)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"펀넬 정보 업데이트 요청 - 사용자: {request.user.username}, 일정 ID: {pk}")
        
        schedule = get_object_or_404(Schedule, pk=pk)
        
        # 권한 체크
        if not can_modify_user_data(request.user, schedule.user):
            logger.warning(f"권한 없음 - 요청자: {request.user.username}, 일정 소유자: {schedule.user.username}")
            return JsonResponse({'success': False, 'error': '수정 권한이 없습니다.'}, status=403)
        
        if request.method == 'POST':
            # 펀넬 필드 업데이트
            expected_revenue = request.POST.get('expected_revenue', '').strip()
            probability = request.POST.get('probability', '').strip()
            expected_close_date = request.POST.get('expected_close_date', '').strip()
            
            # Schedule 업데이트
            from decimal import Decimal
            
            if expected_revenue:
                try:
                    schedule.expected_revenue = Decimal(expected_revenue)
                except (ValueError, TypeError) as e:
                    logger.error(f"예상매출 변환 오류: {e}")
                    schedule.expected_revenue = Decimal('0')
            else:
                schedule.expected_revenue = Decimal('0')
                
            if probability:
                try:
                    schedule.probability = int(probability)
                except (ValueError, TypeError) as e:
                    logger.error(f"확률 변환 오류: {e}")
                    schedule.probability = 0
            else:
                schedule.probability = 0
                
            if expected_close_date:
                try:
                    from datetime import datetime
                    schedule.expected_close_date = datetime.strptime(expected_close_date, '%Y-%m-%d').date()
                except (ValueError, TypeError) as e:
                    logger.error(f"날짜 변환 오류: {e}")
                    schedule.expected_close_date = None
            else:
                schedule.expected_close_date = None
            
            logger.info(f"변환된 값 - 예상매출: {schedule.expected_revenue}, 확률: {schedule.probability}, 마감일: {schedule.expected_close_date}")
            schedule.save()
            logger.info(f"일정 {pk} 펀넬 정보 업데이트 완료")
            
            # OpportunityTracking 생성 또는 업데이트
            if schedule.activity_type != 'service':  # 서비스 일정은 제외
                from .models import OpportunityTracking
                from datetime import date
                
                # OpportunityTracking이 없으면 생성
                if not schedule.opportunity:
                    logger.info(f"OpportunityTracking 없음 - 새로 생성")
                    
                    # 일정 타입에 따른 초기 단계 결정
                    if schedule.activity_type == 'customer_meeting':
                        initial_stage = 'lead'
                    elif schedule.activity_type == 'quote':
                        initial_stage = 'quote'
                    elif schedule.activity_type == 'delivery':
                        initial_stage = 'closing'
                    else:
                        initial_stage = 'contact'
                    
                    opportunity = OpportunityTracking.objects.create(
                        followup=schedule.followup,
                        current_stage=initial_stage,
                        stage_entry_date=date.today(),
                        expected_revenue=schedule.expected_revenue or Decimal('0'),
                        probability=schedule.probability or 50,
                        weighted_revenue=schedule.expected_revenue * (schedule.probability or 50) / 100 if schedule.expected_revenue else Decimal('0'),
                        expected_close_date=schedule.expected_close_date,
                        stage_history=[{
                            'stage': initial_stage,
                            'entered': date.today().isoformat(),
                            'exited': None,
                            'note': '일정 수정 시 펀넬 정보 입력으로 생성'
                        }]
                    )
                    
                    # Schedule과 연결
                    schedule.opportunity = opportunity
                    schedule.save(update_fields=['opportunity'])
                    logger.info(f"OpportunityTracking {opportunity.id} 생성 및 연결 완료")
                    
                else:
                    # OpportunityTracking이 있으면 업데이트
                    logger.info(f"OpportunityTracking {schedule.opportunity.id} 업데이트")
                    opportunity = schedule.opportunity
                    
                    # 예상 매출액 업데이트
                    if schedule.expected_revenue:
                        opportunity.expected_revenue = schedule.expected_revenue
                        # 가중치 매출액도 업데이트
                        probability = schedule.probability if schedule.probability is not None else opportunity.probability or 50
                        opportunity.weighted_revenue = schedule.expected_revenue * probability / 100
                    
                    # 확률 업데이트
                    if schedule.probability is not None:
                        opportunity.probability = schedule.probability
                        # 가중치 매출액 재계산
                        if opportunity.expected_revenue:
                            opportunity.weighted_revenue = opportunity.expected_revenue * schedule.probability / 100
                    
                    # 예상 계약일 업데이트
                    if schedule.expected_close_date:
                        opportunity.expected_close_date = schedule.expected_close_date
                    
                    opportunity.save()
                    logger.info(f"OpportunityTracking {opportunity.id} 업데이트 완료")
            
            return JsonResponse({
                'success': True,
                'message': '펀넬 정보가 업데이트되었습니다.'
            })
        else:
            return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'}, status=405)
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        logger.error(f"펀넬 정보 업데이트 중 예외 발생:")
        logger.error(f"오류 메시지: {error_msg}")
        logger.error(f"스택 트레이스:\n{error_traceback}")
        
        return JsonResponse({
            'success': False,
            'error': f'펀넬 정보 업데이트 중 오류가 발생했습니다: {error_msg}'
        }, status=500)

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
            # 납품 품목 저장
            created_count = save_delivery_items(request, schedule)
            
            if created_count == 0:
                messages.warning(request, '저장된 품목이 없습니다. 품목명과 수량을 모두 입력했는지 확인해주세요.')
            
            # 관련된 History들의 delivery_items 텍스트도 업데이트
            related_histories = schedule.histories.filter(action_type='delivery_schedule')
            
            # 새로 저장된 DeliveryItem들을 텍스트로 변환
            delivery_items = schedule.delivery_items_set.all()
            
            if delivery_items.exists():
                delivery_lines = []
                total_delivery_amount = 0  # 총 납품 금액 계산
                
                for item in delivery_items:
                    if item.unit_price:
                        # 부가세 포함 총액 계산 (단가 * 수량 * 1.1)
                        total_amount = int(float(item.unit_price) * item.quantity * 1.1)
                        total_delivery_amount += total_amount
                        delivery_lines.append(f"{item.item_name}: {item.quantity}개 ({total_amount:,}원)")
                    else:
                        delivery_lines.append(f"{item.item_name}: {item.quantity}개")
                
                delivery_text = '\n'.join(delivery_lines)
                
                # 관련 History가 있으면 업데이트, 없으면 새로 생성
                if related_histories.exists():
                    # 기존 History 업데이트
                    for history in related_histories:
                        history.delivery_items = delivery_text
                        if total_delivery_amount > 0:
                            history.delivery_amount = total_delivery_amount
                        history.save(update_fields=['delivery_items', 'delivery_amount'])
                else:
                    # 새로운 History 생성
                    from .models import History
                    history = History.objects.create(
                        schedule=schedule,
                        user=request.user,
                        action_type='delivery_schedule',
                        delivery_items=delivery_text,
                        delivery_amount=total_delivery_amount if total_delivery_amount > 0 else None,
                        memo=f'납품 품목 {created_count}개 추가'
                    )
            
            messages.success(request, '납품 품목이 성공적으로 업데이트되었습니다.')
        except Exception as e:
            logger.error(f'납품 품목 업데이트 중 오류: {str(e)}', exc_info=True)
            messages.error(request, f'납품 품목 업데이트 중 오류가 발생했습니다: {str(e)}')
        
        return redirect('reporting:schedule_detail', pk=pk)
    
    # GET 요청은 허용하지 않음
    return redirect('reporting:schedule_detail', pk=pk)

@login_required
def schedule_calendar_view(request):
    """일정 캘린더 뷰 (권한 기반 필터링 적용)"""
    user_profile = get_user_profile(request.user)
    
    # 매니저용 실무자 필터
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # URL 파라미터로 특정 사용자 필터링 (기존 호환성)
    user_filter = request.GET.get('user') or selected_user_id
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
        'view_all': view_all,
        'selected_user_id': selected_user_id,
    }
    return render(request, 'reporting/schedule_calendar.html', context)

@login_required
def schedule_api_view(request):
    """일정 데이터 API (JSON 응답) - 권한 기반 필터링 적용"""
    try:
        user_profile = get_user_profile(request.user)
        
        # 매니저용 실무자 필터 (세션 기반)
        view_all = request.GET.get('view_all') == 'true'
        
        # 전체 팀원 선택 시 세션 초기화
        if view_all and user_profile.can_view_all_users():
            if 'selected_user_id' in request.session:
                del request.session['selected_user_id']
            user_filter = None
        else:
            user_filter = request.GET.get('user')
            if not user_filter:
                user_filter = request.session.get('selected_user_id')
            
            if user_filter and user_profile.can_view_all_users():
                request.session['selected_user_id'] = str(user_filter)
        
        # 권한에 따른 데이터 필터링
        if user_profile.can_view_all_users():
            # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
            accessible_users = get_accessible_users(request.user)
            
            # 매니저가 특정 실무자를 선택한 경우
            if user_filter and not view_all:
                try:
                    selected_user = accessible_users.get(id=user_filter)
                    schedules = Schedule.objects.filter(user=selected_user)
                except User.DoesNotExist:
                    schedules = Schedule.objects.filter(user__in=accessible_users)
            else:
                schedules = Schedule.objects.filter(user__in=accessible_users)
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
                # 펀넬 관련 필드 추가
                'expected_revenue': float(schedule.expected_revenue) if schedule.expected_revenue else 0,
                'probability': schedule.probability if schedule.probability is not None else 0,
                'expected_close_date': schedule.expected_close_date.strftime('%Y-%m-%d') if schedule.expected_close_date else '',
            }
            
            # 견적 또는 납품 일정인 경우 품목 정보 추가
            if schedule.activity_type in ['delivery', 'quote']:
                delivery_items_text = ''
                delivery_amount = 0
                has_schedule_items = False  # 스케줄에 직접 등록된 품목이 있는지 여부
                
                # Schedule에 직접 연결된 DeliveryItem이 있는지 먼저 확인
                schedule_delivery_items = schedule.delivery_items_set.all().order_by('id')
                if schedule_delivery_items.exists():
                    has_schedule_items = True
                    delivery_text_parts = []
                    total_amount = 0
                    
                    for item in schedule_delivery_items:
                        item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                        total_amount += item_total
                        text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                        delivery_text_parts.append(text_part)
                    
                    delivery_items_text = '\n'.join(delivery_text_parts)
                    delivery_amount = int(total_amount)
                else:
                    # Schedule에 직접 연결된 DeliveryItem이 없으면 History에서 찾기
                    delivery_history = schedule.histories.filter(action_type='delivery_schedule').first()
                    if delivery_history and delivery_history.delivery_items:
                        delivery_items_text = delivery_history.delivery_items.strip()
                        delivery_amount = delivery_history.delivery_amount or 0
                
                schedule_item.update({
                    'delivery_items': delivery_items_text,
                    'delivery_amount': delivery_amount,
                    'has_schedule_items': has_schedule_items,  # 품목 관리 제한용
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
    
    # 매니저용 실무자 필터 (세션 기반)
    view_all = request.GET.get('view_all') == 'true'
    
    # 전체 팀원 선택 시 세션 초기화
    if view_all and user_profile.can_view_all_users():
        if 'selected_user_id' in request.session:
            del request.session['selected_user_id']
        user_filter = None
    else:
        user_filter = request.GET.get('user')
        if not user_filter:
            user_filter = request.session.get('selected_user_id')
        
        if user_filter and user_profile.can_view_all_users():
            request.session['selected_user_id'] = str(user_filter)
    
    # 권한에 따른 데이터 필터링 (매니저 메모 제외)
    if user_profile.can_view_all_users():
        # Admin이나 Manager는 접근 가능한 사용자의 데이터 조회
        accessible_users = get_accessible_users(request.user)
        
        # 매니저가 특정 실무자를 선택한 경우
        if user_filter and not view_all:
            try:
                selected_user = accessible_users.get(id=user_filter)
                histories = History.objects.filter(user=selected_user, parent_history__isnull=True)  # 매니저 메모 제외
            except (User.DoesNotExist, ValueError):
                histories = History.objects.filter(user__in=accessible_users, parent_history__isnull=True)  # 매니저 메모 제외
        else:
            # 전체보기 또는 선택 안 함
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
    quote_count = base_queryset_for_counts.filter(action_type='quote').count()  # 견적 카운트 추가
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
    
    # 페이지네이션 추가
    from django.core.paginator import Paginator
    paginator = Paginator(histories, 30)  # 페이지당 30개
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'histories': page_obj,
        'page_obj': page_obj,
        'page_title': page_title,
        'action_type_filter': action_type_filter,
        'month_filter': month_filter,
        'total_count': total_count,
        'meeting_count': meeting_count,
        'quote_count': quote_count,  # 견적 카운트 추가
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
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """커스텀 로그아웃 뷰 (성공 메시지 추가)"""
    next_page = reverse_lazy('reporting:login')
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# ============ 사용자 관리 뷰들 ============

# 사용자 생성 폼 (Admin 전용)
class UserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID를 입력하세요', 'autocomplete': 'off'}),
        label='사용자 ID'
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

# 매니저용 사용자 생성 폼 (Manager 전용)
class ManagerUserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID를 입력하세요', 'autocomplete': 'off'}),
        label='사용자 ID'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label='비밀번호'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label='비밀번호 확인'
    )
    # 매니저는 실무자만 생성할 수 있음
    role = forms.CharField(
        initial='salesman',
        widget=forms.HiddenInput(),
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID를 입력하세요', 'autocomplete': 'off'}),
        label='사용자 ID'
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

# ============ 매니저용 사용자 관리 뷰들 ============

@role_required(['manager'])
def manager_user_list(request):
    """매니저가 자신의 회사 소속 사용자 목록을 볼 수 있는 뷰"""
    # 매니저의 회사 정보 확인
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.company:
        messages.error(request, '회사 정보가 없어 사용자 관리를 할 수 없습니다.')
        return redirect('reporting:main')
    
    manager_company = request.user.userprofile.company
    
    # 같은 회사의 사용자들만 조회 (매니저와 실무자만)
    users = User.objects.select_related('userprofile').filter(
        userprofile__company=manager_company,
        userprofile__role__in=['manager', 'salesman']
    ).order_by('username')
    
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
        'role_choices': [('manager', 'Manager (뷰어)'), ('salesman', 'SalesMan (실무자)')],
        'page_title': f'사용자 관리 - {manager_company.name}',
        'company_name': manager_company.name
    }
    return render(request, 'reporting/manager_user_list.html', context)

@role_required(['manager'])
def manager_user_create(request):
    """매니저가 자신의 회사에 실무자 계정을 추가하는 뷰"""
    # 매니저의 회사 정보 확인
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.company:
        messages.error(request, '회사 정보가 없어 사용자 생성을 할 수 없습니다.')
        return redirect('reporting:main')
    
    manager_company = request.user.userprofile.company
    
    if request.method == 'POST':
        form = ManagerUserCreationForm(request.POST)
        
        if form.is_valid():
            # 사용자명 중복 체크
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                form.add_error('username', f'사용자명 "{username}"은(는) 이미 사용 중입니다.')
                messages.error(request, f'사용자명 "{username}"은(는) 이미 사용 중입니다.')
                context = {
                    'form': form,
                    'page_title': f'실무자 계정 생성 - {manager_company.name}',
                    'company_name': manager_company.name
                }
                return render(request, 'reporting/manager_user_create.html', context)
            
            try:
                # 사용자 생성
                user = User.objects.create_user(
                    username=username,
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                # 사용자 프로필 생성 (매니저와 같은 회사로 자동 설정)
                UserProfile.objects.create(
                    user=user,
                    company=manager_company,  # 매니저와 같은 회사
                    role='salesman',  # 매니저는 실무자만 생성 가능
                    can_download_excel=form.cleaned_data['can_download_excel'],
                    created_by=request.user  # 생성자 기록
                )
                
                messages.success(request, f'실무자 계정 "{user.username}"이(가) {manager_company.name}에 성공적으로 생성되었습니다.')
                return redirect('reporting:manager_user_list')
            except Exception as e:
                messages.error(request, f'사용자 생성 중 오류가 발생했습니다: {str(e)}')
                context = {
                    'form': form,
                    'page_title': f'실무자 계정 생성 - {manager_company.name}',
                    'company_name': manager_company.name
                }
                return render(request, 'reporting/manager_user_create.html', context)
    else:
        form = ManagerUserCreationForm()
    
    context = {
        'form': form,
        'page_title': f'실무자 계정 생성 - {manager_company.name}',
        'company_name': manager_company.name
    }
    return render(request, 'reporting/manager_user_create.html', context)

@role_required(['manager'])
def manager_user_edit(request, user_id):
    """매니저가 자신의 회사 소속 사용자를 편집하는 뷰"""
    # 매니저의 회사 정보 확인
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.company:
        messages.error(request, '회사 정보가 없어 사용자 편집을 할 수 없습니다.')
        return redirect('reporting:main')
    
    manager_company = request.user.userprofile.company
    
    # 편집할 사용자 가져오기 (같은 회사의 매니저/실무자만)
    user = get_object_or_404(User, id=user_id, userprofile__company=manager_company, userprofile__role__in=['manager', 'salesman'])
    user_profile = get_object_or_404(UserProfile, user=user)
    
    # 자기 자신의 권한은 변경할 수 없음
    if user.id == request.user.id:
        messages.error(request, '자신의 계정 정보는 이 방법으로 수정할 수 없습니다.')
        return redirect('reporting:manager_user_list')
    
    if request.method == 'POST':
        # 매니저용 편집 폼 (역할 변경 불가)
        form_data = request.POST.copy()
        form_data['role'] = user_profile.role  # 기존 역할 유지
        
        form = UserEditForm(form_data)
        if form.is_valid():
            # 사용자명 중복 체크 (자기 자신 제외)
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, f'사용자명 "{username}"은(는) 이미 사용 중입니다.')
            else:
                # 사용자 정보 수정
                user.username = username
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                
                # 비밀번호 변경
                if form.cleaned_data['change_password'] and form.cleaned_data['password1']:
                    user.set_password(form.cleaned_data['password1'])
                
                user.save()
                
                # 엑셀 다운로드 권한만 수정 가능 (회사와 역할은 변경 불가)
                user_profile.can_download_excel = form.cleaned_data['can_download_excel']
                user_profile.save()
                
                messages.success(request, f'사용자 "{user.username}"의 정보가 성공적으로 수정되었습니다.')
                return redirect('reporting:manager_user_list')
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
        'page_title': f'사용자 편집 - {user.username}',
        'company_name': manager_company.name,
        'is_manager_edit': True  # 매니저 편집 모드 표시
    }
    return render(request, 'reporting/manager_user_edit.html', context)

@role_required(['manager'])
@never_cache
def manager_dashboard(request):
    """Manager 전용 대시보드 - dashboard_view로 리다이렉트"""
    from django.shortcuts import redirect
    
    # user_id 파라미터가 있으면 그대로 전달, 없으면 기본 대시보드로
    user_id = request.GET.get('user_id')
    if user_id:
        return redirect(f"{reverse('reporting:dashboard')}?user={user_id}")
    else:
        return redirect('reporting:dashboard')
    
    # 현재 시간
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # 데이터 필터링
    if view_all:
        # 전체보기: 모든 salesman의 데이터
        followups = FollowUp.objects.filter(user__in=target_users)
        schedules = Schedule.objects.filter(user__in=target_users)
        histories = History.objects.filter(user__in=target_users)
        histories_current_year = History.objects.filter(user__in=target_users, created_at__year=current_year)
        
        followup_count = followups.count()
        schedule_count = schedules.filter(status='scheduled').count()
        sales_record_count = histories_current_year.filter(
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
    else:
        # 특정 사용자 데이터
        followups = FollowUp.objects.filter(user=target_user)
        schedules = Schedule.objects.filter(user=target_user)
        histories = History.objects.filter(user=target_user)
        histories_current_year = History.objects.filter(user=target_user, created_at__year=current_year)
        
        followup_count = followups.count()
        schedule_count = schedules.filter(status='scheduled').count()
        sales_record_count = histories_current_year.filter(
            action_type__in=['customer_meeting', 'delivery_schedule']
        ).count()
    
    # 납품 금액 통계 (현재 연도)
    history_delivery_stats = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False
    ).aggregate(
        total_amount=Sum('delivery_amount'),
        delivery_count=Count('id')
    )
    
    if view_all:
        schedule_delivery_stats = DeliveryItem.objects.filter(
            schedule__user__in=target_users,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).exclude(
            schedule__status='cancelled'
        ).aggregate(
            total_amount=Sum('total_price'),
            delivery_count=Count('schedule', distinct=True)
        )
    else:
        schedule_delivery_stats = DeliveryItem.objects.filter(
            schedule__user=target_user,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).exclude(
            schedule__status='cancelled'
        ).aggregate(
            total_amount=Sum('total_price'),
            delivery_count=Count('schedule', distinct=True)
        )
    
    history_amount = history_delivery_stats['total_amount'] or 0
    schedule_amount = schedule_delivery_stats['total_amount'] or 0
    total_delivery_amount = history_amount + schedule_amount
    
    # 중복 제거된 납품 횟수
    history_with_schedule = histories_current_year.filter(
        action_type='delivery_schedule',
        schedule__isnull=False
    ).values_list('schedule_id', flat=True).distinct()
    
    history_without_schedule = histories_current_year.filter(
        action_type='delivery_schedule',
        schedule__isnull=True
    ).count()
    
    if view_all:
        schedules_with_delivery = DeliveryItem.objects.filter(
            schedule__user__in=target_users,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).values_list('schedule_id', flat=True).distinct()
    else:
        schedules_with_delivery = DeliveryItem.objects.filter(
            schedule__user=target_user,
            schedule__created_at__year=current_year,
            schedule__activity_type='delivery'
        ).values_list('schedule_id', flat=True).distinct()
    
    unique_schedule_ids = set(history_with_schedule) | set(schedules_with_delivery)
    delivery_count = len(unique_schedule_ids) + history_without_schedule
    
    # 활동 유형별 통계 (현재 연도)
    activity_stats = histories_current_year.exclude(action_type='memo').values('action_type').annotate(
        count=Count('id')
    ).order_by('action_type')
    
    # 서비스 통계
    service_count = histories_current_year.filter(action_type='service', service_status='completed').count()
    this_month_service_count = histories.filter(
        action_type='service',
        service_status='completed',
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    
    # 최근 활동 (5개)
    recent_activities = histories_current_year.exclude(action_type='memo').order_by('-created_at')[:5]
    
    # 월별 고객 추가 현황 (최근 6개월)
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
    monthly_customers.reverse()
    
    # 일정 완료율
    schedule_stats = schedules.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        scheduled=Count('id', filter=Q(status='scheduled'))
    )
    
    completion_rate = 0
    if schedule_stats['total'] > 0:
        completion_rate = round((schedule_stats['completed'] / schedule_stats['total']) * 100, 1)
    
    # 영업 기록 추이 (최근 14일)
    fourteen_days_ago = now - timedelta(days=14)
    daily_activities = []
    for i in range(14):
        day = fourteen_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
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
    
    # 성과 지표
    monthly_revenue = histories.filter(
        action_type='delivery_schedule',
        created_at__month=current_month,
        created_at__year=current_year,
        delivery_amount__isnull=False
    ).aggregate(total=Sum('delivery_amount'))['total'] or 0
    
    # 월별 통계 (Schedule 기준)
    schedules_current_month = schedules.filter(
        visit_date__month=current_month,
        visit_date__year=current_year
    )
    
    monthly_meetings = schedules_current_month.filter(activity_type='customer_meeting').count()
    monthly_services = schedules_current_month.filter(activity_type='service', status='completed').count()
    
    # 전환율 계산 (Schedule 기준)
    schedules_current_year = schedules.filter(visit_date__year=current_year)
    total_meetings = schedules_current_year.filter(activity_type='customer_meeting').count()
    total_deliveries = schedules_current_year.filter(activity_type='delivery', status='completed').count()
    
    # 미팅 → 납품 전환율
    conversion_rate = (total_deliveries / total_meetings * 100) if total_meetings > 0 else 0
    
    # 평균 거래 규모 (DeliveryItem 기준)
    avg_deal_size = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year.filter(activity_type='delivery')
    ).aggregate(avg=Avg('total_price'))['avg'] or 0
    
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
    
    # 고객별 납품 현황 (상위 5개)
    customer_revenue_data = histories_current_year.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False,
        followup__isnull=False
    ).values('followup__customer_name', 'followup__company').annotate(
        total_revenue=Sum('delivery_amount')
    ).order_by('-total_revenue')[:5]
    
    customer_labels = [f"{item['followup__customer_name'] or '미정'} ({item['followup__company'] or '미정'})" for item in customer_revenue_data]
    customer_amounts = [float(item['total_revenue']) for item in customer_revenue_data]
    
    # ============================================
    # 📊 새로운 7개 차트를 위한 데이터 준비 - Schedule 기준
    # ============================================
    
    # 1️⃣ 매출 및 납품 추이 (월별 납품 금액 + 건수) - Schedule 기준
    monthly_delivery_stats = {
        'labels': [],
        'amounts': [],
        'counts': []
    }
    
    for i in range(11, -1, -1):  # 최근 12개월
        target_date = now - timedelta(days=30*i)
        month_start = target_date.replace(day=1)
        if target_date.month == 12:
            month_end = target_date.replace(year=target_date.year+1, month=1, day=1)
        else:
            month_end = target_date.replace(month=target_date.month+1, day=1)
        
        month_schedules = schedules.filter(
            visit_date__gte=month_start.date(),
            visit_date__lt=month_end.date(),
            activity_type='delivery'
        )
        
        month_data = DeliveryItem.objects.filter(
            schedule__in=month_schedules
        ).aggregate(
            total=Sum('total_price'),
            count=Count('id')
        )
        
        monthly_delivery_stats['labels'].append(f"{target_date.month}월")
        monthly_delivery_stats['amounts'].append(float(month_data['total'] or 0))
        monthly_delivery_stats['counts'].append(month_data['count'] or 0)
    
    # 2️⃣ 영업 퍼널 (미팅 → 견적 제출 → 발주 예정 → 납품 완료)
    # 기준: 모두 일정(Schedule) 기반으로 집계
    schedules_current_year = schedules.filter(visit_date__year=current_year)
    
    meeting_count_mgr = schedules_current_year.filter(activity_type='customer_meeting').count()
    quote_count_mgr = schedules_current_year.filter(activity_type='quote').count()
    scheduled_delivery_count_mgr = schedules_current_year.filter(activity_type='delivery', status='scheduled').count()
    completed_delivery_count_mgr = schedules_current_year.filter(activity_type='delivery', status='completed').count()
    
    logger.info(f"[매니저 대시보드 펀넬] 선택된 사용자: {target_user.username if target_user else '전체'}")
    logger.info(f"[매니저 대시보드 펀넬] 미팅: {meeting_count_mgr}, 견적: {quote_count_mgr}, 발주예정: {scheduled_delivery_count_mgr}, 납품완료: {completed_delivery_count_mgr}")
    
    # 전환율 계산
    meeting_to_delivery_rate = (completed_delivery_count_mgr / meeting_count_mgr * 100) if meeting_count_mgr > 0 else 0
    quote_to_delivery_rate = (completed_delivery_count_mgr / quote_count_mgr * 100) if quote_count_mgr > 0 else 0
    
    sales_funnel = {
        'stages': ['미팅', '견적 제출', '발주 예정', '납품 완료'],
        'values': [
            meeting_count_mgr,
            quote_count_mgr,
            scheduled_delivery_count_mgr,
            completed_delivery_count_mgr
        ]
    }
    
    # 3️⃣ 고객사별 매출 비중 (Top 5 + 기타) - Schedule + History 기준
    # Schedule 기반 매출
    schedule_top_customers = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # History 기반 매출
    histories_current_year_with_company = histories_current_year.filter(
        followup__isnull=False,
        followup__company__isnull=False
    )
    
    history_top_customers = DeliveryItem.objects.filter(
        history__in=histories_current_year_with_company
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # 고객사별 매출 합산
    from collections import defaultdict
    company_revenue = defaultdict(float)
    
    for item in schedule_top_customers:
        company_name = item['schedule__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    for item in history_top_customers:
        company_name = item['history__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    # 상위 5개 추출
    sorted_companies = sorted(company_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
    
    customer_distribution = {
        'labels': [],
        'data': []
    }
    
    total_top5_revenue = 0
    for company_name, revenue in sorted_companies:
        customer_distribution['labels'].append(company_name)
        customer_distribution['data'].append(revenue)
        total_top5_revenue += revenue
    
    # 기타 금액 계산 - Schedule + History 합산
    schedule_total = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    history_total = DeliveryItem.objects.filter(
        history__in=histories_current_year
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    total_all_revenue = float(schedule_total) + float(history_total)
    other_revenue = total_all_revenue - total_top5_revenue
    if other_revenue > 0:
        customer_distribution['labels'].append('기타')
        customer_distribution['data'].append(other_revenue)
    
    # 4️⃣ 영업 활동 추이 (월별) - Schedule 기준
    monthly_activity_breakdown = {
        'labels': [],
        'sales': []
    }
    
    for i in range(11, -1, -1):  # 최근 12개월
        target_date = now - timedelta(days=30*i)
        month_start = target_date.replace(day=1)
        if target_date.month == 12:
            month_end = target_date.replace(year=target_date.year+1, month=1, day=1)
        else:
            month_end = target_date.replace(month=target_date.month+1, day=1)
        
        sales_count_month = schedules.filter(
            visit_date__gte=month_start.date(),
            visit_date__lt=month_end.date(),
            activity_type__in=['customer_meeting', 'delivery', 'quote']
        ).count()
        
        monthly_activity_breakdown['labels'].append(f"{target_date.month}월")
        monthly_activity_breakdown['sales'].append(sales_count_month)
    
    # 5️⃣ 개인 성과 지표 추세 (납품액, 전환율, 평균 거래 규모) - Schedule 기준
    performance_trends = {
        'labels': [],
        'delivery_amount': [],
        'conversion_rate': [],
        'avg_deal_size': []
    }
    
    for i in range(11, -1, -1):  # 최근 12개월
        target_date = now - timedelta(days=30*i)
        month_start = target_date.replace(day=1)
        if target_date.month == 12:
            month_end = target_date.replace(year=target_date.year+1, month=1, day=1)
        else:
            month_end = target_date.replace(month=target_date.month+1, day=1)
        
        # 해당 월의 일정 데이터
        month_schedules = schedules.filter(
            visit_date__gte=month_start.date(),
            visit_date__lt=month_end.date()
        )
        
        month_meetings = month_schedules.filter(activity_type='customer_meeting').count()
        month_deliveries = month_schedules.filter(activity_type='delivery', status='completed').count()
        
        # 해당 월의 DeliveryItem 통계
        month_delivery_stats = DeliveryItem.objects.filter(
            schedule__in=month_schedules.filter(activity_type='delivery')
        ).aggregate(
            total=Sum('total_price'),
            avg=Avg('total_price')
        )
        
        month_conversion = (month_deliveries / month_meetings * 100) if month_meetings > 0 else 0
        
        performance_trends['labels'].append(f"{target_date.month}월")
        performance_trends['delivery_amount'].append(float(month_delivery_stats['total'] or 0) / 1000000)  # 백만원 단위
        performance_trends['conversion_rate'].append(round(month_conversion, 1))
        performance_trends['avg_deal_size'].append(float(month_delivery_stats['avg'] or 0) / 1000000)  # 백만원 단위
    
    # 6️⃣ 고객 유형별 통계 (대학/기업/관공서) - Schedule + History 기준
    customer_type_stats = {
        'labels': ['대학', '기업', '관공서'],
        'revenue': [0, 0, 0],
        'count': [0, 0, 0]
    }
    
    # Schedule 기반 통계
    schedule_company_stats = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    for item in schedule_company_stats:
        company_name = item['schedule__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt
    
    # History 기반 통계
    history_company_stats = DeliveryItem.objects.filter(
        history__in=histories_current_year,
        history__followup__isnull=False,
        history__followup__company__isnull=False
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    for item in history_company_stats:
        company_name = item['history__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt
    
    # 7️⃣ 활동 히트맵 (현재 달) - 선택된 사용자(들)의 일정만
    daily_activity_heatmap = []
    
    # 현재 달의 첫날과 마지막 날 계산
    current_month_start = now.replace(day=1).date()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    current_month_end = (next_month - timedelta(days=1)).date()
    
    # 현재 달의 각 날짜별 활동 카운트 (선택된 사용자만)
    current_date = current_month_start
    while current_date <= current_month_end:
        day_activity_count = schedules.filter(
            visit_date=current_date
        ).count()
        
        daily_activity_heatmap.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day_of_week': current_date.weekday(),  # 0=월, 6=일
            'intensity': day_activity_count
        })
        
        current_date += timedelta(days=1)
    
    # 선결제 통계 - 등록자 본인만 (Manager도 자신이 등록한 것만)
    from decimal import Decimal
    
    prepayments = Prepayment.objects.filter(created_by=target_user)
    
    prepayment_aggregate = prepayments.aggregate(
        total_amount=Sum('amount'),
        total_balance=Sum('balance')
    )
    
    prepayment_stats = {
        'total_amount': prepayment_aggregate['total_amount'] or Decimal('0'),
        'total_balance': prepayment_aggregate['total_balance'] or Decimal('0'),
        'total_used': (prepayment_aggregate['total_amount'] or Decimal('0')) - (prepayment_aggregate['total_balance'] or Decimal('0')),
        'active_count': prepayments.filter(status='active', balance__gt=0).count(),
        'depleted_count': prepayments.filter(status='depleted').count(),
        'total_count': prepayments.count(),
    }
    
    # Context 구성
    context = {
        'page_title': f"Manager 대시보드 - {'전체보기' if view_all else target_user.username}",
        'current_year': current_year,
        'followup_count': followup_count,
        'schedule_count': schedule_count,
        'sales_record_count': sales_record_count,
        'total_delivery_amount': total_delivery_amount,
        'delivery_count': delivery_count,
        'service_count': service_count,
        'this_month_service_count': this_month_service_count,
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
        'conversion_rate': conversion_rate,
        'meeting_to_delivery_rate': meeting_to_delivery_rate,
        'quote_to_delivery_rate': quote_to_delivery_rate,
        'avg_deal_size': avg_deal_size,
        'monthly_revenue_data': json.dumps(monthly_revenue_data, cls=DjangoJSONEncoder),
        'monthly_revenue_labels': json.dumps(monthly_revenue_labels, cls=DjangoJSONEncoder),
        'customer_labels': json.dumps(customer_labels, cls=DjangoJSONEncoder),
        'customer_amounts': json.dumps(customer_amounts, cls=DjangoJSONEncoder),
        # 새로운 7개 차트 데이터
        'monthly_delivery_stats': json.dumps(monthly_delivery_stats, cls=DjangoJSONEncoder),
        'sales_funnel': json.dumps(sales_funnel, cls=DjangoJSONEncoder),
        'customer_distribution': json.dumps(customer_distribution, cls=DjangoJSONEncoder),
        'customer_type_stats': json.dumps(customer_type_stats, cls=DjangoJSONEncoder),
        'daily_activity_heatmap': json.dumps(daily_activity_heatmap, cls=DjangoJSONEncoder),
        # 선결제 통계 (실무자 대시보드와 동일한 형식)
        'prepayment_stats': prepayment_stats,
        # 관리자용 추가 정보
        'salesman_users': salesman_users,
        'selected_user': target_user,
        'view_all': view_all,
    }
    
    return render(request, 'reporting/dashboard.html', context)


@role_required(['manager'])
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
        
        # 연결된 OpportunityTracking의 날짜도 업데이트
        if schedule.opportunity:
            opportunity = schedule.opportunity
            opportunity.stage_entry_date = new_visit_date
            
            # 견적 일정이면 title도 업데이트 (날짜 변경 반영)
            if schedule.activity_type == 'quote' and opportunity.title:
                # 기존 title이 "견적 - MM/DD" 형식이면 날짜 부분 업데이트
                import re
                if re.match(r'견적 - \d{1,2}/\d{1,2}', opportunity.title):
                    opportunity.title = f"견적 - {new_visit_date.month}/{new_visit_date.day}"
            
            # stage_history의 가장 최근 항목도 업데이트
            if opportunity.stage_history:
                for history in reversed(opportunity.stage_history):
                    if not history.get('exited'):
                        history['entered'] = new_visit_date.isoformat()
                        break
            
            opportunity.save()
        
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        logger.info(f"🔍 일정 상태 업데이트 요청: ID {schedule_id}, 현재 상태: {schedule.status}")
        
        # 권한 체크: 수정 권한이 있는 경우만 상태 변경 가능 (Manager는 읽기 전용)
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
        
        new_status = request.POST.get('status')
        
        if new_status not in ['scheduled', 'completed', 'cancelled']:
            return JsonResponse({'error': '잘못된 상태값입니다.'}, status=400)
        
        # 견적 일정은 완료로 변경 불가 (취소만 가능)
        if schedule.activity_type == 'quote' and new_status == 'completed':
            return JsonResponse({
                'error': '견적 일정은 완료 상태로 변경할 수 없습니다. 견적은 취소만 가능합니다.'
            }, status=400)
        
        old_status = schedule.status
        
        # 취소 처리 시 추가 작업
        if new_status == 'cancelled' and old_status != 'cancelled':
            from datetime import date
            from reporting.models import DeliveryItem, History
            
            # 1. 납품 품목 기록은 유지 (삭제하지 않음 - 카운팅에서만 제외)
            delivery_items = DeliveryItem.objects.filter(schedule=schedule)
            
            # 2. 관련 납품 히스토리 삭제 (납품 활동 기록)
            delivery_histories = History.objects.filter(schedule=schedule, action_type='delivery')
            delivery_histories_count = delivery_histories.count()
            
            if delivery_histories_count > 0:
                delivery_histories.delete()
            
            # 3. 펀넬을 실주로 처리
            if schedule.opportunity:
                opportunity = schedule.opportunity
                
                if opportunity.current_stage != 'lost':  # 이미 실주가 아닌 경우만
                    opportunity.current_stage = 'lost'
                    opportunity.lost_date = date.today()
                    opportunity.lost_reason = f"납품일정 취소 (일정 ID: {schedule.id})"
                    
                    # 단계 이력에 실주 추가
                    if not opportunity.stage_history:
                        opportunity.stage_history = []
                    
                    # 현재 단계 종료 처리
                    for history in reversed(opportunity.stage_history):
                        if not history.get('exited'):
                            history['exited'] = date.today().isoformat()
                            logger.info(f"이전 단계 {history.get('stage')} 종료 처리")
                            break
                    
                    # 실주 단계 추가
                    lost_entry = {
                        'stage': 'lost',
                        'entered': date.today().isoformat(),
                        'exited': None,
                        'note': f'납품일정 취소로 인한 실주 (일정 ID: {schedule.id})'
                    }
                    opportunity.stage_history.append(lost_entry)
                    logger.info("🎯 실주 단계 이력 추가")
                    
                    opportunity.save()
                    opportunity.update_revenue_amounts()
                    logger.info("✅ 펀넬 실주 처리 완료")
                else:
                    logger.info(f"⚠️ 펀넬이 이미 {opportunity.current_stage} 상태라서 실주 처리 안함")
            else:
                logger.warning("❌ 연결된 펀넬이 없음 - 실주 처리 불가")
        
        # 예정 처리 시 추가 작업 (펀넬을 클로징으로 변경)
        if new_status == 'scheduled' and schedule.activity_type == 'delivery':
            logger.info("🔄 예정으로 변경 - 펀넬 클로징 처리 시작!")
            from datetime import date
            
            # 펀넬을 클로징으로 변경
            if schedule.opportunity:
                logger.info(f"🎯 연결된 펀넬 ID: {schedule.opportunity.id}")
                opportunity = schedule.opportunity
                logger.info(f"현재 펀넬 상태: {opportunity.current_stage}")
                
                # lost나 won 상태에서 클로징으로 변경
                if opportunity.current_stage == 'lost':
                    logger.info("🎯 실주에서 펀넬 클로징으로 되돌리기...")
                    opportunity.current_stage = 'closing'
                    opportunity.lost_date = None  # 실주 날짜 제거
                    opportunity.lost_reason = None  # 실주 사유 제거
                    
                    # 단계 이력에 클로징 추가
                    if not opportunity.stage_history:
                        opportunity.stage_history = []
                    
                    # 현재 lost 단계 종료 처리
                    for history in reversed(opportunity.stage_history):
                        if history.get('stage') == 'lost' and not history.get('exited'):
                            history['exited'] = date.today().isoformat()
                            history['note'] = f"{history.get('note', '')} → 취소 철회로 복구"
                            logger.info("이전 실주 단계 종료 처리")
                            break
                    
                    # 클로징 단계 추가
                    closing_entry = {
                        'stage': 'closing',
                        'entered': date.today().isoformat(),
                        'exited': None,
                        'note': f'취소 철회 후 납품 예정으로 클로징 (일정 ID: {schedule.id})'
                    }
                    opportunity.stage_history.append(closing_entry)
                    logger.info("🎯 클로징 단계 이력 추가")
                    
                    opportunity.save()
                    opportunity.update_revenue_amounts()
                    logger.info("✅ 펀넬 클로징 처리 완료")
                    
                elif opportunity.current_stage == 'won':
                    logger.info("🎯 수주에서 펀넬 클로징으로 되돌리기...")
                    opportunity.current_stage = 'closing'
                    opportunity.won_date = None  # 수주 날짜 제거
                    
                    # 단계 이력에 클로징 추가
                    if not opportunity.stage_history:
                        opportunity.stage_history = []
                    
                    # 현재 won 단계 종료 처리
                    for history in reversed(opportunity.stage_history):
                        if history.get('stage') == 'won' and not history.get('exited'):
                            history['exited'] = date.today().isoformat()
                            history['note'] = f"{history.get('note', '')} → 완료 철회로 예정 복귀"
                            logger.info("이전 수주 단계 종료 처리")
                            break
                    
                    # 클로징 단계 추가
                    closing_entry = {
                        'stage': 'closing',
                        'entered': date.today().isoformat(),
                        'exited': None,
                        'note': f'완료 철회 후 납품 예정으로 클로징 (일정 ID: {schedule.id})'
                    }
                    opportunity.stage_history.append(closing_entry)
                    logger.info("🎯 클로징 단계 이력 추가")
                    
                    opportunity.save()
                    opportunity.update_revenue_amounts()
                    logger.info("✅ 펀넬 클로징 처리 완료")
                else:
                    logger.info(f"⚠️ 펀넬이 {opportunity.current_stage} 상태라서 클로징 처리 안함")
            else:
                logger.warning("❌ 연결된 펀넬이 없음 - 클로징 처리 불가")
        
        # 완료 처리 시 추가 작업 (실주였던 펀넬을 수주로 되돌리기)
        if new_status == 'completed' and old_status == 'cancelled':
            logger.info("🎉 취소에서 완료로 변경 - 펀넬 수주 처리 시작!")
            from datetime import date
            
            # 펀넬을 수주로 되돌리기
            if schedule.opportunity:
                logger.info(f"🎯 연결된 펀넬 ID: {schedule.opportunity.id}")
                opportunity = schedule.opportunity
                logger.info(f"현재 펀넬 상태: {opportunity.current_stage}")
                
                if opportunity.current_stage == 'lost':  # 실주 상태인 경우만 수주로 변경
                    logger.info("🎯 펀넬 수주로 되돌리기...")
                    opportunity.current_stage = 'won'
                    opportunity.won_date = date.today()
                    opportunity.lost_date = None  # 실주 날짜 제거
                    opportunity.lost_reason = None  # 실주 사유 제거
                    
                    # 단계 이력에 수주 추가
                    if not opportunity.stage_history:
                        opportunity.stage_history = []
                    
                    # 현재 lost 단계 종료 처리
                    for history in reversed(opportunity.stage_history):
                        if history.get('stage') == 'lost' and not history.get('exited'):
                            history['exited'] = date.today().isoformat()
                            history['note'] = f"{history.get('note', '')} → 취소 철회로 복구"
                            logger.info("이전 실주 단계 종료 처리")
                            break
                    
                    # 수주 단계 추가
                    won_entry = {
                        'stage': 'won',
                        'entered': date.today().isoformat(),
                        'exited': None,
                        'note': f'취소 철회 후 납품 완료로 자동 수주 (일정 ID: {schedule.id})'
                    }
                    opportunity.stage_history.append(won_entry)
                    logger.info("🎯 수주 단계 이력 추가")
                    
                    opportunity.save()
                    opportunity.update_revenue_amounts()
                    logger.info("✅ 펀넬 수주 처리 완료")
                else:
                    logger.info(f"⚠️ 펀넬이 {opportunity.current_stage} 상태라서 수주 처리 안함")
            else:
                logger.warning("❌ 연결된 펀넬이 없음 - 수주 처리 불가")
        
        # 일반적인 납품 완료 시 펀넬을 수주로 업데이트 (scheduled → completed)
        if new_status == 'completed' and old_status == 'scheduled' and schedule.activity_type == 'delivery':
            logger.info("🎉 납품 일정 완료 - 펀넬 수주 처리 시작!")
            from datetime import date
            
            # 펀넬을 수주로 업데이트
            if schedule.opportunity:
                logger.info(f"🎯 연결된 펀넬 ID: {schedule.opportunity.id}")
                opportunity = schedule.opportunity
                logger.info(f"현재 펀넬 상태: {opportunity.current_stage}")
                
                if opportunity.current_stage != 'won' and opportunity.current_stage != 'lost':  # 아직 수주/실주가 아닌 경우
                    logger.info("🎯 펀넬 수주 처리 중...")
                    opportunity.current_stage = 'won'
                    opportunity.won_date = date.today()
                    
                    # 단계 이력에 수주 추가
                    if not opportunity.stage_history:
                        opportunity.stage_history = []
                    
                    # 현재 단계 종료 처리
                    for history in reversed(opportunity.stage_history):
                        if not history.get('exited'):
                            history['exited'] = date.today().isoformat()
                            logger.info(f"이전 단계 {history.get('stage')} 종료 처리")
                            break
                    
                    # 수주 단계 추가
                    won_entry = {
                        'stage': 'won',
                        'entered': date.today().isoformat(),
                        'exited': None,
                        'note': f'납품 완료로 자동 수주 (일정 ID: {schedule.id})'
                    }
                    opportunity.stage_history.append(won_entry)
                    logger.info("🎯 수주 단계 이력 추가")
                    
                    opportunity.save()
                    opportunity.update_revenue_amounts()
                    logger.info("✅ 펀넬 수주 처리 완료")
                elif opportunity.current_stage == 'won':
                    logger.info("⚠️ 펀넬이 이미 수주 상태")
                else:
                    logger.info(f"⚠️ 펀넬이 {opportunity.current_stage} 상태라서 수주 처리 안함")
            else:
                logger.warning("❌ 연결된 펀넬이 없음 - 수주 처리 불가")
        
        schedule.status = new_status
        schedule.save()
        logger.info(f"✅ 일정 상태 저장 완료: {new_status}")
        
        # 상태 변경 시 수주 금액 업데이트
        backlog_amount = 0
        if schedule.opportunity:
            try:
                opportunity = schedule.opportunity
                opportunity.update_revenue_amounts()
                backlog_amount = float(opportunity.backlog_amount)
                logger.info(f"💰 수주 금액 업데이트: {backlog_amount:,}원")
            except Exception as e:
                # 오류 발생 시 무시
                logger.error(f"수주 업데이트 중 오류: {e}")
        
        status_display = {
            'scheduled': '예정됨',
            'completed': '완료됨', 
            'cancelled': '취소됨'
        }
        
        response_data = {
            'success': True,
            'new_status': new_status,
            'status_display': status_display[new_status],
            'message': f'일정 상태가 "{status_display[new_status]}"로 변경되었습니다.',
            'backlog_amount': backlog_amount,
        }
        
        # 취소 시 추가 정보 제공
        if new_status == 'cancelled' and old_status != 'cancelled':
            additional_messages = []
            if 'deleted_items_count' in locals() and deleted_items_count > 0:
                additional_messages.append(f'{deleted_items_count}개 납품 품목이 삭제되었습니다.')
            if 'delivery_histories_count' in locals() and delivery_histories_count > 0:
                additional_messages.append(f'{delivery_histories_count}개 납품 기록이 삭제되었습니다.')
            if schedule.opportunity and schedule.opportunity.current_stage == 'lost':
                additional_messages.append('펀넬 상태가 실주로 변경되었습니다.')
            
            if additional_messages:
                response_data['additional_message'] = ' '.join(additional_messages)
                logger.info(f"📋 추가 메시지: {response_data['additional_message']}")
        
        logger.info("🎉 일정 상태 업데이트 완료")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"❌ 일정 상태 업데이트 오류: {str(e)}", exc_info=True)
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
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Admin 사용자는 모든 업체 검색 가능
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        companies = Company.objects.filter(name__icontains=query).order_by('name')[:10]
    else:
        # 일반 사용자: 같은 회사 소속 사용자들이 생성한 업체만 검색 가능
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        
        if user_company:
            # 미들웨어에서 설정한 user_company 사용
            same_company_users = User.objects.filter(userprofile__company=user_company)
            logger.info(f"[COMPANY_AUTOCOMPLETE] 같은 회사 사용자 수: {same_company_users.count()}")
            
            companies = Company.objects.filter(
                name__icontains=query,
                created_by__in=same_company_users
            ).order_by('name')[:10]
            logger.info(f"[COMPANY_AUTOCOMPLETE] 검색 결과: {companies.count()}개")
            
        elif user_profile and user_profile.company:
            # 백업: UserProfile에서 직접 가져오기
            same_company_users = User.objects.filter(userprofile__company=user_profile.company)
            logger.info(f"[COMPANY_AUTOCOMPLETE] 백업 방식 - 같은 회사 사용자 수: {same_company_users.count()}")
            
            companies = Company.objects.filter(
                name__icontains=query,
                created_by__in=same_company_users
            ).order_by('name')[:10]
            logger.info(f"[COMPANY_AUTOCOMPLETE] 백업 방식 검색 결과: {companies.count()}개")
        else:
            companies = Company.objects.none()
            logger.warning(f"[COMPANY_AUTOCOMPLETE] 회사 정보 없음 - 빈 결과 반환")
    
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
        # 일반 사용자: 같은 회사 사용자들이 생성한 업체의 부서만 검색
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        logger.info(f"[DEPT_AUTOCOMPLETE] user_company: {user_company}, user_profile.company: {user_profile.company if user_profile else None}")
        
        if user_company:
            same_company_users = User.objects.filter(userprofile__company=user_company)
            # 같은 회사 사용자들이 생성한 업체의 부서만 필터링
            departments = Department.objects.filter(
                name__icontains=query,
                company__created_by__in=same_company_users
            )
            logger.info(f"[DEPT_AUTOCOMPLETE] 같은 회사 사용자들의 업체 부서에서 검색")
        elif user_profile and user_profile.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile.company)
            departments = Department.objects.filter(
                name__icontains=query,
                company__created_by__in=same_company_users
            )
            logger.info(f"[DEPT_AUTOCOMPLETE] 백업 방식 - 같은 회사 사용자들의 업체 부서에서 검색")
        else:
            departments = Department.objects.none()
            logger.warning(f"[DEPT_AUTOCOMPLETE] 회사 정보 없음 - 빈 결과 반환")
    
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
        # 일반 사용자: 같은 회사 소속 사용자들이 생성한 업체만 조회
        user_company = getattr(request.user, 'userprofile', None)
        if user_company and user_company.company:
            # 같은 회사 소속 사용자들이 생성한 업체만 조회
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            companies = Company.objects.filter(created_by__in=same_company_users).annotate(
                department_count=Count('departments', distinct=True),
                followup_count=Count('followup_companies', distinct=True)
            ).order_by('name')
            
            logger.info(f"[COMPANY_LIST] 일반 사용자 {request.user.username}: {companies.count()}개 업체 조회 (회사: {user_company.company.name})")
            logger.info(f"[COMPANY_LIST] 같은 회사 사용자 수: {same_company_users.count()}명")
            logger.info(f"[COMPANY_LIST] 같은 회사 사용자 목록: {list(same_company_users.values_list('username', flat=True))}")
        else:
            # 회사 정보가 없는 경우 빈 쿼리셋
            companies = Company.objects.none()
            
            logger.warning(f"[COMPANY_LIST] 사용자 {request.user.username}: 회사 정보 없음, 빈 목록 반환")
    
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
    
    # Admin이 아닌 경우 권한 확인
    if not (getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')):
        # 자신의 회사 소속 사용자들이 생성한 업체인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        if user_company and user_company.company:
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if not Company.objects.filter(pk=pk, created_by__in=same_company_users).exists():
                logger.warning(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 업체 {pk} 접근 권한 없음")
                messages.error(request, '해당 업체/학교에 접근할 권한이 없습니다.')
                return redirect('reporting:company_list')
            logger.info(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 업체 {pk} 접근 권한 있음 (같은 회사)")
        else:
            logger.warning(f"[COMPANY_DETAIL] 사용자 {request.user.username}: 회사 정보 없어 접근 불가")
            messages.error(request, '회사 정보가 없어 접근할 수 없습니다.')
            return redirect('reporting:company_list')
    else:
        logger.info(f"[COMPANY_DETAIL] Admin 사용자 {request.user.username}: 업체 {pk} 접근")
    
    logger.info(f"[COMPANY_DETAIL] 업체 '{company.name}' 상세보기 접근 (생성자: {company.created_by.username if company.created_by else 'Unknown'})")
    
    # 수정/삭제 권한 확인
    is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
    can_edit_company = is_admin or company.created_by == request.user
    
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
    
    # Admin이 아닌 경우 권한 확인
    is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
    
    if not is_admin:
        # 자신의 회사 소속 사용자들이 생성한 업체인지 확인
        user_company = getattr(request.user, 'userprofile', None)
        if user_company and user_company.company:
            same_company_users = User.objects.filter(userprofile__company=user_company.company)
            if not Company.objects.filter(pk=company_pk, created_by__in=same_company_users).exists():
                logger.warning(f"[DEPT_CREATE] 사용자 {request.user.username}: 업체 {company_pk} 부서 추가 권한 없음")
                messages.error(request, '해당 업체/학교에 부서를 추가할 권한이 없습니다.')
                return redirect('reporting:company_detail', pk=company_pk)
            logger.info(f"[DEPT_CREATE] 사용자 {request.user.username}: 업체 {company_pk} '{company.name}'에 부서 추가 권한 있음 (같은 회사)")
        else:
            logger.warning(f"[DEPT_CREATE] 사용자 {request.user.username}: 회사 정보 없어 부서 추가 불가")
            messages.error(request, '회사 정보가 없어 부서를 추가할 수 없습니다.')
            return redirect('reporting:company_detail', pk=company_pk)
    else:
        logger.info(f"[DEPT_CREATE] Admin 사용자 {request.user.username}: 업체 {company_pk} '{company.name}'에 부서 추가 권한 있음")
    
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
        'page_title': f'{department.company.name} - 부서/연구실 수정',
        'customers': department.followup_departments.all().select_related('user')  # 소속 연구원/고객 목록
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
def history_update_tax_invoice(request, pk):
    """세금계산서 발행 상태 업데이트"""
    try:
        history = get_object_or_404(History, pk=pk)
        
        # 권한 체크
        if not can_modify_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '수정 권한이 없습니다.'
            })
        
        # 납품 일정 타입만 세금계산서 상태 변경 가능
        if history.action_type != 'delivery_schedule':
            return JsonResponse({
                'success': False,
                'error': '납품 일정만 세금계산서 상태를 변경할 수 있습니다.'
            })
        
        # 세금계산서 상태 업데이트
        tax_invoice_issued = request.POST.get('tax_invoice_issued') == 'true'
        history.tax_invoice_issued = tax_invoice_issued
        history.save()
        
        # 연결된 스케줄이 있는 경우 스케줄의 납품 품목과 동기화
        if history.schedule:
            try:
                # 연결된 스케줄의 모든 납품 품목 업데이트
                delivery_items = history.schedule.delivery_items_set.all()
                if delivery_items.exists():
                    delivery_items.update(tax_invoice_issued=tax_invoice_issued)
                
                # 연결된 스케줄에 속한 다른 히스토리들도 함께 업데이트
                related_histories = History.objects.filter(
                    schedule=history.schedule, 
                    action_type='delivery_schedule'
                ).exclude(id=history.id)
                
                if related_histories.exists():
                    related_histories.update(tax_invoice_issued=tax_invoice_issued)
                    
            except Exception as sync_error:
                logger.error(f"연결된 스케줄/히스토리 세금계산서 동기화 실패: {sync_error}")
        
        # sync_schedule 파라미터는 향후 확장용으로 유지
        sync_schedule = request.POST.get('sync_schedule') == 'true'
        
        # silent 모드인 경우 (자동 동기화) 별도 메시지
        is_silent = request.POST.get('silent') == 'true'
        if is_silent:
            message = '세금계산서 상태가 자동으로 동기화되었습니다.'
        else:
            message = '세금계산서 상태가 성공적으로 변경되었습니다.'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'세금계산서 상태 변경 중 오류가 발생했습니다: {str(e)}'
        })

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
    
    # 우선순위 필터 적용
    priority_filter = request.GET.get('priority')
    if priority_filter:
        followups = followups.filter(priority=priority_filter)
    
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
        
        # 중복 방지를 위해 처리된 Schedule ID들을 추적
        processed_schedule_ids = set()
        
        for history in delivery_histories:
            # 납품 금액 집계 - History 우선
            if history.delivery_amount:
                total_delivery_amount += history.delivery_amount
            
            # History에 실제 납품 품목 정보가 있는 경우만 Schedule ID 기록
            # (품목 정보가 없으면 Schedule에서 가져와야 함)
            if history.schedule_id and history.delivery_items:
                processed_schedule_ids.add(history.schedule_id)
            
            # 납품 품목 집계 - History 텍스트에서만 처리 (Schedule DeliveryItem은 나중에 별도 처리)
            if history.delivery_items:
                # 다양한 줄바꿈 문자 처리
                processed_items = history.delivery_items
                processed_items = processed_items.replace('\\n', '\n')
                processed_items = processed_items.replace('\\r\\n', '\n')
                processed_items = processed_items.replace('\\r', '\n')
                processed_items = processed_items.replace('\r\n', '\n')
                processed_items = processed_items.replace('\r', '\n')
                processed_items = processed_items.strip()
                
                # 다양한 구분자로 분할 시도
                lines = []
                # 먼저 줄바꿈으로 분할
                for line in processed_items.split('\n'):
                    line = line.strip()
                    if line:
                        # 쉼표로도 분할해보기
                        if ',' in line and ':' in line:
                            sub_lines = [sub.strip() for sub in line.split(',') if sub.strip()]
                            lines.extend(sub_lines)
                        else:
                            lines.append(line)
                
                for line in lines:
                    # 다양한 패턴 시도
                    import re
                    
                    # 패턴 1: "품목명: 수량개 금액원 횟수회" 또는 "품목명 수량개 금액원 횟수회"
                    pattern1 = r'(.+?)[\s:]*([\d,]+)개[\s,]*([\d,]+)원[\s,]*([\d]+)회'
                    match1 = re.search(pattern1, line)
                    
                    if match1:
                        item_name = match1.group(1).replace(':', '').strip()
                        quantity = float(match1.group(2).replace(',', ''))
                        
                        if item_name in item_quantities:
                            item_quantities[item_name] += quantity
                        else:
                            item_quantities[item_name] = quantity
                        continue
                    
                    # 패턴 2: "품목명: 수량개" 또는 "품목명 수량개"
                    pattern2 = r'(.+?)[\s:]*([\d,]+(?:\.\d+)?)개'
                    match2 = re.search(pattern2, line)
                    
                    if match2:
                        item_name = match2.group(1).replace(':', '').strip()
                        quantity = float(match2.group(2).replace(',', ''))
                        
                        if item_name in item_quantities:
                            item_quantities[item_name] += quantity
                        else:
                            item_quantities[item_name] = quantity
                        continue
                    
                    # 패턴 3: 단순 품목명만 있는 경우
                    if line and not any(char in line for char in [':', '개', '원', '회']):
                        item_name = line.strip()
                        
                        if item_name in item_quantities:
                            item_quantities[item_name] += 1
                        else:
                            item_quantities[item_name] = 1
        
        # Schedule 기반 DeliveryItem도 포함 (모든 Schedule 처리)
        all_schedule_deliveries = followup.schedules.filter(
            delivery_items_set__isnull=False
        ).distinct()
        
        # 모든 Schedule 처리 (History에 품목 정보가 없으면 Schedule에서 가져옴)
        for schedule in all_schedule_deliveries:
            # History에서 이미 품목 정보를 처리한 Schedule은 금액만 확인
            if schedule.id in processed_schedule_ids:
                # 금액만 추가 확인 (History에 없었을 수 있음)
                schedule_total = 0
                for item in schedule.delivery_items_set.all():
                    if item.total_price:
                        schedule_total += Decimal(str(item.total_price))
                
                if schedule_total > 0:
                    total_delivery_amount += schedule_total
                continue
            
            # Schedule별 총액 계산 및 품목 집계
            schedule_total = 0
            schedule_items = []
            
            for item in schedule.delivery_items_set.all():
                # Schedule 기반 품목의 금액 포함
                if item.total_price:
                    schedule_total += Decimal(str(item.total_price))
                
                # 품목 정보 저장
                schedule_items.append({
                    'name': item.item_name,
                    'quantity': float(item.quantity)
                })
            
            # Schedule 총액을 전체 납품 금액에 추가 (이미 processed된 경우 위에서 처리됨)
            if schedule.id not in processed_schedule_ids and schedule_total > 0:
                total_delivery_amount += schedule_total
            
            # Schedule 품목 집계 (모든 Schedule에서)
            for item_info in schedule_items:
                item_name = item_info['name']
                quantity = item_info['quantity']
                
                # 품목별 수량 누적 (원본 이름 그대로 사용)
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
            
            # 모든 품목 표시 (제한 제거)
            items_text = ', '.join(items_list)
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
        9: 60,   # 납품 품목 (더 넓게 - 모든 품목 표시를 위해)
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
    
    # 우선순위 필터 적용
    priority_filter = request.GET.get('priority')
    if priority_filter:
        followups = followups.filter(priority=priority_filter)
    
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
    
    # 담당자 필터링 (Manager만)
    view_all = request.GET.get('view_all') == 'true'
    users = []
    selected_user = None
    target_user = request.user  # 기본은 본인
    user_filter = None  # 초기화
    
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user)
        # 전체 팀원 선택 시 세션 초기화
        if view_all:
            if 'selected_user_id' in request.session:
                del request.session['selected_user_id']
            target_user = None  # 전체 팀원 데이터
            user_filter = None
        else:
            user_filter = request.GET.get('user')
            # user_filter가 없으면 세션에서 가져오기
            if not user_filter:
                user_filter = request.session.get('selected_user_id')
        
            if user_filter:
                # Manager가 특정 팀원을 선택한 경우
                try:
                    selected_user = accessible_users.get(id=user_filter)
                    target_user = selected_user
                    # 세션에 저장
                    request.session['selected_user_id'] = str(user_filter)
                except User.DoesNotExist:
                    target_user = None  # 전체 팀원 데이터
                    # 잘못된 세션 값 제거
                    if 'selected_user_id' in request.session:
                        del request.session['selected_user_id']
            else:
                target_user = None  # 전체 팀원 데이터
                # user_filter가 명시적으로 없으면(초기화) 세션도 제거
                if 'selected_user_id' in request.session:
                    del request.session['selected_user_id']
    
    # 모든 고객 조회 (담당자 무관)
    followups = FollowUp.objects.all()
    
    # Manager용 팀원 목록
    if user_profile.can_view_all_users():
        accessible_users_list = get_accessible_users(request.user)
        if not getattr(request, 'is_hanagwahak', False):
            user_profile_obj = getattr(request.user, 'userprofile', None)
            if user_profile_obj and user_profile_obj.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
                accessible_users_list = accessible_users_list.filter(id__in=same_company_users.values_list('id', flat=True))
        users = accessible_users_list.filter(followup__isnull=False).distinct()
    
    # 검색 기능
    search_query = request.GET.get('search')
    if search_query:
        followups = followups.filter(
            Q(customer_name__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(manager__icontains=search_query)
        )
    
    # ✅ Prefetch로 N+1 쿼리 방지 (성능 최적화)
    from django.db.models import Prefetch
    
    # 사용자 필터 설정
    if target_user is None and user_profile.can_view_all_users():
        user_filter_q = Q(user__in=accessible_users)
    else:
        user_filter_q = Q(user=target_user)
    
    # 모든 관련 데이터를 한 번에 가져오기
    followups = followups.prefetch_related(
        Prefetch('histories', queryset=History.objects.filter(user_filter_q).select_related('user')),
        Prefetch('schedules', queryset=Schedule.objects.filter(user_filter_q).select_related('user').prefetch_related('delivery_items_set'))
    )
    
    # 각 고객별 통계 계산
    followups_with_stats = []
    total_amount_sum = Decimal('0')
    total_meetings_sum = 0
    total_deliveries_sum = 0
    total_unpaid_sum = 0
    prepayment_customers = set()
    
    for followup in followups:
        # ✅ Prefetch된 데이터 사용 (추가 쿼리 없음!)
        all_histories = list(followup.histories.all())
        all_schedules = list(followup.schedules.all())
        
        # History 통계
        meetings = sum(1 for h in all_histories if h.action_type == 'customer_meeting')
        delivery_histories = [h for h in all_histories if h.action_type == 'delivery_schedule']
        deliveries = len(delivery_histories)
        history_amount = sum(h.delivery_amount or Decimal('0') for h in delivery_histories)
        unpaid = sum(1 for h in delivery_histories if not h.tax_invoice_issued)
        
        # Schedule 통계
        schedule_deliveries = [s for s in all_schedules if s.activity_type == 'delivery']
        schedule_delivery_count = len(schedule_deliveries)
        schedule_amount = sum(
            item.total_price or Decimal('0')
            for schedule in schedule_deliveries
            for item in schedule.delivery_items_set.all()
        )
        
        # 세금계산서 현황 계산 (History + Schedule DeliveryItem 통합 - 중복 제거)
        # 1. History와 Schedule 연결 관계 분석
        history_with_schedule_ids = set(
            h.schedule_id for h in delivery_histories if h.schedule_id is not None
        )
        
        # 2. History 기반 세금계산서 현황 (Schedule 연결 여부로 구분)
        history_with_schedule_issued = [
            h.schedule_id for h in delivery_histories 
            if h.schedule_id is not None and h.tax_invoice_issued
        ]
        history_with_schedule_pending = [
            h.schedule_id for h in delivery_histories 
            if h.schedule_id is not None and not h.tax_invoice_issued
        ]
        
        history_without_schedule_issued = sum(
            1 for h in delivery_histories 
            if h.schedule_id is None and h.tax_invoice_issued
        )
        history_without_schedule_pending = sum(
            1 for h in delivery_histories 
            if h.schedule_id is None and not h.tax_invoice_issued
        )
        
        # 3. Schedule DeliveryItem 세금계산서 현황 (Prefetch된 데이터 사용)
        # Schedule만 있는 경우 (History에 연결되지 않은 Schedule)
        schedule_only_deliveries = [
            s for s in schedule_deliveries 
            if s.id not in history_with_schedule_ids
        ]
        
        schedule_only_issued = 0
        schedule_only_pending = 0
        
        for schedule in schedule_only_deliveries:
            items = list(schedule.delivery_items_set.all())
            if items:
                # 해당 Schedule에 하나라도 발행된 품목이 있으면 발행으로 카운팅
                if any(item.tax_invoice_issued for item in items):
                    schedule_only_issued += 1
                else:
                    schedule_only_pending += 1
        
        # 4. 중복 제거된 최종 세금계산서 현황
        # History 우선 원칙: History와 Schedule이 모두 있는 경우 History 상태를 사용
        history_schedule_issued_set = set(history_with_schedule_issued)
        history_schedule_pending_set = set(history_with_schedule_pending)
        
        total_tax_issued = len(history_schedule_issued_set) + history_without_schedule_issued + schedule_only_issued
        total_tax_pending = len(history_schedule_pending_set) + history_without_schedule_pending + schedule_only_pending
        
        # 중복 제거된 납품 횟수 계산 (Prefetch된 데이터 사용)
        # History에 기록된 일정 ID들
        history_schedule_ids = set(
            h.schedule_id for h in delivery_histories if h.schedule_id is not None
        )
        # Schedule에 DeliveryItem이 있는 일정 ID들  
        schedule_ids = set(s.id for s in schedule_deliveries)
        
        # History만 있는 납품 + Schedule만 있는 납품 + 둘 다 있는 경우는 1개로 카운팅
        history_only_deliveries = sum(1 for h in delivery_histories if h.schedule_id is None)
        unique_deliveries_count = len(history_schedule_ids | schedule_ids) + history_only_deliveries
        
        # 통합 통계
        total_meetings_count = meetings
        total_deliveries_count = unique_deliveries_count
        total_amount = history_amount + schedule_amount
        last_contact = max((h.created_at for h in all_histories), default=None)  # Prefetch된 데이터 사용
        
        # 선결제 통계 계산 - target_user가 등록한 선결제만
        prepayments = Prepayment.objects.filter(
            customer=followup,
            created_by=target_user
        ).select_related('created_by')
        
        prepayment_total = prepayments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        prepayment_balance = prepayments.aggregate(total=Sum('balance'))['total'] or Decimal('0')
        prepayment_count = prepayments.count()
        
        # 선결제 등록자 정보 (중복 제거)
        prepayment_creators = list(set([p.created_by.get_full_name() or p.created_by.username for p in prepayments])) if prepayment_count > 0 else []
        
        # 객체에 통계 추가
        followup.total_meetings = total_meetings_count
        followup.total_deliveries = total_deliveries_count
        followup.total_amount = total_amount
        followup.tax_invoices_issued = total_tax_issued  # 세금계산서 발행 건수
        followup.tax_invoices_pending = total_tax_pending  # 세금계산서 미발행 건수
        followup.unpaid_count = total_tax_pending  # 미발행 건수를 unpaid_count로 사용
        followup.last_contact = last_contact
        followup.prepayment_total = prepayment_total  # 선결제 총액
        followup.prepayment_balance = prepayment_balance  # 선결제 잔액
        followup.prepayment_count = prepayment_count  # 선결제 건수
        followup.prepayment_creators = ', '.join(prepayment_creators) if prepayment_creators else ''  # 선결제 등록자
        
        # target_user의 활동이 하나라도 있는 경우만 추가 (미팅, 납품, 선결제)
        if total_meetings_count > 0 or total_deliveries_count > 0 or prepayment_count > 0:
            followups_with_stats.append(followup)
            
            # 전체 통계 누적
            total_amount_sum += total_amount
            total_meetings_sum += total_meetings_count
            total_deliveries_sum += total_deliveries_count
            total_unpaid_sum += total_tax_pending  # 세금계산서 미발행 건수로 변경
            if prepayment_count > 0:
                prepayment_customers.add(followup.id)  # 선결제가 있는 고객 추가
    
    # 정렬 처리 - 기본값: 총 납품 금액 내림차순
    sort_by = request.GET.get('sort', 'amount')
    sort_order = request.GET.get('order', 'desc')
    
    from django.utils import timezone
    
    # 정렬 키 매핑
    sort_key_map = {
        'customer_name': lambda x: (x.customer_name or '').lower(),
        'company': lambda x: (x.company.name if x.company else '').lower(),
        'meetings': lambda x: x.total_meetings,
        'deliveries': lambda x: x.total_deliveries,
        'amount': lambda x: x.total_amount,
        'unpaid': lambda x: x.unpaid_count,
        'last_contact': lambda x: x.last_contact or timezone.now().replace(year=1900),
    }
    
    # 정렬 키가 유효한지 확인
    if sort_by in sort_key_map:
        followups_with_stats.sort(
            key=sort_key_map[sort_by],
            reverse=(sort_order == 'desc')
        )
    else:
        # 기본 정렬: 총 납품 금액 기준
        followups_with_stats.sort(key=lambda x: x.total_amount, reverse=True)
    
    # 페이지네이션 추가
    from django.core.paginator import Paginator
    paginator = Paginator(followups_with_stats, 30)  # 페이지당 30개
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'followups': page_obj,
        'page_obj': page_obj,
        'total_customers': len(followups_with_stats),
        'total_amount_sum': total_amount_sum,
        'total_meetings_sum': total_meetings_sum,
        'total_deliveries_sum': total_deliveries_sum,
        'total_unpaid_sum': total_unpaid_sum,
        'total_prepayment_customers': len(prepayment_customers),  # 선결제 고객 수
        'sort_by': sort_by,
        'sort_order': sort_order,
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
    from django.core import serializers
    from django.core.serializers.json import DjangoJSONEncoder
    from datetime import datetime, timedelta
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 권한 확인 및 팔로우업 조회
    try:
        followup = FollowUp.objects.select_related('user', 'company', 'department').get(id=followup_id)
        
        # Admin 사용자는 모든 데이터에 접근 가능
        if getattr(request, 'is_admin', False):
            pass  # Admin은 권한 체크 없이 진행
        else:
            # 권한 체크
            if not can_access_user_data(request.user, followup.user):
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('reporting:customer_report')
            
            # Manager는 회사 체크를 건너뜀 (모든 데이터 조회 가능)
            user_profile = get_user_profile(request.user)
            if not user_profile.is_manager():
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
    
    # 해당 고객의 모든 활동 히스토리
    histories = History.objects.filter(followup=followup).order_by('-created_at')
    
    # 기본 통계 계산
    total_meetings = histories.filter(action_type='customer_meeting').count()
    total_deliveries = histories.filter(action_type='delivery_schedule').count()
    
    # 총 금액 계산 (History + Schedule DeliveryItem 통합)
    history_amount = histories.filter(action_type='delivery_schedule').aggregate(
        total=Sum('delivery_amount')
    )['total'] or 0
    
    # Schedule DeliveryItem 총액 계산
    schedule_amount = 0
    schedule_deliveries = Schedule.objects.filter(
        followup=followup, 
        activity_type='delivery'
    ).prefetch_related('delivery_items_set')
    
    for schedule in schedule_deliveries:
        for item in schedule.delivery_items_set.all():
            if item.total_price:
                schedule_amount += float(item.total_price)
            elif item.unit_price:
                schedule_amount += float(item.unit_price) * item.quantity * 1.1
    
    total_amount = history_amount + schedule_amount
    
    # 세금계산서 현황 계산 (History + Schedule 통합, 중복 제거)
    delivery_histories = histories.filter(action_type='delivery_schedule')
    
    # 1. History와 Schedule 연결 관계 분석
    history_with_schedule_ids = set(
        delivery_histories.filter(schedule__isnull=False).values_list('schedule_id', flat=True)
    )
    
    # 2. History 기반 세금계산서 현황
    history_tax_issued = 0
    history_tax_pending = 0
    
    # History와 Schedule이 연결된 경우
    history_with_schedule_issued = delivery_histories.filter(
        schedule__isnull=False, tax_invoice_issued=True
    ).values_list('schedule_id', flat=True)
    history_with_schedule_pending = delivery_histories.filter(
        schedule__isnull=False, tax_invoice_issued=False
    ).values_list('schedule_id', flat=True)
    
    # History만 있는 경우 (Schedule에 연결되지 않은 History)
    history_without_schedule_issued = delivery_histories.filter(
        schedule__isnull=True, tax_invoice_issued=True
    ).count()
    history_without_schedule_pending = delivery_histories.filter(
        schedule__isnull=True, tax_invoice_issued=False
    ).count()
    
    # 3. Schedule DeliveryItem 세금계산서 현황 (History에 연결되지 않은 Schedule만)
    schedule_tax_issued = 0
    schedule_tax_pending = 0
    
    schedule_only_deliveries = schedule_deliveries.exclude(
        id__in=history_with_schedule_ids
    )
    
    for schedule in schedule_only_deliveries:
        items = schedule.delivery_items_set.all()
        if items.exists():
            # 해당 Schedule에 하나라도 발행된 품목이 있으면 발행으로 카운팅
            if items.filter(tax_invoice_issued=True).exists():
                schedule_tax_issued += 1
            else:
                schedule_tax_pending += 1
    
    # 4. 중복 제거된 최종 세금계산서 현황
    # History 우선 원칙: History와 Schedule이 모두 있는 경우 History 상태를 사용
    history_schedule_issued_set = set(history_with_schedule_issued)
    history_schedule_pending_set = set(history_with_schedule_pending)
    
    tax_invoices_issued = len(history_schedule_issued_set) + history_without_schedule_issued + schedule_tax_issued
    tax_invoices_pending = len(history_schedule_pending_set) + history_without_schedule_pending + schedule_tax_pending
    
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
    
    # Schedule 납품 일정에 총액 정보 추가
    for schedule in schedule_deliveries:
        schedule_total_amount = 0
        tax_invoice_issued_count = 0
        total_items_count = 0
        
        for item in schedule.delivery_items_set.all():
            if item.total_price:
                item_total = float(item.total_price)
            elif item.unit_price:
                item_total = float(item.unit_price) * item.quantity * 1.1
            else:
                item_total = 0
            schedule_total_amount += item_total
            total_items_count += 1
            if item.tax_invoice_issued:
                tax_invoice_issued_count += 1
        
        schedule.calculated_total_amount = schedule_total_amount
        schedule.tax_invoice_issued_count = tax_invoice_issued_count
        schedule.total_items_count = total_items_count
    
    # 통합 납품 내역 생성
    integrated_deliveries = []
    processed_schedule_ids = set()
    
    # 1. History 기반 납품 내역
    for history in delivery_histories:
        delivery_data = {
            'type': 'history',
            'id': history.id,
            'date': (history.delivery_date or history.created_at.date()).strftime('%Y-%m-%d'),
            'schedule_id': history.schedule_id if history.schedule else None,
            'items_display': history.delivery_items or None,
            'amount': history.delivery_amount,
            'tax_invoice_issued': history.tax_invoice_issued,
            'content': history.content,
            'user': history.user.username,
            'has_schedule_items': False,
        }
        
        # 연결된 일정이 있고, 그 일정에 DeliveryItem이 있는지 확인
        if history.schedule:
            schedule_items = history.schedule.delivery_items_set.all()
            if schedule_items.exists():
                delivery_data['has_schedule_items'] = True
                delivery_data['schedule_items'] = schedule_items
                
                # 처리된 Schedule ID 기록
                processed_schedule_ids.add(history.schedule.id)
        
        integrated_deliveries.append(delivery_data)
    
    # 2. History에 없는 Schedule 기반 납품 내역만 추가
    for schedule in schedule_deliveries:
        if schedule.id not in processed_schedule_ids:
            delivery_data = {
                'type': 'schedule_only',
                'id': schedule.id,
                'date': schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '',
                'schedule_id': schedule.id,
                'items_display': None,
                'amount': 0,
                'tax_invoice_issued': schedule.tax_invoice_issued_count == schedule.total_items_count if schedule.total_items_count > 0 else False,
                'content': schedule.notes or '일정 기반 납품',
                'user': schedule.user.username,
                'has_schedule_items': True,
                'schedule_amount': schedule.calculated_total_amount,
            }
            integrated_deliveries.append(delivery_data)
    
    # 날짜순 정렬
    integrated_deliveries.sort(key=lambda x: x['date'], reverse=True)
    
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
        'integrated_deliveries': integrated_deliveries,
        'integrated_deliveries_json': json.dumps(integrated_deliveries, ensure_ascii=False, cls=DjangoJSONEncoder),
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
        
        # 연결된 히스토리들도 함께 업데이트
        try:
            related_histories = History.objects.filter(
                schedule=schedule, 
                action_type='delivery_schedule'
            )
            
            if related_histories.exists():
                history_updated_count = related_histories.update(tax_invoice_issued=new_status)
                
        except Exception as sync_error:
            logger.error(f"스케줄 납품 품목 토글 시 히스토리 동기화 실패: {sync_error}")
        
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
        
        # 권한 체크: Schedule의 followup을 통해 사용자 확인
        if schedule.followup and schedule.followup.user:
            if not can_access_user_data(request.user, schedule.followup.user):
                return JsonResponse({
                    'success': False,
                    'error': '접근 권한이 없습니다.'
                }, status=403)
        
        # 연결된 History가 있는지 확인 (History 기준 세금계산서 상태 적용을 위해)
        related_history = None
        try:
            related_history = History.objects.filter(schedule=schedule).first()  # 이 Schedule에 연결된 첫 번째 History
        except:
            pass
        
        # DeliveryItem 정보 가져오기
        delivery_items = schedule.delivery_items_set.all().order_by('id')
        
        items_data = []
        for item in delivery_items:
            item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
            
            # History가 있으면 History 기준, 없으면 Schedule DeliveryItem 기준
            tax_invoice_status = related_history.tax_invoice_issued if related_history else item.tax_invoice_issued
            
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
            for item in delivery_items:
                item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                # History의 세금계산서 상태를 기준으로 함 (동기화)
                items_data.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item_total),
                    'tax_invoice_issued': history.tax_invoice_issued,  # History 기준으로 강제 설정
                    'source': 'history'  # 출처 표시
                })
        else:
            pass
        
        # 2. History DeliveryItem이 없지만 기존 텍스트 데이터가 있는 경우 (fallback)
        if not has_history_items and history.delivery_items and history.delivery_items.strip():
            has_history_items = True
            # 기존 텍스트 데이터 파싱
            delivery_text = history.delivery_items.strip()
            
            # 줄바꿈으로 분리하여 각 라인 처리
            lines = delivery_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            
            # 만약 줄바꿈이 문자열로 저장되어 있다면 \\n으로도 분리 시도
            if len(lines) == 1 and '\\n' in delivery_text:
                lines = delivery_text.split('\\n')
            
            # 그래도 하나의 라인이면, 품목 패턴을 찾아서 분리
            if len(lines) == 1:
                # 정규식으로 품목 패턴을 모두 찾기
                pattern = r'([A-Z0-9.]+:\s*\d+(?:\.\d+)?개\s*\([0-9,]+원\))'
                matches = re.findall(pattern, delivery_text)
                if len(matches) > 1:
                    lines = matches
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                if not line:
                    continue
                
                # "품목명: 수량개 (금액원)" 패턴 파싱
                match = re.match(r'^(.+?):\s*(\d+(?:\.\d+)?)개\s*\((.+?)원\)$', line)
                if match:
                    item_name = match.group(1).strip()
                    quantity = float(match.group(2))
                    amount_str = match.group(3).replace(',', '').replace(' ', '')
                    
                    logger.info(f"[HISTORY_DELIVERY_API] 파싱 성공 - 품목: '{item_name}', 수량: {quantity}, 금액문자열: '{amount_str}'")
                    
                    try:
                        total_amount = float(amount_str)
                        # 부가세 포함 금액에서 단가 역산 (부가세 포함 / 수량)
                        unit_price = total_amount / quantity if quantity > 0 else 0
                    except ValueError as e:
                        logger.error(f"[HISTORY_DELIVERY_API] 금액 파싱 실패: {e}")
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
                    logger.warning(f"[HISTORY_DELIVERY_API] 패턴 매칭 실패 - 라인: '{line}'")
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
            
            if schedule_items.exists():
                has_schedule_items = True
                for item in schedule_items:
                    item_total = item.total_price or (item.quantity * item.unit_price * 1.1)
                    
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
            pass
        
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
def customer_detail_report_view_simple(request, followup_id):
    """특정 고객의 상세 활동 리포트 - 단순화된 버전"""
    from django.db.models import Count, Sum, Q
    from datetime import datetime, timedelta
    import json
    
    # 권한 확인 및 팔로우업 조회
    try:
        followup = FollowUp.objects.select_related('user', 'company', 'department').get(id=followup_id)
        
        # Admin 사용자는 모든 데이터에 접근 가능
        if getattr(request, 'is_admin', False):
            pass  # Admin은 권한 체크 없이 진행
        else:
            # 권한 체크
            if not can_access_user_data(request.user, followup.user):
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('reporting:customer_report')
            
            # Manager는 회사 체크를 건너뜀 (모든 데이터 조회 가능)
            user_profile = get_user_profile(request.user)
            if not user_profile.is_manager():
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
    
    # 기본 History 데이터 조회
    histories = History.objects.filter(followup=followup).order_by('-created_at')
    
    # 기본 통계 계산
    delivery_histories = histories.filter(action_type='delivery_schedule')
    meeting_histories = histories.filter(action_type='customer_meeting')
    
    total_amount = 0
    for history in delivery_histories:
        if history.delivery_amount:
            total_amount += float(history.delivery_amount)
    
    # Schedule 기반 납품 일정
    schedule_deliveries = Schedule.objects.filter(
        followup=followup,
        activity_type='delivery'
    ).order_by('-visit_date')
    
    # 통합 납품 내역 생성 (템플릿 호환성을 위해)
    integrated_deliveries = []
    
    # History 기반 납품 내역
    for history in delivery_histories:
        # 이 History와 연결된 Schedule이 있고, 그 Schedule에 DeliveryItem이 있는지 확인
        has_schedule_items = False
        schedule_amount = 0
        if history.schedule:
            schedule_delivery_items = history.schedule.delivery_items_set.all()
            if schedule_delivery_items.exists():
                has_schedule_items = True
                # Schedule의 DeliveryItem 금액 계산
                for item in schedule_delivery_items:
                    if item.total_price:
                        schedule_amount += float(item.total_price)
        
        # History의 세금계산서 상태 정보 계산
        history_delivery_items = history.delivery_items_set.all()
        history_tax_status = {
            'has_items': history_delivery_items.exists(),
            'total_count': history_delivery_items.count(),
            'issued_count': history_delivery_items.filter(tax_invoice_issued=True).count(),
            'pending_count': history_delivery_items.filter(tax_invoice_issued=False).count(),
        }
        history_tax_status['all_issued'] = (history_tax_status['total_count'] > 0 and 
                                          history_tax_status['issued_count'] == history_tax_status['total_count'])
        history_tax_status['none_issued'] = (history_tax_status['total_count'] > 0 and 
                                            history_tax_status['issued_count'] == 0)
        
        # has_schedule_items인 경우 Schedule 금액만 사용, 아닌 경우 History 금액 사용
        if has_schedule_items:
            final_amount = schedule_amount
        else:
            final_amount = float(history.delivery_amount) if history.delivery_amount else 0
        
        delivery_data = {
            'type': 'history',
            'id': history.id,
            'date': (history.delivery_date or history.created_at.date()).strftime('%Y-%m-%d'),
            'schedule_id': history.schedule_id if history.schedule else None,
            'scheduleId': history.schedule_id if history.schedule else None,  # JavaScript 호환
            'items_display': history.delivery_items or None,
            'items': history.delivery_items or '',  # JavaScript에서 사용
            'amount': final_amount,
            'tax_invoice_issued': history.tax_invoice_issued,
            'content': history.content or '',
            'user': history.user.username,
            'has_schedule_items': has_schedule_items,
            'history_tax_status': history_tax_status,  # 세금계산서 상태 정보 추가
        }
        integrated_deliveries.append(delivery_data)
    
    # Schedule 기반 납품 일정 추가
    for schedule in schedule_deliveries:
        # 해당 Schedule과 연결된 History 찾기
        related_history = delivery_histories.filter(schedule=schedule).first()
        
        if related_history:
            # Schedule과 연결된 History가 있으면 History 데이터 우선 (이미 위에서 처리됨)
            continue
        else:
            # History에 연결되지 않은 Schedule - 일정 기반으로 표시
            # 하지만 혹시 다른 History에서 이 Schedule을 참조하는지 확인
            schedule_amount = 0
            schedule_items = '일정 기반 (품목 미확정)'
            
            # 이 Schedule을 참조하는 모든 History 검색 (delivery가 아닌 것도 포함)
            all_related_histories = History.objects.filter(schedule=schedule)
            
            for hist in all_related_histories:
                if hist.delivery_amount:
                    schedule_amount += float(hist.delivery_amount)
                if hist.delivery_items:
                    schedule_items = hist.delivery_items
            
            # Schedule에 직접 연결된 DeliveryItem들에서 금액과 품목 정보 가져오기
            schedule_delivery_items = schedule.delivery_items_set.all()
            
            if schedule_delivery_items.exists():
                item_names = []
                delivery_item_amount = 0
                
                for item in schedule_delivery_items:
                    if item.total_price:
                        delivery_item_amount += float(item.total_price)
                    item_names.append(f"{item.item_name}: {item.quantity}개")
                
                if delivery_item_amount > 0:
                    schedule_amount += delivery_item_amount
                
                if item_names:
                    schedule_items = ' / '.join(item_names)
            
            # Schedule의 세금계산서 상태 정보 계산
            schedule_tax_status = {
                'has_items': schedule_delivery_items.exists(),
                'total_count': schedule_delivery_items.count(),
                'issued_count': schedule_delivery_items.filter(tax_invoice_issued=True).count(),
                'pending_count': schedule_delivery_items.filter(tax_invoice_issued=False).count(),
            }
            schedule_tax_status['all_issued'] = (schedule_tax_status['total_count'] > 0 and 
                                              schedule_tax_status['issued_count'] == schedule_tax_status['total_count'])
            schedule_tax_status['none_issued'] = (schedule_tax_status['total_count'] > 0 and 
                                                schedule_tax_status['issued_count'] == 0)
            
            delivery_data = {
                'type': 'schedule_only',
                'id': schedule.id,
                'date': schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '',
                'schedule_id': schedule.id,
                'scheduleId': schedule.id,  # JavaScript 호환
                'items_display': schedule_items,
                'items': schedule_items if schedule_items != '일정 기반 (품목 미확정)' else '',  # JavaScript에서 사용
                'amount': schedule_amount,
                'scheduleAmount': schedule_amount,  # JavaScript 호환
                'tax_invoice_issued': False,
                'content': schedule.notes or '예정된 납품 일정',
                'user': schedule.user.username,
                'has_schedule_items': True,
                'schedule_tax_status': schedule_tax_status,  # 세금계산서 상태 정보 추가
            }
            integrated_deliveries.append(delivery_data)
    
    # 날짜순 정렬
    integrated_deliveries.sort(key=lambda x: x['date'], reverse=True)

    # JSON 직렬화
    try:
        integrated_deliveries_json = json.dumps(integrated_deliveries, ensure_ascii=False, cls=DjangoJSONEncoder)
    except Exception as e:
        integrated_deliveries_json = "[]"

    # 통합 데이터 기반 통계 계산
    integrated_total_amount = 0
    integrated_tax_issued = 0
    integrated_tax_pending = 0
    
    for delivery in integrated_deliveries:
        # 금액 계산
        if delivery['type'] == 'schedule_only':
            amount = delivery.get('scheduleAmount', 0)
        else:  # history
            amount = delivery.get('amount', 0)
        integrated_total_amount += amount
        
        # 세금계산서 상태 계산 (건별로 계산)
        delivery_has_issued_items = False
        delivery_has_pending_items = False
        
        if delivery['type'] == 'history':
            tax_status = delivery.get('history_tax_status', {})
            if tax_status.get('has_items', False):
                # DeliveryItem이 있는 경우 - 하나라도 발행된 것이 있으면 발행건으로 간주
                if tax_status.get('all_issued', False):
                    delivery_has_issued_items = True
                elif tax_status.get('none_issued', False):
                    delivery_has_pending_items = True
                else:
                    # 일부만 발행된 경우 - 혼재 상태이므로 발행건으로 간주
                    delivery_has_issued_items = True
            else:
                # 단순 History인 경우
                if delivery.get('tax_invoice_issued', False):
                    delivery_has_issued_items = True
                else:
                    delivery_has_pending_items = True
        else:  # schedule_only
            tax_status = delivery.get('schedule_tax_status', {})
            if tax_status.get('total_count', 0) > 0:
                if tax_status.get('all_issued', False):
                    delivery_has_issued_items = True
                elif tax_status.get('none_issued', False):
                    delivery_has_pending_items = True
                else:
                    # 일부만 발행된 경우 - 혼재 상태이므로 발행건으로 간주
                    delivery_has_issued_items = True
            # 품목이 없는 경우는 미발행으로 간주
            else:
                delivery_has_pending_items = True
        
        # 건별로 카운트
        if delivery_has_issued_items:
            integrated_tax_issued += 1
        elif delivery_has_pending_items:
            integrated_tax_pending += 1

    # 선결제 통계 계산 - 해당 고객에 등록된 모든 선결제
    prepayments = Prepayment.objects.filter(
        customer=followup
    )
    
    prepayment_total = prepayments.aggregate(total=Sum('amount'))['total'] or 0
    prepayment_balance = prepayments.aggregate(total=Sum('balance'))['total'] or 0
    prepayment_count = prepayments.count()

    context = {
        'followup': followup,
        'histories': histories,
        'total_amount': integrated_total_amount,
        'total_meetings': meeting_histories.count(),
        'total_deliveries': len(integrated_deliveries),
        'tax_invoices_issued': integrated_tax_issued,
        'tax_invoices_pending': integrated_tax_pending,
        'prepayment_total': prepayment_total,  # 선결제 총액
        'prepayment_balance': prepayment_balance,  # 선결제 잔액
        'prepayment_count': prepayment_count,  # 선결제 건수
        'chart_labels': json.dumps([], ensure_ascii=False),
        'chart_meetings': json.dumps([], ensure_ascii=False),
        'chart_deliveries': json.dumps([], ensure_ascii=False),
        'chart_amounts': json.dumps([], ensure_ascii=False),
        'delivery_histories': delivery_histories,
        'schedule_deliveries': schedule_deliveries,
        'integrated_deliveries': integrated_deliveries,
        'meeting_histories': meeting_histories,
        'chart_data': {
            'labels': json.dumps([], ensure_ascii=False),
            'meetings': json.dumps([], ensure_ascii=False),
            'deliveries': json.dumps([], ensure_ascii=False),
            'amounts': json.dumps([], ensure_ascii=False),
        },
        'page_title': f'{followup.company.name} - {followup.customer_name if followup.customer_name else "담당자 미정"}'
    }
    
    return render(request, 'reporting/customer_detail_report.html', context)

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
        
        # 권한 체크: 같은 회사에서 생성된 업체인지 확인
        user_profile_obj = getattr(request.user, 'userprofile', None)
        is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
        
        import logging
        logger = logging.getLogger(__name__)
        
        if not is_admin:
            if user_profile_obj and user_profile_obj.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
                if company.created_by not in same_company_users:
                    logger.warning(f"[FOLLOWUP_CREATE_AJAX] 사용자 {request.user.username}: 업체 {company.name} 접근 권한 없음")
                    return JsonResponse({
                        'success': False,
                        'error': '접근 권한이 없는 업체입니다.'
                    })
                logger.info(f"[FOLLOWUP_CREATE_AJAX] 사용자 {request.user.username}: 업체 {company.name}에 팔로우업 생성 권한 있음 (같은 회사)")
            else:
                logger.warning(f"[FOLLOWUP_CREATE_AJAX] 사용자 {request.user.username}: 회사 정보 없어 팔로우업 생성 불가")
                return JsonResponse({
                    'success': False,
                    'error': '회사 정보가 없어 팔로우업을 생성할 수 없습니다.'
                })
        else:
            logger.info(f"[FOLLOWUP_CREATE_AJAX] Admin 사용자 {request.user.username}: 업체 {company.name}에 팔로우업 생성 권한 있음")
        
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
                
                # History에 직접 연결된 DeliveryItem들도 함께 업데이트
                history_delivery_items = history.delivery_items_set.all()
                if history_delivery_items.exists():
                    updated_count = history_delivery_items.update(tax_invoice_issued=tax_invoice_issued)
                
                # History와 연결된 Schedule의 모든 DeliveryItem도 함께 업데이트
                if history.schedule:
                    schedule_updated_count = DeliveryItem.objects.filter(schedule=history.schedule).update(
                        tax_invoice_issued=tax_invoice_issued
                    )
                
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
                
        elif delivery_type == 'schedule_bulk':
            # Schedule의 모든 DeliveryItem 일괄 업데이트
            try:
                schedule = Schedule.objects.get(id=delivery_id)
                
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
                
                # Schedule의 모든 DeliveryItem 업데이트
                updated_count = DeliveryItem.objects.filter(schedule=schedule).update(
                    tax_invoice_issued=tax_invoice_issued
                )
                
                # 연결된 History도 함께 업데이트
                History.objects.filter(schedule=schedule).update(
                    tax_invoice_issued=tax_invoice_issued
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'세금계산서 상태가 업데이트되었습니다. (품목 {updated_count}개)',
                    'updated_count': updated_count
                })
                
            except Schedule.DoesNotExist:
                return JsonResponse({'error': '해당 일정을 찾을 수 없습니다.'}, status=404)
        
        else:
            return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"세금계산서 상태 업데이트 오류: {str(e)}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)

@login_required
@role_required(['admin', 'salesman', 'manager'])
def schedule_delivery_items_api(request, schedule_id):
    """Schedule의 DeliveryItem 정보를 반환하는 API"""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        # 권한 체크: Schedule의 followup을 통해 사용자 확인
        if schedule.followup and schedule.followup.user:
            if not can_access_user_data(request.user, schedule.followup.user):
                return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
            
            # Manager는 회사 체크를 건너뜀 (모든 데이터 조회 가능)
            user_profile = get_user_profile(request.user)
            if not user_profile.is_manager():
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    schedule_user_profile = getattr(schedule.followup.user, 'userprofile', None)
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
        
        return JsonResponse(debug_info, ensure_ascii=False, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"디버그 뷰 에러: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ============ Admin 전용 API 뷰들 ============

@role_required(['admin'])
@require_http_methods(["GET"])
def api_users_list(request):
    """사용자 목록 API (Admin 전용)"""
    try:
        users = User.objects.select_related('userprofile', 'userprofile__company').all()
        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'company': None
            }
            
            if hasattr(user, 'userprofile') and user.userprofile.company:
                user_data['company'] = user.userprofile.company.name
            
            users_data.append(user_data)
        
        return JsonResponse({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        logger.error(f"사용자 목록 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@role_required(['admin'])
@require_http_methods(["POST"])
@csrf_exempt
def api_change_company_creator(request):
    """업체 생성자 변경 API (Admin 전용)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        company_id = request.POST.get('company_id')
        new_creator_id = request.POST.get('new_creator_id')
        
        if not company_id or not new_creator_id:
            return JsonResponse({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }, status=400)
        
        # 업체 조회
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '존재하지 않는 업체입니다.'
            }, status=404)
        
        # 새 생성자 조회
        try:
            new_creator = User.objects.select_related('userprofile', 'userprofile__company').get(id=new_creator_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '존재하지 않는 사용자입니다.'
            }, status=404)
        
        # 기존 생성자 정보 로깅
        old_creator = company.created_by
        old_creator_info = 'None'
        if old_creator:
            old_creator_company = 'Unknown'
            if hasattr(old_creator, 'userprofile') and old_creator.userprofile.company:
                old_creator_company = old_creator.userprofile.company.name
            old_creator_info = f"{old_creator.username} ({old_creator_company})"
        
        # 새 생성자 정보
        new_creator_company = 'Unknown'
        if hasattr(new_creator, 'userprofile') and new_creator.userprofile.company:
            new_creator_company = new_creator.userprofile.company.name
        new_creator_info = f"{new_creator.username} ({new_creator_company})"
        
        logger.info(f"[ADMIN] 업체 생성자 변경 시작 - 업체: {company.name}, 기존: {old_creator_info}, 신규: {new_creator_info}")
        
        # 업체 생성자 변경
        company.created_by = new_creator
        company.save()
        
        logger.info(f"[ADMIN] 업체 생성자 변경 완료 - 업체: {company.name}, 신규 생성자: {new_creator_info}")
        
        # 응답 데이터
        response_data = {
            'success': True,
            'message': '업체 생성자가 성공적으로 변경되었습니다.',
            'new_creator': {
                'id': new_creator.id,
                'username': new_creator.username,
                'company': new_creator_company
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"업체 생성자 변경 API 에러: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_company_departments(request, company_id):
    """업체별 부서 목록 API"""
    try:
        # 업체 조회 및 접근 권한 확인
        company = get_object_or_404(Company, pk=company_id)
        
        # 접근 권한 확인
        same_company_users = User.objects.filter(
            userprofile__company=request.user.userprofile.company
        )
        
        # 업체가 사용자의 회사와 연결되어 있는지 확인
        if company.created_by not in same_company_users:
            return JsonResponse({'success': False, 'message': '접근 권한이 없습니다.'}, status=403)
        
        # 해당 업체의 부서 목록 조회
        departments = Department.objects.filter(
            company=company
        ).order_by('name')
        
        departments_data = []
        for dept in departments:
            # 각 부서별 고객 수 직접 계산
            followup_count = FollowUp.objects.filter(department=dept).count()
            
            dept_data = {
                'id': dept.id,
                'name': dept.name,
                'followup_count': followup_count,
                'created_date': dept.created_at.strftime('%Y-%m-%d'),
                'created_by': dept.created_by.username if dept.created_by else '정보 없음'
            }
            departments_data.append(dept_data)
        
        return JsonResponse({
            'success': True,
            'company_name': company.name,
            'departments': departments_data,
            'total_count': len(departments_data)
        })
        
    except Exception as e:
        logger.error(f"업체별 부서 목록 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_company_customers(request, company_id):
    """업체별 고객 정보 목록 API"""
    try:
        # 업체 조회 및 접근 권한 확인
        company = get_object_or_404(Company, pk=company_id)
        
        # 접근 권한 확인
        same_company_users = User.objects.filter(
            userprofile__company=request.user.userprofile.company
        )
        
        # 업체가 사용자의 회사와 연결되어 있는지 확인
        if company.created_by not in same_company_users:
            return JsonResponse({'success': False, 'message': '접근 권한이 없습니다.'}, status=403)
        
        # 해당 업체의 고객 정보들 조회
        followups = FollowUp.objects.filter(
            company=company
        ).select_related('department')
        
        customers_data = []
        for followup in followups:
            customer_data = {
                'id': followup.id,
                'customer_name': followup.customer_name or '고객명 미정',
                'phone': followup.phone_number or '-',
                'email': followup.email or '-',
                'position': followup.manager or '-',
                'department_name': followup.department.name if followup.department else '-',
                'created_date': followup.created_at.strftime('%Y-%m-%d'),
                'last_contact': followup.updated_at.strftime('%Y-%m-%d') if followup.updated_at else '연락 없음'
            }
            customers_data.append(customer_data)
        
        return JsonResponse({
            'success': True,
            'company_name': company.name,
            'customers': customers_data,
            'total_count': len(customers_data)
        })
        
    except Exception as e:
        logger.error(f"업체별 고객 정보 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============ 프로필 관리 뷰들 ============

@login_required
def profile_view(request):
    """사용자 프로필 조회"""
    context = {
        'page_title': '프로필 정보',
        'user': request.user,
    }
    return render(request, 'reporting/profile.html', context)


@login_required
def profile_edit_view(request):
    """사용자 프로필 수정"""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    from django import forms
    
    class ProfileEditForm(forms.Form):
        username = forms.CharField(
            max_length=150,
            label="사용자명",
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '사용자명을 입력하세요'
            })
        )
        first_name = forms.CharField(
            max_length=30,
            label="이름",
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '이름을 입력하세요'
            })
        )
        last_name = forms.CharField(
            max_length=30,
            label="성",
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '성을 입력하세요'
            })
        )
        email = forms.EmailField(
            label="이메일",
            required=False,
            widget=forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '이메일을 입력하세요'
            })
        )
        
        def __init__(self, user, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.user = user
            # 현재 값으로 초기화
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
        def clean_username(self):
            username = self.cleaned_data['username']
            # 현재 사용자가 아닌 다른 사용자가 같은 사용자명을 사용하는지 확인
            if User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
                raise forms.ValidationError("이미 사용 중인 사용자명입니다.")
            return username
    
    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            # 프로필 정보 수정
            profile_form = ProfileEditForm(request.user, request.POST)
            password_form = PasswordChangeForm(request.user)
            
            if profile_form.is_valid():
                user = request.user
                user.username = profile_form.cleaned_data['username']
                user.first_name = profile_form.cleaned_data['first_name']
                user.last_name = profile_form.cleaned_data['last_name']
                user.email = profile_form.cleaned_data['email']
                user.save()
                
                messages.success(request, '프로필 정보가 성공적으로 수정되었습니다.')
                return redirect('reporting:profile')
            else:
                messages.error(request, '프로필 정보 수정 중 오류가 발생했습니다.')
                
        elif 'password_submit' in request.POST:
            # 비밀번호 변경
            profile_form = ProfileEditForm(request.user)
            password_form = PasswordChangeForm(request.user, request.POST)
            
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # 세션 유지
                messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
                return redirect('reporting:profile')
            else:
                messages.error(request, '비밀번호 변경 중 오류가 발생했습니다.')
    else:
        profile_form = ProfileEditForm(request.user)
        password_form = PasswordChangeForm(request.user)
    
    context = {
        'page_title': '프로필 수정',
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'reporting/profile_edit.html', context)


# ===== 펀넬 관리 뷰 =====
from .models import OpportunityTracking, Quote, FunnelStage
from .funnel_analytics import FunnelAnalytics


@login_required
def funnel_dashboard_view(request):
    """펀넬 대시보드 - 전체 개요"""
    import logging
    logger = logging.getLogger(__name__)
    
    analytics = FunnelAnalytics()
    user_profile = get_user_profile(request.user)
    
    # FunnelStage 초기 데이터 확인 및 생성
    if not FunnelStage.objects.exists():
        default_stages = [
            {'name': 'lead', 'display_name': '리드', 'stage_order': 1, 'default_probability': 10, 'color': '#94a3b8', 'icon': 'fa-user-plus'},
            {'name': 'contact', 'display_name': '컨택', 'stage_order': 2, 'default_probability': 25, 'color': '#60a5fa', 'icon': 'fa-phone'},
            {'name': 'quote', 'display_name': '견적', 'stage_order': 3, 'default_probability': 40, 'color': '#8b5cf6', 'icon': 'fa-file-invoice'},
            {'name': 'negotiation', 'display_name': '협상', 'stage_order': 4, 'default_probability': 60, 'color': '#f59e0b', 'icon': 'fa-handshake'},
            {'name': 'closing', 'display_name': '클로징', 'stage_order': 5, 'default_probability': 80, 'color': '#10b981', 'icon': 'fa-check-circle'},
            {'name': 'won', 'display_name': '수주', 'stage_order': 6, 'default_probability': 100, 'color': '#22c55e', 'icon': 'fa-trophy'},
            {'name': 'lost', 'display_name': '실주', 'stage_order': 7, 'default_probability': 0, 'color': '#ef4444', 'icon': 'fa-times-circle'},
        ]
        for stage_data in default_stages:
            FunnelStage.objects.create(**stage_data)
    
    # 매니저용 실무자 필터
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 필터: 사용자별
    filter_user = None
    selected_user = None
    
    if user_profile.can_view_all_users():
        # Admin이나 Manager
        # 전체 팀원 선택 시 세션 초기화
        if view_all:
            if 'selected_user_id' in request.session:
                del request.session['selected_user_id']
            filter_user = None
        else:
            user_filter = request.GET.get('user')
            if not user_filter:
                user_filter = request.session.get('selected_user_id')
            
            if user_filter:
                request.session['selected_user_id'] = str(user_filter)
                # 특정 실무자 선택
                try:
                    accessible_users = get_accessible_users(request.user)
                    selected_user = accessible_users.get(id=user_filter)
                    filter_user = selected_user
                except (User.DoesNotExist, ValueError):
                    filter_user = None
            else:
                filter_user = None
    else:
        # Salesman은 본인 데이터만
        filter_user = request.user
    
    # 파이프라인 요약
    pipeline_summary = analytics.get_pipeline_summary(user=filter_user)
    
    # 단계별 분석
    stage_breakdown = analytics.get_stage_breakdown(user=filter_user)
    
    # OpportunityTracking 데이터 확인 (로그 제거)
    
    # 상위 영업 기회
    top_opportunities = analytics.get_top_opportunities(limit=10, user=filter_user)
    
    # 수주/실주 요약
    won_lost_summary = analytics.get_won_lost_summary(user=filter_user)
    
    # 견적 승패 분석 (올해 기준)
    from django.utils import timezone
    current_year = timezone.now().year
    
    quotes = Schedule.objects.filter(
        activity_type='quote',
        visit_date__year=current_year
    )
    
    if filter_user:
        quotes = quotes.filter(user=filter_user)
    
    quote_total = quotes.count()
    quote_won = quotes.filter(status='completed').count()
    quote_lost = quotes.filter(status='cancelled').count()
    quote_pending = quotes.filter(status='scheduled').count()
    
    # 월별 견적 승패 (최근 12개월)
    monthly_quote_stats = []
    for i in range(11, -1, -1):
        target_date = timezone.now() - timezone.timedelta(days=30*i)
        month_quotes = quotes.filter(
            visit_date__year=target_date.year,
            visit_date__month=target_date.month
        )
        
        monthly_quote_stats.append({
            'month_name': f'{target_date.month}월',
            'total': month_quotes.count(),
            'won': month_quotes.filter(status='completed').count(),
            'lost': month_quotes.filter(status='cancelled').count(),
            'pending': month_quotes.filter(status='scheduled').count(),
        })
    
    # 차트 데이터 (JSON)
    stage_chart_data = {
        'labels': [s['stage'] for s in stage_breakdown],
        'counts': [s['count'] for s in stage_breakdown],
        'values': [float(s['weighted_value']) for s in stage_breakdown],
        'colors': [s['color'] for s in stage_breakdown],
    }
    
    quote_chart_data = {
        'labels': [s['month_name'] for s in monthly_quote_stats],
        'won': [s['won'] for s in monthly_quote_stats],
        'lost': [s['lost'] for s in monthly_quote_stats],
        'pending': [s['pending'] for s in monthly_quote_stats],
    }
    
    # 사용자 목록 (Admin/Manager용)
    accessible_users = get_accessible_users(request.user) if user_profile.can_view_all_users() else []
    salesman_users = accessible_users.filter(userprofile__role='salesman') if user_profile.can_view_all_users() else []
    
    context = {
        'page_title': '펀넬 대시보드',
        'pipeline_summary': pipeline_summary,
        'stage_breakdown': stage_breakdown,
        'top_opportunities': top_opportunities,
        'won_lost_summary': won_lost_summary,
        'quote_total': quote_total,
        'quote_won': quote_won,
        'quote_lost': quote_lost,
        'quote_pending': quote_pending,
        'current_year': current_year,
        'stage_chart_data': json.dumps(stage_chart_data, cls=DjangoJSONEncoder),
        'quote_chart_data': json.dumps(quote_chart_data, cls=DjangoJSONEncoder),
        'filter_user': filter_user,
        'users': accessible_users,
        'salesman_users': salesman_users,
        'selected_user': selected_user,
        'view_all': view_all,
    }
    
    return render(request, 'reporting/funnel/dashboard.html', context)


@login_required
def funnel_pipeline_view(request):
    """펀넬 파이프라인 - 칸반 보드"""
    user_profile = get_user_profile(request.user)
    
    # 매니저용 실무자 필터
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 필터: 사용자별
    filter_user = None
    selected_user = None
    
    if user_profile.can_view_all_users():
        # Admin이나 Manager
        if view_all:
            # 전체보기 모드
            filter_user = None
        elif selected_user_id:
            # 특정 실무자 선택
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=selected_user_id)
                filter_user = selected_user
            except User.DoesNotExist:
                filter_user = None
        elif request.GET.get('user'):
            # 기존 호환성
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=request.GET.get('user'))
                filter_user = selected_user
            except User.DoesNotExist:
                pass
    else:
        # Salesman은 본인 데이터만
        filter_user = request.user
    
    # 단계 목록
    stages = FunnelStage.objects.all().order_by('stage_order')
    
    # 각 단계별 영업 기회
    pipeline_data = []
    for stage in stages:
        opps = OpportunityTracking.objects.filter(
            current_stage=stage.name
        ).select_related('followup', 'followup__company', 'followup__user')
        
        if filter_user:
            opps = opps.filter(followup__user=filter_user)
        
        opportunities = []
        for opp in opps.order_by('-weighted_revenue'):
            opportunities.append({
                'id': opp.id,
                'customer_name': opp.followup.customer_name or '고객명 미정',
                'company_name': opp.followup.company.name if opp.followup.company else '업체명 미정',
                'expected_revenue': opp.expected_revenue,
                'weighted_revenue': opp.weighted_revenue,
                'backlog_amount': opp.backlog_amount,
                'probability': opp.probability,
                'expected_close_date': opp.expected_close_date,
                'user': opp.followup.user.username,
                'followup_id': opp.followup.id,
            })
        
        pipeline_data.append({
            'stage': stage,
            'opportunities': opportunities,
            'count': len(opportunities),
            'total_weighted': sum(o['weighted_revenue'] for o in opportunities),
        })
    
    # 사용자 목록 (Admin/Manager용)
    accessible_users = get_accessible_users(request.user) if user_profile.can_view_all_users() else []
    salesman_users = accessible_users.filter(userprofile__role='salesman') if user_profile.can_view_all_users() else []
    
    context = {
        'page_title': '파이프라인 보드',
        'pipeline_data': pipeline_data,
        'filter_user': filter_user,
        'users': accessible_users,
        'salesman_users': salesman_users,
        'selected_user': selected_user,
        'view_all': view_all,
    }
    
    return render(request, 'reporting/funnel/pipeline.html', context)


@login_required
def funnel_analytics_view(request):
    """펀넬 분석 - 전환율 및 병목 분석"""
    analytics = FunnelAnalytics()
    user_profile = get_user_profile(request.user)
    
    # 매니저용 실무자 필터
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 필터: 사용자별
    filter_user = None
    selected_user = None
    
    if user_profile.can_view_all_users():
        # Admin이나 Manager
        if view_all:
            # 전체보기 모드
            filter_user = None
        elif selected_user_id:
            # 특정 실무자 선택
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=selected_user_id)
                filter_user = selected_user
            except User.DoesNotExist:
                filter_user = None
        elif request.GET.get('user'):
            # 기존 호환성
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=request.GET.get('user'))
                filter_user = selected_user
            except User.DoesNotExist:
                pass
    else:
        # Salesman은 본인 데이터만
        filter_user = request.user
    
    # 전환율 분석
    conversion_rates = analytics.get_conversion_rates(user=filter_user)
    
    # 병목 분석
    bottleneck_analysis = analytics.get_bottleneck_analysis(user=filter_user)
    
    # 단계별 평균 체류 시간 차트
    duration_chart_data = {
        'labels': [b['stage'] for b in bottleneck_analysis],
        'expected': [b['expected_duration'] for b in bottleneck_analysis],
        'actual': [b['actual_duration'] for b in bottleneck_analysis],
        'colors': [b['color'] for b in bottleneck_analysis],
    }
    
    # 전환율 차트
    conversion_chart_data = {
        'labels': [f"{c['from_stage']} → {c['to_stage']}" for c in conversion_rates],
        'rates': [c['rate'] for c in conversion_rates],
    }
    
    # 사용자 목록 (Admin/Manager용)
    accessible_users = get_accessible_users(request.user) if user_profile.can_view_all_users() else []
    salesman_users = accessible_users.filter(userprofile__role='salesman') if user_profile.can_view_all_users() else []
    
    context = {
        'page_title': '펀넬 분석',
        'conversion_rates': conversion_rates,
        'bottleneck_analysis': bottleneck_analysis,
        'duration_chart_data': json.dumps(duration_chart_data, cls=DjangoJSONEncoder),
        'conversion_chart_data': json.dumps(conversion_chart_data, cls=DjangoJSONEncoder),
        'filter_user': filter_user,
        'users': accessible_users,
        'salesman_users': salesman_users,
        'selected_user': selected_user,
        'view_all': view_all,
    }
    
    return render(request, 'reporting/funnel/analytics.html', context)


@login_required
def funnel_forecast_view(request):
    """펀넬 예측 - 매출 예측"""
    analytics = FunnelAnalytics()
    user_profile = get_user_profile(request.user)
    
    # 매니저용 실무자 필터
    selected_user_id = request.GET.get('user_id')
    view_all = request.GET.get('view_all') == 'true'
    
    # 필터: 사용자별
    filter_user = None
    selected_user = None
    
    if user_profile.can_view_all_users():
        # Admin이나 Manager
        if view_all:
            # 전체보기 모드
            filter_user = None
        elif selected_user_id:
            # 특정 실무자 선택
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=selected_user_id)
                filter_user = selected_user
            except User.DoesNotExist:
                filter_user = None
        elif request.GET.get('user'):
            # 기존 호환성
            try:
                accessible_users = get_accessible_users(request.user)
                selected_user = accessible_users.get(id=request.GET.get('user'))
                filter_user = selected_user
            except User.DoesNotExist:
                pass
    else:
        # Salesman은 본인 데이터만
        filter_user = request.user
    
    # 월별 예측 (6개월)
    monthly_forecast = analytics.get_monthly_forecast(months=6, user=filter_user)
    
    # 단계별 분석 (예측에 포함될 기회들)
    stage_breakdown = analytics.get_stage_breakdown(user=filter_user)
    
    # 예측 차트 데이터
    forecast_chart_data = {
        'labels': [f['month_name'] for f in monthly_forecast],
        'expected': [float(f['expected']) for f in monthly_forecast],
        'weighted': [float(f['weighted']) for f in monthly_forecast],
        'counts': [f['count'] for f in monthly_forecast],
    }
    
    # 단계별 기여도 차트
    contribution_chart_data = {
        'labels': [s['stage'] for s in stage_breakdown if s['stage_code'] not in ['won', 'quote_lost']],
        'values': [float(s['weighted_value']) for s in stage_breakdown if s['stage_code'] not in ['won', 'quote_lost']],
        'colors': [s['color'] for s in stage_breakdown if s['stage_code'] not in ['won', 'quote_lost']],
    }
    
    # 사용자 목록 (Admin/Manager용)
    accessible_users = get_accessible_users(request.user) if user_profile.can_view_all_users() else []
    salesman_users = accessible_users.filter(userprofile__role='salesman') if user_profile.can_view_all_users() else []
    
    context = {
        'page_title': '매출 예측',
        'monthly_forecast': monthly_forecast,
        'stage_breakdown': [s for s in stage_breakdown if s['stage_code'] not in ['won', 'quote_lost']],
        'forecast_chart_data': json.dumps(forecast_chart_data, cls=DjangoJSONEncoder),
        'contribution_chart_data': json.dumps(contribution_chart_data, cls=DjangoJSONEncoder),
        'filter_user': filter_user,
        'users': accessible_users,
        'salesman_users': salesman_users,
        'selected_user': selected_user,
        'view_all': view_all,
    }
    
    return render(request, 'reporting/funnel/forecast.html', context)


@login_required
@require_http_methods(["POST"])
def update_opportunity_stage_api(request, opportunity_id):
    """
    OpportunityTracking의 단계를 업데이트하는 API
    드래그앤드롭으로 단계 변경 시 호출
    """
    try:
        opportunity = OpportunityTracking.objects.get(id=opportunity_id)
        
        # 권한 체크 - 담당자 또는 관리자만 수정 가능
        if not (request.user == opportunity.followup.user or 
                request.user.is_staff or 
                request.user.is_superuser):
            return JsonResponse({
                'success': False,
                'error': '권한이 없습니다.'
            }, status=403)
        
        # 요청에서 새로운 단계 가져오기
        import json as json_module
        data = json_module.loads(request.body)
        new_stage = data.get('stage')
        
        if not new_stage:
            return JsonResponse({
                'success': False,
                'error': '단계가 지정되지 않았습니다.'
            }, status=400)
        
        # 단계 업데이트
        old_stage = opportunity.current_stage
        opportunity.update_stage(new_stage)
        opportunity.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{old_stage}에서 {new_stage}(으)로 단계가 변경되었습니다.',
            'old_stage': old_stage,
            'new_stage': new_stage
        })
        
    except OpportunityTracking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '영업 기회를 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def followup_quote_items_api(request, followup_id):
    """
    특정 팔로우업의 견적 품목을 가져오는 API
    납품 일정 생성 시 견적에서 품목을 불러오기 위해 사용
    """
    try:
        followup = get_object_or_404(FollowUp, pk=followup_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, followup.user):
            return JsonResponse({
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # 해당 팔로우업의 모든 견적 일정 조회 (납품되지 않은 것만)
        quote_schedules = Schedule.objects.filter(
            followup=followup,
            activity_type='quote'
        ).order_by('-visit_date', '-visit_time')
        
        if not quote_schedules.exists():
            return JsonResponse({
                'error': '이 고객의 견적이 없습니다.'
            })
        
        # 모든 견적 정보 수집 (납품되지 않은 것만)
        from reporting.models import DeliveryItem
        quotes_data = []
        
        for quote_schedule in quote_schedules:
            logger.info(f"[QUOTE_ITEMS_API] Schedule ID: {quote_schedule.id}, visit_date: {quote_schedule.visit_date}")
            
            # 이미 납품된 견적인지 확인
            # 같은 opportunity에 납품 일정이 있으면 제외
            if quote_schedule.opportunity:
                has_delivery = Schedule.objects.filter(
                    opportunity=quote_schedule.opportunity,
                    activity_type='delivery'
                ).exists()
                
                if has_delivery:
                    logger.info(f"[QUOTE_ITEMS_API] Quote {quote_schedule.id} already delivered, skipping")
                    continue
            
            items = DeliveryItem.objects.filter(schedule=quote_schedule)
            
            if items.exists():
                items_data = [{
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                } for item in items]
                
                quote_data = {
                    'schedule_id': quote_schedule.id,
                    'quote_date': quote_schedule.visit_date.strftime('%Y-%m-%d'),
                    'expected_revenue': float(quote_schedule.expected_revenue) if quote_schedule.expected_revenue else 0,
                    'items': items_data,
                    'opportunity_title': quote_schedule.opportunity.title if quote_schedule.opportunity else None,
                    'opportunity_id': quote_schedule.opportunity.id if quote_schedule.opportunity else None,  # opportunity ID 추가
                }
                quotes_data.append(quote_data)
                logger.info(f"[QUOTE_ITEMS_API] Added quote: {quote_data['quote_date']}, opp_id: {quote_data['opportunity_id']}")
        
        if not quotes_data:
            return JsonResponse({
                'error': '견적 품목이 없습니다.'
            })
        
        logger.info(f"[QUOTE_ITEMS_API] Returning {len(quotes_data)} quotes")
        return JsonResponse({
            'success': True,
            'quotes': quotes_data,  # 모든 견적 반환
            'count': len(quotes_data),
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def followup_meetings_api(request, followup_id):
    """
    특정 팔로우업의 미팅 일정을 가져오는 API
    견적 일정 생성 시 미팅을 선택하여 펀넬을 연결하기 위해 사용
    """
    try:
        followup = get_object_or_404(FollowUp, pk=followup_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, followup.user):
            return JsonResponse({
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # 해당 팔로우업의 미팅 일정 조회
        # 조건: OpportunityTracking이 있고, current_stage가 'contact'인 미팅만 (아직 견적과 연결되지 않은 미팅)
        from reporting.models import OpportunityTracking
        
        # contact 단계의 OpportunityTracking 찾기
        contact_opportunities = OpportunityTracking.objects.filter(
            followup=followup,
            current_stage='contact'
        ).values_list('id', flat=True)
        
        # 해당 OpportunityTracking과 연결된 미팅 일정 조회
        meeting_schedules = Schedule.objects.filter(
            followup=followup,
            activity_type='customer_meeting',
            opportunity_id__in=contact_opportunities
        ).select_related('opportunity').order_by('-visit_date', '-visit_time')
        
        if not meeting_schedules.exists():
            return JsonResponse({
                'error': '이 고객의 미팅 일정이 없습니다.'
            })
        
        # 모든 미팅 정보 수집
        meetings_data = []
        
        for meeting_schedule in meeting_schedules:
            logger.info(f"[MEETINGS_API] Schedule ID: {meeting_schedule.id}, visit_date: {meeting_schedule.visit_date}")
            
            meeting_data = {
                'schedule_id': meeting_schedule.id,
                'visit_date': meeting_schedule.visit_date.strftime('%Y-%m-%d'),
                'expected_revenue': float(meeting_schedule.expected_revenue) if meeting_schedule.expected_revenue else None,
                'probability': meeting_schedule.probability,
                'expected_close_date': meeting_schedule.expected_close_date.strftime('%Y-%m-%d') if meeting_schedule.expected_close_date else None,
                'notes': meeting_schedule.notes,
                'opportunity_title': meeting_schedule.opportunity.title if meeting_schedule.opportunity else None,
                'opportunity_id': meeting_schedule.opportunity.id if meeting_schedule.opportunity else None,
            }
            meetings_data.append(meeting_data)
            logger.info(f"[MEETINGS_API] Added meeting: {meeting_data['visit_date']}, opp_id: {meeting_data['opportunity_id']}")
        
        logger.info(f"[MEETINGS_API] Returning {len(meetings_data)} meetings")
        return JsonResponse({
            'success': True,
            'meetings': meetings_data,
            'count': len(meetings_data),
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)


# ============================================
# 선결제 관리
# ============================================

@login_required
def prepayment_list_view(request):
    """선결제 목록 뷰"""
    from reporting.models import Prepayment
    from django.db.models import Q, Sum
    from django.contrib.auth.models import User
    
    user_profile = get_user_profile(request.user)
    base_queryset = Prepayment.objects.select_related('customer', 'company', 'created_by')
    
    # 매니저 세션 기반 필터 적용
    view_all = request.GET.get('view_all') == 'true'
    selected_user = None
    
    if user_profile.can_view_all_users():
        # 전체 팀원 선택 시 세션 초기화
        if view_all:
            if 'selected_user_id' in request.session:
                del request.session['selected_user_id']
            # 접근 가능한 모든 사용자의 선결제 조회
            accessible_users = get_accessible_users(request.user)
            base_queryset = base_queryset.filter(created_by__in=accessible_users)
        else:
            user_filter = request.GET.get('user')
            # user_filter가 없으면 세션에서 가져오기
            if not user_filter:
                user_filter = request.session.get('selected_user_id')
            
            if user_filter:
                try:
                    accessible_users = get_accessible_users(request.user)
                    selected_user = accessible_users.get(id=user_filter)
                    # 세션에 저장
                    request.session['selected_user_id'] = str(user_filter)
                    # 선택된 사용자의 선결제만 조회
                    base_queryset = base_queryset.filter(created_by=selected_user)
                except User.DoesNotExist:
                    # 잘못된 세션 값 제거
                    if 'selected_user_id' in request.session:
                        del request.session['selected_user_id']
                    # 접근 가능한 모든 사용자의 선결제 조회
                    accessible_users = get_accessible_users(request.user)
                    base_queryset = base_queryset.filter(created_by__in=accessible_users)
            else:
                # 접근 가능한 모든 사용자의 선결제 조회
                accessible_users = get_accessible_users(request.user)
                base_queryset = base_queryset.filter(created_by__in=accessible_users)
    elif user_profile.role == 'admin':
        # Admin은 모든 선결제 조회 가능
        pass
    else:
        # 일반 사용자는 본인이 등록한 선결제만 조회
        base_queryset = base_queryset.filter(created_by=request.user)
    
    # 검색 필터
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        base_queryset = base_queryset.filter(
            Q(customer__customer_name__icontains=search_query) |
            Q(payer_name__icontains=search_query) |
            Q(memo__icontains=search_query)
        )
    
    if status_filter:
        base_queryset = base_queryset.filter(status=status_filter)
    
    # 정렬
    prepayments = base_queryset.order_by('-payment_date', '-created_at')
    
    # 통계
    stats = base_queryset.aggregate(
        total_amount=Sum('amount'),
        total_balance=Sum('balance')
    )
    
    # 사용 금액 계산
    total_amount = stats['total_amount'] or 0
    total_balance = stats['total_balance'] or 0
    stats['total_used'] = total_amount - total_balance
    
    # 페이지네이션 추가
    from django.core.paginator import Paginator
    paginator = Paginator(prepayments, 30)  # 페이지당 30개
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': '선결제 현황',
        'prepayments': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'stats': stats,
    }
    
    return render(request, 'reporting/prepayment/list.html', context)


@login_required
def prepayment_create_view(request):
    """선결제 등록 뷰"""
    from reporting.models import Prepayment, FollowUp
    from django import forms
    
    # Tailwind CSS 클래스
    input_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    select_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    textarea_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    
    class PrepaymentForm(forms.ModelForm):
        customer = forms.ModelChoiceField(
            queryset=FollowUp.objects.all(),
            label='고객',
            widget=forms.Select(attrs={'class': select_class})
        )
        
        class Meta:
            model = Prepayment
            fields = ['customer', 'amount', 'payment_date', 'payment_method', 'payer_name', 'memo']
            widgets = {
                'amount': forms.NumberInput(attrs={'class': input_class, 'placeholder': '금액 입력'}),
                'payment_date': forms.DateInput(attrs={'class': input_class, 'type': 'date'}),
                'payment_method': forms.Select(attrs={'class': select_class}),
                'payer_name': forms.TextInput(attrs={'class': input_class, 'placeholder': '입금자명 (선택)'}),
                'memo': forms.Textarea(attrs={'class': textarea_class, 'rows': 3, 'placeholder': '메모 (선택)'}),
            }
    
    if request.method == 'POST':
        form = PrepaymentForm(request.POST)
        if form.is_valid():
            prepayment = form.save(commit=False)
            prepayment.balance = prepayment.amount  # 초기 잔액 = 입금액
            prepayment.company = prepayment.customer.company
            prepayment.created_by = request.user
            prepayment.save()
            
            messages.success(request, f'{prepayment.customer.customer_name}의 선결제 {prepayment.amount:,}원이 등록되었습니다.')
            return redirect('reporting:prepayment_detail', pk=prepayment.pk)
    else:
        # 한국 시간대의 오늘 날짜를 기본값으로 설정
        from django.utils import timezone
        import pytz
        korea_tz = pytz.timezone('Asia/Seoul')
        today_korea = timezone.now().astimezone(korea_tz).date()
        
        form = PrepaymentForm(initial={'payment_date': today_korea})
    
    # 고객 목록 필터링 (회사별)
    user_profile = get_user_profile(request.user)
    if user_profile and user_profile.role != 'admin':
        # 같은 UserCompany 소속 사용자들이 등록한 고객만 표시
        from reporting.models import UserProfile
        same_company_users = UserProfile.objects.filter(
            company=user_profile.company
        ).values_list('user_id', flat=True)
        form.fields['customer'].queryset = FollowUp.objects.filter(user_id__in=same_company_users)
    
    context = {
        'page_title': '선결제 등록',
        'form': form,
    }
    
    return render(request, 'reporting/prepayment/form.html', context)


@login_required
def prepayment_detail_view(request, pk):
    """선결제 상세 뷰"""
    from reporting.models import Prepayment
    
    prepayment = get_object_or_404(Prepayment, pk=pk)
    
    # 권한 체크 - 선결제를 등록한 사용자의 데이터에 접근 가능한지 확인
    if not can_access_user_data(request.user, prepayment.created_by):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:prepayment_list')
    
    # 사용 내역
    usages = prepayment.usages.select_related(
        'schedule', 
        'schedule__followup'
    ).prefetch_related(
        'schedule__delivery_items_set'
    ).order_by('-used_at')
    
    # 각 usage에 delivery_items 첨부
    for usage in usages:
        if usage.schedule:
            usage.delivery_items = usage.schedule.delivery_items_set.all()
        else:
            usage.delivery_items = []
    
    # 금액 계산
    total_used = prepayment.amount - prepayment.balance
    usage_percent = 0
    if prepayment.amount > 0:
        usage_percent = round((total_used / prepayment.amount) * 100, 1)
        balance_percent = round((prepayment.balance / prepayment.amount) * 100, 1)
    else:
        balance_percent = 0
    
    context = {
        'page_title': f'선결제 상세 - {prepayment.customer.customer_name}',
        'prepayment': prepayment,
        'usages': usages,
        'total_used': total_used,
        'usage_percent': usage_percent,
        'balance_percent': balance_percent,
    }
    
    return render(request, 'reporting/prepayment/detail.html', context)


@login_required
def prepayment_edit_view(request, pk):
    """선결제 수정 뷰"""
    from reporting.models import Prepayment, FollowUp
    from django import forms
    
    prepayment = get_object_or_404(Prepayment, pk=pk)
    
    # 권한 체크
    user_profile = get_user_profile(request.user)
    if user_profile and user_profile.role != 'admin':
        from reporting.models import UserProfile
        same_company_users = UserProfile.objects.filter(
            company=user_profile.company
        ).values_list('user_id', flat=True)
        
        if prepayment.created_by_id not in same_company_users:
            messages.error(request, '접근 권한이 없습니다.')
            return redirect('reporting:prepayment_list')
    
    # Tailwind CSS 클래스
    input_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    select_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    textarea_class = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    
    class PrepaymentEditForm(forms.ModelForm):
        customer = forms.ModelChoiceField(
            queryset=FollowUp.objects.all(),
            label='고객',
            widget=forms.Select(attrs={'class': select_class})
        )
        
        class Meta:
            model = Prepayment
            fields = ['customer', 'amount', 'balance', 'payment_date', 'payment_method', 'payer_name', 'status', 'memo']
            widgets = {
                'amount': forms.NumberInput(attrs={'class': input_class, 'placeholder': '금액 입력'}),
                'balance': forms.NumberInput(attrs={'class': input_class, 'placeholder': '잔액'}),
                'payment_date': forms.DateInput(attrs={'class': input_class, 'type': 'date'}),
                'payment_method': forms.Select(attrs={'class': select_class}),
                'payer_name': forms.TextInput(attrs={'class': input_class, 'placeholder': '입금자명 (선택)'}),
                'status': forms.Select(attrs={'class': select_class}),
                'memo': forms.Textarea(attrs={'class': textarea_class, 'rows': 3, 'placeholder': '메모 (선택)'}),
            }
    
    if request.method == 'POST':
        form = PrepaymentEditForm(request.POST, instance=prepayment)
        if form.is_valid():
            prepayment = form.save(commit=False)
            prepayment.company = prepayment.customer.company
            prepayment.save()
            
            messages.success(request, '선결제 정보가 수정되었습니다.')
            return redirect('reporting:prepayment_detail', pk=prepayment.pk)
    else:
        form = PrepaymentEditForm(instance=prepayment)
    
    # 고객 목록 필터링 (회사별)
    user_profile = get_user_profile(request.user)
    if user_profile and user_profile.company:
        accessible_users = get_accessible_users(request.user)
        form.fields['customer'].queryset = FollowUp.objects.filter(user__in=accessible_users)
    
    context = {
        'page_title': '선결제 수정',
        'form': form,
        'prepayment': prepayment,
    }
    
    return render(request, 'reporting/prepayment/form.html', context)


@login_required
def prepayment_delete_view(request, pk):
    """선결제 삭제 뷰"""
    from reporting.models import Prepayment
    from django.utils import timezone
    
    prepayment = get_object_or_404(Prepayment, pk=pk)
    
    # 권한 체크
    user_profile = get_user_profile(request.user)
    if user_profile and user_profile.role != 'admin':
        from reporting.models import UserProfile
        same_company_users = UserProfile.objects.filter(
            company=user_profile.company
        ).values_list('user_id', flat=True)
        
        if prepayment.created_by_id not in same_company_users:
            messages.error(request, '접근 권한이 없습니다.')
            return redirect('reporting:prepayment_list')
    
    if request.method == 'POST':
        # 사용 내역 개수 확인
        usage_count = prepayment.usages.count()
        
        # 취소 요청인 경우
        if request.POST.get('action') == 'cancel':
            prepayment.status = 'cancelled'
            prepayment.cancelled_at = timezone.now()
            prepayment.cancel_reason = request.POST.get('cancel_reason', '사용자 요청으로 취소')
            prepayment.save()
            messages.success(request, f'{prepayment.customer.customer_name}의 선결제가 취소되었습니다.')
            return redirect('reporting:prepayment_detail', pk=pk)
        
        # 삭제 요청인 경우
        if usage_count > 0:
            messages.error(request, f'이미 {usage_count}개의 사용 내역이 있는 선결제는 삭제할 수 없습니다.')
            return redirect('reporting:prepayment_detail', pk=pk)
        
        customer_name = prepayment.customer.customer_name
        prepayment.delete()
        messages.success(request, f'{customer_name}의 선결제가 삭제되었습니다.')
        return redirect('reporting:prepayment_list')
    
    context = {
        'page_title': '선결제 삭제',
        'prepayment': prepayment,
    }
    
    return render(request, 'reporting/prepayment/delete_confirm.html', context)


@login_required
def prepayment_customer_view(request, customer_id):
    """고객별 선결제 관리 뷰"""
    from reporting.models import Prepayment, FollowUp
    from django.db.models import Sum, Q, Count
    
    # 고객 정보 가져오기
    customer = get_object_or_404(FollowUp, pk=customer_id)
    
    # 권한 체크 - 고객의 담당자 데이터에 접근 가능한지 확인
    if not can_access_user_data(request.user, customer.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:prepayment_list')
    
    # 현재 보고 있는 사용자 결정 (세션에서 선택된 사용자 또는 본인)
    user_profile = get_user_profile(request.user)
    target_user = request.user
    
    if user_profile.can_view_all_users():
        user_filter = request.session.get('selected_user_id')
        if user_filter:
            from django.contrib.auth.models import User
            accessible_users = get_accessible_users(request.user)
            try:
                target_user = accessible_users.get(id=user_filter)
            except User.DoesNotExist:
                target_user = request.user
    
    # 해당 고객의 선결제 조회 - target_user가 등록한 것만
    prepayments = Prepayment.objects.filter(
        customer=customer,
        created_by=target_user
    ).select_related('company', 'created_by').prefetch_related('usages').order_by('payment_date', 'id')
    
    # 각 선결제의 사용금액 계산
    for prepayment in prepayments:
        prepayment.used_amount = prepayment.amount - prepayment.balance
    
    # 통계 계산
    stats = prepayments.aggregate(
        total_amount=Sum('amount'),
        total_balance=Sum('balance'),
        count=Count('id')
    )
    
    total_amount = stats['total_amount'] or 0
    total_balance = stats['total_balance'] or 0
    stats['total_used'] = total_amount - total_balance
    
    # 상태별 개수
    active_count = prepayments.filter(status='active').count()
    depleted_count = prepayments.filter(status='depleted').count()
    cancelled_count = prepayments.filter(status='cancelled').count()
    
    context = {
        'page_title': f'{customer.customer_name} - 선결제 관리',
        'customer': customer,
        'prepayments': prepayments,
        'stats': stats,
        'active_count': active_count,
        'depleted_count': depleted_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'reporting/prepayment/customer.html', context)


@login_required
def prepayment_customer_excel(request, customer_id):
    """고객별 선결제 엑셀 다운로드 (2개 시트 + 피벗 테이블)"""
    from reporting.models import Prepayment, FollowUp, PrepaymentUsage
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from datetime import datetime
    
    # 고객 정보 가져오기
    customer = get_object_or_404(FollowUp, pk=customer_id)
    
    # 권한 체크 - 고객의 담당자 데이터에 접근 가능한지 확인
    if not can_access_user_data(request.user, customer.user):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('reporting:prepayment_list')
    
    # 현재 보고 있는 사용자 결정 (세션에서 선택된 사용자 또는 본인)
    user_profile = get_user_profile(request.user)
    target_user = request.user
    
    if user_profile.can_view_all_users():
        user_filter = request.session.get('selected_user_id')
        if user_filter:
            from django.contrib.auth.models import User
            accessible_users = get_accessible_users(request.user)
            try:
                target_user = accessible_users.get(id=user_filter)
            except User.DoesNotExist:
                target_user = request.user
    
    # 해당 고객의 선결제 조회 - target_user가 등록한 것만
    prepayments = Prepayment.objects.filter(
        customer=customer,
        created_by=target_user
    ).select_related('company', 'created_by').prefetch_related(
        'usages__schedule__delivery_items_set'
    ).order_by('payment_date', 'id')
    
    # 엑셀 생성
    wb = Workbook()
    
    # 스타일 정의
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    right_alignment = Alignment(horizontal="right", vertical="center")
    
    # ========================================
    # 시트 1: 선결제 요약
    # ========================================
    ws1 = wb.active
    ws1.title = "선결제 요약"
    
    # 제목
    ws1.merge_cells('A1:H1')
    title_cell = ws1['A1']
    title_cell.value = f"{customer.customer_name} 선결제 요약"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = center_alignment
    ws1.row_dimensions[1].height = 30
    
    # 헤더
    headers1 = ['번호', '결제일', '지불자', '결제방법', '선결제금액', '사용금액', '남은잔액', '상태']
    for col_num, header in enumerate(headers1, 1):
        cell = ws1.cell(row=3, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # 컬럼 너비 설정
    ws1.column_dimensions['A'].width = 8
    ws1.column_dimensions['B'].width = 12
    ws1.column_dimensions['C'].width = 12
    ws1.column_dimensions['D'].width = 12
    ws1.column_dimensions['E'].width = 15
    ws1.column_dimensions['F'].width = 15
    ws1.column_dimensions['G'].width = 15
    ws1.column_dimensions['H'].width = 12
    
    # 데이터 행
    total_amount = 0
    total_used = 0
    total_balance = 0
    
    for idx, prepayment in enumerate(prepayments, 1):
        row = idx + 3
        used_amount = prepayment.amount - prepayment.balance
        
        total_amount += prepayment.amount
        total_used += used_amount
        total_balance += prepayment.balance
        
        # 데이터
        data = [
            idx,
            prepayment.payment_date.strftime('%Y-%m-%d'),
            prepayment.payer_name or '-',
            prepayment.get_payment_method_display(),
            float(prepayment.amount),  # Decimal을 float으로 변환
            float(used_amount),
            float(prepayment.balance),
            prepayment.get_status_display(),
        ]
        
        for col_num, value in enumerate(data, 1):
            cell = ws1.cell(row=row, column=col_num)
            cell.value = value
            cell.border = border
            
            # 정렬 및 서식
            if col_num == 1 or col_num == 8:  # No, 상태
                cell.alignment = center_alignment
            elif col_num >= 5 and col_num <= 7:  # 금액
                cell.alignment = right_alignment
                cell.number_format = '#,##0'
            
            # 상태별 배경색
            if col_num == 8:
                if prepayment.status == 'active':
                    cell.fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                elif prepayment.status == 'depleted':
                    cell.fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
                elif prepayment.status == 'cancelled':
                    cell.fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
            
            # 잔액에 따른 배경색
            if col_num == 7:  # 남은잔액
                if prepayment.balance > 0:
                    cell.fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
    
    # 합계 행
    summary_row = len(prepayments) + 4
    ws1.merge_cells(f'A{summary_row}:D{summary_row}')
    summary_cell = ws1.cell(row=summary_row, column=1)
    summary_cell.value = "합계"
    summary_cell.font = Font(bold=True, size=11)
    summary_cell.alignment = center_alignment
    summary_cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    summary_cell.border = border
    
    for col in range(2, 5):
        ws1.cell(row=summary_row, column=col).border = border
        ws1.cell(row=summary_row, column=col).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # 합계 금액
    for col_num, value in [(5, float(total_amount)), (6, float(total_used)), (7, float(total_balance))]:
        cell = ws1.cell(row=summary_row, column=col_num)
        cell.value = value
        cell.font = Font(bold=True, size=11)
        cell.alignment = right_alignment
        cell.number_format = '#,##0'
        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        cell.border = border
    
    ws1.cell(row=summary_row, column=8).border = border
    ws1.cell(row=summary_row, column=8).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # ========================================
    # 시트 2: 품목별 집계
    # ========================================
    ws2 = wb.create_sheet(title="품목별 집계")
    
    # 제목
    ws2.merge_cells('A1:D1')
    title_cell2 = ws2['A1']
    title_cell2.value = "품목별 사용 집계"
    title_cell2.font = Font(bold=True, size=14)
    title_cell2.alignment = center_alignment
    ws2.row_dimensions[1].height = 30
    
    # 헤더
    headers2 = ['품목명', '총 수량', '단가', '총 사용금액']
    for col_num, header in enumerate(headers2, 1):
        cell = ws2.cell(row=3, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # 컬럼 너비 설정
    ws2.column_dimensions['A'].width = 25
    ws2.column_dimensions['B'].width = 15
    ws2.column_dimensions['C'].width = 15
    ws2.column_dimensions['D'].width = 18
    
    # 품목별 집계 데이터 수집
    from collections import defaultdict
    item_stats = defaultdict(lambda: {'quantity': 0, 'amount': 0, 'count': 0, 'unit_prices': []})
    
    for prepayment in prepayments:
        usages = prepayment.usages.all()
        for usage in usages:
            if usage.schedule:
                delivery_items = usage.schedule.delivery_items_set.all()
                if delivery_items.exists():
                    for item in delivery_items:
                        # 금액 계산
                        item_amount = item.total_price if item.total_price else (float(item.quantity) * float(item.unit_price) * 1.1)
                        
                        # 통계 업데이트
                        item_stats[item.item_name]['quantity'] += float(item.quantity)
                        item_stats[item.item_name]['amount'] += float(item_amount)
                        item_stats[item.item_name]['count'] += 1
                        item_stats[item.item_name]['unit_prices'].append(float(item.unit_price))
    
    # 품목별 데이터 작성 (사용금액 기준 내림차순)
    sorted_items = sorted(item_stats.items(), key=lambda x: x[1]['amount'], reverse=True)
    row_num = 4
    total_summary_quantity = 0
    total_summary_amount = 0
    total_summary_unit_price = 0
    
    for item_name, stats in sorted_items:
        # 평균 단가 계산
        avg_unit_price = sum(stats['unit_prices']) / len(stats['unit_prices']) if stats['unit_prices'] else 0
        
        data = [
            item_name,
            stats['quantity'],
            avg_unit_price,
            stats['amount'],
        ]
        
        total_summary_quantity += stats['quantity']
        total_summary_amount += stats['amount']
        total_summary_unit_price += avg_unit_price
        
        for col_num, value in enumerate(data, 1):
            cell = ws2.cell(row=row_num, column=col_num)
            cell.value = value
            cell.border = border
            
            if col_num == 1:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = right_alignment
                if col_num in [2, 3, 4]:  # 수량, 단가, 금액
                    cell.number_format = '#,##0'
        
        row_num += 1
    
    # 품목별 합계 행 추가
    if sorted_items:
        summary_row = row_num
        ws2.cell(row=summary_row, column=1).value = "합계"
        ws2.cell(row=summary_row, column=1).font = Font(bold=True, size=11)
        ws2.cell(row=summary_row, column=1).alignment = center_alignment
        ws2.cell(row=summary_row, column=1).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        ws2.cell(row=summary_row, column=1).border = border
        
        ws2.cell(row=summary_row, column=2).value = total_summary_quantity
        ws2.cell(row=summary_row, column=2).font = Font(bold=True, size=11)
        ws2.cell(row=summary_row, column=2).alignment = right_alignment
        ws2.cell(row=summary_row, column=2).number_format = '#,##0'
        ws2.cell(row=summary_row, column=2).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        ws2.cell(row=summary_row, column=2).border = border
        
        ws2.cell(row=summary_row, column=3).value = total_summary_unit_price
        ws2.cell(row=summary_row, column=3).font = Font(bold=True, size=11)
        ws2.cell(row=summary_row, column=3).alignment = right_alignment
        ws2.cell(row=summary_row, column=3).number_format = '#,##0'
        ws2.cell(row=summary_row, column=3).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        ws2.cell(row=summary_row, column=3).border = border
        
        ws2.cell(row=summary_row, column=4).value = total_summary_amount
        ws2.cell(row=summary_row, column=4).font = Font(bold=True, size=11)
        ws2.cell(row=summary_row, column=4).alignment = right_alignment
        ws2.cell(row=summary_row, column=4).number_format = '#,##0'
        ws2.cell(row=summary_row, column=4).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        ws2.cell(row=summary_row, column=4).border = border
        
        # 총 남은 선결제 잔액 정보 추가
        row_num += 2
        balance_row = row_num
        ws2.merge_cells(f'A{balance_row}:B{balance_row}')
        balance_label_cell = ws2.cell(row=balance_row, column=1)
        balance_label_cell.value = "총 남은 선결제 잔액"
        balance_label_cell.font = Font(bold=True, size=12, color="FFFFFF")
        balance_label_cell.alignment = center_alignment
        balance_label_cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        balance_label_cell.border = border
        ws2.cell(row=balance_row, column=2).border = border
        ws2.cell(row=balance_row, column=2).fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        ws2.merge_cells(f'C{balance_row}:D{balance_row}')
        balance_value_cell = ws2.cell(row=balance_row, column=3)
        balance_value_cell.value = float(total_balance)
        balance_value_cell.font = Font(bold=True, size=12)
        balance_value_cell.alignment = right_alignment
        balance_value_cell.number_format = '#,##0 "원"'
        balance_value_cell.fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        balance_value_cell.border = border
        ws2.cell(row=balance_row, column=4).border = border
        ws2.cell(row=balance_row, column=4).fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
    
    # 품목 데이터가 없는 경우
    if not sorted_items:
        ws2.merge_cells('A4:D4')
        no_data_cell = ws2['A4']
        no_data_cell.value = "품목별 사용 내역이 없습니다."
        no_data_cell.alignment = center_alignment
        no_data_cell.font = Font(italic=True, color="999999")
    
    # HTTP 응답
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"{customer.customer_name}_선결제내역_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
    
    wb.save(response)
    return response


@login_required
def prepayment_list_excel(request):
    """전체 선결제 엑셀 다운로드"""
    from reporting.models import Prepayment
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from django.http import HttpResponse
    from datetime import datetime
    
    # 권한 체크 및 데이터 필터링 - 등록자 본인만 (Manager도 자신이 등록한 것만)
    prepayments = Prepayment.objects.filter(
        created_by=request.user
    )
    
    prepayments = prepayments.select_related(
        'customer', 'company', 'created_by'
    ).order_by('-payment_date', '-created_at')
    
    # 엑셀 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "전체 선결제"
    
    # 스타일 정의
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    right_alignment = Alignment(horizontal="right", vertical="center")
    
    # 제목
    ws.merge_cells('A1:K1')
    title_cell = ws['A1']
    title_cell.value = f"선결제 전체 내역 ({datetime.now().strftime('%Y-%m-%d')})"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = center_alignment
    ws.row_dimensions[1].height = 30
    
    # 헤더
    headers = ['No', '고객명', '결제일', '지불자', '결제방법', '선결제금액', '사용금액', '남은잔액', '상태', '등록자', '등록일']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # 컬럼 너비 설정
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 10
    ws.column_dimensions['J'].width = 12
    ws.column_dimensions['K'].width = 16
    
    # 데이터 행
    total_amount = 0
    total_used = 0
    total_balance = 0
    
    for idx, prepayment in enumerate(prepayments, 1):
        row = idx + 3
        used_amount = prepayment.amount - prepayment.balance
        
        total_amount += prepayment.amount
        total_used += used_amount
        total_balance += prepayment.balance
        
        # 데이터
        data = [
            idx,
            prepayment.customer.customer_name if prepayment.customer else '-',
            prepayment.payment_date.strftime('%Y-%m-%d'),
            prepayment.payer_name or '-',
            prepayment.get_payment_method_display(),
            prepayment.amount,
            used_amount,
            prepayment.balance,
            prepayment.get_status_display(),
            prepayment.created_by.get_full_name() or prepayment.created_by.username,
            prepayment.created_at.strftime('%Y-%m-%d %H:%M')
        ]
        
        for col_num, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = value
            cell.border = border
            
            # 정렬
            if col_num == 1 or col_num == 9:  # No, 상태
                cell.alignment = center_alignment
            elif col_num >= 6 and col_num <= 8:  # 금액
                cell.alignment = right_alignment
                if isinstance(value, (int, float)):
                    cell.number_format = '#,##0'
            
            # 상태별 배경색
            if col_num == 9:
                if prepayment.status == 'active':
                    cell.fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                elif prepayment.status == 'depleted':
                    cell.fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
                elif prepayment.status == 'cancelled':
                    cell.fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
            
            # 잔액에 따른 배경색
            if col_num == 8:  # 남은잔액
                if prepayment.balance > 0:
                    cell.fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
    
    # 합계 행
    summary_row = len(prepayments) + 4
    ws.merge_cells(f'A{summary_row}:E{summary_row}')
    summary_cell = ws.cell(row=summary_row, column=1)
    summary_cell.value = "합계"
    summary_cell.font = Font(bold=True, size=11)
    summary_cell.alignment = center_alignment
    summary_cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    summary_cell.border = border
    
    for col in range(2, 6):
        ws.cell(row=summary_row, column=col).border = border
        ws.cell(row=summary_row, column=col).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # 합계 금액
    for col_num, value in [(6, total_amount), (7, total_used), (8, total_balance)]:
        cell = ws.cell(row=summary_row, column=col_num)
        cell.value = value
        cell.font = Font(bold=True, size=11)
        cell.alignment = right_alignment
        cell.number_format = '#,##0'
        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        cell.border = border
    
    for col in range(9, 12):
        ws.cell(row=summary_row, column=col).border = border
        ws.cell(row=summary_row, column=col).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # HTTP 응답
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"선결제전체내역_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
    
    wb.save(response)
    return response


@login_required
def prepayment_api_list(request):
    """고객별 선결제 목록 API (AJAX용)"""
    from reporting.models import Prepayment
    from django.http import JsonResponse
    
    customer_id = request.GET.get('customer_id')
    if not customer_id:
        return JsonResponse({'prepayments': []})
    
    try:
        # 해당 고객의 선결제 중 담당자가 등록한 것만
        prepayments = Prepayment.objects.filter(
            customer_id=customer_id,
            created_by__id=FollowUp.objects.get(id=customer_id).user_id,
            status='active',
            balance__gt=0
        ).order_by('id')
        
        prepayments_data = [{
            'id': p.id,
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'payer_name': p.payer_name or '미지정',
            'amount': float(p.amount),
            'balance': float(p.balance),
        } for p in prepayments]
        
        return JsonResponse({'prepayments': prepayments_data})
    except Exception as e:
        return JsonResponse({'prepayments': [], 'error': str(e)})


# ============================================
# 제품 관리 뷰
# ============================================

@login_required
def product_list(request):
    """제품 목록"""
    from reporting.models import Product, DeliveryItem, QuoteItem
    from django.db.models import Q, Count
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    is_active = request.GET.get('is_active', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(product_code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if is_active:
        products = products.filter(is_active=(is_active == 'true'))
    
    # 견적 횟수와 판매 횟수를 미리 계산 (정렬을 위해)
    from django.db.models import Count, Case, When, IntegerField, Value
    from django.db.models.functions import Coalesce
    
    products = products.annotate(
        quote_count=Count(
            'delivery_items__schedule',
            distinct=True,
            filter=Q(
                delivery_items__schedule__isnull=False,
                delivery_items__schedule__activity_type='quote'
            )
        ),
        completed_schedule_count=Count(
            'delivery_items__schedule',
            distinct=True, 
            filter=Q(
                delivery_items__schedule__status='completed',
                delivery_items__schedule__activity_type='delivery'
            )
        ),
        history_count=Count(
            'delivery_items__history',
            distinct=True,
            filter=Q(delivery_items__history__isnull=False)
        )
    ).annotate(
        delivery_count=Coalesce('completed_schedule_count', Value(0)) + Coalesce('history_count', Value(0))
    )
    
    # 정렬
    sort_by = request.GET.get('sort', 'code')
    sort_order = request.GET.get('order', 'asc')  # asc 또는 desc
    
    # 정렬 필드 매핑
    sort_fields = {
        'code': 'product_code',
        'description': 'description',
        'price': 'standard_price',
        'status': 'is_active',
        'quote_count': 'quote_count',
        'delivery_count': 'delivery_count',
    }
    
    # 기본 정렬 필드
    order_field = sort_fields.get(sort_by, 'product_code')
    
    # 내림차순인 경우 '-' 추가
    if sort_order == 'desc':
        order_field = '-' + order_field
    
    # 현재가(프로모션 가격 포함) 정렬은 따로 처리
    if sort_by == 'promo_price':
        from django.db.models import Case, When, F
        if sort_order == 'desc':
            products = products.order_by(
                Case(
                    When(is_promo=True, then=F('promotion_price')),
                    default=F('standard_price')
                ).desc()
            )
        else:
            products = products.order_by(
                Case(
                    When(is_promo=True, then=F('promotion_price')),
                    default=F('standard_price')
                )
            )
    else:
        products = products.order_by(order_field)
    
    # 각 제품의 견적/판매 횟수는 이미 annotate로 계산됨 - 아래 루프 제거
    
    # 페이지네이션
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'is_active': is_active,
        'sort_by': sort_by,
        'sort_order': sort_order,
    }
    
    return render(request, 'reporting/product_list.html', context)


@login_required
def product_create(request):
    """제품 등록"""
    from reporting.models import Product
    from decimal import Decimal
    from django.db import IntegrityError
    
    if request.method == 'POST':
        # AJAX 요청 처리
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                product_code = request.POST.get('product_code', '').strip()
                
                # 품번 중복 체크
                if Product.objects.filter(product_code=product_code).exists():
                    return JsonResponse({
                        'success': False,
                        'error': f'품번 "{product_code}"은(는) 이미 등록되어 있습니다.'
                    }, status=400)
                
                product = Product(
                    product_code=product_code,
                    standard_price=Decimal(request.POST.get('standard_price', 0)),
                    is_active=True,  # 기본값
                )
                
                # 선택 필드들
                if request.POST.get('description'):
                    product.description = request.POST.get('description')
                
                # 프로모션 설정
                if request.POST.get('is_promo') == 'on':
                    product.is_promo = True
                    if request.POST.get('promo_price'):
                        product.promo_price = Decimal(request.POST.get('promo_price'))
                    if request.POST.get('promo_start'):
                        product.promo_start = request.POST.get('promo_start')
                    if request.POST.get('promo_end'):
                        product.promo_end = request.POST.get('promo_end')
                
                product.save()
                return JsonResponse({
                    'success': True,
                    'product_id': product.id,
                    'product_code': product.product_code
                })
                
            except IntegrityError as e:
                logger.error(f"제품 등록 실패 (중복): {e}")
                return JsonResponse({
                    'success': False,
                    'error': '이미 등록된 품번입니다.'
                }, status=400)
            except Exception as e:
                logger.error(f"제품 등록 실패: {e}")
                error_msg = str(e)
                if 'UNIQUE constraint' in error_msg:
                    error_msg = '이미 등록된 품번입니다.'
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
        
        # 일반 폼 제출 처리
        try:
            product_code = request.POST.get('product_code', '').strip()
            
            # 품번 중복 체크
            if Product.objects.filter(product_code=product_code).exists():
                messages.error(request, f'품번 "{product_code}"은(는) 이미 등록되어 있습니다.')
                return render(request, 'reporting/product_form.html', {})
            
            product = Product(
                product_code=product_code,
                standard_price=Decimal(request.POST.get('standard_price', 0)),
                is_active=request.POST.get('is_active') == 'on',
            )
            
            # 선택 필드들
            if request.POST.get('description'):
                product.description = request.POST.get('description')
            
            # 프로모션 설정
            if request.POST.get('is_promo') == 'on':
                product.is_promo = True
                if request.POST.get('promo_price'):
                    product.promo_price = Decimal(request.POST.get('promo_price'))
                if request.POST.get('promo_start'):
                    product.promo_start = request.POST.get('promo_start')
                if request.POST.get('promo_end'):
                    product.promo_end = request.POST.get('promo_end')
            
            product.save()
            messages.success(request, f'제품 "{product.product_code}"이(가) 등록되었습니다.')
            return redirect('product_list')
            
        except IntegrityError as e:
            logger.error(f"제품 등록 실패 (중복): {e}")
            messages.error(request, '이미 등록된 품번입니다.')
        except Exception as e:
            logger.error(f"제품 등록 실패: {e}")
            error_msg = str(e)
            if 'UNIQUE constraint' in error_msg:
                error_msg = '이미 등록된 품번입니다.'
            messages.error(request, f'제품 등록에 실패했습니다: {error_msg}')
    
    return render(request, 'reporting/product_form.html', {})


@login_required
def product_edit(request, product_id):
    """제품 수정"""
    from reporting.models import Product
    from decimal import Decimal
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.product_code = request.POST.get('product_code')
            product.standard_price = Decimal(request.POST.get('standard_price', 0))
            product.is_active = request.POST.get('is_active') == 'on'
            
            # 선택 필드들
            product.description = request.POST.get('description', '')
            
            # 프로모션 설정
            product.is_promo = request.POST.get('is_promo') == 'on'
            if product.is_promo:
                if request.POST.get('promo_price'):
                    product.promo_price = Decimal(request.POST.get('promo_price'))
                if request.POST.get('promo_start'):
                    product.promo_start = request.POST.get('promo_start')
                if request.POST.get('promo_end'):
                    product.promo_end = request.POST.get('promo_end')
            else:
                product.promo_price = None
                product.promo_start = None
                product.promo_end = None
            
            product.save()
            messages.success(request, f'제품 "{product.product_code}"이(가) 수정되었습니다.')
            return redirect('product_list')
            
        except Exception as e:
            logger.error(f"제품 수정 실패: {e}")
            messages.error(request, f'제품 수정에 실패했습니다: {str(e)}')
    
    context = {
        'product': product,
    }
    
    return render(request, 'reporting/product_form.html', context)


@login_required
@require_POST
def product_delete(request, product_id):
    """제품 삭제"""
    from reporting.models import Product
    
    product = get_object_or_404(Product, id=product_id)
    
    # 사용 중인 제품인지 확인
    if product.delivery_items.exists() or product.quoteitems.exists():
        messages.warning(request, '이미 견적 또는 납품에 사용된 제품은 삭제할 수 없습니다. 비활성화를 권장합니다.')
        return redirect('reporting:product_list')
    
    product_code = product.product_code
    product.delete()
    messages.success(request, f'제품 "{product_code}"이(가) 삭제되었습니다.')
    return redirect('reporting:product_list')


@login_required
def product_api_list(request):
    """제품 목록 API (AJAX용) - 견적/납품 작성 시 제품 선택"""
    from reporting.models import Product
    
    search = request.GET.get('search', '')
    
    products = Product.objects.filter(is_active=True)
    
    if search:
        products = products.filter(
            Q(product_code__icontains=search) |
            Q(description__icontains=search)
        )
    
    # 제한 제거 - 모든 제품을 가져와서 클라이언트에서 검색
    # 성능을 위해 필요시 제한 추가 가능: products = products.order_by('product_code')[:1000]
    products = products.order_by('product_code')
    
    products_data = [{
        'id': p.id,
        'product_code': p.product_code,
        'name': p.product_code,
        'description': p.description,  # description 필드 추가
        'standard_price': float(p.standard_price),
        'current_price': float(p.get_current_price()),
        'is_promo': p.is_promo,
    } for p in products]
    
    return JsonResponse({'products': products_data})
