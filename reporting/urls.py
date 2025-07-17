# reporting/urls.py
from django.urls import path
from django.contrib.auth import views as django_auth_views
from . import views

app_name = 'reporting'  # 앱 네임스페이스 설정

urlpatterns = [
    # 회사 로그인 (메인)
    path('', views.company_login_view, name='company_login'),
    path('company-login/', views.company_login_view, name='company_login'),
    
    # Super Admin 로그인 (Django 기본 로그인)
    path('admin-login/', django_auth_views.LoginView.as_view(template_name='registration/admin_login.html'), name='admin_login'),
    
    # 기본 Django 로그인도 회사 로그인으로 리다이렉트
    path('login/', views.company_login_view, name='login'),
    path('logout/', django_auth_views.LogoutView.as_view(), name='logout'),
    
    # 대시보드 (로그인 후 이동할 페이지)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # 팔로우업 관련 URL
    path('followups/', views.followup_list_view, name='followup_list'),
    path('followups/<int:pk>/', views.followup_detail_view, name='followup_detail'),
    path('followups/create/', views.followup_create_view, name='followup_create'),
    path('followups/<int:pk>/edit/', views.followup_edit_view, name='followup_edit'),
    path('followups/<int:pk>/delete/', views.followup_delete_view, name='followup_delete'),
    
    # 일정 관련 URL
    path('schedules/', views.schedule_list_view, name='schedule_list'),
    path('schedules/<int:pk>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedules/create/', views.schedule_create_view, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete_view, name='schedule_delete'),
    path('schedules/calendar/', views.schedule_calendar_view, name='schedule_calendar'),
    
    # 히스토리 관련 URL
    path('histories/', views.history_list_view, name='history_list'),
    path('histories/<int:pk>/', views.history_detail_view, name='history_detail'),
    path('histories/create/', views.history_create_view, name='history_create'),
    path('histories/<int:pk>/edit/', views.history_edit_view, name='history_edit'),
    path('histories/<int:pk>/delete/', views.history_delete_view, name='history_delete'),
    
    # 사용자 관리 URL (Admin 전용)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    
    # Manager 전용 URL
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/salesman/<int:user_id>/', views.salesman_detail, name='salesman_detail'),
    
    # API URL들
    path('api/schedules/', views.schedule_api_view, name='schedule_api'),
    path('api/followup/<int:followup_pk>/schedules/', views.api_followup_schedules, name='api_followup_schedules'),
    path('api/schedule/<int:schedule_id>/histories/', views.schedule_histories_api, name='schedule_histories_api'),
    path('api/followup/<int:followup_id>/histories/', views.followup_histories_api, name='followup_histories_api'),
    path('api/history/<int:history_id>/toggle-tax-invoice/', views.toggle_tax_invoice, name='toggle_tax_invoice'),
    path('api/schedule/<int:pk>/move/', views.schedule_move_api, name='schedule_move_api'),
    path('api/schedule/<int:schedule_id>/status/', views.schedule_status_update_api, name='schedule_status_update_api'),
    
    # 히스토리 생성 (일정에서)
    path('schedules/<int:schedule_id>/add-history/', views.history_create_from_schedule, name='history_create_from_schedule'),
    
    # Super Admin 전용 URL
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/companies/', views.company_list, name='company_list'),
    path('super-admin/companies/create/', views.company_create, name='company_create'),
    path('super-admin/companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('super-admin/companies/<int:company_id>/edit/', views.company_edit, name='company_edit'),
    path('super-admin/companies/<int:company_id>/delete/', views.company_delete, name='company_delete'),
    
    # 팔로우업별 히스토리
    path('followups/<int:followup_pk>/histories/', views.history_by_followup_view, name='history_by_followup'),
]
