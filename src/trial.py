import time as t
from rotary_encoder import get_latest_angle, get_latest, get_data, clear_data, last_move_time
from feeder import  gpio_feed
import numpy as np
from collections import deque
import pandas as pd
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO

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
    def __init__(self, hit_duration, hit_threshold, hold_time, post_duration, iniBaseline,lever_gain, drop_tolerance, session_start, reference_time):
        
        self.hit_duration = hit_duration
        self.hit_threshold = hit_threshold
        self.hold_time = hold_time
        self.iniBaseline = iniBaseline
        self.lever_gain = lever_gain
        self.drop_tolerance = drop_tolerance
        self.peak_value = 0
        self.reference_time = reference_time
        self.success = False
        self.trial_running = True
        self.NEXT_STATE = STATE_TRIAL_STARTED
        
    def run():
        while self.trial_running
            trial_logic()
        
    def trial_logic():
        current_time = t.time()
        
        latest_angle, latest_time = get_latest()
        self.peak_value = max(latest_angle, peak_value)
        self.last_move_time = current_time
        CURRENT_STATE = self.NEXT_STATE
        
        if CURRENT_STATE == STATE_TRIAL_STARTED:
            # Check for trial timeout
            if current_time - self.trial_start_time >= self.hit_duration and latest_angle < self.trial_hit_thresh:
                print("time fail")
                self.NEXT_STATE = STATE_FAILURE
            # Check for hit threshold
            elif latest_angle <= self.peak_value - self.drop_tolerance:
                print("drop fail")
                self.NEXT_STATE = STATE_FAILURE
            elif latest_angle >= self.trial_hit_thresh:
                self.hit_start_time = current_time
                self.NEXT_STATE = STATE_HOLD
        elif CURRENT_STATE == STATE_HOLD:
            if latest_angle < self.trial_hit_thresh:
                self.NEXT_STATE = STATE_TRIAL_STARTED
            elif current_time - self.hit_start_time >= self.trial_hold_time:
                self.NEXT_STATE = STATE_SUCCESS
        elif CURRENT_STATE == STATE_SUCCESS:
            print("Success")
            self.success = True
            self.last_trial_end_time = current_time
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_FAILURE:
            print("Fail")
            self.last_trial_end_time = current_time
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_POST_TRIAL:
            if self.post_trial_start is None:
                print("POST")
                self.post_trial_start = current_time
            elif current_time - self.post_trial_start >= self.post_duration:
                self.record_trial()
                self.trial_running = False

    def get_trial_data():
        return self.trial_stats

    def is_trial_started():
        return self.trial_started
        
    def get_reference_time():
        return self.reference_time
        
    def get_last_values():
        return self.last_hit_thresh, self.last_hold_time

    def record_trial():
        trial_data = get_data()
        timestamps = np.array(trial_data["timestamps"]) - int(self.reference_time * 1000)
        index = np.where(timestamps >= -1000)[0][0]
        trial_data = pd.DataFrame({'timestamps': timestamps[index:], 'angles': trial_data["angles"][index:]})
        
        self.trial_stats = {}
        self.trial_stats["start_time"] = round(self.trial_start_time - self.session_start, 2)
        self.trial_stats["init_thresh"] = self.init_thresh
        self.trial_stats["hit_thresh"] = self.hit_thresh
        self.trial_stats["Force"] = self.trial_data
        self.trial_stats["hold_time"] = self.hold_time * 1000
        self.trial_stats["duration"] = round(trial_end - trial_start_time, 2)
        self.trial_stats["success"] = self.success
        self.trial_stats["peak"] = self.peak_value

    def feed():
        self.num_pellets += 1
        gpio_feed()
        return
    
    def get_success():
        return self.success