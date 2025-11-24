"""
협상(negotiation) 단계 제거 스크립트
Railway에서 실행: python remove_negotiation_stage.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import FunnelStage, OpportunityTracking

print("=" * 50)
print("협상 단계 제거 스크립트")
print("=" * 50)

# 현재 모든 단계 확인
print("\n현재 펀넬 단계:")
stages = FunnelStage.objects.all().order_by('stage_order')
for stage in stages:
    print(f"  {stage.name}: {stage.display_name} (순서: {stage.stage_order})")

# 'negotiation' 단계 확인 및 제거
negotiation = FunnelStage.objects.filter(name='negotiation').first()
if negotiation:
    print(f"\n⚠ 협상 단계 발견: {negotiation.display_name}")
    
    # 협상 단계를 사용하는 영업 기회 확인
    opps = OpportunityTracking.objects.filter(current_stage='negotiation')
    count = opps.count()
    print(f"  협상 단계 영업 기회: {count}개")
    
    if count > 0:
        # 협상 단계를 closing으로 변경
        opps.update(current_stage='closing')
        print(f"  ✓ {count}개 영업 기회를 클로징 단계로 변경했습니다.")
    
    # 협상 단계 삭제
    negotiation.delete()
    print("  ✓ 협상 단계를 삭제했습니다.")
else:
    print("\n✓ 협상 단계 없음 (정상)")

print("\n" + "=" * 50)
print("완료!")
print("=" * 50)
