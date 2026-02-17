from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    # 채팅방 목록
    path('', views.room_list, name='room_list'),
    
    # 채팅방 상세 (대화 UI)
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    
    # 메시지 전송 API
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),
    
    # 미팅록(History)에서 분석 시작
    path('analyze/<int:history_id>/', views.analyze_history, name='analyze_history'),
    
    # PainPoint 카드 검증 업데이트 API
    path('card/<int:card_id>/verify/', views.verify_card, name='verify_card'),
    
    # FollowUp에서 새 채팅방 생성/이동
    path('start/<int:followup_id>/', views.start_chat, name='start_chat'),
]
