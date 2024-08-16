WELCOME TO MOTOPYA!

This software is being created to accomplish tasks previously executed on Matlab with Mototrak devices. Instead of retrieving data using Matlab on the computer, this software is aimed to be used on raspberry pi in order to achieve faster data retrieval and a more independant system. 

RASPBERRY PI:   
  - SETUP 
    - HARDWARE
      - There are 3 components that need to be connected to the device:
        1. Potentiometer (for the moment this mimics the use of the mototrak lever):
          - Using the ADS1015
		- Lever to ADS1015:
			- "+" : 3-5V
			- "-" : GND
			- OUT : A0
		- ADS1015 to Raspbi GPIO:
			- SCL : SCL
			- SDA : SDA
			- INT : #4
			- 3-5V : 5.0V
			- GND : GND
        2. Knob:
            - "+" : 5V
            - "-" : GND
            - OUTA: #20
            - OUTB: #21
        3. Buzzer:
            - "+" : #13
            - "-" : GND
	4. LED:
            - "+" : #19
            - "-" : GND

  - USAGE
    - run "python main.py" in src folder
	- if dependencies in "requirements.txt" are not installed, they will be auto-installed on runtime if there is an internet connection.
