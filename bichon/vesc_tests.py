from pyvesc import VESC
from time import sleep

serial_names = ['pci-0000:00:14.0-usb-0:7.4.3:1.0',
                'pci-0000:00:14.0-usb-0:7.2:1.0',
                'pci-0000:00:14.0-usb-0:7.3:1.0',
                'pci-0000:00:14.0-usb-0:7.1:1.0']

p = "/dev/serial/by-path/"
vescs = [p + fn for fn in serial_names]

motors = list()
retries = 5
for ve in vescs:
    attempt=1
    print(f"Initializing {ve}")
    while attempt <= retries:
        try:
            motor = VESC(serial_port=ve)
            print("Success")
            motors.append(motor)
            break
        except Exception as e:
            print(f"{repr(e)}\nAttempt {attempt}/{retries}")
            attempt+=1
            sleep(1)
sleep(1)
print("Finished")
for motor in motors:
    print(f"Killing {motor}")
    motor.stop_heartbeat()
    motor.serial_port.close()
sleep(1)
for motor in motors:
    del motor
