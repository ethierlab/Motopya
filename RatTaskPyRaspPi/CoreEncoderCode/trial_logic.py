import time
from rotary_encoder import get_latest_angle, get_angles, get_timestamps, clear_data

# Trial state variables
trial_started = False
trial_start_time = None
hit_start_time = None
last_move_time = time.time()
last_trial_end_time = None
in_iti_period = False

# Trial counters
num_trials = 0
num_success = 0

def trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time):
    global trial_started, trial_start_time, hit_start_time, last_move_time, last_trial_end_time, num_trials, num_success, in_iti_period
    
    current_time = time.time()
    latest_angle = get_latest_angle()
    angles = get_angles()
    timestamps = get_timestamps()
    
    # Check for inactivity
    if angles and (current_time - last_move_time > 2):
        clear_data()
        last_move_time = current_time  # Reset the timer
    
    # Check if trial should start
    if not trial_started:
        if latest_angle >= init_threshold:
            # Check ITI
            if last_trial_end_time is None or (current_time - last_trial_end_time >= iti):
                trial_started = True
                trial_start_time = last_move_time
                num_trials += 1
                print("Trial started")

    # Check if trial is ongoing
    if trial_started:
        # Update the last movement time during the trial
        last_move_time = current_time

        # Check for trial timeout
        if current_time - trial_start_time >= hit_duration:
            print("Fail")
            trial_started = False
            trial_start_time = None
            hit_start_time = None
            last_trial_end_time = current_time
            in_iti_period = True
            clear_data()
        
        # Check for hit threshold
        if latest_angle >= hit_threshold:
            if hit_start_time is None:
                hit_start_time = last_move_time
            elif current_time - hit_start_time >= hold_time:
                print("Success")
                trial_started = False
                trial_start_time = None
                hit_start_time = None
                num_success += 1
                last_trial_end_time = current_time
                in_iti_period = True
                # clear_data()
        else:
            hit_start_time = None
    
    # Ensure the last movement time is updated outside of the trial condition
    last_move_time = current_time

    # Check if ITI period is over and reset in_iti_period flag
    if in_iti_period and (current_time - last_trial_end_time >= iti):
        clear_data()
        in_iti_period = False

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
