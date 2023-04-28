"""plantIQ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from base_app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    # datasource
    path('api/datasource/create', createDatasource), # create new datasource
    path('api/datasource/all', loadDatasources), # load all datasource
    path('api/datasource/update', updateDatasource), # update datasource
    path('api/datasource/delete', deleteDatasource), # delete datasource

    # metrics
    path('api/metric/all', loadMetrics), # load all metrics by one datasource
    path('api/metric/load', loadRecords), # load records by one metric

    # processes
    path('api/process/create', createProcess), # create process
    path('api/process/update', updateProcess), # update process
    path('api/process/delete', deleteProcess), # delete process
    path('api/process/all', loadProcesses), # load all process
    path('api/process/metrics', loadMetricsByProcess), # load all process
    path('api/process/detectors', loadDetectorsByProcess), # load all process

    # detectors
    path('api/detector/create', createDetector), # create detector
    path('api/detector/update', updateDetector), # update process
    path('api/detector/delete', deleteDetector), # delete process
    path('api/detector/load', loadDetectors), # load all process
    path('api/detector/process', loadProcessByDetector), # load all process
    path('api/detector/metrics', loadMetricsByDetector), # load all metrics    
    path('api/detector/records', loadDetectorRecords), # load all records  
]