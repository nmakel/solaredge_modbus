#!/usr/bin/env python3

import argparse
import json

import paho.mqtt.client as mqtt  # pip install paho-mqtt

import solaredge_modbus

"""
A way to send data to MQTT broker allowing several subscribers to consume them.

MQTT is a publish-subscribe model, the subscribers receive the data at publishing time (no need for polling).

Use case of subscribers:
- Small ESPHome MCUs with OLED display to show the current power.
- Home-Assistant for various displays and automations.
- MCU to control the water heater according to the solar production.
- Python script that bridges between MQTT messages and InfluxDB.

Subscribtion example:
    mosquitto_sub.exe -h 192.168.1.4 -t 'tele/solarEdge/allData'

"""


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("host", type=str, help="Modbus TCP address")
    argparser.add_argument("port", type=int, help="Modbus TCP port")
    argparser.add_argument("--timeout", type=int, default=1, help="Connection timeout")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus device address")
    argparser.add_argument("--mqttHost", type=str, default="localhost", help="hostname or IP address of the remote broker")
    argparser.add_argument("--mqttTopic", type=str, default="tele/solarEdge/allData", help="the topic that the message should be published on")
    args = argparser.parse_args()

    inverter = solaredge_modbus.Inverter(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        unit=args.unit
    )

    values = {}
    values = inverter.read_all()
    meters = inverter.meters()
    batteries = inverter.batteries()
    values["meters"] = {}
    values["batteries"] = {}

    for meter, params in meters.items():
        meter_values = params.read_all()
        values["meters"][meter] = meter_values

    for battery, params in batteries.items():
        battery_values = params.read_all()
        values["batteries"][battery] = battery_values

    # MQTT
    mqttc = mqtt.Client("SolarEdge2Mqtt")
    #mqttc.username_pw_set(args.username, args.password)
    mqttc.connect(args.mqttHost)
    mqttc.publish(args.mqttTopic, json.dumps(values))
