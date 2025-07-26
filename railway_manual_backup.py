#!/usr/bin/env python
"""
Railway 웹 대시보드를 통한 데이터베이스 백업 가이드
CLI 문제 발생 시 대안 방법
"""

def show_manual_backup_steps():
    """수동 백업 단계별 가이드"""
    print("=" * 60)
    print("🚂 Railway 수동 백업 가이드 (CLI 문제 시)")
    print("=" * 60)
    
    print("\n📋 단계별 백업 방법:")
    
    print("\n1️⃣ Railway 웹 대시보드 접속")
    print("   ➤ https://railway.app/dashboard 방문")
    print("   ➤ 로그인 후 sales-note 프로젝트 선택")
    
    print("\n2️⃣ 데이터베이스 정보 확인")
    print("   ➤ PostgreSQL 서비스 클릭")
    print("   ➤ 'Connect' 탭 선택")
    print("   ➤ 'Database URL' 복사 (postgres://로 시작하는 URL)")
    
    print("\n3️⃣ 로컬에서 백업 실행")
    print("   다음 중 하나의 방법 선택:")
    print("   ")
    print("   📦 방법 A: Django dumpdata (권장)")
    print("   ➤ Railway 환경변수 설정 후:")
    print("     set DATABASE_URL=복사한_URL")
    print("     python manage.py dumpdata reporting --indent=2 > railway_backup.json")
    print("   ")
    print("   🗄️ 방법 B: PostgreSQL 직접 백업")
    print("   ➤ PostgreSQL 설치 후:")
    print("     pg_dump \"복사한_DATABASE_URL\" > railway_backup.sql")
    
    print("\n4️⃣ 백업 검증")
    print("   ➤ 생성된 파일 크기 확인")
    print("   ➤ JSON/SQL 파일 문법 검증")
    
    print("\n💡 추가 팁:")
    print("   • 백업 전 서비스 일시 중단 권장")
    print("   • 여러 형태로 백업 (JSON + SQL)")
    print("   • 안전한 위치에 백업 파일 저장")

def create_env_backup_script():
    """환경변수 기반 백업 스크립트"""
    print("\n" + "=" * 40)
    print("🔧 환경변수 백업 스크립트 생성")
    print("=" * 40)
    
    script_content = '''@echo off
REM Railway 데이터베이스 백업 배치 스크립트
REM 사용법: railway_backup.bat [DATABASE_URL]

set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if "%1"=="" (
    echo 사용법: railway_backup.bat "DATABASE_URL"
    echo 예시: railway_backup.bat "postgres://user:pass@host:port/db"
    pause
    exit /b 1
)

set DATABASE_URL=%1

echo ========================
echo Railway 데이터베이스 백업
echo ========================
echo 시간: %TIMESTAMP%
echo URL: %DATABASE_URL%
echo ========================

REM Django 백업
echo.
echo [1/3] Django 데이터 백업 중...
python manage.py dumpdata reporting --indent=2 > railway_django_backup_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✅ Django 백업 완료: railway_django_backup_%TIMESTAMP%.json
) else (
    echo ❌ Django 백업 실패
)

REM PostgreSQL 백업 (pg_dump 설치된 경우)
echo.
echo [2/3] PostgreSQL 백업 시도 중...
pg_dump "%DATABASE_URL%" > railway_pg_backup_%TIMESTAMP%.sql 2>nul
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL 백업 완료: railway_pg_backup_%TIMESTAMP%.sql
) else (
    echo ⚠️ PostgreSQL 백업 실패 (pg_dump 없음 또는 연결 오류)
)

REM 백업 검증
echo.
echo [3/3] 백업 파일 검증 중...
for %%f in (railway_*_backup_%TIMESTAMP%.*) do (
    echo   📁 %%f - 크기: %%~zf bytes
)

echo.
echo 🎉 백업 작업 완료!
echo 💾 생성된 파일들을 안전한 위치에 보관하세요.
pause
'''
    
    with open("railway_backup.bat", "w", encoding="cp949") as f:
        f.write(script_content)
    
    print("✅ 배치 스크립트 생성: railway_backup.bat")
    print("📋 사용법:")
    print('   railway_backup.bat "복사한_DATABASE_URL"')

if __name__ == "__main__":
    show_manual_backup_steps()
    create_env_backup_script()
