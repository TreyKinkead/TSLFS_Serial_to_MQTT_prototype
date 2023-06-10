# TSLFS_Serial_to_MQTT

_PROTOTYPE_ [Python](https://www.python.org/) script to read TSL FlatSat data from serial port, process values, sent to [MQTT](https://mqtt.org/) broker.

## Local Setup

## Python
Python 3.10+ is required.

To run, a Python [virtual environment (venv)](https://docs.python.org/3/library/venv.html)
is helpful to isolate the third-party packages (libraries). This only needs to be created once:
```
python3 -m venv .venv
```
... and packages installed:
```
. ./.venv/bin/activate
pip3 install -r requirements.txt
```

### Activate .venv to configure shell environment
This is necessary only once per running shell (terminal) environment (until it is terminated, computer rebooted, etc.).
```
. ./.venv/bin/activate
```
From the configured shell environment, one can then run the Python module as often as desired:
```python3 TSLFS_Serial_to_MQTT.py ...``` _(see below for usage)_.

## Usage

```
% . ./.venv/bin/activate
% python3 TSLFS_Serial_to_MQTT.py -h
usage: TSLFS_Serial_to_MQTT.py [-h] [--serial DEVICE] [--baudrate N] [--send_period SECONDS] --host SERVER [--port PORT] [--client_id ID] [--keepalive SECONDS] --username NAME
                               --password PASSWORD [--topic TOPIC] [-n] [-v]

Reads serial FlatSat data and sends to MQTT broker.

options:
  -h, --help            show this help message and exit
  --serial DEVICE       serial port device name to read (default: /dev/cu.usbserial-DM022RIJ)
  --baudrate N          serial baud rate (default: 9600)
  --send_period SECONDS
                        only send every N seconds (default: 5)
  --host SERVER         MQTT broker hostname or IP address (default: None)
  --port PORT           MQTT broker port (default: 1883)
  --client_id ID        MQTT broker hostname or IP address (default: flatsat-serial-to-mqtt)
  --keepalive SECONDS   MQTT keep alive time in seconds (default: 60)
  --username NAME       username (default: None)
  --password PASSWORD   password (default: None)
  --topic TOPIC         password (default: dt/device/flatsat)
  -n, --dryrun          read serial but don't send to MQTT broker (default: False)
  -v, --verbose         verbose output (default: False)
```

For example:
```
python3 TSLFS_Serial_to_MQTT.py --host <MQTT_HOST> --username <USERNAME> --password <SECRET> --send_period 10 -v
```
...which might output something like:
```
connected to /dev/cu.usbserial-DM022RIJ

skipped 0 records
SERIAL data:
{'eeprom_count': 0, 'Vcc': 1023, 'Icc': 79, 'Vbat': 810, 'Lux': 0, 'a_temp': 220, 'ir': 27, 'pot': 0, 'gnd': 0, 'd_temp_lsB': 0, 'd_temp_msB': 22, 'ens210_rh_pct': 38, 'ens210_temp_C': 22, 'bmp280_pressure_Pa': 75714.0, 'bmp280_altitude_m': 2390.685791015625, 'bmp280_temp_C': 22.5, 'imu_temp': 1517, 'gx': 457, 'gy': 1729, 'gz': 1125, 'gyx': -88, 'gyy': 103, 'gyz': 22, 'mx': -87, 'my': -5, 'mz': -33}
MQTT payload:
{"Vcc_V": 3.3, "Vbat_V": 5.225806451612903, "pot_V": 0.0, "gnd_V": 0.0, "Icc_mA": 25.483870967741936, "analog_temp_C": 20.967741935483872, "ens210_temp_C": 22, "d_temp_C": 22.0, "imu_temp_C": 15.17, "bmp280_temp_C": 22.5, "bmp280_pressure_kPa": 75.714, "bmp280_altitude_m": 2390.685791015625, "ens210_rh_pct": 38, "lux": 0, "ir": 27, "accel_x_g": 457, "accel_y_g": 1729, "accel_z_g": 1125, "gyro_x": -88, "gyro_y": 103, "gyro_z": 22, "mag_x_uT": -12.7455, "mag_y_uT": -0.7324999999999999, "mag_z_uT": -4.834499999999999}
total records sent: 1

skipped 16 records
SERIAL data:
{'eeprom_count': 17, 'Vcc': 1023, 'Icc': 78, 'Vbat': 808, 'Lux': 0, 'a_temp': 220, 'ir': 28, 'pot': 0, 'gnd': 0, 'd_temp_lsB': 0, 'd_temp_msB': 22, 'ens210_rh_pct': 38, 'ens210_temp_C': 22, 'bmp280_pressure_Pa': 75710.0, 'bmp280_altitude_m': 2391.108642578125, 'bmp280_temp_C': 22.5, 'imu_temp': 1523, 'gx': 460, 'gy': 1738, 'gz': 1128, 'gyx': -101, 'gyy': 93, 'gyz': 25, 'mx': -86, 'my': -12, 'mz': -28}
MQTT payload:
{"Vcc_V": 3.3, "Vbat_V": 5.212903225806451, "pot_V": 0.0, "gnd_V": 0.0, "Icc_mA": 25.161290322580644, "analog_temp_C": 20.967741935483872, "ens210_temp_C": 22, "d_temp_C": 22.0, "imu_temp_C": 15.23, "bmp280_temp_C": 22.5, "bmp280_pressure_kPa": 75.71, "bmp280_altitude_m": 2391.108642578125, "ens210_rh_pct": 38, "lux": 0, "ir": 28, "accel_x_g": 460, "accel_y_g": 1738, "accel_z_g": 1128, "gyro_x": -101, "gyro_y": 93, "gyro_z": 25, "mag_x_uT": -12.598999999999998, "mag_y_uT": -1.758, "mag_z_uT": -4.101999999999999}
total records sent: 2

...
```

Note, CTRL-C (SigINT) to exit the program.

## TODO
- Default serial port for other platforms. Currently MAC-specific `/dev/cu.usbserial-DM022RIJ`.
- Determine / implement real version with easier install / run for end users.
