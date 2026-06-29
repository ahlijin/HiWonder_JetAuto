#!/usr/bin/env python3
# encoding: utf-8
import os
import time
import math
import rclpy
import threading
from rclpy.node import Node
from std_srvs.srv import Trigger
from sensor_msgs.msg import JointState
from servo_controller.joint_position_controller import JointPositionController
from ros_robot_controller_msgs.msg import ServosPosition, ServoState, ServoStateList
from ros_robot_controller_msgs.srv import GetBusServoState
from ros_robot_controller_msgs.msg import ServoPosition


class ServoStateData:
    def __init__(self, name=''):
        self.name = name
        self.position = 500


class ServoManager(Node):
    def __init__(self, connected_ids={}):
        super().__init__('servo_manager')
        self.servos = {}
        self.connected_ids = connected_ids
        for i in connected_ids:
            self.servos[i] = ServoStateData(connected_ids[i])
        self.servo_position_pub = self.create_publisher(ServosPosition, 'ros_robot_controller/bus_servo/set_position', 1)
        self.client = self.create_client(GetBusServoState, 'ros_robot_controller/bus_servo/get_state')
        self.client.wait_for_service()
        self.get_logger().info('\033[1;32m%s\033[0m' % 'start')

    def connect(self):
        pass

    def get_position(self):
        return self.servos

    def set_position(self, duration, position):
        duration = 0.02 if duration < 0.02 else 30 if duration > 30 else duration
        msg = ServosPosition()
        msg.duration = float(duration)
        for i in position:
            pos = int(i.position)
            pos = 0 if pos < 0 else 1000 if pos > 1000 else pos
            self.servos[str(i.id)].position = pos
            servo_msg = ServoPosition()
            servo_msg.id = i.id
            servo_msg.position = float(pos)
            msg.position.append(servo_msg)
        self.servo_position_pub.publish(msg)


class ControllerManager(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name, allow_undeclared_parameters=True, automatically_declare_parameters_from_overrides=True)
        
        self.joints = ['joint1']       

        # 读取配置参数(Read configuration parameters)
        self.base_frame = self.get_parameter('base_frame').value
        
        # trajectory_controller的初始化(Initialization of the trajectory_controller)
        self.controllers = {}
        connected_ids = {}
        for i in self.joints:
            joint = self.get_parameters_by_prefix(i)
            connected_ids[str(joint['id'].value)] = i
            controller = JointPositionController(joint, i)
            self.controllers[i] = controller

        # 实例化舵机管理节�?Instantiate the servo management node)
        self.servo_manager = ServoManager(connected_ids)
        self.servo_manager.connect()

        self.joint_states_pub = self.create_publisher(JointState, '~/joint_states', 1)
        self.servo_states_pub = self.create_publisher(ServoStateList, '~/servo_states', 1)
        self.create_subscription(ServosPosition, 'servo_controller', self.servo_controller_callback, 1)
        self.create_subscription(JointState, 'joint_controller', self.joint_controller_callback, 1)

        self.clock = self.get_clock()
        # 确保ros_robot_controller已完成初始化(Ensure that ros_robot_controller has been initialized)
        namespace = self.get_namespace()
        if namespace == '/':
            namespace = ''
        self.client = self.create_client(Trigger, namespace + '/ros_robot_controller/init_finish')
        self.client.wait_for_service()

        threading.Thread(target=self.publish_joint_states, daemon=True).start()
        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'start')

    def get_node_state(self, request, response):
        response.success = True
        return response

    def servo_controller_callback(self, msg):
        data = ServosPosition()
        positions = self.servo_manager.get_position()
        if msg.position_unit == 'pulse':
            for i in msg.position:
                if str(i.id) in positions:
                    data.position.append(i)
            self.servo_manager.set_position(msg.duration, data.position)
        elif msg.position_unit == 'rad':
            for i in msg.position:
                if str(i.id) in positions:
                    i.position = self.controllers[positions[str(i.id)].name].pos_rad_to_pulse(i.position)
                    data.position.append(i)
            self.servo_manager.set_position(msg.duration, data.position)
        elif msg.position_unit == 'deg':
            for i in msg.position:
                if str(i.id) in positions:
                    i.position = self.controllers[positions[str(i.id)].name].pos_rad_to_pulse(math.radians(i.position))
                    data.position.append(i)
            self.servo_manager.set_position(msg.duration, data.position)

    def joint_controller_callback(self, msg):
        for name, position in zip(msg.name, msg.position):
            if name in self.controllers:
                self.servo_manager.set_position(self.controllers[name].servo_id, self.controllers[name].pos_rad_to_pulse(position))
                time.sleep(0.005)

    def publish_joint_states(self):
        while True:
            msg = JointState()
            msg.header.stamp = self.clock.now().to_msg()
            msg.header.frame_id = self.base_frame
            positions = self.servo_manager.get_position()
            servos_msg = ServoStateList()
            servos_msg.header = msg.header
            for i in positions:
                msg.name.append(positions[i].name)
                msg.position.append(self.controllers[positions[i].name].pos_pulse_to_rad(positions[i].position))
                
                servo_msg = ServoState()
                servo_msg.id = int(i)
                servo_msg.position = int(positions[i].position)
                servos_msg.servo_state.append(servo_msg)
            self.joint_states_pub.publish(msg)
            self.servo_states_pub.publish(servos_msg)
            time.sleep(0.05)  # 从50Hz降至20Hz，降低CPU占用

def main():
    node = ControllerManager('controller_manager')
    rclpy.spin(node)  # 循环等待ROS2退�?Loop and wait for ROS2 to exit)

if __name__ == "__main__":
    main()
