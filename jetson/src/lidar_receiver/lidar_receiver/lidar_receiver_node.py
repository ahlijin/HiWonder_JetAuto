#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LidarReceiverNode(Node):
    def __init__(self):
        super().__init__('lidar_receiver')
        self.declare_parameter('input_topic', '/pi3/scan')
        self.declare_parameter('output_topic', 'scan')

        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value

        self.subscription = self.create_subscription(
            LaserScan,
            self.input_topic,
            self.scan_callback,
            10
        )

        self.publisher = self.create_publisher(LaserScan, self.output_topic, 10)

        self.get_logger().info(f'Lidar Receiver started: {self.input_topic} -> {self.output_topic}')

    def scan_callback(self, msg: LaserScan):
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LidarReceiverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
