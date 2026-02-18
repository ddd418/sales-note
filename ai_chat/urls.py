from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    # 부서 목록 (분석 대상 선택)
    path('', views.department_list, name='department_list'),

    # 부서 분석 결과 상세
    path('department/<int:department_id>/', views.department_analysis, name='department_analysis'),

    # 분석 실행 API
    path('department/<int:department_id>/run/', views.run_analysis, name='run_analysis'),

    # 분석 삭제 API
    path('department/<int:department_id>/delete/', views.delete_analysis, name='delete_analysis'),

    # PainPoint 카드 검증 업데이트 API
    path('card/<int:card_id>/verify/', views.verify_card, name='verify_card'),

    # FollowUp에서 부서 분석으로 이동
    path('start/<int:followup_id>/', views.start_analysis, name='start_analysis'),
]
