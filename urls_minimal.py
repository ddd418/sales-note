# reporting/urls.py
from django.urls import path
from django.contrib.auth import views as django_auth_views

app_name = 'reporting'

urlpatterns = [
    # 기본 로그인만
    path('', django_auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('login/', django_auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', django_auth_views.LogoutView.as_view(), name='logout'),
]
