#!/usr/bin/env python3

import argparse
import sys
import time

from influxdb import InfluxDBClient
import requests
import solaredge_modbus


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("host", type=str, help="Modbus TCP address")
    argparser.add_argument("port", type=int, help="Modbus TCP port")
    argparser.add_argument("--timeout", type=int, default=1, help="Connection timeout")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus device address")
    argparser.add_argument("--interval", type=int, default=10, help="Update interval")
    argparser.add_argument("--influx_host", type=str, default="localhost", help="InfluxDB host")
    argparser.add_argument("--influx_port", type=int, default=8086, help="InfluxDB port")
    argparser.add_argument("--influx_db", type=str, default="solaredge", help="InfluxDB database")
    argparser.add_argument("--influx_user", type=str, help="InfluxDB username")
    argparser.add_argument("--influx_pass", type=str, help="InfluxDB password")
    args = argparser.parse_args()

    try:
        if args.influx_user and args.influx_pass:
            client = InfluxDBClient(
                host=args.influx_host,
                port=args.influx_port,
                username=args.influx_user,
                password=args.influx_pass
            )
        else:
            client = InfluxDBClient(host=args.influx_host, port=args.influx_port)

        client.switch_database(args.influx_db)
    except (ConnectionRefusedError, requests.exceptions.ConnectionError):
        print(f"database connection failed: {args.influx_host,}:{args.influx_port}/{args.influx_db}")
        sys.exit()

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
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        inverter_data = {
            "measurement": "inverter",
            "tags": {
                "c_manufacturer": values["c_manufacturer"],
                "c_model": values["c_model"],
                "c_version": values["c_version"],
                "c_serialnumber": values["c_serialnumber"],
                "c_deviceaddress": values["c_deviceaddress"],
                "c_sunspec_did": values["c_sunspec_did"]
            },
            "time": current_time,
            "fields": {}
        }

        for k, v in values.items():
            if (isinstance(v, int) or isinstance(v, float)) and "_scale" not in k:
                k_split = k.split("_")
                scale = 0

                if f"{k_split[len(k_split) - 1]}_scale" in values:
                    scale = values[f"{k_split[len(k_split) - 1]}_scale"]
                elif f"{k}_scale" in values:
                    scale = values[f"{k}_scale"]

                inverter_data["fields"].update({k: float(v * (10 ** scale))})

        json_body.append(inverter_data)

        for meter, params in meters.items():
            meter_values = params.read_all()

            meter_data = {
                "measurement": "meter",
                "tags": {
                    "c_manufacturer": meter_values["c_manufacturer"],
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

            for k, v in meter_values.items():
                if (isinstance(v, int) or isinstance(v, float)) and "_scale" not in k:
                    k_split = k.split("_")
                    scale = 0

                    if f"{k_split[len(k_split) - 1]}_scale" in meter_values:
                        scale = meter_values[f"{k_split[len(k_split) - 1]}_scale"]
                    elif f"{k}_scale" in meter_values:
                        scale = meter_values[f"{k}_scale"]

                    meter_data["fields"].update({k: float(v * (10 ** scale))})

            json_body.append(meter_data)

        for battery, params in batteries.items():
            battery_values = params.read_all()

            if not battery_values["c_model"]:
                continue

            battery_data = {
                "measurement": "battery",
                "tags": {
                    "c_manufacturer": battery_values["c_manufacturer"],
                    "c_model": battery_values["c_model"],
                    "c_version": battery_values["c_version"],
                    "c_serialnumber": battery_values["c_serialnumber"],
                    "c_deviceaddress": battery_values["c_deviceaddress"],
                    "c_sunspec_did": battery_values["c_sunspec_did"]
                },
                "time": current_time,
                "fields": {}
            }

            for k, v in battery_values.items():
                if isinstance(v, int) or isinstance(v, float):
                    battery_data["fields"].update({k: v})

            json_body.append(battery_data)

        client.write_points(json_body)
        time.sleep(args.interval)
