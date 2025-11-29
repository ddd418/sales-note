"""
TODOLIST URL 설정
"""
from django.urls import path
from . import views

app_name = 'todos'

urlpatterns = [
    # 메인 목록 (내 할 일)
    path('', views.todo_list, name='list'),
    
    # CRUD
    path('create/', views.todo_create, name='create'),
    path('<int:pk>/', views.todo_detail, name='detail'),
    path('<int:pk>/edit/', views.todo_edit, name='edit'),
    path('<int:pk>/delete/', views.todo_delete, name='delete'),
    
    # 상태 변경
    path('<int:pk>/complete/', views.todo_complete, name='complete'),
    path('<int:pk>/status/', views.todo_change_status, name='change_status'),
    
    # 탭별 목록 (HTMX partial)
    path('my/', views.todo_my_list, name='my_list'),  # 내 할 일
    path('received/', views.todo_received_list, name='received_list'),  # 받은 일
    path('requested/', views.todo_requested_list, name='requested_list'),  # 맡긴 일
    
    # 동료 요청
    path('request/', views.todo_request_to_peer, name='request_to_peer'),
    
    # 매니저 기능
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/assign/', views.manager_assign, name='manager_assign'),
    path('manager/workload/', views.manager_workload, name='manager_workload'),
    
    # API (HTMX용)
    path('api/quick-add/', views.api_quick_add, name='api_quick_add'),
    path('api/<int:pk>/toggle/', views.api_toggle_status, name='api_toggle_status'),
    path('api/search-clients/', views.api_search_clients, name='api_search_clients'),
]
