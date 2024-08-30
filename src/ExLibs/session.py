from ExLibs.clock import clock
import time as t
import numpy as np
from collections import deque
import pandas as pd
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO

from ExLibs.trial import Trial
from ExLibs.feeder import  gpio_feed


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
    def __init__(self, init_threshold, hit_duration, hit_threshold, post_trial_duration, inter_trial_duration, hold_time, iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max,
        hold_time_adapt, hold_time_min, hold_time_max, gain, drop_tolerance, max_trials, input_device, buzzer, light, min_thresh_adapt, max_thresh_adapt, min_time_adapt, max_time_adapt,
        adapt_thresh_change, adapt_time_change, adapt_min_trials):
        
        self.init_threshold = init_threshold
        self.hit_duration = hit_duration
        self.hit_threshold = hit_threshold
        self.post_trial_duration = post_trial_duration
        self.inter_trial_duration = inter_trial_duration
        self.hold_time = hold_time
        self.iniBaseline = iniBaseline
        self.session_duration = session_duration
        self.hit_thresh_adapt = hit_thresh_adapt
        self.hit_thresh_min = hit_thresh_min
        self.hit_thresh_max = hit_thresh_max
        self.hold_time_adapt = hold_time_adapt
        self.hold_time_min = hold_time_min
        self.hold_time_max = hold_time_max
        self.gain = gain
        self.drop_tolerance = drop_tolerance
        self.max_trials = max_trials
        self.input_device = input_device
        self.buzzer = buzzer
        self.light = light
        
        self.min_thresh_adapt = min_thresh_adapt / 100
        self.max_thresh_adapt = max_thresh_adapt/ 100
        self.min_time_adapt = min_time_adapt / 100
        self.max_time_adapt = max_time_adapt / 100
        
        
        self.adapt_thresh_change = adapt_thresh_change
        self.adapt_time_change = adapt_time_change
        self.adapt_min_trials = adapt_min_trials
        
        buzzer.play_init()
        
        self.session_start = clock.time()
        
        self.session = {}
        self.trial_table = []
        
        self.session_running = False
        self.session_done = False
        
        current_datetime = datetime.now()
        
        self.session["Start_time"] = current_datetime.strftime("%d-%B-%Y %H:%M:%S")
        self.session["Initial_hit_thresh"] = self.hit_threshold
        self.session["Initial_hold_time"] = self.hold_time
        
        # Trial counters
        self.num_trials = 0
        self.num_success = 0
        self.num_pellets = 0
        
        self.trial = None
        self.in_iti_period = False
        self.reference_time = clock.time()
        
        self.peak_value = 0
        self.NEXT_STATE = STATE_IDLE
        
        self.stop_session = False
        self.previous_angle = 0
        
        self.successes = []
        
        self.current_time = clock.time()
        self.last_move_time = 0
        
    def start(self):
        print("Session started")
        self.session_running = True
        while self.session_running:
            self.trial_logic()
            t.sleep(0.001)
        print("Session ended")
            
    def is_running(self):
        return self.session_running
    
    def is_done(self):
        return self.session_done
    
    def stop(self):
        clock.reset()
        self.session_running = False
        if self.trial != None:
            self.trial.stop()
             
        
    def trial_logic(self):
        self.current_time = clock.time()
        
        latest_value, latest_time = self.input_device.get_latest()

        self.last_move_time = self.current_time
        CURRENT_STATE = self.NEXT_STATE
        
        # Check if trial should start
        if CURRENT_STATE == STATE_IDLE:
            self.in_iti_period = False
            self.reference_time = latest_time
            if clock.time() - self.session_start > self.session_duration * 60 or self.num_trials >= self.max_trials or self.stop_session:
                self.NEXT_STATE = STATE_SESSION_END   
            elif latest_value >= self.init_threshold and self.previous_angle < self.init_threshold:
                self.NEXT_STATE = STATE_TRIAL_STARTED
                
        elif CURRENT_STATE == STATE_TRIAL_STARTED:
            self.num_trials += 1
            
            self.trial = Trial(self.init_threshold, self.hit_duration, self.hit_threshold, self.hold_time, self.post_trial_duration, self.iniBaseline,
                          self.gain, self.drop_tolerance, self.session_start, latest_time, self.input_device)
            self.trial.run()
            if self.trial.is_finished():
                self.trial_table.append(self.trial.get_trial_data())
                self.record_trial()
                if self.trial.get_success():
                    self.feed()
                self.adapt_values(self.trial.get_success())
               
            
            self.NEXT_STATE = STATE_INTER_TRIAL
            self.in_iti_period = True
            self.input_device.clear_data()
            self.last_trial_end_time = self.trial.get_end()
        elif CURRENT_STATE == STATE_INTER_TRIAL:
            if (self.current_time - self.last_trial_end_time) >= self.inter_trial_duration:
                self.in_iti_period = False
                self.NEXT_STATE = STATE_IDLE
        elif CURRENT_STATE == STATE_SESSION_END:
            self.stop()
            self.session_done = True
        
        self.previous_angle = latest_value
            
    def adapt_values(self, success):
        if success:
            self.num_success += 1
            self.num_pellets +=1
            self.buzzer.play_success()
            self.light.flash()
        else:
            self.buzzer.play_failure()

        
        self.successes.append(success)
        average = self.get_success_average()
        if self.hit_thresh_adapt:
            if average >= self.max_thresh_adapt:
                self.hit_threshold = min(self.hit_thresh_max, self.hit_threshold + self.adapt_thresh_change)
            elif average <= self.min_thresh_adapt:
                self.hit_threshold = max(self.hit_thresh_min, self.hit_threshold - self.adapt_thresh_change)
                
        if self.hold_time_adapt:
            if average >= self.max_time_adapt:
                self.hold_time = min(self.hold_time_max, round(self.hold_time + self.adapt_time_change, 4))
            elif average <= self.min_time_adapt:
                self.hold_time = max(self.hold_time_min, round(self.hold_time - self.adapt_time_change, 4))
                
                
    def is_in_iti_period(self):
        return self.in_iti_period

    def get_trial_counts(self):
        return self.num_trials, self.num_success, self.num_pellets

    def is_trial_started(self):
        return self.trial_started
        
    def get_reference_time(self):
        return self.reference_time
        
    def get_last_values(self):
        return self.last_hit_thresh, self.last_hold_time

    def record_trial(self):
        self.session["Number_trials"] = self.num_trials
        self.session["Number_rewards"] = self.num_success
        self.session["Last_hit_thresh"] = self.hit_threshold
        self.session["Last_hold_time"] = self.hold_time * 1000

    def feed(self):
        self.num_pellets += 1
        gpio_feed()
        return
        
    def get_success_average(self):
        return sum(self.successes) / len(self.successes) if len(self.successes) >= self.adapt_min_trials and len(self.successes) > 0 else 0.5
        
    def get_adapted_values(self):
        return self.hit_threshold, self.hold_time
        
    def get_trial_table(self):
        return self.trial_table
        
    def get_session(self):
        return self.session

