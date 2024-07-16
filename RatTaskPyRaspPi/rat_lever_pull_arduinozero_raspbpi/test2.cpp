/*
 * test2.cpp
 * 
 * Copyright 2024  <ethier-lab@raspberrypi>
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 * 
 * 
 */
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

#include <iostream>
using namespace std;

int main(int argc, char **argv)
{
	if (wiringPiSetup() == -1) {
        std::cerr << "WiringPi setup failed" << std::endl;
        return 1;
	}
	pinMode(22, OUTPUT);
	digitalWrite(22, HIGH);
	//pinMode(6, OUTPUT);
	//digitalWrite(6, HIGH);
	
	//while (true){
		//for (int i = 0; i < 32 ; i += 1){
			//cout << i << endl;
			//pinMode(i, OUTPUT);
			//digitalWrite(i, HIGH);
		    //usleep(10000);
			
		//}
		
	//}
	int i = 0;
	while (true) {
		usleep(100000000);
		cout<< "hi " << i << endl;
		i++;
	}
	
	return 0;
}

