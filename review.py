import os
from telnetlib import GA
import requests
import base64
import hmac
import hashlib
import binascii
import json
import time
from prometheus_client import start_http_server, Summary, Gauge

url = os.environ.get('ISUN_MARKETS_URL', "")
sid = os.environ.get('ISUN_SID', '')
key = os.environ.get('ISUN_KEY', '')
secret = os.environ.get('ISUN_SECRET', '')
path='/api/v1/wallet/list'

def hmac_value(key,data):
    byte_key = bytes(key, 'UTF-8')
    #byte_key = binascii.unhexlify(key)
    h = hmac.new(byte_key, data.encode(), hashlib.sha256)
    return h.hexdigest()

def getjson_private(path,sid,key,secret,url,extra_params={}):
    headers = {"X-api-sid": sid,
        "X-api-key": key,
        "X-api-key-checksum": hmac_value(secret,path+":"),
        "Content-Type": "application/json"}
    params = {}
    for e in extra_params:
        params[e] = extra_params[e]
    response = requests.get(url+path,params = params,headers=headers)
    if response.status_code == 200:
        if (len(response.json())==0):return None
        return response.json()
    else:return response.json()
    raise Exception ("Invalid status code "+str(response.status_code)+" url:"+url+" message"+str(response.content))

def gauge_reparation(param, data):
    return [[i['currencyCode'],i[param]] for i in data]

def Gauge_parsing(param1,param2):
    return Gauge(param1, param2, labelnames=['currency'])

gaugeAvailable = Gauge_parsing('isAvailable', 'Currency Available')
gaugeReserved = Gauge_parsing('reserved', 'Currency Reserved')
gaugeTotal = Gauge_parsing('Total', 'Currency Total')

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8887)
    # Generate some requests.
    while True:

        pre_data=getjson_private(path,sid,key,secret,url)
        gAvalues = gauge_reparation('isAvailable', pre_data['list'])
        gRvalues = gauge_reparation('reserved', pre_data['list'])
        gTvalues = [[i['currencyCode'],i['isAvailable']+i['reserved']] for i in pre_data['list']]
       
        for C,V in gAvalues: #if changing this loop into def , it stops working
            print(C, V)
            gaugeAvailable.labels(C).set(V)
        for C,V in gRvalues:
            gaugeReserved.labels(C).set(V)
        for C,V in gTvalues:
            gaugeTotal.labels(C).set(V)
        time.sleep(10)