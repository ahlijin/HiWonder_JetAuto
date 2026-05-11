#!/usr/bin/env python3
# encoding: utf-8
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from servo_controller_msgs.msg import ServosPosition, ServoPosition

class InitPose(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name, allow_undeclared_parameters=True, automatically_declare_parameters_from_overrides=True)  # 允许未声明的参数(Allow undeclared parameters)
        
        namespace = self.get_namespace()
        if namespace == '/':
            namespace = ''
       
        self.servo_controller_pub = self.create_publisher(ServosPosition, 'servo_controller', 1)

        self.client = self.create_client(Trigger, namespace + '/controller_manager/init_finish')
        self.client.wait_for_service()

        # 读取配置参数，设置舵机初始位置
        pulse = self.get_parameters_by_prefix('servo')
        msg = ServosPosition()
        msg.duration = float(pulse['duration'].value)
        data = []   
        # 只处理舵机 ID=1（单个舵机）
        if 'id1' in pulse:
            servo = ServoPosition()
            servo.id = 1
            servo.position = float(pulse['id1'].value)
            data.append(servo)
        msg.position = data
        self.servo_controller_pub.publish(msg)

        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32mInit pose completed\033[0m')

    def get_node_state(self, request, response):
        response.success = True
        return response

def main():
    node = InitPose('init_pose')
    rclpy.spin(node)  # 循环等待ROS2退出(Loop and wait for ROS2 to exit)

if __name__ == "__main__":
    main()
