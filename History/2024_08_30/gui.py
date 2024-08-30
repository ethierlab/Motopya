import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as font
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import threading
import numpy as np
import time as t
from tkinter.filedialog import askopenfilename
import csv
from datetime import datetime
from datetime import timedelta
import sys

from ExLibs.utils import is_positive_float, is_int, is_boolean



# Create the Tkinter application
root = tk.Tk()
root.title("Rat Task")

session_running = False
session_paused = False

# Define the values modified by entries
parameters = {}

parameters["iniThreshold"] = tk.StringVar(root) #0
parameters["iniBaseline"] = tk.StringVar(root) #1
parameters["minDuration"] = tk.StringVar(root)#2
parameters["hitWindow"] = tk.StringVar(root)#3
parameters["hitThresh"] = tk.StringVar(root)#4
parameters["hitThreshAdapt"] = tk.BooleanVar(root)#5
parameters["hitThreshMin"] = tk.StringVar(root)#6
parameters["hitThreshMax"] = tk.StringVar(root)#7
parameters["gain"] = tk.StringVar(root)#8
parameters["forceDrop"] = tk.StringVar(root)#9
parameters["maxTrials"] = tk.StringVar(root)#10
parameters["holdTime"] = tk.StringVar(root)#11
parameters["holdTimeAdapt"] = tk.BooleanVar(root)#12
parameters["holdTimeMin"] = tk.StringVar(root)#13
parameters["holdTimeMax"] = tk.StringVar(root)#14
parameters["saveFolder"]  = tk.StringVar(root)
parameters["ratID"] = tk.StringVar(root)
parameters["inputType"] = tk.BooleanVar(root)
parameters["iniBaseline"].set("1")


def configure_rows(frame, max_rows, **kwargs):
    for i in range(max_rows + 1):
        frame.grid_rowconfigure(i, **kwargs)
        
def configure_columns(frame, max_rows, **kwargs):
    for i in range(max_rows + 1):
        frame.grid_columnconfigure(i, **kwargs)

def refresh_input_text(frame, depth):
    for child in frame.winfo_children():
        if isinstance(child, (tk.Label)):
            text = child.cget("text")
            if not parameters["inputType"].get():
                child.config(text=text.replace("(g)", "(deg)").replace("Pull", "Knob"))
            else:
                child.config(text=text.replace("(deg)", "(g)").replace("Knob", "Pull"))
        elif isinstance(child, (tk.Frame)) and child != frame:
            refresh_input_text(child, depth + 1)

def set_text_bg(frame):
    # Get the background color of the frame
    bg_color = frame.cget("bg")

    # Configure the background color of all text widgets in the frame
    for child in frame.winfo_children():
        if isinstance(child, (tk.Label, tk.Text, tk.Checkbutton)):
            child.config(bg=bg_color)
        if isinstance(child, (tk.Entry)):
            child.config(width=6)
        if isinstance(child, (tk.Label)) and child["text"] not in ["min", "max", "adapt"]:
            child.config(anchor="e", justify=tk.RIGHT)
            child.grid(sticky="e")
            
            
def set_button_size(frame, width, height, font):
    for child in frame.winfo_children():
        if isinstance(child, (tk.Button)):
            child.config(width=width, height=height, font=font)
        
def set_sticky(frame):
    # Get the background color of the frame
    bg_color = frame.cget("bg")

    # Configure the background color of all text widgets in the frame
    for child in frame.winfo_children():
        if isinstance(child, (tk.Label)):
            child.grid(sticky="w")
            
def manage_threshold():
    if min_thresh['state'] == tk.DISABLED and max_thresh['state'] == tk.DISABLED:
        min_thresh['state'] = tk.NORMAL
        max_thresh['state'] = tk.NORMAL
    elif min_thresh['state'] == tk.NORMAL and max_thresh['state'] == tk.NORMAL:
        min_thresh['state'] = tk.DISABLED
        max_thresh['state'] = tk.DISABLED

def manage_time():
    if min_time['state'] == tk.DISABLED and max_time_entry['state'] == tk.DISABLED:
        min_time['state'] = tk.NORMAL
        max_time_entry['state'] = tk.NORMAL
    elif min_time['state'] == tk.NORMAL and max_time_entry['state'] == tk.NORMAL:
        min_time['state'] = tk.DISABLED
        max_time_entry['state'] = tk.DISABLED
    

def entry_changed(*args):
    global parameters
    parameters["iniBaseline"].set("1")
    start_button.config(state="disabled")
    for key, value in parameters.items():
        if not value.get() and not is_boolean(value.get()) and key not in ["saveFolder","holdTimeMin", "holdTimeMax", "hitThreshMax", "hitThreshMin"]:
            return False
    for key, value in parameters.items():
        if key in ["gain", "holdTime", "hitThresh"] :
            if not is_positive_float(value.get()):
                return False
        elif key == "holdTimeAdapt":
            if not (is_boolean(value.get())):
                return False
            elif bool(value.get()) == True and not (is_positive_float(parameters["holdTimeMin"].get()) and is_positive_float(parameters["holdTimeMax"].get())):
                return False
        elif key == "hitThreshAdapt":
            if not (is_boolean(value.get())):
                return False
            elif bool(value.get()) == True and not (is_positive_float(parameters["hitThreshMin"].get()) and is_positive_float(parameters["hitThreshMax"].get())):
                return False
            
    start_button.config(state="normal")
    return True

for value in parameters.values():
    value.trace_add("write", entry_changed)

LeftFrame =tk.Frame(root)
LeftFrame.grid(row=0, column=0, padx=20, pady=20)

vertical_border =tk.Frame(root, width=1, bg="black")
vertical_border.grid(row=0, column=1, sticky="ns")

RightFrame =tk.Frame(root)
RightFrame.grid(row=0, column=2, padx=20, pady=20)


# Definition of title frame

Title_Frame =tk.Frame(LeftFrame)
Title_Frame.grid(row=1, column=1)


# Title_______________________________________________________________
title = tk.Label(Title_Frame, text="Rat Knob Task", fg='black', justify=tk.CENTER, font=("bold", 25), padx=5, pady=25, width=11, height=1).grid(row=1, column=2)

# Information on the rat
rat_id_label = tk.Label(Title_Frame, text="Rat ID:  ", font=("Serif", 11, "bold")).grid(row=2, column=0)
rat_id_entry = tk.Entry(Title_Frame, width=10, textvariable=parameters["ratID"]).grid(row=2, column=1)

# ________________________________________________________________
# Definition of control buttons frame

Control_Buttons_Frame =tk.Frame(LeftFrame)
Control_Buttons_Frame.grid(row=3, column=1, sticky="n", pady=(20,20))
Control_Buttons_Frame.grid_rowconfigure(0, pad=10,)
configure_columns(Control_Buttons_Frame, 3, pad=10, weight=1)


timer_running = False
session_paused = False
session_running = False

def updateDisplayValues():
    num_trials, num_rewards, num_pellets = main_functions["get_trial_counts"]()
    Trials.config(text=str(num_trials))
    Rewards.config(text=str(num_rewards))
    Pellet.config(text=f"{num_pellets} ({round(num_pellets * 0.045, 3):.3f} g)")


pause_start = t.time()
pause_time = 0
def chronometer(debut):
    global pause_time
    global pause_start
    if (session_paused):
        pause_time += t.time() - pause_start
        pause_start = t.time()
    elif main_functions["is_running"]():
        chrono_sec = t.time() - debut - pause_time
        chrono_timeLapse = timedelta(seconds=chrono_sec)
        hours, remainder = divmod(chrono_timeLapse.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        timer_clock.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        
debut = t.time()
def start():
    global session_running, session, max_force, debut, session_paused, running
    session_paused = False
    session_running = True
    debut = t.time()
    start_trial()
    
    start_button.config(command=pause, text="PAUSE")
    stop_button.config(state = "normal")
    
        
def pause():
    global session_paused, pause_start

    session_paused = True
    pause_start = t.time()
    start_button.config(command=resume_button, text="RESUME")
    
    
def resume():
    global session_paused, pause_time, running
    session_paused = False

    start_button.config(command=pause_button, text="PAUSE")
    
def remove_offset():
    main_functions["remove_offset"]()
    
def stop():
    global session_running, session_paused, running
    main_functions["stop_session"]()
    session_paused = False
    start_button.config(state="normal",command=start, text="START")
    stop_button.config(state="disabled")
    finish_up(False)
    session_running = False
    
def feed():
    main_functions["feed"]()

def load_parameters_button():
    global parameters, canClose
    canClose = False
    file_path = tk.filedialog.askopenfilename()
    canClose = True
    if not file_path:
        return  # User canceled the dialog
    success, message, parameters_list = main_functions["load_parameters"](file_path)
    display(message)
    if not success:
        return
    for i, key in enumerate(parameters):
        parameters[key].set(parameters_list[i])
        
    if bool(parameters["hitThreshAdapt"].get()):
        min_thresh_entry.config(state="normal")
        max_thresh_entry.config(state="normal")
    else:
        min_thresh_entry.config(state="disabled")
        max_thresh_entry.config(state="disabled")
    if bool(parameters["holdTimeAdapt"].get()):
        min_time_entry.config(state="normal")
        max_time_entry.config(state="normal")
    else:
        min_time_entry.config(state="disabled")
        max_time_entry.config(state="disabled")
        
    refresh_input_text(root, 0)
    
        
def get_parameters_list():
    parameters_list = []
    for i, key in enumerate(parameters):
        parameters_list.append(parameters[key].get())
    return parameters_list

def save_parameters_button():
    global parameters, canClose
    canClose = False
    file_path = tk.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    canClose = True
    if not file_path:
        return  # User canceled the dialog
    
    parameters_list = get_parameters_list()
    
    display(main_functions["save_parameters"](parameters_list, file_path))
    

def clear_stats():
    start_button.config(text="START")
    

def finish_up(crashed):
    display('Session Ended')
    save_results(crashed)
    clear_stats()

start_button = tk.Button(Control_Buttons_Frame, text="START", background='#64D413', state=tk.DISABLED, command=lambda: start())
start_button.grid(row=0, column=0)

stop_button = tk.Button(Control_Buttons_Frame, text="STOP", background='red', state=tk.DISABLED, command=stop)
stop_button.grid(row=0, column=1)

    
feed_button = tk.Button(Control_Buttons_Frame, text="FEED", background='#798FD4', state=tk.NORMAL, command=feed)
feed_button.grid(row=0, column=2)

remove_offset_button = tk.Button(Control_Buttons_Frame, text='Remove\nOffset', command=remove_offset)
remove_offset_button.grid(row=0, column=3)


set_button_size(Control_Buttons_Frame, 10, 2, ('Serif', 10, "bold"))


# ________________________________________________________________
# Definition of trial information frame
Stats_Frame =tk.Frame(RightFrame)
Stats_Frame.grid(row=1, column=2)

Stats_Frame.grid_rowconfigure(0, pad=10,)
configure_columns(Stats_Frame, 3, pad=10, weight=1)
Stats_Frame.grid_columnconfigure(2, pad=10, weight=1, minsize=100)

font = ("Serif", 12, "bold")

TrialsLabel = tk.Label(Stats_Frame, text="Num Trials:", font=font)
TrialsLabel.grid(row=1, column=0)
Trials = tk.Label(Stats_Frame, text="0", font=font)
Trials.grid(row=1, column=1)
RewardsLabel = tk.Label(Stats_Frame, text="Num Rewards:", font=font)
RewardsLabel.grid(row=2, column=0)
Rewards = tk.Label(Stats_Frame, text="0", font=font)
Rewards.grid(row=2, column=1)
PelletLabel = tk.Label(Stats_Frame, text="Pellets delivered:", font=font)
PelletLabel.grid(row=1, column=3)
Pellet = tk.Label(Stats_Frame, text="0 (0.000 g)", font=font)
Pellet.grid(row=1, column=4)
timer_label = tk.Label(Stats_Frame, text="Time elapsed:", font=("Serif", 14, weight:="bold"),fg="blue")
timer_label.grid(row=2, column=3)
timer_clock = tk.Label(Stats_Frame, text="00:00:00", font=("Serif", 14,"bold"),fg="blue")
timer_clock.grid(row=2, column=4)

# Med_pick = tk.Label(Stats_Frame, text="Median Peak:", font="bold").grid(row=2, column=1)

set_sticky(Stats_Frame)

# ________________________________________________________________
# Definition of parameters frame
# --------------------------------
Parameters_Frame =tk.Frame(LeftFrame)
Parameters_Frame.grid(row=2, column=1, padx=20, pady=(0, 20))
Parameters_Frame.config(relief=tk.RIDGE)

Inner_Params_Frame =tk.Frame(Parameters_Frame)
Inner_Params_Frame.grid(row=2, column=0)
Inner_Params_Frame.config(relief=tk.RIDGE, bg="#e0e0e0")

configure_rows(Inner_Params_Frame, 6, pad=10)
configure_columns(Inner_Params_Frame, 6, pad=10, weight=1)
Inner_Params_Frame.grid_columnconfigure(5, pad=10, weight=1, minsize=60)


border =tk.Frame(Parameters_Frame, height=0.3, bg="black")
border.grid(row=1, column=0, sticky="ew")

parameter_label = tk.Label(Parameters_Frame, text="Parameters: ", fg='black', justify=tk.LEFT, font="bold").grid(row=0, column=0, sticky="w")

init_thresh_label  = tk.Label(Inner_Params_Frame, text="Init thresh (g):").grid(row=0, column=0)
init_thresh_entry = tk.Entry(Inner_Params_Frame, textvariable = parameters["iniThreshold"]).grid(row=0, column=1)

hit_window_label  = tk.Label(Inner_Params_Frame, text="Hit window (s):").grid(row=1, column=0)
hit_window_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["hitWindow"]).grid(row=1, column=1)

max_duration_label  = tk.Label(Inner_Params_Frame, text="Max Duration (min):").grid(row=2, column=0)
max_duration_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["minDuration"]).grid(row=2, column=1)

gain_label = tk.Label(Inner_Params_Frame, text="Gain :").grid(row=0, column=4, columnspan=2)
gain_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["gain"]).grid(row=0, column=6)

drop_tolerance_label = tk.Label(Inner_Params_Frame, text="Force Drop Tolerance (g) :").grid(row=1, column=3, columnspan=3)
drop_tolerance_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["forceDrop"]).grid(row=1, column=6)

max_trials_label = tk.Label(Inner_Params_Frame, text="Max Trials (num) :").grid(row=2, column=3, columnspan=3)
max_trials_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["maxTrials"]).grid(row=2, column=6)

adapt_label = tk.Label(Inner_Params_Frame, text="adapt").grid(row=3, column=2)
min_label = tk.Label(Inner_Params_Frame, text="min").grid(row=3, column=3)
max_label = tk.Label(Inner_Params_Frame, text="max").grid(row=3, column=4)


min_thresh_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED, textvariable=parameters["hitThreshMin"])
min_thresh_entry.grid(row=4, column=3)


min_time_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED, textvariable=parameters["holdTimeMin"])
min_time_entry.grid(row=5, column=3)

# min_ceiling_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=4)
# min_ceiling_entry.grid(row=6, column=3)

max_thresh_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED, textvariable=parameters["hitThreshMax"])
max_thresh_entry.grid(row=4, column=4)


max_time_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED, textvariable=parameters["holdTimeMax"])
max_time_entry.grid(row=5, column=4)

# max_ceiling_entry = tk.Entry(Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=5)
# max_ceiling_entry.grid(row=5, column=4)

adapt_thresh_checkbox = tk.Checkbutton(Inner_Params_Frame, variable=parameters["hitThreshAdapt"], command=lambda: manage_threshold()).grid(row=4, column=2)  # command=manage_threshold
adapt_time_checkbox = tk.Checkbutton(Inner_Params_Frame, variable=parameters["holdTimeAdapt"], command=lambda: manage_time()).grid(row=5, column=2)

# adapt_ceiling_checkbox = Checkbutton(Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=3)


hit_thresh_label = tk.Label(Inner_Params_Frame, text="Hit Thresh (g):").grid(row=4, column=0)
hit_thresh_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["hitThresh"]).grid(row=4, column=1)

# Hit_ceiling = tk.Label(Inner_Params_Frame, text="Hit ceiling (deg):", state=tk.DISABLED).grid(row=6, column=1)
# HC = tk.Entry(Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=2)

hold_time_label = tk.Label(Inner_Params_Frame, text="Hold time (s):").grid(row=5, column=0)
hold_time_entry = tk.Entry(Inner_Params_Frame, textvariable=parameters["holdTime"]).grid(row=5, column=1)

load_parameters_button = tk.Button(Inner_Params_Frame, text="Load", background='white', width=12, command=load_parameters_button)
load_parameters_button.grid(row=6, column=3, columnspan=2)

save_configuration_button = tk.Button(Inner_Params_Frame, text="Save", background='white', width=10, command=save_parameters_button)
save_configuration_button.grid(row=6, column=5, columnspan=2)

set_text_bg(Inner_Params_Frame)

Graph_Frame =tk.Frame(RightFrame)
Graph_Frame.grid(row=2, column=2)


Lower_Left_Frame =tk.Frame(LeftFrame)
Lower_Left_Frame.grid(row=4, column=1, sticky="n", pady=(20,20))

def toggle_input_type():
    global parameters
    parameters["inputType"].set(not parameters["inputType"].get())
    refresh_input_text(root, 0)
        
toggle_type_button = tk.Button(Lower_Left_Frame, text='Toggle Input Type', command=lambda: toggle_input_type())
toggle_type_button.grid(row=1, column=2)

# Label that shows messages
display_box = tk.Label(Lower_Left_Frame, text="", font=("Serif", 12))
display_box.grid(row=2, column=2, sticky="n", pady=(20,20))

def display(text):
    display_box.config(text=text)

def save_results(crashed):
    file_input_type = "_RatPull"
    if not parameters["inputType"].get():
        file_input_type = "_RatKnob"
    if crashed:
        response = messagebox.askyesno("Sorry about that...", "RatPull lever_pull_behavior Crashed!\nSave results?")
    else:
        response = messagebox.askyesno("End of Session", "End of behavioral session\nSave results?")
    if response:
        display((main_functions["save_session_data"]())[1])
    

# Create a Matplotlib figure and axis
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_title("Motopya")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Angle (degrees)")
init_threshold_line = ax.axhline(parameters["iniThreshold"].get(), color='red', linestyle='--', label='Init Threshold')
hit_threshold_line = ax.axhline(parameters["hitThresh"].get(), color='green', linestyle='--', label='Hit Threshold')
hit_duration_line = ax.axvline(parameters["hitWindow"].get(), color='black', linestyle='--', label='Hit Duration', linewidth=0.25)
zero_line = ax.axvline(0, color='black', linestyle='--', label='Zero', linewidth=0.25)
zero_line = ax.axhline(0, color='black', linestyle='--', label='Zero', linewidth=0.25)

ax.legend()

# Create a Matplotlib canvas and add it to the right frame
canvas = FigureCanvasTkAgg(fig, master=Graph_Frame)
canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)

# Create parameter input fields
def create_parameter_input(frame, label, row, default_value):
    tk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
    entry = ttk.Entry(frame)
    entry.grid(row=row, column=1, pady=2)
    entry.insert(0, str(default_value))
    return entry

def start_trial():
    init_threshold = float(parameters["iniThreshold"].get())
    hit_duration = float(parameters["hitWindow"].get())
    hit_threshold = float(parameters["hitThresh"].get())
    #Update lines on graph
    init_threshold_line.set_ydata([init_threshold, init_threshold])
    hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
    hit_duration_line.set_xdata([hit_duration * 1000, hit_duration * 1000])

    ax.legend()  # Update legend
    
    
    main_functions["update_parameters"](get_parameters_list())
    main_functions["start_session"]()  # Start the trials
    canvas.draw()


# Define an animation update function
def animate(i):
    if main_functions["is_running"]():
        updateDisplayValues()
        chronometer(debut)
        # Check if in ITI period
        if main_functions["is_in_iti_period"]():
            return
        data = main_functions["get_data"]()
        angles = data['values']
        reference_time = main_functions["get_reference_time"]()
        hit_threshold, hold_time = main_functions["get_adapted_values"]()

        parameters["hitThresh"].set(hit_threshold)
        parameters["holdTime"].set(hold_time)
        init_threshold_line.set_ydata([float(parameters["iniThreshold"].get()), float(parameters["iniThreshold"].get())])
        hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
        
        timestamps = data['timestamps'].values - reference_time * 1000
        
        if len(timestamps) > 0:
            ax.set_xlim(-1000, max(timestamps[-1], float(parameters["hitWindow"].get()) * 1000) + 1000)
            timestamps = np.append(timestamps, (t.time() - reference_time) * 1000)
        if len(angles) > 0:
            ax.set_ylim( -10, max(hit_threshold, angles.max()) + 50)  # Add some padding
            angles = np.append(angles, angles[len(angles) - 1])
            
        line.set_data(timestamps, angles)
        canvas.draw()
    
ani = None

# starts the GUI and takes the necessary functions to call with buttons

main_functions = {}
def start_gui(passed_functions):
    global ani, main_functions
    main_functions = passed_functions

    # Create an animation
    ani = animation.FuncAnimation(fig, animate, interval=10, cache_frame_data=False)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    return

canClose = True
def on_closing():
    global ani
    if not canClose:
        return
    main_functions["close"]()
    root.quit()
    root.destroy()
    return
    
