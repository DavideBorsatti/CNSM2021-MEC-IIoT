#!/usr/bin/env python3

# unibo-test-application - Testbed for MEC API 011 applications
# This application is part of unibo-test-mec
# Copyright (C) 2020  Davide Berardi   <berardi.dav@gmail.com>
#                     Davide Borsatti  <davide.borsatti@studio.unibo.it>
#                     Franco Callegati <franco.callegati@unibo.it>
#                     Walter Cerroni   <walter.cerroni@unibo.it>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

# TODO:
#  - This can be transformed into a framework.
#
# TODO:
#  - remove hardcoded and environmental variable with a configurable
#    page
#
# TODO:
#  - README.md

import os
import socket
import json
import requests
import datetime
import subprocess
import threading
import uuid
import logging
from random import choice
from string import ascii_uppercase
import time
from opcua import Client
from opcua import ua
from flask import Flask, Response, request, abort, jsonify
import paho.mqtt.subscribe as subscribe



try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)

def get_nic():
    for k in os.listdir('/sys/class/net'):
        if k != 'lo':
            return k

def set_to_list(s):
    if isinstance(s, set):
        return list(s)
    return None

class pubThread(threading.Thread):
  def __init__(self, threadID, rate, address, port, qos):
    threading.Thread.__init__(self)
    self.name = threadID
    self.rate = rate
    self.address = address
    self.port = port
    self.qos = qos
    self.signal = True
  def run(self):                    #NUOVA DEFINIZONE DELLA CLASSE RUN PER L'ESECUZIONE DEL CLIENT
    ip_address = self.address
    port_number = self.port
    domain = "opc.tcp://"
    ddd = ":"
    final_address = (domain+ip_address+ddd+port_number)
    print (final_address)

     # ok???????????


    client = Client(final_address)
    client.connect()

    from time import sleep #ok?????????????????????????

    while self.signal:
        print(client.get_node("ns=1;s=Random_Number").get_value())
        sleep(1)

    #print('Ended sensor thread  '+str(self.threadID))

# Base dir of the html, css and js files
BASEDIR='/var/www'
# MEC Service endpoint
MEC_SERVICE_MGMT="mec_service_mgmt/v1"
# MEC Application endpoint
MEC_APP_SUPPORT="mec_app_support/v1"

# Application business endpoint
EXTERNAL_ENDPOINT='/external_endpoint'
# Callback proposed
CALLBACK_URL='/_mecSerMgmtApi/callback'

# Network interface for PTP daemon
INTERFACE=get_nic()

# XXX Unsupported in alpine atm.
PTP_COMMAND="ptp4l -A -4 -S -i {}".format(INTERFACE)

# The endpoint we will contact to get data from the application.
other_application_uri=''

sensor_msg = ''

# Service ID, this will be set by the MEC
service_id = ''

# Flask initialization.
app = Flask(__name__)

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

# Default service data, this can be edited within the application
service_data = {
    "serInstanceId": "OPC_UA_SERVER", # CAMBIATA
    "serName": "OPC_UA_SERVER-service", # CAMBIATO
    "serCategory": {
    "href": "/example/catalogue1",
    "id": "id12345",
    "name": "RNI",
    "version": "version1"
    },
    "version": "ServiceVersion1",
    "state": "ACTIVE",
    "transportInfo": {
    "id": "OPC_UA_SERVER---1",  # CAMBIATA
    "name": "OPC_UA_SERVER",  # CAMBIATA
    "description": "OPC_UA_SERVER", # CAMBIATA
    "type": "MB_TOPIC_BASED",
    "protocol": "OPCUA", # CAMBIATO
    "version": "2.0",
    "endpoint": {
        "addresses":[{
            "host" : "mqtt-broker", #???????????????????????????? "host" : "opc.tcp://" IO METTEREI QUESTO
            "port" : "1883"
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

# The application has been notified
application_notified = False

# 404 Error handler
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

# 500 Error handler
@app.errorhandler(500)
def internal_error(e):
    return jsonify(error=str(e)), 500

# 503 Error handler
@app.errorhandler(503)
def internal_error(e):
    return jsonify(error=str(e)), 503

# Transport API
@app.route('/transports')
def transports():
    global mec_base
    query_base = "{}/{}/transports".format(
            mec_base,
            MEC_SERVICE_MGMT
    )
    r = requests.get(query_base)

    return r.text


# Services API
@app.route('/services')
def services():
    global mec_base
    global app_instance_id
    global other_application_uri
    out = ''
    query_base = "{}/{}/applications/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id
    )

    r = requests.get(query_base)

    # Get transport endpoint from services
    try:
        srvs = json.loads(r.text)
        for s in srvs:
            if s['serName'] != target_service:
                continue
            other_application_uri = s['transportInfo']['endpoint']['uris'][0]
    except Exception as e:
        print(str(e))

    return r.text

# Subscribe to service
@app.route('/services/subscribe')
def service_subscribe():
    #data = service_data
    #data = service_data
    global service_data
    global pod_name
    global pod_namespace
    global infra

    if infra == 'fog':
        pod_name = socket.gethostname()
        hostname = "{}.fog.host/start-sensing".format(pod_name) 
    else:
        hostname = "{}.{}.mec.host/start-sensing".format(pod_name, pod_namespace) 

    service_data['transportInfo']['endpoint']['addresses'][0]['uris'] = hostname

    query_base = "{}/{}/applications/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id
    )

    headers = {"content-type": "application/json"}
    r = requests.post(query_base, data=json.dumps(service_data), headers=headers)

    # XXX we don't have any slash in the url?
    #service_id = r.headers['location'].split('/')[-1]

    return 'New service_id: {}'.format(service_id)

# Unsubscribe a service
@app.route('/services/unsubscribe')
def service_unsubscribe():
    query_base = "{}/{}/applications/{}/services/{}".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id,
            service_id
    )
    r = requests.delete(query_base)
    return r.text

# Get DNS Rules
@app.route('/dns_rules')
def dns_rules():
    global dns_rules

    query_base = "{}/{}/applications/{}/dns_rules".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id
    )
    r = requests.get(query_base)

    dns_rules = json.loads(r.text)

    return r.text

# Modify DNS rules
@app.route('/dns_rules/<modification>')
def dns_rule_modify(modification):
    global dns_rules
    dns_rule = dns_rules[0]

    query_base = "{}/{}/applications/{}/dns_rules/{}".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id,
            dns_rule['dnsRuleId']
    )

    dns_rule["state"] = modification
    headers = { 'content-type': 'application/json' }
    r = requests.put(query_base, data=json.dumps(dns_rule), headers=headers)
    return json.dumps(dns_rule)

# Notifications API
@app.route('/notifications')
def notifications():
    query_base = "{}/{}/applications/{}/subscriptions".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id
    )

    r = requests.get(query_base)

    return r.text

# Subscribe to notifications
@app.route('/notifications/subscribe')
def notifications_subscribe():
    global service_id

    # Catch all notification endpoint
    data = {
      "subscriptionType": "SerAvailabilityNotificationSubscription",
      "callbackReference": "string",
      "_links": {
        "self": {
          "href": CALLBACK_URL
        }
      }
    }

    query_base = "{}/{}/applications/{}/subscriptions".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id
    )

    headers = {"content-type": "application/json"}
    r = requests.post(query_base, data=json.dumps(data), headers=headers)

    # XXX we don't have any slash in the url?
    service_id = r.headers['location'].split('/')[-1]

    return 'New notification_id: {}'.format(service_id)

# Unsubscribe notifications
@app.route('/notifications/unsubscribe')
def notification_unsubscribe():
    query_base = "{}/{}/applications/{}/subscriptions/{}".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id,
            service_id
    )
    r = requests.delete(query_base)
    return r.text

@app.route('/notifications/notify_ready')
def notification_confirm_ready():
    query_base = "{}/{}/applications/{}/confirm_ready".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id
    )

    ready_indication = { "indication": "READY" }
    headers = { 'content-type': 'application/json' }

    r = requests.post(query_base, data=json.dumps(ready_indication), headers=headers)
    return r.text

# Time API
@app.route('/timings/timing_caps')
def timing_timing_caps():
    query_base = "{}/{}/timing/timing_caps".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id,
            service_id
    )
    r = requests.get(query_base)
    return r.text

@app.route('/timings/current_time')
def timing_current_time():
    query_base = "{}/{}/timing/current_time".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id,
            service_id
    )
    r = requests.get(query_base)
    return r.text

@app.route('/timings/_ptp_status')
def timing_ptp_status():
    global ptp_process
    if ptp_process.poll != None:
        return "Not Running"
    return "Running"

@app.route('/timings/_start_ptp')
def timing_ptp_start():
    global ptp_process
    if timing_ptp_status() != "Not Running":
        return "Already running"

    ptp_process = subprocess.Popen(PTP_COMMAND.split(" "))
    return "Unimplemented"

@app.route('/timings/_ptp_time')
def timing_ptp_time():
    return str(datetime.datetime.now())

# Get Traffic Rules
@app.route('/traffic_rules')
def traffic_rules():
    global traffic_rules

    query_base = "{}/{}/applications/{}/traffic_rules".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id
    )
    r = requests.get(query_base)

    traffic_rules = json.loads(r.text)

    return r.text

# Modify DNS rules
@app.route('/traffic_rules/<modification>')
def traffic_rule_modify(modification):
    global traffic_rules
    traffic_rule = traffic_rules[0]

    query_base = "{}/{}/applications/{}/traffic_rules/{}".format(
            mec_base,
            MEC_APP_SUPPORT,
            app_instance_id,
            traffic_rule['trafficRuleId']
    )

    traffic_rule["state"] = modification
    headers = { 'content-type': 'application/json' }
    r = requests.put(query_base, data=json.dumps(traffic_rule), headers=headers)
    return json.dumps(traffic_rule)

# Catch all, return the retrieved file
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def catch_all(path):
    if '.ico' in path:
        return '';

    t = 'text/html'
    with open("{}/{}".format(BASEDIR,path)) as f:
        body = f.read()

    if '.css' in path:
        t = 'text/css'
    if '.js' in path:
        t = 'text/javascript'

    return Response(body, mimetype=t)

@app.route("/_get_application_notice")
def get_application_notice():
    return str(application_notified);


# Callback for the notification framework
@app.route(CALLBACK_URL)
def service_notification_callback():
    global application_notified
    application_notified = True

    # XXX We should notify back using a structured json?
    return ""

# Query the other application
@app.route('/_contactapplication')
def contact_application():
    query_base = "{}".format(
            other_application_uri
    )

    r = requests.get(query_base)
    return r.text

# Application endpoint, contacting this will return information
#  on the running application
@app.route(EXTERNAL_ENDPOINT)
def external_endpoint():
    result = { }
    result['app_instance_id'] = app_instance_id
    result['mec_base'] = mec_base
    result['application_notified'] = application_notified
    result['other_application_uri'] = other_application_uri
    result['traffic_rules'] = traffic_rules
    result['service_id'] = service_id
    result['callback_url'] = CALLBACK_URL
    result['dns_rules'] = dns_rules

    # And a dynamic value
    result['current_time'] = str(time.time())

    return json.dumps(result)

# Get and change the configurations
@app.route("/_configuration", methods=[ "GET", "POST" ])
def configuration():
    global mec_base
    global target_service
    global other_application_uri
    global app_instance_id
    global service_data

    if request.method == 'GET':
        result = { }
        result['mec_base'] = mec_base
        result['target_service'] = target_service
        result['other_application_uri'] = other_application_uri
        result['app_instance_id'] = app_instance_id
        result['service_data'] = service_data

        return json.dumps(result, default=set_to_list)
    elif request.method == 'POST':
        r = request.json
        mec_base = r['mec_base']
        target_service = r['target_service']
        other_application_uri = r['other_application_uri']
        app_instance_id = r['app_instance_id']
        service_data = r['service_data']
        return "ok"

@app.route("/_get_sensors", methods=["GET"])
def get_sensors():
    srvs = get_all_services()
    sensor_list=[]
    for s in srvs:
        if s['transportInfo']['protocol'] == 'MQTT':
            sensor_list.extend(s['transportInfo']["endpoint"]['alternative']['mqtt-topics']['topics'])
        if s['transportInfo']['protocol'] == 'OPCUA':
            for opcua_server in s['transportInfo']["endpoint"]['alternative']['opcua']:
                for object in opcua_server['objects']:
                    for variable in object['variables']:
                        sensor_list.append(object['object_name']+'/'+variable)
    sensor_dict={}
    sensor_dict['sensors']=sensor_list
    return json.dumps(sensor_dict)


def get_all_services():
    global mec_base
    out = ''
    query_base = "{}/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
    )

    r = requests.get(query_base)

    return json.loads(r.text)

    # Get transport endpoint from services
    try:
        srvs = json.loads(r.text)
        for s in srvs:
            if s['serName'] != target_service:
                continue
            other_application_uri = s['transportInfo']['endpoint']['uris'][0]
    except Exception as e:
        print(str(e))

    return r.text

def opcua_get_data(hostname, port, uri, object, variable):
    logging.basicConfig(level=logging.WARN)
    global sensor_msg
    domain = "opc.tcp://"
    ddd = ":"
    final_address = (domain+hostname+ddd+port)
    client = Client(final_address)
    try:
        client.connect()
        client.load_type_definitions()
        root = client.get_root_node()
        objects = client.get_objects_node()
        idx = client.get_namespace_index(uri)
        sensor_msg = root.get_child(["0:Objects", "{}:{}".format(idx,object), "{}:{}".format(idx,variable)])
        obj = root.get_child(["0:Objects", "{}:{}".format(idx, object), "{}:{}".format(idx,variable)])
        print(sensor_msg) #Ho già il valore
    finally:
        client.disconnect()
    print

def mqtt_get_data(hostname, port, topic):
    global sensor_msg
    sensor_msg = subscribe.simple(topic, hostname=hostname)


@app.route("/get_sensor_data/<sensorName>")
def get_sensor_data(sensorName):
    srvs = get_all_services()
    for s in srvs:
        if s['transportInfo']['protocol'] == 'MQTT':
            if sensorName in s['transportInfo']["endpoint"]['alternative']['mqtt-topics']['topics']:
                #TODO START MQTT SENSING
                address = s['transportInfo']["endpoint"]['alternative']['mqtt-topics']['host']
                port = s['transportInfo']["endpoint"]['alternative']['mqtt-topics']['port']
                topic = sensorName
                mqtt_get_data(address, port, topic)
                print
        if s['transportInfo']['protocol'] == 'OPCUA':
            for opcua_server in s['transportInfo']["endpoint"]['alternative']['opcua']:
                for object in opcua_server['objects']:
                    if object['object_name'] == sensorName.split("/")[0] and sensorName.split("/")[1] in object['variables']:
                        #TODO START OPCUA SENSING
                        opcua_get_data(opcua_server['host'], opcua_server['port'], opcua_server['uri'], sensorName.split("/")[0], sensorName.split("/")[1])
                        print
    return

@app.route("/_acquire_data")
def acquire_data():
    global sensor_msg
    return str(sensor_msg)


# Start MQTT application    --> START CLIENT-------------------------------------
@app.route("/start-sensing")            #-> START CLIENT-------------------------------------
def start_sensing():
    endpoint = {}
    
    try:
        srvs = get_all_services()
        for s in srvs:
            #if s['transportInfo']['type'] == 'MB_TOPIC_BASED' and s['transportInfo']['protocol'] == 'MQTT':   
            if s['transportInfo']['type'] == 'MB_TOPIC_BASED' and s['transportInfo']['protocol'] == 'OPCUA':    #MODIFICA
                endpoint=s['transportInfo']['endpoint']['addresses']
                #broker_service_id = s['serInstanceId']
                opc_ua_server_service_id = s['serInstanceId']                                                   #MODIFICA
        if not endpoint:
            abort(404, description="No OPCUA endpoint found")
                
    except:
        abort(500, description="Unable to retrive service list")

    #parte vecchia di codice
    #--------------------------------------------------------------------------------------------------------------------------------------
    #Connect to the MQTT broker found in the MEC services
    """
    address = endpoint[0]['host']
    port = endpoint[0]['port']
    #pub = mqtt.Client()
    #pub.max_inflight_messages_set(200)
    qos = 0
    rate = 1000
    #try:
    #    pub.connect(address,int(port),60)
    #    pub.loop_start()
    #except:
    #    abort(503, description="Unable to retrive service list")
    #t = pubThread("mqtt-pub", rate, address, port , qos)
    t = pubThread("opcua_server-pub", rate, address, port , qos)                                                  #MODIFICA
    t.start()
    #return "Sending MQTT data to broker with Service Id: {}".format(#broker_service_id)
    return "Sending OPC UA SERVER data to cliet with Service Id: {}".format(#opc_ua_server_service_i)            #MODIFICA
    #-----------------------------------------------------------------------------------------------------------------------------------------
    """
    #PARTE NUOVA DI CODICE**************************************************************************************************
    qos = 0
    rate = 1000
    address = endpoint[0]['host']
    port = endpoint[0]['port']        
    rate = 100
    qos = 0

    t = pubThread("OPCUA-Client", rate, address, port , qos)
    t.start()
   #******************************************************************************************************************************* 
# Stop MQTT application
@app.route("/stop-sensing")
def stop_sensing():
    for thread in threading.enumerate():
        if thread.name == "opcua_server-pub":
            thread.signal = False
            
    return "ok"


if __name__=='__main__':
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
    app.run("0.0.0.0", port=80)
