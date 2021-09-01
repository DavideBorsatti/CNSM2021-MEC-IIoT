#!/bin/bash

#get opcua variables for setting up the server
cd /home/ubuntu

git clone https://github.com/lorenzobassi96/opcua_server_CNSM
cd opcua_server_CNSM

cd get_json_data

#-----------------------------------------------------------------
#declare RESULT=($(python3 get_all_sensors.py))
#RESULT contiene la stampa di tutti quanti i nomi dei sensori dichiarati nel json

#declare -A sensor_array

#SENSORS=$(python3 get_number_sensors.py)
#SENSORS rappresenta il numero di sensori che sono stati dichiarati nel json

#for ((i=0 ; i<=$SENSORS ; i++));
#do
#    sensor_array[$i]=${RESULT[i]}
#done

#Vado a prendere il nome dei sensori che mi serve
#SENSOR1=${sensor_array[0]}
#SENSOR2=${sensor_array[1]}
#----------------------------------------------------------------



PORT=$(python3 get_port_from_json_opcua.py)
URI=$(python3 get_uri_from_json_opcua.py)

#OBJ=$(python3 get_object_name_from_json_opcua.py)


#Download from Github all files and copy them inside the location
#of the python script mor the registration of the service on the MEC platform

cd /usr/local/bin/
git clone https://github.com/lorenzobassi96/opcua_server_CNSM
cd opcua_server_CNSM/get_json_data
cp -R * /usr/local/bin/




echo "--------------------------------------"
echo "STARTING NEW SERVER..."
echo "--------------------------------------"

#IP=$(/sbin/ifconfig ens3 | grep 'inet' | cut -d: -f2 | awk '{print $2}')

cd /home/ubuntu
cd opcua_server_CNSM/get_json_data
cp -R * /home/ubuntu/opcua_server_CNSM

cd /home/ubuntu/opcua_server_CNSM

python3 /usr/local/bin/opc-ua-server-stuartup.py

#python3 server-example.py $IP $PORT $1 $URI $OBJ $SENSOR1 $SENSOR2
#python3 server-example.py $IP $PORT $1 $URI

python3 server-example.py 0.0.0.0 $PORT $1 $URI 

