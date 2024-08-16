from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
from time import sleep
import threading

#Range is between 220 - 880 for small Piezo buzzer
class Buzzer():
    def __init__(self, pin):
        self.pin = pin
        self.duration = 1
        self.buzzer = TonalBuzzer(self.pin)
        self.thread = None
        
    def play_init(self):
        self.play(300)
        
    def play_success(self):
        self.play(880)
        
    def play_failure(self):
        self.play(400)

    def play(self, tone):
        if self.thread != None and self.thread.is_alive():
            self.thread.join()
        self.thread = threading.Thread(target=self.thread_play, args=(tone,))
        self.thread.start()
        
    def thread_play(self, tone):
        self.buzzer.play(Tone(tone))
        sleep(self.duration)
        self.buzzer.stop()
        
        