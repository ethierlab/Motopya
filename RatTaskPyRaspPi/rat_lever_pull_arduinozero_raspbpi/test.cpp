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
#include <cstdlib>
#include <thread>

#include <bitset>
#include <math.h>

#include <iomanip>

#include <limits.h>

#include <array>

#include <fstream>

#include <sstream>

using namespace std;

const int pinA = 5;  // A output
const int pinB = 6;  // B output

int encoderPos;
int previous_angle;
int moduleValue_encoder;
bool attached = false;
int previousA;
int previousB;

deque<pair<int, int>> deq;

void getEncoderValue(){
  int A = digitalRead(pinA);
  int B = digitalRead(pinB);
  deq.emplace_back(A,B);
}

void updateEncoderValue() {
  
  if(deq.empty()) {
    return;
  }
  int encoderA = deq.front().first;
  int encoderB = deq.front().second;
  deq.pop_front();
  
  
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
  if (encoderPos < 0){
    encoderPos = 0;
  }
  previousA = encoderA;
  previousB = encoderB;
  
  int angle = ((encoderPos / 4)); //%360 abs
  previous_angle = angle;
  moduleValue_encoder = angle;
}


void enableInterruptA(int pin) {
  std::cout << "Enabling on pin " << pin << std::endl;
  if (wiringPiISR(pin, INT_EDGE_BOTH, &getEncoderValue)  < 0) {
    cout << "Failed to enable interrupt" << endl;
  }
  //std::cout << "Interrupts enabled on pin " << pin << std::endl;
}

void enableInterruptB(int pin) {
  std::cout << "Enabling on pin " << pin << std::endl;
  if (wiringPiISR(pin, INT_EDGE_BOTH, &getEncoderValue)  < 0) {
    cout << "Failed to enable interrupt" << endl;
  }
  //std::cout << "Interrupts enabled on pin " << pin << std::endl;
}


void enableInterrupts() {
  if (!attached) {
    enableInterruptA(pinA);
    enableInterruptB(pinB);
    attached = true;
  }
}

void loop_updateValue() {
  while(true){
    //getEncoderValue();
    updateEncoderValue();
    cout << moduleValue_encoder << endl;
  }
  
}

int main() {
	  //pinMode(AnalogIN, INPUT);
    
  if (wiringPiSetup() == -1) {
      std::cerr << "WiringPi setup failed" << std::endl;
      return 1;
  }
  pinMode(pinA, INPUT);// Internal pull-up resistor for switch A
  pinMode(pinB, INPUT);// Internal pull-up resistor for switch B
  enableInterrupts();
  //thread updateValue_loop(loop_updateValue);
  loop_updateValue();

}
