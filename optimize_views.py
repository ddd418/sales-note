"""
views.py 최적화 스크립트
- 모든 logger.info, logger.debug, logger.warning 제거
- logger.error만 남김 (실제 오류 추적용)
"""

import re

def remove_logs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # logger.info, logger.debug, logger.warning 제거 (한 줄 또는 여러 줄)
    patterns = [
        r'logger\.info\([^)]*\)\n',
        r'logger\.debug\([^)]*\)\n',
        r'logger\.warning\([^)]*\)\n',
        # f-string으로 여러 줄에 걸친 경우
        r'logger\.info\(f?"[^"]*"\s*\)\n',
        r'logger\.debug\(f?"[^"]*"\s*\)\n',
        r'logger\.warning\(f?"[^"]*"\s*\)\n',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content)
    
    # 빈 줄 2개 이상을 1개로
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 최적화 완료: {file_path}")

if __name__ == '__main__':
    remove_logs('c:/projects/sales-note/reporting/views.py')
