#!/usr/bin/env python3
# encoding: utf-8
import math
import rclpy
from enum import Enum
from rclpy.node import Node
from std_srvs.srv import Trigger
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from ros_robot_controller_msgs.msg import BuzzerState
from servo_controller.bus_servo_control import set_servo_position
from ros_robot_controller_msgs.msg import ServosPosition, ServoPosition


def val_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

AXES_MAP = 'lx', 'ly', 'rx', 'ry', 'r2', 'l2', 'hat_x', 'hat_y'
BUTTON_MAP = 'cross', 'circle', '', 'square', 'triangle', '', 'l1', 'r1', 'l2', 'r2', 'select', 'start', '', 'l3', 'r3', '', 'hat_xl', 'hat_xr', 'hat_yu', 'hat_yd', ''

class ButtonState(Enum):
    Normal = 0
    Pressed = 1
    Holding = 2
    Released = 3

class JoystickController(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name)

        self.min_value = 0.1
        # 声明参数(Parameters declaration)
        self.declare_parameter('max_linear', 0.7)
        self.declare_parameter('max_angular', 3.0)
        self.declare_parameter('disable_servo_control', True)

        self.max_linear = self.get_parameter('max_linear').value
        self.max_angular = self.get_parameter('max_angular').value
        self.disable_servo_control = self.get_parameter('disable_servo_control').value
        self.get_logger().info('\033[1;32m%s\033[0m' % self.max_linear)
        self.joints_pub = self.create_publisher(ServosPosition, '/servo_controller', 1)
        self.joy_sub = self.create_subscription(Joy, 'ros_robot_controller/joy', self.joy_callback, 1)
        self.buzzer_pub = self.create_publisher(BuzzerState, 'ros_robot_controller/set_buzzer', 1)
        self.mecanum_pub = self.create_publisher(Twist, 'controller/cmd_vel', 1)

        self.last_axes = dict(zip(AXES_MAP, [0.0, ] * len(AXES_MAP)))
        self.last_buttons = dict(zip(BUTTON_MAP, [0.0, ] * len(BUTTON_MAP)))
        self.mode = 0
        
        # 单个舵机控制（ID=1）
        self.servo_position = 500  # 当前位置（初始位置）
        self.servo_home_position = 500      # 原位
        self.servo_step = 62       # 每步脉冲数（约15度）
        self.servo_hold_step = 5   # 长按连续转动时每步脉冲数（细腻平滑）
        self.servo_min = 0         # 最小位置
        self.servo_max = 1000      # 最大位置
        self._servo_direction = 0  # 当前转动方向: 1=左, -1=右, 0=停止
        self._servo_tap = False    # True=单次点击还未触发移动
        
        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'start')

    def get_node_state(self, request, response):
        response.success = True
        return response

    def axes_callback(self, axes):
        twist = Twist()
        if abs(axes['lx']) < self.min_value:
            axes['lx'] = 0
        if abs(axes['ly']) < self.min_value:
            axes['ly'] = 0
        if abs(axes['rx']) < self.min_value:
            axes['rx'] = 0
        if abs(axes['ry']) < self.min_value:
            axes['ry'] = 0

        twist.linear.y = val_map(axes['lx'], -1, 1, -self.max_linear, self.max_linear) 
        twist.linear.x = val_map(axes['ly'], -1, 1, -self.max_linear, self.max_linear)
        twist.angular.z = val_map(axes['rx'], -1, 1, -self.max_angular, self.max_angular)
        self.mecanum_pub.publish(twist)

    def select_callback(self, new_state):
        pass

    def l1_callback(self, new_state):
        pass

    def l2_callback(self, new_state):
        pass

    def r1_callback(self, new_state):
        pass

    def r2_callback(self, new_state):
        pass

    def square_callback(self, new_state):
        # 右左键：舵机左转（累积式）
        # 按下不动→等待松开判断是tap还是hold
        if new_state == ButtonState.Pressed:
            self._servo_direction = 1
            self._servo_tap = True  # 标记为可能的单次点击
        elif new_state == ButtonState.Holding:
            if self._servo_tap:
                self._servo_tap = False  # 进入长按，取消tap标记
            # 每帧微调，平滑连续转动
            self.servo_position += self.servo_hold_step
            if self.servo_position > self.servo_max:
                self.servo_position = self.servo_max
            set_servo_position(self.joints_pub, 0.05, ((1, self.servo_position),))
        elif new_state == ButtonState.Released:
            if self._servo_tap:
                # 快速点击：走一大步
                self.servo_position += self.servo_step
                if self.servo_position > self.servo_max:
                    self.servo_position = self.servo_max
                set_servo_position(self.joints_pub, 0.3, ((1, self.servo_position),))
                self.get_logger().info(f'Servo turned right, current position: {self.servo_position}')
            else:
                # 长按结束：快速停住
                set_servo_position(self.joints_pub, 0.05, ((1, self.servo_position),))
            self._servo_direction = 0
            self._servo_tap = False

    def cross_callback(self, new_state):
        # 右下键：舵机返回原位
        if new_state == ButtonState.Pressed:
            dist = abs(self.servo_position - self.servo_home_position)
            duration = max(0.1, dist / 200.0)  # 200脉冲/秒匀速（hold的2倍）
            self.servo_position = self.servo_home_position
            set_servo_position(self.joints_pub, duration, ((1, self.servo_position),))
            self.get_logger().info(f'Servo returned to home position: {self.servo_position}')

    def circle_callback(self, new_state):
        # 右右键：舵机右转（累积式）
        # 按下不动→等待松开判断是tap还是hold
        if new_state == ButtonState.Pressed:
            self._servo_direction = -1
            self._servo_tap = True  # 标记为可能的单次点击
        elif new_state == ButtonState.Holding:
            if self._servo_tap:
                self._servo_tap = False  # 进入长按，取消tap标记
            # 每帧微调，平滑连续转动
            self.servo_position -= self.servo_hold_step
            if self.servo_position < self.servo_min:
                self.servo_position = self.servo_min
            set_servo_position(self.joints_pub, 0.05, ((1, self.servo_position),))
        elif new_state == ButtonState.Released:
            if self._servo_tap:
                # 快速点击：走一大步
                self.servo_position -= self.servo_step
                if self.servo_position < self.servo_min:
                    self.servo_position = self.servo_min
                set_servo_position(self.joints_pub, 0.3, ((1, self.servo_position),))
                self.get_logger().info(f'Servo turned left, current position: {self.servo_position}')
            else:
                # 长按结束：快速停住
                set_servo_position(self.joints_pub, 0.05, ((1, self.servo_position),))
            self._servo_direction = 0
            self._servo_tap = False

    def triangle_callback(self, new_state):
        # 右上键：舵机返回原位
        if new_state == ButtonState.Pressed:
            dist = abs(self.servo_position - self.servo_home_position)
            duration = max(0.1, dist / 200.0)  # 200脉冲/秒匀速（hold的2倍）
            self.servo_position = self.servo_home_position
            set_servo_position(self.joints_pub, duration, ((1, self.servo_position),))
            self.get_logger().info(f'Servo returned to home position: {self.servo_position}')

    def start_callback(self, new_state):
        if new_state == ButtonState.Pressed:
            msg = BuzzerState()
            msg.freq = 2500
            msg.on_time = 0.05
            msg.off_time = 0.01
            msg.repeat = 1
            self.buzzer_pub.publish(msg)

    def hat_xl_callback(self, new_state):
        pass

    def hat_xr_callback(self, new_state):
        pass

    def hat_yd_callback(self, new_state):
        pass

    def hat_yu_callback(self, new_state):
        pass

    def joy_callback(self, joy_msg):
        axes = dict(zip(AXES_MAP, joy_msg.axes))
        axes_changed = False
        hat_x, hat_y = axes['hat_x'], axes['hat_y']
        hat_xl, hat_xr = 1 if hat_x > 0.5 else 0, 1 if hat_x < -0.5 else 0
        hat_yu, hat_yd = 1 if hat_y > 0.5 else 0, 1 if hat_y < -0.5 else 0
        buttons = list(joy_msg.buttons)
        buttons.extend([hat_xl, hat_xr, hat_yu, hat_yd, 0])
        buttons = dict(zip(BUTTON_MAP, buttons))
        for key, value in axes.items(): # 轴的值被改变(The value of the axis has been changed)
            if self.last_axes[key] != value:
                axes_changed = True
        if axes_changed:
            try:
                self.axes_callback(axes)
            except Exception as e:
                self.get_logger().error(str(e))
        for key, value in buttons.items():
            if value != self.last_buttons[key]:
                new_state = ButtonState.Pressed if value > 0 else ButtonState.Released
            else:
                new_state = ButtonState.Holding if value > 0 else ButtonState.Normal
            callback = "".join([key, '_callback'])
            if new_state != ButtonState.Normal:
                # 仅Press和Release时打日志，避免长按Holding刷屏
                if new_state in (ButtonState.Pressed, ButtonState.Released):
                    self.get_logger().info(str(new_state))
                if  hasattr(self, callback):
                    try:
                        getattr(self, callback)(new_state)
                    except Exception as e:
                        self.get_logger().error(str(e))
        self.last_buttons = buttons
        self.last_axes = axes

def main():
    node = JoystickController('joystick_control')
    rclpy.spin(node)  # 循环等待ROS2退出(Loop to wait for ROS2 to exit)

if __name__ == "__main__":
    main()

