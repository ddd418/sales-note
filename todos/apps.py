from django.apps import AppConfig


class TodosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todos'
    verbose_name = 'TODOLIST 관리'
    
    def ready(self):
        pass  # signals 등 추후 등록
