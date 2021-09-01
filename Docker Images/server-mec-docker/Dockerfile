#FROM eclipse-mosquitto    --> vecchio
FROM lorenzobassi/opcua-base-python



#INSTALLAZIONE LIBRERIE ---------------------------
#RUN apt-get update
#RUN apt-get install -y software-properties-common
#RUN apt-get update
#RUN apt install -y git
#RUN apt-get install -y python3
#RUN apt-get install -y python3-pip
#RUN apt-get install -y cmake
#RUN apt install net-tools 	
#RUN apt-get install -y mysql-server  
RUN pip3 install requests

ENV MY_POD_NAMESPACE=mec
ENV MEC_BASE=mec
ENV MY_POD_NAME=mec

ARG time=default_value

ENV time=${time}

#ADD scripts /home/ubuntu/scripts


COPY opc-ua-server-stuartup.py /usr/local/bin/opc-ua-server-stuartup.py
RUN chmod +x /usr/local/bin/opc-ua-server-stuartup.py


COPY run-mec-opcua-server.sh /home/run-mec-opcua-server.sh
RUN chmod +x /home/run-mec-opcua-server.sh

EXPOSE 4840
CMD /home/run-mec-opcua-server.sh $time

#CMD ["/usr/local/bin/broker-startup.py" "/usr/sbin/mosquitto" "-c" "/mosquitto/config/mosquitto.conf"]