# reporting/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as django_auth_views

app_name = 'reporting'  # 앱 네임스페이스 설정

urlpatterns = [
    # 기본 로그인 (임시)
    path('', django_auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('login/', django_auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', django_auth_views.LogoutView.as_view(), name='logout'),

    # 대시보드
    path('dashboard/', views.dashboard, name='dashboard'),

    # 팔로우업 관련 URL들
    path('followup/', views.followup_list, name='followup_list'),
    path('followup/create/', views.followup_create, name='followup_create'),
    path('followup/<int:pk>/', views.followup_detail, name='followup_detail'),
    path('followup/<int:pk>/edit/', views.followup_edit, name='followup_edit'),
    path('followup/<int:pk>/delete/', views.followup_delete, name='followup_delete'),

    # 일정 관련 URL들
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    path('schedule/calendar/', views.schedule_calendar, name='schedule_calendar'),

    # 히스토리 관련 URL들
    path('history/', views.history_list, name='history_list'),
    path('history/create/', views.history_create, name='history_create'),
    path('history/<int:pk>/', views.history_detail, name='history_detail'),
    path('history/<int:pk>/edit/', views.history_edit, name='history_edit'),
    path('history/<int:pk>/delete/', views.history_delete, name='history_delete'),

    # 사용자 관리 URL들
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),

    # 담당자별 상세 보기
    path('salesman/<int:pk>/', views.salesman_detail, name='salesman_detail'),
]
