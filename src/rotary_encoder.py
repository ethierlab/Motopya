from gpiozero import RotaryEncoder2
import time
import pandas as pd

# Define the GPIO pins for the rotary encoder
encoder_a = 24  # Example GPIO pin for A
encoder_b = 25  # Example GPIO pin for B

# Global variables for the latest angle and timestamps
latest_angle = 0
data = pd.DataFrame(columns=["timestamps", "angles"])
angles = []
timestamps = []
last_move_time = time.time()
initial_time = None
trial_start = time.time()

# Set up the rotary encoder
encoder = None

def setup_encoder():
    global encoder, initial_time
    initial_time = time.time()
    # trial_start = time.time()
    encoder = RotaryEncoder2(encoder_a, encoder_b, max_steps=360,half_step=False)
#     encoder = RotaryEncoder(encoder_a, encoder_b, max_steps=360)
    encoder.when_rotated = rotary_changed
def rotary_changed():
    global latest_angle, last_move_time, data
    latest_angle = encoder.steps   # Get the current angle with 0.5 degree resolution
    timestamp = int(time.time() * 1000)  # Get current time in milliseconds
    new_data = pd.DataFrame({"timestamps": [timestamp], "angles": [latest_angle]})
    data = pd.concat([data, new_data], ignore_index = True)
    last_move_time = time.time()
    if len(data) > 3000:
        data = data.iloc[-3000:]

def get_latest_angle():
    return latest_angle

def get_latest():
    return latest_angle, last_move_time

def get_angles():
    return angles
    
def get_data():
    return data

def get_timestamps():
    return timestamps

def clear_data():
    global angles, timestamps, data
    angles.clear()
    timestamps.clear()
    data = pd.DataFrame(columns=["timestamps", "angles"])
    
def set_trial_start(start):
    global trial_start
    print("setting trial start time")
    trial_start = start
    
def get_trial_start():
    return trial_start
