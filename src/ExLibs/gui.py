import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as font
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import threading
import numpy as np
import time as t
from ExLibs.clock import clock
from tkinter.filedialog import askopenfilename
import csv
from datetime import datetime
from datetime import timedelta
import sys

from ExLibs.utils import is_float, is_positive_float, is_int, is_boolean, is_percentage_range, is_positive_range

class RatTaskGUI():
    def __init__(self, passed_functions):
        self.main_functions = passed_functions
        
        # Create the Tkinter application
        self.root = tk.Tk()
        self.root.title("Rat Task")
        self.session_running = False

        # Define the values modified by entries
        self.parameters = {}

        self.parameters["iniThreshold"] = tk.StringVar(self.root) #0
        self.parameters["iniBaseline"] = tk.StringVar(self.root) #1
        self.parameters["minDuration"] = tk.StringVar(self.root)#2
        self.parameters["hitWindow"] = tk.StringVar(self.root)#3
        self.parameters["hitThresh"] = tk.StringVar(self.root)#4
        self.parameters["hitThreshAdapt"] = tk.BooleanVar(self.root)#5
        self.parameters["hitThreshMin"] = tk.StringVar(self.root)#6
        self.parameters["hitThreshMax"] = tk.StringVar(self.root)#7
        self.parameters["gain"] = tk.StringVar(self.root)#8
        self.parameters["useDropTol"] = tk.BooleanVar(self.root)
        self.parameters["forceDrop"] = tk.StringVar(self.root)#9
        self.parameters["maxTrials"] = tk.StringVar(self.root)#10
        self.parameters["holdTime"] = tk.StringVar(self.root)#11
        self.parameters["holdTimeAdapt"] = tk.BooleanVar(self.root)#12
        self.parameters["holdTimeMin"] = tk.StringVar(self.root)#13
        self.parameters["holdTimeMax"] = tk.StringVar(self.root)#14
        self.parameters["saveFolder"]  = tk.StringVar(self.root)
        self.parameters["ratID"] = tk.StringVar(self.root)
        self.parameters["inputType"] = tk.BooleanVar(self.root)
        self.parameters["iniBaseline"].set("1")
        
        
        
        self.parameters["minThreshAdapt"] = tk.StringVar(self.root)
        self.parameters["maxThreshAdapt"] = tk.StringVar(self.root)
        
        self.parameters["minTimeAdapt"] = tk.StringVar(self.root)
        self.parameters["maxTimeAdapt"] = tk.StringVar(self.root)
        
        self.parameters["postTrialDuration"] = tk.StringVar(self.root)
        self.parameters["interTrialDuration"] = tk.StringVar(self.root)
        
        for value in self.parameters.values():
            value.trace_add("write", self.entry_changed)
            
        
            
        self.debut = clock.time()
        self.ani = None
        self.canClose = True
        self.timer_running = False
        self.session_running = False
        self.create_frames()
        self.paused = False
        
        self.session_running = False
        
        
        parameters_list = self.main_functions["get_parameters_list"]()
        for i, key in enumerate(self.parameters):
            self.parameters[key].set(parameters_list[i])
        
        
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=10, cache_frame_data=False)

        # Start the Tkinter main loop
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
        
    def create_frames(self):
        self.LeftFrame =tk.Frame(self.root)
        self.LeftFrame.grid(row=0, column=0, padx=20, pady=20)

        self.vertical_border =tk.Frame(self.root, width=1, bg="black")
        self.vertical_border.grid(row=0, column=1, sticky="ns")

        self.RightFrame =tk.Frame(self.root)
        self.RightFrame.grid(row=0, column=2, padx=20, pady=20)
        # Definition of title frame

        self.Title_Frame =tk.Frame(self.LeftFrame)
        self.Title_Frame.grid(row=1, column=1)


        # Title_______________________________________________________________
        self.title = tk.Label(self.Title_Frame, text="Rat Knob Task", fg='black', justify=tk.CENTER, font=("bold", 25), padx=5, pady=25, width=11, height=1).grid(row=1, column=2)

        # Information on the rat
        self.rat_id_label = tk.Label(self.Title_Frame, text="Rat ID:  ", font=("Serif", 11, "bold")).grid(row=2, column=0)
        self.rat_id_entry = tk.Entry(self.Title_Frame, width=10, textvariable=self.parameters["ratID"]).grid(row=2, column=1)

        # ________________________________________________________________
        # Definition of control buttons frame

        self.Control_Buttons_Frame =tk.Frame(self.LeftFrame)
        self.Control_Buttons_Frame.grid(row=3, column=1, sticky="n", pady=(20,20))
        self.Control_Buttons_Frame.grid_rowconfigure(0, pad=10,)
        self.configure_columns(self.Control_Buttons_Frame, 3, pad=10, weight=1)
        self.start_button = tk.Button(self.Control_Buttons_Frame, text="START", background='#64D413', state=tk.DISABLED, command=lambda: self.start())
        self.start_button.grid(row=0, column=0)

        self.stop_button = tk.Button(self.Control_Buttons_Frame, text="STOP", background='red', state=tk.DISABLED, command=self.stop)
        self.stop_button.grid(row=0, column=1)

            
        self.feed_button = tk.Button(self.Control_Buttons_Frame, text="FEED", background='#798FD4', state=tk.NORMAL, command=self.feed)
        self.feed_button.grid(row=0, column=2)

        self.remove_offset_button = tk.Button(self.Control_Buttons_Frame, text='Remove\nOffset', command=self.remove_offset)
        self.remove_offset_button.grid(row=0, column=3)


        self.set_button_size(self.Control_Buttons_Frame, 10, 2, ('Serif', 10, "bold"))


        # ________________________________________________________________
        # Definition of trial information frame
        self.Stats_Frame =tk.Frame(self.RightFrame)
        self.Stats_Frame.grid(row=1, column=2)

        self.Stats_Frame.grid_rowconfigure(0, pad=10,)
        self.configure_columns(self.Stats_Frame, 3, pad=10, weight=1)
        self.Stats_Frame.grid_columnconfigure(2, pad=10, weight=1, minsize=100)

        font = ("Serif", 12, "bold")

        self.trials_label = tk.Label(self.Stats_Frame, text="Num Trials:", font=font)
        self.trials_label.grid(row=1, column=0)
        self.trials_num_label = tk.Label(self.Stats_Frame, text="0", font=font)
        self.trials_num_label.grid(row=1, column=1)
        self.rewards_label = tk.Label(self.Stats_Frame, text="Num Rewards:", font=font)
        self.rewards_label.grid(row=2, column=0)
        self.rewards_num_label = tk.Label(self.Stats_Frame, text="0", font=font)
        self.rewards_num_label.grid(row=2, column=1)
        self.pellets_label = tk.Label(self.Stats_Frame, text="Pellets delivered:", font=font)
        self.pellets_label.grid(row=1, column=3)
        self.pellets_num_label = tk.Label(self.Stats_Frame, text="0 (0.000 g)", font=font)
        self.pellets_num_label.grid(row=1, column=4)
        self.timer_label = tk.Label(self.Stats_Frame, text="Time elapsed:", font=("Serif", 14, weight:="bold"),fg="blue")
        self.timer_label.grid(row=2, column=3)
        self.timer_clock = tk.Label(self.Stats_Frame, text="00:00:00", font=("Serif", 14,"bold"),fg="blue")
        self.timer_clock.grid(row=2, column=4)

        # Med_pick = tk.Label(self.Stats_Frame, text="Median Peak:", font="bold").grid(row=2, column=1)

        self.set_sticky(self.Stats_Frame)

        # ________________________________________________________________
        # Definition of self.parameters frame
        # --------------------------------
        self.parameters_Frame =tk.Frame(self.LeftFrame)
        self.parameters_Frame.grid(row=2, column=1, padx=20, pady=(0, 20))
        self.parameters_Frame.config(relief=tk.RIDGE)

        self.Inner_Params_Frame =tk.Frame(self.parameters_Frame)
        self.Inner_Params_Frame.grid(row=2, column=0)
        self.Inner_Params_Frame.config(relief=tk.RIDGE, bg="#e0e0e0")

        self.configure_rows(self.Inner_Params_Frame, 6, pad=10)
        self.configure_columns(self.Inner_Params_Frame, 6, pad=10, weight=1)
        self.Inner_Params_Frame.grid_columnconfigure(5, pad=10, weight=1, minsize=60)


        self.border =tk.Frame(self.parameters_Frame, height=0.3, bg="black")
        self.border.grid(row=1, column=0, sticky="ew")

        self.parameter_label = tk.Label(self.parameters_Frame, text="Parameters: ", fg='black', justify=tk.LEFT, font="bold").grid(row=0, column=0, sticky="w")

        self.init_thresh_label  = tk.Label(self.Inner_Params_Frame, text="Init thresh (g):").grid(row=0, column=0)
        self.init_thresh_entry = tk.Entry(self.Inner_Params_Frame, textvariable = self.parameters["iniThreshold"]).grid(row=0, column=1)

        self.hit_window_label  = tk.Label(self.Inner_Params_Frame, text="Hit window (s):").grid(row=1, column=0)
        self.hit_window_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["hitWindow"]).grid(row=1, column=1)

        self.max_duration_label  = tk.Label(self.Inner_Params_Frame, text="Max Duration (min):").grid(row=2, column=0)
        self.max_duration_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["minDuration"]).grid(row=2, column=1)
        
        self.max_trials_label = tk.Label(self.Inner_Params_Frame, text="Max Trials (num) :").grid(row=0, column=2, columnspan=2)
        self.max_trials_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["maxTrials"]).grid(row=0, column=4)

        self.gain_label = tk.Label(self.Inner_Params_Frame, text="Gain :").grid(row=0, column=4, columnspan=2)
        self.gain_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["gain"]).grid(row=0, column=6)
        
        self.tolerance_label = tk.Label(self.Inner_Params_Frame, text="Tolerance:").grid(row=1, column=2, columnspan=2)
        self.tolerance_checkbox = tk.Checkbutton(self.Inner_Params_Frame, variable=self.parameters["useDropTol"]).grid(row=1, column=4)

        self.drop_tolerance_label = tk.Label(self.Inner_Params_Frame, text="Drop (g) :").grid(row=1, column=4, columnspan=2)
        self.drop_tolerance_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["forceDrop"]).grid(row=1, column=6)

        

        self.adapt_label = tk.Label(self.Inner_Params_Frame, text="adapt").grid(row=3, column=2)
        self.min_label = tk.Label(self.Inner_Params_Frame, text="min").grid(row=3, column=3)
        self.max_label = tk.Label(self.Inner_Params_Frame, text="max").grid(row=3, column=4)
        self.min_adapt_label = tk.Label(self.Inner_Params_Frame, text="Raise (%)").grid(row=3, column=5)
        self.max_adapt_label = tk.Label(self.Inner_Params_Frame, text="Lower (%)").grid(row=3, column=6)

        self.min_thresh_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["hitThreshMin"])
        self.min_thresh_entry.grid(row=4, column=3)


        self.min_time_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["holdTimeMin"])
        self.min_time_entry.grid(row=5, column=3)

        # min_ceiling_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=4)
        # min_ceiling_entry.grid(row=6, column=3)

        self.max_thresh_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["hitThreshMax"])
        self.max_thresh_entry.grid(row=4, column=4)


        self.max_time_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["holdTimeMax"])
        self.max_time_entry.grid(row=5, column=4)
        
        
        
        self.min_thresh_adapt_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["minThreshAdapt"])
        self.min_thresh_adapt_entry.grid(row=4, column=5)


        self.min_time_adapt_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["minTimeAdapt"])
        self.min_time_adapt_entry.grid(row=5, column=5)


        self.max_thresh_adapt_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["maxThreshAdapt"])
        self.max_thresh_adapt_entry.grid(row=4, column=6)


        self.max_time_adapt_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED, textvariable=self.parameters["maxTimeAdapt"])
        self.max_time_adapt_entry.grid(row=5, column=6)
        
        # max_ceiling_entry = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=5)
        # max_ceiling_entry.grid(row=5, column=4)

        self.adapt_thresh_checkbox = tk.Checkbutton(self.Inner_Params_Frame, variable=self.parameters["hitThreshAdapt"], command=lambda: self.manage_threshold()).grid(row=4, column=2)
        self.adapt_time_checkbox = tk.Checkbutton(self.Inner_Params_Frame, variable=self.parameters["holdTimeAdapt"], command=lambda: self.manage_time()).grid(row=5, column=2)

        # adapt_ceiling_checkbox = Checkbutton(self.Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=3)


        self.hit_thresh_label = tk.Label(self.Inner_Params_Frame, text="Hit Thresh (g):").grid(row=4, column=0)
        self.hit_thresh_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["hitThresh"]).grid(row=4, column=1)

        # Hit_ceiling = tk.Label(self.Inner_Params_Frame, text="Hit ceiling (deg):", state=tk.DISABLED).grid(row=6, column=1)
        # HC = tk.Entry(self.Inner_Params_Frame, state=tk.DISABLED).grid(row=6, column=2)

        self.hold_time_label = tk.Label(self.Inner_Params_Frame, text="Hold time (s):").grid(row=5, column=0)
        self.hold_time_entry = tk.Entry(self.Inner_Params_Frame, textvariable=self.parameters["holdTime"]).grid(row=5, column=1)

        self.load_parameters = tk.Button(self.Inner_Params_Frame, text="Load", background='white', width=12, command=self.load_parameters_button)
        self.load_parameters.grid(row=6, column=0, columnspan=2)

        self.save_configuration_button = tk.Button(self.Inner_Params_Frame, text="Save", background='white', width=10, command=self.save_parameters_button)
        self.save_configuration_button.grid(row=7, column=0, columnspan=2)
        
        self.calibrate_lever_button = tk.Button(self.Inner_Params_Frame, text="Calibrate Lever", background='white', width=10, command=self.open_calibration, state=tk.DISABLED)
        self.calibrate_lever_button.grid(row=6, column=5, columnspan=2)
        
        self.advanced_configuration_button = tk.Button(self.Inner_Params_Frame, text="Advanced", background='white', width=10, command=self.open_advanced)
        self.advanced_configuration_button.grid(row=7, column=5, columnspan=2)

        self.set_text_bg(self.Inner_Params_Frame)

        self.Graph_Frame =tk.Frame(self.RightFrame)
        self.Graph_Frame.grid(row=2, column=2)


        self.Lower_Left_Frame =tk.Frame(self.LeftFrame)
        self.Lower_Left_Frame.grid(row=4, column=1, sticky="n", pady=(20,20))
        
        
        self.toggle_type_button = tk.Button(self.Lower_Left_Frame, text='Toggle Input Type', command=lambda: self.toggle_input_type())
        self.toggle_type_button.grid(row=1, column=2)

        # Label that shows messages
        self.display_box = tk.Label(self.Lower_Left_Frame, text="", font=("Serif", 12))
        self.display_box.grid(row=2, column=2, sticky="n", pady=(20,20))

        # Create a Matplotlib self.figure and self.axis
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], lw=2)
        self.ax.set_title("Motopya")
        self.ax.set_xlabel("Time (ms)")
        self.ax.set_ylabel("Angle (degrees)")
        self.init_threshold_line = self.ax.axhline(self.parameters["iniThreshold"].get(), color='red', linestyle='--', label='Init Threshold')
        self.hit_threshold_line = self.ax.axhline(self.parameters["hitThresh"].get(), color='green', linestyle='--', label='Hit Threshold')
        self.hit_duration_line = self.ax.axvline(self.parameters["hitWindow"].get(), color='black', linestyle='--', label='Hit Duration', linewidth=0.25)
        self.zero_line = self.ax.axvline(0, color='black', linestyle='--', linewidth=0.25)
        self.zero_line = self.ax.axhline(0, color='black', linestyle='--', linewidth=0.25)

        self.ax.legend()

        # Create a Matplotlib canvas and add it to thTe right frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.Graph_Frame)
        self.canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)

    def configure_rows(self, frame, max_rows, **kwargs):
        for i in range(max_rows + 1):
            frame.grid_rowconfigure(i, **kwargs)
            
    def configure_columns(self, frame, max_rows, **kwargs):
        for i in range(max_rows + 1):
            frame.grid_columnconfigure(i, **kwargs)

    def refresh_input_text(self, frame, depth):
        if self.parameters["inputType"].get():
            self.calibrate_lever_button.config(state="normal")
        else:
            self.calibrate_lever_button.config(state="disabled")
        
        for child in frame.winfo_children():
            if isinstance(child, (tk.Label)):
                text = child.cget("text")
                if not self.parameters["inputType"].get():
                    child.config(text=text.replace("(g)", "(deg)").replace("Pull", "Knob"))
                else:
                    child.config(text=text.replace("(deg)", "(g)").replace("Knob", "Pull"))
            elif isinstance(child, (tk.Frame)) and child != frame:
                self.refresh_input_text(child, depth + 1)

    def set_text_bg(self, frame):
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
                
                
    def set_button_size(self, frame, width, height, font):
        for child in frame.winfo_children():
            if isinstance(child, (tk.Button)):
                child.config(width=width, height=height, font=font)
            
    def set_sticky(self, frame):
        # Get the background color of the frame
        bg_color = frame.cget("bg")

        # Configure the background color of all text widgets in the frame
        for child in frame.winfo_children():
            if isinstance(child, (tk.Label)):
                child.grid(sticky="w")
                
    def manage_threshold(self):
        if self.min_thresh_entry['state'] == tk.DISABLED and self.max_thresh_entry['state'] == tk.DISABLED:
            self.min_thresh_entry['state'] = tk.NORMAL
            self.max_thresh_entry['state'] = tk.NORMAL
            self.min_thresh_adapt_entry['state'] = tk.NORMAL
            self.max_thresh_adapt_entry['state'] = tk.NORMAL
        elif self.min_thresh_entry['state'] == tk.NORMAL and self.max_thresh_entry['state'] == tk.NORMAL:
            self.min_thresh_entry['state'] = tk.DISABLED
            self.max_thresh_entry['state'] = tk.DISABLED
            self.min_thresh_adapt_entry['state'] = tk.DISABLED
            self.max_thresh_adapt_entry['state'] = tk.DISABLED

    def manage_time(self):
        if self.min_time_entry['state'] == tk.DISABLED and self.max_time_entry['state'] == tk.DISABLED:
            self.min_time_entry['state'] = tk.NORMAL
            self.max_time_entry['state'] = tk.NORMAL
            self.min_time_adapt_entry['state'] = tk.NORMAL
            self.max_time_adapt_entry['state'] = tk.NORMAL
        elif self.min_time_entry['state'] == tk.NORMAL and self.max_time_entry['state'] == tk.NORMAL:
            self.min_time_entry['state'] = tk.DISABLED
            self.max_time_entry['state'] = tk.DISABLED
            self.min_time_adapt_entry['state'] = tk.DISABLED
            self.max_time_adapt_entry['state'] = tk.DISABLED
        

    def entry_changed(self, *args):
        self.parameters["iniBaseline"].set("1")
        self.start_button.config(state="disabled")
        self.refresh_input_text(self.root, 0)
        for key, value in self.parameters.items():
            if not value.get() and not is_boolean(value.get()) and key not in ["saveFolder","holdTimeMin", "holdTimeMax", "hitThreshMax", "hitThreshMin", "forceDrop"]:
                return False
        for key, value in self.parameters.items():
            if key in ["holdTime", "hitThresh", "postTrialDuration", "interTrialDuration", "minDuration"] :
                if not is_positive_float(value.get()):
                    return False
            elif key in ["gain"] :
                if not is_float(value.get()):
                    return False
            elif key == "holdTimeAdapt":
                if not (is_boolean(value.get())):
                    return False
                elif (bool(value.get()) == True and not (is_positive_range(self.parameters["holdTimeMin"].get(),self.parameters["holdTimeMax"].get()) and
                is_percentage_range(self.parameters["minTimeAdapt"].get(), self.parameters["maxTimeAdapt"].get())) ):
                    return False
            elif key == "hitThreshAdapt":
                if not (is_boolean(value.get())):
                    return False
                elif (bool(value.get()) == True and not (is_positive_range(self.parameters["hitThreshMin"].get(),self.parameters["hitThreshMax"].get()) and
                is_percentage_range(self.parameters["minThreshAdapt"].get(), self.parameters["maxThreshAdapt"].get()))):
                    return False
            elif key == "useDropTol":
                if not (is_boolean(value.get())):
                    return False
                elif (bool(value.get()) == True and not (is_positive_float(self.parameters["forceDrop"].get()))):
                    return False
            elif key not in ["saveFolder","holdTimeMin", "holdTimeMax", "hitThreshMax", "hitThreshMin", "forceDrop"]:
                if not (is_int(value.get())):
                    return False
                
        self.start_button.config(state="normal")
        return True

    def updateDisplayValues(self):
        num_trials, num_rewards, num_pellets = self.main_functions["get_trial_counts"]()
        self.trials_num_label.config(text=str(num_trials))
        self.rewards_num_label.config(text=str(num_rewards))
        self.pellets_num_label.config(text=f"{num_pellets} ({round(num_pellets * 0.045, 3):.3f} g)")



    def chronometer(self, debut):
        if self.main_functions["is_running"]():
            chrono_sec = clock.time() - self.debut
            chrono_timeLapse = timedelta(seconds=chrono_sec)
            hours, remainder = divmod(chrono_timeLapse.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            self.timer_clock.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
            

    def start(self):
        self.session_running = True
        self.debut = clock.time()
        self.start_trial()
        
        self.start_button.config(command=self.pause, text="PAUSE")
        self.stop_button.config(state = "normal")
        
            
    def pause(self):
        self.paused = True
        clock.pause()
        self.start_button.config(command=self.resume, text="RESUME")
        
        
    def resume(self):
        self.paused = False
        clock.resume()
        self.start_button.config(command=self.pause, text="PAUSE")
        
    def remove_offset(self):
        self.main_functions["remove_offset"]()
        
    def stop(self):
        self.session_running = False
        self.main_functions["stop_session"]()
        self.start_button.config(state="normal",command=self.start, text="START")
        self.stop_button.config(state="disabled")
        self.finish_up(False)
        self.session_running = False
        
    def feed(self):
        self.main_functions["feed"]()

    def load_parameters_button(self):
        self.canClose = False
        file_path = tk.filedialog.askopenfilename()
        self.canClose = True
        if not file_path:
            return  # User canceled the dialog
        success, message, parameters_list = self.main_functions["load_parameters"](file_path)
        self.display(message)
        if not success:
            return
        for i, key in enumerate(self.parameters):
            self.parameters[key].set(parameters_list[i])
            
        if bool(self.parameters["hitThreshAdapt"].get()):
            self.min_thresh_entry.config(state="normal")
            self.max_thresh_entry.config(state="normal")
        else:
            self.min_thresh_entry.config(state="disabled")
            self.max_thresh_entry.config(state="disabled")
        if bool(self.parameters["holdTimeAdapt"].get()):
            self.min_time_entry.config(state="normal")
            self.max_time_entry.config(state="normal")
        else:
            self.min_time_entry.config(state="disabled")
            self.max_time_entry.config(state="disabled")
            
        self.refresh_input_text(self.root, 0)
        
            
    def get_parameters_list(self):
        parameters_list = []
        for i, key in enumerate(self.parameters):
            parameters_list.append(self.parameters[key].get())
        return parameters_list

    def save_parameters_button(self):
        self.canClose = False
        file_path = tk.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        self.canClose = True
        if not file_path:
            return  # User canceled the dialog
        
        parameters_list = self.get_parameters_list()
        
        self.display(self.main_functions["save_parameters"](parameters_list, file_path))
        

    def clear_stats(self):
        self.start_button.config(text="START")
        

    def finish_up(self, crashed):
        self.display('Session Ended')
        self.save_results(crashed)
        self.clear_stats()



    def toggle_input_type(self):
        self.parameters["inputType"].set(not self.parameters["inputType"].get())
        self.refresh_input_text(self.root, 0)
            

    def display(self, text):
        self.display_box.config(text=text)

    def save_results(self, crashed):
        file_input_type = "_RatPull"
        if not self.parameters["inputType"].get():
            file_input_type = "_RatKnob"
        if crashed:
            response = messagebox.askyesno("Sorry about that...", "RatPull lever_pull_behavior Crashed!\nSave results?")
        else:
            response = messagebox.askyesno("End of Session", "End of behavioral session\nSave results?")
        if response:
            self.display((self.main_functions["save_session_data"]())[1])
        



    # Create parameter input fields
    def create_parameter_input(self, frame, label, row, default_value):
        tk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(frame)
        entry.grid(row=row, column=1, pady=2)
        entry.insert(0, str(default_value))
        return entry

    def start_trial(self):
        self.session_running = True
        init_threshold = float(self.parameters["iniThreshold"].get())
        hit_duration = float(self.parameters["hitWindow"].get())
        hit_threshold = float(self.parameters["hitThresh"].get())
        #Update lines on graph
        self.init_threshold_line.set_ydata([init_threshold, init_threshold])
        self.hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
        self.hit_duration_line.set_xdata([hit_duration * 1000, hit_duration * 1000])
        
        xticks = np.arange(-1000, (int(self.parameters["hitWindow"].get()) + int(self.parameters["interTrialDuration"].get())) * 1000, 500)
        self.ax.set_xticks(xticks)
        formatted_ticks = [f'{tick:.0f}' for tick in xticks]
        self.ax.set_xticklabels(formatted_ticks)
        
        yticks = np.arange(-10, int(float(self.parameters["hitThresh"].get())) + 50, 10)
        self.ax.set_yticks(yticks)
        formatted_ticks = [f'{tick:.0f}' for tick in yticks]
        self.ax.set_yticklabels(formatted_ticks)

        self.ax.legend()  # Update legend
        
        
        self.main_functions["update_parameters"](self.get_parameters_list())
        self.main_functions["start_session"]()  # Start the trials
        self.canvas.draw()


    # Define an animation update function
    def animate(self, i):
        if self.main_functions["is_running"]() and not self.paused:
            self.updateDisplayValues()
            self.chronometer(self.debut)
            # Check if in ITI period
            if self.main_functions["is_in_iti_period"]():
                return
            data = self.main_functions["get_data"]()
            angles = data['values']
            reference_time = self.main_functions["get_reference_time"]()
            hit_threshold, hold_time = self.main_functions["get_adapted_values"]()

            self.parameters["hitThresh"].set(hit_threshold)
            self.parameters["holdTime"].set(hold_time)
            self.init_threshold_line.set_ydata([float(self.parameters["iniThreshold"].get()), float(self.parameters["iniThreshold"].get())])
            self.hit_threshold_line.set_ydata([hit_threshold, hit_threshold])
            timestamps = data['timestamps'].values - reference_time * 1000 
            
            
            if len(timestamps) > 0:
                self.ax.set_xlim(-1000, max(timestamps[-1], float(self.parameters["hitWindow"].get()) * 1000) + 1000)
                timestamps = np.append(timestamps, (clock.time() - (reference_time)) * 1000)
                
            if len(angles) > 0:
                self.ax.set_ylim( -10, max(hit_threshold, angles.max()) + 50)  # Add some padding
                if (list(angles)[-1] > int(float(self.parameters["hitThresh"].get()))):
                    yticks = np.arange(-5, int(angles.max()) + 50, round(angles.max() / 10 / 5) * 5)
                    self.ax.set_yticks(yticks)
                    formatted_ticks = [f'{tick:.0f}' for tick in yticks]
                    self.ax.set_yticklabels(formatted_ticks)
                angles = np.append(angles, angles[len(angles) - 1])
                
            self.line.set_data(timestamps, angles)
#             self.ax.plot(timestamps, angles)
            
            
            self.canvas.draw()
        elif self.paused:
            self.line.set_data([],[])
            self.canvas.draw()
        elif self.session_running and self.main_functions["session_done"]():
            self.line.set_data([],[])
            self.canvas.draw()
            self.stop()
            
    def set_gain(self, gain):
        self.parameters["gain"].set(gain)
            
    def open_advanced(self):
        Advanced_Window(self)
        
    def open_calibration(self):
        Calibration_Window(self, self.main_functions["get_lever_value"], self.set_gain, self.parameters["gain"].get())
        


    # starts the GUI and takes the necessary functions to call with buttons

    def on_closing(self):
        if not self.canClose:
            return
        self.main_functions["close"]()
        self.root.quit()
        self.root.destroy()
        return
    


class Advanced_Window():
    def __init__(self, gui):
        self.gui = gui
        self.parameters = gui.parameters
        self.popup = tk.Toplevel(gui.root)
        self.popup.title("Modify Parameters")
        self.popup.geometry("400x400")

        

        self.popup.grab_set()
        
        self.canvas = tk.Canvas(self.popup)
        self.scrollbar = tk.Scrollbar(self.popup, orient="vertical", command =self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.frame = tk.Frame(self.canvas, padx=10, pady=10)
        self.canvas.create_window((0,0), window=self.frame, anchor="nw")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.add_parameters()
        
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
#         self.frame.pack(fill="both", expand=True)
        
        
        self.popup.protocol("WM_DELETE_WINDOW", self.on_close)
        
        

    def add_parameters(self):
        i = 0
        for key, parameter in self.parameters.items():
            tk.Label(self.frame, text=key).grid(row=i, column=0, stick=tk.W, pady=2)
            if isinstance(parameter, tk.BooleanVar):
                entry = tk.Checkbutton(self.frame, variable=self.parameters[key])
                entry.grid(row=i, column=1, pady=2)
            elif isinstance(parameter, tk.StringVar): 
                entry = tk.Entry(self.frame, textvariable=self.parameters[key])
                entry.grid(row=i, column=1, pady=2)
            i += 1
        height = str(min(len(self.parameters) * 30, 600))
#         self.popup.geometry("400x" + height)



    def create_parameter_input(self, frame, label, row, default_value):
        tk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(frame)
        entry.grid(row=row, column=1, pady=2)
        entry.insert(0, str(default_value))
        return entry

    def on_close(self):
        self.popup.grab_release()
        self.popup.destroy()
        
        
class Calibration_Window():
    def __init__(self, gui, get_lever_value, set_gain, gain):
        
        self.root = gui.root
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Force Calibration")
        self.popup.geometry("750x600")
        self.popup.minsize(width=500, height=600)
        
        self.popup.grab_set()
        
        self.popup.grid_rowconfigure(0, weight=1)
        self.popup.grid_rowconfigure(1, weight=3)
        
        self.popup.grid_columnconfigure(0, weight=1)
        
        self.top_frame = tk.Frame(self.popup)
        self.top_frame.grid(row=0, column=0, sticky="n", padx=10, pady=10)
        
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        
        
        self.bottom_frame = tk.Frame(self.popup)
        self.bottom_frame.grid(row=1, column=0, sticky="nwew")
        
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        
        self.get_lever_value = get_lever_value
        self.set_gain = set_gain
        self.gain = gain
        self.ratios = []
        self.data = []
        
        tk.Label(self.top_frame, text="Known Force (g):").grid(row=0, column=0)
        self.force_entry = tk.Entry(self.top_frame)
        self.force_entry.grid(row=0, column=1)
        
        self.add_button = tk.Button(self.top_frame, text="Add Data Point", command=self.add_data_point)
        self.add_button.grid(row=2, column=0, columnspan=2)
        
        self.gain_label = tk.Label(self.top_frame, text="")
        self.gain_label.grid(row=4, column=0, columnspan=2)
        
        self.gain_label.config(text="Gain: " + str(self.gain))
        
        self.message_label = tk.Label(self.top_frame, text="")
        self.message_label.grid(row=5, column=0, columnspan=2)
        
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Calibration Plot")
        self.ax.set_xlabel("Analog Value")
        self.ax.set_ylabel("Force (g)")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.bottom_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.config(width=600, height=400)
        
        self.canvas_widget.grid(row=5, column=0, columnspan=2, sticky="nsew")
        
        
    def add_data_point(self):
        try:
            force = float(self.force_entry.get())
            analog_value = float(self.get_lever_value())
            if (analog_value != 0):
                self.message_label.config(text="")
                ratio = force / analog_value
                self.data.append((analog_value, force))
                self.ratios.append(ratio)
                self.gain = sum(self.ratios) / len(self.ratios)
                self.set_gain(self.gain)
            else:
                self.message_label.config(text="No points are added when analog value is 0")
            
            self.gain_label.config(text="Gain: " + str(self.gain) + " Analog : " + str(analog_value))
        except ValueError:
            self.message_label.config(text="Input Error : Please enter valid number for force")
            
        self.plot_data()
            
    def plot_data(self):
        if not self.data:
            return
        
        self.ax.clear()
        sorted_data = sorted(self.data)
        x,y = zip(*sorted_data)
        
        self.ax.plot(x,y, 'o-', label="Force vs Analog Value")
        self.ax.set_xlabel("Analog Value")
        self.ax.set_ylabel("Force (g)")
        self.ax.set_title("Calibration Plot")
        self.ax.legend()
        
        
        self.canvas.draw()
        
        
