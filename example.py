#!/usr/bin/env python3

import argparse
import json

import solaredge_modbus


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("host", type=str, help="ModbusTCP address")
    argparser.add_argument("port", type=int, help="ModbusTCP port")
    argparser.add_argument("--timeout", type=int, default=1, help="Connection timeout")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus unit")
    argparser.add_argument("--json", action="store_true", default=False, help="Output as JSON")
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

    if args.json:
        print(json.dumps(values, indent=4))
    else:
        print(f"{inverter}:")
        print("\nRegisters:")

        print(f"\tManufacturer: {values['c_manufacturer']}")
        print(f"\tModel: {values['c_model']}")
        print(f"\tType: {solaredge_modbus.C_SUNSPEC_DID_MAP[str(values['c_sunspec_did'])]}")
        print(f"\tVersion: {values['c_version']}")
        print(f"\tSerial: {values['c_serialnumber']}")
        print(f"\tStatus: {solaredge_modbus.INVERTER_STATUS_MAP[values['status']]}")
        print(f"\tTemperature: {(values['temperature'] * (10 ** values['temperature_scale'])):.2f}{inverter.registers['temperature'][6]}")

        print(f"\tCurrent: {(values['current'] * (10 ** values['temperature_scale'])):.2f}{inverter.registers['current'][6]}")

        if values['c_sunspec_did'] is solaredge_modbus.sunspecDID.THREE_PHASE_INVERTER:
            print(f"\tPhase 1 Current: {(values['p1_current'] * (10 ** values['current_scale'])):.2f}{inverter.registers['p1_current'][6]}")
            print(f"\tPhase 2 Current: {(values['p2_current'] * (10 ** values['current_scale'])):.2f}{inverter.registers['p2_current'][6]}")
            print(f"\tPhase 3 Current: {(values['p3_current'] * (10 ** values['current_scale'])):.2f}{inverter.registers['p3_current'][6]}")
            print(f"\tPhase 1 voltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p1_voltage'][6]}")
            print(f"\tPhase 2 voltage: {(values['p2_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p2_voltage'][6]}")
            print(f"\tPhase 3 voltage: {(values['p3_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p3_voltage'][6]}")
            print(f"\tPhase 1-N voltage: {(values['p1n_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p1n_voltage'][6]}")
            print(f"\tPhase 2-N voltage: {(values['p2n_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p2n_voltage'][6]}")
            print(f"\tPhase 3-N voltage: {(values['p3n_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p3n_voltage'][6]}")
        else:
            print(f"\tVoltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{inverter.registers['p1_voltage'][6]}")

        print(f"\tFrequency: {(values['frequency'] * (10 ** values['frequency_scale'])):.2f}{inverter.registers['frequency'][6]}")
        print(f"\tPower: {(values['power_ac'] * (10 ** values['power_ac_scale'])):.2f}{inverter.registers['power_ac'][6]}")
        print(f"\tPower (Apparent): {(values['power_apparent'] * (10 ** values['power_apparent_scale'])):.2f}{inverter.registers['power_apparent'][6]}")
        print(f"\tPower (Reactive): {(values['power_reactive'] * (10 ** values['power_reactive_scale'])):.2f}{inverter.registers['power_reactive'][6]}")
        print(f"\tPower Factor: {(values['power_factor'] * (10 ** values['power_factor_scale'])):.2f}{inverter.registers['power_factor'][6]}")
        print(f"\tTotal Energy: {(values['energy_total'] * (10 ** values['energy_total_scale']))}{inverter.registers['energy_total'][6]}")

        print(f"\tDC Current: {(values['current_dc'] * (10 ** values['current_dc_scale'])):.2f}{inverter.registers['current_dc'][6]}")
        print(f"\tDC Voltage: {(values['voltage_dc'] * (10 ** values['voltage_dc_scale'])):.2f}{inverter.registers['voltage_dc'][6]}")
        print(f"\tDC Power: {(values['power_dc'] * (10 ** values['power_dc_scale'])):.2f}{inverter.registers['power_dc'][6]}")
