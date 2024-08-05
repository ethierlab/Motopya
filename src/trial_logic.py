import time
from rotary_encoder import get_latest_angle, get_latest, get_angles, get_timestamps, clear_data, trial_start, set_trial_start, last_move_time
import numpy as np


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

# Trial counters
num_trials = 0
num_success = 0

#Matplot usage
reference_time = time.time()

def trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration):
    global trial_started, trial_start_time, hit_start_time, last_move_time, last_trial_end_time, num_trials, num_success, in_iti_period,  trial_start, reference_time
    global CURRENT_STATE, NEXT_STATE, post_trial_start, previous_angle
    
    current_time = time.time()
    
    latest_angle, latest_time = get_latest()
#     print(latest_angle)
    last_move_time = current_time
    CURRENT_STATE = NEXT_STATE
    
    # Check if trial should start
    if CURRENT_STATE == STATE_IDLE:
        reference_time = latest_time
        if latest_angle >= init_threshold and previous_angle < init_threshold:
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
        if current_time - trial_start_time >= hit_duration:
            NEXT_STATE = STATE_FAILURE
        # Check for hit threshold
        elif latest_angle >= hit_threshold:
            hit_start_time = current_time
            NEXT_STATE = STATE_HOLD
    elif CURRENT_STATE == STATE_HOLD:
        if latest_angle < hit_threshold:
            NEXT_STATE = STATE_TRIAL_STARTED
        elif current_time - hit_start_time >= hold_time:
            NEXT_STATE = STATE_SUCCESS
    elif CURRENT_STATE == STATE_SUCCESS:
        print("Success")
        num_success += 1
        NEXT_STATE = STATE_POST_TRIAL
    elif CURRENT_STATE == STATE_FAILURE:
        print("Fail")
        NEXT_STATE = STATE_POST_TRIAL
    elif CURRENT_STATE == STATE_POST_TRIAL:
        if post_trial_start is None:
            print("POST")
            post_trial_start = current_time
        elif current_time - post_trial_start >= post_duration:
            post_trial_start = None
            trial_started = False
            trial_start_time = None
            hit_start_time = None
            last_trial_end_time = current_time
            NEXT_STATE = STATE_INTER_TRIAL
            print("Inter")
            in_iti_period = True
            record_trial()
    elif CURRENT_STATE == STATE_INTER_TRIAL:
        if current_time - last_trial_end_time >= iti:
            clear_data()
            in_iti_period = False
            NEXT_STATE = STATE_IDLE
            print("IDLE")
    elif CURRENT_STATE == STATE_SESSION_END:
        print("Session is over")
        
    previous_angle = latest_angle
        
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
    global num_trials, num_success
    return num_trials, num_success

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
    
def record_trial():
#     return
    timestamps = np.array(get_timestamps()) - int(reference_time * 1000)
    index = np.where(timestamps >= -1000)[0][0]
    timestamps = timestamps[index:]
    angles = get_angles()[index:]
    timestamps = timestamps.tolist()
    
    zipped = list(zip(timestamps, angles))
    # print(zipped)
#     print(timestamps)
#     print(angles)
