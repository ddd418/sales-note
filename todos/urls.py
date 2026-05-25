"""
TODOLIST URL 설정
"""
from django.urls import path
from . import views

app_name = 'todos'

urlpatterns = [
    # 메인 목록 (내 할 일)
    path('', views.react_todo_page(views.todo_list, '/tasks/'), name='list'),
    
    # CRUD
    path('create/', views.react_todo_page(views.todo_create, '/tasks/?create=1'), name='create'),
    path('<int:pk>/', views.react_todo_page(views.todo_detail, lambda request, pk: f'/tasks/{pk}/'), name='detail'),
    path('<int:pk>/edit/', views.react_todo_page(views.todo_edit, lambda request, pk: f'/tasks/{pk}/?edit=1'), name='edit'),
    path('<int:pk>/delete/', views.react_todo_page(views.todo_delete, lambda request, pk: f'/tasks/{pk}/?delete=1'), name='delete'),
    
    # 상태 변경
    path('<int:pk>/complete/', views.todo_complete, name='complete'),
    path('<int:pk>/status/', views.todo_change_status, name='change_status'),
    path('<int:pk>/cancel-request/', views.todo_cancel_request, name='cancel_request'),
    path('<int:pk>/approve/', views.todo_approve_request, name='approve_request'),
    path('<int:pk>/reject/', views.todo_reject_request, name='reject_request'),
    
    # 탭별 목록 (HTMX partial)
    path('my/', views.react_todo_page(views.todo_my_list, '/tasks/?tab=my'), name='my_list'),  # 내 할 일
    path('received/', views.react_todo_page(views.todo_received_list, '/tasks/?tab=received'), name='received_list'),  # 받은 일
    path('requested/', views.react_todo_page(views.todo_requested_list, '/tasks/?tab=requested'), name='requested_list'),  # 맡긴 일
    
    # 동료 요청
    path('request/', views.react_todo_page(views.todo_request_to_peer, '/tasks/?mode=request'), name='request_to_peer'),
    path('<int:pk>/delegate/', views.todo_delegate, name='delegate'),
    path('<int:pk>/upload-completion/', views.upload_completion_file, name='upload_completion_file'),
    
    # 동료 목록 API
    path('api/colleagues/', views.api_get_colleagues, name='api_colleagues'),
    
    # 매니저 기능
    path('manager/', views.react_todo_page(views.manager_dashboard, '/tasks/manager/'), name='manager_dashboard'),
    path('manager/assign/', views.manager_assign, name='manager_assign'),
    path('manager/task/<int:pk>/', views.react_todo_page(views.manager_task_detail, lambda request, pk: f'/tasks/{pk}/'), name='manager_task_detail'),
    path('manager/task/<int:pk>/status/', views.manager_update_status, name='manager_update_status'),
    path('manager/task/<int:pk>/cancel/', views.manager_cancel_task, name='manager_cancel_task'),
    path('manager/workload/', views.react_todo_page(views.manager_workload, '/tasks/manager/'), name='manager_workload'),
    
    # API (HTMX용)
    path('api/quick-add/', views.api_quick_add, name='api_quick_add'),
    path('api/<int:pk>/toggle/', views.api_toggle_status, name='api_toggle_status'),
    path('api/search-clients/', views.api_search_clients, name='api_search_clients'),
    
    # 카테고리 관리
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
