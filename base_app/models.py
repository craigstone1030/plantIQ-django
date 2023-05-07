from django.db import models
import json
import uuid
from datetime import datetime, timedelta

# ALERT TYPE
ALERT_TYPE_NEAR_CRITIAL = 1
ALERT_TYPE_CRITIAL = 2
ALERT_TYPE_NORMAL = 3

# PACKET TYPE
SC_DETECTOR_UPDATED = "DETECTOR_UPDATED"
SC_NEW_ALERT = "NEW_ALERTS"

# Create your models here.
class ModelUser(models.Model):
    firName = models.CharField(max_length=250)
    lastName = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    mobileNumber = models.CharField(max_length=250)
    company = models.CharField(max_length=250)
    password = models.CharField(max_length=250)

    class Meta:
        db_table = "tbl_user"   

    def check_password(self, password):
        return self.password == password

class ModelDatasource(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    token = models.CharField(max_length=250)
    org = models.CharField(max_length=250)
    bucket = models.CharField(max_length=250)
    user = models.ForeignKey(ModelUser, default=-1, on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_datasource"

class ModelProcess(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    datasource = models.ForeignKey(ModelDatasource, default=-1, on_delete=models.CASCADE)
    metricList = models.TextField(default='') # must string array, then each items are holded by " not '
    status = models.IntegerField(default=1)
# 
    def setMetricNames(self, jsonMetricNames):
        self.metricList = jsonMetricNames

    def getMetricList(self):
        return json.loads(self.metricList)

    class Meta:
        db_table = "tbl_process"

class ModelDetector(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    process = models.ForeignKey(ModelProcess,default=-1,on_delete=models.CASCADE)
    metricList = models.TextField(default='')
    exportCode = models.CharField(default='', max_length=250)
    lastUpdate = models.CharField(default='None', max_length=250)
    status = models.IntegerField(default=1)

    def is_valid_uuid(self, value):
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False
    
    def validateName(self):
        return self.is_valid_uuid(self.name) == False

    def getMetricList(self):
        return json.loads(self.metricList)
    
    def getProcess(self):
        process = (ModelProcess.objects.filter(id=self.process_id) or [None])[0]
        return process
    
    def getDatasource(self):
        process = self.getProcess()
        if process == None:
            return None

        datasource = (ModelDatasource.objects.filter(id=process.datasource_id) or [None])[0]
        return datasource
    
    class Meta:
        db_table = "tbl_detector"

class ModelAlert(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    detector = models.ForeignKey(ModelDetector,default=-1,on_delete=models.CASCADE)
    nearCriticalTreshold = models.FloatField(default=None)
    criticalTreshold = models.FloatField(default=None)
    duration = models.IntegerField(default=0) # mseconds
    status = models.IntegerField(default=1)

    def getDetector(self):
        detector = (ModelDetector.objects.filter(id=self.detector_id) or [None])[0]
        return detector
    
    class Meta:
        db_table = "tbl_alert"


class ModelAlertHistory(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    processName = models.CharField(max_length=250)
    detectorName = models.CharField(max_length=250)
    anomalyValue = models.FloatField(default=None)
    alertType = models.IntegerField(default=None) # 1: near-critical 2: critical 3: to be normal
    alertAt = models.DateTimeField(default=datetime.utcnow())

    class Meta:
        db_table = "tbl_alerthistory"




# python manage.py makemigrations
# python manage.py migrate --fake base_app zero
# python manage.py migrate base_app