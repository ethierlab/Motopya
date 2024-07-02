// #include <CircularBuffer.h>

#include <queue>
#include <chrono>
#include <string>
#include <vector>
#include <algorithm>  // Include the algorithm header for std::copy_if
#include <iterator>   // Include the iterator header for std::back_inserter
#include <numeric>
#include <iostream>
#include <sstream>

#include <iostream>
#include <wiringPi.h>
#include <wiringPiI2C.h>
#include <wiringSerial.h>
#include <unistd.h>

#include <cstdio> //for popen() and pclose()
#include <cstring> // for fgets()

#define SERIAL_PORT "/dev/ttyS0"  // Serial port for communication, change if necessary



using namespace std;

// DECLARATION VARIABLES------------

//Settings
int AnalogIN = 0;
const int pinA = 5;  // A output
const int pinB = 6;  // B output
string serialCommand = "wait";

int initial;
int previousA = -1;
int previousB = -1;
int previous_angle;
int sum = 0;
int encoderPos = 0;

int serialFd = 0;
int analog_fd = 0;

const int ADS1015_I2C_ADDR = 0x48;
const int ADS1015_CONFIG_REG= 0x01;
const int ADS1015_CONVERSION_REG = 0x00;


// code controllers
const int lenBuffer = 25000;

//state machine variables

float initTrial;
float baselineTrial;
unsigned long startArduinoProg;
unsigned long startSession;
unsigned long startTrial;
unsigned long bufferTimeFreq;
unsigned long stopTrial;
unsigned long LastTime;  // le dernier temps du buffer data



// - input Parameters

bool input_type = true;


int num_pellets = 0;
int num_rewards = 0;
int num_trials = 0;

int duration;
int MaxTrialNum = 100;

int hold_time = 500;
int trial_hold_time;
int hold_time_min = 0;
int hold_time_max = 1000;

int init_thresh = 0;

int hit_thresh;
int trial_hit_thresh;
int hit_thresh_min;
int hit_thresh_max;

int hit_window;

float lever_gain = 1;
int failure_tolerance = 100;

bool adapt_hit_thresh;
bool adapt_hold_time;
bool adapt_drop_tolerance;

// - lever values
int moduleValue_before = 0;
int moduleValue_now = 0;
int moduleValue_encoder = 0;
int peak_moduleValue = 0;

// - timers
auto hold_timer = millis();
auto it_timer = millis();
int session_t;
int session_t_before = 0;
int trial_start_time = 0;
int trial_end_time;
int trial_time;
auto pause_timer = millis();
auto loop_timer = millis();
long experiment_start;
long pause_time = 0;

// - buffers
std::vector<std::vector<int>> tmp_value_buffer;    // [time value], first row is oldest data
std::vector<std::vector<int>> trial_value_buffer;  // [time value]
std::deque<bool> past_10_trials_succ;

// - bools
bool trial_started = false;
bool success = false;
bool crashed = false;
bool stop_session = false;
bool pause_session = false;
bool isr_running = false;

// - hard-coded values
int post_trial_dur = 1000;
int inter_trial_dur = 500;
int buffer_dur = 1000;


// Define STATES
enum State {
  STATE_IDLE,
  STATE_TRIAL_INIT,
  STATE_TRIAL_STARTED,
  STATE_HOLD,
  STATE_SUCCESS,
  STATE_FAILURE,
  STATE_POST_TRIAL,
  STATE_PARAM_UPDATE,
  STATE_INTER_TRIAL,
  STATE_SESSION_END
};

State CURRENT_STATE = STATE_IDLE;
State NEXT_STATE = CURRENT_STATE;


// FONCTIONS DECLARATIONS---------------------------------

void send_message(const string& message);

void sendTrialData2Python(bool done);

void reInitialize();

std::string readSerial(int fd);

void writeSerial(int fd, const std::string &data);

void updateEncoderValue();


// FONCTIONS ---------------------------------

int getTimerDuration(int start) {
  return millis() - start;
}

int getMean(std::vector<int> numbers) {
  int sum = std::accumulate(numbers.begin(), numbers.end(), 0.0);

  int average = sum / numbers.size();
  return average;
}
double getBoolMean(deque<bool> bools) {
  int sum = std::count(bools.begin(), bools.end(), true);
  double average = static_cast<double>(sum) / bools.size();
  return average;
}


void recordCurrentValue() {
    // update trial_buffer that keeps data 1 second before trial initiation until end of trial:
    if (trial_value_buffer.size() >= lenBuffer) {
      sendTrialData2Python(false);
      trial_value_buffer.clear();
      // trial_value_buffer.erase(trial_value_buffer.begin());
    }
    trial_time = session_t - trial_start_time;
    vector<int> values;
    values.push_back(trial_time);
    //using before value, because the state before is what decides to start the trial
    values.push_back(moduleValue_now);
    trial_value_buffer.push_back(values);
    // and keep track of trial peak force
    peak_moduleValue = max(peak_moduleValue, moduleValue_now);
}


void stateMachine() {
  if (pause_session) {
    //%accumulate pause_time and skip state machine
    pause_time += millis() - pause_timer;
    pause_timer = millis();
    return;
  }

  // warn if longer than expected loop delays
  auto loop_time = millis() - loop_timer;
  if (loop_time - pause_time > 100) {
    // fprintf('--- WARNING --- \nlong delay in while loop (%.0f ms)\n', loop_time * 1000);
    send_message("--- WARNING --- long delay in while loop"); // tmp_value_buffer
  }
  loop_timer = millis();


  // experiment time
  session_t_before = session_t;
  session_t = millis() - experiment_start - pause_time;
 
  //TODO
  // drawnow limitrate;  // process callbacks, update figures at 20Hz max
  //% read module force
   moduleValue_before = moduleValue_now;    // store previous value
  if (input_type) {
    //moduleValue_now = analogRead(AnalogIN) * lever_gain;  // update current value
    cout << "Getting module value" << endl;
    moduleValue_now = wiringPiI2CReadReg16(analog_fd, ADS1015_CONVERSION_REG);
    //moduleValue_now = wiringPiI2CRead(analog_fd);
    cout << moduleValue_now << endl;
    if (moduleValue_now < 0) {
        std::cerr << "Error reading from ADS1015." << endl;
    }
  }
  else {
    moduleValue_now = moduleValue_encoder;
  }

  // fill force buffertrial_start_time
  // limit temp buffer size to 'buffer_dur' (last 1s of data)+

  auto condition = [&](const std::vector<int>& row) {
    return session_t - row[0] <= buffer_dur;
  };

  tmp_value_buffer.erase(
      std::remove_if(tmp_value_buffer.begin(), tmp_value_buffer.end(), 
                      [condition](const std::vector<int>& sublist) {
                          return !condition(sublist);
                      }),
      tmp_value_buffer.end()
  );
  

  if (tmp_value_buffer.size() >= lenBuffer) {
    tmp_value_buffer.erase(tmp_value_buffer.begin());
  }
  tmp_value_buffer.push_back({session_t, moduleValue_now});

  // STATE MACHINE

  if (trial_started) {
    recordCurrentValue();

  }

  switch (CURRENT_STATE) {
    // STATE_IDLE
    case STATE_IDLE:
      //cout << "STATE_IDLE" << endl;
      if (session_t > duration * 60 * 1000) {
        send_message("Time Out");
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (num_trials >= MaxTrialNum) {
        send_message("Reached Maximum Number of Trials");
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (stop_session) {
        send_message("Manual Stop");
        NEXT_STATE = STATE_SESSION_END;
      }
      
      else if (moduleValue_now >= init_thresh && moduleValue_before < init_thresh) {
        // checking value before < init_thresh ensures force is increasing i.e. not already high from previous trial
        NEXT_STATE = STATE_TRIAL_INIT;


        //changes from original state machine
        trial_start_time = session_t;

        trial_started = true;
      }
      break;
    //STATE_TRIAL_INIT
    case STATE_TRIAL_INIT:
       //send_message("STATE_TRIAL_INIT");
      cout << "STATE_TRIAL_INIT" << endl;
      // trial initiated
      
      //changes from original state machine
      // trial_start_time = session_t;
      
      // play(init_sound{1});
      trial_started = true;
      num_trials = num_trials + 1;


      // Output one digital pulse for onset of trial
      //TODO
      // app.moto.stim();

      
      // start recording force data (%skip last entry, it will be added below after the "if trial_started" section
      //we only want the values from this point on (because the last second will be given by the temporary buffer)
      if (tmp_value_buffer.size() > 0) {
        trial_value_buffer.clear();
          std::transform(tmp_value_buffer.begin(), tmp_value_buffer.end() - 1, std::back_inserter(trial_value_buffer), [](const std::vector<int>& sublist) { 
          return std::vector<int>{sublist[0] - trial_start_time, sublist[1]};
          }
        );
      }
      
      NEXT_STATE = STATE_TRIAL_STARTED;
      break;
    // STATE_TRIAL_STARTED
    case STATE_TRIAL_STARTED:
      // send_message("STATE_TRIAL_STARTED");
      //cout << "STATE_TRIAL_STARTED" << endl;
      // check if trial time out (give a chance to continue if force > hit_thresh)
      if (trial_time > hit_window * 1000 && moduleValue_now < hit_thresh) {
        send_message("trial_time > hit_window && moduleValue_now < hit_thresh");
        NEXT_STATE = STATE_FAILURE;
      }
      // check if force decreased from peak too much
      else if (moduleValue_now <= (peak_moduleValue - failure_tolerance)) {
        send_message("moduleValue_now <= (peak_moduleValue - failure_tolerance)");
        NEXT_STATE = STATE_FAILURE;
      }
      // check if hit threshold has been reached
      else if (moduleValue_now >= hit_thresh) {
        send_message("moduleValue_now >= hit_thresh");
        hold_timer = millis();
        NEXT_STATE = STATE_HOLD;
      }
      break;
    // STATE_HOLD
    case STATE_HOLD:
      // send_message("STATE_HOLD");
      //cout << "STATE_HOLD" << endl;
      //check if still in reward zone
      if (moduleValue_now < hit_thresh) {
        hold_timer = millis();
        NEXT_STATE = STATE_TRIAL_STARTED;
      } else if (getTimerDuration(hold_timer) >= hold_time) {
        // convert from ms to seconds
        NEXT_STATE = STATE_SUCCESS;
      }
      break;
    // STATE_SUCCESS
    case STATE_SUCCESS:
      trial_hit_thresh = hit_thresh;
      trial_hold_time = hold_time;
      //send_message("STATE_SUCCESS");
      cout << "STATE_SUCCESS" << endl;
      // we have a success! execute only once
      send_message("trial successful! :D");

      //TODO
      // play(reward_sound{1});
      // drawnow;
      success = true;
      trial_end_time = trial_time;
      // past_10_trials_succ = [true, past_10_trials_succ(1:end - 1)];
      if (past_10_trials_succ.size() >= 10) {
        past_10_trials_succ.pop_back();
      }
      past_10_trials_succ.push_front(true);

      // send 1 pellet
      // app.moto.trigger_feeder(1); TODO

      // send 1 digital pulse
      // app.moto.stim(); TODO

      // adapt hit_threshold
      if (adapt_hit_thresh) {
        // if success rate 70% or more, increase hit_thresh by 1g
        if (getBoolMean(past_10_trials_succ) >= 0.7) {
          hit_thresh = min(hit_thresh_max, hit_thresh + 1);
        }
      }
      // adapt hold_time
      if (adapt_hold_time) {
        // if success rate 70% or more, increase hit_thresh by 10 ms
        if (getBoolMean(past_10_trials_succ) >= 0.7) {
          hold_time = min(hold_time_max, hold_time + 10);
        }
      }

      //update stats & update gui
      num_rewards++;
      num_pellets++;

      NEXT_STATE = STATE_POST_TRIAL;
      break;
    // STATE_FAILURE
    case STATE_FAILURE:
      //send_message("STATE_FAILURE");
      cout << "STATE_FAILURE" << endl;
      trial_hit_thresh = hit_thresh;
      trial_hold_time = hold_time;
      // trial failed. execute only once
      send_message("trial failed :(");
      //TODO
      // play(failure_sound{1});

      if (past_10_trials_succ.size() >= 10) {
        past_10_trials_succ.pop_back();
      }
      past_10_trials_succ.push_front(false);

      success = false;
      trial_end_time = trial_time;

      // adapt hit_threshold
      if (adapt_hit_thresh) {
        // if success rate 40% or less, decrease hit_thresh by 1g
        if (getBoolMean(past_10_trials_succ) <= 0.4) {
          hit_thresh = max(hit_thresh_min, hit_thresh - 1);
        }
      }

      // adapt hold_time
      if (adapt_hold_time) {
        // if success rate 40% or less, decrease hold_time by 10 ms
        if (getBoolMean(past_10_trials_succ) <= 0.4) {
          hold_time = max(hold_time_min, hold_time - 10);
        }
      }
      
      NEXT_STATE = STATE_POST_TRIAL;
      break;
    // STATE_POST_TRIAL
    case STATE_POST_TRIAL:
      // send_message("STATE_POST_TRIAL");
      //cout << "STATE_POST_TRIAL" << endl;
      // wait to accumulate a bit of post_trial data
      if (trial_time - trial_end_time >= post_trial_dur) {
        NEXT_STATE = STATE_PARAM_UPDATE;
      }
      break;
    // STATE_PARAM_UPDATE
    case STATE_PARAM_UPDATE:
      send_message("STATE_PARAM_UPDATE");
      // post trial processing, execute only once.

      sendTrialData2Python(true);
      trial_started = false;
      trial_value_buffer.clear();
      peak_moduleValue = 0;
      success = false;

      it_timer = millis();
      NEXT_STATE = STATE_INTER_TRIAL;
      break;
    // STATE_INTER_TRIAL
    case STATE_INTER_TRIAL:
      // send_message("STATE_INTER_TRIAL");
      // wait a short period of time between trials
      if (getTimerDuration(it_timer) >= inter_trial_dur) {
        it_timer = millis();
        NEXT_STATE = STATE_IDLE;
      }

      break;
    case STATE_SESSION_END:
      send_message("done");
      send_message("STATE_SESSION_END");
      
      // exit while loop
      serialCommand = "e";
      reInitialize();
      break;

    default:
      send_message("default");
      send_message("error in state machine!");

      // exit while loop
      serialCommand = "e";
      break;
  }

  CURRENT_STATE = NEXT_STATE;
}

bool attached = false;
void enableInterrupt(int pin) {
  std::cout << "Enabling on pin " << pin << std::endl;
  if (wiringPiISR(pin, INT_EDGE_BOTH, &updateEncoderValue)  < 0) {
    cout << "Failed to enable interrupt" << endl;
  }
  //std::cout << "Interrupts enabled on pin " << pin << std::endl;
}

void disableInterrupt(int pin) {
  std::cout << "Disabling on pin " << pin << std::endl;
  if (wiringPiISR(pin, INT_EDGE_BOTH, NULL) < 0) {
    cout << "Failed to disable interrupt" << endl;
  }
   // Detach ISR by attaching NULL
  //std::cout << "Interrupts disabled on pin " << pin << std::endl;

}

void enableInterrupts() {
  if (!attached) {
    while (isr_running) {
      usleep(10);
    }
    enableInterrupt(pinA);
    enableInterrupt(pinB);
    attached = true;
  }
}

void disableInterrupts() {
  if (attached) {
    //stringstream command;
    //command << "/usr/local/bin/gpio edge " << pinA << " none";
    //string commandStr = command.str();
    //system(commandStr.c_str());
    //stringstream command2;
    //command2 << "/usr/local/bin/gpio edge " << pinB << " none";
    //string commandStr2 = command2.str();
    //system(commandStr2.c_str());
    
    while (isr_running) {
      usleep(10);
    }
    disableInterrupt(pinA);
    disableInterrupt(pinB);
    attached = false;
  }
  int i = 0;
  i ++;
}

bool sending = false;
void sendTrialData2Python(bool done) {
  //serialFlush(serialFd);
  sending = true;
  string dataDelimiter = "trialData";
  writeSerial(serialFd, dataDelimiter);
  for (size_t i = 0; i < trial_value_buffer.size(); i++) {
    writeSerial(serialFd, to_string(trial_value_buffer[i][0]));
    writeSerial(serialFd, "/");
    writeSerial(serialFd, to_string(trial_value_buffer[i][1]));
    writeSerial(serialFd, ";");
  }
  writeSerial(serialFd, "nt");
  writeSerial(serialFd, to_string(num_trials));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(trial_start_time));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(init_thresh));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(hold_time));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(hit_thresh));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(trial_end_time));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(success));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(peak_moduleValue));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(num_pellets));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(num_rewards));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(trial_hold_time));
  writeSerial(serialFd, ";");
  writeSerial(serialFd, to_string(trial_hit_thresh));
  if (!done) {
    writeSerial(serialFd, "partialEnd");
  }
  writeSerial(serialFd, "fin");
  writeSerial(serialFd, "\r\n");

  
  //serialFlush(serialFd);
  sending = false;
  // code de fin d'envoi de données
  
}

long h = 0;

void send_message(const string& message) {
  //serialFlush(serialFd);
  if (h % 1 == 0) {
    string messageDelimiter = "message";
    writeSerial(serialFd, messageDelimiter);
    writeSerial(serialFd, message);
    writeSerial(serialFd, ";");
    writeSerial(serialFd, "fin");
    writeSerial(serialFd, "\r\n");

   
    // code de fin d'envoi de données
  }
  h += 1;
  //serialFlush(serialFd);
}

void updateEncoderValue() {
  isr_running = true;
  int encoderA = digitalRead(pinA);
  int encoderB = digitalRead(pinB);

  if (encoderA != previousA && previousA != -1) {
    if (encoderB != encoderA) {
      encoderPos ++;
    }
    else {
      encoderPos --;
    }
  }
  if (encoderB != previousB && previousB != -1) {
    if (encoderB == encoderA) {
      encoderPos ++;
    }
    else {
      if (encoderPos > 0) {
        encoderPos --;
      }
     
    }
  }
  
  previousA = encoderA;
  previousB = encoderB;
  
  int angle = ((encoderPos / 4)); //%360 abs
  previous_angle = angle;
  moduleValue_encoder = angle;
  isr_running = false;
}

void feed() {
  num_pellets ++;
}

void experimentOn() {
  int posIndice;
  reInitialize();
  // Devrait aller dans 'case i' :
  posIndice = serialCommand.find('b');
  initTrial = stof(serialCommand.substr(1, posIndice));
  baselineTrial = stof(serialCommand.substr(posIndice + 1));
  while (serialCommand[0] != 'w' && serialCommand[0] != 'e') {
    if (serialCommand[0] == 'f') {
      feed();
      serialCommand = "s";
    }
    else if (serialCommand[0] == 'c') {
      if (!pause_session) {
        pause_timer = millis();
      }
      pause_session = !pause_session;
      serialCommand = "s";
    }
    else if (serialCommand[0] == 'a'){
      send_message("received stop");
      stop_session = true;
    }
    serialCommand = readSerial(serialFd);
    stateMachine();
  }
}

std::vector<std::string> split_string(const std::string& input_string, char delimiter) {
    std::vector<std::string> result;
    std::istringstream iss(input_string);
    std::string token;
    while (std::getline(iss, token, delimiter)) {
        result.push_back(token);
    }
    return result;
}
bool stringToBool(const std::string& str) {
    std::string s = str;

    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::tolower(c); });
    
    if (s == "true" || s == "1") {
        return true;
    } else if (s == "false" || s == "0") {
        return false;
    } 
    else {
      return false;
    }
}

void reInitialize() {
  //serialFlush(serialFd);
  CURRENT_STATE = STATE_IDLE;
  NEXT_STATE = CURRENT_STATE; 
  //tmp_value_buffer.clear();    // [time value], first row is oldest data
  trial_value_buffer.clear();  // [time value]
  past_10_trials_succ.clear();
  num_pellets = 0;
  num_rewards = 0;
  num_trials = 0;
  trial_started = false;
  success = false;
  crashed = false;
  stop_session = false;
  pause_session = false;
  loop_timer = millis();
  experiment_start = millis();
  pause_time = 0;
}


// INITIALISATION-------------------------------

// Function to read from serial
std::string readSerial(int fd) {
    //char buffer[256];
    //int n = read(fd, buffer, sizeof(buffer) - 1);
    //if (n < 0) {
        //std::cerr << "Failed to read from serial port" << std::endl;
        //return "";
    //} else {
        //buffer[n] = '\0';
        //return std::string(buffer);
    //}
    string buffer;
    int bytes_received = serialDataAvail(serialFd);
    if (bytes_received > 0) {
      while(serialDataAvail(serialFd)) {
        buffer += serialGetchar(serialFd);
      }
    }
    return buffer;
}

// Function to write to serial
void writeSerial(int fd, const std::string &data) {
    serialPuts(fd, data.c_str());
}
bool empty_stated = false;

int main() {
	// Initialize wiringPi library and serial port
  //SETUP
	if (wiringPiSetup() == -1) {
        std::cerr << "WiringPi setup failed" << std::endl;
        return 1;
  }
  analog_fd = wiringPiI2CSetup(ADS1015_I2C_ADDR);
  
  if (analog_fd == -1) {
    std::cerr << "Failed to initalize ADS1015 I2C connection." << std::endl;
    return 1;
  }
  
  uint16_t config = 0x83C3; // +/- 2.048V range, continuous conversion mode
  
  wiringPiI2CWriteReg16(analog_fd, ADS1015_CONFIG_REG, config);
  
  
  //serialFd = serialOpen("/dev/ttyAMA0", 115200); //baud rate
  serialFd = serialOpen("/dev/pts/3", 115200); //baud rate
  if (serialFd == -1) {
        std::cout << "Failed to open serial port: " << std::endl;
        return 1;
    }
   // Set pin modes
  //pinMode(AnalogIN, INPUT);
  pinMode(pinA, INPUT);// Internal pull-up resistor for switch A
  pinMode(pinB, INPUT);// Internal pull-up resistor for switch B
   //pinMode(OUTPUT_PIN, OUTPUT);
   
	
  //pinMode(AnalogIN, INPUT);

  startArduinoProg = millis();  // début programme
  loop_timer = millis();
  experiment_start = millis();
  

  //LOOP
  while(true) {
    //std::string serialCommand = readSerial(serialFd);
    serialCommand = "";
    while (serialDataAvail(serialFd)) {
      char ch = serialGetchar(serialFd);
      serialCommand += ch;
    }
    
    //std::cout << serialCommand << std::endl;
    if (!serialCommand.empty()) {
            empty_stated = true;
            cout << " Received: " << serialCommand << endl;
            switch (serialCommand[0]) {  // Première lettre de la commande
              case 'w':  // boucle defaut standby
                break;
              case 'p':  // Initialisation : transmission des paramètres de la tâche à partir de Python
                {
                send_message("received parameters");
                string variables;
                variables = serialCommand.substr(1).c_str();
                serialCommand = "";
                std::vector<std::string> parts = split_string(variables, ';');
                initTrial = stof(parts[0]);
                init_thresh = stoi(parts[0]);
                baselineTrial = stof(parts[1]);
                duration = stof(parts[2]);
                hit_window = stof(parts[3]);
                hit_thresh =stof(parts[4]);
                adapt_hit_thresh = stringToBool(parts[5]);
                hit_thresh_min = stof(parts[6]);
                hit_thresh_max = stof(parts[7]);
                lever_gain =stof(parts[8]);
                failure_tolerance =stof(parts[9]);
                MaxTrialNum =stof(parts[10]);
                hold_time =stof(parts[11]) * 1000;
                adapt_hold_time= stringToBool(parts[12]);
                hold_time_min = stof(parts[13]) * 1000;
                hold_time_max = stof(parts[14]) * 1000;
                input_type = stringToBool(parts[17]);
                
                if(input_type) {
                  //disableInterrupts();
                  enableInterrupts();
                }
                else {
                  enableInterrupts();
                }
              }
              break;
              case 's':  // Start
                send_message("received start");
                experimentOn();
                break;
              case 'a':
                send_message("received stop");
                stop_session = true;
                break;
            }
        }
	}
	  
}
