from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create superuser for production'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'ddd418'
        password = '1676079051aA@!@'
        email = 'admin@company.com'
        
        # 기존 사용자 삭제 후 재생성
        if User.objects.filter(username=username).exists():
            User.objects.filter(username=username).delete()
            self.stdout.write(f'기존 사용자 {username} 삭제됨')
        
        # 새 슈퍼유저 생성
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        self.stdout.write(
            self.style.SUCCESS(f'슈퍼유저 {username} 생성 완료')
        )
