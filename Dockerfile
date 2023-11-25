FROM python:3.8

RUN pip3 install pyserial
RUN pip3 install paho-mqtt

COPY . /app
WORKDIR /app
RUN python3 setup.py install

ENTRYPOINT [ "/usr/local/bin/python3", "example.py" ]
