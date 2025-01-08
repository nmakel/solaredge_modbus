import enum
import time

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusSerialClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse


RETRIES = 3
TIMEOUT = 1
UNIT = 1


class sunspecDID(enum.Enum):
    SINGLE_PHASE_INVERTER = 101
    SPLIT_PHASE_INVERTER = 102
    THREE_PHASE_INVERTER = 103
    SINGLE_PHASE_METER = 201
    SPLIT_PHASE_METER = 202
    WYE_THREE_PHASE_METER = 203
    DELTA_THREE_PHASE_METER = 204
    BATTERY_BASE = 802
    LI_BATTERY_BANK = 803
    LI_BATTERY_STRING = 804
    LI_BATTERY_MODULE = 805
    FLOW_BATTERY = 806
    FLOW_BATTERY_STRING = 807
    FLOW_BATTERY_MODULE = 808
    FLOW_BATTERY_STACK = 809


class inverterStatus(enum.Enum):
    I_STATUS_OFF = 1
    I_STATUS_SLEEPING = 2
    I_STATUS_STARTING = 3
    I_STATUS_MPPT = 4
    I_STATUS_THROTTLED = 5
    I_STATUS_SHUTTING_DOWN = 6
    I_STATUS_FAULT = 7
    I_STATUS_STANDBY = 8


class batteryStatus(enum.Enum):
    B_STATUS_OFF = 1
    B_STATUS_EMPTY = 2
    B_STATUS_DISCHARGING = 3
    B_STATUS_CHARGING = 4
    B_STATUS_FULL = 5
    B_STATUS_HOLDING = 6
    B_STATUS_TESTING = 7


class connectionType(enum.Enum):
    RTU = 1
    TCP = 2


class registerType(enum.Enum):
    INPUT = 1
    HOLDING = 2


class registerDataType(enum.Enum):
    UINT16 = 1
    UINT32 = 2
    UINT64 = 3
    INT16 = 4
    SCALE = 4
    ACC32 = 5
    FLOAT32 = 6
    SEFLOAT = 7
    INT32 = 8
    STRING = 9


SUNSPEC_NOTIMPLEMENTED = {
    "UINT16": 0xffff,
    "UINT32": 0xffffffff,
    "UINT64": 0xffffffffffffffff,
    "INT16": 0x8000,
    "INT32": 0x80000000,
    "SCALE": 0x8000,
    "ACC32": 0x00000000,
    "FLOAT32": 0x7fc00000,
    "SEFLOAT": 0xffffffff,
    "STRING": ""
}

C_SUNSPEC_DID_MAP = {
    "101": "Single Phase Inverter",
    "102": "Split Phase Inverter",
    "103": "Three Phase Inverter",
    "201": "Single Phase Meter",
    "202": "Split Phase Meter",
    "203": "Wye 3P1N Three Phase Meter",
    "204": "Delta 3P Three Phase Meter",
    "802": "Battery",
    "803": "Lithium Ion Bank Battery",
    "804": "Lithium Ion String Battery",
    "805": "Lithium Ion Module Battery",
    "806": "Flow Battery",
    "807": "Flow String Battery",
    "808": "Flow Module Battery",
    "809": "Flow Stack Battery"
}

INVERTER_STATUS_MAP = [
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

BATTERY_STATUS_MAP = [
    "Off",
    "Standby",
    "Init",
    "Charge",
    "Discharge",
    "Fault",
    "Idle"
]

EXPORT_CONTROL_MODE_MAP = {
    0: "Disabled",
    1: "Direct Export Limitation",
    2: "Indirect Export Limitation",
    3: "Production Limitation",
}

EXPORT_CONTROL_LIMIT_MAP = [
    "Total",
    "Per Phase"
]

REACTIVE_POWER_CONFIG_MAP = [
    "Fixed CosPhi Mode",
    "Fixed Q Mode",
    "CosPhi(P) Mode",
    "Q(U) + Q(P) Mode",
    "RRCR Mode"
]

STOREDGE_CONTROL_MODE = {
    0: "Disabled",
    1: "Maximize Self Consumption",
    2: "Time of Use",
    3: "Backup Only",
    4: "Remote Control",
}

STOREDGE_AC_CHARGE_POLICY = {
    0: "Disabled",
    1: "Always Allowed",
    2: "Fixed Energy Limit",
    3: "Percent of Production",
}

STOREDGE_CHARGE_DISCHARGE_MODE = {
    0: "Off",
    1: "Charge from excess PV power only",
    2: "Charge from PV first",
    3: "Charge from PV and AC",
    4: "Maximize export",
    5: "Discharge to match load",
    7: "Maximize self consumption",
}

METER_REGISTER_OFFSETS = [
    0x0,
    0xae,
    0x15c
]

BATTERY_REGISTER_OFFSETS = [
    0x0,
    0x100,
    0x300
]


class SolarEdge:

    model = "SolarEdge"
    stopbits = 1
    parity = "N"
    baud = 115200
    wordorder = Endian.BIG

    def __init__(
        self, host=False, port=False,
        device=False, stopbits=False, parity=False, baud=False,
        timeout=TIMEOUT, retries=RETRIES, unit=UNIT,
        parent=False
    ):
        if parent:
            self.client = parent.client
            self.mode = parent.mode
            self.timeout = parent.timeout
            self.retries = parent.retries

            if unit:
                self.unit = unit
            else:
                self.unit = parent.unit

            if self.mode is connectionType.RTU:
                self.device = parent.device
                self.stopbits = parent.stopbits
                self.parity = parent.parity
                self.baud = parent.baud
            elif self.mode is connectionType.TCP:
                self.host = parent.host
                self.port = parent.port
            else:
                raise NotImplementedError(self.mode)
        else:
            self.host = host
            self.port = port
            self.device = device

            if stopbits:
                self.stopbits = stopbits

            if (parity
                    and parity.upper() in ["N", "E", "O"]):
                self.parity = parity.upper()

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
            return f"{self.model}({self.device}, {self.mode}: stopbits={self.stopbits}, parity={self.parity}, baud={self.baud}, timeout={self.timeout}, retries={self.retries}, unit={hex(self.unit)})"
        elif self.mode == connectionType.TCP:
            return f"{self.model}({self.host}:{self.port}, {self.mode}: timeout={self.timeout}, retries={self.retries}, unit={hex(self.unit)})"
        else:
            return f"<{self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"

    def _read_holding_registers(self, address, length):
        for i in range(self.retries):
            if not self.connected():
                self.connect()
                time.sleep(0.1)
                continue

            result = self.client.read_holding_registers(address, length, slave=self.unit)

            if not isinstance(result, ReadHoldingRegistersResponse):
                continue
            if len(result.registers) != length:
                continue

            return BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=self.wordorder)

        return None

    def _write_holding_register(self, address, value):
        return self.client.write_registers(address=address, values=value, slave=self.unit)

    def _encode_value(self, data, dtype):
        builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=self.wordorder)

        try:
            if dtype == registerDataType.INT16:
                builder.add_16bit_int(data)
            elif dtype == registerDataType.INT32:
                builder.add_32bit_int(data)
            elif dtype == registerDataType.UINT16:
                builder.add_16bit_uint(data)
            elif dtype == registerDataType.UINT32:
                builder.add_32bit_uint(data)
            elif dtype == registerDataType.UINT64:
                builder.add_64bit_uint(data)
            elif (dtype == registerDataType.FLOAT32 or
                  dtype == registerDataType.SEFLOAT):
                builder.add_32bit_float(data)
            elif dtype == registerDataType.STRING:
                builder.add_string(data)
            else:
                raise NotImplementedError(dtype)

        except NotImplementedError:
            raise

        return builder.to_registers()

    def _decode_value(self, data, length, dtype, vtype):
        try:
            if dtype == registerDataType.INT16:
                decoded = data.decode_16bit_int()
            elif dtype == registerDataType.INT32:
                decoded = data.decode_32bit_int()
            elif dtype == registerDataType.UINT16:
                decoded = data.decode_16bit_uint()
            elif (dtype == registerDataType.UINT32 or
                  dtype == registerDataType.ACC32):
                decoded = data.decode_32bit_uint()
            elif dtype == registerDataType.UINT64:
                decoded = data.decode_64bit_uint()
            elif (dtype == registerDataType.FLOAT32 or
                  dtype == registerDataType.SEFLOAT):
                decoded = data.decode_32bit_float()
            elif dtype == registerDataType.STRING:
                decoded = data.decode_string(length * 2).decode(encoding="utf-8", errors="ignore").replace("\x00", "").rstrip()
            else:
                raise NotImplementedError(dtype)

            if decoded == SUNSPEC_NOTIMPLEMENTED[dtype.name]:
                return vtype(False)
            elif decoded != decoded:
                return vtype(False)
            else:
                return vtype(decoded)
        except NotImplementedError:
            raise

    def _read(self, value):
        address, length, rtype, dtype, vtype, label, fmt, batch = value

        try:
            if rtype == registerType.INPUT:
                return self._decode_value(self._read_input_registers(address, length), length, dtype, vtype)
            elif rtype == registerType.HOLDING:
                return self._decode_value(self._read_holding_registers(address, length), length, dtype, vtype)
            else:
                raise NotImplementedError(rtype)
        except NotImplementedError:
            raise
        except AttributeError:
            return False

    def _read_all(self, values, rtype):
        addr_min = False
        addr_max = False

        for k, v in values.items():
            v_addr = v[0]
            v_length = v[1]

            if addr_min is False:
                addr_min = v_addr
            if addr_max is False:
                addr_max = v_addr + v_length

            if v_addr < addr_min:
                addr_min = v_addr
            if (v_addr + v_length) > addr_max:
                addr_max = v_addr + v_length

        results = {}
        offset = addr_min
        length = addr_max - addr_min

        try:
            if rtype == registerType.INPUT:
                data = self._read_input_registers(offset, length)
            elif rtype == registerType.HOLDING:
                data = self._read_holding_registers(offset, length)
            else:
                raise NotImplementedError(rtype)

            if not data:
                return results

            for k, v in values.items():
                address, length, rtype, dtype, vtype, label, fmt, batch = v

                if address > offset:
                    skip_bytes = address - offset
                    offset += skip_bytes
                    data.skip_bytes(skip_bytes * 2)

                results[k] = self._decode_value(data, length, dtype, vtype)
                offset += length
        except NotImplementedError:
            raise

        return results

    def _write(self, value, data):
        address, length, rtype, dtype, vtype, label, fmt, batch = value

        try:
            if rtype == registerType.HOLDING:
                return self._write_holding_register(address, self._encode_value(data, dtype))
            else:
                raise NotImplementedError(rtype)
        except NotImplementedError:
            raise

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.close()

    def connected(self):
        return self.client.is_socket_open()

    def read(self, key):
        if key not in self.registers:
            raise KeyError(key)

        return {key: self._read(self.registers[key])}

    def write(self, key, data):
        if key not in self.registers:
            raise KeyError(key)

        return self._write(self.registers[key], data)

    def read_all(self, rtype=registerType.HOLDING):
        registers = {k: v for k, v in self.registers.items() if (v[2] == rtype)}
        results = {}

        for batch in range(1, len(registers)):
            register_batch = {k: v for k, v in registers.items() if (v[7] == batch)}

            if not register_batch:
                break

            results.update(self._read_all(register_batch, rtype))

        return results


class Inverter(SolarEdge):

    def __init__(self, *args, **kwargs):
        self.model = "Inverter"
        self.wordorder = Endian.BIG

        super().__init__(*args, **kwargs)

        self.registers = {
            # name, address, length, register, type, target type, description, unit, batch
            "c_id": (0x9c40, 2, registerType.HOLDING, registerDataType.STRING, str, "SunSpec ID", "", 1),
            "c_did": (0x9c42, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec DID", "", 1),
            "c_length": (0x9c43, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec Length", "16Bit Words", 1),
            "c_manufacturer": (0x9c44, 16, registerType.HOLDING, registerDataType.STRING, str, "Manufacturer", "", 1),
            "c_model": (0x9c54, 16, registerType.HOLDING, registerDataType.STRING, str, "Model", "", 1),
            "c_version": (0x9c6c, 8, registerType.HOLDING, registerDataType.STRING, str, "Version", "", 1),
            "c_serialnumber": (0x9c74, 16, registerType.HOLDING, registerDataType.STRING, str, "Serial", "", 1),
            "c_deviceaddress": (0x9c84, 1, registerType.HOLDING, registerDataType.UINT16, int, "Modbus ID", "", 1),
            "c_sunspec_did": (0x9c85, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec DID", C_SUNSPEC_DID_MAP, 2),
            "c_sunspec_length": (0x9c86, 1, registerType.HOLDING, registerDataType.UINT16, int, "Length", "16Bit Words", 2),

            "current": (0x9c87, 1, registerType.HOLDING, registerDataType.UINT16, int, "Current", "A", 2),
            "l1_current": (0x9c88, 1, registerType.HOLDING, registerDataType.UINT16, int, "L1 Current", "A", 2),
            "l2_current": (0x9c89, 1, registerType.HOLDING, registerDataType.UINT16, int, "L2 Current", "A", 2),
            "l3_current": (0x9c8a, 1, registerType.HOLDING, registerDataType.UINT16, int, "L3 Current", "A", 2),
            "current_scale": (0x9c8b, 1, registerType.HOLDING, registerDataType.SCALE, int, "Current Scale Factor", "", 2),

            "l1_voltage": (0x9c8c, 1, registerType.HOLDING, registerDataType.UINT16, int, "L1 Voltage", "V", 2),
            "l2_voltage": (0x9c8d, 1, registerType.HOLDING, registerDataType.UINT16, int, "L2 Voltage", "V", 2),
            "l3_voltage": (0x9c8e, 1, registerType.HOLDING, registerDataType.UINT16, int, "L3 Voltage", "V", 2),
            "l1n_voltage": (0x9c8f, 1, registerType.HOLDING, registerDataType.UINT16, int, "L1-N Voltage", "V", 2),
            "l2n_voltage": (0x9c90, 1, registerType.HOLDING, registerDataType.UINT16, int, "L2-N Voltage", "V", 2),
            "l3n_voltage": (0x9c91, 1, registerType.HOLDING, registerDataType.UINT16, int, "L3-N Voltage", "V", 2),
            "voltage_scale": (0x9c92, 1, registerType.HOLDING, registerDataType.SCALE, int, "Voltage Scale Factor", "", 2),

            "power_ac": (0x9c93, 1, registerType.HOLDING, registerDataType.INT16, int, "Power", "W", 2),
            "power_ac_scale": (0x9c94, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power Scale Factor", "", 2),

            "frequency": (0x9c95, 1, registerType.HOLDING, registerDataType.UINT16, int, "Frequency", "Hz", 2),
            "frequency_scale": (0x9c96, 1, registerType.HOLDING, registerDataType.SCALE, int, "Frequency Scale Factor", "", 2),

            "power_apparent": (0x9c97, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Apparent)", "VA", 2),
            "power_apparent_scale": (0x9c98, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power (Apparent) Scale Factor", "", 2),
            "power_reactive": (0x9c99, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Reactive)", "VAr", 2),
            "power_reactive_scale": (0x9c9a, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power (Reactive) Scale Factor", "", 2),
            "power_factor": (0x9c9b, 1, registerType.HOLDING, registerDataType.INT16, int, "Power Factor", "%", 2),
            "power_factor_scale": (0x9c9c, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power Factor Scale Factor", "", 2),

            "energy_total": (0x9c9d, 2, registerType.HOLDING, registerDataType.ACC32, int, "Total Energy", "Wh", 2),
            "energy_total_scale": (0x9c9f, 1, registerType.HOLDING, registerDataType.SCALE, int, "Total Energy Scale Factor", "", 2),

            "current_dc": (0x9ca0, 1, registerType.HOLDING, registerDataType.UINT16, int, "DC Current", "A", 2),
            "current_dc_scale": (0x9ca1, 1, registerType.HOLDING, registerDataType.SCALE, int, "DC Current Scale Factor", "", 2),

            "voltage_dc": (0x9ca2, 1, registerType.HOLDING, registerDataType.UINT16, int, "DC Voltage", "V", 2),
            "voltage_dc_scale": (0x9ca3, 1, registerType.HOLDING, registerDataType.SCALE, int, "DC Voltage Scale Factor", "", 2),

            "power_dc": (0x9ca4, 1, registerType.HOLDING, registerDataType.INT16, int, "DC Power", "W", 2),
            "power_dc_scale": (0x9ca5, 1, registerType.HOLDING, registerDataType.SCALE, int, "DC Power Scale Factor", "", 2),

            "temperature": (0x9ca7, 1, registerType.HOLDING, registerDataType.INT16, int, "Temperature", "°C", 2),
            "temperature_scale": (0x9caa, 1, registerType.HOLDING, registerDataType.SCALE, int, "Temperature Scale Factor", "", 2),

            "status": (0x9cab, 1, registerType.HOLDING, registerDataType.UINT16, int, "Status", INVERTER_STATUS_MAP, 2),
            "vendor_status": (0x9cac, 1, registerType.HOLDING, registerDataType.UINT16, int, "Vendor Status", "", 2),

            "rrcr_state": (0xf000, 1, registerType.HOLDING, registerDataType.UINT16, int, "RRCR State", "", 3),
            "active_power_limit": (0xf001, 1, registerType.HOLDING, registerDataType.UINT16, int, "Active Power Limit", "%", 3),
            "cosphi": (0xf002, 2, registerType.HOLDING, registerDataType.FLOAT32, int, "CosPhi", "", 3),

            "commit_power_control_settings": (0xf100, 1, registerType.HOLDING, registerDataType.INT16, int, "Commit Power Control Settings", "", 4),
            "restore_power_control_default_settings": (0xf101, 1, registerType.HOLDING, registerDataType.INT16, int, "Restore Power Control Default Settings", "", 4),

            "reactive_power_config": (0xf103, 2, registerType.HOLDING, registerDataType.INT32, int, "Reactive Power Config", REACTIVE_POWER_CONFIG_MAP, 4),
            "reactive_power_response_time": (0xf105, 2, registerType.HOLDING, registerDataType.UINT32, int, "Reactive Power Response Time", "ms", 4),

            "advanced_power_control_enable": (0xf142, 2, registerType.HOLDING, registerDataType.UINT16, int, "Advanced Power Control Enable", "", 4),

            "export_control_mode": (0xf700, 1, registerType.HOLDING, registerDataType.UINT16, int, "Export Control Mode", "", 5),
            "export_control_limit_mode": (0xf701, 1, registerType.HOLDING, registerDataType.UINT16, int, "Export Control Limit Mode", EXPORT_CONTROL_LIMIT_MAP, 5),
            "export_control_site_limit": (0xf702, 2, registerType.HOLDING, registerDataType.FLOAT32, int, "Export Control Site Limit", "W", 5)
        }

        self.meter_dids = [
            (0x9cfc, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1),
            (0x9daa, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1),
            (0x9e59, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1)
        ]

        self.battery_dids = [
            (0xe140, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1),
            (0xe240, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1),
            (0xe340, 1, registerType.HOLDING, registerDataType.UINT16, int, "", "", 1)
        ]

    def meters(self):
        meters = [self._read(v) for v in self.meter_dids]

        return {f"Meter{idx + 1}": Meter(offset=idx, parent=self) for idx, v in enumerate(meters) if v}

    def batteries(self):
        batteries = [self._read(v) for v in self.battery_dids]

        return {f"Battery{idx + 1}": Battery(offset=idx, parent=self) for idx, v in enumerate(batteries) if v != 255}


class Meter(SolarEdge):

    def __init__(self, offset=False, *args, **kwargs):
        self.model = f"Meter{offset + 1}"
        self.wordorder = Endian.BIG

        super().__init__(*args, **kwargs)

        self.offset = METER_REGISTER_OFFSETS[offset]
        self.registers = {
            "c_manufacturer": (0x9cbb + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Manufacturer", "", 1),
            "c_model": (0x9ccb + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Model", "", 1),
            "c_option": (0x9cdb + self.offset, 8, registerType.HOLDING, registerDataType.STRING, str, "Mode", "", 1),
            "c_version": (0x9ce3 + self.offset, 8, registerType.HOLDING, registerDataType.STRING, str, "Version", "", 1),
            "c_serialnumber": (0x9ceb + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Serial", "", 1),
            "c_deviceaddress": (0x9cfb + self.offset, 1, registerType.HOLDING, registerDataType.UINT16, int, "Modbus ID", "", 1),
            "c_sunspec_did": (0x9cfc + self.offset, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec DID", C_SUNSPEC_DID_MAP, 2),
            "c_sunspec_length": (0x9cfd + self.offset, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec Length", "16Bit Words", 2),

            "current": (0x9cfe + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Current", "A", 2),
            "l1_current": (0x9cff + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1 Current", "A", 2),
            "l2_current": (0x9d00 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2 Current", "A", 2),
            "l3_current": (0x9d01 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3 Current", "A", 2),
            "current_scale": (0x9d02 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Current Scale Factor", "", 2),

            "voltage_ln": (0x9d03 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L-N Voltage", "V", 2),
            "l1n_voltage": (0x9d04 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1-N Voltage", "V", 2),
            "l2n_voltage": (0x9d05 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2-N Voltage", "V", 2),
            "l3n_voltage": (0x9d06 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3-N Voltage", "V", 2),
            "voltage_ll": (0x9d07 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L-L Voltage", "V", 2),
            "l12_voltage": (0x9d08 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1-l2 Voltage", "V", 2),
            "l23_voltage": (0x9d09 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2-l3 Voltage", "V", 2),
            "l31_voltage": (0x9d0a + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3-l1 Voltage", "V", 2),
            "voltage_scale": (0x9d0b + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Voltage Scale Factor", "", 2),

            "frequency": (0x9d0c + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Frequency", "Hz", 2),
            "frequency_scale": (0x9d0d + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Frequency Scale Factor", "", 2),

            "power": (0x9d0e + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Power", "W", 2),
            "l1_power": (0x9d0f + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1 Power", "W", 2),
            "l2_power": (0x9d10 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2 Power", "W", 2),
            "l3_power": (0x9d11 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3 Power", "W", 2),
            "power_scale": (0x9d12 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power Scale Factor", "", 2),

            "power_apparent": (0x9d13 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Apparent)", "VA", 2),
            "l1_power_apparent": (0x9d14 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1 Power (Apparent)", "VA", 2),
            "l2_power_apparent": (0x9d15 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2 Power (Apparent)", "VA", 2),
            "l3_power_apparent": (0x9d16 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3 Power (Apparent)", "VA", 2),
            "power_apparent_scale": (0x9d17 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power (Apparent) Scale Factor", "", 2),

            "power_reactive": (0x9d18 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Power (Reactive)", "VAr", 2),
            "l1_power_reactive": (0x9d19 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1 Power (Reactive)", "VAr", 2),
            "l2_power_reactive": (0x9d1a + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2 Power (Reactive)", "VAr", 2),
            "l3_power_reactive": (0x9d1b + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3 Power (Reactive)", "VAr", 2),
            "power_reactive_scale": (0x9d1c + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power (Reactive) Scale Factor", "", 2),

            "power_factor": (0x9d1d + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "Power Factor", "", 2),
            "l1_power_factor": (0x9d1e + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L1 Power Factor", "", 2),
            "l2_power_factor": (0x9d1f + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L2 Power Factor", "", 2),
            "l3_power_factor": (0x9d20 + self.offset, 1, registerType.HOLDING, registerDataType.INT16, int, "L3 Power Factor", "", 2),
            "power_factor_scale": (0x9d21 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Power Factor Scale Factor", "", 2),

            "export_energy_active": (0x9d22 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Exported Energy (Active)", "Wh", 2),
            "l1_export_energy_active": (0x9d24 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Exported Energy (Active)", "Wh", 2),
            "l2_export_energy_active": (0x9d26 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Exported Energy (Active)", "Wh", 2),
            "l3_export_energy_active": (0x9d28 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Exported Energy (Active)", "Wh", 2),
            "import_energy_active": (0x9d2a + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Imported Energy (Active)", "Wh", 2),
            "l1_import_energy_active": (0x9d2c + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Imported Energy (Active)", "Wh", 2),
            "l2_import_energy_active": (0x9d2e + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Imported Energy (Active)", "Wh", 2),
            "l3_import_energy_active": (0x9d30 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Imported Energy (Active)", "Wh", 2),
            "energy_active_scale": (0x9d32 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Energy (Active) Scale Factor", "", 2),

            "export_energy_apparent": (0x9d33 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Exported Energy (Apparent)", "VAh", 3),
            "l1_export_energy_apparent": (0x9d35 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Exported Energy (Apparent)", "VAh", 3),
            "l2_export_energy_apparent": (0x9d37 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Exported Energy (Apparent)", "VAh", 3),
            "l3_export_energy_apparent": (0x9d39 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Exported Energy (Apparent)", "VAh", 3),
            "import_energy_apparent": (0x9d3b + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Imported Energy (Apparent)", "VAh", 3),
            "l1_import_energy_apparent": (0x9d3d + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Imported Energy (Apparent)", "VAh", 3),
            "l2_import_energy_apparent": (0x9d3f + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Imported Energy (Apparent)", "VAh", 3),
            "l3_import_energy_apparent": (0x9d41 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Imported Energy (Apparent)", "VAh", 3),
            "energy_apparent_scale": (0x9d43 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Energy (Apparent) Scale Factor", "", 3),

            "import_energy_reactive_q1": (0x9d44 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Imported Energy (Reactive) Quadrant 1", "VArh", 3),
            "l1_import_energy_reactive_q1": (0x9d46 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Imported Energy (Reactive) Quadrant 1", "VArh", 3),
            "l2_import_energy_reactive_q1": (0x9d48 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Imported Energy (Reactive) Quadrant 1", "VArh", 3),
            "l3_import_energy_reactive_q1": (0x9d4a + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Imported Energy (Reactive) Quadrant 1", "VArh", 3),
            "import_energy_reactive_q2": (0x9d4c + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Imported Energy (Reactive) Quadrant 2", "VArh", 3),
            "l1_import_energy_reactive_q2": (0x9d4e + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Imported Energy (Reactive) Quadrant 2", "VArh", 3),
            "l2_import_energy_reactive_q2": (0x9d50 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Imported Energy (Reactive) Quadrant 2", "VArh", 3),
            "l3_import_energy_reactive_q2": (0x9d52 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Imported Energy (Reactive) Quadrant 2", "VArh", 3),
            "export_energy_reactive_q3": (0x9d54 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Exported Energy (Reactive) Quadrant 3", "VArh", 3),
            "l1_export_energy_reactive_q3": (0x9d56 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Exported Energy (Reactive) Quadrant 3", "VArh", 3),
            "l2_export_energy_reactive_q3": (0x9d58 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Exported Energy (Reactive) Quadrant 3", "VArh", 3),
            "l3_export_energy_reactive_q3": (0x9d5a + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Exported Energy (Reactive) Quadrant 3", "VArh", 3),
            "export_energy_reactive_q4": (0x9d5c + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Total Exported Energy (Reactive) Quadrant 4", "VArh", 3),
            "l1_export_energy_reactive_q4": (0x9d5e + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L1 Exported Energy (Reactive) Quadrant 4", "VArh", 3),
            "l2_export_energy_reactive_q4": (0x9d60 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L2 Exported Energy (Reactive) Quadrant 4", "VArh", 3),
            "l3_export_energy_reactive_q4": (0x9d62 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "L3 Exported Energy (Reactive) Quadrant 4", "VArh", 3),
            "energy_reactive_scale": (0x9d64 + self.offset, 1, registerType.HOLDING, registerDataType.SCALE, int, "Energy (Reactive) Scale Factor", "", 3)
        }

class StorEdge(SolarEdge):
    
    def __init__(self, *args, **kwargs):
        self.model = "StorEdge"
        self.wordorder = Endian.LITTLE

        super().__init__(*args, **kwargs)

        self.registers = {
            "export_control_mode": (0xe000, 1, registerType.HOLDING, registerDataType.UINT16, int, "Export Control Mode", EXPORT_CONTROL_MODE_MAP, 1),
            "export_control_limit_mode": (0xe001, 1, registerType.HOLDING, registerDataType.UINT16, int, "Export Control Limit Mode", EXPORT_CONTROL_LIMIT_MAP, 1),
            "export_control_site_limit": (0xe002, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Export Control Site Limit", "", 1),
            
            "storedge_control_mode": (0xe004, 1, registerType.HOLDING, registerDataType.UINT16, int, "StorEdge Control Mode", STOREDGE_CONTROL_MODE, 1),
            "storedge_ac_charge_policy": (0xe005, 1, registerType.HOLDING, registerDataType.UINT16, int, "StorEdge AC Charge Policy", STOREDGE_AC_CHARGE_POLICY, 1),
            "storedge_ac_charge_limit": (0xe006, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "StorEdge AC Charge Limit (kWh or %)", "", 1),
            "storedge_backup_reserved": (0xe008, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "StorEdge Backup Reserved (%)", "", 1),

            "storedge_remote_default_command_mode": (0xe00a, 1, registerType.HOLDING, registerDataType.UINT16, int, "StorEdge Default Charge Mode", STOREDGE_CHARGE_DISCHARGE_MODE, 1),
            "storedge_remote_command_timeout": (0xe00b, 2, registerType.HOLDING, registerDataType.UINT32, int, "StorEdge Remote Command Timeout", "", 1),
            "storedge_remote_command_mode": (0xe00d, 1, registerType.HOLDING, registerDataType.UINT16, int, "StorEdge Remote Command Mode", STOREDGE_CHARGE_DISCHARGE_MODE, 1),
            "storedge_remote_charge_limit": (0xe00e, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "StorEdge Remote Command Charge Limit", "", 1),
            "storedge_remote_discharge_limit": (0xe010, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "StorEdge Remote Command Discharge Limit", "", 1),
        }

class Battery(SolarEdge):

    def __init__(self, offset=False, *args, **kwargs):
        self.model = f"Battery{offset + 1}"
        self.wordorder = Endian.LITTLE

        super().__init__(*args, **kwargs)

        self.offset = BATTERY_REGISTER_OFFSETS[offset]
        self.registers = {
            "c_manufacturer": (0xe100 + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Manufacturer", "", 1),
            "c_model": (0xe110 + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Model", "", 1),
            "c_version": (0xe120 + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Version", "", 1),
            "c_serialnumber": (0xe130 + self.offset, 16, registerType.HOLDING, registerDataType.STRING, str, "Serial", "", 1),
            "c_deviceaddress": (0xe140 + self.offset, 1, registerType.HOLDING, registerDataType.UINT16, int, "Modbus ID", "", 1),
            "c_sunspec_did": (0xe141 + self.offset, 1, registerType.HOLDING, registerDataType.UINT16, int, "SunSpec DID", "", 1),

            "rated_energy": (0xe142 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Rated Energy", "Wh", 2),
            "maximum_charge_continuous_power": (0xe144 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Charge Continuous Power", "W", 2),
            "maximum_discharge_continuous_power": (0xe146 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Discharge Continuous Power", "W", 2),
            "maximum_charge_peak_power": (0xe148 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Charge Peak Power", "W", 2),
            "maximum_discharge_peak_power": (0xe14a + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Discharge Peak Power", "W", 2),

            "average_temperature": (0xe16c + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Average Temperature", "°C", 2),
            "maximum_temperature": (0xe16e + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Temperature", "°C", 2),

            "instantaneous_voltage": (0xe170 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Instantaneous Voltage", "V", 2),
            "instantaneous_current": (0xe172 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Instantaneous Current", "A", 2),
            "instantaneous_power": (0xe174 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Instantaneous Power", "W", 2),

            "lifetime_export_energy_counter": (0xe176 + self.offset, 4, registerType.HOLDING, registerDataType.UINT64, int, "Total Exported Energy", "Wh", 2),
            "lifetime_import_energy_counter": (0xe17A + self.offset, 4, registerType.HOLDING, registerDataType.UINT64, int, "Total Imported Energy", "Wh", 2),

            "maximum_energy": (0xe17e + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Maximum Energy", "Wh", 2),
            "available_energy": (0xe180 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "Available Energy", "Wh", 2),

            "soh": (0xe182 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "State of Health (SOH)", "%", 2),
            "soe": (0xe184 + self.offset, 2, registerType.HOLDING, registerDataType.SEFLOAT, float, "State of Energy (SOE)", "%", 2),

            "status": (0xe186 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Status", BATTERY_STATUS_MAP, 2),
            "status_internal": (0xe188 + self.offset, 2, registerType.HOLDING, registerDataType.UINT32, int, "Internal Status", BATTERY_STATUS_MAP, 2),

            "event_log": (0xe18a + self.offset, 2, registerType.HOLDING, registerDataType.UINT16, int, "Event Log", "", 2),
            "event_log_internal": (0xe192 + self.offset, 2, registerType.HOLDING, registerDataType.UINT16, int, "Internal Event Log", "", 2),
        }
