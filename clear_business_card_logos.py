"""
Railway에서 실행할 스크립트: 기존 명함의 로고를 초기화
python clear_business_card_logos.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import BusinessCard

# 모든 명함의 로고를 초기화
cards = BusinessCard.objects.exclude(logo='')
count = cards.count()

if count > 0:
    cards.update(logo='')
    print(f'{count}개의 명함 로고를 초기화했습니다.')
    print('명함 관리 페이지에서 로고를 다시 업로드하면 Cloudinary에 저장됩니다.')
else:
    print('초기화할 명함 로고가 없습니다.')
