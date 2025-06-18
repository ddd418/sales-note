# reporting/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # auth_views 임포트

app_name = 'reporting'  # 앱 네임스페이스 설정

urlpatterns = [
    # 팔로우업 URL들
    path('followups/', views.followup_list_view, name='followup_list'),
    path('followups/<int:pk>/', views.followup_detail_view, name='followup_detail'),
    path('followups/create/', views.followup_create_view, name='followup_create'),
    path('followups/<int:pk>/edit/', views.followup_edit_view, name='followup_edit'),
    path('followups/<int:pk>/delete/', views.followup_delete_view, name='followup_delete'),
      # 일정 URL들
    path('schedules/', views.schedule_list_view, name='schedule_list'),
    path('schedules/calendar/', views.schedule_calendar_view, name='schedule_calendar'),
    path('schedules/api/', views.schedule_api_view, name='schedule_api'),
    path('schedules/<int:pk>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedules/create/', views.schedule_create_view, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedules/<int:pk>/move/', views.schedule_move_api, name='schedule_move_api'),
    path('schedules/<int:pk>/delete/', views.schedule_delete_view, name='schedule_delete'),
      # 히스토리 URL들
    path('histories/', views.history_list_view, name='history_list'),
    path('histories/<int:pk>/', views.history_detail_view, name='history_detail'),
    path('histories/create/', views.history_create_view, name='history_create'),
    path('histories/create-from-schedule/<int:schedule_id>/', views.history_create_from_schedule, name='history_create_from_schedule'),
    path('histories/<int:pk>/edit/', views.history_edit_view, name='history_edit'),
    path('histories/<int:pk>/delete/', views.history_delete_view, name='history_delete'),
    path('histories/<int:history_id>/toggle-tax-invoice/', views.toggle_tax_invoice, name='toggle_tax_invoice'),
    path('followups/<int:followup_pk>/histories/', views.history_by_followup_view, name='history_by_followup'),
    # API 엔드포인트들
    path('api/followup/<int:followup_pk>/schedules/', views.api_followup_schedules, name='api_followup_schedules'),    # 사용자 관리 URL들 (Admin 전용)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    
    # Manager 전용 URL들
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/salesman/<int:user_id>/', views.salesman_detail, name='salesman_detail'),
    
    # 인증 및 기타 URL들
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]