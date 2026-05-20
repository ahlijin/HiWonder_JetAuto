#!/usr/bin/env python3
# encoding: utf-8
import time
import rclpy
from std_srvs.srv import Trigger
from ros_robot_controller_msgs.msg import BuzzerState


def main():
    rclpy.init()
    node = rclpy.create_node('startup')

    client = node.create_client(Trigger, '/ros_robot_controller/init_finish')
    if not client.wait_for_service(timeout_sec=10.0):
        node.get_logger().warn('ros_robot_controller not ready, skipping beep')
        return

    buzzer_pub = node.create_publisher(BuzzerState, '/ros_robot_controller/set_buzzer', 1)
    time.sleep(0.5)

    msg = BuzzerState()
    msg.freq = 1900
    msg.on_time = 0.2
    msg.off_time = 0.01
    msg.repeat = 1
    buzzer_pub.publish(msg)

if __name__ == '__main__':
    main()
