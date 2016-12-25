
#!/usr/bin/python
import sys
import smbus
import time
import math

bus = smbus.SMBus(1)
address = 0x1e


def read_byte(adr):
    return bus.read_byte_data(address, adr)

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def write_byte(adr, value):
    bus.write_byte_data(address, adr, value)

write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000) # Continuous sampling
#write_byte(0, 0b00000000) # Set to 8 samples @ 15Hz
#write_byte(1, 0b11111111) # 1.3 gain LSb / Gauss 1090 (default)
#write_byte(2, 0b00000000) # Continuous sampling

scale = 0.92

while 1 == 1:
    x_out = read_word_2c(3) * scale
    y_out = read_word_2c(7) * scale
    z_out = read_word_2c(5) * scale

    data = []

    for i in range(0, 3):
	for j in range(0, 3):
	    if i == j:
		continue

	    if i == 0:
		a = x_out
	    elif i == 1:
		a = y_out
	    else:
		a = z_out

	    if j == 0:
		b = x_out
	    elif j == 1:
		b = y_out
	    else:
		b = z_out

	    t  = math.atan2(a, b)
	    if (t < 0):
		t += 2 * math.pi
	    
	    data.append(str(i) + ":" + str(j) + " " + str(round(math.degrees(t))))


#    print "\rBearing: " + str(math.degrees(bearing))
    sys.stdout.write("\rBearing: " + str(data) + "                   ")
#    sys.stdout.write("\rBearing: " + str(math.degrees(bearing)))
    sys.stdout.flush()
    time.sleep(0.1)
