from django.db import models

# Create your models here.
class ModelDatasource(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    token = models.CharField(max_length=250)
    org = models.CharField(max_length=250)
    bucket = models.CharField(max_length=250)

    class Meta:
        db_table = "tbl_datasource"

# python manage.py migrate --fake APPNAME zero
# python manage.py migrate APPNAME