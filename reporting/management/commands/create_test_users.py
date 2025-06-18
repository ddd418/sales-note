from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reporting.models import UserProfile

class Command(BaseCommand):
    help = '테스트용 Manager와 Salesman 계정을 생성합니다'

    def handle(self, *args, **options):
        # Admin 사용자 찾기
        try:
            admin_user = User.objects.get(username='ddd418')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Admin 사용자(ddd418)를 찾을 수 없습니다.')
            )
            return

        # Manager 계정 생성
        manager_user, created = User.objects.get_or_create(
            username='김매니저',
            defaults={
                'first_name': '김',
                'last_name': '매니저',
                'is_active': True
            }
        )
        
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            
            UserProfile.objects.create(
                user=manager_user,
                role='manager',
                created_by=admin_user
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Manager 계정 생성됨: {manager_user.username} (비밀번호: manager123)')
            )
        else:
            # 기존 계정의 권한 업데이트
            profile, profile_created = UserProfile.objects.get_or_create(
                user=manager_user,
                defaults={
                    'role': 'manager',
                    'created_by': admin_user
                }
            )
            if not profile_created and profile.role != 'manager':
                profile.role = 'manager'
                profile.save()
            
            self.stdout.write(
                self.style.WARNING(f'⚠️  Manager 계정 이미 존재: {manager_user.username}')
            )

        # Salesman 계정들 생성
        salesmen_data = [
            {'username': '이영업', 'first_name': '이', 'last_name': '영업'},
            {'username': '박세일즈', 'first_name': '박', 'last_name': '세일즈'},
        ]
        
        for data in salesmen_data:
            salesman_user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_active': True
                }
            )
            
            if created:
                salesman_user.set_password('salesman123')
                salesman_user.save()
                
                UserProfile.objects.create(
                    user=salesman_user,
                    role='salesman',
                    created_by=admin_user
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Salesman 계정 생성됨: {salesman_user.username} (비밀번호: salesman123)')
                )
            else:
                # 기존 계정의 권한 업데이트
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=salesman_user,
                    defaults={
                        'role': 'salesman',
                        'created_by': admin_user
                    }
                )
                if not profile_created and profile.role != 'salesman':
                    profile.role = 'salesman'
                    profile.save()
                
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Salesman 계정 이미 존재: {salesman_user.username}')
                )

        self.stdout.write(
            self.style.SUCCESS('\n🎉 테스트 계정 생성/업데이트 완료!')
        )
        self.stdout.write('📋 생성된 계정 정보:')
        self.stdout.write('   Admin: ddd418 (기존 비밀번호)')
        self.stdout.write('   Manager: 김매니저 / manager123')
        self.stdout.write('   Salesman: 이영업 / salesman123')
        self.stdout.write('   Salesman: 박세일즈 / salesman123')
