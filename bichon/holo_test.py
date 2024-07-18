from holonomic import get_joy,inverse_kinematics
import pygame

motors_invert = [-1, 1, -1, 1]

pygame.init()
cycle1 = 0
joy = pygame.joystick.Joystick(0)
while True:
    try:
        vel_forward, vel_side, rot = get_joy(joy)
    except Exception:
        vel_forward, vel_side, rot = 0, 0, 0
    cmds = inverse_kinematics(vel_forward*0.1, vel_side*0.1, rot)
    print(f"{vel_forward:.2f}, {vel_side:.2f}, {rot:.2f} \t{cmds[0]:.1f}\t{cmds[1]:.1f}\t{cmds[2]:.1f}\t{cmds[3]:.1f}     ",
          end="\r")
