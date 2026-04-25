"""
URL configuration for sales_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='reporting:dashboard', permanent=False)),  # 루트 → 대시보드로 리다이렉트
    path('admin/', admin.site.urls),
    path('reporting/', include('reporting.urls')),
    path('todos/', include('todos.urls')),  # TODOLIST 앱
    path('ai/', include('ai_chat.urls')),  # AI PainPoint 채팅
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 프로덕션 환경에서 미디어 파일 서빙 (Railway Volume 사용)
# static() 함수는 DEBUG=True일 때만 작동하므로, re_path + serve 사용
if not settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
