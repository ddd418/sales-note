# 파일 관리 관련 뷰들
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import HistoryFile, History
import os
import mimetypes


def _can_manage_history_files(user, history):
    """React 영업노트 수정 권한과 동일하게 첨부파일 조작 권한을 제한."""
    from .views import can_modify_user_data

    return bool(
        can_modify_user_data(user, history.user) and
        history.parent_history_id is None and
        history.action_type != 'memo'
    )


def _history_file_payload(file_obj, can_delete=False):
    download_url = reverse('reporting:file_download', args=[file_obj.id])
    delete_url = reverse('reporting:file_delete', args=[file_obj.id]) if can_delete else ''
    uploaded_at = file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None

    return {
        'id': file_obj.id,
        'filename': file_obj.original_filename,
        'size': file_obj.get_file_size_display(),
        'uploadedAt': uploaded_at,
        'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M') if file_obj.uploaded_at else '',
        'uploadedBy': file_obj.uploaded_by.username,
        'uploaded_by': file_obj.uploaded_by.username,
        'downloadHref': download_url,
        'download_url': download_url,
        'deleteHref': delete_url,
        'delete_url': delete_url,
        'canDelete': bool(can_delete),
        'can_delete': bool(can_delete),
    }


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
        from .views import can_access_user_data
        if not can_access_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '이 히스토리에 접근할 권한이 없습니다.'
            }, status=403)
        
        can_delete = _can_manage_history_files(request.user, history)
        files_data = [
            _history_file_payload(file_obj, can_delete=can_delete)
            for file_obj in history.files.all()
        ]
        
        return JsonResponse({
            'success': True,
            'files': files_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 목록을 불러올 수 없습니다: {str(e)}'
        }, status=500)


@login_required
@require_POST
def note_file_upload(request, history_id):
    """React 영업노트 상세 화면용 첨부파일 업로드."""
    try:
        history = get_object_or_404(History, id=history_id)

        if not _can_manage_history_files(request.user, history):
            return JsonResponse({
                'success': False,
                'error': '이 영업노트에 파일을 업로드할 권한이 없습니다.'
            }, status=403)

        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'success': False, 'error': '업로드할 파일을 선택해주세요.'}, status=400)

        existing_files_count = history.files.count()
        if existing_files_count + len(files) > 5:
            return JsonResponse({
                'success': False,
                'error': f'최대 5개까지 파일을 업로드할 수 있습니다. (현재: {existing_files_count}개)'
            }, status=400)

        from .views import validate_file_upload
        for file in files:
            is_valid, message = validate_file_upload(file)
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 "{file.name}": {message}'
                }, status=400)

        uploaded_files = []
        for file in files:
            history_file = HistoryFile.objects.create(
                history=history,
                file=file,
                original_filename=file.name,
                file_size=file.size,
                uploaded_by=request.user,
            )
            uploaded_files.append(_history_file_payload(history_file, can_delete=True))

        return JsonResponse({
            'success': True,
            'message': f'{len(uploaded_files)}개 파일이 업로드되었습니다.',
            'files': uploaded_files,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


def _can_manage_schedule_files(user, schedule):
    """React 일정 수정 권한과 동일하게 일정 첨부파일 조작 권한을 제한."""
    from .views import get_user_profile

    user_profile = get_user_profile(user)
    return bool(schedule.user_id == user.id and not user_profile.is_manager())


def _schedule_file_payload(file_obj, can_delete=False):
    download_url = reverse('reporting:schedule_file_download', args=[file_obj.id])
    delete_url = reverse('reporting:schedule_file_delete', args=[file_obj.id]) if can_delete else ''
    uploaded_at = file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None

    return {
        'id': file_obj.id,
        'filename': file_obj.original_filename,
        'size': file_obj.get_file_size_display(),
        'uploadedAt': uploaded_at,
        'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M') if file_obj.uploaded_at else '',
        'uploadedBy': file_obj.uploaded_by.username,
        'uploaded_by': file_obj.uploaded_by.username,
        'downloadHref': download_url,
        'download_url': download_url,
        'deleteHref': delete_url,
        'delete_url': delete_url,
        'canDelete': bool(can_delete),
        'can_delete': bool(can_delete),
    }


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
        if not _can_manage_schedule_files(request.user, schedule):
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
        allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', 'hwp', 'hwpx']

        # MIME 매직 바이트 시그니처 (확장자 위장 방지)
        MIME_SIGNATURES = [
            (b'%PDF',           ['pdf']),
            (b'PK\x03\x04',    ['docx', 'xlsx', 'pptx', 'zip', 'hwpx']),
            (b'\xff\xd8\xff',  ['jpg', 'jpeg']),
            (b'\x89PNG\r\n',   ['png']),
            (b'GIF87a',        ['gif']),
            (b'GIF89a',        ['gif']),
            (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', ['doc', 'xls', 'ppt', 'hwp']),
            (b'Rar!',          ['rar']),
        ]
        SKIP_MAGIC_EXTENSIONS = ['txt', 'hwp', 'hwpx', 'rar']
        
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

            # MIME 매직 바이트 검사 (확장자 위장 방지)
            if file_extension not in SKIP_MAGIC_EXTENSIONS:
                try:
                    file.seek(0)
                    header = file.read(16)
                    file.seek(0)
                    magic_ok = False
                    for signature, allowed_exts in MIME_SIGNATURES:
                        if header.startswith(signature):
                            if file_extension in allowed_exts:
                                magic_ok = True
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'error': f'파일 "{file.name}": 형식이 확장자와 일치하지 않습니다.'
                                }, status=400)
                            break
                    if not magic_ok and header and file_extension not in ['txt']:
                        return JsonResponse({
                            'success': False,
                            'error': f'파일 "{file.name}": 파일 형식을 확인할 수 없습니다.'
                        }, status=400)
                except Exception:
                    pass  # seek 불가 파일은 확장자 검사만으로 통과
            
            # 파일 저장
            schedule_file = ScheduleFile.objects.create(
                schedule=schedule,
                file=file,
                original_filename=file.name,
                file_size=file.size,
                uploaded_by=request.user
            )
            uploaded_files.append(_schedule_file_payload(schedule_file, can_delete=True))
        
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
        from django.http import FileResponse
        file_obj = get_object_or_404(ScheduleFile, id=file_id)
        
        # 권한 체크
        from .views import can_access_user_data
        if not can_access_user_data(request.user, file_obj.schedule.user):
            return HttpResponse('이 파일에 접근할 권한이 없습니다.', status=403)
        
        # FileResponse로 스트리밍 (전체 메모리 로드 방지)
        response = FileResponse(file_obj.file.open('rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_filename}"'
        return response
        
    except Exception:
        return HttpResponse('파일 다운로드 중 오류가 발생했습니다.', status=500)


@login_required
def schedule_file_delete(request, file_id):
    """일정 파일 삭제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)
    
    try:
        from .models import ScheduleFile
        file_obj = get_object_or_404(ScheduleFile, id=file_id)
        filename = file_obj.original_filename
        
        # 권한 체크
        if not _can_manage_schedule_files(request.user, file_obj.schedule):
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
        from .views import can_access_user_data
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '이 일정에 접근할 권한이 없습니다.'
            }, status=403)
        
        can_delete = _can_manage_schedule_files(request.user, schedule)
        files_data = [
            _schedule_file_payload(file_obj, can_delete=can_delete)
            for file_obj in schedule.files.all()
        ]
        
        return JsonResponse({
            'success': True,
            'files': files_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'파일 목록을 불러올 수 없습니다: {str(e)}'
        }, status=500)
