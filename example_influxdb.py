#!/usr/bin/env python3

import argparse
import json
from influxdb import InfluxDBClient
from datetime import datetime
import requests
import sys
import time

import solaredge_modbus


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("host", type=str, help="ModbusTCP address")
    argparser.add_argument("port", type=int, help="ModbusTCP port")
    argparser.add_argument("--timeout", type=int, default=1, help="Connection timeout")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus unit")
    argparser.add_argument("--influx_host", type=str, default="localhost", help="InfluxDB host")
    argparser.add_argument("--influx_port", type=int, default=8086, help="InfluxDB port")
    argparser.add_argument("--influx_db", type=str, default="solaredge", help="InfluxDB database")
    argparser.add_argument("--influx_user", type=str, help="InfluxDB username")
    argparser.add_argument("--influx_pass", type=str, help="InfluxDB password")
    args = argparser.parse_args()

    client = InfluxDBClient(host=args.influx_host, port=args.influx_port)
    client.switch_database(args.influx_db)

    inverter = solaredge_modbus.Inverter(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        unit=args.unit
    )

    while True:
        values = {}
        values = inverter.read_all()
        meters = inverter.meters()
        batteries = inverter.batteries()

        json_body = []
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),

        inverter_data = {
            "measurement": "inverter",
            "tags": {
                "c_model": values["c_model"],
                "c_version": values["c_version"],
                "c_serialnumber": values["c_serialnumber"],
                "c_deviceaddress": values["c_deviceaddress"],
                "c_sunspec_did": values["c_sunspec_did"]
            },
            "time": current_time,
            "fields": {}
        }
        for key,value in values.items():
            if (isinstance(value, int) or isinstance(value, float)) and '_scale' not in key:
                # search scale
                splitted_key = key.split("_")
                scale = 0
                if splitted_key[len(splitted_key)-1] + "_scale" in values:
                    scale = values[splitted_key[len(splitted_key)-1] + "_scale"]
                elif key + "_scale" in values:
                    scale = values[key + "_scale"]

                if scale < 0:
                    value = value / 10**abs(scale)

                inverter_data["fields"].update({key: value})

        json_body.append(inverter_data)

        # read meters
        for meter,params in meters.items():
            meter_values = params.read_all()
            meter_data = {
                "measurement": "meter",
                "tags": {
                    "c_model": meter_values["c_model"],
                    "c_option": meter_values["c_option"],
                    "c_version": meter_values["c_version"],
                    "c_serialnumber": meter_values["c_serialnumber"],
                    "c_deviceaddress": meter_values["c_deviceaddress"],
                    "c_sunspec_did": meter_values["c_sunspec_did"]
                },
                "time": current_time,
                "fields": {}
            }

            for key,value in meter_values.items():
                if (isinstance(value, int) or isinstance(value, float)) and '_scale' not in key:
                    # search scale
                    splitted_key = key.split("_")
                    scale = 0
                    if splitted_key[len(splitted_key)-1] + "_scale" in values:
                        scale = meter_values[splitted_key[len(splitted_key)-1] + "_scale"]
                    elif key + "_scale" in values:
                        scale = meter_values[key + "_scale"]

                    if scale < 0:
                        value = value / 10**abs(scale)

                    meter_data["fields"].update({key: value})

            json_body.append(meter_data)

        # read batteries
        for battery,params in batteries.items():
            battery_values = params.read_all()

            battery_data = {
                "measurement": "battery",
                "tags": {
                    "manufacturer_name": battery_values["manufacturer_name"],
                    "model": battery_values["model"],
                    "firmware_version": battery_values["firmware_version"],
                    "serial_number": battery_values["serial_number"],
                    "device_id": battery_values["device_id"],
                },
                "time": current_time,
                "fields": {}
            }

            for key,value in battery_values.items():
                if isinstance(value, int) or isinstance(value, float):
                    battery_data["fields"].update({key: value})

            json_body.append(battery_data)

        #print(json.dumps(json_body, indent=4))

        client.write_points(json_body)
        time.sleep(1)