import tkinter as tk
from tkinter import ttk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from signal import pause
from rotary_encoder import setup_encoder, get_latest_angle, get_angles, get_timestamps, trial_start, get_trial_start
from trial_logic import trial_logic, get_trial_counts, reset_trial_counts, is_in_iti_period, is_trial_started, get_reference_time
import threading
import numpy as np
import time as t
# Initialize trial parameters
init_threshold = 50
hit_duration = 5
hit_threshold = 100
hold_time = 1
post_duration = 1
iti = 1

# Create the Tkinter application
root = tk.Tk()
root.title("Rotary Encoder Angle")

# Create the left frame for parameters
left_frame = ttk.Frame(root, padding="10")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the right frame for the plot and trial counts
right_frame = ttk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Create a frame for the trial counts at the top of the right frame
trial_count_frame = ttk.Frame(right_frame)
trial_count_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

# Create labels for the trial counts
num_trials_label = ttk.Label(trial_count_frame, text="Number of Trials: 0")
num_trials_label.pack(side=tk.LEFT, padx=10)
num_success_label = ttk.Label(trial_count_frame, text="Number of Success: 0")
num_success_label.pack(side=tk.LEFT, padx=10)

# Create a Matplotlib figure and axis
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_title("Motopya")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Angle (degrees)")
init_threshold_line = ax.axhline(init_threshold, color='red', linestyle='--', label='Init Threshold')
hit_threshold_line = ax.axhline(hit_threshold, color='green', linestyle='--', label='Hit Threshold')
zero_line = ax.axvline(0, color='black', linestyle='--', label='Zero', linewidth=0.25)
zero_line = ax.axhline(0, color='black', linestyle='--', label='Zero', linewidth=0.25)
hit_duration_line = ax.axvline(hit_threshold, color='black', linestyle='--', label='Hit Duration', linewidth=0.25)
ax.legend()

# Create a Matplotlib canvas and add it to the right frame
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

# Create parameter input fields
def create_parameter_input(frame, label, row, default_value):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
    entry = ttk.Entry(frame)
    entry.grid(row=row, column=1, pady=2)
    entry.insert(0, str(default_value))
    return entry

init_threshold_entry = create_parameter_input(left_frame, "Init Threshold (deg):", 0, init_threshold)
hit_duration_entry = create_parameter_input(left_frame, "Hit Duration (s):", 1, hit_duration)
hit_threshold_entry = create_parameter_input(left_frame, "Hit Threshold (deg):", 2, hit_threshold)
iti_entry = create_parameter_input(left_frame, "ITI (s):", 3, iti)
hold_time_entry = create_parameter_input(left_frame, "Hold Time (s):", 4, hold_time)

# Start button
def start_trial():
    global init_threshold, hit_duration, hit_threshold, iti, hold_time
    init_threshold = float(init_threshold_entry.get())
    hit_duration = float(hit_duration_entry.get())
    hit_threshold = float(hit_threshold_entry.get())
    iti = float(iti_entry.get())
    hold_time = float(hold_time_entry.get())
    init_threshold_line.set_ydata([init_threshold, init_threshold])
    hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
    hit_duration_line.set_xdata([hit_duration * 1000, hit_duration * 1000])
    ax.legend()  # Update legend
    reset_trial_counts()  # Reset trial counts
    start_trials()  # Start the trials
    canvas.draw()

# Function to start the trials
def start_trials():
    global running
    running = True

start_button = ttk.Button(left_frame, text="Start Trial", command=start_trial, style="Start.TButton")
start_button.grid(row=5, columnspan=2, pady=10)

# Function to stop the trials
def stop_trials():
    global running
    running = False

stop_button = ttk.Button(left_frame, text="Stop Trial", command=stop_trials, style="Stop.TButton")
stop_button.grid(row=6, columnspan=2, pady=10)

# Set up the rotary encoder
setup_encoder()

# Initialize running state
running = False

# Define an animation update function
def animate(i):
    if running:
#         trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration)
        # Check if in ITI period
        if is_in_iti_period():
            return
        angles = get_angles()
        
        reference_time = get_reference_time()
        
        #this is an uncessary loop to fix, but good for testing purposes
        timestamps = np.array(get_timestamps()) - reference_time * 1000
        if len(timestamps) > len(angles):
            timestamps = timestamps[:len(angles)]
        elif len(angles) > len(timestamps):
            angles = angles[:len(timestamps)]
        
        line.set_data(timestamps, angles)
        
        if len(timestamps) > 0:
#             ax.set_xlim(timestamps[0] - 1, timestamps[-1] + 1)
            ax.set_xlim(-1000, max(timestamps[-1], hit_duration * 1000) + 1000)
        if len(angles) > 0:
            #ax.set_ylim(min(angles) - 1, max(angles) + 1)  # Add some padding
            ax.set_ylim(min(min(angles), 0) -10, max(hit_threshold, max(angles)) + 10)  # Add some padding
        canvas.draw()
        # Update trial counts
        num_trials, num_success = get_trial_counts()
        num_trials_label.config(text=f"Number of Trials: {num_trials}")
        num_success_label.config(text=f"Number of Success: {num_success}")

def run_logic():
    print("running logic")
    while True:
        trial_logic(init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration)
        t.sleep(0.001)
    

# Create an animation
ani = animation.FuncAnimation(fig, animate, interval=10)
logic = threading.Thread(target=run_logic)
logic.start()

# Set button styles
style = ttk.Style()
style.configure("Start.TButton", foreground="green", font=("Helvetica", 12))
style.configure("Stop.TButton", foreground="red", font=("Helvetica", 12))

# Start the Tkinter main loop
# root.after(100, pause)  # Allow GPIOZero's pause function to run in the background
root.mainloop()
