#!/usr/bin/env python3

import argparse
import json

import paho.mqtt.publish as publish  # pip install paho-mqtt

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
    argparser.add_argument("--mqttPort", type=int, default=1883, help="port of the remote broker")
    argparser.add_argument("--mqttBaseTopic", type=str, default="solaredge", help="the topic that the message should be published on")
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
    
    production_power = (values['power_ac'] * (10 ** values['power_ac_scale']))
    export_power = values['meters']['Meter1']['power'] * (10 ** values['meters']['Meter1']['power_scale'])
    consumption_power = production_power - export_power

    energy_total = values['energy_total'] * (10 ** values['energy_total_scale'])
    import_total = values['meters']['Meter1']['import_energy_active'] * (10 ** values['meters']['Meter1']['energy_active_scale'])
    export_total = values['meters']['Meter1']['export_energy_active'] * (10 ** values['meters']['Meter1']['energy_active_scale'])
    self_consumption_total = energy_total - export_total


    # MQTT
    msgs = [
        # raw json data
        {'topic': f"{args.mqttBaseTopic}/json", 'payload':json.dumps(values)},
        # power
        {'topic': f"{args.mqttBaseTopic}/power/production", 'payload':production_power},
        {'topic': f"{args.mqttBaseTopic}/power/export", 'payload':export_power},
        {'topic': f"{args.mqttBaseTopic}/power/consumption", 'payload':consumption_power},
        # meters
        {'topic': f"{args.mqttBaseTopic}/meter/energy_total", 'payload':energy_total},
        {'topic': f"{args.mqttBaseTopic}/meter/import_energy_active", 'payload':import_total},
        {'topic': f"{args.mqttBaseTopic}/meter/export_energy_active", 'payload':export_total},
    ]
    publish.multiple(msgs, hostname=args.mqttHost, port=args.mqttPort, client_id="", will=None, auth=None, tls=None, transport="tcp")