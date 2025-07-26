@echo off
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
    echo [OK] Django 백업 완료: railway_django_backup_%TIMESTAMP%.json
) else (
    echo [ERROR] Django 백업 실패
)

REM PostgreSQL 백업 (pg_dump 설치된 경우)
echo.
echo [2/3] PostgreSQL 백업 시도 중...
pg_dump "%DATABASE_URL%" > railway_pg_backup_%TIMESTAMP%.sql 2>nul
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL 백업 완료: railway_pg_backup_%TIMESTAMP%.sql
) else (
    echo [WARNING] PostgreSQL 백업 실패 (pg_dump 없음 또는 연결 오류)
)

REM 백업 검증
echo.
echo [3/3] 백업 파일 검증 중...
for %%f in (railway_*_backup_%TIMESTAMP%.*) do (
    echo   파일: %%f - 크기: %%~zf bytes
)

echo.
echo 백업 작업 완료!
echo 생성된 파일들을 안전한 위치에 보관하세요.
pause
