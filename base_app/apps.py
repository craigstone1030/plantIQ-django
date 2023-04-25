from django.apps import AppConfig
import json

class BaseAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base_app"

    def ready(self):
        from .EchoServer import initSocketServer, boradcast
        initSocketServer( 8089 )
        from .DBMonitor import startScheduler
        startScheduler()
        # boradcast(json.dumps({"type": "DETECTOR_UPDATED", "detectorId": 1, "startAt": 1, "stopAt": 1}))