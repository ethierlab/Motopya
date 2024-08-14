#!/usr/bin/env python
import time as t

from ads1015 import ADS1015

CHANNELS = ["in0/ref", "in1/ref", "in2/ref"]

ads1015 = ADS1015()
chip_type = ads1015.detect_chip_type()

ads1015.set_mode("single")
ads1015.set_programmable_gain(2.048)

if chip_type == "ADS1015":
    ads1015.set_sample_rate(1600)
else:
    ads1015.set_sample_rate(860)

reference = ads1015.get_reference_voltage()

latest_force = 0
data = pd.DataFrame(columns=["timestamps", "forces"])
last_move_time = time.time()
initial_time = None

# print("Reference voltage: {:6.3f}v \n".format(reference))

try:
    while True:
        for channel in CHANNELS:
            value = ads1015.get_compensated_voltage(
                channel=channel, reference_voltage=reference
            )
            latest_force = value
            last_move_time = t.time()

        time.sleep(0.001)

except KeyboardInterrupt:
    pass


def get_latest_angle():
    return latest_angle

def get_latest():
    return latest_angle, last_move_time

def get_data():
    return data

def clear_data():
    global angles, timestamps, data
    data = pd.DataFrame(columns=["timestamps", "angles"])


