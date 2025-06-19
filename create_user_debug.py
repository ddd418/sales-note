#!/usr/bin/env python
"""
Railway Console에서 실행할 수 있는 간단한 슈퍼유저 생성 스크립트
"""
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 기존 사용자 확인
username = 'ddd418'
existing_users = User.objects.all()
print(f"현재 사용자 수: {existing_users.count()}")

if existing_users.exists():
    print("기존 사용자들:")
    for user in existing_users:
        print(f"  - {user.username} (슈퍼유저: {user.is_superuser})")

# 지정된 사용자 확인
if User.objects.filter(username=username).exists():
    print(f"사용자 '{username}'가 이미 존재합니다.")
    user = User.objects.get(username=username)
    if not user.is_superuser:
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"사용자 '{username}'를 슈퍼유저로 업그레이드했습니다.")
else:
    # 새 슈퍼유저 생성
    user = User.objects.create_superuser(
        username=username,
        email='admin@company.com',
        password='1676079051aA@!@'
    )
    print(f"슈퍼유저 '{username}' 생성 완료!")

print("\n=== 최종 사용자 목록 ===")
for user in User.objects.all():
    print(f"- {user.username} (슈퍼유저: {user.is_superuser}, 스태프: {user.is_staff})")
