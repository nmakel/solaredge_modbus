FROM python:3.8

RUN pip3 install pyserial

COPY . /app
WORKDIR /app
RUN python3 setup.py install

#Install requirements
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "/usr/local/bin/python3", "data_server.py" ]