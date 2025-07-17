from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.utils.decorators import method_decorator
from .forms import CompanyLoginForm, CompanyRegistrationForm # , UserCreateForm
from .models import Company, UserProfile
from .authentication import CompanyBasedPermissionMixin


def company_login_view(request):
    """
    회사코드 + 사번 + 비밀번호 로그인
    """
    if request.user.is_authenticated:
        return redirect('reporting:dashboard')
    
    form = CompanyLoginForm()
    
    if request.method == 'POST':
        form = CompanyLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # 로그인 상태 유지 설정
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # 브라우저 종료시 로그아웃
            
            messages.success(request, f'{user.userprofile.company.company_name}에 로그인했습니다.')
            
            # 다음 페이지로 리다이렉트
            next_page = request.GET.get('next', 'reporting:dashboard')
            return redirect(next_page)
    
    return render(request, 'registration/company_login.html', {'form': form})


def company_register_view(request):
    """
    회사 등록 뷰
    """
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(
                request, 
                f'회사 등록이 완료되었습니다. 회사코드: {company.company_code}'
            )
            return redirect('reporting:company_login')
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'registration/company_register.html', {'form': form})


def company_logout_view(request):
    """
    로그아웃
    """
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('reporting:company_login')


@method_decorator(login_required, name='dispatch')
class UserManagementView(CompanyBasedPermissionMixin, ListView):
    """
    사용자 관리 뷰 (회사 관리자만 접근 가능)
    """
    model = UserProfile
    template_name = 'reporting/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # 회사 관리자만 접근 가능
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.can_create_users():
            messages.error(request, '접근 권한이 없습니다.')
            return redirect('reporting:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.request.user.userprofile.company
        context['can_add_user'] = self.request.user.userprofile.company.can_add_user()
        return context


# @login_required
# def user_create_view(request):
#     """
#     새 사용자 추가 (회사 관리자만) - 임시 주석 처리
#     """
#     pass


@login_required
def company_info_view(request):
    """
    회사 정보 조회
    """
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, '사용자 프로필이 없습니다.')
        return redirect('reporting:dashboard')
    
    company = request.user.userprofile.company
    users = company.users.all().order_by('role', 'user__username')
    
    context = {
        'company': company,
        'users': users,
        'user_profile': request.user.userprofile,
    }
    
    return render(request, 'reporting/company_info.html', context)
