#!/usr/bin/env python3
import sys
import rclpy
from rclpy.node import Node
from ros_robot_controller_msgs.msg import ServosPosition, ServoPosition


class ServoControl(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name)
        self.servo_pub = self.create_publisher(ServosPosition, '/servo_controller', 1)

    def set_position(self, servo_id, position, duration=0.3, position_unit='pulse'):
        msg = ServosPosition()
        msg.duration = duration
        msg.position_unit = position_unit
        servo = ServoPosition()
        servo.id = servo_id
        servo.position = position
        msg.position = [servo]
        self.servo_pub.publish(msg)


def main():
    if len(sys.argv) < 3:
        print("Usage: ros2 run peripherals servo_control <servo_id> <position> [duration]")
        print("  Example: ros2 run peripherals servo_control 1 500")
        print("  Example: ros2 run peripherals servo_control 1 800 0.5")
        return

    servo_id = int(sys.argv[1])
    position = float(sys.argv[2])
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3

    node = ServoControl('servo_control')
    node.set_position(servo_id, position, duration)
    node.get_logger().info(f'Servo {servo_id} -> {position} (dur={duration}s)')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
