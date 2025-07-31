# 파일 관리 관련 뷰들
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import HistoryFile, History
import os
import mimetypes

@login_required
def file_download_view(request, file_id):
    """히스토리 첨부파일 다운로드"""
    try:
        history_file = get_object_or_404(HistoryFile, id=file_id)
        
        # 권한 체크: 해당 히스토리에 접근할 수 있는 사용자만 다운로드 가능
        from .views import can_access_user_data
        if not can_access_user_data(request.user, history_file.history.user):
            raise Http404("파일에 접근할 권한이 없습니다.")
        
        # 파일이 존재하는지 확인
        if not os.path.exists(history_file.file.path):
            messages.error(request, '파일을 찾을 수 없습니다.')
            return redirect('reporting:history_detail', pk=history_file.history.pk)
        
        # 파일 다운로드 응답 생성
        response = FileResponse(
            open(history_file.file.path, 'rb'),
            as_attachment=True,
            filename=history_file.original_filename
        )
        
        # MIME 타입 설정
        content_type, _ = mimetypes.guess_type(history_file.original_filename)
        if content_type:
            response['Content-Type'] = content_type
        
        return response
        
    except Exception as e:
        messages.error(request, f'파일 다운로드 중 오류가 발생했습니다: {str(e)}')
        return redirect('reporting:history_list')

@login_required
@require_POST
def file_delete_view(request, file_id):
    """히스토리 첨부파일 삭제"""
    try:
        history_file = get_object_or_404(HistoryFile, id=file_id)
        
        # 권한 체크: 해당 히스토리를 수정할 수 있는 사용자만 파일 삭제 가능
        from .views import can_modify_user_data
        if not can_modify_user_data(request.user, history_file.history.user):
            return JsonResponse({
                'success': False,
                'error': '파일을 삭제할 권한이 없습니다.'
            }, status=403)
        
        # 물리적 파일 삭제
        if os.path.exists(history_file.file.path):
            os.remove(history_file.file.path)
        
        # 데이터베이스에서 파일 정보 삭제
        filename = history_file.original_filename
        history_pk = history_file.history.pk
        history_file.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'파일 "{filename}"이(가) 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@login_required
def history_files_api(request, history_id):
    """히스토리의 첨부파일 목록을 JSON으로 반환"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 권한 체크
        from .views import can_access_user_data, can_modify_user_data
        if not can_access_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '이 히스토리에 접근할 권한이 없습니다.'
            }, status=403)
        
        files_data = []
        for file_obj in history.files.all():
            files_data.append({
                'id': file_obj.id,
                'filename': file_obj.original_filename,
                'size': file_obj.get_file_size_display(),
                'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'uploaded_by': file_obj.uploaded_by.username,
                'download_url': reverse('reporting:file_download', args=[file_obj.id]),
                'can_delete': can_modify_user_data(request.user, history.user)
            })
        
        return JsonResponse({
            'success': True,
            'files': files_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 목록을 불러올 수 없습니다: {str(e)}'
        }, status=500)


# 일정 파일 관련 뷰들
@login_required
def schedule_file_upload(request, schedule_id):
    """일정에 파일 업로드"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)
    
    try:
        from .models import Schedule, ScheduleFile
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크
        from .views import can_modify_user_data
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '이 일정을 수정할 권한이 없습니다.'
            }, status=403)
        
        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'success': False, 'error': '업로드할 파일을 선택해주세요.'}, status=400)
        
        # 파일 개수 제한 (5개)
        existing_files_count = schedule.files.count()
        if existing_files_count + len(files) > 5:
            return JsonResponse({
                'success': False,
                'error': f'최대 5개까지 파일을 업로드할 수 있습니다. (현재: {existing_files_count}개)'
            }, status=400)
        
        uploaded_files = []
        allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar']
        
        for file in files:
            # 파일 크기 제한 (10MB)
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 "{file.name}"의 크기가 10MB를 초과합니다.'
                }, status=400)
            
            # 파일 확장자 체크
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'success': False,
                    'error': f'지원하지 않는 파일 형식입니다: {file_extension}'
                }, status=400)
            
            # 파일 저장
            schedule_file = ScheduleFile.objects.create(
                schedule=schedule,
                file=file,
                original_filename=file.name,
                file_size=file.size,
                uploaded_by=request.user
            )
            uploaded_files.append({
                'id': schedule_file.id,
                'filename': schedule_file.original_filename,
                'size': schedule_file.get_file_size_display()
            })
        
        return JsonResponse({
            'success': True,
            'message': f'{len(uploaded_files)}개 파일이 업로드되었습니다.',
            'files': uploaded_files
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
def schedule_file_download(request, file_id):
    """일정 파일 다운로드"""
    try:
        from .models import ScheduleFile
        file_obj = get_object_or_404(ScheduleFile, id=file_id)
        
        # 권한 체크
        from .views import can_access_user_data
        if not can_access_user_data(request.user, file_obj.schedule.user):
            return HttpResponse('이 파일에 접근할 권한이 없습니다.', status=403)
        
        response = HttpResponse(file_obj.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_filename}"'
        return response
        
    except Exception as e:
        return HttpResponse(f'파일 다운로드 중 오류가 발생했습니다: {str(e)}', status=500)


@login_required
@csrf_exempt
def schedule_file_delete(request, file_id):
    """일정 파일 삭제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)
    
    try:
        from .models import ScheduleFile
        file_obj = get_object_or_404(ScheduleFile, id=file_id)
        filename = file_obj.original_filename
        
        # 권한 체크
        from .views import can_modify_user_data
        if not can_modify_user_data(request.user, file_obj.schedule.user):
            return JsonResponse({
                'success': False,
                'error': '이 파일을 삭제할 권한이 없습니다.'
            }, status=403)
        
        # 파일 삭제
        if file_obj.file:
            file_obj.file.delete()
        file_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'파일 "{filename}"이(가) 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
def schedule_files_api(request, schedule_id):
    """일정의 첨부파일 목록을 JSON으로 반환"""
    try:
        from .models import Schedule
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크
        from .views import can_access_user_data, can_modify_user_data
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '이 일정에 접근할 권한이 없습니다.'
            }, status=403)
        
        files_data = []
        for file_obj in schedule.files.all():
            files_data.append({
                'id': file_obj.id,
                'filename': file_obj.original_filename,
                'size': file_obj.get_file_size_display(),
                'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'uploaded_by': file_obj.uploaded_by.username,
                'download_url': reverse('reporting:schedule_file_download', args=[file_obj.id]),
                'can_delete': can_modify_user_data(request.user, schedule.user)
            })
        
        return JsonResponse({
            'success': True,
            'files': files_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 목록을 불러올 수 없습니다: {str(e)}'
        }, status=500)
