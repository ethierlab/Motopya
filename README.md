WELCOME TO MOTOPYA!

This software is being created to accomplish tasks previously executed on Matlab with Mototrak devices. Instead of retrieving data using Matlab on the computer, this software is aimed to be used on raspberry pi in order to achieve faster data retrieval and a more independant system. 

# MOTOPYA WITH RASPBERRY PI
## SETUP
### HARDWARE
#### BOX
- Plug in the lever or knob into the "IN" port
- Plug in the pellet feeder into the square port
- Plug in the 12V power outlet to power the feeder
- Refer to this diagram to use the output port
- LED: #19 + GND
- BUZZER: #13 + GND
#### CIRCUIT
- There are 3 components that need to be connected to the device:
1. Lever / Potentiometer:
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

### SOFTWARE
#### DOWNLOADING THE CODE
- Open a terminal
- Ensure there is an internet connection
- run:

```bash
git clone (this repository)
```

#### Running the code
- Go to the `src` folder.
- Open the terminal in the `src` folder (e.g., Tools -> Open Current Folder in Terminal).
- If there is no virtual environment named `venv`, create it with:

```bash
python3 -m venv venv
```

- Activate the virtual environment with:

```bash
source venv/bin/activate
```

- Run:

```bash
python main.py
```

- If dependencies in `requirements.txt` are not installed, they will be auto-installed at runtime if there is an internet connection.

## USAGE
- Enter parameters into the text boxes or load them with the "load" button
- Press Start button (ensure that the input device is at it's baseline in order for it to calibrate to 0)
- Run session
- When session is over (either from time, max trials or pressing stop button), save session by pressing "yes" when prompted
- Files will be saved in "output_files" folder in a folder dedicated to each rat
