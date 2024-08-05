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

#from ads1015_python import ads1015

from ads1015 import ADS1015

import smbus2

bus = smbus2.SMBus(1)

ads1015 = ADS1015()
ads1015.set_mode("single")
ads1015.set_programmable_gain(2.048)
ads1015.set_sample_rate(1600)

channels = ["in0/ref", "in1/ref","in2/ref"]

reference = ads1015.get_reference_voltage()



import time
import threading
import numpy as np

import smbus2



serialBuffer = []
serialMessageBuffer = []

# SETTINGS
AnalogIN = 0
pinA = 2
pinB = 3
serialCommand = "wait"

init_sound = 400  # 4kHz
reward_sound = 1000  # 10kHz
failure_sound = 100  # 1kHz

initial = 0
previousA = -1
previousB = -1
previous_angle = 0
sum = 0
encoderPos = 0

lenBuffer = 250

# STATE MACHINE VARIABLES
initTrial = 0
baselineTrial = 0
startArduinoProg = time.time() * 1000
startSession = time.time() * 1000
startTrial = time.time() * 1000
bufferTimeFreq = 0
stopTrial = 0
LastTime = 0

# INPUT PARAMETERS
input_type = True

num_pellets = 0
num_rewards = 0
num_trials = 0

duration = 0
MaxTrialNum = 100

hold_time = 500
trial_hold_time = 0
hold_time_min = 0
hold_time_max = 1000

init_thresh = 0

hit_thresh = 0
trial_hit_thresh = 0
hit_thresh_min = 0
hit_thresh_max = 0

hit_window = 0

lever_gain = 1
failure_tolerance = 100

adapt_hit_thresh = False
adapt_hold_time = False
adapt_drop_tolerance = False

# LEVER VALUES
moduleValue_before = 0
moduleValue_now = 0
moduleValue_encoder = 0
peak_moduleValue = 0

# TIMERS
hold_timer = 0
it_timer = 0
session_t = 0
session_t_before = 0
trial_start_time = 0
trial_end_time = 0
trial_time = 0
pause_timer = 0
loop_timer = 0
experiment_start = time.time() * 1000
pause_time = 0

# BUFFERS
tmp_value_buffer = []  # [time, value]
trial_value_buffer = []  # [time, value]
past_10_trials_succ = []

# BOOLS
trial_started = False
success = False
crashed = False
stop_session = False
pause_session = False

# HARD-CODED VALUES
post_trial_dur = 1000
inter_trial_dur = 500
buffer_dur = 1000

# STATES
STATE_IDLE = 0
STATE_TRIAL_INIT = 1
STATE_TRIAL_STARTED = 2
STATE_HOLD = 3
STATE_SUCCESS = 4
STATE_FAILURE = 5
STATE_POST_TRIAL = 6
STATE_PARAM_UPDATE = 7
STATE_INTER_TRIAL = 8
STATE_SESSION_END = 9

CURRENT_STATE = STATE_IDLE
NEXT_STATE = CURRENT_STATE

# FUNCTIONS ---------------------------------

def get_timer_duration(start):
    return time.time() * 1000 - experiment_start - start

def get_mean(numbers):
    return np.mean(numbers)

def get_bool_mean(bools):
    return np.mean(bools)

def record_current_value():
    global trial_time, peak_moduleValue, max
    if not max:
        del max
    trial_time = session_t - trial_start_time
    values = [trial_time, moduleValue_now]
    if len(trial_value_buffer) >= lenBuffer:
        send_trial_data_to_python(False)
        trial_value_buffer.clear()
    trial_value_buffer.append(values)
    if (moduleValue_now > peak_moduleValue):
        print(moduleValue_now)
    peak_moduleValue = max(peak_moduleValue, moduleValue_now)

def state_machine():
    global session_t, session_t_before, moduleValue_before, moduleValue_now, trial_started
    global CURRENT_STATE, NEXT_STATE, num_trials, success, stop_session
    global peak_moduleValue, trial_time, trial_end_time, trial_value_buffer, pause_session, pause_time
    global loop_timer, trial_start_time, hit_thresh, hold_time, hold_timer, min, num_rewards
    global num_pellets, it_timer
    if not min:
        del min
    if pause_session:
        pause_time += time.time() * 1000 - experiment_start - pause_timer
        pause_timer = time.time() * 1000 - experiment_start
        return

    loop_time = time.time() * 1000 - experiment_start - loop_timer
    if loop_time - pause_time > 100:
        send_message("--- WARNING --- long delay in while loop" + str(loop_time))
    loop_timer = time.time() * 1000 - experiment_start

    session_t_before = session_t
    session_t = (time.time() * 1000 - experiment_start - pause_time)

    moduleValue_before = moduleValue_now
    if input_type:
#         moduleValue_now = read_analog(AnalogIN) * lever_gain
        moduleValue_now = ads1015.get_compensated_voltage(channel=channels[0], reference_voltage = reference) * lever_gain
    else:
        moduleValue_now = moduleValue_encoder

    condition = lambda row: session_t - row[0] <= buffer_dur
    tmp_value_buffer[:] = [row for row in tmp_value_buffer if condition(row)]

    if len(tmp_value_buffer) >= lenBuffer:
        tmp_value_buffer.pop(0)
    tmp_value_buffer.append([session_t, moduleValue_now])

    if trial_started:
        record_current_value()

    if CURRENT_STATE == STATE_IDLE:
        if session_t > duration * 60 :
            send_message('Time Out')
            NEXT_STATE = STATE_SESSION_END
        elif num_trials >= MaxTrialNum:
            NEXT_STATE = STATE_SESSION_END
        elif stop_session:
            send_message("Manual Stop")
            NEXT_STATE = STATE_SESSION_END
        elif moduleValue_now >= init_thresh and moduleValue_before < init_thresh:
            NEXT_STATE = STATE_TRIAL_INIT
            trial_start_time = session_t
            trial_started = True
            play(500, init_sound)

    elif CURRENT_STATE == STATE_TRIAL_INIT:
#         print("INIT")
        trial_started = True
        num_trials += 1

        if len(tmp_value_buffer) > 0:
            trial_value_buffer.clear()
            trial_value_buffer.extend([[sublist[0] - trial_start_time, sublist[1]] for sublist in tmp_value_buffer[:-1]])
            send_trial_data_to_python(False)
            trial_value_buffer.clear()

        NEXT_STATE = STATE_TRIAL_STARTED

    elif CURRENT_STATE == STATE_TRIAL_STARTED:
        print("STARTED, module value: " + str(moduleValue_now))
        if trial_time > hit_window * 1000 and moduleValue_now < hit_thresh:
            print("trial_time > hit_window and moduleValue_now < hit_thresh" + str(trial_time) + " > " + str(hit_window))
            NEXT_STATE = STATE_FAILURE
        elif moduleValue_now <= peak_moduleValue - failure_tolerance:
            print("moduleValue_now <= peak_moduleValue - failure_tolerance")
            NEXT_STATE = STATE_FAILURE
        elif moduleValue_now >= hit_thresh:
            hold_timer = time.time() * 1000 - experiment_start
            NEXT_STATE = STATE_HOLD

    elif CURRENT_STATE == STATE_HOLD:
        print("HOLD")
        if moduleValue_now < hit_thresh:
            hold_timer = time.time() * 1000 - experiment_start
            NEXT_STATE = STATE_TRIAL_STARTED
        elif get_timer_duration(hold_timer) >= hold_time:
            NEXT_STATE = STATE_SUCCESS

    elif CURRENT_STATE == STATE_SUCCESS:
        print("SUCCESS")
        trial_hit_thresh = hit_thresh
        trial_hold_time = hold_time
        send_message("STATE_SUCCESS")
        send_message("trial successful! :D\n")

        play(750, reward_sound)
        success = True
        trial_end_time = trial_time
        past_10_trials_succ.insert(0, True)
        if len(past_10_trials_succ) > 10:
            past_10_trials_succ.pop()

        if adapt_hit_thresh:
            if get_bool_mean(past_10_trials_succ) >= 0.7:
                hit_thresh = min(hit_thresh_max, hit_thresh + 1)

        if adapt_hold_time:
            if get_bool_mean(past_10_trials_succ) >= 0.7:
                hold_time = min(hold_time_max, hold_time + 10)

        num_rewards += 1
        num_pellets += 1

        NEXT_STATE = STATE_POST_TRIAL

    elif CURRENT_STATE == STATE_FAILURE:
        print("FAILURE")
        trial_hit_thresh = hit_thresh
        trial_hold_time = hold_time
        send_message("STATE_FAILURE")
        send_message("trial failed :(")

        play(1000, failure_sound)
        past_10_trials_succ.insert(0, False)
        if len(past_10_trials_succ) > 10:
            past_10_trials_succ.pop()

        success = False
        trial_end_time = trial_time

        if adapt_hit_thresh:
            if get_bool_mean(past_10_trials_succ) <= 0.4:
                hit_thresh = max(hit_thresh_min, hit_thresh - 1)

        if adapt_hold_time:
            if get_bool_mean(past_10_trials_succ) <= 0.4:
                hold_time = max(hold_time_min, hold_time - 10)

        NEXT_STATE = STATE_POST_TRIAL

    elif CURRENT_STATE == STATE_POST_TRIAL:
        print("POST_TRIAL")
        if trial_time - trial_end_time >= post_trial_dur:
            NEXT_STATE = STATE_PARAM_UPDATE
        else:
            print("trial_time : " + str(trial_time) + "\ntrial_end_time : " +
                  str(trial_end_time) + "\ntime - end_time = : " + str(trial_time - trial_end_time)
                  + "\npost_trial_dur : " + str(post_trial_dur))

    elif CURRENT_STATE == STATE_PARAM_UPDATE:
        print("UPDATE")
        send_message("STATE_PARAM_UPDATE")
        send_trial_data_to_python(True)
        trial_started = False
        trial_value_buffer.clear()
        peak_moduleValue = 0
        success = False

        it_timer = time.time() * 1000 - experiment_start
        NEXT_STATE = STATE_INTER_TRIAL

    elif CURRENT_STATE == STATE_INTER_TRIAL:
        print("INTER")
        if get_timer_duration(it_timer) >= inter_trial_dur:
            it_timer = time.time() * 1000 - experiment_start
            NEXT_STATE = STATE_IDLE

    elif CURRENT_STATE == STATE_SESSION_END:
        print("SESSION_END")
        send_message(str(time.time() * 1000 - experiment_start))
        send_message("done")
#         send_message("STATE_SESSION_END")

        serialCommand = "e"
        reinitialize()

    else:
        send_message("default")
        send_message("error in state machine!")

        serialCommand = "e"

    CURRENT_STATE = NEXT_STATE

prev_tone = 0

def play(milliseconds, freq):
    global prev_tone
    send_message("in play func")
    if time.time() - prev_tone > 0.2:
        send_message("can play")
        prev_tone = time.time() * 1000 - experiment_start
        threading.Timer(milliseconds / 1000, send_message, args=(freq,)).start()

def read_analog(channel):
    # Simulate reading an analog value (0 to 1023) from the specified channel.
    # Replace this with actual hardware interaction in practice.
    return np.random.randint(0, 1024)

def send_trial_data_to_python(done):
    global trial_value_buffer, success, trial_hit_thresh, trial_hold_time
    global num_trials, trial_start_time, init_thresh, hit_thresh, hold_time, trial_end_time
    global success, peak_moduleValue, num_pellets, num_rewards, trial_hold_time, trial_hit_thresh
    global serialBuffer, sending
    sending = True
    addition = ""
    for i in range(len(trial_value_buffer)):
        # detachInterrupts();
        addition += str(trial_value_buffer[i][0])
        addition += str("/")
        addition += str(trial_value_buffer[i][1])
        addition += str(";")
        # attachInterrupts();
    # detachInterrupts();
    addition += str("nt")
    addition += str(num_trials)
    addition += str(";")
    addition += str(trial_start_time)
    addition += str(";")
    addition += str(init_thresh)
    addition += str(";")
    addition += str(hold_time)
    addition += str(";")
    addition += str(hit_thresh)
    addition += str(";")
    addition += str(trial_end_time)
    addition += str(";")
    addition += str(success)
    addition += str(";")
    addition += str(peak_moduleValue)
    addition += str(";")
    addition += str(num_pellets)
    addition += str(";")
    addition += str(num_rewards)
    addition += str(";")
    addition += str(trial_hold_time)
    addition += str(";")
    addition += str(trial_hit_thresh)
    if (not done):
        addition += str("partialEnd");
    serialBuffer.append(addition)
    
    sending = False;
    # attachInterrupts();
    # interrupts();
    # code de fin d'envoi de données

def send_message(msg):
    global serialMessageBuffer
    serialMessageBuffer.append(str(msg))

def reinitialize():
    global num_trials, num_pellets, num_rewards, initTrial, baselineTrial, trial_started, experiment_start
    num_trials = 0
    num_pellets = 0
    num_rewards = 0
    initTrial = 0
    baselineTrial = 0
    trial_started = False
    experiment_start = time.time() * 1000
    # Reset other necessary variables.

def experimentOn():
    global pause_timer
    global serialCommand
    global stop_session
    while serialCommand[0] != "w" and serialCommand[0] != "e":
        if serialCommand[0] == "f":
            feed()
            serialCommand = "s"
        elif serialCommand[0] == "c":
            if not pause_session:
                pause_timer = time.time() * 1000 - experiment_start
            else:
                send_message("pause time")
                send_message(pause_time)
            pause_session = not pause_session
            serialCommand = "s"
        elif (serialCommand[0] == "a"):
            send_message("received stop")
            stop_session = True
        state_machine()


        
            

def main_loop():
    print("in thread")
    global initTrial
    global init_thresh
    global baselineTrial
    global duration
    global hit_window
    global hit_thresh
    global adapt_hit_thresh
    global hit_thresh_min
    global hit_thresh_max
    global lever_gain
    global failure_tolerance
    global MaxTrialNum
    global hold_time
    global adapt_hold_time
    global hold_time_min
    global hold_time_max
    global input_type
    global stop_session
    global serialCommand
    global serial_command
    while True:
        if serialCommand == "":
            continue
        first = serialCommand[0]
        if first == "w":
            i = 0
        elif first == "p":
            send_message("received parameters");
            variables = serialCommand[1:];
            serialCommand = "";
            parts = variables.split(";");
            initTrial = float(parts[0]);
            init_thresh = int(parts[0]);
            baselineTrial = float(parts[1]);
            duration = float(parts[2]) * 1000;
            hit_window = float(parts[3]);
            hit_thresh =float(parts[4]);
            adapt_hit_thresh = bool(parts[5]);
            hit_thresh_min = float(parts[6]);
            hit_thresh_max = float(parts[7]);
            lever_gain =float(parts[8]);
            failure_tolerance =float(parts[9]);
            MaxTrialNum =float(parts[10]);
            hold_time =float(parts[11]) * 1000;
            adapt_hold_time= bool(parts[12]);
            hold_time_min = float(parts[13]) * 1000;
            hold_time_max = float(parts[14]) * 1000;
            input_type = bool(parts[17]);

            # if(input_type) {
            # detachInterrupt(digitalPinToInterrupt(pinA));
            # detachInterrupt(digitalPinToInterrupt(pinB));
            # send_message("input_type true");
            # }
            # else {
            # attachInterrupt(digitalPinToInterrupt(pinA), updateEncoderValue, CHANGE);
            # attachInterrupt(digitalPinToInterrupt(pinB), updateEncoderValue, CHANGE);
            # send_message("input_type false");
            # }
        elif first == "s":
            send_message("received start")
            experimentOn()
        elif first == "a":
            send_message("received stop")
            stop_session = True
        time.sleep(0.01)  # Simulate loop delay

print("starting thread")
main_thread = threading.Thread(target=main_loop)
#     second_thread = threading.Thread(target=
main_thread.start()



lever_type = True

arduino = None
connected = False



session_running = False
session_paused = False
num_pellets = 0
num_rewards = 0
num_trials = 0
parameters = {}
trial_table = {}


trial_table = []

session = {}




global buffer_size
# buffer_size = 10000

# dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
# timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 

dataDeque = deque()
timeDeque = deque() 

# StorageVariable
# global sensorValueTrial
# sensorValueTrial = np.empty((1, buffer_size),
#                             dtype="float")  # accumulation ligne par ligne des valeurs du senseur à chaque essai
# global sensorTimeStamp
# sensorTimeStamp = np.empty((1, buffer_size), dtype="float")  # les temps pour chacun des essais


def testConnection():
    try:
        return sendArduino("testing")
    except Exception as e:
        print("An error occurred:", e)
        disconnected()
        return False

def connectArduino():
    print("connecting")
    global connected
    clear_stats()
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
        if (not port.description):
            port.description = ""
        if (not port.manufacturer):
            port.manufacturer = ""
        if "tty" in port.description.lower() or "tty" in port.manufacturer.lower() or "tty" in port.device.lower():
            print(port.description.lower())
            description = port.description
            print(description)
            port_found = port.device
    port_found = "/dev/pts/4"
    description = "the raspberry pi"
    if port_found == None:
        print("Arduino not found")
        lamp.turn_off()
        return
    else:
        print(f"Arduino found at port {port_found} in description {description}")
        lamp.turn_on()
        

    
    # Serial communication
    # if arduino:
    #     arduino.close()
    # arduino = serial.Serial(port_found, 115211)
    t.sleep(1)
    # arduino.flushInput()  # vide le buffer en provenance de l'arduino
    connected = True

    testConnection()

    entry_changed()
        

# Boutons de contrôle____________________________________________________________
def sendArduino(text):
    global serialCommand
    cmd = text + '\r'
    try:
#         arduino.write(cmd.encode())
#         arduino.reset_output_buffer()
        serialCommand = text
        print(serialCommand)
        return True
    except serial.SerialException:
        print("Device not connected.")
        disconnected()
        return False
    except PermissionError:
        print("Device not connected.")
        disconnected()
        return False


def readArduinoInput():
    # Arduino envoie deux lignes une première de valeurs du senseur et une deuxième des timestamps
    # global sensorValueTrial
    # global sensorTimeStamp
    global dataDeque, timeDeque

    received, dataArray, timeArray = readArduinoLine()
    if not received:
        return
    else:
        print("received")

    # # Deuxième ligne
        
    plotData(timeArray, dataArray)
    
    # arduino.flushInput()  # vide le buffer en provenance de l'arduino

stateList = []
pieces = 0
def readArduinoLine():
    global pieces
    global dataDeque
    global timeDeque
    global num_trials, num_pellets, num_rewards
    global serialBuffer, serialMessageBuffer
#     output = arduino.readline()
#     output = str(output, 'utf-8') 
    if (len(serialMessageBuffer) > 0):
        new_output = serialMessageBuffer[0]
        serialMessageBuffer.pop(0)
        stateList.append(new_output)    
#         print("*\n*")
#         print(stateList[-100:])
        if ("done" in new_output):
            stop_Button()
        return False, np.zeros(0), np.zeros(0)
    if (len(serialBuffer) > 0):
        print("got trial data")
        partial = False
        output = serialBuffer[0]
        serialBuffer.pop(0)
        

        if ("partialEnd" in output):
            partial = True
            pieces += 1
            output = output.removesuffix('partialEnd')  # input en 'string'. Each arduino value is separated by ';'
        # data = output.split(";nt", 1)
#         print(output)
        data = output.split("nt", 1)
        trial_data = data[0].split(";")
#         print(len(trial_data))
        # dataDeque = deque([0] * buffer_size, maxlen=buffer_size)
        # timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        for pair in trial_data:
            if pair:  # Ignore empty strings
#                 print(pair, end=' ')
                try:
                    time, value = pair.split('/')
                except ValueError as e:
                    print("pair : " + str(pair))
                    print(e)
                except Exception as e:
                     print("pair : " + str(pair))
                     print(e)
                try:
                    if not (time == '0' and value == '0') and abs(float(time)) < 10000 and float(value) < 2000:
                        dataDeque.extend([value])
                        timeDeque.extend([time])
                except ValueError as e:
                    print("pair : " + str(pair))
                    print(e)
                    continue
#         print("\n")

        
#         zipped = list(zip(timeDeque, dataDeque))
#         for item in range(len(zipped)):
#             if (float(zipped[item][0]) > 10000):
#                 print(str(item) + str(zipped[item]), end = " ")
#         print("x")

        dataArray = np.array(dataDeque).astype(float)
        timeArray = np.array(timeDeque).astype(float)
        
        dataList = dataArray
        timeList = timeArray
        dataList = dataList.tolist()
        timeList = timeList.tolist()

        if partial:
            pieces += 1
            print("PARTIAL SPLIT")
            return False, np.zeros(0), np.zeros(0)
        else:
            print("FULL")
        
        pieces += 1
#         print("pieces" + str(pieces))
        pieces = 0
        # dataDeque = deque([0], maxlen=buffer_size)
        # timeDeque = deque([0] * buffer_size, maxlen=buffer_size) 
        dataDeque.clear()
        timeDeque.clear()
        stateList.clear()

    
    
    
        trial_numbers = data[1].split(";")
        num_trials = int(trial_numbers[0])
        trial_start_time = int(float(trial_numbers[1]) / 1000)
        
        init_thresh = int(trial_numbers[2])
        hold_time = int(float(trial_numbers[3]))
        parameters["holdTime"].set(str(float(trial_numbers[3]) / 1000))

        hit_thresh = int(float(trial_numbers[4]))
        parameters["hitThresh"].set(str(int(float(trial_numbers[4]))))
        trial_end_time = int(float(trial_numbers[5]))
        success = bool(trial_numbers[6])
        if success:
            display("Success")
        else:
            display("Failed")
        peak_moduleValue = int(float(trial_numbers[7]))
        num_pellets = int(trial_numbers[8])
        num_rewards = int(trial_numbers[9])
        trial_hold_time = int(float(trial_numbers[10]))
        trial_hit_thresh = int(float(trial_numbers[11]))

        trial = {}
        trial["start_time"] = trial_start_time / 1000
        trial["init_thresh"] = init_thresh
        trial["hit_thresh"] = trial_hit_thresh
        trial["Force"] = list(zip(list(timeList), list(dataList)))
        trial["hold_time"] = trial_hold_time
        trial["duration"] = trial_end_time / 1000
        trial["success"] = success
        trial["peak"] = peak_moduleValue

        trial_table.append(trial)

        session["Last_hit_thresh"] = trial_hit_thresh
        session["Last_hold_time"] = trial_hold_time


        return True, dataArray, timeArray

    else:

        print("full input not found")

        return False, np.zeros(0), np.zeros(0)
    



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
    sum = 0
    for i in range(len(time_Array) - 1):
        sum += time_Array[i + 1] - time_Array[i];
    if (len(time_Array) > 0):
        average = sum / len(time_Array)
        time_total = (time_Array[len(time_Array) - 1] - time_Array[0]) / 1000
        print("Time total" + str(time_total))
        hertz = len(data_Array) / time_total
        print("Average time between! : " + str(average))
        print("Time example: " + str(time_Array[0]) + " " + str(time_Array[len(time_Array) - 1]))
        print("Hertz : " + str(hertz))
    time_Array = time_Array[length:]
    data_Array = data_Array[length:]
    # for i in range(len(time_Array)):
    #     if float(data_Array[i]) != 0:
            # print(str(time_Array[i]) + " with " + str(data_Array[i]))
    # axeTempRel
    global max_force
    
    # axeTempRel = (time_Array - time_Array.min()) / 1000
    axeTempRel = (time_Array) / 1000
    
    if len(axeTempRel) == 0:
        max_time = 3
    else:
        max_time = axeTempRel.max()

    ax.clear()
    
    canvas.draw()
    canvas.flush_events()
    if len(data_Array) > 0:
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
        ax.plot([-1, float(parameters["hitWindow"].get())], [0, 0], color='black', linestyle='--', linewidth=0.25)
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
    
    if lever_type:
        ax.set_title("Pulling Force", fontsize=7)
        ax.set_ylabel('Force(g)',fontsize=6)
    else:
        ax.set_title("Knob Rotation", fontsize=7)
        ax.set_ylabel('Rotation(deg)',fontsize=6)
    ax.set_xlabel('Time(s)',fontsize=6)
    ax.margins(.15)
    canvas.draw()
    canvas.flush_events()

def updateDisplayValues():
    Trials.config(text=str(num_trials))
    Rewards.config(text=str(num_rewards))
    Pellet.config(text=f"{num_pellets} ({round(num_pellets * 0.045, 3):.3f} g)")

pause_start = t.time()
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

    

def disconnected():
    global session_running
    global session_paused
    global connected
    session_paused = False
    session_running = False
    connected = False
    lamp.turn_off()
    startButton.config(state="disabled")
    startButton.config(text="START")
    stopButton.config(state="disabled")
    entry_changed()

def toggle_start2():
    global session_paused
    if not session_paused and session_running:
        session_paused = True
        pause()
    else:
        session_paused = False
        startButton.config(text="PAUSE")
        if not session_running:
            start()
        else:
            resume()

pause_start = None
pause_time = 0
def resume():
    global session_paused
    global pause_time
    session_paused = False
    sendArduino('c')
    print("setting thing to pause in resume")
    startButton.config(text="PAUSE")
    # start()
        

def pause():
    global session_paused
    global pause_start
    pause_start = t.time()
    session_paused = True
    sendArduino('c')
    startButton.config(text="RESUME")

start_time = None

def start():
    # Déclenche la session comportement
    print("starting")
    global session_running
    global session
    global max_force
    global serialBuffer, serialMessageBuffer
    max_force = 0
    current_datetime = datetime.now()
    session["Start_time"] = current_datetime.strftime("%d-%B-%Y %H:%M:%S")
    session["Initial_hit_thresh"] = parameters["hitThresh"].get()
    session["Initial_hold_time"] = float(parameters["holdTime"].get()) * 1000

    session_running = True
    startButton.config(text="PAUSE")
    stopButton.config(state="normal")
    if not testConnection():
        return
    try:
        # arduino.flush()
        # arduino.flushInput()
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
                # if arduino.inWaiting() > 1:
                #     readArduinoInput()
                if len(serialBuffer) > 0 or len(serialMessageBuffer) > 0:
                    readArduinoInput()
                top.update()
            except serial.SerialException:
                disconnected()
                print("The device unexpectedly disconnected.")
                break
        
            
    except serial.SerialException as E:
        print(E)
        stop_Button()
        disconnected()
        
        print("There is no device connected.")


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
        sendArduino('a')
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

def save_trial_table(filename):
    global trial_table

    try:
        with open(filename, mode='w', newline='') as csvfile:
            fieldnames = ["start_time", "init_thresh", "hit_thresh", "Force", "hold_time", "duration", "success", "peak"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for trial in trial_table:
                # Convert list of Force values to a string for CSV
                trial["Force"] = ', '.join(map(str, trial["Force"]))
                writer.writerow(trial)
    except PermissionError:
        display("Cannot write to open file")

def save_file(file_path, dict):
    saved_parameters = {}
    for key, value in dict.items():
        saved_parameters[key] = value.get()

    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in saved_parameters.items():
                writer.writerow([key, value])
    except PermissionError:
        display("Cannot write to open file")

    

    

def display(text):
    DisplayBox.config(text=text)


def save_results(crashed):
    file_input_type = "_RatPull"
    if not lever_type:
        file_input_type = "_RatKnob"
    if crashed:
        response = messagebox.askyesno("Sorry about that...", "RatPull lever_pull_behavior Crashed!\nSave results?")
    else:
        response = messagebox.askyesno("End of Session", "End of behavioral session\nSave results?")
    
    rat_dir = os.path.join(parameters["saveFolder"].get(), str(parameters["ratID"].get()))
    if response:
        dir_exists = os.path.exists(rat_dir)
        if not dir_exists:
            display(f'Creating new folder for animal parameters["ratID"].get()\n')
            try:
                dir_exists = True
                os.mkdir(rat_dir)
            except OSError:
                dir_exists = False
                display('Failed to create new folder in specified location')
                
            
        
        if dir_exists:
            ttfname = parameters["ratID"].get() + file_input_type + '_trial_table_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
            pfname = parameters["ratID"].get() + file_input_type + '_params_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
            gfname = parameters["ratID"].get() + '_global_stats.csv'
            save_trial_table(os.path.join(rat_dir, ttfname))
            # save_file(os.join(rat_dir, ttfname), trial_table)
            save_file(os.path.join(rat_dir, pfname), parameters)

            display('Behavior stats and parameters saved successfully')
            update_global_stats(os.path.join(rat_dir, gfname))
        else:
            display('Behavior stats and parameters NOT saved')
    

# def save_session():
#     global sensorValueTrial
#     global sensorTimeStamp
#     dir_target = parameters["savefolder"].get()
#     np.savetxt(dir_target, sensorValueTrial, delimiter=",")

def update_global_stats(filename):
    global session
    session["Number_trials"] = num_trials
    session["Number_rewards"] = num_rewards

    exists = os.path.isfile(filename)
    try:
        with open(filename, mode='a', newline='') as csvfile:
            fieldnames = ["Start_time", "Number_trials", "Number_rewards", "Initial_hit_thresh", "Last_hit_thresh", "Initial_hold_time", "Last_hold_time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not exists:
                print("writing header")
                writer.writeheader()

            writer.writerow(session)
    except PermissionError:
        display("Cannot write to open file")


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

def clear_stats():
    trial_table.clear()
    session.clear()
    startButton.config(text="START")

def reset_device():
    print("resetting")
    # if arduino:
    #     print("resetting")
    #     # time.sleep(0.1)
    #     # arduino.setDTR(True)
    #     # arduino.setRTS(True)
    #     # arduino.dtr = True
    #     arduino.close()
    # else:
    #     print("not resetting")


def finish_up(crashed):
    display('Session Ended');
    
    # reset_buttons(app)

    # trial_table = trial_table(1:num_trials, :);  
    # trial_table.Properties.CustomProperties.num_trials  = num_trials;
    # trial_table.Properties.CustomProperties.num_rewards = num_rewards;
    # trial_table.Properties.CustomProperties.rat_id      = app.rat_id.Value;
    # display_results(session_t, num_trials, num_rewards, app.num_pellets, app.man_pellets);
    save_results(crashed);
    clear_stats()

def save_configuration():
    global parameters
    # top.withdraw()  # Hide the main window
    saved_parameters = {}
    for key, value in parameters.items():
        saved_parameters[key] = value.get()



    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return  # User canceled the dialog
    
    try:
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in saved_parameters.items():
                writer.writerow([key, value])
    except PermissionError:
        display("Cannot write to open file")
    

    print("Configuration saved")
    # top.deiconify()

def send_parameters():
    global parameters
    parameters["iniBaseline"].set("1")
    message = "p"
    for value in parameters.values():
        message += str(value.get()) + ";"
    message += str(lever_type)
    sendArduino(message)
    # sendArduino("p" + init_thresh + ";" + init_baseline + ";" + min_duration + ";" + hit_window + ";" + hit_thresh)
    reload_plot()
    



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
    if not connected:
        return False
    parameters["iniBaseline"].set("1")
    startButton.config(state="disabled")
    for key, value in parameters.items():
        if not value.get() and not is_boolean(value.get()):
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
            startButton.config(state="normal")
            return True
        else:
            if not is_int(value.get()):
                return False
            
    startButton.config(state="normal")
    return True

def toggle_input_type(frame, depth):
    global lever_type
    # print("\n" + str(depth))
    
    for child in frame.winfo_children():
        if isinstance(child, (Label)):
            text = child.cget("text")
            if lever_type:
                child.config(text=text.replace("(g)", "(deg)").replace("Pull", "Knob"))
            else:
                child.config(text=text.replace("(deg)", "(g)").replace("Knob", "Pull"))
        elif isinstance(child, (Frame)) and child != frame:
            # print("Going deeper...")
            toggle_input_type(child, depth + 1)
    if depth == 0:
        lever_type = not lever_type
        reload_plot()

def reload_plot():
    plotData(np.array(timeDeque).astype(float), np.array(dataDeque).astype(float))
#########################################################
#########################################################
##########GGGGGG######U##############U####I##############
#######G##############U##############U####I##############
#####G################U##############U####I##############
####G#################U##############U####I##############
###G##################U##############U####I##############
###G##################U##############U####I##############
###G#########GGGGGG###U##############U####I##############
###G##############G###U##############U####I##############
####G#############G###U##############U####I##############
#####G############G###U##############U####I##############
#######G#GGGGGGGG#####UUUUUUUUUUUUUUUU####I##############
#########################################################
#########################################################
#########################################################
# #_______________________________________________________________________________
# GUI
# création de l'interface avec titre et taille de la fenêtre
top = Tk()
top.title("Moto Knob Controller")
top.resizable(False, False)

# définition des valeurs modifiable par des entrés

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

for value in parameters.values():
    value.trace_add("write", entry_changed)

CadreGauche = Frame(top)
CadreGauche.grid(row=0, column=0, padx=20, pady=20)
vertical_border = Frame(top, width=1, bg="black")
vertical_border.grid(row=0, column=1, sticky="ns")
CadreDroite = Frame(top)
CadreDroite.grid(row=0, column=2, padx=20, pady=20)

# ________________________________________________________________

# définition du cadre de titre

Cadre1 = Frame(CadreGauche)
Cadre1.grid(row=1, column=1)


# Boutons de tests_______________________________________________________________
Title = Label(Cadre1, text="Rat Pull Task", fg='black', justify=CENTER, font=("bold", 25), padx=5, pady=25, width=11, height=1).grid(row=1, column=2)
lamp = UILamp(Cadre1, diameter=32)
lamp.grid(row=2, column=4)
Connect = Button(Cadre1, text="Connect Device", command=connectArduino, width=13, font= ("Serif", 11, "bold")).grid(row=2, column=5)
# Retract = Button(Cadre1, text="Retract\nSensor At Pos", state=DISABLED).grid(row=2, column=5)

# infos sur le rat et la sauvegarde des données
Rat = Label(Cadre1, text="Rat ID:  ", font=("Serif", 11, "bold")).grid(row=2, column=0)
Rat_ID = Entry(Cadre1, width=10, textvariable=parameters["ratID"]).grid(row=2, column=1)

# ________________________________________________________________
# définition du cadre de boutons

Cadre2 = Frame(CadreGauche)
Cadre2.grid(row=3, column=1, sticky="n", pady=(20,20))
Cadre2.grid_rowconfigure(0, pad=10,)
Cadre2.grid_columnconfigure(0, pad=10, weight=1)
Cadre2.grid_columnconfigure(1, pad=10, weight=1)
Cadre2.grid_columnconfigure(2, pad=10, weight=1)
Cadre2.grid_columnconfigure(3, pad=10, weight=1)
timer_running = False


startButton = Button(Cadre2, text="START", background='#64D413', state=DISABLED, command=lambda: toggle_start2())
startButton.grid(row=0, column=0)

stopButton = Button(Cadre2, text="STOP", background='red', state=DISABLED, command=stop_Button)
stopButton.grid(row=0, column=1)

feedButton = Button(Cadre2, text="FEED", background='#798FD4', state=NORMAL, command=feed)
feedButton.grid(row=0, column=2)

removeOffsetButton = Button(Cadre2, text='Remove\nOffset', state=DISABLED)
removeOffsetButton.grid(row=0, column=3)


set_button_size(Cadre2, 10, 2, ('Serif', 10, "bold"))





# ________________________________________________________________
# définition du cadre d'information de trials
# #infos sur les trials, rewards et temps passé
Cadre3 = Frame(CadreDroite)
Cadre3.grid(row=1, column=2)

Cadre3.grid_rowconfigure(0, pad=10,)
Cadre3.grid_columnconfigure(0, pad=10, weight=1)
Cadre3.grid_columnconfigure(1, pad=10, weight=1)
Cadre3.grid_columnconfigure(2, pad=10, weight=1, minsize=100)
Cadre3.grid_columnconfigure(3, pad=10, weight=1)

font = ("Serif", 12, "bold")

TrialsLabel = Label(Cadre3, text="Num Trials:", font=font)
TrialsLabel.grid(row=1, column=0)
Trials = Label(Cadre3, text="0", font=font)
Trials.grid(row=1, column=1)
RewardsLabel = Label(Cadre3, text="Num Rewards:", font=font)
RewardsLabel.grid(row=2, column=0)
Rewards = Label(Cadre3, text="0", font=font)
Rewards.grid(row=2, column=1)
# Med_pick = Label(Cadre3, text="Median Peak:", font="bold").grid(row=2, column=1)
PelletLabel = Label(Cadre3, text="Pellets delivered:", font=font)
PelletLabel.grid(row=1, column=3)
Pellet = Label(Cadre3, text="0 (0.000 g)", font=font)
Pellet.grid(row=1, column=4)
timer_label = Label(Cadre3, text="Time elapsed:", font=("Serif", 14, weight:="bold"),fg="blue")
timer_label.grid(row=2, column=3)
timer_clock = Label(Cadre3, text="00:00:00", font=("Serif", 14,"bold"),fg="blue")
timer_clock.grid(row=2, column=4)


set_sticky(Cadre3)

# ________________________________________________________________
# définition du cadre d'entrées de paramètres
# --------------------------------
Cadre4 = Frame(CadreGauche)
Cadre4.grid(row=2, column=1, padx=20, pady=(0, 20))
# Cadre5.config(borderwidth=2, relief=RIDGE)
Cadre4.config(relief=RIDGE)
Cadre5 = Frame(Cadre4)
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
border = Frame(Cadre4, height=0.3, bg="black")
border.grid(row=1, column=0, sticky="ew")

Parametre = Label(Cadre4, text="Parameters: ", fg='black', justify=LEFT, font="bold").grid(row=0, column=0, sticky="w")

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

loadParametersButton = Button(Cadre5, text="Load", background='white', width=12, command=load_parameters)
loadParametersButton.grid(row=6, column=3, columnspan=2)

saveConfigurationButton = Button(Cadre5, text="Save", background='white', width=10, command=save_configuration)
saveConfigurationButton.grid(row=6, column=5, columnspan=2)

set_text_bg(Cadre5)

Cadre6 = Frame(CadreDroite)
Cadre6.grid(row=2, column=2)

Title_array = Label(Cadre6, text="Knob Rotation Angle").grid(row=1, column=1, columnspan=2, pady=2)
# fig = plt.Figure(figsize=(3, 2), dpi=211, layout='constrained')
fig = plt.Figure(figsize=(3, 3), dpi=200)
ax = fig.add_subplot(111)

fig.patch.set_facecolor('#f0f0f0')
canvas = FigureCanvasTkAgg(fig, master=Cadre6)  # tk.DrawingArea.
canvas.get_tk_widget().grid(row=1, column=1, columnspan=2, sticky='E', pady=2)


Cadre7 = Frame(CadreGauche)
Cadre7.grid(row=4, column=1, sticky="n", pady=(20,20))


typeButton = Button(Cadre7, text='Toggle Input Type', command=lambda: toggle_input_type(top, 0))
typeButton.grid(row=1, column=2)
# Label qui montre des messages
DisplayBox = Label(Cadre7, text="", font=("Serif", 12))
DisplayBox.grid(row=2, column=2, sticky="n", pady=(20,20))


reload_plot()
top.mainloop()


# removed stuff



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