from django.apps import AppConfig
from . import DBMonitor

class BaseAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base_app"

    def ready(self):
        DBMonitor.start()