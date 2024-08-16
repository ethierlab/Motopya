# RotaryEncoder2: Custom Rotary Encoder Implementation

## Overview

`RotaryEncoder2` is a customized implementation of a rotary encoder class based on the `RotaryEncoder` class from the `gpiozero` library. This custom class adds support for half-step resolutions and provides more flexibility in handling rotary encoder events. 

The class has been tailored for use in projects where precise rotational measurements are required, such as tracking the position of a knob or dial, with high precision and configurable steps.

## Features

- **Half-Step Support:** The `RotaryEncoder2` class includes support for half-step transitions, allowing for finer resolution in measuring rotational movement.
- **Event Handling:** The class provides event handlers for detecting rotation in both clockwise and counterclockwise directions, as well as generic rotation events.
- **Customizable Steps:** The class allows you to define the number of steps (or increments) that correspond to a full rotation, making it adaptable to different types of rotary encoders.
- **Data Logging:** The provided example script demonstrates how to log rotation data, including timestamps and angles, using pandas.

## Changes from the Original `RotaryEncoder`

The `RotaryEncoder2` class differs from the original `RotaryEncoder` class in the following ways:

1. **Half-Step Mode:** Added support for half-step transitions, which increases the resolution of the encoder by detecting intermediate states.
2. **Simplified Event Handling:** Removed the `event` decorator and implemented custom properties for handling rotation events (`when_rotated`, `when_rotated_clockwise`, and `when_rotated_counter_clockwise`).
3. **Data Logging:** The example script demonstrates how to integrate the encoder with a data logging system using pandas for capturing timestamps and angles during rotation.

## Installation

1. **Download the `encoder.py` file:**
   Place the `encoder.py` file into a directory of your choice, e.g., `ExLibs`.

2. **Ensure Dependencies are Installed:**
   Make sure you have the following libraries installed on your Raspberry Pi:
   - `gpiozero`
   - `pandas`

   You can install these dependencies using pip:
   ```bash
   pip install gpiozero pandas
   ```

## Usage

The following is an example of how to use the `RotaryEncoder2` class in a script:

```python
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
    encoder = RotaryEncoder2(encoder_a, encoder_b, max_steps=360, half_step=True)
    encoder.when_rotated = rotary_changed

def rotary_changed():
    global latest_angle, last_move_time, data
    latest_angle = encoder.steps  # Get the current angle with 0.5 degree resolution
    print(latest_angle)
    timestamp = int(time.time() * 1000)  # Get current time in milliseconds
    new_data = pd.DataFrame({"timestamps": [timestamp], "angles": [latest_angle]})
    data = pd.concat([data, new_data], ignore_index=True)
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
    global data
    data = pd.DataFrame(columns=["timestamps", "angles"])

# Example of how to run the setup and start logging data
setup_encoder()
while True:
    time.sleep(0.1)  # Main loop, do other tasks or just wait
```

### Explanation

1. **Initialization:**
   - The GPIO pins for the rotary encoder are defined (`encoder_a` and `encoder_b`).
   - Global variables are used to store the latest angle and timestamps.

2. **Setting Up the Encoder:**
   - `setup_encoder()` initializes the `RotaryEncoder2` object with the defined GPIO pins and sets up an event handler for rotation.
   - The encoder is configured with `max_steps=360` to represent a full 360-degree rotation.

3. **Event Handling:**
   - `rotary_changed()` is called every time the encoder is rotated. It updates the `latest_angle`, logs the timestamp and angle in a pandas DataFrame, and manages the data to keep only the most recent 3000 entries.

4. **Data Access:**
   - `get_latest_angle()` returns the most recent angle.
   - `get_latest()` returns both the latest angle and the time of the last movement.
   - `get_data()` returns the DataFrame containing the logged timestamps and angles.
   - `clear_data()` clears the logged data.

5. **Main Loop:**
   - The example script includes a main loop that calls `setup_encoder()` and waits, allowing the encoder to run and capture data.

## How to Use

1. **Include the `encoder.py` in Your Project:**
   Make sure `encoder.py` is located in the directory you reference in your script (`ExLibs` in this case).

2. **Modify GPIO Pins:**
   Adjust the `encoder_a` and `encoder_b` variables to match the GPIO pins you are using for the rotary encoder.

3. **Run the Script:**
   Execute your script to start capturing rotation data from the encoder.

## Notes

- Ensure your Raspberry Pi is properly connected to the rotary encoder with appropriate pull-up resistors if needed.
- Adjust the `max_steps` parameter in the `RotaryEncoder2` initialization to match the resolution of your specific rotary encoder.

This README provides a complete overview of how to use the `RotaryEncoder2` class, explaining its features, installation, and usage in a Python script.