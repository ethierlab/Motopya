from abc import ABC, abstractmethod

import time as t

from ads1015 import ADS1015

from ExLibs.encoder import RotaryEncoder2

import pandas as pd


class InputDevice(ABC):
    
    def __init__(self, gain):
        self.gain = gain
        self.data = pd.DataFrame(columns=["timestamps", "values"])
        self.latest_value = 0
        self.latest_move_time = t.time()
        self.initial_time = None
        
    def get_latest(self):
        return self.latest_value, self.latest_move_time
    
    def get_latest_value(self):
        return self.latest_value
    
    def update_data(self, timestamp, value):
        new_data = pd.DataFrame({"timestamps": [timestamp], "values": [self.latest_value]})
        
        if self.data.empty:
            self.data = new_data
            return
        self.data = pd.concat([self.data, new_data], ignore_index = True)
        if len(self.data) > 5000:
            self.data = self.data.iloc[-3000:]
            
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


    def update_value(self):
    
        timestamp = int(t.time() * 1000)  # Get current time in milliseconds
        try:
            self.latest_value = round(self.ads1015.get_compensated_voltage(
                channel=self.CHANNELS[0], reference_voltage=self.reference
            ) * self.gain, 2)
    #         print("In lever", self.latest_value)
        except OSError:
            print("ADS disconnected")
            return
        self.latest_move_time = t.time()
        
        self.update_data(timestamp, self.latest_value)
        
        
        
        

class RotaryEncoder(InputDevice):
    def __init__(self, gain):
        super().__init__(gain)
        self.encoder_a = 20  
        self.encoder_b = 21  

        self.latest_value = 0
        self.data = pd.DataFrame(columns=["timestamps", "values"])
        self.encoder = None
        
    def setup_encoder(self):
        self.initial_time = t.time()
        self.encoder = RotaryEncoder2(self.encoder_a, self.encoder_b, max_steps=360,half_step=True)
        self.encoder.when_rotated = self.rotary_changed
        
    def rotary_changed(self):
        timestamp = int(t.time() * 1000)  # Get current time in milliseconds
        self.latest_value = round(self.encoder.steps * self.gain, 2)  # Get the current angle with 0.5 degree resolution
        
        self.latest_move_time = t.time()
        
        self.update_data(timestamp, self.latest_value)