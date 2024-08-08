import os
import sys
from signal import pause
import threading
import numpy as np
import time as t
import csv
from datetime import datetime
from datetime import timedelta

from rotary_encoder import setup_encoder, get_latest_angle, trial_start, get_trial_start, get_data
from trial_logic import trial_logic, get_trial_counts, reset_trial_counts, is_in_iti_period, is_trial_started, get_reference_time, feed, get_adapted_values, reset, get_trial_table
from trial_logic import get_last_values, initialize_session, get_session
from gui import start_gui

# Initialize trial parameters
iniBaseline = 0
session_duration = 30
init_threshold = 50
hit_duration = 5
hit_threshold = 100
hold_time = 1
post_duration = 1
iti = 1
hit_thresh_adapt = False
hit_thresh_min = 0
hit_thresh_max = 1000
hold_time_adapt = False
hold_time_min = 0
hold_time_max = 1000
lever_gain = 1
drop_tolerance = 1000
max_trials = 100
save_folder = ""
ratID = 1

session_running = False
session_paused = False
num_pellets = 0
num_rewards = 0
num_trials = 0

session = {}
parameters = {}

parameters["iniThreshold"] = 1 #0
parameters["iniBaseline"] = 2 #1
parameters["minDuration"] = 3#2
parameters["hitWindow"] = 4 #3
parameters["hitThresh"] = 5 #4
parameters["hitThreshAdapt"] = False #5
parameters["hitThreshMin"] = 6 #6
parameters["hitThreshMax"] = 7 #7
parameters["leverGain"] = 8 #8
parameters["forceDrop"] = 9 #9
parameters["maxTrials"] = 10 #10
parameters["holdTime"] = 11 #11
parameters["holdTimeAdapt"] = False #12
parameters["holdTimeMin"] = 12 #13
parameters["holdTimeMax"] = 13 #14
parameters["saveFolder"]  = "" #15
parameters["ratID"] = "" #16

def gui_save_parameters(parameters_list, file_path):
    update_parameters(parameters_list)
    return save_parameters(file_path)

def update_parameters(parameters_list):
    print("updating parameters")
    for i, key in enumerate(parameters):
        parameters[key] = parameters_list[i]
        print(parameters_list[i])
        
def save_parameters(file_path):
    global parameters
    saved_parameters = {}
    for key, value in parameters.items():
        saved_parameters[key] = value
    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in saved_parameters.items():
                writer.writerow([key, value])
    except PermissionError:
        message = "Cannot write to open file"
        return message
    

    message = "Configuration saved"
    return message

def load_parameters(file_path):
    global parameters
    
    directory = os.path.dirname(file_path)
    message = ""
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                key, value = row
                print(key, value)
                if key not in parameters.keys():
                    message = "That is not a configuration file." + str(key)
                    return False, message, list(parameters.values())
                parameters[key] = value

    except Exception as e: 
        message = "Error reading file." + str(file_path)
        print(e)
        return False, message, list(parameters.values())
    if not os.path.exists(parameters["saveFolder"]):
        parameters["saveFolder"] = directory

    message = "Parameters loaded"
    return True, message, list(parameters.values())

timer_running = False
_paused = False
session_running = False
    
def resume():
    global session_paused
    global pause_time
    session_paused = False

pause_start = t.time()
pause_time = 0
        
debut = t.time()
def start():
    # Déclenche la session comportement
    global session_running, session, max_force, debut
    initialize_session(parameters["hitThresh"], float(parameters["holdTime"]) * 1000)
    
    session_running = True
    debut = t.time()
    
        
def pause():
    global session_paused
    global pause_start
    pause_start = t.time()
    session_paused = True

# Function to stop the trials
def stop_session():
    print("stopping session")
    global running
    running = False
    reset()
    
def save_trial_table(filename):
    trial_table = get_trial_table()

    try:
        with open(filename, mode='w', newline='') as csvfile:
            fieldnames = ["start_time", "init_thresh", "hit_thresh", "Force", "hold_time", "duration", "success", "peak"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for trial in trial_table:
                # Convert list of Force values to a string for CSV
                df_string = {"time, angle": ','.join(f"({row['timestamps']}, {row['angles']})" for _, row in trial["Force"].iterrows())}
                trial["Force"] = df_string
                writer.writerow(trial)
    except PermissionError:
        print("Cannot write to open file")

def save_file(file_path, dict):
    saved_parameters = {}
    for key, value in dict.items():
        saved_parameters[key] = value

    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in saved_parameters.items():
                writer.writerow([key, value])
    except PermissionError:
        print("Cannot write to open file")

def save_session_data():
    file_input_type = "_RatKnob"
    rat_dir = os.path.join(parameters["saveFolder"], str(parameters["ratID"]))
    dir_exists = os.path.exists(rat_dir)
    message = ""
    if not dir_exists:
        message = f'Creating new folder for animal parameters["ratID"]\n'
        try:
            dir_exists = True
            os.mkdir(rat_dir)
        except OSError:
            dir_exists = False
            message = 'Failed to create new folder in specified location'
            return False, message
    if dir_exists:
        ttfname = parameters["ratID"] + file_input_type + '_trial_table_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
        pfname = parameters["ratID"] + file_input_type + '_params_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
        gfname = parameters["ratID"] + '_global_stats.csv'
        save_trial_table(os.path.join(rat_dir, ttfname))
        # save_file(os.join(rat_dir, ttfname), trial_table)
        save_file(os.path.join(rat_dir, pfname), parameters)

        message = 'Behavior stats and parameters saved successfully'
        update_global_stats(os.path.join(rat_dir, gfname))
    else:
        message = 'Behavior stats and parameters NOT saved'
        return False, message
        
    return True, message
    

def update_global_stats(filename):
    session = get_session()

    exists = os.path.isfile(filename)
    try:
        with open(filename, mode='a', newline='') as csvfile:
            fieldnames = ["Start_time", "Number_trials", "Number_rewards", "Initial_hit_thresh", "Last_hit_thresh", "Initial_hold_time", "Last_hold_time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not exists:
                print("writing header")
                writer.writeheader()

            writer.writerow(session)
    except PermissionError:
        print("Cannot write to open file")
    


# Create parameter input fields
def create_parameter_input(frame, label, row, default_value):
    tk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
    entry = ttk.Entry(frame)
    entry.grid(row=row, column=1, pady=2)
    entry.insert(0, str(default_value))
    return entry

# Function to start the trials
def start_session():
    global running
    global init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration,iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max
    global hold_time_adapt, hold_time_min, hold_time_max, lever_gain, drop_tolerance, max_trials, save_folder, ratID
    init_threshold = float(parameters["iniThreshold"])
    hit_duration = float(parameters["hitWindow"])
    hit_threshold = float(parameters["hitThresh"])
    # iti = float(iti_entry)
    hold_time = float(parameters["holdTime"])
    iniBaseline = float(parameters["iniBaseline"])
    session_duration = float(parameters["minDuration"])
    post_duration = float(1)
    hit_thresh_adapt = bool(parameters["hitThreshAdapt"])
    hit_thresh_min = float(parameters["hitThreshMin"])
    hit_thresh_max = float(parameters["hitThreshMax"])
    hold_time_adapt = bool(parameters["holdTimeAdapt"])
    hold_time_min = float(parameters["holdTimeMin"])
    hold_time_max = float(parameters["holdTimeMax"])
    lever_gain = float(parameters["leverGain"])
    drop_tolerance = float(parameters["forceDrop"])
    max_trials = float(parameters["maxTrials"])
    save_folder = str(parameters["saveFolder"])
    ratID = str(parameters["ratID"])
    
    initialize_session(float(parameters["hitThresh"]), float(parameters["holdTime"]) * 1000)
    
    running = True

# Set up the rotary encoder
setup_encoder()

# Initialize running state
running = False
exit_program = False
def run_logic():
    global parameters
    print("running logic")
    while True:
        if running:
            trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration,iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max,
            hold_time_adapt, hold_time_min, hold_time_max, lever_gain, drop_tolerance, max_trials, save_folder, ratID)
        elif exit_program:
            break
        t.sleep(0.001)
        
logic = threading.Thread(target=run_logic)
logic.start()

def is_running():
    global running
    return running
def close():
    print("Closing")
    global exit_program, running
    running = False
    exit_program = True
    logic.join()

# start_session_func, stop_session_func, feed_func, load_parameters_func, save_parameters_func, get_data_func, save_session_data_func

passed_functions = {
    'start_session': start_session,
    'stop_session': stop_session,
    'feed': feed,
    'load_parameters': load_parameters,
    'gui_save_parameters': gui_save_parameters,
    'get_data': get_data,
    'save_session_data': save_session_data,
    'is_in_iti_period': is_in_iti_period,
    'get_reference_time': get_reference_time,
    'get_adapted_values': get_adapted_values,
    'get_trial_counts': get_trial_counts,
    'update_parameters': update_parameters,
    'close': close,
    'is_running': is_running
}

start_gui(passed_functions)
