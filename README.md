WELCOME TO MOTOPYA!

This software is being created to accomplish tasks previously executed on matlab with Mototrak device. Instead of retrieving data using matlab on the computer, this software is aimed to be used on either an arduino or raspberry pi in order to achieve faster data retrieval 
and a more independant system. 

Here are the usage directions for each option:

ARDUINO:   
  SETUP 
    HARDWARE
  - There are 3 components that need to be connected to the device:
    1. Potentiometer (for the moment this mimics the use of the mototrak lever):
    + : 5V
    - : GND
    OUT: A0
    2. Knob:
    + : 5V
    - : GND
    OUTA: pin 2
    OUTB: pin 3
    3. Buzzer:
    - : GND
    + : pin 8
   
  USAGE
    - Run the GUI_tkinter python application and connect the arduino via USB-A to micro-USB cable.
   

RASPBERRY PI:   
  SETUP 

    HARDWARE
  - There are 3 components that need to be connected to the device:
    1. Potentiometer (for the moment this mimics the use of the mototrak lever):
      Non-implemented

    2. Knob:
    + : 5V
    - : GND
    OUTA: pin 24
    OUTB: pin 25
    3. Buzzer:
      Non-implemented

  USAGE
    - (currently) Run "socat -d -d pty,raw,echo=0 pty,raw,echo=0" in order to create virtual ports to communicate between python and c++ file. Make sure the ports listed are the ones used in each file.
    - Run the GUI_tkinter python application and connect the arduino via USB-A to micro-USB cable.
