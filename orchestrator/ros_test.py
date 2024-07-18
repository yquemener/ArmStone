#!/usr/bin/env python
# license removed for brevity
import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

def talker():
    pub = rospy.Publisher('/as_base_holonomic_controller/cmd_vel', Twist)
    rospy.init_node('talker', anonymous=False)
    rate = rospy.Rate(100) # 10hz
    while not rospy.is_shutdown():
        t = Twist()
        t.linear.x = -0.4
        # rospy.loginfo(t)
        pub.publish(t)
        rate.sleep()

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass