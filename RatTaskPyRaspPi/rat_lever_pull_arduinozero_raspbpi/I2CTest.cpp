
#include <iostream>
#include <wiringPi.h>
#include <wiringPiI2C.h>
#include <wiringSerial.h>
#include <unistd.h>
#include <math.h>
#include <bitset>
#include <cstdlib>
#include <thread>


const int ADS1015_I2C_ADDR = 0x48;
const int ADS1015_CONFIG_REG= 0x01;
const int ADS1015_CONVERSION_REG = 0x00;

using namespace std;

void runPythonScript(const std::string& scriptPath) {
	string command = "python " + scriptPath;
	system(command.c_str());
}


int main() {
	
	string path = "./read-all.py";
	
	thread pythonThread(runPythonScript, path);
	// Initialize wiringPi library and serial port
  //SETUP
  while(true) {
	  if (wiringPiSetup() == -1) {
		std::cerr << "WiringPi setup failed" << std::endl;
		continue;
		
	 }
	 int analog_fd = wiringPiI2CSetup(ADS1015_I2C_ADDR);
	  if (analog_fd == -1) {
		std::cerr << "Failed to initalize ADS1015 I2C connection." << std::endl;
		continue;
	  }
	  else {
		cout << "Successfully setup I2C" << std::endl;
	  }
	 
	  
	  
		//wiringPiI2CWriteReg8(analog_fd, 0x2D, 0b00001000);
	  //LOOP
	  while(true) {
		  bitset<16> bits;
		  bits =  wiringPiI2CReadReg16(analog_fd, ADS1015_CONVERSION_REG);
		  uint16_t bits2;
		  bits2 = static_cast<uint16_t>(bits.to_ulong());
		  uint8_t highByte = (bits2 >> 8) & 0xFF;
		  uint8_t lowByte = bits2 & 0xFF;
		  uint16_t proper_number = (static_cast<uint16_t>(lowByte) << 8) | highByte;
		  proper_number = proper_number / pow(2, 4);
		  if (proper_number != 0) {
			   cout << "proper number:  " << proper_number << endl;
		  }
		  int moduleValue_now = wiringPiI2CReadReg16(analog_fd, ADS1015_CONVERSION_REG);
		  int adc_value = moduleValue_now & 0xFFF;
		  double value = ( (moduleValue_now  - adc_value )/ pow(2, 12)) + (adc_value * pow(2, 4));
		  double before_value = value;
		  if (value < 200) {
			value += 4095;
			}
			value -= 4036;
			if (value != 0 && moduleValue_now !=0) {
			  std::cout << value << std::endl;
			  std::cout << before_value << std::endl;
			  std::cout << moduleValue_now << std::endl;
			  cout << bits << endl;
			 }
		  
		  if (moduleValue_now == -1) {
			  std::cout << "error -1" << std::endl;
			  break;
		  }
	  }
	
	}
  }
