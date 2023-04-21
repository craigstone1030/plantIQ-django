from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .influxDB import *
import django.core.serializers

######### DATSOURCE & METRICS PAGE #########
@csrf_exempt
def createDatasource(request):
    if request.method == 'POST':
        userId = request.POST.get('userId')
        user = (ModelUser.objects.filter(id=userId) or [None])[0]
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

        dataSource = (ModelDatasource.objects.filter(id=dsId) or [None])[0]
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getAllMeasurements(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket)
        print(result)
        return JsonResponse({'status': ret, 'data' : result})
    
@csrf_exempt
def loadRecords(request):
    if request.method == 'GET':
        dsId = request.GET.get("dsId")
        metric = request.GET.get("metric")
        startAt = request.GET.get("startAt")
        stopAt = request.GET.get("stopAt")

        dataSource = (ModelDatasource.objects.filter(id=dsId) or [None])[0]
        if dataSource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        ret, result = getRecords(getInfluxHandle(dataSource.url, dataSource.token, dataSource.org), dataSource.bucket, metric, startAt, stopAt)

        return JsonResponse({'status': ret, 'data' : result})
    
######### METRICS PAGE #########
@csrf_exempt
def createProcess(request):
    if request.method == 'GET':
        dsId = request.GET.get('dsId')
        datasource = (ModelDatasource.objects.filter(id=dsId) or [None])[0]
        if datasource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})

        newProcess = ModelProcess( name=request.GET.get('name'), description=request.GET.get('description'),
                             datasource=datasource, metricList=request.GET.get('metricNames') )
        newProcess.save()
        
        json = django.core.serializers.serialize('json',[newProcess])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
 
@csrf_exempt
def loadProcesses(request):
    processes = ModelProcess.objects.all()
    json = django.core.serializers.serialize('json',processes)
    return JsonResponse({'status': 'success', 'data': json})
  
@csrf_exempt
def loadMetricsByProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")

        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        
        return JsonResponse({'status': 'success', 'data' : process.getMetricList()})
    
@csrf_exempt
def loadDetectorsByProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")
        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        
        detectors = ModelDetector.objects.filter(process=process)
        json = django.core.serializers.serialize('json',detectors)
        return JsonResponse({'status': 'success', 'data' : json})

######### DETECTOR PAGE #########
@csrf_exempt
def createDetector(request):
    if request.method == 'GET':
        processId = request.GET.get('processId')
        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})

        newDetector = ModelDetector( name=request.GET.get('name'), description=request.GET.get('description'),
                             process=process, metricList=request.GET.get('metricNames') )
        newDetector.save()
        
        json = django.core.serializers.serialize('json',[newDetector])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
 
@csrf_exempt
def loadDetectors(request):
    detectors = ModelDetector.objects.all()
    json = django.core.serializers.serialize('json',detectors)
    return JsonResponse({'status': 'success', 'data': json})

@csrf_exempt
def loadProcessByDetector(request):
    if request.method == 'GET':
        detectorId = request.GET.get('detectorId')
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})

        process = (ModelProcess.objects.filter(id=detector.process_id) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {process_id.process} at detector id - {detectorId}'})
        
        json = django.core.serializers.serialize('json', [process])
        json = json.strip('[]')
        return JsonResponse({'status': 'success', 'data': json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadMetricsByDetector(request):
    if request.method == 'GET':
        detectorId = request.GET.get('detectorId')
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})

        process = (ModelProcess.objects.filter(id=detector.process_id) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {process_id.process} at detector id - {detectorId}'})
        return JsonResponse({'status': 'success', 'data' : detector.getMetricList()})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadDetectorRecords(request):
    if request.method == 'GET':
        detectorId = request.GET.get("detectorId")
        startAt = request.GET.get("startAt")
        stopAt = request.GET.get("stopAt")

        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})
        
        process = (ModelProcess.objects.filter(id=detector.process_id) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {detector.process_id}'})

        datasource = (ModelDatasource.objects.filter(id=process.datasource_id) or [None])[0]
        if datasource == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {process.datasource_id}'})             
        
        ret, result = getDetectorRecords(getInfluxHandle(datasource.url, datasource.token, datasource.org), datasource.bucket, detector.getMetricList(), startAt, stopAt)

        return JsonResponse({'status': ret, 'data' : result})