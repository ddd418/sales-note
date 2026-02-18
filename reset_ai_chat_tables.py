"""
프로덕션 배포 시 ai_chat 테이블 리셋 스크립트
이전 채팅 기반 모델(AIChatRoom, AIChatMessage)을 삭제하고
새 부서 분석 모델(AIDepartmentAnalysis)로 전환

한 번 실행 후 startCommand에서 제거해도 됨
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # 이미 새 테이블이 존재하면 스킵
    cursor.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_chat_aidepartmentanalysis')"
    )
    exists = cursor.fetchone()[0]
    if exists:
        print("[ai_chat_reset] 새 테이블 이미 존재 - 스킵")
    else:
        print("[ai_chat_reset] 기존 ai_chat 테이블 리셋 시작...")
        cursor.execute("DELETE FROM django_migrations WHERE app='ai_chat'")
        cursor.execute("DROP TABLE IF EXISTS ai_chat_painpointcard CASCADE")
        cursor.execute("DROP TABLE IF EXISTS ai_chat_aichatmessage CASCADE")
        cursor.execute("DROP TABLE IF EXISTS ai_chat_aichatroom CASCADE")
        print("[ai_chat_reset] 완료 - migrate에서 새 테이블 생성됨")
