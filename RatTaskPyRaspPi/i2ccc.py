import smbus

device_address_1 = 0x53
device_address_2 = 0x44

i2c = smbus.SMBus(1)

def write_data(adress_reg, data):
    global device_address_1
    global device_address_2
    
    id = i2c.read_byte_data(device_address_1, 0x00)
    i2c.write_byte_data(device_address_2, address_reg, data)