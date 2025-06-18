from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reporting.models import UserProfile

class Command(BaseCommand):
    help = 'ddd418 사용자에게 Admin 권한을 부여합니다'

    def handle(self, *args, **options):
        try:
            # ddd418 사용자 찾기
            user = User.objects.get(username='ddd418')
            
            # UserProfile이 이미 있는지 확인
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'admin',
                    'created_by': user  # 자기 자신이 생성한 것으로 설정
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {user.username}에게 Admin 권한이 부여되었습니다.')
                )
            else:
                # 이미 존재하는 경우 admin 권한으로 업데이트
                profile.role = 'admin'
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {user.username}의 권한이 Admin으로 업데이트되었습니다.')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ ddd418 사용자를 찾을 수 없습니다.')
            )
