import spidev
import time


spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 500000

CLR_MDR0 = 0x08
CLR_MDR1 = 0x10
CLR_CNTR = 0x20
CLR_STR = 0x30
READ_CNTR = 0x60
WRITE_MDR0 = 0x88
WRITE_MDR1 = 0x90

def initialize_ls7366r():
    spi.xfer2([CLR_MDR0])
    spi.xfer2([CLR_MDR1])
    spi.xfer2([CLR_CNTR])
    spi.xfer2([CLR_STR])
    
    spi.xfer2([WRITE_MDR0, 0x03])
    spi.xfer2([WRITE_MDR1, 0x00])
    
    
def read_counter():
    response = spi.xfer2([READ_CNTR, 0x00, 0x00, 0x00, 0x00])
    #counter = (response[1] << 24) | (response[2] << 16) | (response[3] << 8) |response[4]
    counter = response
    return counter

initialize_ls7366r()

while True:
    print("Resetting")
    initialize_ls7366r()
    for i in range(5):
        counter_value = read_counter()
        print("Counter Value:", counter_value)
        time.sleep(0.1)
    
spi.close()