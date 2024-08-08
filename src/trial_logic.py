import time
from rotary_encoder import get_latest_angle, get_latest, get_data, clear_data, trial_start, set_trial_start, last_move_time
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

# Trial state variables
trial_started = False
trial_start_time = None
hit_start_time = None
last_trial_end_time = None
post_trial_start = None
in_iti_period = False
previous_angle = 0
success = False
reset_data = False

# Trial counters
num_trials = 0
num_success = 0
num_pellets = 0

#Matplot usage
reference_time = time.time()
session_start = time.time()
stop_session = False
peak_value = 0
successes = deque(maxlen=10)

last_hit_thresh = None
last_hold_time = None
session_hold_time = None
session_hit_thresh = None
trial_hold_time = None
trial_hit_thresh = None

trial_data = pd.DataFrame(columns=["timestamps", "angles"])
trial_table = []

session = {}

def initialize_session(hit_thresh, hold_time):
    global session, trial_table
    current_datetime = datetime.now()
    session["Start_time"] = current_datetime.strftime("%d-%B-%Y %H:%M:%S")
    session["Initial_hit_thresh"] = hit_thresh
    session["Initial_hold_time"] = hold_time
    trial_table = []
    
    session_hit_thresh = None
    session_hold_time = None
    trial_hit_thresh = None
    trial_hold_time = None


def trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration, iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max,
    hold_time_adapt, hold_time_min, hold_time_max, lever_gain, drop_tolerance, max_trials, save_folder, ratID):
    global trial_started, trial_start_time, hit_start_time, last_move_time, last_trial_end_time, num_trials, num_success, in_iti_period,  trial_start, reference_time
    global CURRENT_STATE, NEXT_STATE, post_trial_start, previous_angle, peak_value, num_pellets, session_hold_time, session_hit_thresh, trial_hit_thresh, trial_hold_time, success
    global last_hit_thresh, last_hold_time, reset_data
    
    
    session_hit_thresh = hit_threshold if session_hit_thresh is None else session_hit_thresh
    session_hold_time = hold_time if session_hold_time is None else session_hold_time
    trial_hit_thresh = hit_threshold if trial_hit_thresh is None else trial_hit_thresh
    trial_hold_time = hold_time if trial_hold_time is None else trial_hold_time
    
    current_time = time.time()
    
    latest_angle, latest_time = get_latest()
    peak_value = max(latest_angle, peak_value)
#     print(latest_angle)
    last_move_time = current_time
    CURRENT_STATE = NEXT_STATE
    
    # Check if trial should start
    if CURRENT_STATE == STATE_IDLE:
        reference_time = latest_time
        if time.time() - session_start > session_duration * 60 * 60 or num_trials >= max_trials or stop_session:
            NEXT_STATE = STATE_SESSION_END   
        elif latest_angle >= init_threshold and previous_angle < init_threshold:
            print(latest_angle, " ", previous_angle)
            trial_started = True
            trial_start_time = current_time
            num_trials += 1
            print("Trial started")
            NEXT_STATE = STATE_TRIAL_STARTED
    elif CURRENT_STATE == STATE_TRIAL_STARTED:
        # Update the last movement time during the trial
#         last_move_time = current_time

        # Check for trial timeout
        if current_time - trial_start_time >= hit_duration and latest_angle < trial_hit_thresh:
            print("time fail")
            NEXT_STATE = STATE_FAILURE
        # Check for hit threshold
        elif latest_angle <= peak_value - drop_tolerance:
            print("drop fail")
            NEXT_STATE = STATE_FAILURE
        elif latest_angle >= trial_hit_thresh:
            hit_start_time = current_time
            NEXT_STATE = STATE_HOLD
    elif CURRENT_STATE == STATE_HOLD:
        if latest_angle < trial_hit_thresh:
            NEXT_STATE = STATE_TRIAL_STARTED
        elif current_time - hit_start_time >= trial_hold_time:
            NEXT_STATE = STATE_SUCCESS
    elif CURRENT_STATE == STATE_SUCCESS:
        print("Success")
        successes.append(True)
        success = True
        last_trial_end_time = current_time
        if get_average(successes) >= 0.7:
            if hit_thresh_adapt:
                trial_hit_thresh = min(hit_thresh_max, trial_hit_thresh + 10)
            if hold_time_adapt:
                trial_hold_time = min(hold_time_max, round(trial_hold_time + 0.1, 4))
        num_success += 1
        num_pellets += 1
        NEXT_STATE = STATE_POST_TRIAL
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
        NEXT_STATE = STATE_POST_TRIAL
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
            NEXT_STATE = STATE_INTER_TRIAL
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
            NEXT_STATE = STATE_IDLE
            print("IDLE")
    elif CURRENT_STATE == STATE_SESSION_END:
        print("Session is over")
    
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
    global in_iti_period
    return in_iti_period

def get_trial_counts():
    global num_trials, num_success, num_pellets
    return num_trials, num_success, num_pellets

def reset_trial_counts():
    global num_trials, num_success
    num_trials = 0
    num_success = 0

def is_trial_started():
    global trial_started
    return trial_started
    
def get_reference_time():
    global reference_time
    return reference_time
    
def get_last_values():
    global last_hit_thresh, last_hold_time
    return last_hit_thresh, last_hold_time

def record_trial(init_thresh, hit_thresh, hold_time, trial_end, success, peak_value):
#     return
    global trial_data, trial_table
    global num_trials, num_success, num_pellets
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
    
    session["Number_trials"] = num_trials
    session["Number_rewards"] = num_success
    session["Last_hit_thresh"] = hit_thresh
    session["Last_hold_time"] = hold_time * 1000

def feed():
    global num_pellets
    num_pellets += 1
    gpio_feed()
    print("fed")
    return
    
def get_average(successes):
    return sum(successes) / len(successes) if len(successes) > 0 else 0.5
    
def get_adapted_values():
    return session_hit_thresh, session_hold_time
    
def reset():
    global reset_data
    reset_data = True
    
def reset_stats():
    global trial_started, trial_start_time, hit_start_time, last_trial_end_time, post_trial_start,in_iti_period, previous_angle
    global num_trials, num_success, num_pellets
    global reference_time, session_start, stop_session, peak_value, successes
    global session_hold_time, session_hit_thresh
    
    CURRENT_STATE = NEXT_STATE = STATE_IDLE
    
    
    trial_started = False
    trial_start_time = None
    hit_start_time = None
    last_trial_end_time = None
    post_trial_start = None
    in_iti_period = False
    previous_angle = 0

    # Trial counters
    num_trials = 0
    num_success = 0
    num_pellets = 0

    #Matplot usage
    reference_time = time.time()
    session_start = time.time()
    stop_session = False
    peak_value = 0
    successes = deque(maxlen=10)

    session_hold_time = None
    session_hit_thresh = None

def get_trial_table():
    global trial_table
    return trial_table
    
def get_session():
    global session
    return session

