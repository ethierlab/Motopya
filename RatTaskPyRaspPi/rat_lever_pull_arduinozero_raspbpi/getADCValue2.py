#!/usr/bin/env python
import time

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
print("Getting value in python file")
value = ads1015.get_compensated_voltage(
                channel=CHANNELS[0], reference_voltage=reference
            )
print("Value: ", value)


def getValue():
    try:
        # for channel in CHANNELS:
            # value = ads1015.get_compensated_voltage(
                # channel=channel, reference_voltage=reference
            # )
            # # print("{}: {:6.3f}v".format(channel, value))

        # print("")
        # time.sleep(0.1)
        value = ads1015.get_compensated_voltage(
                channel=CHANNELS[0], reference_voltage=reference
            )
        print("Value3333: ", value)
        return value

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error occured: {e}")
        return 0
