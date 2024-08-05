import spidev

dev1 = spidev.SpiDev()
dev2 = spidev.SpiDev()

def dec_config(cfg1, cfg2):
    dev1.open(0,0)
    dev1.writebytes([cfg1])
    dev2.open(0,1)
    dev2.writebytes([cfg1, cfg2])
    
    
dec_config(Counter