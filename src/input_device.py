from abc import ABC, abstractmethod

import time as t

from ads1015 import ADS1015

from ExLibs.encoder import RotaryEncoder2
import pandas as pd


class InputDevice(ABC):
    
    def __init__(self, gain):
        self.gain = gain
        self.data = pd.DataFrame(columns=["timestamps", "values"])
        
    @abstractmethod
    def get_latest(self):
        pass
    
    @abstractmethod
    def get_latest_value(self):
        pass
    
    def get_data(self):
        return self.data
    
    def clear_data(self):
        self.data = pd.DataFrame(columns=["timestamps", "values"])
    
    def modify_gain(self, gain):
        self.gain = gain
    

class Lever(InputDevice):
    def __init__(self, gain):
        super().__init__(gain)
        self.CHANNELS = ["in0/ref", "in1/ref", "in2/ref"]
        self.ads1015 = ADS1015()
        self.chip_type = self.ads1015.detect_chip_type()

        self.ads1015.set_mode("single")
        self.ads1015.set_programmable_gain(2.048)

        if self.chip_type == "ADS1015":
            self.ads1015.set_sample_rate(1600)
        else:
            self.ads1015.set_sample_rate(860)

        self.reference = self.ads1015.get_reference_voltage()

        self.latest_force = 0
        
        self.latest_move_time = t.time()
        self.initial_time = None
    
    def get_latest(self):
        return self.latest_force, self.latest_move_time
    
    def get_latest_value(self):
        return self.latest_force

        
        
    def update_value(self):
    
        timestamp = int(t.time() * 1000)  # Get current time in milliseconds
        try:
            self.latest_force = self.ads1015.get_compensated_voltage(
                channel=self.CHANNELS[0], reference_voltage=self.reference
            ) * self.gain
    #         print("In lever", self.latest_force)
        except OSError:
            print("ADS disconnected")
            return
        self.latest_move_time = t.time()
        
        new_data = pd.DataFrame({"timestamps": [timestamp], "values": [self.latest_force]})
        self.data = pd.concat([self.data, new_data], ignore_index = True)
        if len(self.data) > 3000:
            self.data = self.data.iloc[-3000:]
        
        

class RotaryEncoder(InputDevice):
    
    def __init__(self, gain):
        super().__init__(gain)
        self.encoder_a = 20  
        self.encoder_b = 21  

        self.latest_angle = 0
        self.data = pd.DataFrame(columns=["timestamps", "values"])
        self.latest_move_time = t.time()
        self.initial_time = None
        self.encoder = None
        
    def setup_encoder(self):
        self.initial_time = t.time()
        self.encoder = RotaryEncoder2(self.encoder_a, self.encoder_b, max_steps=360,half_step=True)
        self.encoder.when_rotated = self.rotary_changed
        
    def rotary_changed(self):
        self.latest_angle = self.encoder.steps * self.gain  # Get the current angle with 0.5 degree resolution
#         print("In rotary", self.latest_angle)
        timestamp = int(t.time() * 1000)  # Get current time in milliseconds
        new_data = pd.DataFrame({"timestamps": [timestamp], "values": [self.latest_angle]})
        self.data = pd.concat([self.data, new_data], ignore_index = True)
        self.latest_move_time = t.time()
        if len(self.data) > 3000:
            self.data = self.data.iloc[-3000:]
        
    def get_latest_value(self):
        return self.latest_angle

    def get_latest(self):
        return self.latest_angle, self.latest_move_time
