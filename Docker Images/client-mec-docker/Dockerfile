FROM ubuntu

#RUN apk update
#RUN apk add python3
#RUN apk add py3-flask
#RUN apk add py3-requests
#RUN apk add py3-paho-mqtt

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get update
RUN apt install -y git
RUN apt-get install -y python3
RUN apt-get install -y python3-pip


RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install paho-mqtt

#RUN pip3 install time
RUN pip3 install opcua
#RUN pip3 install signal

#pip install opcua ????????????????????????????????????????????????

ENV MY_POD_NAMESPACE=mec
ENV MEC_BASE=mec
ENV MY_POD_NAME=mec

COPY app.py /usr/local/bin/app.py
COPY app_site /var/www/

#Aggiunta di ulteriori files
COPY node.py /usr/local/bin/node.py
RUN chmod +x /usr/local/bin/node.py

COPY NodeBrowser.py /usr/local/bin/NodeBrowser.py
RUN chmod +x /usr/local/bin/NodeBrowser.py

COPY change_parameter_namespace.py /usr/local/bin/change_parameter_namespace.py
RUN chmod +x /usr/local/bin/change_parameter_namespace.py

COPY show_namespace_variable.py /usr/local/bin/show_namespace_variable.py
RUN chmod +x /usr/local/bin/show_namespace_variable.py


RUN chmod +x /usr/local/bin/app.py
EXPOSE 80

CMD /usr/local/bin/app.py
