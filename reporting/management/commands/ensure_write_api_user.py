"""쓰기 MCP 프록시용 전용 기계 유저를 보장(생성/정규화)하는 관리 커맨드.

이 유저는 환경변수 SALES_NOTE_WRITE_USER_ID 로 지정되어 write bearer 의 acting
유저가 된다(reporting/write_api.py). 안전 불변식상 반드시 **비-staff·비-superuser·
salesman** 이어야 하며(권한 붕괴 방지), 비밀번호 로그인은 비활성한다(bearer 전용).

사용 예:
    railway run --service web --environment production py -3.13 manage.py ensure_write_api_user
    ... manage.py ensure_write_api_user --username ai-writer
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from reporting.models import UserProfile


class Command(BaseCommand):
    help = "쓰기 MCP 프록시용 전용 기계 유저(non-staff salesman)를 생성/정규화한다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="ai-writer",
            help="기계 유저 username (기본: ai-writer)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"].strip()

        user, created = User.objects.get_or_create(username=username)

        # 안전 불변식: 절대 staff/superuser 가 아니어야 한다.
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.set_unusable_password()  # 비밀번호 로그인 비활성 (bearer 전용)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != "salesman":
            profile.role = "salesman"
            profile.save(update_fields=["role"])

        state = "생성됨" if created else "기존 유저 정규화"
        self.stdout.write(
            self.style.SUCCESS(
                f"[ensure_write_api_user] {state}: username={username} id={user.id} "
                f"role={profile.role} is_staff={user.is_staff} "
                f"is_superuser={user.is_superuser}"
            )
        )
        # 아래 줄의 값을 SALES_NOTE_WRITE_USER_ID 로 설정한다.
        self.stdout.write(f"WRITE_API_USER_ID={user.id}")
