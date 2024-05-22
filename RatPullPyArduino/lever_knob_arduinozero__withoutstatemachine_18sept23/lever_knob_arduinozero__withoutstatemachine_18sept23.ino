// #include <CircularBuffer.h>

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

using namespace std;

// DECLARATION VARIABLES------------
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

auto loop_timer = std::chrono::high_resolution_clock::now();
auto experiment_start = std::chrono::high_resolution_clock::now();
double pause_time;
//Input Parameters
int num_rewards = 0;
int num_trials = 0;
int moduleValue_now = 0;
int peak_moduleValue = 0;
auto hold_timer = std::chrono::high_resolution_clock::now();
auto it_timer = std::chrono::high_resolution_clock::now();
std::vector<std::vector<double>> tmp_value_buffer;    // [time value], first row is oldest data
std::vector<std::vector<double>> trial_value_buffer;  // [time value]
double duration;
int MaxTrialNum;
double hold_time_min;
double hit_thresh_min;

//Initial Parameters
int num_pellets = 0;
std::deque<bool> past_10_trials_succ;


int init_thresh = 0;
double session_t;


int moduleValue_before;

bool trial_started = false;
unsigned long trial_start_time;
unsigned long trial_end_time;
unsigned long trial_time;
bool success = false;
// std::list<std::list<double>> trial_value_buffer; // Assuming buffer size is 2x2
bool crashed = false;  // Assuming this variable is declared elsewhere
int duration_minutes;  // Assuming app.duration.Value is in minutes
int max_trial_num;
bool stop_session;
bool pause_session;
int hit_thresh;
int hit_window;
double failure_tolerance;
double hold_time;
double hit_thresh_max;
double hold_time_max;
bool adapt_hit_thresh;
bool adapt_hold_time;
bool adapt_drop_tolerance;
int post_trial_dur;
int inter_trial_dur;
double buffer_dur = 1;


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


double timePointsToDouble(const std::chrono::time_point<std::chrono::high_resolution_clock>& start, const std::chrono::time_point<std::chrono::high_resolution_clock>& end) {
  auto duration = end - start;
  double double_duration = std::chrono::duration_cast<std::chrono::duration<double>>(duration).count();
  return double_duration;
}

double getTimerDuration(const std::chrono::time_point<std::chrono::high_resolution_clock>& start) {
  return timePointsToDouble(start, std::chrono::high_resolution_clock::now());
}

double getMean(std::vector<double> numbers) {
  double sum = std::accumulate(numbers.begin(), numbers.end(), 0.0);

  double average = sum / numbers.size();
  return average;
}
double getBoolMean(deque<bool> bools) {
  double sum = std::accumulate(bools.begin(), bools.end(), 0.0);

  double average = sum / bools.size();
  return average;
}

// void finish_up(trial_table, session_t, num_trials, num_rewards, app, crashed) {
//   //TO-DO
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


void sendData2Python() {
  // envoie les données de l'essai : sous la forme ##;##;##;...fin et
  // la forme temps correspondant en seconde ligne
  unsigned long timeStamp;
  unsigned long StartTime;
  SerialUSB.flush();
  // Data
  SerialUSB.print('d');
  for (int i = 0; i < dataBuffer.size(); i++) {
    SerialUSB.print(dataBuffer[i]);
    SerialUSB.print(';');
  }
  // Temps
  StartTime = LastTime - (lenBuffer * DL_Sampling);
  SerialUSB.print('t');
  for (int i = 0; i < dataBuffer.size(); i++) {
    timeStamp = StartTime + (i * DL_Sampling);
    SerialUSB.print(timeStamp);
    SerialUSB.print(';');
  }
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
    delay(5);
    if (SerialUSB.available() > 0) {
      serialCommand = SerialUSB.readStringUntil('\r');
    }
    // stateMachine();
    fillBuffer();
    delay(DL_Sampling);
    valMoyenne = avebuffer(aveOnLast);

    if (valMoyenne > initTrial) {
      sendData2Python();
    }
  }
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
  loop_timer = std::chrono::high_resolution_clock::now();
  experiment_start = std::chrono::high_resolution_clock::now();
}

void loop() {
  if (SerialUSB.available() > 0) {
    serialCommand = SerialUSB.readStringUntil('\r');
  }

  switch (serialCommand.charAt(0)) {  // Première lettre de la commande

    case 'w':  // boucle defaut standby
      digitalWrite(13, LOW);
      break;
    case 'i':  // Initialisation : transmission des paramètres de la tâche à partir de Python
      
      break;
    case 's':  // Start
      digitalWrite(13, HIGH);
      experimentOn();
      break;
  }
}
