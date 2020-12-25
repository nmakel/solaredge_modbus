# solaredge_modbus

solaredge_modbus is a python library that collects data from SolarEdge inverters over Modbus RTU or Modbus TCP.

## Installation

To install, either clone this project and install using `setuptools`:

```python3 setup.py install```

or install the package from PyPi:

```pip3 install solaredge_modbus```

## Usage

The script `example.py` provides a minimal example of connecting to and displaying all registers from a SolarEdge power inverter over Modbus TCP.

```
usage: example.py [-h] [--timeout TIMEOUT] [--unit UNIT] [--json] host port

positional arguments:
  host               Modbus TCP address
  port               Modbus TCP port

optional arguments:
  -h, --help         show this help message and exit
  --timeout TIMEOUT  Connection timeout
  --unit UNIT        Modbus device address
  --json             Output as JSON
```

Output:

```
Inverter(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1):

Registers:
    Manufacturer: SolarEdge
    Model: SE3500H-RW000BNN4
    Type: Single Phase Inverter
    Version: 0004.0009.0030
    Serial: 123ABC12
    Status: Producing
    Temperature: 49.79°C
    Current: 8.93A
    Voltage: 240.20V
    Frequency: 50.00Hz
    Power: 2141.80W
    Power (Apparent): 2149.60VA
    Power (Reactive): 183.20VAr
    Power Factor: 99.69%
    Total Energy: 3466757Wh
    DC Current: 5.68A
    DC Voltage: 382.50V
    DC Power: 2173.50W
```

Passing `--json` returns:

```
{
    "c_manufacturer": "SolarEdge",
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
    'frequency': 50003,
    'frequency_scale': -3,
    'power_ac': 21413,
    'power_ac_scale': -1, 
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
```

Note that if kWh meters or batteries are connected to your inverter, these will also be presented in the JSON output.

A second script, `example_influxdb.py` provides an example InfluxDB writer. It connects to an inverter over Modbus TCP, and writes inverter, battery and meter values to an InfluxDB every second.


```
usage: example_influxdb.py [-h] [--timeout TIMEOUT] [--unit UNIT] [--interval INTERVAL] [--influx_host INFLUX_HOST] [--influx_port INFLUX_PORT] [--influx_db INFLUX_DB]
                           [--influx_user INFLUX_USER] [--influx_pass INFLUX_PASS]
                           host port

positional arguments:
  host                  Modbus TCP address
  port                  Modbus TCP port

optional arguments:
  -h, --help            show this help message and exit
  --timeout TIMEOUT     Connection timeout
  --unit UNIT           Modbus device address
  --interval INTERVAL   Update interval
  --influx_host INFLUX_HOST
                        InfluxDB host
  --influx_port INFLUX_PORT
                        InfluxDB port
  --influx_db INFLUX_DB
                        InfluxDB database
  --influx_user INFLUX_USER
                        InfluxDB username
  --influx_pass INFLUX_PASS
                        InfluxDB password
```

### Connecting

If you wish to use Modbus TCP the following parameters are relevant:

`host = IP or DNS name of your Modbus TCP device, required`  
`port = TCP port of the Modbus TCP device, required`  
`unit = Modbus device address, default=1, optional`

While if you are using a Modbus RTU connection you can specify:

`device = path to serial device, e.g. /dev/ttyUSB0, required`  
`baud = baud rate of your device, defaults to product default, optional`  
`unit = Modbus device address, defaults to 1, optional`

Connecting to the inverter:

```
    >>> import solaredge_modbus

    # Inverter over Modbus TCP
    >>> inverter = solaredge_modbus.Inverter(host="10.0.0.123", port=1502)
    
    # Inverter over Modbus RTU
    >>> inverter = solaredge_modbus.Inverter(device="/dev/ttyUSB0", baud=115200)
```

Test the connection, remember that only a single connection at a time is allowed:

```
    >>> inverter.connect()
    True

    >>> inverter.connected()
    True
```

While it is not necessary to explicitly call `connect()` before reading registers, you should do so before calling `connected()`. The connection can be closed by calling `disconnect()`.

Printing the class yields basic device parameters:

```
    >>> inverter
    Inverter(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1)
```

### Reading Registers

Reading a single input register by name:

```
    >>> inverter.read("current")
    {
        'current': 895
    }
```

Read all input registers using `read_all()`:

```
    >>> inverter.read_all()
    {
        'c_manufacturer': 'SolarEdge',
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
```

### Register Details

If you need more information about a particular register, to look up the units or enumerations, for example:

```
    >>> inverter.registers["current"]
        # address, length, type, datatype, valuetype, name, unit, batching
        (
            40071, 
            1, 
            <registerType.HOLDING: 2>, 
            <registerDataType.UINT16: 3>, 
            <class 'int'>, 
            'Current', 
            'A', 
            2
        )

    >>> inverter.registers["status"]
        # address, length, type, datatype, valuetype, name, unit, batching
        (
            40107, 
            1, 
            <registerType.HOLDING: 2>, 
            <registerDataType.UINT16: 3>, 
            <class 'int'>, 
            'Status', 
            ['Undefined', 'Off', 'Sleeping', 'Grid Monitoring', 'Producing', 'Producing (Throttled)', 'Shutting Down', 'Fault', 'Standby'], 
            2
        )
```

### Multiple Inverters

If you have multiple inverters connected together over the RS485 bus, you can query the individual inverters using Modbus RTU or Modbus TCP by instantiating multiple inverter objects:

```
    # Master inverter over Modbus TCP
    >>> master = solaredge_modbus.Inverter(host="10.0.0.123", port=1502, unit=1)

    # Second inverter using master's connection
    >>> second = solaredge_modbus.Inverter(parent=master, unit=2)

    # Third inverter
    >>> third = solaredge_modbus.Inverter(parent=master, unit=3)
```

### Meters & Batteries

SolarEdge supports various kWh meters and batteries, and exposes their registers through a set of pre-defined registers on the inverter. The number of supported registers is hard-coded, per the SolarEdge SunSpec implementation, to three meters and two batteries. It is possible to query their registers:

```
    >>> inverter.meters()
    {
        'Meter1': Meter1(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1)
    }

    >>> meter1 = inverter.meters()["Meter1"]
    >>> meter1
    Meter1(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1)

    >>> meter1.read_all()
    {
        'c_manufacturer': 'SolarEdge',
        'c_model': 'PRO380-Mod',
        'c_option': 'Export+Import',
        'c_version': '2.19',
        'c_serialnumber': '12312332',
        'c_deviceaddress': 1,
        'c_sunspec_did': 203,
        'current': -13,
        ...
    }
```

Or similarly for batteries:

```
    >>> inverter.batteries()
    {
        'Battery1': Battery(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1)
    }

    >>> battery1 = inverter.batteries()["Battery1"]
    >>> battery1
    Battery1(10.0.0.123:1502, connectionType.TCP: timeout=1, retries=3, unit=0x1)

    >>> battery1.read_all()
    {
        ...
    }
```

Calling `meters()` or `batteries()` on an inverter object is the recommended way of instantiating their objects. This way, checking for available devices, register offsetting, and sharing of the pymodbus connection is taken care of. If you want to to create a meter or battery object independently, do the following:

```
    # Meter #1 via the existing inverter connection
    >>> meter1 = solaredge_modbus.Meter(parent=inverter, offset=0)

    # Meter #2 over Modbus TCP, without a parent connection
    >>> meter2 = solaredge_modbus.Meter(host="10.0.0.123", port=1502, offset=1)

    # Battery #1 via the existing inverter connection
    >>> battery1 = solaredge_modbus.Battery(parent=inverter, offset=0)

    # Battery #1 over Modbus TCP, without a parent connection
    >>> battery1 = solaredge_modbus.Battery(host="10.0.0.123", port=1502, offset=1)
```

There are two points to consider when doing this. You will need to manually pass the `parent` and `offset` parameters, which take care of sharing an existing Modbus connection, and set the correct register addresses. Use `offset` 0 for the first device, 1 for the second, and 2 for the third. If you do not pass a parent inverter object, you will need to supply connection parameters just like those required by the inverter object. Remember that a second Modbus TCP or Modbus RTU connection will fail when already in use by another inverter, meter, or battery object.

**Note:** as I do not have access to a compatible kWh meter nor battery, this implementation is not thoroughly tested. If you have issues with this functionality, please open a GitHub issue.

## Contributing

Contributions are more than welcome.