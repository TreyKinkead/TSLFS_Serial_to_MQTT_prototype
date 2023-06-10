import argparse
import json
import paho.mqtt.client as mqtt
import serial
import signal
import struct
import time

DEFAULT_SERIAL_PORT = '/dev/cu.usbserial-DM022RIJ'
DEFAULT_BAUD_RATE = 9600

DEFAULT_SEND_PERIOD = 5 # seconds, can be fractional

DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_KEEPALIVE = 60 # seconds
DEFAULT_MQTT_TOPIC = "dt/device/flatsat"
DEFAULT_MQTT_CLIENT_ID = "flatsat-serial-to-mqtt"

# incoming data format
START_OF_DATA_FRAME = b'\x58\x58'
END_OF_DATA_FRAME =  b'\x40\x0a'
END_AND_START_OF_DATA_FRAME = END_OF_DATA_FRAME + START_OF_DATA_FRAME

# incoming data fields - those starting with '_' used for framing, etc.
# and will be ignored as telemetry data
incoming_data_fields = [
    # start, size, struct format, name
    (0,1,'B','_sig_88_1'),
    (1,1,'B','_sig_88_2'),
    (2,1,'B','_tslfs_id'),
    (3,1,'B','eeprom_count'),
    (4,2,'<H','Vcc'),
    (6,2,'<H','Icc'),
    (8,2,'<H','Vbat'),
    (10,2,'<H','Lux'),
    (12,2,'<H','a_temp'),
    (14,2,'<H','ir'),
    (16,2,'<H','pot'),
    (18,2,'<H','gnd'),
    (20,1,'B','d_temp_lsB'),
    (21,1,'B','d_temp_msB'),
    # 22 TBD
    (24,2,'<H','ens210_rh_pct'),    # ENS210
    (26,2,'<H','ens210_temp_C'),    # ENS210
    (28,4,'f','bmp280_pressure_Pa'),
    (32,4,'f','bmp280_altitude_m'), # BMP280 altitude m
    (36,4,'f','bmp280_temp_C'),     # BMP280 temp C
    (40,2,'<H','imu_temp'),         # raw value needs formula
    # 42 TBD
    (44,2,'<h','gx'),
    (46,2,'<h','gy'),
    (48,2,'<h','gz'),
    (50,2,'<h','gyx'),
    (52,2,'<h','gyy'),
    (54,2,'<h','gyz'),
    (56,2,'<h','mx'),
    (58,2,'<h','my'),
    (60,2,'<h','mz'),
    (62,1,'B','_tail_1'),
    (63,1,'B','_tail_2'),
]

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Reads serial FlatSat data and sends to MQTT broker.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--serial', metavar='DEVICE',
        default=DEFAULT_SERIAL_PORT,
        help="serial port device name to read")
    parser.add_argument(
        '--baudrate', metavar='N',
        type=int,
        default=DEFAULT_BAUD_RATE,
        help="serial baud rate")
    parser.add_argument(
        '--send_period', metavar='SECONDS',
        type=float,
        default=DEFAULT_SEND_PERIOD,
        help="only send every N seconds")
    parser.add_argument(
        '--host', metavar='SERVER',
        type=str,
        required=True,
        help="MQTT broker hostname or IP address")
    parser.add_argument(
        '--port', metavar='PORT',
        type=int,
        default=DEFAULT_MQTT_PORT,
        help="MQTT broker port")
    parser.add_argument(
        '--client_id', metavar='ID',
        type=str,
        default=DEFAULT_MQTT_CLIENT_ID,
        help="MQTT broker hostname or IP address")
    parser.add_argument(
        '--keepalive', metavar='SECONDS',
        type=int,
        default=DEFAULT_MQTT_KEEPALIVE,
        help="MQTT keep alive time in seconds")
    parser.add_argument(
        '--username', metavar='NAME',
        type=str,
        required=True,
        help="username")
    parser.add_argument(
        '--password', metavar='PASSWORD',
        type=str,
        required=True,
        help="password")
    parser.add_argument(
        '--topic', metavar='TOPIC',
        default=DEFAULT_MQTT_TOPIC,
        help="password")
    parser.add_argument(
        '-n', '--dryrun',
        action='store_true',
        default=False,
        help="read serial but don't send to MQTT broker")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help="verbose output")

    return parser.parse_args()


def parse_serial_fields(incoming_data_fields, line_buffer):
    data = {}
    for field_tuple in incoming_data_fields:
        slice_start = field_tuple[0]
        slice_length = field_tuple[1]
        slice_stop = slice_start + slice_length
        format = field_tuple[2]
        name = field_tuple[3]
        the_bytes = line_buffer[slice_start:slice_stop]
        val_bytes = struct.unpack(format, the_bytes)
        assert len(val_bytes) == 1 # it's a list
        val = val_bytes[0]
        if not name.startswith('_'):
            data[name] = val
    return data


def fixup_data(data):
    fixed_data = {}

    # voltages
    fixed_data['Vcc_V'] = data['Vcc']*3.3/1023
    fixed_data['Vbat_V'] = data['Vbat']*6.6/1023
    fixed_data['pot_V'] = data['pot']*3.3/1023
    fixed_data['gnd_V'] = data['gnd']*3.3/1023

    # current
    fixed_data['Icc_mA'] = data['Icc']*330/1023

    #  temperatures
    fixed_data['analog_temp_C'] = (data['a_temp']*3.3/10.23)-50
    fixed_data['ens210_temp_C'] = data['ens210_temp_C']
    data['d_temp_lsB'] = 1 if data['d_temp_lsB'] else 0 # want either 1 or 0
    fixed_data['d_temp_C'] = data['d_temp_msB'] + data['d_temp_lsB'] * 0.5
    fixed_data['imu_temp_C'] = data['imu_temp'] / 100.0 # investigate further
    fixed_data['bmp280_temp_C'] = data['bmp280_temp_C']

    # miscellaneous
    fixed_data['bmp280_pressure_kPa'] = data['bmp280_pressure_Pa'] / 1000.0
    fixed_data['bmp280_altitude_m'] = data['bmp280_altitude_m']
    fixed_data['ens210_rh_pct'] = data['ens210_rh_pct']
    fixed_data['lux'] = data['Lux']
    fixed_data['ir'] = data['ir']

    # acceleration
    fixed_data['accel_x_g'] = data['gx']
    fixed_data['accel_y_g'] = data['gy']
    fixed_data['accel_z_g'] = data['gz']

    # gyroscope
    fixed_data['gyro_x'] = data['gyx']
    fixed_data['gyro_y'] = data['gyy']
    fixed_data['gyro_z'] = data['gyz']

    # magnetic field
    conv_m = 0.1465 # convertion factor for +-4,800uT range 0.6uT, 16bits>0.1465, 14bits>0.2929
    fixed_data['mag_x_uT'] = data['mx'] * conv_m
    fixed_data['mag_y_uT'] = data['my'] * conv_m
    fixed_data['mag_z_uT'] = data['mz'] * conv_m

    return fixed_data


if __name__ == '__main__':

    args = parse_arguments()

    ser = serial.Serial(port=args.serial, baudrate=args.baudrate,
                        timeout=None, exclusive=False)
    print(f"connected to {ser.name}")

    mqtt_client = mqtt.Client(args.client_id)
    mqtt_client.username_pw_set(args.username, args.password)
    mqtt_client.connect(args.host, args.port, args.keepalive)

    # buffer to accumulate serial bytes as read
    line_buffer = b''

    # seconds after which okay to send again
    send_okay_after = 0

    skip_count = 0
    send_count = 0

    # set up SIGINT handler
    do_process = True
    def sig_interrupt_handler(signal, frame):
        global do_process
        do_process = False
    signal.signal(signal.SIGINT, sig_interrupt_handler)

    while (do_process):
        a_byte = ser.read() # read bytes array of length
        line_buffer += bytes(a_byte)
        # look for the end of one frame and the start of another
        if line_buffer[-(len(END_AND_START_OF_DATA_FRAME)):] == END_AND_START_OF_DATA_FRAME:
            # starting to look like a match, but need to check
            # that it starts with the expected framing characters
            if line_buffer[:len(START_OF_DATA_FRAME)] == START_OF_DATA_FRAME:
                # a match!
                now = time.time()
                if now >= send_okay_after:
                    send_okay_after = now + args.send_period
                    print(f"\nskipped {skip_count} records")
                    skip_count = 0
                    data = parse_serial_fields(incoming_data_fields, line_buffer)
                    if args.verbose:
                        print("SERIAL data:")
                        print(data)

                    fixed_data = fixup_data(data)

                    mqtt_payload = json.dumps(fixed_data)
                    if args.verbose:
                        print("MQTT payload:")
                        print(mqtt_payload)
                    if not args.dryrun:
                        mqtt_client.publish(args.topic, payload=mqtt_payload)
                        send_count += 1
                        print(f"total records sent: {send_count}")
                else:
                    skip_count += 1
            # keep the two starting bytes only (at end of buffer)
            line_buffer = line_buffer[-2:]
