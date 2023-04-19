from django.db import models
import json

# Create your models here.
class ModelUser(models.Model):
    firName = models.CharField(max_length=250)
    lastName = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    mobileNumber = models.CharField(max_length=250)
    company = models.CharField(max_length=250)

    class Meta:
        db_table = "tbl_user"   

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
    status = models.BooleanField(default=True)
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
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_detector"

# python manage.py makemigrations
# python manage.py migrate --fake base_app zero
# python manage.py migrate base_app