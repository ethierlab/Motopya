from tkinter import *
from tkinter import messagebox
import tkinter.font as font
import time as t
from datetime import datetime
from datetime import timedelta
import serial
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.filedialog import askopenfilename
import serial.tools.list_ports
import sys
from collections import deque
from tkinter import filedialog
import time
import csv
import os

arduino = None

# création de l'interface avec titre et taille de la fenêtre
top = Tk()
top.title("Moto Knob Controller")

top.resizable(False, False)
# top.minsize(1211, 611)


session_running = False
session_paused = False
num_pellets = 0
num_rewards = 0
num_trials = 0
parameters = {}
trial_table = {}

parameters["iniThreshold"] = StringVar(top) #0
parameters["iniBaseline"] = StringVar(top) #1
parameters["minDuration"] = StringVar(top)#2
parameters["hitWindow"] = StringVar(top)#3
parameters["hitThresh"] = StringVar(top)#4
parameters["hitThreshAdapt"] = BooleanVar(top)#5
parameters["hitThreshMin"] = StringVar(top)#6
parameters["hitThreshMax"] = StringVar(top)#7
parameters["leverGain"] = StringVar(top)#8
parameters["forceDrop"] = StringVar(top)#9
parameters["maxTrials"] = StringVar(top)#10
parameters["holdTime"] = StringVar(top)#11
parameters["holdTimeAdapt"] = BooleanVar(top)#12
parameters["holdTimeMin"] = StringVar(top)#13
parameters["holdTimeMax"] = StringVar(top)#14
parameters["saveFolder"]  = StringVar(top)
parameters["ratID"] = StringVar(top)

parameters["iniBaseline"].set("1")

trial_table = []
# trial_table["start_time"] = []
# trial_table["init_thresh"] = []
# trial_table["hit_thresh"] = []
# trial_table["Force"] = []
# trial_table["hold_time"] = []
# trial_table["duration"] = []
# trial_table["success"] = []
# trial_table["peak"] = []


CadreGauche = Frame(top)
CadreGauche.grid(row=0, column=0, padx=20, pady=20)
vertical_border = Frame(top, width=1, bg="black")
vertical_border.grid(row=0, column=1, sticky="ns")
CadreDroite = Frame(top)
CadreDroite.grid(row=0, column=2, padx=20, pady=20)
# scrollbar.config( command = CadreGauche.yview )
global buffer_size
buffer_size = 500

dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 

# StorageVariable
global sensorValueTrial
sensorValueTrial = np.empty((1, buffer_size),
                            dtype="float")  # accumulation ligne par ligne des valeurs du senseur à chaque essai
global sensorTimeStamp
sensorTimeStamp = np.empty((1, buffer_size), dtype="float")  # les temps pour chacun des essais

Cadre6 = Frame(CadreDroite)
Cadre6.grid(row=2, column=2)

Title_array = Label(Cadre6, text="Knob Rotation Angle").grid(row=1, column=1, columnspan=2, pady=2)
# fig = plt.Figure(figsize=(3, 2), dpi=211, layout='constrained')
fig = plt.Figure(figsize=(3, 3), dpi=200)
ax = fig.add_subplot(111)

fig.patch.set_facecolor('#f0f0f0')
canvas = FigureCanvasTkAgg(fig, master=Cadre6)  # tk.DrawingArea.
canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)


def testConnection():
    sendArduino("Testing")

def connectArduino():
    global arduino
    if arduino:
        print("resetting")
        arduino.setDTR(False)
        arduino.setRTS(False)
        time.sleep(0.1)
        arduino.setDTR(True)
        arduino.setRTS(True)
        arduino.dtr = True
        arduino.close()
    else:
        print("not resetting")
    ports = serial.tools.list_ports.comports()
    port_found = None
    for port in ports:
        print("Port:", port.device)
        print("Description:", port.description)
        print("Hardware ID:", port.hwid)
        print("Manufacturer:", port.manufacturer)
        print("Product:", port.product)
        print("Serial Number:", port.serial_number)
        print("===================================")
        
        if "arduino" in port.description.lower():
            print(port.description.lower())
            description = port.description
            print(description)
            port_found = port.device
    if port_found == None:
        print("Arduino not found")
        sys.exit()
    else:
        print(f"Arduino found at port {port_found} in description {description}")
        lamp.turn_on()
        

    
    # Serial communication

    arduino = serial.Serial(port_found, 115211)
    t.sleep(1)
    arduino.flushInput()  # vide le buffer en provenance de l'arduino

    try:
        sendArduino("testing")
    except Exception as e:
        print("An error occurred:", e)
        

# Boutons de contrôle____________________________________________________________
def sendArduino(text):
    cmd = text + '\r'
    try:
        arduino.write(cmd.encode())
        arduino.reset_output_buffer()
    except serial.SerialException:
        print("Device not connected.")


def readArduinoInput():
    # Arduino envoie deux lignes une première de valeurs du senseur et une deuxième des timestamps
    global sensorValueTrial
    global sensorTimeStamp
    global dataDeque, timeDeque

    received, dataArray, timeArray = readArduinoLine()
    if not received:
        return
    else:
        print("received")

    if (len(dataArray) < buffer_size):
        dataArray = np.pad(dataArray, (0,  (buffer_size - len(dataArray))), mode="constant")
    elif (len(dataArray) > buffer_size):
        tempData = np.array(dataArray[len(dataArray) - buffer_size:])
        dataArray = np.reshape(tempData, (1, -1))

    # # Deuxième ligne
        

    # compilation des essais
    sensorValueTrial = np.vstack((sensorValueTrial, dataArray))
    sensorTimeStamp = np.vstack((sensorTimeStamp, timeArray))  # les temps pour chacun des essais
    plotData(timeArray, dataArray)
    # arduino.flushInput()  # vide le buffer en provenance de l'arduino

stateList = []

def readArduinoLine():
    global dataDeque
    global timeDeque
    global num_trials, num_pellets, num_rewards
    output = arduino.readline()
    output = str(output, 'utf-8')

    if ("trialData" in output and "fin\r\n" in output):
        partial = False
        output = output.strip(';fin\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('trialData')

        if ("partialEnd" in output):
            print(output)
            partial = True
            output = output.removesuffix('partialEnd')  # input en 'string'. Each arduino value is separated by ';'
            print(output)
        data = output.split(";nt", 1)
        trial_data = data[0].split(";")
        # dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        # timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        for pair in trial_data:
            if pair:  # Ignore empty strings
                time, value = pair.split('/')
                dataDeque.extend([value])
                timeDeque.extend([time])

        dataArray = np.array(dataDeque).astype(float) 
        timeArray = np.array(timeDeque).astype(float)

        if partial:
            print("PARTIAL SPLIT")
            return False, np.zeros(buffer_size), np.zeros(buffer_size)
        
        dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 

    
    
    
        trial_numbers = data[1].split(";")
        num_trials = int(trial_numbers[0])
        trial_start_time = int(trial_numbers[1])
        
        init_thresh = int(trial_numbers[2])
        hold_time = int(trial_numbers[3])
        parameters["holdTime"].set(str(float(trial_numbers[3]) / 1000))

        hit_thresh = int(trial_numbers[4])
        parameters["hitThresh"].set(str(int(trial_numbers[4])))
        trial_end_time = int(trial_numbers[5])
        success = int(trial_numbers[6])
        if success:
            display("Success")
        else:
            display("Failed")
        peak_moduleValue = int(trial_numbers[7])
        num_pellets = int(trial_numbers[8])
        num_rewards = int(trial_numbers[9])
        trial_hold_time = int(trial_numbers[10])
        trial_hit_thresh = int(trial_numbers[11])

        trial = {}
        trial["start_time"] = trial_start_time / 1000
        trial["init_thresh"] = init_thresh
        trial["hit_thresh"] = trial_hit_thresh
        trial["Force"] = list(zip(list(timeArray), list(dataArray)))
        trial["hold_time"] = trial_hold_time
        trial["duration"] = trial_end_time / 1000
        trial["success"] = success
        trial["peak"] = peak_moduleValue

        trial_table.append(trial)


        return True, dataArray, timeArray
        
    elif ("message" in output):
        
        output = output.removeprefix("message")
        output = output.removesuffix(";fin\r\n")
        stateList.append(output)
        print("*\n*\n*")
        print(stateList)
        if ("done" in output):
            stop_Button()
        return False, np.zeros(buffer_size), np.zeros(buffer_size)
    else:
        print(output)
        print("full input not found")

        return False, np.zeros(buffer_size), np.zeros(buffer_size)
    



def listStr2listFloat(inList):
    #can be replaced with .asType(float)
    floatList = np.zeros(len(inList), dtype=float)
    u = 0
    for val in inList:
        if val == "":
            val = 0
        floatList[u] = float(val)
        u = u + 1
    floatList = np.reshape(floatList, (1, len(floatList)))

    return floatList

global max_force
max_force = 0
def plotData(time_Array, data_Array):
    length = 0
    for i in range(len(time_Array)):
        if float(time_Array[i]) != 0:
            length = i
            break
    time_Array = time_Array[length:]
    data_Array = data_Array[length:]
    # for i in range(len(time_Array)):
    #     if float(data_Array[i]) != 0:
            # print(str(time_Array[i]) + " with " + str(data_Array[i]))
    # axeTempRel
    global max_force
    
    # axeTempRel = (time_Array - time_Array.min()) / 1000
    axeTempRel = (time_Array) / 1000
    min_time = axeTempRel.min()
    max_time = axeTempRel.max()
    if not max_time:
        max_time = 3

    ax.clear()
    ax.set_title("Pulling Force", fontsize=7)
    canvas.draw()
    canvas.flush_events()

    max_force = data_Array.max() if data_Array.max() >= max_force else max_force
    if not max_force:
        if (parameters["hitThresh"].get() == ""):
            max_force = 0
        else:
            max_force = float(parameters["hitThresh"].get()) + 10

    colors_normalized = list(np.random.rand(len(data_Array)))
    ax.plot(axeTempRel, data_Array, linewidth=0.5)
    # ax.scatter(axeTempRel, data_Array, c=colors_normalized, cmap='viridis', s=0.1)
    
    
    

    # ax.axhline(float(iniThreshold.get()), color='r', linestyle='--', label='Threshold 1', linewidth=0.5)
    # ax.axhline(float(hitThresh.get()), color='g', linestyle='--', label='Threshold 2', linewidth=0.5)
    if entry_changed():
        ax.plot([-1, 0], [float(parameters["iniThreshold"].get()), float(parameters["iniThreshold"].get())], color='g', linestyle='--', linewidth=0.5)
        ax.plot([0, float(parameters["hitWindow"].get())], [float(parameters["hitThresh"].get()), float(parameters["hitThresh"].get())], color='r', linestyle='--', linewidth=0.5)
        ax.axvline(x=-1, color='gray', linestyle='--', linewidth=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.5)
        ax.axvline(x=float(parameters["hitWindow"].get()), color='gray', linestyle='--', linewidth=0.5)
    
    ticks = np.arange(np.floor(-1), np.ceil(max_time), .5)
    ax.set_xticks(ticks)
    ticks = np.arange(0, max_force + 100, 100)
    ax.set_yticks(ticks)
    ax.set_ylim(-100, max_force + 100)
    ax.tick_params(axis='both', labelsize=3)

    ax.set_xlabel('Time(s)',fontsize=6)

    ax.set_ylabel('Force(g)',fontsize=6)
    ax.margins(.15)
   
    canvas.draw()
    canvas.flush_events()

def updateDisplayValues():
    Trials.config(text=str(num_trials))
    Rewards.config(text=str(num_rewards))
    Pellet.config(text=f"{num_pellets} ({round(num_pellets * 0.045, 3):.3f} g)")


def chronometer(debut):
    chrono_sec = t.time() - debut
    chrono_timeLapse = timedelta(seconds=chrono_sec)
    hours, remainder = divmod(chrono_timeLapse.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # timer_clock.config(text=str(chrono_timeLapse))
    timer_clock.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")

def disconnected():
    global session_running
    global session_paused
    session_paused = False
    session_running = False
    lamp.turn_off()
    startButton.config(state="disabled")
    startButton.config(text="START")
    stopButton.config(state="disabled")
    entry_changed()

def toggle_start():
    global session_paused
    if session_paused:
        session_paused = not session_paused
        pause()
    else:
        startButton.config(text="PAUSE")
        session_paused = not session_paused
        start()

def resume():
    startButton.config(text="PAUSE")
    # start()
        
def pause():
    global session_paused
    startButton.config(text="RESUME")



def start():
    # Déclenche la session comportement
    global session_running
    session_running = True
    startButton.config(text="PAUSE")
    stopButton.config(state="normal")
    try:
        arduino.flushInput()
        send_parameters()
        sendArduino("s" + parameters["iniThreshold"].get() + "b" + parameters["iniBaseline"].get()) # déclenche la boucle essai dans arduino et envoie le seuil pour déclencher l essaie
        # t.sleep(8) # permet au buffer d'arduino de se remplir



        # Boucle sans fin
        # arduino.flushInput()
        debut = t.time()
        while session_running:
            chronometer(debut)
            updateDisplayValues()
            try:
                if arduino.inWaiting() > 1:
                    readArduinoInput()
                top.update()
            except serial.SerialException:
                disconnected()
                print("The device unexpectedly disconnected.")
                break
        
            
    except serial.SerialException:
        print("did not work")
        stop_Button()
        disconnected()
        
        print("There is no device connected.")

Cadre3 = Frame(CadreGauche)
Cadre3.grid(row=3, column=1, sticky="n", pady=(20,20))
Cadre3.grid_rowconfigure(0, pad=10,)
Cadre3.grid_columnconfigure(0, pad=10, weight=1)
Cadre3.grid_columnconfigure(1, pad=10, weight=1)
Cadre3.grid_columnconfigure(2, pad=10, weight=1)
Cadre3.grid_columnconfigure(3, pad=10, weight=1)
timer_running = False
Gras = font.Font(weight="bold")  # variable qui contient l'attribut "texte en gras"

def feed():
    sendArduino("f")
# stop l'expérience
def stop_Button():
    global session_running
    global session_paused
    session_paused = False
    startButton.config(state="normal")
    startButton.config(text="START")
    stopButton.config(state="disabled")
    try:
        finish_up(False)
        stateList.clear()
    except serial.SerialException:
        disconnected()
        print("There is no device connected.")
    session_running = False


def set_button_size(frame, width, height, font):

    for child in frame.winfo_children():
        if isinstance(child, (Button)):
            child.config(width=width, height=height, font=font)


class UILamp(Canvas):
    def __init__(self, parent, diameter=50, color="#5d615d", *args, **kwargs):
        super().__init__(parent, width=diameter, height=diameter, *args, **kwargs)
        self.diameter = diameter
        self.color = color
        self.lamp = self.create_oval(2, 2, diameter-2, diameter-2, fill=color, outline="black")
    
    def change_color(self, new_color):
        self.color = new_color
        self.itemconfig(self.lamp, fill=new_color)

    def turn_on(self):
        self.color = "#24fc03"
        self.itemconfig(self.lamp, fill = "#24fc03")

    def turn_off(self):
        self.color = "#5d615d"
        self.itemconfig(self.lamp, fill = "#5d615d")


startButton = Button(Cadre3, text="START", background='#64D413', state=DISABLED, command=toggle_start)
startButton.grid(row=0, column=0)

stopButton = Button(Cadre3, text="STOP", background='red', state=DISABLED, command=stop_Button)
stopButton.grid(row=0, column=1)

feedButton = Button(Cadre3, text="FEED", background='#798FD4', state=NORMAL, command=feed)
feedButton.grid(row=0, column=2)

removeOffsetButton = Button(Cadre3, text='Remove\nOffset', state=DISABLED)
removeOffsetButton.grid(row=0, column=3)

set_button_size(Cadre3, 10, 2, ('Serif', 10, "bold"))


DisplayBox = Label(CadreGauche, text="TextBox", font=("Serif", 12))
DisplayBox.grid(row=4, column=1, sticky="n", pady=(20,20))


# _______________________________________________________________________________

# définition du premier cadre


Cadre1 = Frame(CadreGauche)
Cadre1.grid(row=1, column=1)


# Boutons de tests_______________________________________________________________
Title = Label(Cadre1, text="Rat Pull Task", fg='black', justify=CENTER, font= (Gras, 25, "bold"), padx=5, pady=25).grid(row=1, column=2)
lamp = UILamp(Cadre1, diameter=32)
lamp.grid(row=2, column=4)
Connect = Button(Cadre1, text="Connect Device", command=connectArduino, width=13, font= ("Serif", 11, "bold")).grid(row=2, column=5)
# Retract = Button(Cadre1, text="Retract\nSensor At Pos", state=DISABLED).grid(row=2, column=5)

# infos sur le rat et la sauvegarde des données
Rat = Label(Cadre1, text="Rat ID:  ", font=("Serif", 11, "bold")).grid(row=2, column=0)
Rat_ID = Entry(Cadre1, width=10, textvariable=parameters["ratID"]).grid(row=2, column=1)


# def browse():
#     Save_browser = askopenfilename()
#     Save_location.delete(1, END)
#     Save_location.insert(1, Save_browser)


# Save = Label(Cadre1, text="Save location (parent folder):").grid(row=3, column=1)
# Save_location = Entry(Cadre1, textvariable=savefolder).grid(row=3, column=2)
# Browse = Button(Cadre1, text="Browse", command=browse)
# Browse.grid(row=3, column=3)

# Calibration = Label(Cadre1, text="Calibration file location:").grid(row=4, column=1)
# Calib = Entry(Cadre1, ).grid(row=4, column=2)
# Change = Button(Cadre1, text="Change").grid(row=4, column=3)
def save_trial_table(filename):
    global trial_table
    with open(filename, mode='w', newline='') as csvfile:
        fieldnames = ["start_time", "init_thresh", "hit_thresh", "Force", "hold_time", "duration", "success", "peak"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        print("writing trials")
        for trial in trial_table:
            # Convert list of Force values to a string for CSV
            trial["Force"] = ', '.join(map(str, trial["Force"]))
            writer.writerow(trial)

def save_file(file_path, dict):
    saved_parameters = {}
    for key, value in dict.items():
        saved_parameters[key] = value.get()


    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, value in saved_parameters.items():
            writer.writerow([key, value])

    

def display(text):
    DisplayBox.config(text=text)


def save_results(crashed):
    response = messagebox.askyesno("Confirmation", "Do you want to save the session?")
    if response:
        display("yes")
    else:
        display("no")

    if crashed:
        response = messagebox.askyesno("Sorry about that...", "RatPull lever_pull_behavior Crashed!\nSave results?")
    else:
        response = messagebox.askyesno("End of Session", "End of behavioral session\nSave results?")
    
    rat_dir = os.path.join(parameters["saveFolder"].get(), str(parameters["ratID"].get()))
    if response:
        dir_exists = os.path.exists(rat_dir)
        print(dir_exists)
        if not dir_exists:
            display(f'Creating new folder for animal parameters["ratID"].get()\n')
            dir_exists = os.mkdir(rat_dir)
            if not dir_exists:
                display('Failed to create new folder in specifiec location')
            
        
        if dir_exists:
            ttfname = parameters["ratID"].get() + '_RatPull_trial_table_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
            pfname = parameters["ratID"].get() + '_RatPull_params_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'

            print(rat_dir)
            print(ttfname)
            save_trial_table(os.path.join(rat_dir, ttfname))
            # save_file(os.join(rat_dir, ttfname), trial_table)
            save_file(os.path.join(rat_dir, pfname), parameters)

            display('behavior stats and parameters saved successfully')
            # update_global_stats(trial_table)
        else:
            display('behavior stats and parameters not saved')
    

def save_session():
    global sensorValueTrial
    global sensorTimeStamp
    dir_target = parameters["savefolder"].get()
    np.savetxt(dir_target, sensorValueTrial, delimiter=",")

def update_global_stats():
    print("Update global stats")


# Save_session = Button(Cadre1, text="Save Session", command=save_session)
# Save_session.grid(row=5, column=1)
# _______________________________________________________________________________

def set_text_bg(frame):
    # Get the background color of the frame
    bg_color = frame.cget("bg")

    # Configure the background color of all text widgets in the frame
    for child in frame.winfo_children():
        if isinstance(child, (Label, Text, Checkbutton)):
            child.config(bg=bg_color)
        # if isinstance(child, (Label, Text, Entry, Checkbutton)):
            # child.config(relief="solid")
        if isinstance(child, (Entry)):
            child.config(width=6)
        if isinstance(child, (Label)) and child["text"] not in ["min", "max", "adapt"]:
            child.config(anchor="e", justify=RIGHT)
            child.grid(sticky="e")
        # if isinstance(child, (Button)):
            # child.config(justify=CENTER)
            # child.grid(sticky="w")

def set_sticky(frame):
    # Get the background color of the frame
    bg_color = frame.cget("bg")

    # Configure the background color of all text widgets in the frame
    for child in frame.winfo_children():
        if isinstance(child, (Label)):
            child.grid(sticky="w")


# --------------------------------
Cadre7 = Frame(CadreGauche)
Cadre7.grid(row=2, column=1, padx=20, pady=(0, 20))
# Cadre5.config(borderwidth=2, relief=RIDGE)
Cadre7.config(relief=RIDGE)
Cadre5 = Frame(Cadre7)
Cadre5.grid(row=2, column=0)
# Cadre5.config(borderwidth=2, relief=RIDGE)
Cadre5.config(relief=RIDGE, bg="#e0e0e0")
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
border = Frame(Cadre7, height=0.3, bg="black")
border.grid(row=1, column=0, sticky="ew")

Parametre = Label(Cadre7, text="Parameters: ", fg='black', justify=LEFT, font=Gras).grid(row=0, column=0, sticky="w")

Init_thresh = Label(Cadre5, text="Init thresh (g):").grid(row=0, column=0)
IT = Entry(Cadre5, textvariable = parameters["iniThreshold"]).grid(row=0, column=1)

Hit_window = Label(Cadre5, text="Hit window (s):").grid(row=1, column=0)
HW = Entry(Cadre5, textvariable=parameters["hitWindow"]).grid(row=1, column=1)

Duree = Label(Cadre5, text="Max Duration (min):").grid(row=2, column=0)
min = Entry(Cadre5, textvariable=parameters["minDuration"]).grid(row=2, column=1)


Lever_gain = Label(Cadre5, text="Lever Gain :").grid(row=0, column=4, columnspan=2)
Gain_entry = Entry(Cadre5, textvariable=parameters["leverGain"]).grid(row=0, column=6)

Drop_Tolerance = Label(Cadre5, text="Force Drop Tolerance (g) :").grid(row=1, column=3, columnspan=3)
Drop_entry = Entry(Cadre5, textvariable=parameters["forceDrop"]).grid(row=1, column=6)

Max_Trials = Label(Cadre5, text="Max Trials (num) :").grid(row=2, column=3, columnspan=3)
Max_entry = Entry(Cadre5, textvariable=parameters["maxTrials"]).grid(row=2, column=6)
# Sensor_pos = Label(Cadre5, text="Sensor pos (cm):").grid(row=3, column=1)
# Sensor = Entry(Cadre5).grid(row=3, column=2)

# Init_baseline = Label(Cadre5, text="Init baseline (g):").grid(row=3, column=5)
# IB = Entry(Cadre5, textvariable = iniBaseline).grid(row=3, column=6)

adaptive = Label(Cadre5, text="adapt").grid(row=3, column=2)


# def adapt_thres():

min = Label(Cadre5, text="min").grid(row=3, column=3)
min_thresh = Entry(Cadre5, state=DISABLED, textvariable=parameters["hitThreshMin"])
min_thresh.grid(row=4, column=3)
# min_ceiling = Entry(Cadre5, state=DISABLED).grid(row=6, column=4)
min_time = Entry(Cadre5, state=DISABLED, textvariable=parameters["holdTimeMin"])
min_time.grid(row=5, column=3)

max = Label(Cadre5, text="max").grid(row=3, column=4)
max_thresh = Entry(Cadre5, state=DISABLED, textvariable=parameters["hitThreshMax"])
max_thresh.grid(row=4, column=4)
# max_ceiling = Entry(Cadre5, state=DISABLED).grid(row=6, column=5)
max_time = Entry(Cadre5, state=DISABLED, textvariable=parameters["holdTimeMax"])
max_time.grid(row=5, column=4)

def manage_threshold():
    if min_thresh['state'] == DISABLED and max_thresh['state'] == DISABLED:
        min_thresh['state'] = NORMAL
        max_thresh['state'] = NORMAL
    elif min_thresh['state'] == NORMAL and max_thresh['state'] == NORMAL:
        min_thresh['state'] = DISABLED
        max_thresh['state'] = DISABLED

def manage_time():
    if min_time['state'] == DISABLED and max_time['state'] == DISABLED:
        min_time['state'] = NORMAL
        max_time['state'] = NORMAL
    elif min_time['state'] == NORMAL and max_time['state'] == NORMAL:
        min_time['state'] = DISABLED
        max_time['state'] = DISABLED


adapter_threshold = IntVar()
adapt_thresh = Checkbutton(Cadre5, variable=parameters["hitThreshAdapt"], command=lambda: manage_threshold()).grid(row=4, column=2)  # command=manage_threshold
# adapt_ceiling = Checkbutton(Cadre5, state=DISABLED).grid(row=6, column=3)
adapt_time = Checkbutton(Cadre5, variable=parameters["holdTimeAdapt"], command=lambda: manage_time()).grid(row=5, column=2)



Hit_thresh = Label(Cadre5, text="Hit Thresh (g):").grid(row=4, column=0)
HThresh = Entry(Cadre5, textvariable=parameters["hitThresh"]).grid(row=4, column=1)

# Hit_ceiling = Label(Cadre5, text="Hit ceiling (deg):", state=DISABLED).grid(row=6, column=1)
# HC = Entry(Cadre5, state=DISABLED).grid(row=6, column=2)

Hold_time = Label(Cadre5, text="Hold time (s):").grid(row=5, column=0)
HTime = Entry(Cadre5, textvariable=parameters["holdTime"]).grid(row=5, column=1)


def load_parameters():
    global parameters
    file_path = filedialog.askopenfilename()
    directory = os.path.dirname(file_path)
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                key, value = row
                if key not in parameters.keys():
                    print("That is not a configuration file." + str(key))
                    return
                parameters[key].set(value)
            if parameters["hitThreshAdapt"]:
                min_thresh.config(state="normal")
                max_thresh.config(state="normal")
            else:
                min_thresh.config(state="disabled")
                max_thresh.config(state="disabled")
            if parameters["holdTimeAdapt"]:
                min_time.config(state="normal")
                max_time.config(state="normal")
            else:
                min_time.config(state="disabled")
                max_time.config(state="disabled")
    except: 
        print("Error reading file.")
        return
    if not os.path.exists(parameters["saveFolder"].get()):
        parameters["saveFolder"].set(directory)

    print("Parameters loaded")
    return parameters

def finish_up(crashed):
    display('Session Ended');
    
    # reset_buttons(app)

    # trial_table = trial_table(1:num_trials, :);  
    # trial_table.Properties.CustomProperties.num_trials  = num_trials;
    # trial_table.Properties.CustomProperties.num_rewards = num_rewards;
    # trial_table.Properties.CustomProperties.rat_id      = app.rat_id.Value;
    # display_results(session_t, num_trials, num_rewards, app.num_pellets, app.man_pellets);
    save_results(crashed);

def save_configuration():
    global parameters
    # top.withdraw()  # Hide the main window
    saved_parameters = {}
    for key, value in parameters.items():
        saved_parameters[key] = value.get()



    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return  # User canceled the dialog
    
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, value in saved_parameters.items():
            writer.writerow([key, value])
    print("Configuration saved")
    # top.deiconify()

def send_parameters():
    global parameters
    parameters["iniBaseline"].set("1")
    message = "p"
    for value in parameters.values():
        message += str(value.get()) + ";"
    sendArduino(message)
    # sendArduino("p" + init_thresh + ";" + init_baseline + ";" + min_duration + ";" + hit_window + ";" + hit_thresh)
    plotData(np.array(timeDeque).astype(float), np.array(dataDeque).astype(float))
    
loadParametersButton = Button(Cadre5, text="Load", background='white', width=12, command=load_parameters)
loadParametersButton.grid(row=6, column=3, columnspan=2)

saveConfigurationButton = Button(Cadre5, text="Save", background='white', width=10, command=save_configuration)
saveConfigurationButton.grid(row=6, column=5, columnspan=2)


# saveParametersButton = Button(Cadre5, text="Save Parameters", background='white', command=save_parameters, state="disabled")
# saveParametersButton.grid(row=7, column=6)

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
        if not value.get():
            return False
    startButton.config(state="normal")
    for key, value in parameters.items():
        if key in ["leverGain", "holdTime", "holdTimeMin", "holdTimeMax"] :
            if not is_positive_float(value.get()):
                return False
        elif key in ["leverGain", "holdTimeAdapt", "hitThreshAdapt"]:
            if not is_boolean(value.get()):
                return False
        elif key in ["saveFolder", "ratID"]:
            return True
        else:
            if not is_int(value.get()):
                return False
            
    startButton.config(state="normal")
    return True

for value in parameters.values():
    value.trace_add("write", entry_changed)

# #infos sur les trials, rewards et temps passé
Cadre4 = Frame(CadreDroite)
Cadre4.grid(row=1, column=2)

Cadre4.grid_rowconfigure(0, pad=10,)
Cadre4.grid_columnconfigure(0, pad=10, weight=1)
Cadre4.grid_columnconfigure(1, pad=10, weight=1)
Cadre4.grid_columnconfigure(2, pad=10, weight=1, minsize=100)
Cadre4.grid_columnconfigure(3, pad=10, weight=1)

TrialsLabel = Label(Cadre4, text="Num Trials:", font=Gras)
TrialsLabel.grid(row=1, column=0)
Trials = Label(Cadre4, text="0", font=Gras)
Trials.grid(row=1, column=1)
RewardsLabel = Label(Cadre4, text="Num Rewards:", font=Gras)
RewardsLabel.grid(row=2, column=0)
Rewards = Label(Cadre4, text="0", font=Gras)
Rewards.grid(row=2, column=1)
# Med_pick = Label(Cadre4, text="Median Peak:", font=Gras).grid(row=2, column=1)
PelletLabel = Label(Cadre4, text="Pellet delivered:", font=Gras)
PelletLabel.grid(row=1, column=3)
Pellet = Label(Cadre4, text="0 (0.000 g)", font=Gras)
Pellet.grid(row=1, column=4)
timer_label = Label(Cadre4, text="Time elapsed:", font=("Gras", 14, "bold"),fg="blue")
timer_label.grid(row=2, column=3)
timer_clock = Label(Cadre4, text="00:00:00", font=("Gras", 14, "bold"),fg="blue")
timer_clock.grid(row=2, column=4)

set_sticky(Cadre4)
set_text_bg(Cadre5)
plotData(np.array(timeDeque).astype(float), np.array(dataDeque).astype(float))
# #_______________________________________________________________________________
top.mainloop()
