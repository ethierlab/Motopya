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
using namespace std;

// DECLARATION VARIABLES------------

//Settings
int AnalogIN = A0;
String serialCommand = "wait";


// code controllers
const int lenBuffer = 255;

//state machine variables

float initTrial;
float baselineTrial;
unsigned long startArduinoProg;
unsigned long startSession;
unsigned long startTrial;
unsigned long bufferTimeFreq;
unsigned long stopTrial;
unsigned long LastTime;  // le dernier temps du buffer data

auto loop_timer = millis();
long experiment_start;
int pause_time = 0;

// - input Parameters
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
int peak_moduleValue = 0;

// - timers
auto hold_timer = millis();
auto it_timer = millis();
int session_t;
int session_t_before = 0;
int trial_start_time = 0;
int trial_end_time;
int trial_time;

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
    //%accumulate pause_time (in app code) and skip state machine
    delay(1000);
    // continue;
    return;
  }

  // warn if longer than expected loop delays
  auto loop_time = millis() - loop_timer;
  if (loop_time > 0.1) {
    // fprintf('--- WARNING --- \nlong delay in while loop (%.0f ms)\n', loop_time * 1000);
    send("--- WARNING --- \nlong delay in while loop"); // tmp_value_buffer
  }
  loop_timer = millis();
  // experiment time
  session_t_before = session_t;
  session_t = millis() - experiment_start - pause_time;
  // app.TimeelapsedCounterLabel.Text = datestr((session_t) / 86400, 'HH:MM:SS');
  // drawnow limitrate;  // process callbacks, update figures at 20Hz max
  //% read module force
  moduleValue_before = moduleValue_now;    // store previous value
  // moduleValue_now = (app.moto.read_Pull() - app.moto.baseline) * app.lever_gain; % update current value
  moduleValue_now = analogRead(AnalogIN) * lever_gain;  // update current value
  // fill force buffertrial_start_time
  // limit temp buffer size to 'buffer_dur' (last 1s of data)+
  // tmp_value_buffer = [tmp_value_buffer(session_t - tmp_value_buffer(:, 1) <= app.buffer_dur, :); session_t moduleValue_now];

  auto condition = [&](const std::vector<int>& row) {
    return session_t - row[0] <= buffer_dur;
  };
  std::vector<std::vector<int>> filtered_rows;
  std::copy_if(tmp_value_buffer.begin(), tmp_value_buffer.end(), std::back_inserter(filtered_rows), condition);
  if (filtered_rows.size() >= lenBuffer) {
    filtered_rows.erase(filtered_rows.begin());
  }
  filtered_rows.push_back({session_t, moduleValue_now});
  tmp_value_buffer = filtered_rows;

  // STATE MACHINE
  switch (CURRENT_STATE) {
    // STATE_IDLE
    case STATE_IDLE:
      // send("STATE_IDLE");
      if (session_t > duration * 60 * 1000) {
        send(String('Time Out'));
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (num_trials >= MaxTrialNum) {
        // send("Reached Maximum Number of Trials");
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (stop_session) {
        send("Manual Stop");
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
      send("STATE_TRIAL_INIT");
      // trial initiated
      
      //changes from original state machine
      // trial_start_time = session_t;
      
      // send("Trial initiated... ");
      // play(init_sound{1});
      trial_started = true;
      num_trials = num_trials + 1;

      //clear force plot
      //TO-DO: send data to be drawn in plot in python
      // set(app.force_line, 'Visible','off');
      // update_lines_in_fig(app);

      // update GUI counters
      //TO-DO: send data to python
      // app.NumTrialsCounterLabel.Text = num2str(num_trials);

      // Output one digital pulse for onset of trial
      //TODO
      // app.moto.stim();

      
      // trial_value_buffer = [tmp_value_buffer(1:end - 1, 1) - trial_start_time, tmp_value_buffer(1:end - 1, 2)];
      
      // start recording force data (%skip last entry, it will be added below after the "if trial_started" section
      
      //we only want the values from this point on (because the last second will be given by the temporary buffer)
      // trial_value_buffer.clear();
      std::transform(tmp_value_buffer.begin(), tmp_value_buffer.end() - 1, std::back_inserter(trial_value_buffer), [](const std::vector<int>& sublist) { 
        return std::vector<int>{sublist[0] - trial_start_time, sublist[1]};
        }
      );
      //putting the first value (at 0);
    
      NEXT_STATE = STATE_TRIAL_STARTED;
      break;
    // STATE_TRIAL_STARTED
    case STATE_TRIAL_STARTED:
      // send("STATE_TRIAL_STARTED");
      // check if trial time out (give a chance to continue if force > hit_thresh)
      if (trial_time > hit_window * 1000 && moduleValue_now < hit_thresh) {
        send("trial_time > hit_window && moduleValue_now < hit_thresh");
        NEXT_STATE = STATE_FAILURE;
      }
      // check if force decreased from peak too much
      else if (moduleValue_now <= (peak_moduleValue - failure_tolerance)) {
        send("moduleValue_now <= (peak_moduleValue - failure_tolerance)");
        // send(String(peak_moduleValue));
        NEXT_STATE = STATE_FAILURE;
      }
      // check if hit threshold has been reached
      else if (moduleValue_now >= hit_thresh) {
        digitalWrite(13, HIGH);
        send("moduleValue_now >= hit_thresh");
        hold_timer = millis();
        NEXT_STATE = STATE_HOLD;
      }
      break;
    // STATE_HOLD
    case STATE_HOLD:
      send("STATE_HOLD");
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
      send("STATE_SUCCESS");
      // we have a success! execute only once
      // fprintf('trial successful! :D\n');

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
      //TODO
      // app.PelletsdeliveredCounterLabel.Text = sprintf('%d (%.3f g)', sum(app.num_pellets) + app.man_pellets, (sum(app.num_pellets) + app.man_pellets) * 0.045); //each pellet 45mg
      // app.NumRewardsCounterLabel.Text = num2str(num_rewards);

      NEXT_STATE = STATE_POST_TRIAL;
      break;
    // STATE_FAILURE
    case STATE_FAILURE:
      send("STATE_FAILURE");
      trial_hit_thresh = hit_thresh;
      trial_hold_time = hold_time;
      // trial failed. execute only once
      // fprintf('trial failed :(\n');
      //TODO
      // play(failure_sound{1});

      // past_10_trials_succ = [false, past_10_trials_succ(1:end - 1)];

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
      // send("STATE_POST_TRIAL");
      // wait to accumulate a bit of post_trial data
      if (trial_time - trial_end_time >= post_trial_dur) {
        NEXT_STATE = STATE_PARAM_UPDATE;
      }
      break;
    // STATE_PARAM_UPDATE
    case STATE_PARAM_UPDATE:
      send("STATE_PARAM_UPDATE");
      // post trial processing, execute only once.

      // update force plot with new trial data

      //TODO

      //should include trial_value_buffer data, first and second column, and a maximum (maybe), number of trials, trial start time, initial threshold, hit threshold, trial_value_buffer,
      //hold  time, trial end time, success, peak_moduleValue
      sendTrialData2Python(true);
      trial_started = false;
      // set(app.force_line, 'XData', trial_value_buffer(:, 1), ...
      //     'YData', trial_value_buffer(:, 2),'Visible','on');
      // ymax = max(app.hit_thresh.Value, peak_moduleValue) * 1.25;
      // ylim(app.moduleValueAxes, [-5 ymax]);

      // // update trial_table
      // trial_table(num_trials, :) = {trial_start_time, app.init_thresh.Value, app.hit_thresh.Value, trial_value_buffer, ...
      //     app.hold_time.Value, trial_end_time, success, peak_moduleValue};

      // reset data buffer
      trial_value_buffer.clear();
      peak_moduleValue = 0;
      success = false;

      it_timer = millis();
      NEXT_STATE = STATE_INTER_TRIAL;
      break;
    // STATE_INTER_TRIAL
    case STATE_INTER_TRIAL:
      // send("STATE_INTER_TRIAL");
      // wait a short period of time between trials
      if (getTimerDuration(it_timer) >= inter_trial_dur) {
        it_timer = millis();
        NEXT_STATE = STATE_IDLE;
      }

      break;
    case STATE_SESSION_END:
      send("done");
      send("STATE_SESSION_END");
      //TO-DO
      // finish_up(trial_table,session_t, num_trials, num_rewards, app, crashed);
      
      // exit while loop
      serialCommand = "e";
      break;

    default:
      send("default");
      send("error in state machine!");
      //TO-DO
      // finish_up(trial_table,session_t, num_trials, num_rewards, app, crashed);
      // exit while loop
      serialCommand = "e";
      break;
  }

  if (trial_started) {
    recordCurrentValue();
  }

  CURRENT_STATE = NEXT_STATE;
}

// void finish_up(trial_table, session_t, num_trials, num_rewards, app, crashed) {
// //   //TO-DO
    // send('Session Ended');
    
//     //reset the gui buttons
//     // reset_buttons(app);

//     // trial_table = trial_table(1:num_trials, :);  
//     // trial_table.Properties.CustomProperties.num_trials  = num_trials;
//     // trial_table.Properties.CustomProperties.num_rewards = num_rewards;
//     // trial_table.Properties.CustomProperties.rat_id      = app.rat_id.Value;
//     // display_results(session_t, num_trials, num_rewards, app.num_pellets, app.man_pellets);
//     // save_results(app, trial_table, crashed);
// }

  // void save_results(app, trial_table, bool crashed) {
        // if (crashed) {
        //       SaveButton = questdlg(sprintf('RatPull lever_pull_behavior Crashed!\n Save results?'), 'Sorry about that...', 'Yes','No','Yes');
        //}
        //else {
        //SaveButton = questdlg(sprintf('End of behavioral session\nSave results?'), 'End of Session', 'Yes','No','Yes');
        //}
        
    //     if (SaveButton.compare('Yes'))
    //         dir_exist = isfolder(fullfile(app.params.save_dir,app.rat_id.Value));
    //         if ~dir_exist
    //             fprintf('Creating new folder for animal %s\n',app.rat_id.Value);
    //             dir_exist = mkdir(app.params.save_dir,app.rat_id.Value);
    //             if ~dir_exist
    //                 disp('Failed to create new folder in specifiec location');
    //             end
    //         end
        
    //         if dir_exist
    //             ttfname = [app.rat_id.Value,'_RatPull_trial_table_',datestr(datetime('now'),'yyyymmdd_HHMMSS'),'.mat'];
    //             pfname  = [app.rat_id.Value,'_RatPull_params_',datestr(datetime('now'),'yyyymmdd_HHMMSS'),'.mat'];

    //             params = app.params;
    //             save(fullfile(app.params.save_dir, app.rat_id.Value, ttfname), 'trial_table');
    //             save(fullfile(app.params.save_dir, app.rat_id.Value, pfname), '-Struct', 'params');

    //             disp('behavior stats and parameters saved successfully');
        
    //             update_global_stats(app,trial_table);
    //         else
    //             disp('behavior stats and parameters not saved');
    //         end
        
    //     end
  // }

void sendTrialData2Python(bool done) {
  //should include trial_value_buffer data, first and second column, and a maximum (maybe), number of trials, trial start time, initial threshold, hit threshold, trial_value_buffer,
  //hold  time, trial end time, success, peak_moduleValue
  // envoie les données de l'essai : sous la forme ##;##;##;...fin et
  // la forme temps correspondant en seconde ligne
  unsigned long timeStamp;
  unsigned long StartTime;
  SerialUSB.flush();
  // Data
  String dataDelimiter = "trialData";
  SerialUSB.print(dataDelimiter);
  for (int i = 0; i < trial_value_buffer.size(); i++) {
    SerialUSB.print(trial_value_buffer[i][0]);
    SerialUSB.print('/');
    SerialUSB.print(trial_value_buffer[i][1]);
    SerialUSB.print(';');
  }

  SerialUSB.print("nt");
  SerialUSB.print(String(num_trials));
  SerialUSB.print(";");
  SerialUSB.print(String(trial_start_time));
  SerialUSB.print(";");
  SerialUSB.print(String(init_thresh));
  SerialUSB.print(";");
  SerialUSB.print(String(hold_time));
  SerialUSB.print(";");
  SerialUSB.print(String(hit_thresh));
  SerialUSB.print(";");
  SerialUSB.print(String(trial_end_time));
  SerialUSB.print(";");
  SerialUSB.print(String(success));
  SerialUSB.print(";");
  SerialUSB.print(String(peak_moduleValue));
  SerialUSB.print(";");
  SerialUSB.print(String(num_pellets));
  SerialUSB.print(";");
  SerialUSB.print(String(num_rewards));
  SerialUSB.print(";");
  SerialUSB.print(String(trial_hold_time));
  SerialUSB.print(";");
  SerialUSB.print(String(trial_hit_thresh));

  if (!done) {
    SerialUSB.print("partialEnd");
  }

  SerialUSB.println("fin");
  // code de fin d'envoi de données
}

void send(String error) {
  unsigned long timeStamp;
  unsigned long StartTime;
  SerialUSB.flush();
  // Error
  String messageDelimiter = "message";
  SerialUSB.print(messageDelimiter);
  SerialUSB.print(error);
  SerialUSB.print(';');
  SerialUSB.println("fin");
  // code de fin d'envoi de données
}

void sendSpec(String error) {
  unsigned long timeStamp;
  unsigned long StartTime;
  SerialUSB.flush();
  // Error
  String messageDelimiter = "yumm";
  SerialUSB.print(messageDelimiter);
  SerialUSB.print(error);
  SerialUSB.print(';');
  SerialUSB.println("fin");
  // code de fin d'envoi de données
}

void feed() {
  num_pellets ++;
}

void experimentOn() {

  int posIndice;
  reInitialize();
  // Devrait aller dans 'case i' :
  posIndice = serialCommand.indexOf('b');
  initTrial = serialCommand.substring(1, posIndice).toFloat();
  baselineTrial = serialCommand.substring(posIndice + 1).toFloat();
  while (serialCommand.charAt(0) != 'w' && serialCommand.charAt(0) != 'e') {
    if (serialCommand.charAt(0) == 'f') {
      feed();
      serialCommand = "s";
    }
    delay(5);
    if (SerialUSB.available() > 0) {
      serialCommand = SerialUSB.readStringUntil('\r');
    }
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
    // Convert the string to lowercase for case-insensitive comparison
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::tolower(c); });
    
    if (s == "true" || s == "1") {
        return true;
    } else if (s == "false" || s == "0") {
        return false;
    } 
    // else {
    //     throw std::invalid_argument("Invalid string for conversion to bool");
    // }
}

void reInitialize() {
  CURRENT_STATE = STATE_IDLE;
  NEXT_STATE = CURRENT_STATE; 
  loop_timer = millis();
  experiment_start = millis();
}


// INITIALISATION-------------------------------
void setup() {
  // put your setup code here, to run once:
  pinMode(AnalogIN, INPUT);
  pinMode(13, OUTPUT);
  pinMode(12, OUTPUT);
  // pinMode(10, OUTPUT);
  // pinMode(9,OUTPUT);
  SerialUSB.begin(115200);      // baud rate
  startArduinoProg = millis();  // début programme
  loop_timer = millis();
  experiment_start = millis();
  // trial_value_buffer.resize(255, std::vector<int>(2));
}


void loop() {
  if (SerialUSB.available() > 0) {
    serialCommand = SerialUSB.readStringUntil('\r');
  }
  send("here");

  switch (serialCommand.charAt(0)) {  // Première lettre de la commande
    case 'w':  // boucle defaut standby
      break;
    case 'p':  // Initialisation : transmission des paramètres de la tâche à partir de Python
      {
      send("received parameters");
      string variables;
      variables = serialCommand.substring(1).c_str();
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

      }
      break;
    case 's':  // Start
      send("received start");
      experimentOn();
      break;
    case 'a':
      send("received stop");
      stop_session = true;
      break;
  }
}
