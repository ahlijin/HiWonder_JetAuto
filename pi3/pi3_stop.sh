#!/bin/bash

echo "Stopping Pi3 ROS2 nodes..."

# Kill ros2 launch and all node processes
pkill -f 'ros2 launch .*pi3_bringup' 2>/dev/null
sleep 1
pkill -f 'sllidar_node' 2>/dev/null
pkill -f 'odom_publisher' 2>/dev/null
pkill -f 'joystick_control' 2>/dev/null
pkill -f 'joint_state_publisher' 2>/dev/null
pkill -f 'ros_robot_controller' 2>/dev/null
pkill -f 'servo_controller' 2>/dev/null
pkill -f 'robot_state_publisher' 2>/dev/null
pkill -f 'startup_check' 2>/dev/null

sleep 1
remaining=$(ps aux | grep -E 'ros2|python3.*node' | grep -v grep | grep -v ros2-daemon)
if [ -z "$remaining" ]; then
    echo "All nodes stopped."
else
    echo "Warning: remaining processes:"
    echo "$remaining"
fi
