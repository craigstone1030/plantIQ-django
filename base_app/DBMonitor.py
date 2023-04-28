from apscheduler.schedulers.background import BackgroundScheduler
from .models import *
from .influxDB import *
from .EchoServer import *
from django.conf import settings

metricList = []
update_callcnt = 0

def indexOfMetric( dsId, metricName ):
    i = 0
    for metric in metricList:
        if metric["dsId"] == dsId and metric["metric"] == metricName:
            return i
        i = i + 1
    return -1

def startScheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run, 'interval', seconds=settings.UPDATE_INTERVAL)
    scheduler.add_job(socket_handler, 'interval', seconds=1)
    scheduler.start()    

def socket_handler():
    websocketServer.handle_request()

def run():
    global update_callcnt
    update_callcnt = update_callcnt + 1
    print("==============", update_callcnt, "================")
    global metricList

    # Update datasource
    datasources = ModelDatasource.objects.all()
    for datasource in datasources:
        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        ret, metrics = getAllMeasurements(influxHandle, datasource.bucket)
        for metricName in metrics:
            lastUpdate = 'None'
            indexOf = indexOfMetric(datasource.pk, metricName)
            if indexOf > -1:
                lastUpdate = metricList[indexOf]["lastUpdate"]
                metricList.remove(metricList[indexOf])
            ret, curLastUpdate = isUpdateAvailable(influxHandle, datasource.bucket, metricName, lastUpdate)
            metricList.append( { "dsId": datasource.pk, "metric": metricName, "lastUpdate": curLastUpdate, "prevLastUpdate": lastUpdate } )
            # print( datasource.pk, metricName, lastUpdate, curLastUpdate, len(metricList) )
        influxHandle.close(); del influxHandle
    
    # 
    detectors = ModelDetector.objects.all()
    for detector in detectors:
        datasource = detector.getDatasource()
        if datasource == None: continue

        metrics = detector.getMetricList()
        startUpdatedAt = None; stopUpdatedAt = None

        for metric in metrics:
            indexOf = indexOfMetric(datasource.pk, metric)
            if indexOf == -1:
                continue

            if startUpdatedAt == None or startUpdatedAt > metricList[indexOf]["prevLastUpdate"]:
                startUpdatedAt = metricList[indexOf]["prevLastUpdate"]
            if stopUpdatedAt == None or stopUpdatedAt > metricList[indexOf]["lastUpdate"]:
                stopUpdatedAt = metricList[indexOf]["lastUpdate"]
        
        # print( startUpdatedAt, stopUpdatedAt )
        if pd.isnull(startUpdatedAt) or pd.isnull(stopUpdatedAt):
            continue

        if startUpdatedAt >= stopUpdatedAt:
            continue

        print(f"Update need! {detector.pk} {startUpdatedAt} ~ {stopUpdatedAt}")

        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        updateDetection(influxHandle, datasource.bucket, datasource.org, detector.exportCode, metrics, startUpdatedAt, stopUpdatedAt)
        influxHandle.close(); del influxHandle

        # print(result)

        boradcast(json.dumps({
            "type": "DETECTOR_UPDATED",
            "detectorId": detector.pk,
            "startAt": startUpdatedAt,
            "stopAt": stopUpdatedAt}))