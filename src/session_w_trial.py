import time as t
from rotary_encoder import get_latest_angle, get_latest, get_data, clear_data, last_move_time
from feeder import  gpio_feed
import numpy as np
from collections import deque
import pandas as pd
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO

from trial import trial

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


class Session():
    def __init__(self, init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration, iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max,
        hold_time_adapt, hold_time_min, hold_time_max, lever_gain, drop_tolerance, max_trials):
        
        self.init_threshold = init_threshold
        self.hit_duration = hit_duration
        self.hit_threshold = hit_threshold
        self.iti = iti
        self.hold_time = hold_time
        self.iniBaseline = iniBaseline
        self.session_duration = session_duration
        self.post_duration = post_duration
        self.hit_thresh_adapt = hit_thresh_adapt
        self.hit_thresh_min = hit_thresh_min
        self.hit_thresh_max = hit_thresh_max
        self.hold_time_adapt = hold_time_adapt
        self.hold_time_min = hold_time_min
        self.hold_time_max = hold_time_max
        self.lever_gain = lever_gain
        self.drop_tolerance = drop_tolerance
        self.max_trials = max_trials
        
        self.session_start = t.time()
        
        self.session = {}
        self.trial_table = []
        
        current_datetime = datetime.now()
        
        self.session["Start_time"] = current_datetime.strftime("%d-%B-%Y %H:%M:%S")
        self.session["Initial_hit_thresh"] = hit_thresh
        self.session["Initial_hold_time"] = hold_time
        
        # Trial counters
        self.num_trials = 0
        self.num_success = 0
        self.num_pellets = 0
        
        
    def start():
        while True:
            self.trial_logic()
             
        
    def trial_logic():
        current_time = t.time()
        
        latest_angle, latest_time = get_latest()
        self.peak_value = max(latest_angle, peak_value)
        self.last_move_time = current_time
        CURRENT_STATE = self.NEXT_STATE
        
        # Check if trial should start
        if CURRENT_STATE == STATE_IDLE:
            reference_time = latest_time
            if t.time() - self.session_start > self.session_duration * 60 * 60 or self.num_trials >= self.max_trials or self.stop_session:
                self.NEXT_STATE = STATE_SESSION_END   
            elif latest_angle >= init_threshold and previous_angle < init_threshold:
                self.NEXT_STATE = STATE_TRIAL_STARTED
        elif CURRENT_STATE == STATE_TRIAL_STARTED:
            self.num_trials += 1
            print("Trial started")
            
            trial = Trial(self.hit_duration, self.hit_threshold, self.hold_time, self.post_duration, self.iniBaseline,
                          self.lever_gain, self.drop_tolerance, self.session_start, latest_time)
            trial.run()
            
            trial_table.append(trial.get_trial_data())
            adapt_values(trial.get_success())
            
            NEXT_STATE = STATE_INTER_TRIAL
            self.last_trial_end_time = current_time
        elif CURRENT_STATE == STATE_INTER_TRIAL:
            if current_time - self.last_trial_end_time >= iti:
                in_iti_period = False
                self.NEXT_STATE = STATE_IDLE
                print("IDLE")
        elif CURRENT_STATE == STATE_SESSION_END:
            pass
        
        previous_angle = latest_angle
            
    #     angles = get_angles()
    #     timestamps = get_timestamps()
        
        # Check for inactivity+--------------------------------------------------+
        # if angles and (current_time - last_move_time > 2):
            # clear_data()
            # last_move_time = current_time  # Reset the timer
    #
    def adapt_values(success):
        if success:
            self.num_success += 1
            self.num_pellets +=1 
            
        self.successes.append(success)
        average = self.get_success_average()
        if average >= 0.7:
            if self.hit_thresh_adapt:
                self.hit_threshold = min(self.hit_thresh_max, self.hit_threshold + 10)
            if self.hold_time_adapt:
                self.hold_time = min(self.hold_time_max, round(self.hold_time + 0.1, 4))

        if get_average(successes) <= 0.4:
            if hit_thresh_adapt:
                self.hit_threshold = max(hit_thresh_min, self.hit_threshold - 10)
            if hold_time_adapt:
                self.hold_time = max(hold_time_min, round(self.hold_time - 0.1, 4))
                
    def is_in_iti_period():
        return self.in_iti_period

    def get_trial_counts():
        return self.num_trials, self.num_success, self.num_pellets

    def is_trial_started():
        return self.trial_started
        
    def get_reference_time():
        return self.reference_time
        
    def get_last_values():
        return self.last_hit_thresh, self.last_hold_time

    def record_trial(init_thresh, hit_thresh, hold_time, trial_end, success, peak_value):
        trial_table.append(self.trial.get_trial_data())
        
        self.session["Number_trials"] = num_trials
        self.session["Number_rewards"] = num_success
        self.session["Last_hit_thresh"] = hit_thresh
        self.session["Last_hold_time"] = hold_time * 1000

    def feed():
        self.num_pellets += 1
        gpio_feed()
        return
        
    def get_success_average():
        return sum(self.successes) / len(self.successes) if len(self.successes) > 0 else 0.5
        
    def get_adapted_values():
        return self.session_hit_thresh, self.session_hold_time
        
    def get_trial_table():
        return self.trial_table
        
    def get_session():
        return self.session

