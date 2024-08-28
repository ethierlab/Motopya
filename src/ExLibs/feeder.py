from gpiozero import LED
import time

pin = 6
led = LED(pin)
def gpio_feed():
    try:
        print("feeding")
        led.on()
        time.sleep(0.005)
        led.off()
    finally:
        pass
