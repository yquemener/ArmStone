from pyvesc import VESC
from time import sleep, time
import pygame



def get_joy(joy):
    pygame.event.get()
    vel_forward = joy.get_axis(1)
    vel_side = joy.get_axis(0)
    rot = joy.get_button(1) - joy.get_button(3)
    return vel_forward, vel_side, rot
    

def inverse_kinematics(vx, vy, wz, lx=29, ly=29.5, r=8):
    wfl = 1/r*(vx-vy-(lx+ly)*wz)
    wfr = 1/r*(vx+vy+(lx+ly)*wz)
    wrl = 1/r*(vx+vy-(lx+ly)*wz)
    wrr = 1/r*(vx-vy+(lx+ly)*wz)
    return wfl, wfr, wrl, wrr

def motors_init():
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
    return [front_left, front_right, rear_left, rear_right]

def control_loop(timeout=10):
    tstart = time()
    motors_invert = [-1, 1, -1, 1]
    initialized = False
    tries=0
    while not initialized and tries<5:
        try:
            motors = motors_init()
            initialized = True
        except Exception:
            tries+=1
            sleep(1)
    pygame.init()
    cycle1=0
    joy = pygame.joystick.Joystick(0)
    while time()-tstart<timeout or timeout<0:
        try:
            vel_forward, vel_side, rot = get_joy(joy)
        except Exception:
            vel_forward, vel_side, rot = 0,0,0
        print(f"{vel_forward:.2f}, {vel_side:.2f}, {rot:.2f}             ")
        cmds = inverse_kinematics(vel_forward, vel_side, rot)
        print(f"{cmds[0]:.3f} {cmds[1]:.3f} {cmds[2]:.3f} {cmds[3]:.3f} ")
        for cmd, motor, invert in zip(cmds, motors, motors_invert):
            cmd = min(0.1, max(-0.1, cmd*invert))
            motor.set_duty_cycle(cmd)
        sleep(0.0)
        print()
    for motor in motors:
        motor.set_duty_cycle(0)


if __name__ == "__main__":
    control_loop(-1)
