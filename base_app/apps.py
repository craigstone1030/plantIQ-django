from django.apps import AppConfig
import json
import os

class BaseAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base_app"

    def ready(self):
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE') 
        if run_once is not None:
            return
        os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True' 
    
        from .EchoServer import initSocketServer, boradcast
        initSocketServer( 8089 )
        from .DBMonitor import startScheduler
        startScheduler()