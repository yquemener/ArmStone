from pyvesc import VESC
from time import sleep
from holonomic import *
import os


serial_names = ['pci-0000:00:14.0-usb-0:7.4.3:1.0',
                'pci-0000:00:14.0-usb-0:7.2:1.0',
                'pci-0000:00:14.0-usb-0:7.3:1.0',
                'pci-0000:00:14.0-usb-0:7.1:1.0']


front_left = serial_names[1]
front_right = serial_names[3]
back_left = serial_names[2]
back_right = serial_names[0]


# vescs = /dev/serial/by-path/[vesc1, vesc2, vesc3, vesc4]
p="/dev/serial/by-path/"
vescs = [p+fn for fn in serial_names]
print(vescs)

motors = list()
for vesc in vescs:
    sleep(0.5)
    motors.append(VESC(serial_port=vesc))

front_left = motors[1]
front_right = motors[3]
rear_left = motors[2]
rear_right = motors[0]

rcount = 0
while True :
    try:
        rpm = front_left.get_rpm()
    except AttributeError:
        rcount = rcount+1
#        print("Error", rcount, end="\r")
        continue
    print(-rpm, rcount, end="\r")
    sleep(0.01)