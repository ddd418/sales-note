# reporting/urls.py
from django.urls import path
from . import views
from . import backup_api
from . import personal_schedule_views
from . import funnel_views
from django.contrib.auth import views as auth_views # auth_views 임포트
from importlib import import_module


def lazy_view(view_path):
    """Import rarely used view modules only when their URL is requested."""
    module_path, view_name = view_path.rsplit('.', 1)

    def _wrapped(request, *args, **kwargs):
        view = getattr(import_module(module_path), view_name)
        return view(request, *args, **kwargs)

    _wrapped.__name__ = view_name
    _wrapped.__module__ = module_path
    return _wrapped

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
    path('schedules/create/', views.schedule_create_view, name='schedule_create'),  # 캘린더 더블클릭에서 사용
    path('schedules/<int:pk>/edit/', views.schedule_edit_view, name='schedule_edit'),
    path('schedules/<int:pk>/update-delivery-items/', views.schedule_update_delivery_items, name='schedule_update_delivery_items'),
    path('schedules/<int:schedule_id>/delivery-items-api/', views.schedule_delivery_items_api, name='schedule_delivery_items_api'),
    path('schedules/<int:pk>/move/', views.schedule_move_api, name='schedule_move_api'),
    path('schedules/<int:schedule_id>/status/', views.schedule_status_update_api, name='schedule_status_update'),
    path('schedules/<int:schedule_id>/add-memo/', views.schedule_add_memo_api, name='schedule_add_memo'),
    path('schedules/<int:schedule_id>/histories/', views.schedule_histories_api, name='schedule_histories_api'),
    path('schedules/<int:pk>/delete/', views.schedule_delete_view, name='schedule_delete'),
    path('schedules/<int:schedule_id>/toggle-delivery-tax-invoice/', views.toggle_schedule_delivery_tax_invoice, name='toggle_schedule_delivery_tax_invoice'),
      # 히스토리 URL들
    path('histories/', views.history_list_view, name='history_list'),
    path('histories/<int:pk>/', views.history_detail_view, name='history_detail'),
    # 삭제됨 - 히스토리 직접 추가 불가: path('histories/create/', views.history_create_view, name='history_create'),
    path('histories/create-from-schedule/<int:schedule_id>/', views.history_create_from_schedule, name='history_create_from_schedule'),  # 캘린더에서 사용
    path('histories/<int:pk>/edit/', views.history_edit_view, name='history_edit'),
    path('histories/<int:pk>/delete/', views.history_delete_view, name='history_delete'),
    path('histories/<int:pk>/toggle-reviewed/', views.history_toggle_reviewed, name='history_toggle_reviewed'),
    path('histories/<int:history_id>/toggle-tax-invoice/', views.toggle_tax_invoice, name='toggle_tax_invoice'),
    path('histories/<int:pk>/update-tax-invoice/', views.history_update_tax_invoice, name='history_update_tax_invoice'),
    path('histories/<int:history_id>/delivery-items-api/', views.history_delivery_items_api, name='history_delivery_items_api'),
    path('followups/<int:followup_pk>/histories/', views.history_by_followup_view, name='history_by_followup'),
    
    # 고객 리포트 URL들
    path('customer-report/', views.customer_report_view, name='customer_report'),
    path('customer-report/<int:followup_id>/', views.customer_detail_report_view_simple, name='customer_detail_report'),
    path('customer-report/<int:followup_id>/toggle-all-tax-invoices/', views.toggle_all_tax_invoices, name='toggle_all_tax_invoices'),
    path('followups/<int:followup_id>/priority-update/', views.customer_priority_update, name='customer_priority_update'),
    
    # 카테고리 관리 URL들
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:category_id>/update/', views.category_update, name='category_update'),
    path('category/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('departments/<int:department_id>/assign-category/', views.department_assign_category, name='department_assign_category'),
    
    # 메모 URL들
    path('memo/create/', views.memo_create_view, name='memo_create'),
    
    # 히스토리 API 엔드포인트들
    path('api/histories/<int:history_id>/', views.history_detail_api, name='history_detail_api'),
    path('api/histories/<int:history_id>/update/', views.history_update_api, name='history_update_api'),
    path('api/histories/<int:pk>/update-memo/', views.history_update_memo, name='history_update_memo'),
    path('api/histories/<int:history_id>/add-manager-memo/', views.add_manager_memo_to_history_api, name='add_manager_memo_to_history_api'),
    path('api/histories/<int:history_id>/delete-manager-memo/', views.delete_manager_memo_api, name='delete_manager_memo_api'),
    path('api/histories/<int:history_id>/files/', views.history_files_api, name='history_files_api'),
    path('api/notes/<int:history_id>/files/upload/', views.note_file_upload, name='note_file_upload'),
    
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
    # Phase 8.6-1: 세금계산서 요청 API
    path('api/followup/<int:followup_id>/tax-invoices/', views.followup_tax_invoices_api, name='followup_tax_invoices_api'),
    path('api/tax-invoice/<int:request_id>/status/', views.tax_invoice_update_status_api, name='tax_invoice_update_status_api'),
    path('api/dashboard/', views.dashboard_summary_api, name='dashboard_summary_api'),
    # [재현] 대시보드 통합 검색 API
    path('api/dashboard/search/', views.dashboard_search_api, name='dashboard_search_api'),

    # 자동완성 API 엔드포인트들
    path('api/companies/autocomplete/', views.company_autocomplete, name='company_autocomplete'),
    path('api/companies/autocomplete/', views.company_autocomplete, name='company_autocomplete'),
    path('api/departments/autocomplete/', views.department_autocomplete, name='department_autocomplete'),
    path('api/followups/autocomplete/', views.followup_autocomplete, name='followup_autocomplete'),
    path('api/followups/<int:followup_id>/quote-items/', views.followup_quote_items_api, name='followup_quote_items_api'),
    path('api/followups/<int:followup_id>/records/', views.customer_records_api, name='customer_records_api'),
    path('api/companies/create/', views.company_create_api, name='company_create_api'),
    path('api/departments/create/', views.department_create_api, name='department_create_api'),
    path('api/followups/create/', views.followup_create_ajax, name='followup_create_ajax'),
    path('api/departments/list/<int:company_id>/', views.department_list_ajax, name='department_list_ajax'),
    path('api/schedule/activity-type/', views.schedule_activity_type, name='schedule_activity_type'),
    path('api/tax-invoice/update/', views.update_tax_invoice_status, name='update_tax_invoice_status'),
    path('api/schedules/<int:schedule_id>/delivery-items/', views.schedule_delivery_items_api, name='schedule_delivery_items_api'),
    
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
    path('users/<int:user_id>/toggle-ai/', views.user_toggle_ai, name='user_toggle_ai'),
    
    # 매니저용 사용자 관리 URL들 (Manager 전용)
    path('manager/users/', views.manager_user_list, name='manager_user_list'),
    path('manager/users/create/', views.manager_user_create, name='manager_user_create'),
    path('manager/users/<int:user_id>/edit/', views.manager_user_edit, name='manager_user_edit'),
    
    # Manager 전용 URL들
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/salesman/<int:user_id>/', views.salesman_detail, name='salesman_detail'),

    # Phase 6: 분석 보고서 URL들
    path('analytics/', views.analytics_dashboard_view, name='analytics_dashboard'),
    path('analytics/export/activity.csv', views.analytics_activity_csv_export, name='analytics_activity_csv'),
    path('analytics/export/pipeline.csv', views.analytics_pipeline_csv_export, name='analytics_pipeline_csv'),
    path('analytics/export/activity.xlsx', views.analytics_activity_xlsx_export, name='analytics_activity_xlsx'),
    path('analytics/export/pipeline.xlsx', views.analytics_pipeline_xlsx_export, name='analytics_pipeline_xlsx'),

    # 인증 및 기타 URL들
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # 프로필 관리 URL들
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # 백업 API URL들
    path('backup/database/', backup_api.backup_database_api, name='backup_database_api'),
    path('backup/status/', backup_api.backup_status_api, name='backup_status_api'),
    
    # Admin 전용 API URL들
    path('api/users/', views.api_users_list, name='api_users_list'),
    path('api/customers/', views.customers_summary_api, name='customers_summary_api'),
    path('api/customers/<int:followup_id>/', views.customer_detail_summary_api, name='customer_detail_summary_api'),
    path('api/customers/<int:followup_id>/update/', views.customer_update_api, name='customer_update_api'),
    path('api/notes/', views.notes_summary_api, name='notes_summary_api'),
    path('api/notes/create/', views.notes_create_api, name='notes_create_api'),
    path('api/notes/<int:history_id>/', views.notes_detail_api, name='notes_detail_api'),
    path('api/notes/<int:history_id>/update/', views.notes_update_api, name='notes_update_api'),
    path('api/schedules/', views.schedules_summary_api, name='schedules_summary_api'),
    path('api/schedules/create/', views.schedules_create_api, name='schedules_create_api'),
    path('api/schedules/calendar/', views.schedules_calendar_api, name='schedules_calendar_api'),
    path('api/schedules/<int:schedule_id>/', views.schedules_detail_api, name='schedules_detail_api'),
    path('api/schedules/<int:schedule_id>/update/', views.schedules_update_api, name='schedules_update_api'),
    path('api/schedules/<int:schedule_id>/delivery-items/update/', views.schedules_delivery_items_update_api, name='schedules_delivery_items_update_api'),
    path('api/personal-schedules/create/', personal_schedule_views.personal_schedules_create_api, name='personal_schedules_create_api'),
    path('api/personal-schedules/<int:pk>/', personal_schedule_views.personal_schedules_detail_api, name='personal_schedules_detail_api'),
    path('api/personal-schedules/<int:pk>/update/', personal_schedule_views.personal_schedules_update_api, name='personal_schedules_update_api'),
    path('api/personal-schedules/<int:pk>/delete/', personal_schedule_views.personal_schedules_delete_api, name='personal_schedules_delete_api'),
    path('api/ai-workspace/', views.ai_workspace_summary_api, name='ai_workspace_summary_api'),
    path('api/ai-workspace/actions/draft/', views.ai_workspace_action_draft_api, name='ai_workspace_action_draft_api'),
    path('api/companies/change-creator/', views.api_change_company_creator, name='api_change_company_creator'),
    path('api/companies/<int:company_id>/departments/', views.api_company_departments, name='api_company_departments'),
    path('api/companies/<int:company_id>/customers/', views.api_company_customers, name='api_company_customers'),
    
    # 선결제 URL들
    path('prepayment/', views.prepayment_list_view, name='prepayment_list'),
    path('prepayment/create/', views.prepayment_create_view, name='prepayment_create'),
    path('prepayment/<int:pk>/', views.prepayment_detail_view, name='prepayment_detail'),
    path('prepayment/<int:pk>/edit/', views.prepayment_edit_view, name='prepayment_edit'),
    path('prepayment/<int:pk>/delete/', views.prepayment_delete_view, name='prepayment_delete'),
    path('prepayment/<int:pk>/transfer/', views.prepayment_transfer_view, name='prepayment_transfer'),
    path('prepayment/customer/<int:customer_id>/', views.prepayment_customer_view, name='prepayment_customer'),
    path('prepayment/customer/<int:customer_id>/excel/', views.prepayment_customer_excel, name='prepayment_customer_excel'),
    path('prepayment/excel/', views.prepayment_list_excel, name='prepayment_list_excel'),
    
    # 선결제 API
    path('api/prepayments/', views.prepayment_api_list, name='prepayment_api_list'),
    path('api/prepayments/create/', views.prepayment_create_api, name='prepayment_create_api'),
    path('api/prepayments/customer/<int:customer_id>/', views.prepayment_customer_api, name='prepayment_customer_api'),
    path('api/prepayments/<int:pk>/', views.prepayment_detail_api, name='prepayment_detail_api'),
    path('api/prepayments/<int:pk>/update/', views.prepayment_update_api, name='prepayment_update_api'),
    path('api/prepayments/<int:pk>/cancel/', views.prepayment_cancel_api, name='prepayment_cancel_api'),
    path('api/prepayments/<int:pk>/delete/', views.prepayment_delete_api, name='prepayment_delete_api'),
    path('api/prepayments/<int:pk>/transfer/', views.prepayment_transfer_api, name='prepayment_transfer_api'),
    
    # 부서 메모 API
    path('api/department/<int:department_id>/memo/', views.department_memo_api, name='department_memo_api'),
    
    # 제품 관리 URL들
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/bulk-create/', views.product_bulk_create, name='product_bulk_create'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # 제품 API
    path('api/products/', views.product_api_list, name='product_api_list'),
    path('api/products/manage/', views.products_management_api, name='products_management_api'),
    path('api/products/save/', views.product_save_api, name='product_save_api'),
    path('api/products/<int:product_id>/save/', views.product_save_api, name='product_update_api'),
    path('api/products/bulk-upsert/', views.products_bulk_upsert_api, name='products_bulk_upsert_api'),
    path('api/products/bulk-delete/', views.products_bulk_delete_api, name='products_bulk_delete_api'),
    path('api/products/replace-reference/', views.product_replace_reference_api, name='product_replace_reference_api'),
    path('api/products/export.xlsx', views.products_excel_export_api, name='products_excel_export_api'),
    
    # 개인 일정 URL들
    path('personal-schedules/create/', personal_schedule_views.personal_schedule_create_view, name='personal_schedule_create'),
    path('personal-schedules/<int:pk>/', personal_schedule_views.personal_schedule_detail_view, name='personal_schedule_detail'),
    path('personal-schedules/<int:pk>/edit/', personal_schedule_views.personal_schedule_edit_view, name='personal_schedule_edit'),
    path('personal-schedules/<int:pk>/delete/', personal_schedule_views.personal_schedule_delete_view, name='personal_schedule_delete'),
    path('personal-schedules/<int:pk>/add-comment/', personal_schedule_views.personal_schedule_add_comment, name='personal_schedule_add_comment'),
    path('personal-schedules/comments/<int:comment_id>/edit/', personal_schedule_views.personal_schedule_edit_comment, name='personal_schedule_edit_comment'),
    path('personal-schedules/comments/<int:comment_id>/delete/', personal_schedule_views.personal_schedule_delete_comment, name='personal_schedule_delete_comment'),
    
    # 서류 템플릿 관리 URL들
    path('api/documents/', views.document_templates_api, name='document_templates_api'),
    path('api/documents/create/', views.document_template_create_api, name='document_template_api_create'),
    path('api/documents/<int:pk>/update/', views.document_template_update_api, name='document_template_api_update'),
    path('api/documents/<int:pk>/delete/', views.document_template_delete_api, name='document_template_api_delete'),
    path('api/documents/<int:pk>/toggle-default/', views.document_template_toggle_default_api, name='document_template_api_toggle_default'),
    path('documents/', views.document_template_list, name='document_template_list'),
    path('documents/create/', views.document_template_create, name='document_template_create'),
    path('documents/<int:pk>/edit/', views.document_template_edit, name='document_template_edit'),
    path('documents/<int:pk>/delete/', views.document_template_delete, name='document_template_delete'),
    path('documents/<int:pk>/download/', views.document_template_download, name='document_template_download'),
    path('documents/<int:pk>/toggle-default/', views.document_template_toggle_default, name='document_template_toggle_default'),
    path('documents/generated/<int:log_id>/download/', views.generated_document_download, name='generated_document_download'),
    path('documents/generated/<int:log_id>/delete/', views.generated_document_delete, name='generated_document_delete'),
    
    # 서류 템플릿 데이터 API (클라이언트 xlwings 처리용)
    path('documents/template-data/<str:document_type>/<int:schedule_id>/', views.get_document_template_data, name='get_document_template_data'),
    
    # 서류 생성 API (일정 기반) - 더 구체적인 패턴을 먼저
    path('documents/generate/<str:document_type>/<int:schedule_id>/<str:output_format>/', views.generate_document_pdf, name='generate_document_pdf_format'),
    path('documents/generate/<str:document_type>/<int:schedule_id>/', views.generate_document_pdf, name='generate_document_pdf'),
    
    # ============================================
    # Gmail 연동 URL들
    # ============================================
    
    # Gmail OAuth2 인증
    path('gmail/connect/', lazy_view('reporting.gmail_views.gmail_connect'), name='gmail_connect'),
    path('gmail/callback/', lazy_view('reporting.gmail_views.gmail_callback'), name='gmail_callback'),
    path('gmail/disconnect/', lazy_view('reporting.gmail_views.gmail_disconnect'), name='gmail_disconnect'),
    
    # 이메일 발송
    path('gmail/send/schedule/<int:schedule_id>/', lazy_view('reporting.gmail_views.send_email_from_schedule'), name='send_email_from_schedule'),
    path('gmail/send/mailbox/', lazy_view('reporting.gmail_views.send_email_from_mailbox'), name='send_email_from_mailbox'),
    path('gmail/send/mailbox/<int:followup_id>/', lazy_view('reporting.gmail_views.send_email_from_mailbox'), name='send_email_from_mailbox_with_followup'),
    path('gmail/reply/<int:email_log_id>/', lazy_view('reporting.gmail_views.reply_email'), name='reply_email'),
    
    # ============================================
    # IMAP/SMTP 연동 URL들 (커스텀 도메인 지원)
    # ============================================
    
    # IMAP/SMTP 연결 설정
    path('imap/connect/', lazy_view('reporting.imap_views.imap_connect'), name='imap_connect'),
    path('imap/disconnect/', lazy_view('reporting.imap_views.imap_disconnect'), name='imap_disconnect'),
    
    # IMAP 이메일 동기화
    path('imap/sync/', lazy_view('reporting.imap_views.sync_imap_emails'), name='sync_imap_emails'),
    
    # SMTP 이메일 발송
    path('imap/send/', lazy_view('reporting.imap_views.send_email_imap'), name='send_email_imap'),
    
    # 메일함
    path('mailbox/inbox/', lazy_view('reporting.gmail_views.mailbox_inbox'), name='mailbox_inbox'),
    path('mailbox/sent/', lazy_view('reporting.gmail_views.mailbox_sent'), name='mailbox_sent'),
    path('mailbox/starred/', lazy_view('reporting.gmail_views.mailbox_starred'), name='mailbox_starred'),
    path('mailbox/trash/', lazy_view('reporting.gmail_views.mailbox_trash'), name='mailbox_trash'),
    path('mailbox/thread/<str:thread_id>/', lazy_view('reporting.gmail_views.mailbox_thread'), name='mailbox_thread'),
    path('mailbox/sync/', lazy_view('reporting.gmail_views.sync_received_emails'), name='sync_received_emails'),
    path('mailbox/delete/<int:email_id>/', lazy_view('reporting.gmail_views.delete_email'), name='delete_email'),
    path('mailbox/toggle-star/<int:email_id>/', lazy_view('reporting.gmail_views.toggle_star_email'), name='toggle_star_email'),
    path('mailbox/archive/<int:email_id>/', lazy_view('reporting.gmail_views.archive_email'), name='archive_email'),
    path('mailbox/move-to-trash/<int:email_id>/', lazy_view('reporting.gmail_views.move_to_trash_email'), name='move_to_trash_email'),
    path('mailbox/restore/<int:email_id>/', lazy_view('reporting.gmail_views.restore_email'), name='restore_email'),

    # React 메일함 API
    path('api/mailbox/', lazy_view('reporting.gmail_views.mailbox_api_list'), name='mailbox_api_list'),
    path('api/mailbox/thread/<str:thread_id>/', lazy_view('reporting.gmail_views.mailbox_api_thread'), name='mailbox_api_thread'),
    path('api/mailbox/send/', lazy_view('reporting.gmail_views.mailbox_api_send'), name='mailbox_api_send'),
    path('api/mailbox/reply/<int:email_id>/', lazy_view('reporting.gmail_views.mailbox_api_reply'), name='mailbox_api_reply'),
    path('api/mailbox/sync/', lazy_view('reporting.gmail_views.mailbox_api_sync'), name='mailbox_api_sync'),
    path('api/mailbox/<int:email_id>/toggle-star/', lazy_view('reporting.gmail_views.mailbox_api_toggle_star'), name='mailbox_api_toggle_star'),
    path('api/mailbox/<int:email_id>/archive/', lazy_view('reporting.gmail_views.mailbox_api_archive'), name='mailbox_api_archive'),
    path('api/mailbox/<int:email_id>/move-to-trash/', lazy_view('reporting.gmail_views.mailbox_api_move_to_trash'), name='mailbox_api_move_to_trash'),
    path('api/mailbox/<int:email_id>/restore/', lazy_view('reporting.gmail_views.mailbox_api_restore'), name='mailbox_api_restore'),
    path('api/mailbox/<int:email_id>/delete/', lazy_view('reporting.gmail_views.mailbox_api_delete'), name='mailbox_api_delete'),
    path('api/mailbox/<int:email_id>/attachments/<int:attachment_index>/', lazy_view('reporting.gmail_views.mailbox_api_attachment_download'), name='mailbox_api_attachment_download'),
    
    # 명함 관리
    path('business-cards/', lazy_view('reporting.gmail_views.business_card_list'), name='business_card_list'),
    path('business-cards/create/', lazy_view('reporting.gmail_views.business_card_create'), name='business_card_create'),
    path('business-cards/<int:card_id>/edit/', lazy_view('reporting.gmail_views.business_card_edit'), name='business_card_edit'),
    path('business-cards/<int:card_id>/delete/', lazy_view('reporting.gmail_views.business_card_delete'), name='business_card_delete'),
    path('business-cards/<int:card_id>/set-default/', lazy_view('reporting.gmail_views.business_card_set_default'), name='business_card_set_default'),
    
    # 이미지 업로드
    path('upload-image/', lazy_view('reporting.gmail_views.upload_editor_image'), name='upload_editor_image'),
    
    # 관리자 필터 API
    path('set-admin-filter/', views.set_admin_filter, name='set_admin_filter'),
    path('get-company-users/<int:company_id>/', views.get_company_users, name='get_company_users'),
    
    # 빠른 고객 등록 (이메일 발송용)
    path('quick-add-customer/', views.quick_add_customer, name='quick_add_customer'),
    path('quick-add-company/', views.quick_add_company, name='quick_add_company'),
    path('quick-add-department/', views.quick_add_department, name='quick_add_department'),
    
    # 법적 문서
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    
    # ============================================
    # 펀넬 관리 URL들
    # ============================================
    path('funnel/', funnel_views.funnel_list_view, name='funnel_list'),
    path('funnel/pipeline/', funnel_views.funnel_pipeline_view, name='funnel_pipeline'),
    path('funnel/<int:department_id>/', funnel_views.funnel_detail_view, name='funnel_detail'),
    path('api/pipeline/', funnel_views.pipeline_command_center_api, name='pipeline_command_center_api'),
    path('funnel/api/save-target/', funnel_views.funnel_save_target, name='funnel_save_target'),
    path('funnel/api/auto-target/', funnel_views.funnel_auto_target, name='funnel_auto_target'),
    path('funnel/api/bulk-auto-target/', funnel_views.funnel_bulk_auto_target, name='funnel_bulk_auto_target'),
    path('funnel/api/add-department/', funnel_views.funnel_add_department, name='funnel_add_department'),
    path('funnel/api/remove-department/', funnel_views.funnel_remove_department, name='funnel_remove_department'),
    path('funnel/api/search-departments/', funnel_views.funnel_search_departments, name='funnel_search_departments'),
    path('funnel/api/pipeline-move/', funnel_views.funnel_pipeline_move, name='funnel_pipeline_move'),
    path('funnel/api/pipeline-sync/', funnel_views.funnel_pipeline_sync, name='funnel_pipeline_sync'),

    # ============================================
    # 주간보고 URL
    # ============================================
    path('weekly-reports/', views.weekly_report_list, name='weekly_report_list'),
    path('weekly-reports/create/', views.weekly_report_create, name='weekly_report_create'),
    path('weekly-reports/<int:pk>/', views.weekly_report_detail, name='weekly_report_detail'),
    path('weekly-reports/<int:pk>/edit/', views.weekly_report_edit, name='weekly_report_edit'),
    path('weekly-reports/<int:pk>/delete/', views.weekly_report_delete, name='weekly_report_delete'),
    path('api/weekly-reports/', views.weekly_reports_api, name='weekly_reports_api'),
    path('api/weekly-reports/create/', views.weekly_report_create_api, name='weekly_report_create_api'),
    path('api/weekly-reports/<int:pk>/', views.weekly_report_detail_api, name='weekly_report_detail_api'),
    path('api/weekly-reports/<int:pk>/update/', views.weekly_report_update_api, name='weekly_report_update_api'),
    path('api/weekly-reports/<int:pk>/delete/', views.weekly_report_delete_api, name='weekly_report_delete_api'),
    path('api/weekly-reports/schedules/', views.weekly_report_load_schedules, name='weekly_report_load_schedules'),
    path('api/weekly-reports/ai-draft/', views.weekly_report_ai_draft, name='weekly_report_ai_draft'),
    path('api/weekly-reports/<int:pk>/manager-comment/', views.weekly_report_manager_comment, name='weekly_report_manager_comment'),
]

