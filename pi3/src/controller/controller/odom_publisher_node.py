#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import math
import time
import rclpy
import signal
import threading
from rclpy.node import Node
from controller import mecanum
from std_srvs.srv import Trigger
from nav_msgs.msg import Odometry
from ros_robot_controller_msgs.msg import MotorsState, BusServoState, SetBusServoState 
from geometry_msgs.msg import Pose2D, Pose, Twist, PoseWithCovarianceStamped, TransformStamped
from sensor_msgs.msg import LaserScan

ODOM_POSE_COVARIANCE = list(map(float, 
                        [1e-3, 0, 0, 0, 0, 0, 
                        0, 1e-3, 0, 0, 0, 0,
                        0, 0, 1e6, 0, 0, 0,
                        0, 0, 0, 1e6, 0, 0,
                        0, 0, 0, 0, 1e6, 0,
                        0, 0, 0, 0, 0, 1e3]))

ODOM_POSE_COVARIANCE_STOP = list(map(float, 
                            [1e-9, 0, 0, 0, 0, 0, 
                             0, 1e-3, 1e-9, 0, 0, 0,
                             0, 0, 1e6, 0, 0, 0,
                             0, 0, 0, 1e6, 0, 0,
                             0, 0, 0, 0, 1e6, 0,
                             0, 0, 0, 0, 0, 1e-9]))

ODOM_TWIST_COVARIANCE = list(map(float, 
                        [1e-3, 0, 0, 0, 0, 0, 
                         0, 1e-3, 0, 0, 0, 0,
                         0, 0, 1e6, 0, 0, 0,
                         0, 0, 0, 1e6, 0, 0,
                         0, 0, 0, 0, 1e6, 0,
                         0, 0, 0, 0, 0, 1e3]))

ODOM_TWIST_COVARIANCE_STOP = list(map(float, 
                            [1e-9, 0, 0, 0, 0, 0, 
                              0, 1e-3, 1e-9, 0, 0, 0,
                              0, 0, 1e6, 0, 0, 0,
                              0, 0, 0, 1e6, 0, 0,
                              0, 0, 0, 0, 1e6, 0,
                              0, 0, 0, 0, 0, 1e-9]))

def rpy2qua(roll, pitch, yaw):
    cy = math.cos(yaw*0.5)
    sy = math.sin(yaw*0.5)
    cp = math.cos(pitch*0.5)
    sp = math.sin(pitch*0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    
    q = Pose()
    q.orientation.w = cy * cp * cr + sy * sp * sr
    q.orientation.x = cy * cp * sr - sy * sp * cr
    q.orientation.y = sy * cp * sr + cy * sp * cr
    q.orientation.z = sy * cp * cr - cy * sp * sr
    return q.orientation

def qua2rpy(x, y, z, w):
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(2 * (w * y - x * z))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (z * z + y * y))
  
    return roll, pitch, yaw

class Controller(Node):
    
    def __init__(self, name):
        rclpy.init()
        super().__init__(name)

        self.x = 0.0
        self.y = 0.0
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.angular_z = 0.0
        self.pose_yaw = 0
        self.last_time = None
        self.current_time = None
        signal.signal(signal.SIGINT, self.shutdown)

        self.mecanum = mecanum.MecanumChassis(wheelbase=0.216, track_width=0.195, wheel_diameter=0.097)

        # 声明参数
        self.declare_parameter('pub_odom_topic', True)
        self.declare_parameter('base_frame_id', 'base_footprint')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('linear_correction_factor', 1.00)
        self.declare_parameter('angular_correction_factor', 1.00)
        self.declare_parameter('safety_enabled', True)
        self.declare_parameter('safety_stop_distance', 0.15)
        self.declare_parameter('safety_slow_distance', 0.30)
        self.declare_parameter('safety_forward_angle', 30.0)  # ±度，前方检测范围
        
        self.pub_odom_topic = self.get_parameter('pub_odom_topic').value
        self.base_frame_id = self.get_parameter('base_frame_id').value
        self.odom_frame_id = self.get_parameter('odom_frame_id').value
        
        self.linear_factor = self.get_parameter('linear_correction_factor').value
        self.angular_factor = self.get_parameter('angular_correction_factor').value

        self.clock = self.get_clock() 
        if self.pub_odom_topic:
            self.odom = Odometry()
            self.odom.header.frame_id = self.odom_frame_id
            self.odom.child_frame_id = self.base_frame_id
            
            self.odom.pose.covariance = ODOM_POSE_COVARIANCE
            self.odom.twist.covariance = ODOM_TWIST_COVARIANCE
            
            self.odom_pub = self.create_publisher(Odometry, 'odom', 1)
            self.dt = 1.0/50.0

            threading.Thread(target=self.cal_odom_fun, daemon=True).start()
        self.get_logger().info('\033[1;32m%f %f\033[0m' % (self.linear_factor, self.angular_factor))
        self.motor_pub = self.create_publisher(MotorsState, 'ros_robot_controller/set_motor', 1)
        self.servo_state_pub = self.create_publisher(SetBusServoState, 'ros_robot_controller/bus_servo/set_state', 1)
        self.pose_pub = self.create_publisher(PoseWithCovarianceStamped, 'set_pose', 1)
        self.create_subscription(Pose2D, 'set_odom', self.set_odom, 1)
        self.create_subscription(Twist, 'controller/cmd_vel', self.cmd_vel_callback, 1)
        self.create_subscription(Twist, 'cmd_vel', self.app_cmd_vel_callback, 1)
        self.create_subscription(LaserScan, 'scan_raw', self.scan_callback, 1)
        self.create_service(Trigger, 'controller/load_calibrate_param', self.load_calibrate_param)

        # 安全保护参数
        self.safety_enabled = self.get_parameter('safety_enabled').value
        self.safety_stop_distance = self.get_parameter('safety_stop_distance').value
        self.safety_slow_distance = self.get_parameter('safety_slow_distance').value
        self.safety_forward_angle = self.get_parameter('safety_forward_angle').value
        self.front_distance = float('inf')
        self.scan_received = False

        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'start')

    def get_node_state(self, request, response):
        response.success = True
        return response

    def shutdown(self, signum, frame):
        self.get_logger().info('\033[1;32m%s\033[0m' % 'shutdown')
        rclpy.shutdown()

    def load_calibrate_param(self, request, response):
        self.linear_factor = self.get_parameter('~linear_correction_factor').value or 1.00
        self.angular_factor = self.get_parameter('~angular_correction_factor').value or 1.00
        self.get_logger().info('\033[1;32m%s\033[0m' % 'load_calibrate_param')

        response.success = True
        return response

    def set_odom(self, msg):
        self.odom = Odometry()
        self.odom.header.frame_id = self.odom_frame_id
        self.odom.child_frame_id = self.base_frame_id
        
        self.odom.pose.covariance = ODOM_POSE_COVARIANCE
        self.odom.pose.pose.position.x = msg.x
        self.odom.pose.pose.position.y = msg.y
        self.pose_yaw = msg.theta
        self.odom.pose.pose.orientation = rpy2qua(0, 0, self.pose_yaw)
        
        self.linear_x = 0
        self.linear_y = 0
        self.angular_z = 0
        
        pose = PoseWithCovarianceStamped()
        pose.header.frame_id = self.odom_frame_id
        pose.header.stamp = self.clock().now().to_msg()
        pose.pose.pose = self.odom.pose.pose
        pose.pose.covariance = ODOM_POSE_COVARIANCE
        self.pose_pub.publish(pose)

    def scan_callback(self, msg):
        """Store minimum forward distance from LiDAR scan.
           Note: LiDAR frame is rotated 180° vs base_link, so forward = angle ~π."""
        if not msg.ranges:
            return
        angle_rad = math.radians(self.safety_forward_angle)
        min_dist = float('inf')
        for i, r in enumerate(msg.ranges):
            if r <= msg.range_min or r >= msg.range_max:
                continue
            angle = msg.angle_min + i * msg.angle_increment
            # LiDAR 0° = robot back, forward = around π
            forward_angle = abs(angle - math.pi)
            # Normalize to [0, π]
            while forward_angle > math.pi:
                forward_angle = abs(forward_angle - 2 * math.pi)
            if forward_angle <= angle_rad:
                if r < min_dist:
                    min_dist = r
        self.front_distance = min_dist
        self.scan_received = True

    def _check_safety(self, linear_x, linear_y, angular_z):
        """Apply safety limits based on forward LiDAR distance.
           Only limits forward movement; backward/lateral/rotation allowed."""
        if not self.safety_enabled or not self.scan_received:
            return linear_x, linear_y, angular_z

        fd = self.front_distance
        if fd > self.safety_slow_distance or linear_x <= 0:
            return linear_x, linear_y, angular_z

        # 前方有障碍：只限制前进
        if linear_x > 0:
            if fd < self.safety_stop_distance:
                self.get_logger().warn(
                    f'Collision STOP: front={fd:.2f}m')
                return 0.0, linear_y, angular_z
            # 减速区：线性缩放前进速度
            factor = (fd - self.safety_stop_distance) / \
                     (self.safety_slow_distance - self.safety_stop_distance)
            factor = max(0.0, min(1.0, factor))
            self.get_logger().info(
                f'Collision SLOW: front={fd:.2f}m factor={factor:.2f}')
            return linear_x * factor, linear_y, angular_z

        return linear_x, linear_y, angular_z

    def app_cmd_vel_callback(self, msg):
        if msg.linear.x > 0.2:
            msg.linear.x = 0.2
        if msg.linear.x < -0.2:
            msg.linear.x = -0.2
        if msg.linear.y > 0.2:
            msg.linear.y = 0.2
        if msg.linear.y < -0.2:
            msg.linear.y = -0.2
        if msg.angular.z > 0.5:
            msg.angular.z = 0.5
        if msg.angular.z < -0.5:
            msg.angular.z = -0.5
        self.cmd_vel_callback(msg)

    def cmd_vel_callback(self, msg):
        # 安全检测
        lx, ly, az = self._check_safety(
            msg.linear.x, msg.linear.y, msg.angular.z)

        self.linear_x = lx
        self.linear_y = ly
        self.angular_z = az
        speeds = self.mecanum.set_velocity(lx, ly, az)
        self.motor_pub.publish(speeds)

    def cal_odom_fun(self):
        while True:
            self.current_time = time.time()
            if self.last_time is None:
                self.dt = 0.0
            else:
                # 计算时间间隔
                self.dt = self.current_time - self.last_time
            self.odom.header.stamp = self.clock.now().to_msg()

            self.x += math.cos(self.pose_yaw)*self.linear_x*self.dt - math.sin(self.pose_yaw)*self.linear_y*self.dt
            self.y += math.sin(self.pose_yaw)*self.linear_x*self.dt + math.cos(self.pose_yaw)*self.linear_y*self.dt

            self.odom.pose.pose.position.x = self.linear_factor*self.x
            self.odom.pose.pose.position.y = self.linear_factor*self.y
            self.odom.pose.pose.position.z = 0.0

            self.pose_yaw += self.angular_factor*self.angular_z*self.dt

            self.odom.pose.pose.orientation = rpy2qua(0.0, 0.0, self.pose_yaw)
            self.odom.twist.twist.linear.x = self.linear_x
            self.odom.twist.twist.linear.y = self.linear_y
            self.odom.twist.twist.angular.z = self.angular_z

            # 如果velocity是零，说明编码器的误差会比较小，认为编码器数据更可靠
            # 如果velocity非零，考虑到运动中编码器可能带来的滑动误差，认为imu的数据更可靠
            if self.linear_x == 0 and self.linear_y == 0 and self.angular_z == 0:
                self.odom.pose.covariance = ODOM_POSE_COVARIANCE_STOP
                self.odom.twist.covariance = ODOM_TWIST_COVARIANCE_STOP
            else:
                self.odom.pose.covariance = ODOM_POSE_COVARIANCE
                self.odom.twist.covariance = ODOM_TWIST_COVARIANCE

            self.odom_pub.publish(self.odom)
            self.last_time = self.current_time
            time.sleep(0.05)  # 从50Hz降至20Hz，降低CPU占用

def main():
    node = Controller('odom_publisher')
    rclpy.spin(node)  # 循环等待ROS2退出

if __name__ == "__main__":
    main()
