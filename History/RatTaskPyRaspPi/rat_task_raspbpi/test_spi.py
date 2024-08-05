import spidev
import time


spi = spidev.SpiDev()
spi.open(0,1)
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
    #print("Resetting")
    #initialize_ls7366r()
    for i in range(5):
        counter_value = read_counter()
        if counter_value != [0,0,0,0,0] and counter_value != [96,0,0,0,0]:
            print("Counter Value:", counter_value)
        time.sleep(0.0001)
    
spi.close()




# class ls7366r:
#     def __init__(self, spi_channel=0):
#         self.spi_channel = spi_channel
#         self.conn = spidev.SpiDev(0, spi_channel)
#         #self.conn = spidev.SpiDev(1, spi_channel)
#         self.conn.max_speed_hz = 1000000
#         
#     def __del__(self):
#         self.close
#         
#     def close(self):
#         if self.conn != None:
#             self.conn.close
#             self.conn = None
#             
#     def bitstring(self, n):
#         s = bin(n)[2:]
#         return '0'*(8-len(s)) + s
#     
#     def read(self, adc_channel=0):
#         cmd = 128
#         cmd  += 64
#         if adc_channel % 2 == 1:
#             cmd += 8
#         if (adc_channel/2) % 2 == 1:
#             cmd += 16
#         if (adc_channel / 4) % 2 == 1:
#             cmd += 32
#             
#         reply_bytes = self.conn.xfer2([cmd, 0,0,0,])
#         
#         reply_bitstring = ''.join(self.bitstring(n) for n in reply_bytes)
#         
#         reply = reply_bitstring[5:19]
#         
#         return int(reply,2)
#     
# if __name__ == '__main__':
#     spi = ls7366r(1)
#     count = 0
#     a0 = 0
#     a1 = 0
#     a2 = 0
#     a3 = 0
#     
#     while True:
#         count += 1
#         a0 += spi.read(0)
#         a1 += spi.read(1)
#         a2 += spi.read(2)
#         a3 += spi.read(3)
#         
#         if count == 10:
#             print("ch0=%04d, ch1=%04d, ch2=%04d, ch3=%04d" % (a0/10, a1/10, a2/10, a3/10))
#             count = 0
#             a0 = 0
#             a1 = 0
#             a2 = 0
#             a3 = 0
#             time.sleep(2)