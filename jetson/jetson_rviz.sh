#!/bin/bash

set -e

source /opt/ros/humble/setup.bash
source ~/jetson_ws/install/setup.bash

export ROS_DOMAIN_ID=42

ros2 launch slam rviz_slam.launch.py