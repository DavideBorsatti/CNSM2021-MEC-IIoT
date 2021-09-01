#!/usr/bin/env python3

import os
import socket
import json
import requests
import datetime
import subprocess
import threading
import uuid
from random import choice
from string import ascii_uppercase
import time
import paho.mqtt.client as mqtt


def set_to_list(s):
    if isinstance(s, set):
        return list(s)
    return None

class pubThread(threading.Thread):
  def __init__(self, threadID, rate, address, port, qos, topics):
    threading.Thread.__init__(self)
    self.name = threadID
    self.rate = rate
    self.address = address
    self.port = port
    self.qos = qos
    self.signal = True
    self.topics = topics
  def run(self):
    pub = mqtt.Client()
    pub.max_inflight_messages_set(200)
    try:
        pub.connect(self.address,int(self.port),60)
        pub.loop_start()
    except:
       raise ValueError("Unable to connect to MQTT broker")
    while self.signal:
        for topic in self.topics:
            pub.publish(topic,''.join(choice(ascii_uppercase) for i in range(5)),qos=self.qos)
        time.sleep(self.rate/1000)
    #print('Ended sensor thread  '+str(self.threadID))

# Base dir of the html, css and js files
BASEDIR='/var/www'
# MEC Service endpoint
MEC_SERVICE_MGMT="mec_service_mgmt/v1"
# MEC Application endpoint
MEC_APP_SUPPORT="mec_app_support/v1"

MEC_DEVICES = "/mec_service_mgmt/v1/devices/"

# Application business endpoint
EXTERNAL_ENDPOINT='/external_endpoint'
# Callback proposed
CALLBACK_URL='/_mecSerMgmtApi/callback'


# The endpoint we will contact to get data from the application.
other_application_uri=''

# Service ID, this will be set by the MEC
service_id = ''


# MEC Base Endpoint.
mec_base = ''

# Application instance, this can be set by environment variables and
#  overwritten within the application
app_instance_id = ''

#K8s metadata for external DNS
pod_name = ''
pod_namespace = ''

infra = ''

# The service we are searching in the services list to be notified on.
target_service = ''

# Sample topic add config

sample_add_topic = {
    'topics': []
}

# Default service data, this can be edited within the application
service_data = {
    "serInstanceId": "Mec-MQTT-1",
    "serName": "Mec-MQTT-Service",
    "serCategory": {
      "href": "/example/catalogue1",
      "id": "id12345",
      "name": "RNI",
      "version": "version1"
    },
    "version": "ServiceVersion1",
    "state": "ACTIVE",
    "transportInfo": {
      "id": "MqttPubId01",
      "name": "Start Sensing",
      "description": "Start Sensing",
      "type": "REST_HTTP",
      "protocol": "HTTP",
      "version": "2.0",
      "endpoint": {
        "addresses":[{
          "uris":"/start-sensing"
        }]  
      },
      "security": {
        "oAuth2Info": {
          "grantTypes": [
            "OAUTH2_CLIENT_CREDENTIALS"
          ],
          "tokenEndpoint": "/mecSerMgmtApi/security/TokenEndPoint"
        }
      },
      "implSpecificInfo": {}
    },
    "serializer": "JSON",
    "scopeOfLocality": "MEC_SYSTEM",
    "consumedLocalOnly": False,
    "isLocal": True
}

def get_all_services():
    global mec_base
    out = ''
    query_base = "{}/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
    )

    r = requests.get(query_base)

    return json.loads(r.text)

# The application has been notified
application_notified = False


# Start MQTT application
def start_sensing(topics):
    address = ''
    
    try:
        srvs = get_all_services()
        for s in srvs:
            if s['transportInfo']['type'] == 'MB_TOPIC_BASED' and s['transportInfo']['protocol'] == 'MQTT':
                address=s['transportInfo']['endpoint']['alternative']["mqtt-topics"]['host']
                port=s['transportInfo']['endpoint']['alternative']["mqtt-topics"]['port']
                broker_service_id = s['serInstanceId']
        if not address:
            raise ValueError("No valid enpoint found")
                
    except:
        print("Unable to retrive service list")

    #Connect to the MQTT broker found in the MEC services
    #pub = mqtt.Client()
    #pub.max_inflight_messages_set(200)
    qos = 0
    rate = 3000
    #try:
    #    pub.connect(address,int(port),60)
    #    pub.loop_start()
    #except:
    #    abort(503, description="Unable to retrive service list")
    t = pubThread("mqtt-pub", rate, address, port , qos, topics)
    t.start()
    t.join()
    return "Sending MQTT data to broker with Service Id: {}".format(broker_service_id)
    
## Stop MQTT application
#@app.route("/stop-sensing")
#def stop_sensing():
#    for thread in threading.enumerate():
#        if thread.name == "mqtt-pub":
#            thread.signal = False
#            
#    return "ok"



try:
    #app_instance_id = os.environ['APP_INSTANCE_ID']
    app_instance_id = uuid.uuid1()
    mec_base = os.environ['MEC_BASE']
    pod_namespace = os.environ['MY_POD_NAMESPACE']
    pod_name = os.environ['MY_POD_NAME']
    infra = os.environ['INFRA']
except:
    # No configuration for now, will except when a request to an
    # invalid endpoint will be made.
    pass

try:
    with open('/etc/mqtt/topics.json') as file:
        data = json.load(file)
except:
    print("No topic config found")
url = "{}/{}/{}/".format(
        mec_base,
        MEC_DEVICES,
        app_instance_id
)
x = requests.post(url, data = json.dumps(data))
start_sensing(data['topics'])