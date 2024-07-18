import sys
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=10,    
			parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS)
time.sleep(0.3)

for k in range(-180,360,5):
    print(k)
    ser.write("\n\n\n".encode('utf-8'))
    cmd = f"111 {k} 222\n"
    ser.write(cmd.encode('utf-8'))
    ser.flush()
    time.sleep(0.3)
ser.close()
    
