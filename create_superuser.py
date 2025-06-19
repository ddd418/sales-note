#!/usr/bin/env python
import os
import django
from django.contrib.auth import get_user_model

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')
django.setup()

User = get_user_model()

# 슈퍼유저가 없으면 생성
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'  # 실제 운영시 강력한 비밀번호 사용
    )
    print("슈퍼유저 'admin' 생성됨 (비밀번호: admin123)")
else:
    print("슈퍼유저가 이미 존재합니다")
