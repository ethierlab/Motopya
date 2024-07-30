from gpiozero import RotaryEncoder2
import time

# Define the GPIO pins for the rotary encoder
encoder_a = 20  # Example GPIO pin for A
encoder_b = 21  # Example GPIO pin for B

# Global variables for the latest angle and timestamps
latest_angle = 0
angles = []
timestamps = []
last_move_time = time.time()

# Set up the rotary encoder
encoder = None

def setup_encoder():
    global encoder
    encoder = RotaryEncoder2(encoder_a, encoder_b, max_steps=360,half_step=True)
    encoder.when_rotated = rotary_changed

def rotary_changed():
    global latest_angle, last_move_time
    latest_angle = encoder.steps   # Get the current angle with 0.5 degree resolution
    timestamp = int(time.time() * 1000)  # Get current time in milliseconds
    angles.append(latest_angle)
    timestamps.append(timestamp)
    last_move_time = time.time()
    
    if len(angles) > 1000:  # Keep the last 1000 data points
        angles.pop(0)
        timestamps.pop(0)

def get_latest_angle():
    return latest_angle

def get_angles():
    return angles

def get_timestamps():
    return timestamps

def clear_data():
    global angles, timestamps
    angles.clear()
    timestamps.clear()
