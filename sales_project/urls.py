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
from django.urls import path, include
from django.contrib.auth import views as auth_views # auth_views 임포트
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# 루트 URL을 대시보드로 리디렉션하는 뷰
def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('reporting:dashboard')
    else:
        return redirect('reporting:login')

urlpatterns = [
    path('', home_redirect, name='home'),  # 루트 URL 추가
    path('admin/', admin.site.urls),
    path('reporting/', include('reporting.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), # logout URL 추가
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
