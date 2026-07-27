from django.apps import AppConfig


class ReportingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reporting'
    
    def ready(self):
        """앱 초기화 시 시그널 등록"""
        import reporting.signals
