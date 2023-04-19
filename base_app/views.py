from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .influxDB import getInfluxHandle, getAllMeasurements, getRecords
import django.core.serializers

######### DATSOURCE & METRICS PAGE #########
@csrf_exempt
def createDatasource(request):
    if request.method == 'POST':
        userId = request.POST.get('userId')
        user = ModelUser.objects.get(id=userId) or None
        if user == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid user id - {userId}'})
        
        newDS = ModelDatasource( name=request.POST.get('name'), description=request.POST.get('description'),
                                url=request.POST.get('url'), token=request.POST.get('token'),
                                org=request.POST.get('org'), bucket=request.POST.get('bucket'),
                                user=user )
        newDS.save()

        json = django.core.serializers.serialize('json',[newDS])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    
@csrf_exempt
def loadDatasources(request):
    connections = ModelDatasource.objects.all()
    json = django.core.serializers.serialize('json',connections)
    return JsonResponse({'status': 'success', 'data': json})
    
@csrf_exempt
def loadMetrics(request):
    if request.method == 'GET':
        dsId = request.GET.get("dsId")

        dataSource = ModelDatasource.objects.get(id=dsId) or None
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getAllMeasurements(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket)

        return JsonResponse({'status': ret, 'data' : result})
    
@csrf_exempt
def loadRecords(request):
    if request.method == 'GET':
        dsId = request.GET.get("dsId")
        metric = request.GET.get("metric")
        startAt = request.GET.get("startAt")
        stopAt = request.GET.get("stopAt")

        dataSource = ModelDatasource.objects.get(id=dsId) or None
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getRecords(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket, metric, startAt, stopAt)

        return JsonResponse({'status': ret, 'data' : result})
    
######### METRICS PAGE #########
@csrf_exempt
def createProcess(request):
    if request.method == 'POST':
        dsId = request.POST.get('dsId')
        datasource = ModelDatasource.objects.get(id=dsId) or None
        if datasource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
                        
        newProcess = ModelProcess( name=request.POST.get('name'), description=request.POST.get('description'),
                             datasource=datasource, metricList=request.POST.get('metricNames') )
        newProcess.save()

        print(newProcess.getMetricList())

        json = django.core.serializers.serialize('json',[newProcess])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
 
@csrf_exempt
def loadProcesses(request):
    processes = ModelProcess.objects.all()
    json = django.core.serializers.serialize('json',processes)
    return JsonResponse({'status': 'success', 'data': json})
  
@csrf_exempt
def loadMetricsByProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")

        process = ModelProcess.objects.get(id=processId) or None
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        
        return JsonResponse({'status': 'success', 'data' : process.getMetricList()})
    
@csrf_exempt
def loadDetectorsByProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")
        process = ModelProcess.objects.get(id=processId) or None
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        
        detectors = ModelDetector.objects.filter(process=process)
        return JsonResponse({'status': 'success', 'data' : detectors})
    
@csrf_exempt
def deleteProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")
        process = ModelProcess.objects.get(id=processId) or None
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        process.delete()
        return JsonResponse({'status': 'success', 'data' : ''})

