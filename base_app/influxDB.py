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
import uuid
import rrcf
import warnings
from influxdb_client.client.warnings import MissingPivotFunction

#token = os.environ.get("INFLUXDB_TOKEN")

# token = "Hhv9w-E6ZSlsFOFFnRoG0aja43-Zxis3LBBTfbKLrhzzigTo_KhvLRbRWCvmFLDgO5vziIO5LNIa0ipdBcIDPA=="
# org = "AI"
# url = "https://us-east-1-1.aws.cloud2.influxdata.com"

# client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

# bucket="data2"

def getInfluxHandle(url, token, org):
    warnings.simplefilter("ignore", MissingPivotFunction)
    return influxdb_client.InfluxDBClient(url=url, token=token, org=org)

def getAllMeasurements(influxClient, bucket):

    def is_valid_uuid(value):
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False
        
    client = influxClient
    try:
        query = f"""
        import \"influxdata/influxdb/schema\"
        schema.measurements(bucket: \"{bucket}\")
        """

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)

        measurements = []
        for table in result :
            for row in table :
                if is_valid_uuid(row.values["_value"]) == False:
                    measurements.append(row.values["_value"])

        return 'success', measurements
    
    except Exception as e:
        return 'error', f'{e}'

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

        # print(query)

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)
        # system_stats  = result.query_data_frame()

        # print(system_stats)

        datas = [ ]
        for table in result:
            for row in table.records:
                try:
                    dt = datetime.strptime(row.values["_time"], "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    datas.append( [ row.values["_field"], dt, row.values["_value"] ] )
                except:
                    datas.append( [ row.values["_field"], row.values["_time"], row.values["_value"] ] )

        return 'success', datas
    except Exception as e:
        return 'error', f'{e}'

def getDetectorRecords(influxClient, bucket, detectorName, startAt, stopAt):
    client = influxClient
    try:
        query = f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt}) |> filter(fn: (r) => r._measurement == "{detectorName}")'
        if startAt == None and stopAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: -365d) |> filter(fn: (r) => r._measurement == "{detectorName}")'
        elif stopAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: {startAt}) |> filter(fn: (r) => r._measurement == "{detectorName}")'
        elif startAt == None:
            query = f'from(bucket: "{bucket}") |> range(start: -365d, stop:{stopAt}) |> filter(fn: (r) => r._measurement == "{detectorName}")'

        # print(query)

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)
        # system_stats  = result.query_data_frame()

        # print(system_stats)

        datas = [ ]
        for table in result:
            for row in table.records:

                rfc3339_string = row.values["_time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                datas.append( [ row.values["_field"], rfc3339_string, row.values["_value"] ] )

                
                

        return 'success', datas
    except Exception as e:
        return 'error', f'{e}'
    
def rrcf_detect(array, size):
    # Set tree parameters
    num_trees = 40
    shingle_size = size
    tree_size = 256

    # Create a forest of empty trees
    forest = []
    for _ in range(num_trees):
        tree = rrcf.RCTree()
        forest.append(tree)
        
    # Use the "shingle" generator to create rolling window
    points = rrcf.shingle(array, size=shingle_size)

    # Create a dict to store anomaly score of each point
    avg_codisp = {}

    # For each shingle...
    for index, point in enumerate(points):
        # For each tree in the forest...
        for tree in forest:
            # If tree is above permitted size, drop the oldest point (FIFO)
            if len(tree.leaves) > tree_size:
                tree.forget_point(index - tree_size)
            # Insert the new point into the tree
            tree.insert_point(point, index=index)
            # Compute codisp on the new point and take the average among all trees
            if not index in avg_codisp:
                avg_codisp[index] = 0
            avg_codisp[index] += tree.codisp(index) / num_trees
    return avg_codisp

def detectMetrics(influxClient, bucket, measurementList, startAt, stopAt):

    client = influxClient
    query_api = client.query_api()

    if startAt == None:
        startAt = '1970-12-31T00:00:00.000Z'
    if stopAt == None:
        stopAt = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    data = {}; i = 0
    for measurement in measurementList:
        query = ''
        if startAt == None and stopAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z)'
        elif stopAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: {startAt})'
        elif startAt == None:
            query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z, stop:{stopAt})'
        else:
            query += f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt})'

        query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
        query += f' |> drop(columns:["_start", "_stop", "_measurement", "result", "table"])'
        query += f' |> yield(name: "result") \n'
        query
        data_frame = query_api.query_data_frame(org=settings.INFLUX_ORG, query=query)
        data["time"] = data_frame['_time']
        data[f"value{i}"] = data_frame['_value']

        i = i + 1

    detectorFrame = pd.DataFrame(data)
    detectorFrame = detectorFrame.loc[pd.isnull(detectorFrame["time"]) == False]
    i = 0
    for metric in measurementList:
        detectorFrame = detectorFrame.loc[pd.isnull(detectorFrame[f"value{i}"]) == False]; i = i + 1
    # print( detectorFrame )

    variable_columns = []; rate_columns = []; i = 0
    for metric in measurementList:
        variable_columns.append(f"value{i}"); i = i + 1
        rate_columns.append( 1. / len(measurementList) )

    # print( detectorFrame )
        

    # ============== Isolation ==============
    # model=IsolationForest(n_estimators=50, max_samples='auto', contamination=float(0.1),max_features=1.0)        
    # model.fit(detectorFrame[variable_columns])

    # detectorFrame['scores']=model.decision_function(detectorFrame[variable_columns])
    # detectorFrame['anomaly']=model.predict(detectorFrame[variable_columns])

    # results = []
    # for ind in detectorFrame.index:
    #     results.append( ["value", detectorFrame['time'][ind], detectorFrame['scores'][ind]] )

    # ============== Robust ==============
    np_data = detectorFrame[variable_columns].to_numpy()
    np_data = np.average(np_data, axis=1, weights=rate_columns)

    # Generate data
    try:
        anomaly_results = rrcf_detect(np_data.tolist(), 4)
    except Exception as e:
        return 'error', []
    
    distance = datetime.strptime(stopAt, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp() - datetime.strptime(startAt, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
    dtInd = datetime.strptime(startAt, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
    results = []; i = 0
    for i in anomaly_results:
        results.append(["value", datetime.fromtimestamp(dtInd).strftime('%Y-%m-%dT%H:%M:%S.%fZ'), anomaly_results[i]])
        dtInd = dtInd + distance / len(anomaly_results)

    return 'success', results

def updateDetection(influxClient, bucket, org, detectorName, measurementList, startAt, stopAt):
    ret, result = detectMetrics(influxClient, bucket, measurementList, startAt, stopAt)

    records = []
    for item in result:
        records.append({"measurement": detectorName, "fields": {item[0]: item[2]}, "time": item[1]})

    write_api = influxClient.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket, org, records )

    return result

def isUpdateAvailable(influxClient, bucket, measurement, lastUpdatedAt):
    query_api = influxClient.query_api()

    query = ''
    if lastUpdatedAt == 'None':
        query = f'from(bucket: "{bucket}") |> range(start: 0, stop:{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")})'
    else:
        query = f'from(bucket: "{bucket}") |> range(start: {lastUpdatedAt}, stop:{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")})'
    query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
    # query += f' |> keep(columns: ["_time"])'
    query += f' |> sort(columns: ["_time"], desc: false)'
    query += f' |> last()'

    bUpdate = False

    try:
        result = query_api.query(org=settings.INFLUX_ORG, query=query)
    except Exception as e:
        print(f'{e}')
        result = []

    if len(result) > 0:
        lastUpdatedAt = result[0].records[0]["_time"]
        # + timedelta(seconds=1)
        lastUpdatedAt = lastUpdatedAt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # print( "New Data", lastUpdatedAt )
        bUpdate = True
    else:
        # print( "No Data", lastUpdatedAt )
        bUpdate = False

    return bUpdate, lastUpdatedAt

def getInitialAt(influxClient, bucket, measurement):
    query_api = influxClient.query_api()

    query = f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z, stop:{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")})'
    query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
    # query += f' |> keep(columns: ["_time"])'
    query += f' |> sort(columns: ["_time"], desc: false)'
    query += f' |> first()'

    initialAt = None
    result = query_api.query(org=settings.INFLUX_ORG, query=query)
    if len(result) > 0:
        initialAt = result[0].records[0]["_time"]
        initialAt = initialAt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return initialAt

def getMaxAnomaly(influxClient, bucket, measurement, startAt, stopAt):
    query_api = influxClient.query_api()

    query = ''
    if startAt == None and stopAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z)'
    elif stopAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: {startAt})'
    elif startAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z, stop:{stopAt})'
    else:
        query += f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt})'
    query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
    query += f' |> max(column: "_value")'

    result = query_api.query(org=settings.INFLUX_ORG, query=query)
    if len(result) > 0: maxValue = result[0].records[0].values['_value']
    else: maxValue = 0

    return maxValue

def getLastValue(influxClient, bucket, measurement, startAt, stopAt):
    query_api = influxClient.query_api()

    query = ''
    if startAt == None and stopAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z)'
    elif stopAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: {startAt})'
    elif startAt == None:
        query += f'from(bucket: "{bucket}") |> range(start: 1970-12-31T00:00:00.000Z, stop:{stopAt})'
    else:
        query += f'from(bucket: "{bucket}") |> range(start: {startAt}, stop:{stopAt})'
    query += f' |> filter(fn: (r) => r._measurement == "{measurement}")'
    query += f' |> sort(columns: ["_time"], desc: false)'
    query += f' |> first(column: "_value")'

    result = query_api.query(org=settings.INFLUX_ORG, query=query)
    if len(result) > 0: maxValue = result[0].records[0].values['_value']
    else: maxValue = 0

    return maxValue

