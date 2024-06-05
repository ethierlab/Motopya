from tkinter import *
import tkinter as tk
from tkinter import ttk
import customtkinter
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
    
# Serial communication

arduino = serial.Serial(port_found, 115211)
t.sleep(1)
arduino.flushInput()  # vide le buffer en provenance de l'arduino

try:
    cmd = "testing" + '\r'
    arduino.write(cmd.encode())
    arduino.reset_output_buffer()
except Exception as e:
    print("An error occurred:", e)

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

saveFolder = StringVar(top)
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

parameters["iniBaseline"].set("1")



# Create a canvas
# canvas = tk.Canvas(width=1000, height=600)
# canvas.grid(row=0, column=0, sticky="nsew")

# def on_frame_configure(event):
#         # Update the scroll region of the canvas to include the frame
#         canvas.configure(scrollregion=canvas.bbox("all"))

# # Add a vertical scrollbar to the canvas
# scrollbar = ttk.Scrollbar(top, orient=VERTICAL, command=canvas.xview)
# scrollbar.grid(row=0, column=1, sticky="ns")

# # Configure the canvas to use the scrollbar
# canvas.configure(yscrollcommand=scrollbar.set)

# # Create a frame inside the canvas
# scrollable_frame = Frame(canvas)

# # Add the frame to the canvas window
# canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# # Bind the frame configuration to the canvas scroll region
# scrollable_frame.bind("<Configure>", on_frame_configure)


# variables

# scrollbar = Scrollbar(top)
# scrollbar.grid( row=0,column=0, sticky="ns" )

# mylist = Listbox(top, yscrollcommand = scrollbar.set )
# for line in range(100):
#    mylist.insert(END, "This is line number " + str(line))
   
# mylist.grid(row=0, column=0, sticky="nswe" )


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
    arduino.close()
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
    print("arrays")
    print(timeArray)
    print(dataArray)
    plotData(timeArray, dataArray)
    # arduino.flushInput()  # vide le buffer en provenance de l'arduino

stateList = []

def readArduinoLine():
    global dataDeque
    global timeDeque
    global num_trials, num_pellets, num_rewards
    output = arduino.readline()
    output = str(output, 'utf-8')

    if ("data" in output and "time" in output and "fin\r\n" in output):
        "other data"
        output = output.strip(';fin\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('data')
        
        data = output.split(";t", 1)
        # dataDeque.extend(data[0].split(';'))
        # timeDeque.extend(data[1].split(';'))
        dataArray = np.array(dataDeque).astype(float)
        timeArray = np.array(timeDeque).astype(float)
        return True, dataArray, timeArray
    elif ("trialData" in output and "fin\r\n" in output):
        print("end")
        print(output)
        output = output.strip(';fin\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('trialData')
        
        data = output.split(";nt", 1)
        trial_data = data[0].split(";")
        # dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        # timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        print("dataDeque 1")
        print(dataDeque)
        print("trial data")
        print(trial_data)
        for pair in trial_data:
            if pair:  # Ignore empty strings
                time, value = pair.split('/')
                dataDeque.extend([value])
                timeDeque.extend([time])
        print("dataDeque 1")
        print(dataDeque)
        dataArray = np.array(dataDeque).astype(float) 
        timeArray = np.array(timeDeque).astype(float)
        print("before")
        print(dataArray)
        print("resetting the deque")
        dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        print("after")
        print(dataArray)
        # print(dataArray)


        trial_numbers = data[1].split(";")
        print("numbers")
        for pair in trial_numbers:
            print(pair)
        num_trials = int(trial_numbers[0])
        trial_start_time = int(trial_numbers[1]) 
        init_thresh = int(trial_numbers[2])
        hold_time = int(trial_numbers[3])
        hit_thresh = int(trial_numbers[4])
        trial_end_time = int(trial_numbers[5])
        success = int(trial_numbers[6])
        peak_moduleValue = int(trial_numbers[7])
        num_pellets = int(trial_numbers[8])
        num_rewards = int(trial_numbers[9])


        return True, dataArray, timeArray
    elif ("trialData" in output and "partialEnd\r\n" in output):
        print("partial")
        print(output)
        output = output.removesuffix('partialEnd\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('trialData')
        print(output)

        print(dataDeque)
        print(timeDeque)
        
        data = output.split(";nt", 1)
        trial_data = data[0].split(";")

        print("dataDeque 1")
        print(dataDeque)
        for pair in trial_data:
            if pair:  # Ignore empty strings
                time, value = pair.split('/')
                dataDeque.extend([value])
                timeDeque.extend([time])

        print("dataDeque 2")
        print(dataDeque)
        dataArray = np.array(dataDeque).astype(float) 
        timeArray = np.array(timeDeque).astype(float)
        trial_numbers = data[1].split(";")
        print("numbers")
        for pair in trial_numbers:
            print(pair)
        num_trials = int(trial_numbers[0])
        trial_start_time = int(trial_numbers[1]) 
        init_thresh = int(trial_numbers[2])
        hold_time = int(trial_numbers[3])
        hit_thresh = int(trial_numbers[4])
        trial_end_time = int(trial_numbers[5])
        success = int(trial_numbers[6])
        peak_moduleValue = int(trial_numbers[7])
        num_pellets = int(trial_numbers[8])
        num_rewards = int(trial_numbers[9])
        # print(dataArray)
        return False, dataArray, timeArray
    elif ("message" in output):
        print(output)
        output = output.removeprefix("message")
        output = output.removesuffix(";fin\r\n")
        stateList.append(output)
        print("*\n*\n*")
        print(stateList)
        return False, np.zeros(buffer_size), np.zeros(buffer_size)
    elif ("yumm" in output):
        output = output.removeprefix("yumm")
        output = output.removesuffix(";fin\r\n")
        return False, np.zeros(buffer_size), np.zeros(buffer_size)
    else:
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
    print("length")
    print(length)
    time_Array = time_Array[length:]
    data_Array = data_Array[length:]
    print(len(time_Array))
    print(len(data_Array))
    for i in range(len(time_Array)):
        if float(data_Array[i]) != 0:
            print(str(time_Array[i]) + " with " + str(data_Array[i]))
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

    # colors_normalized = list(np.random.rand(len(data_Array)))
    # try:

        # colors_normalized = (data_Array - np.min(data_Array)) / (np.max(data_Array) - np.min(data_Array))
        # print(len(colors_normalized))
        # ax.scatter(axeTempRel, data_Array, c=colors_normalized, cmap='viridis', s=0.1)
    # except:
    colors_normalized = list(np.random.rand(len(data_Array)))
    print(len(colors_normalized))
    ax.scatter(axeTempRel, data_Array, c=colors_normalized, cmap='viridis', s=0.1)
    
    

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
    Trials.config(text="Num Trials: " + str(num_trials))
    Rewards.config(text="Num Rewards: " + str(num_rewards))
    Pellet.config(text="Num Pellets: " + str(num_pellets))


def chronometer(debut):
    chrono_sec = t.time() - debut
    chrono_timeLapse = timedelta(seconds=chrono_sec)
    timer_label.config(text="Time elapsed: " + str(chrono_timeLapse))

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
        send_parameters()
        print("s" + parameters["iniThreshold"].get() + "b" + parameters["iniBaseline"].get())
        sendArduino("s" + parameters["iniThreshold"].get() + "b" + parameters["iniBaseline"].get()) # déclenche la boucle essai dans arduino et envoie le seuil pour déclencher l essaie
        # t.sleep(8) # permet au buffer d'arduino de se remplir



        # Boucle sans fin
        # arduino.flushInput()ùù
        debut = t.time()
        while session_running:
            chronometer(debut)
            updateDisplayValues()
            try:
                if arduino.inWaiting() > 1:
                    print("receiving")
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

#def

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
        sendArduino("w")
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
Rat_ID = Entry(Cadre1, width=10).grid(row=2, column=1)


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


def save_session():
    global sensorValueTrial
    global sensorTimeStamp
    dir_target = savefolder.get()
    np.savetxt(dir_target, sensorValueTrial, delimiter=",")


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

    print("managing")
    if min_thresh['state'] == DISABLED and max_thresh['state'] == DISABLED:
        min_thresh['state'] = NORMAL
        max_thresh['state'] = NORMAL
    elif min_thresh['state'] == NORMAL and max_thresh['state'] == NORMAL:
        min_thresh['state'] = DISABLED
        max_thresh['state'] = DISABLED

def manage_time():

    print("managing")
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
    print("Selected file:", file_path)
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                key, value = row
                if key not in parameters.keys():
                    print("That is not a configuration file." + str(key))
                    return
                parameters[key].set(value)
    except: 
        print("Error reading file.")
        return
    print("Parameters loaded")
    return parameters

def save_configuration():
    global parameters
    top.withdraw()  # Hide the main window
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
    top.deiconify()

def send_parameters():
    global parameters
    parameters["iniBaseline"].set("1")
    message = "p"
    for value in parameters.values():
        message += str(value.get()) + ";"
    print(message)
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
    
def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def is_boolean(value):
    return isinstance(value, bool)

def entry_changed(*args):
    parameters["iniBaseline"].set("1")
    startButton.config(state="disabled")
    for key, value in parameters.items():
        if not value.get():
            print("Not enough values" + str(key))
            return False
    startButton.config(state="normal")
    for key, value in parameters.items():
        if key in ["leverGain", "holdTime", "holdTimeMin", "holdTimeMax"] :
            if not is_float(value.get()):
                print("Values are not correct types" + str(key))
                return False
        elif key in ["leverGain", "holdTimeAdapt", "hitThreshAdapt"]:
            if not is_boolean(value.get()):
                print("Values are not correct types" + str(key))
                return False
        else:
            if not is_int(value.get()):
                print("Values are not correct types" + str(key))
                return False
            
    startButton.config(state="normal")
    return True
    # if ((iniThreshold.get() and minDuration.get() and hitWindow.get() and hitThresh.get()
    #       and leverGain.get() and forceDrop.get() and maxTrials.get())): # and iniBaseline.get()
    #     # saveParametersButton.config(state="normal")
    #     startButton.config(state="normal")
    #     if not (is_int(iniThreshold.get()) and is_int(iniBaseline.get()) and is_int(minDuration.get()) and is_int(hitWindow.get()) and is_int(hitThresh.get())
    #              and is_float(leverGain.get()) and is_int(forceDrop.get()) and is_int(maxTrials.get())):
    #         startButton.config(state="disabled")
    #         print("not enough values")
    #         print("hh")
    #         return False
    #     else:
    #         return True
    # else:
    #     print("else")
    #     return False
        # saveParametersButton.config(state="disabled")

for value in parameters.values():
    value.trace_add("write", entry_changed)

# #infos sur les trials, rewards et temps passé
Cadre4 = Frame(CadreDroite)
Cadre4.grid(row=1, column=2)

Trials = Label(Cadre4, text="Num Trials:", font=Gras)
Trials.grid(row=1, column=0)
Rewards = Label(Cadre4, text="Num Rewards:", font=Gras)
Rewards.grid(row=2, column=0)
# Med_pick = Label(Cadre4, text="Median Peak:", font=Gras).grid(row=2, column=1)
Pellet = Label(Cadre4, text="Pellet delivered:", font=Gras)
Pellet.grid(row=1, column=1)
timer_label = Label(Cadre4, text="Time elapsed: 0:00:00:000000", font=Gras)
timer_label.grid(row=2, column=1)

set_text_bg(Cadre5)
plotData(np.array(timeDeque).astype(float), np.array(dataDeque).astype(float))
# #_______________________________________________________________________________
top.mainloop()
