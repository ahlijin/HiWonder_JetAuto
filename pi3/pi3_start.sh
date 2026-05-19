#!/bin/bash


source /opt/ros/humble/setup.bash
source ~/pi3_ws/install/setup.bash
export ROS_DOMAIN_ID=42

ros2 launch bringup pi3_bringup.launch.py
