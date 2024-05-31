from tkinter import *
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
    print("hi")
except Exception as e:
    print("An error occurred:", e)

# création de l'interface avec titre et taille de la fenêtre
top = Tk()
top.title("Moto Knob Controller")
# top.minsize(1211, 611)


onVarCheckButton = IntVar(top)
offVarCheckButton = IntVar(top)
savefolder = StringVar(top)
iniThreshold = StringVar(top)
iniBaseline = StringVar(top)
minDuration = StringVar(top)
hitWindow = StringVar(top)
hitThresh = StringVar(top)


# variables

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

Cadre6 = Frame(top)
Cadre6.grid(row=2, column=2)

Title_array = Label(Cadre6, text="Knob Rotation Angle").grid(row=1, column=1, columnspan=2, pady=2)
# fig = plt.Figure(figsize=(3, 2), dpi=211, layout='constrained')
fig = plt.Figure(figsize=(3, 2), dpi=211)
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=Cadre6)  # tk.DrawingArea.
canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)

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
    arduino.write(cmd.encode())
    arduino.reset_output_buffer()


def readArduinoInput():
    # Arduino envoie deux lignes une première de valeurs du senseur et une deuxième des timestamps
    global sensorValueTrial
    global sensorTimeStamp
    global dataDeque, timeDeque

    received, dataArray, timeArray = readArduinoLine()
    if not received:
        return

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
    output = arduino.readline()
    output = str(output, 'utf-8')
    print(output)
    if ("data" in output and "time" in output and "fin\r\n" in output):
        output = output.strip(';fin\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('data')
        
        data = output.split(";t", 1)
        dataDeque.extend(data[0].split(';'))
        timeDeque.extend(data[1].split(';'))
        dataArray = np.array(dataDeque).astype(float)
        timeArray = np.array(timeDeque).astype(float)
        return True, dataArray, timeArray
    elif ("trialData" in output and "fin\r\n" in output):
        output = output.strip(';fin\r\n')  # input en 'string'. Each arduino value is separated by ';'
        output = output.removeprefix('trialData')
        
        data = output.split(";nt", 1)
        trial_data = data[0].split(";")
        dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        for pair in trial_data:
            if pair:  # Ignore empty strings
                time, value = pair.split('/')
                dataDeque.extend([value])
                timeDeque.extend([time])
        dataArray = np.array(dataDeque).astype(float) 
        timeArray = np.array(timeDeque).astype(float)
        # print(dataArray)
        return True, dataArray, timeArray
    elif ("message" in output):
        output = output.removeprefix("message")
        output = output.removesuffix(";fin\r\n")
        stateList.append(output)
        # print("*\n*\n*\n*\n*")
        print(stateList[-50:-1])
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
    canvas.draw()
    canvas.flush_events()

    max_force = data_Array.max() if data_Array.max() >= max_force else max_force
    if not max_force:
        max_force = float(hitThresh.get()) + 10
    ax.plot(axeTempRel, data_Array, linewidth=0.5)

    # ax.axhline(float(iniThreshold.get()), color='r', linestyle='--', label='Threshold 1', linewidth=0.5)
    # ax.axhline(float(hitThresh.get()), color='g', linestyle='--', label='Threshold 2', linewidth=0.5)
    ax.plot([-1, 0], [float(iniThreshold.get()), float(iniThreshold.get())], color='g', linestyle='--', linewidth=0.5)
    ax.plot([0, float(hitWindow.get())], [float(hitThresh.get()), float(hitThresh.get())], color='r', linestyle='--', linewidth=0.5)
    ax.axvline(x=-1, color='gray', linestyle='--', linewidth=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.5)
    ax.axvline(x=float(hitWindow.get()), color='gray', linestyle='--', linewidth=0.5)
    
    ticks = np.arange(np.floor(-1), np.ceil(max_time), .5)
    ax.set_xticks(ticks)
    ticks = np.arange(0, max_force + 100, 100)
    ax.set_yticks(ticks)
    ax.set_ylim(-100, max_force + 100)
    ax.tick_params(axis='both', labelsize=3)

    ax.set_xlabel('times (s)')

    ax.set_ylabel('Force')
    ax.margins(.15)
   
    canvas.draw()
    canvas.flush_events()


def chronometer(debut):
    chrono_sec = t.time() - debut
    chrono_timeLapse = timedelta(seconds=chrono_sec)
    timer_label.config(text=str(chrono_timeLapse))


def startButton():
    # Déclenche la session comportement

    sendArduino("s" + iniThreshold.get() + "b" + iniBaseline.get()) # déclenche la boucle essai dans arduino et envoie le seuil pour déclencher l essaie
    # t.sleep(8) # permet au buffer d'arduino de se remplir



    # Boucle sans fin
    arduino.flushInput()
    debut = t.time()
    while onVarCheckButton.get():
        chronometer(debut)
        if arduino.inWaiting() > 1:
           readArduinoInput()

        top.update()

#def

Cadre3 = Frame(top)
Cadre3.grid(row=3, column=1)
timer_running = False
Gras = font.Font(weight="bold")  # variable qui contient l'attribut "texte en gras"


# stop l'expérience
def stop_Button():
    sendArduino("w")
    stateList.clear()
    onVarCheckButton.set(0)


startButton_name = Checkbutton(Cadre3, text="START", background='green', variable=onVarCheckButton, command=startButton)
startButton_name.grid(row=1, column=1)

feedButton = Button(Cadre3, text="FEED", background='blue', state=DISABLED)
feedButton.grid(row=1, column=2)

pauseButton = Checkbutton(Cadre3, text='PAUSE', state=DISABLED)
pauseButton.grid(row=1, column=4)

stopButton = Checkbutton(Cadre3, text="STOP", background='red', variable=onVarCheckButton, command=stop_Button)
stopButton.grid(row=1, column=6)
# _______________________________________________________________________________

# définition du premier cadre
Cadre1 = Frame(top)
Cadre1.grid(row=1, column=1)

# Boutons de tests_______________________________________________________________
Title = Label(Cadre1, text="Moto Track", fg='blue', justify=CENTER, font=Gras).grid(row=1, column=2)
Connect = Button(Cadre1, text="Connect\nMoto Track", command=connectArduino).grid(row=1, column=5)
Retract = Button(Cadre1, text="Retract\nSensor At Pos", state=DISABLED).grid(row=2, column=5)

# infos sur le rat et la sauvegarde des données
Rat = Label(Cadre1, text="Rat ID:").grid(row=2, column=1)
Rat_ID = Entry(Cadre1, ).grid(row=2, column=2)


def browse():
    Save_browser = askopenfilename()
    Save_location.delete(1, END)
    Save_location.insert(1, Save_browser)


Save = Label(Cadre1, text="Save location (parent folder):").grid(row=3, column=1)
Save_location = Entry(Cadre1, textvariable=savefolder).grid(row=3, column=2)
Browse = Button(Cadre1, text="Browse", command=browse)
Browse.grid(row=3, column=3)

Calibration = Label(Cadre1, text="Calibration file location:").grid(row=4, column=1)
Calib = Entry(Cadre1, ).grid(row=4, column=2)
Change = Button(Cadre1, text="Change").grid(row=4, column=3)


def save_session():
    global sensorValueTrial
    global sensorTimeStamp
    dir_target = savefolder.get()
    np.savetxt(dir_target, sensorValueTrial, delimiter=",")


Save_session = Button(Cadre1, text="Save Session", command=save_session)
Save_session.grid(row=5, column=1)
# _______________________________________________________________________________


# --------------------------------
Cadre5 = Frame(top)
Cadre5.grid(row=2, column=1)
Cadre5.config(borderwidth=2, relief=RIDGE)

Parametre = Label(Cadre5, text="Parameters", fg='blue', justify=CENTER, font=Gras).grid(row=1, column=1)

Duree = Label(Cadre5, text="Duration (min):").grid(row=2, column=1)
min = Entry(Cadre5, textvariable=minDuration).grid(row=2, column=2)

Hit_window = Label(Cadre5, text="Hit window (s):").grid(row=2, column=3)
HW = Entry(Cadre5, textvariable=hitWindow).grid(row=2, column=4)

Sensor_pos = Label(Cadre5, text="Sensor pos (cm):").grid(row=3, column=1)
Sensor = Entry(Cadre5).grid(row=3, column=2)

Init_thresh = Label(Cadre5, text="Init thresh (deg):").grid(row=3, column=3)
IT = Entry(Cadre5, textvariable = iniThreshold).grid(row=3, column=4)

Init_baseline = Label(Cadre5, text="Init baseline (deg):").grid(row=3, column=5)
IB = Entry(Cadre5, textvariable = iniBaseline).grid(row=3, column=6)

adaptive = Label(Cadre5, text="adaptive").grid(row=4, column=3)


# def adapt_thres():

def manage_threshold():
    if min_thresh['state'] == 'disabled' and max_thresh['state'] == 'disabled':
        min_thresh['state'] = 'normal'
        max_thresh['state'] = 'normal'
    elif min_thresh['state'] == 'normal' and max_thresh['state'] == 'normal':
        min_thresh['state'] = 'disabled'
        max_thresh['state'] = 'disabled'


adapter_threshold = IntVar()
adapt_thresh = Checkbutton(Cadre5).grid(row=5, column=3)  # command=manage_threshold
adapt_ceiling = Checkbutton(Cadre5, state=DISABLED).grid(row=6, column=3)
adapt_time = Checkbutton(Cadre5, state=DISABLED).grid(row=7, column=3)

min = Label(Cadre5, text="min").grid(row=4, column=4)
min_thresh = Entry(Cadre5, state=DISABLED).grid(row=5, column=4)
min_ceiling = Entry(Cadre5, state=DISABLED).grid(row=6, column=4)
min_time = Entry(Cadre5, state=DISABLED).grid(row=7, column=4)

max = Label(Cadre5, text="max").grid(row=4, column=5)
max_thresh = Entry(Cadre5, state=DISABLED).grid(row=5, column=5)
max_ceiling = Entry(Cadre5, state=DISABLED).grid(row=6, column=5)
max_time = Entry(Cadre5, state=DISABLED).grid(row=7, column=5)

Hit_thresh = Label(Cadre5, text="Hit Thresh (deg):").grid(row=5, column=1)
HThresh = Entry(Cadre5, textvariable=hitThresh).grid(row=5, column=2)

Hit_ceiling = Label(Cadre5, text="Hit ceiling (deg):", state=DISABLED).grid(row=6, column=1)
HC = Entry(Cadre5, state=DISABLED).grid(row=6, column=2)

Hold_time = Label(Cadre5, text="Hold time (s):", state=DISABLED).grid(row=7, column=1)
HTime = Entry(Cadre5, state=DISABLED).grid(row=7, column=2)

def load_parameters():
    file_path = filedialog.askopenfilename()
    print("Selected file:", file_path)

    parameters = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            key, value = row
            parameters[key] = value
    
    return parameters

def save_configuration():
    top.withdraw()  # Hide the main window
    parameters = {}
    parameters['min_duration'] = minDuration.get().strip()
    hit_window = hitWindow.get().strip()
    hit_thresh = hitThresh.get().strip()
    init_thresh = iniThreshold.get().strip()
    init_baseline = iniBaseline.get().strip()

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return  # User canceled the dialog
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, value in parameters.items():
            writer.writerow([key, value])
            
    top.deiconify()

def save_parameters():
    min_duration = minDuration.get().strip()
    hit_window = hitWindow.get().strip()
    hit_thresh = hitThresh.get().strip()
    init_thresh = iniThreshold.get().strip()
    init_baseline = iniBaseline.get().strip()
    sendArduino("p" + init_thresh + ";" + init_baseline + ";" + min_duration + ";" + hit_window + ";" + hit_thresh)
    plotData(np.array(timeDeque).astype(float), np.array(dataDeque).astype(float))
    
loadParametersButton = Button(Cadre5, text="Load Parameters", background='white', command=load_parameters)
loadParametersButton.grid(row=6, column=6)


saveParametersButton = Button(Cadre5, text="Save Parameters", background='white', command=save_parameters, state="disabled")
saveParametersButton.grid(row=7, column=6)

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def entry_changed(*args):
    if ((iniThreshold.get().strip() and iniBaseline.get().strip() and minDuration.get().strip() and hitWindow.get().strip() and hitThresh.get().strip() )):
        saveParametersButton.config(state="normal")
        if not (is_int(iniThreshold.get()) and is_int(iniBaseline.get()) and is_int(minDuration.get()) and is_int(hitWindow.get()) and is_int(hitThresh.get())):
            saveParametersButton.config(state="disabled")
    else:
        saveParametersButton.config(state="disabled")

iniThreshold.trace_add("write", entry_changed)
iniBaseline.trace_add("write", entry_changed)
minDuration.trace_add("write", entry_changed)
hitWindow.trace_add("write", entry_changed)
hitThresh.trace_add("write", entry_changed)

# #infos sur les trials, rewards et temps passé
Cadre4 = Frame(top)
Cadre4.grid(row=1, column=2)

Trials = Label(Cadre4, text="Num Trials:", font=Gras).grid(row=1, column=1)
Rewards = Label(Cadre4, text="Num Rewards:", font=Gras).grid(row=1, column=1)
Med_pick = Label(Cadre4, text="Median Peak:", font=Gras).grid(row=2, column=1)
Pellet = Label(Cadre4, text="Pellet delivered:", font=Gras).grid(row=1, column=3)
timer_label = Label(Cadre4, text="Time elapsed: 11:11:11", font=Gras)
timer_label.grid(row=2, column=3)

# #_______________________________________________________________________________
top.mainloop()
