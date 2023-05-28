from apscheduler.schedulers.background import BackgroundScheduler
from .models import *
from .influxDB import *
from .EchoServer import *
from django.conf import settings
import django.core.serializers
import threading
import time

class DetectorThread(threading.Thread):
    # overriding constructor
    def __init__(self, detectorId):
    # calling parent class constructor
        threading.Thread.__init__(self)
        self.detectorId = detectorId
        self.metricList = []
        self._stop_event = threading.Event()  # Event to signal the thread to stop

    def indexOfMetric( self, dsId, metricName ):
        i = 0
        for metric in self.metricList:
            if metric["dsId"] == dsId and metric["metric"] == metricName:
                return i
            i = i + 1
        return -1    
    
    # define your own run method
    def run(self):
        print(f"Start detecting thread({self.detectorId})")

        call_count = 0

        while not self._stop_event.is_set():
            if call_count > 0:
                time.sleep(settings.UPDATE_INTERVAL)
            
            call_count = call_count + 1
            print(f"Running Detect thread({self.detectorId}), {call_count}")

            detector = (ModelDetector.objects.filter(pk=self.detectorId) or [None])[0]
            if detector == None:
                print(f"Detect thread({self.detectorId} was ignored by none detector infomation)")
                continue
            if detector.status == 0:
                print(f"Disabled detecting thread({self.detectorId})")
                continue

            datasource = detector.getDatasource()
            if datasource == None:
                print(f"Detect thread({self.detectorId} was ignored by none datasource infomation)")
                continue
            
            influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
            ret, metrics = getAllMeasurements(influxHandle, datasource.bucket)

            for metricName in metrics:
                lastUpdate = 'None'; initialAt = 'None'
                indexOf = self.indexOfMetric(datasource.pk, metricName)
                if indexOf > -1:
                    lastUpdate = self.metricList[indexOf]["lastUpdate"]
                    self.metricList.remove(self.metricList[indexOf])

                initialAt = getInitialAt(influxHandle, datasource.bucket, metricName)
                ret, curLastUpdate = isUpdateAvailable(influxHandle, datasource.bucket, metricName, lastUpdate)
                self.metricList.append( { "dsId": datasource.pk, "metric": metricName, "initialAt": initialAt,"lastUpdate": curLastUpdate, "prevLastUpdate": lastUpdate } )

            metrics = detector.getMetricList()
            startUpdatedAt = None; stopUpdatedAt = None

            for metric in metrics:
                indexOf = self.indexOfMetric(datasource.pk, metric)
                if indexOf == -1:
                    continue

                if detector.lastUpdate == 'None':
                    if startUpdatedAt == None or startUpdatedAt > self.metricList[indexOf]["initialAt"]:
                        startUpdatedAt = self.metricList[indexOf]["initialAt"]
                else:
                    if startUpdatedAt == None or startUpdatedAt > self.metricList[indexOf]["prevLastUpdate"]:
                        startUpdatedAt = self.metricList[indexOf]["prevLastUpdate"]

                if stopUpdatedAt == None or stopUpdatedAt > self.metricList[indexOf]["lastUpdate"]:
                    stopUpdatedAt = self.metricList[indexOf]["lastUpdate"]
            
            # print( startUpdatedAt, stopUpdatedAt )

            if detector.lastUpdate != 'None':
                if pd.isnull(startUpdatedAt) or pd.isnull(stopUpdatedAt):
                    continue

                if startUpdatedAt >= stopUpdatedAt:
                    continue

            print(f"Update need! {detector.pk} {startUpdatedAt} ~ {stopUpdatedAt}")

            # influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
            detectResult = updateDetection(influxHandle, datasource.bucket, datasource.org, detector.exportCode, metrics, startUpdatedAt, stopUpdatedAt)

            print(f"Detecting anomaly {detector.pk}")
            
            self.detectAnomaly( detector, detectResult )

            # detector.lastScore = detectResult[len(detectResult) - 1][2] # [field, time, value] : detectResult
            detector.lastUpdate = stopUpdatedAt
            detector.save()

            boradcast(json.dumps({
                "type": SC_DETECTOR_UPDATED,
                "detectorId": detector.pk,
                "startAt": startUpdatedAt,
                "stopAt": stopUpdatedAt}))


            influxHandle.close(); del influxHandle

    def stop(self):
        self._stop_event.set()  # Set the stop event to exit the loop

    # detectResult: should be sorted by datetime
    def detectAnomaly(self, detector, detectResult): 
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