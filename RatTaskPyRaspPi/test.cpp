// #include <CircularBuffer.h>
#include <Python.h>
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

const int pinA = 5;  // A output
const int pinB = 6;  // B output

int encoderPos;
int moduleValue_encoder;
bool attached = false;

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
  if (encoderPos < 0){
    encoderPos = 0;
  }
  
  previousA = encoderA;
  previousB = encoderB;
  
  int angle = ((encoderPos / 4)); //%360 abs
  previous_angle = angle;
  moduleValue_encoder = angle;
  isr_running = false;
}


void enableInterrupt(int pin) {
  std::cout << "Enabling on pin " << pin << std::endl;
  if (wiringPiISR(pin, INT_EDGE_BOTH, &updateEncoderValue)  < 0) {
    cout << "Failed to enable interrupt" << endl;
  }
  //std::cout << "Interrupts enabled on pin " << pin << std::endl;
}


void enableInterrupts() {
  if (!attached) {
    enableInterrupt(pinA);
    enableInterrupt(pinB);
    attached = true;
  }
}


int main() {
	  //pinMode(AnalogIN, INPUT);
  pinMode(pinA, INPUT);// Internal pull-up resistor for switch A
  pinMode(pinB, INPUT);// Internal pull-up resistor for switch B
    
  cout << moduleValue_encoder << endl;

}
