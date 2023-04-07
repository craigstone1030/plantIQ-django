from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ModelDatasource
from .influxDB import getInfluxHandle, getAllMeasurements, getRecords
import django.core.serializers


@csrf_exempt
def createDatasource(request):
    if request.method == 'POST':
        newDS = ModelDatasource( url=request.POST.get('url'), token=request.POST.get('token'), org=request.POST.get('org'), bucket=request.POST.get('bucket'))
        newDS.save()

        json = django.core.serializers.serialize('json',[newDS])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    
@csrf_exempt
def loadDatasources(request):
    if request.method == 'POST':
        connections = ModelDatasource.objects.all()
        json = django.core.serializers.serialize('json',connections)
        return JsonResponse({'status': 'success', 'data': json})
    
@csrf_exempt
def loadMetrics(request):
    if request.method == 'POST':
        dsId = request.POST.get("dsId")
        metricName = request.POST.get("metric")

        dataSource = ModelDatasource.objects.get(id=dsId) or None
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getAllMeasurements(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket)

        return JsonResponse({'status': ret, 'data' : result})
    
@csrf_exempt
def loadRecords(request):
    if request.method == 'POST':
        dsId = request.POST.get("dsId")
        metric = request.POST.get("metric")

        dataSource = ModelDatasource.objects.get(id=dsId) or None
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getRecords(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket, metric)

        return JsonResponse({'status': ret, 'data' : result})

