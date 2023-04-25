import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from django.conf import settings
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

#token = os.environ.get("INFLUXDB_TOKEN")

# token = "Hhv9w-E6ZSlsFOFFnRoG0aja43-Zxis3LBBTfbKLrhzzigTo_KhvLRbRWCvmFLDgO5vziIO5LNIa0ipdBcIDPA=="
# org = "AI"
# url = "https://us-east-1-1.aws.cloud2.influxdata.com"

# client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

# bucket="data2"

def getInfluxHandle(url, token, org):
    return influxdb_client.InfluxDBClient(url=url, token=token, org=org)

def getAllMeasurements(influxClient, bucket):
    client = influxClient
    try:
        query = f"""
        import \"influxdata/influxdb/schema\"
        schema.measurements(bucket: \"{bucket}\")
        """

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)
        measurements = [row.values["_value"] for table in result for row in table]

        return 'success', measurements
    
    except Exception as e:
        return 'error', e

def getRecords(influxClient, bucket, measurement, startAt, stopAt):

    client = influxClient
    try:
        query = f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt}) |> filter(fn: (r) => r._measurement == "{measurement}")'
        if startAt == None and stopAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: -365d) |> filter(fn: (r) => r._measurement == "{measurement}")'
        elif stopAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: {startAt}) |> filter(fn: (r) => r._measurement == "{measurement}")'
        elif startAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: -365d, stop:{stopAt}) |> filter(fn: (r) => r._measurement == "{measurement}")'

        print(query)

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)
        # system_stats  = result.query_data_frame()

        # print(system_stats)

        datas = [ ]
        for table in result:
            for row in table.records:
                datas.append( [ row.values["_field"], row.values["_time"], row.values["_value"] ] )

        return 'success', datas
    except Exception as e:
        return 'error', e

# nat = np.datetime64('NaT')

# def nat_check(nat):
#     return nat == np.datetime64('NaT')
    
def getDetectorRecords(influxClient, bucket, measurementList, startAt, stopAt):

    client = influxClient
    query_api = client.query_api()

    data = {}; i = 0
    for measurement in measurementList:
        query = ''
        if startAt == None and stopAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: -365d)'
        elif stopAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: {startAt})'
        elif startAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: -365d, stop:{stopAt})'
        else:
            query += f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt})'

        query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
        query += f' |> drop(columns:["_start", "_stop", "_measurement", "result", "table"])'
        query += f' |> yield(name: "result") \n'
        data_frame = query_api.query_data_frame(org=settings.INFLUX_ORG, query=query)
        data["time"] = data_frame['_time']
        data[f"value{i}"] = data_frame['_value']
        i = i + 1

    detectorFrame = pd.DataFrame(data)
    detectorFrame = detectorFrame.loc[pd.isnull(detectorFrame["time"]) == False]

    variable_columns = []; i = 0
    for metric in measurementList:
        variable_columns.append(f"value{i}"); i = i + 1
        

    model=IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.1),max_features=1.0)        
    model.fit(detectorFrame[variable_columns])

    detectorFrame['scores']=model.decision_function(detectorFrame[variable_columns])
    detectorFrame['anomaly']=model.predict(detectorFrame[variable_columns])

    # print( detectorFrame )

    results = []
    for ind in data_frame.index:
        results.append( ["value", detectorFrame['time'][ind], detectorFrame['scores'][ind]] )

    print( results )
    
    return 'success', results

def isUpdateAvailable(influxClient, bucket, measurement, lastUpdatedAt):
    query_api = influxClient.query_api()

    query = ''
    if lastUpdatedAt == 'None':
        query = f'from(bucket: "{bucket}") |> range(start: 0, stop:{datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")})'
    else:
        query = f'from(bucket: "{bucket}") |> range(start: {lastUpdatedAt}, stop:{datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")})'
    query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
    # query += f' |> keep(columns: ["_time"])'
    query += f' |> sort(columns: ["_time"], desc: false)'
    query += f' |> last()'    

    bUpdate = False
    result = query_api.query(org=settings.INFLUX_ORG, query=query)
    if len(result) > 0:
        lastUpdatedAt = result[0].records[0]["_time"] + timedelta(seconds=1)
        lastUpdatedAt = lastUpdatedAt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        # print( "New Data", lastUpdatedAt )
        bUpdate = True
    else:
        # print( "No Data", lastUpdatedAt )
        bUpdate = False

    return bUpdate, lastUpdatedAt