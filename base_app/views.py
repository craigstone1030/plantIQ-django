from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .influxDB import *
import django.core.serializers
from django.db.models.lookups import *

######### LOGIN PAGE #########
@csrf_exempt
def login(request) :
    email = request.GET.get('email')
    password = request.GET.get('password')

    #   if the user enters an email address then we retrieve the username of the user
    try : 
        email = ModelUser.objects.get(email=email).username
    except : 
        return JsonResponse({'status': 'error', 'data': 'Does not exist!'})

    user = authenticate(request, email=email, password = password)

    if user is None : 
        JsonResponse({'status': 'error', 'data': 'Not authorized!'})
    else :
        request.session['user_id'] = user.pk
        JsonResponse({'status': 'success', 'data': 'authenticated successfully'})

@csrf_exempt
def logout(request):
    try:
        del request.session['user_id']
        request.session.flush()
    except KeyError:
        pass
    
def authenticate(request, email = None, password = None) : 
    try : 
        #   if the user exists
        user = ModelUser.objects.get(email = email)

        #   authenticating using password
        if user.check_password(password) : 
            return user

        #   if the password is invalid
        return None

    except: 
        return None
    
######### DATSOURCE & METRICS PAGE #########
@csrf_exempt
def createDatasource(request):
    if request.method == 'GET':
        userId = request.GET.get('userId')
        user = (ModelUser.objects.filter(id=userId) or [None])[0]
        if user == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid user id - {userId}'})
        
        newDS = ModelDatasource( name=request.GET.get('name'), description=request.GET.get('description'),
                                url=request.GET.get('url'), token=request.GET.get('token'),
                                org=request.GET.get('org'), bucket=request.GET.get('bucket'),
                                user=user )
        newDS.save()

        json = django.core.serializers.serialize('json',[newDS])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
    
@csrf_exempt
def updateDatasource(request):
    if request.method == 'GET':
        dsId = request.GET.get('id')
        curDS = (ModelDatasource.objects.filter(id=dsId) or [None])[0]
        if curDS == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid datasource id - {dsId}'})
        
        userId = request.GET.get('userId')
        user = (ModelUser.objects.filter(id=userId) or [None])[0]
        if user == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid user id - {userId}'})
        
        curDS.name = request.GET.get('name')
        curDS.description = request.GET.get('description')
        curDS.url = request.GET.get('url')
        curDS.token = request.GET.get('token')
        curDS.org = request.GET.get('org')
        curDS.bucket = request.GET.get('bucket')
        curDS.save()

        json = django.core.serializers.serialize('json',[curDS])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
    
@csrf_exempt
def deleteDatasource(request):
    if request.method == 'GET':
        dsId = request.GET.get('id')
        curDS = (ModelDatasource.objects.filter(id=dsId) or [None])[0]
        if curDS == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid datasource id - {dsId}'})
        
        curDS.delete()

        return JsonResponse({'status': 'success', 'data': ''} )
    return JsonResponse({'status': 'error', 'data': ''} )

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
        
        influxHandle = getInfluxHandle(dataSource.url, dataSource.token, dataSource.org)
        ret, result = getAllMeasurements(influxHandle, dataSource.bucket); influxHandle.close(); del influxHandle
        return JsonResponse({'status': ret, 'data' : result})
    return JsonResponse({'status': 'error', 'data': ''} )
    
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
        
        influxHandle = getInfluxHandle(dataSource.url, dataSource.token, dataSource.org)
        ret, result = getRecords(influxHandle, dataSource.bucket, metric, startAt, stopAt); influxHandle.close(); del influxHandle

        return JsonResponse({'status': ret, 'data' : result})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadMonitorsByProcess(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")

        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {process}'})
        
        # influxHandle = getInfluxHandle(dataSource.url, dataSource.token, dataSource.org)
        # ret, result = getRecords(influxHandle, dataSource.bucket, metric, startAt, stopAt); influxHandle.close(); del influxHandle

        monitorResult = []
        detectors = ModelDetector.objects.filter(process=process)
        for detector in detectors:
            status = ALERT_TYPE_NORMAL; maxAnomaly = None
            totalAlerts = None; actualScore = None; lastUpdatedAt = None

            histories = ModelAlertHistory.objects.filter(detector=detector)
            for history in histories:
                if maxAnomaly == None: maxAnomaly = history.anomalyValue
                if maxAnomaly > history.anomalyValue: maxAnomaly = history.anomalyValue

            if len(histories) > 0:
                status = histories.last().alertType
                actualScore = histories.last().anomalyValue
                lastUpdatedAt = histories.last().alertAt

            totalAlerts = len(histories)

            monitorResult.append({'status': status, 'maxAnomaly': maxAnomaly, 'totalAlerts': totalAlerts,
                                  'actualScore': actualScore, 'lastUpdatedAt': lastUpdatedAt})
        
        return JsonResponse({'status': 'success', 'data' : monitorResult})
    return JsonResponse({'status': 'error', 'data': ''} )

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
def updateProcess(request):
    if request.method == 'GET':
        processId = request.GET.get('id')
        curProcess = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if curProcess == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
                
        curProcess.name = request.GET.get('name')
        curProcess.description = request.GET.get('description')
        curProcess.save()

        json = django.core.serializers.serialize('json',[curProcess])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
  
@csrf_exempt
def deleteProcess(request):
    if request.method == 'GET':
        processId = request.GET.get('id')
        curProcess = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if curProcess == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
        
        curProcess.delete()

        return JsonResponse({'status': 'success', 'data': ''} )
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
    return JsonResponse({'status': 'error', 'data': ''} )
    
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
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def setProcessStatus(request):
    if request.method == 'GET':
        processId = request.GET.get("processId")
        status = request.GET.get("status")
        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid process id - {processId}'})
        
        process.status = status
        detectors = ModelDetector.objects.filter(process=process)
        for detector in detectors:
            detector.status = status
            detector.save()

            alerts = ModelAlert.objects.filter(detector=detector)
            for alert in alerts:
                alert.status = status
                alert.save()

        process.save()
        
        json = django.core.serializers.serialize('json',[process])
        json = json.strip('[]')
        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

######### DETECTOR PAGE #########
@csrf_exempt
def createDetector(request):
    if request.method == 'GET':
        processId = request.GET.get('processId')
        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})

        newDetector = ModelDetector( name=request.GET.get('name'), description=request.GET.get('description'),
                             process=process, metricList=request.GET.get('metricNames'), exportCode=uuid.uuid1() )
        if newDetector.validateName() == False :
            return JsonResponse({'status': 'error', 'error': 'Please input another name.'})
        
        newDetector.save()
        
        json = django.core.serializers.serialize('json',[newDetector])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )
 
@csrf_exempt
def updateDetector(request):
    if request.method == 'GET':
        detectorId = request.GET.get('id')
        curDetector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if curDetector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {variable}'})
        
        processId = request.GET.get('processId')
        process = (ModelProcess.objects.filter(id=processId) or [None])[0]
        if process == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid process id - {processId}'})
                
        curDetector.name = request.GET.get('name')
        curDetector.description = request.GET.get('description')
        curDetector.process = process
        curDetector.metricList = request.GET.get('metricNames')

        if curDetector.validateName() == False :
            return JsonResponse({'status': 'error', 'error': 'Please input another name.'})
        
        curDetector.save()

        json = django.core.serializers.serialize('json',[curDetector])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data': json} )
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def deleteDetector(request):
    if request.method == 'GET':
        detectorId = request.GET.get('id')
        curDetector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if curDetector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})
        
        curDetector.delete()

        return JsonResponse({'status': 'success', 'data': ''} )
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
        
        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        ret, result = getDetectorRecords(influxHandle, datasource.bucket, detector.exportCode, startAt, stopAt); influxHandle.close(); del influxHandle

        return JsonResponse({'status': ret, 'data' : result})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def setDetectorStatus(request):
    if request.method == 'GET':
        detectorId = request.GET.get("id")
        status = request.GET.get("status")
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid detector id - {detectorId}'})
        
        detector.status = status
        detector.save()

        alerts = ModelAlert.objects.filter(detector=detector)
        for alert in alerts:
            alert.status = status
            alert.save()

        json = django.core.serializers.serialize('json',[detector])
        json = json.strip('[]')

        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadGraphData(request):
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
        
        result = map()

        influxHandle = getInfluxHandle(datasource.url, datasource.token, datasource.org)
        ret, records = getDetectorRecords(influxHandle, datasource.bucket, detector.exportCode, startAt, stopAt); influxHandle.close(); del influxHandle

        alert = (ModelAlert.objects.filter(detector=detector) or [None])[0]; history = []
        if startAt != None and stopAt != None : history = ModelAlertHistory.objects.filter(detector=detector, alertAt__gte=startAt, endAt__lte=stopAt )
        elif startAt != None and stopAt == None : history = ModelAlertHistory.objects.filter(detector=detector, alertAt__gte=startAt )
        elif startAt != None and stopAt == None : history = ModelAlertHistory.objects.filter(detector=detector, alertAt__lte=stopAt )
        else: history = stopAt.objects.filter(detector=detector)

        result = { 'alert': alert, 'histories': history, 'records': records}

        return JsonResponse({'status': ret, 'data' : result})
    return JsonResponse({'status': 'error', 'data': ''} )

######### ALERT PAGE #########

@csrf_exempt
def createAlert(request):
    if request.method == 'GET':
        detectorId = request.GET.get("detectorId")
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid detector id - {detectorId}'})
        
        alert = ModelAlert(name=request.GET.get('name'), description=request.GET.get('description'),
                           nearCriticalTreshold=request.GET.get('treshold1'), detector=detector,
                        criticalTreshold=request.GET.get('treshold2'), duration=request.GET.get('duration'))
        alert.save()

        json = django.core.serializers.serialize('json',[alert])
        json = json.strip('[]')
        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def updateAlert(request):
    if request.method == 'GET':
        alertId = request.GET.get("id")
        curAlert = (ModelAlert.objects.filter(id=alertId) or [None])[0]
        if curAlert == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid alert id - {alertId}'})
        
        curAlert.name = request.GET.get('name')
        curAlert.description = request.GET.get('description')
        curAlert.nearCriticalTreshold = request.GET.get('treshold1')
        curAlert.criticalTreshold = request.GET.get('treshold2')
        curAlert.duration = request.GET.get('duration')
        curAlert.save()

        json = django.core.serializers.serialize('json',[curAlert])
        json = json.strip('[]')
        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def deleteAlert(request):
    if request.method == 'GET':
        alertId = request.GET.get('id')
        curAlert = (ModelAlert.objects.filter(id=alertId) or [None])[0]
        if curAlert == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid alert id - {alertId}'})

        curAlert.delete()

        return JsonResponse({'status': 'success', 'data': ''} )
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadAlertsByDetector(request):
    if request.method == 'GET':
        detectorId = request.GET.get('detectorId')
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})

        alerts = ModelAlert.objects.filter(detector=detector)
        json = django.core.serializers.serialize('json', alerts)
        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def setAlertStatus(request):
    if request.method == 'GET':
        alertId = request.GET.get("id")
        status = request.GET.get("status")
        curAlert = (ModelAlert.objects.filter(id=alertId) or [None])[0]
        if curAlert == None:
            return JsonResponse({'status': 'error', 'error': f'Invalid alert id - {alertId}'})
        
        curAlert.status = status
        curAlert.save()
        
        json = django.core.serializers.serialize('json',[curAlert])
        json = json.strip('[]')
        return JsonResponse({'status': 'success', 'data' : json})
    return JsonResponse({'status': 'error', 'data': ''} )

@csrf_exempt
def loadAlertHistoryByDetector(request):
    if request.method == 'GET':

        detectorId = request.GET.get('detectorId')
        detector = (ModelDetector.objects.filter(id=detectorId) or [None])[0]
        if detector == None:
            return JsonResponse({'status': 'error', 'error': 'Invalid detector id - {detectorId}'})
        
        startAt = request.GET.get('startAt')
        endAt = request.GET.get('endAt')  
        
        history = []
        if startAt != None and endAt != None : history = ModelAlertHistory.objects.filter(detector=detector, startAt__gte=startAt, endAt__lte=endAt )
        elif startAt != None and endAt == None : history = ModelAlertHistory.objects.filter(detector=detector, startAt__gte=startAt )
        elif startAt != None and endAt == None : history = ModelAlertHistory.objects.filter(detector=detector, endAt__lte=endAt )
        else: history = ModelAlertHistory.objects.filter(detector=detector)

        json = django.core.serializers.serialize('json', history)
        return JsonResponse({'status': 'success', 'data' : json})
        
    return JsonResponse({'status': 'error', 'data': ''} )