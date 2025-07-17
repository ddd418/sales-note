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
