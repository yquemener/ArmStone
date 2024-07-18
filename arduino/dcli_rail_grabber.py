import sys
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
#ser.open()
time.sleep(0.5)
cmd = f"111 100 222\n"
print(cmd)
if ser.is_open:
	ser.write(cmd.encode('utf-8'))
	ser.write(cmd.encode('utf-8'))
	ser.write(cmd.encode('utf-8'))
time.sleep(1)

