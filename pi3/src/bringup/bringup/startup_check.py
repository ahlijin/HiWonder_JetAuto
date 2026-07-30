#!/usr/bin/env python3
# encoding: utf-8
import time
import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_srvs.srv import Trigger
from ros_robot_controller_msgs.msg import BuzzerState


def main():
    rclpy.init()
    node = rclpy.create_node('startup')
    executor = SingleThreadedExecutor()
    executor.add_node(node)

    client = node.create_client(Trigger, '/ros_robot_controller/init_finish')
    if not client.wait_for_service(timeout_sec=10.0):
        node.get_logger().warn('ros_robot_controller not ready, skipping beep')
        return

    buzzer_pub = node.create_publisher(BuzzerState, '/ros_robot_controller/set_buzzer', 1)
    # 等待 DDS 发现并建立连接
    end = time.time() + 2.0
    while time.time() < end:
        executor.spin_once(timeout_sec=0.1)

    msg = BuzzerState()
    msg.freq = 1900
    msg.on_time = 0.2
    msg.off_time = 0.01
    msg.repeat = 1
    buzzer_pub.publish(msg)

    # 保持 spinning 确保消息被投递
    end = time.time() + 1.0
    while time.time() < end:
        executor.spin_once(timeout_sec=0.1)

    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
