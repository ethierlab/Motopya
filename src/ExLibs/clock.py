import time as t


class Clock():
    def __init__(self):
        self.paused = False
        self.pause_time = 0
        self.pause_start = t.time()
        
        
    def pause(self):
        self.pause_start = t.time()
        self.paused = True
        
    def resume(self):
        self.paused = False
        
    def reset(self):
        self.resume()
        self.pause_time = 0
        
    def is_paused(self):
        return self.paused
        
    def time(self):
        if self.paused:
            self.pause_time += t.time() - self.pause_start
            self.pause_start = t.time()
        return t.time() - self.pause_time
    
    
clock = Clock()