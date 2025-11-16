"""
로그 제거 스크립트 - 남은 모든 logger.info/debug/warning 제거
"""
import re

# 파일 읽기
with open('reporting/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# logger.info(...) 패턴 제거 (여러 줄에 걸쳐있을 수 있음)
content = re.sub(r'\s*logger\.info\([^)]*\)\s*\n', '\n', content)

# logger.debug(...) 패턴 제거  
content = re.sub(r'\s*logger\.debug\([^)]*\)\s*\n', '\n', content)

# logger.warning(...) 패턴 제거
content = re.sub(r'\s*logger\.warning\([^)]*\)\s*\n', '\n', content)

# 불필요한 빈 줄 정리 (3개 이상의 연속된 빈 줄을 2개로)
content = re.sub(r'\n\n\n+', '\n\n', content)

# 저장
with open('reporting/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("로그 제거 완료!")

