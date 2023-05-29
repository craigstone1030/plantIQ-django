from apscheduler.schedulers.background import BackgroundScheduler
from .models import *
from .influxDB import *
from .EchoServer import *
from django.conf import settings
import django.core.serializers
import threading
import time

class MeasurementThread(threading.Thread):
    # overriding constructor
    def __init__(self, datasourceId):
    # calling parent class constructor
        threading.Thread.__init__(self)
        self.datasourceId = datasourceId
        self.metricList = []
        self._stop_event = threading.Event()  # Event to signal the thread to stop
        self.log = True

    def indexOfMetric( self, dsId, metricName ):
        i = 0
        for metric in self.metricList:
            if metric["dsId"] == dsId and metric["metric"] == metricName:
                return i
            i = i + 1
        return -1    
    
    # define your own run method
    def run(self):
        if self.log == True : print(f"Start metric thread({self.datasourceId})")

        call_count = 0

        while not self._stop_event.is_set():
            if call_count > 0:
                time.sleep(settings.UPDATE_DATASOURCE_INTERVAL)
            
            call_count = call_count + 1
            if self.log == True : print(f"Running metric thread({self.datasourceId}), {call_count}")

            datasource = (ModelDatasource.objects.filter(pk=self.datasourceId, deleted=0) or [None])[0]
            if datasource == None:
                if self.log == True : print(f"metric thread({self.datasourceId} was ignored by none datasource infomation)")
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

                if lastUpdate == 'None' or curLastUpdate == 'None':
                    continue

                if ret == True and datetime.strptime(curLastUpdate, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp() > datetime.strptime(lastUpdate, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp():
                    if self.log == True : print(f"Metrics updated! {datasource.pk}-{metricName} {lastUpdate} ~ {curLastUpdate}")
                    
                    datasource.lastUpdate = curLastUpdate
                    datasource.save()

                    boradcast(json.dumps({
                        "type": SC_METRIC_UPDATED,
                        "datasourceId": self.datasourceId,
                        "metric": metricName,
                        "startAt": lastUpdate,
                        "stopAt": curLastUpdate}))             

            influxHandle.close(); del influxHandle

    def stop(self):
        self._stop_event.set()  # Set the stop event to exit the loop