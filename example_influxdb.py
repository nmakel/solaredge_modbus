#!/usr/bin/env python3

import argparse
from influxdb import InfluxDBClient
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

                if scale < 0:
                    v = v / 10 ** abs(scale)

                inverter_data["fields"].update({k: float(v)})

        json_body.append(inverter_data)

        for meter, params in meters.items():
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

            # calc self consumption from 
            # inverter.power_ac, inverter.power_ac_scale 
            # meter.power, meter.power_scale
            inverter_power_ac = values["power_ac"] / 10 ** abs(values["power_ac_scale"])
            meter_power = meter_values["power"] / 10 ** abs(meter_values["power_scale"])
                
            meter_values["power_selfconsumption"] = inverter_power_ac - meter_power

            if meter_power < 0:
                meter_values["power_import_from_grid"] = float(abs(meter_power))
            else:
                meter_values["power_import_from_grid"] = float(0)
            
            if meter_power > 0:
                meter_values["power_export_to_grid"] = float(meter_power)
            else:
                meter_values["power_export_to_grid"] = float(0)

            for k, v in meter_values.items():
                if (isinstance(v, int) or isinstance(v, float)) and "_scale" not in k:
                    k_split = k.split("_")
                    scale = 0

                    if f"{k_split[len(k_split) - 1]}_scale" in values:
                        scale = values[f"{k_split[len(k_split) - 1]}_scale"]
                    elif f"{k}_scale" in values:
                        scale = values[f"{k}_scale"]

                    if scale < 0:
                        v = v / 10 ** abs(scale)

                    meter_data["fields"].update({k: v})

            json_body.append(meter_data)

        for battery, params in batteries.items():
            battery_values = params.read_all()

            # calc current pv power from battery.power and inverter.power_dc
            # battery.instantaneous_power and inverter.power_dc, inverter.power_dc_scale 
            inverter_power_dc = values["power_dc"] / 10 ** abs(values["power_dc_scale"])
            battery_power = battery_values["instantaneous_power"]
            battery_values["power_pv_dc"] = inverter_power_dc + battery_power

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

            for k, v in battery_values.items():
                if isinstance(v, int) or isinstance(v, float):
                    battery_data["fields"].update({k: v})

            json_body.append(battery_data)

        client.write_points(json_body)
        time.sleep(args.interval)
