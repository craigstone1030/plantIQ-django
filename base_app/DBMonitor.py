from apscheduler.schedulers.background import BackgroundScheduler
from .models import *
from .influxDB import *
from .EchoServer import *
from django.conf import settings
import django.core.serializers
from .DetectorThread import DetectorThread
from .MeasurementThread import MeasurementThread

# metricList = [] # this variables are for updating last update dates
# update_callcnt = 0
detectThreadList = []
metricThreadList = []

def startScheduler():

    scheduler = BackgroundScheduler()
    # scheduler.add_job(run, 'interval', seconds=settings.UPDATE_INTERVAL)
    scheduler.add_job(socket_handler, 'interval', seconds=1)
    scheduler.add_job(processDetector, 'interval', seconds=5)
    scheduler.add_job(processDatasource, 'interval', seconds=5)
    scheduler.start()


    # run()

    detectors = ModelDetector.objects.filter(deleted=0)
    for detector in detectors:
        thread = DetectorThread(detector.pk)
        thread.start()

        detectThreadList.append(thread)

    datasources = ModelDatasource.objects.filter(deleted=0)
    for datasource in datasources:
        thread = MeasurementThread(datasource.pk)
        thread.start()

        metricThreadList.append(thread)

def createNewDatasource(datasourceId):
    for thread in metricThreadList:
        if thread.datasourceId == datasourceId: return

    thread = MeasurementThread(datasourceId)
    thread.start()

    metricThreadList.append(thread)

def createNewDetector(detectorId):
    for thread in detectThreadList:
        if thread.detectorId == detectorId:
            print(f'create detector faild detectorId:{detectorId}')
            return
    
    thread = DetectorThread(detectorId)
    thread.start()
    
    prevLength = len(detectThreadList)
    detectThreadList.append(thread)

def deleteDatasource(datasourceId):
    for thread in metricThreadList:
        if thread.datasourceId == datasourceId:
            thread.stop(); metricThreadList.remove(thread)

def deleteDetector(detectorId):
    prevLength = len(detectThreadList)
    for thread in detectThreadList:
        if thread.detectorId == detectorId:
            thread.stop(); detectThreadList.remove(thread)

# this func is to create thread for new detector every 5 seconds
def processDetector():
    detectors = ModelDetector.objects.all()
    for detector in detectors:
        if detector.lastUpdate == 'None':
            createNewDetector(detector.pk)
        if detector.deleted == 1:
            deleteDetector(detector.pk)

def processDatasource():
    datasources = ModelDatasource.objects.all()
    for datasource in datasources:
        if datasource.lastUpdate == 'None':
            createNewDatasource(datasource.pk)
        if datasource.deleted == 1:
            deleteDatasource(datasource.pk)

def socket_handler():
    websocketServer.handle_request()