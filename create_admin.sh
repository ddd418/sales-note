#!/usr/bin/env bash
# Railway에서 직접 실행할 수 있는 슈퍼유저 생성 스크립트

echo "슈퍼유저 생성 중..."

python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# 기존 사용자 확인 및 삭제
username = 'ddd418'
if User.objects.filter(username=username).exists():
    User.objects.filter(username=username).delete()
    print(f"기존 사용자 {username} 삭제됨")

# 새 슈퍼유저 생성
user = User.objects.create_superuser(
    username='ddd418',
    email='admin@company.com',
    password='1676079051aA@!@'
)
print(f"슈퍼유저 {username} 생성 완료!")
EOF

echo "슈퍼유저 생성 스크립트 완료"
