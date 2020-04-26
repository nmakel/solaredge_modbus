# solaredge_modbus

solaredge_modbus is a python library that collects data from SolarEdge power inverters over Modbus or ModbusTCP.

## Installation

To install, either clone this project and install using `setuptools`:

```python3 setup.py install```

or install the package from PyPi:

```pip3 install solaredge_modbus```

## Usage

The script `example.py` provides a minimal example of connecting to and displaying all registers from a SolarEdge power inverter over ModbusTCP.

```
usage: example.py [-h] [--unit UNIT] host port

positional arguments:
  host         ModbusTCP address
  port         ModbusTCP port

optional arguments:
  -h, --help   show this help message and exit
  --unit UNIT  Modbus unit
```

Output:

```
{
    'c_model': 'SE3500H-RW000BNN4',
    'c_version': '0004.0009.0030',
    'c_serialnumber': '123ABC12',
    'c_deviceaddress': 1,
    'c_sunspec_did': 101,
    'current': 895,
    'p1_current': 895,
    'p2_current': False,
    'p3_current': False,
    'current_scale': -2,
    'p1_voltage': 2403,
    'p2_voltage': False,
    'p3_voltage': False,
    'p1n_voltage': False,
    'p2n_voltage': False,
    'p3n_voltage': False,
    'voltage_scale': -1,
    'power_ac': 21413,
    'power_ac_scale': -1, 
    'frequency': 50003,
    'frequency_scale': -3,
    'power_apparent': 21479,
    'power_apparent_scale': -1,
    'power_reactive': 16859,
    'power_reactive_scale': -2,
    'power_factor': 9969,
    'power_factor_scale': -2,
    'energy_total': 3466757,
    'energy_total_scale': 0,
    'current_dc': 5678,
    'current_dc_scale': -3,
    'voltage_dc': 3826,
    'voltage_dc_scale': -1,
    'power_dc': 21726,
    'power_dc_scale': -1,
    'temperature': 4979,
    'temperature_scale': -2,
    'status': 4,
    'vendor_status': 0
}

SolarEdge(10.0.98.247:1502, unit=0x1):

Registers:
    Model: SE3500H-RW000BNN4
    Type: Single Phase
    Version: 0004.0009.0030
    Serial: 123ABC12
    Status: Producing
    Temperature: 49.79°C
    Current: 8.93A
    Voltage: 240.20V
    Power: 2141.80W
    Frequency: 50.00Hz
    Power (Apparent): 2149.60VA
    Power (Reactive): 183.20VA
    Power Factor: 99.69%
    Total Energy: 3466757Wh
    DC Current: 5.68A
    DC Voltage: 382.50V
    DC Power: 2173.50W
```

## Contributing

Contributions are more than welcome.