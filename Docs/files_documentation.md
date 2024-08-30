# FILES DOCUMENTATION
Here is a small description of each file and class and their use in order to understand for future modification

## main.py

This file is what we run to start the program and hold a few essential functions for running sessions and recording data

## buzzer.py

Holds buzzer class that uses a simple piezo buzzer

## clock.py

Keeps time for the entire program and allows for pausing so that recorded data doesn't have gaps when the session is paused. Is used throughout the program with clock.time() instead of t.time()

## encoder.py

Class used to get input from a rotary encoder

## feeder.py

Includes simple function to send feed signal to food distributor

## gui.py

Includes main gui, advanced popup and calibration popup classes used by main.py

## input_device.py

Includes abstract class and the inheriting lever and encoder classes for input

## light.py

Includes simple class to use an LED light as output

## session.py

Includes Session class that initializes trials when the initial threshold is passed

## trial.py

Includes Trial class that succeeds or fails based on input and parameters such as the hit threshold

## utils.py

Includes useful functions for other files

