#!/usr/bin/env python
"""기존 납품 품목의 단위를 '개'에서 'EA'로 변경"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import DeliveryItem

# "개"를 "EA"로 변경
updated = DeliveryItem.objects.filter(unit='개').update(unit='EA')
print(f'✅ {updated}개 품목의 단위를 "개" → "EA"로 변경했습니다.')

# 전체 통계
total = DeliveryItem.objects.count()
ea_count = DeliveryItem.objects.filter(unit='EA').count()
print(f'📊 전체 품목: {total}개, EA: {ea_count}개')
