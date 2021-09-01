#script.py (ip_server) (port) (index_namespace)
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
from flask import Flask, Response, request, abort, jsonify

import time
from multiprocessing import Process
import signal
from node import *
from opcua import Client
import sys

MEC_SERVICE_MGMT="mec_service_mgmt/v1"

mec_base = str(sys.argv[1])

def get_all_services():
    global mec_base
    out = ''
    query_base = "http://{}/{}/services".format(
            mec_base,
            MEC_SERVICE_MGMT,
    )

    r = requests.get(query_base)

    return json.loads(r.text)

def do_actions():
    endpoint = {}
    
    try:
        srvs = get_all_services()
        for s in srvs:
            if s['transportInfo']['type'] == 'MB_TOPIC_BASED' and s['transportInfo']['protocol'] == 'OPCUA':   
                endpoint=s['transportInfo']['endpoint']['addresses']
                opc_ua_server_service_id = s['serInstanceId']                                               
        if not endpoint:
            abort(404, description="No OPCUA endpoint found")
                
    except:
        abort(500, description="Unable to retrive service list")
    
    qos = 0
    rate = 1000
    hostname = endpoint[0]['host']
    port = endpoint[0]['port']
    
    
    index = int(sys.argv[2])

    print (index)
    domain = "opc.tcp://"
    ddd = ":"
    final_address = (domain+hostname+ddd+port)



    try:
       client=Client(final_address)
       client.connect()
    except:
       print("Client couldn't connect to Server at " + "opc.tcp://"+hostname+":"+str(port))
       sys.exit(-1)


    #from node import *
    Server_Nodes = ServerNodes()
    Server_Nodes.build_list(Node(client.get_objects_node(), None))
    #Server_Nodes.show_hierarchie()
    print ("-------------------------------")
    Server_Nodes.node_list[index].get_node_value()

    print ("--")

if __name__ == '__main__':
    with open ("/usr/local/bin/result","w") as f:
        f.write("")
    # We create a Process
    action_process = Process(target=do_actions)

    # We start the process and we block for 5 seconds.
    action_process.start()
    action_process.join(timeout=3)

    # We terminate the process.
    action_process.terminate()
    index = int(sys.argv[2])
    print("This is the variable in position "+str(index)+" inside the Namespace" )
    with open ("/usr/local/bin/result","r") as f:
        print(f.read())


