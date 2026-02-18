from django.contrib import admin
from .models import AIDepartmentAnalysis, PainPointCard


@admin.register(AIDepartmentAnalysis)
class AIDepartmentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['department', 'user', 'meeting_count', 'quote_count', 'delivery_count', 'token_usage', 'updated_at']
    list_filter = ['user']
    search_fields = ['department__name', 'department__company__name']
    readonly_fields = ['analysis_data', 'quote_delivery_data']


@admin.register(PainPointCard)
class PainPointCardAdmin(admin.ModelAdmin):
    list_display = ['category', 'hypothesis_short', 'confidence', 'confidence_score', 'verification_status', 'created_at']
    list_filter = ['category', 'confidence', 'verification_status']
    search_fields = ['hypothesis']

    def hypothesis_short(self, obj):
        return obj.hypothesis[:50]
    hypothesis_short.short_description = '가설'
