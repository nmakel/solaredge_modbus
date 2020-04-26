#!/usr/bin/env python3

import argparse
import solaredge_modbus


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("host", type=str, help="ModbusTCP address")
    argparser.add_argument("port", type=int, help="ModbusTCP port")
    argparser.add_argument("--unit", type=int, default=1, help="Modbus unit")
    args = argparser.parse_args()

    inverter = solaredge_modbus.Inverter(host=args.host, port=args.port, unit=args.unit)

    print(inverter.read_all())
    inverter.pprint()
