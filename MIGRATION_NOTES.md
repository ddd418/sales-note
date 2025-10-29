# OpportunityTracking OneToMany 마이그레이션

## 변경 사항

### 모델 (models.py)

- ✅ `OpportunityTracking.followup`: `OneToOneField` → `ForeignKey`
- ✅ `OpportunityTracking.title` 필드 추가 (영업 기회 구분용)
- ✅ related_name: `opportunity` → `opportunities`

### Views (views.py) - 수정 필요

1. **schedule_create_view** - ✅ 완료
   - `schedule.followup.opportunity` → `schedule.followup.opportunities.exclude(current_stage='lost').first()`
2. **schedule_edit_view** - ⚠️ 수정 필요
   - Line ~1693: `updated_schedule.followup.opportunity` 변경 필요
3. **schedule_delete_view** - ⚠️ 수정 필요
   - Line ~1895: `schedule.followup.opportunity` 변경 필요
4. **schedule_move_api** - ⚠️ 수정 필요
   - Line ~4493: `schedule.followup.opportunity` 변경 필요
5. **schedule_status_update_api** - ⚠️ 수정 필요
   - Line ~4539: `schedule.followup.opportunity` 변경 필요

## 다음 단계

1. 나머지 views.py 함수 수정
2. 펀넬 분석 함수들 (funnel_analytics.py) 수정
3. 템플릿에서 복수 영업 기회 표시 UI 개선
4. 테스트

## 주의사항

- 기존 데이터는 마이그레이션으로 자동 변환됨
- 한 고객에게 여러 영업 기회 생성 가능
- 일정 생성 시 가장 최근 진행 중인 영업 기회에 자동 연결
