# DeliveryItem 모델 관리자 설정
@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'schedule', 'quantity', 'unit', 'unit_price', 'total_price', 'created_at')
    list_filter = ('schedule__activity_type', 'schedule__user', 'created_at')
    search_fields = ('item_name', 'schedule__followup__customer_name', 'notes')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['schedule']
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    list_per_page = 20
