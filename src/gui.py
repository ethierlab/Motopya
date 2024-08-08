import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as font
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from signal import pause
import threading
import numpy as np
import time as t
from tkinter.filedialog import askopenfilename
import csv
from datetime import datetime
from datetime import timedelta
import sys

# Functions to be imported
start_session = None
stop_session = None
feed = None
load_parameters = None
save_parameters = None
get_data = None
save_session_data = None
is_in_iti_period = None
get_reference_time = None
get_adapted_values = None
get_trial_counts = None
update_parameters = None
close = None


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


# Create the Tkinter application
root = tk.Tk()
root.title("Rotary Encoder Angle")

# #_______________________________________________________________________________
# GUI
# création de l'interface avec titre et taille de la fenêtre

# définition des valeurs modifiable par des entrés\

session_running = False
session_paused = False
num_pellets = 0
num_rewards = 0
num_trials = 0
running = False

session = {}
parameters = {}

parameters["iniThreshold"] = tk.StringVar(root) #0
parameters["iniBaseline"] = tk.StringVar(root) #1
parameters["minDuration"] = tk.StringVar(root)#2
parameters["hitWindow"] = tk.StringVar(root)#3
parameters["hitThresh"] = tk.StringVar(root)#4
parameters["hitThreshAdapt"] = tk.BooleanVar(root)#5
parameters["hitThreshMin"] = tk.StringVar(root)#6
parameters["hitThreshMax"] = tk.StringVar(root)#7
parameters["leverGain"] = tk.StringVar(root)#8
parameters["forceDrop"] = tk.StringVar(root)#9
parameters["maxTrials"] = tk.StringVar(root)#10
parameters["holdTime"] = tk.StringVar(root)#11
parameters["holdTimeAdapt"] = tk.BooleanVar(root)#12
parameters["holdTimeMin"] = tk.StringVar(root)#13
parameters["holdTimeMax"] = tk.StringVar(root)#14
parameters["saveFolder"]  = tk.StringVar(root)
parameters["ratID"] = tk.StringVar(root)
parameters["iniBaseline"].set("1")


def set_text_bg(frame):
    # Get the background color of the frame
    bg_color = frame.cget("bg")

    # Configure the background color of all text widgets in the frame
    for child in frame.winfo_children():
        if isinstance(child, (tk.Label, tk.Text, tk.Checkbutton)):
            child.config(bg=bg_color)
        # if isinstance(child, (Label, Text, Entry, Checkbutton)):
            # child.config(relief="solid")
        if isinstance(child, (tk.Entry)):
            child.config(width=6)
        if isinstance(child, (tk.Label)) and child["text"] not in ["min", "max", "adapt"]:
            child.config(anchor="e", justify=tk.RIGHT)
            child.grid(sticky="e")
        # if isinstance(child, (Button)):
            # child.config(justify=CENTER)
            # child.grid(sticky="w")
            
            
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
    if min_time['state'] == tk.DISABLED and max_time['state'] == tk.DISABLED:
        min_time['state'] = tk.NORMAL
        max_time['state'] = tk.NORMAL
    elif min_time['state'] == tk.NORMAL and max_time['state'] == tk.NORMAL:
        min_time['state'] = tk.DISABLED
        max_time['state'] = tk.DISABLED

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
    
def is_positive_float(s):
    try:
        float_value = float(s)
        return float_value >= 0
    except ValueError:
        return False
    
def is_boolean(value):
    return isinstance(value, bool)
    

def entry_changed(*args):
    global parameters
    parameters["iniBaseline"].set("1")
    startButton.config(state="disabled")
    for key, value in parameters.items():
        if not value.get() and not is_boolean(value.get()) and key not in ["saveFolder","holdTimeMin", "holdTimeMax", "hitThreshMax", "hitThreshMin"]:
            return False
    #startButton.config(state="normal")
    for key, value in parameters.items():
        if key in ["leverGain", "holdTime", "hitThresh"] :
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
            
    startButton.config(state="normal")
    return True

for value in parameters.values():
    value.trace_add("write", entry_changed)

CadreGauche =tk.Frame(root)
CadreGauche.grid(row=0, column=0, padx=20, pady=20)
vertical_border =tk.Frame(root, width=1, bg="black")
vertical_border.grid(row=0, column=1, sticky="ns")
CadreDroite =tk.Frame(root)
CadreDroite.grid(row=0, column=2, padx=20, pady=20)

# ________________________________________________________________

# définition du cadre de titre

Cadre1 =tk.Frame(CadreGauche)
Cadre1.grid(row=1, column=1)


# Boutons de tests_______________________________________________________________
Title = tk.Label(Cadre1, text="Rat Knob Task", fg='black', justify=tk.CENTER, font=("bold", 25), padx=5, pady=25, width=11, height=1).grid(row=1, column=2)
# lamp = UILamp(Cadre1, diameter=32)
# lamp.grid(row=2, column=4)
# Connect = tk.Button(Cadre1, text="Connect Device", command=connectArduino, width=13, font= ("Serif", 11, "bold")).grid(row=2, column=5)
# Retract = tk.Button(Cadre1, text="Retract\nSensor At Pos", state=tk.DISABLED).grid(row=2, column=5)

# infos sur le rat et la sauvegarde des données
Rat = tk.Label(Cadre1, text="Rat ID:  ", font=("Serif", 11, "bold")).grid(row=2, column=0)
Rat_ID = tk.Entry(Cadre1, width=10, textvariable=parameters["ratID"]).grid(row=2, column=1)

# ________________________________________________________________
# définition du cadre de boutons

Cadre2 =tk.Frame(CadreGauche)
Cadre2.grid(row=3, column=1, sticky="n", pady=(20,20))
Cadre2.grid_rowconfigure(0, pad=10,)
Cadre2.grid_columnconfigure(0, pad=10, weight=1)
Cadre2.grid_columnconfigure(1, pad=10, weight=1)
Cadre2.grid_columnconfigure(2, pad=10, weight=1)
Cadre2.grid_columnconfigure(3, pad=10, weight=1)
timer_running = False
_paused = False
session_running = False

def updateDisplayValues():
    num_trials, num_rewards, num_pellets = get_trial_counts()
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
    else:
        chrono_sec = t.time() - debut - pause_time
        chrono_timeLapse = timedelta(seconds=chrono_sec)
        hours, remainder = divmod(chrono_timeLapse.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        timer_clock.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        
debut = t.time()
def start_button():
    # Déclenche la session comportement
    global session_running, session, max_force, debut, session_paused, running
    session_paused = False
    session_running = True
    running = True
    debut = t.time()
    start_trial()
    
    startButton.config(command=pause_button, text="PAUSE")
    stopButton.config(state = "normal")
    
        
def pause_button():
    global session_paused, pause_start

    session_paused = True
    pause_start = t.time()
    # sendArduino('c')
    startButton.config(command=resume_button, text="RESUME")
    
    
def resume_button():
    global session_paused, pause_time, running
    session_paused = False


    startButton.config(command=pause_button, text="PAUSE")
    running = True
    
def stop_button():
    global session_running, session_paused, running
    running = False
    stop_session()
    session_paused = False
    startButton.config(state="normal",command=start_button, text="START")
    stopButton.config(state="disabled")
    finish_up(False)
    session_running = False
    
def feed_button():
    feed()

def load_parameters_button():
    global parameters
    file_path = tk.filedialog.askopenfilename()
    success, message, parameters_list = load_parameters(file_path)
    display(message)
    if not success:
        return
    for i, key in enumerate(parameters):
        parameters[key].set(parameters_list[i])
        
    if bool(parameters["hitThreshAdapt"].get()):
        min_thresh.config(state="normal")
        max_thresh.config(state="normal")
    else:
        min_thresh.config(state="disabled")
        max_thresh.config(state="disabled")
    if bool(parameters["holdTimeAdapt"].get()):
        min_time.config(state="normal")
        max_time.config(state="normal")
    else:
        min_time.config(state="disabled")
        max_time.config(state="disabled")
    
        
def get_parameters_list():
    parameters_list = []
    for i, key in enumerate(parameters):
        parameters_list.append(parameters[key].get())
    return parameters_list
def save_parameters_button():
    global parameters
    file_path = tk.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return  # User canceled the dialog
    
    parameters_list = get_parameters_list()
    
    display(save_parameters(parameters_list, file_path))
    

def clear_stats():
    startButton.config(text="START")
    

def finish_up(crashed):
    display('Session Ended')
    save_results(crashed)
    clear_stats()

startButton = tk.Button(Cadre2, text="START", background='#64D413', state=tk.DISABLED, command=lambda: start_button())
startButton.grid(row=0, column=0)

stopButton = tk.Button(Cadre2, text="STOP", background='red', state=tk.DISABLED, command=stop_button)
stopButton.grid(row=0, column=1)

    
feedButton = tk.Button(Cadre2, text="FEED", background='#798FD4', state=tk.NORMAL, command=feed_button)
feedButton.grid(row=0, column=2)

removeOffsetButton = tk.Button(Cadre2, text='Remove\nOffset', state=tk.DISABLED)
removeOffsetButton.grid(row=0, column=3)


set_button_size(Cadre2, 10, 2, ('Serif', 10, "bold"))


# ________________________________________________________________
# définition du cadre d'information de trials
# #infos sur les trials, rewards et temps passé
Cadre3 =tk.Frame(CadreDroite)
Cadre3.grid(row=1, column=2)

Cadre3.grid_rowconfigure(0, pad=10,)
Cadre3.grid_columnconfigure(0, pad=10, weight=1)
Cadre3.grid_columnconfigure(1, pad=10, weight=1)
Cadre3.grid_columnconfigure(2, pad=10, weight=1, minsize=100)
Cadre3.grid_columnconfigure(3, pad=10, weight=1)

font = ("Serif", 12, "bold")

TrialsLabel = tk.Label(Cadre3, text="Num Trials:", font=font)
TrialsLabel.grid(row=1, column=0)
Trials = tk.Label(Cadre3, text="0", font=font)
Trials.grid(row=1, column=1)
RewardsLabel = tk.Label(Cadre3, text="Num Rewards:", font=font)
RewardsLabel.grid(row=2, column=0)
Rewards = tk.Label(Cadre3, text="0", font=font)
Rewards.grid(row=2, column=1)
# Med_pick = tk.Label(Cadre3, text="Median Peak:", font="bold").grid(row=2, column=1)
PelletLabel = tk.Label(Cadre3, text="Pellets delivered:", font=font)
PelletLabel.grid(row=1, column=3)
Pellet = tk.Label(Cadre3, text="0 (0.000 g)", font=font)
Pellet.grid(row=1, column=4)
timer_label = tk.Label(Cadre3, text="Time elapsed:", font=("Serif", 14, weight:="bold"),fg="blue")
timer_label.grid(row=2, column=3)
timer_clock = tk.Label(Cadre3, text="00:00:00", font=("Serif", 14,"bold"),fg="blue")
timer_clock.grid(row=2, column=4)


set_sticky(Cadre3)

# ________________________________________________________________
# définition du cadre d'entrées de paramètres
# --------------------------------
Cadre4 =tk.Frame(CadreGauche)
Cadre4.grid(row=2, column=1, padx=20, pady=(0, 20))
# Cadre5.config(borderwidth=2, relief=RIDGE)
Cadre4.config(relief=tk.RIDGE)
Cadre5 =tk.Frame(Cadre4)
Cadre5.grid(row=2, column=0)
# Cadre5.config(borderwidth=2, relief=RIDGE)
Cadre5.config(relief=tk.RIDGE, bg="#e0e0e0")
Cadre5.grid_rowconfigure(0, pad=10,)
Cadre5.grid_rowconfigure(1, pad=10)
Cadre5.grid_rowconfigure(2, pad=10)
Cadre5.grid_rowconfigure(3, pad=10)
Cadre5.grid_rowconfigure(4, pad=10)
Cadre5.grid_rowconfigure(5, pad=10)
Cadre5.grid_rowconfigure(6, pad=10)
Cadre5.grid_columnconfigure(0, pad=10, weight=1)
Cadre5.grid_columnconfigure(1, pad=10, weight=1)
Cadre5.grid_columnconfigure(2, pad=10, weight=1)
Cadre5.grid_columnconfigure(3, pad=10, weight=1)
Cadre5.grid_columnconfigure(4, pad=10, weight=1)
Cadre5.grid_columnconfigure(5, pad=10, weight=1, minsize=60)
Cadre5.grid_columnconfigure(6, pad=10, weight=1)
border =tk.Frame(Cadre4, height=0.3, bg="black")
border.grid(row=1, column=0, sticky="ew")

Parametre = tk.Label(Cadre4, text="Parameters: ", fg='black', justify=tk.LEFT, font="bold").grid(row=0, column=0, sticky="w")

Init_thresh = tk.Label(Cadre5, text="Init thresh (g):").grid(row=0, column=0)
IT = tk.Entry(Cadre5, textvariable = parameters["iniThreshold"]).grid(row=0, column=1)

Hit_window = tk.Label(Cadre5, text="Hit window (s):").grid(row=1, column=0)
HW = tk.Entry(Cadre5, textvariable=parameters["hitWindow"]).grid(row=1, column=1)

Duree = tk.Label(Cadre5, text="Max Duration (min):").grid(row=2, column=0)
min_duration_entry = tk.Entry(Cadre5, textvariable=parameters["minDuration"]).grid(row=2, column=1)

Lever_gain = tk.Label(Cadre5, text="Lever Gain :").grid(row=0, column=4, columnspan=2)
Gain_entry = tk.Entry(Cadre5, textvariable=parameters["leverGain"]).grid(row=0, column=6)

Drop_Tolerance = tk.Label(Cadre5, text="Force Drop Tolerance (g) :").grid(row=1, column=3, columnspan=3)
Drop_entry = tk.Entry(Cadre5, textvariable=parameters["forceDrop"]).grid(row=1, column=6)

Max_Trials = tk.Label(Cadre5, text="Max Trials (num) :").grid(row=2, column=3, columnspan=3)
Max_entry = tk.Entry(Cadre5, textvariable=parameters["maxTrials"]).grid(row=2, column=6)
# Sensor_pos = tk.Label(Cadre5, text="Sensor pos (cm):").grid(row=3, column=1)
# Sensor = tk.Entry(Cadre5).grid(row=3, column=2)

# Init_baseline = tk.Label(Cadre5, text="Init baseline (g):").grid(row=3, column=5)
# IB = tk.Entry(Cadre5, textvariable = iniBaseline).grid(row=3, column=6)

adaptive = tk.Label(Cadre5, text="adapt").grid(row=3, column=2)


# def adapt_thres():

min_label = tk.Label(Cadre5, text="min").grid(row=3, column=3)
min_thresh = tk.Entry(Cadre5, state=tk.DISABLED, textvariable=parameters["hitThreshMin"])
min_thresh.grid(row=4, column=3)
# min_ceiling = tk.Entry(Cadre5, state=tk.DISABLED).grid(row=6, column=4)
min_time = tk.Entry(Cadre5, state=tk.DISABLED, textvariable=parameters["holdTimeMin"])
min_time.grid(row=5, column=3)

max_label = tk.Label(Cadre5, text="max").grid(row=3, column=4)
max_thresh = tk.Entry(Cadre5, state=tk.DISABLED, textvariable=parameters["hitThreshMax"])
max_thresh.grid(row=4, column=4)
# max_ceiling = tk.Entry(Cadre5, state=tk.DISABLED).grid(row=6, column=5)
max_time = tk.Entry(Cadre5, state=tk.DISABLED, textvariable=parameters["holdTimeMax"])
max_time.grid(row=5, column=4)


adapter_threshold = tk.IntVar()
adapt_thresh = tk.Checkbutton(Cadre5, variable=parameters["hitThreshAdapt"], command=lambda: manage_threshold()).grid(row=4, column=2)  # command=manage_threshold
# adapt_ceiling = Checkbutton(Cadre5, state=tk.DISABLED).grid(row=6, column=3)
adapt_time = tk.Checkbutton(Cadre5, variable=parameters["holdTimeAdapt"], command=lambda: manage_time()).grid(row=5, column=2)



Hit_thresh = tk.Label(Cadre5, text="Hit Thresh (g):").grid(row=4, column=0)
HThresh = tk.Entry(Cadre5, textvariable=parameters["hitThresh"]).grid(row=4, column=1)

# Hit_ceiling = tk.Label(Cadre5, text="Hit ceiling (deg):", state=tk.DISABLED).grid(row=6, column=1)
# HC = tk.Entry(Cadre5, state=tk.DISABLED).grid(row=6, column=2)

Hold_time = tk.Label(Cadre5, text="Hold time (s):").grid(row=5, column=0)
HTime = tk.Entry(Cadre5, textvariable=parameters["holdTime"]).grid(row=5, column=1)

loadParametersButton = tk.Button(Cadre5, text="Load", background='white', width=12, command=load_parameters_button)
loadParametersButton.grid(row=6, column=3, columnspan=2)

saveConfigurationButton = tk.Button(Cadre5, text="Save", background='white', width=10, command=save_parameters_button)
saveConfigurationButton.grid(row=6, column=5, columnspan=2)

set_text_bg(Cadre5)

Cadre6 =tk.Frame(CadreDroite)
Cadre6.grid(row=2, column=2)

Title_array = tk.Label(Cadre6, text="Knob Rotation Angle").grid(row=1, column=1, columnspan=2, pady=2)
# fig = plt.Figure(figsize=(3, 2), dpi=211, layout='constrained')
# fig = plt.Figure(figsize=(3, 3), dpi=200)
# ax = fig.add_subplot(111)

# fig.patch.set_facecolor('#f0f0f0')
# canvas = FigureCanvasTkAgg(fig, master=Cadre6)  # tk.DrawingArea.
# canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)


Cadre7 =tk.Frame(CadreGauche)
Cadre7.grid(row=4, column=1, sticky="n", pady=(20,20))


# typeButton = tk.Button(Cadre7, text='Toggle Input Type', command=lambda: toggle_input_type(root, 0))
# typeButton.grid(row=1, column=2)

# Label qui montre des messages
DisplayBox = tk.Label(Cadre7, text="", font=("Serif", 12))
DisplayBox.grid(row=2, column=2, sticky="n", pady=(20,20))

def display(text):
    DisplayBox.config(text=text)

def save_results(crashed):
    # file_input_type = "_RatPull"
    # if not lever_type:
    file_input_type = "_RatKnob"
    if crashed:
        response = messagebox.askyesno("Sorry about that...", "RatPull lever_pull_behavior Crashed!\nSave results?")
    else:
        response = messagebox.askyesno("End of Session", "End of behavioral session\nSave results?")
    if response:
        display((save_session_data())[1])
    

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
canvas = FigureCanvasTkAgg(fig, master=Cadre6)
# canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)

# Create parameter input fields
def create_parameter_input(frame, label, row, default_value):
    tk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
    entry = ttk.Entry(frame)
    entry.grid(row=row, column=1, pady=2)
    entry.insert(0, str(default_value))
    return entry

# iti_entry = create_parameter_input(left_frame, "ITI (s):", 3, iti)

# Start button

def start_trial():
    global init_threshold, hit_duration, hit_threshold, iti, hold_time, post_duration,iniBaseline, session_duration, hit_thresh_adapt, hit_thresh_min, hit_thresh_max
    global hold_time_adapt, hold_time_min, hold_time_max, lever_gain, drop_tolerance, max_trials, save_folder, ratID
    init_threshold = float(parameters["iniThreshold"].get())
    hit_duration = float(parameters["hitWindow"].get())
    hit_threshold = float(parameters["hitThresh"].get())
    # iti = float(iti_entry.get())
    hold_time = float(parameters["holdTime"].get())
    init_threshold_line.set_ydata([init_threshold, init_threshold])
    hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
    hit_duration_line.set_xdata([hit_duration * 1000, hit_duration * 1000])
    iniBaseline = float(parameters["iniBaseline"].get())
    session_duration = float(parameters["minDuration"].get())
    post_duration = float(1)
    hit_thresh_adapt = bool(parameters["hitThreshAdapt"].get())
    hit_thresh_min = float(parameters["hitThreshMin"].get())
    hit_thresh_max = float(parameters["hitThreshMax"].get())
    hold_time_adapt = bool(parameters["holdTimeAdapt"].get())
    hold_time_min = float(parameters["holdTimeMin"].get())
    hold_time_max = float(parameters["holdTimeMax"].get())
    lever_gain = float(parameters["leverGain"].get())
    drop_tolerance = float(parameters["forceDrop"].get())
    max_trials = float(parameters["maxTrials"].get())
    save_folder = str(parameters["saveFolder"].get())
    ratID = str(parameters["ratID"].get())

    init_threshold_line.set_ydata([init_threshold, init_threshold])
    hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
    hit_duration_line.set_xdata([hit_duration * 1000, hit_duration * 1000])

    ax.legend()  # Update legend
    # reset_trial_counts()  # Reset trial counts
    
    
    update_parameters(get_parameters_list())
    
    start_session()  # Start the trials
    
    canvas.draw()


# Define an animation update function
def animate(i):
    global hit_threshold, hold_time, running
    updateDisplayValues()
    if running:
        # Check if in ITI period
        if is_in_iti_period():
            return
        data = get_data()
        
        angles = np.array(data['angles'])
        reference_time = get_reference_time()
        adapted_threshold, adapted_time = get_adapted_values()
        
        if adapted_threshold != None and adapted_time != None:
            hit_threshold = adapted_threshold
            hold_time = adapted_time
            parameters["hitThresh"].set(hit_threshold)
            parameters["holdTime"].set(hold_time)
            init_threshold_line.set_ydata([init_threshold, init_threshold])
            hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
        
        # this is an uncessary loop that needs to be fixed, but good for testing purposes
        timestamps = np.array(data['timestamps']) - reference_time * 1000
        
        
        
        if len(timestamps) > len(angles):
            timestamps = timestamps[:len(angles)]
        elif len(angles) > len(timestamps):
            angles = angles[:len(timestamps)]
        
        
        
        if len(timestamps) > 0:
            ax.set_xlim(-1000, max(timestamps[-1], hit_duration * 1000) + 1000)
            timestamps = np.append(timestamps, (t.time() - reference_time) * 1000)
        if len(angles) > 0:
            ax.set_ylim( -10, max(hit_threshold, max(angles)) + 50)  # Add some padding
            angles = np.append(angles, angles[-1])
        line.set_data(timestamps, angles)
        canvas.draw()
        # Update trial counts
        chronometer(debut)
    
    




# Set button styles
# style = ttk.Style()
# style.configure("Start.TButton", foreground="green", font=("Helvetica", 12))
# style.configure("Stop.TButton", foreground="red", font=("Helvetica", 12))

ani = None

# starts the GUI and takes the necessary functions to call with buttons
def start_gui(start_session_func, stop_session_func, feed_func, load_parameters_func, save_parameters_func, get_data_func, save_session_data_func, is_in_iti_period_func,
              get_reference_time_func, get_adapted_values_func, get_trial_counts_func, update_parameters_func, close_func):
    global start_session, stop_session, feed, load_parameters, save_parameters, get_data, save_session_data, is_in_iti_period, get_reference_time, get_adapted_values
    global get_trial_counts, update_parameters, close, ani
    start_session = start_session_func
    stop_session = stop_session_func
    feed = feed_func
    load_parameters = load_parameters_func
    save_parameters = save_parameters_func
    get_data = get_data_func
    save_session_data = save_session_data_func
    is_in_iti_period = is_in_iti_period_func
    get_reference_time = get_reference_time_func
    get_adapted_values = get_adapted_values_func
    get_trial_counts = get_trial_counts_func
    update_parameters = update_parameters_func
    close = close_func
    # Create an animation
    ani = animation.FuncAnimation(fig, animate, interval=10, cache_frame_data=False)

    # Start the Tkinter main loop
    # root.after(100, pause)  # Allow GPIOZero's pause function to run in the background
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    return

def on_closing():
    global close, ani
    ani.event_source.stop()
    root.quit()
    root.destroy()
    close()
    return
    
