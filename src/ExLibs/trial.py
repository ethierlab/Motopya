import time as t
import numpy as np
from collections import deque
import pandas as pd
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO

from ExLibs.feeder import  gpio_feed
from ExLibs.clock import clock

STATE_IDLE = 0
STATE_TRIAL_INIT = 1 #probably not necessary
STATE_TRIAL_STARTED = 2
STATE_HOLD = 3
STATE_SUCCESS = 4
STATE_FAILURE = 5
STATE_POST_TRIAL = 6
STATE_PARAM_UPDATE = 7
STATE_INTER_TRIAL = 8
STATE_SESSION_END = 9

CURRENT_STATE = STATE_IDLE
NEXT_STATE = CURRENT_STATE


class Trial():
    def __init__(self, init_threshold, hit_duration, hit_threshold, hold_time,
                 post_trial_duration, iniBaseline,gain, drop_tolerance, session_start, reference_time, input_device):
        
        self.init_threshold = init_threshold
        self.hit_duration = hit_duration
        self.hit_threshold = hit_threshold
        self.hold_time = hold_time
        self.post_trial_duration = post_trial_duration
        self.iniBaseline = iniBaseline
        self.gain = gain
        self.drop_tolerance = drop_tolerance
        self.session_start = session_start
        self.peak_value = 0
        self.reference_time = reference_time
        self.success = False
        self.trial_running = True
        self.NEXT_STATE = STATE_TRIAL_STARTED
        self.post_trial_start = None
        self.finished = False
        self.trial_stats = {}
        self.last_trial_end_time = 0
        self.input_device = input_device
        
    def run(self):
        print("Trial started")
        while self.trial_running:
            self.trial_logic()
            t.sleep(0.001)
        print("Trial ended")
            
    def stop(self):
        self.trial_running = False
        
    def trial_logic(self):
        current_time = clock.time()
        
        latest_value, latest_time = self.input_device.get_latest()
        
        self.peak_value = max(latest_value, self.peak_value)
        self.last_move_time = current_time
        CURRENT_STATE = self.NEXT_STATE
        
        if CURRENT_STATE == STATE_TRIAL_STARTED:
            # Check for trial timeout
            if current_time - self.reference_time >= self.hit_duration and latest_value < self.hit_threshold:
                self.NEXT_STATE = STATE_FAILURE
            # Check for hit threshold
            elif latest_value <= self.peak_value - self.drop_tolerance:
                self.NEXT_STATE = STATE_FAILURE
            elif latest_value >= self.hit_threshold:
                self.hit_start_time = current_time
                self.NEXT_STATE = STATE_HOLD
        elif CURRENT_STATE == STATE_HOLD:
            if latest_value < self.hit_threshold:
                self.NEXT_STATE = STATE_TRIAL_STARTED
            elif current_time - self.hit_start_time >= self.hold_time:
                self.NEXT_STATE = STATE_SUCCESS
        elif CURRENT_STATE == STATE_SUCCESS:
            print("SUCCESS")
            self.success = True
            self.last_trial_end_time = current_time
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_FAILURE:
            print("FAIL")
            self.last_trial_end_time = current_time
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_POST_TRIAL:
            if self.post_trial_start is None:
                self.post_trial_start = current_time
            elif current_time - self.post_trial_start >= self.post_trial_duration:
                self.last_trial_end_time = current_time
                self.record_trial()
                self.trial_running = False
                self.finished = True

    def get_trial_data(self):
        return self.trial_stats

    def is_finished(self):
        return self.finished
    
    def is_trial_started(self):
        return self.trial_started
    
    def get_last_values(self):
        return self.last_hit_thresh, self.last_hold_time

    def record_trial(self):
        trial_data = self.input_device.get_data()
        timestamps = np.array(trial_data["timestamps"]) - int(self.reference_time * 1000)
        index = 0
        if len(timestamps) > 0:  
            index = np.where(timestamps >= -1000)[0][0]
        trial_data = pd.DataFrame({'timestamps': timestamps[index:], 'values': trial_data["values"][index:]})
        
        self.trial_stats = {}
        self.trial_stats["start_time"] = round(self.reference_time - self.session_start, 2)
        self.trial_stats["init_thresh"] = self.init_threshold
        self.trial_stats["hit_thresh"] = self.hit_threshold
        self.trial_stats["Force"] = trial_data
        self.trial_stats["hold_time"] = self.hold_time * 1000
        self.trial_stats["duration"] = round(self.last_trial_end_time - self.reference_time, 2)
        self.trial_stats["success"] = self.success
        self.trial_stats["peak"] = self.peak_value

    def get_end(self):
        return self.last_trial_end_time
    
    def get_success(self):
        return self.success