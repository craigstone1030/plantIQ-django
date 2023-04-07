import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from django.conf import settings
from flightsql import FlightSQLClient

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
    finally:
        client.close()

def getRecords(influxClient, bucket, measurement):

    client = influxClient
    try:
        query = f'from(bucket: "{bucket}") |> range(start: -1d) |> filter(fn: (r) => r._measurement == "{measurement}")'

        query_api = client.query_api()
        result = query_api.query(org=settings.INFLUX_ORG, query=query)

        datas = [ ]
        for table in result:
            for row in table.records:
                datas.append( [ row.values["_field"], row.values["_time"], row.values["_value"] ] )

        return 'success', datas
    except Exception as e:
        return 'error', e
    finally:
        client.close()

