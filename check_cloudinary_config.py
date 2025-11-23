"""
Cloudinary 설정 확인 스크립트
Railway에서 실행: python check_cloudinary_config.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.conf import settings

print("=" * 50)
print("Cloudinary 설정 확인")
print("=" * 50)

# 환경 변수 확인
cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
api_key = os.environ.get('CLOUDINARY_API_KEY')
api_secret = os.environ.get('CLOUDINARY_API_SECRET')

print(f"CLOUDINARY_CLOUD_NAME: {cloud_name if cloud_name else 'NOT SET'}")
print(f"CLOUDINARY_API_KEY: {api_key if api_key else 'NOT SET'}")
print(f"CLOUDINARY_API_SECRET: {'SET' if api_secret else 'NOT SET'}")
print()

# Django 설정 확인
print(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")

if hasattr(settings, 'CLOUDINARY_STORAGE'):
    print(f"CLOUDINARY_STORAGE: {settings.CLOUDINARY_STORAGE}")
else:
    print("CLOUDINARY_STORAGE: NOT CONFIGURED")

print("=" * 50)

# 테스트 업로드
if cloud_name and api_key and api_secret:
    try:
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print("✓ Cloudinary 설정이 올바릅니다!")
    except Exception as e:
        print(f"✗ Cloudinary 설정 오류: {e}")
else:
    print("✗ Cloudinary 환경 변수가 설정되지 않았습니다!")
    print("Railway Variables에 다음을 추가하세요:")
    print("  - CLOUDINARY_CLOUD_NAME")
    print("  - CLOUDINARY_API_KEY")
    print("  - CLOUDINARY_API_SECRET")
