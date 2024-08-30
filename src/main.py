import os
import sys
import threading
import pkg_resources
import subprocess
import stat

def install(package):
    try:
        result = subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print("Installation was unsuccesseful. Verify internet connection and permissions")
        print(e)

def check_packages(do_install):
    with open('requirements.txt') as f:
        dependencies = f.read().splitlines()
    canRun = True
    for dependency in dependencies:
        try:
            pkg_resources.require(dependency)
        except pkg_resources.DistributionNotFound:
            print(f"{dependency} is not installed.")
            if do_install:
                print("Installing...")
                install(dependency)
            else:
                canRun = False
        except pkg_resources.VersionConflict as e:
            print(e)
            canRun = False
            
        if not canRun:
            sys.exit()
            
def check_permissions():
    output_dir = "output_files"
    working_directory = os.getcwd()
    
    permissions = os.stat(working_directory).st_mode
    
    readable_permissions = stat.filemode(permissions)
    
    is_writable = permissions & stat.S_IWUSR != 0
    is_readable = permissions & stat.S_IWUSR != 0
    
    if not is_writable and not is_readable:
        print(f"Permissions for {working_directory}: {readable_permissions}")
        print("Error: The working directory is not readable and writeable.")
        sys.exit()

check_permissions()
check_packages(True)



import numpy as np
import time as t
import csv
from datetime import datetime
from datetime import timedelta

from ExLibs.input_device import RotaryEncoder, Lever
from ExLibs.session import Session
from ExLibs.utils import is_positive_float, is_percentage_range
from ExLibs.feeder import gpio_feed
from ExLibs.buzzer import Buzzer
from ExLibs.light import Light
from ExLibs.gui import RatTaskGUI
from ExLibs.clock import clock


#Initialize Session object

session = None

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
gain = 1
drop_tolerance = 1000
max_trials = 100
save_folder = ""
ratID = 1

session_running = False
session_paused = False
num_pellets = 0
num_rewards = 0
num_trials = 0

# session_info = {}
parameters = {}

parameters["iniThreshold"] = 40 #0
parameters["iniBaseline"] = 0 #1
parameters["minDuration"] = 30#2
parameters["hitWindow"] = 2 #3
parameters["hitThresh"] = 100 #4
parameters["hitThreshAdapt"] = False #5
parameters["hitThreshMin"] = 10 #6
parameters["hitThreshMax"] = 100 #7
parameters["gain"] = 1 #8
parameters["useDropTol"] = False
parameters["forceDrop"] = 1000 #9
parameters["maxTrials"] = 10 #10
parameters["holdTime"] = 1 #11
parameters["holdTimeAdapt"] = False #12
parameters["holdTimeMin"] = 0.7 #13
parameters["holdTimeMax"] = 1.3 #14
parameters["saveFolder"]  = "" #15
parameters["ratID"] = "" #16
parameters["inputType"] = True

parameters["minThreshAdapt"] = 40
parameters["maxThreshAdapt"] = 70

parameters["minTimeAdapt"] = 40
parameters["maxTimeAdapt"] = 70

parameters["postTrialDuration"] = 1
parameters["interTrialDuration"] = 1

def gui_save_parameters(parameters_list, file_path):
    update_parameters(parameters_list)
    return save_parameters(file_path)

def update_parameters(parameters_list):
    global parameters
    for i, key in enumerate(parameters):
        parameters[key] = parameters_list[i]
        
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

def get_parameters_list():
    return list(parameters.values())

def load_parameters(file_path):
    global parameters
    
    directory = os.path.dirname(file_path)
    message = ""
    
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            headers = []
            for row in reader:
                key, value = row
                headers.append(key)
                if key not in parameters.keys():
                    message = "That is not a configuration file. " + str(key) + " is not a parameter. "
                    return False, message, list(parameters.values())
                parameters[key] = value
                
            for key in parameters.keys():
                if key not in headers:
                    message = "That is not a configuration file." + str(key) + " is not a parameter. "
                    return False, message, list(parameters.values())
                
                                
                                

    except Exception as e: 
        message = "Error reading file." + str(file_path)
        print(e)
        return False, message, list(parameters.values())
    if not os.path.exists(parameters["saveFolder"]):
        parameters["saveFolder"] = directory

    message = "Parameters loaded"
    return True, message, list(parameters.values())

timer_running = False
session_running = False

        
def start():
    global session_running
    session_running = True

# Function to stop the trials
def stop_session():
    global running, session
    if session != None:
        session.stop()
    running = False
    
def save_trial_table(filename):
    trial_table = session.get_trial_table()

    try:
        with open(filename, mode='w', newline='') as csvfile:
            fieldnames = ["start_time", "init_thresh", "hit_thresh", "Force", "hold_time", "duration", "success", "peak"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for trial in trial_table:
                # Convert list of Force values to a string for CSV
                df_string = {"time, value": ','.join(f"({row['timestamps']}, {row['values']})" for _, row in trial["Force"].iterrows())}
                trial["Force"] = df_string
                writer.writerow(trial)
    except PermissionError:
        print("Cannot write to open file")

def save_session_parameters(file_path, dict):
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
#     rat_dir = os.path.join(parameters["saveFolder"], "output_files", str(parameters["ratID"]))
    rat_dir = os.path.join("output_files", str(parameters["ratID"]))
    dir_exists = os.path.exists(rat_dir)
    message = ""
    try:
        os.makedirs(rat_dir, exist_ok=True)
    except:
        message = 'Failed to create new folder in specified location'
        return False, message
    ttfname = parameters["ratID"] + file_input_type + '_trial_table_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
    pfname = parameters["ratID"] + file_input_type + '_params_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
    gfname = parameters["ratID"] + '_global_stats.csv'
    save_trial_table(os.path.join(rat_dir, ttfname))
    save_session_parameters(os.path.join(rat_dir, pfname), parameters)
    update_global_stats(os.path.join(rat_dir, gfname))
    message = 'Behavior stats and parameters saved successfully'
        
    return True, message
    

def update_global_stats(filename):
    
    session_info = session.get_session()

    exists = os.path.isfile(filename)
    try:
        with open(filename, mode='a', newline='') as csvfile:
            fieldnames = ["Start_time", "Number_trials", "Number_rewards", "Initial_hit_thresh", "Last_hit_thresh", "Initial_hold_time", "Last_hold_time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not exists:
                print("writing header")
                writer.writeheader()

            writer.writerow(session_info)
    except PermissionError:
        print("Cannot write to open file")

session_thread = None

def get_lever_value():
    return lever.get_value()

# Function to start the trials
def start_session():
    global session, session_thread
    global running
    global init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration,iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max
    global hold_time_adapt, hold_time_min, hold_time_max, gain, drop_tolerance, max_trials, save_folder, ratID
    global input_device, lever, encoder
    init_threshold = float(parameters["iniThreshold"])
    hit_duration = float(parameters["hitWindow"])
    hit_threshold = float(parameters["hitThresh"])
    inter_trial_duration = float(parameters["interTrialDuration"])
    hold_time = float(parameters["holdTime"])
    iniBaseline = float(parameters["iniBaseline"])
    session_duration = float(parameters["minDuration"])
    hit_thresh_adapt = bool(parameters["hitThreshAdapt"])
    hit_thresh_min = float(parameters["hitThreshMin"]) if is_positive_float(parameters["hitThreshMin"]) else 0
    hit_thresh_max = float(parameters["hitThreshMax"]) if is_positive_float(parameters["hitThreshMax"]) else 0
    hold_time_adapt = bool(parameters["holdTimeAdapt"])
    hold_time_min = float(parameters["holdTimeMin"]) if is_positive_float(parameters["holdTimeMin"]) else 0
    hold_time_max = float(parameters["holdTimeMax"]) if is_positive_float(parameters["holdTimeMax"]) else 0
    gain = float(parameters["gain"])
    drop_tolerance = float(parameters["forceDrop"])
    max_trials = float(parameters["maxTrials"])
    save_folder = str(parameters["saveFolder"])
    ratID = str(parameters["ratID"])
    input_type = bool(parameters["inputType"])
    
    min_thresh_adapt = float(parameters["minThreshAdapt"])
    max_thresh_adapt = float(parameters["maxThreshAdapt"])

    min_time_adapt = float(parameters["minTimeAdapt"])
    max_time_adapt = float(parameters["maxTimeAdapt"])
    
    post_trial_duration = float(parameters["postTrialDuration"])
    
    
    
    if (input_type):
        input_device = lever
    else:
        input_device = encoder
    
    input_device.modify_gain(gain)
    
    session = Session(init_threshold, hit_duration, hit_threshold, post_trial_duration, inter_trial_duration, hold_time, iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max,
    hold_time_adapt, hold_time_min, hold_time_max, gain, drop_tolerance, max_trials, input_device, buzzer, light, min_thresh_adapt, max_thresh_adapt, min_time_adapt, max_time_adapt)
    
    running = True

buzzer = Buzzer(13)
light = Light(19)
light.flash()
encoder = RotaryEncoder(1)

exit_program = False
lever = None
try:
    lever = Lever(1)
except OSError:
    print("ADS1015 not connected")
#     sys.exit(1)


def lever_loop():
    while True:
        if exit_program:
            break
        for i in range(250):
            lever.update_value()
            t.sleep(0.001)

input_device = encoder
leverThread = threading.Thread(target=lever_loop)
if lever != None:
    leverThread.start()
    input_device = lever
        

def get_data():
    return input_device.get_data()

# Initialize running state
running = False

def run_logic():
    global parameters, session
    while True:
        if running and session != None and not session.is_running() and not session.is_done():
            session.start()
        if exit_program:
            break
        t.sleep(0.001)
        
logic = None

def is_running():
    if session != None:
        return session.is_running()
    return False

def session_done():
    if session != None:
        return session.is_done()
    return False

def close():
    global exit_program, running
    stop_session()
    running = False
    exit_program = True
    if logic:
        logic.join()
    if leverThread and leverThread.is_alive():
        leverThread.join()
    
def get_reference():
    return session.get_reference_time()

def get_adapted():
    return session.get_adapted_values()

def get_counts():
    return session.get_trial_counts()

def in_iti():
    return session.is_in_iti_period()

def gui_feed():
    if session != None: 
        session.feed()
    else:
        gpio_feed()
        
def remove_offset():
    input_device.remove_offset()
# start_session_func, stop_session_func, feed_func, load_parameters_func, save_parameters_func, get_data_func, save_session_data_func

passed_functions = {
    'start_session': start_session,
    'stop_session': stop_session,
    'feed': gui_feed,
    'load_parameters': load_parameters,
    'save_parameters': gui_save_parameters,
    'get_data': get_data,
    'save_session_data': save_session_data,
    'is_in_iti_period': in_iti,
    'get_reference_time': get_reference,
    'get_adapted_values': get_adapted,
    'get_trial_counts': get_counts,
    'update_parameters': update_parameters,
    'close': close,
    'is_running': is_running,
    'remove_offset': remove_offset,
    'get_parameters_list': get_parameters_list,
    'session_done': session_done,
    'get_lever_value': get_lever_value
}


gui = None
        
def main():
    global logic, gui
    logic = threading.Thread(target=run_logic)
    logic.start()
    gui = RatTaskGUI(passed_functions)
#     start_gui(passed_functions)

if __name__ == "__main__":
    main()
