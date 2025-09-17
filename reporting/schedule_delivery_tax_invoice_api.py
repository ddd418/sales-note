# Schedule DeliveryItem 세금계산서 토글 API

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Schedule, DeliveryItem
from .views import can_modify_user_data

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def toggle_schedule_delivery_tax_invoice(request, schedule_id):
    """Schedule의 DeliveryItem 세금계산서 발행여부 일괄 토글 API"""
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 가능
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '세금계산서 상태를 변경할 권한이 없습니다.'
            }, status=403)
        
        # Schedule에 연결된 DeliveryItem들 조회
        delivery_items = schedule.delivery_items_set.all()
        
        if not delivery_items.exists():
            return JsonResponse({
                'success': False,
                'error': '해당 일정에 납품 품목이 없습니다.'
            })
        
        # 현재 상태 확인 (하나라도 미발행이면 모두 발행으로, 모두 발행이면 모두 미발행으로)
        any_not_issued = delivery_items.filter(tax_invoice_issued=False).exists()
        new_status = any_not_issued  # 미발행이 있으면 True(발행)로, 없으면 False(미발행)로
        
        # 일괄 업데이트
        updated_count = delivery_items.update(tax_invoice_issued=new_status)
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'updated_count': updated_count,
            'status_text': '발행됨' if new_status else '미발행'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'세금계산서 상태 변경 중 오류가 발생했습니다: {str(e)}'
        })