from django.contrib import admin
from .models import AIChatRoom, AIChatMessage, PainPointCard


@admin.register(AIChatRoom)
class AIChatRoomAdmin(admin.ModelAdmin):
    list_display = ['followup', 'user', 'title', 'updated_at']
    list_filter = ['user']
    search_fields = ['title', 'followup__customer_name']


@admin.register(AIChatMessage)
class AIChatMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'role', 'content_short', 'token_usage', 'created_at']
    list_filter = ['role', 'room']
    readonly_fields = ['structured_data']

    def content_short(self, obj):
        return obj.content[:60]
    content_short.short_description = '내용'


@admin.register(PainPointCard)
class PainPointCardAdmin(admin.ModelAdmin):
    list_display = ['category', 'hypothesis_short', 'confidence', 'confidence_score', 'verification_status', 'created_at']
    list_filter = ['category', 'confidence', 'verification_status']
    search_fields = ['hypothesis']

    def hypothesis_short(self, obj):
        return obj.hypothesis[:50]
    hypothesis_short.short_description = '가설'
