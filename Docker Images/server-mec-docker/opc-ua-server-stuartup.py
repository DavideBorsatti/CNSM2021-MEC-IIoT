#!/usr/bin/env python3

#!/usr/bin/env python3

import os
import json
import requests
import uuid
import socket
import sys

# GET OPCUA DATA 
with open('/usr/local/bin/opcua_fields.json') as file:
   data = json.load(file)
 
#ipadd = socket.gethostname()
#valore_ip = socket.gethostbyname(ipadd)

#valore_porta = data["opcua"][0]["port"]
#valore_uri = data["opcua"][0]["uri"]


#valore_object_name = data["opcua"][1]["objects"][0]["object_name"]
#valore_sensor1 = data["opcua"][1]["objects"][0]["variables"][0]
#valore_sensor2 = data["opcua"][1]["objects"][0]["variables"][1]


# MEC Service endpoint
MEC_SERVICE_MGMT="mec_service_mgmt/v1"

#mec_base = 'http://{}'.format(sys.argv[1])   

mec_base = os.environ['MEC_BASE']

pod_namespace = os.environ['MY_POD_NAMESPACE']
pod_name = os.environ['MY_POD_NAME']

service_data = {
    "serInstanceId": "OPC_UA_SERVER", 
    "serName": "OPC_UA_SERVER-service", 
    "serCategory": {
    "href": "/example/catalogue1",
    "id": "id12345",
    "name": "RNI",
    "version": "version1"
    },
    "version": "ServiceVersion1",
    "state": "ACTIVE",
    "transportInfo": {
    "id": "OPC_UA_SERVER---1",  
    "name": "OPC_UA_SERVER", 
    "description": "OPC_UA_SERVER", 
    "type": "MB_TOPIC_BASED",
    "protocol": "OPCUA", 
    "version": "2.0",
    "endpoint": {
        "alternative": {
            "opcua":[] 
        
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
    "scopeOfLocality": "NFVI_NODE",
    "consumedLocalOnly": False,
    "isLocal": True
}
}


service_data["transportInfo"]["endpoint"]["alternative"]["opcua"] = data["opcua"]  

app_instance_id = uuid.uuid1()

#hostname = "{}.{}.mec.host".format(pod_name, pod_namespace)
hostname = "{}.{}.mec.host".format(pod_name, pod_namespace)
service_data['transportInfo']['endpoint']['alternative']['opcua'][0]['host'] = hostname

query_base = "{}/{}/applications/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
            app_instance_id
    )
headers = {"content-type": "application/json"}
r = requests.post(query_base, data=json.dumps(service_data), headers=headers)