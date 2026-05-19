#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

import sys, select, os
if os.name == 'nt':
  import msvcrt, time
else:
  import tty, termios

if os.name != 'nt':
    settings = termios.tcgetattr(sys.stdin)

LIN_VEL = 0.25
ANG_VEL = 1.0

msg = """
Control Your Robot from Jetson!
---------------------------
Moving around:
        w
   a    s    d
CTRL-C to quit
"""

def getKey(settings):
    if os.name == 'nt':
        timeout = 0.1
        startTime = time.time()
        while True:
            if msvcrt.kbhit():
                if sys.version_info[0] >= 3:
                    return msvcrt.getch().decode()
                else:
                    return msvcrt.getch()
            elif time.time() - startTime > timeout:
                return ''

    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class TeleopControl(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name)

        self.cmd_vel = self.create_publisher(Twist, "/cmd_vel", 1)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'start')

    def run(self):
        while rclpy.ok():
            key = getKey(settings)
            twist = Twist()
            if key == 'w':
                twist.linear.x = LIN_VEL
            elif key == 'x':
                twist.linear.x = -LIN_VEL
            elif key == 'a':
                twist.linear.y = LIN_VEL
            elif key == 'd':
                twist.linear.y = -LIN_VEL
            elif key == 'q':
                twist.angular.z = ANG_VEL
            elif key == 'e':
                twist.angular.z = -ANG_VEL
            elif key == 's':
                pass
            else:
                continue
            self.cmd_vel.publish(twist)
        rclpy.shutdown()

def main():
    node = TeleopControl('teleop_key_control')
    node.run()

if __name__ == "__main__":
    main()
