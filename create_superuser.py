#!/usr/bin/env python
import os
import django
from django.contrib.auth import get_user_model

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')
django.setup()

User = get_user_model()

# 지정된 슈퍼유저가 없으면 생성
username = 'ddd418'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email='admin@company.com',
        password='1676079051aA@!@'
    )
    print(f"슈퍼유저 '{username}' 생성됨")
else:
    print(f"사용자 '{username}'가 이미 존재합니다")
