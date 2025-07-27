#!/usr/bin/env python
"""
PostgreSQL 백업 테스트 스크립트
배포 전에 로컬에서 백업 기능을 테스트할 수 있습니다.
"""
import os
import sys
import subprocess
import datetime
from pathlib import Path

def test_backup():
    """백업 기능 테스트"""
    print("🧪 PostgreSQL 백업 기능 테스트")
    print("=" * 50)
    
    # 환경변수 확인
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
        print("💡 Railway에서 복사한 DATABASE_URL을 설정하세요:")
        print("   export DATABASE_URL='postgresql://...'")
        return False
    
    print(f"✅ DATABASE_URL 확인됨")
    print(f"🔗 {database_url[:50]}...")
    
    # pg_dump 사용 가능 확인
    try:
        result = subprocess.run(['pg_dump', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pg_dump 사용 가능: {result.stdout.strip()}")
        else:
            print("❌ pg_dump를 찾을 수 없습니다.")
            print("💡 PostgreSQL 클라이언트를 설치하세요:")
            print("   - Windows: https://www.postgresql.org/download/windows/")
            print("   - macOS: brew install postgresql")
            print("   - Linux: sudo apt-get install postgresql-client")
            return False
    except FileNotFoundError:
        print("❌ pg_dump를 찾을 수 없습니다.")
        return False
    
    # 연결 테스트
    print("\n🔄 데이터베이스 연결 테스트 중...")
    try:
        result = subprocess.run([
            'psql', database_url, '-c', 'SELECT version();'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 데이터베이스 연결 성공")
        else:
            print(f"❌ 데이터베이스 연결 실패:")
            print(f"   stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 데이터베이스 연결 타임아웃")
        return False
    except FileNotFoundError:
        print("❌ psql을 찾을 수 없습니다.")
        return False
    
    # 실제 백업 테스트
    print("\n🔄 백업 테스트 실행 중...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"test_backup_{timestamp}.sql"
    
    try:
        dump_command = [
            "pg_dump",
            database_url,
            "--verbose",
            "--no-password",
            "--format=plain",
            "--file", backup_file
        ]
        
        result = subprocess.run(
            dump_command,
            capture_output=True,
            text=True,
            timeout=300  # 5분
        )
        
        if result.returncode == 0:
            # 파일 크기 확인
            file_size = os.path.getsize(backup_file)
            print(f"✅ 백업 파일 생성 성공:")
            print(f"   📁 파일명: {backup_file}")
            print(f"   📏 크기: {file_size / 1024:.2f} KB")
            
            # 파일 내용 간단 확인
            with open(backup_file, 'r', encoding='utf-8') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                if any('PostgreSQL database dump' in line for line in first_lines):
                    print("✅ 백업 파일 형식 정상")
                else:
                    print("⚠️ 백업 파일 형식이 예상과 다릅니다")
            
            # 정리
            os.remove(backup_file)
            print(f"🗑️ 테스트 파일 삭제: {backup_file}")
            
            return True
        else:
            print(f"❌ 백업 실패:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 백업 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"❌ 백업 중 오류: {e}")
        return False

def test_scheduler_import():
    """백업 스케줄러 스크립트 import 테스트"""
    print("\n🧪 백업 스케줄러 import 테스트")
    print("-" * 30)
    
    try:
        # 기본 스케줄러 테스트
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        print("📦 railway_backup_scheduler 모듈 import 중...")
        import railway_backup_scheduler
        print("✅ railway_backup_scheduler import 성공")
        
        print("📦 advanced_backup_scheduler 모듈 import 중...")
        import advanced_backup_scheduler
        print("✅ advanced_backup_scheduler import 성공")
        
        return True
        
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Sales Note PostgreSQL 백업 시스템 테스트")
    print("=" * 60)
    
    # 환경 정보
    print(f"🖥️ 운영체제: {os.name}")
    print(f"🐍 Python: {sys.version}")
    print(f"📅 현재 시간: {datetime.datetime.now()}")
    print()
    
    # 테스트 실행
    tests = [
        ("PostgreSQL 백업 기능", test_backup),
        ("스케줄러 모듈 import", test_scheduler_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 테스트 중 예상치 못한 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} {test_name}")
        if success:
            success_count += 1
    
    print(f"\n📈 전체 결과: {success_count}/{len(results)} 테스트 통과")
    
    if success_count == len(results):
        print("🎉 모든 테스트가 성공했습니다!")
        print("💡 이제 Railway에 배포하여 자동 백업을 설정할 수 있습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        print("💡 문제를 해결한 후 다시 테스트해주세요.")
    
    return success_count == len(results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 테스트가 중단되었습니다.")
        sys.exit(1)
