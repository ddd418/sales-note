"""
기존 명함의 서명 HTML을 새로운 포맷으로 업데이트하는 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import BusinessCard

def update_all_signatures():
    """모든 명함의 서명을 새 포맷으로 재생성"""
    
    cards = BusinessCard.objects.all()
    total = cards.count()
    
    print(f"총 {total}개 명함의 서명을 업데이트합니다...\n")
    
    updated_count = 0
    
    for i, card in enumerate(cards, 1):
        try:
            # 기존 signature_html 백업 (필요시)
            old_signature = card.signature_html
            
            # signature_html을 비우고 generate_signature로 새로 생성
            card.signature_html = ''
            new_signature = card.generate_signature()
            
            # 새 서명으로 업데이트
            card.signature_html = new_signature
            card.save(update_fields=['signature_html'])
            
            updated_count += 1
            print(f"[{i}/{total}] ✓ {card.name} - {card.full_name}")
            print(f"   회사: {card.company_name}")
            
        except Exception as e:
            print(f"[{i}/{total}] ✗ {card.name} - 오류: {e}")
    
    print(f"\n{'='*50}")
    print(f"완료: {updated_count}/{total}건 업데이트")
    print(f"{'='*50}\n")
    
    if updated_count > 0:
        print("✓ 명함 서명이 새 포맷으로 업데이트되었습니다.")
        print("  - line-height: 1.3")
        print("  - 각 줄 간격: 2px")
        print("  - 로고 하단 여백: 4px")
    else:
        print("업데이트할 명함이 없습니다.")

if __name__ == '__main__':
    update_all_signatures()
