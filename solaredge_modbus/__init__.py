import enum

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse


RETRIES = 3
TIMEOUT = 1
UNIT = 1


class inverterDID(enum.Enum):
    SINGLE_PHASE = 101
    SPLIT_PHASE = 102
    THREE_PHASE = 103


class inverterStatus(enum.Enum):
    I_STATUS_OFF = 1
    I_STATUS_SLEEPING = 2
    I_STATUS_STARTING = 3
    I_STATUS_MPPT = 4
    I_STATUS_THROTTLED = 5
    I_STATUS_SHUTTING_DOWN = 6
    I_STATUS_FAULT = 7
    I_STATUS_STANDBY = 8


class connectionType(enum.Enum):
    RTU = 1
    TCP = 2


class registerType(enum.Enum):
    INPUT = 1
    HOLDING = 2


class registerDataType(enum.Enum):
    BITS = 1
    UINT8 = 2
    UINT16 = 3
    UINT32 = 4
    UINT64 = 5
    INT8 = 6
    INT16 = 7
    INT32 = 8
    INT64 = 9
    FLOAT16 = 10
    FLOAT32 = 11
    STRING = 12


sunspec_notimplemented = {
    "UINT16": 0xffff,
    "ACC16": 0x0000,
    "UINT32": 0xffffffff,
    "ACC32": 0x00000000,
    "UINT64": 0xffffffffffffffff,
    "ACC64": 0x0000000000000000,
    "INT16": 0x8000,
    "SCALE": 0x8000,
    "INT32": 0x80000000,
    "INT64": 0x8000000000000000,
    "FLOAT": 0x7fc00000,
    "STRING": "\x00"
}

c_sunspec_did_map = {
    "101": "Single Phase",
    "102": "Split Phase",
    "103": "Three Phase"
}

inverter_status_map = [
    "Undefined",
    "Off",
    "Sleeping",
    "Grid Monitoring",
    "Producing",
    "Producing (Throttled)",
    "Shutting Down",
    "Fault",
    "Standby"
]


class Inverter:

    model = "SolarEdge"
    stopbits = 1
    parity = "N"
    baud = 115200

    registers = {
        "c_model": (0x9c54, 16, registerType.HOLDING, registerDataType.STRING, str, "Model", ""),
        "c_version": (0x9c6c, 8, registerType.HOLDING, registerDataType.STRING, str, "Version", ""),
        "c_serialnumber": (0x9c74, 16, registerType.HOLDING, registerDataType.STRING, str, "Serial", ""),
        "c_deviceaddress": (0x9c84, 1, registerType.HOLDING, registerDataType.UINT16, int, "Modbus ID", ""),
        "c_sunspec_did": (0x9c85, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec DID", c_sunspec_did_map),
        "current": (0x9c87, 1, registerType.HOLDING, registerDataType.UINT16, int, "Current", "A"),
        "p1_current": (0x9c88, 1, registerType.HOLDING, registerDataType.UINT16, int, "P1 Current", "A"),
        "p2_current": (0x9c89, 1, registerType.HOLDING, registerDataType.UINT16, int, "P2 Current", "A"),
        "p3_current": (0x9c8a, 1, registerType.HOLDING, registerDataType.UINT16, int, "P3 Current", "A"),
        "current_scale": (0x9c8b, 1, registerType.HOLDING, registerDataType.INT16, int, "Current Scale Factor", ""),
        "p1_voltage": (0x9c8c, 1, registerType.HOLDING, registerDataType.UINT16, int, "P1 Voltage", "V"),
        "p2_voltage": (0x9c8d, 1, registerType.HOLDING, registerDataType.UINT16, int, "P2 Voltage", "V"),
        "p3_voltage": (0x9c8e, 1, registerType.HOLDING, registerDataType.UINT16, int, "P3 Voltage", "V"),
        "p1n_voltage": (0x9c8f, 1, registerType.HOLDING, registerDataType.UINT16, int, "P1-N Voltage", "V"),
        "p2n_voltage": (0x9c90, 1, registerType.HOLDING, registerDataType.UINT16, int, "P2-N Voltage", "V"),
        "p3n_voltage": (0x9c91, 1, registerType.HOLDING, registerDataType.UINT16, int, "P3-N Voltage", "V"),
        "voltage_scale": (0x9c92, 1, registerType.HOLDING, registerDataType.INT16, int, "Voltage Scale Factor", ""),
        "power_ac": (0x9c93, 1, registerType.HOLDING, registerDataType.INT16, int, "Power", "W"),
        "power_ac_scale": (0x9c94, 1, registerType.HOLDING, registerDataType.INT16, int, "Power Scale Factor", ""),
        "frequency": (0x9c95, 1, registerType.HOLDING, registerDataType.UINT16, int, "Frequency", "Hz"),
        "frequency_scale": (0x9c96, 1, registerType.HOLDING, registerDataType.INT16, int, "Frequency Scale Factor", ""),
        "power_apparent": (0x9c97, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Apparent)", "VA"),
        "power_apparent_scale": (0x9c98, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Apparent) Scale Factor", ""),
        "power_reactive": (0x9c99, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Reactive)", "VA"),
        "power_reactive_scale": (0x9c9a, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Reactive) Scale Factor", ""),
        "power_factor": (0x9c9b, 1, registerType.HOLDING, registerDataType.INT16, int, "Power Factor", "%"),
        "power_factor_scale": (0x9c9c, 1, registerType.HOLDING, registerDataType.INT16, int, "Power Factor Scale Factor", ""),
        "energy_total": (0x9c9d, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Energy", "Wh"),
        "energy_total_scale": (0x9c9f, 1, registerType.HOLDING, registerDataType.UINT16, int, "Total Energy Scale Factor", ""),
        "current_dc": (0x9ca0, 1, registerType.HOLDING, registerDataType.UINT16, int, "DC Current", "A"),
        "current_dc_scale": (0x9ca1, 1, registerType.HOLDING, registerDataType.INT16, int, "DC Current Scale Factor", ""),
        "voltage_dc": (0x9ca2, 1, registerType.HOLDING, registerDataType.UINT16, int, "DC Voltage", "V"),
        "voltage_dc_scale": (0x9ca3, 1, registerType.HOLDING, registerDataType.INT16, int, "DC Voltage Scale Factor", ""),
        "power_dc": (0x9ca4, 1, registerType.HOLDING, registerDataType.INT16, int, "DC Power", "W"),
        "power_dc_scale": (0x9ca5, 1, registerType.HOLDING, registerDataType.INT16, int, "DC Power Scale Factor", ""),
        "temperature": (0x9ca7, 1, registerType.HOLDING, registerDataType.INT16, int, "Temperature", "°C"),
        "temperature_scale": (0x9caa, 1, registerType.HOLDING, registerDataType.INT16, int, "Temperature Scale Factor", ""),
        "status": (0x9cab, 1, registerType.HOLDING, registerDataType.UINT16, int, "Status", inverter_status_map),
        "vendor_status": (0x9cac, 1, registerType.HOLDING, registerDataType.UINT16, int, "Vendor Status", ""),
    }

    def __init__(
        self, host=False, port=False,
        device=False, stopbits=False, parity=False, baud=False,
        timeout=TIMEOUT, retries=RETRIES, unit=UNIT
    ):
        self.host = host
        self.port = port
        self.device = device

        if stopbits:
            self.stopbits = stopbits

        if parity:
            self.parity = parity

        if baud:
            self.baud = baud

        self.timeout = timeout
        self.retries = retries
        self.unit = unit

        if device:
            self.mode = connectionType.RTU
            self.client = ModbusSerialClient(
                method="rtu",
                port=self.device,
                stopbits=self.stopbits,
                parity=self.parity,
                baudrate=self.baud,
                timeout=self.timeout)
        else:
            self.mode = connectionType.TCP
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )

    def __repr__(self):
        if self.mode == connectionType.RTU:
            return f"{self.model}({self.device}, {self.mode}: stopbits={self.stopbits}, parity={self.parity}, baud={self.baud}, timeout={self.timeout}, unit={hex(self.unit)})"
        elif self.mode == connectionType.TCP:
            return f"{self.model}({self.host}:{self.port}, {self.mode}: timeout={self.timeout}, unit={hex(self.unit)})"
        else:
            return f"<{self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"

    def _read_holding_registers(self, address, length):
        for i in range(self.retries):
            result = self.client.read_holding_registers(address=address, count=length, unit=self.unit)

            if isinstance(result, ReadHoldingRegistersResponse):
                return BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Big)

        return None

    def _decode_value(self, data, length, dtype, vtype):
        try:
            if dtype == registerDataType.UINT16:
                decoded = data.decode_16bit_uint()
            elif dtype == registerDataType.UINT32:
                decoded = data.decode_32bit_uint()
            elif dtype == registerDataType.INT16:
                decoded = data.decode_16bit_int()
            elif dtype == registerDataType.STRING:
                decoded = data.decode_string(length * 2).decode("utf-8").replace("\x00", "")
            else:
                raise NotImplementedError(dtype)

            if decoded == sunspec_notimplemented[dtype.name]:
                return False
            else:
                return vtype(decoded)
        except NotImplementedError:
            raise

    def _read(self, value):
        address, length, rtype, dtype, vtype, label, fmt = value

        try:
            if rtype == registerType.HOLDING:
                return self._decode_value(self._read_holding_registers(address, length), length, dtype, vtype)
            else:
                raise NotImplementedError(rtype)
        except NotImplementedError:
            raise

    def connected(self):
        return bool(self.client.connect())

    def read(self, key):
        if key not in self.registers:
            raise KeyError(key)

        return self._read(self.registers[key])

    def read_all(self, rtype=False):
        if rtype:
            return {k: self.read(k) for k, v in self.registers.items() if (v[2] == rtype)}
        else:
            return {k: self.read(k) for k, v in self.registers.items()}

    def pprint(self):
        values = self.read_all()

        print(f"{self}:")

        print("\nRegisters:")
        print(f"\tModel: {values['c_model']}")
        print(f"\tType: {c_sunspec_did_map[str(values['c_sunspec_did'])]}")
        print(f"\tVersion: {values['c_version']}")
        print(f"\tSerial: {values['c_serialnumber']}")
        print(f"\tStatus: {inverter_status_map[values['status']]}")
        print(f"\tTemperature: {(values['temperature'] * (10 ** values['temperature_scale'])):.2f}{self.registers['temperature'][6]}")

        print(f"\tCurrent: {(values['current'] * (10 ** values['temperature_scale'])):.2f}{self.registers['current'][6]}")

        if values['c_sunspec_did'] is inverterDID.THREE_PHASE:
            print(f"\tPhase 1 Current: {(values['p1_current'] * (10 ** values['current_scale'])):.2f}{self.registers['p1_current'][6]}")
            print(f"\tPhase 2 Current: {(values['p2_current'] * (10 ** values['current_scale'])):.2f}{self.registers['p2_current'][6]}")
            print(f"\tPhase 3 Current: {(values['p3_current'] * (10 ** values['current_scale'])):.2f}{self.registers['p3_current'][6]}")
            print(f"\tPhase 1 voltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p1_voltage'][6]}")
            print(f"\tPhase 2 voltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p1_voltage'][6]}")
            print(f"\tPhase 3 voltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p1_voltage'][6]}")
            print(f"\tPhase 1-N voltage: {(values['p1n_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p1n_voltage'][6]}")
            print(f"\tPhase 2-N voltage: {(values['p2n_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p2n_voltage'][6]}")
            print(f"\tPhase 3-N voltage: {(values['p3n_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p3n_voltage'][6]}")
        else:
            print(f"\tVoltage: {(values['p1_voltage'] * (10 ** values['voltage_scale'])):.2f}{self.registers['p1_voltage'][6]}")

        print(f"\tPower: {(values['power_ac'] * (10 ** values['power_ac_scale'])):.2f}{self.registers['power_ac'][6]}")
        print(f"\tFrequency: {(values['frequency'] * (10 ** values['frequency_scale'])):.2f}{self.registers['frequency'][6]}")
        print(f"\tPower (Apparent): {(values['power_apparent'] * (10 ** values['power_apparent_scale'])):.2f}{self.registers['power_apparent'][6]}")
        print(f"\tPower (Reactive): {(values['power_reactive'] * (10 ** values['power_reactive_scale'])):.2f}{self.registers['power_reactive'][6]}")
        print(f"\tPower Factor: {(values['power_factor'] * (10 ** values['power_factor_scale'])):.2f}{self.registers['power_factor'][6]}")
        print(f"\tTotal Energy: {(values['energy_total'] * (10 ** values['energy_total_scale']))}{self.registers['energy_total'][6]}")

        print(f"\tDC Current: {(values['current_dc'] * (10 ** values['current_dc_scale'])):.2f}{self.registers['current_dc'][6]}")
        print(f"\tDC Voltage: {(values['voltage_dc'] * (10 ** values['voltage_dc_scale'])):.2f}{self.registers['voltage_dc'][6]}")
        print(f"\tDC Power: {(values['power_dc'] * (10 ** values['power_dc_scale'])):.2f}{self.registers['power_dc'][6]}")
