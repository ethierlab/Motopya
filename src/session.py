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
        
        self.session = {}
        self.trial_table = []
        
        current_datetime = datetime.now()
        
        self.session["Start_time"] = current_datetime.strftime("%d-%B-%Y %H:%M:%S")
        self.session["Initial_hit_thresh"] = hit_thresh
        self.session["Initial_hold_time"] = hold_time
        
        
        
        last_hit_thresh = None
        last_hold_time = None
        session_hold_time = None
        session_hit_thresh = None
        trial_hold_time = None
        trial_hit_thresh = None
        
        
    def start():
        while True:
            self.trial_logic()
             
        
    def trial_logic():
        
        self.session_hit_thresh = self.hit_threshold if self.session_hit_thresh is None else self.session_hit_thresh
        self.session_hold_time = self.hold_time if self.session_hold_time is None else self.session_hold_time
        self.trial_hit_thresh = self.hit_threshold if self.trial_hit_thresh is None else self.trial_hit_thresh
        self.trial_hold_time = self.hold_time if self.trial_hold_time is None else self.trial_hold_time
        
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
                self.trial_started = True
                self.trial_start_time = current_time
                self.num_trials += 1
                print("Trial started")
                self.NEXT_STATE = STATE_TRIAL_STARTED
        elif CURRENT_STATE == STATE_TRIAL_STARTED:
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
            elif current_time - hit_start_time >= trial_hold_time:
                self.NEXT_STATE = STATE_SUCCESS
        elif CURRENT_STATE == STATE_SUCCESS:
            print("Success")
            self.successes.append(True)
            success = True
            last_trial_end_time = current_time
            if get_average(successes) >= 0.7:
                if hit_thresh_adapt:
                    trial_hit_thresh = min(hit_thresh_max, trial_hit_thresh + 10)
                if hold_time_adapt:
                    trial_hold_time = min(hold_time_max, round(trial_hold_time + 0.1, 4))
            self.num_success += 1
            self.num_pellets += 1
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_FAILURE:
            print("Fail")
            success = False
            successes.append(False)
            last_trial_end_time = current_time
            if get_average(successes) <= 0.4:
                if hit_thresh_adapt:
                    trial_hit_thresh = max(hit_thresh_min, trial_hit_thresh - 10)
                if hold_time_adapt:
                    trial_hold_time = max(hold_time_min, round(trial_hold_time - 0.1, 4))
            self.NEXT_STATE = STATE_POST_TRIAL
        elif CURRENT_STATE == STATE_POST_TRIAL:
            if post_trial_start is None:
                print("POST")
                post_trial_start = current_time
            elif current_time - post_trial_start >= post_duration:
                
                record_trial(init_threshold, hit_threshold, hold_time, last_trial_end_time, success, peak_value)
                peak_value = 0
                post_trial_start = None
                trial_started = False
                trial_start_time = None
                hit_start_time = None
                self.NEXT_STATE = STATE_INTER_TRIAL
                print("Inter")
                in_iti_period = True
                success = False
                last_trial_end_time = current_time
        elif CURRENT_STATE == STATE_INTER_TRIAL:
            last_hit_thresh = session_hit_thresh
            last_hold_time = session_hold_time
            session_hit_thresh = trial_hit_thresh
            session_hold_time = trial_hold_time
            if current_time - last_trial_end_time >= iti:
                clear_data()
                in_iti_period = False
                self.NEXT_STATE = STATE_IDLE
                print("IDLE")
        elif CURRENT_STATE == STATE_SESSION_END:
            pass
        
        previous_angle = latest_angle
        
        
        
        if reset_data:
            reset_data = False
            reset_stats()
            
    #     angles = get_angles()
    #     timestamps = get_timestamps()
        
        # Check for inactivity+--------------------------------------------------+
        # if angles and (current_time - last_move_time > 2):
            # clear_data()
            # last_move_time = current_time  # Reset the timer
    #
    
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
        trial_data = get_data()
        timestamps = np.array(trial_data["timestamps"]) - int(reference_time * 1000)
        index = np.where(timestamps >= -1000)[0][0]
        trial_data = pd.DataFrame({'timestamps': timestamps[index:], 'angles': trial_data["angles"][index:]})
        trial = {}
        trial["start_time"] = round(trial_start_time - session_start, 2)
        trial["init_thresh"] = init_thresh
        trial["hit_thresh"] = hit_thresh
        trial["Force"] = trial_data
        trial["hold_time"] = hold_time * 1000
        trial["duration"] = round(trial_end - trial_start_time, 2)
        trial["success"] = success
        trial["peak"] = peak_value
        trial_table.append(trial)
        
        self.session["Number_trials"] = num_trials
        self.session["Number_rewards"] = num_success
        self.session["Last_hit_thresh"] = hit_thresh
        self.session["Last_hold_time"] = hold_time * 1000

    def feed():
        self.num_pellets += 1
        gpio_feed()
        return
        
    def get_average(successes):
        return sum(successes) / len(successes) if len(successes) > 0 else 0.5
        
    def get_adapted_values():
        return self.session_hit_thresh, self.session_hold_time
        
    def reset():
        self.reset_data = True
        
    def get_trial_table():
        return self.trial_table
        
    def get_session():
        return self.session

