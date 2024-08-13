# encoder.py

from gpiozero import InputDevice, CompositeDevice, EventsMixin
from threading import Event

class RotaryEncoder2(EventsMixin, CompositeDevice):
    FULL_STEP_TRANSITIONS = {
        'cw3':  ['+1',   'cw3',  'idle', 'cw2'],
        'cw2':  ['idle', 'cw3',  'cw1',  'cw2'],
        'cw1':  ['idle', 'cw3',  'cw1',  'cw2'],
        'idle': ['idle', 'ccw1', 'cw1',  'idle'],
        'ccw1': ['idle', 'ccw1', 'ccw3', 'ccw2'],
        'ccw2': ['idle', 'ccw1', 'ccw3', 'ccw2'],
        'ccw3': ['-1',   'idle', 'ccw3', 'ccw2'],
    }
    
    QUARTER_STEP_TRANSITIONS = {
        '0': ['0', '-1', '+1',  'x'],
        '1': ['+1', '0', 'x', '-1'],
        '2': ['-1', 'x', '0', '+1'],
        '3': ['x',   '+1', '-1', '0'],
    }

    def __init__(self, a, b, *, bounce_time=None, max_steps=16,
                 threshold_steps=(0, 0), wrap=False, pin_factory=None, half_step=False):
        min_thresh, max_thresh = threshold_steps
        if max_thresh < min_thresh:
            raise ValueError('maximum threshold cannot be less than minimum')
        self._steps = 0
        self._max_steps = int(max_steps)
        self._threshold = (int(min_thresh), int(max_thresh))
        self._wrap = bool(wrap)
        self._state = 'idle'
        self._edge = 0
        self._last_edge = 0
        self._rotate_event = Event()
        self._rotate_cw_event = Event()
        self._rotate_ccw_event = Event()
        self._half_step = bool(half_step)
        self._when_rotated = None
        self._when_rotated_cw = None
        self._when_rotated_ccw = None
        super().__init__(
            a=InputDevice(a, pull_up=True, pin_factory=pin_factory),
            b=InputDevice(b, pull_up=True, pin_factory=pin_factory),
            _order=('a', 'b'), pin_factory=pin_factory)
        self.a.pin.bounce_time = bounce_time
        self.b.pin.bounce_time = bounce_time
        self.a.pin.edges = 'both'
        self.b.pin.edges = 'both'
        self.a.pin.when_changed = self._a_changed
        self.b.pin.when_changed = self._b_changed
        self._fire_events(self.pin_factory.ticks(), self.is_active)

    def __repr__(self):
        try:
            self._check_open()
            return (
                f"<gpiozero.{self.__class__.__name__} object on pins "
                f"{self.a.pin!r} and {self.b.pin!r}>")
        except DeviceClosed:
            return super().__repr__()

    def _a_changed(self, ticks, state):
        edge = (self.a._state_to_value(state) << 1) | (self._edge & 0x1)
        if self._half_step:
            self._change_state2(ticks, edge)
        else:
            self._change_state(ticks, edge)

    def _b_changed(self, ticks, state):
        edge = (self._edge & 0x2) | self.b._state_to_value(state)
        if self._half_step:
            self._change_state2(ticks, edge)
        else:
            self._change_state(ticks, edge)

    def _change_state(self, ticks, edge):
        self._edge = edge
        transitions = RotaryEncoder2.FULL_STEP_TRANSITIONS
        new_state = transitions[self._state][edge]
        if new_state == '+1':
            self._steps = (
                self._steps + 0.5
                if not self._max_steps or self._steps < self._max_steps else
                -self._max_steps if self._wrap else self._max_steps
            )
            self._rotate_cw_event.set()
            self._fire_rotated_cw()
            self._rotate_cw_event.clear()
            self._state = 'idle'
        elif new_state == '-1':
            self._steps = (
                self._steps - 0.5
                if not self._max_steps or self._steps > -self._max_steps else
                self._max_steps if self._wrap else -self._max_steps
            )
            self._rotate_ccw_event.set()
            self._fire_rotated_ccw()
            self._rotate_ccw_event.clear()   
            self._state = 'idle'        
        else:
            self._state = new_state
            return
        self._rotate_event.set()
        self._fire_rotated()
        self._rotate_event.clear()
        self._fire_events(ticks, self.is_active)

    def _change_state2(self, ticks, edge):
        self._edge = edge
        transitions = RotaryEncoder2.QUARTER_STEP_TRANSITIONS
        new_state = transitions[str(self._last_edge)][edge]
        if new_state == '+1':
            self._steps = (
                self._steps + 0.25
                if not self._max_steps or self._steps < self._max_steps else
                -self._max_steps if self._wrap else self._max_steps
            )
            self._rotate_cw_event.set()
            self._fire_rotated_cw()
            self._rotate_cw_event.clear()
            self._state = 'idle'
        elif new_state == '-1':
            self._steps = (
                self._steps - 0.25
                if not self._max_steps or self._steps > -self._max_steps else
                self._max_steps if self._wrap else -self._max_steps
            )
            self._rotate_ccw_event.set()
            self._fire_rotated_ccw()
            self._rotate_ccw_event.clear()   
            self._state = 'idle'
        else:
            self._state = new_state
            return
        self._last_edge = self._edge
        self._rotate_event.set()
        self._fire_rotated()
        self._rotate_event.clear()
        self._fire_events(ticks, self.is_active)        

    def wait_for_rotate(self, timeout=None):
        return self._rotate_event.wait(timeout)

    def wait_for_rotate_clockwise(self, timeout=None):
        return self._rotate_cw_event.wait(timeout)

    def wait_for_rotate_counter_clockwise(self, timeout=None):
        return self._rotate_ccw_event.wait(timeout)

    @property
    def when_rotated(self):
        return self._when_rotated

    @when_rotated.setter
    def when_rotated(self, value):
        self._when_rotated = value

    @property
    def when_rotated_clockwise(self):
        return self._when_rotated_cw

    @when_rotated_clockwise.setter
    def when_rotated_clockwise(self, value):
        self._when_rotated_cw = value

    @property
    def when_rotated_counter_clockwise(self):
        return self._when_rotated_ccw

    @when_rotated_counter_clockwise.setter
    def when_rotated_counter_clockwise(self, value):
        self._when_rotated_ccw = value

    @property
    def steps(self):
        return self._steps

    def _fire_rotated(self):
        if self.when_rotated:
            self.when_rotated()

    def _fire_rotated_cw(self):
        if self.when_rotated_clockwise:
            self.when_rotated_clockwise()

    def _fire_rotated_ccw(self):
        if self.when_rotated_counter_clockwise:
            self.when_rotated_counter_clockwise()

    @steps.setter
    def steps(self, value):
        value = int(value)
        if self._max_steps:
            value = max(-self._max_steps, min(self._max_steps, value))
        self._steps = value

    @property
    def value(self):
        try:
            return self._steps / self._max_steps
        except ZeroDivisionError:
            return 0

    @value.setter
    def value(self, value):
        self._steps = int(max(-0.5, min(0.5, float(value))) * self._max_steps)

    @property
    def is_active(self):
        return self._threshold[0] <= self._steps <= self._threshold[1]

    @property
    def max_steps(self):
        return self._max_steps

    @property
    def threshold_steps(self):
        return self._threshold

    @property
    def wrap(self):
        return self._wrap

# Example usage:
if __name__ == "__main__":
    encoder = RotaryEncoder2(a=21, b=20, half_step=True)
    print(f"Initial steps: {encoder.steps}")
    encoder.wait_for_rotate()
    print(f"Steps after rotation: {encoder.steps}")
