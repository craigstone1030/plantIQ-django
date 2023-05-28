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

def indexOfMetric( dsId, metricName ):
    i = 0
    for metric in metricList:
        if metric["dsId"] == dsId and metric["metric"] == metricName:
            return i
        i = i + 1
    return -1

def startScheduler():

    scheduler = BackgroundScheduler()
    # scheduler.add_job(run, 'interval', seconds=settings.UPDATE_INTERVAL)
    scheduler.add_job(socket_handler, 'interval', seconds=1)
    # scheduler.add_job(processDetector, 'interval', seconds=5)
    scheduler.start()

    # run()

    detectors = ModelDetector.objects.all()
    for detector in detectors:
        thread = DetectorThread(detector.pk)
        thread.start()

        detectThreadList.append(thread)

    datasources = ModelDatasource.objects.all()
    for datasource in datasources:
        thread = MeasurementThread(datasource.pk)
        thread.start()

        metricThreadList.append(thread)

def processDetector():
    detectors = ModelDetector.objects.all()
    for detector in detectors:
        if detector.lastUpdate == 'None':

            datasource = detector.getDatasource()
            if datasource == None: continue

            influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
            metrics = detector.getMetricList()
            startUpdatedAt = None; stopUpdatedAt = None

            for metricName in metrics:
                
                lastUpdate = 'None'; initialAt = 'None'
                initialAt = getInitialAt(influxHandle, datasource.bucket, metricName)
                ret, curLastUpdate = isUpdateAvailable(influxHandle, datasource.bucket, metricName, lastUpdate)
                
                if startUpdatedAt == None or startUpdatedAt < initialAt:
                    startUpdatedAt = initialAt
                if stopUpdatedAt == None or stopUpdatedAt > curLastUpdate:
                    stopUpdatedAt = curLastUpdate

            print(f"Create need! {detector.pk} {startUpdatedAt} ~ {stopUpdatedAt}")

            updateDetection(influxHandle, datasource.bucket, datasource.org, detector.exportCode, metrics, startUpdatedAt, stopUpdatedAt)
            influxHandle.close(); del influxHandle

            detector.lastUpdate = stopUpdatedAt
            detector.save()

            boradcast(json.dumps({
                "type": "DETECTOR_UPDATED",
                "detectorId": detector.pk,
                "startAt": startUpdatedAt,
                "stopAt": stopUpdatedAt}))

def socket_handler():
    websocketServer.handle_request()


def run():
    global metricList
    global update_callcnt

    update_callcnt = update_callcnt + 1
    print("==============", update_callcnt, "================")

    # Update lastUpdate
    datasources = ModelDatasource.objects.all()
    for datasource in datasources:
        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        ret, metrics = getAllMeasurements(influxHandle, datasource.bucket)
        if ret == 'success':
            for metricName in metrics:
                lastUpdate = 'None'; initialAt = 'None'
                indexOf = indexOfMetric(datasource.pk, metricName)
                if indexOf > -1:
                    lastUpdate = metricList[indexOf]["lastUpdate"]
                    metricList.remove(metricList[indexOf])

                initialAt = getInitialAt(influxHandle, datasource.bucket, metricName)
                ret, curLastUpdate = isUpdateAvailable(influxHandle, datasource.bucket, metricName, lastUpdate)
                metricList.append( { "dsId": datasource.pk, "metric": metricName, "initialAt": initialAt,"lastUpdate": curLastUpdate, "prevLastUpdate": lastUpdate } )
                # print( datasource.pk, metricName, lastUpdate, curLastUpdate, len(metricList) )
        influxHandle.close(); del influxHandle
    
    #  
    detectors = ModelDetector.objects.all()
    for detector in detectors:
        if detector.status == 0: continue

        datasource = detector.getDatasource()
        if datasource == None: continue

        metrics = detector.getMetricList()
        startUpdatedAt = None; stopUpdatedAt = None

        for metric in metrics:
            indexOf = indexOfMetric(datasource.pk, metric)
            if indexOf == -1:
                continue

            if detector.lastUpdate == 'None':
                if startUpdatedAt == None or startUpdatedAt > metricList[indexOf]["initialAt"]:
                    startUpdatedAt = metricList[indexOf]["initialAt"]
            else:
                if startUpdatedAt == None or startUpdatedAt > metricList[indexOf]["prevLastUpdate"]:
                    startUpdatedAt = metricList[indexOf]["prevLastUpdate"]

            if stopUpdatedAt == None or stopUpdatedAt > metricList[indexOf]["lastUpdate"]:
                stopUpdatedAt = metricList[indexOf]["lastUpdate"]
        
        # print( startUpdatedAt, stopUpdatedAt )

        if detector.lastUpdate != 'None':
            if pd.isnull(startUpdatedAt) or pd.isnull(stopUpdatedAt):
                continue

            if startUpdatedAt >= stopUpdatedAt :
                continue

        print(f"Update need! {detector.pk} {startUpdatedAt} ~ {stopUpdatedAt}")

        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        detectResult = updateDetection(influxHandle, datasource.bucket, datasource.org, detector.exportCode, metrics, startUpdatedAt, stopUpdatedAt)
        influxHandle.close(); del influxHandle

        print(f"Detecting anomaly {detector.pk}")
        
        detectAnomaly( detector, detectResult )

        detector.lastScore = detectResult[len(detectResult) - 1][1]
        detector.lastUpdate = stopUpdatedAt
        detector.save()

        boradcast(json.dumps({
            "type": SC_DETECTOR_UPDATED,
            "detectorId": detector.pk,
            "startAt": startUpdatedAt,
            "stopAt": stopUpdatedAt}))
        
# detectResult: should be sorted by datetime
def detectAnomaly(detector, detectResult): 
    alertHistorys = []

    alerts = ModelAlert.objects.filter(detector=detector)
    
    for alert in alerts:
        # Immedietly Detection
        if alert.duration == 0:
            pLevel = 0; cLevel = 0
            for detectItem in detectResult:
                at = detectItem[1]; value = detectItem[2]

                if detector.maxAnomaly < detectItem[2]:
                    detector.maxAnomaly = detectItem[2]
                    detector.save()

                if value < alert.nearCriticalTreshold:
                    cLevel = 0
                if value >= alert.nearCriticalTreshold and value < alert.criticalTreshold:
                    cLevel = 1                    
                if value >= alert.criticalTreshold:
                    cLevel = 2
                
                newAlertType = -1
                if cLevel == 2 and pLevel != cLevel:
                    newAlertType = ALERT_TYPE_CRITIAL
                if cLevel == 1 and pLevel == 0:
                    newAlertType = ALERT_TYPE_NEAR_CRITIAL
                if cLevel == 0 and pLevel != cLevel:
                    newAlertType = ALERT_TYPE_NORMAL
                
                if newAlertType != -1:
                    print("anomaly value:", detectItem[2], value)
                    newAlert = ModelAlertHistory(name=alert.name, alert=alert, detector=detector, description=alert.description,
                                processName=alert.getDetector().getProcess().name, detectorName=alert.getDetector().name,
                                anomalyValue=value, alertType=newAlertType, alertAt=at )
                    newAlert.save()
                    alertHistorys.append(newAlert)

                pLevel = cLevel
        # Duration Detection
        if alert.duration > 0:
            pLevel = 0; cLevel = 0; pDuration = 0; pDetectItem = None
            for detectItem in detectResult:
                at = detectItem[1]; value = detectItem[2]

                if detector.maxAnomaly < detectItem[2]:
                    detector.maxAnomaly = detectItem[2]
                    detector.save()

                if value < alert.nearCriticalTreshold:
                    cLevel = 0
                if value >= alert.nearCriticalTreshold and value < alert.criticalTreshold:
                    cLevel = 1
                if value >= alert.criticalTreshold:
                    cLevel = 2
                
                newAlertType = -1
                if cLevel == 2 and pLevel != cLevel and pDuration >= alert.duration:
                    newAlertType = ALERT_TYPE_CRITIAL
                if cLevel == 1 and pLevel == 0 and pDuration >= alert.duration:
                    newAlertType = ALERT_TYPE_NEAR_CRITIAL
                if cLevel == 0 and pLevel != cLevel and pDuration >= alert.duration:
                    newAlertType = ALERT_TYPE_NORMAL
                
                if newAlertType != -1:
                    newAlert = ModelAlertHistory(name=alert.name, alert=alert, detector=detector, description=alert.description,
                                processName=alert.getDetector().getProcess().name, detectorName=alert.getDetector().name,
                                anomalyValue=value, alertType=newAlertType, alertAt=at )
                    newAlert.save()
                    alertHistorys.append(newAlert)

                if pLevel == cLevel and pDetectItem != None:
                    pDuration = pDuration + datetime.strptime(pDetectItem[2], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp() - datetime.strptime(at, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                else:
                    pDuration = 0
                pLevel = cLevel; pDetectItem = detectItem
    
        if len(alertHistorys) > 0:
            print("New alerts in", detector.pk, " count:", len(alertHistorys))
            
            history_json = [ob.as_json() for ob in alertHistorys]

            boradcast(json.dumps({
            "type": SC_NEW_ALERT,
            "detectorId": detector.id, 
            "alerts": json.dumps(history_json)}))