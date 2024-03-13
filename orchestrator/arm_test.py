#!/usr/bin/env python3

import time
from xarm.wrapper import XArmAPI

arm = XArmAPI("192.168.1.212")
arm.motion_enable(enable=True)
arm.set_mode(5)
arm.set_state(state=0)

arm.reset(wait=True)

#ret = arm.set_position(*poses[0], speed=10, mvacc=100, wait=False)
p = arm.position
# arm.set_position(x=p[0]+20)
arm.vc_set_cartesian_velocity(speeds=[15,0,0,0,0,0], duration=1)
time.sleep(2)
arm.vc_set_cartesian_velocity(speeds=[-15,0,0,0,0,0], duration=1)
time.sleep(2)
arm.set_mode(0)
arm.set_state(state=0)

# arm.set_position(x=p[0]+40)
# print('set_position, ret: {}'.format(ret))
arm.reset(wait=True)
arm.disconnect()