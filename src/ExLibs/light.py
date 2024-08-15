from gpiozero import LED
from time import sleep
import time as t
import threading

#Range is between 220 - 880 for small Piezo buzzer
class Light():
    def __init__(self, pin):
        self.pin = pin
        self.duration = 1
        self.led = LED(self.pin)
        self.thread = None

    def flash(self):
        if self.thread != None and self.thread.is_alive():
            self.thread.join()
        self.thread = threading.Thread(target=self.thread_flash)
        self.thread.start()
        
    def thread_flash(self):
        self.led.on()
        sleep(self.duration)
        self.led.off()
        
        
