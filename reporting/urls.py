# reporting/urls.py
from django.urls import path
from . import views
from . import backup_api
from django.contrib.auth import views as auth_views # auth_views 임포트

app_name = 'reporting'  # 앱 네임스페이스 설정

urlpatterns = [
    # 팔로우업 URL들
    path('followups/', views.followup_list_view, name='followup_list'),
    path('followups/<int:pk>/', views.followup_detail_view, name='followup_detail'),
    path('followups/create/', views.followup_create_view, name='followup_create'),
    path('followups/<int:pk>/edit/', views.followup_edit_view, name='followup_edit'),
    path('followups/<int:pk>/delete/', views.followup_delete_view, name='followup_delete'),
    path('followups/excel-download/', views.followup_excel_download, name='followup_excel_download'),
    path('followups/basic-excel-download/', views.followup_basic_excel_download, name='followup_basic_excel_download'),
      # 일정 URL들
    path('schedules/', views.schedule_list_view, name='schedule_list'),
    path('schedules/calendar/', views.schedule_calendar_view, name='schedule_calendar'),
    path('schedules/api/', views.schedule_api_view, name='schedule_api'),
    path('schedules/<int:pk>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedules/create/', views.schedule_create_view, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedules/<int:pk>/move/', views.schedule_move_api, name='schedule_move_api'),
    path('schedules/<int:schedule_id>/status/', views.schedule_status_update_api, name='schedule_status_update'),
    path('schedules/<int:schedule_id>/add-memo/', views.schedule_add_memo_api, name='schedule_add_memo'),
    path('schedules/<int:schedule_id>/histories/', views.schedule_histories_api, name='schedule_histories_api'),
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
    
    # 메모 URL들
    path('memo/create/', views.memo_create_view, name='memo_create'),
    
    # 히스토리 API 엔드포인트들
    path('api/histories/<int:history_id>/', views.history_detail_api, name='history_detail_api'),
    path('api/histories/<int:history_id>/update/', views.history_update_api, name='history_update_api'),
    path('api/histories/<int:pk>/update-memo/', views.history_update_memo, name='history_update_memo'),
    path('api/histories/<int:history_id>/files/', views.history_files_api, name='history_files_api'),
    
    # 파일 관리 URL들
    path('files/<int:file_id>/download/', views.file_download_view, name='file_download'),
    path('files/<int:file_id>/delete/', views.file_delete_view, name='file_delete'),
    
    # 일정 파일 관리 URL들
    path('schedules/<int:schedule_id>/files/upload/', views.schedule_file_upload, name='schedule_file_upload'),
    path('schedule-files/<int:file_id>/download/', views.schedule_file_download, name='schedule_file_download'),
    path('schedule-files/<int:file_id>/delete/', views.schedule_file_delete, name='schedule_file_delete'),
    path('api/schedules/<int:schedule_id>/files/', views.schedule_files_api, name='schedule_files_api'),
    # API 엔드포인트들
    path('api/followup/<int:followup_pk>/schedules/', views.api_followup_schedules, name='api_followup_schedules'),
    path('api/followup/<int:followup_id>/histories/', views.followup_histories_api, name='followup_histories_api'),
    
    # 자동완성 API 엔드포인트들
    path('api/companies/autocomplete/', views.company_autocomplete, name='company_autocomplete'),
    path('api/departments/autocomplete/', views.department_autocomplete, name='department_autocomplete'),
    path('api/followups/autocomplete/', views.followup_autocomplete, name='followup_autocomplete'),
    path('api/companies/create/', views.company_create_api, name='company_create_api'),
    path('api/departments/create/', views.department_create_api, name='department_create_api'),
    path('api/schedule/activity-type/', views.schedule_activity_type, name='schedule_activity_type'),
    
    # 개별 조회 API 엔드포인트들
    path('api/companies/<int:pk>/', views.api_company_detail, name='api_company_detail'),
    path('api/departments/<int:pk>/', views.api_department_detail, name='api_department_detail'),
    
    # 업체/부서 관리 URL들
    path('companies/', views.company_list_view, name='company_list'),
    path('companies/create/', views.company_create_view, name='company_create'),
    path('companies/<int:pk>/', views.company_detail_view, name='company_detail'),
    path('companies/<int:pk>/edit/', views.company_edit_view, name='company_edit'),
    path('companies/<int:pk>/delete/', views.company_delete_view, name='company_delete'),
    path('companies/<int:company_pk>/departments/create/', views.department_create_view, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit_view, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete_view, name='department_delete'),

    # 매니저용 읽기 전용 업체 관리 URL들
    path('manager/companies/', views.manager_company_list_view, name='manager_company_list'),
    path('manager/companies/<int:pk>/', views.manager_company_detail_view, name='manager_company_detail'),    # 사용자 관리 URL들 (Admin 전용)
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
    
    # 백업 API URL들
    path('backup/database/', backup_api.backup_database_api, name='backup_database_api'),
    path('backup/status/', backup_api.backup_status_api, name='backup_status_api'),
]