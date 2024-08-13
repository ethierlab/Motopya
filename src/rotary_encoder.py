from ExLibs.encoder import RotaryEncoder2
import time
import pandas as pd

# Define the GPIO pins for the rotary encoder
encoder_a = 20  # Example GPIO pin for A
encoder_b = 21  # Example GPIO pin for B

# Global variables for the latest angle and timestamps
latest_angle = 0
data = pd.DataFrame(columns=["timestamps", "angles"])
last_move_time = time.time()
initial_time = None

# Set up the rotary encoder
encoder = None

def setup_encoder():
    global encoder, initial_time
    initial_time = time.time()
    encoder = RotaryEncoder2(encoder_a, encoder_b, max_steps=360,half_step=True)
    encoder.when_rotated = rotary_changed
def rotary_changed():
    global latest_angle, last_move_time, data
    latest_angle = encoder.steps   # Get the current angle with 0.5 degree resolution
#     print(latest_angle)
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

def get_data():
    return data

def clear_data():
    global angles, timestamps, data
    data = pd.DataFrame(columns=["timestamps", "angles"])
