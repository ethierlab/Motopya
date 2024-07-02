import time
import threading
import numpy as np

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
startArduinoProg = time.time()
startSession = time.time()
startTrial = time.time()
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
hold_timer = time.time()
it_timer = time.time()
session_t = 0
session_t_before = 0
trial_start_time = 0
trial_end_time = 0
trial_time = 0
pause_timer = time.time()
loop_timer = time.time()
experiment_start = time.time()
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
    return time.time() - start

def get_mean(numbers):
    return np.mean(numbers)

def get_bool_mean(bools):
    return np.mean(bools)

def record_current_value():
    global trial_time, peak_moduleValue
    trial_time = session_t - trial_start_time
    values = [trial_time, moduleValue_now]
    if len(trial_value_buffer) >= lenBuffer:
        send_trial_data_to_python(False)
        trial_value_buffer.clear()
    trial_value_buffer.append(values)
    peak_moduleValue = max(peak_moduleValue, moduleValue_now)

def state_machine():
    global session_t, session_t_before, moduleValue_before, moduleValue_now, trial_started
    global CURRENT_STATE, NEXT_STATE, num_trials, success, stop_session
    global peak_moduleValue, trial_time, trial_end_time, trial_value_buffer, pause_session, pause_time

    if pause_session:
        pause_time += time.time() - pause_timer
        pause_timer = time.time()
        return

    loop_time = time.time() - loop_timer
    if loop_time - pause_time > 0.1:
        send_message("--- WARNING --- long delay in while loop")
    loop_timer = time.time()

    session_t_before = session_t
    session_t = time.time() - experiment_start - pause_time

    moduleValue_before = moduleValue_now
    if input_type:
        moduleValue_now = read_analog(AnalogIN) * lever_gain
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
        if session_t > duration * 60:
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
        trial_started = True
        num_trials += 1

        if len(tmp_value_buffer) > 0:
            trial_value_buffer.clear()
            trial_value_buffer.extend([[sublist[0] - trial_start_time, sublist[1]] for sublist in tmp_value_buffer[:-1]])
            send_trial_data_to_python(False)
            trial_value_buffer.clear()

        NEXT_STATE = STATE_TRIAL_STARTED

    elif CURRENT_STATE == STATE_TRIAL_STARTED:
        if trial_time > hit_window and moduleValue_now < hit_thresh:
            NEXT_STATE = STATE_FAILURE
        elif moduleValue_now <= peak_moduleValue - failure_tolerance:
            NEXT_STATE = STATE_FAILURE
        elif moduleValue_now >= hit_thresh:
            hold_timer = time.time()
            NEXT_STATE = STATE_HOLD

    elif CURRENT_STATE == STATE_HOLD:
        if moduleValue_now < hit_thresh:
            hold_timer = time.time()
            NEXT_STATE = STATE_TRIAL_STARTED
        elif get_timer_duration(hold_timer) >= hold_time:
            NEXT_STATE = STATE_SUCCESS

    elif CURRENT_STATE == STATE_SUCCESS:
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
        if trial_time - trial_end_time >= post_trial_dur:
            NEXT_STATE = STATE_PARAM_UPDATE

    elif CURRENT_STATE == STATE_PARAM_UPDATE:
        send_message("STATE_PARAM_UPDATE")
        send_trial_data_to_python(True)
        trial_started = False
        trial_value_buffer.clear()
        peak_moduleValue = 0
        success = False

        it_timer = time.time()
        NEXT_STATE = STATE_INTER_TRIAL

    elif CURRENT_STATE == STATE_INTER_TRIAL:
        if get_timer_duration(it_timer) >= inter_trial_dur:
            it_timer = time.time()
            NEXT_STATE = STATE_IDLE

    elif CURRENT_STATE == STATE_SESSION_END:
        send_message(str(time.time()))
        send_message("done")
        send_message("STATE_SESSION_END")

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
        prev_tone = time.time()
        threading.Timer(milliseconds / 1000, send_message, args=(freq,)).start()

def read_analog(channel):
    # Simulate reading an analog value (0 to 1023) from the specified channel.
    # Replace this with actual hardware interaction in practice.
    return np.random.randint(0, 1024)

def send_trial_data_to_python(trial_end):
    global trial_value_buffer, success, trial_hit_thresh, trial_hold_time
    trial_data = {
        "trial_end": trial_end,
        "success": success,
        "trial_hit_thresh": trial_hit_thresh,
        "trial_hold_time": trial_hold_time,
        "data": trial_value_buffer
    }
    print(trial_data)  # Replace with actual data sending mechanism.

def send_message(msg):
    print(msg)  # Replace with actual message sending mechanism.

def reinitialize():
    global num_trials, num_pellets, num_rewards, initTrial, baselineTrial, trial_started
    num_trials = 0
    num_pellets = 0
    num_rewards = 0
    initTrial = 0
    baselineTrial = 0
    trial_started = False
    # Reset other necessary variables.

# Example main loop, replace with appropriate execution mechanism
def main_loop():
    while not stop_session:
        state_machine()
        time.sleep(0.01)  # Simulate loop delay

if __name__ == "__main__":
    main_thread = threading.Thread(target=main_loop)
    main_thread.start()