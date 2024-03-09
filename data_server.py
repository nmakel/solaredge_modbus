#!/usr/bin/env python3

import os
import json
from flask import Flask, jsonify

import solaredge_modbus

app = Flask(__name__)

global inverter

@app.route('/', methods=['GET'])
def get_values():
    global inverter

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

    return jsonify(values)

def parse_environment_variables():
    host = os.environ.get("MODBUS_HOST", "localhost")
    port = os.environ.get("MODBUS_PORT", "502")
    timeout = os.environ.get("MODBUS_TIMEOUT", "1")
    unit = os.environ.get("MODBUS_UNIT", "1")

    return {
        "host": host,
        "port": port,
        "timeout": timeout,
        "unit": unit,
    }

args = parse_environment_variables()  # Parse environment variables
inverter = solaredge_modbus.Inverter(
    host=args["host"],
    port=int(args["port"]),
    timeout=int(args["timeout"]),
    unit=int(args["unit"])
)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)