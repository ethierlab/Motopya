// #include <CircularBuffer.h>
#pragma GCC enable ("-fexceptions")
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wpsabi"

// #pragma GCC diagnostic pop

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

// code controllers
bool flash_enabled = false;

const int lenBuffer = 1000;
std::deque<int> dataBuffer(lenBuffer, 0);
// CircularBuffer<int, lenBuffer> dataBuffer;
int AnalogIN = A0;
int leverVal;
int DL = 10;           // sampling freq
int DL_Sampling = 10;  // buffer freq : every x ms
float valMoyenne;
float initTrial;
float baselineTrial;
int aveOnLast = 10;
float ave = 0.0;
unsigned long startArduinoProg;
unsigned long startSession;
unsigned long startTrial;
unsigned long bufferTimeFreq;
unsigned long stopTrial;
unsigned long LastTime;  // le dernier temps du buffer data
int compteur = 0;
String serialCommand = "wait";
bool sendData = false;

auto loop_timer = millis();
long experiment_start;
double pause_time = 0;
//Input Parameters
int num_rewards = 0;
int num_trials = 0;
int moduleValue_now = 0;
int peak_moduleValue = 0;
auto hold_timer = millis();
auto it_timer = millis();
std::vector<std::vector<double>> tmp_value_buffer;    // [time value], first row is oldest data
std::vector<std::vector<double>> trial_value_buffer;  // [time value]
double duration;
int MaxTrialNum = 10;
double hold_time_min;
double hit_thresh_min;

//Initial Parameters
int num_pellets = 0;
std::deque<bool> past_10_trials_succ;


int init_thresh = 0;
double session_t;


int moduleValue_before;

bool trial_started = false;
unsigned long trial_start_time = 0;
unsigned long trial_end_time;
unsigned long trial_time;
bool success = false;
bool crashed = false;  // Assuming this variable is declared elsewhere
int duration_minutes;  // Assuming app.duration.Value is in minutes
int max_trial_num;
bool stop_session;
bool pause_session;
int hit_thresh;
int hit_window;
double failure_tolerance = 100;
double hold_time;
double hit_thresh_max;
double hold_time_max;
bool adapt_hit_thresh;
bool adapt_hold_time;
bool adapt_drop_tolerance;
int post_trial_dur;
int inter_trial_dur;
double buffer_dur = 1000;


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

double timePointToDouble(const std::chrono::time_point<std::chrono::high_resolution_clock>& tp) {
  auto duration = tp.time_since_epoch();
    
  return std::chrono::duration_cast<std::chrono::duration<double>>(duration).count();
}

float timePointsToDouble(const std::chrono::time_point<std::chrono::high_resolution_clock>& start, const std::chrono::time_point<std::chrono::high_resolution_clock>& end) {
  auto duration = end - start;
  float double_duration = std::chrono::duration_cast<std::chrono::duration<double>>(duration).count();
  return double_duration;
}

double getTimerDuration(double start) {
  return millis() - start;
}

double getMean(std::vector<double> numbers) {
  double sum = std::accumulate(numbers.begin(), numbers.end(), 0.0);

  double average = sum / numbers.size();
  return average;
}
double getBoolMean(deque<bool> bools) {
  double sum = std::accumulate(bools.begin(), bools.end(), 0.0);

  double average = sum / bools.size();
  send("average");
  send(String(average));
  return average;
}

void flash(int number) {
  if (flash_enabled) {
    if (number == 0) {
      digitalWrite(12, LOW);
      digitalWrite(13, HIGH);
      delay(3000);
      digitalWrite(13, LOW);
      digitalWrite(12, HIGH);
      delay(3000);
      digitalWrite(13, LOW);
      digitalWrite(12, LOW);
    }
    else if (number < 0) {
      fastflash(5);
      digitalWrite(12, LOW);
      digitalWrite(13, HIGH);
      delay(3000);
      digitalWrite(13, LOW);
      digitalWrite(12, HIGH);
      delay(3000);
      digitalWrite(13, LOW);
      digitalWrite(12, LOW);
      fastflash(5);
    }
    int time = 350;
    for (int i = 0; i < number; i++) {
      digitalWrite(12, LOW);
      digitalWrite(13, HIGH);
      delay(time);
      digitalWrite(13, LOW);
      digitalWrite(12, HIGH);
      delay(time);
      digitalWrite(13, LOW);
      digitalWrite(12, LOW);
    }
    delay(500);
  }
  
}
void fastflash(int number) {
  if (flash_enabled) {
    int time = 100;
    for (int i = 0; i < number; i++) {
      digitalWrite(12, LOW);
      digitalWrite(13, HIGH);
      delay(time);
      digitalWrite(13, LOW);
      digitalWrite(12, HIGH);
      delay(time);
      digitalWrite(13, LOW);
      digitalWrite(12, LOW);
    }
    delay(500);
  }
  
}

void flash2Decimal(int number) {
  if (flash_enabled) {
    int time = 300;
    int tens = number / 10;
    int ones = number - (tens * 10);
    for (int i = 0; i < tens; i++) {
      digitalWrite(12, HIGH);
      delay(time);
      digitalWrite(12, LOW);
      delay(time);
    }
    for (int i = 0; i < ones; i++) {
      digitalWrite(13, HIGH);
      delay(time);
      digitalWrite(13, LOW);
      delay(time);
    }
    delay(500);
  }
  
}

void flashfloat2Decimal(float number) {
  int time = 300;
  int hundreds = number / 100;
  int tens = (number - (hundreds * 100)) / 10;
  int ones = number - (tens * 10);
  for (int i = 0; i < hundreds; i++) {
    digitalWrite(12, LOW);
    digitalWrite(13, HIGH);
    delay(time);
    digitalWrite(13, LOW);
    digitalWrite(12, HIGH);
    delay(time);
    digitalWrite(13, LOW);
    digitalWrite(12, LOW);
  }
  for (int i = 0; i < tens; i++) {
    digitalWrite(12, HIGH);
    delay(time);
    digitalWrite(12, LOW);
    delay(time);
  }
  for (int i = 0; i < ones; i++) {
    digitalWrite(13, HIGH);
    delay(time);
    digitalWrite(13, LOW);
    delay(time);
  }
  delay(500);
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
    // send("--- WARNING --- \nlong delay in while loop");
  }
  loop_timer = millis();

  // experiment time
  session_t = millis() - experiment_start - pause_time;
  // app.TimeelapsedCounterLabel.Text = datestr((session_t) / 86400, 'HH:MM:SS');
  // drawnow limitrate;  // process callbacks, update figures at 20Hz max

  //% read module force
  moduleValue_before = moduleValue_now;    // store previous value
  moduleValue_now = analogRead(AnalogIN);  // update current value

  // fill force buffertrial_start_time
  // limit temp buffer size to 'buffer_dur' (last 1s of data)+
  // tmp_value_buffer = [tmp_value_buffer(session_t - tmp_value_buffer(:, 1) <= app.buffer_dur, :); session_t moduleValue_now];

  auto condition = [&](const std::vector<double>& row) {
    return session_t - row[0] <= buffer_dur;
  };

  std::vector<std::vector<double>> filtered_rows;
  std::copy_if(tmp_value_buffer.begin(), tmp_value_buffer.end(), std::back_inserter(filtered_rows), condition);
  filtered_rows.push_back({session_t, moduleValue_now});
  tmp_value_buffer = filtered_rows;


  if (trial_started) {
    // update trial_buffer that keeps data 1 second before trial initiation until end of trial:
    sendSpec("trial started");
    sendSpec(String(trial_time));
    trial_time = session_t - trial_start_time;
    send(String(session_t));
    send(String(trial_start_time));
    vector<double> values;
    values.push_back(trial_time);
    values.push_back(moduleValue_now);
    trial_value_buffer.push_back(values);

    // and keep track of trial peak force
    peak_moduleValue = max(peak_moduleValue, moduleValue_now);
  }
  // STATE MACHINE
  switch (CURRENT_STATE) {
    // STATE_IDLE
    case STATE_IDLE:
      send("STATE_IDLE");
      flash(6);
      if (session_t > duration * 60 * 1000) {
        flash(3);
        send(String('Time Out'));
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (num_trials >= MaxTrialNum) {
        flash(4);
        send("Reached Maximum Number of Trials");
        NEXT_STATE = STATE_SESSION_END;
      }

      else if (stop_session) {
        flash(5);
        send("Manual Stop");
        NEXT_STATE = STATE_SESSION_END;
      }

      else {
        // check for trial initiation
        fastflash(4);
        if (moduleValue_now >= init_thresh && moduleValue_before < init_thresh) {
          fastflash(8);
          // checking value before < init_thresh ensures force is increasing i.e. not already high from previous trial
          NEXT_STATE = STATE_TRIAL_INIT;
        }
      }
      break;
    //STATE_TRIAL_INIT
    case STATE_TRIAL_INIT:
      send("STATE_TRIAL_INIT");
      flash(8);
      // trial initiated
      trial_start_time = session_t;
      send("Trial initiated... ");
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
      std::transform(tmp_value_buffer.begin(), tmp_value_buffer.end() - 1, std::back_inserter(trial_value_buffer), [](std::vector<double> sublist) { 
        vector<double> sublist2;
        sublist2.push_back(sublist[0] - trial_start_time);
        sublist2.push_back(sublist[1]);
        // sublist[0] -= trial_start_time; 
        return sublist2; 
        });

      for (int i = 0; i < trial_value_buffer.size(); i++) {
        sendSpec("trial from tmp with subtraction");
        sendSpec(String(trial_value_buffer[i][0]));
        sendSpec(String(trial_value_buffer[i][1]));
      }
    
      NEXT_STATE = STATE_TRIAL_STARTED;
      fastflash(25);
      break;
    // STATE_TRIAL_STARTED
    case STATE_TRIAL_STARTED:
      send("STATE_TRIAL_STARTED");
      flash(7);
      // check if trial time out (give a chance to continue if force > hit_thresh)
      if (trial_time > hit_window * 1000 && moduleValue_now < hit_thresh) {
        send("trial_time > hit_window && moduleValue_now < hit_thresh");
        NEXT_STATE = STATE_FAILURE;
      }
      // check if force decreased from peak too much
      else if (moduleValue_now <= (peak_moduleValue - failure_tolerance)) {
        send("moduleValue_now <= (peak_moduleValue - failure_tolerance)");
        send(String(peak_moduleValue));
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
      flash(9);
      //check if still in reward zone
      if (moduleValue_now < hit_thresh) {
        hold_timer = millis();
        NEXT_STATE = STATE_TRIAL_STARTED;
      } else if (getTimerDuration(hold_timer) >= hold_time / 1000) {
        // convert from ms to seconds
        NEXT_STATE = STATE_SUCCESS;
      }
      break;
    // STATE_SUCCESS
    case STATE_SUCCESS:
      send("STATE_SUCCESS");
      flash(4);
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
      fastflash(20);
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
      send("STATE_POST_TRIAL");
      flash(5);
      // wait to accumulate a bit of post_trial data
      if (trial_time - trial_end_time >= post_trial_dur) {

        NEXT_STATE = STATE_PARAM_UPDATE;
      }
      break;
    // STATE_PARAM_UPDATE
    case STATE_PARAM_UPDATE:
      send("STATE_PARAM_UPDATE");
      flash(10);
      // post trial processing, execute only once.

      // update force plot with new trial data

      //TODO

      //should include trial_value_buffer data, first and second column, and a maximum (maybe), number of trials, trial start time, initial threshold, hit threshold, trial_value_buffer,
      //hold  time, trial end time, success, peak_moduleValue
      sendTrialData2Python();
      // set(app.force_line, 'XData', trial_value_buffer(:, 1), ...
      //     'YData', trial_value_buffer(:, 2),'Visible','on');
      // ymax = max(app.hit_thresh.Value, peak_moduleValue) * 1.25;
      // ylim(app.moduleValueAxes, [-5 ymax]);

      // // update trial_table
      // trial_table(num_trials, :) = {trial_start_time, app.init_thresh.Value, app.hit_thresh.Value, trial_value_buffer, ...
      //     app.hold_time.Value, trial_end_time, success, peak_moduleValue};

      // reset data buffer
      trial_value_buffer.clear();
      tmp_value_buffer.clear();
      peak_moduleValue = 0;
      success = false;

      it_timer = millis();
      NEXT_STATE = STATE_INTER_TRIAL;
      break;
    // STATE_INTER_TRIAL
    case STATE_INTER_TRIAL:
      send("STATE_INTER_TRIAL");
      flash(12);
      // wait a short period of time between trials
      if (getTimerDuration(it_timer) >= inter_trial_dur) {
        it_timer = millis();
        NEXT_STATE = STATE_IDLE;
      }

      break;
    case STATE_SESSION_END:
      send("STATE_SESSION_END");
      flash(5);
      //TO-DO
      // finish_up(trial_table,session_t, num_trials, num_rewards, app, crashed);
      // exit while loop
      break;

    default:
      send("default");
      fastflash(20);
      send("error in state machine!");
      //TO-DO
      // finish_up(trial_table,session_t, num_trials, num_rewards, app, crashed);
      // exit while loop
      break;
  }

  CURRENT_STATE = NEXT_STATE;
}

// void finish_up(trial_table, session_t, num_trials, num_rewards, app, crashed) {
// //   //TO-DO
//     send('Session Ended');
    
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


float avebuffer(int aveOnLast) {
  // sort la moyenne des x derniers
  float ave = 0.0;
  for (int i = dataBuffer.size() - aveOnLast; i < dataBuffer.size(); i++) {
    ave += dataBuffer[i];
  }
  ave = ave / aveOnLast;
  return ave;
}

void sendTrialData2Python() {
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
  SerialUSB.print("ts");
  SerialUSB.print(String(trial_start_time));
  SerialUSB.print("it");
  SerialUSB.print(String(init_thresh));
  SerialUSB.print("hth");
  SerialUSB.print(String(num_trials));
  SerialUSB.print("ht");
  SerialUSB.print(String(hit_thresh));
  SerialUSB.print("te");
  SerialUSB.print(String(trial_end_time));
  SerialUSB.print("s");
  SerialUSB.print(String(success));
  SerialUSB.print("pk");
  SerialUSB.print(String(peak_moduleValue));

  SerialUSB.println("fin");
  trial_value_buffer.clear();
  tmp_value_buffer.clear();
  // code de fin d'envoi de données
}

void sendData2Python() {
  // envoie les données de l'essai : sous la forme ##;##;##;...fin et
  // la forme temps correspondant en seconde ligne
  unsigned long timeStamp;
  unsigned long StartTime;
  SerialUSB.flush();
  // Data
  String dataDelimiter = "data";
  SerialUSB.print(dataDelimiter);
  for (int i = 0; i < dataBuffer.size(); i++) {
    SerialUSB.print(dataBuffer[i]);
    SerialUSB.print(';');
  }
  // Temps
  StartTime = LastTime - (lenBuffer * DL_Sampling);
  String timeDelimiter = "time";
  SerialUSB.print(timeDelimiter);
  for (int i = 0; i < dataBuffer.size(); i++) {
    timeStamp = StartTime + (i * DL_Sampling);
    SerialUSB.print(timeStamp);
    SerialUSB.print(';');
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

void fillBuffer() {
  // Rempli la pile temps et data et retourne la moyenne des n dernières valeurs data

  // rempli le buffer data
  leverVal = analogRead(AnalogIN);
  if (dataBuffer.size() >= lenBuffer) {
    dataBuffer.pop_front();
  }
  dataBuffer.push_back(leverVal);

  // Prends en note le dernier temps enregistre dans le buffer
  LastTime = millis() - startArduinoProg;
  delay(10);
}
void experimentOn() {

  int posIndice;

  // Devrait aller dans 'case i' :
  posIndice = serialCommand.indexOf('b');
  initTrial = serialCommand.substring(1, posIndice).toFloat();
  baselineTrial = serialCommand.substring(posIndice + 1).toFloat();
  while (serialCommand.charAt(0) == 's') {
    fastflash(5);
    delay(50);
    if (SerialUSB.available() > 0) {
      serialCommand = SerialUSB.readStringUntil('\r');
    }
    stateMachine();
    // fillBuffer();
    // // delay(DL_Sampling);
    // valMoyenne = avebuffer(aveOnLast);

    // if (valMoyenne > initTrial) {
    //   sendData2Python();
    // }
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
}


void loop() {
  if (SerialUSB.available() > 0) {
    serialCommand = SerialUSB.readStringUntil('\r');
  }

  switch (serialCommand.charAt(0)) {  // Première lettre de la commande
    case 'w':  // boucle defaut standby
      break;
    case 'p':  // Initialisation : transmission des paramètres de la tâche à partir de Python
      {
        send("hi");
        // sendArduino("p" + init_thresh + ";" + init_baseline + ";" + min_duration + ";" + hit_window + ";" + hit_thresh)
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
      fastflash(2);
      }
      break;
    case 's':  // Start
      experimentOn();
      break;
  }
}
