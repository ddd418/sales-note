from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Company
from django.contrib.auth.models import User


# 기본 로그인 폼
class SimpleLoginForm(forms.Form):
    """
    간단한 로그인 폼
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '사용자명'
        }),
        label='사용자명'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호'
        }),
        label='비밀번호'
    )


# 회사코드 + 사번 + 비밀번호 로그인 폼
class CompanyLoginForm(forms.Form):
    """
    회사코드 + 사번 + 비밀번호로 로그인하는 폼
    """
    company_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '회사코드 (예: BYXWZT)',
            'autocomplete': 'off'
        }),
        label='회사코드'
    )
    
    employee_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '사번 (예: EMP001)',
            'autocomplete': 'username'
        }),
        label='사번'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호',
            'autocomplete': 'current-password'
        }),
        label='비밀번호'
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """
        폼 전체 유효성 검사 및 인증
        """
        cleaned_data = super().clean()
        company_code = cleaned_data.get('company_code')
        employee_id = cleaned_data.get('employee_id')
        password = cleaned_data.get('password')
        
        if company_code and employee_id and password:
            # 회사코드 + 사번 + 비밀번호로 인증 시도
            self.user_cache = authenticate(
                self.request,
                company_code=company_code,
                employee_id=employee_id,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    "회사코드, 사번, 또는 비밀번호가 올바르지 않습니다.",
                    code='invalid_login'
                )
            
            if not self.user_cache.is_active:
                raise ValidationError(
                    "이 계정은 비활성화되어 있습니다.",
                    code='inactive'
                )
        
        return cleaned_data
    
    def get_user(self):
        """
        인증된 사용자 반환
        """
        return self.user_cache
