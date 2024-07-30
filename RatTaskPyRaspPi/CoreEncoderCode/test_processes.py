from gpiozero import RotaryEncoder
from signal import pause
import threading
import time
import os
import psutil
# Define the GPIO pins for the rotary encoder
encoder_a = 24  # Example GPIO pin for A
encoder_b = 25  # Example GPIO pin for B
# Setup the rotary encoder
encoder = RotaryEncoder(encoder_a, encoder_b, max_steps=360, threshold_steps=(10, 90))
print(f"hi we have {os.cpu_count()} cores")
# Define a function to be called when the encoder is rotated
def rotary_changed():
    position = encoder.steps
    print("Position:", position)
# Attach the function to the encoder's when_rotated event
encoder.when_rotated = rotary_changed
# Define a dummy CPU-intensive task
def cpu_intensive_task():
    while True:
        # Perform a dummy computation to keep the CPU busy
        result = sum(i*i for i in range(100000))
        # Sleep for a short period to avoid complete CPU hogging
        time.sleep(0.1)
# Define a function to print CPU load
def print_cpu_load():
    while True:
        cpu_load = psutil.cpu_percent(interval=1, percpu=False)
        print(f"CPU Load: {4*cpu_load}%")
        print(encoder.steps)
# Start as many CPU-intensive tasks as possible
num_cores = os.cpu_count()
threads = []
for _ in range(num_cores * 4):  # Attempt to start twice as many tasks as there are CPU cores
    cpu_thread = threading.Thread(target=cpu_intensive_task)
    cpu_thread.daemon = True
    cpu_thread.start()
    threads.append(cpu_thread)
# Start the CPU load monitoring in a separate thread
cpu_load_thread = threading.Thread(target=print_cpu_load)
cpu_load_thread.daemon = True
cpu_load_thread.start()
# Wait for the interrupt
pause()

