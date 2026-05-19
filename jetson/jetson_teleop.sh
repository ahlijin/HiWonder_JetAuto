#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/jetson_ws/install/setup.bash

export ROS_DOMAIN_ID=42

echo "Starting Jetson teleop keyboard control..."
echo "  w/a/s/d - move"
echo "  q/e     - rotate"
echo "  s       - stop"
echo ""

ros2 run jetauto_peripherals teleop_key_control
