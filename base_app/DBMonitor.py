from apscheduler.schedulers.background import BackgroundScheduler
from .models import *
from .influxDB import *

lastUpdatedAt = 'None'
influxHandle = getInfluxHandle("https://us-east-1-1.aws.cloud2.influxdata.com", "8oDOTz3lMBYFuMVeTI7OQYRgHD_GsNbDKVtnHnHBpI29M1mueK8VvkordimEZuRWv3pzqJZ1fjwuu6DWx8Z9XQ==", "Vostok Games")

metricList = []

def indexOfMetric( dsId, metricName ):
    i = 0
    for metric in metricList:
        if metric["dsId"] == dsId and metric["metric"] == metricName:
            return i
        i = i + 1
    return -1

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update, 'interval', seconds=10)
    scheduler.start()

def update():

    global metricList

    datasources = ModelDatasource.objects.all()
    for datasource in datasources:
        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        metrics = getAllMeasurements(influxHandle, datasource.bucket)
        for metricName in metrics:
            lastUpdate = 'None'
            indexOf = indexOfMetric(datasource.pk, metricName)
            if indexOf > 0:
                lastUpdate = metricList[indexOf]["lastUpdate"]
                metricList.remove(indexOf)

            lastUpdate = isUpdateAvailable(influxHandle, datasource.bucket, metric, None)
            metricList.append( { "dsId": datasource.pk, "metric": metric, "lastUpdate": lastUpdate } )

    global lastUpdatedAt
    ret, lastUpdatedAt = isUpdateAvailable(influxHandle, "data1", "SMART_3D_L.GLASS_A_ORI", lastUpdatedAt)
    # print( ret, lastUpdatedAt )