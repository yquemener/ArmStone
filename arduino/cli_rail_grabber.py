import sys
import serial
import time

if __name__ == '__main__':
    value = int(sys.argv[1])
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=10,    
        			parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_ONE,
    				bytesize=serial.EIGHTBITS)
        time.sleep(0.3)
        ser.write("\n\n\n".encode('utf-8'))
        cmd = f"111 {value} 222\n"
        ser.write(cmd.encode('utf-8'))
        ser.flush()
        ser.close()
    except Exception as e:
    	print("Failed to connect to the serial port.")
    	print(e)
